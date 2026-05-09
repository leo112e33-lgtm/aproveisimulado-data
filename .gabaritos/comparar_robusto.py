"""
Verificacao robusta. Para cada questao do JSON, extrai uma frase-chave
unica do enunciado e busca no PDF da prova oficial. Se a frase nao aparece
em nenhum lugar, eh candidato a texto trocado.
"""
from __future__ import annotations
import json, re, unicodedata
from pathlib import Path
import pymupdf

ROOT = Path(__file__).resolve().parent.parent

def normaliza(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = s.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", s)).strip()

def melhor_frase(json_txt: str) -> list[str]:
    """Retorna lista de 3 'fingerprints' do enunciado: 4-grams de palavras
    longas. Se algum delas aparecer no PDF, considera-se texto certo."""
    palavras = [w for w in normaliza(json_txt).split() if len(w) >= 5]
    if len(palavras) < 4:
        return []
    candidatos = []
    # Pegar 4-grams de inicio, meio e fim
    for idx in (0, len(palavras)//2, len(palavras)-4):
        if idx >= 0 and idx + 4 <= len(palavras):
            candidatos.append(" ".join(palavras[idx:idx+4]))
    return candidatos

def texto_pdf(pdf_path: Path) -> str:
    doc = pymupdf.open(pdf_path)
    chunks = [doc[i].get_text() for i in range(len(doc))]
    doc.close()
    return normaliza("\n".join(chunks))

def comparar(ano: int, dia: int):
    pdf_path = ROOT / ".provas" / f"{ano}_d{dia}.pdf"
    if not pdf_path.exists():
        return []
    pdf_normal = texto_pdf(pdf_path)
    arq = ROOT / "enem" / str(ano) / f"dia{dia}.json"
    d = json.loads(arq.read_text(encoding="utf-8"))
    suspeitos = []
    for q in d["questoes"]:
        n = q["numero"]
        json_txt = (q.get("enunciado","") or "") + " " + (q.get("alternativas_introducao","") or "")
        if not json_txt.strip():
            continue
        fingerprints = melhor_frase(json_txt)
        if not fingerprints:
            continue
        # Se NENHUMA das 3 fingerprints aparece no PDF, eh suspeito
        achou = any(fp in pdf_normal for fp in fingerprints)
        if not achou:
            suspeitos.append((n, fingerprints, json_txt[:140].replace("\n"," ")))
    return suspeitos

def main():
    total = 0
    for ano in (2018, 2019, 2020, 2021, 2022, 2023):
        for dia in (1, 2):
            sus = comparar(ano, dia)
            if sus:
                print(f"\n=== ENEM {ano} dia {dia} — {len(sus)} suspeito(s) REAIS ===")
                for n, fps, t in sus:
                    print(f"  Q{n}")
                    print(f"    fingerprints: {fps}")
                    print(f"    JSON: {t!r}")
                total += len(sus)
    print(f"\nTotal: {total}")

if __name__ == "__main__":
    main()
