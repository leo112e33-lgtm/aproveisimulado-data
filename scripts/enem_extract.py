# -*- coding: utf-8 -*-
"""Extrai ENEM de PDF oficial INEP (caderno azul) -> _enem_extract_<ANO>_d<DIA>.json.
D1: QUESTAO 1-90 (renumera igual). D2: QUESTAO 91-180 -> renumera 1-90.
Q1-5 tem INGLES e ESPANHOL (usa a 1a ocorrencia = ingles). 2 colunas.
Uso: python enem_extract.py <ANO> <DIA>"""
import fitz, re, os, json, sys, unicodedata
ANO = sys.argv[1]; DIA = int(sys.argv[2])
HERE = os.path.dirname(__file__)
PDF = os.path.join(HERE, "..", ".provas", f"enem_{ANO}_d{DIA}.pdf")
IMGDIR = os.path.join(HERE, "..", "enem", ANO, "img")
os.makedirs(IMGDIR, exist_ok=True)
ZOOM = 2.0; MIDX = 284.0
d = fitz.open(PDF)
def norm(s): return unicodedata.normalize("NFKC", s)
LO, HI = (1, 90) if DIA == 1 else (91, 180)
OFF = 0 if DIA == 1 else 90

# 1) texto por questao (ordem de leitura), primeira ocorrencia de cada numero
txt = norm("\n".join(d[i].get_text() for i in range(d.page_count)))
txt = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", txt)   # de-hifenizacao
# remove secao ESPANHOL 1-5 (fica com ingles, como a base existente)
txt = re.sub(r"(?is)Quest[õo]es de 0*1 a 0*5\s*\(op[cç][ãa]o espanhol\).*?(?=Quest[õo]es de 0*1 a 0*5\s*\(op[cç][ãa]o ingl[êe]s\)|Quest[ãa]o\s+0*6\b)", " ", txt)
parts = re.split(r"(?i)QUEST[ÃA]O\s+0*(\d{1,3})", txt)
qtext = {}
for k in range(1, len(parts), 2):
    n = int(parts[k])
    if LO <= n <= HI and n not in qtext:            # 1a ocorrencia (ingles p/ 1-5)
        qtext[n] = parts[k + 1]

# 1b) textos-base de grupo
GRP = re.compile(r"(?i)(?:para responder [àa]s? quest[õo]es de|texto para as quest[õo]es)\s*0*(\d{1,3})\s*(?:a|à|e)\s*0*(\d{1,3})")
KW = re.compile(r"(?i)(Leia o|Leia a|Leia os|Leia as|Considere o|Considere a|Observe|Analise|TEXTO|Para responder)")
bases = {}
for num in list(qtext):
    c = qtext[num]; mg = GRP.search(c)
    if not mg: continue
    a, b = int(mg.group(1)), int(mg.group(2))
    kws = [m.start() for m in KW.finditer(c) if m.start() <= mg.start() + 40]
    bstart = kws[-1] if kws else mg.start()
    base = c[bstart:].strip()
    qtext[num] = c[:bstart].strip()
    for n in range(a, b + 1):
        if n not in bases: bases[n] = base
for n, bt in bases.items():
    if n in qtext: qtext[n] = bt + "\n\n" + qtext[n]

def limpa(s):
    out = []
    for ln in s.split("\n"):
        t = ln.rstrip()
        if re.fullmatch(r"\s*\d{1,3}\s*", t): continue
        if re.search(r"(LC|CH|CN|MT) - \d| DIA| CADERNO|\*\d", t): continue
        out.append(t)
    return "\n".join(out)

ALTMARK = re.compile(r"(?m)^([A-E])[\t ]+(?=\S)")
def separa_alts(corpo):
    corpo = limpa(corpo)
    ms = list(ALTMARK.finditer(corpo))
    # exige sequencia A,B,C,D,E
    seq = [m for m in ms if m.group(1) == "ABCDE"[len([x for x in ms[:ms.index(m)] if False])]] if False else ms
    # filtra para achar a 1a ocorrencia de A seguida de B..E em ordem
    start = None
    for idx, m in enumerate(ms):
        if m.group(1) == "A":
            letters = [x.group(1) for x in ms[idx:idx+5]]
            if letters == list("ABCDE"):
                start = idx; break
    if start is None:
        return corpo.strip(), []
    blocos = ms[start:start+5]
    enun = corpo[:blocos[0].start()].strip()
    alts = {}
    for j, m in enumerate(blocos):
        L = m.group(1)
        end = blocos[j+1].start() if j+1 < len(blocos) else len(corpo)
        alts[L] = re.sub(r"\s+", " ", corpo[m.end():end]).strip()
    return enun, [f"{L}) {alts[L]}" for L in "ABCDE" if alts.get(L)]

# 2) figuras coluna-aware
MARK = re.compile(r"(?i)QUEST[ÃA]O\s+0*(\d{1,3})")
elems = []
seen_m = set()
for i in range(d.page_count):
    pg = d[i]
    for b in pg.get_text("dict")["blocks"]:
        if "lines" not in b: continue
        first = norm("".join(s["text"] for s in b["lines"][0]["spans"]))
        m = MARK.search(first)
        if m:
            n = int(m.group(1))
            if LO <= n <= HI and n not in seen_m:
                seen_m.add(n)
                elems.append({"page": i, "band": 0 if b["bbox"][0] < MIDX else 1, "y": b["bbox"][1], "kind": "mark", "num": n})
    sset = set()
    for img in pg.get_images(full=True):
        for r in pg.get_image_rects(img[0]):
            if r.width < 45 or r.height < 45: continue
            key = (round(r.x0), round(r.y0))
            if key in sset: continue
            sset.add(key)
            elems.append({"page": i, "band": 0 if r.x0 < MIDX else 1, "y": r.y0, "kind": "img", "rect": [r.x0, r.y0, r.x1, r.y1]})
elems.sort(key=lambda e: (e["page"], e["band"], e["y"]))
figs = {}; atual = None
for e in elems:
    if e["kind"] == "mark": atual = e["num"]
    elif atual is not None: figs.setdefault(atual, []).append((e["page"], e["rect"]))

def render(num, i, page, rect):
    r = fitz.Rect(rect) + (-3, -3, 3, 3)
    pix = d[page].get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), clip=r)
    fn = f"{ANO}_d{DIA}_q{num-OFF:02d}_fig{i}.png"
    pix.save(os.path.join(IMGDIR, fn))
    return f"enem/{ANO}/img/{fn}"

saida = []
for num in sorted(qtext):
    enun, alts = separa_alts(qtext[num])
    fm = [f"![]({render(num,i,pg,rect)})" for i, (pg, rect) in enumerate(figs.get(num, []), 1)]
    if fm: enun = (enun + "\n\n" + "\n".join(fm)).strip()
    saida.append({"numero": num - OFF, "enunciado": enun, "alternativas": alts, "n_alts": len(alts), "n_figs": len(fm)})
out = os.path.join(HERE, f"_enem_extract_{ANO}_d{DIA}.json")
json.dump(saida, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"ENEM {ANO} D{DIA} | questoes:", len(saida), "| faltando:", [n for n in range(1, 91) if n not in [q['numero'] for q in saida]])
print("!= 5 alts:", [(q["numero"], q["n_alts"]) for q in saida if q["n_alts"] != 5])
print("figuras:", sum(q["n_figs"] for q in saida), "-> salvo", out)
