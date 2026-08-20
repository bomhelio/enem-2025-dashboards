"""
17_deploy_concorrencia.py [--gerar] [--prod]

Empacota e publica a tela de inteligência competitiva.

O passo fácil de errar é a cópia com renome: os HTMLs saem de output/ como
Concorrencia_<Marca>.html e precisam chegar no deploy como matriz.html,
apogeu.html, qi.html (+ index.html da home). Os nomes vêm de deploy_file no
concorrencia_config.py - aqui não há nome hardcoded.

Antes de subir, valida que cada página tem os marcadores da versão atual. Se um
gerador falhou pela metade, o deploy aborta em vez de publicar página quebrada.

Uso:
    python 17_deploy_concorrencia.py                # empacota e sobe preview
    python 17_deploy_concorrencia.py --gerar        # regenera tudo antes
    python 17_deploy_concorrencia.py --gerar --prod # regenera e publica em produção

Produção pede confirmação. Para pular (CI), use --sim.
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

from concorrencia_config import MARCAS
from config import OUTPUT_DIR

AQUI = Path(__file__).parent
DEPLOY_DIR = Path(OUTPUT_DIR) / "deploy_concorrencia"
HOME_SRC = Path(OUTPUT_DIR) / "Concorrencia_Home.html"
SCOPE = "profheliogeo-9936s-projects"
PROJETO = "concorrencia-enem-raiz"
URL_PROD = "https://concorrencia-enem-raiz.vercel.app"

# Marcadores da versão atual das telas de marca. Se algum sumir, o gerador
# regrediu - melhor abortar do que publicar.
MARCADORES = {
    "Concorrente de massa": "consolidado com os dois donos da praça",
    "verdict-eixo": "veredicto por eixo (massa/topo)",
    "tag-seleta": "badge TURMA SELETA",
    ">700+<": "coluna de contagem absoluta",
    "margem ±": "intervalo de confiança 95%",
}
# O que NÃO pode mais existir: o corte de 30 decidindo veredicto.
PROIBIDOS = {"† menos de 30 alunos": "critério antigo por † ainda presente"}

VERCEL_JSON = '{\n  "cleanUrls": true,\n  "trailingSlash": true\n}\n'
ROBOTS_TXT = "User-agent: *\nDisallow: /\n"


def escreve_sem_bom(caminho: Path, conteudo: str) -> None:
    """PowerShell/Out-File cravam BOM e a Vercel rejeita o vercel.json."""
    caminho.write_text(conteudo, encoding="utf-8", newline="\n")


def vercel_bin() -> str:
    exe = shutil.which("vercel") or shutil.which("vercel.cmd")
    if not exe:
        raise SystemExit("Vercel CLI não encontrado no PATH. `npm i -g vercel`")
    return exe


def roda(cmd: list, cwd: Path = None, capturar: bool = True):
    r = subprocess.run(cmd, cwd=str(cwd) if cwd else None,
                       capture_output=capturar, text=True, encoding="utf-8",
                       errors="replace")
    return r


def gerar() -> None:
    print("· regerando as telas")
    for nome in MARCAS:
        r = roda([sys.executable, "13_gerar_concorrencia.py", nome], cwd=AQUI)
        if r.returncode != 0:
            raise SystemExit(f"  13_gerar_concorrencia.py falhou em {nome}:\n{r.stderr}")
        print(f"    {nome}")
    r = roda([sys.executable, "16_gerar_home_concorrencia.py"], cwd=AQUI)
    if r.returncode != 0:
        raise SystemExit(f"  16_gerar_home_concorrencia.py falhou:\n{r.stderr}")
    print("    home")


def valida(caminho: Path, checar_marcadores: bool) -> list:
    """Retorna lista de problemas encontrados na página."""
    if not caminho.exists():
        return [f"não existe: {caminho.name}"]
    if caminho.stat().st_size < 20_000:
        return [f"{caminho.name} tem só {caminho.stat().st_size} bytes - geração truncada?"]
    txt = caminho.read_text(encoding="utf-8")
    problemas = []
    if checar_marcadores:
        for marcador, desc in MARCADORES.items():
            if marcador not in txt:
                problemas.append(f"{caminho.name}: falta {desc}")
    for proibido, desc in PROIBIDOS.items():
        if proibido in txt:
            problemas.append(f"{caminho.name}: {desc}")
    return problemas


def empacota() -> list:
    """Copia com os nomes de deploy. Retorna a lista de arquivos publicáveis."""
    DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
    problemas, arquivos = [], []

    pares = [(HOME_SRC, "index.html", False)]
    for nome, cfg in MARCAS.items():
        pares.append((Path(OUTPUT_DIR) / cfg["html_out"], cfg["deploy_file"], True))

    for origem, destino, checar in pares:
        problemas += valida(origem, checar)
        if origem.exists():
            shutil.copy2(origem, DEPLOY_DIR / destino)
            arquivos.append(destino)
            kb = origem.stat().st_size / 1024
            print(f"    {origem.name:<32} -> {destino:<14} {kb:>7.0f} KB")

    escreve_sem_bom(DEPLOY_DIR / "vercel.json", VERCEL_JSON)
    escreve_sem_bom(DEPLOY_DIR / "robots.txt", ROBOTS_TXT)

    if problemas:
        print("\n  ABORTADO - a validação encontrou problemas:")
        for p in problemas:
            print(f"    ! {p}")
        raise SystemExit(1)
    return arquivos


def garante_link(vc: str) -> None:
    if (DEPLOY_DIR / ".vercel" / "project.json").exists():
        return
    print(f"· linkando ao projeto {PROJETO}")
    r = roda([vc, "link", "--yes", "--project", PROJETO, "--scope", SCOPE], cwd=DEPLOY_DIR)
    if not (DEPLOY_DIR / ".vercel" / "project.json").exists():
        raise SystemExit(f"  link falhou:\n{r.stdout}\n{r.stderr}")


def publica(vc: str, prod: bool) -> str:
    cmd = [vc, "deploy", "--scope", SCOPE, "--yes"]
    if prod:
        cmd.append("--prod")
    print(f"· subindo ({'PRODUÇÃO' if prod else 'preview'})")
    r = roda(cmd, cwd=DEPLOY_DIR)
    saida = (r.stdout or "") + (r.stderr or "")
    # O CLI imprime "Preview   https://..." e mistura escapes ANSI de progresso.
    saida_limpa = re.sub(r"\x1b\[[0-9;]*[A-Za-z]|\[\d*[A-Z]", " ", saida)
    urls = re.findall(r"https://[\w.-]+\.vercel\.app\b", saida_limpa)
    if r.returncode != 0 and not urls:
        raise SystemExit(f"  deploy falhou:\n{saida[-1500:]}")
    # a última URL de deployment é a do build recém-criado; ignora a de inspeção
    deploys = [u for u in urls if "vercel.com" not in u]
    return deploys[-1] if deploys else ""


def confere_producao() -> None:
    """Bate as 4 rotas no ar. trailingSlash=true, então a barra final importa."""
    import urllib.request
    print("· conferindo no ar")
    for rota in ["/"] + [f"/{c['deploy_file'].removesuffix('.html')}/" for c in MARCAS.values()]:
        try:
            with urllib.request.urlopen(URL_PROD + rota, timeout=30) as resp:
                corpo = resp.read().decode("utf-8", "replace")
            marca_ok = rota == "/" or all(m in corpo for m in MARCADORES)
            print(f"    {rota:<12} {resp.status}  {len(corpo)/1024:>6.0f} KB  "
                  f"{'ok' if marca_ok else 'SEM OS MARCADORES'}")
        except Exception as e:
            print(f"    {rota:<12} ERRO {e}")


def main() -> None:
    args = sys.argv[1:]
    prod = "--prod" in args
    if prod and "--sim" not in args:
        print(f"Publicar em PRODUÇÃO: {URL_PROD}")
        if input("Confirma? [s/N] ").strip().lower() not in ("s", "sim", "y"):
            raise SystemExit("cancelado")

    if "--gerar" in args:
        gerar()

    print("· empacotando")
    empacota()

    vc = vercel_bin()
    garante_link(vc)
    url = publica(vc, prod)

    print(f"\nOK -> {url or '(sem URL na saída)'}")
    if prod:
        confere_producao()
    else:
        print(f"  preview fica atrás do login da Vercel; abra no navegador logado.")
        print(f"  para promover: python {Path(__file__).name} --prod")


if __name__ == "__main__":
    main()
