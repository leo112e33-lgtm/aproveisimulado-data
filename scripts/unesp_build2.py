# -*- coding: utf-8 -*-
import re, json, pypdf
from pathlib import Path
ROOT = Path(r"C:\Users\leo11\AndroidStudioProjects\aproveisimulado-data\vestibular\unesp")
GABPDF = r"C:\Users\leo11\.claude\projects\C--Users-leo11\6da471ab-3033-4493-87bd-4350fd5e829b\tool-results\webfetch-1781393762495-lamsfx.pdf"

# gabarito versao 1
txt = "\n".join((pg.extract_text() or "") for pg in pypdf.PdfReader(GABPDF).pages)
gab = {}
for n, l in re.findall(r"(\d{1,2})\s*-\s*([A-E])", txt):
    n = int(n)
    if 1 <= n <= 90 and n not in gab: gab[n] = l
assert len(gab) == 90, len(gab)

draft = json.loads((ROOT / "_enem_draft.json").read_text(encoding="utf-8"))

def clean_text(s):
    blocks = s.split("\n\n")
    out = []
    for b in blocks:
        b = b.strip()
        if not b: continue
        if b.startswith("!["):
            out.append(b); continue
        b = b.replace("-\n", "")            # de-hifeniza quebra de linha
        b = re.sub(r"\s*\n\s*", " ", b)      # junta linhas do paragrafo
        b = re.sub(r"[ \t]+", " ", b).strip()
        if b: out.append(b)
    return "\n\n".join(out)

def clean_alt(a):
    a = a.replace("- ", "")  # de-hifeniza (corpo ja em 1 linha)
    return re.sub(r"\s+", " ", a).strip()

questoes = []
for n in range(1, 91):
    q = draft[str(n)]
    enun = clean_text(q["enun"])
    alts = [clean_alt(a) for a in q["alts"]]
    questoes.append({
        "numero": n, "ano": 2023,
        "titulo": f"Questão {n} - UNESP 2023",
        "enunciado": enun,
        "alternativas_introducao": "",
        "alternativas": alts,
        "imagens_alternativas": [None]*len(alts),
        "imagem_principal": "",
        "imagens_extras": [],
        "correta": gab[n],
        "explicacao": f"**Resposta correta: {gab[n]}.**\n\nUNESP 2023 (1ª fase, versão 1). Resolução comentada completa em curso-objetivo.br.",
        "fonte": "unesp_oficial",
        "fonte_url": "https://www.curso-objetivo.br/vestibular/resolucao-comentada/unesp/2023/1fase/UNESP2023_1fase_prova.pdf",
    })

payload = {
    "vestibular": "UNESP", "ano": 2023,
    "titulo": "UNESP 2023 — 1ª fase (prova completa, versão 1)",
    "totalQuestoes": 90,
    "observacao": "Prova completa da 1ª fase da UNESP 2023 (versão 1): enunciado e alternativas em texto extraídos do PDF oficial; figuras recortadas do caderno oficial. Gabarito oficial da versão 1.",
    "questoes": questoes,
}
(ROOT / "2023.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
n_fig = sum(1 for q in questoes if "![](" in q["enunciado"])
print("unesp/2023.json OK | questoes:", len(questoes), "| com figura:", n_fig)
