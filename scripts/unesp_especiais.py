# -*- coding: utf-8 -*-
"""Renderiza como imagem da questao inteira as questoes UNESP que NAO rendem 5
alternativas limpas. Uso: python unesp_especiais.py <ANO>"""
import fitz, re, os, json, sys
ANO = sys.argv[1] if len(sys.argv) > 1 else "2022"
HERE = os.path.dirname(__file__)
PDF = os.path.join(HERE, "..", ".provas", f"unesp_{ANO}_f1.pdf")
IMGDIR = os.path.join(HERE, "..", "vestibular", "unesp", "img")
ZOOM = 2.0; MIDX = 297.0
d = fitz.open(PDF)
extract = {q["numero"]: q for q in json.load(open(os.path.join(HERE,f"_unesp_extract_{ANO}.json"),encoding="utf-8"))}
bad = [n for n,q in extract.items() if q["n_alts"] != 5]
print("ANO",ANO,"| render como imagem:",bad)
marks=[]
for i in range(d.page_count):
    for b in d[i].get_text("dict")["blocks"]:
        if "lines" not in b: continue
        for ln in b["lines"]:
            t="".join(s["text"] for s in ln["spans"])
            m=re.match(r"\s*QUEST[ÃA]O\s+0*(\d{1,2})\b", t)
            if m: marks.append({"num":int(m.group(1)),"page":i,"band":0 if ln["bbox"][0]<MIDX else 1,"y":ln["bbox"][1]})
marks.sort(key=lambda e:(e["page"],e["band"],e["y"]))
def render_full(num):
    idx=next((i for i,m in enumerate(marks) if m["num"]==num),None)
    if idx is None: raise RuntimeError(f"Q{num} sem marcador")
    mk=marks[idx]; nxt=marks[idx+1] if idx+1<len(marks) else None
    x0,x1=(26,294) if mk["band"]==0 else (300,569)
    ytop=mk["y"]-4
    ybot=nxt["y"]-4 if (nxt and nxt["page"]==mk["page"] and nxt["band"]==mk["band"]) else 812
    pix=d[mk["page"]].get_pixmap(matrix=fitz.Matrix(ZOOM,ZOOM),clip=fitz.Rect(x0,ytop,x1,ybot))
    fn=f"{ANO}_q{num:02d}_full.png"; pix.save(os.path.join(IMGDIR,fn))
    return f"vestibular/unesp/img/{fn}"
patch={}
for num in bad:
    p=render_full(num)
    patch[str(num)]={"imagem_principal":p,"alternativas":["A","B","C","D","E"]}
    print(f"  Q{num} -> {p}")
json.dump(patch,open(os.path.join(HERE,f"_unesp_especiais_{ANO}.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("patch salvo")
