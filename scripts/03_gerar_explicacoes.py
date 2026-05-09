"""
03_gerar_explicacoes.py
=======================
Para cada questao do dataset, gera uma explicacao didatica em portugues
chamando a API Gemini. Idempotente: questoes que ja tem explicacao sao
puladas (use --forcar para refazer).

Uso:
    python scripts/03_gerar_explicacoes.py
    python scripts/03_gerar_explicacoes.py --anos 2023 --dias 1
    python scripts/03_gerar_explicacoes.py --modelo gemini-2.5-flash
    python scripts/03_gerar_explicacoes.py --paralelo 4 --rpm 12

Chave da API:
    Variavel de ambiente GEMINI_API_KEY ou flag --api-key.
    Recomendado usar arquivo .env (carregado se python-dotenv instalado).

Free tier do gemini-2.5-flash-lite: 30 RPM, 1500 RPD. Default --rpm=20 fica
dentro do limite. Para 1080 questoes, levara ~54 minutos por dia (limite
diario de 1500 nao e atingido).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
ENEM_DIR = ROOT / "enem"

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(ROOT / ".env")
except Exception:
    pass

MODELOS_FALLBACK = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
]


class RateLimiter:
    """Limita chamadas a `rpm` por minuto considerando todas as threads."""

    def __init__(self, rpm: int) -> None:
        self.intervalo = 60.0 / rpm if rpm > 0 else 0
        self.lock = threading.Lock()
        self.proximo = 0.0

    def wait(self) -> None:
        if self.intervalo == 0:
            return
        with self.lock:
            agora = time.monotonic()
            if agora < self.proximo:
                time.sleep(self.proximo - agora)
                agora = time.monotonic()
            self.proximo = agora + self.intervalo


def montar_prompt(q: dict) -> str:
    correta = q.get("correta") or "X"
    enunciado = q.get("enunciado") or ""
    intro = q.get("alternativas_introducao") or ""
    alts = "\n".join(q.get("alternativas") or [])
    cabecalho = (
        f"Questao {q['numero']} do ENEM {q['ano']} (Dia {q['dia']}). "
        f"Resposta correta oficial: alternativa {correta}.\n\n"
    )
    return (
        cabecalho
        + (enunciado + "\n\n" if enunciado else "")
        + (intro + "\n\n" if intro else "")
        + ("Alternativas:\n" + alts + "\n\n" if alts else "")
        + "Explique de forma didatica em portugues do Brasil, em ate 4 paragrafos curtos:\n"
        + f"1. Por que a alternativa {correta} esta correta (1-2 paragrafos).\n"
        + "2. Por que as outras alternativas estao erradas (de forma sucinta, junte tudo em 1 paragrafo).\n"
        + "3. O conceito-chave que o aluno precisa dominar (1 paragrafo).\n\n"
        + "Seja conciso, preciso e nao invente fatos."
    )


def chamar_gemini(api_key: str, prompt: str, modelo: str) -> str:
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{modelo}:generateContent?key={api_key}"
    )
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1200},
    }).encode("utf-8")

    req = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=90) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        detalhe = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code} {detalhe[:300]}") from None
    except URLError as e:
        raise RuntimeError(f"URL error: {e.reason}") from None

    cand = payload.get("candidates") or []
    if not cand:
        raise RuntimeError("Sem candidatos na resposta")
    parts = cand[0].get("content", {}).get("parts") or []
    if not parts:
        raise RuntimeError("Resposta vazia")
    return parts[0].get("text", "").strip()


def gerar_para_questao(q: dict, api_key: str, modelos: list[str], rate: RateLimiter) -> tuple[int, str | None, str | None]:
    if q.get("fonte") == "indisponivel" or not (q.get("alternativas") or []):
        return q["numero"], None, "indisponivel"

    prompt = montar_prompt(q)
    ultimo_erro = ""
    # Para cada modelo, retry interno com backoff em caso de 429.
    for modelo in modelos:
        for tentativa in range(3):
            rate.wait()
            try:
                texto = chamar_gemini(api_key, prompt, modelo)
                if texto:
                    return q["numero"], texto, None
            except RuntimeError as e:
                ultimo_erro = str(e)
                # 401/403 = chave invalida, abandona tudo
                if "401" in ultimo_erro or "403" in ultimo_erro:
                    return q["numero"], None, ultimo_erro
                # 429 = rate limit: espera progressivamente mais (15s, 45s, 90s)
                if "429" in ultimo_erro or "RESOURCE_EXHAUSTED" in ultimo_erro:
                    espera = [15, 45, 90][tentativa]
                    time.sleep(espera)
                    continue
                # Outros erros transientes: backoff curto
                time.sleep(3)
    return q["numero"], None, ultimo_erro or "falhou"


def processar_dia(ano: int, dia: int, api_key: str, modelos: list[str],
                  paralelo: int, rate: RateLimiter, forcar: bool) -> None:
    arquivo = ENEM_DIR / str(ano) / f"dia{dia}.json"
    if not arquivo.exists():
        print(f"[ENEM {ano} dia {dia}] sem JSON, pule a fase 01 primeiro")
        return

    payload = json.loads(arquivo.read_text(encoding="utf-8"))
    questoes = payload["questoes"]
    pendentes = [
        q for q in questoes
        if forcar or not (q.get("explicacao") or "").strip()
    ]
    if not pendentes:
        print(f"[ENEM {ano} dia {dia}] todas com explicacao (cache)")
        return

    print(f"[ENEM {ano} dia {dia}] {len(pendentes)} questoes precisam de explicacao")

    sucesso = 0
    falhas = 0
    indisponivel = 0
    questoes_por_num = {q["numero"]: q for q in questoes}

    with ThreadPoolExecutor(max_workers=paralelo) as pool:
        futuros = {
            pool.submit(gerar_para_questao, q, api_key, modelos, rate): q["numero"]
            for q in pendentes
        }
        for i, fut in enumerate(as_completed(futuros), 1):
            numero, texto, erro = fut.result()
            if texto:
                questoes_por_num[numero]["explicacao"] = texto
                sucesso += 1
                simbolo = "."
            elif erro == "indisponivel":
                indisponivel += 1
                simbolo = "_"
            else:
                falhas += 1
                simbolo = "X"
            print(simbolo, end="", flush=True)
            # Salva a cada 10 questoes para nao perder progresso
            if i % 10 == 0:
                payload["geradoEm"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                arquivo.write_text(
                    json.dumps(payload, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
    print()

    payload["geradoEm"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    arquivo.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  -> sucesso={sucesso} indisponivel={indisponivel} falhas={falhas}")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--anos", nargs="*", type=int)
    p.add_argument("--dias", nargs="*", type=int, default=[1, 2])
    p.add_argument("--api-key", default=os.environ.get("GEMINI_API_KEY", ""))
    p.add_argument("--modelo", default="")
    p.add_argument("--paralelo", type=int, default=1)
    p.add_argument("--rpm", type=int, default=10)
    p.add_argument("--forcar", action="store_true")
    args = p.parse_args()

    if not args.api_key:
        print("ERRO: defina GEMINI_API_KEY no ambiente ou passe --api-key")
        print("Para criar uma chave gratuita: https://aistudio.google.com/app/apikey")
        return 2

    modelos = [args.modelo] if args.modelo else MODELOS_FALLBACK

    anos = args.anos
    if not anos:
        if not ENEM_DIR.exists():
            print("Nenhum dado em enem/. Rode 01 e 02 antes.")
            return 1
        anos = sorted(int(p.name) for p in ENEM_DIR.iterdir() if p.is_dir() and p.name.isdigit())

    rate = RateLimiter(args.rpm)
    for ano in anos:
        for dia in args.dias:
            processar_dia(ano, dia, args.api_key, modelos, args.paralelo, rate, args.forcar)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
