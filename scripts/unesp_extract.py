# -*- coding: utf-8 -*-
"""Extrai UNESP F1 (90 q, 5 alternativas (A)-(E), marcador QUESTAO N) -> JSON.
Uso: python unesp_extract.py <ANO>. Texto via reading order; figuras coluna-aware."""
import fitz, re, os, json, sys, unicodedata
ANO = sys.argv[1] if len(sys.argv) > 1 else "2022"
HERE = os.path.dirname(__file__)
PDF = os.path.join(HERE, "..", ".provas", f"unesp_{ANO}_f1.pdf")
IMGDIR = os.path.join(HERE, "..", "vestibular", "unesp", "img")
os.makedirs(IMGDIR, exist_ok=True)
ZOOM = 2.0; MIDX = 297.0
d = fitz.open(PDF)

def norm(s): return unicodedata.normalize("NFKC", s)
MARK = re.compile(r"QUEST[ÃA]O\s+0*(\d{1,2})\b")

# 1) texto por questao (reading order)
txt = norm("\n".join(d[i].get_text() for i in range(d.page_count)))
# de-hifenizacao de quebra de linha: "ques-\ntoes" -> "questoes" (corrige tambem alternativas)
txt = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", txt)
parts = re.split(r"QUEST[ÃA]O\s+0*(\d{1,2})\b", txt)
qtext = {}
for k in range(1, len(parts), 2):
    n = int(parts[k])
    if 1 <= n <= 90:
        qtext[n] = parts[k+1]

# 1b) textos-base de grupo: "...para responder as questoes de X a Y..." (ou a questao X)
# aparecem no RABO da questao anterior; extrai e prepende a cada membro X..Y.
KW = re.compile(r"(Para responder|Leia (?:o|a|os|as) |Examine |Considere (?:o|a) |Observe (?:o|a) |Analise (?:o|a) |TEXTO PARA|Texto para)")
GRP = re.compile(r"para responder [àa]s? quest[õo]es de (\d+)\s*a\s*(\d+)", re.I)
GRP1 = re.compile(r"para responder [àa] quest[ãa]o (\d+)", re.I)
bases = {}
for num in list(qtext):
    c = qtext[num]
    mg = GRP.search(c)
    if mg: a, b = int(mg.group(1)), int(mg.group(2))
    else:
        mg = GRP1.search(c)
        if not mg: continue
        a = b = int(mg.group(1))
    kws = [m.start() for m in KW.finditer(c) if m.start() <= mg.start() + 60]
    bstart = kws[-1] if kws else mg.start()
    base = c[bstart:].strip()
    qtext[num] = c[:bstart].strip()
    for n in range(a, b + 1):
        if n not in bases:
            bases[n] = base
for n, bt in bases.items():
    if n in qtext:
        qtext[n] = bt + "\n\n" + qtext[n]
print("grupos de texto-base: membros com base anexada =", sorted(bases))

def limpa(s):
    out=[]
    for ln in s.split("\n"):
        t=ln.rstrip()
        if re.fullmatch(r"\s*\d{1,3}\s*", t): continue
        if "Confidencial at" in t or "ProvaObjetiva" in t or re.match(r"^vnsp", t): continue
        out.append(t)
    return "\n".join(out)

def separa_alts(corpo):
    corpo = limpa(corpo)
    mA = re.search(r"\(A\)", corpo)
    if not mA: return corpo.strip(), []
    enun = corpo[:mA.start()].strip(); resto = corpo[mA.start():]
    alts={}
    for L in "ABCDE":
        nxt=chr(ord(L)+1)
        pat = rf"\({L}\)(.*?)(?=\({nxt}\)|$)" if L!="E" else r"\(E\)(.*)$"
        mm=re.search(pat, resto, re.S)
        if mm: alts[L]=re.sub(r"\s+"," ",mm.group(1)).strip()
    return enun, [f"{L}) {alts[L]}" for L in "ABCDE" if L in alts]

# 2) figuras coluna-aware
elems=[]
for i in range(d.page_count):
    pg=d[i]
    for b in pg.get_text("dict")["blocks"]:
        if "lines" not in b: continue
        first=norm("".join(s["text"] for s in b["lines"][0]["spans"]))
        m=MARK.search(first)
        if m:
            x0=b["bbox"][0]
            elems.append({"page":i,"band":0 if x0<MIDX else 1,"y":b["bbox"][1],"kind":"mark","num":int(m.group(1))})
    seen=set()
    for img in pg.get_images(full=True):
        for r in pg.get_image_rects(img[0]):
            if r.width<45 or r.height<45: continue
            key=(round(r.x0),round(r.y0))
            if key in seen: continue
            seen.add(key)
            elems.append({"page":i,"band":0 if r.x0<MIDX else 1,"y":r.y0,"kind":"img","rect":[r.x0,r.y0,r.x1,r.y1]})
elems.sort(key=lambda e:(e["page"],e["band"],e["y"]))
figs={}; atual=None
for e in elems:
    if e["kind"]=="mark": atual=e["num"]
    elif atual is not None: figs.setdefault(atual,[]).append((e["page"],e["rect"]))

def render(num,i,page,rect):
    r=fitz.Rect(rect)+(-3,-3,3,3)
    pix=d[page].get_pixmap(matrix=fitz.Matrix(ZOOM,ZOOM),clip=r)
    fn=f"{ANO}_q{num:02d}_fig{i}.png"; pix.save(os.path.join(IMGDIR,fn))
    return f"vestibular/unesp/img/{fn}"

saida=[]
for num in sorted(qtext):
    enun,alts=separa_alts(qtext[num])
    fm=[f"![]({render(num,i,pg,rect)})" for i,(pg,rect) in enumerate(figs.get(num,[]),1)]
    if fm: enun=(enun+"\n\n"+"\n".join(fm)).strip()
    saida.append({"numero":num,"enunciado":enun,"alternativas":alts,"n_alts":len(alts),"n_figs":len(fm)})
out=os.path.join(HERE,f"_unesp_extract_{ANO}.json")
json.dump(saida,open(out,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("ANO",ANO,"| questoes:",len(saida),"| faltando:",[n for n in range(1,91) if n not in qtext])
print("!= 5 alts:",[(q["numero"],q["n_alts"]) for q in saida if q["n_alts"]!=5])
print("figuras:",sum(q["n_figs"] for q in saida),"| salvo ->",out)
