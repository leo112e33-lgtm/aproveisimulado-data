"""
04_aplicar_explicacoes.py
=========================
Aplica explicacoes geradas externamente (manualmente ou por outro modelo)
diretamente nos JSONs do dataset, mantendo a mesma formatacao.

Recebe um arquivo JSON com a estrutura:

    {
      "ano": 2023,
      "dia": 1,
      "explicacoes": {
        "1": "explicacao da questao 1...",
        "5": "explicacao da questao 5...",
        ...
      }
    }

Uso:
    python scripts/04_aplicar_explicacoes.py --arquivo lote.json
    python scripts/04_aplicar_explicacoes.py --stdin   # le JSON da stdin
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENEM_DIR = ROOT / "enem"


def aplicar(payload: dict, sobrescrever: bool) -> tuple[int, int]:
    ano = int(payload["ano"])
    dia = int(payload["dia"])
    explicacoes = payload.get("explicacoes") or {}

    arquivo = ENEM_DIR / str(ano) / f"dia{dia}.json"
    if not arquivo.exists():
        raise FileNotFoundError(f"JSON nao encontrado: {arquivo}")

    dados = json.loads(arquivo.read_text(encoding="utf-8"))
    questoes_por_num = {int(q["numero"]): q for q in dados["questoes"]}

    aplicadas = 0
    puladas = 0
    for num_str, texto in explicacoes.items():
        num = int(num_str)
        if num not in questoes_por_num:
            print(f"  ! questao {num} nao existe na prova {ano} dia {dia}")
            continue
        q = questoes_por_num[num]
        ja_tem = bool((q.get("explicacao") or "").strip())
        if ja_tem and not sobrescrever:
            puladas += 1
            continue
        q["explicacao"] = texto.strip()
        aplicadas += 1

    arquivo.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return aplicadas, puladas


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--arquivo", type=Path)
    p.add_argument("--stdin", action="store_true")
    p.add_argument("--sobrescrever", action="store_true",
                   help="Substitui explicacoes existentes")
    args = p.parse_args()

    if args.stdin:
        payload = json.loads(sys.stdin.read())
    elif args.arquivo:
        payload = json.loads(args.arquivo.read_text(encoding="utf-8"))
    else:
        p.error("Use --arquivo ou --stdin")

    aplicadas, puladas = aplicar(payload, args.sobrescrever)
    ano = payload["ano"]; dia = payload["dia"]
    print(f"[ENEM {ano} dia {dia}] aplicadas={aplicadas} puladas={puladas}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
