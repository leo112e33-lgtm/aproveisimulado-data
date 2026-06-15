# -*- coding: utf-8 -*-
"""Monta vestibular/unicamp/<ANO>.json (formato ENEM). Uso: python unicamp_build_json.py <ANO>
Fontes: _unicamp_extract_<ANO>.json, _unicamp_especiais_<ANO>.json (opcional),
_unicamp_gab_autoritativo_<ANO>.json, _u<ANO>expl_*.json (ou _uexpl_*.json p/ 2023)."""
import json, os, re, glob, sys
ANO = sys.argv[1] if len(sys.argv) > 1 else "2023"
HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "..", "vestibular", "unicamp", f"{ANO}.json")

extract = {q["numero"]: q for q in json.load(open(os.path.join(HERE,f"_unicamp_extract_{ANO}.json"),encoding="utf-8"))}
esp_path = os.path.join(HERE,f"_unicamp_especiais_{ANO}.json")
esp = json.load(open(esp_path,encoding="utf-8")) if os.path.exists(esp_path) else {}
auth = json.load(open(os.path.join(HERE,f"_unicamp_gab_autoritativo_{ANO}.json"),encoding="utf-8"))

expl = {}
pat = os.path.join(HERE, f"_u{ANO}expl_*.json")
for fp in sorted(glob.glob(pat)):
    for k,v in json.load(open(fp,encoding="utf-8")).items(): expl[int(k)] = v

def strip_figs(s): return re.sub(r"\n*!\[\]\([^)]*\)\n*","\n",s).strip()

questoes=[]; anuladas=[]
for n in range(1,73):
    if n not in extract: continue
    q=extract[n]; enun=q["enunciado"]; alts=list(q["alternativas"])
    e=esp.get(str(n))
    if e and e.get("imagem_principal"):
        enun = "![](" + e["imagem_principal"] + ")"  # questao inteira como imagem
        alts = e["alternativas"]
    corr=auth.get(str(n),"X").upper()
    if corr=="ANULADA":
        corr="X"; anuladas.append(n); explic=""; fonte="anulada_inep"
    else:
        explic=expl.get(n,{}).get("explicacao",""); fonte=""
    questoes.append({"numero":n,"ano":int(ANO),"titulo":f"Questão {n} - UNICAMP {ANO}",
        "enunciado":enun,"alternativas_introducao":"","alternativas":alts,
        "imagens_alternativas":[],"imagem_principal":"","imagens_extras":[],
        "correta":corr,"explicacao":explic,"fonte":fonte,"fonte_url":""})

doc={"vestibular":"unicamp","ano":int(ANO),
     "titulo":f"UNICAMP {ANO} - 1ª fase (Conhecimentos Gerais)","totalQuestoes":len(questoes),
     "observacao":f"Caderno conforme PDF oficial. Anuladas: {anuladas if anuladas else 'nenhuma'}.",
     "questoes":questoes}
json.dump(doc,open(OUT,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("escrito:",OUT,"| questoes:",len(questoes),"| anuladas:",anuladas)
semexpl=[q["numero"] for q in questoes if q["correta"]!="X" and not q["explicacao"].strip()]
nalt=[(q["numero"],len(q["alternativas"])) for q in questoes if len(q["alternativas"])!=4]
print("sem explicacao:",semexpl,"| alt!=4:",nalt)
