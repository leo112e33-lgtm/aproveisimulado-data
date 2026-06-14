# -*- coding: utf-8 -*-
"""Mescla os JSONs _expl_*.json (explicacoes Q21-90 geradas pelos agentes) no
fuvest/2023.json. Valida formato Q91 e a letra correta. Idempotente."""
import json, os, re, glob

HERE = os.path.dirname(__file__)
FU = os.path.join(HERE, "..", "vestibular", "fuvest", "2023.json")

def main():
    d = json.load(open(FU, encoding="utf-8"))
    qs = {q["numero"]: q for q in d["questoes"]}

    expl = {}
    for fp in sorted(glob.glob(os.path.join(HERE, "_expl_*.json"))):
        data = json.load(open(fp, encoding="utf-8"))
        for k, v in data.items():
            expl[int(k)] = v
        print(f"carregado {os.path.basename(fp)}: {len(data)} questoes")

    aplicadas = 0
    problemas = []
    for n in range(21, 91):
        if n not in expl:
            problemas.append(f"Q{n}: SEM explicacao gerada")
            continue
        texto = expl[n].strip()
        correta = qs[n].get("correta", "X")
        # validacao de formato Q91
        if not texto.startswith("**Por que a alternativa"):
            problemas.append(f"Q{n}: nao comeca com '**Por que a alternativa'")
        if "Conceito-chave" not in texto:
            problemas.append(f"Q{n}: falta 'Conceito-chave'")
        # confere se a letra citada bate com a correta oficial
        m = re.match(r"\*\*Por que a alternativa ([A-E])", texto)
        if m and correta in "ABCDE" and m.group(1) != correta:
            problemas.append(f"Q{n}: letra citada {m.group(1)} != correta {correta}")
        qs[n]["explicacao"] = texto
        aplicadas += 1

    json.dump(d, open(FU, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n=== {aplicadas} explicacoes aplicadas ===")
    if problemas:
        print(f"--- {len(problemas)} PROBLEMAS ---")
        for p in problemas:
            print(" ", p)
    else:
        print("Sem problemas de validacao.")

if __name__ == "__main__":
    main()
