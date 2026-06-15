# -*- coding: utf-8 -*-
"""Para provas FUVEST com PDF de fonte ilegivel (texto nao extrai), renderiza
cada questao como IMAGEM (2 colunas, coluna-aware). Uso: python fuvest_render_images.py <ANO>
Gera _fuvest_extract_<ANO>.json com enunciado=![](img) e alternativas=[A..E]."""
import fitz, re, os, json, sys
ANO = sys.argv[1] if len(sys.argv) > 1 else "2021"
HERE = os.path.dirname(__file__)
PDF = os.path.join(HERE, "..", ".provas", f"fuvest_{ANO}_f1.pdf")
IMGDIR = os.path.join(HERE, "..", "vestibular", "fuvest", "img")
os.makedirs(IMGDIR, exist_ok=True)
ZOOM = 2.0; MIDX = 297.0
d = fitz.open(PDF)

# 1) candidatos a marcador: linha = numero isolado 1..90
cand = []
for i in range(d.page_count):
    for b in d[i].get_text("dict")["blocks"]:
        if "lines" not in b: continue
        for ln in b["lines"]:
            # marcador de questao: fonte SegoeUIBlack (size ~13), numero 2 digitos
            if not ln["spans"]: continue
            fonts = "".join(s["font"] for s in ln["spans"])
            if "SegoeUIBlack" not in fonts and "Black" not in fonts: continue
            t = "".join(s["text"] for s in ln["spans"]).strip()
            if re.fullmatch(r"\d{2}", t) and 1 <= int(t) <= 90:
                cand.append({"num": int(t), "page": i, "band": 0 if ln["bbox"][0] < MIDX else 1,
                             "y": ln["bbox"][1], "x": ln["bbox"][0]})
# 2) o filtro de fonte (SegoeUIBlack) ja e preciso: 1 candidato por questao.
# dedupe por num e ordena por leitura (page, band, y) para limitar regioes.
by_num = {}
for c in sorted(cand, key=lambda e: (e["page"], e["band"], e["y"])):
    by_num.setdefault(c["num"], c)
markers = sorted(by_num.values(), key=lambda e: (e["page"], e["band"], e["y"]))
print("ANO", ANO, "| markers:", len(markers), "| faltando:", [n for n in range(1,91) if n not in by_num])

# 3) renderiza cada questao (regiao coluna-aware do marcador ao proximo)
def render(idx):
    mk = markers[idx]
    nxt = markers[idx+1] if idx+1 < len(markers) else None
    page, band = mk["page"], mk["band"]
    x0, x1 = (26, 294) if band == 0 else (300, 569)
    ytop = mk["y"] - 2
    if nxt and nxt["page"] == page and nxt["band"] == band:
        ybot = nxt["y"] - 2
    else:
        ybot = 838
    pix = d[page].get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), clip=fitz.Rect(x0, ytop, x1, ybot))
    fn = f"{ANO}_q{mk['num']:02d}.png"
    pix.save(os.path.join(IMGDIR, fn))
    return f"vestibular/fuvest/img/{fn}"

saida = []
for idx, mk in enumerate(markers):
    p = render(idx)
    saida.append({"numero": mk["num"], "enunciado": f"![]({p})",
                  "alternativas": ["A","B","C","D","E"], "n_alts": 5, "n_figs": 1, "img_only": True})
out = os.path.join(HERE, f"_fuvest_extract_{ANO}.json")
json.dump(saida, open(out,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("questoes renderizadas:", len(saida), "| salvo ->", out)
