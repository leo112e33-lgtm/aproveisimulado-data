# -*- coding: utf-8 -*-
"""Render de questoes UNICAMP como IMAGEM. Layout MISTO (paginas 1 ou 2 colunas)
-> deteccao de coluna por pagina + marcadores indexados por numero (nao
sequencial). Uso: python render_unicamp.py <ANO> <n1,n2,...>"""
import fitz, re, os, json, sys
from PIL import Image
ANO = sys.argv[1]
ALVOS = set(int(x) for x in sys.argv[2].split(",")) if len(sys.argv) > 2 else set()
HERE = os.path.dirname(__file__)
PDF = os.path.join(HERE, "..", ".provas", f"unicamp_{ANO}_f1.pdf")
IMGDIR = os.path.join(HERE, "..", "vestibular", "unicamp", "img")
JSONP = os.path.join(HERE, "..", "vestibular", "unicamp", f"{ANO}.json")
ZOOM = 3.0; MIDX = 297.0; COL_TOP = 50.0; COL_BOT = 800.0
d = fitz.open(PDF)
NUM = re.compile(r"^QUEST[ÃA]O\s*0*(\d{1,2})\b", re.I)

# 1) coluna por pagina: 2col se ha linhas confinadas a esq E a dir e poucas cruzam
is2col = {}
for i in range(d.page_count):
    L = R = cross = 0
    for b in d[i].get_text("dict")["blocks"]:
        for ln in b.get("lines", []):
            x0, x1 = ln["bbox"][0], ln["bbox"][2]
            if not "".join(s["text"] for s in ln["spans"]).strip(): continue
            if x1 < MIDX - 5: L += 1
            elif x0 > MIDX + 5: R += 1
            elif x0 < MIDX - 15 and x1 > MIDX + 15: cross += 1
    is2col[i] = (L >= 3 and R >= 3 and cross <= max(2, (L + R) // 8))

def pw(): return d[0].rect.width
def band_of(page, x0):
    return 0 if (not is2col[page] or x0 < MIDX) else 1
def band_x(page, bd):
    if not is2col[page]: return (26, pw() - 26)
    return (26, MIDX - 4) if bd == 0 else (MIDX + 4, pw() - 26)

# 2) marcadores por numero (primeira ocorrencia)
marks = {}
for i in range(d.page_count):
    for b in d[i].get_text("dict")["blocks"]:
        for ln in b.get("lines", []):
            t = "".join(s["text"] for s in ln["spans"]).strip()
            m = NUM.match(t)
            if m:
                n = int(m.group(1))
                if n not in marks: marks[n] = (i, band_of(i, ln["bbox"][0]), ln["bbox"][1])

def reading_key(page, band, y): return (page, band, y)

def render_q(num):
    if num not in marks: return None
    pa, ba, ya = marks[num]
    nxt = marks.get(num + 1)
    if nxt: pb, bb, yb = nxt
    else: pb, bb, yb = pa, ba, COL_BOT
    # slots (page,band) de leitura de (pa,ba) ate (pb,bb)
    sl = []; p, bd = pa, ba
    guard = 0
    while reading_key(p, bd, 0) <= reading_key(pb, bb, 1e9) and guard < 12:
        sl.append((p, bd)); guard += 1
        if not is2col[p]:
            p += 1; bd = 0
        else:
            if bd == 0: bd = 1
            else: bd = 0; p += 1
        if p > pb + 1: break
    pieces = []
    for k, (p, bd) in enumerate(sl):
        x0, x1 = band_x(p, bd)
        yt = ya - 2 if k == 0 else COL_TOP
        yb2 = (yb - 2) if (p == pb and bd == bb) else COL_BOT
        if yb2 - yt < 8: continue
        pix = d[p].get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), clip=fitz.Rect(x0, yt, x1, yb2))
        pieces.append(Image.frombytes("RGB", [pix.width, pix.height], pix.samples))
    if not pieces: return None
    W = max(im.width for im in pieces); H = sum(im.height for im in pieces) + 12 * (len(pieces) - 1)
    canvas = Image.new("RGB", (W, H), "white"); y = 0
    for im in pieces: canvas.paste(im, (0, y)); y += im.height + 12
    fn = f"{ANO}_q{num:02d}_full.png"; canvas.save(os.path.join(IMGDIR, fn))
    return f"vestibular/unicamp/img/{fn}", len(pieces)

doc = json.load(open(JSONP, encoding="utf-8"))
done = {}
for num in sorted(ALVOS):
    r = render_q(num)
    if r: done[num] = r[0]; print(f"Q{num}: {r[1]} regiao(oes) -> {r[0]}")
    else: print(f"Q{num}: FALHOU (marcador {num} em {marks.get(num)})")
for q in doc["questoes"]:
    if q["numero"] in done:
        q["enunciado"] = f"![]({done[q['numero']]})"
        q["alternativas"] = [f"{L})" for L in "ABCD"]
        q["imagens_alternativas"] = [None]*4
json.dump(doc, open(JSONP, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("2col por pagina:", {k: v for k, v in is2col.items() if v})
print("atualizadas:", sorted(done.keys()))
