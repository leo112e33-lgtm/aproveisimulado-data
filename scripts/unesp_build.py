# -*- coding: utf-8 -*-
"""Monta vestibular/unesp/<ANO>.json de _unesp_extract_<ANO>.json + gabarito
(.gabaritos/unesp_<ANO>.pdf, VERSAO 1) + explicacoes _unesp<ANO>expl_*.json.
Uso: python unesp_build.py <ANO> <PROVA_URL>"""
import json, os, glob, re, sys, unicodedata, pypdf
ANO = sys.argv[1]
URL = sys.argv[2] if len(sys.argv) > 2 else ""
HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "..", "vestibular", "unesp", f"{ANO}.json")
extract = {q["numero"]: q for q in json.load(open(os.path.join(HERE, f"_unesp_extract_{ANO}.json"), encoding="utf-8"))}
GABPDF = os.path.join(HERE, "..", ".gabaritos", f"unesp_{ANO}.pdf")
gtxt = "\n".join((pg.extract_text() or "") for pg in pypdf.PdfReader(GABPDF).pages)
gab = {}
for n, l in re.findall(r"(\d{1,2})\s*-\s*([A-E])", gtxt):
    n = int(n)
    if 1 <= n <= 90 and n not in gab:
        gab[n] = l
expl = {}
for fp in sorted(glob.glob(os.path.join(HERE, f"_unesp{ANO}expl_*.json"))):
    for k, v in json.load(open(fp, encoding="utf-8")).items():
        expl[int(k)] = v["explicacao"] if isinstance(v, dict) else v

def norm_text(s):
    s = unicodedata.normalize("NFKC", s)
    out, buf = [], []
    def flush():
        if buf:
            out.append(re.sub(r"\s+", " ", " ".join(buf)).strip()); buf.clear()
    for ln in s.split("\n"):
        t = ln.strip()
        if t.startswith("![]("): flush(); out.append(t)
        elif t == "": flush(); out.append("")
        else: buf.append(t)
    flush()
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()

questoes = []
for n in range(1, 91):
    if n not in extract: continue
    q = extract[n]
    corr = gab.get(n, "X")
    alts = [re.sub(r"\s+", " ", a).strip() for a in q["alternativas"]]
    questoes.append({
        "numero": n, "ano": int(ANO), "titulo": f"Questão {n} - UNESP {ANO}",
        "enunciado": norm_text(q["enunciado"]), "alternativas_introducao": "",
        "alternativas": alts, "imagens_alternativas": [None]*5,
        "imagem_principal": "", "imagens_extras": [],
        "correta": corr, "explicacao": expl.get(n, ""),
        "fonte": "unesp_oficial", "fonte_url": URL,
    })
doc = {"vestibular": "UNESP", "ano": int(ANO),
       "titulo": f"UNESP {ANO} — 1ª fase (prova completa, versão 1)",
       "totalQuestoes": len(questoes),
       "observacao": f"Prova completa da 1ª fase da UNESP {ANO} (versão 1): texto do PDF oficial + figuras recortadas. Gabarito oficial da versão 1.",
       "questoes": questoes}
json.dump(doc, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("escrito:", OUT, "| questoes:", len(questoes), "| gabarito:", len(gab))
print("alt!=5:", [(q["numero"], len(q["alternativas"])) for q in questoes if len(q["alternativas"]) != 5])
print("sem gabarito:", [n for n in range(1, 91) if n not in gab])
