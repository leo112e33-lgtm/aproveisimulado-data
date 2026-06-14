# -*- coding: utf-8 -*-
"""FUVEST 2023 (Prova V) no formato ENEM. Marcador = numero isolado (01-90);
2 colunas; extracao seguindo o fluxo de leitura (esq->dir->proxima pagina)."""
import fitz, re, os, json
from collections import defaultdict
PDF = r"C:\Users\leo11\.claude\projects\C--Users-leo11\6da471ab-3033-4493-87bd-4350fd5e829b\tool-results\webfetch-1781391948957-c2dwlb.pdf"
ROOT = r"C:\Users\leo11\AndroidStudioProjects\aproveisimulado-data\vestibular\fuvest"
IMG = os.path.join(ROOT, "img")
os.makedirs(IMG, exist_ok=True)
d = fitz.open(PDF)
W = d[0].rect.width; H = d[0].rect.height; mid = W/2
SENT = "\x00"; GAP = 24; TOPM = 56; BOTM = H-28

NUM = re.compile(r"^\s*0?(\d{1,2})\s*$")
BASE = re.compile(r"(?i)(?:TEXTO PARA (?:AS )?QUEST[ÕO]ES|para responder|leia).{0,80}?\b0*(\d{1,2})\s*(?:e|a|à|até|,)\s*0*(\d{1,2})\b")

def slot(page, col): return page*2 + col
def col_x(col): return (28, mid-3) if col == 0 else (mid+3, W-24)

# eventos: marcadores e bases
marks = {}; base_groups = []
for pi in range(d.page_count):
    for blk in d[pi].get_text("dict").get("blocks", []):
        if blk.get("type") != 0: continue
        for ln in blk.get("lines", []):
            t = "".join(s["text"] for s in ln.get("spans", [])).strip()
            bb = ln["bbox"]; col = 0 if bb[0] < mid else 1
            m = NUM.match(t)
            if m and 1 <= int(m.group(1)) <= 90 and bb[1] < 800:
                num = int(m.group(1))
                if num not in marks: marks[num] = (slot(pi, col), bb[1])
            b = BASE.search(re.sub(r"\s+", " ", t))
            if b:
                a1, a2 = int(b.group(1)), int(b.group(2))
                if 1 <= a1 <= 90 and a2 >= a1: base_groups.append((a1, a2, slot(pi, col), bb[1]))

# lista de eventos ordenada por leitura (slot, y)
eventos = [(s, y, "M", n) for n, (s, y) in marks.items()]
eventos += [(s, y, "B", (a1, a2)) for (a1, a2, s, y) in base_groups]
eventos.sort(key=lambda e: (e[0], e[1]))
print("marcadores:", len(marks), "faltando:", [n for n in range(1, 91) if n not in marks], "| bases:", len(base_groups))

# ---- conteudo grafico (figuras) ----
_cc = {}
def content_rects(pi):
    if pi in _cc: return _cc[pi]
    pg = d[pi]; imgs = []; draws = []
    for blk in pg.get_text("dict").get("blocks", []):
        if blk.get("type") == 1: imgs.append(fitz.Rect(blk["bbox"]))
    for dr in pg.get_drawings():
        r = dr.get("rect")
        if r and r.width > 2 and r.height > 2: draws.append(fitz.Rect(r))
    _cc[pi] = (imgs, draws); return _cc[pi]
def _inter(r, xl, xr, ya, yb):
    return min(r.x1, xr) > max(r.x0, xl) and min(r.y1, yb) > max(r.y0, ya)
def banda_fig(pi, xl, xr, ya, yb):
    if yb-ya < GAP: return False
    imgs, draws = content_rects(pi); ab = (xr-xl)*(yb-ya)
    for r in imgs:
        ix = min(r.x1, xr)-max(r.x0, xl); iy = min(r.y1, yb)-max(r.y0, ya)
        if ix > 0 and iy > 0 and (ix*iy > 0.08*ab or (r.height > 28 and r.width > 28)): return True
    return sum(1 for r in draws if _inter(r, xl, xr, ya, yb)) >= 5

figc = defaultdict(int)
def crop(pi, rect, key):
    figc[key] += 1; nome = f"2023_{key}_fig{figc[key]}.png"
    r = fitz.Rect(rect.x0-2, rect.y0-2, rect.x1+2, rect.y1+2)
    d[pi].get_pixmap(clip=r, matrix=fitz.Matrix(3, 3)).save(os.path.join(IMG, nome))
    return "vestibular/fuvest/img/" + nome

def extrai_regiao(pi, col, y0, y1, key):
    pg = d[pi]; xl, xr = col_x(col); linhas = []
    for blk in pg.get_text("dict").get("blocks", []):
        if blk.get("type") != 0: continue
        for ln in blk.get("lines", []):
            lx0, ly0, lx1, ly1 = ln["bbox"]
            if ly0 < y0-2 or ly0 > y1-2: continue
            if lx1 < xl or lx0 > xr: continue
            t = "".join(s["text"] for s in ln.get("spans", []))
            if NUM.match(t.strip()): continue
            if "Concurso Vestibular FUVEST" in t: continue
            linhas.append((ly0, ly1, t))
    linhas.sort()
    partes = []; pb = y0
    for (ly0, ly1, t) in linhas:
        if banda_fig(pi, xl, xr, pb, ly0):
            partes.append(SENT + crop(pi, fitz.Rect(xl, pb, xr, ly0), key) + SENT)
        partes.append(t + "\n"); pb = ly1
    if banda_fig(pi, xl, xr, pb, y1-2):
        partes.append(SENT + crop(pi, fitz.Rect(xl, pb, xr, y1-2), key) + SENT)
    return "".join(partes)

def extrai_span(s1, y1, s2, y2, key):
    out = ""
    for s in range(s1, s2+1):
        page = s//2; col = s % 2
        yt = y1 if s == s1 else TOPM
        yb = y2 if s == s2 else BOTM
        if yb-yt > 4: out += extrai_regiao(page, col, yt, yb, key)
    return out

# ---- parsing texto/alternativas ----
ALT = re.compile(r"\(([A-E])\)")
def separa(texto):
    m = ALT.search(texto)
    if not m: return texto, []
    stmt = texto[:m.start()]; rest = texto[m.start():]
    pos = [(mm.group(1), mm.start()) for mm in ALT.finditer(rest)]
    alts = []
    for i, (letra, st) in enumerate(pos):
        en = pos[i+1][1] if i+1 < len(pos) else len(rest)
        c = re.sub(r"^\([A-E]\)", "", rest[st:en])
        c = re.sub(SENT + r"[^" + SENT + r"]*" + SENT, "", c)
        alts.append(letra + ") " + re.sub(r"\s+", " ", c).strip())
    return stmt, alts
def limpa(s):
    s = re.sub(SENT + r"([^" + SENT + r"]+)" + SENT, r"\n\n![](\1)\n\n", s)
    blocks = []
    for b in s.split("\n\n"):
        b = b.strip()
        if not b: continue
        if b.startswith("!["): blocks.append(b); continue
        b = b.replace("-\n", ""); b = re.sub(r"\s*\n\s*", " ", b); b = re.sub(r"[ \t]+", " ", b).strip()
        if b: blocks.append(b)
    return "\n\n".join(blocks)

# ---- bases ----
def next_event_after(s, y):
    for (es, ey, k, info) in eventos:
        if (es, ey) > (s, y): return (es, ey)
    return (slot(d.page_count-1, 1), H)
base_enun = {}
for (a1, a2, s, y) in base_groups:
    if a1 not in marks: continue
    ms, my = marks[a1]
    raw = extrai_span(s, y, ms, my, f"base{a1}")
    txt = limpa(raw)
    for q in range(a1, a2+1): base_enun[q] = txt

# ---- questoes ----
gab = json.loads(open(os.path.join(ROOT, "_gab_v.json")).read())
questoes = []
for n in range(1, 91):
    if n not in marks: continue
    ms, my = marks[n]
    es, ey = next_event_after(ms, my)
    raw = extrai_span(ms, my, es, ey, f"q{n:02d}")
    stmt, alts = separa(raw)
    enun = limpa(stmt)
    if n in base_enun: enun = base_enun[n] + "\n\n" + enun
    questoes.append({
        "numero": n, "ano": 2023, "titulo": f"Questão {n} - FUVEST 2023",
        "enunciado": enun, "alternativas_introducao": "",
        "alternativas": alts, "imagens_alternativas": [None]*len(alts),
        "imagem_principal": "", "imagens_extras": [],
        "correta": gab.get(str(n), "X"),
        "explicacao": f"**Resposta correta: {gab.get(str(n),'X')}.**\n\nFUVEST 2023 (1ª fase, Prova V).",
        "fonte": "fuvest_oficial",
        "fonte_url": "https://www.fuvest.br/wp-content/uploads/fuvest2023_primeira_fase_prova_V.pdf"})
ruins = [q["numero"] for q in questoes if len(q["alternativas"]) != 5]
print("questoes:", len(questoes), "| sem 5 alts:", ruins, "| com figura:", sum(1 for q in questoes if "![](" in q["enunciado"]))
payload = {"vestibular": "FUVEST", "ano": 2023,
    "titulo": "FUVEST 2023 — 1ª fase (prova completa, Prova V)", "totalQuestoes": len(questoes),
    "observacao": "Prova completa da 1ª fase da FUVEST 2023 (Prova V): texto do PDF oficial + figuras recortadas. Gabarito oficial da Prova V.",
    "questoes": questoes}
open(os.path.join(ROOT, "2023.json"), "w", encoding="utf-8").write(json.dumps(payload, ensure_ascii=False, indent=2))
