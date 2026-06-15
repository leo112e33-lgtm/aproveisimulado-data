# -*- coding: utf-8 -*-
"""Monta desafios/desafios.json a partir dos arquivos de staging gerados pelos
agentes (um por materia) e valida a estrutura."""
import json, os, sys

STAGING = r"C:\Users\leo11\desafios_staging"
OUT = os.path.join(os.path.dirname(__file__), "..", "desafios", "desafios.json")

ORDEM = ["quimica", "matematica", "fisica", "biologia", "portugues", "geografia", "historia"]

GEO_NV = {0:1,1:2,2:2,3:3,4:1,5:3,6:2,7:2,8:1,9:3,10:1,11:2,12:2}

def valida_fig(fig, ctx, probs):
    t = fig.get("t")
    if t == "geo":
        i = fig.get("i"); v = fig.get("v")
        if not isinstance(i,int) or i not in GEO_NV: probs.append(f"{ctx}: fig geo i invalido {i}")
        elif not isinstance(v,list) or len(v)!=GEO_NV[i]: probs.append(f"{ctx}: fig geo v tamanho!={GEO_NV[i]}")
    elif t == "fis":
        i = fig.get("i"); v = fig.get("v")
        if i not in (0,1,3,4,5,6): probs.append(f"{ctx}: fig fis i invalido {i}")
        elif not isinstance(v,list): probs.append(f"{ctx}: fig fis v ausente")
    elif t == "mol":
        for k in ("nC","lig","f"):
            if not isinstance(fig.get(k),int): probs.append(f"{ctx}: fig mol {k} invalido")
    else:
        probs.append(f"{ctx}: fig tipo desconhecido {t}")

def main():
    materias = []
    probs = []
    total = 0
    for chave in ORDEM:
        path = os.path.join(STAGING, chave + ".json")
        if not os.path.exists(path):
            probs.append(f"FALTA arquivo {chave}.json"); continue
        with open(path, encoding="utf-8") as f:
            mat = json.load(f)
        nome = mat.get("nome","?")
        topicos = mat.get("topicos",[])
        if len(topicos) != 5:
            probs.append(f"{nome}: {len(topicos)} topicos (esperado 5)")
        for tp in topicos:
            des = tp.get("desafios",[])
            tnome = tp.get("nome","?")
            if len(des) != 20:
                probs.append(f"{nome}/{tnome}: {len(des)} desafios (esperado 20)")
            for k,d in enumerate(des):
                ctx = f"{nome}/{tnome}#{k+1}"
                if not d.get("p"): probs.append(f"{ctx}: sem pergunta")
                alt = d.get("alt",[])
                if not isinstance(alt,list) or len(alt)!=4: probs.append(f"{ctx}: alt!=4")
                c = d.get("c")
                if not isinstance(c,int) or c<0 or c>3: probs.append(f"{ctx}: c invalido {c}")
                if not d.get("e"): probs.append(f"{ctx}: sem explicacao")
                if "fig" in d and d["fig"] is not None: valida_fig(d["fig"], ctx, probs)
                total += 1
        materias.append(mat)

    banco = {"versao": 1, "materias": materias}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(banco, f, ensure_ascii=False, indent=1)

    # distribuicao das corretas (sanidade: nao deve ser tudo 0)
    dist = {0:0,1:0,2:0,3:0}
    for mat in materias:
        for tp in mat["topicos"]:
            for d in tp["desafios"]:
                c=d.get("c")
                if c in dist: dist[c]+=1

    print(f"Materias: {len(materias)} | Total desafios: {total}")
    print(f"Distribuicao corretas A/B/C/D: {dist}")
    if probs:
        print(f"\n{len(probs)} PROBLEMAS:")
        for p in probs[:60]:
            print(" -", p)
    else:
        print("0 problemas. desafios.json gravado:", os.path.abspath(OUT))

if __name__ == "__main__":
    main()
