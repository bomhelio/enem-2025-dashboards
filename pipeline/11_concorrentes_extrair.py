"""
11_concorrentes_extrair.py
Varre RESULTADOS_2025.csv (2 GB) e extrai os microdados das unidades dos
CONCORRENTES mapeados (piloto: Elite e Santa Mônica, concorrentes diretos
da Matriz Educação). Mesmas colunas do 01_extrair.py → estatísticas
comparáveis 1:1 com as nossas marcas.

Saídas em output/:
  - Concorrentes_resultados.csv   (linhas de todos os concorrentes)
  - concorrentes_unidades.json    (metadados: rede, label, município, bairro)

Editar CONCORRENTES para adicionar/remover unidades (fonte: Censo Escolar
Tabela_Escola_2025.csv, TP_DEPENDENCIA=4).
"""

import json
import os
import pandas as pd
from config import RESULTADOS_CSV, OUTPUT_DIR, CSV_SEP, CSV_ENCODING, CHUNK_SIZE

COLUNAS_UTEIS = [
    "NU_SEQUENCIAL", "CO_ESCOLA", "CO_MUNICIPIO_ESC", "NO_MUNICIPIO_ESC",
    "CO_UF_ESC", "SG_UF_ESC", "TP_DEPENDENCIA_ADM_ESC", "TP_LOCALIZACAO_ESC",
    "CO_MUNICIPIO_PROVA", "NO_MUNICIPIO_PROVA", "CO_UF_PROVA", "SG_UF_PROVA",
    "TP_PRESENCA_CN", "TP_PRESENCA_CH", "TP_PRESENCA_LC", "TP_PRESENCA_MT",
    "NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC", "NU_NOTA_MT",
    "TP_LINGUA",
    "TP_STATUS_REDACAO",
    "NU_NOTA_COMP1", "NU_NOTA_COMP2", "NU_NOTA_COMP3", "NU_NOTA_COMP4", "NU_NOTA_COMP5",
    "NU_NOTA_REDACAO",
]

# rede -> {CO_ESCOLA: {label, municipio, bairro}}
CONCORRENTES: dict[str, dict[int, dict]] = {
    "Elite": {
        33520321: {"label": "Campo Grande I",      "municipio": "Rio de Janeiro",     "bairro": "CAMPO GRANDE"},
        33520330: {"label": "Campo Grande II",     "municipio": "Rio de Janeiro",     "bairro": "SENADOR VASCONCELOS"},
        33169713: {"label": "Taquara",             "municipio": "Rio de Janeiro",     "bairro": "TAQUARA"},
        33159130: {"label": "Bangu",               "municipio": "Rio de Janeiro",     "bairro": "BANGU"},
        33122245: {"label": "Realengo",            "municipio": "Rio de Janeiro",     "bairro": "REALENGO"},
        33140626: {"label": "Madureira 1",         "municipio": "Rio de Janeiro",     "bairro": "MADUREIRA"},
        33149780: {"label": "Madureira 2",         "municipio": "Rio de Janeiro",     "bairro": "MADUREIRA"},
        33531218: {"label": "Madureira 3",         "municipio": "Rio de Janeiro",     "bairro": "MADUREIRA"},
        33162999: {"label": "Norte Shopping",      "municipio": "Rio de Janeiro",     "bairro": "CACHAMBI"},
        33152276: {"label": "Tijuca",              "municipio": "Rio de Janeiro",     "bairro": "TIJUCA"},
        33193649: {"label": "Irajá",               "municipio": "Rio de Janeiro",     "bairro": "IRAJA"},
        33193720: {"label": "Guadalupe",           "municipio": "Rio de Janeiro",     "bairro": "GUADALUPE"},
        33195757: {"label": "Bonsucesso",          "municipio": "Rio de Janeiro",     "bairro": "BONSUCESSO"},
        33172331: {"label": "Ilha do Governador",  "municipio": "Rio de Janeiro",     "bairro": "JARDIM GUANABARA"},
        33125228: {"label": "Santa Cruz",          "municipio": "Rio de Janeiro",     "bairro": "SANTA CRUZ"},
        33526249: {"label": "Vila Valqueire",      "municipio": "Rio de Janeiro",     "bairro": "VILA VALQUEIRE"},
        33173850: {"label": "Duque de Caxias",     "municipio": "Duque de Caxias",    "bairro": "CENTRO"},
        33060355: {"label": "Iguaçuano",           "municipio": "Nova Iguaçu",        "bairro": "CENTRO"},
        33526214: {"label": "Nova Iguaçu (Luz)",   "municipio": "Nova Iguaçu",        "bairro": "DA LUZ"},
        33176752: {"label": "São João de Meriti",  "municipio": "São João de Meriti", "bairro": "CENTRO"},
        33182884: {"label": "Nilópolis",           "municipio": "Nilópolis",          "bairro": "NILOPOLIS"},
        33195978: {"label": "Itaguaí",             "municipio": "Itaguaí",            "bairro": "PROGRESSO"},
        33139032: {"label": "São Gonçalo",         "municipio": "São Gonçalo",        "bairro": "CENTRO"},
        33184844: {"label": "Três Rios",           "municipio": "Três Rios",          "bairro": "CENTRO"},
    },
    "ZeroHum": {
        33185476: {"label": "Centro",              "municipio": "Rio de Janeiro",     "bairro": "CENTRO"},
        33193495: {"label": "Maracanã",            "municipio": "Rio de Janeiro",     "bairro": "MARACANA"},
        33067821: {"label": "Vila Isabel",         "municipio": "Rio de Janeiro",     "bairro": "VILA ISABEL"},
        33105138: {"label": "Méier",               "municipio": "Rio de Janeiro",     "bairro": "MEIER"},
        33197350: {"label": "Madureira",           "municipio": "Rio de Janeiro",     "bairro": "MADUREIRA"},
        33394202: {"label": "Olaria",              "municipio": "Rio de Janeiro",     "bairro": "OLARIA"},
        33183155: {"label": "Galeão",              "municipio": "Rio de Janeiro",     "bairro": "GALEAO"},
        33202850: {"label": "Ilha do Governador",  "municipio": "Rio de Janeiro",     "bairro": "GALEAO"},
        33187681: {"label": "Nova Iguaçu",         "municipio": "Nova Iguaçu",        "bairro": "CENTRO"},
        33198926: {"label": "Da Prata",            "municipio": "Nova Iguaçu",        "bairro": "VILA CATIA"},
        33200572: {"label": "S. J. de Meriti",     "municipio": "São João de Meriti", "bairro": "JARDIM JOSE BONIFACIO"},
        33185700: {"label": "Jardim Metrópole",    "municipio": "São João de Meriti", "bairro": "JARDIM METROPOLE"},
        33193444: {"label": "Nilópolis",           "municipio": "Nilópolis",          "bairro": "CENTRO"},
        33199949: {"label": "Belford Roxo",        "municipio": "Belford Roxo",       "bairro": "CENTRO"},
        33176787: {"label": "Niterói Centro",      "municipio": "Niterói",            "bairro": "CENTRO"},
        33055416: {"label": "Icaraí",              "municipio": "Niterói",            "bairro": "ICARAI"},
        33193991: {"label": "Itaipu",              "municipio": "Niterói",            "bairro": "ITAIPU"},
        33179301: {"label": "São Gonçalo",         "municipio": "São Gonçalo",        "bairro": "PARAISO"},
        33180660: {"label": "Alcântara",           "municipio": "São Gonçalo",        "bairro": "ALCANTARA"},
        33186928: {"label": "Maricá Centro",       "municipio": "Maricá",             "bairro": "CENTRO"},
        33203130: {"label": "Maricá Barroco",      "municipio": "Maricá",             "bairro": "BARROCO"},
        33166951: {"label": "Araruama",            "municipio": "Araruama",           "bairro": "CENTRO"},
        33184666: {"label": "Cabo Frio",           "municipio": "Cabo Frio",          "bairro": "PARQUE RIVIERA"},
        33196826: {"label": "Itaboraí",            "municipio": "Itaboraí",           "bairro": "CENTRO"},
        33021678: {"label": "Nova Friburgo",       "municipio": "Nova Friburgo",      "bairro": "CORDOEIRA"},
        33200068: {"label": "Volta Redonda",       "municipio": "Volta Redonda",      "bairro": "VILA SANTA CECILIA"},
    },
    "Santa Mônica": {
        33113114: {"label": "Campo Grande",        "municipio": "Rio de Janeiro",     "bairro": "CAMPO GRANDE"},
        33111642: {"label": "Taquara (Colégio)",   "municipio": "Rio de Janeiro",     "bairro": "TAQUARA"},
        33173907: {"label": "Taquara (Rede)",      "municipio": "Rio de Janeiro",     "bairro": "TAQUARA"},
        33094861: {"label": "Madureira",           "municipio": "Rio de Janeiro",     "bairro": "MADUREIRA"},
        33071926: {"label": "Cachambi",            "municipio": "Rio de Janeiro",     "bairro": "CACHAMBI"},
        33075581: {"label": "Cascadura",           "municipio": "Rio de Janeiro",     "bairro": "CASCADURA"},
        33075603: {"label": "Bento Ribeiro A",     "municipio": "Rio de Janeiro",     "bairro": "BENTO RIBEIRO"},
        33075620: {"label": "Bento Ribeiro B",     "municipio": "Rio de Janeiro",     "bairro": "BENTO RIBEIRO"},
        33088519: {"label": "Bonsucesso",          "municipio": "Rio de Janeiro",     "bairro": "BONSUCESSO"},
        33085609: {"label": "Ilha do Governador",  "municipio": "Rio de Janeiro",     "bairro": "JARDIM GUANABARA"},
        33084262: {"label": "Santa Cruz",          "municipio": "Rio de Janeiro",     "bairro": "SANTA CRUZ"},
        33148937: {"label": "Freguesia",           "municipio": "Rio de Janeiro",     "bairro": "FREGUESIA"},
        33160031: {"label": "Recreio",             "municipio": "Rio de Janeiro",     "bairro": "RECREIO"},
        33100985: {"label": "Barra da Tijuca",     "municipio": "Rio de Janeiro",     "bairro": "BARRA DA TIJUCA"},
        33139458: {"label": "Duque de Caxias",     "municipio": "Duque de Caxias",    "bairro": "JARDIM ANHANGA"},
        33185000: {"label": "Liceu (N. Iguaçu)",   "municipio": "Nova Iguaçu",        "bairro": "KENNEDY"},
        33197946: {"label": "Nilópolis",           "municipio": "Nilópolis",          "bairro": "CENTRO"},
        33115478: {"label": "Maricá",              "municipio": "Maricá",             "bairro": "CENTRO"},
        33089825: {"label": "São Gonçalo",         "municipio": "São Gonçalo",        "bairro": "MUTUA"},
        33112657: {"label": "Seropédica",          "municipio": "Seropédica",         "bairro": "PIRANEMA"},
    },
}


def _todos_codigos() -> set[int]:
    codigos: set[int] = set()
    for unidades in CONCORRENTES.values():
        codigos.update(unidades)
    return codigos


def extrair():
    codigos_alvo = _todos_codigos()
    n_unidades = sum(len(u) for u in CONCORRENTES.values())
    print(f"Varrendo {RESULTADOS_CSV} ...")
    print(f"  Buscando {n_unidades} unidade(s) de {len(CONCORRENTES)} rede(s) concorrente(s)")

    partes: list[pd.DataFrame] = []
    total_lido = 0
    for chunk in pd.read_csv(
        RESULTADOS_CSV,
        sep=CSV_SEP,
        encoding=CSV_ENCODING,
        usecols=COLUNAS_UTEIS,
        dtype={"CO_ESCOLA": "Int64"},
        chunksize=CHUNK_SIZE,
    ):
        total_lido += len(chunk)
        filtrado = chunk[chunk["CO_ESCOLA"].isin(codigos_alvo)]
        if not filtrado.empty:
            partes.append(filtrado)
        print(f"  Lidos {total_lido:,} registros...", end="\r")

    print(f"\nTotal lido: {total_lido:,} registros.")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df = pd.concat(partes, ignore_index=True)
    destino = os.path.join(OUTPUT_DIR, "Concorrentes_resultados.csv")
    df.to_csv(destino, index=False, encoding="utf-8")

    encontrados = set(df["CO_ESCOLA"].unique().tolist())
    meta = {}
    for rede, unidades in CONCORRENTES.items():
        for co, info in unidades.items():
            meta[str(co)] = {
                "rede": rede,
                "label": f"{rede} - {info['label']}",
                "municipio": info["municipio"],
                "bairro": info["bairro"],
                "tem_dados_2025": co in encontrados,
                "n_inscritos": int((df["CO_ESCOLA"] == co).sum()),
            }
    destino_meta = os.path.join(OUTPUT_DIR, "concorrentes_unidades.json")
    with open(destino_meta, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    com_dados = sum(1 for m in meta.values() if m["tem_dados_2025"])
    print(f"  {len(df):,} inscritos em {com_dados}/{n_unidades} unidades -> {destino}")
    sem = [m["label"] for m in meta.values() if not m["tem_dados_2025"]]
    if sem:
        print(f"  Sem dados 2025: {', '.join(sem)}")


if __name__ == "__main__":
    extrair()
