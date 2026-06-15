# -*- coding: utf-8 -*-
"""Dump para agentes de explicacao FUVEST, com resposta correta oficial.
Uso: python fuvest_prep_expl.py <ANO>"""
import json, os, re, sys
ANO = sys.argv[1] if len(sys.argv) > 1 else "2022"
HERE = os.path.dirname(__file__)
extract = {q["numero"]: q for q in json.load(open(os.path.join(HERE,f"_fuvest_extract_{ANO}.json"),encoding="utf-8"))}
auth = json.load(open(os.path.join(HERE,f"_fuvest_gab_{ANO}.json"),encoding="utf-8"))
L=[]
for n in range(1,91):
    if n not in extract: continue
    a=auth.get(str(n),"?").upper()
    if a=="ANULADA": continue
    q=extract[n]; enun=re.sub(r"!\[\]\([^)]*\)","[FIGURA]",q["enunciado"]).strip()
    L.append("="*70); L.append(f"QUESTAO {n}  | RESPOSTA_CORRETA_OFICIAL={a}")
    L.append("ENUNCIADO: "+enun)
    L.append("ALTERNATIVAS:")
    for alt in q["alternativas"]: L.append("  "+alt)
    L.append("")
open(os.path.join(HERE,f"_fuvest_dump_{ANO}.txt"),"w",encoding="utf-8").write("\n".join(L))
print("ANO",ANO,"| dump gerado | anuladas:",[n for n in range(1,91) if auth.get(str(n),"").upper()=="ANULADA"])
