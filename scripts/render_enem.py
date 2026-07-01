# -*- coding: utf-8 -*-
"""Render de questoes ENEM como IMAGEM (2 colunas, multi-regiao). D2 renumera
(marcador N+90 -> numero N). Uso: python render_enem.py <ANO> <DIA> <n1,n2,...>
n = numero do JSON (1-90)."""
import fitz, re, os, json, sys
from PIL import Image
ANO = sys.argv[1]; DIA = int(sys.argv[2])
ALVOS = set(int(x) for x in sys.argv[3].split(",")) if len(sys.argv) > 3 else set()
HERE = os.path.dirname(__file__)
PDF = os.path.join(HERE, "..", ".provas", f"enem_{ANO}_d{DIA}.pdf")
IMGDIR = os.path.join(HERE, "..", "enem", ANO, "img")
JSONP = os.path.join(HERE, "..", "enem", ANO, f"dia{DIA}.json")
ZOOM = 3.0; MIDX = 284.0; COL_TOP = 44.0; COL_BOT = 760.0
OFF = 0 if DIA == 1 else 90
d = fitz.open(PDF)
NUM = re.compile(r"(?i)^QUEST[ÃA]O\s+0*(\d{1,3})\b")

lines = []
for i in range(d.page_count):
    for b in d[i].get_text("dict")["blocks"]:
        if "lines" not in b: continue
        for ln in b["lines"]:
            t = "".join(s["text"] for s in ln["spans"])
            if t.strip():
                e = {"page": i, "band": 0 if ln["bbox"][0] < MIDX else 1, "y0": ln["bbox"][1]}
                m = NUM.match(t.strip())
                if m: e["mark"] = int(m.group(1))
                lines.append(e)
lines.sort(key=lambda e: (e["page"], e["band"], e["y0"]))
# marcadores por numero (1a ocorrencia)
marks = {}
for e in lines:
    n = e.get("mark")
    if n and OFF + 1 <= n <= OFF + 90 and n not in marks:
        marks[n] = (e["page"], e["band"], e["y0"])

def band_x(bd):
    pw = d[0].rect.width
    return (24, MIDX - 3) if bd == 0 else (MIDX + 3, pw - 24)

def render_q(numj):
    pm = numj + OFF
    if pm not in marks: return None
    pa, ba, ya = marks[pm]
    nxt = marks.get(pm + 1)
    if nxt: pb, bb, yb = nxt
    else: pb, bb, yb = pa, ba, COL_BOT
    sl = []; p, bd = pa, ba
    while (p, bd) <= (pb, bb):
        sl.append((p, bd)); bd, p = (1, p) if bd == 0 else (0, p + 1)
        if p > pb + 1: break
    pieces = []
    for k, (p, bd) in enumerate(sl):
        x0, x1 = band_x(bd)
        yt = ya - 2 if k == 0 else COL_TOP
        yb2 = (yb - 2) if (p == pb and bd == bb) else COL_BOT
        if yb2 - yt < 8: continue
        pix = d[p].get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), clip=fitz.Rect(x0, yt, x1, yb2))
        pieces.append(Image.frombytes("RGB", [pix.width, pix.height], pix.samples))
    if not pieces: return None
    W = max(im.width for im in pieces); H = sum(im.height for im in pieces) + 12 * (len(pieces) - 1)
    canvas = Image.new("RGB", (W, H), "white"); y = 0
    for im in pieces: canvas.paste(im, (0, y)); y += im.height + 12
    fn = f"{ANO}_d{DIA}_q{numj:02d}_full.png"; canvas.save(os.path.join(IMGDIR, fn))
    return f"enem/{ANO}/img/{fn}", len(pieces)

doc = json.load(open(JSONP, encoding="utf-8")); done = {}
for numj in sorted(ALVOS):
    r = render_q(numj)
    if r: done[numj] = r[0]; print(f"Q{numj}: {r[1]} regiao(oes) -> {r[0]}")
    else: print(f"Q{numj}: FALHOU")
for q in doc["questoes"]:
    if q["numero"] in done:
        q["enunciado"] = f"![]({done[q['numero']]})"
        q["alternativas"] = [f"{L})" for L in "ABCDE"]
        q["imagens_alternativas"] = [None]*5
json.dump(doc, open(JSONP, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("atualizadas:", sorted(done.keys()))
