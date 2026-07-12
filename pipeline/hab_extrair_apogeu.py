"""
hab_extrair_apogeu.py
Re-extrai os inscritos do Apogeu do RESULTADOS_2025.csv INCLUINDO as colunas de
resposta/gabarito/versao de prova, necessarias para a analise por habilidade.
Salva output/Apogeu_respostas.csv (cache; rodar uma vez).
"""
import os, sys, time
import pandas as pd
from config import ESCOLAS, RESULTADOS_CSV, OUTPUT_DIR, CSV_SEP, CSV_ENCODING, CHUNK_SIZE

CODIGOS = set(ESCOLAS["Apogeu"])

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
    t0 = time.time()
    partes, total = [], 0
    for chunk in pd.read_csv(RESULTADOS_CSV, sep=CSV_SEP, encoding=CSV_ENCODING,
                             usecols=COLS, dtype={"CO_ESCOLA": "Int64"},
                             chunksize=CHUNK_SIZE):
        total += len(chunk)
        sub = chunk[chunk["CO_ESCOLA"].isin(CODIGOS)]
        if not sub.empty:
            partes.append(sub)
        print(f"  lidos {total:,}...", end="\r")
    df = pd.concat(partes, ignore_index=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    dest = os.path.join(OUTPUT_DIR, "Apogeu_respostas.csv")
    df.to_csv(dest, index=False, encoding="utf-8")
    print(f"\nApogeu: {len(df):,} inscritos -> {dest}  ({time.time()-t0:.0f}s)")

if __name__ == "__main__":
    main()
