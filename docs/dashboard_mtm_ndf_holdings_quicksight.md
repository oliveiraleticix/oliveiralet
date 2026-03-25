# Dashboard MTM NDF Holdings por Book (QuickSight)

## 1) Objetivo

Disponibilizar no QuickSight uma visao mensal de MTM das NDFs de Holdings por `book`, com:

- filtro de mes (`month_label`);
- variacao mensal (`mtm_variation_mom`);
- variacao YTD (`mtm_variation_ytd`);
- atualizacao automatica a cada fechamento mensal (ultimo dia util com dados).

## 2) Fonte de dados

A view base foi criada em:

- `usr.market_risk.vw_mtm_ndf_holdings_book_monthly`

Script de criacao:

- `databricks/mtm_ndf_holdings_quicksight.sql`

Essa view:

1. Le dados de `usr.market_risk.pricing_consolidated_holdings_v2` (source = `ndf`, instrumento `FXNDF%`);
2. Enriquecimento de `book` via `br__dataset.calypso_positions_report_bonds_latest`;
3. Seleciona automaticamente o ultimo `base_date` disponivel de cada mes;
4. Mantem seed historico de dez/2025 (baseline validado);
5. Calcula metricas de MoM e YTD por `book`.

## 3) Dicionario de colunas (dataset pronto para BI)

- `snapshot_date`: data de fechamento efetiva (ultimo dia com dado no mes);
- `month_ref`: primeiro dia do mes de referencia (date);
- `month_label`: mes em formato `YYYY-MM` (ideal para filtro);
- `year_ref`: ano;
- `month_num`: numero do mes;
- `book`: estrategia/book de hedge;
- `mtm_month`: MTM consolidado do mes para o book;
- `mtm_prev_month`: MTM do mes anterior para o mesmo book;
- `mtm_variation_mom`: variacao mensal (`mtm_month - mtm_prev_month`);
- `mtm_first_month_year`: MTM do primeiro fechamento do ano para o book;
- `mtm_variation_ytd`: variacao YTD (`mtm_month - mtm_first_month_year`).

## 4) Como criar o dataset no QuickSight

1. `New dataset` -> selecione a conexao da camada SQL (Athena/Trino/Databricks SQL, conforme ambiente).
2. Escolha a view `usr.market_risk.vw_mtm_ndf_holdings_book_monthly`.
3. Use SPICE para performance (recomendado).
4. Valide os tipos:
   - `snapshot_date` e `month_ref` como Date;
   - `month_label` como String;
   - medidas de MTM como Decimal.

## 5) Sugestao de analise/dashboard

Visuais recomendados:

1. **Tabela por book**
   - Linhas: `book`
   - Colunas/medidas: `mtm_month`, `mtm_variation_mom`, `mtm_variation_ytd`
2. **Linha temporal**
   - Eixo X: `snapshot_date`
   - Valor: `mtm_month`
   - Cor: `book`
3. **KPI cards**
   - Soma de `mtm_month`
   - Soma de `mtm_variation_mom`
   - Soma de `mtm_variation_ytd`

Filtros:

- `month_label` (single-select ou multi-select);
- `book` (multi-select).

## 6) Atualizacao automatica (fechamento mensal)

### Opcao recomendada (simples)

- Agendar **refresh mensal do SPICE** para o dia 1 do mes (ex.: 07:00 America/Sao_Paulo).

Motivo:

- A view ja pega o ultimo dia com dado no mes anterior, entao no dia 1 o fechamento normalmente ja esta estabilizado.

### Opcao estrita de calendario util

Se for obrigatorio executar no ultimo dia util do mes:

1. Criar um job externo (ex.: Databricks Job, Airflow, Lambda) com calendario de negocio;
2. Esse job chama API do QuickSight para iniciar ingestion do dataset;
3. Alternativamente, manter refresh diario (baixo risco operacional) e usar apenas o `snapshot_date` maximo por mes na analise.

## 7) Query de validacao rapida

```sql
SELECT
  month_label,
  book,
  mtm_month,
  mtm_variation_mom,
  mtm_variation_ytd
FROM usr.market_risk.vw_mtm_ndf_holdings_book_monthly
ORDER BY snapshot_date DESC, book;
```

## 8) Observacoes

- O seed de dez/2025 esta fixo por desenho para manter continuidade historica inicial.
- Caso seja necessario remover o seed no futuro, basta retirar o CTE `seed_dez_2025`.
- Se algum `book` nao tiver registro em determinado fechamento, a view retorna `mtm_month = 0` para manter comparabilidade de serie.
