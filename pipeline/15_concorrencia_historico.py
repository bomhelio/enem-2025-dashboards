"""
15_concorrencia_historico.py
Série histórica para a tela de concorrência: médias por área das 4 redes
(Matriz, Elite, Santa Mônica, ZeroHum) em 2024 e 2025, mais rede privada
municipal 2021-2025 e Top 100 BR 2024-2025 (dos JSONs do pipeline histórico).

CO_ESCOLA não existe nos microdados 2021-2023 (INEP suprimiu; voltou em
2024) - por isso as séries de rede começam em 2024.

Saída: output/concorrencia_historico.json
"""

import importlib
import json
import os
import pandas as pd

from config import ESCOLAS, BASE_DIR, OUTPUT_DIR, CSV_SEP, CSV_ENCODING, CHUNK_SIZE

extrair11 = importlib.import_module("11_concorrentes_extrair")

RESULTADOS_2024 = os.path.join(os.path.dirname(BASE_DIR), "Microdados do Enem 2024",
                               "DADOS", "RESULTADOS_2024.csv")
MARCA = "Matriz Educação"
MUNICIPIOS = {"Rio de Janeiro", "Duque de Caxias", "Nova Iguaçu", "São João de Meriti"}
METRICAS = ["CN", "CH", "LC", "MT", "RD"]


def metricas(df: pd.DataFrame) -> dict:
    out = {"n": int(len(df))}
    for a in ["CN", "CH", "LC", "MT"]:
        s = df[df[f"TP_PRESENCA_{a}"] == 1][f"NU_NOTA_{a}"].dropna()
        out[a] = round(float(s.mean()), 1) if len(s) else None
    r = df[df["TP_STATUS_REDACAO"] == 1]["NU_NOTA_REDACAO"].dropna()
    out["RD"] = round(float(r.mean()), 1) if len(r) else None
    return out


def grupos() -> dict:
    g = {MARCA: set(ESCOLAS[MARCA])}
    for rede, unidades in extrair11.CONCORRENTES.items():
        g[rede] = set(unidades)
    return g


def main():
    g = grupos()
    todos = set().union(*g.values())

    # 2024: uma varredura do RESULTADOS_2024
    print(f"Varrendo {RESULTADOS_2024} para {len(todos)} código(s)...")
    partes = []
    for chunk in pd.read_csv(RESULTADOS_2024, sep=CSV_SEP, encoding=CSV_ENCODING,
                             usecols=extrair11.COLUNAS_UTEIS, dtype={"CO_ESCOLA": "Int64"},
                             chunksize=CHUNK_SIZE):
        f = chunk[chunk["CO_ESCOLA"].isin(todos)]
        if not f.empty:
            partes.append(f)
    df24 = pd.concat(partes, ignore_index=True)

    # 2025: CSVs já extraídos
    df25 = pd.concat([
        pd.read_csv(os.path.join(OUTPUT_DIR, f"{MARCA.replace(' ', '_')}_resultados.csv"),
                    dtype={"CO_ESCOLA": "Int64"}),
        pd.read_csv(os.path.join(OUTPUT_DIR, "Concorrentes_resultados.csv"),
                    dtype={"CO_ESCOLA": "Int64"}),
    ], ignore_index=True)

    redes = {}
    for rede, codigos in g.items():
        redes[rede] = {
            "2024": metricas(df24[df24["CO_ESCOLA"].isin(codigos)]),
            "2025": metricas(df25[df25["CO_ESCOLA"].isin(codigos)]),
        }

    hist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historico")
    bench = json.load(open(os.path.join(hist_dir, "historico_benchmark.json"), encoding="utf-8"))
    privada = {}
    for m in bench["municipios"].values():
        if m["nome"] in MUNICIPIOS:
            privada[m["nome"]] = {ano: {k: v[k] for k in METRICAS if k in v}
                                  for ano, v in m["anos"].items()}

    top100_raw = json.load(open(os.path.join(hist_dir, "historico_top100.json"), encoding="utf-8"))
    top100 = {ano: {m: v[m]["media_top100"] for m in METRICAS if m in v}
              for ano, v in top100_raw.items() if ano.isdigit()}

    saida = {"anos": ["2021", "2022", "2023", "2024", "2025"],
             "redes": redes, "privada_municipal": privada, "top100": top100}
    destino = os.path.join(OUTPUT_DIR, "concorrencia_historico.json")
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)
    print(f"-> {destino}")
    for rede, anos in redes.items():
        print(f"  [{rede}] 2024 n={anos['2024']['n']} MT={anos['2024']['MT']} | 2025 n={anos['2025']['n']} MT={anos['2025']['MT']}")


if __name__ == "__main__":
    main()
