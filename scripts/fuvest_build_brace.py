# -*- coding: utf-8 -*-
"""Monta vestibular/fuvest/<ANO>.json a partir de _fuvest_extract_<ANO>.json +
_fuvest_gab_<ANO>.json (+ explicacoes _f<ANO>expl_*.json se existirem).
Normaliza quebras de linha artificiais. Uso: python fuvest_build_brace.py <ANO> <PROVA_URL>"""
import json, os, glob, re, sys, unicodedata
ANO = sys.argv[1] if len(sys.argv) > 1 else "2025"
PROVA_URL = sys.argv[2] if len(sys.argv) > 2 else ""
HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "..", "vestibular", "fuvest", f"{ANO}.json")
extract = {q["numero"]: q for q in json.load(open(os.path.join(HERE, f"_fuvest_extract_{ANO}.json"), encoding="utf-8"))}
gab = json.load(open(os.path.join(HERE, f"_fuvest_gab_{ANO}.json"), encoding="utf-8"))
expl = {}
for fp in sorted(glob.glob(os.path.join(HERE, f"_f{ANO}expl_*.json"))):
    for k, v in json.load(open(fp, encoding="utf-8")).items():
        expl[int(k)] = v

def norm_text(s):
    """Junta quebras de linha dentro do paragrafo; preserva linhas de imagem e
    paragrafos (linha em branco). Aplica NFKC."""
    s = unicodedata.normalize("NFKC", s)
    linhas = s.split("\n")
    out = []
    buf = []
    def flush():
        if buf:
            out.append(re.sub(r"\s+", " ", " ".join(buf)).strip())
            buf.clear()
    for ln in linhas:
        t = ln.strip()
        if t.startswith("![]("):          # imagem em linha propria
            flush(); out.append(t)
        elif t == "":                      # quebra de paragrafo
            flush(); out.append("")
        else:
            buf.append(t)
    flush()
    res = "\n".join(out)
    res = re.sub(r"\n{3,}", "\n\n", res).strip()
    return res

questoes = []; anuladas = []
for n in range(1, 91):
    if n not in extract: continue
    q = extract[n]
    corr = gab.get(str(n), "X").upper()
    if corr in ("ANULADA", "X", "*", "-"):
        corr = "X"; anuladas.append(n); explic = ""; fonte = "anulada_fuvest"
    else:
        explic = expl.get(n, {}).get("explicacao", "") if isinstance(expl.get(n), dict) else expl.get(n, "")
        fonte = "fuvest_oficial"
    alts = [re.sub(r"\s+", " ", a).strip() for a in q["alternativas"]]
    questoes.append({
        "numero": n, "ano": int(ANO), "titulo": f"Questão {n} - FUVEST {ANO}",
        "enunciado": norm_text(q["enunciado"]), "alternativas_introducao": "",
        "alternativas": alts, "imagens_alternativas": [None]*5,
        "imagem_principal": "", "imagens_extras": [],
        "correta": corr, "explicacao": explic or "",
        "fonte": fonte, "fonte_url": PROVA_URL,
    })

doc = {"vestibular": "FUVEST", "ano": int(ANO),
       "titulo": f"FUVEST {ANO} — 1ª fase (prova completa, Prova V1)",
       "totalQuestoes": len(questoes),
       "observacao": f"Prova completa da 1ª fase da FUVEST {ANO} (Prova V1): texto do PDF oficial + figuras recortadas. Gabarito oficial da Prova V1. Anuladas: {anuladas if anuladas else 'nenhuma'}.",
       "questoes": questoes}
json.dump(doc, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("escrito:", OUT, "| questoes:", len(questoes), "| anuladas:", anuladas)
print("alt!=5:", [(q["numero"], len(q["alternativas"])) for q in questoes if len(q["alternativas"]) != 5])
print("sem explicacao (nao anuladas):", len([q for q in questoes if q["correta"] != "X" and not q["explicacao"].strip()]))
