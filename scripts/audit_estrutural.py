# -*- coding: utf-8 -*-
"""Auditoria estrutural das provas ENEM do app AproveiSimulado."""
import json, os, re, glob, hashlib
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")
VALID = set("ABCDE")

report = {}
all_issues = []
hash_global = defaultdict(list)  # detectar questoes repetidas entre provas

def existe_img(path):
    if not path: return True
    if path.startswith("http"): return True  # remoto, nao verificavel localmente
    return os.path.isfile(os.path.join(ROOT, path))

provas = sorted(glob.glob(os.path.join(ROOT, "enem", "*", "dia*.json")))
for fpath in provas:
    rel = os.path.relpath(fpath, ROOT).replace("\\", "/")
    d = json.loads(open(fpath, "rb").read().decode("utf-8"))
    qs = d.get("questoes", [])
    info = {
        "arquivo": rel, "ano": d.get("ano"), "dia": d.get("dia"),
        "total_declarado": d.get("total"), "total_real": len(qs),
        "anuladas": [], "gabarito_invalido": [], "numeracao_problema": [],
        "alts_diferentes_de_5": [], "enunciado_vazio": [], "alt_vazia": [],
        "img_principal_faltando": [], "img_inline_faltando": [],
        "img_alt_faltando": [], "fonte_indisponivel": [], "sem_explicacao": [],
        "duplicadas_internas": [], "gabarito": {},
    }
    numeros = []
    hashes_local = {}
    for q in qs:
        n = q.get("numero")
        numeros.append(n)
        correta = (q.get("correta") or "").strip()
        info["gabarito"][n] = correta
        # gabarito
        if correta == "X":
            info["anuladas"].append(n)
        elif correta not in VALID:
            info["gabarito_invalido"].append((n, correta))
        # fonte anulada/erro
        if q.get("fonte") in ("indisponivel", "erro"):
            info["fonte_indisponivel"].append((n, q.get("fonte")))
        # alternativas
        alts = q.get("alternativas") or []
        if len(alts) != 5:
            info["alts_diferentes_de_5"].append((n, len(alts)))
        for i, a in enumerate(alts):
            if not (a or "").strip():
                info["alt_vazia"].append((n, chr(65+i)))
        # enunciado
        enun = (q.get("enunciado") or "").strip()
        introd = (q.get("alternativas_introducao") or "").strip()
        if not enun and not introd and not (q.get("imagem_principal") or ""):
            info["enunciado_vazio"].append(n)
        # explicacao
        if not (q.get("explicacao") or "").strip():
            info["sem_explicacao"].append(n)
        # imagens
        imgp = q.get("imagem_principal") or ""
        if imgp and not existe_img(imgp):
            info["img_principal_faltando"].append((n, imgp))
        for m in IMG_RE.findall(enun):
            if not existe_img(m):
                info["img_inline_faltando"].append((n, m))
        for i, ia in enumerate(q.get("imagens_alternativas") or []):
            if ia and not existe_img(ia):
                info["img_alt_faltando"].append((n, chr(65+i), ia))
        # hash para duplicatas (texto normalizado)
        chave = re.sub(r"\s+", " ", (enun + " " + introd).lower()).strip()
        if chave and len(chave) > 30:
            h = hashlib.md5(chave.encode()).hexdigest()
            if h in hashes_local:
                info["duplicadas_internas"].append((hashes_local[h], n))
            else:
                hashes_local[h] = n
            hash_global[h].append(f"{rel}#{n}")
    # numeracao
    esperado = list(range(1, len(qs)+1))
    if sorted(numeros) != esperado:
        faltando = set(esperado) - set(numeros)
        extra = set(numeros) - set(esperado)
        dup = [x for x in numeros if numeros.count(x) > 1]
        info["numeracao_problema"] = {"faltando": sorted(faltando),
                                      "extra": sorted(extra),
                                      "duplicados": sorted(set(dup))}
    report[rel] = info

# duplicatas entre provas
dup_cross = {h: locs for h, locs in hash_global.items() if len(locs) > 1}

out = os.path.join(ROOT, "scripts", "audit_resultado.json")
json.dump({"provas": report, "duplicatas_cross_prova": dup_cross},
          open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# resumo no stdout
print("RESUMO DA AUDITORIA ESTRUTURAL")
print("="*70)
for rel, info in report.items():
    flags = []
    if info["total_real"] != 90: flags.append(f"TOTAL={info['total_real']}")
    if info["numeracao_problema"]: flags.append("NUMERACAO!")
    if info["gabarito_invalido"]: flags.append(f"GAB_INVALIDO={len(info['gabarito_invalido'])}")
    if info["alts_diferentes_de_5"]: flags.append(f"ALTS!={len(info['alts_diferentes_de_5'])}")
    if info["img_principal_faltando"]: flags.append(f"IMGp={len(info['img_principal_faltando'])}")
    if info["img_inline_faltando"]: flags.append(f"IMGinline={len(info['img_inline_faltando'])}")
    if info["img_alt_faltando"]: flags.append(f"IMGalt={len(info['img_alt_faltando'])}")
    if info["enunciado_vazio"]: flags.append(f"ENUNvazio={len(info['enunciado_vazio'])}")
    if info["alt_vazia"]: flags.append(f"ALTvazia={len(info['alt_vazia'])}")
    if info["duplicadas_internas"]: flags.append(f"DUP={len(info['duplicadas_internas'])}")
    status = "OK" if not flags else " | ".join(flags)
    print(f"{rel:24} anul={len(info['anuladas']):2} semExpl={len(info['sem_explicacao']):2}  {status}")
print("="*70)
print("Duplicatas entre provas distintas:", len(dup_cross))
print("Resultado completo salvo em:", out)
