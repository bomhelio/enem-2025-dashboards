"""
06_concorrentes_ranking.py
Para marcas especificadas, gera/atualiza:
  benchmark_bairro.json       — pool de escolas por bairro (fonte: Censo + ENEM)
  ranking_posicoes.json       — ranking BR/UF/município por área (por marca > unidade)
  bench_bairro_por_marca.json — BENCH_BAIRRO pronto para HTML (por marca > unidade)

Fontes:
  DADOS/Tabela_Escola_2025.csv — Censo Escolar 2025
  DADOS/RESULTADOS_2025.csv    — Microdados ENEM 2025

Uso:
  python 06_concorrentes_ranking.py "Colégio Leonardo da Vinci" "Cubo Global"
  python 06_concorrentes_ranking.py   # todas as marcas em config.py
"""
import os, sys, json
import pandas as pd

ANALISE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ANALISE_DIR)
from config import ESCOLAS, OUTPUT_DIR, RESULTADOS_CSV, CSV_SEP, CSV_ENCODING, CHUNK_SIZE

BASE_DIR = os.path.dirname(ANALISE_DIR)
TABELA_CSV        = os.path.join(BASE_DIR, "DADOS", "Tabela_Escola_2025.csv")
BENCH_BAIRRO_JSON = os.path.join(OUTPUT_DIR, "benchmark_bairro.json")
RANKING_JSON      = os.path.join(OUTPUT_DIR, "ranking_posicoes.json")
BENCH_MARCA_JSON  = os.path.join(OUTPUT_DIR, "bench_bairro_por_marca.json")
MAPA_JSON         = os.path.join(OUTPUT_DIR, "mapa_escola_bairro.json")
# Concorrentes curados de bairros adjacentes (fora do filtro de bairro exato).
EXTRA_CONC_JSON   = os.path.join(ANALISE_DIR, "concorrentes_extra.json")
AUSENTES_JSON     = os.path.join(OUTPUT_DIR, "bairro_ausentes_por_marca.json")

AREAS = ["CN", "CH", "LC", "MT"]
MIN_N = 5  # mínimo de alunos para média válida


# ── Utilitários ───────────────────────────────────────────────────────────────

def _load_json(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _bairro_key(bairro, municipio, uf):
    return f"{bairro}|{municipio}|{uf}"


# ── Cadastro Escolar ──────────────────────────────────────────────────────────

def load_catalog():
    """Lê Tabela_Escola_2025.csv → dict {co_escola(int): info}"""
    print("Lendo Tabela_Escola_2025.csv...")
    df = pd.read_csv(
        TABELA_CSV, sep=";", encoding="latin-1",
        usecols=["CO_ENTIDADE", "NO_ENTIDADE", "NO_BAIRRO", "CO_CEP",
                 "NO_MUNICIPIO", "CO_MUNICIPIO", "SG_UF", "TP_DEPENDENCIA"],
        dtype={"CO_ENTIDADE": "Int64", "CO_CEP": str, "CO_MUNICIPIO": "Int64"},
    )
    out = {}
    for _, row in df.iterrows():
        if pd.isna(row["CO_ENTIDADE"]):
            continue
        co = int(row["CO_ENTIDADE"])
        out[co] = {
            "nome":        str(row["NO_ENTIDADE"]).strip() if pd.notna(row["NO_ENTIDADE"]) else "",
            "bairro":      str(row["NO_BAIRRO"]).strip()   if pd.notna(row["NO_BAIRRO"])   else "",
            "cep":         str(row["CO_CEP"]).strip().zfill(8) if pd.notna(row["CO_CEP"])  else "",
            "municipio":   str(row["NO_MUNICIPIO"])         if pd.notna(row["NO_MUNICIPIO"]) else "",
            "co_municipio": int(row["CO_MUNICIPIO"])        if pd.notna(row["CO_MUNICIPIO"]) else 0,
            "uf":           str(row["SG_UF"])               if pd.notna(row["SG_UF"])       else "",
            "dep":          int(row["TP_DEPENDENCIA"])      if pd.notna(row["TP_DEPENDENCIA"]) else 0,
        }
    print(f"  {len(out):,} escolas no cadastro.")
    return out


# ── Varredura de RESULTADOS ───────────────────────────────────────────────────

def scan_resultados() -> dict:
    """
    Única passagem por RESULTADOS_2025.csv.
    Acumula somas e contagens por CO_ESCOLA (rede privada apenas).
    Retorna: {co(int): {uf, co_municipio, n_total, CN_s, CN_n, ..., RED_s, RED_n}}
    """
    print(f"Varrendo {RESULTADOS_CSV}...")
    COLS = (
        ["CO_ESCOLA", "SG_UF_ESC", "CO_MUNICIPIO_ESC", "TP_DEPENDENCIA_ADM_ESC"] +
        [f"TP_PRESENCA_{a}" for a in AREAS] +
        [f"NU_NOTA_{a}"     for a in AREAS] +
        ["TP_STATUS_REDACAO", "NU_NOTA_REDACAO"]
    )
    acum: dict = {}
    total = 0
    for chunk in pd.read_csv(
        RESULTADOS_CSV, sep=CSV_SEP, encoding=CSV_ENCODING,
        usecols=COLS, chunksize=CHUNK_SIZE,
        dtype={"CO_ESCOLA": "Int64", "CO_MUNICIPIO_ESC": "Int64"},
    ):
        priv = chunk[chunk["TP_DEPENDENCIA_ADM_ESC"] == 4]
        total += len(chunk)
        for co_esc, grp in priv.groupby("CO_ESCOLA", sort=False):
            if pd.isna(co_esc):
                continue
            co = int(co_esc)
            if co not in acum:
                uf  = grp["SG_UF_ESC"].dropna().mode()
                mun = grp["CO_MUNICIPIO_ESC"].dropna().mode()
                acum[co] = {
                    "uf": str(uf.iloc[0]) if len(uf) else "",
                    "co_municipio": int(mun.iloc[0]) if len(mun) else 0,
                    "n_total": 0, "RED_s": 0.0, "RED_n": 0,
                    **{f"{a}_s": 0.0 for a in AREAS},
                    **{f"{a}_n": 0   for a in AREAS},
                }
            acum[co]["n_total"] += len(grp)
            for a in AREAS:
                p = grp[grp[f"TP_PRESENCA_{a}"] == 1][f"NU_NOTA_{a}"].dropna()
                acum[co][f"{a}_s"] += float(p.sum())
                acum[co][f"{a}_n"] += len(p)
            red = grp[grp["TP_STATUS_REDACAO"] == 1]["NU_NOTA_REDACAO"].dropna()
            acum[co]["RED_s"] += float(red.sum())
            acum[co]["RED_n"] += len(red)
        print(f"  {total:,} lidos...", end="\r")
    print(f"\n  {len(acum):,} escolas privadas encontradas.")
    return acum


def compute_means(acum: dict) -> dict:
    """Somas/contagens → médias. media=None se n < MIN_N."""
    out = {}
    for co, d in acum.items():
        e = {"uf": d["uf"], "co_municipio": d["co_municipio"], "n_total": d["n_total"]}
        for a in AREAS:
            n = d[f"{a}_n"]
            e[a]        = round(d[f"{a}_s"] / n, 1) if n >= MIN_N else None
            e[f"{a}_n"] = n
        n_red = d["RED_n"]
        e["REDACAO"] = round(d["RED_s"] / n_red, 1) if n_red >= MIN_N else None
        e["RED_n"]   = n_red
        vals = [e[a] for a in AREAS + ["REDACAO"] if e[a] is not None]
        e["nota_geral"] = round(sum(vals) / len(vals), 1) if vals else None
        out[co] = e
    return out


# ── Benchmark por Bairro ──────────────────────────────────────────────────────

def build_bairro_entry(bairro, municipio, uf, cos_bairro, means, catalog) -> dict:
    """Entrada de benchmark_bairro para um bairro (pool de escolas com dados ENEM)."""
    escolas = []
    for co in cos_bairro:
        if co not in means:
            continue
        m   = means[co]
        cat = catalog.get(co, {})
        entry = {
            "co_escola": co,
            "nome":      cat.get("nome", str(co)),
            "bairro":    cat.get("bairro", bairro),
            "cep":       cat.get("cep", ""),
            "municipio": municipio,
            "uf":        uf,
            "n":         m["n_total"],
        }
        for a in AREAS:
            entry[a] = m[a]
        entry["redacao"]    = m["REDACAO"]
        entry["nota_geral"] = m["nota_geral"]
        escolas.append(entry)

    if not escolas:
        return {}

    n_alunos = sum(e["n"] for e in escolas)
    areas_agg = {}
    for a in AREAS:
        vals = [e[a] for e in escolas if e[a] is not None]
        areas_agg[a] = {"media": round(sum(vals) / len(vals), 1), "n": len(vals)} if vals else {}
    red_vals = [e["redacao"] for e in escolas if e["redacao"] is not None]
    red_agg  = {"media": round(sum(red_vals) / len(red_vals), 1), "n": len(red_vals)} if red_vals else {}

    return {
        "bairro": bairro, "municipio": municipio, "uf": uf,
        "n_escolas": len(escolas), "n_alunos": n_alunos,
        "areas": areas_agg, "redacao": red_agg,
        "escolas": escolas,
    }


def _extra_entry(xco, adj_label, unit_bairro, catalog, means) -> dict:
    """Monta a linha de um concorrente curado (bairro adjacente)."""
    m   = means[xco]
    cat = catalog.get(xco, {})
    entry = {
        "co_escola": xco,
        "nome":      cat.get("nome", str(xco)),
        "bairro":    cat.get("bairro", ""),
        "cep":       cat.get("cep", ""),
        "municipio": cat.get("municipio", ""),
        "uf":        cat.get("uf", ""),
        "n":         m["n_total"],
    }
    for a in AREAS:
        entry[a] = m[a]
    entry["redacao"]    = m["REDACAO"]
    entry["nota_geral"] = m["nota_geral"]
    if adj_label:
        entry["adj"] = adj_label   # rótulo de bairro exibido ao lado do nome
    return entry


def build_bench_bairro_unidade(co_esc, unit_name, catalog, bench_bairro, means,
                               extra_list=None) -> dict:
    """BENCH_BAIRRO pronto para JS, para uma unidade específica."""
    if co_esc not in catalog or co_esc not in means:
        return {}
    cat = catalog[co_esc]
    key = _bairro_key(cat["bairro"], cat["municipio"], cat["uf"])
    if key not in bench_bairro:
        return {}

    pool = list(bench_bairro[key].get("escolas", []))

    # Injeta concorrentes curados de bairros adjacentes (planilha comercial).
    have = {e["co_escola"] for e in pool}
    for x in (extra_list or []):
        xco = x["co"]
        if xco in have:
            continue
        if xco not in means or means[xco]["nota_geral"] is None:
            print(f"      AVISO: extra {xco} sem dados ENEM válidos — ignorado.")
            continue
        pool.append(_extra_entry(xco, x.get("adj"), cat["bairro"], catalog, means))
        have.add(xco)

    escolas_raw = sorted(
        pool,
        key=lambda x: x.get("nota_geral") or 0, reverse=True
    )
    nossa_pos = None
    escolas_out = []
    for i, e in enumerate(escolas_raw):
        is_nossa = (e["co_escola"] == co_esc)
        if is_nossa:
            nossa_pos = i + 1
        escolas_out.append({**e, "pos": i + 1, "nossa": is_nossa})

    outras = [e for e in escolas_raw if e["co_escola"] != co_esc]
    bench_areas = {}
    for a in AREAS:
        vals = [e[a] for e in outras if e.get(a) is not None]
        if vals:
            bench_areas[a] = round(sum(vals) / len(vals), 1)
    red_vals    = [e["redacao"] for e in outras if e.get("redacao") is not None]
    bench_red   = round(sum(red_vals) / len(red_vals), 1) if red_vals else None

    return {
        "bairro":       cat["bairro"],
        "municipio":    cat["municipio"],
        "uf":           cat["uf"],
        "n_escolas":    len(escolas_out),
        "nossa_pos":    nossa_pos,
        "bench_areas":  bench_areas,
        "bench_redacao": bench_red,
        "escolas":      escolas_out,
    }


# ── Ranking ───────────────────────────────────────────────────────────────────

def compute_ranking_unidade(co_esc, catalog, means) -> dict:
    """Ranking BR/UF/município para cada área de uma unidade."""
    if co_esc not in means:
        return {}
    m   = means[co_esc]
    cat = catalog.get(co_esc, {})
    uf      = m["uf"]        or cat.get("uf", "")
    co_mun  = m["co_municipio"] or cat.get("co_municipio", 0)
    municipio = cat.get("municipio", "")

    result = {"uf": uf, "municipio": municipio, "areas": {}}

    for area in AREAS + ["REDACAO"]:
        v = m[area]
        if v is None:
            continue
        n_key = "RED_n" if area == "REDACAO" else f"{area}_n"
        n = m.get(n_key, 0)

        br  = [(co, d[area]) for co, d in means.items() if d[area] is not None]
        uf_ = [(co, v2) for co, v2 in br if means[co]["uf"] == uf]
        mn_ = [(co, v2) for co, v2 in br if means[co]["co_municipio"] == co_mun]

        def rank_of(lst, target):
            s = sorted(lst, key=lambda x: x[1], reverse=True)
            pos = next((i + 1 for i, (c, _) in enumerate(s) if c == target), None)
            return pos, len(s)

        rbr, tbr = rank_of(br,  co_esc)
        ruf, tuf = rank_of(uf_, co_esc)
        rmn, tmn = rank_of(mn_, co_esc)

        result["areas"][area] = {
            "media": v, "n": n,
            "rank_br": rbr, "total_br": tbr,
            "rank_uf": ruf, "total_uf": tuf,
            "rank_mun": rmn, "total_mun": tmn,
        }
    return result


# ── Pipeline principal ────────────────────────────────────────────────────────

def _unit_name_from_mapa(co, mapa):
    co_str = str(co)
    if co_str in mapa:
        full = mapa[co_str].get("label", co_str)
        return full.split(" — ", 1)[-1]
    return co_str


def processar_marcas(alvos: list):
    catalog = load_catalog()
    mapa    = _load_json(MAPA_JSON)
    extra_cfg = _load_json(EXTRA_CONC_JSON)
    extras_all   = extra_cfg.get("extras", {})
    ausentes_all = extra_cfg.get("ausentes", {})

    # Descobrir bairros de todas as unidades-alvo
    print("\nMapeando bairros...")
    bairros_alvos: dict = {}   # key → (bairro, municipio, uf, [cos])
    for marca in alvos:
        for co in ESCOLAS.get(marca, []):
            if co not in catalog:
                print(f"  AVISO: {co} não encontrado no Cadastro — ignorado.")
                continue
            cat = catalog[co]
            key = _bairro_key(cat["bairro"], cat["municipio"], cat["uf"])
            if key not in bairros_alvos:
                cos_bairro = [
                    c for c, info in catalog.items()
                    if info["dep"] == 4
                    and info["bairro"] == cat["bairro"]
                    and info["co_municipio"] == cat["co_municipio"]
                ]
                bairros_alvos[key] = (cat["bairro"], cat["municipio"], cat["uf"], cos_bairro)
                print(f"  '{key}': {len(cos_bairro)} escolas privadas no Cadastro.")

    # Varredura única do RESULTADOS
    acum  = scan_resultados()
    means = compute_means(acum)

    # benchmark_bairro.json
    bench_bairro = _load_json(BENCH_BAIRRO_JSON)
    for key, (bairro, municipio, uf, cos_bairro) in bairros_alvos.items():
        entry = build_bairro_entry(bairro, municipio, uf, cos_bairro, means, catalog)
        if entry:
            bench_bairro[key] = entry
            print(f"  benchmark_bairro '{key}': {entry['n_escolas']} escolas com dados.")
        else:
            print(f"  benchmark_bairro '{key}': nenhuma escola com dados ENEM — pulado.")
    _save_json(BENCH_BAIRRO_JSON, bench_bairro)
    print("  Salvo: benchmark_bairro.json")

    # bench_bairro_por_marca.json + ranking_posicoes.json
    bench_marca = _load_json(BENCH_MARCA_JSON)
    ranking_pos = _load_json(RANKING_JSON)

    for marca in alvos:
        print(f"\n  [{marca}]")
        bench_marca[marca] = {}
        ranking_pos[marca] = {}
        extras_marca   = extras_all.get(marca, {})
        ausentes_marca = ausentes_all.get(marca, {})

        for co in ESCOLAS.get(marca, []):
            if co not in catalog:
                continue
            unit = _unit_name_from_mapa(co, mapa)

            bb = build_bench_bairro_unidade(
                co, unit, catalog, bench_bairro, means,
                extra_list=extras_marca.get(unit),
            )
            if bb:
                bench_marca[marca][unit] = bb
                n_extra = len(extras_marca.get(unit, []))
                extra_txt = f" (+{n_extra} adj.)" if n_extra else ""
                print(f"    {unit}: {bb['bairro']} — pos {bb['nossa_pos']}/{bb['n_escolas']}{extra_txt}")
            else:
                print(f"    {unit}: sem dados de bairro.")

            rk = compute_ranking_unidade(co, catalog, means)
            if rk:
                ranking_pos[marca][unit] = rk
                for area, d in rk["areas"].items():
                    print(f"    {unit} {area}: {d['rank_br']}°/{d['total_br']} BR | "
                          f"{d['rank_uf']}°/{d['total_uf']} {rk['uf']} | "
                          f"{d['rank_mun']}°/{d['total_mun']} {rk['municipio']}")

    _save_json(BENCH_MARCA_JSON, bench_marca)
    _save_json(RANKING_JSON, ranking_pos)
    # Concorrentes da planilha sem dados ENEM 2025 (rodapé por unidade no HTML).
    _save_json(AUSENTES_JSON, ausentes_all)
    print("\n  Salvo: bench_bairro_por_marca.json")
    print("  Salvo: ranking_posicoes.json")
    print("  Salvo: bairro_ausentes_por_marca.json")


def main():
    alvos = sys.argv[1:] if len(sys.argv) > 1 else list(ESCOLAS.keys())
    print(f"\n{'='*60}")
    print(f"  Processando: {', '.join(alvos)}")
    print(f"{'='*60}")
    processar_marcas(alvos)
    print(f"\n{'='*60}")
    print("  Concluído.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
