# -*- coding: utf-8 -*-
"""Extrai FUVEST F1 (90 q, 5 alternativas (A)-(E)) -> intermediario JSON.
Uso: python fuvest_extract.py <ANO>. Marcador = numero isolado 01..90 (deteccao
sequencial). Texto via reading order; figuras coluna-aware renderizadas inline."""
import fitz, re, os, json, sys
ANO = sys.argv[1] if len(sys.argv) > 1 else "2022"
HERE = os.path.dirname(__file__)
PDF = os.path.join(HERE, "..", ".provas", f"fuvest_{ANO}_f1.pdf")
IMGDIR = os.path.join(HERE, "..", "vestibular", "fuvest", "img")
os.makedirs(IMGDIR, exist_ok=True)
ZOOM = 2.0; MIDX = 297.0
d = fitz.open(PDF)
NUMLINE = re.compile(r"^\s*0*(\d{1,2})\s*$")

# 1) coletar TODOS os elementos (linhas de texto + imagens) com posicao
elems = []
for i in range(d.page_count):
    pg = d[i]
    for b in pg.get_text("dict")["blocks"]:
        if "lines" not in b: continue
        for ln in b["lines"]:
            t = "".join(s["text"] for s in ln["spans"])
            if t.strip():
                elems.append({"page": i, "band": 0 if ln["bbox"][0] < MIDX else 1,
                              "y": ln["bbox"][1], "x": ln["bbox"][0], "kind": "txt", "text": t})
    seen = set()
    for img in pg.get_images(full=True):
        for r in pg.get_image_rects(img[0]):
            if r.width < 45 or r.height < 45: continue
            k = (round(r.x0), round(r.y0))
            if k in seen: continue
            seen.add(k)
            elems.append({"page": i, "band": 0 if r.x0 < MIDX else 1, "y": r.y0,
                          "kind": "img", "rect": [r.x0, r.y0, r.x1, r.y1]})
elems.sort(key=lambda e: (e["page"], e["band"], e["y"]))

# 2) detectar marcadores sequenciais 1..90
markers = {}  # num -> index em elems
expected = 1
for idx, e in enumerate(elems):
    if e["kind"] != "txt": continue
    m = NUMLINE.match(e["text"])
    if m and int(m.group(1)) == expected:
        markers[expected] = idx
        expected += 1
        if expected > 90: break
print("ANO", ANO, "| markers sequenciais detectados:", len(markers), "| ultimo:", max(markers) if markers else 0)
faltando = [n for n in range(1,91) if n not in markers]
print("faltando:", faltando)

# 3) agrupar elems por questao e montar
def render_fig(num, i, page, rect):
    r = fitz.Rect(rect) + (-3,-3,3,3)
    pix = d[page].get_pixmap(matrix=fitz.Matrix(ZOOM,ZOOM), clip=r)
    fn = f"{ANO}_q{num:02d}_fig{i}.png"
    pix.save(os.path.join(IMGDIR, fn))
    return f"vestibular/fuvest/img/{fn}"

idxs = sorted(markers.items())  # (num, idx)
saida = []
for j,(num,idx) in enumerate(idxs):
    end = idxs[j+1][1] if j+1 < len(idxs) else len(elems)
    bloco = elems[idx+1:end]  # tudo entre este marcador e o proximo
    textbuf = []; figc = 0
    for e in bloco:
        if e["kind"] == "img":
            figc += 1
            textbuf.append(f"![]({render_fig(num,figc,e['page'],e['rect'])})")
        else:
            textbuf.append(e["text"])
    full = "\n".join(textbuf)
    # separa alternativas (A)..(E)
    mA = re.search(r"\(A\)", full)
    if mA:
        enun = full[:mA.start()].strip()
        resto = full[mA.start():]
        alts = {}
        for L in "ABCDE":
            nxt = chr(ord(L)+1)
            pat = rf"\({L}\)(.*?)(?=\({nxt}\)|$)" if L!="E" else r"\(E\)(.*)$"
            mm = re.search(pat, resto, re.S)
            if mm: alts[L] = re.sub(r"\s+"," ", mm.group(1)).strip()
        alternativas = [f"{L}) {alts[L]}" for L in "ABCDE" if L in alts]
    else:
        enun = full.strip(); alternativas = []
    # remove figuras do meio do enunciado? nao: mantem inline. limpa numero de pagina solto
    enun = re.sub(r"\n\s*\d{1,3}\s*\n", "\n", enun)
    enun = re.sub(r"Concurso Vestibular FUVEST.*?\n", "", enun)
    enun = re.sub(r"\n{3,}", "\n\n", enun).strip()
    saida.append({"numero": num, "enunciado": enun, "alternativas": alternativas,
                  "n_alts": len(alternativas), "n_figs": figc})

out = os.path.join(HERE, f"_fuvest_extract_{ANO}.json")
json.dump(saida, open(out,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("questoes:", len(saida), "| != 5 alts:", [(q["numero"],q["n_alts"]) for q in saida if q["n_alts"]!=5][:30])
print("total figuras:", sum(q["n_figs"] for q in saida), "| salvo ->", out)
