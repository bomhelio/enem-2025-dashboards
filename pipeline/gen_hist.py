# -*- coding: utf-8 -*-
"""Gera e insere a secao Evolucao Historica para uma marca (single ou multi-municipio).
Uso: python gen_hist.py "Matriz Educação"
"""
import io, os, re, sys, json
from collections import Counter

REPO = r"C:\Users\helio.barbosa\AppData\Local\Temp\enem-2025-dashboards"
SCR = r"C:\Users\HELIO~1.BAR\AppData\Local\Temp\claude\C--Users-helio-barbosa\c037e361-3139-4823-a131-2dac8f91f58f\scratchpad"
BENCH = json.load(open(os.path.join(SCR, "historico_benchmark.json"), encoding="utf-8"))
UNID = json.load(open(os.path.join(SCR, "historico_unidades.json"), encoding="utf-8"))
TOP = json.load(open(os.path.join(SCR, "historico_top100.json")))
AR = ["CN", "CH", "LC", "MT", "RD"]
UF_NOME = {"RJ": "Rio de Janeiro", "MG": "Minas Gerais", "RS": "Rio Grande do Sul",
           "SP": "São Paulo", "ES": "Espírito Santo", "PR": "Paraná", "SC": "Santa Catarina"}

BRANDS = {
    "Apogeu": "apogeu.html",
    "QI Bilíngue": "qi-bilingue.html",
    "Matriz Educação": "matriz-educacao.html",
    "Cubo Global": "cubo-global.html",
    "Colégio Leonardo da Vinci": "leonardo-da-vinci.html",
}


def yrs(anos):
    return {y: {k: anos[y][k] for k in AR} for y in sorted(anos)}


def mapear_nomes(marca, html):
    t = io.open(html, encoding="utf-8").read()
    d = json.loads(re.search(r'const DADOS\s*=\s*(\{.*?\});\s*\n', t, re.S).group(1))
    dash = {}
    for nome, info in d["unidades"].items():
        a = info["areas"]
        dash[nome] = (a['CN']['media'], a['CH']['media'], a['LC']['media'], a['MT']['media'], info['redacao']['media'])
    mp = {}
    for co, node in UNID.items():
        if node.get("marca") != marca or "2025" not in node["anos"]:
            continue
        a = node["anos"]["2025"]
        key = (a['CN'], a['CH'], a['LC'], a['MT'], a['RD'])
        for nome, dk in dash.items():
            if all(abs(x - y) < 0.2 for x, y in zip(key, dk)):
                mp[co] = nome
                break
    return mp


def montar_consts(marca, mp):
    hu = {mp[co]: yrs(UNID[co]["anos"]) for co in mp}
    uni_mun = {mp[co]: str(UNID[co]["municipio"]) for co in mp if UNID[co].get("municipio")}
    cnt = Counter(UNID[co]["municipio"] for co in mp if UNID[co].get("municipio"))
    mun_ordem = [str(c) for c, _ in cnt.most_common()]
    municipios, uf = {}, None
    for mc in mun_ordem:
        info = BENCH["municipios"][mc]
        municipios[mc] = {"nome": info["nome"], "anos": yrs(info["anos"])}
        uf = info["uf"]
    top_anos = {y: {a: TOP[y][a]["media_top100"] for a in AR} for y in ("2024", "2025")}
    HB = {"municipios": municipios, "mun_ordem": mun_ordem,
          "uf": {"sigla": uf, "nome": UF_NOME.get(uf, uf), "anos": yrs(BENCH["ufs"][uf]["anos"])},
          "brasil": {"anos": yrs(BENCH["brasil"]["anos"])},
          "top100": {"anos": top_anos}}
    return hu, HB, uf, uni_mun


def consts_js(hu, HB, uni_mun):
    return ("const HIST_UNIDADES = " + json.dumps(hu, ensure_ascii=False) + ";\n"
            + "const HIST_BENCH = " + json.dumps(HB, ensure_ascii=False) + ";\n"
            + "const UNI_MUN = " + json.dumps(uni_mun, ensure_ascii=False) + ";\n")


SCRIPT_TMPL = '''<script>
(function(){
__CONSTS__
  const METRICAS = [["GERAL","Geral"],["CN","C. Natureza"],["CH","C. Humanas"],["LC","Linguagens"],["MT","Matemática"],["RD","Redação"]];
  const PAL = ["#2563eb","#f97316","#16a34a","#9333ea","#0891b2","#db2777","#ca8a04","#4f46e5"];
  const TOP = "#f59e0b", C_JF = "#334155", C_MG = "#94a3b8", C_BR = "#b6c2cf";
  const cssv = k => (getComputedStyle(document.documentElement).getPropertyValue(k)||"").trim();
  const ACC = () => cssv('--azul-m') || '#2563eb';
  const MORD = HIST_BENCH.mun_ordem, MULTI = MORD.length > 1;
  const ufNome = HIST_BENCH.uf.nome, ufSig = HIST_BENCH.uf.sigla;
  let metMer="GERAL", metUni="GERAL", munSel=MORD[0], munSel2=MORD[0];

  function val(o,met){ if(!o) return null;
    if(met==="GERAL"){ const v=["CN","CH","LC","MT","RD"].map(k=>o[k]).filter(x=>x!=null); return v.length?+(v.reduce((s,x)=>s+x,0)/v.length).toFixed(1):null; }
    return o[met]==null?null:o[met]; }
  const serie=(anos,years,met)=>years.map(y=>val(anos[y],met));
  const topSerie=(years,met)=>years.map(y=>{const o=HIST_BENCH.top100.anos[y];return o?val(o,met):null;});

  function opts(met){ const ti=met==="GERAL"?"Nota média (5 áreas)":(met==="RD"?"Nota média de Redação":"Nota média");
    return {responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
      plugins:{legend:{position:'bottom',labels:{boxWidth:12,font:{size:10},usePointStyle:true}},
        tooltip:{callbacks:{label:c=>`${c.dataset.label}: ${c.parsed.y!=null?c.parsed.y:'—'}`}}},
      scales:{y:{ticks:{font:{size:10}},grid:{color:'#f1f5f9'},title:{display:true,text:ti,font:{size:10}}},
              x:{ticks:{font:{size:11}},grid:{display:false}}}}; }

  let chMer=null, chUni=null;
  function syncChart(inst, id, labels, datasets, opt){
    if(inst && inst.data.datasets.length===datasets.length){
      inst.data.labels=labels;
      datasets.forEach((d,i)=>{ for(const k in d) inst.data.datasets[i][k]=d[k]; });
      inst.options=opt; inst.update(); return inst;
    }
    if(inst) inst.destroy();
    return new Chart(document.getElementById(id),{type:'line',data:{labels,datasets},options:opt});
  }
  function buildMercado(){ const years=["2021","2022","2023","2024","2025"], m=metMer;
    const mun=HIST_BENCH.municipios[munSel];
    const ds=[
      {label:'Rede privada de '+mun.nome, data:serie(mun.anos,years,m), borderColor:C_JF, backgroundColor:C_JF+'22', borderWidth:2.8, tension:0.25, pointRadius:4, pointBackgroundColor:C_JF, fill:false},
      {label:'Rede privada de '+ufSig+' (estado)', data:serie(HIST_BENCH.uf.anos,years,m), borderColor:C_MG, borderWidth:1.6, borderDash:[6,4], tension:0.25, pointRadius:2, fill:false},
      {label:'Brasil', data:serie(HIST_BENCH.brasil.anos,years,m), borderColor:C_BR, borderWidth:1.6, borderDash:[2,3], tension:0.25, pointRadius:2, fill:false},
      {label:'Top 100 BR', data:topSerie(years,m), borderColor:TOP, borderWidth:1.8, borderDash:[4,3], tension:0.25, pointRadius:3, pointBackgroundColor:TOP, spanGaps:false, fill:false},
    ];
    chMer=syncChart(chMer,'chartHistMercado',years,ds,opts(m)); }

  function buildUnidades(){ const years=["2024","2025"], m=metUni; let i=0;
    const ds=Object.entries(HIST_UNIDADES).map(([nome,anos])=>{ const c=(typeof corIdx==='function'&&corIdx(nome))?corIdx(nome):PAL[i++%PAL.length];
      return {label:nome,data:serie(anos,years,m),borderColor:c,backgroundColor:c,borderWidth:2.4,tension:0,pointRadius:4,fill:false}; });
    const munU=HIST_BENCH.municipios[munSel2];
    ds.push({label:'Rede privada de '+munU.nome,data:serie(munU.anos,years,m),borderColor:C_JF,borderWidth:1.8,borderDash:[6,4],pointRadius:3,fill:false});
    ds.push({label:'Rede privada de '+ufSig+' (estado)',data:serie(HIST_BENCH.uf.anos,years,m),borderColor:C_MG,borderWidth:1.6,borderDash:[4,4],pointRadius:3,fill:false});
    ds.push({label:'Brasil',data:serie(HIST_BENCH.brasil.anos,years,m),borderColor:C_BR,borderWidth:1.6,borderDash:[2,3],pointRadius:3,fill:false});
    ds.push({label:'Top 100 BR',data:topSerie(years,m),borderColor:TOP,borderWidth:1.8,borderDash:[4,3],pointRadius:3,fill:false});
    chUni=syncChart(chUni,'chartHistUnidades',years,ds,opts(m)); }

  function btns(box, items, ativo, onPick){ box.innerHTML=''; const a=ACC();
    items.forEach(([k,lbl])=>{ const on=k===ativo;
      const b=document.createElement('button'); b.textContent=lbl;
      b.style.cssText=`padding:5px 12px;border-radius:7px;border:1px solid ${on?a:'#e2e8f0'};background:${on?a:'#fff'};color:${on?'#fff':'#475569'};font-size:0.74rem;font-weight:600;cursor:pointer;letter-spacing:0.02em;transition:all .15s`;
      b.onclick=()=>onPick(k); box.appendChild(b); }); }

  function selMerArea(){ btns(document.getElementById('histMetricSel'), METRICAS, metMer, k=>{metMer=k;selMerArea();buildMercado();}); }
  function selMun(){ const box=document.getElementById('histMunSel'); if(!box||!MULTI) return;
    btns(box, MORD.map(c=>[c, HIST_BENCH.municipios[c].nome]), munSel, k=>{munSel=k;selMun();buildMercado();}); }
  function applyMunFilter(){ if(!chUni) return;
    chUni.data.datasets.forEach((d,i)=>{ const mc=UNI_MUN[d.label]; if(mc!==undefined) chUni.getDatasetMeta(i).hidden=(mc!==String(munSel2)); });
    chUni.update(); }
  function selMun2(){ const box=document.getElementById('histMunSel2'); if(!box||!MULTI) return;
    btns(box, MORD.map(c=>[c, HIST_BENCH.municipios[c].nome]), munSel2, k=>{munSel2=k;selMun2();buildUnidades();applyMunFilter();}); }
  function selUniArea(){ btns(document.getElementById('histMetricSel2'), METRICAS, metUni, k=>{metUni=k;selUniArea();buildUnidades();}); }

  function init(){ if(!document.getElementById('chartHistMercado')) return; selMun(); selMun2(); selMerArea(); selUniArea(); buildMercado(); buildUnidades(); }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init); else init();
})();
</script>
'''


def secao_html(marca, HB, uf):
    multi = len(HB["mun_ordem"]) > 1
    sig = HB["uf"]["sigla"]
    if multi:
        titulo1 = "Médias da rede privada por município — 2021 a 2025"
        sub1 = (f'Escolha o município e a área. Nota média da rede privada municipal ao longo dos anos, '
                f'com referências de <span style="color:#94a3b8;font-weight:600">{sig} (estado)</span>, '
                f'<span style="color:#64748b;font-weight:600">Brasil</span> e '
                f'<span style="color:#f59e0b;font-weight:600">Top 100 BR</span>.')
        munsel1 = '<div id="histMunSel" class="hist-sel" style="margin-bottom:2px"></div>'
        munsel2 = '<div id="histMunSel2" class="hist-sel" style="margin-bottom:2px"></div>'
        sub2 = (f'Escolha o município de referência e a área. Nota média de cada unidade {marca}, comparada à '
                f'<span style="color:#334155;font-weight:600">rede privada do município selecionado</span>, à '
                f'<span style="color:#94a3b8;font-weight:600">{sig} (estado)</span>, ao '
                f'<span style="color:#64748b;font-weight:600">Brasil</span> e ao '
                f'<span style="color:#f59e0b;font-weight:600">Top 100 BR</span> (linhas tracejadas).')
    else:
        mun_nome = HB["municipios"][HB["mun_ordem"][0]]["nome"]
        titulo1 = f"Médias da rede privada de {mun_nome} — 2021 a 2025"
        sub1 = (f'Nota média da rede privada do município ao longo dos anos, com referências de '
                f'<span style="color:#94a3b8;font-weight:600">{sig} (estado)</span>, '
                f'<span style="color:#64748b;font-weight:600">Brasil</span> e '
                f'<span style="color:#f59e0b;font-weight:600">Top 100 BR</span>. Use os botões para alternar a área.')
        munsel1 = munsel2 = ''
        sub2 = (f'Nota média de cada unidade {marca}, comparada à '
                f'<span style="color:#334155;font-weight:600">rede privada de {mun_nome}</span>, à '
                f'<span style="color:#94a3b8;font-weight:600">{sig} (estado)</span>, ao '
                f'<span style="color:#64748b;font-weight:600">Brasil</span> e ao '
                f'<span style="color:#f59e0b;font-weight:600">Top 100 BR</span> (linhas tracejadas).')
    return f'''<p class="section-titulo" id="sec-historico" style="scroll-margin-top:84px">Evolução Histórica</p>
<div class="card" style="margin-bottom:16px">
  <div class="card-titulo">{titulo1}</div>
  <div class="card-sub">{sub1}</div>
  {munsel1}
  <div id="histMetricSel" class="hist-sel"></div>
  <div class="chart-wrap" style="height:320px"><canvas id="chartHistMercado"></canvas></div>
  <div class="hist-nota">O <strong>Top 100 BR</strong> (média das 100 melhores escolas do país) só aparece a partir de 2024: ranquear escolas exige o código da escola, que o INEP suprimiu nos microdados de 2021 a 2023.</div>
</div>
<div class="card" style="margin-bottom:16px">
  <div class="card-titulo">Médias das Unidades — 2024 e 2025</div>
  <div class="card-sub">{sub2}</div>
  {munsel2}
  <div id="histMetricSel2" class="hist-sel"></div>
  <div class="chart-wrap" style="height:300px"><canvas id="chartHistUnidades"></canvas></div>
  <div class="hist-nota">A série por escola começa em 2024 — o INEP suprimiu o código da escola de 2021 a 2023, então não é possível recuperar a nota de uma unidade específica nesses anos. O contexto de mercado (gráfico acima), por depender só de município e rede, cobre os cinco anos.</div>
</div>
'''


CSS = '''  .hist-sel { display:flex; gap:6px; flex-wrap:wrap; margin:12px 0 6px; }
  .hist-nota { margin-top:10px; font-size:0.74rem; color:#94a3b8; font-style:italic; line-height:1.5; }
</style>'''


def aplicar(marca):
    html = os.path.join(REPO, BRANDS[marca])
    mp = mapear_nomes(marca, html)
    if not mp:
        print(f"[{marca}] nenhuma unidade casada — abortando"); return
    hu, HB, uf, uni_mun = montar_consts(marca, mp)
    t = io.open(html, encoding="utf-8").read()
    if 'id="sec-historico"' in t:
        print(f"[{marca}] secao ja existe — reverter antes"); return
    HTML = secao_html(marca, HB, uf)
    a1 = '<p class="section-titulo">Filtrar por Unidade</p>'
    assert t.count(a1) == 1, f"[{marca}] anchor filtrar"
    t = t.replace(a1, HTML + a1, 1)
    assert t.count("</style>") >= 1
    t = t.replace("</style>", CSS, 1)
    SC = SCRIPT_TMPL.replace("__CONSTS__", consts_js(hu, HB, uni_mun))
    assert t.count("</body>") == 1
    t = t.replace("</body>", SC + "</body>", 1)
    io.open(html, "w", encoding="utf-8").write(t)
    print(f"[{marca}] OK | unidades={len(mp)} | municipios={len(HB['mun_ordem'])} ({'multi' if len(HB['mun_ordem'])>1 else 'single'}) | uf={uf}")
    print(f"          muns={[HB['municipios'][c]['nome'] for c in HB['mun_ordem']]}")


if __name__ == "__main__":
    aplicar(sys.argv[1])
