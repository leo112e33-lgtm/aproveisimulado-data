# -*- coding: utf-8 -*-
"""Renderiza questoes como IMAGEM (multi-regiao, empilha fatias que cruzam
coluna/pagina). Generico por banca. Uso:
  python render_vestibular.py <banca> <ANO> <mode> <n1,n2,...>
banca: fuvest|unesp|unicamp   mode: brace({NN}) | bare(NN) | questao(QUESTAO N)
Atualiza vestibular/<banca>/<ANO>.json: enunciado=![](img), alternativas=letras."""
import fitz, re, os, json, sys
from PIL import Image
BANCA = sys.argv[1]; ANO = sys.argv[2]; MODE = sys.argv[3]
ALVOS = set(int(x) for x in sys.argv[4].split(",")) if len(sys.argv) > 4 else set()
HERE = os.path.dirname(__file__)
PDF = os.path.join(HERE, "..", ".provas", f"{BANCA}_{ANO}_f1.pdf")
IMGDIR = os.path.join(HERE, "..", "vestibular", BANCA, "img")
JSONP = os.path.join(HERE, "..", "vestibular", BANCA, f"{ANO}.json")
ZOOM = 3.0; COL_TOP = 56.0; COL_BOT = 800.0
SINGLECOL = (BANCA == "unicamp")
MIDX = 99999.0 if SINGLECOL else 297.0   # coluna unica: tudo vira band 0
d = fitz.open(PDF)
if MODE == "brace":   NUM = re.compile(r"^\{0*(\d{1,2})\}$")
elif MODE == "questao": NUM = re.compile(r"^QUEST[ÃA]O\s*0*(\d{1,2})\b", re.I)
else:                 NUM = re.compile(r"^0*(\d{1,2})$")

BASEKW = re.compile(r"(?i)(para responder|leia (?:o|a|os|as)\b|examine|considere (?:o|a)\b|observe (?:o|a)\b|analise (?:o|a)\b|texto para).{0,90}?quest")
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
                if BASEKW.search(t.strip()): e["base"] = True
                lines.append(e)
lines.sort(key=lambda e: (e["page"], e["band"], e["y0"]))
bases = [(e["page"], e["band"], e["y0"]) for e in lines if e.get("base")]
marks = []; expected = 1
for e in lines:
    if e.get("mark") == expected:
        marks.append((expected, e["page"], e["band"], e["y0"])); expected += 1
        if expected > 90: break
mby = {m[0]: i for i, m in enumerate(marks)}

def band_x(bd):
    pw = d[0].rect.width
    if SINGLECOL: return (26, pw - 26)
    return (28, MIDX - 3) if bd == 0 else (MIDX + 3, pw - 28)

def render_q(num):
    idx = mby[num]; _, pa, ba, ya = marks[idx]
    if idx + 1 < len(marks): _, pb, bb, yb = marks[idx + 1]
    else: pb, bb, yb = pa, ba, COL_BOT
    # se um texto-base de grupo comeca antes do proximo marcador, corta nele
    for (bp, bbd, by) in bases:
        if (pa, ba, ya) < (bp, bbd, by) <= (pb, bb, yb):
            pb, bb, yb = bp, bbd, by; break
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
    fn = f"{ANO}_q{num:02d}_full.png"; canvas.save(os.path.join(IMGDIR, fn))
    return f"vestibular/{BANCA}/img/{fn}", len(pieces)

doc = json.load(open(JSONP, encoding="utf-8"))
done = {}
for num in sorted(ALVOS):
    if num not in mby: print(f"Q{num}: marcador nao encontrado"); continue
    r = render_q(num)
    if r: done[num] = r[0]; print(f"Q{num}: {r[1]} regiao(oes) -> {r[0]}")
LETRAS = "ABCD" if SINGLECOL else "ABCDE"   # UNICAMP: 4 alternativas
for q in doc["questoes"]:
    if q["numero"] in done:
        q["enunciado"] = f"![]({done[q['numero']]})"
        q["alternativas"] = [f"{L})" for L in LETRAS]
        q["imagens_alternativas"] = [None]*len(LETRAS)
json.dump(doc, open(JSONP, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("atualizadas:", sorted(done.keys()))
