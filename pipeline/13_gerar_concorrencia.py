"""
13_gerar_concorrencia.py
Gera a tela standalone de inteligência competitiva (piloto Matriz Educação
vs Elite e Santa Mônica), unidade a unidade, com a identidade visual da
home ENEM 2025 (réplica UERJ).

Entrada: output/concorrencia_matriz.json (produzido pelo 12)
Saída:   output/Concorrencia_Matriz.html
"""

import json
import os
from datetime import date

from config import OUTPUT_DIR

# Praças da Matriz: concorrentes no mesmo bairro (diretos) e vizinhos (adjacentes)
PRACAS = [
    {"titulo": "Campo Grande", "municipio": "Rio de Janeiro", "nossa": 33183368,
     "diretos": [33520321, 33113114], "adjacentes": [],
     "nota": "Elite Campo Grande II (Senador Vasconcelos) sem dados no ENEM 2024 e 2025."},
    {"titulo": "Taquara", "municipio": "Rio de Janeiro", "nossa": 33187770,
     "diretos": [33169713, 33111642, 33173907], "adjacentes": [], "nota": ""},
    {"titulo": "Bangu", "municipio": "Rio de Janeiro", "nossa": 33187789,
     "diretos": [33159130], "adjacentes": [33122245],
     "nota": "Elite Realengo exibido como praça adjacente."},
    {"titulo": "Madureira", "municipio": "Rio de Janeiro", "nossa": 33197466,
     "diretos": [33140626, 33149780, 33094861, 33197350], "adjacentes": [],
     "nota": "Elite Madureira 3 sem dados no ENEM 2024 e 2025."},
    {"titulo": "Rocha Miranda", "municipio": "Rio de Janeiro", "nossa": 33192685,
     "diretos": [], "adjacentes": [33193649, 33193720],
     "nota": "Sem concorrente mapeado no bairro - exibidos os mais próximos (Irajá e Guadalupe)."},
    {"titulo": "Nova Iguaçu", "municipio": "Nova Iguaçu", "nossa": 33187762,
     "diretos": [33060355, 33185000, 33187681], "adjacentes": [33198926],
     "nota": "Elite Nova Iguaçu (bairro da Luz) sem dados no ENEM 2024 e 2025."},
    {"titulo": "Duque de Caxias", "municipio": "Duque de Caxias", "nossa": 33048185,
     "diretos": [], "adjacentes": [], "ref2024": [33173850],
     "nota": "O Elite de Caxias pontuou no ENEM 2024 (referência acima) e não registrou participantes em 2025. Santa Mônica de Caxias sem dados nos dois anos."},
    {"titulo": "São João de Meriti", "municipio": "São João de Meriti", "nossa": 33190674,
     "diretos": [33200572], "adjacentes": [], "ref2024": [33176752, 33185700],
     "nota": "Elite S. J. de Meriti e ZeroHum Jardim Metrópole pontuaram no ENEM 2024 (referências acima) e não registraram participantes em 2025."},
]


def _pt(v: float) -> str:
    return f"{v:.1f}".replace(".", ",")


def _insight_redacao(data: dict) -> str:
    redes = data["redes"]
    curto = lambda r: "Matriz" if r == "Matriz Educação" else r
    medias = {r: redes[r]["redacao"].get("media") or 0 for r in redes}
    lider = max(medias, key=medias.get)
    outros = sorted((r for r in medias if r != lider), key=lambda r: -medias[r])
    outros_txt = ", ".join(f"{_pt(medias[r])} do {curto(r)}" for r in outros)
    m = redes["Matriz Educação"]["redacao"]["comps"]
    l = redes[lider]["redacao"]["comps"]
    vence_todas = all(
        (l[c] or 0) >= max((redes[r]["redacao"]["comps"][c] or 0) for r in redes) for c in l)
    deltas = {c: (l[c] or 0) - (m[c] or 0) for c in m}
    pior = max(deltas, key=deltas.get)
    nomes = {"C1": "norma culta", "C2": "compreensão da proposta", "C3": "seleção de argumentos",
             "C4": "coesão", "C5": "proposta de intervenção"}
    baixas = sorted(m, key=lambda c: m[c] or 0)[:2]
    baixas_txt = " e ".join(f"{c} ({nomes[c]}: {_pt(m[c])})" for c in baixas)
    return (
        f"O {curto(lider)} lidera a redação (média {_pt(medias[lider])}, contra {outros_txt})"
        f"{', vencendo nas cinco competências' if vence_todas else ''}. A maior distância do Matriz "
        f"para o {curto(lider)} está em {pior} ({nomes[pior]}): {_pt(m[pior])} × {_pt(l[pior])}. "
        f"Internamente, as competências mais baixas do Matriz seguem sendo {baixas_txt}."
    )


TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<title>ENEM 2025 · Inteligência Competitiva - Matriz Educação</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0"></script>
<script>Chart.defaults.font.family="'Segoe UI', system-ui, sans-serif";Chart.defaults.color="#334155";Chart.defaults.locale='pt-BR';</script>
<style>
  :root { --ink:#1e293b; --muted:#64748b; --line:#e2e8f0; --bg:#f1f5f9; --pos:#15803d; --neg:#b91c1c; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--ink); font-family:"Segoe UI", system-ui, Arial, sans-serif; }
  header { background:linear-gradient(135deg,#1e293b 0%,#0a1940 100%); box-shadow:0 4px 12px rgba(0,0,0,.25); }
  .hero { max-width:1180px; margin:0 auto; min-height:96px; padding:0 24px; display:flex; align-items:center; gap:18px; }
  .hero .wordmark { color:#fff; font-size:20px; font-weight:800; letter-spacing:.02em; white-space:nowrap; }
  .hero-divider { width:1px; height:44px; background:rgba(255,255,255,.35); flex-shrink:0; }
  .hero h1 { margin:0; color:#fff; font-size:22px; font-weight:800; letter-spacing:-.01em; }
  .hero p { margin:2px 0 0; color:rgba(255,255,255,.75); font-size:13px; }
  main { max-width:1180px; margin:0 auto; padding:28px 24px 40px; }
  .stats { display:grid; grid-template-columns:repeat(6,minmax(0,1fr)); gap:12px; }
  @media (max-width:1000px){ .stats { grid-template-columns:repeat(3,minmax(0,1fr)); } }
  @media (max-width:640px){ .stats { grid-template-columns:repeat(2,minmax(0,1fr)); } }
  .stat { background:#fff; border:1px solid var(--line); border-radius:14px; padding:14px 16px; box-shadow:0 1px 2px rgba(15,23,42,.04); }
  .stat small { display:block; color:var(--muted); font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:.06em; margin-bottom:7px; }
  .stat strong { display:block; color:#0f172a; font-size:22px; font-weight:800; line-height:1.1; font-variant-numeric:tabular-nums; }
  .stat span { display:block; margin-top:5px; color:var(--muted); font-size:12px; }
  .stat .dot { display:inline-block; width:9px; height:9px; border-radius:50%; margin-right:6px; }
  .section-title { margin:30px 0 14px; color:#334155; font-size:14px; font-weight:800; letter-spacing:.09em; text-transform:uppercase; display:flex; align-items:center; gap:12px; }
  .section-title::after { content:""; flex:1; height:1px; background:var(--line); }
  .card { background:#fff; border:1px solid var(--line); border-radius:14px; padding:18px; box-shadow:0 1px 2px rgba(15,23,42,.04); }
  .card h3 { margin:0 0 4px; font-size:15px; color:#0f172a; }
  .card .sub { margin:0 0 12px; color:var(--muted); font-size:12.5px; }
  .duo { display:grid; grid-template-columns:1.25fr 1fr; gap:14px; align-items:stretch; }
  @media (max-width:900px){ .duo { grid-template-columns:1fr; } }
  .duo > .card { display:flex; flex-direction:column; }
  .duo > .card .chart-wrap { flex:1 1 auto; height:auto; min-height:300px; }
  .card-fill { margin-top:auto; padding-top:12px; border-top:1px solid var(--line); }
  .mini-head { color:var(--muted); font-size:11px; text-transform:uppercase; letter-spacing:.05em; font-weight:700; margin-bottom:6px; }
  .mini-row { display:flex; justify-content:space-between; align-items:baseline; gap:10px; font-size:13px; padding:5px 0; border-bottom:1px solid #eef2f6; }
  .mini-row:last-child { border-bottom:0; }
  .mini-row strong { font-variant-numeric:tabular-nums; }
  .chart-wrap { position:relative; height:300px; }
  table { border-collapse:collapse; width:100%; font-size:13px; font-variant-numeric:tabular-nums; }
  th, td { padding:7px 9px; text-align:right; border-bottom:1px solid #eef2f6; white-space:nowrap; }
  th { color:var(--muted); font-size:11px; text-transform:uppercase; letter-spacing:.05em; font-weight:700; }
  th:first-child, td:first-child { text-align:left; }
  .tbl-scroll { overflow-x:auto; }
  .rede-dot { display:inline-block; width:9px; height:9px; border-radius:50%; margin-right:7px; vertical-align:baseline; }
  .nossa-row { background:#15803d0d; }
  .nossa-row td:first-child { box-shadow:inset 3px 0 0 var(--pos); }
  .star { color:var(--pos); font-weight:800; }
  .delta-pos { color:var(--pos); font-weight:700; }
  .delta-neg { color:var(--neg); font-weight:700; }
  .delta-neutro { color:var(--muted); }
  .filters { display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin-bottom:14px; }
  .chip { border:1px solid var(--line); background:#fff; color:#334155; border-radius:999px; padding:6px 14px; font-size:12.5px; font-weight:700; cursor:pointer; }
  .chip.on { color:#fff; border-color:transparent; }
  select, .filters label { font-size:12.5px; color:#334155; }
  select { border:1px solid var(--line); border-radius:8px; padding:6px 10px; background:#fff; font-family:inherit; }
  th.sortable { cursor:pointer; user-select:none; }
  th.sorted-desc::after { content:" ↓"; } th.sorted-asc::after { content:" ↑"; }
  .versus { display:flex; flex-wrap:wrap; gap:12px; align-items:center; margin-bottom:14px; }
  .versus .lado { flex:1; min-width:240px; }
  .versus .lado small { display:block; color:var(--muted); font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:.05em; margin-bottom:4px; }
  .versus select { width:100%; }
  .placar { display:flex; gap:14px; align-items:center; justify-content:center; margin:6px 0 14px; }
  .placar .num { font-size:30px; font-weight:800; font-variant-numeric:tabular-nums; }
  .placar .vs { color:var(--muted); font-size:13px; font-weight:700; }
  .placar .who { font-size:12px; color:var(--muted); display:block; text-align:center; margin-top:2px; max-width:190px; }
  .badge-delta { display:inline-block; border-radius:8px; padding:3px 10px; font-size:13px; font-weight:800; color:#fff; }
  .pracas { display:grid; grid-template-columns:repeat(auto-fit,minmax(min(520px,100%),1fr)); gap:14px; }
  .praca th, .praca td { padding:6px 7px; }
  .praca th:first-child, .praca td:first-child { white-space:normal; }
  .praca h4 { margin:0; font-size:14.5px; color:#0f172a; }
  .praca .mun { color:var(--muted); font-size:12px; margin:2px 0 10px; }
  .praca .nota { color:var(--muted); font-size:12px; margin-top:10px; border-top:1px dashed var(--line); padding-top:8px; }
  .verdict { font-size:12.5px; font-weight:600; margin:9px 0 0; }
  .consol { margin-top:14px; }
  .consol summary { list-style:none; cursor:pointer; display:flex; align-items:center; justify-content:space-between; gap:14px; padding:14px 18px; background:#fff; border:1px solid var(--line); border-radius:14px; font-size:13.5px; font-weight:700; color:#334155; box-shadow:0 1px 2px rgba(15,23,42,.04); }
  .consol summary::-webkit-details-marker { display:none; }
  .consol summary .hint { color:var(--muted); font-weight:400; font-size:12.5px; }
  .consol[open] summary { border-radius:14px 14px 0 0; }
  .consol .body { background:#fff; border:1px solid var(--line); border-top:0; border-radius:0 0 14px 14px; padding:14px 18px; }
  .tag-adj { font-size:10px; font-weight:800; letter-spacing:.04em; color:#64748b; border:1px solid var(--line); border-radius:6px; padding:1px 6px; margin-left:6px; vertical-align:middle; }
  .obs { color:var(--muted); font-size:12px; margin-top:10px; }
  footer { max-width:1180px; margin:0 auto; padding:0 24px 36px; color:var(--muted); font-size:12px; line-height:1.6; }
</style>
</head>
<body>
<header>
  <div class="hero">
    <div class="wordmark">ENEM 2025</div>
    <div class="hero-divider"></div>
    <div>
      <h1>Inteligência Competitiva - Matriz Educação</h1>
      <p>Comparação unidade a unidade com Elite e Santa Mônica · Microdados INEP · Uso interno</p>
    </div>
  </div>
</header>
<main>
  <div class="stats" id="statsRow"></div>

  <div class="section-title">Evolução 2024-2025</div>
  <div class="card">
    <h3>Redes, mercado municipal e Top 100 BR</h3>
    <p class="sub">Média entre presentes por prova · anos em que o INEP identifica a escola nos microdados (2021-2023 não têm essa informação) · Privada = todas as escolas privadas do município</p>
    <div class="filters">
      <button class="chip hm-chip" data-m="NG">NG</button>
      <button class="chip hm-chip" data-m="CN">CN</button>
      <button class="chip hm-chip" data-m="CH">CH</button>
      <button class="chip hm-chip" data-m="LC">LC</button>
      <button class="chip hm-chip" data-m="MT">MT</button>
      <button class="chip hm-chip" data-m="RD">RD</button>
      <select id="histMun" autocomplete="off">
        <option>Rio de Janeiro</option>
        <option>Duque de Caxias</option>
        <option>Nova Iguaçu</option>
        <option>São João de Meriti</option>
      </select>
    </div>
    <div class="chart-wrap" style="height:340px"><canvas id="chartHist"></canvas></div>
    <details class="consol" style="margin-top:12px">
      <summary>Ver dados<span class="hint">série × ano · variação 2024→2025 · clique para abrir</span></summary>
      <div class="body"><div class="tbl-scroll"><table id="tblHist"></table></div></div>
    </details>
  </div>

  <div class="section-title">Panorama das redes</div>
  <div class="duo">
    <div class="card">
      <h3>Média por área - redes completas</h3>
      <p class="sub">Média entre presentes em cada prova · RD = Redação</p>
      <div class="chart-wrap"><canvas id="chartPanorama"></canvas></div>
    </div>
    <div class="card">
      <h3>Escala e funil de excelência</h3>
      <p class="sub">Rede completa · NG = média das 5 áreas (presença completa + redação válida)</p>
      <div class="tbl-scroll"><table id="tblRedes"></table></div>
      <p class="obs" id="obsPanorama"></p>
      <div class="card-fill" id="fillRedes"></div>
    </div>
  </div>

  <div class="section-title">Ranking unificado das unidades</div>
  <div class="card">
    <div class="filters">
      <button class="chip" data-rede="*">Todas as redes</button>
      <button class="chip" data-rede="Matriz Educação">Matriz</button>
      <button class="chip" data-rede="Elite">Elite</button>
      <button class="chip" data-rede="Santa Mônica">Santa Mônica</button>
      <button class="chip" data-rede="ZeroHum">ZeroHum</button>
      <select id="filtroMun" autocomplete="off"><option value="*">Todos os municípios</option></select>
      <label><input type="checkbox" id="filtroN30" autocomplete="off"> ocultar unidades com menos de 30 alunos</label>
    </div>
    <div class="tbl-scroll"><table id="tblRanking"></table></div>
    <p class="obs">★ unidade Matriz · † nota geral com menos de 30 alunos válidos · médias entre presentes por prova · clique nos cabeçalhos para ordenar</p>
  </div>

  <div class="section-title">Confronto direto</div>
  <div class="card">
    <div class="versus">
      <div class="lado"><small>Nossa unidade</small><select id="selA"></select></div>
      <div class="lado"><small>Concorrente (ou outra unidade)</small><select id="selB"></select></div>
    </div>
    <div class="placar" id="placar"></div>
    <div class="duo">
      <div>
        <h3 style="font-size:14px;margin:0 0 2px">Médias por área</h3>
        <p class="sub" id="subConfArea"></p>
        <div class="chart-wrap"><canvas id="chartConfAreas"></canvas></div>
      </div>
      <div>
        <h3 style="font-size:14px;margin:0 0 2px">Redação por competência</h3>
        <p class="sub">Média de C1 a C5 entre redações válidas (0 a 200)</p>
        <div class="chart-wrap"><canvas id="chartConfComps"></canvas></div>
      </div>
    </div>
    <div class="tbl-scroll" style="margin-top:14px"><table id="tblConfronto"></table></div>
  </div>

  <div class="section-title">Batalha territorial - praça a praça</div>
  <div class="pracas" id="pracasGrid"></div>
  <details class="consol">
    <summary>Consolidado por praça<span class="hint">uma linha por bairro, da melhor para a pior situação · clique para abrir</span></summary>
    <div class="body">
      <div class="tbl-scroll"><table id="tblConsol"></table></div>
      <p class="obs">Situação = diferença de NG entre a nossa unidade e o melhor concorrente com dados 2025 na praça · † menos de 30 alunos</p>
    </div>
  </details>

  <div class="section-title">Redação em detalhe</div>
  <div class="duo">
    <div class="card">
      <h3>Competências C1-C5 por rede</h3>
      <p class="sub">Média de cada competência (0 a 200) entre redações válidas</p>
      <div class="chart-wrap"><canvas id="chartRedacaoRedes"></canvas></div>
    </div>
    <div class="card">
      <h3>Leitura estratégica</h3>
      <p class="sub">Síntese automática dos microdados</p>
      <p style="font-size:13.5px;line-height:1.65;margin:0">__INSIGHT_RED__</p>
      <div class="card-fill" id="fillRedacao"></div>
    </div>
  </div>
</main>
<footer>
  <strong>Metodologia.</strong> Mesma métrica dos dashboards de marca: média por área entre presentes na prova
  (TP_PRESENCA = 1); Redação entre redações válidas (TP_STATUS_REDACAO = 1); Nota Geral = média de
  Ciências da Natureza, Ciências Humanas, Linguagens e Códigos, Matemática e Redação para alunos com presença completa e redação válida.
  Rede privada municipal = todas as escolas privadas do município nos microdados.
  Top 100 BR = média das 100 melhores escolas privadas do país (30 ou mais alunos válidos), por área e na Nota Geral.<br>
  <strong>Concorrentes sem dados no ENEM 2025:</strong> __NOTA_SEM_DADOS__.<br>
  Fonte: Microdados ENEM 2025 e Censo Escolar 2025 (INEP) · Gerado em __GERADO_EM__ · Uso interno - não distribuir.
</footer>
<script>
const DATA = __DATA__;
const PRACAS = __PRACAS__;
const REF2024 = __REF2024__;
const CORES = {"Matriz Educação":"#15803d","Elite":"#1d4ed8","Santa Mônica":"#be123c","ZeroHum":"#b45309"};
const CINZA = "#334155";
const AREAS5 = ["CN","CH","LC","MT","RD"];
const REDES = ["Matriz Educação","Elite","Santa Mônica","ZeroHum"];
const byCo = {}; DATA.unidades.forEach(u => byCo[u.co] = u);

const fmt = v => (v==null || isNaN(v)) ? "-" : v.toLocaleString("pt-BR",{minimumFractionDigits:1,maximumFractionDigits:1});
const fmtInt = v => v==null ? "-" : v.toLocaleString("pt-BR");
const areaStat = (u,a) => a==="RD" ? (u.redacao||{}) : ((u.areas||{})[a]||{});
const ngOf = u => (u.nota_geral||{}).media ?? null;
const dot = rede => '<span class="rede-dot" style="background:'+CORES[rede]+'"></span>';
const deltaHtml = d => d==null ? '<span class="delta-neutro">-</span>'
  : '<span class="'+(d>=0?'delta-pos':'delta-neg')+'">'+(d>=0?'+':'−')+fmt(Math.abs(d))+'</span>';

// ---------- Cards do topo ----------
(function(){
  const r = DATA.redes;
  const alunos = DATA.unidades.reduce((s,u)=>s+u.n_inscritos,0);
  const cards = [
    {t:"Unidades comparadas", v: fmtInt(DATA.unidades.length), s: "8 Matriz · "+(DATA.unidades.length-8)+" concorrentes"},
    {t:"Alunos analisados", v: fmtInt(alunos), s: "inscritos no ENEM 2025"},
  ];
  REDES.forEach(rd => {
    const x = r[rd];
    cards.push({t: rd, v: fmt((x.nota_geral||{}).media), dot: CORES[rd],
      s: x.n_unidades+" unidades · "+fmtInt(x.n_inscritos)+" alunos"});
  });
  document.getElementById("statsRow").innerHTML = cards.map(c =>
    '<div class="stat"><small>'+(c.dot?'<span class="dot" style="background:'+c.dot+'"></span>':'')+c.t+
    '</small><strong>'+c.v+'</strong><span>'+c.s+'</span></div>').join("");
})();

// ---------- Panorama ----------
new Chart(document.getElementById("chartPanorama"), {
  type: "bar",
  data: { labels: AREAS5, datasets: REDES.map(rd => ({
    label: rd, backgroundColor: CORES[rd]+"cc", borderColor: CORES[rd],
    borderRadius: 6, borderSkipped: false,
    data: AREAS5.map(a => a==="RD" ? DATA.redes[rd].redacao.media : DATA.redes[rd].areas[a].media)
  })) },
  options: { maintainAspectRatio:false, plugins:{ legend:{ labels:{ usePointStyle:true, boxWidth:8 } } },
    scales: { x:{ grid:{ display:false } },
      y:{ min:400, grid:{ color:"#eef2f6" }, ticks:{ font:{size:11.5}, color:"#64748b" } } } }
});
(function(){
  const rows = REDES.map(rd => {
    const x = DATA.redes[rd];
    return "<tr><td>"+dot(rd)+rd+"</td><td>"+x.n_unidades+"</td><td>"+fmtInt(x.n_inscritos)+"</td><td>"+
      fmt(x.taxa_presenca_pct)+"%</td><td><strong>"+fmt((x.nota_geral||{}).media)+"</strong></td><td>"+
      fmt(x.areas.MT.pct_acima_700)+"%</td><td>"+fmt(x.redacao.pct_acima_800)+"%</td></tr>";
  }).join("");
  document.getElementById("tblRedes").innerHTML =
    "<thead><tr><th>Rede</th><th>Un.</th><th>Alunos</th><th>Presença</th><th>NG</th><th>MT ≥700</th><th>RD ≥800</th></tr></thead><tbody>"+rows+"</tbody>";
  const ngRede = r => (DATA.redes[r].nota_geral||{}).media||0;
  const rel = d => d>=0 ? fmt(d)+" acima" : fmt(-d)+" abaixo";
  const lider = REDES.reduce((a,b)=> ngRede(b)>ngRede(a) ? b : a);
  document.getElementById("obsPanorama").textContent =
    "O Matriz está " + rel(ngRede("Matriz Educação")-ngRede("Elite")) + " do Elite e " +
    rel(ngRede("Matriz Educação")-ngRede("ZeroHum")) + " do ZeroHum na nota geral de rede; o " +
    lider + " lidera o grupo" + (lider==="Santa Mônica" ? ", puxado pela Redação." : ".");
})();

// ---------- Preenchimentos dos cards laterais ----------
(function(){
  const melhor = rede => DATA.unidades
    .filter(u => u.rede===rede && u.n_inscritos>=30 && ngOf(u)!=null)
    .sort((a,b)=>ngOf(b)-ngOf(a))[0];
  const labelMun = u => u.label + (u.label.includes(u.municipio) ? "" : " · "+u.municipio);
  document.getElementById("fillRedes").innerHTML =
    '<div class="mini-head">Melhor unidade de cada rede · 30+ alunos</div>' +
    REDES.map(rd => { const u = melhor(rd); return u ?
      '<div class="mini-row"><span>'+dot(rd)+(u.nossa?'<span class="star">★ </span>':'')+labelMun(u)+
      '</span><strong>'+fmt(ngOf(u))+'</strong></div>' : ''; }).join("");

  const comRD = DATA.unidades.filter(u => u.n_inscritos>=30 && (u.redacao||{}).media!=null)
    .sort((a,b)=>b.redacao.media-a.redacao.media);
  const top3 = comRD.slice(0,3);
  const melhorNossa = comRD.find(u=>u.nossa);
  const pos = comRD.indexOf(melhorNossa)+1;
  document.getElementById("fillRedacao").innerHTML =
    '<div class="mini-head">Referências em redação · 30+ alunos</div>' +
    top3.map(u => '<div class="mini-row"><span>'+dot(u.rede)+labelMun(u)+
      '</span><strong>'+fmt(u.redacao.media)+'</strong></div>').join("") +
    (melhorNossa ? '<div class="mini-row"><span>'+dot(melhorNossa.rede)+'<span class="star">★ </span>'+
      melhorNossa.label+' · melhor do Matriz ('+pos+'ª de '+comRD.length+')</span><strong>'+
      fmt(melhorNossa.redacao.media)+'</strong></div>' : '');
})();

// ---------- Ranking unificado ----------
let fRede = "*", fMun = "*", fN30 = false, sortKey = "ng", sortDir = -1;
const colDefs = [
  {k:"label", t:"Unidade"}, {k:"municipio", t:"Município"}, {k:"n", t:"Alunos"},
  {k:"CN", t:"CN"}, {k:"CH", t:"CH"}, {k:"LC", t:"LC"}, {k:"MT", t:"MT"}, {k:"RD", t:"RD"}, {k:"ng", t:"NG"}
];
const valOf = (u,k) => k==="label" ? u.label : k==="municipio" ? u.municipio : k==="n" ? u.n_inscritos
  : k==="ng" ? ngOf(u) : (areaStat(u,k).media ?? null);

function renderRanking(){
  let lista = DATA.unidades.filter(u =>
    (fRede==="*" || u.rede===fRede) && (fMun==="*" || u.municipio===fMun) && (!fN30 || u.n_inscritos>=30));
  lista.sort((a,b)=>{
    const va = valOf(a,sortKey), vb = valOf(b,sortKey);
    if (va==null && vb==null) return 0; if (va==null) return 1; if (vb==null) return -1;
    return (typeof va==="string" ? va.localeCompare(vb,"pt-BR") : va-vb) * sortDir;
  });
  const head = "<thead><tr>"+colDefs.map(c =>
    '<th class="sortable'+(sortKey===c.k ? (sortDir<0?' sorted-desc':' sorted-asc') : '')+'" data-k="'+c.k+'">'+c.t+"</th>").join("")+"<th>Pos.</th></tr></thead>";
  const rows = lista.map((u,i) => {
    const peq = ((u.nota_geral||{}).n ?? 0) < 30 ? " †" : "";
    return '<tr class="'+(u.nossa?'nossa-row':'')+'"><td>'+dot(u.rede)+(u.nossa?'<span class="star">★ </span>':'')+
      u.label+peq+"</td><td>"+u.municipio+"</td><td>"+fmtInt(u.n_inscritos)+"</td>"+
      ["CN","CH","LC","MT","RD"].map(a=>"<td>"+fmt(areaStat(u,a).media)+"</td>").join("")+
      "<td><strong>"+fmt(ngOf(u))+"</strong></td><td>"+(i+1)+"º</td></tr>";
  }).join("");
  document.getElementById("tblRanking").innerHTML = head+"<tbody>"+rows+"</tbody>";
  document.querySelectorAll("#tblRanking th.sortable").forEach(th => th.onclick = () => {
    const k = th.dataset.k;
    if (sortKey===k) sortDir *= -1; else { sortKey = k; sortDir = (k==="label"||k==="municipio") ? 1 : -1; }
    renderRanking();
  });
}
document.querySelectorAll(".chip").forEach(ch => ch.onclick = () => {
  fRede = ch.dataset.rede;
  document.querySelectorAll(".chip").forEach(c => { c.classList.toggle("on", c===ch);
    c.style.background = c===ch ? (CORES[c.dataset.rede]||"#334155") : "#fff"; });
  renderRanking();
});
(function(){
  const muns = [...new Set(DATA.unidades.map(u=>u.municipio))].sort((a,b)=>a.localeCompare(b,"pt-BR"));
  const sel = document.getElementById("filtroMun");
  muns.forEach(m => sel.insertAdjacentHTML("beforeend", '<option value="'+m+'">'+m+"</option>"));
  sel.onchange = () => { fMun = sel.value; renderRanking(); };
  const chk = document.getElementById("filtroN30");
  chk.onchange = () => { fN30 = chk.checked; renderRanking(); };
  // o browser pode restaurar estado do formulário no reload; sincroniza antes do 1º render
  fMun = sel.value; fN30 = chk.checked;
  document.querySelector('.chip[data-rede="*"]').click();
})();

// ---------- Confronto direto ----------
let chConfAreas = null, chConfComps = null;
const benchByMun = {};
Object.values(DATA.bench_municipal).forEach(b => benchByMun[b.municipio] = b);

(function(){
  const selA = document.getElementById("selA"), selB = document.getElementById("selB");
  DATA.unidades.filter(u=>u.nossa).forEach(u =>
    selA.insertAdjacentHTML("beforeend", '<option value="'+u.co+'">'+u.label+" · "+u.municipio+"</option>"));
  REDES.forEach(rd => {
    const grupo = DATA.unidades.filter(u=>u.rede===rd);
    if (!grupo.length) return;
    const og = document.createElement("optgroup"); og.label = rd;
    grupo.sort((a,b)=>(ngOf(b)||0)-(ngOf(a)||0)).forEach(u => {
      const o = document.createElement("option"); o.value = u.co;
      o.textContent = u.label+" · "+u.municipio+" (NG "+fmt(ngOf(u))+")";
      og.appendChild(o);
    });
    selB.appendChild(og);
  });
  selA.value = 33183368;  // Matriz - Campo Grande
  selB.value = 33520321;  // Elite - Campo Grande I
  selA.onchange = selB.onchange = renderConfronto;
  renderConfronto();
})();

function renderConfronto(){
  const A = byCo[document.getElementById("selA").value];
  const B = byCo[document.getElementById("selB").value];
  const ngA = ngOf(A), ngB = ngOf(B), d = (ngA!=null && ngB!=null) ? ngA-ngB : null;
  document.getElementById("placar").innerHTML =
    '<div><div class="num" style="color:'+CORES[A.rede]+'">'+fmt(ngA)+'</div><span class="who">'+A.label+"</span></div>"+
    '<div class="vs">NG<br><span class="badge-delta" style="background:'+(d>=0?"#15803d":"#b91c1c")+'">'+
      (d==null?"-":(d>=0?"+":"−")+fmt(Math.abs(d)))+"</span></div>"+
    '<div><div class="num" style="color:'+CORES[B.rede]+'">'+fmt(ngB)+'</div><span class="who">'+B.label+"</span></div>";

  const bench = benchByMun[A.municipio];
  document.getElementById("subConfArea").textContent =
    bench ? "Linha cinza = rede privada de "+A.municipio+" ("+fmtInt(bench.n_alunos)+" alunos)" : "Média entre presentes";

  const dsets = [
    { label: A.label+" ★", backgroundColor: CORES[A.rede]+"cc", borderColor: CORES[A.rede],
      borderRadius:6, borderSkipped:false, data: AREAS5.map(a=>areaStat(A,a).media ?? null) },
    { label: B.label, backgroundColor: CORES[B.rede]+"cc", borderColor: CORES[B.rede],
      borderRadius:6, borderSkipped:false, data: AREAS5.map(a=>areaStat(B,a).media ?? null) },
  ];
  if (bench) dsets.push({ label:"Privada "+A.municipio, type:"line", borderColor:CINZA, borderWidth:2,
    borderDash:[6,4], pointRadius:3, pointBackgroundColor:CINZA, fill:false,
    data: AREAS5.map(a => a==="RD" ? bench.redacao.media : bench.areas[a].media) });
  if (chConfAreas) chConfAreas.destroy();
  chConfAreas = new Chart(document.getElementById("chartConfAreas"), {
    type:"bar", data:{ labels:AREAS5, datasets:dsets },
    options:{ maintainAspectRatio:false, plugins:{ legend:{ labels:{ usePointStyle:true, boxWidth:8 } } },
      scales:{ x:{ grid:{ display:false } },
        y:{ min:400, grid:{ color:"#eef2f6" }, ticks:{ font:{size:11.5}, color:"#64748b" } } } }
  });

  const compsA = (A.redacao||{}).comps||{}, compsB = (B.redacao||{}).comps||{};
  if (chConfComps) chConfComps.destroy();
  chConfComps = new Chart(document.getElementById("chartConfComps"), {
    type:"bar", data:{ labels:["C1","C2","C3","C4","C5"], datasets:[
      { label:A.label+" ★", backgroundColor:CORES[A.rede]+"cc", borderColor:CORES[A.rede], borderRadius:6, borderSkipped:false,
        data:["C1","C2","C3","C4","C5"].map(c=>compsA[c] ?? null) },
      { label:B.label, backgroundColor:CORES[B.rede]+"cc", borderColor:CORES[B.rede], borderRadius:6, borderSkipped:false,
        data:["C1","C2","C3","C4","C5"].map(c=>compsB[c] ?? null) } ] },
    options:{ maintainAspectRatio:false, plugins:{ legend:{ labels:{ usePointStyle:true, boxWidth:8 } } },
      scales:{ x:{ grid:{ display:false } },
        y:{ min:80, max:200, grid:{ color:"#eef2f6" }, ticks:{ font:{size:11.5}, color:"#64748b" } } } }
  });

  const corA = h => '<span style="color:'+CORES[A.rede]+';font-weight:600">'+h+"</span>";
  const corB = h => '<span style="color:'+CORES[B.rede]+';font-weight:600">'+h+"</span>";
  const par = (va, vb, suf) => corA(fmt(va)+(va!=null?suf:"")) + " × " + corB(fmt(vb)+(vb!=null?suf:""));
  const linhas = [["NG", u=>u.nota_geral||{}]].concat(AREAS5.map(a => [a, u=>areaStat(u,a)]));
  const rows = linhas.map(([nome, get]) => {
    const sa = get(A), sb = get(B);
    const dd = (sa.media!=null && sb.media!=null) ? sa.media-sb.media : null;
    return "<tr><td><strong>"+nome+"</strong></td><td>"+par(sa.media, sb.media, "")+"</td><td>"+deltaHtml(dd)+
      "</td><td>"+par(sa.mediana, sb.mediana, "")+"</td><td>"+par(sa.p90, sb.p90, "")+
      "</td><td>"+par(sa.pct_acima_600, sb.pct_acima_600, "%")+"</td><td>"+
      par(sa.pct_acima_700, sb.pct_acima_700, "%")+"</td></tr>";
  }).join("");
  document.getElementById("tblConfronto").innerHTML =
    "<thead><tr><th></th><th>Média</th><th>Δ</th><th>Mediana</th>"+
    "<th>P90</th><th>≥600</th><th>≥700</th></tr></thead><tbody>"+rows+
    '</tbody><tfoot><tr><td colspan="7" style="text-align:left;color:#64748b;font-size:12px;border:0;padding-top:10px">'+
    "Cada par: "+corA("★ "+A.label)+" × "+corB(B.label)+" · Δ = média da unidade ★ menos o concorrente · Alunos: "+
    corA(fmtInt(A.n_inscritos))+" ("+fmt(A.taxa_presenca_pct)+"% presença) × "+
    corB(fmtInt(B.n_inscritos))+" ("+fmt(B.taxa_presenca_pct)+"% presença)<br>"+
    "Mediana = nota que divide a turma ao meio · P90 = nota superada apenas pelos 10% melhores alunos "+
    "· ≥600 e ≥700 = % dos alunos que atingem esse patamar</td></tr></tfoot>";
}

// ---------- Batalha territorial ----------
(function(){
  const grid = document.getElementById("pracasGrid");
  grid.innerHTML = PRACAS.map(p => {
    const nossa = byCo[p.nossa];
    const rivais = p.diretos.map(co=>({u:byCo[co],adj:false})).concat(p.adjacentes.map(co=>({u:byCo[co],adj:true})))
      .filter(x=>x.u);
    const refs = (p.ref2024||[]).map(co=>REF2024[co]).filter(Boolean);
    const ngN = ngOf(nossa);
    let corpo;
    if (!rivais.length && !refs.length) {
      corpo = '<p class="obs" style="margin:6px 0 0">Sem concorrente direto com dados no ENEM 2025 nesta praça.</p>';
    } else {
      const linhas = [{u:nossa, nossa:true, adj:false}].concat(rivais.map(x=>({u:x.u, nossa:false, adj:x.adj})));
      const val = (u,m) => m==="NG" ? ngOf(u) : areaStat(u,m).media;
      const best = {};
      ["NG","MT","RD"].forEach(m => best[m] = Math.max(...linhas.map(l=>val(l.u,m)).filter(v=>v!=null)));
      const cel = (u,m) => { const v = val(u,m);
        return "<td"+(v!=null && v===best[m] ? ' style="font-weight:800"' : "")+">"+fmt(v)+"</td>"; };
      corpo = '<div class="tbl-scroll"><table><thead><tr><th>Unidade</th><th>Alunos</th><th>NG</th><th>MT</th><th>RD</th></tr></thead><tbody>'+
        linhas.map(l => '<tr class="'+(l.nossa?'nossa-row':'')+'"><td>'+dot(l.u.rede)+(l.nossa?'<span class="star">★ </span>':'')+
          l.u.label+(l.u.n_inscritos<30?' †':'')+(l.adj?'<span class="tag-adj">ADJACENTE</span>':'')+"</td><td>"+
          fmtInt(l.u.n_inscritos)+"</td>"+cel(l.u,"NG")+cel(l.u,"MT")+cel(l.u,"RD")+"</tr>").join("")+
        refs.map(r => '<tr style="color:#64748b"><td>'+dot(r.label.split(" - ")[0])+r.label+
          '<span class="tag-adj">ENEM 2024</span></td><td>'+fmtInt(r.n_inscritos)+"</td><td>"+fmt(r.ng)+
          "</td><td>"+fmt(r.mt)+"</td><td>"+fmt(r.rd)+"</td></tr>").join("")+
        "</tbody></table></div>";
      if (rivais.length) {
        const ord = linhas.filter(l=>val(l.u,"NG")!=null).sort((a,b)=>val(b.u,"NG")-val(a.u,"NG"));
        const lider = ord[0];
        const peq = u => u.n_inscritos<30 ? " †" : "";
        if (lider.nossa) {
          const vice = ord[1];
          corpo += '<p class="verdict" style="color:var(--pos)">O Matriz lidera a praça em NG, '+
            fmt(val(lider.u,"NG")-val(vice.u,"NG"))+' pontos à frente do '+vice.u.label+peq(vice.u)+'.</p>';
        } else {
          corpo += '<p class="verdict" style="color:var(--neg)">O '+lider.u.label+peq(lider.u)+
            ' lidera a praça em NG; o Matriz está '+fmt(val(lider.u,"NG")-ngN)+' pontos atrás.</p>';
        }
      }
    }
    return '<div class="card praca"><h4>'+p.titulo+'</h4><div class="mun">'+p.municipio+
      " · médias ENEM 2025 · melhor valor da praça em negrito · † menos de 30 alunos</div>"+corpo+
      (p.nota?'<div class="nota">'+p.nota+"</div>":"")+"</div>";
  }).join("");

  // Consolidado por praça (tabela expansível)
  const peqTag = u => u.n_inscritos<30 ? " †" : "";
  const consol = PRACAS.map(p => {
    const nossa = byCo[p.nossa];
    const rivaisU = p.diretos.concat(p.adjacentes).map(co=>byCo[co]).filter(u=>u && ngOf(u)!=null);
    const ngN = ngOf(nossa);
    if (!rivaisU.length) return {p, nossa, ngN, melhor:null, diff:null};
    const melhor = [...rivaisU].sort((a,b)=>ngOf(b)-ngOf(a))[0];
    return {p, nossa, ngN, melhor, diff: ngN-ngOf(melhor), nRivais: rivaisU.length};
  }).sort((a,b) => (b.diff==null?-1e9:b.diff) - (a.diff==null?-1e9:a.diff));
  document.getElementById("tblConsol").innerHTML =
    "<thead><tr><th>Praça</th><th>Município</th><th>Alunos ★</th><th>NG ★</th><th>Melhor concorrente</th><th>NG conc.</th><th>Situação</th></tr></thead><tbody>"+
    consol.map(c => {
      let sit, conc, ngc;
      if (c.melhor==null) {
        sit = '<span class="delta-neutro">única com dados 2025 na praça</span>'; conc = "-"; ngc = "-";
      } else {
        conc = dot(c.melhor.rede)+c.melhor.label+peqTag(c.melhor);
        ngc = fmt(ngOf(c.melhor));
        sit = c.diff>=0
          ? '<span class="delta-pos">à frente por '+fmt(c.diff)+'</span>'
          : '<span class="delta-neg">atrás por '+fmt(-c.diff)+'</span>';
      }
      return "<tr><td><strong>"+c.p.titulo+"</strong></td><td>"+c.p.municipio+"</td><td>"+
        fmtInt(c.nossa.n_inscritos)+"</td><td><strong>"+fmt(c.ngN)+"</strong></td><td>"+conc+
        "</td><td>"+ngc+"</td><td>"+sit+"</td></tr>";
    }).join("")+"</tbody>";
})();

// ---------- Evolução histórica ----------
const HIST = __HIST__;
let histMetric = "MT", chartHist = null;
function renderHist(){
  const anos = ["2024", "2025"];
  const mun = document.getElementById("histMun").value;
  const series = REDES.map(rd => ({label: rd, cor: CORES[rd], dash: [],
    data: anos.map(a => ((HIST.redes[rd]||{})[a]||{})[histMetric] ?? null)}));
  series.push({label: "Privada "+mun, cor: CINZA, dash: [],
    data: anos.map(a => (((HIST.privada_municipal||{})[mun]||{})[a]||{})[histMetric] ?? null)});
  series.push({label: "Top 100 BR", cor: "#64748b", dash: [6,4],
    data: anos.map(a => ((HIST.top100||{})[a]||{})[histMetric] ?? null)});
  if (chartHist) chartHist.destroy();
  chartHist = new Chart(document.getElementById("chartHist"), {
    type: "line",
    data: { labels: anos, datasets: series.map(s => ({label: s.label, data: s.data,
      borderColor: s.cor, backgroundColor: s.cor, borderDash: s.dash, borderWidth: 2.5,
      pointRadius: 3.5, pointBackgroundColor: s.cor, spanGaps: false, fill: false, tension: .15})) },
    options: { maintainAspectRatio:false, plugins:{ legend:{ labels:{ usePointStyle:true, boxWidth:8 } } },
      scales:{ x:{ grid:{ display:false } },
        y:{ grid:{ color:"#eef2f6" }, ticks:{ font:{size:11.5}, color:"#64748b" } } } }
  });
  document.getElementById("tblHist").innerHTML =
    "<thead><tr><th>Série</th>"+anos.map(a=>"<th>"+a+"</th>").join("")+
    "<th>Variação 24→25</th><th>%</th></tr></thead><tbody>"+
    series.map(s => {
      const v24 = s.data[0], v25 = s.data[1];
      const dv = (v24!=null && v25!=null) ? v25-v24 : null;
      const pc = (dv!=null && v24) ? dv/v24*100 : null;
      const cls = dv==null ? "delta-neutro" : (dv>=0 ? "delta-pos" : "delta-neg");
      return '<tr><td><span class="rede-dot" style="background:'+s.cor+'"></span>'+s.label+"</td>"+
        s.data.map(v=>"<td>"+fmt(v)+"</td>").join("")+
        '<td><span class="'+cls+'">'+(dv==null?"-":(dv>=0?"+":"−")+fmt(Math.abs(dv)))+"</span></td>"+
        '<td><span class="'+cls+'">'+(pc==null?"-":(pc>=0?"+":"−")+fmt(Math.abs(pc))+"%")+"</span></td></tr>";
    }).join("")+"</tbody>";
}
document.querySelectorAll(".hm-chip").forEach(ch => ch.onclick = () => {
  histMetric = ch.dataset.m;
  document.querySelectorAll(".hm-chip").forEach(c => {
    c.classList.toggle("on", c===ch);
    c.style.background = c===ch ? CORES["Matriz Educação"] : "#fff";
    c.style.color = c===ch ? "#fff" : "#334155";
  });
  renderHist();
});
document.getElementById("histMun").onchange = renderHist;
document.querySelector('.hm-chip[data-m="NG"]').click();

// ---------- Redação por rede ----------
new Chart(document.getElementById("chartRedacaoRedes"), {
  type:"bar",
  data:{ labels:["C1","C2","C3","C4","C5"], datasets: REDES.map(rd => ({
    label: rd, backgroundColor: CORES[rd]+"cc", borderColor: CORES[rd], borderRadius:6, borderSkipped:false,
    data: ["C1","C2","C3","C4","C5"].map(c => DATA.redes[rd].redacao.comps[c])
  })) },
  options:{ maintainAspectRatio:false, plugins:{ legend:{ labels:{ usePointStyle:true, boxWidth:8 } } },
    scales:{ x:{ grid:{ display:false } },
      y:{ min:80, max:200, grid:{ color:"#eef2f6" }, ticks:{ font:{size:11.5}, color:"#64748b" } } } }
});
</script>
</body>
</html>
"""


def main():
    with open(os.path.join(OUTPUT_DIR, "concorrencia_matriz.json"), encoding="utf-8") as f:
        data = json.load(f)
    ref_path = os.path.join(OUTPUT_DIR, "concorrencia_ref2024.json")
    ref2024 = json.load(open(ref_path, encoding="utf-8")) if os.path.exists(ref_path) else {}
    hist_path = os.path.join(OUTPUT_DIR, "concorrencia_historico.json")
    hist = json.load(open(hist_path, encoding="utf-8")) if os.path.exists(hist_path) else {}

    html = (TEMPLATE
            .replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
            .replace("__PRACAS__", json.dumps(PRACAS, ensure_ascii=False, separators=(",", ":")))
            .replace("__REF2024__", json.dumps(ref2024, ensure_ascii=False, separators=(",", ":")))
            .replace("__HIST__", json.dumps(hist, ensure_ascii=False, separators=(",", ":")))
            .replace("__INSIGHT_RED__", _insight_redacao(data))
            .replace("__NOTA_SEM_DADOS__", "; ".join(data.get("concorrentes_sem_dados_2025", [])) or "nenhum")
            .replace("__GERADO_EM__", date.today().strftime("%d/%m/%Y")))

    destino = os.path.join(OUTPUT_DIR, "Concorrencia_Matriz.html")
    with open(destino, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Tela gerada: {destino} ({os.path.getsize(destino):,} bytes)")


if __name__ == "__main__":
    main()
