"""
calcular_benchmark_municipio.py
Calcula benchmark da rede privada para municípios ainda não cobertos
em output/benchmark_municipal.json.

Uso:
    python calcular_benchmark_municipio.py "Porto Alegre" RS 4314902
"""
import os, sys, json
import pandas as pd
import numpy as np

ANALISE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ANALISE_DIR)
from config import RESULTADOS_CSV, CSV_SEP, CSV_ENCODING, CHUNK_SIZE, OUTPUT_DIR

AREAS  = ["CN", "CH", "LC", "MT"]
COLUNAS = (
    ["CO_MUNICIPIO_ESC", "NO_MUNICIPIO_ESC", "SG_UF_ESC",
     "TP_DEPENDENCIA_ADM_ESC", "CO_ESCOLA"] +
    [f"TP_PRESENCA_{a}" for a in AREAS] +
    [f"NU_NOTA_{a}" for a in AREAS] +
    ["TP_STATUS_REDACAO", "NU_NOTA_REDACAO"]
)

BENCH_MUN_PATH = os.path.join(OUTPUT_DIR, "benchmark_municipal.json")
CORTES = [500, 600, 700, 800]


def calcular(municipio: str, uf: str, co_municipio: int):
    print(f"Varrendo {RESULTADOS_CSV} para {municipio} ({uf})...")
    acum: dict = {}   # co_escola → lista de stats
    total = 0
    encontrado = 0

    for chunk in pd.read_csv(
        RESULTADOS_CSV, sep=CSV_SEP, encoding=CSV_ENCODING,
        usecols=COLUNAS, chunksize=CHUNK_SIZE,
        dtype={"CO_ESCOLA": "Int64", "CO_MUNICIPIO_ESC": "Int64"},
    ):
        total += len(chunk)
        sub = chunk[
            (chunk["CO_MUNICIPIO_ESC"] == co_municipio) &
            (chunk["TP_DEPENDENCIA_ADM_ESC"] == 4)     # privada
        ]
        if not sub.empty:
            encontrado += len(sub)
            for co_esc, grp in sub.groupby("CO_ESCOLA"):
                if co_esc not in acum:
                    acum[co_esc] = []
                acum[co_esc].append(grp)
        print(f"  {total:,} lidos, {encontrado} privados em {municipio}...", end="\r")

    print(f"\n  Total: {total:,} | Privados {municipio}: {encontrado}")

    if not acum:
        print(f"  AVISO: nenhuma escola privada encontrada para CO_MUNICIPIO={co_municipio}")
        return

    # Junta todos os dados de todas as escolas
    dfs = [pd.concat(partes) for partes in acum.values()]
    df  = pd.concat(dfs)

    n_escolas = len(acum)
    n_alunos  = len(df)

    areas_stats = {}
    for a in AREAS:
        pres = df[df[f"TP_PRESENCA_{a}"] == 1][f"NU_NOTA_{a}"].dropna()
        if pres.empty:
            areas_stats[a] = {}
            continue
        areas_stats[a] = {
            "n":       int(len(pres)),
            "media":   round(float(pres.mean()), 1),
            "mediana": round(float(pres.median()), 1),
            "dp":      round(float(pres.std()), 1),
            "p25":     round(float(pres.quantile(0.25)), 1),
            "p75":     round(float(pres.quantile(0.75)), 1),
            "pct_500": round(float((pres >= 500).mean() * 100), 1),
            "pct_600": round(float((pres >= 600).mean() * 100), 1),
            "pct_700": round(float((pres >= 700).mean() * 100), 1),
            "pct_800": round(float((pres >= 800).mean() * 100), 1),
        }

    red_val = df[df["TP_STATUS_REDACAO"] == 1]["NU_NOTA_REDACAO"].dropna()
    red_stats = {}
    if not red_val.empty:
        red_stats = {
            "n":       int(len(red_val)),
            "media":   round(float(red_val.mean()), 1),
            "pct_600": round(float((red_val >= 600).mean() * 100), 1),
            "pct_700": round(float((red_val >= 700).mean() * 100), 1),
            "pct_800": round(float((red_val >= 800).mean() * 100), 1),
        }

    entry = {
        "municipio": municipio,
        "uf": uf,
        "n_escolas": n_escolas,
        "n_alunos":  n_alunos,
        "areas":   areas_stats,
        "redacao": red_stats,
    }

    # Lê JSON existente e adiciona
    bench = {}
    if os.path.exists(BENCH_MUN_PATH):
        with open(BENCH_MUN_PATH, encoding="utf-8") as f:
            bench = json.load(f)

    chave = f"{municipio} ({uf})"
    bench[chave] = entry
    with open(BENCH_MUN_PATH, "w", encoding="utf-8") as f:
        json.dump(bench, f, ensure_ascii=False, indent=2)

    print(f"\nAdicionado '{chave}' ao benchmark_municipal.json")
    print(f"  {n_escolas} escolas privadas | {n_alunos} alunos")
    for a, s in areas_stats.items():
        print(f"  {a}: média={s.get('media','?')} | %≥600={s.get('pct_600','?')}%")
    print(f"  Redação: média={red_stats.get('media','?')}")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: python calcular_benchmark_municipio.py 'Porto Alegre' RS 4314902")
        sys.exit(1)
    municipio_arg  = sys.argv[1]
    uf_arg         = sys.argv[2]
    co_municipio   = int(sys.argv[3])
    calcular(municipio_arg, uf_arg, co_municipio)
