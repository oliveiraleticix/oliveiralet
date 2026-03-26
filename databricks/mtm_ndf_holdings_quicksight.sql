-- Dataset base para dashboard de MTM NDF Holdings por book (QuickSight).
-- Dialeto: Trino/Athena (funciona em Databricks SQL com pequenos ajustes de funcoes de data).
--
-- Objetivo:
-- 1) consolidar MTM mensal por book no fechamento (ultimo base_date disponivel de cada mes);
-- 2) manter seed historico validado para dez/2025;
-- 3) entregar metricas prontas para dashboard: variacao MoM e variacao YTD.

CREATE OR REPLACE VIEW usr.market_risk.vw_mtm_ndf_holdings_book_monthly AS
WITH seed_dez_2025 AS (
  -- Seed historico para manter continuidade dos numeros ja validados.
  SELECT DATE '2025-12-31' AS snapshot_date, 'NU HOLDINGS INVOICES HEDGE BOOK' AS book, -944277.72 AS mtm_value UNION ALL
  SELECT DATE '2025-12-31', 'NU HOLDINGS RSU HEDGE BOOK', -799121.58 UNION ALL
  SELECT DATE '2025-12-31', 'NU HOLDINGS RSU HEDGE BOOK', -180908.38 UNION ALL
  SELECT DATE '2025-12-31', 'NU HOLDINGS RSU HEDGE BOOK', -8826.75 UNION ALL
  SELECT DATE '2025-12-31', 'NU HOLDINGS RSU HEDGE BOOK', 3598.17 UNION ALL
  SELECT DATE '2025-12-31', 'NU HOLDINGS RSU HEDGE BOOK', 8719.57 UNION ALL
  SELECT DATE '2025-12-31', 'NU HOLDINGS RSU HEDGE BOOK', 3940088.20 UNION ALL
  SELECT DATE '2025-12-31', 'NU HOLDINGS HEDGE BOOK', 8457201.23 UNION ALL
  SELECT DATE '2025-12-31', 'NU HOLDINGS HEDGE BOOK', 8584534.82
),
raw_ndf AS (
  SELECT
    b1.base_date,
    b2.book,
    b1.mtm AS mtm_value
  FROM usr.market_risk.pricing_consolidated_holdings_v2 b1
  LEFT JOIN br__dataset.calypso_positions_report_bonds_latest b2
    ON  b1.base_date = b2.reference_date
    AND b1.instrumento = b2.product_description
    AND CAST(regexp_substr(b1.id_posicao, '[0-9]+') AS BIGINT) = b2.position_id
  WHERE LOWER(b1.source) = 'ndf'
    AND b1.instrumento LIKE 'FXNDF%'
    AND b2.book IS NOT NULL
),
month_close_dates AS (
  -- "Fechamento mensal" = ultimo dia com dado disponivel no mes (normalmente ultimo dia util).
  SELECT
    date_trunc('month', base_date) AS month_ref,
    MAX(base_date) AS snapshot_date
  FROM raw_ndf
  GROUP BY 1
),
monthly_from_source AS (
  SELECT
    d.snapshot_date,
    r.book,
    SUM(r.mtm_value) AS mtm_value
  FROM raw_ndf r
  INNER JOIN month_close_dates d
    ON r.base_date = d.snapshot_date
  GROUP BY 1, 2
),
month_close_with_seed AS (
  SELECT snapshot_date
  FROM month_close_dates
  UNION
  SELECT DISTINCT snapshot_date
  FROM seed_dez_2025
),
books AS (
  SELECT DISTINCT book FROM raw_ndf
  UNION
  SELECT DISTINCT book FROM seed_dez_2025
),
monthly_union_raw AS (
  SELECT snapshot_date, book, mtm_value FROM seed_dez_2025
  UNION ALL
  SELECT snapshot_date, book, mtm_value FROM monthly_from_source
),
monthly_union AS (
  -- Garante linha para todo book em todo fechamento mensal (preenche com 0 quando ausente).
  SELECT
    d.snapshot_date,
    b.book,
    COALESCE(SUM(u.mtm_value), 0) AS mtm_month
  FROM month_close_with_seed d
  CROSS JOIN books b
  LEFT JOIN monthly_union_raw u
    ON u.snapshot_date = d.snapshot_date
   AND u.book = b.book
  GROUP BY 1, 2
),
final_enriched AS (
  SELECT
    snapshot_date,
    date_trunc('month', snapshot_date) AS month_ref,
    date_format(snapshot_date, 'yyyy-MM') AS month_label,
    year(snapshot_date) AS year_ref,
    month(snapshot_date) AS month_num,
    book,
    mtm_month,
    LAG(mtm_month) OVER (PARTITION BY book ORDER BY snapshot_date) AS mtm_prev_month,
    FIRST_VALUE(mtm_month) OVER (
      PARTITION BY book, year(snapshot_date)
      ORDER BY snapshot_date
    ) AS mtm_first_month_year
  FROM monthly_union
)
SELECT
  snapshot_date,
  month_ref,
  month_label,
  year_ref,
  month_num,
  book,
  mtm_month,
  mtm_prev_month,
  mtm_month - mtm_prev_month AS mtm_variation_mom,
  mtm_first_month_year,
  mtm_month - mtm_first_month_year AS mtm_variation_ytd
FROM final_enriched
ORDER BY snapshot_date, book;
