# -*- coding: utf-8 -*-
"""Monta vestibular/unicamp/<ANO>.json (72 q, 4 alts A-D) de
_unicamp_extract_<ANO>.json + gabarito (.gabaritos/unicamp_<ANO>.pdf) +
explicacoes _unicamp<ANO>expl_*.json. Uso: python unicamp_build.py <ANO> <URL>"""
import json, os, glob, re, sys, unicodedata, pypdf
ANO = sys.argv[1]
URL = sys.argv[2] if len(sys.argv) > 2 else ""
HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "..", "vestibular", "unicamp", f"{ANO}.json")
extract = {q["numero"]: q for q in json.load(open(os.path.join(HERE, f"_unicamp_extract_{ANO}.json"), encoding="utf-8"))}
gtxt = "\n".join((p.extract_text() or "") for p in pypdf.PdfReader(os.path.join(HERE, "..", ".gabaritos", f"unicamp_{ANO}.pdf")).pages)
gab = {}; anuladas = []
# formato "01 B 19 A 37 D 55 B"; anulada marcada com *
for n, l in re.findall(r"\b(\d{1,2})\s+([A-Da-d\*])", gtxt):
    n = int(n)
    if 1 <= n <= 72 and n not in gab:
        if l == "*": gab[n] = "X"; anuladas.append(n)
        else: gab[n] = l.upper()
expl = {}
for fp in sorted(glob.glob(os.path.join(HERE, f"_unicamp{ANO}expl_*.json"))):
    for k, v in json.load(open(fp, encoding="utf-8")).items():
        expl[int(k)] = v["explicacao"] if isinstance(v, dict) else v

def norm_text(s):
    s = unicodedata.normalize("NFKC", s); out, buf = [], []
    def flush():
        if buf: out.append(re.sub(r"\s+", " ", " ".join(buf)).strip()); buf.clear()
    for ln in s.split("\n"):
        t = ln.strip()
        if t.startswith("![]("): flush(); out.append(t)
        elif t == "": flush(); out.append("")
        else: buf.append(t)
    flush()
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()

questoes = []
for n in range(1, 73):
    if n not in extract: continue
    q = extract[n]
    corr = gab.get(n, "X")
    alts = [re.sub(r"\s+", " ", a).strip() for a in q.get("alternativas", [])]
    questoes.append({
        "numero": n, "ano": int(ANO), "titulo": f"Questão {n} - UNICAMP {ANO}",
        "enunciado": norm_text(q["enunciado"]), "alternativas_introducao": "",
        "alternativas": alts, "imagens_alternativas": [None]*len(alts) if alts else [],
        "imagem_principal": "", "imagens_extras": [],
        "correta": corr, "explicacao": "" if corr == "X" else expl.get(n, ""),
        "fonte": "anulada_unicamp" if corr == "X" else "unicamp_oficial", "fonte_url": URL,
    })
doc = {"vestibular": "unicamp", "ano": int(ANO),
       "titulo": f"UNICAMP {ANO} - 1ª fase (Conhecimentos Gerais)",
       "totalQuestoes": len(questoes),
       "observacao": f"Prova completa da 1ª fase da UNICAMP {ANO}. Anuladas: {anuladas if anuladas else 'nenhuma'}.",
       "questoes": questoes}
json.dump(doc, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("escrito:", OUT, "| questoes:", len(questoes), "| gabarito:", len(gab), "| anuladas:", anuladas)
print("alt!=4 (nao anulada):", [(q["numero"], len(q["alternativas"])) for q in questoes if q["correta"] != "X" and len(q["alternativas"]) != 4])
print("sem gabarito:", [n for n in range(1, 73) if n not in gab])
