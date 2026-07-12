# -*- coding: utf-8 -*-
"""
hab_extrair.py
Re-extrai inscritos das marcas do RESULTADOS_2025.csv INCLUINDO as colunas de
resposta/gabarito/versao de prova, necessarias para a analise por habilidade.

Faz UMA UNICA varredura do arquivo de 2 GB e grava um CSV por marca:
  output/{marca}_respostas.csv  (cache; rodar uma vez por atualizacao dos microdados)

Uso:
  python hab_extrair.py                       # todas as marcas com dashboard
  python hab_extrair.py "QI Bilíngue" "Cubo Global"
"""
import os, sys, time
import pandas as pd
from config import ESCOLAS, RESULTADOS_CSV, OUTPUT_DIR, CSV_SEP, CSV_ENCODING, CHUNK_SIZE

# marcas que possuem dashboard/paleta (mesmo conjunto de 05_gerar_dashboards)
MARCAS_PADRAO = ["Apogeu", "QI Bilíngue", "Matriz Educação",
                 "Colégio Leonardo da Vinci", "Cubo Global"]

COLS = [
    "NU_SEQUENCIAL", "CO_ESCOLA", "NO_MUNICIPIO_ESC", "SG_UF_ESC",
    "TP_PRESENCA_CN", "TP_PRESENCA_CH", "TP_PRESENCA_LC", "TP_PRESENCA_MT",
    "NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC", "NU_NOTA_MT",
    "CO_PROVA_CN", "CO_PROVA_CH", "CO_PROVA_LC", "CO_PROVA_MT",
    "TX_RESPOSTAS_CN", "TX_RESPOSTAS_CH", "TX_RESPOSTAS_LC", "TX_RESPOSTAS_MT",
    "TX_GABARITO_CN", "TX_GABARITO_CH", "TX_GABARITO_LC", "TX_GABARITO_MT",
    "TP_LINGUA", "TP_STATUS_REDACAO",
    "NU_NOTA_COMP1", "NU_NOTA_COMP2", "NU_NOTA_COMP3", "NU_NOTA_COMP4", "NU_NOTA_COMP5",
    "NU_NOTA_REDACAO",
]


def main():
    marcas = sys.argv[1:] if len(sys.argv) > 1 else MARCAS_PADRAO
    marcas = [m for m in marcas if m in ESCOLAS]
    if not marcas:
        print("Nenhuma marca valida informada."); return

    # code -> marca (um code pertence a uma unica marca)
    code2marca = {}
    for m in marcas:
        for c in ESCOLAS[m]:
            code2marca[c] = m
    todos_codigos = set(code2marca)
    partes = {m: [] for m in marcas}

    t0, total = time.time(), 0
    for chunk in pd.read_csv(RESULTADOS_CSV, sep=CSV_SEP, encoding=CSV_ENCODING,
                             usecols=COLS, dtype={"CO_ESCOLA": "Int64"},
                             chunksize=CHUNK_SIZE):
        total += len(chunk)
        sub = chunk[chunk["CO_ESCOLA"].isin(todos_codigos)]
        if not sub.empty:
            for m in marcas:
                s = sub[sub["CO_ESCOLA"].isin(ESCOLAS[m])]
                if not s.empty:
                    partes[m].append(s)
        print(f"  lidos {total:,}...", end="\r")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print()
    for m in marcas:
        if not partes[m]:
            print(f"  [{m}] 0 inscritos encontrados — pulando.")
            continue
        df = pd.concat(partes[m], ignore_index=True)
        dest = os.path.join(OUTPUT_DIR, f"{m}_respostas.csv")
        df.to_csv(dest, index=False, encoding="utf-8")
        print(f"  [{m}] {len(df):,} inscritos -> {dest}")
    print(f"Concluido em {time.time()-t0:.0f}s.")


if __name__ == "__main__":
    main()
