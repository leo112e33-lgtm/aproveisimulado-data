# -*- coding: utf-8 -*-
"""Corrige textos-base compartilhados ('TEXTO PARA AS QUESTOES X E Y') que vazam
no fim do bloco da questao anterior. Remove o vazamento e anexa o texto-base ao
enunciado de cada questao do grupo. Opera sobre _fuvest_extract_<ANO>.json.
Uso: python fuvest_fix_textbase.py <ANO>"""
import json, re, os, sys
ANO = sys.argv[1]
HERE = os.path.dirname(__file__)
EXP = os.path.join(HERE, f"_fuvest_extract_{ANO}.json")
data = json.load(open(EXP, encoding="utf-8"))
ex = {q["numero"]: q for q in data}

LABEL = re.compile(r"TEXTO PARA\s+(?:AS\s+)?QUEST(?:[ÕO]ES|[ÃA]O)\s+(\d{1,2})\s*(?:e|E|a|A|à|até)\s*(\d{1,2})")
HEADER = re.compile(r"Concurso Vestibular FUVEST\s*\d{4}\s*-?\s*Prova\s*\w*", re.I)

def clean(s):
    s = HEADER.sub(" ", s)
    s = s.replace("#####", " ")
    s = re.sub(r"\n\s*\d{1,3}\s*\n", "\n", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

fixes = []
for q in data:
    blob = q["enunciado"] + "\n@@ALT@@\n" + "\n@@ALT@@\n".join(q["alternativas"])
    m = LABEL.search(blob)
    if not m:
        continue
    a, b = int(m.group(1)), int(m.group(2))
    membros = list(range(a, b + 1))
    base = clean(blob[m.end():])          # texto-base = tudo apos o rotulo
    # remove o vazamento da questao de origem: corta em "TEXTO PARA..."
    cut = m.start()
    head = blob[:cut]
    parts = head.split("\n@@ALT@@\n")
    q["enunciado"] = clean(parts[0])
    q["alternativas"] = [clean(p) for p in parts[1:]] if len(parts) > 1 else q["alternativas"]
    # anexa base aos membros
    for n in membros:
        if n in ex:
            pref = f"**Texto para as questões {a} e {b}:**\n{base}\n\n" if len(membros)==2 else f"**Texto para as questões {a} a {b}:**\n{base}\n\n"
            ex[n]["enunciado"] = pref + ex[n]["enunciado"]
    fixes.append((q["numero"], membros, len(base)))

json.dump(data, open(EXP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("FUVEST", ANO, "| textos-base corrigidos:")
for src, mem, ln in fixes:
    print(f"  origem Q{src} -> grupo {mem} (base {ln} chars)")
