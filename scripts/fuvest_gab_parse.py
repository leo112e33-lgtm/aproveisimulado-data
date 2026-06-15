# -*- coding: utf-8 -*-
"""Extrai o gabarito da PROVA V do PDF oficial FUVEST (grade 5 versoes), via
coordenadas (coluna V = mais a esquerda). Uso: python fuvest_gab_parse.py <ANO>"""
import fitz, os, sys, json, re
ANO = sys.argv[1] if len(sys.argv) > 1 else "2022"
HERE = os.path.dirname(__file__)
PDF = os.path.join(HERE, "..", ".gabaritos", f"fuvest_{ANO}_f1.pdf")
d = fitz.open(PDF)

# 1) achar x dos headers V,K (para limitar a coluna V)
headers = {}
for i in range(d.page_count):
    for w in d[i].get_text("words"):
        if w[4] in ("V","K","Q","X","Z") and w[1] < 200 and w[4] not in headers:
            headers[w[4]] = w[0]
limite = (headers["V"] + headers["K"]) / 2 if "V" in headers and "K" in headers else 170
print("headers:", {k:round(v) for k,v in headers.items()}, "| limite coluna V:", round(limite))

# 2) coletar words da coluna V (x0 < limite) em todas as paginas
col = []
for i in range(d.page_count):
    for w in d[i].get_text("words"):
        if w[0] < limite and w[1] > 160:  # abaixo dos headers
            col.append((i, round(w[1]), w[0], w[4]))
col.sort(key=lambda t: (t[0], t[1], t[2]))

# 3) agrupar por linha (page,y) e parear (num,ans,num,ans)
from itertools import groupby
gab = {}; anuladas = []
for (pg,y), grp in groupby(col, key=lambda t: (t[0], t[1])):
    toks = [g[3] for g in sorted(grp, key=lambda t: t[2])]
    # toks ~ [numL, ansL, numR, ansR]
    i = 0
    while i < len(toks)-1:
        a, b = toks[i], toks[i+1]
        if re.fullmatch(r"\d{1,2}", a):
            n = int(a)
            if 1 <= n <= 90:
                if b in "ABCDE":
                    gab[n] = b
                elif "*" in b or b == "-":
                    gab[n] = "ANULADA"; anuladas.append(n)
            i += 2
        else:
            i += 1
out = os.path.join(HERE, f"_fuvest_gab_{ANO}.json")
json.dump({str(k):v for k,v in sorted(gab.items())}, open(out,"w",encoding="utf-8"), ensure_ascii=False, indent=0)
print("ANO",ANO,"| respostas:",len(gab),"| faltando:",[n for n in range(1,91) if n not in gab],"| anuladas:",anuladas)
print("salvo ->", out)
print("amostra:", {k:gab[k] for k in list(range(1,6))+list(range(46,51)) if k in gab})
