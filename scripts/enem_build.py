# -*- coding: utf-8 -*-
"""Monta enem/<ANO>/dia<DIA>.json de _enem_extract_<ANO>_d<DIA>.json + gabarito
INEP (.gabaritos/enem_<ANO>_d<DIA>.pdf). D2: gabarito 91-180 -> numero 1-90.
Uso: python enem_build.py <ANO> <DIA>"""
import json, os, glob, re, sys, unicodedata, pypdf
ANO = sys.argv[1]; DIA = int(sys.argv[2])
HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "..", "enem", ANO, f"dia{DIA}.json")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
extract = {q["numero"]: q for q in json.load(open(os.path.join(HERE, f"_enem_extract_{ANO}_d{DIA}.json"), encoding="utf-8"))}
gtxt = "\n".join((p.extract_text() or "") for p in pypdf.PdfReader(os.path.join(HERE, "..", ".gabaritos", f"enem_{ANO}_d{DIA}.pdf")).pages)
OFF = 0 if DIA == 1 else 90
gab = {}; anuladas = []
for n, l in re.findall(r"\b(\d{1,3})\s+(Anulad[oa]|[A-Ea-e\*Xx])\b", gtxt):
    n = int(n)
    if not (OFF + 1 <= n <= OFF + 90): continue
    nn = n - OFF
    if nn in gab: continue
    if l[0] in "*Xx" or l.startswith("Anulad"): gab[nn] = "X"; anuladas.append(nn)
    else: gab[nn] = l.upper()
expl = {}
for fp in sorted(glob.glob(os.path.join(HERE, f"_enem{ANO}d{DIA}expl_*.json"))):
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
for n in range(1, 91):
    if n not in extract: continue
    q = extract[n]; corr = gab.get(n, "X")
    alts = [re.sub(r"\s+", " ", a).strip() for a in q.get("alternativas", [])]
    questoes.append({
        "ano": int(ANO), "dia": DIA, "numero": n, "titulo": f"Questão {n} - ENEM {ANO}",
        "enunciado": norm_text(q["enunciado"]), "alternativas_introducao": "",
        "alternativas": alts, "imagens_alternativas": [None]*len(alts) if alts else [],
        "imagem_principal": "", "imagens_extras": [],
        "correta": corr, "explicacao": "" if corr == "X" else expl.get(n, ""),
        "fonte": "anulada_inep" if corr == "X" else "inep_oficial",
        "fonte_url": f"https://download.inep.gov.br/enem/provas_e_gabaritos/{ANO}_PV_impresso_D{DIA}_CD{'1' if DIA==1 else '7'}.pdf",
    })
doc = {"ano": int(ANO), "dia": DIA, "total": len(questoes), "geradoEm": "", "questoes": questoes}
json.dump(doc, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"ENEM {ANO} D{DIA}: {len(questoes)} q | gabarito {len(gab)} | anuladas {anuladas}")
print(" alt!=5 (nao anulada):", [q["numero"] for q in questoes if q["correta"] != "X" and len(q["alternativas"]) != 5])
print(" sem gabarito:", [n for n in range(1, 91) if n not in gab])
