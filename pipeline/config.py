import os

# ──────────────────────────────────────────────────────────────────────────────
# Preencher com os códigos INEP de cada escola (CO_ESCOLA em RESULTADOS_2025.csv)
# Uma escola pode ter múltiplas unidades → liste todos os códigos da marca.
# ──────────────────────────────────────────────────────────────────────────────
ESCOLAS: dict[str, list[int]] = {
    # Apogeu inclui Apogeu Global School (Cidade Alta + Ferreira Guimarães)
    "Apogeu":          [31317101, 31356816, 31256285, 31380024, 31363383],
    # Qi Valqueire sem código INEP — não entra na análise
    "QI Bilíngue":     [33135924, 33071721, 33156026, 33199400, 33124418, 33143331, 33187924],
    # Retiro dos Artistas e Tijuca sem código INEP — não entram na análise
    "Matriz Educação": [33187789, 33183368, 33048185, 33197466, 33187762, 33192685, 33190674, 33187770],
    "União":                    [43162703],
    "Unificado":                [43214754],
    "Americano":                [43107524],
    "Colégio Leonardo da Vinci": [43172423, 43172440, 43213278],
    "Cubo Global":              [33178828, 33186260],
}

# ──────────────────────────────────────────────────────────────────────────────
# Caminhos
# ──────────────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR   = os.path.join(BASE_DIR, "DADOS")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

RESULTADOS_CSV   = os.path.join(DATA_DIR, "RESULTADOS_2025.csv")
PARTICIPANTES_CSV = os.path.join(DATA_DIR, "PARTICIPANTES_2025.csv")

# ──────────────────────────────────────────────────────────────────────────────
# Parâmetros de leitura dos CSVs do INEP
# ──────────────────────────────────────────────────────────────────────────────
CSV_SEP      = ";"
CSV_ENCODING = "latin-1"
CHUNK_SIZE   = 200_000   # linhas por chunk ao varrer o arquivo de 2 GB

# Limites para % acima (análise quantitativa)
CORTES_NOTA = [500, 600, 700, 800]
