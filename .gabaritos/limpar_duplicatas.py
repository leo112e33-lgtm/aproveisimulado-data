"""
Aplica limpeza: para cada (imagem_principal, imagens_extras[i]) que tem
hash sha256 identico a uma imagem inline do enunciado, remove a referencia
do JSON. A imagem inline continua renderizando.

Tambem remove imagens orfas em disco que nao sao mais referenciadas por
nenhuma questao.
"""
from __future__ import annotations
import json, hashlib, re, sys, io, os
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent

def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

INLINE_RE = re.compile(r"!\[(?:[^\]]*)?\]\((enem/[^)\s]+)\)")

def main():
    total = 0
    for ano_dir in sorted((ROOT / "enem").iterdir()):
        if not ano_dir.is_dir() or not ano_dir.name.isdigit():
            continue
        for arq in sorted(ano_dir.glob("dia*.json")):
            d = json.loads(arq.read_text(encoding="utf-8"))
            mudou = False
            for q in d["questoes"]:
                inline_refs = INLINE_RE.findall(q.get("enunciado", "") or "")
                inline_hashes = set()
                for ref in inline_refs:
                    p = ROOT / ref
                    if p.exists():
                        inline_hashes.add(sha256(p))
                # principal
                ip = q.get("imagem_principal", "")
                if ip:
                    p = ROOT / ip
                    if p.exists() and sha256(p) in inline_hashes:
                        q["imagem_principal"] = ""
                        mudou = True; total += 1
                # extras
                novos_extras = []
                for e in q.get("imagens_extras", []) or []:
                    if not e:
                        continue
                    p = ROOT / e
                    if p.exists() and sha256(p) in inline_hashes:
                        mudou = True; total += 1
                    else:
                        novos_extras.append(e)
                if novos_extras != (q.get("imagens_extras", []) or []):
                    q["imagens_extras"] = novos_extras
            if mudou:
                arq.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"  {arq.name} atualizado")
    print(f"\nTotal duplicatas removidas: {total}")

    # remover imagens orfas
    referenciadas = set()
    for ano_dir in sorted((ROOT / "enem").iterdir()):
        if not ano_dir.is_dir() or not ano_dir.name.isdigit(): continue
        for arq in sorted(ano_dir.glob("dia*.json")):
            d = json.loads(arq.read_text(encoding="utf-8"))
            for q in d["questoes"]:
                ip = q.get("imagem_principal", "")
                if ip and not ip.startswith("http"):
                    referenciadas.add(ip)
                for e in q.get("imagens_extras", []) or []:
                    if e and not e.startswith("http"):
                        referenciadas.add(e)
                for ia in q.get("imagens_alternativas", []) or []:
                    if ia and not ia.startswith("http"):
                        referenciadas.add(ia)
                for m in INLINE_RE.finditer(q.get("enunciado","") or ""):
                    referenciadas.add(m.group(1))
    no_disco = set()
    for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
        for f in (ROOT / "enem").rglob(ext):
            no_disco.add(str(f.relative_to(ROOT)).replace("\\", "/"))
    orfas = no_disco - referenciadas
    print(f"\nImagens orfas detectadas: {len(orfas)}")
    # NAO removemos automaticamente - apenas reporta
    for o in sorted(orfas)[:20]:
        print(f"  {o}")

if __name__ == "__main__":
    main()
