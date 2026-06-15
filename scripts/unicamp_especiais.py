# -*- coding: utf-8 -*-
"""Para QUALQUER questao da UNICAMP cujo texto NAO rende 4 alternativas limpas
(alternativas em formula/grafico/multicoluna), renderiza a QUESTAO INTEIRA como
imagem (imagem_principal) e usa alternativas=[A,B,C,D]. Uso: python unicamp_especiais.py <ANO>"""
import fitz, re, os, json, sys
ANO = sys.argv[1] if len(sys.argv) > 1 else "2023"
HERE = os.path.dirname(__file__)
PDF = os.path.join(HERE, "..", ".provas", f"unicamp_{ANO}_f1.pdf")
IMGDIR = os.path.join(HERE, "..", "vestibular", "unicamp", "img")
ZOOM = 2.0; MIDX = 297.0
d = fitz.open(PDF)
MARK = re.compile(r"QUEST[ÃA]O\s+0*(\d{1,2})\b")

extract = {q["numero"]: q for q in json.load(open(os.path.join(HERE,f"_unicamp_extract_{ANO}.json"),encoding="utf-8"))}
bad = [n for n,q in extract.items() if q["n_alts"] != 4]
print("ANO", ANO, "| questoes a renderizar como imagem:", bad)

marks = []
for i in range(d.page_count):
    for b in d[i].get_text("dict")["blocks"]:
        if "lines" not in b: continue
        for ln in b["lines"]:
            t = "".join(s["text"] for s in ln["spans"])
            m = re.match(r"\s*QUEST[ÃA]O\s+0*(\d{1,2})\b", t)
            if m:
                x0, y0 = ln["bbox"][0], ln["bbox"][1]
                marks.append({"num": int(m.group(1)), "page": i, "band": 0 if x0<MIDX else 1, "y": y0})
marks.sort(key=lambda e:(e["page"],e["band"],e["y"]))

def render_full(num):
    idx = next((i for i,m in enumerate(marks) if m["num"]==num), None)
    if idx is None:
        raise RuntimeError(f"marcador Q{num} nao encontrado")
    mk = marks[idx]
    nxt = marks[idx+1] if idx+1 < len(marks) else None
    page, band = mk["page"], mk["band"]
    x0,x1 = (26,296) if band==0 else (300,570)
    ytop = mk["y"]-4
    ybot = nxt["y"]-4 if (nxt and nxt["page"]==page and nxt["band"]==band) else 812
    pix = d[page].get_pixmap(matrix=fitz.Matrix(ZOOM,ZOOM), clip=fitz.Rect(x0,ytop,x1,ybot))
    fn = f"{ANO}_q{num:02d}_full.png"
    pix.save(os.path.join(IMGDIR, fn))
    return f"vestibular/unicamp/img/{fn}"

patch = {}
for num in bad:
    p = render_full(num)
    patch[str(num)] = {"imagem_principal": p, "alternativas": ["A","B","C","D"]}
    print(f"  Q{num} -> {p}")
json.dump(patch, open(os.path.join(HERE,f"_unicamp_especiais_{ANO}.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("patch salvo")
