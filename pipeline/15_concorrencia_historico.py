"""
15_concorrencia_historico.py [marca]
Série 2024-2025 para a tela de concorrência: médias por área E nota geral
(NG) das redes, da rede privada municipal, da rede privada do Brasil e do
Top 100 BR.

NG = média das 5 áreas para alunos com presença completa + redação válida
(mesma definição dos dashboards). Top 100 BR (NG) = média das 100 melhores
escolas privadas com 30+ alunos válidos, calculada aqui; por área continua
vindo de historico/historico_top100.json (mesma receita).

CO_ESCOLA não existe nos microdados 2021-2023 - por isso a série é 24-25.

Uso: python 15_concorrencia_historico.py "QI Bilíngue"   (default: Matriz Educação)
Saída: output/concorrencia_historico_{slug}.json
"""

import importlib
import json
import os
import sys
import pandas as pd

from config import ESCOLAS, BASE_DIR, OUTPUT_DIR, CSV_SEP, CSV_ENCODING, CHUNK_SIZE
from concorrencia_config import get_marca

extrair11 = importlib.import_module("11_concorrentes_extrair")

RESULTADOS = {
    "2024": os.path.join(os.path.dirname(BASE_DIR), "Microdados do Enem 2024",
                         "DADOS", "RESULTADOS_2024.csv"),
    "2025": os.path.join(BASE_DIR, "DADOS", "RESULTADOS_2025.csv"),
}
MIN_ALUNOS_TOP100 = 30


def com_ng(df: pd.DataFrame) -> pd.DataFrame:
    """Subconjunto presença completa + redação válida, com coluna NG."""
    comp = df[(df["TP_PRESENCA_CN"] == 1) & (df["TP_PRESENCA_CH"] == 1) &
              (df["TP_PRESENCA_LC"] == 1) & (df["TP_PRESENCA_MT"] == 1) &
              (df["TP_STATUS_REDACAO"] == 1)].copy()
    comp["NG"] = (comp["NU_NOTA_CN"] + comp["NU_NOTA_CH"] + comp["NU_NOTA_LC"]
                  + comp["NU_NOTA_MT"] + comp["NU_NOTA_REDACAO"]) / 5
    return comp


def metricas(df: pd.DataFrame) -> dict:
    out = {"n": int(len(df))}
    for a in ["CN", "CH", "LC", "MT"]:
        s = df[df[f"TP_PRESENCA_{a}"] == 1][f"NU_NOTA_{a}"].dropna()
        out[a] = round(float(s.mean()), 1) if len(s) else None
    r = df[df["TP_STATUS_REDACAO"] == 1]["NU_NOTA_REDACAO"].dropna()
    out["RD"] = round(float(r.mean()), 1) if len(r) else None
    ng = com_ng(df)["NG"]
    out["NG"] = round(float(ng.mean()), 1) if len(ng) else None
    return out


def scan_ano(path: str, codigos_redes: set, mun_codes: dict) -> tuple:
    """Uma varredura: linhas das redes, linhas privadas dos municípios de
    benchmark, e NG por escola privada do Brasil (para o Top 100)."""
    partes_redes, partes_mun, partes_ng = [], [], []
    for chunk in pd.read_csv(path, sep=CSV_SEP, encoding=CSV_ENCODING,
                             usecols=extrair11.COLUNAS_UTEIS, dtype={"CO_ESCOLA": "Int64"},
                             chunksize=CHUNK_SIZE):
        f = chunk[chunk["CO_ESCOLA"].isin(codigos_redes)]
        if not f.empty:
            partes_redes.append(f)
        priv = chunk[chunk["TP_DEPENDENCIA_ADM_ESC"] == 4]
        mun = priv[priv["CO_MUNICIPIO_ESC"].isin(mun_codes)]
        if not mun.empty:
            partes_mun.append(mun)
        ng = com_ng(priv[priv["CO_ESCOLA"].notna()])
        if not ng.empty:
            partes_ng.append(ng[["CO_ESCOLA", "NG"]])
    return (pd.concat(partes_redes, ignore_index=True),
            pd.concat(partes_mun, ignore_index=True),
            pd.concat(partes_ng, ignore_index=True))


def top100_ng(ng_br: pd.DataFrame) -> dict:
    por_escola = ng_br.groupby("CO_ESCOLA")["NG"].agg(["mean", "count"])
    elegiveis = por_escola[por_escola["count"] >= MIN_ALUNOS_TOP100]
    top = elegiveis.sort_values("mean", ascending=False).head(100)
    return {"NG": round(float(top["mean"].mean()), 1), "n_escolas": int(len(top))}


def main(marca: str, cfg: dict):
    slug = cfg["slug"]
    mun_codes = cfg["municipios_bench"]
    g = {marca: set(ESCOLAS[marca])}
    for rede, unidades in cfg["concorrentes"].items():
        g[rede] = set(unidades)
    todos = set().union(*g.values())

    hist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historico")
    top100_raw = json.load(open(os.path.join(hist_dir, "historico_top100.json"), encoding="utf-8"))
    bench_brasil = json.load(open(os.path.join(hist_dir, "historico_benchmark.json"),
                                  encoding="utf-8"))["brasil"]["anos"]

    redes = {rede: {} for rede in g}
    privada = {nome: {} for nome in mun_codes.values()}
    privada_brasil = {}
    top100 = {}

    for ano, path in RESULTADOS.items():
        print(f"[{marca}] Varrendo {path} ...")
        df_redes, df_mun, ng_br = scan_ano(path, todos, mun_codes)
        for rede, codigos in g.items():
            redes[rede][ano] = metricas(df_redes[df_redes["CO_ESCOLA"].isin(codigos)])
        for cod, nome in mun_codes.items():
            privada[nome][ano] = metricas(df_mun[df_mun["CO_MUNICIPIO_ESC"] == cod])
        privada_brasil[ano] = {
            "NG": round(float(ng_br["NG"].mean()), 1), "n": int(len(ng_br)),
            **{m: bench_brasil.get(ano, {}).get(m) for m in ["CN", "CH", "LC", "MT", "RD"]},
        }
        areas = {m: top100_raw[ano][m]["media_top100"] for m in ["CN", "CH", "LC", "MT", "RD"]
                 if ano in top100_raw and m in top100_raw[ano]}
        top100[ano] = {**areas, **top100_ng(ng_br)}

    saida = {"anos": ["2024", "2025"], "redes": redes,
             "privada_municipal": privada, "privada_brasil": privada_brasil,
             "top100": top100}
    destino = os.path.join(OUTPUT_DIR, f"concorrencia_historico_{slug}.json")
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)
    print(f"-> {destino}")
    for rede in redes:
        print(f"  [{rede}] NG {redes[rede]['2024']['NG']} -> {redes[rede]['2025']['NG']}")
    print(f"  [Top 100 BR] NG {top100['2024']['NG']} -> {top100['2025']['NG']}")


if __name__ == "__main__":
    marca, cfg = get_marca(sys.argv)
    main(marca, cfg)
