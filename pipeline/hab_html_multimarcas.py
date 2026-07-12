# -*- coding: utf-8 -*-
"""Gerador do HTML de análise por habilidade na escala da REDE (multimarcas)."""
import json

ACCENT = "#475569"  # slate neutro (o bloco abrange todas as marcas)


def gerar_html(D):
    dados = json.dumps(D, ensure_ascii=False)
    return TEMPLATE.replace("/*__DATA__*/", dados).replace("__ACCENT__", ACCENT)


TEMPLATE = r"""<!doctype html>
<html lang="pt-BR"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Multimarcas - Diagnóstico por Habilidade | ENEM 2025</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script>if(window.Chart){Chart.defaults.font.family="'Segoe UI', system-ui, sans-serif";Chart.defaults.color="#334155";}</script>
<style>
:root{--accent:__ACCENT__;--ink:#0f172a;--muted:#64748b;--line:#e2e8f0;--bg:#f1f5f9;}
*{box-sizing:border-box}
body{margin:0;font-family:'Segoe UI',system-ui,sans-serif;color:var(--ink);background:var(--bg);}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px 80px;}
header{background:#fff;border-bottom:3px solid var(--accent);}
.hd{max-width:1180px;margin:0 auto;padding:22px 20px;display:flex;align-items:baseline;gap:16px;flex-wrap:wrap;}
.hd .logo{font-size:24px;font-weight:800;color:var(--accent);letter-spacing:-.5px;}
.hd .sub{color:var(--muted);font-size:14px;border-left:1px solid var(--line);padding-left:16px;}
h2{font-size:19px;margin:40px 0 6px;letter-spacing:-.3px;}
h2 .tag{font-size:12px;font-weight:600;color:var(--accent);text-transform:uppercase;letter-spacing:.5px;display:block;margin-bottom:2px;}
.desc{color:var(--muted);font-size:13.5px;margin:0 0 16px;max-width:880px;line-height:1.5;}
.card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:20px;margin-bottom:16px;box-shadow:0 1px 2px rgba(15,23,42,.04),0 6px 16px rgba(15,23,42,.05);}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:8px;}
.kpi{background:#fff;border:1px solid var(--line);border-radius:14px;padding:18px;min-height:84px;display:flex;flex-direction:column;justify-content:center;gap:4px;box-shadow:0 1px 2px rgba(15,23,42,.04),0 6px 16px rgba(15,23,42,.05);}
.kpi .v{font-size:26px;font-weight:800;color:var(--accent);line-height:1;}
.kpi .l{font-size:12.5px;color:var(--muted);}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--muted);margin:8px 0 14px;align-items:center;}
.sw{display:inline-block;width:13px;height:13px;border-radius:3px;margin-right:5px;vertical-align:-2px;}

/* ── S1 gargalos ── */
.garg{display:flex;flex-direction:column;gap:10px;}
.g-row{display:grid;grid-template-columns:minmax(0,1fr) 64px 180px 128px;gap:14px;align-items:center;
  border:1px solid var(--line);border-radius:11px;padding:11px 14px;background:#fff;}
.g-head .ah{font-size:11px;font-weight:700;color:var(--accent);letter-spacing:.3px;}
.g-head .dsc{font-size:12.5px;color:#334155;line-height:1.35;margin-top:1px;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}
.g-rede{text-align:center;}
.g-rede .n{font-size:20px;font-weight:800;}
.g-rede .l{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.4px;}
.g-mini{display:flex;gap:5px;align-items:flex-end;height:44px;}
.g-mini .col{flex:1;display:flex;flex-direction:column;align-items:center;gap:3px;justify-content:flex-end;}
.g-mini .bar{width:100%;border-radius:3px 3px 0 0;min-height:2px;}
.g-mini .nd{font-size:8.5px;color:#cbd5e1;font-weight:700;letter-spacing:.3px;}
.g-mini .cn{font-size:9px;color:var(--muted);}
.tipo{font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:.4px;
  padding:5px 10px;border-radius:12px;text-align:center;white-space:normal;line-height:1.25;}
.tipo small{display:block;font-weight:600;text-transform:none;letter-spacing:0;font-size:10px;color:var(--muted);margin-top:2px;}
.t-universal{background:#fef2f2;color:#b91c1c;}
.t-local{background:#eff6ff;color:#1d4ed8;}
.t-misto{background:#f8fafc;color:#475569;}

/* ── S2 matriz ── */
.mtx{width:100%;border-collapse:collapse;font-size:12.5px;table-layout:fixed;}
.mtx th,.mtx td{padding:8px 6px;text-align:center;border-bottom:1px solid var(--line);vertical-align:middle;}
.mtx th:first-child,.mtx td:first-child{text-align:left;white-space:nowrap;width:42%;}
.mtx thead th{font-size:11px;color:#fff;border-radius:7px 7px 0 0;}
.mtx .cell{color:#fff;font-weight:700;border-radius:6px;padding:6px 4px;min-width:44px;display:inline-block;}
.mtx .small{opacity:.45;}
.mtx td .hcell{display:flex;align-items:center;gap:10px}.mtx td .hb{font-weight:700;flex:0 0 auto}.mtx td .hdsc{color:var(--muted);font-size:11px;flex:1 1 auto;min-width:0;white-space:normal;line-height:1.4}

/* ── S3 heatmap ── */
.tabs{display:flex;gap:8px;margin:0 0 14px;flex-wrap:wrap;}
.tabs button{padding:7px 15px;border-radius:20px;border:2px solid var(--line);background:#fff;font:inherit;font-size:13px;font-weight:600;color:var(--muted);cursor:pointer;transition:all .15s;}
.tabs button.on{color:#fff;}
.heat-area{margin-bottom:16px;}
.heat-area h4{margin:0 0 8px;font-size:13.5px;}.heat-area h4 small{color:var(--muted);font-weight:400;}
.grid{display:grid;grid-template-columns:repeat(15,1fr);gap:4px;}
.cell{aspect-ratio:1;border-radius:6px;display:flex;flex-direction:column;align-items:center;justify-content:center;
  color:#fff;font-size:12px;font-weight:700;cursor:default;}
.cell .hn{font-size:8.5px;font-weight:600;opacity:.9;}
@media(max-width:800px){.grid{grid-template-columns:repeat(10,1fr)}}

/* ── S4 dificuldade ── */
.two{display:grid;grid-template-columns:1.4fr 1fr;gap:16px;}
@media(max-width:820px){.two{grid-template-columns:1fr}}
.dif-wrap{position:relative;height:300px;}
.lr{display:flex;flex-direction:column;gap:12px;height:100%;}
.lr-item{flex:1;border-left:3px solid;border-radius:0 9px 9px 0;padding:12px 15px;display:flex;flex-direction:column;justify-content:center;}
.lr-item .h{font-size:11.5px;font-weight:700;text-transform:uppercase;letter-spacing:.4px;margin-bottom:4px;}
.lr-item .b{font-size:12.5px;color:#334155;line-height:1.45;}
.lr-warn{border-color:#d97706;background:#fffbeb;}.lr-warn .h{color:#b45309;}
.lr-info{border-color:#2563eb;background:#eff6ff;}.lr-info .h{color:#1d4ed8;}

/* ── S5 consistência ── */
.cons-row{display:grid;grid-template-columns:120px 1fr 96px;gap:12px;align-items:center;margin-bottom:10px;}
.cons-row .nm{font-size:13px;font-weight:600;}
.cons-bar{display:flex;height:26px;border-radius:7px;overflow:hidden;border:1px solid var(--line);}
.cons-bar span{display:flex;align-items:center;justify-content:center;font-size:10.5px;color:#fff;font-weight:700;}
.cons-gap{font-size:12px;color:var(--muted);text-align:right;}
.cons-leg{display:flex;gap:16px;font-size:12px;color:var(--muted);margin-bottom:14px;flex-wrap:wrap;}

/* ── tooltip ── */
.tip{position:fixed;z-index:60;max-width:340px;background:#0f172a;color:#fff;padding:13px 15px;border-radius:11px;
  box-shadow:0 10px 30px rgba(15,23,42,.28);font-size:12.5px;line-height:1.5;pointer-events:none;opacity:0;transition:opacity .12s;}
.tip.on{opacity:1;}
.tip .th{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:7px;}
.tip .badge{font-weight:700;font-size:12px;color:#93c5fd;}
.tip .pct{font-weight:700;font-size:12.5px;background:#1e293b;padding:3px 9px;border-radius:12px;white-space:nowrap;}
.tip .tn{color:#94a3b8;font-size:11.5px;margin-top:8px;border-top:1px solid #1e293b;padding-top:7px;}
</style></head>
<body>
<header><div class="hd">
  <div class="logo">Multimarcas</div>
  <div class="sub">Diagnóstico Pedagógico Multimarcas por Habilidade &middot; ENEM 2025</div>
</div></header>
<div class="wrap">

<div class="kpis" id="kpis"></div>
<p class="desc">Item a item, cruzando as respostas de <b id="ntot"></b> alunos das 5 marcas com o gabarito
e a habilidade da Matriz de Referência. O total Multimarcas é a soma das 5 marcas; cada marca funciona como uma unidade de comparação.</p>

<h2><span class="tag">Prioridade das marcas</span>Gargalos e onde eles são universais ou locais</h2>
<p class="desc">As habilidades de menor domínio no conjunto das 5 marcas. <b>Universal</b> (todas as marcas parecidas) pede
intervenção de conteúdo compartilhada; <b>local</b> (uma marca vai bem melhor) pede troca de prática entre marcas.
Barras à direita = acerto de cada marca (A/Q/M/L/C). <span style="color:var(--muted)">n/d = a marca teve menos de 15 itens
naquela habilidade (amostra insuficiente); fica de fora da comparação.</span></p>
<div class="card"><div class="garg" id="garg"></div></div>

<h2><span class="tag">Benchmark interno</span>Matriz marca &times; habilidade-gargalo</h2>
<p class="desc">O acerto de cada marca nas habilidades-gargalo. Como são os piores pontos do conjunto, os valores são baixos
em todas - por isso as cores comparam <b>dentro de cada linha</b>: verde = quem vai relativamente melhor naquele
gargalo, vermelho = pior. Serve para achar quem lidera cada um. <span style="color:var(--muted)">† = amostra pequena, fora da comparação.</span></p>
<div class="card" style="overflow-x:auto"><table class="mtx" id="mtx"></table></div>

<h2><span class="tag">Mapa de calor</span>Domínio de habilidades das 5 marcas (H1-H30 por área)</h2>
<p class="desc">Cada célula é uma habilidade. Alterne entre o total das marcas e cada uma. Passe o mouse para ver o acerto e o nº de itens.</p>
<div class="tabs" id="heat-tabs"></div>
<div class="legend">
  <span><span class="sw" style="background:#c0392b"></span>&lt;40%</span>
  <span><span class="sw" style="background:#e67e22"></span>40-50%</span>
  <span><span class="sw" style="background:#d4a017"></span>50-60%</span>
  <span><span class="sw" style="background:#5a9e2f"></span>60-70%</span>
  <span><span class="sw" style="background:#15803d"></span>&gt;70%</span>
</div>
<div class="card" id="heat"></div>

<h2><span class="tag">Estratégia</span>Erro evitável (fáceis) &times; teto (difíceis) por marca</h2>
<p class="desc">Cada questão é fácil, média ou difícil pelo parâmetro de dificuldade (TRI). Acerto baixo nas
<b>fáceis</b> indica erro evitável (ganho rápido de gestão); o acerto nas <b>difíceis</b> mede o teto de conteúdo.</p>
<div class="two">
  <div class="card"><h4 style="margin:0 0 10px;font-size:14px;text-align:center">Acerto por dificuldade, por marca</h4>
    <div class="dif-wrap"><canvas id="difChart"></canvas></div></div>
  <div class="card"><div class="lr" id="lr"></div></div>
</div>

<h2><span class="tag">Perfil das marcas</span>Consistência dos alunos por marca</h2>
<p class="desc">Equilíbrio entre as 4 áreas objetivas por aluno (redação fora: escala distinta).
<b>Equilibrado</b> = diferença &lt; 80 pts entre a melhor e a pior área; <b>desbalanceado</b> = &ge; 160 pts.</p>
<div class="cons-leg">
  <span><span class="sw" style="background:#15803d"></span>Equilibrado</span>
  <span><span class="sw" style="background:#d4a017"></span>Moderado</span>
  <span><span class="sw" style="background:#c0392b"></span>Desbalanceado</span>
  <span style="margin-left:auto">Gap mediano = diferença típica entre melhor e pior área</span>
</div>
<div class="card" id="cons"></div>

</div>
<div id="tip" class="tip"></div>
<script>
const D=/*__DATA__*/;
const AREAS=["CN","CH","LC","MT"], AN=D.area_nomes, MARCAS=D.marcas;
const tip=document.getElementById("tip");
function corAcerto(v){if(v==null)return "#e2e8f0";if(v<40)return "#c0392b";if(v<50)return "#e67e22";if(v<60)return "#d4a017";if(v<70)return "#5a9e2f";return "#15803d";}
function showTip(html,e){tip.innerHTML=html;tip.classList.add("on");moveTip(e);}
function moveTip(e){const p=14;let x=e.clientX+p,y=e.clientY+p;const r=tip.getBoundingClientRect();
  if(x+r.width>innerWidth-8)x=e.clientX-r.width-p;if(y+r.height>innerHeight-8)y=e.clientY-r.height-p;tip.style.left=x+"px";tip.style.top=y+"px";}
function hideTip(){tip.classList.remove("on");}

// ── KPIs ──
(function(){
  document.getElementById("ntot").textContent=D.n_total.toLocaleString("pt-BR");
  let h=`<div class="kpi"><div class="v">${D.n_total.toLocaleString("pt-BR")}</div><div class="l">alunos nas 5 marcas</div></div>`;
  AREAS.forEach(a=>{h+=`<div class="kpi"><div class="v">${D.acerto_area_rede[a]}%</div><div class="l">acerto ${AN[a]}</div></div>`;});
  document.getElementById("kpis").innerHTML=h;
})();

// ── S1 gargalos ──
(function(){
  const TIPO={universal:["t-universal","Universal","conteúdo compartilhado"],
              local:["t-local","Local","troca entre marcas"],
              misto:["t-misto","Misto","avaliar caso a caso"]};
  let h="";
  D.gargalos.forEach(g=>{
    const mini=MARCAS.map(m=>{const o=g.marcas[m.nome];const v=o.acerto;const isb=(m.nome===g.best);
      if(v==null){
        return `<div class="col"><div class="nd" title="${m.curta}: amostra insuficiente (${o.n} itens)">n/d</div><div class="cn" style="opacity:.4">${m.curta[0]}</div></div>`;
      }
      return `<div class="col"><div class="bar" style="height:${Math.max(4,v*0.42)}px;background:${m.cor};opacity:${isb?1:.55}" title="${m.curta}: ${v}% (${o.n} itens)"></div><div class="cn">${m.curta[0]}</div></div>`;
    }).join("");
    const t=TIPO[g.tipo];
    const bestv=g.marcas[g.best]?g.marcas[g.best].acerto:null;
    h+=`<div class="g-row">
      <div class="g-head"><div class="ah">${g.area} &middot; H${g.hab}</div><div class="dsc">${g.desc||""}</div></div>
      <div class="g-rede"><div class="n" style="color:${corAcerto(g.rede)}">${g.rede}%</div><div class="l">5 marcas</div></div>
      <div class="g-mini">${mini}</div>
      <div class="tipo ${t[0]}">${t[1]}<small>${g.tipo==='local'?'melhor: '+ (D.marcas.find(x=>x.nome===g.best)||{}).curta+' '+bestv+'%':t[2]}</small></div>
    </div>`;
  });
  document.getElementById("garg").innerHTML=h;
})();

// ── S2 matriz ──
(function(){
  const REFCOR="#334155";
  const head="<thead><tr><th style='background:#0f172a;border-radius:7px 7px 0 0'>Habilidade</th>"+
    `<th style="background:${REFCOR}">Multimarcas</th>`+
    MARCAS.map(c=>`<th style="background:${c.cor}">${c.curta}</th>`).join("")+"</tr></thead>";
  let body="<tbody>";
  D.gargalos.forEach(g=>{
    // escala RELATIVA entre as marcas com dado (pior=vermelho, melhor=verde)
    const vals=MARCAS.map(m=>g.marcas[m.nome].acerto).filter(v=>v!=null);
    const vmin=Math.min(...vals), vmax=Math.max(...vals);
    const corRel=(v)=>{if(v==null)return "#e2e8f0";if(vmax===vmin)return "#64748b";
      const t=Math.max(0,Math.min(1,(v-vmin)/(vmax-vmin)));return `hsl(${Math.round(t*125)},55%,42%)`;};
    body+=`<tr><td><div class="hcell"><span class="hb">${g.area} H${g.hab}</span><span class="hdsc" title="${(g.desc||'').replace(/"/g,'&quot;')}">${g.desc||''}</span></div></td>`;
    body+=`<td><span class="cell" style="background:${corRel(g.rede)}">${g.rede}</span></td>`;
    MARCAS.forEach(m=>{const o=g.marcas[m.nome];const v=o.acerto;
      body+=`<td><span class="cell ${o.n<15?'small':''}" style="background:${corRel(v)}">${v==null?'†':v}</span></td>`;});
    body+="</tr>";
  });
  document.getElementById("mtx").innerHTML=head+body+"</tbody>";
})();

// ── S3 heatmap ──
let heatMode="rede";
function renderHeat(){
  const el=document.getElementById("heat");let h="";
  AREAS.forEach(a=>{
    const rows=D.heat[a];
    h+=`<div class="heat-area"><h4>${AN[a]} <small>- ${rows.length} habilidades avaliadas</small></h4><div class="grid">`;
    rows.forEach(r=>{
      const v = heatMode==="rede" ? r.rede : r.marcas[heatMode];
      const desc=(r.desc||"").replace(/"/g,"&quot;");
      h+=`<div class="cell" style="background:${corAcerto(v)}" data-a="${a}" data-h="${r.hab}" data-d="${desc}" data-v="${v==null?'':v}" data-n="${r.n}">
        <span class="hn">H${r.hab}</span><span>${v==null?"-":Math.round(v)}</span></div>`;
    });
    h+=`</div></div>`;
  });
  el.innerHTML=h;
  el.querySelectorAll(".cell").forEach(c=>{
    c.onmousemove=e=>{const v=c.dataset.v;const modo=heatMode==="rede"?"Multimarcas":(MARCAS.find(m=>m.nome===heatMode)||{}).curta;
      showTip(`<div class="th"><span class="badge">${c.dataset.a} &middot; H${c.dataset.h}</span><span class="pct">${v===""?"sem dados":v+"% de acerto"}</span></div>
        <div>${c.dataset.d||""}</div><div class="tn">${modo} &middot; ${c.dataset.n} itens avaliados</div>`,e);};
    c.onmouseleave=hideTip;
  });
}
(function(){
  const t=document.getElementById("heat-tabs");
  let h=`<button class="on" data-m="rede" style="background:#334155;border-color:#334155">Multimarcas</button>`;
  MARCAS.forEach(m=>h+=`<button data-m="${m.nome}">${m.curta} (${m.n})</button>`);
  t.innerHTML=h;
  t.querySelectorAll("button").forEach(b=>{
    b.onclick=()=>{
      t.querySelectorAll("button").forEach(x=>{x.classList.remove("on");x.style.background="";x.style.borderColor="";x.style.color="";});
      b.classList.add("on");heatMode=b.dataset.m;
      const cor = heatMode==="rede"?"#334155":(MARCAS.find(m=>m.nome===heatMode)||{}).cor;
      b.style.background=cor;b.style.borderColor=cor;b.style.color="#fff";
      renderHeat();
    };
  });
  renderHeat();
})();

// ── S4 dificuldade ──
(function(){
  const dif=D.dificuldade;
  const mk=(t,lab,c)=>({label:lab,backgroundColor:c,borderRadius:5,
    data:MARCAS.map(m=>dif.marcas[m.nome][t])});
  new Chart(document.getElementById("difChart"),{type:"bar",
    data:{labels:MARCAS.map(m=>m.curta),
      datasets:[mk("facil","fáceis","#15803d"),mk("medio","médios","#d4a017"),mk("dificil","difíceis","#b91c1c")]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{position:"bottom"}},
      scales:{y:{beginAtZero:true,max:100,ticks:{callback:v=>v+"%"}}}}});
  // leitura rápida
  const fac=dif.rede.facil, difi=dif.rede.dificil;
  const bestFac=MARCAS.slice().sort((a,b)=>dif.marcas[b.nome].facil-dif.marcas[a.nome].facil)[0];
  const worstFac=MARCAS.slice().sort((a,b)=>dif.marcas[a.nome].facil-dif.marcas[b.nome].facil)[0];
  document.getElementById("lr").innerHTML=`
    <div class="lr-item lr-warn"><div class="h">Erro evitável - o ganho rápido</div>
      <div class="b">Nas 5 marcas, ${fac}% de acerto nas <b>fáceis</b> - cerca de ${Math.round(100-fac)}% de pontos fáceis ficam pelo caminho.
      Maior folga em <b>${worstFac.curta}</b> (${dif.marcas[worstFac.nome].facil}% nas fáceis); <b>${bestFac.curta}</b> lidera (${dif.marcas[bestFac.nome].facil}%).</div></div>
    <div class="lr-item lr-info"><div class="h">Teto das marcas - o ganho estrutural</div>
      <div class="b">Nas <b>difíceis</b>, o acerto médio das 5 marcas é ${difi}% - elevar esse patamar exige aprofundamento de conteúdo avançado, um ganho mais lento.</div></div>`;
})();

// ── S5 consistência ──
(function(){
  const rows=[{nome:"Rede",curta:"Multimarcas",n:D.consistencia.rede.n,c:D.consistencia.rede}]
    .concat(MARCAS.map(m=>({nome:m.nome,curta:m.curta,n:D.consistencia.marcas[m.nome].n,c:D.consistencia.marcas[m.nome]})));
  let h="";
  rows.forEach(r=>{
    const ca=r.c.cats;const seg=(k,col)=>{const p=ca[k].pct;return p>0?`<span style="width:${p}%;background:${col}">${p>=8?p+'%':''}</span>`:"";};
    h+=`<div class="cons-row"><div class="nm">${r.curta} <span style="color:#94a3b8;font-weight:400;font-size:11px">(${r.n})</span></div>
      <div class="cons-bar">${seg('equilibrado','#15803d')}${seg('moderado','#d4a017')}${seg('desbalanceado','#c0392b')}</div>
      <div class="cons-gap">gap ${r.c.gap_mediano} pts</div></div>`;
  });
  document.getElementById("cons").innerHTML=h;
})();
</script>
</body></html>"""
