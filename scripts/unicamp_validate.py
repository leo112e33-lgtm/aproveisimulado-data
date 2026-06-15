# -*- coding: utf-8 -*-
"""Valida vestibular/unicamp/<ANO>.json. Uso: python unicamp_validate.py <ANO>"""
import json, os, re, sys
ANO = sys.argv[1] if len(sys.argv) > 1 else "2023"
HERE = os.path.dirname(__file__)
doc = json.load(open(os.path.join(HERE,"..","vestibular","unicamp",f"{ANO}.json"),encoding="utf-8"))
auth = json.load(open(os.path.join(HERE,f"_unicamp_gab_autoritativo_{ANO}.json"),encoding="utf-8"))
probs=[]
for q in doc["questoes"]:
    n=q["numero"]; c=q["correta"]; ex=(q["explicacao"] or "").strip(); a=auth.get(str(n),"?").upper()
    if a=="ANULADA":
        if c!="X": probs.append(f"Q{n}: deveria ser anulada (X), esta {c}")
        continue
    if c!=a: probs.append(f"Q{n}: correta {c} != autoritativo {a}")
    if not ex.startswith("**Por que a alternativa"): probs.append(f"Q{n}: formato inicio")
    if "Conceito-chave" not in ex: probs.append(f"Q{n}: sem Conceito-chave")
    m=re.match(r"\*\*Por que a alternativa ([A-E])",ex)
    if m and m.group(1)!=c: probs.append(f"Q{n}: letra texto {m.group(1)} != correta {c}")
    if len(q["alternativas"])!=4: probs.append(f"Q{n}: {len(q['alternativas'])} alternativas")
print(f"UNICAMP {ANO}: {len(doc['questoes'])} questoes, {len(probs)} problemas")
for p in probs: print("  ",p)
print("OK" if not probs else "TEM PROBLEMAS")
