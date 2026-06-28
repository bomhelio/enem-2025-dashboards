"""
03_benchmark.py
Calcula médias nacionais e por UF a partir do RESULTADOS_2025.csv completo (2 GB).
Lê em chunks para não estourar memória.
Salva output/benchmarks.csv com médias por UF + nacional.
"""

import os
import pandas as pd
import numpy as np
from config import RESULTADOS_CSV, OUTPUT_DIR, CSV_SEP, CSV_ENCODING, CHUNK_SIZE, ESCOLAS

AREAS = ["CN", "CH", "LC", "MT"]
COLUNAS = (
    ["SG_UF_ESC", "TP_DEPENDENCIA_ADM_ESC"] +
    [f"TP_PRESENCA_{a}" for a in AREAS] +
    [f"NU_NOTA_{a}" for a in AREAS] +
    ["TP_STATUS_REDACAO", "NU_NOTA_REDACAO"]
)


def _soma_contagem_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    """Para cada UF, retorna soma das notas e contagens de presentes."""
    rows = []
    for uf, grp in chunk.groupby("SG_UF_ESC", sort=False):
        row: dict = {"SG_UF_ESC": uf}
        for a in AREAS:
            presentes = grp[grp[f"TP_PRESENCA_{a}"] == 1][f"NU_NOTA_{a}"].dropna()
            row[f"soma_{a}"] = presentes.sum()
            row[f"n_{a}"]    = len(presentes)
        red_valida = grp[grp["TP_STATUS_REDACAO"] == 1]["NU_NOTA_REDACAO"].dropna()
        row["soma_RED"] = red_valida.sum()
        row["n_RED"]    = len(red_valida)
        rows.append(row)
    return pd.DataFrame(rows)


def calcular_benchmarks(privadas_apenas: bool = False) -> pd.DataFrame:
    """
    privadas_apenas=True → filtra TP_DEPENDENCIA_ADM_ESC == 4
    para comparação mais justa com escolas privadas.
    """
    print(f"Varrendo {RESULTADOS_CSV} para benchmarks...")
    acumulado: pd.DataFrame | None = None
    total = 0

    for chunk in pd.read_csv(
        RESULTADOS_CSV,
        sep=CSV_SEP,
        encoding=CSV_ENCODING,
        usecols=COLUNAS,
        chunksize=CHUNK_SIZE,
    ):
        if privadas_apenas:
            chunk = chunk[chunk["TP_DEPENDENCIA_ADM_ESC"] == 4]

        total += len(chunk)
        parcial = _soma_contagem_chunk(chunk)
        acumulado = parcial if acumulado is None else (
            pd.concat([acumulado, parcial])
            .groupby("SG_UF_ESC", sort=False)
            .sum()
            .reset_index()
        )
        print(f"  {total:,} registros processados...", end="\r")

    print(f"\n  Total: {total:,} registros.")

    # Calcula médias por UF
    for a in AREAS + ["RED"]:
        acumulado[f"media_{a}"] = (acumulado[f"soma_{a}"] / acumulado[f"n_{a}"]).round(1)

    # Linha nacional
    nacional = acumulado.sum(numeric_only=True)
    linha_nacional = {"SG_UF_ESC": "BRASIL"}
    for a in AREAS + ["RED"]:
        linha_nacional[f"soma_{a}"] = nacional[f"soma_{a}"]
        linha_nacional[f"n_{a}"]    = nacional[f"n_{a}"]
        linha_nacional[f"media_{a}"] = round(nacional[f"soma_{a}"] / nacional[f"n_{a}"], 1)
    acumulado = pd.concat([acumulado, pd.DataFrame([linha_nacional])], ignore_index=True)

    colunas_finais = ["SG_UF_ESC"] + [f"media_{a}" for a in AREAS + ["RED"]] + [f"n_{a}" for a in AREAS + ["RED"]]
    return acumulado[colunas_finais].rename(columns={"media_RED": "media_REDACAO", "n_RED": "n_REDACAO"})


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("\n--- Benchmark Geral (todas as redes) ---")
    df_geral = calcular_benchmarks(privadas_apenas=False)
    geral_path = os.path.join(OUTPUT_DIR, "benchmark_geral.csv")
    df_geral.to_csv(geral_path, index=False)
    print(f"Salvo: {geral_path}")

    print("\n--- Benchmark Rede Privada ---")
    df_priv = calcular_benchmarks(privadas_apenas=True)
    priv_path = os.path.join(OUTPUT_DIR, "benchmark_privada.csv")
    df_priv.to_csv(priv_path, index=False)
    print(f"Salvo: {priv_path}")

    # Mostra linha nacional
    print("\nMédias nacionais (todas as redes):")
    brasil = df_geral[df_geral["SG_UF_ESC"] == "BRASIL"].iloc[0]
    for a in ["CN", "CH", "LC", "MT", "REDACAO"]:
        col = f"media_{a}" if a != "REDACAO" else "media_REDACAO"
        print(f"  {a}: {brasil[col]}")
