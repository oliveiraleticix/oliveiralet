"""Gera planejamento/agenda_nubie_gpa_fi.xlsx (plano de trabalho do Nubie de GPA-FI).

Uso: python planejamento/gerar_agenda_nubie.py
"""

from datetime import date, timedelta
from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule, DataBarRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

INICIO = date(2026, 11, 9)
N_SEMANAS = 18
SAIDA = Path(__file__).with_name("agenda_nubie_gpa_fi.xlsx")

STATUS = ["Não iniciado", "Em andamento", "Bloqueado", "Done"]
FLAGS = ["✔", "Pendente", "N/A"]

ROXO = "820AD1"
HEADER_FILL = PatternFill("solid", fgColor=ROXO)
HEADER_FONT = Font(bold=True, color="FFFFFF")
TITLE_FONT = Font(bold=True, size=14, color=ROXO)
THIN = Side(style="thin", color="D9D9D9")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)

GREEN = PatternFill("solid", fgColor="C6EFCE")
YELLOW = PatternFill("solid", fgColor="FFEB9C")
RED = PatternFill("solid", fgColor="FFC7CE")
BAR = PatternFill("solid", fgColor="B4A7D6")
BAR_DONE = PatternFill("solid", fgColor="63BE7B")


def semana(n):
    ini = INICIO + timedelta(weeks=n - 1)
    return ini, ini + timedelta(days=4)


def periodo(s_ini, s_fim=None):
    s_fim = s_fim or s_ini
    label = f"S{s_ini}" if s_ini == s_fim else f"S{s_ini}–S{s_fim}"
    return semana(s_ini)[0], semana(s_fim)[1], label


# (ID, Frente, Entidade, Fase, Tarefa, Entregável / critério de pronto, Prioridade, (sem_ini, sem_fim), Observações)
BACKLOG = [
    # Onboarding
    ("ONB-01", "Onboarding", "Todas", "Acessos",
     "Solicitar e testar acessos: Databricks (workspace, cluster, schemas Calypso e SAP), repositório Git, "
     "planilhas de reconciliação, caixa/grupo de e-mail onde chegam notas de corretagem e Excel das contrapartes, canais de Slack.",
     "Todos os acessos testados (consegue rodar o notebook e abrir as planilhas).", "Alta", (1, 1), ""),
    ("ONB-02", "Onboarding", "Todas", "Entendimento",
     "Walkthrough com o gestor da recon de out/26 de Futuros, Swap e NDF (fontes, planilha, contas SAP, check com contraparte manual).",
     "Fluxograma as-is por produto (passo a passo, inputs, outputs, tempo gasto hoje).", "Alta", (1, 2), ""),
    ("ONB-03", "Onboarding", "BR11/BR12/BR28", "Entendimento",
     "Estudar o notebook 'recon_futuros_calypso_sap' e o job diário 'reconciliacao_calypso_sap_slack' (queries, tabelas de origem, parâmetros, saídas).",
     "Resumo técnico de 1 página: tabelas usadas, chaves de batimento, saídas geradas.", "Alta", (1, 2), ""),
    ("ONB-04", "Onboarding", "Todas", "Conceitos",
     "Conceitos de produto e contabilização: futuros B3 (ajuste diário, margem, DI1/DOL/IND), swap (pontas, MtM, accrual), "
     "NDF (fixing, PTAX) e contas SAP por produto/entidade.",
     "Glossário + mapa de contas SAP por produto e entidade validado pelo gestor.", "Alta", (1, 2), ""),
    ("ONB-05", "Onboarding", "BR11/BR12", "Conceitos",
     "Leitura introdutória de hedge accounting (BR11 cash flow hedge, BR12 fair value hedge). Somente contexto, sem entregável de automação.",
     "Consegue explicar a diferença entre os dois modelos e onde aparecem na contabilidade.", "Baixa", (2, 2),
     "Escopo de hedge ainda não definido para o Nubie."),
    ("ONB-06", "Onboarding", "Todas", "Padrões",
     "Definir padrões do projeto: pasta/repo, nomenclatura de notebooks e tabelas, parâmetros (run_date, erp_company_code), onde salvar outputs.",
     "Padrão documentado e aprovado pelo gestor.", "Média", (2, 2), ""),
    ("ONB-07", "Onboarding", "Todas", "Shadowing",
     "Acompanhar o fechamento de nov/26 (WD1–WD3) ao lado do gestor: recon de Futuros, Swap e NDF e lançamentos.",
     "Lista de dores/pontos manuais observados no fechamento real.", "Alta", (4, 4), "Fechamento de nov/26 cai em 01–03/12."),

    # Futuros
    ("FUT-01", "Futuros", "BR11/BR12/BR28", "Contraparte",
     "Inventário das contrapartes: corretoras por entidade, formato (nota de corretagem PDF x Excel), remetente, assunto, frequência.",
     "Tabela de inventário com 1 exemplo de arquivo de cada corretora.", "Alta", (2, 3), ""),
    ("FUT-02", "Futuros", "BR11/BR12/BR28", "Contraparte",
     "Definir a ingestão dos anexos do e-mail para o Databricks (ex.: regra de e-mail → pasta compartilhada → Volume/S3; MVP com upload padronizado).",
     "Decisão documentada + pasta de landing criada e testada.", "Alta", (3, 3), "Validar com o gestor/plataforma qual ferramenta é permitida."),
    ("FUT-03", "Futuros", "BR11/BR12/BR28", "Contraparte",
     "Parser dos arquivos Excel das contrapartes → tabela normalizada (data, entidade, corretora, ticker, vencimento, C/V, qtd, preço, ajuste, taxas).",
     "Tabela normalizada carregando 1 mês histórico sem erro.", "Alta", (3, 4), ""),
    ("FUT-04", "Futuros", "BR11/BR12/BR28", "Contraparte",
     "Parser das notas de corretagem (PDF) → mesma tabela normalizada, tratando variações de layout por corretora.",
     "Notas de 1 mês histórico lidas e conferidas por amostragem.", "Alta", (4, 5), ""),
    ("FUT-05", "Futuros", "BR11/BR12/BR28", "Contraparte",
     "Definir regras do batimento Calypso x contraparte: chave, campos comparados (qtd, preço, ajuste, taxas) e tolerância.",
     "Regras aprovadas pelo gestor.", "Alta", (4, 4), ""),
    ("FUT-06", "Futuros", "BR11/BR12/BR28", "Contraparte",
     "Implementar o batimento dentro do notebook 'recon_futuros_calypso_sap' (nova seção 'Check contraparte') com output de quebras "
     "(só Calypso / só contraparte / diferença de valor).",
     "Notebook roda ponta a ponta e gera tabela de quebras.", "Alta", (5, 6), ""),
    ("FUT-07", "Futuros", "BR11/BR12/BR28", "Validação",
     "Rodar para BR12, BR11 e BR28 (parâmetro erp_company_code) e comparar com a recon manual de out/26 e nov/26.",
     "Resultado automático = manual (ou diferenças explicadas).", "Alta", (6, 6), ""),
    ("FUT-08", "Futuros", "BR11/BR12/BR28", "Planilha recon",
     "Exportar as tabelas do notebook para a planilha de reconciliação (abas: Calypso x SAP, Calypso x Contraparte, Quebras, Novos contratos, Liquidações).",
     "Planilha de recon preenchida automaticamente, sem copiar/colar.", "Alta", (6, 7), "Confirmar se a planilha é Excel ou Google Sheets."),
    ("FUT-09", "Futuros", "BR11/BR12/BR28", "Novos/liquidações",
     "Relatório do mês: novos contratos e liquidações (por entidade, ticker, vencimento, valor) como base para lançamentos.",
     "Relatório gerado pelo notebook e exportado para a planilha.", "Alta", (7, 7), ""),
    ("FUT-10", "Futuros", "BR11/BR12/BR28", "Validação",
     "Rodada paralela no fechamento de dez/26 (automático x manual) e ajustes finais.",
     "Fechamento de dez/26 sem diferenças entre manual e automático.", "Alta", (9, 9), "Fechamento de dez/26 cai em 04–06/01/27."),
    ("FUT-11", "Futuros", "BR11/BR12/BR28", "Go-live",
     "Agendar Job no Databricks e alerta no Slack de quebras com a contraparte (reaproveitar webhook existente).",
     "Job agendado e alerta chegando no canal.", "Média", (9, 9), ""),
    ("FUT-12", "Futuros", "BR11/BR12/BR28", "Documentação",
     "Runbook do processo automatizado (como rodar, como tratar quebras, como incluir nova corretora).",
     "Runbook publicado em docs/.", "Média", (7, 8), "Semanas de festas: ritmo mais leve."),

    # Swap
    ("SWP-01", "Swap", "BR12", "Entendimento",
     "Mapear o as-is da recon de swap: fontes no Calypso, contas SAP, planilha atual e qual é a contraparte (confirmações, MtM das contrapartes, registro B3).",
     "Fluxograma as-is + exemplo de arquivo de contraparte.", "Alta", (8, 8), ""),
    ("SWP-02", "Swap", "BR12", "Recon",
     "Extração Calypso parametrizada por data: posição por operação, nocional, MtM e accrual por ponta.", "Query/tabela validada.", "Alta", (9, 10), ""),
    ("SWP-03", "Swap", "BR12", "Recon",
     "Extração SAP: saldos das contas de swap BR12 (ativo/passivo MtM, resultado).", "Query/tabela validada.", "Alta", (9, 10), ""),
    ("SWP-04", "Swap", "BR12", "Recon",
     "Criar notebook 'recon_swap_calypso_sap' com o batimento Calypso x SAP.", "Notebook gera diferenças por conta.", "Alta", (10, 10), ""),
    ("SWP-05", "Swap", "BR12", "Contraparte",
     "Ingestão e parser do arquivo da contraparte (mesma estrutura de landing de Futuros).", "Tabela normalizada da contraparte.", "Alta", (10, 11), ""),
    ("SWP-06", "Swap", "BR12", "Contraparte",
     "Batimento Calypso x contraparte por operação (nocional, taxas, vencimento, MtM com tolerância).", "Tabela de quebras por operação.", "Alta", (11, 11), ""),
    ("SWP-07", "Swap", "BR12", "Novos/liquidações",
     "Visão do mês: novos contratos e liquidações (inclui vencimentos e pagamentos de juros intermediários) para lançamento.",
     "Relatório gerado pelo notebook.", "Alta", (11, 12), ""),
    ("SWP-08", "Swap", "BR12", "Planilha recon", "Exportar as tabelas para a planilha de reconciliação de swap.",
     "Planilha preenchida automaticamente.", "Alta", (12, 12), ""),
    ("SWP-09", "Swap", "BR12", "Validação", "Rodada paralela no fechamento de jan/27 (automático x manual).",
     "Fechamento sem diferenças ou diferenças explicadas.", "Alta", (13, 13), "Fechamento de jan/27 cai em 01–03/02/27."),
    ("SWP-10", "Swap", "BR12", "Go-live", "Job agendado + alerta Slack + runbook.", "Job rodando e runbook publicado.", "Média", (13, 13), ""),

    # NDF
    ("NDF-01", "NDF", "BR12", "Entendimento",
     "Mapear o as-is da recon de NDF: fontes Calypso, contas SAP, planilha atual, contraparte.", "Fluxograma as-is + exemplo de arquivo de contraparte.", "Alta", (12, 12), ""),
    ("NDF-02", "NDF", "BR12", "Recon", "Extrações Calypso (posição, nocional, taxa a termo, MtM) e SAP (saldos das contas de NDF).",
     "Queries/tabelas validadas.", "Alta", (13, 13), ""),
    ("NDF-03", "NDF", "BR12", "Recon", "Criar notebook 'recon_ndf_calypso_sap' com o batimento Calypso x SAP.", "Notebook gera diferenças por conta.", "Alta", (14, 14), "Carnaval 08–09/02/27."),
    ("NDF-04", "NDF", "BR12", "Contraparte", "Ingestão e parser do arquivo da contraparte.", "Tabela normalizada da contraparte.", "Alta", (14, 15), ""),
    ("NDF-05", "NDF", "BR12", "Contraparte", "Batimento Calypso x contraparte por operação (nocional, taxa, vencimento, MtM).", "Tabela de quebras por operação.", "Alta", (15, 15), ""),
    ("NDF-06", "NDF", "BR12", "Contraparte", "Check de liquidação: fixing (PTAX) usado na liquidação x Calypso x contraparte.",
     "Quebras de fixing destacadas no output.", "Média", (15, 15), ""),
    ("NDF-07", "NDF", "BR12", "Novos/liquidações", "Visão do mês: novos contratos e liquidações para lançamento.", "Relatório gerado pelo notebook.", "Alta", (16, 16), ""),
    ("NDF-08", "NDF", "BR12", "Planilha recon", "Exportar as tabelas para a planilha de reconciliação de NDF.", "Planilha preenchida automaticamente.", "Alta", (16, 16), ""),
    ("NDF-09", "NDF", "BR12", "Validação", "Rodada paralela no fechamento de fev/27 (automático x manual).",
     "Fechamento sem diferenças ou diferenças explicadas.", "Alta", (17, 17), "Fechamento de fev/27 cai em 01–03/03/27."),
    ("NDF-10", "NDF", "BR12", "Go-live", "Job agendado + alerta Slack + runbook.", "Job rodando e runbook publicado.", "Média", (17, 17), ""),

    # Consolidação
    ("CON-01", "Consolidação", "Todas", "Go-live",
     "Workflow único no Databricks orquestrando as recons de Futuros, Swap e NDF + relatório consolidado de novos contratos e liquidações.",
     "1 job roda tudo no WD1 e preenche as planilhas.", "Média", (17, 18), ""),
    ("CON-02", "Consolidação", "Todas", "Encerramento", "Apresentar ao time o antes x depois (tempo gasto, quebras encontradas, riscos mitigados).",
     "Apresentação feita.", "Média", (18, 18), ""),
    ("CON-03", "Consolidação", "Todas", "Encerramento", "Retro e backlog da fase 2 (ex.: hedge accounting, novas entidades/produtos).",
     "Backlog fase 2 priorizado com o gestor.", "Baixa", (18, 18), ""),

    # DF Finance Forge
    ("DF-01", "DF Finance Forge", "BR11/BR12", "Alinhamento",
     "Entender o escopo e o cronograma do projeto da DF de derivativos e hedge no Finance Forge e combinar com o gestor/time onde o Nubie entra.",
     "Escopo do Nubie no projeto definido (pode ajustar os itens DF abaixo).", "Média", (3, 3), "A definir com o gestor."),
    ("DF-02", "DF Finance Forge", "BR11/BR12", "Requisitos",
     "Mapear cada número das notas de derivativos e hedge (valor justo por hierarquia, nocional por vencimento, MtM ativo/passivo por instrumento, "
     "sensibilidade, hedge: objeto, instrumento, efetividade, reserva de cash flow hedge) e de onde vem cada um.",
     "Matriz 'número da nota → fonte → responsável'.", "Média", (5, 7), "Sugestão."),
    ("DF-03", "DF Finance Forge", "BR11/BR12", "Dados",
     "Reaproveitar as tabelas das recons automatizadas (posição por produto/entidade/vencimento, nocional, MtM) como tabelas-base para o Forge.",
     "Tabelas-base disponíveis e documentadas.", "Média", (10, 12), "Sugestão. Sinergia direta com as recons."),
    ("DF-04", "DF Finance Forge", "BR11/BR12", "Dados",
     "Rollforward de derivativos por produto: saldo inicial + novos contratos − liquidações ± MtM = saldo final (usa os relatórios de novos/liquidados).",
     "Rollforward fechando com o SAP.", "Média", (12, 14), "Sugestão."),
    ("DF-05", "DF Finance Forge", "BR11/BR12", "Validação",
     "Tie-out: amarrar os números gerados pelo Forge x recons x SAP x DF do período anterior.",
     "Checklist de amarração preenchido e diferenças explicadas.", "Média", (15, 16), "Sugestão."),
    ("DF-06", "DF Finance Forge", "BR11/BR12", "Documentação",
     "Dicionário de dados e lineage das tabelas usadas na DF de derivativos e hedge.", "Documento publicado.", "Baixa", (16, 18), "Sugestão."),
]

# (ID, Atividade, Frente, Periodicidade, Quando, Entregável, A partir de, Observações)
ROTINA = [
    ("R-D1", "Salvar na pasta de landing os anexos (notas de corretagem / Excel) recebidos por e-mail", "Futuros", "Diária", "Até 10h",
     "Arquivos do dia na pasta", "S3", "Some quando a ingestão automática (FUT-02) estiver no ar."),
    ("R-D2", "Checar alerta do Slack do job Calypso x SAP (D-2 útil) e registrar a explicação das quebras", "Futuros", "Diária", "Manhã",
     "Quebras explicadas ou escaladas", "S2", ""),
    ("R-D3", "Checar resultado do check com a contraparte de futuros e tratar quebras com a corretora", "Futuros", "Diária", "Manhã",
     "Quebras tratadas", "S10", "Após go-live (FUT-11)."),
    ("R-S1", "Atualizar status e datas nesta planilha (aba Backlog)", "Gestão", "Semanal", "Segunda-feira", "Planilha atualizada", "S1", ""),
    ("R-S2", "1:1 / status com o gestor: progresso, bloqueios e próximas prioridades", "Gestão", "Semanal", "Segunda-feira",
     "Bloqueios endereçados", "S1", ""),
    ("R-S3", "Revisão das quebras em aberto (aging) de todas as recons automatizadas", "Recons", "Semanal", "Sexta-feira",
     "Lista de quebras com responsável e prazo", "S10", ""),
    ("R-M1", "Rodar recon completa de Futuros BR11/BR12/BR28 (Calypso x SAP + contraparte) e atualizar a planilha", "Futuros", "Mensal", "WD1",
     "Planilha de recon preenchida", "Fech. dez/26", ""),
    ("R-M2", "Gerar relatório de novos contratos e liquidações do mês (Futuros, Swap, NDF) e enviar para lançamento", "Recons", "Mensal", "WD1–WD2",
     "Relatório enviado", "Fech. dez/26", "Swap a partir de jan/27, NDF a partir de fev/27."),
    ("R-M3", "Rodar recon completa de Swap BR12 (Calypso x SAP + contraparte) e atualizar a planilha", "Swap", "Mensal", "WD2",
     "Planilha de recon preenchida", "Fech. jan/27", ""),
    ("R-M4", "Rodar recon completa de NDF BR12 (Calypso x SAP + contraparte) e atualizar a planilha", "NDF", "Mensal", "WD2",
     "Planilha de recon preenchida", "Fech. fev/27", ""),
    ("R-M5", "Revisão com o gestor e sign-off das recons; arquivar evidências", "Recons", "Mensal", "WD3", "Recons assinadas", "Fech. dez/26", ""),
    ("R-M6", "Conferir se os lançamentos foram feitos e reexecutar as recons para confirmar zeradas", "Recons", "Mensal", "WD5",
     "Recons zeradas ou pendências justificadas", "Fech. dez/26", ""),
    ("R-M7", "Melhoria contínua: registrar o que ainda é manual e propor próximo ajuste", "Gestão", "Mensal", "Última semana do mês",
     "1 melhoria proposta", "S4", ""),
    ("R-T1", "Suporte à DF de derivativos e hedge (tabelas-base, rollforward, tie-out)", "DF Finance Forge", "Trimestral", "Fechamento trimestral",
     "Tie-out preenchido", "Fech. dez/26", "Conforme escopo definido em DF-01."),
]

MESES = ["nov/26", "dez/26", "jan/27", "fev/27", "mar/27", "abr/27", "mai/27", "jun/27"]


def style_header(ws, row, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = CENTER
        cell.border = BORDER


def set_widths(ws, widths):
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


def status_formatting(ws, rng):
    ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"Done"'], fill=GREEN))
    ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"Em andamento"'], fill=YELLOW))
    ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"Bloqueado"'], fill=RED))


def build_leiame(wb):
    ws = wb.active
    ws.title = "Leia-me"
    linhas = [
        ("Plano de trabalho – Nubie GPA-FI (Derivativos)", TITLE_FONT),
        ("", None),
        ("Objetivo", Font(bold=True)),
        ("Automatizar o ciclo completo das reconciliações de derivativos (Futuros BR11/BR12/BR28, Swap BR12 e NDF BR12): "
         "Calypso x SAP, check com a contraparte, visão de novos contratos e liquidações do mês e preenchimento automático da planilha de recon. "
         "Em paralelo, apoiar o projeto da DF de derivativos e hedge no Finance Forge.", None),
        ("", None),
        ("Como usar", Font(bold=True)),
        ("1. Backlog: lista de entregas com datas previstas. Atualize a coluna Status (lista suspensa). Ao marcar 'Done', o ✔ aparece e a linha fica verde.", None),
        ("2. Rotina: atividades recorrentes com periodicidade (diária, semanal, mensal, trimestral) e a partir de quando entram em vigor.", None),
        ("3. Checklist Mensal: marque ✔ / Pendente / N/A para cada atividade do fechamento em cada mês.", None),
        ("4. Cronograma: Gantt semanal gerado a partir do Backlog (barra roxa = planejado, verde = done). Alterar datas no Backlog atualiza o Gantt.", None),
        ("5. Dashboard: % concluído por frente, calculado automaticamente.", None),
        ("", None),
        ("Fases (semanas a partir de 09/11/2026)", Font(bold=True)),
        ("S1–S2  Onboarding (acessos, entendimento do as-is, conceitos).", None),
        ("S2–S9  Futuros: check com contraparte no notebook 'recon_futuros_calypso_sap' + export para a planilha + novos/liquidações. Paralelo no fechamento de dez/26.", None),
        ("S8–S13 Swap BR12: recon ponta a ponta no notebook + contraparte. Paralelo no fechamento de jan/27.", None),
        ("S12–S17 NDF BR12: recon ponta a ponta no notebook + contraparte. Paralelo no fechamento de fev/27.", None),
        ("S17–S18 Consolidação: workflow único, apresentação e backlog da fase 2.", None),
        ("S3–S18 DF Finance Forge (paralelo, prioridade média): itens sugeridos, a validar em DF-01.", None),
        ("", None),
        ("Premissas", Font(bold=True)),
        ("Início em 09/11/2026. Feriados no período: 20/11 (Consciência Negra), 25/12, 01/01 e Carnaval 08–09/02/27. Semanas de 21/12 e 28/12 com ritmo mais leve.", None),
        ("Hedge accounting (BR11 cash flow / BR12 fair value): sem entrega específica; apenas leitura de contexto (ONB-05).", None),
        ("", None),
        ("Pontos em aberto para o gestor decidir", Font(bold=True)),
        ("• Planilha de reconciliação é Excel ou Google Sheets? (define como será o export do FUT-08).", None),
        ("• Ferramenta permitida para levar os anexos do e-mail até o Databricks (FUT-02).", None),
        ("• Qual é a contraparte de Swap e NDF (confirmações, arquivo de MtM do banco, registro B3).", None),
        ("• Escopo do Nubie no projeto da DF no Finance Forge (DF-01).", None),
    ]
    for i, (texto, fonte) in enumerate(linhas, start=1):
        c = ws.cell(row=i, column=1, value=texto)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        if fonte:
            c.font = fonte
    ws.column_dimensions["A"].width = 150

    ws.cell(row=1, column=3, value="Legenda de status").font = Font(bold=True)
    for i, (s, fill) in enumerate(zip(STATUS, [None, YELLOW, RED, GREEN]), start=2):
        c = ws.cell(row=i, column=3, value=s)
        c.border = BORDER
        if fill:
            c.fill = fill
    ws.column_dimensions["C"].width = 18


def build_backlog(wb):
    ws = wb.create_sheet("Backlog")
    headers = ["ID", "Frente", "Entidade", "Fase", "Tarefa", "Entregável / critério de pronto", "Prioridade",
               "Início previsto", "Fim previsto", "Semanas", "Dono", "Status", "✔", "Data conclusão", "Observações / bloqueios"]
    ws.append(headers)
    style_header(ws, 1, len(headers))

    for item in BACKLOG:
        id_, frente, ent, fase, tarefa, entregavel, prio, (s1, s2), obs = item
        ini, fim, label = periodo(s1, s2)
        r = ws.max_row + 1
        ws.append([id_, frente, ent, fase, tarefa, entregavel, prio, ini, fim, label, "Nubie", "Não iniciado",
                   f'=IF(L{r}="Done","✔","")', None, obs])

    last = ws.max_row
    for row in ws.iter_rows(min_row=2, max_row=last, max_col=len(headers)):
        for c in row:
            c.alignment = WRAP
            c.border = BORDER
    for r in range(2, last + 1):
        for col in ("H", "I", "N"):
            ws[f"{col}{r}"].number_format = "DD/MM/YYYY"
        for col in ("A", "G", "J", "K", "L", "M"):
            ws[f"{col}{r}"].alignment = CENTER
        ws[f"M{r}"].font = Font(bold=True, color="006100", size=12)

    dv_status = DataValidation(type="list", formula1=f'"{",".join(STATUS)}"', allow_blank=False)
    dv_prio = DataValidation(type="list", formula1='"Alta,Média,Baixa"', allow_blank=True)
    ws.add_data_validation(dv_status)
    ws.add_data_validation(dv_prio)
    dv_status.add(f"L2:L{last}")
    dv_prio.add(f"G2:G{last}")

    status_formatting(ws, f"L2:L{last}")
    ws.conditional_formatting.add(f"A2:K{last}", FormulaRule(formula=[f'$L2="Done"'], fill=GREEN))
    ws.conditional_formatting.add(f"N2:O{last}", FormulaRule(formula=[f'$L2="Done"'], fill=GREEN))

    set_widths(ws, [9, 16, 15, 16, 60, 42, 10, 12, 12, 10, 9, 14, 5, 13, 34])
    ws.freeze_panes = "F2"
    ws.auto_filter.ref = f"A1:O{last}"
    return last


def build_rotina(wb):
    ws = wb.create_sheet("Rotina")
    headers = ["ID", "Atividade", "Frente", "Periodicidade", "Quando", "Entregável", "A partir de", "Observações"]
    ws.append(headers)
    style_header(ws, 1, len(headers))
    for item in ROTINA:
        ws.append(list(item))
    last = ws.max_row
    for row in ws.iter_rows(min_row=2, max_row=last, max_col=len(headers)):
        for c in row:
            c.alignment = WRAP
            c.border = BORDER
    for r in range(2, last + 1):
        for col in ("A", "D", "E", "G"):
            ws[f"{col}{r}"].alignment = CENTER
    cores = {"Diária": "DDEBF7", "Semanal": "E2EFDA", "Mensal": "FFF2CC", "Trimestral": "FCE4D6"}
    for per, cor in cores.items():
        ws.conditional_formatting.add(f"D2:D{last}", CellIsRule(operator="equal", formula=[f'"{per}"'],
                                                                fill=PatternFill("solid", fgColor=cor)))
    set_widths(ws, [7, 70, 16, 13, 16, 32, 13, 40])
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = f"A1:H{last}"


def build_checklist(wb):
    ws = wb.create_sheet("Checklist Mensal")
    ws["A1"] = "Checklist do fechamento – marque ✔ / Pendente / N/A (mês = competência do fechamento)"
    ws["A1"].font = TITLE_FONT
    headers = ["ID", "Atividade", "Quando"] + MESES
    ws.append([])
    ws.append(headers)
    style_header(ws, 3, len(headers))
    mensais = [r for r in ROTINA if r[3] in ("Mensal", "Trimestral")]
    inicio_por_id = {"R-M1": 1, "R-M2": 1, "R-M3": 2, "R-M4": 3, "R-M5": 1, "R-M6": 1, "R-M7": 0, "R-T1": 1}
    for r in mensais:
        primeiro = inicio_por_id.get(r[0], 0)
        valores = []
        for i, mes in enumerate(MESES):
            trimestral_fora = r[3] == "Trimestral" and mes.split("/")[0] not in ("dez", "mar", "jun", "set")
            valores.append("N/A" if i < primeiro or trimestral_fora else "Pendente")
        ws.append([r[0], r[1], r[4]] + valores)
    last = ws.max_row
    for row in ws.iter_rows(min_row=4, max_row=last, max_col=len(headers)):
        for c in row:
            c.border = BORDER
            c.alignment = CENTER if c.column != 2 else WRAP
    rng = f"D4:{get_column_letter(len(headers))}{last}"
    dv = DataValidation(type="list", formula1=f'"{",".join(FLAGS)}"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(rng)
    ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"✔"'], fill=GREEN))
    ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"Pendente"'], fill=YELLOW))
    ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"N/A"'],
                                                  fill=PatternFill("solid", fgColor="EDEDED")))
    set_widths(ws, [7, 70, 16] + [10] * len(MESES))
    ws.freeze_panes = "D4"


def build_cronograma(wb, backlog_last):
    ws = wb.create_sheet("Cronograma")
    fixed = ["ID", "Frente", "Tarefa", "Início", "Fim", "Status"]
    week_starts = [semana(n)[0] for n in range(1, N_SEMANAS + 1)]
    ws.append(fixed + [f"S{n}" for n in range(1, N_SEMANAS + 1)])
    ws.append([""] * len(fixed) + week_starts)
    style_header(ws, 1, len(fixed) + N_SEMANAS)
    style_header(ws, 2, len(fixed) + N_SEMANAS)
    for c in range(len(fixed) + 1, len(fixed) + N_SEMANAS + 1):
        ws.cell(row=2, column=c).number_format = "DD/MM"
        ws.column_dimensions[get_column_letter(c)].width = 6.5

    for i, br in enumerate(range(2, backlog_last + 1)):
        r = 3 + i
        ws.append([f"=Backlog!A{br}", f"=Backlog!B{br}", f"=Backlog!E{br}", f"=Backlog!H{br}",
                   f"=Backlog!I{br}", f"=Backlog!L{br}"])
        ws[f"D{r}"].number_format = "DD/MM/YY"
        ws[f"E{r}"].number_format = "DD/MM/YY"
        for c in range(1, len(fixed) + N_SEMANAS + 1):
            ws.cell(row=r, column=c).border = BORDER
        ws[f"C{r}"].alignment = Alignment(vertical="top", wrap_text=False, shrink_to_fit=False)

    last = 2 + (backlog_last - 1)
    first_w = get_column_letter(len(fixed) + 1)
    last_w = get_column_letter(len(fixed) + N_SEMANAS)
    rng = f"{first_w}3:{last_w}{last}"
    em_semana = f"AND({first_w}$2<=$E3,{first_w}$2+4>=$D3)"
    ws.conditional_formatting.add(rng, FormulaRule(formula=[f'AND({em_semana},$F3="Done")'], fill=BAR_DONE, stopIfTrue=True))
    ws.conditional_formatting.add(rng, FormulaRule(formula=[em_semana], fill=BAR))
    ws.conditional_formatting.add(rng, FormulaRule(formula=[f"AND(TODAY()>={first_w}$2,TODAY()<={first_w}$2+6)"],
                                                   border=Border(left=Side(style="medium", color="C00000"),
                                                                 right=Side(style="medium", color="C00000"))))
    status_formatting(ws, f"F3:F{last}")
    set_widths(ws, [9, 16, 55, 10, 10, 13])
    ws.freeze_panes = "G3"


def build_dashboard(wb):
    ws = wb.create_sheet("Dashboard")
    ws["A1"] = "Dashboard – andamento do plano"
    ws["A1"].font = TITLE_FONT
    headers = ["Frente", "Total", "Done", "Em andamento", "Bloqueado", "Não iniciado", "% concluído", "Atrasadas"]
    ws.append([])
    ws.append(headers)
    style_header(ws, 3, len(headers))
    frentes = []
    for item in BACKLOG:
        if item[1] not in frentes:
            frentes.append(item[1])
    for f in frentes + ["Total"]:
        r = ws.max_row + 1
        crit = '"*"' if f == "Total" else f"$A{r}"
        ws.append([
            f,
            f"=COUNTIFS(Backlog!$B:$B,{crit},Backlog!$A:$A,\"?*\")-IF($A{r}=\"Total\",1,0)",
            f'=COUNTIFS(Backlog!$B:$B,{crit},Backlog!$L:$L,"Done")',
            f'=COUNTIFS(Backlog!$B:$B,{crit},Backlog!$L:$L,"Em andamento")',
            f'=COUNTIFS(Backlog!$B:$B,{crit},Backlog!$L:$L,"Bloqueado")',
            f'=COUNTIFS(Backlog!$B:$B,{crit},Backlog!$L:$L,"Não iniciado")',
            f"=IF(B{r}=0,0,C{r}/B{r})",
            f'=COUNTIFS(Backlog!$B:$B,{crit},Backlog!$I:$I,"<"&TODAY(),Backlog!$L:$L,"<>Done")',
        ])
        ws[f"G{r}"].number_format = "0%"
        for c in range(1, len(headers) + 1):
            ws.cell(row=r, column=c).border = BORDER
            ws.cell(row=r, column=c).alignment = CENTER
        if f == "Total":
            for c in range(1, len(headers) + 1):
                ws.cell(row=r, column=c).font = Font(bold=True)
    last = ws.max_row
    ws.conditional_formatting.add(f"G4:G{last}", DataBarRule(start_type="num", start_value=0, end_type="num",
                                                              end_value=1, color="63BE7B"))
    ws.conditional_formatting.add(f"H4:H{last}", CellIsRule(operator="greaterThan", formula=["0"], fill=RED))
    ws.cell(row=last + 2, column=1, value="Atrasadas = fim previsto já passou e status diferente de Done.").font = Font(italic=True, color="7F7F7F")
    set_widths(ws, [18, 8, 8, 14, 11, 13, 13, 11])


def main():
    wb = Workbook()
    build_leiame(wb)
    backlog_last = build_backlog(wb)
    build_rotina(wb)
    build_checklist(wb)
    build_cronograma(wb, backlog_last)
    build_dashboard(wb)
    wb.save(SAIDA)
    print(f"Gerado: {SAIDA}")


if __name__ == "__main__":
    main()
