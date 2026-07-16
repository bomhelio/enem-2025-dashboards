# -*- coding: utf-8 -*-
"""09_gerar_home.py — Home consolidada da Rede Raiz (ENEM 2025).

Identidade visual: réplica da home da Análise UERJ (uerj-eq1-2027.vercel.app):
header navy com wordmark do exame, stats em cards, section-titles à esquerda
com hairline, faixas hist-link/top-details e cards de marca com tile de logo.

Le o const DADOS e o BENCH_UNIDADE dos HTMLs de deploy do repo (fonte auditada)
e gera output/Home_Raiz.html com KPIs de rede, analises cross-marca e o portal
dos dashboards.

Uso: python 09_gerar_home.py
Deploy: projeto Vercel proprio (enem-2025-raiz) — nao altera as URLs das marcas.
"""
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "output")
LOGOS = os.path.join(BASE, "logos")
REPO = r"C:\Users\helio.barbosa\AppData\Local\Temp\enem-2025-dashboards"

MARCAS = {
    "Apogeu": {"html": "apogeu.html", "url": "https://apogeu-enem-deploy.vercel.app",
               "cor": "#2563eb", "tile": "#1a3a6e", "logo": "Apogeu.imgtag"},
    "QI Bilíngue": {"html": "qi-bilingue.html", "url": "https://qi-enem-deploy.vercel.app",
                    "cor": "#7c3aed", "tile": "#4c1d95", "logo": "QI_Bilíngue.imgtag"},
    "Matriz Educação": {"html": "matriz-educacao.html", "url": "https://matriz-enem-deploy.vercel.app",
                        "cor": "#15803d", "tile": "#0a4d2b", "logo": "Matriz_Educação.imgtag"},
    "Colégio Leonardo da Vinci": {"html": "leonardo-da-vinci.html", "url": "https://leonardo-enem-deploy.vercel.app",
                                  "cor": "#c2560a", "tile": "#b44408", "logo": "Colegio_Leonardo_da_Vinci.imgtag"},
    "Cubo Global": {"html": "cubo-global.html", "url": "https://cubo-enem-deploy.vercel.app",
                    "cor": "#0f9d96", "tile": "#097570", "logo": "Cubo_Global.imgtag"},
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


def milhar(v):
    return f"{v:,}".replace(",", ".")


def logo_src(fname):
    """extrai o data-URI do .imgtag (logo branca extraida dos dashboards)."""
    path = os.path.join(LOGOS, fname)
    if not os.path.exists(path):
        return None
    tag = open(path, encoding="utf-8").read()
    m = re.search(r'src="(data:image/png;base64,[^"]+)"', tag)
    return m.group(1) if m else None


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
    funil = {a: {"s600": 0.0, "s700": 0.0, "n": 0} for a in AREAS}

    for marca, cfg in MARCAS.items():
        g = dados[marca]["DADOS"]["geral"]
        unis = dados[marca]["DADOS"]["unidades"]
        bench = dados[marca]["BENCH_UNIDADE"]
        ngm = g.get("nota_geral") or {}
        marcas.append({
            "marca": marca, "cor": cfg["cor"], "tile": cfg["tile"], "url": cfg["url"],
            "logo": logo_src(cfg["logo"]),
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
        red = g["redacao"]
        funil["RD"]["s600"] += red["pct_600"] * red["n"]
        funil["RD"]["s700"] += red["pct_700"] * red["n"]
        funil["RD"]["n"] += red["n"]
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


CSS = """
    :root { --ink:#1e293b; --muted:#64748b; --line:#e2e8f0; --bg:#f1f5f9; }
    * { box-sizing: border-box; }
    body { margin:0; background:var(--bg); color:var(--ink); font-family:"Segoe UI", system-ui, Arial, sans-serif; }
    header { background:linear-gradient(135deg,#1e293b 0%,#0a1940 100%); box-shadow:0 4px 12px rgba(0,0,0,.25); }
    .hero { max-width:1120px; margin:0 auto; min-height:96px; padding:0 24px; display:flex; align-items:center; gap:18px; }
    .hero h1 { margin:0; color:#fff; font-size:24px; font-weight:800; letter-spacing:-.01em; }
    .hero p { margin:0; color:rgba(255,255,255,.75); font-size:14px; }
    .hero-divider { width:1px; height:44px; background:rgba(255,255,255,.35); flex-shrink:0; }
    main { max-width:1120px; margin:0 auto; padding:28px 24px 40px; }
    .stats { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:12px; }
    .stat { background:#fff; border:1px solid var(--line); border-radius:14px; padding:14px 16px; box-shadow:0 1px 2px rgba(15,23,42,.04); }
    .stat small { display:block; color:var(--muted); font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:.06em; margin-bottom:7px; }
    .stat strong { display:block; color:#0f172a; font-size:22px; font-weight:800; line-height:1.1; font-variant-numeric:tabular-nums; }
    .stat strong.txt { font-size:17px; line-height:1.25; min-height:38px; }
    .stat span { display:block; margin-top:5px; color:var(--muted); font-size:12px; }
    .section-title { margin:30px 0 14px; color:#334155; font-size:14px; font-weight:800; letter-spacing:.09em; text-transform:uppercase; display:flex; align-items:center; gap:12px; }
    .section-title::after { content:""; flex:1; height:1px; background:var(--line); }
    .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:14px; }
    a.card { display:flex; align-items:center; gap:16px; min-height:104px; padding:16px 18px; background:#fff; border:1px solid var(--line); border-radius:14px; color:inherit; text-decoration:none; box-shadow:0 1px 2px rgba(15,23,42,.04); transition:box-shadow .15s ease, border-color .15s ease; }
    a.card:hover { border-color:var(--brand); box-shadow:0 10px 24px color-mix(in srgb, var(--brand) 18%, transparent); }
    .mark { width:104px; height:64px; border-radius:12px; display:grid; place-items:center; padding:0 10px; color:#fff; font-weight:800; font-size:20px; flex:0 0 auto; }
    .mark img { max-height:44px; max-width:84px; width:auto; display:block; }
    .card-body { display:block; }
    .name { display:block; font-size:17px; font-weight:800; color:#0f172a; }
    .meta { display:block; margin-top:4px; color:var(--muted); font-size:13px; }
    .top-details { margin-top:10px; }
    .top-details summary { list-style:none; cursor:pointer; display:flex; align-items:center; justify-content:space-between; gap:14px; padding:14px 18px; background:#fff; border:1px solid var(--line); border-radius:14px; color:#334155; font-size:13px; box-shadow:0 1px 2px rgba(15,23,42,.04); transition:border-color .15s ease; }
    .top-details summary::-webkit-details-marker { display:none; }
    .top-details summary:hover { border-color:#1e293b; }
    .top-details summary b { color:#0f172a; }
    .top-details[open] .caret { transform:rotate(180deg); }
    .caret { transition:transform .15s ease; }
    .top-panel { margin-top:10px; background:#fff; border:1px solid var(--line); border-radius:14px; padding:6px 18px 14px; box-shadow:0 1px 2px rgba(15,23,42,.04); overflow-x:auto; }
    .top-table { width:100%; border-collapse:collapse; font-size:13px; }
    .top-table th, .top-table td { padding:8px 12px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
    .top-table tbody tr:last-child td { border-bottom:0; }
    .top-table th { color:#64748b; font-size:11px; background:#f8fafc; font-weight:600; text-transform:uppercase; letter-spacing:.05em; }
    .top-table th.num, .top-table td.num { text-align:right; white-space:nowrap; }
    .top-brand { font-weight:600; color:#0f172a; white-space:nowrap; }
    .top-unit { font-weight:500; color:#334155; }
    .top-score { font-weight:600; color:#0f172a; font-variant-numeric:tabular-nums; }
    .top-local { color:var(--muted); font-size:12px; font-weight:400; }
    .top-flag { display:inline-block; margin-right:8px; background:#f0fdf4; border:1px solid #bbf7d0; color:#166534; border-radius:999px; padding:2px 8px; font-size:10.5px; font-weight:700; white-space:nowrap; }
    .hist-link { display:flex; align-items:center; justify-content:space-between; gap:14px; margin-top:14px; padding:14px 18px; background:#fff; border:1px solid var(--line); border-radius:14px; color:#334155; text-decoration:none; font-size:13px; box-shadow:0 1px 2px rgba(15,23,42,.04); transition:border-color .15s ease; }
    .hist-link:hover { border-color:#1e293b; }
    .hist-link b { color:#0f172a; }
    .hist-arrow { font-weight:800; color:#0f172a; }
    .panel { background:#fff; border:1px solid var(--line); border-radius:14px; padding:16px 18px; box-shadow:0 1px 2px rgba(15,23,42,.04); }
    .panel-note { margin:0 0 12px; color:var(--muted); font-size:12.5px; }
    .mb-row { display:grid; grid-template-columns:200px 1fr 64px; gap:14px; align-items:center; padding:7px 0; font-size:13px; }
    .mb-name { font-weight:600; color:#0f172a; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .mb-track { position:relative; background:#eef2f6; border-radius:6px; height:16px; }
    .mb-bar { height:100%; border-radius:6px; }
    .mb-ref { position:absolute; top:-4px; bottom:-4px; width:0; border-left:2px dashed #94a3b8; }
    .mb-val { font-weight:600; color:#0f172a; text-align:right; font-variant-numeric:tabular-nums; }
    .ref-legend { display:flex; gap:20px; justify-content:flex-end; font-size:12px; color:var(--muted); margin-top:10px; }
    .ref-legend i { display:inline-block; width:14px; height:0; border-top:2px dashed #94a3b8; vertical-align:middle; margin-right:5px; }
    footer { color:var(--muted); font-size:12px; text-align:center; padding:20px 0 4px; }
    @media (max-width: 900px) { .stats { grid-template-columns:repeat(2,1fr); } .mb-row { grid-template-columns:120px 1fr 56px; } }
    @media (max-width: 600px) { .stats, .grid { grid-template-columns:1fr; } }
"""


def gerar_html(rede, marcas, unidades, raiz_logo):
    # ---- stats (Resultado geral da rede)
    melhor = marcas[0]
    melhor_uni = unidades[0]
    stats = [
        ("Rede Raiz", milhar(rede["inscritos"]) + " alunos", False,
         f"{rede['marcas']} marcas · {rede['unidades']} unidades no ENEM 2025"),
        ("Presença 2 dias", fmt(rede["presenca"]) + "%", False,
         f"{milhar(rede['presentes'])} presentes"),
        ("Nota geral da rede", fmt(rede["ng"]), False,
         f"Brasil: {fmt(BRASIL_NG)} · Top 100 BR: {fmt(TOP100_NG)}"),
        ("Melhor marca", melhor["marca"], True, f"Nota Geral {fmt(melhor['ng'])}"),
        ("Melhor unidade", melhor_uni["unidade"], True,
         f"{melhor_uni['marca']} · {fmt(melhor_uni['ng'])}"),
    ]
    stats_html = "\n".join(
        f'      <div class="stat"><small>{label}</small>'
        f'<strong{" class=\"txt\"" if txt else ""}>{value}</strong><span>{note}</span></div>'
        for label, value, txt, note in stats
    )

    # ---- ranking das unidades (top-details)
    rk_rows = []
    for i, u in enumerate(unidades, 1):
        flag = '<span class="top-flag">Top 3</span>' if i <= 3 else ""
        rk_rows.append(
            f'            <tr><td class="num top-score">{i}º</td>'
            f'<td class="top-unit">{flag}{u["unidade"]}</td>'
            f'<td class="top-brand" style="border-left:3px solid {u["cor"]};padding-left:11px">{u["marca"]}</td>'
            f'<td class="top-local">{u["mun"]}</td>'
            f'<td class="num">{u["n"]}</td>'
            f'<td class="num top-score">{fmt(u["ng"])}</td></tr>'
        )

    # ---- marcas vs referencias (regua 450-900)
    mb_lo, mb_hi = 450, 900

    def pos(v):
        return (v - mb_lo) / (mb_hi - mb_lo) * 100

    mb_rows = []
    for m in marcas:
        mb_rows.append(f"""      <div class="mb-row">
        <div class="mb-name">{m['marca']}</div>
        <div class="mb-track">
          <div class="mb-bar" style="width:{pos(m['ng']):.1f}%;background:{m['cor']}"></div>
          <div class="mb-ref" style="left:{pos(BRASIL_NG):.1f}%"></div>
          <div class="mb-ref" style="left:{pos(TOP100_NG):.1f}%"></div>
        </div>
        <div class="mb-val">{fmt(m['ng'])}</div>
      </div>""")

    # ---- cards de marca (portal)
    cards = []
    raiz_img = f'<img src="{raiz_logo}" alt="Rede Raiz" />' if raiz_logo else "Raiz"
    cards.append(f"""      <a class="card" style="--brand:#c45800" href="{MULTIMARCAS_URL}">
        <span class="mark" style="background:linear-gradient(135deg,#fa820a 0%,#c45800 100%)">{raiz_img}</span>
        <span class="card-body">
          <span class="name">Multimarcas</span>
          <span class="meta">{milhar(rede['inscritos'])} alunos · 5 marcas comparadas · abrir dashboard</span>
        </span>
      </a>""")
    for m in sorted(marcas, key=lambda x: -x["n"]):
        img = f'<img src="{m["logo"]}" alt="{m["marca"]}" />' if m["logo"] else m["marca"]
        cards.append(f"""      <a class="card" style="--brand:{m['cor']}" href="{m['url']}">
        <span class="mark" style="background:{m['tile']}">{img}</span>
        <span class="card-body">
          <span class="name">{m['marca']}</span>
          <span class="meta">{m['n']} alunos · Nota Geral {fmt(m['ng'])} · abrir dashboard</span>
        </span>
      </a>""")

    html = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="robots" content="noindex, nofollow" />
  <title>Dashboards ENEM 2025 | Rede Raiz</title>
  <style>{CSS}</style>
</head>
<body>
  <header>
    <div class="hero">
      <h1>ENEM 2025</h1>
      <div class="hero-divider"></div>
      <p>Análise de Performance · Microdados INEP · dashboards por marca</p>
    </div>
  </header>
  <main>
    <p class="section-title">Resultado geral da rede</p>
    <section class="stats">
{stats_html}
    </section>
    <details class="top-details">
      <summary>
        <span><b>Ranking das unidades</b> · as {rede['unidades']} unidades da rede ordenadas pela Nota Geral (média das 5 áreas por aluno)</span>
        <span class="hist-arrow caret">▾</span>
      </summary>
      <div class="top-panel">
        <table class="top-table">
          <thead><tr><th class="num">Pos.</th><th>Unidade</th><th>Marca</th><th>Município</th><th class="num">Alunos</th><th class="num">Nota Geral</th></tr></thead>
          <tbody>
{chr(10).join(rk_rows)}
          </tbody>
        </table>
      </div>
    </details>
    <p class="section-title">Marcas vs referências nacionais</p>
    <div class="panel">
      <p class="panel-note">Nota Geral de cada marca na régua de 450 a 900 pontos. Linhas tracejadas: Brasil {fmt(BRASIL_NG)} e Top 100 BR {fmt(TOP100_NG)} (média das 5 áreas).</p>
{chr(10).join(mb_rows)}
      <div class="ref-legend"><span><i></i>Brasil {fmt(BRASIL_NG)}</span><span><i></i>Top 100 BR {fmt(TOP100_NG)}</span></div>
    </div>
    <p class="section-title">Dashboards por marca</p>
    <section class="grid">
{chr(10).join(cards)}
    </section>
    <footer>Diretoria de Performance Pedagógica · INEP: Microdados do Enem 2025 · Julho 2026</footer>
  </main>
</body>
</html>
"""
    return html


def main():
    raiz_logo = logo_src("raiz.imgtag")
    dados = carregar()
    rede, marcas, unidades, _campeas, _funil = montar_modelo(dados)
    html = gerar_html(rede, marcas, unidades, raiz_logo)
    dest = os.path.join(OUT, "Home_Raiz.html")
    open(dest, "w", encoding="utf-8").write(html)
    print(f"OK -> {dest} ({len(html):,} chars) | rede NG={rede['ng']:.1f} "
          f"unidades={rede['unidades']} inscritos={rede['inscritos']}")


if __name__ == "__main__":
    main()
