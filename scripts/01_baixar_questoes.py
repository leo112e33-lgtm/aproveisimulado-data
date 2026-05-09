"""
01_baixar_questoes.py
=====================
Baixa todas as questoes do ENEM (2018-2023) da API enem.dev e salva em JSON.

Saida: enem/<ano>/dia<N>.json (90 questoes por arquivo).

Uso:
    python scripts/01_baixar_questoes.py
    python scripts/01_baixar_questoes.py --anos 2023 --dias 1
    python scripts/01_baixar_questoes.py --paralelo 16

Caracteristicas:
- Usa ThreadPoolExecutor para baixar varias questoes em paralelo.
- Faz fallback automatico para correcoes manuais quando a API falha.
- Idempotente: se o JSON ja existe e foi gerado com sucesso, nao refaz
  (use --forcar para refazer).
- Marca questoes nao encontradas (404 definitivo) com fonte = "indisponivel"
  para que o app possa anular automaticamente, sem nova consulta.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# Permite importar correcoes_manuais como modulo irmao.
sys.path.insert(0, str(Path(__file__).parent))
import correcoes_manuais  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ENEM_DIR = ROOT / "enem"

ANOS_DEFAULT = [2018, 2019, 2020, 2021, 2022, 2023]
QUESTOES_POR_DIA = 90
TIMEOUT = 10
MAX_TENTATIVAS = 5
SLEEP_RETRY = 1.0


def buscar_da_api(ano: int, api_idx: int) -> Optional[dict]:
    """
    Retorna o JSON da API enem.dev para uma questao.
    None: erro temporario (vale a pena tentar de novo).
    {"_404": True}: 404 definitivo, questao nao existe na base.
    """
    url = f"https://api.enem.dev/v1/exams/{ano}/questions/{api_idx}"
    req = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        if e.code == 404:
            return {"_404": True}
        return None
    except (URLError, TimeoutError, json.JSONDecodeError):
        return None


def normalizar_da_api(payload: dict, ano: int, dia: int, numero: int) -> dict:
    """Converte o JSON cru da API enem.dev para o formato do dataset."""
    contexto = (payload.get("context") or "").replace(
        "![](https://enem.dev/broken-image.svg)", ""
    ).strip()
    intro = payload.get("alternativesIntroduction") or ""
    correta = payload.get("correctAlternative") or "X"

    alts_raw = payload.get("alternatives") or []
    alternativas: list[str] = []
    imagens_alts: list[Optional[str]] = []
    for j, a in enumerate(alts_raw):
        letra = a.get("letter") or chr(ord("A") + j)
        texto = a.get("text") or ""
        if texto == "null":
            texto = ""
        alternativas.append(f"{letra}) {texto}".rstrip() if texto else f"{letra})")
        imagens_alts.append(a.get("file"))

    files = payload.get("files") or []
    imagem_principal = files[0] if files else ""
    imagens_extras = files[1:] if len(files) > 1 else []

    return {
        "ano": ano,
        "dia": dia,
        "numero": numero,
        "titulo": payload.get("title") or f"Questao {numero}",
        "enunciado": contexto,
        "alternativas_introducao": intro,
        "alternativas": alternativas,
        "imagens_alternativas": imagens_alts,
        "imagem_principal": imagem_principal,
        "imagens_extras": imagens_extras,
        "correta": correta,
        "explicacao": "",  # preenchido na fase 03
        "fonte": "api.enem.dev",
        "fonte_url": f"https://api.enem.dev/v1/exams/{ano}/questions/{(numero if dia == 1 else QUESTOES_POR_DIA + numero)}",
    }


def aplicar_correcao_manual(c: dict) -> dict:
    """Converte uma correcao manual (correcoes_manuais.py) para formato do dataset."""
    imagem_principal = ""
    if "_local_imagem_principal" in c:
        imagem_principal = f"local:{c['_local_imagem_principal']}"
    imagens_alts: list[Optional[str]] = list(c.get("imagens_alternativas", [None] * 5))
    if "_local_imagens_alternativas" in c:
        imagens_alts = [f"local:{n}" for n in c["_local_imagens_alternativas"]]

    return {
        "ano": c["ano"],
        "dia": c["dia"],
        "numero": c["numero"],
        "titulo": c["titulo"],
        "enunciado": c["enunciado"],
        "alternativas_introducao": c.get("alternativas_introducao", ""),
        "alternativas": c["alternativas"],
        "imagens_alternativas": imagens_alts,
        "imagem_principal": imagem_principal,
        "imagens_extras": [],
        "correta": c["correta"],
        "explicacao": "",
        "fonte": "correcao_manual",
        "fonte_url": "",
    }


def buscar_questao(ano: int, dia: int, numero: int) -> dict:
    """Pipeline completo: correcao manual -> API com retry -> placeholder indisponivel."""
    correcao = correcoes_manuais.obter(ano, dia, numero)
    if correcao:
        return aplicar_correcao_manual(correcao)

    api_idx = numero if dia == 1 else QUESTOES_POR_DIA + numero

    for tentativa in range(MAX_TENTATIVAS):
        payload = buscar_da_api(ano, api_idx)
        if payload is None:
            time.sleep(SLEEP_RETRY * (tentativa + 1))
            continue
        if payload.get("_404"):
            return {
                "ano": ano,
                "dia": dia,
                "numero": numero,
                "titulo": f"Questao {numero} - ENEM {ano}",
                "enunciado": "",
                "alternativas_introducao": "",
                "alternativas": [],
                "imagens_alternativas": [],
                "imagem_principal": "",
                "imagens_extras": [],
                "correta": "X",
                "explicacao": "",
                "fonte": "indisponivel",
                "fonte_url": f"https://api.enem.dev/v1/exams/{ano}/questions/{api_idx}",
            }
        return normalizar_da_api(payload, ano, dia, numero)

    # Esgotou tentativas
    return {
        "ano": ano,
        "dia": dia,
        "numero": numero,
        "titulo": f"Questao {numero} - ENEM {ano}",
        "enunciado": "",
        "alternativas_introducao": "",
        "alternativas": [],
        "imagens_alternativas": [],
        "imagem_principal": "",
        "imagens_extras": [],
        "correta": "X",
        "explicacao": "",
        "fonte": "erro",
        "fonte_url": f"https://api.enem.dev/v1/exams/{ano}/questions/{api_idx}",
    }


def baixar_dia(ano: int, dia: int, paralelo: int, forcar: bool) -> dict:
    arquivo = ENEM_DIR / str(ano) / f"dia{dia}.json"
    if arquivo.exists() and not forcar:
        existente = json.loads(arquivo.read_text(encoding="utf-8"))
        # Refaz so se faltarem questoes ou existir erro temporario.
        falhas = sum(1 for q in existente["questoes"] if q["fonte"] == "erro")
        if falhas == 0 and len(existente["questoes"]) == QUESTOES_POR_DIA:
            print(f"[ENEM {ano} dia {dia}] OK (cache)")
            return existente
        print(f"[ENEM {ano} dia {dia}] reprocessando ({falhas} falhas)")

    print(f"[ENEM {ano} dia {dia}] baixando 90 questoes (paralelo={paralelo})...")
    questoes: list[Optional[dict]] = [None] * QUESTOES_POR_DIA

    with ThreadPoolExecutor(max_workers=paralelo) as pool:
        futuros = {
            pool.submit(buscar_questao, ano, dia, n + 1): n
            for n in range(QUESTOES_POR_DIA)
        }
        for fut in as_completed(futuros):
            idx = futuros[fut]
            questoes[idx] = fut.result()
            tag = questoes[idx]["fonte"]
            simbolo = {
                "api.enem.dev": ".",
                "correcao_manual": "M",
                "indisponivel": "_",
                "erro": "X",
            }.get(tag, "?")
            print(simbolo, end="", flush=True)
    print()

    payload_dia = {
        "ano": ano,
        "dia": dia,
        "total": QUESTOES_POR_DIA,
        "geradoEm": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "questoes": questoes,
    }
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    arquivo.write_text(
        json.dumps(payload_dia, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    contagem = {}
    for q in questoes:
        contagem[q["fonte"]] = contagem.get(q["fonte"], 0) + 1
    print(f"  -> salvo em {arquivo.relative_to(ROOT)} | {contagem}")
    return payload_dia


def gerar_manifest(provas: list[dict]) -> None:
    manifest = {
        "geradoEm": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "provas": [
            {
                "ano": p["ano"],
                "dia": p["dia"],
                "totalQuestoes": p["total"],
                "arquivo": f"enem/{p['ano']}/dia{p['dia']}.json",
                "fontes": _contar_fontes(p["questoes"]),
            }
            for p in provas
        ],
    }
    (ROOT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"manifest.json atualizado ({len(provas)} provas).")


def _contar_fontes(questoes: list[dict]) -> dict:
    out: dict = {}
    for q in questoes:
        out[q["fonte"]] = out.get(q["fonte"], 0) + 1
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--anos", nargs="*", type=int, default=ANOS_DEFAULT)
    p.add_argument("--dias", nargs="*", type=int, default=[1, 2])
    p.add_argument("--paralelo", type=int, default=12)
    p.add_argument("--forcar", action="store_true")
    args = p.parse_args()

    provas: list[dict] = []
    for ano in args.anos:
        for dia in args.dias:
            provas.append(baixar_dia(ano, dia, args.paralelo, args.forcar))

    gerar_manifest(provas)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
