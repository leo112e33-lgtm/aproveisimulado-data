"""
Compara o enunciado de cada questao no JSON com o texto extraido da prova
oficial INEP. Identifica casos de texto trocado.

Estrategia: extrair todo texto do PDF, identificar marcadores "QUESTAO N",
isolar bloco de texto entre QUESTAO N e QUESTAO N+1, e comparar primeiras
palavras com o enunciado do JSON pela presenca de N-grams (trigrams de
palavras consecutivas com 4+ letras).
"""
from __future__ import annotations
import json, re, unicodedata
from pathlib import Path
import pymupdf

ROOT = Path(__file__).resolve().parent.parent

def normaliza(s: str) -> str:
    """Lowercase, remove acentos, remove pontuacao."""
    s = unicodedata.normalize("NFD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def trigrams(text: str, min_len: int = 4) -> set:
    """Conjunto de trigrams de palavras com >=min_len chars."""
    palavras = [w for w in normaliza(text).split() if len(w) >= min_len]
    return set(zip(palavras, palavras[1:], palavras[2:]))

def extrair_questoes_pdf(pdf_path: Path) -> dict:
    """Retorna {numero: texto_da_questao} extraido do PDF."""
    doc = pymupdf.open(pdf_path)
    todo = []
    for i in range(len(doc)):
        todo.append(doc[i].get_text())
    doc.close()
    full = "\n".join(todo)
    # Marcadores "QUESTAO 91" / "QUESTAO 1" etc.
    # No PDF original aparece "QUESTÃO" maiusculo
    # Capturar numero apos "QUESTÃO " e o texto seguinte
    parts = re.split(r"QUEST[AÃÄ]O\s+(\d+)", full)
    # parts: [pre, num, body, num, body, ...]
    out = {}
    for k in range(1, len(parts) - 1, 2):
        num = int(parts[k])
        body = parts[k+1]
        # cortar onde comeca a proxima questao (caso regex nao tenha capturado)
        m = re.search(r"QUEST[AÃÄ]O\s+\d+", body)
        if m:
            body = body[:m.start()]
        out[num] = body[:1500]
    return out

def comparar(ano: int, dia: int):
    pdf = ROOT / ".provas" / f"{ano}_d{dia}.pdf"
    if not pdf.exists():
        return []
    pdf_q = extrair_questoes_pdf(pdf)
    arq = ROOT / "enem" / str(ano) / f"dia{dia}.json"
    d = json.loads(arq.read_text(encoding="utf-8"))
    suspeitos = []
    for q in d["questoes"]:
        n_json = q["numero"]
        # No dia 2, oficial = JSON + 90
        n_oficial = n_json if dia == 1 else n_json + 90
        json_txt = (q.get("enunciado","") or "") + " " + (q.get("alternativas_introducao","") or "")
        if not json_txt.strip():
            continue
        pdf_txt = pdf_q.get(n_oficial, "")
        if not pdf_txt:
            continue
        # Comparar trigrams
        json_tri = trigrams(json_txt)
        pdf_tri = trigrams(pdf_txt)
        if not json_tri:
            continue
        comum = json_tri & pdf_tri
        sim = len(comum) / max(len(json_tri), 1)
        if sim < 0.15:  # baixa similaridade
            suspeitos.append((n_json, sim, json_txt[:140].replace("\n"," "), pdf_txt[:140].replace("\n"," ")))
    return suspeitos

def main():
    casos = []
    for ano in (2018, 2019, 2020, 2021, 2022, 2023):
        for dia in (1, 2):
            sus = comparar(ano, dia)
            if sus:
                print(f"\n=== ENEM {ano} dia {dia} — {len(sus)} suspeito(s) ===")
                for n, sim, j, p in sus:
                    print(f"  Q{n} (sim={sim:.2f})")
                    print(f"    JSON: {j!r}")
                    print(f"    PDF : {p!r}")
                    casos.append((ano, dia, n, sim))
    print(f"\nTotal casos suspeitos: {len(casos)}")

if __name__ == "__main__":
    main()
