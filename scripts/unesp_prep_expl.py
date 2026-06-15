# -*- coding: utf-8 -*-
"""Dump para agentes de explicacao UNESP, com resposta correta oficial.
Uso: python unesp_prep_expl.py <ANO>"""
import json, os, re, sys
ANO = sys.argv[1] if len(sys.argv) > 1 else "2022"
HERE = os.path.dirname(__file__)
extract = {q["numero"]: q for q in json.load(open(os.path.join(HERE,f"_unesp_extract_{ANO}.json"),encoding="utf-8"))}
auth = json.load(open(os.path.join(HERE,f"_unesp_gab_autoritativo_{ANO}.json"),encoding="utf-8"))
esp_p = os.path.join(HERE,f"_unesp_especiais_{ANO}.json")
esp = json.load(open(esp_p,encoding="utf-8")) if os.path.exists(esp_p) else {}
L=[]
for n in range(1,91):
    if n not in extract: continue
    a=auth.get(str(n),"?").upper()
    if a=="ANULADA": continue
    q=extract[n]; enun=re.sub(r"!\[\]\([^)]*\)","[FIGURA]",q["enunciado"]).strip()
    L.append("="*70); L.append(f"QUESTAO {n}  | RESPOSTA_CORRETA_OFICIAL={a}")
    L.append("ENUNCIADO: "+enun)
    if str(n) in esp or not q["alternativas"]:
        L.append("ALTERNATIVAS: (em imagem - questao renderizada como imagem)")
    else:
        L.append("ALTERNATIVAS:")
        for alt in q["alternativas"]: L.append("  "+alt)
    L.append("")
open(os.path.join(HERE,f"_unesp_dump_{ANO}.txt"),"w",encoding="utf-8").write("\n".join(L))
print("ANO",ANO,"| dump gerado | anuladas:",[n for n in range(1,91) if auth.get(str(n),"").upper()=="ANULADA"])
