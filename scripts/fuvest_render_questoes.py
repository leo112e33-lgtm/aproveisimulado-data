# -*- coding: utf-8 -*-
"""Renderiza questoes especificas da FUVEST como IMAGEM (questoes com formula/
glifo ambiguo ou alternativas-grafico). Reusa deteccao de marcador {NN} ou NN.
Uso: python fuvest_render_questoes.py <ANO> <brace|bare> <n1,n2,...>
Atualiza vestibular/fuvest/<ANO>.json: enunciado=![](img full), alternativas=letras."""
import fitz, re, os, json, sys
ANO = sys.argv[1]
MODE = sys.argv[2] if len(sys.argv) > 2 else "brace"
ALVOS = set(int(x) for x in sys.argv[3].split(",")) if len(sys.argv) > 3 else set()
HERE = os.path.dirname(__file__)
PDF = os.path.join(HERE, "..", ".provas", f"fuvest_{ANO}_f1.pdf")
IMGDIR = os.path.join(HERE, "..", "vestibular", "fuvest", "img")
JSONP = os.path.join(HERE, "..", "vestibular", "fuvest", f"{ANO}.json")
ZOOM = 3.0; MIDX = 297.0
d = fitz.open(PDF)
NUM = re.compile(r"^\s*\{0*(\d{1,2})\}\s*$") if MODE == "brace" else re.compile(r"^\s*0*(\d{1,2})\s*$")

# coletar linhas com posicao (coluna-aware)
lines = []
for i in range(d.page_count):
    pw = d[i].rect.width
    for b in d[i].get_text("dict")["blocks"]:
        if "lines" not in b: continue
        for ln in b["lines"]:
            t = "".join(s["text"] for s in ln["spans"])
            if t.strip():
                lines.append({"page": i, "band": 0 if ln["bbox"][0] < MIDX else 1,
                              "y0": ln["bbox"][1], "y1": ln["bbox"][3], "x0": ln["bbox"][0], "text": t})
lines.sort(key=lambda e: (e["page"], e["band"], e["y0"]))

# marcadores sequenciais
marks = []  # (num, idx)
expected = 1
for idx, e in enumerate(lines):
    m = NUM.match(e["text"])
    if m and int(m.group(1)) == expected:
        marks.append((expected, idx)); expected += 1
        if expected > 90: break

PADX = 6
results = {}
for j, (num, idx) in enumerate(marks):
    if num not in ALVOS: continue
    e = lines[idx]
    page, band = e["page"], e["band"]
    pw = d[page].rect.width; ph = d[page].rect.height
    x0 = 30 if band == 0 else MIDX + 2
    x1 = MIDX - 2 if band == 0 else pw - 30
    y0 = e["y0"] - 2
    # fim = proximo marcador na MESMA pagina+band, senao fundo da coluna
    y1 = ph - 40
    if j + 1 < len(marks):
        ne = lines[marks[j+1][1]]
        if ne["page"] == page and ne["band"] == band and ne["y0"] > y0:
            y1 = ne["y0"] - 2
    rect = fitz.Rect(x0 - PADX, y0, x1 + PADX, y1)
    pix = d[page].get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), clip=rect)
    fn = f"{ANO}_q{num:02d}_full.png"
    pix.save(os.path.join(IMGDIR, fn))
    results[num] = (f"vestibular/fuvest/img/{fn}", round(rect.height))
    print(f"Q{num}: pagina {page} band {band} -> {fn} (h={round(rect.height)})")

# atualizar JSON
doc = json.load(open(JSONP, encoding="utf-8"))
for q in doc["questoes"]:
    n = q["numero"]
    if n in results:
        path, h = results[n]
        q["enunciado"] = f"![]({path})"
        q["alternativas"] = [f"{L})" for L in "ABCDE"]
        q["imagens_alternativas"] = [None]*5
json.dump(doc, open(JSONP, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("atualizadas:", sorted(results.keys()))
