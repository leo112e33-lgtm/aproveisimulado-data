# -*- coding: utf-8 -*-
"""Remove figuras de Geometria (Matematica) que rotulam um valor ausente do
enunciado — sinal de que a figura esta mostrando a propria RESPOSTA (ex.: a
hipotenusa pedida, ou o lado de um quadrado dado pela area)."""
import json, os, re

STAGING = r"C:\Users\leo11\desafios_staging"
path = os.path.join(STAGING, "matematica.json")
d = json.load(open(path, encoding="utf-8"))

def num_no_enunciado(valor, p):
    # casa o numero como token isolado (evita 6 casar dentro de 16)
    if float(valor).is_integer():
        s = str(int(valor))
    else:
        s = str(valor).rstrip("0").rstrip(".")
    # aceita 9 ou 9,0 / 9.0 no texto; e separadores de milhar ignorados
    return re.search(r"(?<!\d)" + re.escape(s) + r"(?:[.,]0+)?(?!\d)", p) is not None

removidos = []
for tp in d["topicos"]:
    if tp["nome"] != "Geometria":
        continue
    for x in tp["desafios"]:
        fig = x.get("fig")
        if not fig or fig.get("t") != "geo":
            continue
        v = fig.get("v", [])
        faltando = [val for val in v if not num_no_enunciado(val, x["p"])]
        if faltando:
            x.pop("fig", None)
            removidos.append(f"v={v} faltando={faltando} | {x['p'][:70]}")

json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
restantes = sum(1 for tp in d["topicos"] if tp["nome"]=="Geometria"
                for x in tp["desafios"] if x.get("fig"))
print(f"Removidas {len(removidos)} figuras geo; restam {restantes} em Geometria.")
for r in removidos:
    print(" -", r)
