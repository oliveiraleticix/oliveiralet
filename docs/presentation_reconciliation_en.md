# Presentation (EN) - Calypso x SAP Reconciliation Automation

## Slide 1 - Title
**Title:** From manual checks to smart flow: our new daily Futures reconciliation  
**Subtitle:** How we improved speed, control, and pre-closing readiness  
**Visual (Nubank style):**
- Dark background: `#111111`
- Primary color: `#820AD1`
- Accent color: `#B266FF`

**Suggested script (30s):**  
"Today I want to share a practical automation we implemented: we turned a manual recurring reconciliation into a daily, monitored, and action-oriented process."

---

## Slide 2 - The problem (before)
**Title:** What was painful in the old process?
- Manual, repetitive routine with operational variability
- Time spent on low-value checks
- Slower response to mismatches before pre-closing
- High dependency on individual context

**Key metric:** ~**1.5 hours saved per week**

---

## Slide 3 - Why we changed
**Title:** What we decided to improve
- Automate Calypso x SAP reconciliation
- Run daily for 3 entities: **BR11, BR12, BR28**
- Send automated Slack notifications
- Tag owners automatically when differences are found

**Core shift:** from "check when possible" to "continuous monitoring".

---

## Slide 4 - The solution
**Title:** How the automation works (simple view)
1. A daily Databricks Job runs one parameterized notebook per entity
2. SQL compares Calypso vs SAP positions
3. System classifies status:
   - `:white_check_mark:` no relevant differences
   - `:warning:` differences found
4. Slack receives a detailed summary by account

---

## Slide 5 - Storyline flow
**Title:** Data-to-action journey
**Flow:**  
Calypso + SAP -> Databricks Job -> Entity-based reconciliation -> Slack status -> Fast team action

**Visual recommendation:** use a clean horizontal process line with purple milestones.

---

## Slide 6 - Business impact
**Title:** What improved in practice
- **~1.5 hours saved per week**
- Faster **Futures pre-closing**
- Lower manual operational risk
- Better team transparency (daily status in Slack)
- Scalable structure for new entities/accounts

---

## Slide 7 - Slack output example
**Title:** What the team receives
- Entity + reference date
- Monitored account counts
- Accounts with and without activity
- Number of differences + net sum
- Differences by account
- Automatic owner mention when needed

---

## Slide 8 - Governance and reliability
**Title:** Built-in controls
- Entity parameterization (BR11/BR12/BR28)
- Default date rule (second prior business day, weekends + BR national holidays)
- Webhook stored in Databricks Secrets
- Runbook for operations and troubleshooting

---

## Slide 9 - What is next
**Title:** Next evolution opportunities
- Add state/municipal holidays by parameter (if needed)
- Build historical differences dashboard
- Define SLA by mismatch severity
- Track monthly quality and efficiency KPIs

---

## Slide 10 - Closing
**Title:** Team call to action
- Use Slack channel as the official daily reconciliation source
- Prioritize same-day response for warnings
- Keep improving rules and observability together

**Final message:**  
"Automation does not replace expertise - it amplifies the team's ability to act faster and better."

---

## Quick design guide (Nubank-style)
**Suggested palette:**
- Primary purple: `#820AD1`
- Light purple: `#B266FF`
- Dark background: `#111111`
- Secondary text gray: `#A0A0A0`
- Main text white: `#FFFFFF`
- Success: `#00C48C`
- Warning: `#FFB020`

**Typography:**
- Titles: sans-serif bold (Inter/Helvetica/Arial)
- Body: sans-serif regular

**Best practices:**
- One main idea per slide
- Keep text concise; tell the story verbally
- Highlight the metric visually (1.5h/week)
- Use real Slack screenshots for credibility
