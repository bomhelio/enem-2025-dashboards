# -*- coding: utf-8 -*-
"""
integrar_dashboard.py
Injeta o bloco de analise por HABILIDADE (gerado por hab_analise) dentro do
dashboard principal da marca, de forma nao-destrutiva.

- CSS do bloco e escopado sob .hab-scope (nao colide com o CSS do dashboard).
- JS do bloco roda dentro de um IIFE (nao vaza/colide variaveis globais).
- Chart.js ja esta carregado no dashboard (mesma versao 4.4.0) - nao reinjeta.
- Divisor de secao usa a classe nativa .section-titulo do dashboard.
- Descarta o <h2> "Panorama" (redundante); a faixa de KPIs vira a abertura do bloco.

Uso: python integrar_dashboard.py Apogeu
"""
import os, re, sys

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "output")
SCOPE = "hab-scope"
BANNER = "Diagnóstico Pedagógico por Habilidade"
# ancora: insere o bloco antes da 1a secao de MERCADO (agrupa mercado no fim)
ANCORA = '<p class="section-titulo">Posição na Rede Privada Municipal</p>'


def preparar_dashboard(html: str) -> str:
    """Ajustes de ordenamento/visual no dashboard base, antes de injetar o bloco."""
    # 1) funde o duplo banner: "Painel de Prioridades" + "Notas por Área Objetiva"
    html = re.sub(
        r'(?:<!--[^>]*-->\s*)?<p class="section-titulo" id="sec-prioridades">[^<]*</p>\s*'
        r'<div id="priorityCards"></div>\s*'
        r'<p class="section-titulo" id="sec-notas">([^<]*)</p>',
        r'<p class="section-titulo" id="sec-notas">\1</p>\n'
        r'<p class="sub-titulo">Painel de Prioridades</p>\n'
        r'<div id="priorityCards" style="margin-bottom:24px"></div>',
        html, count=1)
    # 2) remove o grafico de coluna redundante (mesmos dados do Radar ao lado)
    html = re.sub(
        r'<div class="card"><div class="card-titulo">[^<]*</div><div class="card-sub">.*?'
        r'<canvas id="chartAreas"></canvas></div></div>',
        "", html, count=1, flags=re.S)
    # 3) funde grid-3 + grid-2 numa linha de 3 colunas: Radar + %>=600 + %>=700
    html = html.replace('<div class="grid-3">', '<div class="grid-3cols">', 1)
    html = re.sub(r'</div>\s*<div class="grid-2">', "", html, count=1)
    # 4) remove chamada e registro do chartAreas no JS
    html = html.replace("buildAreas();", "", 1).replace("'chartAreas',", "", 1)
    # 4b) move a "Tabela Comparativa Detalhada" para o fim de "Notas por Área
    #     Objetiva", como bloco expansível (elimina a redundância visual sem
    #     perder o dado - ela resume Radar/%≥/Redação/Presença/Ranking).
    m = re.search(
        r'<p class="section-titulo">Tabela Comparativa Detalhada</p>\s*'
        r'<div class="card">\s*(<div class="card-sub"[^>]*>.*?</div>)\s*'
        r'(<div class="table-wrap"><table id="tabelaComparativa"></table></div>)\s*</div>',
        html, flags=re.S)
    if m:
        sub, tabela = m.group(1), m.group(2)
        html = html[:m.start()] + html[m.end():]
        bloco = (
            '<details class="tabela-exp">'
            '<summary>Ver tabela comparativa detalhada - todas as áreas por unidade</summary>'
            f'<div class="card">{sub}{tabela}</div></details>\n\n')
        html = html.replace(
            '<p class="section-titulo" id="sec-redacao">Redação</p>',
            bloco + '<p class="section-titulo" id="sec-redacao">Redação</p>', 1)
    # 5) CSS da nova grade de 3 colunas (responsiva)
    html = html.replace(
        "</style>",
        ".grid-3cols{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:16px}"
        "@media(max-width:900px){.grid-3cols{grid-template-columns:1fr}}"
        ".sub-titulo{display:flex;align-items:center;gap:12px;margin:0 0 18px;"
        "font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.10em;"
        "color:var(--texto-sec)}"
        ".sub-titulo::after{content:'';flex:1;height:1px;background:var(--cinza-borda)}"
        ".tabela-exp{margin:8px 0 0;border:1px solid var(--cinza-borda);border-radius:14px;"
        "background:#fff;box-shadow:0 1px 2px rgba(15,23,42,.04),0 6px 16px rgba(15,23,42,.05);overflow:hidden}"
        ".tabela-exp>summary{cursor:pointer;list-style:none;padding:16px 20px;font-weight:700;"
        "font-size:.9rem;color:var(--azul-m);display:flex;align-items:center;gap:10px}"
        ".tabela-exp>summary::-webkit-details-marker{display:none}"
        ".tabela-exp>summary::before{content:'\\25B8';font-size:.8rem;transition:transform .2s}"
        ".tabela-exp[open]>summary::before{transform:rotate(90deg)}"
        ".tabela-exp .card{border:0;box-shadow:none;background:transparent;margin:0;padding:0 20px 20px}"
        "</style>", 1)
    return html


def scope_css(css: str, scope: str) -> str:
    sc = "." + scope
    def scope_sels(sels: str) -> str:
        out = []
        for s in sels.split(","):
            s = s.strip()
            if not s:
                continue
            if s in (":root", "html", "body"):
                out.append(sc)
            elif s == "*":
                out.append(sc + " *")
            else:
                out.append(sc + " " + s)
        return ",".join(out)

    res, i, n = [], 0, len(css)
    while i < n:
        brace = css.find("{", i)
        if brace == -1:
            break
        header = css[i:brace].strip()
        if header.startswith("@"):
            depth, j = 0, brace
            while j < n:
                if css[j] == "{":
                    depth += 1
                elif css[j] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            inner = css[brace + 1:j]
            if header.startswith(("@media", "@supports")):
                res.append(header + "{" + scope_css(inner, scope) + "}")
            else:  # @keyframes/@font-face: sem escopo
                res.append(header + "{" + inner + "}")
            i = j + 1
        else:
            close = css.find("}", brace)
            res.append(scope_sels(header) + "{" + css[brace + 1:close] + "}")
            i = close + 1
    return "".join(res)


def construir_fragmento(hab_html: str) -> str:
    # 1) CSS (unico bloco <style> no <head> do standalone)
    css = re.search(r"<style>(.*?)</style>", hab_html, re.S).group(1)
    css_scoped = scope_css(css, SCOPE)

    # 2) Secoes do corpo: interior de .wrap (ate o </div> antes do #tip) + o proprio #tip
    m = re.search(r'<div class="wrap">(.*?)</div>\s*<div id="tip" class="tip"></div>', hab_html, re.S)
    secoes = m.group(1)
    # descarta o <h2> "Panorama" (mantem a desc como intro do bloco + os KPIs)
    secoes = re.sub(r'<h2><span class="tag">Panorama</span>[^<]*</h2>\s*', "", secoes, count=1)
    # intro do bloco: centraliza (consistencia com subtitulos do dashboard)
    secoes = re.sub(r'<p class="desc">', '<p class="desc hab-intro" '
                    'style="margin-left:auto;margin-right:auto;text-align:center;max-width:860px">',
                    secoes, count=1)
    tip = '<div id="tip" class="tip"></div>'

    # 3) JS do fim do corpo, sem a chamada de fonte (o dashboard ja define Chart.defaults)
    js = re.search(r'<div id="tip" class="tip"></div>\s*<script>(.*?)</script>', hab_html, re.S).group(1)
    js = js.replace("window.__CHARTFONT__();", "").strip()

    return (
        f'<p class="section-titulo">{BANNER}</p>\n'
        f"<style>{css_scoped}</style>\n"
        f'<div class="{SCOPE}">\n{secoes}\n{tip}\n</div>\n'
        f"<script>(function(){{\n{js}\n}})();</script>\n"
    )


def integrar(marca: str):
    safe = marca.replace(" ", "_").replace("é", "e").replace("ô", "o")
    hab_path = os.path.join(OUT, f"{safe}_Habilidades.html")
    dash_path = os.path.join(OUT, f"{safe}_Dashboard.html")
    dest_path = os.path.join(OUT, f"{safe}_Dashboard_Integrado.html")

    hab_html = open(hab_path, encoding="utf-8").read()
    dash_html = open(dash_path, encoding="utf-8").read()
    dash_html = preparar_dashboard(dash_html)
    if ANCORA not in dash_html:
        raise SystemExit(f"Ancora nao encontrada no dashboard de {marca}: {ANCORA}")

    fragmento = construir_fragmento(hab_html)
    dash_novo = dash_html.replace(ANCORA, fragmento + "\n" + ANCORA, 1)
    open(dest_path, "w", encoding="utf-8").write(dash_novo)
    print(f"OK -> {dest_path}  (+{len(dash_novo)-len(dash_html):,} bytes)")


if __name__ == "__main__":
    integrar(sys.argv[1] if len(sys.argv) > 1 else "Apogeu")
