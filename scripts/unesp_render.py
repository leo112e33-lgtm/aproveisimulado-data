# -*- coding: utf-8 -*-
import fitz, re, os, json
from collections import defaultdict
PDF = r"C:\Users\leo11\.claude\projects\C--Users-leo11\6da471ab-3033-4493-87bd-4350fd5e829b\tool-results\webfetch-1781392739634-9mu28i.pdf"
IMG = r"C:\Users\leo11\AndroidStudioProjects\aproveisimulado-data\vestibular\unesp\img"
os.makedirs(IMG, exist_ok=True)
d = fitz.open(PDF)

MARK = re.compile(r"^\s*QUEST[ÃA]O\s*0*(\d{1,2})\b", re.I)
BASE = re.compile(r"(?i)(para responder|leia o|leia a|considere o|considere a|com base no texto|analise o texto).{0,90}?quest(?:ões|ao|ão)\s*(?:de\s*)?0*(\d{1,2})\s*(?:a|à|até)\s*0*(\d{1,2})")
BASE1 = re.compile(r"(?i)(para responder|leia o|leia a|considere o|considere a).{0,90}?quest(?:ão|ao)\s*0*(\d{1,2})\b(?!\s*(?:a|à|até))")

marks = {}          # num -> {num,page,col,y}
base_groups = []    # (ini, fim, page, col, y)
for pi in range(d.page_count):
    pg = d[pi]; W = pg.rect.width; mid = W/2
    for blk in pg.get_text("dict").get("blocks", []):
        for ln in blk.get("lines", []):
            spans = ln.get("spans", [])
            if not spans: continue
            texto = "".join(s["text"] for s in spans).strip()
            bbox = ln["bbox"]; col = 0 if bbox[0] < mid else 1
            m = MARK.match(texto)
            if m and 1 <= int(m.group(1)) <= 90:
                marks[int(m.group(1))] = {"num": int(m.group(1)), "page": pi, "col": col, "y": bbox[1]}
                continue
            b = BASE.search(texto)
            if b:
                base_groups.append((int(b.group(2)), int(b.group(3)), pi, col, bbox[1])); continue
            b1 = BASE1.search(texto)
            if b1:
                n = int(b1.group(2)); base_groups.append((n, n, pi, col, bbox[1]))

# cut points por (page,col): markers + inicios de base
cuts = defaultdict(list)
for mk in marks.values():
    cuts[(mk["page"], mk["col"])].append(mk["y"])
for (ini, fim, pi, col, y) in base_groups:
    cuts[(pi, col)].append(y)
for k in cuts: cuts[k] = sorted(cuts[k])

W = d[0].rect.width; H = d[0].rect.height; mid = W/2
COL0 = (26, mid-3); COL1 = (mid+3, W-22)
TOP_MARGIN = 38; BOT_MARGIN = H-26

def render(page, col, y_top, y_bot, nome):
    pg = d[page]; x = COL0 if col == 0 else COL1
    rect = fitz.Rect(x[0], max(y_top, TOP_MARGIN), x[1], min(y_bot, BOT_MARGIN))
    if rect.height < 8: return False
    pg.get_pixmap(clip=rect, matrix=fitz.Matrix(2, 2)).save(os.path.join(IMG, nome))
    return True

def prox_cut(page, col, y):
    nx = [c for c in cuts[(page, col)] if c > y + 5]
    return min(nx) if nx else BOT_MARGIN

# questoes
for mk in marks.values():
    render(mk["page"], mk["col"], mk["y"]-6, prox_cut(mk["page"], mk["col"], mk["y"]), f"2023_q{mk['num']:02d}.png")

# bases
base_img = {}
for (ini, fim, pi, col, y) in base_groups:
    if ini not in marks: continue
    nome = f"2023_base_{ini}_{fim}.png"
    yb = prox_cut(pi, col, y)
    if render(pi, col, y-4, yb, nome):
        for q in range(ini, fim+1):
            base_img[q] = nome

json.dump({"base_img": {str(k): v for k, v in base_img.items()}},
          open(os.path.join(IMG, "_meta.json"), "w"))
print("questoes:", len(marks), "| grupos base:", sorted(set((b[0], b[1]) for b in base_groups)))
print("base_img p/ questoes:", sorted(base_img.keys()))
