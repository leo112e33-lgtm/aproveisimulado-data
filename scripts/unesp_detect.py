# -*- coding: utf-8 -*-
import fitz, re, json
p = r"C:\Users\leo11\.claude\projects\C--Users-leo11\6da471ab-3033-4493-87bd-4350fd5e829b\tool-results\webfetch-1781392739634-9mu28i.pdf"
d = fitz.open(p)

MARK = re.compile(r"^\s*QUEST[ÃA]O\s*0*(\d{1,2})\b", re.I)
BASE = re.compile(r"(?i)(para responder|leia).{0,80}?quest(?:ões|ao|ão)\s*(?:de\s*)?0*(\d{1,2})\s*(?:a|à|até)\s*0*(\d{1,2})")

marks = []   # (qnum, page, col, x0, y0, x1, y1)
bases = []   # (ini, fim, page, col, y0)
for pi in range(d.page_count):
    pg = d[pi]; W = pg.rect.width; mid = W/2
    dct = pg.get_text("dict")
    for blk in dct.get("blocks", []):
        for ln in blk.get("lines", []):
            spans = ln.get("spans", [])
            if not spans: continue
            texto = "".join(s["text"] for s in spans).strip()
            bbox = ln["bbox"]
            col = 0 if bbox[0] < mid else 1
            m = MARK.match(texto)
            if m:
                num = int(m.group(1))
                if 1 <= num <= 90:
                    marks.append((num, pi, col, bbox[0], bbox[1], bbox[2], bbox[3]))
            # base por linha (parcial): detecta inicio do enunciado-base
            b = BASE.search(texto)
            if b:
                bases.append((int(b.group(2)), int(b.group(3)), pi, col, bbox[1], texto[:60]))

nums = [m[0] for m in marks]
print("marcadores encontrados:", len(marks))
print("numeros:", sorted(set(nums)))
faltando = [n for n in range(1, 91) if n not in nums]
print("FALTANDO:", faltando)
dup = [n for n in set(nums) if nums.count(n) > 1]
print("DUPLICADOS:", dup)
print("bases detectadas:", len(bases))
for b in bases[:20]:
    print("  base", b[0], "a", b[1], "pag", b[2], "col", b[3])
