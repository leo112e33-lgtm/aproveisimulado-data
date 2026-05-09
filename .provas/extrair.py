"""
Extrai paginas especificas das provas oficiais INEP como PNG, para revisao visual.
"""
import pymupdf
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def extrair_paginas(pdf_path, paginas, prefixo):
    doc = pymupdf.open(pdf_path)
    out_dir = ROOT / "imagens"
    out_dir.mkdir(exist_ok=True)
    for p in paginas:
        if p < 1 or p > len(doc):
            print(f"  [skip] pagina {p} fora do range (total {len(doc)})")
            continue
        pix = doc[p-1].get_pixmap(dpi=150)
        out = out_dir / f"{prefixo}_p{p:02d}.png"
        pix.save(out)
        print(f"  -> {out.name}  ({pix.width}x{pix.height})")
    doc.close()

# Pre-listei aproximadamente onde cada questao aparece nos PDFs.
# Vou extrair paginas variadas para encontrar as questoes alvo.
TASKS = [
    ("2018_d1.pdf", "2018d1", [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]),
]

if __name__ == "__main__":
    for f, prefix, paginas in TASKS:
        pdf = ROOT / f
        if pdf.exists():
            print(f"=== {f} ({len(paginas)} paginas) ===")
            extrair_paginas(pdf, paginas, prefix)
