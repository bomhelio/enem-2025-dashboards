"""
12_analise_concorrencia.py [marca]
Consolida estatísticas unidade a unidade para a tela de inteligência
competitiva da marca (concorrencia_config.py).

Usa a MESMA estatisticas_area do 02_quantitativo.py → números idênticos
aos dos dashboards de marca.

Uso: python 12_analise_concorrencia.py "QI Bilíngue"   (default: Matriz Educação)
Saída: output/concorrencia_{slug}.json
"""

import importlib
import json
import math
import os
import sys
import pandas as pd

from config import OUTPUT_DIR
from concorrencia_config import get_marca

quant = importlib.import_module("02_quantitativo")
estatisticas_area = quant.estatisticas_area
AREAS = list(quant.AREAS)  # ["CN", "CH", "LC", "MT"]

N_SELETA = 30   # abaixo disso, turma seleta: sinaliza, não exclui


# ─────────────────────────────────────────────────────────────────────────────
# Veredicto — calculado UMA vez, aqui. A tela só renderiza.
#
# "Lidera" só quando a diferença supera a margem de erro da amostra. Um corte
# binário de tamanho (o antigo †) não distingue uma unidade de 12 alunos com
# gap de 113 pontos (real) de uma de 20 alunos com gap de 26 (ruído); o
# intervalo distingue, porque é contínuo.
# ─────────────────────────────────────────────────────────────────────────────

def erro_padrao(ng: dict) -> float | None:
    n, dp = ng.get("n"), ng.get("dp")
    return dp / math.sqrt(n) if (n and n > 1 and dp) else None


def veredicto(ng_nosso: dict, ng_deles: dict) -> dict | None:
    a, b = ng_nosso.get("media"), ng_deles.get("media")
    if a is None or b is None:
        return None
    dif = round(a - b, 1)
    ea, eb = erro_padrao(ng_nosso), erro_padrao(ng_deles)
    if ea is None or eb is None:
        return {"dif": dif, "ic95": None, "tipo": "indef", "txt": "amostra insuficiente"}
    ic = round(1.96 * math.sqrt(ea ** 2 + eb ** 2), 1)
    if abs(dif) <= ic:
        return {"dif": dif, "ic95": ic, "tipo": "empate", "txt": "empate técnico"}
    venceu = dif > 0
    return {"dif": dif, "ic95": ic, "tipo": "vitoria" if venceu else "derrota",
            "txt": "vitória real" if venceu else "derrota real"}


def confrontos_por_praca(cfg: dict, unidades: list) -> list:
    """Dois donos por praça: massa (mais alunos) e topo (maior nota).

    Nunca se escolhe um dos dois — são disputas de naturezas diferentes e as
    duas contam. Turma pequena no topo recebe alerta, não exclusão.
    """
    byco = {u["co"]: u for u in unidades}
    saida = []
    for p in cfg["pracas"]:
        nossa = byco.get(p["nossa"])
        if not nossa:
            # Nossa unidade sem dados 2025 (ex.: UAU fora do Censo 2025) — a
            # praça continua na tela, com a nossa linha vinda do ref2024.
            saida.append({"titulo": p["titulo"], "municipio": p["municipio"],
                          "nossa_co": p["nossa"], "nota": p.get("nota", ""),
                          "estado": "nossa_ref2024"})
            continue
        advs = [byco[c] for c in p.get("diretos", []) + p.get("adjacentes", [])
                if c in byco and (byco[c].get("nota_geral") or {}).get("media") is not None]
        item = {"titulo": p["titulo"], "municipio": p["municipio"],
                "nossa_co": p["nossa"], "nota": p.get("nota", "")}
        if not advs:
            item["estado"] = "sem_concorrente"
        else:
            eixos = {"massa": max(advs, key=lambda u: u["n_inscritos"]),
                     "topo": max(advs, key=lambda u: u["nota_geral"]["media"])}
            for eixo, adv in eixos.items():
                v = veredicto(nossa["nota_geral"], adv["nota_geral"]) or {}
                n_val = (adv.get("nota_geral") or {}).get("n") or 0
                item[eixo] = {**v, "co": adv["co"], "label": adv["label"],
                              "rede": adv["rede"], "n_inscritos": adv["n_inscritos"],
                              "n_validos": n_val, "ng": adv["nota_geral"].get("media"),
                              "seleta": n_val < N_SELETA}
            item["mesmo_dono"] = eixos["massa"]["co"] == eixos["topo"]["co"]
        saida.append(item)
    return saida


def placar(itens: list, chave: str) -> dict:
    p = {"vitoria": 0, "empate": 0, "derrota": 0}
    for it in itens:
        tipo = (it.get(chave) or {}).get("tipo")
        if tipo in p:
            p[tipo] += 1
    p["resumo"] = f"{p['vitoria']} · {p['empate']} · {p['derrota']}"
    return p


def stats_df(df: pd.DataFrame) -> dict:
    """Estatísticas completas de um conjunto de alunos (unidade ou rede)."""
    total = len(df)
    presentes_2dias = df[
        (df["TP_PRESENCA_CN"] == 1) & (df["TP_PRESENCA_CH"] == 1) &
        (df["TP_PRESENCA_LC"] == 1) & (df["TP_PRESENCA_MT"] == 1)
    ]
    r = {
        "n_inscritos": total,
        "n_presentes_2dias": len(presentes_2dias),
        "taxa_presenca_pct": round(len(presentes_2dias) / total * 100, 1) if total else 0,
        "areas": {},
    }
    for sigla in AREAS:
        presentes = df[df[f"TP_PRESENCA_{sigla}"] == 1][f"NU_NOTA_{sigla}"]
        r["areas"][sigla] = estatisticas_area(presentes)

    red = df[df["TP_STATUS_REDACAO"] == 1]
    r["redacao"] = estatisticas_area(red["NU_NOTA_REDACAO"].dropna())
    r["redacao"]["comps"] = {
        f"C{i}": round(red[f"NU_NOTA_COMP{i}"].mean(), 1) if len(red) else None
        for i in range(1, 6)
    }

    completos = presentes_2dias[presentes_2dias["TP_STATUS_REDACAO"] == 1].copy()
    if not completos.empty:
        ng = (completos["NU_NOTA_CN"] + completos["NU_NOTA_CH"] + completos["NU_NOTA_LC"]
              + completos["NU_NOTA_MT"] + completos["NU_NOTA_REDACAO"]) / 5
        r["nota_geral"] = estatisticas_area(ng)
    else:
        r["nota_geral"] = {}
    return r


def pareado_por_rede(cfg: dict, unidades: list, df_nossa: pd.DataFrame,
                     df_conc: pd.DataFrame, conc_meta: dict) -> dict:
    """Confronto simétrico: só as praças onde AS DUAS redes têm unidade com dados.

    A comparação rede-contra-rede inteira mistura praças onde não disputamos
    (o ZeroHum em Nova Friburgo, o Pensi em Campos), o que vira um efeito de
    composição: a média do concorrente é puxada por mercados que não são o
    nosso jogo. Aqui o recorte é o par de redes, e é simétrico - nossas
    unidades também entram só nas praças onde o concorrente está.

    A unidade de recorte é a praça curada em concorrencia_config.py (diretos +
    adjacentes), não a string de bairro: bairro do INEP e bairro do config não
    batem ('MEIER' x 'MÉIER') e vizinhança real ignora fronteira de bairro
    (Bangu x Realengo, Freguesia cadastrada em Jacarepaguá).
    """
    com_ng = {u["co"] for u in unidades if (u.get("nota_geral") or {}).get("n")}
    rede_de = {int(co): m["rede"] for co, m in conc_meta.items()}
    out = {}

    for rede in cfg["concorrentes"]:
        cos_rede = {co for co, r in rede_de.items() if r == rede}
        nossos, deles, pracas = {}, {}, {}
        for p in cfg["pracas"]:
            alvo = [c for c in p.get("diretos", []) + p.get("adjacentes", [])
                    if c in cos_rede and c in com_ng]
            if not alvo or p["nossa"] not in com_ng:
                continue
            pracas[p["titulo"]] = None
            nossos[p["nossa"]] = None
            deles.update((c, None) for c in alvo)

        if not nossos or not deles:
            out[rede] = {"pracas": [], "nossa": None, "deles": None}
            continue

        lado_a = stats_df(df_nossa[df_nossa["CO_ESCOLA"].isin(nossos)])
        lado_b = stats_df(df_conc[df_conc["CO_ESCOLA"].isin(deles)])
        lado_a["n_unidades"], lado_a["cos"] = len(nossos), list(nossos)
        lado_b["n_unidades"], lado_b["cos"] = len(deles), list(deles)
        out[rede] = {"pracas": list(pracas), "nossa": lado_a, "deles": lado_b,
                     "veredicto": veredicto(lado_a.get("nota_geral") or {},
                                            lado_b.get("nota_geral") or {})}

    return out


def main(marca: str, cfg: dict):
    slug = cfg["slug"]
    mapa = json.load(open(os.path.join(OUTPUT_DIR, "mapa_escola_bairro.json"), encoding="utf-8"))
    conc_meta = json.load(open(os.path.join(OUTPUT_DIR, f"concorrentes_unidades_{slug}.json"),
                               encoding="utf-8"))

    df_nossa = pd.read_csv(os.path.join(OUTPUT_DIR, f"{marca.replace(' ', '_')}_resultados.csv"),
                           dtype={"CO_ESCOLA": "Int64"})
    df_conc = pd.read_csv(os.path.join(OUTPUT_DIR, f"Concorrentes_{slug}_resultados.csv"),
                          dtype={"CO_ESCOLA": "Int64"})

    unidades = []

    # Nossas unidades (labels do mapa; travessão normalizado p/ traço simples)
    for co, grupo in df_nossa.groupby("CO_ESCOLA"):
        info = mapa.get(str(co), {})
        unidades.append({
            "co": int(co),
            "rede": marca,
            "nossa": True,
            "label": info.get("label", f"Escola {co}").replace("—", "-"),
            "municipio": info.get("municipio", ""),
            "bairro": info.get("bairro", ""),
            **stats_df(grupo),
        })

    # Unidades concorrentes
    for co, grupo in df_conc.groupby("CO_ESCOLA"):
        info = conc_meta.get(str(co))
        if info is None:
            continue
        unidades.append({
            "co": int(co),
            "rede": info["rede"],
            "nossa": False,
            "label": info["label"].replace("—", "-"),
            "municipio": info["municipio"],
            "bairro": info["bairro"],
            **stats_df(grupo),
        })

    redes = {marca: stats_df(df_nossa)}
    for rede in cfg["concorrentes"]:
        codigos = [int(co) for co, m in conc_meta.items() if m["rede"] == rede]
        redes[rede] = stats_df(df_conc[df_conc["CO_ESCOLA"].isin(codigos)])
        redes[rede]["n_unidades"] = int(df_conc[df_conc["CO_ESCOLA"].isin(codigos)]["CO_ESCOLA"].nunique())
    redes[marca]["n_unidades"] = int(df_nossa["CO_ESCOLA"].nunique())

    bench_path = os.path.join(OUTPUT_DIR, "benchmark_municipal.json")
    bench_raw = json.load(open(bench_path, encoding="utf-8")) if os.path.exists(bench_path) else {}
    # 'todas_escolas' é pesado e não é usado pela tela
    bench = {k: {kk: vv for kk, vv in v.items() if kk != "todas_escolas"}
             for k, v in bench_raw.items()}

    sem_dados = [m["label"].replace("—", "-") for m in conc_meta.values() if not m["tem_dados_2025"]]

    # Nossas unidades sem nenhum vínculo no ENEM 2025 (fora do Censo 2025)
    from config import ESCOLAS
    nossas_2025 = set(df_nossa["CO_ESCOLA"].dropna().astype(int))
    nossas_sem_dados = [mapa.get(str(co), {}).get("label", f"Escola {co}").replace("—", "-")
                        for co in ESCOLAS.get(marca, []) if co not in nossas_2025]

    pareado = pareado_por_rede(cfg, unidades, df_nossa, df_conc, conc_meta)
    pracas = confrontos_por_praca(cfg, unidades)

    saida = {
        "marca": marca,
        "redes": redes,
        "pareado": pareado,
        "pracas": pracas,
        "placar": {
            "massa": placar(pracas, "massa"),
            "topo": placar(pracas, "topo"),
            "pareado": placar([{"v": p.get("veredicto")} for p in pareado.values()], "v"),
        },
        "unidades": unidades,
        "bench_municipal": bench,
        "concorrentes_sem_dados_2025": sem_dados,
        "nossas_sem_dados_2025": nossas_sem_dados,
    }
    destino = os.path.join(OUTPUT_DIR, f"concorrencia_{slug}.json")
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)
    print(f"{len(unidades)} unidades ({sum(1 for u in unidades if u['nossa'])} nossas) -> {destino}")
    print(f"  placar massa {saida['placar']['massa']['resumo']} · "
          f"topo {saida['placar']['topo']['resumo']} · "
          f"pareado {saida['placar']['pareado']['resumo']}")
    for rede, r in redes.items():
        ng = r.get("nota_geral", {}).get("media")
        print(f"  [{rede}] {r['n_unidades']} unidades, {r['n_inscritos']} inscritos, NG {ng}")

    print("  --- confronto pareado (só praças em comum) ---")
    for rede, p in saida["pareado"].items():
        if not p["nossa"]:
            print(f"  [{rede}] sem praça em comum com dados 2025")
            continue
        a, b = p["nossa"]["nota_geral"], p["deles"]["nota_geral"]
        print(f"  [{rede}] {len(p['pracas'])} praças | {cfg['curto']} {a['media']} (n={a['n']}, "
              f"{p['nossa']['n_unidades']}u) x {b['media']} (n={b['n']}, {p['deles']['n_unidades']}u) "
              f"| dif {round(a['media'] - b['media'], 1):+}")


if __name__ == "__main__":
    marca, cfg = get_marca(sys.argv)
    main(marca, cfg)
