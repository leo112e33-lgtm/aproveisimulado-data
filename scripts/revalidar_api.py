# -*- coding: utf-8 -*-
"""Revalida os gabaritos do dataset contra a fonte ao vivo api.enem.dev.

Para cada questao com fonte_url, busca o correctAlternative atual da API e
compara com o campo 'correta' do dataset. Divergencias em questoes marcadas
como correcao_manual/inep_oficial sao ESPERADAS (correcao deliberada).
"""
import json, os, glob, re, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "audit-aproveisimulado"})
    for tent in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            if tent == 2:
                return {"_erro": f"{type(e).__name__}: {str(e)[:60]}"}
            time.sleep(1.0)

def checar_questao(item):
    rel, ano, dia, q = item
    n = q["numero"]
    url = q.get("fonte_url") or ""
    res = {"prova": rel, "numero": n, "correta_dataset": q.get("correta"),
           "fonte": q.get("fonte"), "url": url}
    if not url or "api.enem.dev" not in url:
        res["status"] = "sem_url_api"
        return res
    # questao de lingua estrangeira (dia1, index 1..5): dataset usa espanhol
    m = re.search(r"/questions/(\d+)", url)
    idx = int(m.group(1)) if m else None
    if dia == 1 and idx is not None and idx <= 5:
        url = url + "?language=espanhol"
    data = fetch(url)
    if data is None or "_erro" in (data or {}):
        res["status"] = "erro_rede"
        res["detalhe"] = (data or {}).get("_erro", "None")
        return res
    api_correta = data.get("correctAlternative")
    res["correta_api"] = api_correta
    if api_correta is None:
        res["status"] = "api_sem_gabarito"
    elif str(api_correta).strip().upper() == str(q.get("correta")).strip().upper():
        res["status"] = "match"
    else:
        res["status"] = "divergente"
    return res

# montar lista de questoes
itens = []
for f in sorted(glob.glob(os.path.join(ROOT, "enem", "*", "dia*.json"))):
    rel = os.path.relpath(f, ROOT).replace("\\", "/")
    d = json.loads(open(f, "rb").read().decode("utf-8"))
    for q in d["questoes"]:
        itens.append((rel, d["ano"], d["dia"], q))

print(f"Revalidando {len(itens)} questoes contra api.enem.dev (ao vivo)...")
resultados = []
with ThreadPoolExecutor(max_workers=12) as ex:
    futs = [ex.submit(checar_questao, it) for it in itens]
    feitos = 0
    for fut in as_completed(futs):
        resultados.append(fut.result())
        feitos += 1
        if feitos % 90 == 0:
            print(f"  {feitos}/{len(itens)} ...")

# salvar e resumir
out = os.path.join(ROOT, "scripts", "revalidacao_api.json")
json.dump(resultados, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

from collections import Counter
status = Counter(r["status"] for r in resultados)
print("\nRESULTADO DA REVALIDACAO CONTRA API OFICIAL (api.enem.dev)")
print("=" * 64)
for k, v in status.most_common():
    print(f"  {k:20} {v}")
print("=" * 64)

div = [r for r in resultados if r["status"] == "divergente"]
print(f"\nDIVERGENCIAS ({len(div)}):")
for r in sorted(div, key=lambda x: (x["prova"], x["numero"])):
    esperado = "  <-- correcao deliberada" if r["fonte"] in ("correcao_manual", "inep_oficial") else "  *** VERIFICAR ***"
    print(f"  {r['prova']:22} Q{r['numero']:<3} dataset={r['correta_dataset']} api={r.get('correta_api')} fonte={r['fonte']}{esperado}")

semgab = [r for r in resultados if r["status"] == "api_sem_gabarito"]
print(f"\nAPI SEM GABARITO ({len(semgab)}) (anuladas/sem resposta na API):")
for r in sorted(semgab, key=lambda x: (x["prova"], x["numero"])):
    print(f"  {r['prova']:22} Q{r['numero']:<3} dataset={r['correta_dataset']} fonte={r['fonte']}")

erros = [r for r in resultados if r["status"] in ("erro_rede",)]
print(f"\nERROS DE REDE ({len(erros)})")
print("Resultado completo:", out)
