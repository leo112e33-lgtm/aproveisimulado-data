"""
Separa imagens por dia: enem/<ano>/img/ -> enem/<ano>/dia<N>/img/

Para cada questao em cada dia, copia (nao move) suas imagens para a
nova pasta especifica do dia, e atualiza referencias no JSON.

Apos rodar:
- enem/<ano>/dia1/img/q<num>_*.{png,jpg}
- enem/<ano>/dia2/img/q<num>_*.{png,jpg}

Quando a mesma imagem original e usada por dia 1 E dia 2, ambas as
pastas terao copias, mas isso e aceitavel pois o conflito de nomes
fica resolvido. Pos-processamento futuro pode substituir uma das copias
pela imagem correta de cada dia (caso atual: Q24 2023 onde dia 1 tem
campanha e dia 2 tem caminhao).
"""
from __future__ import annotations
import json, re, shutil, sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
INLINE_RE = re.compile(r"!\[(?:[^\]]*)?\]\((enem/\d+/img/[^)\s]+)\)")

def transform_ref(ref: str, ano: int, dia: int) -> str:
    """enem/2023/img/q024_principal.png -> enem/2023/dia2/img/q024_principal.png"""
    if not ref or ref.startswith("http"): return ref
    return ref.replace(f"enem/{ano}/img/", f"enem/{ano}/dia{dia}/img/")

def main():
    copiados = set()  # (origem, destino)
    for ano_dir in sorted((ROOT / "enem").iterdir()):
        if not ano_dir.is_dir() or not ano_dir.name.isdigit():
            continue
        ano = int(ano_dir.name)
        for arq in sorted(ano_dir.glob("dia*.json")):
            d = json.loads(arq.read_text(encoding="utf-8"))
            dia = d["dia"]
            mudou = False
            for q in d["questoes"]:
                # imagem_principal
                ip = q.get("imagem_principal", "")
                if ip and not ip.startswith("http"):
                    novo = transform_ref(ip, ano, dia)
                    if novo != ip:
                        copiados.add((ip, novo))
                        q["imagem_principal"] = novo
                        mudou = True
                # imagens_extras
                novos = []
                for e in q.get("imagens_extras", []) or []:
                    if e and not e.startswith("http"):
                        n = transform_ref(e, ano, dia)
                        if n != e:
                            copiados.add((e, n))
                            mudou = True
                        novos.append(n)
                    else:
                        novos.append(e)
                q["imagens_extras"] = novos
                # imagens_alternativas
                novas_alts = []
                for ia in q.get("imagens_alternativas", []) or []:
                    if ia and not ia.startswith("http"):
                        n = transform_ref(ia, ano, dia)
                        if n != ia:
                            copiados.add((ia, n))
                            mudou = True
                        novas_alts.append(n)
                    else:
                        novas_alts.append(ia)
                q["imagens_alternativas"] = novas_alts
                # inline no enunciado
                en = q.get("enunciado", "") or ""
                def repl(m):
                    ref = m.group(1)
                    novo = transform_ref(ref, ano, dia)
                    if novo != ref:
                        copiados.add((ref, novo))
                    return f"![]({novo})"
                novo_en = INLINE_RE.sub(repl, en)
                if novo_en != en:
                    q["enunciado"] = novo_en
                    mudou = True
            if mudou:
                arq.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"  {arq.relative_to(ROOT)} atualizado")
    # Copiar arquivos
    for origem, destino in copiados:
        psrc = ROOT / origem
        pdst = ROOT / destino
        if not psrc.exists():
            print(f"  AVISO: origem nao existe: {origem}")
            continue
        pdst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(psrc, pdst)
    print(f"\nTotal arquivos copiados: {len(copiados)}")

if __name__ == "__main__":
    main()
