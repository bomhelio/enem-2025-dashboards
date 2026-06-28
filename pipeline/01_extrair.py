"""
01_extrair.py
Varre RESULTADOS_2025.csv (2 GB) em chunks e salva um CSV por escola.
Rodar uma vez; os demais scripts usam os arquivos gerados em output/.
"""

import os
import sys
import pandas as pd
from config import ESCOLAS, RESULTADOS_CSV, OUTPUT_DIR, CSV_SEP, CSV_ENCODING, CHUNK_SIZE

COLUNAS_UTEIS = [
    "NU_SEQUENCIAL", "CO_ESCOLA", "CO_MUNICIPIO_ESC", "NO_MUNICIPIO_ESC",
    "CO_UF_ESC", "SG_UF_ESC", "TP_DEPENDENCIA_ADM_ESC", "TP_LOCALIZACAO_ESC",
    "CO_MUNICIPIO_PROVA", "NO_MUNICIPIO_PROVA", "CO_UF_PROVA", "SG_UF_PROVA",
    "TP_PRESENCA_CN", "TP_PRESENCA_CH", "TP_PRESENCA_LC", "TP_PRESENCA_MT",
    "NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC", "NU_NOTA_MT",
    "TP_LINGUA",
    "TP_STATUS_REDACAO",
    "NU_NOTA_COMP1", "NU_NOTA_COMP2", "NU_NOTA_COMP3", "NU_NOTA_COMP4", "NU_NOTA_COMP5",
    "NU_NOTA_REDACAO",
]


def _todos_codigos() -> set[int]:
    codigos: set[int] = set()
    for lista in ESCOLAS.values():
        codigos.update(lista)
    return codigos


def extrair():
    codigos_alvo = _todos_codigos()
    if not codigos_alvo:
        print("ATENÇÃO: Nenhum código INEP configurado em config.py → edite ESCOLAS antes de continuar.")
        sys.exit(1)

    print(f"Varrendo {RESULTADOS_CSV} ...")
    print(f"  Buscando {len(codigos_alvo)} código(s) de escola em {len(ESCOLAS)} marca(s)")

    acumulados: dict[str, list[pd.DataFrame]] = {marca: [] for marca in ESCOLAS}

    total_lido = 0
    for chunk in pd.read_csv(
        RESULTADOS_CSV,
        sep=CSV_SEP,
        encoding=CSV_ENCODING,
        usecols=COLUNAS_UTEIS,
        dtype={"CO_ESCOLA": "Int64"},
        chunksize=CHUNK_SIZE,
    ):
        total_lido += len(chunk)
        filtrado = chunk[chunk["CO_ESCOLA"].isin(codigos_alvo)]
        if filtrado.empty:
            continue

        for marca, codigos in ESCOLAS.items():
            subset = filtrado[filtrado["CO_ESCOLA"].isin(codigos)]
            if not subset.empty:
                acumulados[marca].append(subset)

        print(f"  Lidos {total_lido:,} registros...", end="\r")

    print(f"\nTotal lido: {total_lido:,} registros.")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for marca, partes in acumulados.items():
        if not partes:
            print(f"  [{marca}] Nenhum resultado encontrado — verifique os códigos.")
            continue
        df = pd.concat(partes, ignore_index=True)
        destino = os.path.join(OUTPUT_DIR, f"{marca.replace(' ', '_')}_resultados.csv")
        df.to_csv(destino, index=False, encoding="utf-8")
        print(f"  [{marca}] {len(df):,} inscritos -> {destino}")


if __name__ == "__main__":
    extrair()
