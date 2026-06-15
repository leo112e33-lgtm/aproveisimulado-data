# -*- coding: utf-8 -*-
"""Monta vestibular/unesp/<ANO>.json (pipeline de TEXTO). Uso: python unesp_build_text.py <ANO>"""
import json, os, glob, sys
ANO = sys.argv[1] if len(sys.argv) > 1 else "2022"
HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "..", "vestibular", "unesp", f"{ANO}.json")
extract = {q["numero"]: q for q in json.load(open(os.path.join(HERE,f"_unesp_extract_{ANO}.json"),encoding="utf-8"))}
esp_p = os.path.join(HERE,f"_unesp_especiais_{ANO}.json")
esp = json.load(open(esp_p,encoding="utf-8")) if os.path.exists(esp_p) else {}
auth = json.load(open(os.path.join(HERE,f"_unesp_gab_autoritativo_{ANO}.json"),encoding="utf-8"))
expl={}
for fp in sorted(glob.glob(os.path.join(HERE,f"_unesp{ANO}expl_*.json"))):
    for k,v in json.load(open(fp,encoding="utf-8")).items(): expl[int(k)]=v
questoes=[]; anuladas=[]
for n in range(1,91):
    if n not in extract: continue
    q=extract[n]; enun=q["enunciado"]; alts=list(q["alternativas"])
    e=esp.get(str(n))
    if e and e.get("imagem_principal"):
        enun="![]("+e["imagem_principal"]+")"; alts=e["alternativas"]
    corr=auth.get(str(n),"X").upper()
    if corr=="ANULADA":
        corr="X"; anuladas.append(n); explic=""; fonte="anulada_inep"
    else:
        explic=expl.get(n,{}).get("explicacao",""); fonte=""
    questoes.append({"numero":n,"ano":int(ANO),"titulo":f"Questão {n} - UNESP {ANO}",
        "enunciado":enun,"alternativas_introducao":"","alternativas":alts,
        "imagens_alternativas":[],"imagem_principal":"","imagens_extras":[],
        "correta":corr,"explicacao":explic,"fonte":fonte,"fonte_url":""})
doc={"vestibular":"unesp","ano":int(ANO),"titulo":f"UNESP {ANO} - 1ª fase","totalQuestoes":len(questoes),
     "observacao":f"Prova objetiva. Anuladas: {anuladas if anuladas else 'nenhuma'}.","questoes":questoes}
json.dump(doc,open(OUT,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("escrito:",OUT,"| questoes:",len(questoes),"| anuladas:",anuladas)
print("sem expl:",[q["numero"] for q in questoes if q["correta"]!="X" and not q["explicacao"].strip()],
      "| alt!=5:",[(q["numero"],len(q["alternativas"])) for q in questoes if len(q["alternativas"])!=5])
