# Pipeline — Análise ENEM (Microdados)

Snapshot versionado do pipeline que gera os dashboards deste repositório.
Cópia de trabalho (viva) fica em `Documents\Microdados do Enem\Microdados do Enem 2025\ANALISE\`.

> **Não versionado** (tamanho): microdados `DADOS\*.csv` (~2 GB/ano), `output\*.html` e
> `output\*.csv`. Aqui ficam só os **scripts** e os **JSONs históricos** (pequenos).

## Fluxo

```
config.py                      # ESCOLAS por marca (CO_ESCOLA do INEP) + caminhos
run_all.py → 01..04            # extrai → estatísticas → benchmarks → relatório Excel
06_concorrentes_ranking.py     # concorrentes por bairro/município (BENCH_BAIRRO)
05_gerar_dashboards.py         # gera output/{Marca}_Dashboard.html a partir do template
   └─ chama 08 ao final        # _aplicar_historico()
08_historico_secao.py          # injeta a seção "Evolução Histórica" em cada dashboard
```

`05` lê o template **pristino** `output/_template_base.html` (não versionado) e, no fim,
chama `08`, que lê o `DADOS` injetado, mapeia CO→nome pelas médias de 2025 e adiciona a
seção histórica (com seletor de município nas marcas multi-município).

## Dados históricos (2021–2025) — estáticos

`historico/*.json` são calculados **uma vez** (só re-rodar quando chegar um ENEM novo):

- `hist_local.py` — varre os 5 anos (2021–2025) e agrega rede privada por município/UF/Brasil
  + médias por unidade (CO_ESCOLA). Gera `historico_benchmark.json` e `historico_unidades.json`.
- `top100_calib.py` — calibra e calcula `historico_top100.json` (média das 100 melhores
  escolas; rede privada, mín. 30 participantes/área), reproduzindo o TOPTIERS 2025.

**Trava do INEP:** `CO_ESCOLA` não existe em 2021–2023 (só 2024–2025). Por isso a série
**por escola/marca** cobre só 2024–2025; a de **mercado** (município/UF/Brasil) cobre 2021–2025.

## Geradores da seção histórica

- `08_historico_secao.py` — usado **pelo pipeline** (mira `output/{Marca}_Dashboard.html`).
- `gen_hist.py` — variante standalone que mira os HTMLs **deste repo de deploy**
  (`apogeu.html`, etc.). Mesma lógica.

Fontes históricas (microdados 2021–2024) ficam em `Documents\Microdados do Enem\Microdados do Enem 20XX\`.
