# Databricks notebook source
# MAGIC %md
# MAGIC ## Reconciliacao diaria Calypso x SAP com alerta no Slack
# MAGIC
# MAGIC Widgets:
# MAGIC - `run_date` (YYYY-MM-DD) - se vazio, usa ontem.
# MAGIC - `slack_webhook_secret_scope` - scope do Databricks Secret.
# MAGIC - `slack_webhook_secret_key` - chave com webhook URL do Slack.
# MAGIC - `tolerance` - limite para considerar divergencia (default: 0.01).
# MAGIC - `slack_alert_user_ids` - 1+ user ids Slack para mention quando houver divergencia (opcional).
# MAGIC   Aceita IDs e/ou mentions separados por virgula, espaco ou ponto e virgula.

# COMMAND ----------

import json
import re
from datetime import date, timedelta
from urllib import request

# COMMAND ----------

dbutils.widgets.text("run_date", "")
dbutils.widgets.text("slack_webhook_secret_scope", "monitoring")
dbutils.widgets.text("slack_webhook_secret_key", "reconciliacao_calypso_sap_webhook")
dbutils.widgets.text("tolerance", "0.01")
dbutils.widgets.text("slack_alert_user_ids", "")

run_date = dbutils.widgets.get("run_date").strip()
secret_scope = dbutils.widgets.get("slack_webhook_secret_scope").strip()
secret_key = dbutils.widgets.get("slack_webhook_secret_key").strip()
tolerance = float(dbutils.widgets.get("tolerance").strip() or "0.01")
slack_alert_user_ids = dbutils.widgets.get("slack_alert_user_ids").strip()

if not run_date:
    run_date = (date.today() - timedelta(days=1)).isoformat()

if not re.match(r"^\d{4}-\d{2}-\d{2}$", run_date):
    raise ValueError(f"Formato invalido de run_date: {run_date}. Use YYYY-MM-DD.")


def normalize_slack_user_mentions(user_ids_raw: str) -> str:
    if not user_ids_raw:
        return ""

    tokens = [t for t in re.split(r"[,;\s]+", user_ids_raw) if t]
    mentions = []

    for token in tokens:
        user_id = token
        mention_match = re.match(r"^<@([A-Z0-9]+)>$", token)
        if mention_match:
            user_id = mention_match.group(1)

        if not re.match(r"^[A-Z0-9]+$", user_id):
            raise ValueError(
                "Formato invalido de slack_alert_user_ids. Use IDs/mentions separados por virgula, espaco ou ';'."
            )

        mentions.append(f"<@{user_id}>")

    unique_mentions = list(dict.fromkeys(mentions))
    return " ".join(unique_mentions)

# COMMAND ----------

query = f"""
WITH tradesCalypso AS (
  SELECT
    account_number,
    SUM(CASE WHEN credit_debit_indicator = 'C' THEN amount ELSE 0 END) AS total_creditado_2,
    SUM(CASE WHEN credit_debit_indicator = 'D' THEN amount ELSE 0 END) AS total_debitado_2
  FROM (
    SELECT creditaccount AS account_number, 'C' AS credit_debit_indicator, amount
    FROM (
      SELECT p.*, t.*
      FROM (
        SELECT *
        FROM etl.br__dataset.calypso_accounting_postings_report_latest
        WHERE accounting_rule IN ('NU_CS Fee', 'NU_CS Fee2')
          AND effective_date = DATE('{run_date}')
          AND processing_org_attribute_nu_companyerp = 'BR11'
      ) p
      LEFT JOIN (
        SELECT *
        FROM etl.br__dataset.calypso_trades_report_latest
      ) t
      ON p.trade_id = t.trade_id
    )
    UNION ALL
    SELECT debitaccount AS account_number, 'D' AS credit_debit_indicator, amount
    FROM (
      SELECT p.*, t.*
      FROM (
        SELECT *
        FROM etl.br__dataset.calypso_accounting_postings_report_latest
        WHERE accounting_rule IN ('NU_CS Fee', 'NU_CS Fee2')
          AND effective_date = DATE('{run_date}')
          AND processing_org_attribute_nu_companyerp = 'BR11'
      ) p
      LEFT JOIN (
        SELECT *
        FROM etl.br__dataset.calypso_trades_report_latest
      ) t
      ON p.trade_id = t.trade_id
    )
  )
  WHERE account_number IN (
    '1232011006', '1232011007', '1661011994', '4112011004', '4112011005',
    '4311021996', '7132021004', '7132031002', '8132021004', '8132031001', '8211031003'
  )
  GROUP BY account_number
),
SAP AS (
  SELECT
    glaccount__number AS account_number,
    SUM(CASE WHEN LOWER(movement__identifier) = 'credit' THEN movement__amount * -1 ELSE 0 END) AS total_creditado_3,
    SUM(CASE WHEN LOWER(movement__identifier) = 'debit' THEN movement__amount ELSE 0 END) AS total_debitado_3
  FROM usr.erp.streaming_data
  WHERE glaccount__number IN (
    '1232011006', '1232011007', '4112011004', '4112011005', '4311021996',
    '7132031002', '8132021004', '8211031003'
  )
    AND movement__entry_date = DATE('{run_date}')
    AND movement__erp_company_code = 'BR11'
    AND movement__erp_document_type = 'YX'
  GROUP BY glaccount__number
)
SELECT
  COALESCE(t2.account_number, t3.account_number) AS account_number,
  DATE('{run_date}') AS data,
  (COALESCE(t2.total_debitado_2, 0) - COALESCE(t3.total_debitado_3, 0)) AS diferenca
FROM tradesCalypso t2
FULL OUTER JOIN SAP t3
  ON t2.account_number = t3.account_number
ORDER BY account_number
"""

df = spark.sql(query)
display(df)

# COMMAND ----------

rows = df.collect()
total_accounts = len(rows)
divergentes = [r for r in rows if abs(float(r["diferenca"] or 0.0)) > tolerance]
qtd_divergentes = len(divergentes)
total_diferenca = sum(float(r["diferenca"] or 0.0) for r in rows)
status_emoji = ":white_check_mark:" if qtd_divergentes == 0 else ":warning:"

top_linhas = []
for row in sorted(rows, key=lambda r: abs(float(r["diferenca"] or 0.0)), reverse=True)[:10]:
    top_linhas.append(f"- `{row['account_number']}`: {float(row['diferenca'] or 0.0):,.2f}")

resumo = "\n".join(top_linhas) if top_linhas else "- sem dados"
slack_alert_mentions = normalize_slack_user_mentions(slack_alert_user_ids)

mention_line = ""
if qtd_divergentes > 0 and slack_alert_mentions:
    mention_line = f"\n*Acao:* {slack_alert_mentions} favor verificar divergencias."

mensagem = (
    f"{status_emoji} *Reconciliacao Calypso x SAP (BR11)*\n"
    f"*Data:* {run_date}\n"
    f"*Contas avaliadas:* {total_accounts}\n"
    f"*Contas divergentes (>|{tolerance}|):* {qtd_divergentes}\n"
    f"*Soma das diferencas:* {total_diferenca:,.2f}\n"
    f"*Top 10 diferencas por conta:*\n{resumo}"
    f"{mention_line}"
)

print(mensagem)

# COMMAND ----------

webhook_url = dbutils.secrets.get(scope=secret_scope, key=secret_key)
payload = json.dumps({"text": mensagem}).encode("utf-8")
req = request.Request(
    webhook_url,
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST",
)

with request.urlopen(req, timeout=15) as resp:
    response_body = resp.read().decode("utf-8")
    print(f"Slack HTTP status: {resp.status}")
    print(f"Slack response: {response_body}")
