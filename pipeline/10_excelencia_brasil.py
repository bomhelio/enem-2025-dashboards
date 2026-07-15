# -*- coding: utf-8 -*-
"""10_excelencia_brasil.py — % de alunos com nota >=600 e >=700 por area,
no Brasil (todos) e na rede privada (TP_DEPENDENCIA_ADM_ESC==4).

Varre o RESULTADOS_2025.csv (2 GB) uma vez e salva
output/benchmark_excelencia.json — consumido pelo 09_gerar_home.py.
Metrica identica aos dashboards: area = TP_PRESENCA==1; RD = TP_STATUS_REDACAO==1.

Uso: python 10_excelencia_brasil.py  (~1-2 min)
"""
import json
import os
import time

import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
DADOS = os.path.join(os.path.dirname(BASE), "DADOS", "RESULTADOS_2025.csv")
DEST = os.path.join(BASE, "output", "benchmark_excelencia.json")

AREAS = {"CN": ("TP_PRESENCA_CN", "NU_NOTA_CN"), "CH": ("TP_PRESENCA_CH", "NU_NOTA_CH"),
         "LC": ("TP_PRESENCA_LC", "NU_NOTA_LC"), "MT": ("TP_PRESENCA_MT", "NU_NOTA_MT")}
USECOLS = ["TP_DEPENDENCIA_ADM_ESC", "TP_STATUS_REDACAO", "NU_NOTA_REDACAO"] + [
    c for par in AREAS.values() for c in par]


def main():
    acc = {esc: {a: {"n": 0, "n600": 0, "n700": 0} for a in list(AREAS) + ["RD"]}
           for esc in ("brasil", "privada")}
    t0 = time.time()
    for chunk in pd.read_csv(DADOS, sep=";", encoding="latin-1",
                             usecols=USECOLS, chunksize=500_000):
        priv = chunk["TP_DEPENDENCIA_ADM_ESC"] == 4
        for esc, df in (("brasil", chunk), ("privada", chunk[priv])):
            for a, (pcol, ncol) in AREAS.items():
                notas = df.loc[df[pcol] == 1, ncol].dropna()
                acc[esc][a]["n"] += len(notas)
                acc[esc][a]["n600"] += int((notas >= 600).sum())
                acc[esc][a]["n700"] += int((notas >= 700).sum())
            red = df.loc[df["TP_STATUS_REDACAO"] == 1, "NU_NOTA_REDACAO"].dropna()
            acc[esc]["RD"]["n"] += len(red)
            acc[esc]["RD"]["n600"] += int((red >= 600).sum())
            acc[esc]["RD"]["n700"] += int((red >= 700).sum())

    out = {}
    for esc, areas in acc.items():
        out[esc] = {}
        for a, v in areas.items():
            out[esc][a] = {
                "n": v["n"],
                "pct_600": round(v["n600"] / v["n"] * 100, 1) if v["n"] else None,
                "pct_700": round(v["n700"] / v["n"] * 100, 1) if v["n"] else None,
            }
    json.dump(out, open(DEST, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"OK -> {DEST} ({time.time()-t0:.0f}s)")
    for esc in out:
        print(esc, {a: out[esc][a]["pct_700"] for a in out[esc]})


if __name__ == "__main__":
    main()
