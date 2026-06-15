# -*- coding: utf-8 -*-
"""Detecta e insere figuras (raster OU VETOR) perdidas: para questoes SEM imagem
no enunciado, acha lacunas verticais grandes entre linhas de texto que contem
desenhos/rasters (= figura) e renderiza essa faixa, inserindo ![]() no enunciado.
Auto-filtra falsos positivos (questoes so-texto nao tem lacuna-figura).
Uso: python fix_missing_figs.py <prova> <ano> [--apply]"""
import fitz, re, os, sys, json
PROVA, ANO = sys.argv[1], sys.argv[2]
APPLY = "--apply" in sys.argv
HERE = os.path.dirname(__file__)
PDF = os.path.join(HERE, "..", ".provas", f"{PROVA}_{ANO}_f1.pdf")
IMGDIR = os.path.join(HERE, "..", "vestibular", PROVA, "img")
JSONP = os.path.join(HERE, "..", "vestibular", PROVA, f"{ANO}.json")
ZOOM = 2.0; MIDX = 297.0
d = fitz.open(PDF)

# markers
marks = []; useq = False
for i in range(d.page_count):
    for b in d[i].get_text("dict")["blocks"]:
        if "lines" not in b: continue
        for ln in b["lines"]:
            t = "".join(s["text"] for s in ln["spans"]).strip()
            m = re.match(r"QUEST[ÃA]O\s+0*(\d{1,2})\b", t)
            if m:
                useq = True
                marks.append({"num": int(m.group(1)), "page": i, "band": 0 if ln["bbox"][0] < MIDX else 1, "y": ln["bbox"][1], "y1": ln["bbox"][3]})
if not useq:
    for i in range(d.page_count):
        for b in d[i].get_text("dict")["blocks"]:
            if "lines" not in b: continue
            for ln in b["lines"]:
                t = "".join(s["text"] for s in ln["spans"]).strip()
                if re.fullmatch(r"\d{2}", t) and 1 <= int(t) <= 90:
                    marks.append({"num": int(t), "page": i, "band": 0 if ln["bbox"][0] < MIDX else 1, "y": ln["bbox"][1], "y1": ln["bbox"][3]})
by = {}
for c in sorted(marks, key=lambda e:(e["page"],e["band"],e["y"])):
    by.setdefault(c["num"], c)
order = sorted(by.values(), key=lambda e:(e["page"],e["band"],e["y"]))

doc = json.load(open(JSONP, encoding="utf-8"))
jq = {q["numero"]: q for q in doc["questoes"]}

def region(num):
    mk = by[num]; i = order.index(mk); nxt = order[i+1] if i+1 < len(order) else None
    page, band = mk["page"], mk["band"]
    x0, x1 = (24, 300) if band == 0 else (296, 575)
    ytop, ybot = mk["y1"], (nxt["y"] if (nxt and nxt["page"]==page and nxt["band"]==band) else 820)
    return page, band, x0, x1, ytop, ybot

def figuras_em(num):
    """retorna lista de (y0,y1) das faixas-figura na regiao da questao."""
    if num not in by: return []
    page, band, x0, x1, ytop, ybot = region(num)
    pg = d[page]
    clip = fitz.Rect(x0, ytop, x1, ybot)
    # linhas de texto na regiao
    tls = []
    for b in pg.get_text("dict")["blocks"]:
        if "lines" not in b: continue
        for ln in b["lines"]:
            r = fitz.Rect(ln["bbox"])
            if r.y0 >= ytop-2 and r.y1 <= ybot+2 and r.x0 >= x0-5 and r.x1 <= x1+30 and "".join(s["text"] for s in ln["spans"]).strip():
                tls.append((r.y0, r.y1))
    tls.sort()
    # desenhos e rasters na regiao (descarta linhas finas: altura<6 e largura<6)
    elems = []
    for dr in pg.get_drawings():
        r = fitz.Rect(dr["rect"])
        if r.y0 >= ytop and r.y1 <= ybot and r.x0 >= x0-5 and r.x1 <= x1+30:
            if r.height > 4 or r.width > 20:
                elems.append((r.y0, r.y1))
    for img in pg.get_images(full=True):
        for r in pg.get_image_rects(img[0]):
            if r.y0 >= ytop and r.y1 <= ybot and r.x0 >= x0-5: elems.append((r.y0, r.y1))
    if not elems: return []
    # construir gaps entre linhas de texto
    bounds = [ytop] + [y for t in tls for y in t] + [ybot]
    gaps = []
    prev = ytop
    pts = sorted([ytop, ybot] + [y for t in tls for y in (t[0],t[1])])
    # gaps = intervalos entre fim de uma linha e inicio da proxima
    seq = [ytop]
    for a,b2 in tls:
        seq.append(a); seq.append(b2)
    seq.append(ybot)
    gbands = []
    # intervalos sem texto: (fim linha i, inicio linha i+1)
    edges = [ytop] + [v for t in tls for v in t] + [ybot]
    i = 0
    pts2 = [ytop]
    for a,b2 in tls: pts2 += [a,b2]
    pts2 += [ybot]
    # caminhar
    cursor = ytop
    for a,b2 in tls:
        if a - cursor > 38:  # lacuna grande antes desta linha
            gbands.append((cursor, a))
        cursor = max(cursor, b2)
    if ybot - cursor > 38:
        gbands.append((cursor, ybot))
    # uma faixa eh figura se contem desenho/raster
    figs = []
    for g0,g1 in gbands:
        if any(not(e1 <= g0 or e0 >= g1) for e0,e1 in elems):
            figs.append((g0-2, g1+2))
    return figs

cands = [q["numero"] for q in doc["questoes"] if q.get("correta")!="X" and "![" not in q["enunciado"]
         and not all(re.fullmatch(r"[A-E]",a.strip()) for a in q["alternativas"])]
achados = {}
for num in cands:
    figs = figuras_em(num)
    if figs: achados[num] = figs
print(PROVA, ANO, "| questoes sem-img com figura-gap detectada:", sorted(achados))
if APPLY:
    for num, figs in achados.items():
        page, band, x0, x1, ytop, ybot = region(num)
        marks_img = []
        for idx,(g0,g1) in enumerate(figs,1):
            pix = d[page].get_pixmap(matrix=fitz.Matrix(ZOOM,ZOOM), clip=fitz.Rect(x0,g0,x1,g1))
            fn = f"{ANO}_q{num:02d}_vfig{idx}.png"; pix.save(os.path.join(IMGDIR,fn))
            marks_img.append(f"![](vestibular/{PROVA}/img/{fn})")
        jq[num]["enunciado"] = jq[num]["enunciado"].strip() + "\n\n" + "\n".join(marks_img)
    json.dump(doc, open(JSONP,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    print("  aplicado em", sorted(achados))
