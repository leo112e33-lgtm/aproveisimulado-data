# -*- coding: utf-8 -*-
"""
Normaliza explicacoes para o padrao Q91:
  **Por que a alternativa X esta correta:** ...
  [opcional: Por que as outras estao erradas ...]
  **Conceito-chave:** ...

- Garante o cabecalho "Por que a alternativa X ...".
- Renomeia/rotula a secao de conceito existente como "**Conceito-chave:**".
- Aceita textos de conceito escritos a mao (CONCEITOS) para questoes que nao
  possuem nenhuma secao de conceito.
"""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Conceitos escritos manualmente para as questoes sem nenhuma secao de conceito.
# Preenchido em etapas; o que faltar fica vazio e o script avisa.
CONCEITOS = {}

def carregar_conceitos():
    p = ROOT / "scripts" / "conceitos_manuais.json"
    if p.exists():
        CONCEITOS.update(json.loads(p.read_text(encoding="utf-8")))

HDR_CONCEITO = re.compile(
    r'(?im)^\s*#{0,3}\s*\*{0,2}\s*\d*\.?\s*\*{0,2}\s*'
    r'(?:qual\s+(?:o\s+)?conceito|conceito\s+que\s+o\s+aluno)[^\n]*$'
)
INLINE_CONCEITO = re.compile(
    r'(?im)^\s*(?:para\s+acertar|o\s+aluno\s+precisa\s+dominar|'
    r'o\s+conceito\s+fundamental|o\s+conceito-chave|o\s+conceito\s)[^\n]*'
)

def normaliza_porque(exp, correta):
    # tira numeracao dos cabecalhos "1. Por que..." / "2. Por que as outras..."
    exp = re.sub(r'(?im)^\s*#{0,3}\s*\*{0,2}\s*\d+\.\s*\*{0,2}\s*(Por que a alternativa)',
                 r'**\1', exp)
    exp = re.sub(r'(?im)^\s*#{0,3}\s*\*{0,2}\s*\d+\.\s*\*{0,2}\s*(Por que (?:as|cada|todas))',
                 r'**\1', exp)
    # garante o cabecalho inicial se ausente
    if 'Por que a alternativa' not in exp:
        exp = f"**Por que a alternativa {correta} esta correta:**\n" + exp.lstrip()
    return exp

def rotula_conceito(exp, k):
    if 'Conceito-chave' in exp:
        return exp, True
    # 1) cabecalho de secao de conceito -> substitui pela label
    m = HDR_CONCEITO.search(exp)
    if m:
        return exp[:m.start()] + '**Conceito-chave:**' + exp[m.end():], True
    # 2) paragrafo inline de conceito -> prefixa a label
    m = INLINE_CONCEITO.search(exp)
    if m:
        return exp[:m.start()] + '**Conceito-chave:** ' + exp[m.start():], True
    # 3) nada: usa conceito manual, se houver
    if CONCEITOS.get(k):
        return exp.rstrip() + "\n\n**Conceito-chave:** " + CONCEITOS[k].strip(), True
    return exp, False

def main():
    carregar_conceitos()
    falta = json.loads((ROOT/"scripts"/"falta.json").read_text())
    pendentes_conceito = []
    por_arq = {}
    for ano,dia,num in falta:
        por_arq.setdefault((ano,dia),[]).append(num)
    for (ano,dia),nums in por_arq.items():
        arq = ROOT/"enem"/str(ano)/f"dia{dia}.json"
        payload = json.loads(arq.read_text(encoding="utf-8"))
        idx = {q["numero"]:q for q in payload["questoes"]}
        for num in nums:
            q = idx[num]; k=f"{ano}_{dia}_{num}"
            exp = q.get("explicacao","") or ""
            exp = normaliza_porque(exp, q.get("correta","X"))
            exp, ok = rotula_conceito(exp, k)
            q["explicacao"] = exp
            if not ok: pendentes_conceito.append(k)
        arq.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("normalizado. ainda sem conceito (precisam de texto manual):", len(pendentes_conceito))
    print(pendentes_conceito)

if __name__ == "__main__":
    main()
