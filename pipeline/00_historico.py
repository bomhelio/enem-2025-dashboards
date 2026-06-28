"""
00_historico.py
Serie historica ENEM 2021-2025 para as 6 marcas.

Dois regimes de dado:
  - 2024-2025: RESULTADOS_YYYY.csv tem CO_ESCOLA -> serie POR UNIDADE + mercado.
  - 2021-2023: MICRODADOS_ENEM_YYYY.csv NAO tem CO_ESCOLA -> so mercado
    (rede privada por municipio / UF / Brasil).

Metrica identica ao 03_benchmark.py:
  - area: media de NU_NOTA_{a} entre TP_PRESENCA_{a}==1
  - redacao: media de NU_NOTA_REDACAO entre TP_STATUS_REDACAO==1
  - rede privada: TP_DEPENDENCIA_ADM_ESC==4

Uso:
  python 00_historico.py            # todos os anos
  python 00_historico.py 2025       # so 2025 (validacao)
  python 00_historico.py 2021 2022 2023 2024

Saidas (output/):
  historico_benchmark.json  -> municipios/UFs/Brasil x ano (rede privada)
  historico_unidades.json   -> CO_ESCOLA x ano (2024-2025)
"""

import os
import sys
import glob
import json
from collections import defaultdict

import pandas as pd

from config import ESCOLAS, OUTPUT_DIR, CSV_SEP, CSV_ENCODING, CHUNK_SIZE

DOCS = r"C:\Users\helio.barbosa\Documents"
YEAR_FILES = {
    2021: (os.path.join(DOCS, "microdados_enem_2021", "DADOS", "MICRODADOS_ENEM_2021.csv"), False),
    2022: (os.path.join(DOCS, "microdados_enem_2022", "DADOS", "MICRODADOS_ENEM_2022.csv"), False),
    2023: (os.path.join(DOCS, "microdados_enem_2023", "DADOS", "MICRODADOS_ENEM_2023.csv"), False),
    2024: (os.path.join(DOCS, "microdados_enem_2024", "DADOS", "RESULTADOS_2024.csv"), True),
    2025: (os.path.join(DOCS, "Microdados do Enem 2025", "DADOS", "RESULTADOS_2025.csv"), True),
}

AREAS = ["CN", "CH", "LC", "MT"]
BENCH_JSON = os.path.join(OUTPUT_DIR, "historico_benchmark.json")
UNID_JSON = os.path.join(OUTPUT_DIR, "historico_unidades.json")


def _novo_acc():
    d = {f"s_{a}": 0.0 for a in AREAS}
    d.update({f"n_{a}": 0 for a in AREAS})
    d["s_RD"] = 0.0
    d["n_RD"] = 0
    return d


def _somar(acc: dict, df: pd.DataFrame, keycol: str) -> None:
    """Acumula soma/contagem por chave (municipio/UF/escola), por area + redacao."""
    for a in AREAS:
        pres = df[df[f"TP_PRESENCA_{a}"] == 1]
        if pres.empty:
            continue
        g = pres.groupby(keycol)[f"NU_NOTA_{a}"].agg(["sum", "count"])
        for k, row in g.iterrows():
            acc[k][f"s_{a}"] += float(row["sum"])
            acc[k][f"n_{a}"] += int(row["count"])
    red = df[df["TP_STATUS_REDACAO"] == 1]
    if not red.empty:
        g = red.groupby(keycol)["NU_NOTA_REDACAO"].agg(["sum", "count"])
        for k, row in g.iterrows():
            acc[k]["s_RD"] += float(row["sum"])
            acc[k]["n_RD"] += int(row["count"])


def _medias(acc_row: dict) -> dict:
    out = {}
    for a in AREAS:
        n = acc_row[f"n_{a}"]
        out[a] = round(acc_row[f"s_{a}"] / n, 1) if n else None
        out[f"n_{a}"] = n
    n = acc_row["n_RD"]
    out["RD"] = round(acc_row["s_RD"] / n, 1) if n else None
    out["n_RD"] = n
    return out


def target_municipios() -> dict:
    """Municipios das unidades (a partir dos extracts 2025 ja gerados)."""
    mun: dict[int, dict] = {}
    for f in glob.glob(os.path.join(OUTPUT_DIR, "*_resultados.csv")):
        df = pd.read_csv(f, usecols=["CO_MUNICIPIO_ESC", "NO_MUNICIPIO_ESC", "SG_UF_ESC"])
        for _, r in df.drop_duplicates("CO_MUNICIPIO_ESC").iterrows():
            mun[int(r["CO_MUNICIPIO_ESC"])] = {
                "nome": str(r["NO_MUNICIPIO_ESC"]),
                "uf": str(r["SG_UF_ESC"]),
            }
    return mun


def target_escolas() -> set:
    s: set[int] = set()
    for v in ESCOLAS.values():
        s.update(v)
    return s


def escola_to_municipio() -> dict:
    """CO_ESCOLA -> CO_MUNICIPIO_ESC (dos extracts 2025)."""
    m: dict[int, int] = {}
    for f in glob.glob(os.path.join(OUTPUT_DIR, "*_resultados.csv")):
        df = pd.read_csv(f, usecols=["CO_ESCOLA", "CO_MUNICIPIO_ESC"]).dropna()
        for _, r in df.drop_duplicates("CO_ESCOLA").iterrows():
            m[int(r["CO_ESCOLA"])] = int(r["CO_MUNICIPIO_ESC"])
    return m


def _colunas(has_escola: bool) -> list:
    cols = (
        ["CO_MUNICIPIO_ESC", "SG_UF_ESC", "TP_DEPENDENCIA_ADM_ESC"]
        + [f"TP_PRESENCA_{a}" for a in AREAS]
        + [f"NU_NOTA_{a}" for a in AREAS]
        + ["TP_STATUS_REDACAO", "NU_NOTA_REDACAO"]
    )
    if has_escola:
        cols.append("CO_ESCOLA")
    return cols


def processar_ano(ano: int, mun_alvo: set, esc_alvo: set,
                  acc_mun: dict, acc_uf: dict, acc_br: dict, acc_esc: dict) -> None:
    path, has_escola = YEAR_FILES[ano]
    print(f"\n[{ano}] varrendo {os.path.basename(path)} ...")
    total = 0
    for chunk in pd.read_csv(
        path, sep=CSV_SEP, encoding=CSV_ENCODING,
        usecols=_colunas(has_escola),
        dtype={"CO_ESCOLA": "Int64", "CO_MUNICIPIO_ESC": "Int64"},
        chunksize=CHUNK_SIZE,
    ):
        total += len(chunk)
        priv = chunk[chunk["TP_DEPENDENCIA_ADM_ESC"] == 4]

        sub_mun = priv[priv["CO_MUNICIPIO_ESC"].isin(mun_alvo)]
        if not sub_mun.empty:
            _somar(acc_mun[ano], sub_mun, "CO_MUNICIPIO_ESC")
        _somar(acc_uf[ano], priv.assign(_uf=priv["SG_UF_ESC"]), "_uf")
        _somar(acc_br[ano], priv.assign(_br="BRASIL"), "_br")

        if has_escola:
            sub_e = chunk[chunk["CO_ESCOLA"].isin(esc_alvo)]
            if not sub_e.empty:
                _somar(acc_esc[ano], sub_e, "CO_ESCOLA")

        print(f"  {total:,} registros...", end="\r")
    print(f"\n[{ano}] total: {total:,}")


def main(anos: list) -> None:
    mun_meta = target_municipios()
    esc_alvo = target_escolas()
    esc_mun = escola_to_municipio()
    mun_alvo = set(mun_meta.keys())
    uf_alvo = {v["uf"] for v in mun_meta.values()}
    print(f"Municipios-alvo: {len(mun_alvo)} | UFs: {sorted(uf_alvo)} | escolas: {len(esc_alvo)}")

    acc_mun = {a: defaultdict(_novo_acc) for a in anos}
    acc_uf = {a: defaultdict(_novo_acc) for a in anos}
    acc_br = {a: defaultdict(_novo_acc) for a in anos}
    acc_esc = {a: defaultdict(_novo_acc) for a in anos}

    for ano in anos:
        processar_ano(ano, mun_alvo, esc_alvo, acc_mun, acc_uf, acc_br, acc_esc)

    _gravar(anos, mun_meta, esc_mun, acc_mun, acc_uf, acc_br, acc_esc)


def _merge_anos(dst_anos: dict, novos: list, acc: dict, key) -> None:
    for ano in novos:
        if key in acc[ano]:
            dst_anos[str(ano)] = _medias(acc[ano][key])


def _gravar(anos, mun_meta, esc_mun, acc_mun, acc_uf, acc_br, acc_esc) -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # merge incremental: preserva anos ja gravados em runs anteriores
    bench = json.load(open(BENCH_JSON, encoding="utf-8")) if os.path.exists(BENCH_JSON) else {"municipios": {}, "ufs": {}, "brasil": {"anos": {}}}
    unid = json.load(open(UNID_JSON, encoding="utf-8")) if os.path.exists(UNID_JSON) else {}

    for co, meta in mun_meta.items():
        node = bench["municipios"].setdefault(str(co), {"nome": meta["nome"], "uf": meta["uf"], "anos": {}})
        _merge_anos(node["anos"], anos, acc_mun, co)
    for uf in {m["uf"] for m in mun_meta.values()}:
        node = bench["ufs"].setdefault(uf, {"anos": {}})
        _merge_anos(node["anos"], anos, acc_uf, uf)
    _merge_anos(bench["brasil"]["anos"], anos, acc_br, "BRASIL")

    for co_esc, mun in esc_mun.items():
        for ano in anos:
            if co_esc in acc_esc[ano]:
                node = unid.setdefault(str(co_esc), {"municipio": mun, "anos": {}})
                node["anos"][str(ano)] = _medias(acc_esc[ano][co_esc])

    json.dump(bench, open(BENCH_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(unid, open(UNID_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\nSalvo: {BENCH_JSON}")
    print(f"Salvo: {UNID_JSON}")


if __name__ == "__main__":
    anos = [int(x) for x in sys.argv[1:]] or list(YEAR_FILES.keys())
    main(anos)
