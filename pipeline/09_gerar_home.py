# -*- coding: utf-8 -*-
"""09_gerar_home.py — Home consolidada da Rede Raiz (ENEM 2025).

Le o const DADOS e o BENCH_UNIDADE dos HTMLs de deploy do repo (fonte auditada)
e gera output/Home_Raiz.html: portal com KPIs de rede, cards por marca e
analises ineditas cross-marca (ranking de unidades, marcas vs referencias,
campeas por area, funil de excelencia).

Uso: python 09_gerar_home.py
Deploy: projeto Vercel proprio (enem-2025-raiz) — nao altera as URLs das marcas.
"""
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "output")
REPO = r"C:\Users\helio.barbosa\AppData\Local\Temp\enem-2025-dashboards"

MARCAS = {
    "Apogeu": {"html": "apogeu.html", "url": "https://apogeu-enem-deploy.vercel.app", "cor": "#2563eb", "escura": "#1a3a6e"},
    "QI Bilíngue": {"html": "qi-bilingue.html", "url": "https://qi-enem-deploy.vercel.app", "cor": "#7c3aed", "escura": "#4c1d95"},
    "Matriz Educação": {"html": "matriz-educacao.html", "url": "https://matriz-enem-deploy.vercel.app", "cor": "#15803d", "escura": "#0a4d2b"},
    "Colégio Leonardo da Vinci": {"html": "leonardo-da-vinci.html", "url": "https://leonardo-enem-deploy.vercel.app", "cor": "#c2560a", "escura": "#b44408"},
    "Cubo Global": {"html": "cubo-global.html", "url": "https://cubo-enem-deploy.vercel.app", "cor": "#0f9d96", "escura": "#097570"},
}
MULTIMARCAS_URL = "https://multimarcas-enem-deploy.vercel.app"

BRASIL = {"CN": 491.6, "CH": 502.9, "LC": 524.5, "MT": 513.8, "RD": 618.8}
TOP100 = {"CN": 660.5, "CH": 657.0, "LC": 643.6, "MT": 786.9, "RD": 873.0}
BRASIL_NG = round(sum(BRASIL.values()) / 5, 1)   # media das 5 areas
TOP100_NG = round(sum(TOP100.values()) / 5, 1)
AREAS = ["CN", "CH", "LC", "MT", "RD"]
AREA_NOME = {"CN": "Ciências da Natureza", "CH": "Ciências Humanas",
             "LC": "Linguagens e Códigos", "MT": "Matemática", "RD": "Redação"}


def fmt(v, dec=1):
    """numero pt-BR com virgula."""
    if v is None:
        return "-"
    s = f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s


def extrair(html, nome):
    m = re.search(r"const %s\s*=\s*(.*?);\n" % nome, html, re.S)
    return json.loads(m.group(1)) if m else None


def carregar():
    dados = {}
    for marca, cfg in MARCAS.items():
        h = open(os.path.join(REPO, cfg["html"]), encoding="utf-8").read()
        dados[marca] = {
            "DADOS": extrair(h, "DADOS"),
            "BENCH_UNIDADE": extrair(h, "BENCH_UNIDADE") or {},
        }
    return dados


def montar_modelo(dados):
    marcas = []
    unidades = []
    tot_insc = tot_pres = 0
    ng_s = ng_n = 0.0
    # funil de excelencia (ponderado por n de cada area)
    funil = {a: {"s600": 0.0, "s700": 0.0, "n": 0} for a in ["CN", "CH", "LC", "MT"]}
    red_800 = {"s": 0.0, "n": 0}

    for marca, cfg in MARCAS.items():
        g = dados[marca]["DADOS"]["geral"]
        unis = dados[marca]["DADOS"]["unidades"]
        bench = dados[marca]["BENCH_UNIDADE"]
        ngm = g.get("nota_geral") or {}
        marcas.append({
            "marca": marca, "cor": cfg["cor"], "escura": cfg["escura"], "url": cfg["url"],
            "n": g["n_inscritos"], "unidades": len(unis), "presenca": g["taxa_presenca"],
            "ng": ngm.get("media"), "mt": g["areas"]["MT"]["media"],
            "rd": g["redacao"]["media"], "p700mt": g["areas"]["MT"]["pct_700"],
        })
        tot_insc += g["n_inscritos"]
        tot_pres += g["n_presentes"]
        if ngm:
            ng_s += ngm["media"] * ngm["n"]
            ng_n += ngm["n"]
        for a in ["CN", "CH", "LC", "MT"]:
            ar = g["areas"][a]
            funil[a]["s600"] += ar["pct_600"] * ar["n"]
            funil[a]["s700"] += ar["pct_700"] * ar["n"]
            funil[a]["n"] += ar["n"]
        for u, d in unis.items():
            ung = d.get("nota_geral") or {}
            if not ung.get("media"):
                continue
            b = bench.get(u, {})
            mun = f"{b.get('municipio','')}" + (f" ({b['uf']})" if b.get("uf") else "")
            areas_u = {a: (d["areas"].get(a) or {}).get("media") for a in ["CN", "CH", "LC", "MT"]}
            areas_u["RD"] = (d.get("redacao") or {}).get("media")
            unidades.append({
                "unidade": u, "marca": marca, "cor": cfg["cor"], "mun": mun,
                "n": ung.get("n"), "ng": ung["media"], "areas": areas_u,
            })

    unidades.sort(key=lambda x: -x["ng"])
    marcas.sort(key=lambda x: -(x["ng"] or 0))
    rede = {
        "inscritos": tot_insc, "presentes": tot_pres,
        "presenca": tot_pres / tot_insc * 100 if tot_insc else 0,
        "ng": ng_s / ng_n if ng_n else None,
        "unidades": len(unidades), "marcas": len(marcas),
    }
    funil_out = {a: {"p600": v["s600"] / v["n"], "p700": v["s700"] / v["n"]}
                 for a, v in funil.items() if v["n"]}
    campeas = {}
    for a in AREAS:
        best = max(unidades, key=lambda u: (u["areas"].get(a) or 0))
        campeas[a] = {"unidade": best["unidade"], "marca": best["marca"],
                      "cor": best["cor"], "media": best["areas"][a]}
    return rede, marcas, unidades, campeas, funil_out


def gerar_html(rede, marcas, unidades, campeas, funil, logo_tag):
    css = """
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',system-ui,sans-serif;background:#f6f8fb;color:#0f172a;line-height:1.45}
header{background:linear-gradient(135deg,#fa820a 0%,#c45800 100%);height:110px;padding:0 32px;display:flex;align-items:center;box-shadow:0 4px 12px rgba(0,0,0,.12)}
header .divisor{width:1px;height:58px;background:rgba(255,255,255,.35);margin:0 22px}
header h1{color:#fff;font-size:1.25rem;font-weight:600;letter-spacing:.2px}
header .sub{color:rgba(255,255,255,.85);font-size:.8rem;font-weight:400;display:block;margin-top:2px}
.wrap{max-width:1180px;margin:0 auto;padding:8px 24px 64px}
.section-titulo{text-align:center;font-size:.92rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#c45800;margin:52px 0 22px;display:flex;align-items:center;gap:18px}
.section-titulo::before,.section-titulo::after{content:"";flex:1;height:1px;background:#e2e8f0}
.card{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:22px 24px;box-shadow:0 1px 2px rgba(15,23,42,.04),0 6px 16px rgba(15,23,42,.05)}
.card-sub{color:#64748b;font-size:.8rem}
.kpi-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px;margin-top:26px}
.kpi{background:#fff;border:1px solid #e2e8f0;border-top:3px solid #c45800;border-radius:14px;padding:18px 20px;box-shadow:0 1px 2px rgba(15,23,42,.04),0 6px 16px rgba(15,23,42,.05)}
.kpi-label{font-size:.7rem;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;color:#64748b}
.kpi-value{font-size:1.9rem;font-weight:700;color:#c45800;margin:2px 0}
.kpi-sub{font-size:.75rem;color:#94a3b8}
.grid-marcas{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}
.marca-card{display:flex;flex-direction:column;gap:12px;border-top:4px solid;text-decoration:none;color:inherit;transition:transform .15s,box-shadow .15s}
.marca-card:hover{transform:translateY(-3px);box-shadow:0 4px 8px rgba(15,23,42,.08),0 12px 28px rgba(15,23,42,.12)}
.marca-head{display:flex;justify-content:space-between;align-items:baseline}
.marca-nome{font-weight:700;font-size:1.02rem}
.marca-meta{font-size:.72rem;color:#94a3b8}
.marca-kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}
.mk{text-align:center}
.mk b{display:block;font-size:1.05rem}
.mk span{font-size:.62rem;letter-spacing:.6px;text-transform:uppercase;color:#94a3b8}
.marca-cta{font-size:.78rem;font-weight:600;text-align:right}
.rk-row{display:grid;grid-template-columns:34px minmax(150px,1.4fr) minmax(90px,1fr) 3fr 64px;gap:10px;align-items:center;padding:7px 0;border-bottom:1px solid #f1f5f9;font-size:.82rem}
.rk-row:last-child{border-bottom:none}
.rk-pos{color:#94a3b8;font-weight:700;text-align:right}
.rk-row.top3 .rk-pos{color:#0f172a}
.rk-uni{font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rk-uni small{display:block;font-weight:400;color:#94a3b8;font-size:.68rem}
.rk-chip{font-size:.66rem;font-weight:700;letter-spacing:.4px;padding:2px 8px;border-radius:99px;justify-self:start;white-space:nowrap}
.rk-bar-bg{background:#eef2f6;border-radius:6px;height:14px;position:relative;overflow:hidden}
.rk-bar{height:100%;border-radius:6px}
.rk-val{font-weight:700;text-align:right}
.ref-legend{display:flex;gap:20px;justify-content:flex-end;font-size:.72rem;color:#64748b;margin-top:10px}
.ref-legend i{display:inline-block;width:14px;height:0;border-top:2px dashed #94a3b8;vertical-align:middle;margin-right:5px}
.mb-row{display:grid;grid-template-columns:minmax(150px,1.2fr) 4fr 64px;gap:12px;align-items:center;padding:8px 0;font-size:.84rem}
.mb-bar-wrap{position:relative;background:#eef2f6;border-radius:6px;height:18px}
.mb-bar{height:100%;border-radius:6px}
.mb-ref{position:absolute;top:-4px;bottom:-4px;width:0;border-left:2px dashed #94a3b8}
.grid-camp{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px}
.camp-card{border-top:3px solid;text-align:center;padding:18px 14px}
.camp-area{font-size:.68rem;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#64748b}
.camp-uni{font-weight:700;font-size:1rem;margin:6px 0 1px}
.camp-marca{font-size:.72rem;color:#94a3b8}
.camp-val{font-size:1.45rem;font-weight:700;margin-top:6px}
.fx-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px}
.fx-card{padding:18px 20px}
.fx-area{font-size:.72rem;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#64748b;margin-bottom:10px}
.fx-line{display:flex;justify-content:space-between;font-size:.78rem;margin:8px 0 3px}
.fx-line b{font-size:.85rem}
.fx-bar-bg{background:#eef2f6;border-radius:5px;height:10px;overflow:hidden}
.fx-bar{height:100%;border-radius:5px}
footer{text-align:center;color:#94a3b8;font-size:.75rem;padding:26px 0;border-top:1px solid #e2e8f0;margin-top:56px}
footer a{color:#c45800;text-decoration:none;font-weight:600}
@media(max-width:720px){.rk-row{grid-template-columns:26px 1.4fr 2.2fr 52px}.rk-chip{display:none}header{padding:0 16px}}
"""
    # ---- cards de marca
    cards = []
    for m in marcas:
        cards.append(f"""
<a class="card marca-card" style="border-top-color:{m['cor']}" href="{m['url']}">
  <div class="marca-head"><span class="marca-nome">{m['marca']}</span>
    <span class="marca-meta">{m['unidades']} unidades &middot; {m['n']} inscritos &middot; presença {fmt(m['presenca'])}%</span></div>
  <div class="marca-kpis">
    <div class="mk"><b style="color:{m['cor']}">{fmt(m['ng'])}</b><span>Nota Geral</span></div>
    <div class="mk"><b>{fmt(m['mt'])}</b><span>Matemática</span></div>
    <div class="mk"><b>{fmt(m['rd'])}</b><span>Redação</span></div>
    <div class="mk"><b>{fmt(m['p700mt'])}%</b><span>&ge;700 MT</span></div>
  </div>
  <div class="marca-cta" style="color:{m['cor']}">Abrir dashboard &rarr;</div>
</a>""")
    card_mm = f"""
<a class="card marca-card" style="border-top-color:#c45800" href="{MULTIMARCAS_URL}">
  <div class="marca-head"><span class="marca-nome">Multimarcas - Comparativo</span>
    <span class="marca-meta">5 marcas lado a lado</span></div>
  <div class="card-sub">Evolução comparativa, redação, mercado local e diagnóstico por habilidade das 5 marcas em uma única tela.</div>
  <div class="marca-cta" style="color:#c45800">Abrir comparativo &rarr;</div>
</a>"""

    # ---- ranking de unidades (escala comum)
    ng_vals = [u["ng"] for u in unidades]
    lo, hi = min(ng_vals) - 30, max(ng_vals) + 10
    rk_rows = []
    for i, u in enumerate(unidades, 1):
        w = (u["ng"] - lo) / (hi - lo) * 100
        top = " top3" if i <= 3 else ""
        rk_rows.append(f"""
<div class="rk-row{top}">
  <div class="rk-pos">{i}º</div>
  <div class="rk-uni">{u['unidade']}<small>{u['mun']} &middot; {u['n']} alunos</small></div>
  <span class="rk-chip" style="background:{u['cor']}14;color:{u['cor']};border:1px solid {u['cor']}45">{u['marca']}</span>
  <div class="rk-bar-bg"><div class="rk-bar" style="width:{w:.1f}%;background:{u['cor']}{'' if i<=3 else 'cc'}"></div></div>
  <div class="rk-val">{fmt(u['ng'])}</div>
</div>""")

    # ---- marcas vs referencias (escala 450-900 com refs)
    mb_lo, mb_hi = 450, 900
    def pos(v):
        return (v - mb_lo) / (mb_hi - mb_lo) * 100
    mb_rows = []
    for m in marcas:
        mb_rows.append(f"""
<div class="mb-row">
  <div style="font-weight:600">{m['marca']}</div>
  <div class="mb-bar-wrap">
    <div class="mb-bar" style="width:{pos(m['ng']):.1f}%;background:{m['cor']}"></div>
    <div class="mb-ref" style="left:{pos(BRASIL_NG):.1f}%"></div>
    <div class="mb-ref" style="left:{pos(TOP100_NG):.1f}%"></div>
  </div>
  <div class="rk-val" style="color:{m['cor']}">{fmt(m['ng'])}</div>
</div>""")

    # ---- campeas por area
    camp_cards = []
    for a in AREAS:
        c = campeas[a]
        camp_cards.append(f"""
<div class="card camp-card" style="border-top-color:{c['cor']}">
  <div class="camp-area">{AREA_NOME[a]}</div>
  <div class="camp-uni">{c['unidade']}</div>
  <div class="camp-marca">{c['marca']}</div>
  <div class="camp-val" style="color:{c['cor']}">{fmt(c['media'])}</div>
</div>""")

    # ---- funil de excelencia
    fx_cards = []
    for a in ["CN", "CH", "LC", "MT"]:
        f6, f7 = funil[a]["p600"], funil[a]["p700"]
        fx_cards.append(f"""
<div class="card fx-card">
  <div class="fx-area">{AREA_NOME[a]}</div>
  <div class="fx-line"><span>Nota &ge; 600</span><b>{fmt(f6)}%</b></div>
  <div class="fx-bar-bg"><div class="fx-bar" style="width:{f6:.1f}%;background:#c4580999"></div></div>
  <div class="fx-line"><span>Nota &ge; 700</span><b>{fmt(f7)}%</b></div>
  <div class="fx-bar-bg"><div class="fx-bar" style="width:{f7:.1f}%;background:#c45800"></div></div>
</div>""")

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<title>Rede Raiz - ENEM 2025</title>
<style>{css}</style>
</head>
<body>
<header>
  {logo_tag}
  <div class="divisor"></div>
  <h1>ENEM 2025 - Análise da Rede<span class="sub">Visão consolidada das 5 marcas e portal dos dashboards</span></h1>
</header>
<div class="wrap">

<div class="kpi-row">
  <div class="kpi"><div class="kpi-label">Inscritos</div><div class="kpi-value">{rede['inscritos']}</div><div class="kpi-sub">{rede['marcas']} marcas &middot; {rede['unidades']} unidades</div></div>
  <div class="kpi"><div class="kpi-label">Presentes 2 dias</div><div class="kpi-value">{rede['presentes']}</div><div class="kpi-sub">{fmt(rede['presenca'])}% de presença</div></div>
  <div class="kpi"><div class="kpi-label">Nota Geral da Rede</div><div class="kpi-value">{fmt(rede['ng'])}</div><div class="kpi-sub">média 5 áreas por aluno &middot; Brasil: {fmt(BRASIL_NG)}</div></div>
  <div class="kpi"><div class="kpi-label">Melhor marca</div><div class="kpi-value" style="font-size:1.35rem;line-height:2.4rem">{marcas[0]['marca']}</div><div class="kpi-sub">Nota Geral {fmt(marcas[0]['ng'])}</div></div>
  <div class="kpi"><div class="kpi-label">Melhor unidade</div><div class="kpi-value" style="font-size:1.35rem;line-height:2.4rem">{unidades[0]['unidade']}</div><div class="kpi-sub">{unidades[0]['marca']} &middot; {fmt(unidades[0]['ng'])}</div></div>
</div>

<p class="section-titulo">Dashboards por Marca</p>
<div class="grid-marcas">{''.join(cards)}{card_mm}</div>

<p class="section-titulo">Ranking das Unidades da Rede</p>
<div class="card">
  <div class="card-sub" style="margin-bottom:14px">As {rede['unidades']} unidades da rede ordenadas pela Nota Geral (média das 5 áreas por aluno, presença completa e redação válida).</div>
  {''.join(rk_rows)}
</div>

<p class="section-titulo">Marcas vs Referências Nacionais</p>
<div class="card">
  <div class="card-sub" style="margin-bottom:6px">Nota Geral de cada marca na régua nacional. Linhas tracejadas: Brasil {fmt(BRASIL_NG)} e Top 100 BR {fmt(TOP100_NG)} (média das 5 áreas).</div>
  {''.join(mb_rows)}
  <div class="ref-legend"><span><i></i>Brasil {fmt(BRASIL_NG)}</span><span><i></i>Top 100 BR {fmt(TOP100_NG)}</span></div>
</div>

<p class="section-titulo">Melhor Unidade da Rede por Área</p>
<div class="grid-camp">{''.join(camp_cards)}</div>

<p class="section-titulo">Excelência Acadêmica da Rede</p>
<div class="card-sub" style="text-align:center;max-width:760px;margin:-8px auto 16px">Percentual de alunos da rede (todas as marcas) com nota acima dos cortes de 600 e 700 pontos, por área objetiva.</div>
<div class="fx-grid">{''.join(fx_cards)}</div>

</div>
<footer>Diretoria de Performance Pedagógica &nbsp;|&nbsp; INEP: Microdados do Enem &nbsp;|&nbsp; Julho 2026<br>
<a href="{MULTIMARCAS_URL}">Comparativo Multimarcas</a></footer>
</body>
</html>"""
    return html


def main():
    logo_path = os.path.join(BASE, "logos", "raiz.imgtag")
    if not os.path.exists(logo_path):
        sys.exit(f"Logo Raiz nao encontrada: {logo_path}")
    logo_tag = open(logo_path, encoding="utf-8").read()
    dados = carregar()
    rede, marcas, unidades, campeas, funil = montar_modelo(dados)
    html = gerar_html(rede, marcas, unidades, campeas, funil, logo_tag)
    dest = os.path.join(OUT, "Home_Raiz.html")
    open(dest, "w", encoding="utf-8").write(html)
    print(f"OK -> {dest} ({len(html):,} chars) | rede NG={rede['ng']:.1f} "
          f"unidades={rede['unidades']} inscritos={rede['inscritos']}")


if __name__ == "__main__":
    main()
