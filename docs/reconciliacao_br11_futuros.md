# Reconciliação automática BR11 (Futuros): Calypso vs SAP

Este documento descreve o fluxo diário de reconciliação para a entidade **BR11**, comparando os lançamentos entre:

- **Calypso**: `etl.br__dataset.calypso_accounting_postings_report_latest`
- **SAP**: `usr.erp.streaming_data` (somente `movement__erp_document_type = 'YX'`)

## Escopo inicial

Contas contábeis:

- `1232011006` (MtM receivable) → batimento + saldo final SAP
- `4112011005` → batimento + saldo final SAP
- `8132031001` → apenas batimento
- `7132031002` → apenas batimento

## Regra de reconciliação

Batimento diário por:

- `posting_date`
- `account`
- `canu`

Métricas comparadas:

- Total **debitado** no dia
- Total **creditado** no dia

Classificação:

- `RECONCILED`: diferença de débito e crédito dentro da tolerância
- `DIFFERENCE`: qualquer divergência acima da tolerância

## Saída no Slack

A mensagem diária contém:

1. Status geral da reconciliação do dia
2. Resumo por conta (Calypso vs SAP)
3. Saldo final SAP para `1232011006` e `4112011005`
4. Lista de divergências por `conta/canu`

## Script

Arquivo principal:

- `br11_futuros_reconciliation.py`

Parâmetros (widgets Databricks):

- `run_date` (formato `yyyy-MM-dd`, default: ontem)
- `tolerance` (default: `0.01`)
- `slack_webhook_url` (opcional)
- `output_table_prefix` (opcional, para modo teste)

## Testar o resultado da reconciliação (sem Slack)

Para validar primeiro o resultado:

1. Execute o script com:
   - `run_date=2026-01-31` (ou a data desejada)
   - `tolerance=0.01`
   - `slack_webhook_url` vazio
   - `output_table_prefix=tmp.br11_futuros_recon_20260131`
2. O script salvará:
   - `tmp.br11_futuros_recon_20260131_detail`
   - `tmp.br11_futuros_recon_20260131_summary`
   - `tmp.br11_futuros_recon_20260131_balances`
3. Consultas de validação:

```sql
-- Visão detalhada: diferenças por conta/canu
select *
from tmp.br11_futuros_recon_20260131_detail
where status = 'DIFFERENCE'
order by account, canu;
```

```sql
-- Resumo por conta
select *
from tmp.br11_futuros_recon_20260131_summary
order by account;
```

```sql
-- Saldos finais SAP das contas que exigem saldo
select *
from tmp.br11_futuros_recon_20260131_balances
order by account;
```

## Execução recomendada (Databricks Jobs)

1. Criar um Job diário (ex.: após carga de Calypso/SAP).
2. Adicionar task Python apontando para `br11_futuros_reconciliation.py`.
3. Configurar parâmetros:
   - `run_date`: data de referência da reconciliação
   - `tolerance`: tolerância de batimento
   - `slack_webhook_url`: webhook do canal de operação
4. Agendar execução diária.

## Formas corretas de executar (evitar NameError)

### Opção A: Databricks Job (Python file task)

Aponte diretamente para o arquivo `br11_futuros_reconciliation.py`.
Nesse modo, o script executa automaticamente.

### Opção B: Notebook com `%run`

```python
%run ./br11_futuros_reconciliation
br11_futuros_reconciliation()
```

> Se você chamar apenas `br11_futuros_reconciliation` sem `()`, ou sem ter feito `%run`,
> ocorrerá `NameError`.

### Opção C: Import como módulo Python

```python
import br11_futuros_reconciliation as recon
recon.main()
```

## Observações importantes

- O script foi feito para ser resiliente a variações de nomes de colunas (usa lista de candidatos por campo).
- No Calypso, também suporta o layout com `debitaccount`/`creditaccount` (uma linha com as duas pernas contábeis).
- Se a coluna de saldo SAP não existir, o script usa o **net movement** agregado como fallback para saldo final.
- A filtragem de produto usa o texto `"Futuro DOL"` quando a coluna de produto existir.
