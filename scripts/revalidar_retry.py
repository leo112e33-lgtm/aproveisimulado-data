# -*- coding: utf-8 -*-
"""Reprocessa apenas as questoes que deram erro_rede na revalidacao."""
import json, os, glob, re, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
res_path = os.path.join(ROOT, "scripts", "revalidacao_api.json")
resultados = json.load(open(res_path, encoding="utf-8"))

# indexar dataset por (prova, numero)
ds = {}
for f in sorted(glob.glob(os.path.join(ROOT, "enem", "*", "dia*.json"))):
    rel = os.path.relpath(f, ROOT).replace("\\", "/")
    d = json.loads(open(f, "rb").read().decode("utf-8"))
    for q in d["questoes"]:
        ds[(rel, q["numero"])] = (d["dia"], q)

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "audit-aproveisimulado"})
    for t in range(5):
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            time.sleep(1.5 * (t + 1))
    return None

pend = [r for r in resultados if r["status"] == "erro_rede"]
print(f"Reprocessando {len(pend)} questoes (sequencial, com pausa)...")
for i, r in enumerate(pend):
    dia, q = ds[(r["prova"], r["numero"])]
    url = q.get("fonte_url")
    m = re.search(r"/questions/(\d+)", url)
    idx = int(m.group(1)) if m else None
    if dia == 1 and idx is not None and idx <= 5:
        url = url + "?language=espanhol"
    data = fetch(url)
    if data is None:
        continue  # mantem erro_rede
    api = data.get("correctAlternative")
    r["correta_api"] = api
    if api is None:
        r["status"] = "api_sem_gabarito"
    elif str(api).strip().upper() == str(q.get("correta")).strip().upper():
        r["status"] = "match"
    else:
        r["status"] = "divergente"
    time.sleep(0.25)
    if (i + 1) % 40 == 0:
        print(f"  {i+1}/{len(pend)} ...")

json.dump(resultados, open(res_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

from collections import Counter
status = Counter(r["status"] for r in resultados)
print("\nRESULTADO FINAL (apos retry):")
for k, v in status.most_common():
    print(f"  {k:20} {v}")
div = [r for r in resultados if r["status"] == "divergente"]
print(f"\nDIVERGENCIAS ({len(div)}):")
for r in sorted(div, key=lambda x: (x["prova"], x["numero"])):
    tag = "correcao deliberada" if r["fonte"] in ("correcao_manual","inep_oficial","anulada_inep") else "*** VERIFICAR ***"
    print(f"  {r['prova']:22} Q{r['numero']:<3} dataset={r['correta_dataset']} api={r.get('correta_api')} fonte={r['fonte']:16} {tag}")
err = [r for r in resultados if r["status"] == "erro_rede"]
print(f"\nainda com erro_rede: {len(err)}")
