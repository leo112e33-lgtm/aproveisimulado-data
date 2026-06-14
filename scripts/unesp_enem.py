# -*- coding: utf-8 -*-
"""Reconstroi a UNESP 2023 no formato ENEM: enunciado em TEXTO + figuras
recortadas (apenas as imagens) inline + alternativas em TEXTO."""
import fitz, re, os, json
from collections import defaultdict
PDF = r"C:\Users\leo11\.claude\projects\C--Users-leo11\6da471ab-3033-4493-87bd-4350fd5e829b\tool-results\webfetch-1781392739634-9mu28i.pdf"
ROOT = r"C:\Users\leo11\AndroidStudioProjects\aproveisimulado-data\vestibular\unesp"
IMG = os.path.join(ROOT, "img")
os.makedirs(IMG, exist_ok=True)
d = fitz.open(PDF)
W = d[0].rect.width; H = d[0].rect.height; mid = W/2
SENT = "\x00"

MARK = re.compile(r"^\s*QUEST[ÃA]O\s*0*(\d{1,2})\b", re.I)
BOIL = re.compile(r"(?i)vnsp\s*\d|prova\s*objetiva|001-cg|confidencial at[eé]")
BASE = re.compile(r"(?i)(?:para responder|leia|com base|considere|examine|observe|analise|tomando|a partir d).{0,200}?quest(?:ões|ão|ao)\s*(?:de\s+)?0*(\d{1,2})\s*(?:a|à|até|e)\s*0*(\d{1,2})")

marks = {}; base_groups = []
for pi in range(d.page_count):
    for blk in d[pi].get_text("dict").get("blocks", []):
        bb_blk = blk["bbox"]; col_blk = 0 if bb_blk[0] < mid else 1
        block_txt = ""
        for ln in blk.get("lines", []):
            t = "".join(s["text"] for s in ln.get("spans", [])).strip()
            bb = ln["bbox"]; col = 0 if bb[0] < mid else 1
            m = MARK.match(t)
            if m and 1 <= int(m.group(1)) <= 90:
                marks[int(m.group(1))] = (pi, col, bb[1])
            block_txt += " " + t
        b = BASE.search(re.sub(r"\s+", " ", block_txt))
        if b:
            a1, a2 = int(b.group(1)), int(b.group(2))
            if 1 <= a1 <= 90 and a2 >= a1 and a2 - a1 <= 12:
                base_groups.append((a1, a2, pi, col_blk, bb_blk[1]))

cuts = defaultdict(list)
for (pi, col, y) in marks.values(): cuts[(pi, col)].append(y)
for (a, b2, pi, col, y) in base_groups: cuts[(pi, col)].append(y)
for k in cuts: cuts[k].sort()
def prox(pi, col, y):
    nx = [c for c in cuts[(pi, col)] if c > y+5]
    return min(nx) if nx else H-26
def col_x(col): return (24, mid-2) if col == 0 else (mid+2, W-20)

fig_counter = defaultdict(int)
def crop_fig(pi, rect, key):
    fig_counter[key] += 1
    nome = f"2023_{key}_fig{fig_counter[key]}.png"
    pad = 2
    r = fitz.Rect(rect.x0-pad, rect.y0-pad, rect.x1+pad, rect.y1+pad)
    d[pi].get_pixmap(clip=r, matrix=fitz.Matrix(3, 3)).save(os.path.join(IMG, nome))
    return "vestibular/unesp/img/" + nome

GAP = 24  # gap vertical minimo (px) que indica uma figura

# cache de "retangulos de conteudo grafico" (imagens + desenhos vetoriais) por pagina
_content_cache = {}
def content_rects(pi):
    if pi in _content_cache: return _content_cache[pi]
    pg = d[pi]; imgs = []; draws = []
    HD, FT = 54, H-28   # zona de cabecalho/rodape (decoracao da pagina)
    for blk in pg.get_text("dict").get("blocks", []):
        if blk.get("type") == 1:
            r = fitz.Rect(blk["bbox"])
            if r.y1 <= HD or r.y0 >= FT: continue
            imgs.append(r)
    for dr in pg.get_drawings():
        r = dr.get("rect")
        if r and r.width > 2 and r.height > 5 and r.y1 > HD and r.y0 < FT:
            draws.append(fitz.Rect(r))
    _content_cache[pi] = (imgs, draws)
    return _content_cache[pi]

def _inter(r, xl, xr, ya, yb):
    return min(r.x1, xr) > max(r.x0, xl) and min(r.y1, yb) > max(r.y0, ya)

def banda_tem_figura(pi, xl, xr, ya, yb):
    if yb - ya < GAP: return False
    imgs, draws = content_rects(pi)
    area_band = (xr-xl) * (yb-ya)
    for r in imgs:  # imagem rasterizada ocupando parte relevante
        ix = min(r.x1, xr)-max(r.x0, xl); iy = min(r.y1, yb)-max(r.y0, ya)
        if ix > 0 and iy > 0 and (ix*iy > 0.08*area_band or (r.height > 28 and r.width > 28)):
            return True
    # densidade de tracos vetoriais (graficos/diagramas sao muitos paths)
    n = sum(1 for r in draws if _inter(r, xl, xr, ya, yb))
    return n >= 5

def extrai(pi, col, y0, y1, key):
    pg = d[pi]; xl, xr = col_x(col)
    # linhas de texto na regiao (fora o marcador)
    linhas = []
    for blk in pg.get_text("dict").get("blocks", []):
        if blk.get("type") != 0: continue
        for ln in blk.get("lines", []):
            lx0, ly0, lx1, ly1 = ln["bbox"]
            if ly0 < y0-2 or ly0 > y1-2: continue
            if lx1 < xl or lx0 > xr: continue
            t = "".join(s["text"] for s in ln.get("spans", []))
            ts = re.sub(r"\s+", " ", t).strip()
            if MARK.match(ts): continue
            if BOIL.search(ts) or re.fullmatch(r"\d{1,3}", ts): continue  # cabecalho/rodape/num pagina
            linhas.append((ly0, ly1, t))
    linhas.sort()
    partes = []
    prev_bottom = y0
    for (ly0, ly1, t) in linhas:
        if banda_tem_figura(pi, xl, xr, prev_bottom, ly0):
            md = crop_fig(pi, fitz.Rect(xl, prev_bottom, xr, ly0), key)
            partes.append(SENT + md + SENT)
        partes.append(t + "\n")
        prev_bottom = ly1
    # figura apos a ultima linha (ate o fim da regiao)
    if banda_tem_figura(pi, xl, xr, prev_bottom, y1-2):
        md = crop_fig(pi, fitz.Rect(xl, prev_bottom, xr, y1-2), key)
        partes.append(SENT + md + SENT)
    return "".join(partes)

ALT = re.compile(r"\(([A-E])\)")
def separa(texto):
    m = ALT.search(texto)
    if not m: return texto, []
    stmt = texto[:m.start()]; rest = texto[m.start():]
    pos = [(mm.group(1), mm.start()) for mm in ALT.finditer(rest)]
    alts = []
    for i, (letra, st) in enumerate(pos):
        en = pos[i+1][1] if i+1 < len(pos) else len(rest)
        corpo = re.sub(r"^\([A-E]\)", "", rest[st:en])
        corpo = re.sub(SENT + r"[^" + SENT + r"]*" + SENT, "", corpo)  # remove imgs em alts
        corpo = re.sub(r"\s+", " ", corpo).strip()
        alts.append(letra + ") " + corpo)
    return stmt, alts

def limpa(s):
    s = re.sub(SENT + r"([^" + SENT + r"]+)" + SENT, r"\n\n![](\1)\n\n", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

base_enun = {}
for (ini, fim, pi, col, y) in base_groups:
    if ini not in marks: continue
    raw = extrai(pi, col, y, prox(pi, col, y), f"base{ini}")
    texto = limpa(raw)
    for q in range(ini, fim+1): base_enun[q] = texto

questoes = {}
for num, (pi, col, y) in marks.items():
    raw = extrai(pi, col, y, prox(pi, col, y), f"q{num:02d}")
    raw = re.sub(r"^\s*QUEST[ÃA]O\s*0*\d+\s*", "", raw, flags=re.I)
    stmt, alts = separa(raw)
    enun = limpa(stmt)
    if num in base_enun:
        enun = base_enun[num] + "\n\n" + enun
    questoes[num] = {"enun": enun, "alts": alts}

q1 = questoes[1]
print("=== Q1 ENUNCIADO ===")
print(q1["enun"].encode("ascii", "replace").decode())
print("=== Q1 ALTERNATIVAS ===")
for a in q1["alts"]: print("  " + a.encode("ascii", "replace").decode())
ruins = [n for n in range(1, 91) if len(questoes[n]["alts"]) != 5]
print("=== questoes sem 5 alternativas:", ruins)
json.dump({str(n): questoes[n] for n in questoes},
          open(os.path.join(ROOT, "_enem_draft.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
