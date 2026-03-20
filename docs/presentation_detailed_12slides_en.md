# Detailed Presentation (EN) - 12 slides

## Slide 1 - Cover
**Title:** Automated Calypso x SAP Reconciliation  
**Subtitle:** Operational efficiency and faster Futures pre-closing

## Slide 2 - Agenda
1. Context
2. Operational pain points
3. Objectives
4. Implemented solution
5. Architecture
6. Core rules
7. Daily flow
8. Slack communication
9. Business impact
10. Risk and controls
11. Next improvements
12. Call to action

## Slide 3 - Process context
- Daily reconciliation between Calypso and SAP
- Critical for confidence before pre-closing
- Need to reduce recurring manual effort

## Slide 4 - Key pain points before automation
- Manual execution dependent on individual routine
- Limited process standardization
- Time consumed by repetitive checks
- Slower response to mismatches

## Slide 5 - Initiative goals
- Automate daily execution
- Standardize reconciliation criteria
- Provide team-wide Slack visibility
- Reduce manual effort and operational risk

## Slide 6 - Delivered solution
- Single Databricks notebook
- Entity parameterization: `BR11`, `BR12`, `BR28`
- Daily Job with 3 tasks (one per entity)
- Slack notification with status and account details

## Slide 7 - Architecture (simple view)
**Flow:**  
Calypso + SAP -> Databricks Job -> Reconciliation query -> Difference analysis -> Slack

**Controls:**  
- Webhook in Databricks Secrets  
- Configurable tolerance  
- Automatic mentions when mismatches exist

## Slide 8 - Core notebook rules
- Empty `run_date`: uses second prior business day (weekends + BR national holidays)
- Entity filter applied in Calypso and SAP
- Account lists maintained per entity
- Account-level and net difference calculations

## Slide 9 - Slack output content
- Date
- Monitored accounts (Calypso/SAP)
- Monitored unique accounts
- Accounts with / without activity
- Accounts with differences
- Net sum of differences
- Differences by account

## Slide 10 - Observed impact
- **~1.5 hours saved per week**
- Faster Futures pre-closing
- Better team-level transparency
- Lower dependency on manual checks

## Slide 11 - Risk, controls, governance
- Secure webhook management via Secrets
- Task-level parameter governance
- Operational runbook for troubleshooting
- Daily execution traceability in Databricks Jobs

## Slide 12 - Next steps and CTA
**Potential improvements:**
- Add state/municipal holidays by parameter
- Build historical differences dashboard
- Define severity-based SLA

**CTA:**
- Follow the official Slack channel daily
- Resolve warnings on the same day
- Share continuous improvement ideas
