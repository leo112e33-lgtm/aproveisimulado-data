# -*- coding: utf-8 -*-
"""Monta vestibular/fuvest/<ANO>.json. Uso: python fuvest_build_json.py <ANO>"""
import json, os, glob, sys
ANO = sys.argv[1] if len(sys.argv) > 1 else "2022"
HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "..", "vestibular", "fuvest", f"{ANO}.json")
extract = {q["numero"]: q for q in json.load(open(os.path.join(HERE,f"_fuvest_extract_{ANO}.json"),encoding="utf-8"))}
auth = json.load(open(os.path.join(HERE,f"_fuvest_gab_{ANO}.json"),encoding="utf-8"))
expl={}
for fp in sorted(glob.glob(os.path.join(HERE,f"_f{ANO}expl_*.json"))):
    for k,v in json.load(open(fp,encoding="utf-8")).items(): expl[int(k)]=v
questoes=[]; anuladas=[]
for n in range(1,91):
    if n not in extract: continue
    q=extract[n]; corr=auth.get(str(n),"X").upper()
    if corr=="ANULADA":
        corr="X"; anuladas.append(n); explic=""; fonte="anulada_inep"
    else:
        explic=expl.get(n,{}).get("explicacao",""); fonte=""
    questoes.append({"numero":n,"ano":int(ANO),"titulo":f"Questão {n} - FUVEST {ANO}",
        "enunciado":q["enunciado"],"alternativas_introducao":"","alternativas":q["alternativas"],
        "imagens_alternativas":[],"imagem_principal":"","imagens_extras":[],
        "correta":corr,"explicacao":explic,"fonte":fonte,"fonte_url":""})
doc={"vestibular":"fuvest","ano":int(ANO),"titulo":f"FUVEST {ANO} - 1ª fase","totalQuestoes":len(questoes),
     "observacao":f"Prova V. Anuladas: {anuladas if anuladas else 'nenhuma'}.","questoes":questoes}
json.dump(doc,open(OUT,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("escrito:",OUT,"| questoes:",len(questoes),"| anuladas:",anuladas)
print("sem expl:",[q["numero"] for q in questoes if q["correta"]!="X" and not q["explicacao"].strip()],
      "| alt!=5:",[(q["numero"],len(q["alternativas"])) for q in questoes if len(q["alternativas"])!=5])
