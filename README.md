# oliveiralet

Automacao simples de reconciliacao diaria Calypso x SAP no Databricks com envio para Slack.

## Arquivo principal

- `databricks/reconciliacao_calypso_sap_slack.py`
- `docs/processo_batimento_calypso_sap.md` (runbook detalhado)

Esse arquivo esta no formato de notebook Python para Databricks e faz:
1. Recebe `run_date` (ou usa D-1).
2. Executa a query de batimento Calypso x SAP.
3. Calcula quantidade de contas divergentes e soma de diferencas.
4. Envia resumo para Slack via webhook salvo em Databricks Secret.

## Como configurar no Databricks

1. Importe o arquivo `databricks/reconciliacao_calypso_sap_slack.py` como notebook.
2. Crie o secret com o webhook:
   - Scope: `monitoring` (ou outro)
   - Key: `reconciliacao_calypso_sap_webhook`
3. Crie um Job com agendamento diario (ex.: 08:00).
4. Configure os parametros do notebook no Job:
   - `run_date` = vazio (usa D-1 automaticamente)
   - `erp_company_code` = `BR11` (opcoes: `BR11`, `BR12`, `BR28`)
   - `slack_webhook_secret_scope` = `monitoring`
   - `slack_webhook_secret_key` = `reconciliacao_calypso_sap_webhook`
   - `tolerance` = `0.01`
   - `slack_alert_user_ids` = `UXXXXXXXX,UYYYYYYYY` (opcional; mention quando houver diferenca)

## Observacoes

- Se quiser alertar apenas quando houver diferenca, condicione o envio ao `qtd_divergentes > 0`.
- Se preferir sem codigo, tambem da para usar Databricks SQL Query + Alert + Slack Destination.
