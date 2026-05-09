"""
Audita as imagens do dataset.
- Lista referenciadas em todos os JSON
- Compara com arquivos em disco
- Reporta inexistentes e orfas
"""
from __future__ import annotations
import json, re, sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent

referenciadas: set[str] = set()
inexistentes: list[tuple] = []
no_disco: set[str] = set()

for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
    for f in (ROOT / "enem").rglob(ext):
        rel = str(f.relative_to(ROOT)).replace("\\", "/")
        no_disco.add(rel)

for ano_dir in sorted((ROOT / "enem").iterdir()):
    if not ano_dir.is_dir() or not ano_dir.name.isdigit():
        continue
    for arq in sorted(ano_dir.glob("dia*.json")):
        d = json.loads(arq.read_text(encoding="utf-8"))
        for q in d["questoes"]:
            ip = q.get("imagem_principal", "")
            if ip and not ip.startswith("http"):
                referenciadas.add(ip)
                if ip not in no_disco:
                    inexistentes.append((arq.name, q["numero"], "imagem_principal", ip))
            for e in q.get("imagens_extras", []) or []:
                if e and not e.startswith("http"):
                    referenciadas.add(e)
                    if e not in no_disco:
                        inexistentes.append((arq.name, q["numero"], "extra", e))
            for i, ia in enumerate(q.get("imagens_alternativas", []) or []):
                if ia and not ia.startswith("http"):
                    referenciadas.add(ia)
                    if ia not in no_disco:
                        inexistentes.append((arq.name, q["numero"], f"alt_{chr(65+i)}", ia))
            for m in re.finditer(r"!\[(?:[^\]]*)?\]\((enem/[^)\s]+)\)", q.get("enunciado", "") or ""):
                ref = m.group(1)
                referenciadas.add(ref)
                if ref not in no_disco:
                    inexistentes.append((arq.name, q["numero"], "inline", ref))

print(f"Imagens referenciadas: {len(referenciadas)}")
print(f"Imagens no disco:      {len(no_disco)}")
print(f"\nReferenciadas mas INEXISTENTES no disco: {len(inexistentes)}")
for n, q, tipo, ref in inexistentes[:30]:
    print(f"  {n} Q{q} ({tipo}): {ref}")
if len(inexistentes) > 30:
    print(f"  ... e mais {len(inexistentes)-30}")

orfas = no_disco - referenciadas
print(f"\nOrfas (no disco, nunca referenciadas): {len(orfas)}")
for o in sorted(orfas)[:30]:
    print(f"  {o}")
if len(orfas) > 30:
    print(f"  ... e mais {len(orfas)-30}")
