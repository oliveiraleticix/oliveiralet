# Apresentacao Detalhada (PT-BR) - 12 slides

## Slide 1 - Capa
**Titulo:** Reconciliacao Calypso x SAP automatizada  
**Subtitulo:** Eficiencia operacional e velocidade no pre-closing de Futuros

## Slide 2 - Agenda
1. Contexto
2. Dor operacional
3. Objetivos
4. Solucao
5. Arquitetura
6. Regras principais
7. Fluxo diario
8. Mensageria no Slack
9. Impacto
10. Riscos e controles
11. Proximos passos
12. Call to action

## Slide 3 - Contexto do processo
- Reconciliacao diaria entre Calypso e SAP
- Processo critico para confianca no pre-closing
- Necessidade de reduzir trabalho manual recorrente

## Slide 4 - Principais dores antes da automacao
- Execucao manual e dependente de rotina individual
- Menor padronizacao na verificacao
- Tempo gasto em atividade repetitiva
- Resposta menos rapida a divergencias

## Slide 5 - Objetivos da iniciativa
- Automatizar execucao diaria
- Padronizar criterio de batimento
- Dar visibilidade no Slack para o time
- Reduzir tempo operacional e risco manual

## Slide 6 - Solucao implementada
- Notebook unico no Databricks
- Parametrizacao por empresa: `BR11`, `BR12`, `BR28`
- Job diario com 3 tasks (uma por empresa)
- Notificacao no Slack com status e detalhamento

## Slide 7 - Arquitetura (visao simples)
**Fluxo:**  
Calypso + SAP -> Databricks Job -> Query de reconciliacao -> Analise de diferencas -> Slack

**Detalhes:**  
- Secrets para webhook  
- Tolerancia configuravel  
- Mention automatica em caso de divergencia

## Slide 8 - Regras relevantes do notebook
- `run_date` vazio: usa D-2 util (fim de semana + feriados nacionais BR)
- Filtro por empresa no Calypso e SAP
- Contas monitoradas por empresa (configuracao versionada)
- Calculo por conta e soma liquida de diferencas

## Slide 9 - O que chega no Slack
- Date
- Monitored accounts (Calypso/SAP)
- Monitored unique accounts
- Accounts with activity / without activity
- Accounts with differences
- Net sum of differences
- Differences by account

## Slide 10 - Impacto observado
- **Saving de ~1h30 por semana**
- Maior velocidade no pre-closing de Futuros
- Melhor visibilidade para o time
- Menor dependencia de checagem manual

## Slide 11 - Riscos, controles e governanca
- Webhook protegido por Databricks Secrets
- Parametros centralizados por task
- Runbook de troubleshooting
- Registro diario de execucoes no Job

## Slide 12 - Proximos passos e CTA
**Evolucoes:**
- Incluir feriados estaduais/municipais por parametro
- Dashboard historico de divergencias
- SLA por severidade

**CTA:**
- Acompanhar o canal oficial diariamente
- Tratar alertas no mesmo dia
- Sugerir melhorias continuas
