"""
02_quantitativo.py
Calcula estatísticas por escola e por marca a partir dos arquivos extraídos
por 01_extrair.py.

Retorna um dict com os resultados consolidados (também salvo em output/).
"""

import os
import numpy as np
import pandas as pd
from config import ESCOLAS, OUTPUT_DIR, CORTES_NOTA

AREAS = {
    "CN": "Ciências da Natureza",
    "CH": "Ciências Humanas",
    "LC": "Linguagens e Códigos",
    "MT": "Matemática",
}
COMPS_REDACAO = {
    1: "Domínio da Língua Escrita",
    2: "Compreensão da Proposta",
    3: "Seleção de Argumentos",
    4: "Mecanismos de Coesão",
    5: "Proposta de Intervenção",
}


def _nota_col(area: str) -> str:
    return f"NU_NOTA_{area}"

def _presenca_col(area: str) -> str:
    return f"TP_PRESENCA_{area}"


def estatisticas_area(serie: pd.Series) -> dict:
    s = serie.dropna()
    if s.empty:
        return {}
    stats = {
        "n":      len(s),
        "media":  round(s.mean(), 1),
        "mediana": round(s.median(), 1),
        "dp":     round(s.std(), 1),
        "min":    round(s.min(), 1),
        "max":    round(s.max(), 1),
        "p25":    round(s.quantile(0.25), 1),
        "p75":    round(s.quantile(0.75), 1),
        "p90":    round(s.quantile(0.90), 1),
    }
    for corte in CORTES_NOTA:
        stats[f"pct_acima_{corte}"] = round((s >= corte).mean() * 100, 1)
    return stats


def analisar_marca(marca: str) -> dict | None:
    caminho = os.path.join(OUTPUT_DIR, f"{marca.replace(' ', '_')}_resultados.csv")
    if not os.path.exists(caminho):
        print(f"  [{marca}] Arquivo não encontrado: {caminho}")
        return None

    df = pd.read_csv(caminho, dtype={"CO_ESCOLA": "Int64"})
    total = len(df)

    # Presença nos 2 dias: todos presentes (TP_PRESENCA = 1) em todas as 4 provas
    presentes_2dias = df[
        (df["TP_PRESENCA_CN"] == 1) &
        (df["TP_PRESENCA_CH"] == 1) &
        (df["TP_PRESENCA_LC"] == 1) &
        (df["TP_PRESENCA_MT"] == 1)
    ]
    n_presentes = len(presentes_2dias)

    resultado: dict = {
        "marca": marca,
        "n_inscritos": total,
        "n_presentes_2dias": n_presentes,
        "taxa_presenca_pct": round(n_presentes / total * 100, 1) if total > 0 else 0,
        "areas": {},
        "redacao": {},
        "nota_geral": {},
        "unidades": df["CO_ESCOLA"].nunique(),
        "estados": sorted(df["SG_UF_ESC"].dropna().unique().tolist()),
    }

    # Análise por área
    for sigla in AREAS:
        presentes_area = df[df[_presenca_col(sigla)] == 1][_nota_col(sigla)]
        resultado["areas"][sigla] = estatisticas_area(presentes_area)

    # Redação
    redacao_valida = df[df["TP_STATUS_REDACAO"] == 1]
    n_redacao = len(redacao_valida)
    n_faltou_redacao = (df["TP_STATUS_REDACAO"].isna() | (df["TP_PRESENCA_LC"] != 1)).sum()
    n_anulada = (df["TP_STATUS_REDACAO"].isin([2, 3, 4, 5, 6, 7])).sum()

    comp_stats = {}
    for num in range(1, 6):
        col = f"NU_NOTA_COMP{num}"
        comp_stats[f"comp{num}"] = {
            "nome": COMPS_REDACAO[num],
            **estatisticas_area(redacao_valida[col]),
        }

    # Distribuição por faixa (nota total redação)
    notas_red = redacao_valida["NU_NOTA_REDACAO"].dropna()
    faixas = {}
    for faixa in [0, 200, 400, 600, 800, 1000]:
        if faixa < 1000:
            cnt = ((notas_red >= faixa) & (notas_red < faixa + 200)).sum()
        else:
            cnt = (notas_red == 1000).sum()
        faixas[f"{faixa}-{faixa+200 if faixa < 1000 else 1000}"] = int(cnt)

    resultado["redacao"] = {
        "n_validas": n_redacao,
        "pct_nota_zero_anulada": round((n_anulada / total * 100), 1) if total > 0 else 0,
        "competencias": comp_stats,
        "distribuicao_faixas": faixas,
        **estatisticas_area(notas_red),
    }

    # Nota geral = média das 5 áreas (apenas presença completa + redação válida)
    df_completo = presentes_2dias[presentes_2dias["TP_STATUS_REDACAO"] == 1].copy()
    if not df_completo.empty:
        df_completo["NOTA_GERAL"] = (
            df_completo["NU_NOTA_CN"] +
            df_completo["NU_NOTA_CH"] +
            df_completo["NU_NOTA_LC"] +
            df_completo["NU_NOTA_MT"] +
            df_completo["NU_NOTA_REDACAO"]
        ) / 5
        resultado["nota_geral"] = estatisticas_area(df_completo["NOTA_GERAL"])
        resultado["nota_geral"]["n_completos"] = len(df_completo)

    return resultado


def analisar_todas() -> dict:
    resultados = {}
    for marca in ESCOLAS:
        print(f"  Analisando {marca}...")
        r = analisar_marca(marca)
        if r:
            resultados[marca] = r
    return resultados


if __name__ == "__main__":
    import json
    res = analisar_todas()
    destino = os.path.join(OUTPUT_DIR, "analise_quantitativa.json")
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print(f"\nResultados salvos em: {destino}")
