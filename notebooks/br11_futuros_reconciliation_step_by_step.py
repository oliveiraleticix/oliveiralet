# Databricks notebook source
# MAGIC %md
# MAGIC # BR11 Futuros - Teste da reconciliação (Calypso vs SAP)
# MAGIC
# MAGIC Notebook pronto para testar o resultado da reconciliação antes de ativar Slack.
# MAGIC
# MAGIC **Pré-requisito**: arquivo `br11_futuros_reconciliation.py` no repositório.

# COMMAND ----------

dbutils.widgets.text("run_date", "2026-01-31", "run_date (yyyy-MM-dd)")
dbutils.widgets.text("tolerance", "0.01", "tolerance")
dbutils.widgets.text("output_table_prefix", "tmp.br11_futuros_recon_20260131", "output_table_prefix")
dbutils.widgets.text("slack_webhook_url", "", "slack_webhook_url (opcional)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1) Conferir parâmetros
# MAGIC
# MAGIC Para testar sem enviar Slack, deixe `slack_webhook_url` vazio.

# COMMAND ----------

run_date = dbutils.widgets.get("run_date").strip()
tolerance = dbutils.widgets.get("tolerance").strip()
output_table_prefix = dbutils.widgets.get("output_table_prefix").strip()
slack_webhook_url = dbutils.widgets.get("slack_webhook_url").strip()

if not output_table_prefix:
    output_table_prefix = f"tmp.br11_futuros_recon_{run_date.replace('-', '')}"
    print(f"output_table_prefix vazio. Usando fallback: {output_table_prefix}")

print("Parâmetros de execução:")
print(f"- run_date={run_date}")
print(f"- tolerance={tolerance}")
print(f"- output_table_prefix={output_table_prefix}")
print(f"- slack_webhook_url={'preenchido' if slack_webhook_url else 'vazio'}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2) Executar reconciliação
# MAGIC
# MAGIC O script principal lê os widgets e:
# MAGIC - reconcilia BR11 por `data + conta + canu`
# MAGIC - compara débito/crédito Calypso vs SAP
# MAGIC - grava tabelas de teste com o prefixo informado

# COMMAND ----------

import importlib
import os
import sys

repo_root = os.path.abspath("..")
if repo_root not in sys.path:
    sys.path.append(repo_root)

import br11_futuros_reconciliation as recon

importlib.reload(recon)
result_df, summary_df, balances_df, slack_message = recon.br11_futuros_reconciliation()
print("Execução concluída.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3) Ler tabelas geradas

# COMMAND ----------

detail_table = f"{output_table_prefix}_detail"
summary_table = f"{output_table_prefix}_summary"
balance_table = f"{output_table_prefix}_balances"

print("Tabelas de saída:")
print(f"- {detail_table}")
print(f"- {summary_table}")
print(f"- {balance_table}")
print("")
print("Existem no metastore?")
print(f"- detail: {spark.catalog.tableExists(detail_table)}")
print(f"- summary: {spark.catalog.tableExists(summary_table)}")
print(f"- balances: {spark.catalog.tableExists(balance_table)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4) Resultado detalhado (todas as linhas)

# COMMAND ----------

if spark.catalog.tableExists(detail_table):
    display(spark.table(detail_table).orderBy("account", "canu"))
else:
    print(f"Tabela {detail_table} não encontrada. Exibindo DataFrame da execução atual.")
    display(result_df.orderBy("account", "canu"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5) Apenas diferenças (se houver)

# COMMAND ----------

if spark.catalog.tableExists(detail_table):
    display(
        spark.sql(
            f"""
            SELECT *
            FROM {detail_table}
            WHERE status = 'DIFFERENCE'
            ORDER BY account, canu
            """
        )
    )
else:
    print(f"Tabela {detail_table} não encontrada. Exibindo diferenças do DataFrame da execução atual.")
    display(result_df.filter("status = 'DIFFERENCE'").orderBy("account", "canu"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6) Resumo por conta

# COMMAND ----------

if spark.catalog.tableExists(summary_table):
    display(spark.table(summary_table).orderBy("account"))
else:
    print(f"Tabela {summary_table} não encontrada. Exibindo resumo do DataFrame da execução atual.")
    display(summary_df.orderBy("account"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7) Saldos finais SAP (contas com saldo exigido)

# COMMAND ----------

if spark.catalog.tableExists(balance_table):
    display(spark.table(balance_table).orderBy("account"))
else:
    print(f"Tabela {balance_table} não encontrada. Exibindo saldos do DataFrame da execução atual.")
    display(balances_df.orderBy("account"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8) Critério de aceite do teste
# MAGIC
# MAGIC - Sem linhas em `DIFFERENCE` na etapa 5.
# MAGIC - No resumo por conta, status `RECONCILED`.
# MAGIC - Saldos SAP das contas `1232011006` e `4112011005` preenchidos conforme esperado.
# MAGIC
# MAGIC Quando validado, basta preencher `slack_webhook_url` e reexecutar para enviar no Slack.
