# -*- coding: utf-8 -*-
"""
hab_analise.py
Motor de analise por HABILIDADE (Matriz de Referencia ENEM) - multimarcas.
Le output/{marca}_respostas.csv (cache; gerado por hab_extrair.py) + ITENS_PROVA,
cruza TX_RESPOSTAS x gabarito x habilidade item-a-item e gera:
  output/{marca}_Habilidades.html  (dashboard self-contained da marca)

Fonte unica de gabarito+habilidade = ITENS_PROVA (evita o gabarito de 50 chars do LC).
UNIT_NAMES e derivado do mapa_escola_bairro.json (mesmos nomes do dashboard base).

Uso:
  python hab_analise.py                 # todas as marcas com dashboard
  python hab_analise.py "QI Bilíngue"
"""
import os, sys, json
import pandas as pd
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, "..", "DADOS")
OUT = os.path.join(BASE, "output")

AREAS = ["CN", "CH", "LC", "MT"]
ACERTO_CHARS = set("ABCDE")

# accent (segunda cor da paleta) por marca - igual a BRAND_COLORS de 05_gerar_dashboards
ACCENTS = {
    "Apogeu":                    "#2563eb",
    "QI Bilíngue":               "#7c3aed",
    "Matriz Educação":           "#15803d",
    "Colégio Leonardo da Vinci": "#c2560a",
    "Cubo Global":               "#0f9d96",
}
MARCAS_PADRAO = list(ACCENTS.keys())

with open(os.path.join(BASE, "habilidades_labels.json"), encoding="utf-8") as f:
    LABELS = json.load(f)
AREA_NOMES = LABELS["AREA_NOMES"]

with open(os.path.join(OUT, "mapa_escola_bairro.json"), encoding="utf-8") as f:
    MAPA = json.load(f)


# ── ITENS: sequencias por (prova, area, lingua) - independente de marca ──────
it = pd.read_csv(os.path.join(DATA_DIR, "ITENS_PROVA_2025.csv"), sep=";", encoding="latin-1")
it["IN_ITEM_ABAN"] = it["IN_ITEM_ABAN"].fillna(0).astype(int)

DIFF_THRESH = {}
for a in AREAS:
    b = it[(it.SG_AREA == a) & (it.IN_ITEM_ABAN == 0)]["NU_PARAM_B"].dropna()
    DIFF_THRESH[a] = (b.quantile(1/3), b.quantile(2/3))


def _tercil(area, b):
    if pd.isna(b):
        return None
    lo, hi = DIFF_THRESH[area]
    return "facil" if b <= lo else ("dificil" if b > hi else "medio")


_seq_cache = {}
def seq(prova, area, lingua):
    key = (prova, area, int(lingua) if not pd.isna(lingua) else -1)
    if key in _seq_cache:
        return _seq_cache[key]
    s = it[(it.CO_PROVA == prova) & (it.SG_AREA == area)]
    if area == "LC":
        s = s[(s.TP_LINGUA == lingua) | (s.TP_LINGUA.isna())]
    s = s.sort_values("CO_POSICAO")
    rows = [(int(h) if not pd.isna(h) else 0, g, int(ab), _tercil(area, b))
            for h, g, ab, b in zip(s.CO_HABILIDADE, s.TX_GABARITO, s.IN_ITEM_ABAN, s.NU_PARAM_B)]
    _seq_cache[key] = rows
    return rows


# ── Nomes de unidade por marca (mesma logica do dashboard base) ──────────────
def build_unit_names(codes_present):
    names, seen = {}, {}
    for co in sorted(int(c) for c in codes_present):
        info = MAPA.get(str(co), {})
        lbl = info.get("label", "")
        # o mapa usa " — " (travessão) como separador "Marca — Unidade" (delimitador interno)
        nome = lbl.split(" — ", 1)[-1] if lbl else (info.get("municipio") or str(co))
        if nome in seen:
            nome = f"{nome} ({co})"
        seen[nome] = 1
        names[co] = nome
    return names


def desc_hab(area, h):
    return LABELS.get(area, {}).get(str(h), "")


def label_hab(area, h):
    txt = desc_hab(area, h)
    return f"H{h}" + (f" - {txt}" if txt else "")


# ── Analise de uma marca ─────────────────────────────────────────────────────
def analisar(marca):
    csv_path = os.path.join(OUT, f"{marca}_respostas.csv")
    if not os.path.exists(csv_path):
        print(f"  [{marca}] CSV nao encontrado: {csv_path} - rode hab_extrair.py.")
        return
    df = pd.read_csv(csv_path)
    UNIT_NAMES = build_unit_names(df.CO_ESCOLA.unique())

    def _mk():
        return {"tot": 0, "cor": 0, "seen": 0}

    def novo_agg():
        return {
            "hab": {a: {h: _mk() for h in range(1, 31)} for a in AREAS},
            "diff": {a: {t: _mk() for t in ("facil", "medio", "dificil")} for a in AREAS},
            "area": {a: _mk() for a in AREAS},
            "branco_fim": {a: _mk() for a in AREAS},
            "nval": {a: 0 for a in AREAS},   # alunos com resposta valida por area
            "n_red": 0, "red": {c: 0.0 for c in range(1, 6)},
        }

    rede = novo_agg()
    und = {c: novo_agg() for c in UNIT_NAMES}

    for _, r in df.iterrows():
        co = int(r.CO_ESCOLA)
        if co not in und:
            und[co] = novo_agg()
        A = und[co]
        for area in AREAS:
            if r.get(f"TP_PRESENCA_{area}") != 1:
                continue
            resp = str(r.get(f"TX_RESPOSTAS_{area}"))
            s = seq(r[f"CO_PROVA_{area}"], area, r.TP_LINGUA)
            if len(resp) != len(s):
                continue
            rede["nval"][area] += 1
            A["nval"][area] += 1
            tot = 0
            n_items = len(s)
            for i, (hab, gab, aban, terc) in enumerate(s):
                if hab != 0:
                    rede["hab"][area][hab]["seen"] += 1
                    A["hab"][area][hab]["seen"] += 1
                if aban == 1 or hab == 0:
                    continue
                ch = resp[i]
                acertou = (ch == gab and ch in ACERTO_CHARS)
                branco = ch not in ACERTO_CHARS
                for agg in (rede, A):
                    agg["hab"][area][hab]["tot"] += 1
                    agg["area"][area]["tot"] += 1
                    if terc:
                        agg["diff"][area][terc]["tot"] += 1
                    if acertou:
                        agg["hab"][area][hab]["cor"] += 1
                        agg["area"][area]["cor"] += 1
                        if terc:
                            agg["diff"][area][terc]["cor"] += 1
                if i >= int(n_items * 2 / 3):
                    for agg in (rede, A):
                        agg["branco_fim"][area]["tot"] += 1
                        if branco:
                            agg["branco_fim"][area]["cor"] += 1
                tot += 1
        if r.get("TP_STATUS_REDACAO") == 1:
            for agg in (rede, A):
                agg["n_red"] += 1
                for c in range(1, 6):
                    agg["red"][c] += float(r.get(f"NU_NOTA_COMP{c}") or 0)

    def pct(m):
        return round(m["cor"] / m["tot"] * 100, 1) if m["tot"] else None

    unidades_meta = [{"code": c, "nome": UNIT_NAMES.get(c, str(c)),
                      "n": int((df.CO_ESCOLA == c).sum())}
                     for c in df.CO_ESCOLA.value_counts().index]

    heat = {}
    for a in AREAS:
        linhas = []
        for h in range(1, 31):
            rd = rede["hab"][a][h]
            if rd["seen"] == 0:
                continue
            status = "ok" if rd["tot"] > 0 else "anulada"
            linhas.append({
                "hab": h, "label": label_hab(a, h), "desc": desc_hab(a, h),
                "rede": pct(rd), "n": rd["tot"], "status": status,
                "unidades": {c: pct(und[c]["hab"][a][h]) for c in UNIT_NAMES},
                "unidades_n": {c: und[c]["hab"][a][h]["tot"] for c in UNIT_NAMES},
            })
        heat[a] = linhas

    garg = []
    for a in AREAS:
        tot_area = sum(rede["hab"][a][h]["tot"] for h in range(1, 31))
        for h in range(1, 31):
            rd = rede["hab"][a][h]
            if rd["tot"] < 30:
                continue
            ac = pct(rd)
            freq = rd["tot"] / tot_area * 45 if tot_area else 0
            garg.append({"area": a, "hab": h, "label": label_hab(a, h), "desc": desc_hab(a, h),
                         "acerto": ac, "freq": round(freq, 1),
                         "prioridade": round((100 - ac) * freq, 1), "n": rd["tot"]})
    garg.sort(key=lambda x: (x["acerto"], -x["freq"]))
    garg = garg[:15]

    dif = {}
    for a in AREAS:
        dif[a] = {
            "rede": {t: pct(rede["diff"][a][t]) for t in ("facil", "medio", "dificil")},
            "unidades": {c: {t: pct(und[c]["diff"][a][t]) for t in ("facil", "medio", "dificil")}
                         for c in UNIT_NAMES},
        }

    def red_block(agg):
        if not agg["n_red"]:
            return None
        return {f"C{c}": round(agg["red"][c] / agg["n_red"], 1) for c in range(1, 6)}
    redacao = {"rede": red_block(rede),
               "unidades": {c: red_block(und[c]) for c in UNIT_NAMES}}

    dicionario = {}
    for a in AREAS:
        rows = []
        for h in range(1, 31):
            rd = rede["hab"][a][h]
            if rd["tot"] > 0:
                status, ac = "ok", pct(rd)
            elif rd["seen"] > 0:
                status, ac = "anulada", None
            else:
                status, ac = "ausente", None
            rows.append({"hab": h, "desc": desc_hab(a, h), "acerto": ac,
                         "n": rd["tot"], "status": status})
        dicionario[a] = rows

    acerto_area = {"rede": {a: pct(rede["area"][a]) for a in AREAS},
                   "unidades": {c: {a: pct(und[c]["area"][a]) for a in AREAS} for c in UNIT_NAMES}}

    branco_fim = {"rede": {a: pct(rede["branco_fim"][a]) for a in AREAS},
                  "unidades": {c: {a: pct(und[c]["branco_fim"][a]) for a in AREAS} for c in UNIT_NAMES}}

    _n4 = df[[f"NU_NOTA_{a}" for a in AREAS]].dropna()
    _n4.columns = AREAS
    _gap = _n4.max(axis=1) - _n4.min(axis=1)
    _cats = {"equilibrado": 0, "moderado": 0, "desbalanceado": 0}
    for g in _gap:
        _cats["equilibrado" if g < 80 else ("moderado" if g < 160 else "desbalanceado")] += 1
    _nn = len(_n4)
    consistencia = {
        "n": _nn,
        "gap_mediano": int(np.median(_gap)) if _nn else 0,
        "cats": {k: {"n": v, "pct": round(v / _nn * 100) if _nn else 0} for k, v in _cats.items()},
        "mais_fraca": {a: round(float((_n4.idxmin(axis=1) == a).mean() * 100), 1) for a in AREAS} if _nn else {},
        "mais_forte": {a: round(float((_n4.idxmax(axis=1) == a).mean() * 100), 1) for a in AREAS} if _nn else {},
    }

    D = {
        "marca": marca,
        "accent": ACCENTS.get(marca, "#2563eb"),
        "n_alunos": len(df),
        "n_presentes": {a: int((df[f"TP_PRESENCA_{a}"] == 1).sum()) for a in AREAS},
        "n_avaliados": {a: rede["nval"][a] for a in AREAS},
        "n_avaliados_und": {c: {a: und[c]["nval"][a] for a in AREAS} for c in UNIT_NAMES},
        "area_nomes": AREA_NOMES,
        "unidades": unidades_meta,
        "acerto_area": acerto_area,
        "heat": heat,
        "dicionario": dicionario,
        "gargalos": garg,
        "dificuldade": dif,
        "redacao": redacao,
        "branco_fim": branco_fim,
        "consistencia": consistencia,
    }

    from hab_html import gerar_html
    html = gerar_html(D, accent=D["accent"])
    safe = marca.replace(" ", "_").replace("é", "e").replace("ô", "o")
    dest = os.path.join(OUT, f"{safe}_Habilidades.html")
    with open(dest, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"OK -> {dest}")
    print(f"  [{marca}] {len(df)} alunos | {len(UNIT_NAMES)} unidades | acerto rede: " +
          " ".join(f"{a} {acerto_area['rede'][a]}%" for a in AREAS))
    if garg:
        print(f"  top gargalo: {garg[0]['area']} {garg[0]['label']} ({garg[0]['acerto']}% acerto)")


def main():
    marcas = sys.argv[1:] if len(sys.argv) > 1 else MARCAS_PADRAO
    for m in marcas:
        analisar(m)


if __name__ == "__main__":
    main()
