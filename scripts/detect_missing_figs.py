# -*- coding: utf-8 -*-
"""Detecta questoes com FIGURA VETORIAL (grafico/mapa/diagrama desenhado com
linhas, que get_images() nao captura) e n_figs==0 no extract -> candidatas a
renderizar como imagem. Uso: python detect_missing_figs.py <banca> <ANO> <mode>"""
import fitz, re, os, json, sys
BANCA, ANO, MODE = sys.argv[1], sys.argv[2], sys.argv[3]
HERE = os.path.dirname(__file__)
PDF = os.path.join(HERE, "..", ".provas", f"{BANCA}_{ANO}_f1.pdf")
EXP = json.load(open(os.path.join(HERE, f"_{BANCA}_extract_{ANO}.json"), encoding="utf-8"))
nfigs = {q["numero"]: q["n_figs"] for q in EXP}
d = fitz.open(PDF)
SINGLECOL = (BANCA == "unicamp")
MIDX = 99999.0 if SINGLECOL else 297.0
if MODE == "brace": NUM = re.compile(r"^\{0*(\d{1,2})\}$")
elif MODE == "questao": NUM = re.compile(r"^QUEST[ÃA]O\s*0*(\d{1,2})\b", re.I)
else: NUM = re.compile(r"^0*(\d{1,2})$")

# markers em ordem de leitura
lines = []
for i in range(d.page_count):
    for b in d[i].get_text("dict")["blocks"]:
        if "lines" not in b: continue
        for ln in b["lines"]:
            t = "".join(s["text"] for s in ln["spans"]).strip()
            e = {"page": i, "band": 0 if ln["bbox"][0] < MIDX else 1, "y0": ln["bbox"][1]}
            m = NUM.match(t)
            if m: e["mark"] = int(m.group(1))
            lines.append(e)
lines.sort(key=lambda e: (e["page"], e["band"], e["y0"]))
marks = []; expected = 1
for e in lines:
    if e.get("mark") == expected:
        marks.append((expected, e["page"], e["band"], e["y0"])); expected += 1
        if expected > 90: break

# desenhos vetoriais por pagina (exclui linhas finas = separadores/regr as)
draws = {i: [] for i in range(d.page_count)}
for i in range(d.page_count):
    for dr in d[i].get_drawings():
        r = dr["rect"]
        if r.width > 16 and r.height > 16 and r.width < 560 and r.height < 780:
            draws[i].append(r)

def region_fig_area(pa, ba, ya, pb, bb, yb):
    """maior cluster de desenho na regiao da questao (mesma pagina+band da marca)."""
    x0, x1 = (26, 570) if SINGLECOL else ((28, MIDX) if ba == 0 else (MIDX, 568))
    y1 = yb if (pb == pa and bb == ba) else 800
    best = 0
    for r in draws.get(pa, []):
        cx = (r.x0 + r.x1) / 2
        if x0 <= cx <= x1 and ya - 2 <= r.y0 <= y1 + 2:
            best = max(best, r.width * r.height)
    return best

cand = []
for idx, (num, pa, ba, ya) in enumerate(marks):
    if nfigs.get(num, 0) > 0: continue
    if idx + 1 < len(marks): _, pb, bb, yb = marks[idx + 1]
    else: pb, bb, yb = pa, ba, 800
    area = region_fig_area(pa, ba, ya, pb, bb, yb)
    if area > 6000:   # cluster vetorial substancial (~ >77x77pt)
        cand.append((num, round(area)))
cand.sort()
print(f"{BANCA} {ANO} | candidatas (figura vetorial, n_figs=0):", [c[0] for c in cand])
print("detalhe area:", cand)
