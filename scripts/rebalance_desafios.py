# -*- coding: utf-8 -*-
"""Reequilibra a posicao da alternativa correta (A/B/C/D) nos arquivos de
staging que NAO citam alternativas por letra na explicacao. Para cada desafio
seguro, recoloca a correta em posicao round-robin (distribuicao uniforme),
preservando o conteudo das alternativas. Pula desafios que citem letras."""
import json, os, re

STAGING = r"C:\Users\leo11\desafios_staging"
ALVOS = ["matematica", "portugues", "geografia"]

# detecta citacao por letra que quebraria se embaralhassemos
LETRA = re.compile(r"\([A-D]\)|\b[A-D]\s*\(|letra\s+[A-D]|alternativa\s+[A-D]|item\s+[A-D]", re.I)

def cita_letra(e):
    return bool(LETRA.search(e or ""))

def main():
    for chave in ALVOS:
        path = os.path.join(STAGING, chave + ".json")
        d = json.load(open(path, encoding="utf-8"))
        alvo = 0           # posicao destino round-robin
        mexidos = 0; pulados = 0
        for tp in d["topicos"]:
            for x in tp["desafios"]:
                if cita_letra(x.get("e","")):
                    pulados += 1
                    continue
                alts = x["alt"]; c = x["c"]
                if not (isinstance(alts, list) and len(alts) == 4 and 0 <= c <= 3):
                    pulados += 1; continue
                correta = alts[c]
                outras = [a for i, a in enumerate(alts) if i != c]
                pos = alvo % 4
                nova = []
                it = iter(outras)
                for i in range(4):
                    nova.append(correta if i == pos else next(it))
                x["alt"] = nova
                x["c"] = pos
                alvo += 1
                mexidos += 1
        json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        # nova distribuicao
        dist = {0:0,1:0,2:0,3:0}
        for tp in d["topicos"]:
            for x in tp["desafios"]: dist[x["c"]] += 1
        print(f"{chave:11} reequilibrados={mexidos} pulados={pulados} -> A={dist[0]} B={dist[1]} C={dist[2]} D={dist[3]}")

if __name__ == "__main__":
    main()
