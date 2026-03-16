"""
Reconciliação diária Calypso vs SAP para Futuros (entidade BR11).

Uso no Databricks (Job):
  1) Configure widgets (opcional):
     - run_date: yyyy-MM-dd (default: ontem)
     - tolerance: tolerância numérica (default: 0.01)
     - slack_webhook_url: webhook do Slack (opcional)
     - output_table_prefix: prefixo para salvar resultados de teste (opcional)
  2) Execute este script como notebook job ou python task.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable, Optional, Sequence
from urllib import request

from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F

CALYPSO_TABLE = "etl.br__dataset.calypso_accounting_postings_report_latest"
SAP_TABLE = "usr.erp.streaming_data"
ENTITY = "BR11"
PRODUCT_HINT = "Futuro DOL"

ACCOUNTS_TO_RECONCILE = (
    "1232011006",
    "4112011005",
    "8132031001",
    "7132031002",
)

ACCOUNTS_WITH_SAP_BALANCE = {"1232011006", "4112011005"}

CALYPSO_CANDIDATES = {
    "posting_date": ("posting_date", "accounting_date", "movement_date", "trade_date", "date"),
    "account": ("account", "gl_account", "account_number", "sap_account", "movement__gl_account"),
    "entity": ("entity", "legal_entity", "company_code", "movement__company_code"),
    "canu": ("canu", "canal", "movement__canu", "cost_center", "profit_center"),
    "debit_credit": ("debit_credit", "dc_indicator", "dr_cr", "movement_type"),
    "amount": ("amount", "signed_amount", "movement_amount", "value"),
    "product": ("product", "product_type", "instrument", "trade_family", "underlying"),
}

SAP_CANDIDATES = {
    "posting_date": ("movement__posting_date", "posting_date", "document_date", "date"),
    "posting_ts": ("movement__posting_ts", "posting_ts", "updated_at", "ingestion_ts"),
    "account": ("movement__gl_account", "gl_account", "account", "account_number"),
    "entity": ("movement__company_code", "company_code", "entity", "legal_entity"),
    "canu": ("movement__canu", "canu", "cost_center", "profit_center"),
    "debit_credit": ("movement__debit_credit", "debit_credit", "dc_indicator", "dr_cr"),
    "amount": ("movement__amount", "amount", "signed_amount", "value"),
    "erp_document_type": ("movement__erp_document_type", "erp_document_type"),
    "balance": ("movement__account_balance", "account_balance", "balance", "movement__balance"),
}


@dataclass
class ReconciliationConfig:
    run_date: str
    tolerance: float
    slack_webhook_url: Optional[str]
    output_table_prefix: Optional[str]


def get_widget(name: str, default: str) -> str:
    try:
        # dbutils existe apenas no Databricks runtime.
        return dbutils.widgets.get(name)  # type: ignore[name-defined]
    except Exception:
        return default


def resolve_config() -> ReconciliationConfig:
    default_date = (date.today() - timedelta(days=1)).isoformat()
    run_date = get_widget("run_date", default_date).strip() or default_date
    tolerance = float(get_widget("tolerance", "0.01"))
    webhook = get_widget("slack_webhook_url", "").strip() or None
    output_table_prefix = get_widget("output_table_prefix", "").strip() or None
    return ReconciliationConfig(
        run_date=run_date,
        tolerance=tolerance,
        slack_webhook_url=webhook,
        output_table_prefix=output_table_prefix,
    )


def first_existing(columns: Iterable[str], candidates: Sequence[str]) -> Optional[str]:
    available = set(columns)
    for c in candidates:
        if c in available:
            return c
    return None


def required_col(df: DataFrame, logical_name: str, candidates: Sequence[str]) -> str:
    resolved = first_existing(df.columns, candidates)
    if not resolved:
        raise ValueError(
            f"Coluna obrigatória '{logical_name}' não encontrada. Candidatas: {list(candidates)}. "
            f"Colunas disponíveis: {df.columns}"
        )
    return resolved


def optional_col(df: DataFrame, candidates: Sequence[str]) -> Optional[str]:
    return first_existing(df.columns, candidates)


def normalize_amounts(df: DataFrame, amount_col: str, dc_col: Optional[str]) -> DataFrame:
    amount = F.coalesce(F.col(amount_col).cast("double"), F.lit(0.0))
    if dc_col:
        dc = F.upper(F.trim(F.col(dc_col)))
        debit = F.when(dc.isin("D", "DR", "DEBIT"), F.abs(amount)).otherwise(F.lit(0.0))
        credit = F.when(dc.isin("C", "CR", "CREDIT"), F.abs(amount)).otherwise(F.lit(0.0))
        # Fallback para códigos inesperados: usa sinal do valor.
        debit = F.when((debit == 0.0) & (credit == 0.0) & (amount < 0), F.abs(amount)).otherwise(debit)
        credit = F.when((debit == 0.0) & (credit == 0.0) & (amount > 0), F.abs(amount)).otherwise(credit)
    else:
        # Convenção fallback: positivo = crédito, negativo = débito.
        debit = F.when(amount < 0, F.abs(amount)).otherwise(F.lit(0.0))
        credit = F.when(amount > 0, F.abs(amount)).otherwise(F.lit(0.0))
    return df.withColumn("debit_amount", debit).withColumn("credit_amount", credit)


def prepare_calypso(spark: SparkSession, cfg: ReconciliationConfig) -> DataFrame:
    df = spark.table(CALYPSO_TABLE)
    posting_date_col = required_col(df, "posting_date", CALYPSO_CANDIDATES["posting_date"])
    account_col = required_col(df, "account", CALYPSO_CANDIDATES["account"])
    amount_col = required_col(df, "amount", CALYPSO_CANDIDATES["amount"])
    entity_col = optional_col(df, CALYPSO_CANDIDATES["entity"])
    canu_col = optional_col(df, CALYPSO_CANDIDATES["canu"])
    dc_col = optional_col(df, CALYPSO_CANDIDATES["debit_credit"])
    product_col = optional_col(df, CALYPSO_CANDIDATES["product"])

    base = (
        df.withColumn("posting_date", F.to_date(F.col(posting_date_col)))
        .withColumn("account", F.col(account_col).cast("string"))
        .withColumn("canu", F.coalesce(F.col(canu_col).cast("string"), F.lit("UNKNOWN")) if canu_col else F.lit("UNKNOWN"))
        .withColumn("amount_value", F.col(amount_col).cast("double"))
    )

    if entity_col:
        base = base.filter(F.col(entity_col) == ENTITY)

    if product_col:
        base = base.filter(F.upper(F.col(product_col)).contains(PRODUCT_HINT.upper()))

    base = base.filter(F.col("posting_date") == F.to_date(F.lit(cfg.run_date)))
    base = base.filter(F.col("account").isin(*ACCOUNTS_TO_RECONCILE))
    base = normalize_amounts(base, "amount_value", dc_col)

    return (
        base.groupBy("posting_date", "account", "canu")
        .agg(
            F.sum("debit_amount").alias("calypso_debit"),
            F.sum("credit_amount").alias("calypso_credit"),
        )
        .withColumn("calypso_net", F.col("calypso_credit") - F.col("calypso_debit"))
    )


def prepare_sap(spark: SparkSession, cfg: ReconciliationConfig) -> tuple[DataFrame, DataFrame]:
    df = spark.table(SAP_TABLE)
    posting_date_col = required_col(df, "posting_date", SAP_CANDIDATES["posting_date"])
    account_col = required_col(df, "account", SAP_CANDIDATES["account"])
    amount_col = required_col(df, "amount", SAP_CANDIDATES["amount"])
    erp_document_col = required_col(df, "erp_document_type", SAP_CANDIDATES["erp_document_type"])
    entity_col = optional_col(df, SAP_CANDIDATES["entity"])
    canu_col = optional_col(df, SAP_CANDIDATES["canu"])
    dc_col = optional_col(df, SAP_CANDIDATES["debit_credit"])
    balance_col = optional_col(df, SAP_CANDIDATES["balance"])
    posting_ts_col = optional_col(df, SAP_CANDIDATES["posting_ts"])

    base = (
        df.withColumn("posting_date", F.to_date(F.col(posting_date_col)))
        .withColumn("account", F.col(account_col).cast("string"))
        .withColumn("canu", F.coalesce(F.col(canu_col).cast("string"), F.lit("UNKNOWN")) if canu_col else F.lit("UNKNOWN"))
        .withColumn("amount_value", F.col(amount_col).cast("double"))
        .filter(F.col(erp_document_col) == F.lit("YX"))
        .filter(F.col("posting_date") == F.to_date(F.lit(cfg.run_date)))
        .filter(F.col("account").isin(*ACCOUNTS_TO_RECONCILE))
    )

    if entity_col:
        base = base.filter(F.col(entity_col) == ENTITY)

    normalized = normalize_amounts(base, "amount_value", dc_col)
    agg = (
        normalized.groupBy("posting_date", "account", "canu")
        .agg(
            F.sum("debit_amount").alias("sap_debit"),
            F.sum("credit_amount").alias("sap_credit"),
        )
        .withColumn("sap_net", F.col("sap_credit") - F.col("sap_debit"))
    )

    if balance_col:
        with_balance = base.withColumn("sap_balance_raw", F.col(balance_col).cast("double"))
        if posting_ts_col:
            w = Window.partitionBy("posting_date", "account").orderBy(F.col(posting_ts_col).desc_nulls_last())
            balances = (
                with_balance.withColumn("rn", F.row_number().over(w))
                .filter(F.col("rn") == 1)
                .select("posting_date", "account", F.col("sap_balance_raw").alias("sap_final_balance"))
            )
        else:
            balances = (
                with_balance.groupBy("posting_date", "account")
                .agg(F.max("sap_balance_raw").alias("sap_final_balance"))
            )
    else:
        balances = (
            agg.groupBy("posting_date", "account")
            .agg(F.sum("sap_net").alias("sap_final_balance"))
            .withColumn("sap_final_balance", F.round(F.col("sap_final_balance"), 2))
        )

    balances = balances.filter(F.col("account").isin(*ACCOUNTS_WITH_SAP_BALANCE))
    return agg, balances


def reconcile(calypso: DataFrame, sap: DataFrame, tolerance: float) -> DataFrame:
    return (
        calypso.join(sap, ["posting_date", "account", "canu"], "full")
        .fillna(0.0, subset=["calypso_debit", "calypso_credit", "calypso_net", "sap_debit", "sap_credit", "sap_net"])
        .withColumn("debit_diff", F.col("calypso_debit") - F.col("sap_debit"))
        .withColumn("credit_diff", F.col("calypso_credit") - F.col("sap_credit"))
        .withColumn("net_diff", F.col("calypso_net") - F.col("sap_net"))
        .withColumn(
            "status",
            F.when((F.abs(F.col("debit_diff")) <= tolerance) & (F.abs(F.col("credit_diff")) <= tolerance), F.lit("RECONCILED"))
            .otherwise(F.lit("DIFFERENCE")),
        )
    )


def build_account_summary(result_df: DataFrame) -> DataFrame:
    return (
        result_df.groupBy("account")
        .agg(
            F.sum("calypso_debit").alias("calypso_debit"),
            F.sum("calypso_credit").alias("calypso_credit"),
            F.sum("sap_debit").alias("sap_debit"),
            F.sum("sap_credit").alias("sap_credit"),
            F.max(F.when(F.col("status") == "DIFFERENCE", F.lit(1)).otherwise(F.lit(0))).alias("has_difference"),
        )
        .withColumn("status", F.when(F.col("has_difference") == 1, F.lit("DIFFERENCE")).otherwise(F.lit("RECONCILED")))
    )


def build_slack_message(result_df: DataFrame, balance_df: DataFrame, run_date: str) -> str:
    account_summary = build_account_summary(result_df).orderBy("account").collect()

    diffs = (
        result_df.filter(F.col("status") == "DIFFERENCE")
        .select("account", "canu", "debit_diff", "credit_diff", "net_diff")
        .orderBy("account", "canu")
        .collect()
    )

    balances = {
        (r["account"]): r["sap_final_balance"]
        for r in balance_df.orderBy("account").collect()
    }

    reconciled_count = result_df.filter(F.col("status") == "RECONCILED").count()
    diff_count = result_df.filter(F.col("status") == "DIFFERENCE").count()
    header_status = "OK RECONCILIADO" if diff_count == 0 else "ATENCAO DIFERENCAS"

    lines = [
        f"*BR11 - Reconciliacao Futuros ({run_date})*",
        f"Status geral: *{header_status}*",
        f"Linhas reconciliadas: {reconciled_count} | Linhas com diferenca: {diff_count}",
        "",
        "*Resumo por conta*",
    ]

    for r in account_summary:
        account = r["account"]
        extra = ""
        if account in ACCOUNTS_WITH_SAP_BALANCE:
            extra = f" | saldo_final_sap={balances.get(account, 0.0):,.2f}"
        lines.append(
            f"- {account} [{r['status']}]: "
            f"Calypso D={r['calypso_debit']:,.2f} C={r['calypso_credit']:,.2f} | "
            f"SAP D={r['sap_debit']:,.2f} C={r['sap_credit']:,.2f}{extra}"
        )

    if diffs:
        lines.extend(["", "*Detalhes das diferencas (conta/canu)*"])
        for d in diffs[:40]:
            lines.append(
                f"- conta={d['account']} canu={d['canu']}: "
                f"diff_debito={d['debit_diff']:,.2f}, diff_credito={d['credit_diff']:,.2f}, diff_liquido={d['net_diff']:,.2f}"
            )
        if len(diffs) > 40:
            lines.append(f"- ... {len(diffs) - 40} linhas adicionais com diferenca")

    return "\n".join(lines)


def send_slack_message(webhook_url: str, message: str) -> None:
    payload = json.dumps({"text": message}).encode("utf-8")
    req = request.Request(webhook_url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with request.urlopen(req, timeout=20) as resp:
        if resp.status >= 300:
            raise RuntimeError(f"Erro ao enviar mensagem para Slack. HTTP status: {resp.status}")


def main() -> None:
    spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()
    cfg = resolve_config()

    calypso = prepare_calypso(spark, cfg)
    sap, balances = prepare_sap(spark, cfg)
    result = reconcile(calypso, sap, cfg.tolerance).cache()
    account_summary_df = build_account_summary(result).cache()

    message = build_slack_message(result, balances, cfg.run_date)
    print(message)

    if cfg.slack_webhook_url:
        send_slack_message(cfg.slack_webhook_url, message)
        print("Mensagem enviada ao Slack com sucesso.")
    else:
        print("Webhook do Slack nao informado; mensagem apenas exibida no log.")

    if cfg.output_table_prefix:
        detail_table = f"{cfg.output_table_prefix}_detail"
        summary_table = f"{cfg.output_table_prefix}_summary"
        balance_table = f"{cfg.output_table_prefix}_balances"
        result.write.mode("overwrite").saveAsTable(detail_table)
        account_summary_df.write.mode("overwrite").saveAsTable(summary_table)
        balances.write.mode("overwrite").saveAsTable(balance_table)
        print(
            "Modo teste: resultados salvos em tabelas -> "
            f"{detail_table}, {summary_table}, {balance_table}"
        )

    # Resultado detalhado para inspeção no Databricks.
    result.orderBy("account", "canu").show(truncate=False)


def br11_futuros_reconciliation() -> None:
    """
    Entry point amigável para execução via notebook (%run).
    Exemplo:
      %run ./br11_futuros_reconciliation
      br11_futuros_reconciliation()
    """
    main()


if __name__ == "__main__":
    main()
