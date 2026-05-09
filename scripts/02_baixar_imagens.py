"""
02_baixar_imagens.py
====================
Baixa todas as imagens referenciadas nos JSONs gerados pela fase 01 e
copia as imagens locais (drawables) das correcoes manuais.

Para cada imagem:
- "imagem_principal" se URL: baixa para enem/<ano>/img/q<NN>_principal.<ext>
- "imagem_principal" se "local:<arquivo>": copia do drawable do app
- "imagens_extras": baixa cada uma para q<NN>_extra<i>.<ext>
- "imagens_alternativas[i]" se URL: baixa para q<NN>_alt<L>.<ext>
- "imagens_alternativas[i]" se "local:...": copia do drawable

Atualiza in-place os caminhos no JSON para o caminho relativo final do repo
(ex: "enem/2023/img/q34_principal.png").

Uso:
    python scripts/02_baixar_imagens.py
    python scripts/02_baixar_imagens.py --anos 2023
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).parent))
import correcoes_manuais  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ENEM_DIR = ROOT / "enem"
TIMEOUT = 15
EXTENSOES_VALIDAS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}


def detectar_extensao(url: str) -> str:
    caminho = urlparse(url).path.lower()
    for ext in EXTENSOES_VALIDAS:
        if caminho.endswith(ext):
            return ext
    return ".png"


def baixar_url(url: str, destino: Path) -> bool:
    if destino.exists() and destino.stat().st_size > 0:
        return True
    destino.parent.mkdir(parents=True, exist_ok=True)
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 aproveisimulado-data"})
        with urlopen(req, timeout=TIMEOUT) as r:
            tmp = destino.with_suffix(destino.suffix + ".tmp")
            tmp.write_bytes(r.read())
            tmp.replace(destino)
        return True
    except Exception as e:
        print(f"  ! falhou {url}: {e}")
        if destino.exists():
            destino.unlink(missing_ok=True)
        return False


def copiar_local(nome_arquivo: str, destino: Path) -> bool:
    origem = Path(correcoes_manuais.ANDROID_DRAWABLE_DIR) / nome_arquivo
    if not origem.exists():
        print(f"  ! drawable nao encontrado: {origem}")
        return False
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(origem, destino)
    return True


def processar_questao(q: dict, dir_img: Path) -> bool:
    """Baixa as imagens da questao e atualiza os caminhos in-place. Retorna True se mudou algo."""
    mudou = False
    n = q["numero"]
    rel_img = dir_img.relative_to(ROOT).as_posix()

    # imagem principal
    img_principal = q.get("imagem_principal") or ""
    if img_principal.startswith("http"):
        ext = detectar_extensao(img_principal)
        nome = f"q{n:03d}_principal{ext}"
        destino = dir_img / nome
        if baixar_url(img_principal, destino):
            q["imagem_principal"] = f"{rel_img}/{nome}"
            mudou = True
    elif img_principal.startswith("local:"):
        nome_origem = img_principal[len("local:"):]
        ext = Path(nome_origem).suffix or ".png"
        nome = f"q{n:03d}_principal{ext}"
        destino = dir_img / nome
        if copiar_local(nome_origem, destino):
            q["imagem_principal"] = f"{rel_img}/{nome}"
            mudou = True

    # imagens extras
    extras = q.get("imagens_extras") or []
    novas_extras: list[str] = []
    for i, url in enumerate(extras):
        if not url:
            continue
        if url.startswith("http"):
            ext = detectar_extensao(url)
            nome = f"q{n:03d}_extra{i + 1}{ext}"
            destino = dir_img / nome
            if baixar_url(url, destino):
                novas_extras.append(f"{rel_img}/{nome}")
                mudou = True
            else:
                novas_extras.append(url)
        else:
            novas_extras.append(url)
    if novas_extras != extras:
        q["imagens_extras"] = novas_extras

    # imagens das alternativas
    alts = q.get("imagens_alternativas") or []
    novas_alts: list = list(alts)
    for i, url in enumerate(alts):
        if not url:
            continue
        letra = chr(ord("A") + i)
        if url.startswith("http"):
            ext = detectar_extensao(url)
            nome = f"q{n:03d}_alt{letra}{ext}"
            destino = dir_img / nome
            if baixar_url(url, destino):
                novas_alts[i] = f"{rel_img}/{nome}"
                mudou = True
        elif url.startswith("local:"):
            nome_origem = url[len("local:"):]
            ext = Path(nome_origem).suffix or ".png"
            nome = f"q{n:03d}_alt{letra}{ext}"
            destino = dir_img / nome
            if copiar_local(nome_origem, destino):
                novas_alts[i] = f"{rel_img}/{nome}"
                mudou = True
    if novas_alts != alts:
        q["imagens_alternativas"] = novas_alts

    return mudou


def processar_dia(ano: int, dia: int, paralelo: int) -> None:
    arquivo = ENEM_DIR / str(ano) / f"dia{dia}.json"
    if not arquivo.exists():
        print(f"[ENEM {ano} dia {dia}] sem JSON, pulando")
        return
    payload = json.loads(arquivo.read_text(encoding="utf-8"))
    dir_img = ENEM_DIR / str(ano) / "img"
    print(f"[ENEM {ano} dia {dia}] processando imagens...")

    contador_mudancas = 0
    with ThreadPoolExecutor(max_workers=paralelo) as pool:
        futuros = {
            pool.submit(processar_questao, q, dir_img): q["numero"]
            for q in payload["questoes"]
        }
        for fut in as_completed(futuros):
            if fut.result():
                contador_mudancas += 1
                print(".", end="", flush=True)
            else:
                print("-", end="", flush=True)
    print()

    if contador_mudancas:
        payload["geradoEm"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        arquivo.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    print(f"  -> {contador_mudancas} questoes com imagens atualizadas")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--anos", nargs="*", type=int)
    p.add_argument("--dias", nargs="*", type=int, default=[1, 2])
    p.add_argument("--paralelo", type=int, default=8)
    args = p.parse_args()

    anos = args.anos
    if not anos:
        if not ENEM_DIR.exists():
            print("Nenhum dado em enem/. Rode 01_baixar_questoes.py primeiro.")
            return 1
        anos = sorted(int(p.name) for p in ENEM_DIR.iterdir() if p.is_dir() and p.name.isdigit())

    for ano in anos:
        for dia in args.dias:
            processar_dia(ano, dia, args.paralelo)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
