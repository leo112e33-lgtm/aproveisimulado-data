# -*- coding: utf-8 -*-
import fitz, re, os
PDF = r"C:\Users\leo11\.claude\projects\C--Users-leo11\6da471ab-3033-4493-87bd-4350fd5e829b\tool-results\webfetch-1781392739634-9mu28i.pdf"
OUT = r"C:\Users\leo11\AndroidStudioProjects\aproveisimulado-data\vestibular\_teste"
os.makedirs(OUT, exist_ok=True)
d = fitz.open(PDF)

# acha pagina/coluna da QUESTAO 01
pg = d[2]            # sabemos que Q01 esta na pag index 2, col esquerda
W = pg.rect.width; mid = W/2

# 1) texto da coluna esquerda da pagina (Q01 ate base "Para responder")
txt = pg.get_text()
print("=== TEXTO BRUTO (inicio) ===")
print(txt[:900].encode("ascii", "replace").decode())

# 2) imagens embutidas na pagina e seus retangulos
print("\n=== IMAGENS NA PAGINA 2 ===")
for img in pg.get_images(full=True):
    xref = img[0]
    rects = pg.get_image_rects(xref)
    for r in rects:
        print("xref", xref, "rect", [round(v) for v in r], "w", round(r.width), "h", round(r.height))
