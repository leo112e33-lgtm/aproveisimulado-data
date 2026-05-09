"""
06_backup_explicacoes.py
========================
Salva todas as explicacoes existentes em arquivo separado para poder
restaurar apos reprocessamento dos JSONs.

Uso:
    # backup
    python scripts/06_backup_explicacoes.py --salvar
    # restaurar
    python scripts/06_backup_explicacoes.py --restaurar
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENEM_DIR = ROOT / "enem"
BACKUP = ROOT / ".explicacoes_backup.json"


def salvar() -> None:
    backup = {}
    for ano_dir in sorted(ENEM_DIR.iterdir()):
        if not ano_dir.is_dir() or not ano_dir.name.isdigit():
            continue
        for arquivo in sorted(ano_dir.glob("dia*.json")):
            d = json.loads(arquivo.read_text(encoding="utf-8"))
            ano = d["ano"]
            dia = d["dia"]
            chave = f"{ano}_{dia}"
            backup[chave] = {}
            for q in d["questoes"]:
                expl = (q.get("explicacao") or "").strip()
                if expl:
                    backup[chave][str(q["numero"])] = expl
    BACKUP.write_text(json.dumps(backup, ensure_ascii=False, indent=2), encoding="utf-8")
    total = sum(len(v) for v in backup.values())
    print(f"Backup salvo em {BACKUP.relative_to(ROOT)} — {total} explicacoes")


def restaurar() -> None:
    if not BACKUP.exists():
        print("Sem backup")
        return
    backup = json.loads(BACKUP.read_text(encoding="utf-8"))
    aplicadas = 0
    for chave, expls in backup.items():
        ano, dia = chave.split("_")
        arquivo = ENEM_DIR / ano / f"dia{dia}.json"
        if not arquivo.exists():
            continue
        d = json.loads(arquivo.read_text(encoding="utf-8"))
        for q in d["questoes"]:
            num = str(q["numero"])
            if num in expls and not (q.get("explicacao") or "").strip():
                q["explicacao"] = expls[num]
                aplicadas += 1
        arquivo.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Restauradas {aplicadas} explicacoes")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--salvar", action="store_true")
    p.add_argument("--restaurar", action="store_true")
    args = p.parse_args()
    if args.salvar:
        salvar()
    elif args.restaurar:
        restaurar()
    else:
        p.error("--salvar ou --restaurar")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
