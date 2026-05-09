"""
Auditoria visual completa de imagens do dataset:

1) DUPLICATAS: detecta quando imagem_principal/extras tem hash identico a
   imagens inline do enunciado markdown. Quando duplicada, remove o campo
   JSON e mantem apenas a inline (que renderiza no fluxo do texto).

2) IMAGENS POSSIVELMENTE TROCADAS: usa hash perceptual (pHash) para
   verificar se a imagem do JSON aparece na pagina oficial correspondente
   do PDF do INEP. Se nao bate com NADA na pagina, e candidato a troca.

Saida: lista de problemas + diff aplicavel.
"""
from __future__ import annotations
import json, hashlib, re, sys, io, subprocess
from pathlib import Path
from PIL import Image
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
PROVAS = ROOT / ".provas"

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def phash(path: Path, size: int = 16) -> int:
    """Hash perceptual simples: redimensiona para size x size grayscale,
    converte para bits acima da media."""
    try:
        im = Image.open(path).convert("L").resize((size, size), Image.LANCZOS)
        pixels = list(im.getdata())
        avg = sum(pixels) / len(pixels)
        bits = 0
        for i, p in enumerate(pixels):
            if p > avg:
                bits |= 1 << i
        return bits
    except Exception:
        return 0

def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")

INLINE_RE = re.compile(r"!\[(?:[^\]]*)?\]\((enem/[^)\s]+)\)")

def detectar_duplicatas() -> list:
    """Retorna [(arquivo_json, q_num, campo, ref, ref_inline)] onde campo e
    'imagem_principal' ou 'imagens_extras[i]' e ref tem hash igual a uma
    inline do enunciado."""
    problemas = []
    for ano_dir in sorted((ROOT / "enem").iterdir()):
        if not ano_dir.is_dir() or not ano_dir.name.isdigit():
            continue
        for arq in sorted(ano_dir.glob("dia*.json")):
            d = json.loads(arq.read_text(encoding="utf-8"))
            for q in d["questoes"]:
                inline_refs = INLINE_RE.findall(q.get("enunciado", "") or "")
                inline_hashes = {}
                for ref in inline_refs:
                    p = ROOT / ref
                    if p.exists():
                        inline_hashes[sha256(p)] = ref
                # principal
                ip = q.get("imagem_principal", "")
                if ip:
                    p = ROOT / ip
                    if p.exists() and sha256(p) in inline_hashes:
                        problemas.append((arq.name, q["numero"], "imagem_principal", ip, inline_hashes[sha256(p)]))
                # extras
                for i, e in enumerate(q.get("imagens_extras", []) or []):
                    if not e: continue
                    p = ROOT / e
                    if p.exists() and sha256(p) in inline_hashes:
                        problemas.append((arq.name, q["numero"], f"imagens_extras[{i}]", e, inline_hashes[sha256(p)]))
    return problemas

def detectar_trocadas() -> list:
    """Para cada questao com imagem, extrai todas imagens raster da pagina
    oficial correspondente do PDF e compara via pHash. Se nenhum match
    aceitavel, marca como suspeito."""
    problemas = []
    for ano in (2018, 2019, 2020, 2021, 2022, 2023):
        for dia in (1, 2):
            pdf = PROVAS / f"{ano}_d{dia}.pdf"
            if not pdf.exists(): continue
            doc = pymupdf.open(pdf)
            # Mapeia numero oficial para pagina e suas imagens raster
            pdf_imgs_por_q = {}
            current_q = None
            for i in range(len(doc)):
                t = doc[i].get_text()
                qmatches = list(re.finditer(r"QUEST[AÃÄ]O\s+(\d+)", t))
                # raster imgs da pagina
                imgs_raster = []
                for info in doc[i].get_images(full=True):
                    xref = info[0]
                    try:
                        pix = pymupdf.Pixmap(doc, xref)
                        if pix.n - pix.alpha < 4 and pix.width > 80 and pix.height > 80:
                            tmp = PROVAS / f"_tmp_{ano}_{dia}_{i}_{xref}.png"
                            pix.save(tmp)
                            imgs_raster.append((xref, tmp, phash(tmp)))
                    except: pass
                # Para cada questao detectada nessa pagina, atribui essas imagens
                if qmatches:
                    nums = [int(m.group(1)) for m in qmatches]
                    # Heuristica: associa todas as imagens raster da pagina a TODAS as questoes da pagina
                    for n in nums:
                        if n not in pdf_imgs_por_q:
                            pdf_imgs_por_q[n] = []
                        pdf_imgs_por_q[n].extend(imgs_raster)
            doc.close()
            arq = ROOT / "enem" / str(ano) / f"dia{dia}.json"
            if not arq.exists(): continue
            d = json.loads(arq.read_text(encoding="utf-8"))
            for q in d["questoes"]:
                n_oficial = q["numero"] if dia == 1 else q["numero"] + 90
                pdf_hashes = [h for _,_,h in pdf_imgs_por_q.get(n_oficial, [])]
                if not pdf_hashes:
                    continue  # nao tem imagens raster na pagina (vetorial, etc.)
                # Coletar imagens do JSON
                refs = []
                ip = q.get("imagem_principal", "")
                if ip and not ip.startswith("http"): refs.append(("principal", ip))
                for i,e in enumerate(q.get("imagens_extras", []) or []):
                    if e and not e.startswith("http"): refs.append((f"extra{i}", e))
                for m in INLINE_RE.finditer(q.get("enunciado","") or ""):
                    refs.append(("inline", m.group(1)))
                for tag, ref in refs:
                    p = ROOT / ref
                    if not p.exists(): continue
                    h = phash(p)
                    if h == 0: continue
                    melhor = min((hamming(h, ph) for ph in pdf_hashes), default=999)
                    if melhor > 60:
                        problemas.append((f"{ano}d{dia}", q["numero"], n_oficial, tag, ref, melhor))
    # limpar tmp files
    for f in PROVAS.glob("_tmp_*.png"):
        try: f.unlink()
        except: pass
    return problemas


def main():
    print("=== 1) DUPLICATAS principal/extras x inline ===")
    dups = detectar_duplicatas()
    for nome, n, campo, ref, inl in dups:
        print(f"  {nome} Q{n}  {campo}={ref}  ==  inline={inl}")
    print(f"Total duplicatas: {len(dups)}\n")

    print("=== 2) IMAGENS SUSPEITAS DE TROCA (pHash distance > 60) ===")
    trocas = detectar_trocadas()
    for ad, n, no, tag, ref, dist in trocas:
        print(f"  {ad} Q{n} (oficial {no}) [{tag}] dist={dist}: {ref}")
    print(f"Total suspeitas: {len(trocas)}")
    return dups, trocas

if __name__ == "__main__":
    main()
