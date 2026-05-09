"""
05_corrigir_imagens.py
======================
Corrige problemas de imagens no dataset:

1. Quando uma questao tem `imagem_principal` populada E o enunciado contem
   uma tag markdown de imagem `![](URL)`, remove a PRIMEIRA tag (assume que
   e duplicata da imagem principal). Demais tags (formulas, simbolos
   pequenos) sao mantidas inline.

2. Quando o enunciado contem o "broken-image.svg" do enem.dev, remove.

3. Limpa whitespace excessivo e linhas em branco resultantes do passo 1.

Uso:
    python scripts/05_corrigir_imagens.py
    python scripts/05_corrigir_imagens.py --anos 2023 --dias 1
"""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENEM_DIR = ROOT / "enem"

MD_IMAGE = re.compile(r"!\[(?:[^\]]*)?\]\(([^)\s]+)\)")
BROKEN_IMG = "https://enem.dev/broken-image.svg"


def limpar_enunciado(enunciado: str, tem_imagem_principal: bool) -> str:
    if not enunciado:
        return enunciado

    # Remove referencias a broken-image
    enunciado = enunciado.replace(f"![]({BROKEN_IMG})", "")
    enunciado = enunciado.replace(BROKEN_IMG, "")

    # Se tem imagem principal, remove a PRIMEIRA tag de imagem markdown
    # (geralmente e a duplicata da imagem principal).
    if tem_imagem_principal:
        m = MD_IMAGE.search(enunciado)
        if m:
            enunciado = enunciado[:m.start()] + enunciado[m.end():]

    # Limpa linhas em branco excessivas
    enunciado = re.sub(r"\n{3,}", "\n\n", enunciado)
    enunciado = enunciado.strip()
    return enunciado


def processar_arquivo(arquivo: Path) -> int:
    dados = json.loads(arquivo.read_text(encoding="utf-8"))
    mudancas = 0

    for q in dados["questoes"]:
        original = q.get("enunciado") or ""
        tem_principal = bool((q.get("imagem_principal") or "").strip())
        novo = limpar_enunciado(original, tem_principal)
        if novo != original:
            q["enunciado"] = novo
            mudancas += 1

    if mudancas > 0:
        dados["geradoEm"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        arquivo.write_text(
            json.dumps(dados, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return mudancas


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--anos", nargs="*", type=int)
    p.add_argument("--dias", nargs="*", type=int, default=[1, 2])
    args = p.parse_args()

    anos = args.anos
    if not anos:
        if not ENEM_DIR.exists():
            print("Sem dados em enem/")
            return 1
        anos = sorted(int(p.name) for p in ENEM_DIR.iterdir() if p.is_dir() and p.name.isdigit())

    total = 0
    for ano in anos:
        for dia in args.dias:
            arquivo = ENEM_DIR / str(ano) / f"dia{dia}.json"
            if arquivo.exists():
                m = processar_arquivo(arquivo)
                print(f"[ENEM {ano} dia {dia}] {m} questoes corrigidas")
                total += m
    print(f"\nTotal: {total} questoes ajustadas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
