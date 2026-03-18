# Databricks notebook source
# MAGIC %md
# MAGIC ## Reconciliacao diaria Calypso x SAP com alerta no Slack
# MAGIC
# MAGIC Widgets:
# MAGIC - `run_date` (YYYY-MM-DD) - se vazio, usa penultimo dia util (D-2 util) considerando fim de semana e feriados nacionais BR.
# MAGIC - `erp_company_code` - empresa alvo (`BR11`, `BR12`, `BR28`).
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

COMPANY_ACCOUNT_CONFIG = {
    "BR11": {
        "calypso_accounts": [
            "1232011006",
            "1232011007",
            "1661011994",
            "4112011004",
            "4112011005",
            "4311021996",
            "7132021004",
            "7132031002",
            "8132021004",
            "8132031001",
            "8211031003",
        ],
        "sap_accounts": [
            "1232011006",
            "1232011007",
            "4112011004",
            "4112011005",
            "4311021996",
            "7132031002",
            "8132021004",
            "8211031003",
        ],
    },
    "BR12": {
        "calypso_accounts": [
            "1661011994",
            "4311021996",
            "8211031003",
            "1232011001",
            "4112011002",
            "7132021001",
            "8132021001",
            "7132021015",
            "8132021014",
            "1232011006",
            "4112011005",
            "7132031002",
            "8132031001",
        ],
        "sap_accounts": [
            "1661011994",
            "4311021996",
            "8211031003",
            "1232011001",
            "4112011002",
            "7132021001",
            "8132021001",
            "7132021015",
            "8132021014",
            "1232011006",
            "4112011005",
            "7132031002",
            "8132031001",
        ],
    },
    "BR28": {
        "calypso_accounts": [
            "1661011994",
            "4311021996",
            "1232011006",
            "4112011005",
            "8211031003",
            "7132031022",
            "8132031023",
            "7132031002",
            "8132031001",
        ],
        "sap_accounts": [
            "1661011994",
            "4311021996",
            "1232011006",
            "4112011005",
            "8211031003",
            "7132031022",
            "8132031023",
            "7132031002",
            "8132031001",
        ],
    },
}


def to_sql_string_literal_list(values: list[str]) -> str:
    if not values:
        raise ValueError("Lista de contas vazia. Verifique configuracao da empresa.")
    return ", ".join(f"'{v}'" for v in values)


NATIONAL_HOLIDAYS_CACHE = {}


def easter_sunday(year: int) -> date:
    # Algoritmo de Meeus/Jones/Butcher para calendario gregoriano.
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def brazil_national_holidays(year: int) -> set[date]:
    if year in NATIONAL_HOLIDAYS_CACHE:
        return NATIONAL_HOLIDAYS_CACHE[year]

    easter = easter_sunday(year)
    holidays = {
        date(year, 1, 1),   # Confraternizacao Universal
        easter - timedelta(days=2),  # Paixao de Cristo (Sexta-feira Santa)
        date(year, 4, 21),  # Tiradentes
        date(year, 5, 1),   # Dia do Trabalho
        date(year, 9, 7),   # Independencia do Brasil
        date(year, 10, 12), # Nossa Senhora Aparecida
        date(year, 11, 2),  # Finados
        date(year, 11, 15), # Proclamacao da Republica
        date(year, 11, 20), # Dia Nacional de Zumbi e da Consciencia Negra
        date(year, 12, 25), # Natal
    }

    NATIONAL_HOLIDAYS_CACHE[year] = holidays
    return holidays


def is_business_day(target_date: date) -> bool:
    return (
        target_date.weekday() < 5
        and target_date not in brazil_national_holidays(target_date.year)
    )


def subtract_business_days(base_date: date, business_days: int) -> date:
    if business_days < 0:
        raise ValueError("business_days deve ser >= 0")

    current = base_date
    remaining = business_days
    while remaining > 0:
        current -= timedelta(days=1)
        if is_business_day(current):
            remaining -= 1
    return current


dbutils.widgets.text("run_date", "")
dbutils.widgets.dropdown("erp_company_code", "BR11", ["BR11", "BR12", "BR28"])
dbutils.widgets.text("slack_webhook_secret_scope", "monitoring")
dbutils.widgets.text("slack_webhook_secret_key", "reconciliacao_calypso_sap_webhook")
dbutils.widgets.text("tolerance", "0.01")
dbutils.widgets.text("slack_alert_user_ids", "")

run_date = dbutils.widgets.get("run_date").strip()
erp_company_code = dbutils.widgets.get("erp_company_code").strip().upper()
secret_scope = dbutils.widgets.get("slack_webhook_secret_scope").strip()
secret_key = dbutils.widgets.get("slack_webhook_secret_key").strip()
tolerance = float(dbutils.widgets.get("tolerance").strip() or "0.01")
slack_alert_user_ids = dbutils.widgets.get("slack_alert_user_ids").strip()

if not run_date:
    run_date = subtract_business_days(date.today(), 2).isoformat()

if not re.match(r"^\d{4}-\d{2}-\d{2}$", run_date):
    raise ValueError(f"Formato invalido de run_date: {run_date}. Use YYYY-MM-DD.")

if erp_company_code not in COMPANY_ACCOUNT_CONFIG:
    raise ValueError(
        f"erp_company_code invalido: {erp_company_code}. Opcoes: {sorted(COMPANY_ACCOUNT_CONFIG.keys())}"
    )

company_config = COMPANY_ACCOUNT_CONFIG[erp_company_code]
calypso_accounts_sql = to_sql_string_literal_list(company_config["calypso_accounts"])
sap_accounts_sql = to_sql_string_literal_list(company_config["sap_accounts"])


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
          AND processing_org_attribute_nu_companyerp = '{erp_company_code}'
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
          AND processing_org_attribute_nu_companyerp = '{erp_company_code}'
      ) p
      LEFT JOIN (
        SELECT *
        FROM etl.br__dataset.calypso_trades_report_latest
      ) t
      ON p.trade_id = t.trade_id
    )
  )
  WHERE account_number IN ({calypso_accounts_sql})
  GROUP BY account_number
),
SAP AS (
  SELECT
    glaccount__number AS account_number,
    SUM(CASE WHEN LOWER(movement__identifier) = 'credit' THEN movement__amount * -1 ELSE 0 END) AS total_creditado_3,
    SUM(CASE WHEN LOWER(movement__identifier) = 'debit' THEN movement__amount ELSE 0 END) AS total_debitado_3
  FROM usr.erp.streaming_data
  WHERE glaccount__number IN ({sap_accounts_sql})
    AND movement__entry_date = DATE('{run_date}')
    AND movement__erp_company_code = '{erp_company_code}'
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
    f"{status_emoji} *Reconciliacao Calypso x SAP ({erp_company_code})*\n"
    f"*Data:* {run_date}\n"
    f"*Contas monitoradas (Calypso/SAP):* {len(company_config['calypso_accounts'])}/{len(company_config['sap_accounts'])}\n"
    f"*Contas avaliadas:* {total_accounts}\n"
    f"*Contas divergentes (>|{tolerance}|):* {qtd_divergentes}\n"
    f"*Soma das diferencas:* {total_diferenca:,.2f}\n"
    f"*Diferencas por conta:*\n{resumo}"
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
