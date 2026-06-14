# -*- coding: utf-8 -*-
"""Monta vestibular/unicamp/2023.json (formato ENEM) a partir de:
- _unicamp_extract.json (enunciado, alternativas, figuras inline)
- _unicamp_especiais.json (Q33/Q51 imagem; Q72 imagens_alternativas)
- _unicamp_gab_autoritativo.json (correta; ANULADA -> X)
- _uexpl_*.json + _uregen_*.json (explicacoes; regen sobrescreve)"""
import json, os, re, glob
HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "..", "vestibular", "unicamp", "2023.json")

extract = {q["numero"]: q for q in json.load(open(os.path.join(HERE,"_unicamp_extract.json"),encoding="utf-8"))}
esp = json.load(open(os.path.join(HERE,"_unicamp_especiais.json"),encoding="utf-8"))
auth = json.load(open(os.path.join(HERE,"_unicamp_gab_autoritativo.json"),encoding="utf-8"))

# explicacoes: base (agg) + regen sobrescreve
expl = {}
for fp in sorted(glob.glob(os.path.join(HERE,"_uexpl_*.json"))):
    for k,v in json.load(open(fp,encoding="utf-8")).items():
        expl[int(k)] = v
for fp in sorted(glob.glob(os.path.join(HERE,"_uregen_*.json"))):
    for k,v in json.load(open(fp,encoding="utf-8")).items():
        expl[int(k)] = v  # sobrescreve

def strip_figs(s):
    return re.sub(r"\n*!\[\]\([^)]*\)\n*", "\n", s).strip()

questoes = []
anuladas = []
for n in range(1,73):
    q = extract[n]
    enun = q["enunciado"]
    alts = list(q["alternativas"])
    imgs_alt = []
    img_princ = ""
    e = esp.get(str(n))
    if e:
        if e.get("imagens_alternativas"):
            imgs_alt = e["imagens_alternativas"]
            alts = e["alternativas"]
            enun = strip_figs(enun)  # Q72: remove os 4 graficos do enunciado
        if e.get("imagem_principal"):
            alts = e["alternativas"]
            # Q33 e Q51: a imagem completa ja contem enunciado + alternativas em
            # formula -> usar so a imagem (evita duplicar o enunciado em texto).
            enun = "![](" + e["imagem_principal"] + ")"
    corr = auth.get(str(n),"X").upper()
    if corr == "ANULADA":
        corr = "X"; anuladas.append(n)
        explic = ""
        fonte = "anulada_inep"
    else:
        explic = expl.get(n,{}).get("explicacao","")
        fonte = ""
    questoes.append({
        "numero": n,
        "ano": 2023,
        "titulo": f"Questão {n} - UNICAMP 2023",
        "enunciado": enun,
        "alternativas_introducao": "",
        "alternativas": alts,
        "imagens_alternativas": imgs_alt,
        "imagem_principal": img_princ,
        "imagens_extras": [],
        "correta": corr,
        "explicacao": explic,
        "fonte": fonte,
        "fonte_url": ""
    })

doc = {
    "vestibular": "unicamp",
    "ano": 2023,
    "titulo": "UNICAMP 2023 - 1ª fase (Conhecimentos Gerais)",
    "totalQuestoes": 72,
    "observacao": "Caderno Q/Z. Questões 3 e 23 anuladas pela banca.",
    "questoes": questoes
}
json.dump(doc, open(OUT,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
print("escrito:", OUT)
print("anuladas:", anuladas)
# validacao
semexpl = [q["numero"] for q in questoes if q["correta"]!="X" and not q["explicacao"].strip()]
print("sem explicacao (nao anuladas):", semexpl)
nalt = [(q["numero"],len(q["alternativas"])) for q in questoes if len(q["alternativas"])!=4]
print("alternativas != 4:", nalt)
