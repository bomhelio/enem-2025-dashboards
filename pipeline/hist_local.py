# -*- coding: utf-8 -*-
"""
hist_local.py  — auto-contido (le da pasta estavel, escreve local).
Serie historica ENEM 2021-2025: 6 marcas + UF + Brasil (rede privada).
Metrica identica ao 03_benchmark.py.
"""
import os, json
import pandas as pd

STABLE = r"C:\Users\helio.barbosa\Documents\Microdados do Enem"
OUT = r"C:\Users\HELIO~1.BAR\AppData\Local\Temp\claude\C--Users-helio-barbosa\c037e361-3139-4823-a131-2dac8f91f58f\scratchpad"

YEAR_FILES = {
    2025: (os.path.join(STABLE, "Microdados do Enem 2025", "DADOS", "RESULTADOS_2025.csv"), True),
    2024: (os.path.join(STABLE, "Microdados do Enem 2024", "DADOS", "RESULTADOS_2024.csv"), True),
    2023: (os.path.join(STABLE, "Microdados do Enem 2023", "DADOS", "MICRODADOS_ENEM_2023.csv"), False),
    2022: (os.path.join(STABLE, "Microdados do Enem 2022", "DADOS", "MICRODADOS_ENEM_2022.csv"), False),
    2021: (os.path.join(STABLE, "Microdados do Enem 2021", "DADOS", "MICRODADOS_ENEM_2021.csv"), False),
}
ORDEM = [2025, 2024, 2023, 2022, 2021]

ESCOLAS = {
    "Apogeu":          [31317101, 31356816, 31256285, 31380024, 31363383],
    "QI Bilíngue":     [33135924, 33071721, 33156026, 33199400, 33124418, 33143331, 33187924],
    "Matriz Educação": [33187789, 33183368, 33048185, 33197466, 33187762, 33192685, 33190674, 33187770],
    "União":           [43162703],
    "Unificado":       [43214754],
    "Americano":       [43107524],
    "Colégio Leonardo da Vinci": [43172423, 43172440, 43213278],
    "Cubo Global":     [33178828, 33186260],
}
ESC_ALVO = {c for lst in ESCOLAS.values() for c in lst}
ESC_MARCA = {c: m for m, lst in ESCOLAS.items() for c in lst}

AREAS = ["CN", "CH", "LC", "MT"]
SEP, ENC, CHUNK = ";", "latin-1", 200_000


def agg_chunk(df, keycol):
    parts = []
    for a in AREAS:
        pres = df[df[f"TP_PRESENCA_{a}"] == 1]
        g = pres.groupby(keycol)[f"NU_NOTA_{a}"].agg(["sum", "count"])
        g.columns = [f"s_{a}", f"n_{a}"]
        parts.append(g)
    red = df[df["TP_STATUS_REDACAO"] == 1]
    gr = red.groupby(keycol)["NU_NOTA_REDACAO"].agg(["sum", "count"])
    gr.columns = ["s_RD", "n_RD"]
    parts.append(gr)
    return pd.concat(parts, axis=1).fillna(0)


def acc_add(master, partial):
    return partial if master is None else master.add(partial, fill_value=0)


def medias(row):
    out = {}
    for a in AREAS:
        n = int(row[f"n_{a}"])
        out[a] = round(row[f"s_{a}"] / n, 1) if n else None
        out[f"n_{a}"] = n
    n = int(row["n_RD"])
    out["RD"] = round(row["s_RD"] / n, 1) if n else None
    out["n_RD"] = n
    return out


def cols(has_escola):
    c = (["CO_MUNICIPIO_ESC", "SG_UF_ESC", "TP_DEPENDENCIA_ADM_ESC"]
         + [f"TP_PRESENCA_{a}" for a in AREAS] + [f"NU_NOTA_{a}" for a in AREAS]
         + ["TP_STATUS_REDACAO", "NU_NOTA_REDACAO"])
    if has_escola:
        c += ["CO_ESCOLA", "NO_MUNICIPIO_ESC"]
    return c


def main():
    mun_m = {a: None for a in YEAR_FILES}
    uf_m = {a: None for a in YEAR_FILES}
    esc_m = {a: None for a in YEAR_FILES}
    mun_meta = {}      # cod -> (nome, uf)
    esc_mun = {}       # co_escola -> cod_municipio

    for ano in ORDEM:
        path, has_esc = YEAR_FILES[ano]
        print(f"[{ano}] {os.path.basename(path)} ...", flush=True)
        tot = 0
        for chunk in pd.read_csv(path, sep=SEP, encoding=ENC, usecols=cols(has_esc),
                                 dtype={"CO_ESCOLA": "Int64", "CO_MUNICIPIO_ESC": "Int64"},
                                 chunksize=CHUNK):
            tot += len(chunk)
            priv = chunk[chunk["TP_DEPENDENCIA_ADM_ESC"] == 4]
            if priv.empty:
                continue
            mun_m[ano] = acc_add(mun_m[ano], agg_chunk(priv, "CO_MUNICIPIO_ESC"))
            uf_m[ano] = acc_add(uf_m[ano], agg_chunk(priv, "SG_UF_ESC"))
            if has_esc:
                meta = priv[["CO_MUNICIPIO_ESC", "NO_MUNICIPIO_ESC", "SG_UF_ESC"]].dropna().drop_duplicates("CO_MUNICIPIO_ESC")
                for _, r in meta.iterrows():
                    mun_meta.setdefault(int(r["CO_MUNICIPIO_ESC"]), (str(r["NO_MUNICIPIO_ESC"]), str(r["SG_UF_ESC"])))
                sub = chunk[chunk["CO_ESCOLA"].isin(ESC_ALVO)]
                if not sub.empty:
                    esc_m[ano] = acc_add(esc_m[ano], agg_chunk(sub, "CO_ESCOLA"))
                    for _, r in sub[["CO_ESCOLA", "CO_MUNICIPIO_ESC"]].dropna().drop_duplicates("CO_ESCOLA").iterrows():
                        esc_mun.setdefault(int(r["CO_ESCOLA"]), int(r["CO_MUNICIPIO_ESC"]))
            print(f"  {tot:,}...", end="\r", flush=True)
        print(f"  [{ano}] total {tot:,}")

    gravar(mun_m, uf_m, esc_m, mun_meta, esc_mun)


def gravar(mun_m, uf_m, esc_m, mun_meta, esc_mun):
    unid = {}
    for ano, df in esc_m.items():
        if df is None:
            continue
        for co, row in df.iterrows():
            co = int(co)
            node = unid.setdefault(str(co), {"marca": ESC_MARCA.get(co), "municipio": esc_mun.get(co), "anos": {}})
            node["anos"][str(ano)] = medias(row)

    mun_alvo = set(esc_mun.values())
    ufs_alvo = {mun_meta.get(m, ("", ""))[1] for m in mun_alvo}

    bench = {"municipios": {}, "ufs": {}, "brasil": {"anos": {}}}
    for m in mun_alvo:
        nome, uf = mun_meta.get(m, (str(m), ""))
        node = {"nome": nome, "uf": uf, "anos": {}}
        for ano, df in mun_m.items():
            if df is not None and m in df.index:
                node["anos"][str(ano)] = medias(df.loc[m])
        bench["municipios"][str(m)] = node
    for uf in ufs_alvo:
        node = {"anos": {}}
        for ano, df in uf_m.items():
            if df is not None and uf in df.index:
                node["anos"][str(ano)] = medias(df.loc[uf])
        bench["ufs"][uf] = node
    for ano, df in uf_m.items():
        if df is not None:
            bench["brasil"]["anos"][str(ano)] = medias(df.sum())

    json.dump(bench, open(os.path.join(OUT, "historico_benchmark.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(unid, open(os.path.join(OUT, "historico_unidades.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("Gravado em", OUT)


if __name__ == "__main__":
    main()
