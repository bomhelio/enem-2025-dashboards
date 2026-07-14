# -*- coding: utf-8 -*-
"""
hab_analise_multimarcas.py
Diagnóstico por HABILIDADE na escala da REDE (5 marcas agregadas).
Cada MARCA é tratada como uma "unidade" (toggle/comparação).
Reaproveita o motor de hab_analise (ITENS/seq/labels/tercis TRI).
Gera output/Multimarcas_Habilidades.html (protótipo self-contained).

5 seções:
  1. Gargalos universais da rede (classifica universal x local)
  2. Matriz marca x habilidade-gargalo
  3. Mapa de calor da rede (H1-H30, toggle Rede + marcas)
  4. Erro evitável x teto por marca
  5. Consistência por marca
"""
import os, json, sys
import pandas as pd
import numpy as np
import hab_analise as ha  # ITENS já carregado; seq/label_hab/desc_hab/AREAS/ACERTO_CHARS

OUT = ha.OUT
AREAS = ha.AREAS

MARCAS = ["Apogeu", "QI Bilíngue", "Matriz Educação", "Colégio Leonardo da Vinci", "Cubo Global"]
MARCA_COR = {"Apogeu": "#1a3a6e", "QI Bilíngue": "#4c1d95", "Matriz Educação": "#0a4d2b",
             "Colégio Leonardo da Vinci": "#b44408", "Cubo Global": "#097570"}
MARCA_CURTA = {"Apogeu": "Apogeu", "QI Bilíngue": "QI", "Matriz Educação": "Matriz",
               "Colégio Leonardo da Vinci": "Leonardo", "Cubo Global": "Cubo"}

MIN_NET = 100    # itens mínimos na rede p/ a habilidade entrar em gargalo
MIN_MARCA = 15   # itens mínimos na marca p/ mostrar acerto marca-a-marca


def _mk():
    return {"tot": 0, "cor": 0, "seen": 0}


def novo_agg():
    return {
        "hab": {a: {h: _mk() for h in range(1, 31)} for a in AREAS},
        "diff": {a: {t: _mk() for t in ("facil", "medio", "dificil")} for a in AREAS},
        "area": {a: _mk() for a in AREAS},
        "nval": {a: 0 for a in AREAS},   # alunos com resposta valida por area
    }


def pct(x):
    return round(x["cor"] / x["tot"] * 100, 1) if x["tot"] else None


def computar():
    rede = novo_agg()
    mrc = {m: novo_agg() for m in MARCAS}
    n_alunos = {m: 0 for m in MARCAS}
    gap_all, gap_marca = [], {m: [] for m in MARCAS}

    for m in MARCAS:
        path = os.path.join(OUT, f"{m}_respostas.csv")
        df = pd.read_csv(path)
        n_alunos[m] = len(df)
        for _, r in df.iterrows():
            for area in AREAS:
                if r.get(f"TP_PRESENCA_{area}") != 1:
                    continue
                resp = str(r.get(f"TX_RESPOSTAS_{area}"))
                s = ha.seq(r[f"CO_PROVA_{area}"], area, r.TP_LINGUA)
                if len(resp) != len(s):
                    continue
                rede["nval"][area] += 1
                mrc[m]["nval"][area] += 1
                for i, (hab, gab, aban, terc) in enumerate(s):
                    if hab != 0:
                        rede["hab"][area][hab]["seen"] += 1
                        mrc[m]["hab"][area][hab]["seen"] += 1
                    if aban == 1 or hab == 0:
                        continue
                    ch = resp[i]
                    acertou = (ch == gab and ch in ha.ACERTO_CHARS)
                    for agg in (rede, mrc[m]):
                        agg["hab"][area][hab]["tot"] += 1
                        agg["area"][area]["tot"] += 1
                        if terc:
                            agg["diff"][area][terc]["tot"] += 1
                        if acertou:
                            agg["hab"][area][hab]["cor"] += 1
                            agg["area"][area]["cor"] += 1
                            if terc:
                                agg["diff"][area][terc]["cor"] += 1
            notas = [r.get(f"NU_NOTA_{a}") for a in AREAS]
            if all(pd.notna(v) for v in notas):
                g = float(max(notas) - min(notas))
                gap_all.append(g)
                gap_marca[m].append(g)

    return rede, mrc, n_alunos, gap_all, gap_marca


def classify(per):
    """per = {marca: {acerto, n}}. Classifica o gargalo."""
    accs = [v["acerto"] for v in per.values() if v["acerto"] is not None]
    if not accs:
        return ("difuso", 0.0, None)
    best, worst = max(accs), min(accs)
    spread = round(best - worst, 1)
    best_m = next(k for k, v in per.items() if v["acerto"] == best)
    # dispersão entre marcas define a ação:
    if spread >= 20:
        return ("local", spread, best_m)        # alguém vai bem melhor -> troca entre marcas
    if spread <= 10:
        return ("universal", spread, best_m)    # todas parecidas -> conteúdo sistêmico
    return ("misto", spread, best_m)


def _cats(gaps):
    c = {"equilibrado": 0, "moderado": 0, "desbalanceado": 0}
    for g in gaps:
        c["equilibrado" if g < 80 else ("moderado" if g < 160 else "desbalanceado")] += 1
    n = len(gaps) or 1
    return {"n": len(gaps), "gap_mediano": int(np.median(gaps)) if gaps else 0,
            "cats": {k: {"n": v, "pct": round(v / n * 100)} for k, v in c.items()}}


def montar_dados():
    rede, mrc, n_alunos, gap_all, gap_marca = computar()

    # heat: por área -> [{hab,label,desc,rede,marcas:{m:pct},n,status}]
    heat = {}
    for a in AREAS:
        linhas = []
        for h in range(1, 31):
            rd = rede["hab"][a][h]
            if rd["seen"] == 0:
                continue
            linhas.append({
                "hab": h, "label": ha.label_hab(a, h), "desc": ha.desc_hab(a, h),
                "rede": pct(rd), "n": rd["tot"],
                "status": "ok" if rd["tot"] > 0 else "anulada",
                "marcas": {m: pct(mrc[m]["hab"][a][h]) for m in MARCAS},
                "marcas_n": {m: mrc[m]["hab"][a][h]["tot"] for m in MARCAS},
            })
        heat[a] = linhas

    # gargalos da rede (acerto asc) com breakdown por marca + classificação
    cand = []
    for a in AREAS:
        for h in range(1, 31):
            rd = rede["hab"][a][h]
            if rd["tot"] < MIN_NET:
                continue
            per = {}
            for m in MARCAS:
                mm = mrc[m]["hab"][a][h]
                per[m] = {"acerto": pct(mm) if mm["tot"] >= MIN_MARCA else None,
                          "n": mm["tot"]}
            tipo, spread, best_m = classify(per)
            cand.append({"area": a, "hab": h, "label": ha.label_hab(a, h),
                         "desc": ha.desc_hab(a, h), "rede": pct(rd), "n": rd["tot"],
                         "marcas": per, "tipo": tipo, "spread": spread, "best": best_m})
    cand.sort(key=lambda x: (x["rede"] if x["rede"] is not None else 999))
    gargalos = cand[:12]

    # dificuldade (tercis TRI) por marca + rede
    dificuldade = {
        "rede": {t: pct({"cor": sum(rede["diff"][a][t]["cor"] for a in AREAS),
                         "tot": sum(rede["diff"][a][t]["tot"] for a in AREAS)})
                 for t in ("facil", "medio", "dificil")},
        "marcas": {m: {t: pct({"cor": sum(mrc[m]["diff"][a][t]["cor"] for a in AREAS),
                               "tot": sum(mrc[m]["diff"][a][t]["tot"] for a in AREAS)})
                       for t in ("facil", "medio", "dificil")} for m in MARCAS},
    }

    consistencia = {"rede": _cats(gap_all),
                    "marcas": {m: _cats(gap_marca[m]) for m in MARCAS}}

    return {
        "n_total": sum(n_alunos.values()),
        "marcas": [{"nome": m, "curta": MARCA_CURTA[m], "cor": MARCA_COR[m], "n": n_alunos[m]}
                   for m in MARCAS],
        "area_nomes": ha.AREA_NOMES,
        "acerto_area_rede": {a: pct(rede["area"][a]) for a in AREAS},
        "n_avaliados": {a: rede["nval"][a] for a in AREAS},
        "n_avaliados_marca": {m: {a: mrc[m]["nval"][a] for a in AREAS} for m in MARCAS},
        "heat": heat,
        "gargalos": gargalos,
        "dificuldade": dificuldade,
        "consistencia": consistencia,
    }


if __name__ == "__main__":
    D = montar_dados()
    # resumo de validação
    print(f"Rede: {D['n_total']} alunos | acerto médio rede: " +
          " ".join(f"{a} {D['acerto_area_rede'][a]}%" for a in AREAS))
    print("Marcas:", ", ".join(f"{m['curta']}({m['n']})" for m in D["marcas"]))
    print("\nTop gargalos da rede:")
    for g in D["gargalos"][:8]:
        pm = " ".join(f"{MARCA_CURTA[m]}:{g['marcas'][m]['acerto']}" for m in MARCAS)
        print(f"  [{g['tipo']:9}] {g['area']} H{g['hab']} rede={g['rede']}% spread={g['spread']} | {pm}")
    print("\nDificuldade rede:", D["dificuldade"]["rede"])
    print("Consistência rede:", D["consistencia"]["rede"]["cats"])

    from hab_html_multimarcas import gerar_html
    html = gerar_html(D)
    dest = os.path.join(OUT, "Multimarcas_Habilidades.html")
    with open(dest, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\nOK -> {dest}")
