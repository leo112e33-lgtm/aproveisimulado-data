# -*- coding: utf-8 -*-
"""Extrai questoes da prova V da FUVEST 2023 a partir do texto do PDF oficial,
corrige o artefato de 'letter-spacing' e separa por questao/alternativas."""
import re, json
from pathlib import Path

BASE = Path(r"C:\Users\leo11\AndroidStudioProjects\aproveisimulado-data\vestibular\fuvest")
raw = (BASE / "_prova_v_raw.txt").read_text(encoding="utf-8")
gab = json.loads((BASE / "_gab_v.json").read_text())

def corrige_spacing(linha):
    # Linhas justificadas vem com 1 espaco entre CADA caractere e 2+ espacos
    # entre palavras. Detecta isso e reconstroi.
    toks = linha.split(' ')
    singles = sum(1 for t in toks if len(t) == 1)
    if len(toks) >= 6 and singles >= len(toks) * 0.6:
        # split por 2+ espacos -> palavras; remove espacos simples dentro
        palavras = re.split(r' {2,}', linha.strip())
        return ' '.join(p.replace(' ', '') for p in palavras)
    return linha

linhas = [corrige_spacing(l) for l in raw.split('\n')]
txt = '\n'.join(linhas)
# remove cabecalho/rodape repetido
txt = re.sub(r'Concurso Vestibular FUVEST 2023 .*?PROVA V', '', txt)

# Divide por marcador de questao: linha com numero 01..90 isolado
# (apos um \n e seguido de \n)
partes = re.split(r'\n\s*(\d{2})\s*\n', '\n' + txt)
# partes[0] = lixo antes da Q1; depois alterna numero, conteudo
questoes = {}
for i in range(1, len(partes) - 1, 2):
    num = int(partes[i])
    corpo = partes[i + 1].strip()
    if 1 <= num <= 90:
        questoes[num] = corpo

def parse_alts(corpo):
    # separa enunciado e alternativas (A)..(E)
    m = re.search(r'\n?\(A\)', corpo)
    if not m: return None, None
    enun = corpo[:m.start()].strip()
    resto = corpo[m.start():]
    alts = {}
    for letra in 'ABCDE':
        mm = re.search(r'\(' + letra + r'\)(.*?)(?=\(' + chr(ord(letra)+1) + r'\)|$)', resto, re.S) \
             if letra != 'E' else re.search(r'\(E\)(.*)$', resto, re.S)
        if mm:
            alts[letra] = re.sub(r'\s+', ' ', mm.group(1)).strip()
    return enun, alts

saida = []
for num in range(1, 91):
    if num not in questoes: continue
    enun, alts = parse_alts(questoes[num])
    if not alts or len(alts) < 5: continue
    enun_limpo = re.sub(r'\s+', ' ', enun).strip()
    saida.append({
        "numero": num,
        "correta": gab.get(str(num), "X"),
        "n_alts": len(alts),
        "enun_len": len(enun_limpo),
        "enun": enun_limpo,
        "alts": alts,
    })

(BASE / "_candidatas.json").write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
print("questoes com 5 alternativas parseadas:", len(saida))
print("numeros:", [q["numero"] for q in saida])
