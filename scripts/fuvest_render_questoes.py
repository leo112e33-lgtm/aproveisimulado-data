# -*- coding: utf-8 -*-
"""Renderiza questoes FUVEST como IMAGEM, com suporte a questao que ATRAVESSA
coluna/pagina (multi-regiao: empilha as fatias verticalmente). Para questoes de
formula/glifo-ambiguo ou alternativas-grafico.
Uso: python fuvest_render_questoes.py <ANO> <brace|bare> <n1,n2,...>"""
import fitz, re, os, json, sys
from PIL import Image
ANO = sys.argv[1]
MODE = sys.argv[2] if len(sys.argv) > 2 else "brace"
ALVOS = set(int(x) for x in sys.argv[3].split(",")) if len(sys.argv) > 3 else set()
HERE = os.path.dirname(__file__)
PDF = os.path.join(HERE, "..", ".provas", f"fuvest_{ANO}_f1.pdf")
IMGDIR = os.path.join(HERE, "..", "vestibular", "fuvest", "img")
JSONP = os.path.join(HERE, "..", "vestibular", "fuvest", f"{ANO}.json")
ZOOM = 3.0; MIDX = 297.0
COL_TOP = 66.0; COL_BOT = 812.0
d = fitz.open(PDF)
NUM = re.compile(r"^\{0*(\d{1,2})\}$") if MODE == "brace" else re.compile(r"^0*(\d{1,2})$")

lines = []
for i in range(d.page_count):
    for b in d[i].get_text("dict")["blocks"]:
        if "lines" not in b: continue
        for ln in b["lines"]:
            t = "".join(s["text"] for s in ln["spans"])
            if t.strip():
                lines.append({"page": i, "band": 0 if ln["bbox"][0] < MIDX else 1, "y0": ln["bbox"][1]})
            tt = t.strip()
            mm = NUM.match(tt)
            if mm:
                lines[-1]["mark"] = int(mm.group(1))
lines.sort(key=lambda e: (e["page"], e["band"], e["y0"]))

marks = []; expected = 1
for e in lines:
    if e.get("mark") == expected:
        marks.append((expected, e["page"], e["band"], e["y0"])); expected += 1
        if expected > 90: break
mark_by_num = {m[0]: m for m in marks}

def band_x(band):
    pw = d[0].rect.width
    return (30, MIDX - 3) if band == 0 else (MIDX + 3, pw - 30)

def slots_between(a, b):
    """lista de (page,band) em ordem de leitura de a=(p,bd) ate b=(p,bd) inclusive."""
    out = []; p, bd = a
    while (p, bd) <= b:
        out.append((p, bd))
        if bd == 0: bd = 1
        else: bd = 0; p += 1
        if p > b[0] + 1: break
    return out

def render_q(num):
    idx = [i for i, m in enumerate(marks) if m[0] == num][0]
    _, pa, ba, ya = marks[idx]
    if idx + 1 < len(marks):
        _, pb, bb, yb = marks[idx + 1]
    else:
        pb, bb, yb = pa, ba, COL_BOT
    pieces = []
    sl = slots_between((pa, ba), (pb, bb))
    for k, (p, bd) in enumerate(sl):
        x0, x1 = band_x(bd)
        y_top = ya - 2 if k == 0 else COL_TOP
        y_bot = (yb - 2) if (p == pb and bd == bb) else COL_BOT
        if y_bot - y_top < 8: continue
        rect = fitz.Rect(x0, y_top, x1, y_bot)
        pix = d[p].get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), clip=rect)
        pieces.append(Image.frombytes("RGB", [pix.width, pix.height], pix.samples))
    if not pieces: return None
    W = max(im.width for im in pieces)
    GAP = 12
    H = sum(im.height for im in pieces) + GAP * (len(pieces) - 1)
    canvas = Image.new("RGB", (W, H), "white")
    y = 0
    for im in pieces:
        canvas.paste(im, (0, y)); y += im.height + GAP
    fn = f"{ANO}_q{num:02d}_full.png"
    canvas.save(os.path.join(IMGDIR, fn))
    return f"vestibular/fuvest/img/{fn}", len(pieces), H

doc = json.load(open(JSONP, encoding="utf-8"))
done = {}
for num in sorted(ALVOS):
    if num not in mark_by_num:
        print(f"Q{num}: marcador nao encontrado!"); continue
    r = render_q(num)
    if r:
        path, np, h = r
        done[num] = path
        print(f"Q{num}: {np} regiao(oes), altura {h}px -> {path}")
for q in doc["questoes"]:
    if q["numero"] in done:
        q["enunciado"] = f"![]({done[q['numero']]})"
        q["alternativas"] = [f"{L})" for L in "ABCDE"]
        q["imagens_alternativas"] = [None]*5
json.dump(doc, open(JSONP, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("atualizadas:", sorted(done.keys()))
