"""
11_concorrentes_extrair.py [marca]
Varre RESULTADOS_2025.csv (2 GB) e extrai os microdados das unidades dos
concorrentes da marca (definidos em concorrencia_config.py). Mesmas colunas
do 01_extrair.py → estatísticas comparáveis 1:1 com as nossas marcas.

Uso: python 11_concorrentes_extrair.py "QI Bilíngue"   (default: Matriz Educação)

Saídas em output/:
  - Concorrentes_{slug}_resultados.csv
  - concorrentes_unidades_{slug}.json
"""

import json
import os
import sys
import pandas as pd
from config import RESULTADOS_CSV, OUTPUT_DIR, CSV_SEP, CSV_ENCODING, CHUNK_SIZE
from concorrencia_config import get_marca

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


def extrair(marca: str, cfg: dict):
    concorrentes = cfg["concorrentes"]
    slug = cfg["slug"]
    codigos_alvo: set[int] = set()
    for unidades in concorrentes.values():
        codigos_alvo.update(unidades)
    n_unidades = sum(len(u) for u in concorrentes.values())
    print(f"[{marca}] Varrendo {RESULTADOS_CSV} ...")
    print(f"  Buscando {n_unidades} unidade(s) de {len(concorrentes)} rede(s) concorrente(s)")

    partes: list[pd.DataFrame] = []
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
        if not filtrado.empty:
            partes.append(filtrado)
        print(f"  Lidos {total_lido:,} registros...", end="\r")

    print(f"\nTotal lido: {total_lido:,} registros.")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df = pd.concat(partes, ignore_index=True)
    destino = os.path.join(OUTPUT_DIR, f"Concorrentes_{slug}_resultados.csv")
    df.to_csv(destino, index=False, encoding="utf-8")

    encontrados = set(df["CO_ESCOLA"].unique().tolist())
    meta = {}
    for rede, unidades in concorrentes.items():
        for co, info in unidades.items():
            meta[str(co)] = {
                "rede": rede,
                "label": f"{rede} - {info['label']}",
                "municipio": info["municipio"],
                "bairro": info["bairro"],
                "tem_dados_2025": co in encontrados,
                "n_inscritos": int((df["CO_ESCOLA"] == co).sum()),
            }
    destino_meta = os.path.join(OUTPUT_DIR, f"concorrentes_unidades_{slug}.json")
    with open(destino_meta, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    com_dados = sum(1 for m in meta.values() if m["tem_dados_2025"])
    print(f"  {len(df):,} inscritos em {com_dados}/{n_unidades} unidades -> {destino}")
    sem = [m["label"] for m in meta.values() if not m["tem_dados_2025"]]
    if sem:
        print(f"  Sem dados 2025: {', '.join(sem)}")


if __name__ == "__main__":
    marca, cfg = get_marca(sys.argv)
    extrair(marca, cfg)
