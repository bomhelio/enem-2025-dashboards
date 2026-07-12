"""
hab_analise_apogeu.py
Motor de analise por HABILIDADE (Matriz de Referencia ENEM) para o Apogeu.
Le output/Apogeu_respostas.csv (cache) + ITENS_PROVA_2025.csv, cruza
TX_RESPOSTAS x gabarito x habilidade item-a-item e gera:
  output/Apogeu_Habilidades.html  (dashboard self-contained)

Fonte unica de gabarito+habilidade = ITENS_PROVA (evita o gabarito de 50 chars do LC).
"""
import os, json
import pandas as pd
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "..", "DADOS")
OUT = os.path.join(BASE, "output")

UNIT_NAMES = {31356816: "Santo Antônio II", 31317101: "Santo Antônio I", 31256285: "Zona Norte"}
AREAS = ["CN", "CH", "LC", "MT"]
ACERTO_CHARS = set("ABCDE")

with open(os.path.join(BASE, "habilidades_labels.json"), encoding="utf-8") as f:
    LABELS = json.load(f)
AREA_NOMES = LABELS["AREA_NOMES"]


# ── ITENS: sequencias por (prova, area, lingua) ──────────────────────────────
it = pd.read_csv(os.path.join(DATA, "ITENS_PROVA_2025.csv"), sep=";", encoding="latin-1")
it["IN_ITEM_ABAN"] = it["IN_ITEM_ABAN"].fillna(0).astype(int)

# tercis de dificuldade (NU_PARAM_B) por area — menor B = mais facil
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


# ── Alunos ───────────────────────────────────────────────────────────────────
df = pd.read_csv(os.path.join(OUT, "Apogeu_respostas.csv"))

def _mk():  # tot/cor = itens validos; seen = itens enfrentados (inclui anulados)
    return {"tot": 0, "cor": 0, "seen": 0}

# acumuladores rede e por unidade: hab[area][hab] e diff[area][tercil]
def novo_agg():
    return {
        "hab": {a: {h: _mk() for h in range(1, 31)} for a in AREAS},
        "diff": {a: {t: _mk() for t in ("facil", "medio", "dificil")} for a in AREAS},
        "area": {a: _mk() for a in AREAS},
        "branco_fim": {a: _mk() for a in AREAS},  # brancos no ultimo terco
        "n_red": 0, "red": {c: 0.0 for c in range(1, 6)},
    }

rede = novo_agg()
und = {u: novo_agg() for u in UNIT_NAMES}
alunos = []

for _, r in df.iterrows():
    co = int(r.CO_ESCOLA)
    unome = UNIT_NAMES.get(co, str(co))
    a_und = und.get(co) or und.get(unome)
    a_und = und[co] if co in und else None
    # und keyed by code:
    if co not in und:
        und[co] = novo_agg()
    A = und[co]

    aluno = {"unidade": unome, "acerto": {}, "erros_hab": {}, "notas": {}}
    for area in AREAS:
        if r.get(f"TP_PRESENCA_{area}") != 1:
            continue
        resp = str(r.get(f"TX_RESPOSTAS_{area}"))
        s = seq(r[f"CO_PROVA_{area}"], area, r.TP_LINGUA)
        if len(resp) != len(s):
            continue
        tot = cor = 0
        n_items = len(s)
        erros = {}
        for i, (hab, gab, aban, terc) in enumerate(s):
            if hab != 0:  # habilidade enfrentada (mesmo que o item tenha sido anulado)
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
            if acertou:
                cor += 1
            else:
                erros[hab] = erros.get(hab, 0) + 1
            # branco no ultimo terco (fadiga/tempo)
            if i >= int(n_items * 2 / 3):
                for agg in (rede, A):
                    agg["branco_fim"][area]["tot"] += 1
                    if branco:
                        agg["branco_fim"][area]["cor"] += 1  # aqui cor = qtd brancos
            tot += 1
        aluno["acerto"][area] = round(cor / tot * 100, 1) if tot else None
        aluno["erros_hab"][area] = erros
    # redacao
    if r.get("TP_STATUS_REDACAO") == 1:
        for agg in (rede, A):
            agg["n_red"] += 1
            for c in range(1, 6):
                agg["red"][c] += float(r.get(f"NU_NOTA_COMP{c}") or 0)
    # notas do aluno
    notas = {}
    for k, col in [("CN", "NU_NOTA_CN"), ("CH", "NU_NOTA_CH"), ("LC", "NU_NOTA_LC"),
                   ("MT", "NU_NOTA_MT"), ("RED", "NU_NOTA_REDACAO")]:
        v = r.get(col)
        notas[k] = round(float(v), 1) if pd.notna(v) else None
    vals = [notas[k] for k in ("CN", "CH", "LC", "MT", "RED") if notas[k] is not None]
    notas["NG"] = round(sum(vals) / len(vals), 1) if len(vals) == 5 else None
    aluno["notas"] = notas
    alunos.append(aluno)


# ── Consolidacao para JSON ───────────────────────────────────────────────────
def pct(m):
    return round(m["cor"] / m["tot"] * 100, 1) if m["tot"] else None

def desc_hab(area, h):
    return LABELS.get(area, {}).get(str(h), "")

def label_hab(area, h):
    txt = desc_hab(area, h)
    return f"H{h}" + (f" — {txt}" if txt else "")

unidades_meta = [{"code": c, "nome": UNIT_NAMES.get(c, str(c)),
                  "n": int((df.CO_ESCOLA == c).sum())}
                 for c in df.CO_ESCOLA.value_counts().index]

# heatmap: area -> [{hab, label, rede, freq, unidades:{code:acerto}}]
heat = {}
for a in AREAS:
    linhas = []
    for h in range(1, 31):
        rd = rede["hab"][a][h]
        if rd["seen"] == 0:  # habilidade nao apareceu em nenhuma prova destes alunos
            continue
        status = "ok" if rd["tot"] > 0 else "anulada"  # seen>0 e tot==0 => item anulado
        linhas.append({
            "hab": h, "label": label_hab(a, h), "desc": desc_hab(a, h),
            "rede": pct(rd), "n": rd["tot"], "status": status,
            "unidades": {c: pct(und[c]["hab"][a][h]) for c in UNIT_NAMES},
        })
    heat[a] = linhas

# gargalos priorizados: (1-acerto) * freq_relativa, top 15
garg = []
for a in AREAS:
    tot_area = sum(rede["hab"][a][h]["tot"] for h in range(1, 31))
    for h in range(1, 31):
        rd = rede["hab"][a][h]
        if rd["tot"] < 30:  # habilidade com poucos itens no ano -> ignora
            continue
        ac = pct(rd)
        freq = rd["tot"] / tot_area * 45  # itens medios por prova
        garg.append({"area": a, "hab": h, "label": label_hab(a, h), "desc": desc_hab(a, h),
                     "acerto": ac, "freq": round(freq, 1),
                     "prioridade": round((100 - ac) * freq, 1), "n": rd["tot"]})
garg.sort(key=lambda x: (x["acerto"], -x["freq"]))  # menor dominio primeiro; desempata por frequencia
garg = garg[:15]

# dificuldade por tercil
dif = {}
for a in AREAS:
    dif[a] = {
        "rede": {t: pct(rede["diff"][a][t]) for t in ("facil", "medio", "dificil")},
        "unidades": {c: {t: pct(und[c]["diff"][a][t]) for t in ("facil", "medio", "dificil")}
                     for c in UNIT_NAMES},
    }

# redacao comps
def red_block(agg):
    if not agg["n_red"]:
        return None
    return {f"C{c}": round(agg["red"][c] / agg["n_red"], 1) for c in range(1, 6)}
redacao = {"rede": red_block(rede),
           "unidades": {c: red_block(und[c]) for c in UNIT_NAMES}}

# dicionario completo: todas as 30 habilidades por area (desc + acerto + status)
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

# acerto por area (rede/unidade)
acerto_area = {"rede": {a: pct(rede["area"][a]) for a in AREAS},
               "unidades": {c: {a: pct(und[c]["area"][a]) for a in AREAS} for c in UNIT_NAMES}}

# branco no fim (fadiga)
branco_fim = {"rede": {a: pct(rede["branco_fim"][a]) for a in AREAS},
              "unidades": {c: {a: pct(und[c]["branco_fim"][a]) for a in AREAS} for c in UNIT_NAMES}}

# alunos: ordenar por NG desc, anonimizar
alunos_ok = [al for al in alunos if al["notas"].get("NG") is not None]
alunos_ok.sort(key=lambda x: -x["notas"]["NG"])
for i, al in enumerate(alunos_ok, 1):
    al["id"] = f"Aluno {i:03d}"
# converter erros_hab (dict) para lista top habilidades erradas por area (com label)
for al in alunos_ok:
    eh = {}
    for a, d in al["erros_hab"].items():
        top = sorted(d.items(), key=lambda x: -x[1])[:4]
        eh[a] = [{"hab": h, "n": n} for h, n in top]  # desc resolvida no cliente via dicionario
    al["erros_hab"] = eh

# consistencia: equilibrio entre as 4 areas objetivas por aluno
# (redacao fica de fora — escala distinta distorce o gap; e a mais forte de ~87%)
_n4 = df[[f"NU_NOTA_{a}" for a in AREAS]].dropna()
_n4.columns = AREAS
_gap = _n4.max(axis=1) - _n4.min(axis=1)
_cats = {"equilibrado": 0, "moderado": 0, "desbalanceado": 0}
for g in _gap:
    _cats["equilibrado" if g < 80 else ("moderado" if g < 160 else "desbalanceado")] += 1
_nn = len(_n4)
consistencia = {
    "n": _nn,
    "gap_mediano": int(np.median(_gap)),
    "cats": {k: {"n": v, "pct": round(v / _nn * 100)} for k, v in _cats.items()},
    "mais_fraca": {a: round(float((_n4.idxmin(axis=1) == a).mean() * 100), 1) for a in AREAS},
    "mais_forte": {a: round(float((_n4.idxmax(axis=1) == a).mean() * 100), 1) for a in AREAS},
}

DATA = {
    "marca": "Apogeu",
    "n_alunos": len(df),
    "n_presentes": {a: int((df[f"TP_PRESENCA_{a}"] == 1).sum()) for a in AREAS},
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

# ── HTML ─────────────────────────────────────────────────────────────────────
from hab_html import gerar_html
html = gerar_html(DATA)
dest = os.path.join(OUT, "Apogeu_Habilidades.html")
with open(dest, "w", encoding="utf-8") as f:
    f.write(html)
print(f"OK -> {dest}")
print(f"  {len(df)} alunos | acerto rede: " +
      " ".join(f"{a} {acerto_area['rede'][a]}%" for a in AREAS))
print(f"  top gargalo: {garg[0]['area']} {garg[0]['label']} ({garg[0]['acerto']}% acerto)")
