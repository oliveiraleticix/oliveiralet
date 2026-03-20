# Apresentacao (PT-BR) - Automacao de Reconciliacao Calypso x SAP

## Slide 1 - Titulo
**Titulo:** Da planilha ao fluxo inteligente: nova reconciliacao diaria de Futuros  
**Subtitulo:** Como ganhamos tempo, previsibilidade e qualidade no pre-closing  
**Visual (Nubank):**
- Fundo escuro: `#111111`
- Cor principal: `#820AD1`
- Cor de destaque: `#B266FF`

**Fala sugerida (30s):**  
"Hoje eu quero mostrar uma mudanca simples na superficie, mas muito relevante na pratica: transformamos uma rotina manual de reconciliacao em um processo diario, automatico e monitorado no Slack."

---

## Slide 2 - O problema (antes)
**Titulo:** O que doia no processo anterior?
- Processo manual, repetitivo e sujeito a variacao operacional
- Tempo consumido em checagens de baixo valor
- Resposta mais lenta para desvios antes do pre-closing
- Dependencia de memoria/contexto individual

**Dado-chave:** ~**1h30 de saving semanal**

**Fala sugerida:**  
"Nao era uma dor de um unico dia; era um desgaste recorrente. Todo ciclo, a mesma friccao."

---

## Slide 3 - O gatilho da mudanca
**Titulo:** O que decidimos mudar?
- Automatizar a reconciliacao Calypso x SAP
- Rodar diariamente para 3 empresas: **BR11, BR12, BR28**
- Notificar resultado automaticamente no Slack
- Alertar pessoas responsaveis quando houver diferenca

**Mensagem-chave:** de "verificar quando der" para "monitorar continuamente".

---

## Slide 4 - A solucao
**Titulo:** Como a automacao funciona (visao simples)
1. Job diario no Databricks executa notebook unico parametrizado por empresa
2. Query compara posicoes Calypso x SAP
3. Sistema classifica status:  
   - `:white_check_mark:` sem diferencas relevantes  
   - `:warning:` com diferencas
4. Resultado enviado no Slack com detalhes por conta

**Fala sugerida:**  
"Padronizamos o processo inteiro, com uma fonte unica de verdade e comunicacao proativa."

---

## Slide 5 - Storytelling visual (jornada)
**Titulo:** Jornada do dado ate a decisao
**Fluxo:**  
Calypso + SAP -> Databricks Job -> Reconciliacao por empresa -> Status no Slack -> Acao rapida do time

**Sugestao visual:** setas/etapas em roxo, icones simples, sem excesso de texto.

---

## Slide 6 - O que melhorou na pratica
**Titulo:** Impacto operacional real
- **Saving de ~1h30 por semana**
- Mais velocidade no **pre-closing de Futuros**
- Menor risco operacional manual
- Mais transparencia para o time (status diario visivel)
- Escalavel para novas empresas/contas

---

## Slide 7 - Exemplo de mensagem (Slack)
**Titulo:** O que chega no canal
- Empresa e data de referencia
- Contas monitoradas
- Contas com atividade e sem atividade
- Quantidade de diferencas e soma liquida
- Diferencas por conta
- Mention automatica de responsaveis (quando aplicavel)

**Fala sugerida:**  
"O objetivo nao e so alertar, e direcionar a acao certa, rapido."

---

## Slide 8 - Governanca e confiabilidade
**Titulo:** Controles embutidos no processo
- Parametros por empresa (BR11/BR12/BR28)
- Regra automatica de data (D-2 util, com fim de semana + feriados nacionais BR)
- Segredo de webhook no Databricks Secrets
- Documentacao e runbook de operacao/troubleshooting

---

## Slide 9 - Proximos passos
**Titulo:** Evolucoes planejadas
- Incluir feriados estaduais/municipais por parametro (se necessario)
- Dashboard historico de divergencias
- SLA de tratativa por severidade
- Indicadores mensais de qualidade e eficiencia

---

## Slide 10 - Encerramento (call to action)
**Titulo:** O que esperamos do time
- Usar o canal como fonte oficial diaria da reconciliacao
- Tratar alertas com prioridade no mesmo dia
- Sugerir melhorias continuas no processo

**Mensagem final:**  
"Automacao nao substitui o olhar do time; ela libera o time para decidir melhor e mais rapido."

---

## Guia rapido de design (Nubank-style)
**Paleta sugerida:**
- Roxo principal: `#820AD1`
- Roxo claro: `#B266FF`
- Fundo escuro: `#111111`
- Cinza texto secundario: `#A0A0A0`
- Branco texto principal: `#FFFFFF`
- Sucesso: `#00C48C`
- Alerta: `#FFB020`

**Tipografia sugerida:**
- Titulos: sans-serif bold (ex.: Inter, Helvetica, Arial)
- Corpo: sans-serif regular

**Boas praticas:**
- 1 ideia principal por slide
- Pouco texto, mais narrativa na fala
- Destaque numerico grande (1h30/semana)
- Usar screenshots reais do Slack/fluxo para credibilidade
