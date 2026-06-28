"""
07_concorrentes_municipio.py
Gera seção "Concorrentes por Município" e injeta no dashboard da marca.

Uso:
    python 07_concorrentes_municipio.py Apogeu
    python 07_concorrentes_municipio.py  # padrão = Apogeu
"""
import os, sys, json, csv
import pandas as pd

ANALISE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ANALISE_DIR)
from config import RESULTADOS_CSV, OUTPUT_DIR, CSV_SEP, CSV_ENCODING, CHUNK_SIZE

TABELA_ESCOLA = os.path.join(
    os.path.dirname(ANALISE_DIR), "DADOS", "Tabela_Escola_2025.csv"
)

# Configuração por marca (extensível para os demais dashboards)
BRAND_CONFIG = {
    "Apogeu": {
        "municipio": "Juiz de Fora",
        "uf": "MG",
        "dashboard": "Apogeu_Dashboard.html",
        "cor_primaria": "#1e326e",
        "codigos_proprios": [31317101, 31356816, 31256285, 31380024, 31363383],
    },
    "Matriz Educação": {
        "municipio": "Rio de Janeiro",
        "municipios": ["Rio de Janeiro", "Duque de Caxias", "São João de Meriti", "Nova Iguaçu"],
        "uf": "RJ",
        "dashboard": "Matriz_Educação_Dashboard.html",
        "cor_primaria": "#166534",
        "codigos_proprios": [33187789, 33183368, 33048185, 33197466, 33187762, 33192685, 33190674, 33187770],
    },
    "QI Bilíngue": {
        "municipio": "Rio de Janeiro",
        "uf": "RJ",
        "dashboard": "QI_Bilíngue_Dashboard.html",
        "cor_primaria": "#4c1d95",
        "codigos_proprios": [33135924, 33071721, 33156026, 33199400, 33124418, 33143331, 33187924],
    },
    "Colégio Leonardo da Vinci": {
        "municipio": "Porto Alegre",
        "uf": "RS",
        "dashboard": "Colegio_Leonardo_da_Vinci_Dashboard.html",
        "cor_primaria": "#b44408",
        "codigos_proprios": [43172423, 43172440, 43213278],
    },
    "Cubo Global": {
        "municipio": "Rio de Janeiro",
        "uf": "RJ",
        "dashboard": "Cubo_Global_Dashboard.html",
        "cor_primaria": "#097570",
        "codigos_proprios": [33178828, 33186260],
    },
}

SCORE_COLS = ["NU_NOTA_LC", "NU_NOTA_CH", "NU_NOTA_CN", "NU_NOTA_MT", "NU_NOTA_REDACAO"]
AREAS_PRES = ["CN", "CH", "LC", "MT"]
USECOLS = [
    "CO_ESCOLA", "NO_MUNICIPIO_ESC", "SG_UF_ESC",
    "TP_DEPENDENCIA_ADM_ESC", "TP_STATUS_REDACAO",
] + [f"TP_PRESENCA_{a}" for a in AREAS_PRES] + SCORE_COLS


# ── 1. Extração e ranking ─────────────────────────────────────────────────────

def extrair_e_rankear(marca: str) -> dict:
    cfg = BRAND_CONFIG[marca]
    target_mun = cfg["municipio"].strip().lower()
    target_uf  = cfg["uf"].strip().upper()

    print(f"  Varrendo RESULTADOS_2025 ({os.path.getsize(RESULTADOS_CSV)//1024//1024} MB)...")

    acc: dict[int, dict] = {}  # co_escola → somas/contagem

    for i_chunk, chunk in enumerate(pd.read_csv(
        RESULTADOS_CSV, sep=CSV_SEP, encoding=CSV_ENCODING,
        usecols=USECOLS, dtype={"CO_ESCOLA": "Int64"}, chunksize=CHUNK_SIZE,
    ), start=1):
        # Filtros de elegibilidade
        mask = (
            (chunk["TP_DEPENDENCIA_ADM_ESC"] == 4) &   # rede privada
            (chunk["TP_STATUS_REDACAO"] == 1)            # redação válida
        )
        for a in AREAS_PRES:
            mask &= (chunk[f"TP_PRESENCA_{a}"] == 1)    # presença em todas as áreas
        chunk = chunk[mask].dropna(subset=SCORE_COLS)

        if chunk.empty:
            continue

        chunk = chunk.copy()
        chunk["MEDIA"] = chunk[SCORE_COLS].mean(axis=1)

        for co_raw, grp in chunk.groupby("CO_ESCOLA", sort=False):
            if pd.isna(co_raw):
                continue
            co = int(co_raw)
            mun_mode = grp["NO_MUNICIPIO_ESC"].mode()
            uf_mode  = grp["SG_UF_ESC"].mode()

            if co not in acc:
                acc[co] = {
                    "n": 0, "lc": 0.0, "ch": 0.0, "cn": 0.0,
                    "mt": 0.0, "rd": 0.0, "media": 0.0,
                    "mun": mun_mode.iloc[0] if len(mun_mode) else "",
                    "uf":  uf_mode.iloc[0]  if len(uf_mode)  else "",
                }
            acc[co]["n"]     += len(grp)
            acc[co]["lc"]    += float(grp["NU_NOTA_LC"].sum())
            acc[co]["ch"]    += float(grp["NU_NOTA_CH"].sum())
            acc[co]["cn"]    += float(grp["NU_NOTA_CN"].sum())
            acc[co]["mt"]    += float(grp["NU_NOTA_MT"].sum())
            acc[co]["rd"]    += float(grp["NU_NOTA_REDACAO"].sum())
            acc[co]["media"] += float(grp["MEDIA"].sum())

        print(f"    Chunk {i_chunk}: {len(acc):,} escolas acumuladas...", end="\r")

    print(f"\n  Total nacional: {len(acc):,} escolas privadas com dados completos.")

    # Calcular médias finais
    for v in acc.values():
        n = v["n"]
        for k in ("lc", "ch", "cn", "mt", "rd", "media"):
            v[k] = round(v[k] / n, 2)

    # Ranking nacional por média geral (decrescente)
    ranking_nac = {
        co: pos
        for pos, (co, _) in enumerate(
            sorted(acc.items(), key=lambda x: -x[1]["media"]), start=1
        )
    }

    # Ler nomes do Tabela_Escola
    print("  Lendo nomes das escolas (Tabela_Escola_2025.csv)...")
    nomes: dict[int, str] = {}
    with open(TABELA_ESCOLA, encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            co_str = row.get("CO_ENTIDADE", "").strip()
            if co_str.isdigit():
                co = int(co_str)
                if co in acc:
                    nomes[co] = row.get("NO_ENTIDADE", "").strip()

    print(f"  Nomes encontrados: {len(nomes):,}")

    codigos_proprios = set(cfg["codigos_proprios"])

    def _grupos_para_municipio(mun_name: str) -> dict:
        tmun = mun_name.strip().lower()
        jf = {
            co: v for co, v in acc.items()
            if v["mun"].strip().lower() == tmun
            and v["uf"].strip().upper() == target_uf
        }
        print(f"  Escolas em {mun_name}/{target_uf}: {len(jf)}")
        jf_sorted = sorted(jf.items(), key=lambda x: -x[1]["media"])
        rank_local = {co: i + 1 for i, (co, _) in enumerate(jf_sorted)}
        grupos: dict[str, list] = {"lt30": [], "de30a59": [], "ge60": []}
        for co, v in jf_sorted:
            n = v["n"]
            grupo = "lt30" if n < 30 else ("de30a59" if n <= 59 else "ge60")
            grupos[grupo].append({
                "pos_geral": ranking_nac.get(co, 9999),
                "pos_local": rank_local[co],
                "co_escola": co,
                "nome":      nomes.get(co, f"Escola {co}"),
                "alunos":    n,
                "lc":        v["lc"],
                "ch":        v["ch"],
                "cn":        v["cn"],
                "mt":        v["mt"],
                "rd":        v["rd"],
                "media":     v["media"],
                "is_marca":  co in codigos_proprios,
            })
        for g, items in grupos.items():
            print(f"    Grupo {g}: {len(items)} escola(s)")
        return grupos

    municipios_lista = cfg.get("municipios")
    if municipios_lista and len(municipios_lista) > 1:
        return {mun: _grupos_para_municipio(mun) for mun in municipios_lista}
    else:
        return _grupos_para_municipio(cfg["municipio"])


# ── 2. Geração do HTML da seção ───────────────────────────────────────────────

def _css_botoes() -> str:
    return """
  .concmun-btn {
    padding: 7px 18px; border-radius: 20px; border: 1.5px solid #cbd5e1;
    background: #fff; color: #475569; font-size: 0.83rem; cursor: pointer;
    transition: all 0.15s ease; font-family: inherit;
  }
  .concmun-btn:hover { border-color: #1e326e; color: #1e326e; background: #f0f4ff; }
  .concmun-btn.active { background: #1e326e; color: #fff; border-color: #1e326e; font-weight: 600; }
"""


def _html_secao(marca: str, cfg: dict) -> str:
    uf  = cfg["uf"]
    municipios_lista = cfg.get("municipios")
    multi_mun = municipios_lista and len(municipios_lista) > 1

    if multi_mun:
        desc = (
            f"Escolas privadas com participantes no ENEM 2025 no mesmo município de cada unidade — "
            f"<strong>{uf}</strong>. Com redação válida e presença em todas as áreas objetivas. "
            f"<strong>★</strong> = unidade {marca}. Ordenado por Nota Geral (média LC+CH+CN+MT+RD)."
        )
        mun_btns = "\n    ".join(
            f'<button class="concmun-btn{"  active" if i == 0 else ""}" data-mun="{m}">{m}</button>'
            for i, m in enumerate(municipios_lista)
        )
        mun_tabs_html = f"""
  <div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;border-bottom:1px solid #e2e8f0;padding-bottom:12px" id="concmunMunTabs">
    {mun_btns}
  </div>"""
    else:
        mun = cfg["municipio"]
        desc = (
            f"Escolas privadas com participantes no ENEM 2025 em <strong>{mun} — {uf}</strong>, "
            f"com redação válida e presença em todas as áreas objetivas. "
            f"<strong>★</strong> = unidade {marca}. Ordenado por Nota Geral (média LC+CH+CN+MT+RD)."
        )
        mun_tabs_html = ""

    return f"""
<p class="section-titulo" id="sec-concorrentes-mun">Concorrentes por Município</p>
<div class="card" style="margin-bottom:16px">
  <div class="card-sub" style="margin-bottom:14px">{desc}</div>{mun_tabs_html}
  <div style="display:flex;gap:8px;margin-bottom:18px;flex-wrap:wrap" id="concmunTabs">
    <button class="concmun-btn" data-grupo="lt30">Menos de 30 alunos</button>
    <button class="concmun-btn active" data-grupo="de30a59">De 30 a 59 alunos</button>
    <button class="concmun-btn" data-grupo="ge60">60 ou mais alunos</button>
  </div>
  <div id="concmunTabela" style="overflow-x:auto"></div>
</div>
"""


def _js_render(cfg: dict) -> str:
    cor = cfg["cor_primaria"]
    municipios_lista = cfg.get("municipios")
    multi_mun = municipios_lista and len(municipios_lista) > 1
    first_mun = municipios_lista[0] if multi_mun else ""

    # Trecho JS exclusivo para multi-município
    if multi_mun:
        multi_init = f"  var _currentMun = '{first_mun}';"
        data_access = "CONCORRENTES_MUN[_currentMun][grupo]"
        filtrar_mun_fn = """
  window.filtrarMunicipio = function(mun) {
    _currentMun = mun;
    _concmunPage = {};
    document.querySelectorAll('#concmunMunTabs .concmun-btn').forEach(function(b) {
      b.classList.toggle('active', b.dataset.mun === mun);
    });
    document.querySelectorAll('#concmunTabs .concmun-btn').forEach(function(b) {
      b.classList.toggle('active', b.dataset.grupo === 'de30a59');
    });
    renderConcMun('de30a59');
  };
  document.querySelectorAll('#concmunMunTabs .concmun-btn').forEach(function(b) {
    b.addEventListener('click', function() { filtrarMunicipio(b.dataset.mun); });
  });"""
    else:
        multi_init = ""
        data_access = "CONCORRENTES_MUN[grupo]"
        filtrar_mun_fn = ""

    return f"""
// ── Concorrentes por Município ────────────────────────────────────────────────
(function() {{
  var _concmunPage = {{}};
  var PAGE_SIZE = 50;
{multi_init}

  function th(txt, right) {{
    var w = right ? ';width:72px' : '';
    return '<th style="padding:8px ' + (right ? '10px' : '14px') + ';text-align:' + (right ? 'right' : 'left') +
      ';white-space:nowrap;background:#1a3a6e;color:white;font-size:0.77rem;font-weight:600;letter-spacing:0.04em;border-bottom:none' + w + '">' + txt + '</th>';
  }}
  function td(v, right, extra) {{
    return '<td style="padding:7px ' + (right ? '10px' : '14px') + ';text-align:' + (right ? 'right' : 'left') +
      ';' + (extra || '') + '">' + v + '</td>';
  }}

  function buildPagination(grupo, current, total) {{
    if (total <= 1) return '';
    function pgBtn(label, page, isActive, isDisabled) {{
      var s = 'border-radius:8px;width:36px;height:36px;font-size:0.9rem;font-family:inherit;cursor:' +
        (isDisabled || isActive ? 'default' : 'pointer') + ';';
      if (isActive)    s += 'border:none;background:#1a3a6e;color:white;';
      else if (isDisabled) s += 'border:none;background:#e2e8f0;color:#94a3b8;';
      else             s += 'border:1.5px solid #cbd5e1;background:white;color:#475569;';
      var extra = (!isDisabled && !isActive)
        ? ' data-g="' + grupo + '" data-p="' + page + '" data-t="' + total +
          '" onclick="window._concmunGo(this.dataset.g,+this.dataset.p,+this.dataset.t)"' : '';
      return '<button style="' + s + '"' + extra + '>' + label + '</button>';
    }}
    var nav = '<div style="display:flex;align-items:center;justify-content:center;gap:6px;margin-top:16px;flex-wrap:wrap">';
    nav += pgBtn('&#8249;', current - 1, false, current <= 1);
    var pages = [];
    if (total <= 7) {{
      for (var i = 1; i <= total; i++) pages.push(i);
    }} else {{
      pages.push(1);
      if (current > 3) pages.push(-1);
      for (var i = Math.max(2, current - 1); i <= Math.min(total - 1, current + 1); i++) pages.push(i);
      if (current < total - 2) pages.push(-1);
      pages.push(total);
    }}
    pages.forEach(function(p) {{
      if (p === -1) {{
        nav += '<span style="color:#64748b;font-size:0.85rem;width:36px;text-align:center">…</span>';
      }} else {{
        nav += pgBtn(p, p, p === current, false);
      }}
    }});
    nav += pgBtn('&#8250;', current + 1, false, current >= total);
    nav += '</div>';
    return nav;
  }}

  window._concmunGo = function(grupo, page, total) {{
    if (page < 1 || page > total) return;
    _concmunPage[grupo] = page;
    renderConcMun(grupo);
  }};

  function renderConcMun(grupo) {{
    var page = _concmunPage[grupo] || 1;
    var allRows = {data_access} || [];
    var cont = document.getElementById('concmunTabela');
    if (!cont) return;
    if (!allRows.length) {{
      cont.innerHTML = '<p style="color:#94a3b8;text-align:center;padding:28px">Nenhuma escola neste grupo.</p>';
      return;
    }}
    var totalPages = Math.ceil(allRows.length / PAGE_SIZE);
    if (page > totalPages) {{ page = 1; _concmunPage[grupo] = 1; }}
    var start = (page - 1) * PAGE_SIZE;
    var rows = allRows.slice(start, start + PAGE_SIZE);

    var html = '<table style="width:100%;border-collapse:collapse;font-size:0.84rem">';
    html += '<thead><tr>';
    html += '<th style="padding:8px 14px;text-align:left;white-space:nowrap;background:#1a3a6e;color:white;font-size:0.77rem;font-weight:600;letter-spacing:0.04em;border-bottom:none;width:100px">Posição Geral</th>' +
            '<th style="padding:8px 10px;text-align:right;white-space:nowrap;background:#1a3a6e;color:white;font-size:0.77rem;font-weight:600;letter-spacing:0.04em;border-bottom:none;width:72px">Posição</th>' +
            '<th style="padding:8px 14px;text-align:left;background:#1a3a6e;color:white;font-size:0.77rem;font-weight:600;letter-spacing:0.04em;border-bottom:none;width:35%">Escola</th>' +
            th('Alunos', true) + th('LC', true) + th('CH', true) +
            th('CN', true) + th('MT', true) + th('RD', true) + th('Média', true);
    html += '</tr></thead><tbody>';

    rows.forEach(function(r, idx) {{
      var isMarca = r.is_marca;
      var posGrupo = start + idx + 1;
      var bg  = isMarca ? '#eef2ff' : (idx % 2 === 0 ? '#ffffff' : '#f8fafc');
      var fw  = isMarca ? '700' : '400';
      var cor = isMarca ? '{cor}' : '#1e293b';
      var star = isMarca ? ' ★' : '';
      html += '<tr style="background:' + bg + ';border-bottom:1px solid #f1f5f9">';
      html += td('<span style="color:#94a3b8;font-size:0.77rem">' + r.pos_geral + '</span>', false);
      html += td('<strong style="color:' + cor + '">' + posGrupo + '</strong>', true);
      html += '<td style="padding:7px 14px;text-align:left">' +
                '<span style="font-weight:' + fw + ';color:' + cor + '">' + r.nome.toLowerCase().replace(/(?:^|\\s|-)\\S/g, function(c) {{ return c.toUpperCase(); }}) + star + '</span>' +
                '<br><span style="font-size:0.72rem;color:#94a3b8">' + r.co_escola + '</span>' +
              '</td>';
      html += td(r.alunos, true);
      html += td(r.lc.toFixed(2), true);
      html += td(r.ch.toFixed(2), true);
      html += td(r.cn.toFixed(2), true);
      html += td(r.mt.toFixed(2), true);
      html += td(r.rd.toFixed(2), true);
      html += td('<strong style="color:' + (isMarca ? '{cor}' : '#334155') + '">' + r.media.toFixed(2) + '</strong>', true);
      html += '</tr>';
    }});

    html += '</tbody></table>';
    html += buildPagination(grupo, page, totalPages);
    cont.innerHTML = html;
  }}

  window.filtrarConcMun = function(grupo) {{
    document.querySelectorAll('#concmunTabs .concmun-btn').forEach(function(b) {{
      b.classList.toggle('active', b.dataset.grupo === grupo);
    }});
    renderConcMun(grupo);
  }};
{filtrar_mun_fn}
  document.querySelectorAll('#concmunTabs .concmun-btn').forEach(function(b) {{
    b.addEventListener('click', function() {{ filtrarConcMun(b.dataset.grupo); }});
  }});

  renderConcMun('de30a59');
}})();
"""


# ── 3. Injeção no dashboard ───────────────────────────────────────────────────

def injetar_no_dashboard(marca: str, grupos: dict):
    cfg = BRAND_CONFIG[marca]
    dash_path = os.path.join(OUTPUT_DIR, cfg["dashboard"])

    print(f"  Lendo {dash_path} ({os.path.getsize(dash_path)//1024} KB)...")
    with open(dash_path, encoding="utf-8") as f:
        html = f.read()

    # Guarda ponto de restauração em caso de erro
    html_original = html

    # ── a) CSS: inserir antes de </style> (idempotente) ───────────────────────
    css = _css_botoes()
    if ".concmun-btn {" not in html:
        style_close = "</style>"
        if style_close not in html:
            print("  ERRO: </style> não encontrado — abortando.")
            return
        html = html.replace(style_close, css + style_close, 1)
        print("  CSS injetado.")
    else:
        print("  CSS já presente — mantido.")

    # ── b) const CONCORRENTES_MUN: substituir ou inserir ──────────────────────
    const_js = f"const CONCORRENTES_MUN = {json.dumps(grupos, ensure_ascii=False)};"
    if "const CONCORRENTES_MUN = " in html:
        idx = html.find("const CONCORRENTES_MUN = ")
        eol = html.find("\n", idx)
        html = html[:idx] + const_js + html[eol:]
        print("  const CONCORRENTES_MUN substituído.")
    else:
        bench_label_marker = 'const BENCH_LABEL = '
        idx = html.find(bench_label_marker)
        if idx == -1:
            print("  ERRO: 'const BENCH_LABEL' não encontrado — abortando.")
            return
        eol = html.find("\n", idx)
        html = html[:eol + 1] + const_js + "\n" + html[eol + 1:]
        print("  const CONCORRENTES_MUN injetado.")

    # ── c) HTML da seção: substituir ou inserir ───────────────────────────────
    secao = _html_secao(marca, cfg)
    HTML_ID = 'id="sec-concorrentes-mun"'
    if HTML_ID in html:
        # Substituir do início do parágrafo até o fim do card div
        p_start = html.find('\n<p class="section-titulo" id="sec-concorrentes-mun">')
        if p_start == -1:
            p_start = html.find('<p class="section-titulo" id="sec-concorrentes-mun">')
        card_open = html.find('<div class="card"', p_start)
        depth = 0
        i = card_open
        while i < len(html):
            if html[i:i+4] == '<div':
                depth += 1
            elif html[i:i+6] == '</div>':
                depth -= 1
                if depth == 0:
                    end = i + 6
                    break
            i += 1
        if html[end:end+1] == '\n':
            end += 1
        html = html[:p_start] + '\n' + secao.strip('\n') + '\n' + html[end:]
        print("  HTML da seção substituído.")
    else:
        if "</main>" not in html:
            print("  ERRO: </main> não encontrado — abortando.")
            return
        html = html.replace("</main>", secao + "</main>", 1)
        print("  HTML da seção injetado.")

    # ── d) JS render: substituir ou inserir ───────────────────────────────────
    js_render = _js_render(cfg)
    JS_ANCHOR = "// ── Concorrentes por Munic"
    if JS_ANCHOR in html:
        js_start = html.find(JS_ANCHOR)
        # Volta ao início da linha
        line_start = html.rfind('\n', 0, js_start)
        if line_start == -1:
            line_start = js_start
        end_marker = "})();"
        js_end = html.find(end_marker, js_start)
        if js_end != -1:
            js_end += len(end_marker)
            if html[js_end:js_end+1] == '\n':
                js_end += 1
            html = html[:line_start + 1] + js_render.lstrip('\n') + html[js_end:]
            print("  JS render substituído.")
        else:
            print("  WARN: fim do bloco JS não encontrado — inserindo.")
            last_script = html.rfind("</script>")
            html = html[:last_script] + js_render + "\n" + html[last_script:]
    else:
        last_script = html.rfind("</script>")
        if last_script == -1:
            print("  ERRO: </script> não encontrado — abortando.")
            return
        html = html[:last_script] + js_render + "\n" + html[last_script:]
        print("  JS render injetado.")

    # ── Salvar ────────────────────────────────────────────────────────────────
    with open(dash_path, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = os.path.getsize(dash_path) // 1024
    print(f"  Dashboard atualizado: {dash_path}  ({size_kb} KB)")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    marca = sys.argv[1] if len(sys.argv) > 1 else "Apogeu"

    if marca not in BRAND_CONFIG:
        print(f"Marca '{marca}' não configurada em BRAND_CONFIG. Disponíveis: {list(BRAND_CONFIG)}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  Concorrentes por Município — {marca}")
    print(f"{'='*60}\n")

    grupos = extrair_e_rankear(marca)

    # Salvar JSON intermediário
    json_path = os.path.join(OUTPUT_DIR, f"concorrentes_mun_{marca}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(grupos, f, ensure_ascii=False, indent=2)
    print(f"  JSON salvo: {json_path}")

    injetar_no_dashboard(marca, grupos)

    print(f"\n{'='*60}")
    print("  Concluído. Abra o dashboard localmente para revisar.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
