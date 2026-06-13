# -*- coding: utf-8 -*-
import re, json, pypdf
from pathlib import Path

BASE = Path(r"C:\Users\leo11\AndroidStudioProjects\aproveisimulado-data\vestibular\unesp")
GABPDF = r"C:\Users\leo11\.claude\projects\C--Users-leo11\6da471ab-3033-4493-87bd-4350fd5e829b\tool-results\webfetch-1781393762495-lamsfx.pdf"

# 1) gabarito (VERSAO 1)
txt = "\n".join((pg.extract_text() or "") for pg in pypdf.PdfReader(GABPDF).pages)
gab = {}
for n, l in re.findall(r"(\d{1,2})\s*-\s*([A-E])", txt):
    n = int(n)
    if 1 <= n <= 90 and n not in gab:
        gab[n] = l
assert len(gab) == 90, f"gabarito incompleto: {len(gab)}"

# 2) base images por questao
meta = json.loads((BASE / "img" / "_meta.json").read_text())
base_img = {int(k): v for k, v in meta["base_img"].items()}

# 3) monta questoes
IMGBASE = "vestibular/unesp/img/"
questoes = []
for n in range(1, 91):
    imgs = []
    if n in base_img:
        imgs.append("![](" + IMGBASE + base_img[n] + ")")
    imgs.append("![](" + IMGBASE + f"2023_q{n:02d}.png" + ")")
    enun = "\n\n".join(imgs)
    questoes.append({
        "numero": n,
        "ano": 2023,
        "titulo": f"Questão {n} - UNESP 2023",
        "enunciado": enun,
        "alternativas_introducao": "",
        "alternativas": ["A", "B", "C", "D", "E"],
        "imagens_alternativas": [None]*5,
        "imagem_principal": "",
        "imagens_extras": [],
        "correta": gab[n],
        "explicacao": f"**Resposta correta: {gab[n]}.**\n\nUNESP 2023 (1ª fase, versão 1). Veja a resolução comentada completa em curso-objetivo.br.",
        "fonte": "unesp_oficial",
        "fonte_url": "https://www.curso-objetivo.br/vestibular/resolucao-comentada/unesp/2023/1fase/UNESP2023_1fase_prova.pdf",
    })

payload = {
    "vestibular": "UNESP",
    "ano": 2023,
    "titulo": "UNESP 2023 — 1ª fase (prova completa, versão 1)",
    "totalQuestoes": 90,
    "observacao": "Prova completa da 1ª fase da UNESP 2023 (versão 1), com cada questão renderizada como imagem do caderno oficial (inclui todas as figuras). Gabarito oficial da versão 1.",
    "questoes": questoes,
}
(BASE / "2023.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
print("unesp/2023.json:", len(questoes), "questoes | gabarito 1-10:", [gab[i] for i in range(1,11)])
