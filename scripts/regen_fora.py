"""
regen_fora.py — regera SOMENTE as questoes fora do padrao Q91 listadas em
scripts/fora_padrao.json, no formato:

    **Por que a alternativa X esta correta:** ...
    **Conceito-chave:** ...

Usa gemini-2.5-flash (flash-lite esta com a cota esgotada). Salva a cada
questao para nao perder progresso. Imprime quais falharam.
"""
import json, os, sys, time, urllib.request, urllib.error
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
KEY = os.environ["GEMINI_API_KEY"]
MODELOS = ["gemini-2.5-flash", "gemini-2.5-pro"]

def montar_prompt(q):
    correta = q.get("correta") or "X"
    enun = q.get("enunciado") or ""
    intro = q.get("alternativas_introducao") or ""
    alts = "\n".join(q.get("alternativas") or [])
    return (
        f"Questao {q['numero']} do ENEM {q['ano']} (Dia {q['dia']}). "
        f"Resposta correta oficial: alternativa {correta}.\n\n"
        + (enun + "\n\n" if enun else "")
        + (intro + "\n\n" if intro else "")
        + ("Alternativas:\n" + alts + "\n\n" if alts else "")
        + "Escreva uma explicacao didatica em portugues do Brasil seguindo "
        "EXATAMENTE este formato, com estes dois titulos em negrito (markdown **) "
        "e nada alem disso:\n\n"
        f"**Por que a alternativa {correta} esta correta:** (1 a 2 paragrafos "
        "explicando, de forma clara e direta, por que essa e a resposta certa)\n\n"
        "**Conceito-chave:** (1 paragrafo com o conceito principal que o aluno "
        "precisa dominar para resolver questoes parecidas)\n\n"
        "Regras: comece a resposta diretamente com \"**Por que a alternativa\"; "
        "use exatamente esses dois titulos; nao numere; nao crie secao de outras "
        "alternativas; seja conciso e preciso; use acentuacao correta; nao invente."
    )

def chamar(prompt, modelo):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={KEY}"
    body = json.dumps({"contents":[{"parts":[{"text":prompt}]}],
                       "generationConfig":{"temperature":0.3,"maxOutputTokens":1400}}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type":"application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.loads(r.read())
    return d["candidates"][0]["content"]["parts"][0]["text"].strip()

def gerar(q):
    prompt = montar_prompt(q)
    for modelo in MODELOS:
        for tent in range(4):
            try:
                t = chamar(prompt, modelo)
                if t: return t
            except urllib.error.HTTPError as e:
                msg = e.read().decode()[:80]
                if e.code in (401,403): return None
                if e.code == 429:
                    time.sleep([8,20,40,60][tent]); continue
                time.sleep(3)
            except Exception:
                time.sleep(3)
    return None

def main():
    fora = json.loads((ROOT/"scripts"/"fora_padrao.json").read_text())
    por_arq = {}
    for ano,dia,num in fora:
        por_arq.setdefault((ano,dia),[]).append(num)
    falhas = []
    for (ano,dia),nums in sorted(por_arq.items()):
        arq = ROOT/"enem"/str(ano)/f"dia{dia}.json"
        payload = json.loads(arq.read_text(encoding="utf-8"))
        idx = {q["numero"]:q for q in payload["questoes"]}
        for num in nums:
            q = idx[num]
            t = gerar(q)
            if t:
                q["explicacao"] = t
                print(f"OK  {ano}d{dia} Q{num}", flush=True)
            else:
                falhas.append([ano,dia,num])
                print(f"FALHA {ano}d{dia} Q{num}", flush=True)
            arq.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            time.sleep(5)
    (ROOT/"scripts"/"falhas.json").write_text(json.dumps(falhas))
    print(f"\n=== concluido. sucesso={len(fora)-len(falhas)} falhas={len(falhas)} ===")
    if falhas: print("falhas:", falhas)

if __name__ == "__main__":
    main()
