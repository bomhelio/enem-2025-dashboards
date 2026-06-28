# -*- coding: utf-8 -*-
"""Calibra metodologia Top 100 BR contra TOPTIERS 2025 e computa 2024+2025."""
import os, json
import pandas as pd

STABLE = r"C:\Users\helio.barbosa\Documents\Microdados do Enem"
OUT = r"C:\Users\HELIO~1.BAR\AppData\Local\Temp\claude\C--Users-helio-barbosa\c037e361-3139-4823-a131-2dac8f91f58f\scratchpad"
FILES = {
    2025: os.path.join(STABLE, "Microdados do Enem 2025", "DADOS", "RESULTADOS_2025.csv"),
    2024: os.path.join(STABLE, "Microdados do Enem 2024", "DADOS", "RESULTADOS_2024.csv"),
}
AREAS = ["CN", "CH", "LC", "MT"]
SEP, ENC, CHUNK = ";", "latin-1", 200_000

# alvo (TOPTIERS 2025 media_top100 / entrada_top100)
ALVO_MEDIA = {"CN": 660.5, "CH": 657.0, "LC": 643.6, "MT": 786.9, "RD": 873.0}
ALVO_ENTRADA = {"CN": 632.9, "CH": 636.7, "LC": 629.5, "MT": 750.4, "RD": 860.5}


def agg(df, key):
    parts = []
    for a in AREAS:
        pres = df[df[f"TP_PRESENCA_{a}"] == 1]
        g = pres.groupby(key)[f"NU_NOTA_{a}"].agg(["sum", "count"])
        g.columns = [f"s_{a}", f"n_{a}"]
        parts.append(g)
    red = df[df["TP_STATUS_REDACAO"] == 1]
    gr = red.groupby(key)["NU_NOTA_REDACAO"].agg(["sum", "count"])
    gr.columns = ["s_RD", "n_RD"]
    parts.append(gr)
    return pd.concat(parts, axis=1).fillna(0)


def acc(m, p):
    return p if m is None else m.add(p, fill_value=0)


def scan(ano):
    cols = (["CO_ESCOLA", "TP_DEPENDENCIA_ADM_ESC"]
            + [f"TP_PRESENCA_{a}" for a in AREAS] + [f"NU_NOTA_{a}" for a in AREAS]
            + ["TP_STATUS_REDACAO", "NU_NOTA_REDACAO"])
    master, dep = None, {}
    tot = 0
    for chunk in pd.read_csv(FILES[ano], sep=SEP, encoding=ENC, usecols=cols,
                             dtype={"CO_ESCOLA": "Int64"}, chunksize=CHUNK):
        tot += len(chunk)
        ch = chunk.dropna(subset=["CO_ESCOLA"])
        master = acc(master, agg(ch, "CO_ESCOLA"))
        d = ch[["CO_ESCOLA", "TP_DEPENDENCIA_ADM_ESC"]].dropna().drop_duplicates("CO_ESCOLA")
        for _, r in d.iterrows():
            dep.setdefault(int(r["CO_ESCOLA"]), int(r["TP_DEPENDENCIA_ADM_ESC"]))
        print(f"  [{ano}] {tot:,}...", end="\r")
    print(f"\n  [{ano}] total {tot:,}, escolas {len(master)}")
    df = master.copy()
    df["dep"] = [dep.get(int(i)) for i in df.index]
    for a in AREAS:
        df[f"m_{a}"] = df[f"s_{a}"] / df[f"n_{a}"]
    df["m_RD"] = df["s_RD"] / df["n_RD"]
    return df


def top100(df, area, min_n, dep_priv):
    sub = df.copy()
    if dep_priv:
        sub = sub[sub["dep"] == 4]
    sub = sub[sub[f"n_{area}"] >= min_n].dropna(subset=[f"m_{area}"])
    top = sub.nlargest(100, f"m_{area}")
    return round(top[f"m_{area}"].mean(), 1), round(top[f"m_{area}"].min(), 1), len(top)


def calibrar(df25):
    print("\n=== CALIBRACAO (2025) ===")
    melhor = None
    for dep_priv in [False, True]:
        for min_n in [1, 10, 20, 30, 50]:
            erro = 0
            res = {}
            for a in AREAS + ["RD"]:
                med, ent, n = top100(df25, a, min_n, dep_priv)
                res[a] = (med, ent)
                erro += abs(med - ALVO_MEDIA[a]) + abs(ent - ALVO_ENTRADA[a])
            tag = f"dep_priv={dep_priv} min_n={min_n}"
            print(f"  {tag}: erro={erro:.1f}  CN={res['CN']} vs ({ALVO_MEDIA['CN']},{ALVO_ENTRADA['CN']})")
            if melhor is None or erro < melhor[0]:
                melhor = (erro, dep_priv, min_n)
    print(f"\n>>> MELHOR: erro={melhor[0]:.1f} dep_priv={melhor[1]} min_n={melhor[2]}")
    return melhor[1], melhor[2]


def main():
    df = {a: scan(a) for a in (2025, 2024)}
    dep_priv, min_n = calibrar(df[2025])
    saida = {}
    for ano in (2025, 2024):
        saida[str(ano)] = {}
        for a in AREAS + ["RD"]:
            med, ent, n = top100(df[ano], a, min_n, dep_priv)
            saida[str(ano)][a] = {"media_top100": med, "entrada_top100": ent, "n": n}
    saida["_metodo"] = {"dep_priv": dep_priv, "min_n": min_n}
    json.dump(saida, open(os.path.join(OUT, "historico_top100.json"), "w"), indent=1)
    print("\n=== RESULTADO ===")
    print(json.dumps(saida, indent=1))


if __name__ == "__main__":
    main()
