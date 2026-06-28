"""
run_all.py
Orquestrador principal. Rode este script após preencher os códigos INEP em config.py.

Etapas:
  1. Extrai dados por escola (varre 2 GB)
  2. Calcula estatísticas quantitativas
  3. Calcula benchmarks nacionais / rede privada (varre 2 GB novamente)
  4. Gera relatório Excel

Tempo estimado: 10–20 minutos dependendo do hardware.
"""

import os
import sys
import time
import subprocess

ANALISE_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable

def _checar_config():
    sys.path.insert(0, ANALISE_DIR)
    from config import ESCOLAS
    vazias = [m for m, c in ESCOLAS.items() if not c]
    if vazias:
        print("ATENÇÃO: As seguintes marcas não têm códigos INEP configurados em config.py:")
        for m in vazias:
            print(f"  - {m}")
        print("\nEdite config.py, preencha ESCOLAS e rode novamente.")
        sys.exit(1)

def _rodar(script: str, descricao: str):
    print(f"\n{'='*60}")
    print(f"  {descricao}")
    print(f"{'='*60}")
    caminho = os.path.join(ANALISE_DIR, script)
    result = subprocess.run([PYTHON, caminho], cwd=ANALISE_DIR)
    if result.returncode != 0:
        print(f"\nERRO: {script} terminou com código {result.returncode}. Interrompendo.")
        sys.exit(result.returncode)

def main():
    _checar_config()
    inicio = time.time()

    _rodar("01_extrair.py",    "PASSO 1: Extraindo dados por escola (varre 2 GB)")
    _rodar("02_quantitativo.py","PASSO 2: Calculando estatísticas quantitativas")
    _rodar("03_benchmark.py",  "PASSO 3: Calculando benchmarks nacionais")
    _rodar("04_relatorio.py",  "PASSO 4: Gerando relatório Excel")

    minutos = (time.time() - inicio) / 60
    from config import OUTPUT_DIR
    print(f"\n{'='*60}")
    print(f"  CONCLUÍDO em {minutos:.1f} minutos")
    print(f"  Saída em: {OUTPUT_DIR}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
