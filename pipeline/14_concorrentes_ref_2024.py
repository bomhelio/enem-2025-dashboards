"""
14_concorrentes_ref_2024.py [marca]
Referência ENEM 2024 para unidades concorrentes SEM dados em 2025
(ex.: Elite Caxias/SJM, ZeroHum Galeão - recadastramentos e turmas
concentradas). A tela mostra os números de 2024 nas praças vazias.

Uso: python 14_concorrentes_ref_2024.py "QI Bilíngue"   (default: Matriz Educação)
Saída: output/concorrencia_ref2024_{slug}.json
"""

import importlib
import json
import os
import sys
import pandas as pd

from config import BASE_DIR, OUTPUT_DIR, CSV_SEP, CSV_ENCODING, CHUNK_SIZE
from concorrencia_config import get_marca

RESULTADOS_2024 = os.path.join(os.path.dirname(BASE_DIR), "Microdados do Enem 2024",
                               "DADOS", "RESULTADOS_2024.csv")

extrair11 = importlib.import_module("11_concorrentes_extrair")
analise12 = importlib.import_module("12_analise_concorrencia")


def main(marca: str, cfg: dict):
    slug = cfg["slug"]
    meta = json.load(open(os.path.join(OUTPUT_DIR, f"concorrentes_unidades_{slug}.json"),
                          encoding="utf-8"))
    alvo = {int(co) for co, m in meta.items() if not m["tem_dados_2025"]}

    # NOSSAS unidades sem 2025 (caso UAU: escola fora do Censo 2025 não recebe
    # vínculo nenhum no ENEM 2025 — a tela mostra a última foto, ENEM 2024).
    from config import ESCOLAS
    mapa = json.load(open(os.path.join(OUTPUT_DIR, "mapa_escola_bairro.json"), encoding="utf-8"))
    df_nossa = pd.read_csv(os.path.join(OUTPUT_DIR, f"{marca.replace(' ', '_')}_resultados.csv"),
                           dtype={"CO_ESCOLA": "Int64"})
    nossas_2025 = set(df_nossa["CO_ESCOLA"].dropna().astype(int))
    nossas_sem_2025 = {co for co in ESCOLAS.get(marca, []) if co not in nossas_2025}
    alvo |= nossas_sem_2025

    destino = os.path.join(OUTPUT_DIR, f"concorrencia_ref2024_{slug}.json")
    if not alvo:
        json.dump({}, open(destino, "w", encoding="utf-8"))
        print("Nenhuma unidade sem dados 2025 - referência vazia.")
        return

    print(f"[{marca}] Varrendo {RESULTADOS_2024} para {len(alvo)} código(s) "
          f"({len(nossas_sem_2025)} nossos)...")
    partes = []
    for chunk in pd.read_csv(RESULTADOS_2024, sep=CSV_SEP, encoding=CSV_ENCODING,
                             usecols=extrair11.COLUNAS_UTEIS, dtype={"CO_ESCOLA": "Int64"},
                             chunksize=CHUNK_SIZE):
        f = chunk[chunk["CO_ESCOLA"].isin(alvo)]
        if not f.empty:
            partes.append(f)

    ref = {}
    if partes:
        df = pd.concat(partes, ignore_index=True)
        for co, grupo in df.groupby("CO_ESCOLA"):
            co = int(co)
            s = analise12.stats_df(grupo)
            if co in nossas_sem_2025:
                m = mapa.get(str(co), {})
                base = {"label": m.get("label", f"Escola {co}").replace("—", "-"),
                        "municipio": m.get("municipio", ""), "rede": marca, "nossa": True}
            else:
                m = meta[str(co)]
                base = {"label": m["label"].replace("—", "-"), "municipio": m["municipio"],
                        "rede": m.get("rede"), "nossa": False}
            ref[str(co)] = {
                **base,
                "n_inscritos": s["n_inscritos"],
                "ng": (s.get("nota_geral") or {}).get("media"),
                "mt": (s["areas"].get("MT") or {}).get("media"),
                "rd": s["redacao"].get("media"),
            }

    with open(destino, "w", encoding="utf-8") as f:
        json.dump(ref, f, ensure_ascii=False, indent=2)
    print(f"{len(ref)} unidade(s) com dados 2024 -> {destino}")
    for co, r in ref.items():
        print(f"  {r['label']:32s} n={r['n_inscritos']:3d}  NG={r['ng']}  MT={r['mt']}  RD={r['rd']}")


if __name__ == "__main__":
    marca, cfg = get_marca(sys.argv)
    main(marca, cfg)
