# -*- coding: utf-8 -*-
"""Gera o dump para os agentes de explicacao da UNICAMP, JA com a resposta
correta oficial (do gabarito autoritativo). Uso: python unicamp_prep_expl.py <ANO>"""
import json, os, re, sys
ANO = sys.argv[1] if len(sys.argv) > 1 else "2023"
HERE = os.path.dirname(__file__)
extract = {q["numero"]: q for q in json.load(open(os.path.join(HERE,f"_unicamp_extract_{ANO}.json"),encoding="utf-8"))}
auth = json.load(open(os.path.join(HERE,f"_unicamp_gab_autoritativo_{ANO}.json"),encoding="utf-8"))
esp_path = os.path.join(HERE,f"_unicamp_especiais_{ANO}.json")
esp = json.load(open(esp_path,encoding="utf-8")) if os.path.exists(esp_path) else {}

L=[]
faltam=[]
for n in range(1,73):
    if n not in extract: faltam.append(n); continue
    q=extract[n]; a=auth.get(str(n),"?").upper()
    if a=="ANULADA": continue
    enun=re.sub(r"!\[\]\([^)]*\)","[FIGURA]",q["enunciado"]).strip()
    L.append("="*70)
    L.append(f"QUESTAO {n}  | RESPOSTA_CORRETA_OFICIAL={a}")
    L.append("ENUNCIADO: "+enun)
    if str(n) in esp or not q["alternativas"]:
        L.append("ALTERNATIVAS: (em imagem/formula - a questao foi renderizada como imagem)")
    else:
        L.append("ALTERNATIVAS:")
        for alt in q["alternativas"]: L.append("  "+alt)
    L.append("")
open(os.path.join(HERE,f"_unicamp_dump_{ANO}.txt"),"w",encoding="utf-8").write("\n".join(L))
print("ANO",ANO,"| dump gerado. faltam extract:",faltam,"| anuladas:",[n for n in range(1,73) if auth.get(str(n),"").upper()=="ANULADA"])
