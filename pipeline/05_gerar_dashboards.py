"""
05_gerar_dashboards.py
Gera HTMLs de dashboard para marcas especificadas.

Uso:
    python 05_gerar_dashboards.py "Colégio Leonardo da Vinci" "Cubo Global"
    python 05_gerar_dashboards.py   # gera para todas as marcas em config.py

Depende de:
    output/{marca}_resultados.csv   (gerado por 01_extrair.py)
    output/benchmark_municipal.json (benchmark rede privada por município)
    output/benchmark_bairro.json    (comparativo por bairro — opcional)
    output/ranking_posicoes.json    (ranking nacional/UF/mun — opcional)
    output/ranking_toptiers.json    (top 100 Brasil — opcional)
    output/mapa_escola_bairro.json  (nomes de unidades — opcional)
    output/Apogeu_Dashboard.html    (template HTML base)
"""

import os, sys, json, re
import numpy as np
import pandas as pd

# ── Caminhos ──────────────────────────────────────────────────────────────────
ANALISE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ANALISE_DIR)
from config import ESCOLAS, OUTPUT_DIR, CORTES_NOTA, RESULTADOS_CSV, CSV_SEP, CSV_ENCODING

TEMPLATE_HTML  = os.path.join(OUTPUT_DIR, "_template_base.html")
BENCH_MUN_JSON = os.path.join(OUTPUT_DIR, "benchmark_municipal.json")
BENCH_BAIRRO_JSON = os.path.join(OUTPUT_DIR, "bench_bairro_por_marca.json")
RANKING_JSON   = os.path.join(OUTPUT_DIR, "ranking_posicoes.json")
TOPTIERS_JSON  = os.path.join(OUTPUT_DIR, "ranking_toptiers.json")
MAPA_JSON      = os.path.join(OUTPUT_DIR, "mapa_escola_bairro.json")
AUSENTES_JSON  = os.path.join(OUTPUT_DIR, "bairro_ausentes_por_marca.json")

AREAS = ["CN", "CH", "LC", "MT"]
COMPS = {1: "Domínio da Língua", 2: "Compreensão da Proposta",
         3: "Seleção de Argumentos", 4: "Mecanismos de Coesão",
         5: "Proposta de Intervenção"}

# Benchmarks nacionais ENEM 2025 (rede privada nacional)
BRASIL_PRIV = {"CN": 533.6, "CH": 543.8, "LC": 546.5, "MT": 561.9, "RED": 669.3}
BRASIL_GERAL = {"CN": 491.6, "CH": 502.9, "LC": 524.5, "MT": 513.8, "RED": 618.8}


# ── Cálculo de estatísticas ───────────────────────────────────────────────────

def _hist(serie: pd.Series) -> list:
    """10 bins de 100 pontos: 0-100, 100-200, ..., 900-1000."""
    s = serie.dropna()
    bins = [0] * 10
    for v in s:
        idx = min(int(v // 100), 9)
        bins[idx] += 1
    return bins


def _stats_area(serie: pd.Series) -> dict:
    s = serie.dropna()
    if s.empty:
        return {}
    out = {
        "n":       int(len(s)),
        "media":   round(float(s.mean()), 1),
        "mediana": round(float(s.median()), 1),
        "dp":      round(float(s.std()), 1),
        "p25":     round(float(s.quantile(0.25)), 1),
        "p75":     round(float(s.quantile(0.75)), 1),
        "min":     round(float(s.min()), 1),
        "max":     round(float(s.max()), 1),
        "histograma": _hist(s),
    }
    for c in CORTES_NOTA:
        out[f"pct_{c}"] = round(float((s >= c).mean() * 100), 1)
    return out


def _stats_redacao(df: pd.DataFrame) -> dict:
    valida = df[df["TP_STATUS_REDACAO"] == 1]
    n_val  = len(valida)
    n_tot  = len(df)
    n_anut = int((df["TP_STATUS_REDACAO"].isin([2,3,4,5,6,7])).sum())

    notas_red = valida["NU_NOTA_REDACAO"].dropna()
    base = _stats_area(notas_red)

    comps = {}
    for num in range(1, 6):
        col = f"NU_NOTA_COMP{num}"
        if col in valida.columns:
            comps[str(num)] = {"nome": COMPS[num], **_stats_area(valida[col].dropna())}

    faixas = {}
    for f in [0, 200, 400, 600, 800]:
        key = f"{f}-{f+200}"
        faixas[key] = int(((notas_red >= f) & (notas_red < f + 200)).sum())
    faixas["1000-1200"] = int((notas_red == 1000).sum())

    return {
        "n_validas": n_val,
        "pct_nota_zero_anulada": round(n_anut / n_tot * 100, 1) if n_tot else 0,
        "competencias": comps,
        "distribuicao_faixas": faixas,
        **base,
    }


def _stats_nota_geral(presentes2, df_red_valida_mask) -> dict:
    completo = presentes2[df_red_valida_mask]
    if completo.empty:
        return {}
    ng = (completo["NU_NOTA_CN"] + completo["NU_NOTA_CH"] +
          completo["NU_NOTA_LC"] + completo["NU_NOTA_MT"] +
          completo["NU_NOTA_REDACAO"]) / 5
    out = _stats_area(ng)
    out["n_completos"] = int(len(completo))
    return out


def _bloco_df(df: pd.DataFrame, label_estados: list, unidades_n: int) -> dict:
    """Computa todos os stats de um sub-DataFrame (marca inteira ou uma unidade)."""
    n_ins = len(df)
    pres2 = df[
        (df["TP_PRESENCA_CN"] == 1) & (df["TP_PRESENCA_CH"] == 1) &
        (df["TP_PRESENCA_LC"] == 1) & (df["TP_PRESENCA_MT"] == 1)
    ]
    n_pres = len(pres2)

    areas_stats = {}
    for a in AREAS:
        p = df[df[f"TP_PRESENCA_{a}"] == 1][f"NU_NOTA_{a}"]
        areas_stats[a] = _stats_area(p)

    red_stats = _stats_redacao(df)

    val_mask = (pres2["TP_STATUS_REDACAO"] == 1) if len(pres2) else pd.Series([], dtype=bool)
    ng_stats  = _stats_nota_geral(pres2, val_mask) if len(pres2) else {}

    return {
        "n_inscritos":  n_ins,
        "n_presentes":  n_pres,
        "taxa_presenca": round(n_pres / n_ins * 100, 1) if n_ins else 0,
        "n_redacao_valida": red_stats.get("n_validas", 0),
        "pct_problema_redacao": red_stats.get("pct_nota_zero_anulada", 0),
        "areas": areas_stats,
        "redacao": red_stats,
        "competencias": red_stats.get("competencias", {}),
        "nota_geral": ng_stats,
        "faixas_redacao": red_stats.get("distribuicao_faixas", {}),
        "estados": label_estados,
        "unidades_n": unidades_n,
    }


def computar_dados(df: pd.DataFrame, mapa: dict, codigos: list) -> dict:
    """Retorna DADOS = {geral: {...}, unidades: {nome: {...}}}."""
    estados = sorted(df["SG_UF_ESC"].dropna().unique().tolist())
    n_uni   = df["CO_ESCOLA"].nunique()

    geral = _bloco_df(df, estados, n_uni)

    # Per-unit: agrupa por CO_ESCOLA
    unidades = {}
    for co_esc, sub in df.groupby("CO_ESCOLA"):
        co_str = str(int(co_esc))
        # Label: mapa → {label minus "Marca — "} or municipio or code
        if co_str in mapa:
            full_label = mapa[co_str].get("label", co_str)
            # Remove prefix "Marca — " se presente
            partes = full_label.split(" — ", 1)
            nome = partes[-1]
        else:
            # Deriva do município + sequencial se necessário
            mun = sub["NO_MUNICIPIO_ESC"].dropna().mode()
            nome = str(mun.iloc[0]) if len(mun) else co_str
            # Se já existe um com esse nome, adiciona sufixo
            if nome in unidades:
                nome = f"{nome} ({co_str})"

        est_uni = sorted(sub["SG_UF_ESC"].dropna().unique().tolist())
        unidades[nome] = _bloco_df(sub, est_uni, 1)

    return {"geral": geral, "unidades": unidades}


# ── Lookup de dados auxiliares ────────────────────────────────────────────────

def _load_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def bench_para_unidades(unidades_nomes: list, mapa: dict, bench_mun: dict) -> tuple[dict, dict, str]:
    """
    Retorna (BENCH_UNIDADE, BENCH_GERAL, BENCH_LABEL).
    BENCH_UNIDADE: dict {unidade: bench_mun_entry}
    """
    # Descobrir municípios dos codigos de unidades
    # Usa mapa_escola_bairro para mapear unidade→municipio
    nome_para_mun: dict[str, str] = {}
    for co_str, info in mapa.items():
        full_label = info.get("label", "")
        partes = full_label.split(" — ", 1)
        nome = partes[-1]
        mun  = info.get("municipio", "")
        uf   = info.get("uf", "")
        chave = f"{mun} ({uf})"
        if nome in unidades_nomes:
            nome_para_mun[nome] = chave

    # Montar BENCH_UNIDADE
    bu = {}
    todos_muns = set()
    for nome in unidades_nomes:
        chave = nome_para_mun.get(nome)
        if chave and chave in bench_mun:
            bu[nome] = bench_mun[chave]
            todos_muns.add(chave)

    # BENCH_GERAL = benchmark do município mais frequente (ou primeiros)
    bg = {}
    label = "Rede Privada — Município"
    if todos_muns:
        chave_prim = next(iter(todos_muns))
        if chave_prim in bench_mun:
            bg = bench_mun[chave_prim]
            label = f"{bg.get('municipio',chave_prim)} — Rede Privada"

    return bu, bg, label


# ── Geração do HTML ───────────────────────────────────────────────────────────

def _ler_template() -> list[str]:
    if not os.path.exists(TEMPLATE_HTML):
        raise FileNotFoundError(f"Template não encontrado: {TEMPLATE_HTML}")
    with open(TEMPLATE_HTML, encoding="utf-8") as f:
        return f.readlines()


def _substituir_linha(line: str, prefix: str, novo_valor: str) -> str:
    """Substitui linha que começa com 'const X = ...' pelo novo valor."""
    stripped = line.lstrip()
    if stripped.startswith(prefix):
        indent = line[:len(line) - len(stripped)]
        return f"{indent}{novo_valor}\n"
    return line


def gerar_html(
    marca: str,
    dados: dict,
    bench_unidade: dict,
    bench_geral: dict,
    bench_label: str,
    bench_bairro: dict,
    ranking: dict,
    toptiers: dict,
    bairro_ausentes: dict = None,
) -> str:
    linhas = _ler_template()

    n_uni = len(dados["unidades"])
    estados = dados["geral"].get("estados", [])
    uf_str  = " | ".join(estados) if estados else ""

    saida = []
    for line in linhas:
        stripped = line.lstrip()

        # Substituições de constantes JS (uma constante por linha no template)
        if stripped.startswith("const DADOS = "):
            line = _substituir_linha(line, "const DADOS = ",
                f"const DADOS = {json.dumps(dados, ensure_ascii=False)};")

        elif stripped.startswith("const BENCH_UNIDADE = "):
            line = _substituir_linha(line, "const BENCH_UNIDADE = ",
                f"const BENCH_UNIDADE = {json.dumps(bench_unidade, ensure_ascii=False)};")

        elif stripped.startswith("const BENCH_GERAL = "):
            line = _substituir_linha(line, "const BENCH_GERAL = ",
                f"const BENCH_GERAL = {json.dumps(bench_geral, ensure_ascii=False)};")

        elif stripped.startswith("const BENCH_LABEL = "):
            line = _substituir_linha(line, "const BENCH_LABEL = ",
                f"const BENCH_LABEL = {json.dumps(bench_label, ensure_ascii=False)};")

        elif stripped.startswith("const BENCH_BAIRRO = "):
            line = _substituir_linha(line, "const BENCH_BAIRRO = ",
                f"const BENCH_BAIRRO = {json.dumps(bench_bairro, ensure_ascii=False)};")

        elif stripped.startswith("const BAIRRO_AUSENTES = "):
            line = _substituir_linha(line, "const BAIRRO_AUSENTES = ",
                f"const BAIRRO_AUSENTES = {json.dumps(bairro_ausentes or {}, ensure_ascii=False)};")

        elif stripped.startswith("const RANKING_POSICOES = "):
            line = _substituir_linha(line, "const RANKING_POSICOES = ",
                f"const RANKING_POSICOES = {json.dumps(ranking, ensure_ascii=False)};")

        elif stripped.startswith("const TOPTIERS = "):
            line = _substituir_linha(line, "const TOPTIERS = ",
                f"const TOPTIERS = {json.dumps(toptiers, ensure_ascii=False)};")

        saida.append(line)

    html = "".join(saida)

    # Substituições de texto estático (brand name, title, etc.)
    marca_segura = marca  # nome completo da marca
    html = html.replace("<title>Apogeu — ENEM 2025</title>",
                        f"<title>{marca_segura} — ENEM 2025</title>")

    # Subtitle linha da header
    html = html.replace(
        'Análise de Performance - Enem 2025',
        f'Análise de Performance - Enem 2025'  # mantém igual
    )

    # Ocorrências hardcoded de "Apogeu" em strings JS e HTML
    html = html.replace("Geral Apogeu", f"Geral {marca_segura}")
    html = html.replace("média geral Apogeu", f"média geral {marca_segura}")
    html = html.replace("Média Geral Apogeu:", f"Média Geral {marca_segura}:")
    html = html.replace("${'Apogeu'} Geral", f"${{'{_js_esc(marca_segura)}' }} Geral")
    html = html.replace("${'Apogeu' } Geral", f"${{'{_js_esc(marca_segura)}' }} Geral")
    # Subtítulo do card "Concorrentes por Município": "★ = unidade Apogeu"
    html = html.replace("unidade Apogeu", f"unidade {marca_segura}")

    # Logo do header — injeta a logo base64 embutida da marca (asset em logos/{safe}.imgtag).
    # Fallback: <span> com o nome da marca, caso o asset não exista.
    _safe = marca.replace(" ", "_").replace("é", "e").replace("ô", "o")
    _logo_path = os.path.join(ANALISE_DIR, "logos", f"{_safe}.imgtag")
    if os.path.exists(_logo_path):
        with open(_logo_path, encoding="utf-8") as _lf:
            logo_html = _lf.read().strip()
    else:
        logo_html = (
            f'<span style="color:#ffffff;font-size:1.6rem;font-weight:700;'
            f'letter-spacing:0.01em;white-space:nowrap;">{marca_segura}</span>'
        )
    # Substitui o placeholder <span>Apogeu</span> do template pela logo.
    html = re.sub(
        r'<span style="color:#ffffff;font-size:1\.6rem;font-weight:700;'
        r'letter-spacing:0\.01em;white-space:nowrap;">Apogeu</span>',
        lambda _m: logo_html, html, count=1)
    # Fallback adicional: caso o template ainda traga uma logo em <img> antiga.
    html = re.sub(r'<img\s+src="data:image[^"]*"[^>]*>', lambda _m: logo_html, html, count=1)

    # KPI placeholder estático "3 unidades" (será sobrescrito pelo JS, mas bom garantir)
    html = html.replace(
        '<div class="kpi-sub">3 unidades</div>',
        f'<div class="kpi-sub">{n_uni} unidade{"s" if n_uni != 1 else ""}</div>'
    )

    # KPI valor inicial de inscritos (placeholder visual)
    n_ins_str = str(dados["geral"]["n_inscritos"])
    html = html.replace(
        'id="kInscritos">290</div>',
        f'id="kInscritos">{n_ins_str}</div>'
    )

    # Reaplica a paleta da marca (template é o Apogeu repaginado)
    html = _aplicar_cores(html, marca)

    return html


def _js_esc(s: str) -> str:
    """Escapa aspas simples para uso em string JS."""
    return s.replace("'", "\\'")


# Cores por marca (primária, destaque). O template é o Apogeu repaginado;
# aqui trocamos as cores-base do Apogeu pelas da marca-alvo.
BRAND_COLORS = {
    "Apogeu":                    ("#1a3a6e", "#2563eb"),
    "QI Bilíngue":               ("#4c1d95", "#7c3aed"),
    "Matriz Educação":           ("#0a4d2b", "#15803d"),
    "Colégio Leonardo da Vinci": ("#b44408", "#c2560a"),
    "Cubo Global":               ("#097570", "#0f9d96"),
}

_APOGEU_PRIMARY = "#1a3a6e"
_APOGEU_DARK    = "#1e326e"
_APOGEU_ACCENT  = "#2563eb"


def _aplicar_cores(html: str, marca: str) -> str:
    """Reaplica a paleta da marca (mesma lógica da repaginação por marca).
    Protege a paleta categórica de unidades (inicia em ["#2563eb")."""
    primary, accent = BRAND_COLORS.get(marca, (_APOGEU_PRIMARY, _APOGEU_ACCENT))
    if (primary, accent) == (_APOGEU_PRIMARY, _APOGEU_ACCENT):
        return html  # Apogeu = base, nada a trocar
    html = html.replace('["' + _APOGEU_ACCENT + '"', '["@@U0@@"')
    html = html.replace(_APOGEU_PRIMARY, primary)
    html = html.replace(_APOGEU_DARK,    primary)
    html = html.replace(_APOGEU_ACCENT,  accent)
    html = html.replace('["@@U0@@"', '["' + _APOGEU_ACCENT + '"')
    return html


# ── Pipeline principal ────────────────────────────────────────────────────────

def processar_marca(marca: str):
    csv_path = os.path.join(OUTPUT_DIR, f"{marca.replace(' ', '_')}_resultados.csv")
    if not os.path.exists(csv_path):
        print(f"  [{marca}] CSV não encontrado: {csv_path}")
        print(f"  [{marca}] Execute 01_extrair.py primeiro.")
        return

    print(f"\n  [{marca}] Lendo {csv_path}...")
    df = pd.read_csv(csv_path, dtype={"CO_ESCOLA": "Int64"})
    print(f"  [{marca}] {len(df):,} inscritos, {df['CO_ESCOLA'].nunique()} unidade(s).")

    # Carrega auxiliares
    mapa      = _load_json(MAPA_JSON)
    bench_mun = _load_json(BENCH_MUN_JSON)
    bench_bairro_all = _load_json(BENCH_BAIRRO_JSON)
    ranking_all      = _load_json(RANKING_JSON)
    toptiers         = _load_json(TOPTIERS_JSON)

    # Calcula DADOS
    print(f"  [{marca}] Calculando estatísticas...")
    codigos = ESCOLAS.get(marca, [])
    dados = computar_dados(df, mapa, codigos)

    unidades_nomes = list(dados["unidades"].keys())
    print(f"  [{marca}] Unidades: {unidades_nomes}")

    # Benchmarks municipais
    bench_unidade, bench_geral, bench_label = bench_para_unidades(
        unidades_nomes, mapa, bench_mun
    )

    # Bairro e ranking — só para esta marca
    bench_bairro = bench_bairro_all.get(marca, {})
    ranking      = ranking_all.get(marca, {})
    bairro_ausentes = _load_json(AUSENTES_JSON).get(marca, {})

    # Gera HTML
    print(f"  [{marca}] Gerando HTML...")
    html = gerar_html(
        marca, dados,
        bench_unidade, bench_geral, bench_label,
        bench_bairro, ranking, toptiers,
        bairro_ausentes,
    )

    # Salva
    safe_nome = marca.replace(" ", "_").replace("é", "e").replace("ô", "o")
    destino = os.path.join(OUTPUT_DIR, f"{safe_nome}_Dashboard.html")
    with open(destino, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  [{marca}] Salvo: {destino}")

    # Também salva dados JSON para referência futura
    json_dest = os.path.join(OUTPUT_DIR, f"dados_{safe_nome}.json")
    with open(json_dest, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print(f"  [{marca}] JSON: {json_dest}")


def _aplicar_historico(alvos):
    """Pos-processamento: insere a secao Evolucao Historica via 08_historico_secao.py."""
    script = os.path.join(ANALISE_DIR, "08_historico_secao.py")
    if not os.path.exists(script):
        return
    print(f"\n{'='*60}")
    print("  PASSO POS: Seção Evolução Histórica (08)")
    print(f"{'='*60}")
    try:
        import subprocess
        subprocess.run([sys.executable, script] + [m for m in alvos if m in ESCOLAS], cwd=ANALISE_DIR)
    except Exception as e:
        print(f"  Seção histórica não aplicada: {e}")


def main():
    alvos = sys.argv[1:] if len(sys.argv) > 1 else list(ESCOLAS.keys())

    print(f"\n{'='*60}")
    print(f"  Gerando dashboards para: {', '.join(alvos)}")
    print(f"{'='*60}")

    for marca in alvos:
        if marca not in ESCOLAS:
            print(f"  AVISO: '{marca}' não encontrado em config.py — ignorando.")
            continue
        processar_marca(marca)

    _aplicar_historico(alvos)

    print(f"\n{'='*60}")
    print("  Concluído.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
