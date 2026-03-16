# oliveiralet

Starter de reconciliação financeira para Databricks.

## Conteúdo

- `br11_futuros_reconciliation.py`: reconciliação diária Calypso vs SAP para BR11 (produto Futuro DOL)
- `docs/reconciliacao_br11_futuros.md`: regras, escopo e configuração do job diário

## Execução rápida

No Databricks Job, execute `br11_futuros_reconciliation.py` com widgets:

- `run_date` (yyyy-MM-dd)
- `tolerance` (ex.: 0.01)
- `slack_webhook_url` (opcional)
- `output_table_prefix` (opcional, para salvar resultado de teste em tabelas)
- `build_message_preview` (opcional; use `false` no teste)

No notebook, execute com:

```python
%run ./br11_futuros_reconciliation
br11_futuros_reconciliation()
```

Notebook pronto (passo a passo) para teste:

- `notebooks/br11_futuros_reconciliation_step_by_step.py`
