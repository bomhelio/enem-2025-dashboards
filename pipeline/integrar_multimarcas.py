# -*- coding: utf-8 -*-
"""
integrar_multimarcas.py
Injeta o bloco de análise por HABILIDADE (Multimarcas_Habilidades.html) dentro do
dashboard multimarcas, com a MESMA lógica dos dashboards de marca (integrar_dashboard):
- CSS do bloco escopado sob .hab-scope (não colide com o CSS do dashboard).
- JS do bloco em IIFE (não vaza variáveis globais).
- Chart.js e Chart.defaults.font já definidos no dashboard (não reinjeta).
- Banner divisor usa a classe nativa .section-titulo.
- Âncora: antes da 1a seção de MERCADO (agrupa o pedagógico antes do mercado).

Uso: python integrar_multimarcas.py
"""
import os, re
from integrar_dashboard import scope_css, SCOPE

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "output")
REPO_MM = r"C:\Users\helio.barbosa\AppData\Local\Temp\enem-2025-dashboards\multimarcas.html"
BANNER = "Diagnóstico Pedagógico por Habilidade"
HAB = os.path.join(OUT, "Multimarcas_Habilidades.html")
DEST = os.path.join(OUT, "Multimarcas_Dashboard_Integrado.html")


def construir_fragmento(hab_html: str) -> str:
    css = re.search(r"<style>(.*?)</style>", hab_html, re.S).group(1)
    css_scoped = scope_css(css, SCOPE)
    secoes = re.search(r'<div class="wrap">(.*?)</div>\s*<div id="tip" class="tip"></div>',
                       hab_html, re.S).group(1)
    tip = '<div id="tip" class="tip"></div>'
    js = re.search(r'<div id="tip" class="tip"></div>\s*<script>(.*?)</script>',
                   hab_html, re.S).group(1).strip()
    return (
        f'<p class="section-titulo">{BANNER}</p>\n'
        f"<style>{css_scoped}</style>\n"
        f'<div class="{SCOPE}">\n{secoes}\n{tip}\n</div>\n'
        f"<script>(function(){{\n{js}\n}})();</script>\n"
    )


def integrar():
    hab_html = open(HAB, encoding="utf-8").read()
    dash = open(REPO_MM, encoding="utf-8").read()

    m = re.search(r'<p class="section-titulo">Posição no Mercado Local[^<]*</p>', dash)
    if not m:
        raise SystemExit("Âncora de mercado não encontrada no multimarcas.html")

    frag = construir_fragmento(hab_html)
    novo = dash[:m.start()] + frag + "\n" + dash[m.start():]
    open(DEST, "w", encoding="utf-8").write(novo)
    print(f"OK -> {DEST}  (+{len(novo)-len(dash):,} bytes)")


if __name__ == "__main__":
    integrar()
