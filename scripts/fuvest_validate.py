# -*- coding: utf-8 -*-
"""Valida vestibular/fuvest/<ANO>.json. Uso: python fuvest_validate.py <ANO>"""
import json, os, re, sys
ANO = sys.argv[1] if len(sys.argv) > 1 else "2022"
HERE = os.path.dirname(__file__)
doc = json.load(open(os.path.join(HERE,"..","vestibular","fuvest",f"{ANO}.json"),encoding="utf-8"))
auth = json.load(open(os.path.join(HERE,f"_fuvest_gab_{ANO}.json"),encoding="utf-8"))
probs=[]
for q in doc["questoes"]:
    n=q["numero"]; c=q["correta"]; ex=(q["explicacao"] or "").strip(); a=auth.get(str(n),"?").upper()
    if a=="ANULADA":
        if c!="X": probs.append(f"Q{n}: deveria X")
        continue
    if c!=a: probs.append(f"Q{n}: correta {c}!=auth {a}")
    if not ex.startswith("**Por que a alternativa"): probs.append(f"Q{n}: inicio")
    if "Conceito-chave" not in ex: probs.append(f"Q{n}: sem Conceito-chave")
    m=re.match(r"\*\*Por que a alternativa ([A-E])",ex)
    if m and m.group(1)!=c: probs.append(f"Q{n}: letra {m.group(1)}!=correta {c}")
    if len(q["alternativas"])!=5: probs.append(f"Q{n}: {len(q['alternativas'])} alts")
print(f"FUVEST {ANO}: {len(doc['questoes'])} questoes, {len(probs)} problemas")
for p in probs[:40]: print("  ",p)
print("OK" if not probs else "TEM PROBLEMAS")
