# Databricks notebook source
# MAGIC %md
# MAGIC # BR11 Futuros - Reconciliação diária (produção)
# MAGIC
# MAGIC Notebook enxuto para execução automática em Job:
# MAGIC - Reconcilia Calypso vs SAP em memória
# MAGIC - Monta mensagem consolidada
# MAGIC - Envia resultado para Slack

# COMMAND ----------

from datetime import date, timedelta

default_run_date = (date.today() - timedelta(days=1)).isoformat()

dbutils.widgets.text("run_date", default_run_date, "run_date (yyyy-MM-dd)")
dbutils.widgets.text("tolerance", "0.01", "tolerance")
dbutils.widgets.text("dry_run", "false", "dry_run (true/false)")
dbutils.widgets.text("slack_webhook_url", "", "slack_webhook_url (opcional)")
dbutils.widgets.text("slack_webhook_scope", "", "slack_webhook_scope (opcional)")
dbutils.widgets.text("slack_webhook_key", "", "slack_webhook_key (opcional)")

# COMMAND ----------

import importlib
import os
import sys

run_date = dbutils.widgets.get("run_date").strip()
tolerance = float(dbutils.widgets.get("tolerance").strip() or "0.01")
dry_run = dbutils.widgets.get("dry_run").strip().lower() in ("1", "true", "yes", "y")
slack_webhook_url = dbutils.widgets.get("slack_webhook_url").strip()
slack_webhook_scope = dbutils.widgets.get("slack_webhook_scope").strip()
slack_webhook_key = dbutils.widgets.get("slack_webhook_key").strip()

if (not slack_webhook_url) and slack_webhook_scope and slack_webhook_key:
    slack_webhook_url = dbutils.secrets.get(slack_webhook_scope, slack_webhook_key)

repo_root = os.path.abspath("..")
if repo_root not in sys.path:
    sys.path.append(repo_root)

import br11_futuros_reconciliation as recon

importlib.reload(recon)

print("Parâmetros:")
print(f"- run_date={run_date}")
print(f"- tolerance={tolerance}")
print(f"- dry_run={dry_run}")
print(f"- slack_webhook_url={'preenchido' if bool(slack_webhook_url) else 'vazio'}")
print(f"- slack_webhook_scope={'preenchido' if bool(slack_webhook_scope) else 'vazio'}")
print(f"- slack_webhook_key={'preenchido' if bool(slack_webhook_key) else 'vazio'}")

# COMMAND ----------

cfg = recon.ReconciliationConfig(
    run_date=run_date,
    tolerance=tolerance,
    slack_webhook_url=None,
    output_table_prefix=None,
    build_message_preview=False,
)

result_df, summary_df, balances_df = recon.run_reconciliation(spark, cfg)

result_df = result_df.cache()
summary_df = summary_df.cache()
balances_df = balances_df.cache()

print("Reconciliação executada com sucesso.")

# COMMAND ----------

message = recon.build_slack_message(result_df, balances_df, run_date)

print(message)

display(summary_df.orderBy("account"))
display(result_df.filter("status = 'DIFFERENCE'").orderBy("account", "canu"))
display(balances_df.orderBy("account"))

# COMMAND ----------

if dry_run:
    print("dry_run=true: mensagem não enviada ao Slack.")
elif not slack_webhook_url:
    raise ValueError(
        "Webhook não informado. Preencha slack_webhook_url "
        "ou configure slack_webhook_scope/slack_webhook_key."
    )
else:
    recon.send_slack_message(slack_webhook_url, message)
    print("Mensagem enviada ao Slack com sucesso.")
