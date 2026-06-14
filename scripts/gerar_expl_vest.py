# -*- coding: utf-8 -*-
"""Gera 'ver resposta' (explicacao no padrao Q91) para um JSON de prova de
vestibular, via Gemini. Uso: python gerar_expl_vest.py <caminho.json>"""
import sys, os, re, json, time, urllib.request, urllib.error
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
KEY = os.environ["GEMINI_API_KEY"]
MODELOS = ["gemini-2.5-flash-lite", "gemini-2.5-flash"]

def chamar(prompt, modelo):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={KEY}"
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}],
                       "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1200}}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read())["candidates"][0]["content"]["parts"][0]["text"].strip()

def prompt_de(q, vest, ano):
    enun = re.sub(r"!\[\]\([^)]*\)", "[figura]", q.get("enunciado", ""))
    alts = "\n".join(q.get("alternativas", []))
    corr = q.get("correta", "X")
    return (f"Questao {q.get('numero')} do vestibular {vest} {ano}. "
            f"Resposta correta oficial: alternativa {corr}.\n\n{enun}\n\nAlternativas:\n{alts}\n\n"
            "Escreva uma explicacao didatica em portugues do Brasil seguindo EXATAMENTE este "
            "formato, com estes dois titulos em negrito (markdown **) e nada alem disso:\n\n"
            f"**Por que a alternativa {corr} está correta:** (1 a 2 paragrafos)\n\n"
            "**Conceito-chave:** (1 paragrafo com o conceito principal)\n\n"
            "Se houver [figura] que voce nao ve, baseie-se no enunciado textual e na resposta "
            "oficial. Comece com \"**Por que a alternativa\"; nao invente dados; use acentuacao correta.")

def gerar(q, vest, ano):
    p = prompt_de(q, vest, ano)
    for modelo in MODELOS:
        for tent in range(4):
            try:
                t = chamar(p, modelo)
                if t and "Por que a alternativa" in t: return t
            except urllib.error.HTTPError as e:
                if e.code in (401, 403): return None
                if e.code == 429: time.sleep([6, 18, 40, 60][tent]); continue
                time.sleep(3)
            except Exception:
                time.sleep(3)
    return None

def main():
    path = sys.argv[1]
    d = json.load(open(path, encoding="utf-8"))
    vest = d.get("vestibular", "?"); ano = d.get("ano", "")
    qs = d["questoes"]
    ok = 0; fail = 0
    for i, q in enumerate(qs):
        if q.get("correta", "X") == "X":  # anulada/sem gabarito
            continue
        t = gerar(q, vest, ano)
        if t:
            q["explicacao"] = t; ok += 1; sym = "."
        else:
            fail += 1; sym = "X"
        print(sym, end="", flush=True)
        time.sleep(2.5)
        if (i+1) % 10 == 0:
            json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n=== {vest} {ano}: explicacoes ok={ok} fail={fail} ===")

if __name__ == "__main__":
    main()
