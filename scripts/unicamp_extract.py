# -*- coding: utf-8 -*-
"""Extrai UNICAMP 2023 F1 -> intermediario JSON.
Texto (enunciado+alternativas) via get_text() em ordem de leitura (confiavel);
figuras associadas por ordem coluna-aware (banda esq/dir em x=297) e renderizadas."""
import fitz, re, os, json

HERE = os.path.dirname(__file__)
PDF = os.path.join(HERE, "..", ".provas", "unicamp_2023_f1.pdf")
IMGDIR = os.path.join(HERE, "..", "vestibular", "unicamp", "img")
os.makedirs(IMGDIR, exist_ok=True)
ZOOM = 2.0
MIDX = 297.0

d = fitz.open(PDF)
MARK = re.compile(r"QUEST[ÃA]O\s+0*(\d{1,2})\b")

# ---------- 1) TEXTO por questao (ordem de leitura) ----------
fulltext = []
for i in range(2, d.page_count):
    fulltext.append(d[i].get_text())
txt = "\n".join(fulltext)
# split mantendo o numero
parts = re.split(r"QUEST[ÃA]O\s+0*(\d{1,2})\b", txt)
# parts[0] = lixo antes da Q1; depois alterna [num, corpo, num, corpo...]
qtext = {}
for k in range(1, len(parts), 2):
    num = int(parts[k]); corpo = parts[k+1]
    qtext[num] = corpo  # se repetir, ultimo vence (nao deve repetir)

def limpa(s):
    linhas = []
    for ln in s.split("\n"):
        t = ln.rstrip()
        if re.fullmatch(r"\s*\d{1,2}\s*", t):  # numero de pagina isolado
            continue
        if t.strip() in ("Q e Z", "RASCUNHO"):
            continue
        linhas.append(t)
    return "\n".join(linhas)

def separa_alts(corpo):
    corpo = limpa(corpo)
    linhas = corpo.split("\n")
    # acha primeira linha "a)" no inicio
    ai = None
    for i, ln in enumerate(linhas):
        if re.match(r"^\s*a\)\s", ln):
            ai = i; break
    if ai is None:
        return corpo.strip(), []
    enun = "\n".join(linhas[:ai]).strip()
    alts = {}
    cur = None
    for ln in linhas[ai:]:
        m = re.match(r"^\s*([a-d])\)\s*(.*)$", ln)
        if m:
            cur = m.group(1); alts[cur] = m.group(2).strip()
        elif cur is not None and ln.strip():
            alts[cur] = (alts[cur] + " " + ln.strip()).strip()
    alternativas = [f"{c.upper()}) {alts[c]}" for c in ["a","b","c","d"] if c in alts]
    return enun, alternativas

# ---------- 2) FIGURAS: ordem coluna-aware p/ associar a questao ----------
elems = []  # {page, band, y, kind, num?/rect?}
for i in range(2, d.page_count):
    pg = d[i]
    for b in pg.get_text("dict")["blocks"]:
        if "lines" not in b: continue
        first = "".join(s["text"] for s in b["lines"][0]["spans"])
        m = MARK.search(first)
        if m:
            x0, y0 = b["bbox"][0], b["bbox"][1]
            elems.append({"page": i, "band": 0 if x0 < MIDX else 1, "y": y0,
                          "kind": "mark", "num": int(m.group(1))})
    seen = set()
    for img in pg.get_images(full=True):
        for r in pg.get_image_rects(img[0]):
            if r.width < 45 or r.height < 45: continue
            key = (round(r.x0), round(r.y0))
            if key in seen: continue
            seen.add(key)
            elems.append({"page": i, "band": 0 if r.x0 < MIDX else 1, "y": r.y0,
                          "kind": "img", "rect": [r.x0, r.y0, r.x1, r.y1]})

elems.sort(key=lambda e: (e["page"], e["band"], e["y"]))
figs_por_q = {}  # num -> [rect_page,...]
atual = None
for e in elems:
    if e["kind"] == "mark":
        atual = e["num"]
    elif atual is not None:
        figs_por_q.setdefault(atual, []).append((e["page"], e["rect"]))

def render_fig(num, idx, page, rect):
    r = fitz.Rect(rect) + (-3, -3, 3, 3)
    pix = d[page].get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), clip=r)
    fn = f"2023_q{num:02d}_fig{idx}.png"
    pix.save(os.path.join(IMGDIR, fn))
    return f"vestibular/unicamp/img/{fn}"

# ---------- 3) Monta saida ----------
saida = []
for num in range(1, 73):
    corpo = qtext.get(num, "")
    enun, alts = separa_alts(corpo)
    figmarks = []
    for idx, (pg, rect) in enumerate(figs_por_q.get(num, []), 1):
        figmarks.append("![](" + render_fig(num, idx, pg, rect) + ")")
    if figmarks:
        enun = (enun + "\n\n" + "\n".join(figmarks)).strip()
    saida.append({"numero": num, "enunciado": enun, "alternativas": alts,
                  "n_alts": len(alts), "n_figs": len(figmarks)})

out = os.path.join(HERE, "_unicamp_extract.json")
json.dump(saida, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
ruins = [(q["numero"], q["n_alts"]) for q in saida if q["n_alts"] != 4]
print("!= 4 alternativas:", ruins)
print("com figuras:", [(q["numero"], q["n_figs"]) for q in saida if q["n_figs"]])
print("total figuras:", sum(q["n_figs"] for q in saida))
print("salvo ->", out)
