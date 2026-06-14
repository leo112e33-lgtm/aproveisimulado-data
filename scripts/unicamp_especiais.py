# -*- coding: utf-8 -*-
"""Renderiza imagens das 3 questoes especiais da UNICAMP 2023 (alternativas em
formula/grafico): Q33 e Q51 -> imagem da questao inteira; Q72 -> ja tem 4 figs
(graficos) que viram imagens_alternativas. Gera _unicamp_especiais.json (patch)."""
import fitz, re, os, json
HERE = os.path.dirname(__file__)
PDF = os.path.join(HERE, "..", ".provas", "unicamp_2023_f1.pdf")
IMGDIR = os.path.join(HERE, "..", "vestibular", "unicamp", "img")
ZOOM = 2.0
MIDX = 297.0
d = fitz.open(PDF)
MARK = re.compile(r"QUEST[ÃA]O\s+0*(\d{1,2})\b")

# coleta marcadores com bbox e banda
marks = []
for i in range(2, d.page_count):
    for b in d[i].get_text("dict")["blocks"]:
        if "lines" not in b: continue
        first = "".join(s["text"] for s in b["lines"][0]["spans"])
        m = MARK.search(first)
        if m:
            x0, y0 = b["bbox"][0], b["bbox"][1]
            marks.append({"num": int(m.group(1)), "page": i,
                          "band": 0 if x0 < MIDX else 1, "y": y0})
marks.sort(key=lambda e: (e["page"], e["band"], e["y"]))

def region_after(num):
    """retorna (page, band, ytop) do marcador num e (ynext) do proximo elemento."""
    for idx, mk in enumerate(marks):
        if mk["num"] == num:
            nxt = marks[idx+1] if idx+1 < len(marks) else None
            return mk, nxt
    return None, None

def render_full(num):
    mk, nxt = region_after(num)
    page = mk["page"]; band = mk["band"]
    x0, x1 = (26, 296) if band == 0 else (300, 570)
    ytop = mk["y"] - 2
    if nxt and nxt["page"] == page and nxt["band"] == band:
        ybot = nxt["y"] - 2
    else:
        ybot = 812  # ate quase o fim da coluna
    r = fitz.Rect(x0, ytop, x1, ybot)
    pix = d[page].get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), clip=r)
    fn = f"2023_q{num:02d}_full.png"
    pix.save(os.path.join(IMGDIR, fn))
    return f"vestibular/unicamp/img/{fn}"

patch = {}
for num in (33, 51):
    path = render_full(num)
    patch[str(num)] = {"imagem_principal": path, "alternativas": ["A","B","C","D"],
                       "enunciado_img_only": True}
    print(f"Q{num}: imagem renderizada -> {path}")

# Q72: usa os 4 figs ja gerados como imagens_alternativas
figs72 = [f"vestibular/unicamp/img/2023_q72_fig{i}.png" for i in range(1,5)]
ok = all(os.path.exists(os.path.join(HERE, "..", p)) for p in figs72)
patch["72"] = {"imagens_alternativas": figs72, "alternativas": ["A","B","C","D"],
               "strip_figs_enunciado": True}
print("Q72 figs existem:", ok, figs72)

json.dump(patch, open(os.path.join(HERE, "_unicamp_especiais.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("patch salvo")
