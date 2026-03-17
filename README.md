# Dashboard - NDF MtM Monthly Variations

Dashboard em Streamlit para visualizar variacoes mensais de MtM de NDF, com foco em Holdings e opcao de abertura por `book`.

## 1) Objetivo de calculo

A logica considera que a posicao de MtM e revertida no dia seguinte.
Por isso, o efeito diario realizado e tratado como:

`daily_delta = MtM_dia_atual - MtM_dia_anterior`

Depois, para cada mes:

`monthly_delta_effect = soma(daily_delta no mes)`

E a variacao mes contra mes:

`mom_variation = monthly_delta_effect_mes_atual - monthly_delta_effect_mes_anterior`

## 2) SQL base (ajuste datas conforme necessario)

```sql
SELECT
  to_date(file_datetime) AS reference_date,
  processing_org_full_name,
  book,
  product_description,
  product_currency,
  position_id,
  quantity,
  notional,
  market_value,
  npv,
  accrual_bo,
  total_accrual,
  product_type,
  product_subtype
FROM br__dataset.calypso_positions_report_bonds_latest
WHERE (product_type = 'FXNDF' OR product_subtype = 'FXNDF')
  AND to_date(file_datetime) BETWEEN DATE '2025-01-01' AND DATE '2025-12-31';
```

Exporte o resultado para CSV ou Parquet e carregue no app.

## 3) Rodar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 4) Recursos do dashboard

- Paleta roxa inspirada no Nubank
- Selecao da coluna base de MtM (`market_value` ou `npv`)
- Filtro por `processing_org_full_name`
- Filtro por `book`
- Opcao de visualizar consolidado total ou com abertura por `book`
- Graficos de:
  - efeito delta mensal
  - variacao MoM do efeito delta mensal
- Tabelas de detalhe diario e mensal
