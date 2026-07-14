# -*- coding: utf-8 -*-
"""Gerador do HTML de análise por habilidade (multimarcas)."""
import json

ACCENT = "#2563eb"

def gerar_html(D, accent=None):
    dados = json.dumps(D, ensure_ascii=False)
    marca = D.get("marca", "Apogeu")
    acc = accent or D.get("accent") or ACCENT
    html = TEMPLATE.replace("/*__DATA__*/", dados).replace("__ACCENT__", acc)
    # troca as ocorrências textuais fixas de "Apogeu" pela marca-alvo
    html = html.replace("Apogeu - Análise por Habilidade", f"{marca} - Análise por Habilidade")
    html = html.replace('<div class="logo">Apogeu</div>', f'<div class="logo">{marca}</div>')
    html = html.replace("Rede Apogeu", f"{marca}")
    html = html.replace("inscritos do Apogeu", f"inscritos do {marca}")
    return html


TEMPLATE = r"""<!doctype html>
<html lang="pt-BR"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Apogeu - Análise por Habilidade | ENEM 2025</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script>window.__CHARTFONT__=function(){if(window.Chart){Chart.defaults.font.family="'Segoe UI', system-ui, sans-serif";Chart.defaults.color="#334155";}};</script>
<style>
:root{--accent:__ACCENT__;--ink:#0f172a;--muted:#64748b;--line:#e2e8f0;--bg:#f1f5f9;}
*{box-sizing:border-box}
body{margin:0;font-family:'Segoe UI',system-ui,sans-serif;color:var(--ink);background:var(--bg);}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px 80px;}
header{background:#fff;border-bottom:3px solid var(--accent);}
.hd{max-width:1180px;margin:0 auto;padding:22px 20px;display:flex;align-items:center;gap:16px;}
.hd .logo{font-size:26px;font-weight:800;color:var(--accent);letter-spacing:-.5px;}
.hd .sub{color:var(--muted);font-size:14px;border-left:1px solid var(--line);padding-left:16px;}
h2{font-size:19px;margin:38px 0 6px;letter-spacing:-.3px;}
h2 .tag{font-size:12px;font-weight:600;color:var(--accent);text-transform:uppercase;letter-spacing:.5px;display:block;margin-bottom:2px;}
.desc{color:var(--muted);font-size:13.5px;margin:0 0 16px;max-width:820px;line-height:1.5;}
.card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:20px;margin-bottom:16px;box-shadow:0 1px 2px rgba(15,23,42,.04),0 6px 16px rgba(15,23,42,.05);}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;}
.kpi{background:#fff;border:1px solid var(--line);border-radius:14px;padding:18px 20px;box-shadow:0 1px 2px rgba(15,23,42,.04),0 6px 16px rgba(15,23,42,.05);}
.kpi .v{font-size:28px;font-weight:800;color:var(--accent);}
.kpi .l{font-size:12.5px;color:var(--muted);margin-top:2px;}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--muted);margin:6px 0 14px;align-items:center;}
.sw{display:inline-block;width:13px;height:13px;border-radius:3px;margin-right:5px;vertical-align:-2px;}
.tabs{display:flex;gap:8px;margin:0 0 12px;flex-wrap:wrap;}
.tabs button{padding:7px 16px;border-radius:20px;border:2px solid var(--line);background:#fff;font:inherit;font-size:13px;font-weight:600;color:var(--muted);cursor:pointer;transition:all .15s;}
.tabs button.on{background:var(--azul,var(--accent));border-color:var(--azul,var(--accent));color:#fff;}
.heat-area{margin-bottom:18px;}
.heat-area h4{margin:0 0 8px;font-size:14px;color:var(--ink);}
.heat-area h4 small{color:var(--muted);font-weight:400;}
.grid{display:grid;grid-template-columns:repeat(15,1fr);gap:4px;}
.cell{aspect-ratio:1;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:#fff;cursor:help;position:relative;}
.cell span{opacity:.95}
.cell .hn{position:absolute;top:2px;left:4px;font-size:8px;font-weight:600;opacity:.7}
.grow-row{display:grid;grid-template-columns:28px 1fr 92px;gap:16px;align-items:center;
  padding:11px 0;border-bottom:1px solid #f1f5f9;}
.grow-row:last-child{border-bottom:0;}
.gr-rank{color:#cbd5e1;font-size:14px;font-weight:800;text-align:center;font-variant-numeric:tabular-nums;}
.gr-main{min-width:0;}
.gr-top{display:flex;gap:9px;align-items:baseline;font-size:13px;margin-bottom:7px;
  white-space:nowrap;overflow:hidden;}
.gr-hab{flex:none;font-weight:700;color:var(--ink);}
.gr-hab b{color:var(--accent);}
.gr-desc{color:var(--muted);font-size:12.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0;}
.gr-track{height:7px;border-radius:4px;background:#eef2f7;overflow:hidden;}
.gr-track i{display:block;height:100%;border-radius:4px;}
.gr-metric{text-align:right;line-height:1.15;}
.gr-metric b{font-size:15.5px;font-variant-numeric:tabular-nums;color:var(--ink);}
.gr-metric span{display:block;font-size:11px;color:var(--muted);margin-top:1px;}
.gr-metric span.hi{color:var(--accent);font-weight:600;}
table{width:100%;border-collapse:collapse;font-size:13px;}
th,td{padding:8px 10px;text-align:left;border-bottom:1px solid var(--line);}
th{color:var(--muted);font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.3px;}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums;}
select{font:inherit;font-size:14px;padding:8px 12px;border:1px solid var(--line);border-radius:8px;background:#fff;}
.two{display:grid;grid-template-columns:1fr 1fr;gap:16px;}
.dif-wrap{position:relative;height:300px;}
@media(max-width:800px){.two{grid-template-columns:1fr}.grid{grid-template-columns:repeat(10,1fr)}}
.chip{display:inline-block;padding:2px 8px;border-radius:20px;font-size:11px;font-weight:600;}
.foot{color:var(--muted);font-size:12px;line-height:1.6;margin-top:30px;border-top:1px solid var(--line);padding-top:16px;}
.mini{font-size:12px;color:var(--muted);margin:2px 0 0;}
.tip{position:fixed;z-index:60;max-width:340px;background:#0f172a;color:#fff;padding:13px 15px;border-radius:11px;box-shadow:0 10px 30px rgba(15,23,42,.28);font-size:13px;line-height:1.5;pointer-events:none;opacity:0;transition:opacity .12s ease;}
.tip.on{opacity:1;}
.tip .th{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:7px;}
.tip .badge{font-weight:700;font-size:12px;letter-spacing:.4px;color:#93c5fd;background:none;padding:0;border-radius:0;}
.tip .pct{font-weight:700;font-size:12.5px;background:#1e293b;padding:3px 9px;border-radius:12px;white-space:nowrap;}
.tip .td{color:#e6ebf3;}
.tip .tn{color:#94a3b8;font-size:11.5px;margin-top:8px;border-top:1px solid #1e293b;padding-top:7px;}
details.dic{background:#fff;border:1px solid var(--line);border-radius:12px;margin:-4px 0 16px;overflow:hidden;box-shadow:0 1px 2px rgba(0,0,0,.03);}
details.dic>summary{cursor:pointer;padding:15px 20px;font-weight:600;font-size:14.5px;list-style:none;
  display:flex;justify-content:space-between;align-items:center;gap:12px;}
details.dic>summary::-webkit-details-marker{display:none;}
details.dic>summary .arw{color:var(--accent);font-size:12.5px;font-weight:600;white-space:nowrap;}
details.dic[open]>summary{border-bottom:1px solid var(--line);}
details.dic[open]>summary .arw span{display:inline-block;transform:rotate(180deg);}
.dic-body{padding:4px 20px 18px;}
.dic-area-h{margin:18px 0 4px;font-size:12px;font-weight:700;color:var(--accent);
  text-transform:uppercase;letter-spacing:.5px;}
.dic-tbl{width:100%;border-collapse:collapse;font-size:13px;}
.dic-tbl td{padding:7px 8px;border-bottom:1px solid #eef2f6;vertical-align:top;line-height:1.4;}
.dic-tbl td.hb{font-weight:700;color:var(--accent);white-space:nowrap;width:44px;}
.dic-tbl td.ac{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;width:120px;}
.badge-anul{font-size:10.5px;background:#fef3c7;color:#92400e;padding:2px 8px;border-radius:10px;font-weight:600;}
.freqchip{font-size:10px;background:#e0e7ff;color:#3730a3;padding:1px 7px;border-radius:9px;font-weight:600;white-space:nowrap;}
.diag-card{display:flex;flex-direction:column;}
#diag-insights{flex:1;display:flex;flex-direction:column;gap:12px;}
#diag-insights .lr-item{flex:1;display:flex;flex-direction:column;justify-content:center;}
#cons-dist,#cons-sig{flex:1;display:flex;flex-direction:column;gap:16px;}
.cons-bot{flex:1;display:flex;flex-direction:column;gap:12px;}
.cons-bot>*{flex:1;}
.cons-bot .lr-item{display:flex;flex-direction:column;justify-content:center;}
.lr-item{border-left:3px solid;border-radius:0 9px 9px 0;padding:13px 16px;}
.lr-item .lr-h{font-size:11.5px;font-weight:700;text-transform:uppercase;letter-spacing:.4px;margin-bottom:4px;}
.lr-item .lr-t{font-size:12.5px;color:#334155;line-height:1.5;}
.lr-item .lr-t b{color:var(--ink);}
.lr-warn{border-color:#d97706;background:#fffbeb;} .lr-warn .lr-h{color:#b45309;}
.lr-info{border-color:#2563eb;background:#eff6ff;} .lr-info .lr-h{color:#1d4ed8;}
.lr-ok{border-color:#16a34a;background:#f0fdf4;} .lr-ok .lr-h{color:#15803d;}
.seg-bar{display:flex;height:32px;border-radius:8px;overflow:hidden;font-size:12px;font-weight:700;color:#fff;}
.seg{display:flex;align-items:center;justify-content:center;min-width:30px;}
.seg-leg{display:flex;gap:18px;flex-wrap:wrap;margin-top:12px;font-size:12.5px;color:var(--muted);}
.seg-leg i{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:6px;vertical-align:-1px;}
.seg-leg b{color:var(--ink);}
.cons-stat{display:flex;gap:14px;align-items:center;margin-top:18px;padding:14px 16px;background:#f8fafc;
  border:1px solid var(--line);border-radius:10px;font-size:13px;color:#334155;line-height:1.45;}
.cons-big{font-size:30px;font-weight:800;color:var(--accent);line-height:1;white-space:nowrap;}
.fraca-bars{display:flex;flex-direction:column;gap:9px;margin-bottom:4px;}
.fb-row{display:grid;grid-template-columns:132px 1fr 42px;gap:10px;align-items:center;font-size:12.5px;}
.fb-l{color:var(--ink);}
.fb-track{height:15px;background:#eef2f7;border-radius:5px;overflow:hidden;}
.fb-track i{display:block;height:100%;background:var(--accent);border-radius:5px;}
.fb-v{text-align:right;color:var(--muted);font-variant-numeric:tabular-nums;}
.boletim-grid{display:grid;grid-template-columns:340px 1fr;gap:20px;align-items:start;}
@media(max-width:800px){.boletim-grid{grid-template-columns:1fr}}
.nota-row{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--line);font-size:14px;}
.nota-row b{font-variant-numeric:tabular-nums;}
</style></head>
<body>
<header><div class="hd">
  <div class="logo">Apogeu</div>
  <div class="sub">Análise por Habilidade &middot; Matriz de Referência ENEM 2025<br>
  <span style="font-size:12px">Diagnóstico item a item &middot; resposta &times; gabarito &times; habilidade</span></div>
</div></header>
<div class="wrap">

<h2><span class="tag">Panorama</span>Acerto médio por área de conhecimento</h2>
<p class="desc">Percentual de acerto nas questões objetivas (item a item), calculado a partir das respostas
reais dos alunos cruzadas com o gabarito da sua prova. Base da leitura pedagógica que segue.</p>
<div class="kpis" id="kpis"></div>

<h2><span class="tag">Mapa de calor</span>Domínio de habilidades (H1&ndash;H30 por área)</h2>
<p class="desc">Cada célula é uma habilidade da Matriz de Referência. A cor indica o percentual de acerto da rede
naquela habilidade - do vermelho (dificuldade) ao verde (domínio). Passe o mouse para ver o acerto e as respostas.
Alterne entre a rede e cada unidade.</p>
<div class="tabs" id="heat-tabs"></div>
<div class="legend">
  <span><span class="sw" style="background:#b91c1c"></span>&lt;40%</span>
  <span><span class="sw" style="background:#ea580c"></span>40&ndash;50%</span>
  <span><span class="sw" style="background:#d4a017"></span>50&ndash;60%</span>
  <span><span class="sw" style="background:#65a30d"></span>60&ndash;70%</span>
  <span><span class="sw" style="background:#15803d"></span>&gt;70%</span>
</div>
<div class="card" id="heat"></div>
<details class="dic"><summary>Dicionário de habilidades - Matriz de Referência ENEM (H1&ndash;H30 por área)
  <span class="arw">expandir <span>&#9662;</span></span></summary>
  <div class="dic-body" id="dic-body"></div>
</details>

<h2><span class="tag">Prioridade</span>Habilidades-gargalo da rede</h2>
<p class="desc">As 15 habilidades de <b>menor domínio</b> na rede - o foco de recuperação, da mais crítica para a menos.
A <b>barra</b> e a <b>cor</b> representam o <b>% de acerto</b>: quanto menor e mais vermelha, mais crítica.
À direita, a <b>frequência</b> na prova (destacada em azul quando a habilidade aparece muito) indica o peso de cada uma na nota.</p>
<div class="card" id="gargalos"></div>

<h2><span class="tag">Diagnóstico</span>Erro evitável (fáceis) &times; teto da rede (difíceis)</h2>
<p class="desc">Cada questão é classificada em <b>fácil</b>, <b>média</b> ou <b>difícil</b> pelo parâmetro de dificuldade (TRI).
A leitura pedagógica: acerto alto nas <b>fáceis</b> é esperado - se cai, indica <b>erro evitável</b> (desatenção, gestão
de tempo, lacuna básica); o acerto nas <b>difíceis</b> mede o <b>teto da rede</b> (defasagem real em conteúdo avançado).</p>
<div class="two">
  <div class="card"><h4 style="margin:0 0 10px;font-size:14px;text-align:center">Acerto por dificuldade da questão - rede</h4><div class="dif-wrap"><canvas id="difChart"></canvas></div></div>
  <div class="card diag-card">
    <h4 style="margin:0 0 4px;font-size:14px">Leitura rápida do diagnóstico</h4>
    <p class="mini" style="margin-bottom:14px">Erro evitável e teto vêm do gráfico ao lado; a gestão de tempo, do padrão de itens em branco.</p>
    <div id="diag-insights"></div>
  </div>
</div>

<h2><span class="tag">Nível aluno</span>Consistência dos alunos - equilíbrio entre áreas</h2>
<p class="desc">Dois alunos com a mesma nota geral podem ter perfis opostos. Para cada aluno medimos o
<b>gap entre a melhor e a pior área objetiva</b> (CN, CH, LC e MT; a redação fica de fora por estar em outra escala).
Isso revela quem é <b>equilibrado</b> e quem é <b>especialista</b> - e onde está o furo, acionável por grupo, sem depender de nome.</p>
<div class="two">
  <div class="card diag-card">
    <h4 style="margin:0 0 4px;font-size:14px">Equilíbrio da rede</h4>
    <p class="mini" style="margin-bottom:16px">Gap entre a melhor e a pior das 4 áreas objetivas, por aluno.</p>
    <div id="cons-dist"></div>
  </div>
  <div class="card diag-card">
    <h4 style="margin:0 0 4px;font-size:14px">A assinatura da rede</h4>
    <p class="mini" style="margin-bottom:14px">Para quantos alunos cada área é a mais fraca - o furo a atacar.</p>
    <div id="cons-sig"></div>
  </div>
</div>

<div class="foot" id="foot"></div>
</div>
<div id="tip" class="tip"></div>

<script>
window.__CHARTFONT__();
const D = /*__DATA__*/;
const AREAS=["CN","CH","LC","MT"], AN=D.area_nomes, ACC="__ACCENT__";
const UN=D.unidades; // [{code,nome,n}]
const fmt=v=>v==null?"-":v.toFixed(1);
const DESC={}; AREAS.forEach(a=>{DESC[a]={};(D.dicionario[a]||[]).forEach(r=>DESC[a][r.hab]=r.desc);});
function corAcerto(v){
  if(v==null) return "#cbd5e1";
  if(v<40) return "#b91c1c"; if(v<50) return "#ea580c";
  if(v<60) return "#d4a017"; if(v<70) return "#65a30d"; return "#15803d";
}

// KPIs
(function(){
  const el=document.getElementById("kpis"); let h="";
  h+=`<div class="kpi"><div class="v">${D.n_alunos}</div><div class="l">alunos analisados</div></div>`;
  AREAS.forEach(a=>{const v=D.acerto_area.rede[a];
    h+=`<div class="kpi"><div class="v">${fmt(v)}%</div><div class="l">${AN[a]} &middot; ${D.n_presentes[a]} presentes</div></div>`;});
  el.innerHTML=h;
})();

// HEATMAP
let heatMode="rede";
function renderHeat(){
  const el=document.getElementById("heat"); let h="";
  AREAS.forEach(a=>{
    const rows=D.heat[a];
    h+=`<div class="heat-area"><h4>${AN[a]} <small>- ${rows.length} habilidades avaliadas</small></h4><div class="grid">`;
    rows.forEach(r=>{
      const v = heatMode==="rede" ? r.rede : r.unidades[heatMode];
      const desc=(r.desc||"").replace(/"/g,"&quot;");
      const anul=r.status==="anulada";
      const bg=anul?"repeating-linear-gradient(45deg,#e2e8f0,#e2e8f0 5px,#eef2f7 5px,#eef2f7 10px)":corAcerto(v);
      const inner=anul?"&empty;":(v==null?"-":Math.round(v));
      const nResp = heatMode==="rede" ? r.n : (r.unidades_n ? (r.unidades_n[heatMode]||0) : 0);
      const nAl = heatMode==="rede" ? D.n_avaliados[a] : ((D.n_avaliados_und[heatMode]||{})[a]||0);
      h+=`<div class="cell" style="background:${bg}${anul?';color:#94a3b8':''}" data-area="${a}" data-hab="${r.hab}"
        data-desc="${desc}" data-v="${v==null?'':v}" data-n="${nResp}" data-alunos="${nAl}" data-status="${r.status}">
        <span class="hn">H${r.hab}</span><span>${inner}</span></div>`;
    });
    h+=`</div></div>`;
  });
  el.innerHTML=h;
}
(function(){
  const t=document.getElementById("heat-tabs");
  let h=`<button class="on" data-m="rede">Rede Apogeu</button>`;
  UN.forEach(u=>h+=`<button data-m="${u.code}">${u.nome} (${u.n})</button>`);
  t.innerHTML=h;
  t.querySelectorAll("button").forEach(b=>b.onclick=()=>{
    t.querySelectorAll("button").forEach(x=>x.classList.remove("on"));
    b.classList.add("on"); heatMode=b.dataset.m; renderHeat();
  });
  renderHeat();
})();

// TOOLTIP elegante (mapa de calor)
(function(){
  const tip=document.getElementById("tip"), heat=document.getElementById("heat");
  function move(e){
    const pad=14, w=tip.offsetWidth, h=tip.offsetHeight;
    let x=e.clientX+pad, y=e.clientY+pad;
    if(x+w>innerWidth-8) x=e.clientX-w-pad;
    if(y+h>innerHeight-8) y=e.clientY-h-pad;
    tip.style.left=x+"px"; tip.style.top=y+"px";
  }
  heat.addEventListener("mouseover",e=>{
    const c=e.target.closest(".cell"); if(!c) return;
    const a=c.dataset.area, hab=c.dataset.hab, v=c.dataset.v, n=c.dataset.n, al=c.dataset.alunos, st=c.dataset.status;
    const desc=c.dataset.desc||"(sem descrição)";
    const anul = st==="anulada";
    const pctxt = anul ? "anulada" : (v==="" ? "sem dados" : (+v).toFixed(1)+"% de acerto");
    let tn;
    if (anul) tn = "Questão anulada pelo INEP (item previamente exposto) - sem dados de acerto";
    else {
      const R=+n, A=+al;
      if (A>0 && R % A === 0) { const q=R/A; tn = `${R} respostas = ${A} alunos &times; ${q} ${q===1?'questão da prova':'questões da prova'}`; }
      else tn = `${R} respostas de ${A} alunos`;
    }
    tip.innerHTML=`<div class="th"><span class="badge">${a} &middot; H${hab}</span><span class="pct">${pctxt}</span></div>
      <div class="td">${desc}</div><div class="tn">${tn}</div>`;
    tip.classList.add("on"); move(e);
  });
  heat.addEventListener("mousemove",e=>{ if(tip.classList.contains("on")) move(e); });
  heat.addEventListener("mouseout",e=>{
    if(!e.relatedTarget || !e.relatedTarget.closest || !e.relatedTarget.closest(".cell")) tip.classList.remove("on");
  });
})();

// DICIONÁRIO expansível
(function(){
  const el=document.getElementById("dic-body"); let h="";
  AREAS.forEach(a=>{
    h+=`<div class="dic-area-h">${AN[a]}</div><table class="dic-tbl"><tbody>`;
    D.dicionario[a].forEach(r=>{
      let ac;
      if(r.status==="anulada") ac=`<span class="badge-anul">anulada</span>`;
      else if(r.status==="ausente") ac=`<span class="mini">não avaliada</span>`;
      else ac=`<b style="color:${corAcerto(r.acerto)}">${fmt(r.acerto)}%</b> <span class="mini">&middot; ${r.n} respostas</span>`;
      h+=`<tr><td class="hb">H${r.hab}</td><td>${r.desc||""}</td><td class="ac">${ac}</td></tr>`;
    });
    h+=`</tbody></table>`;
  });
  el.innerHTML=h;
})();

// GARGALOS - uma variável só (acerto) governa ordem, barra, cor e número
function gargColor(v){ // gradiente vermelho profundo -> âmbar conforme o acerto sobe
  const t=Math.max(0,Math.min(1,(v-8)/(42-8)));
  const r=Math.round(153+(245-153)*t), g=Math.round(27+(158-27)*t), b=Math.round(27+(11-27)*t);
  return `rgb(${r},${g},${b})`;
}
(function(){
  const el=document.getElementById("gargalos"); let h="";
  D.gargalos.forEach((g,i)=>{
    const w=Math.max(3, g.acerto);
    const hi = g.freq>=2.0;
    const desc=(g.desc||"").replace(/"/g,"&quot;");
    h+=`<div class="grow-row">
      <div class="gr-rank">${i+1}</div>
      <div class="gr-main">
        <div class="gr-top"><span class="gr-hab"><b>${g.area}</b> H${g.hab}</span><span class="gr-desc" title="${desc}">${g.desc||''}</span></div>
        <div class="gr-track"><i style="width:${w}%;background:${gargColor(g.acerto)}"></i></div>
      </div>
      <div class="gr-metric"><b>${fmt(g.acerto)}%</b><span class="${hi?'hi':''}">${g.freq} q/prova</span></div>
    </div>`;
  });
  el.innerHTML=h;
})();

// DIFICULDADE
(function(){
  const labels=AREAS.map(a=>AN[a]);
  const mk=(t,r,c)=>({label:r,data:AREAS.map(a=>D.dificuldade[a].rede[t]),backgroundColor:c,borderRadius:5});
  new Chart(document.getElementById("difChart"),{type:"bar",data:{labels,
    datasets:[mk("facil","fáceis","#15803d"),mk("medio","médios","#d4a017"),mk("dificil","difíceis","#b91c1c")]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{title:{display:false},legend:{position:"bottom",labels:{font:{family:"'Segoe UI', system-ui, sans-serif"}}}},
      scales:{y:{beginAtZero:true,max:100,ticks:{callback:v=>v+"%"}}}}});
})();
// LEITURA RÁPIDA do diagnóstico (sintetiza o gráfico de dificuldade; preenche o card)
(function(){
  const avg=k=>Math.round(AREAS.reduce((s,a)=>s+D.dificuldade[a].rede[k],0)/AREAS.length);
  const fac=avg("facil"), dif=avg("dificil"), evit=100-fac;
  const b=D.branco_fim.rede, mx=Math.max(...AREAS.map(a=>b[a]));
  document.getElementById("diag-insights").innerHTML=`
    <div class="lr-item lr-warn"><div class="lr-h">Erro evitável - o ganho mais rápido</div>
      <div class="lr-t">A rede acerta cerca de <b>${fac}%</b> das questões <b>fáceis</b> - ou seja, aproximadamente
      <b>${evit}%</b> ficam pelo caminho. Recuperar parte disso não depende de conteúdo novo, apenas de consistência.</div></div>
    <div class="lr-item lr-info"><div class="lr-h">Teto da rede</div>
      <div class="lr-t">Nas questões <b>difíceis</b>, o acerto médio é de <b>${dif}%</b>. Elevar esse patamar exige
      aprofundamento de conteúdo avançado - um ganho mais lento e estrutural.</div></div>
    <div class="lr-item lr-ok"><div class="lr-h">Gestão de tempo - sem alerta</div>
      <div class="lr-t"><b>&lt; ${fmt(mx)}%</b> de itens em branco no terço final, em todas as áreas
      (${AREAS.map(a=>a+" "+fmt(b[a])+"%").join(" &middot; ")}). Concluir a prova não é um gargalo.</div></div>`;
})();

// CONSISTÊNCIA - distribuição do equilíbrio (esquerda)
(function(){
  const c=D.consistencia, cat=c.cats;
  const order=[["equilibrado","Equilibrado","#15803d"],["moderado","Moderado","#d4a017"],["desbalanceado","Desbalanceado","#b91c1c"]];
  let seg=`<div class="seg-bar">`;
  order.forEach(([k,,col])=>{seg+=`<div class="seg" style="width:${cat[k].pct}%;background:${col}">${cat[k].pct}%</div>`;});
  seg+=`</div>`;
  const leg=`<div class="seg-leg">`+order.map(([k,l,col])=>`<span><i style="background:${col}"></i>${l} <b>${cat[k].n}</b></span>`).join("")+`</div>`;
  const bands=`<div class="mini" style="margin-top:8px">Faixas do gap: equilibrado &lt; 80 &middot; moderado 80&ndash;160 &middot; desbalanceado &gt; 160 pontos.</div>`;
  const desnivel=cat.moderado.pct+cat.desbalanceado.pct;
  const stat=`<div class="cons-stat"><div class="cons-big">${c.gap_mediano}</div>
    <div>pontos de <b>gap mediano</b> - metade dos alunos tem um desnível maior que esse entre a melhor e a pior área.</div></div>`;
  const interp=`<div class="lr-item lr-info"><div class="lr-h">A oportunidade</div>
    <div class="lr-t"><b>${desnivel}%</b> dos alunos têm desnível relevante (moderado ou maior): uma área puxa a nota para
    baixo e pode ser recuperada com reforço dirigido. Os outros <b>${cat.equilibrado.pct}%</b> já rendem de forma homogênea.</div></div>`;
  document.getElementById("cons-dist").innerHTML=`<div class="cons-top">${seg}${leg}${bands}</div><div class="cons-bot">${stat}${interp}</div>`;
})();
// CONSISTÊNCIA - assinatura da rede (direita): área mais fraca + leitura
(function(){
  const c=D.consistencia, mf=c.mais_fraca, ms=c.mais_forte;
  const worst=AREAS.slice().sort((a,b)=>mf[b]-mf[a]);
  const mx=Math.max(...AREAS.map(a=>mf[a]));
  let bars=`<div class="fraca-bars">`;
  worst.forEach(a=>{bars+=`<div class="fb-row"><span class="fb-l">${AN[a]}</span>
    <div class="fb-track"><i style="width:${Math.round(mf[a]/mx*100)}%"></i></div><span class="fb-v">${fmt(mf[a])}%</span></div>`;});
  bars+=`</div>`;
  const forte=AREAS.slice().sort((a,b)=>ms[b]-ms[a])[0], fraca=worst[0];
  const li=`<div class="lr-item lr-info"><div class="lr-h">Perfil da rede</div>
      <div class="lr-t"><b>${AN[forte]}</b> é a área mais forte de <b>${fmt(ms[forte])}%</b> dos alunos - a rede tem assinatura de exatas.</div></div>
    <div class="lr-item lr-warn"><div class="lr-h">O furo - alvo nº 1</div>
      <div class="lr-t"><b>${AN[fraca]}</b> é a pior área de <b>${fmt(mf[fraca])}%</b> dos alunos. Uma tutoria dirigida a
      ${AN[fraca]} recupera o maior grupo de uma vez, sem precisar identificar cada aluno.</div></div>`;
  document.getElementById("cons-sig").innerHTML=`<div class="cons-top">${bars}</div><div class="cons-bot">${li}</div>`;
})();

// FOOT
document.getElementById("foot").innerHTML=`
<b>Metodologia.</b> Acerto por habilidade calculado item a item: para cada aluno, a resposta marcada (TX_RESPOSTAS)
é comparada ao gabarito da sua versão de prova (ITENS_PROVA_2025), e cada item é atribuído a uma das 30 habilidades
da Matriz de Referência (CO_HABILIDADE) da respectiva área. Itens anulados foram excluídos. Dificuldade = parâmetro
TRI (b) do item, em terços. Redação por competência = média de NU_NOTA_COMP1..5 entre redações válidas.
<br><br><b>Base:</b> ${D.n_alunos} inscritos do Apogeu no ENEM 2025 (${UN.map(u=>u.nome+": "+u.n).join(" &middot; ")}).
<br><b>Limitação:</b> o questionário socioeconômico (PARTICIPANTES) não possui chave de ligação com os resultados em 2025,
portanto não há recorte socioeconômico por aluno/unidade. A habilidade individual (poucos itens por aluno) é usada apenas de
forma agregada; no nível do aluno, reporta-se o acerto por área e as habilidades mais erradas.`;
</script>
</body></html>
"""
