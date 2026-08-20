"""
16_gerar_home_concorrencia.py
Home do portal de Inteligência Competitiva - mesma identidade das homes
UERJ e ENEM (header navy, stat cards, cards de marca com tile e logo).

Lista automaticamente as marcas de concorrencia_config.py que já têm
`output/concorrencia_{slug}.json` gerado. Minimalista por decisão do
usuário: as análises moram nas telas de cada marca.

Saída: output/Concorrencia_Home.html (deploy: index.html do projeto)
"""

import json
import os
import re
from datetime import date

from config import OUTPUT_DIR
from concorrencia_config import MARCAS

LOGOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logos")


def milhar(v: int) -> str:
    return f"{v:,}".replace(",", ".")


def _pt(v: float) -> str:
    return f"{v:.1f}".replace(".", ",")


def logo_src(fname: str):
    path = os.path.join(LOGOS, fname or "")
    if not fname or not os.path.exists(path):
        return None
    tag = open(path, encoding="utf-8").read()
    m = re.search(r'src="(data:image/png;base64,[^"]+)"', tag)
    return m.group(1) if m else None


def lista_redes(nomes: list[str]) -> str:
    if len(nomes) <= 1:
        return nomes[0] if nomes else ""
    return ", ".join(nomes[:-1]) + " e " + nomes[-1]


def main():
    marcas = []
    total_unidades = total_alunos = 0
    redes_concorrentes: set[str] = set()
    for marca, cfg in MARCAS.items():
        path = os.path.join(OUTPUT_DIR, f"concorrencia_{cfg['slug']}.json")
        if not os.path.exists(path):
            continue
        data = json.load(open(path, encoding="utf-8"))
        alunos = sum(u["n_inscritos"] for u in data["unidades"])
        ng = (data["redes"][marca].get("nota_geral") or {}).get("media")
        ng_ref2024 = False
        if ng is None:
            # marca sem vínculo no ENEM 2025 (fora do Censo 2025, caso UAU):
            # o card mostra a referência 2024 vinda do histórico
            hist_path = os.path.join(OUTPUT_DIR, f"concorrencia_historico_{cfg['slug']}.json")
            if os.path.exists(hist_path):
                hist = json.load(open(hist_path, encoding="utf-8"))
                ng = ((hist.get("redes", {}).get(marca) or {}).get("2024") or {}).get("NG")
                ng_ref2024 = ng is not None
        marcas.append({
            "marca": marca, "cfg": cfg,
            "n_unidades": len(data["unidades"]),
            "alunos": alunos,
            "ng": ng, "ng_ref2024": ng_ref2024,
            "redes": list(cfg["concorrentes"]),
            "logo": logo_src(cfg.get("logo")),
        })
        total_unidades += len(data["unidades"])
        total_alunos += alunos
        redes_concorrentes.update(cfg["concorrentes"])

    cards = []
    for m in marcas:
        img = f'<img src="{m["logo"]}" alt="{m["marca"]}" />' if m["logo"] else m["cfg"]["curto"]
        ng_txt = "NG -" if m["ng"] is None else (
            f"NG {_pt(m['ng'])} <em>(ENEM 2024)</em>" if m["ng_ref2024"] else f"NG {_pt(m['ng'])}")
        selo = (f'<span class="meta selo">{m["cfg"]["selo_card"]}</span>'
                if m["cfg"].get("selo_card") else "")
        cards.append(f"""      <a class="card" style="--brand:{m['cfg']['cor']}" href="{m['cfg']['slug']}">
        <span class="mark" style="background:{m['cfg']['tile']}">{img}</span>
        <span class="card-body">
          <span class="name">{m['marca']}</span>
          <span class="meta">vs {lista_redes(m['redes'])}</span>
          <span class="meta">{m['n_unidades']} unidades comparadas · {milhar(m['alunos'])} alunos · {ng_txt}</span>
{selo}
        </span>
      </a>""")

    stats = [
        ("Marcas analisadas", str(len(marcas)), "telas ativas no portal"),
        ("Redes concorrentes", str(len(redes_concorrentes)), lista_redes(sorted(redes_concorrentes))),
        ("Unidades comparadas", milhar(total_unidades), "nossas + concorrentes com dados 2025"),
        ("Alunos analisados", milhar(total_alunos), "inscritos no ENEM 2025"),
    ]
    stats_html = "".join(
        f'<div class="stat"><small>{t}</small><strong>{v}</strong><span>{s}</span></div>'
        for t, v, s in stats)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<title>ENEM 2025 · Inteligência Competitiva</title>
<style>
  :root {{ --ink:#1e293b; --muted:#64748b; --line:#e2e8f0; --bg:#f1f5f9; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink); font-family:"Segoe UI", system-ui, Arial, sans-serif; }}
  header {{ background:linear-gradient(135deg,#1e293b 0%,#0a1940 100%); box-shadow:0 4px 12px rgba(0,0,0,.25); }}
  .hero {{ max-width:1120px; margin:0 auto; min-height:96px; padding:0 24px; display:flex; align-items:center; gap:18px; }}
  .hero .wordmark {{ color:#fff; font-size:20px; font-weight:800; letter-spacing:.02em; white-space:nowrap; }}
  .hero-divider {{ width:1px; height:44px; background:rgba(255,255,255,.35); flex-shrink:0; }}
  .hero h1 {{ margin:0; color:#fff; font-size:24px; font-weight:800; letter-spacing:-.01em; }}
  .hero p {{ margin:2px 0 0; color:rgba(255,255,255,.75); font-size:14px; }}
  main {{ max-width:1120px; margin:0 auto; padding:28px 24px 40px; }}
  .stats {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; }}
  @media (max-width:900px){{ .stats {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} }}
  .stat {{ background:#fff; border:1px solid var(--line); border-radius:14px; padding:14px 16px; box-shadow:0 1px 2px rgba(15,23,42,.04); }}
  .stat small {{ display:block; color:var(--muted); font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:.06em; margin-bottom:7px; }}
  .stat strong {{ display:block; color:#0f172a; font-size:22px; font-weight:800; line-height:1.1; font-variant-numeric:tabular-nums; }}
  .stat span {{ display:block; margin-top:5px; color:var(--muted); font-size:12px; }}
  .section-title {{ margin:30px 0 14px; color:#334155; font-size:14px; font-weight:800; letter-spacing:.09em; text-transform:uppercase; display:flex; align-items:center; gap:12px; }}
  .section-title::after {{ content:""; flex:1; height:1px; background:var(--line); }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(340px,1fr)); gap:14px; }}
  a.card {{ display:flex; align-items:center; gap:16px; min-height:104px; padding:16px 18px; background:#fff; border:1px solid var(--line); border-radius:14px; color:inherit; text-decoration:none; box-shadow:0 1px 2px rgba(15,23,42,.04); transition:box-shadow .15s ease, border-color .15s ease; }}
  a.card:hover {{ border-color:var(--brand); box-shadow:0 10px 24px color-mix(in srgb, var(--brand) 18%, transparent); }}
  .mark {{ width:104px; height:64px; border-radius:12px; display:grid; place-items:center; padding:0 10px; color:#fff; font-weight:800; font-size:20px; flex:0 0 auto; }}
  .mark img {{ max-height:44px; max-width:84px; width:auto; display:block; }}
  .card-body {{ display:block; }}
  .name {{ display:block; font-size:17px; font-weight:800; color:#0f172a; }}
  .meta {{ display:block; margin-top:4px; color:var(--muted); font-size:13px; }}
  .meta em {{ font-style:normal; color:#b45309; font-weight:700; }}
  .meta.selo {{ display:inline-block; margin-top:6px; font-size:11px; font-weight:800; letter-spacing:.03em; color:#92400e; background:#fef3c7; border:1px solid #fcd34d; border-radius:6px; padding:2px 8px; }}
  footer {{ max-width:1120px; margin:0 auto; padding:0 24px 36px; color:var(--muted); font-size:12px; line-height:1.6; }}
</style>
</head>
<body>
<header>
  <div class="hero">
    <div class="wordmark">ENEM 2025</div>
    <div class="hero-divider"></div>
    <div>
      <h1>Inteligência Competitiva</h1>
      <p>Comparação unidade a unidade com os concorrentes diretos de cada marca · Microdados INEP · Uso interno</p>
    </div>
  </div>
</header>
<main>
  <div class="stats">{stats_html}</div>
  <div class="section-title">Marcas</div>
  <div class="grid">
{chr(10).join(cards)}
  </div>
</main>
<footer>
  Cada tela compara as unidades da marca com as redes concorrentes mapeadas no Censo Escolar, com a mesma métrica
  dos dashboards de marca (médias entre presentes; Nota Geral = média das 5 áreas com presença completa e redação válida).<br>
  Fonte: Microdados ENEM 2025 e Censo Escolar 2025 (INEP) · Gerado em {date.today().strftime("%d/%m/%Y")} · Uso interno - não distribuir.
</footer>
</body>
</html>
"""
    destino = os.path.join(OUTPUT_DIR, "Concorrencia_Home.html")
    with open(destino, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Home gerada com {len(marcas)} marca(s): {destino} ({os.path.getsize(destino):,} bytes)")


if __name__ == "__main__":
    main()
