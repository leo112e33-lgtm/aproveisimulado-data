# -*- coding: utf-8 -*-
"""Remove figuras de Fisica que nao representam a pergunta:
- Cinematica: o catalogo 'fis' so tem diagramas de forca/vetor (nao ha diagrama
  de cinematica), entao qualquer fig em Cinematica e enganosa.
- Demais topicos: se a figura implica uma massa (i in 3,4,6 -> v[0]=massa) e essa
  massa NAO aparece como '<m> kg' no enunciado, a massa foi inventada -> remove."""
import json, os, re

STAGING = r"C:\Users\leo11\desafios_staging"
path = os.path.join(STAGING, "fisica.json")
d = json.load(open(path, encoding="utf-8"))

MASSA_I = {3, 4, 6}   # i cujo v[0] e massa em kg
removidos = []

for tp in d["topicos"]:
    nome = tp["nome"]
    for x in tp["desafios"]:
        fig = x.get("fig")
        if not fig:
            continue
        motivo = None
        if nome == "Cinemática":
            motivo = "cinematica sem diagrama proprio"
        elif fig.get("i") in MASSA_I:
            v = fig.get("v", [])
            if v:
                m = v[0]
                ms = str(int(m)) if float(m).is_integer() else str(m)
                if (ms + " kg") not in x["p"] and (ms + "kg") not in x["p"]:
                    motivo = f"massa {ms} kg ausente no enunciado"
        if motivo:
            x.pop("fig", None)
            removidos.append(f"{nome}: {x['p'][:60]}  [{motivo}]")

json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

restantes = sum(1 for tp in d["topicos"] for x in tp["desafios"] if x.get("fig"))
print(f"Removidas {len(removidos)} figuras; restam {restantes} figuras em Fisica.")
for r in removidos:
    print(" -", r)
