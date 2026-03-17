# Processo de Batimento Diario Calypso x SAP (Databricks + Slack)

## 1) Objetivo

Executar diariamente a reconciliacao entre posicao Calypso e movimentos no SAP e enviar o status para Slack:

- `:white_check_mark:` sem divergencias relevantes
- `:warning:` com divergencias acima da tolerancia

## 2) Escopo da automacao

- Fonte Calypso: `etl.br__dataset.calypso_accounting_postings_report_latest`
- Fonte SAP: `usr.erp.streaming_data`
- Empresa ERP: `BR11`
- Tipo documento SAP: `YX`
- Regras Calypso: `NU_CS Fee`, `NU_CS Fee2`
- Notebook principal: `databricks/reconciliacao_calypso_sap_slack.py`

## 3) Pre-requisitos

1. Acesso ao workspace Databricks.
2. Canal Slack para receber notificacoes.
3. Webhook Slack ativo para o canal alvo.
4. Permissao para criar/usar Databricks Secrets.
5. Cluster ou Job Compute com acesso as tabelas consultadas.

## 4) Arquitetura resumida

1. Job diario executa notebook no Databricks.
2. Notebook calcula diferenca por conta (`diferenca = debitado_calypso - debitado_sap`).
3. Notebook classifica status por tolerancia.
4. Notebook envia mensagem para Slack via webhook armazenado em Secret.

## 5) Configuracao inicial (uma vez)

### 5.1) Publicar notebook no Databricks

Opcoes:

- Via Git folder (recomendado): abrir repo `oliveiralet`, fazer sync/pull e abrir `databricks/reconciliacao_calypso_sap_slack.py`.
- Via upload/import de arquivo `.py` no Workspace.

### 5.2) Criar webhook no Slack

1. Criar app em `https://api.slack.com/apps`.
2. Habilitar `Incoming Webhooks`.
3. Adicionar webhook ao canal do batimento.
4. Copiar URL `https://hooks.slack.com/services/...`.

> Se o workspace Slack exigir aprovacao de admin, solicitar liberacao do webhook.

### 5.3) Armazenar webhook em Databricks Secret

No terminal com Databricks CLI autenticado:

```bash
databricks auth login --host https://nubank-e2-general.cloud.databricks.com
databricks secrets create-scope monitoring
databricks secrets put-secret monitoring reconciliacao_calypso_sap_webhook
databricks secrets list-secrets monitoring
```

Esperado na listagem: key `reconciliacao_calypso_sap_webhook`.

## 6) Parametros do notebook

Widgets esperados:

- `run_date`: data de referencia (`YYYY-MM-DD`); vazio = D-1.
- `slack_webhook_secret_scope`: ex. `monitoring`.
- `slack_webhook_secret_key`: ex. `reconciliacao_calypso_sap_webhook`.
- `tolerance`: limiar de divergencia (default `0.01`).
- `slack_alert_user_id`: user id do Slack para mention em caso de divergencia (opcional).

## 7) Teste funcional (antes de agendar)

1. Anexar compute ao notebook.
2. Preencher:
   - `run_date = 2026-03-02` (ou data conhecida com dados)
   - `slack_webhook_secret_scope = monitoring`
   - `slack_webhook_secret_key = reconciliacao_calypso_sap_webhook`
   - `tolerance = 0.01`
   - `slack_alert_user_id = UXXXXXXXX` (opcional)
3. Executar `Run all`.
4. Validar:
   - resultado SQL exibido;
   - log com `Slack HTTP status: 200`;
   - mensagem recebida no canal Slack.

## 8) Criacao do Job diario

1. Databricks `Jobs` -> `Create job`.
2. Task tipo `Notebook` apontando para `reconciliacao_calypso_sap_slack.py`.
3. Configurar parametros da task:
   - `run_date =` vazio
   - `slack_webhook_secret_scope = monitoring`
   - `slack_webhook_secret_key = reconciliacao_calypso_sap_webhook`
   - `tolerance = 0.01`
   - `slack_alert_user_id = UXXXXXXXX` (opcional)
4. Definir schedule diario (ex.: 08:00, `America/Sao_Paulo`).
5. Executar `Run now` para validacao final.

## 9) Operacao diaria

Conferir no Slack:

- `:white_check_mark:` indica sem divergencias acima da tolerancia.
- `:warning:` indica ao menos uma conta divergente.

Campos enviados na mensagem:

- data processada;
- total de contas avaliadas;
- quantidade de contas divergentes;
- soma das diferencas;
- top 10 maiores diferencas por conta.
- mention ao usuario configurado quando houver divergencia.

## 10) Troubleshooting

### Erro: `Secret does not exist with scope ... and key ...`

- Scope/key invertidos nos widgets.
- Secret nao criado no Databricks.
- Key com nome diferente do configurado no Job.

### Erro: `ValueError: unknown url type`

- Webhook salvo incorretamente no Secret (sem `https://` ou com caracteres extras).
- Regravar secret com valor valido.

### Erro: `Formato invalido de slack_alert_user_id`

- Parametro preenchido fora do padrao.
- Usar `UXXXXXXXX` ou `<@UXXXXXXXX>`.

### Erro: `databricks: command not found`

- Databricks CLI nao instalada localmente.
- Instalar via Homebrew: `brew install databricks/tap/databricks`.

## 11) Seguranca e compliance

1. Nao armazenar webhook no codigo-fonte.
2. Usar apenas Databricks Secrets para valores sensiveis.
3. Se webhook for exposto, revogar e gerar novo imediatamente.

## 12) Checklist de go-live

- [ ] Notebook executa sem erro para data de teste.
- [ ] Mensagem chega no Slack.
- [ ] Job diario ativo com timezone correta.
- [ ] Widgets scope/key preenchidos corretamente.
- [ ] Segredo validado em `monitoring/reconciliacao_calypso_sap_webhook`.
