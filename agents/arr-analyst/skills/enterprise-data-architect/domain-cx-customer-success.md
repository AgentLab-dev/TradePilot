# Domain — CX (Customer Experience / Customer Success)

Owner: CX Analytics Engineering team.
Project: `eda-dbt-cx`.
Output DBs (three sub-domains):
- `ACTIVATION_USAGE_ADOPTION_PROD` + `ACTIVATION_USAGE_ADOPTION_INT_PROD` — product usage / feature adoption
- `LOYALTY_ADVOCACY_PROD` + `LOYALTY_ADVOCACY_INT_PROD` — NPS / health / advocacy
- `PRODUCT_IMPLEMENTATION_PROD` + `PRODUCT_IMPLEMENTATION_INT_PROD` — PSO / time-to-value

Primary sources: Gainsight, Medallia, Qualtrics, Zendesk, ServiceNow, product telemetry (FullStory / Mixpanel / Pendo), Workday Professional Services.

---

## §1. What this domain owns

| Sub-domain | What it covers |
|---|---|
| **ACTIVATION_USAGE_ADOPTION** | Feature usage, product adoption funnels, active users, time-in-app, login frequency, feature penetration, depth-of-usage |
| **LOYALTY_ADVOCACY** | Customer health scores, NPS, CSAT, advocacy programs, references, churn risk, renewal probability, executive sentiment |
| **PRODUCT_IMPLEMENTATION** | PSO project tracking, implementation milestones, time-to-value, go-live dates, project health |

What this domain does NOT own:
- ❌ ARR / billing — that's Finance
- ❌ Sales pipeline / forecasting — that's Sales/GTM
- ❌ Marketing campaigns — that's Marketing
- ❌ Support ticket volume by product (operational metric) — owned, but consumed by Product / Engineering separately

---

## §2. Source systems

| System | Connector | Refresh | Sub-domain | Primary tables |
|---|---|---|---|---|
| **Gainsight** | Fivetran | 1 hr | Loyalty | `COMPANY`, `ACTIVITY`, `CTA` (calls-to-action), `SUCCESS_PLAN`, `JOURNEY_ORCHESTRATOR_PARTICIPANT`, `CUSTOMER_360` |
| **Medallia** | Fivetran | Daily | Loyalty | `SURVEY_RESPONSE`, `NPS_SCORE`, `RESPONSE_DETAIL`, `THEME` |
| **Qualtrics** | Fivetran | Daily | Loyalty (also EX) | `SURVEY`, `RESPONSE`, `EMPLOYEE_RESPONSE` |
| **Zendesk** | Fivetran | 1 hr | Activation (also Support) | `TICKET`, `TICKET_COMMENT`, `USER`, `ORGANIZATION`, `SATISFACTION_RATING` |
| **ServiceNow** | Fivetran | 1 hr | Activation (Support) | `INCIDENT`, `CHANGE_REQUEST`, `SC_REQUEST` |
| **FullStory** | Fivetran | Daily | Activation | `EVENT`, `SESSION`, `PAGE` — product telemetry |
| **Mixpanel** | Fivetran | 4 hr | Activation | `EVENT`, `PEOPLE`, `COHORT` |
| **Pendo** | Fivetran | Daily | Activation | `VISITOR`, `ACCOUNT`, `FEATURE_USAGE`, `GUIDE_VIEW` |
| **Workday Professional Services** | Custom | Daily | Implementation | Project plans, milestones, resource hours |
| **Custom telemetry (Snowpipe)** | Snowpipe (Kafka) | ~1 min | Activation | `PRODUCT_EVENT_STREAM` — application telemetry |

---

## §3. Sub-domain 1: ACTIVATION_USAGE_ADOPTION

### 3.1 Purpose
Measure how customers use the product post-purchase. Drives onboarding optimization, feature adoption campaigns, and product roadmap decisions.

### 3.2 Key metrics

| Metric | Definition |
|---|---|
| **Time-to-first-value (TTFV)** | Days from contract signing → first meaningful product use |
| **Active users (DAU/WAU/MAU)** | Daily / weekly / monthly active users per tenant |
| **Feature adoption rate** | % of users using feature X within Y days of provisioning |
| **Depth of usage** | Avg actions per session, feature coverage % |
| **Login frequency** | Logins per user per week |
| **Stickiness** | DAU / MAU ratio (engagement intensity) |
| **Tenant health score** | Composite: activation + usage + engagement |

### 3.3 Key models

| Model | Schema | Grain |
|---|---|---|
| `WD_TENANT_ACTIVATION_SCD2` | `MANAGED` | Tenant × snapshot (when activated, when first used) |
| `BT_FEATURE_ADOPTION` | `MANAGED` | Tenant × feature × day (adoption events) |
| `AGG_TENANT_ACTIVITY_DAILY` | `AGGREGATIONS` | Tenant × day (DAU + actions count) |
| `AGG_TENANT_ACTIVITY_WEEKLY` | `AGGREGATIONS` | Tenant × week |
| `DASH_TENANT_USAGE_TRENDS` | `DATA_PRODUCTS` | Executive dashboard |

### 3.4 Common gotchas
- Product telemetry has **bot traffic** (automated scripts, scraping) — filter `user_agent NOT LIKE '%bot%'`
- Multi-tenant tenants have nested user populations — count distinct users at the tenant level, not aggregate
- Some features have multi-step adoption (e.g., "Goals" requires both creating + activating); define adoption explicitly per feature

---

## §4. Sub-domain 2: LOYALTY_ADVOCACY (the customer-health hub)

### 4.1 Purpose
Measure customer sentiment + predict churn risk + drive CS interventions.

### 4.2 The Customer Health Score

A composite score (typically 0-100) per account/tenant that predicts renewal likelihood.

**Inputs** (weights vary; reviewed quarterly):

| Dimension | Weight | Source |
|---|---|---|
| Product usage | 25% | `AGG_TENANT_ACTIVITY_DAILY` |
| Support tickets | 15% | Zendesk (volume + severity + CSAT on resolution) |
| NPS trend | 15% | Medallia (trailing 6-mo) |
| Executive engagement | 10% | Gainsight (exec sponsor meetings) |
| Implementation health | 10% | PSO project status (active / overdue / at risk) |
| Renewal proximity | 10% | Days to contract end |
| Expansion signals | 10% | Cross-sell intent (Gainsight, sales notes) |
| Risk flags | 5% | Manual CSM-flagged risk (Gainsight CTAs) |

Score buckets:
- 80-100: **Green** (healthy, likely renewal)
- 60-79: **Yellow** (watch, intervene)
- 40-59: **Orange** (at risk, formal save plan)
- 0-39: **Red** (high churn risk, exec escalation)

Canonical view: `LOYALTY_ADVOCACY_PROD.MANAGED.CUSTOMER_HEALTH_SCORE`
- Grain: Account × snapshot_date
- Daily refresh

### 4.3 NPS / CSAT

**NPS (Net Promoter Score)**: -100 to +100, based on "How likely are you to recommend us?" (0-10 scale).
- Promoters (9-10), Passives (7-8), Detractors (0-6)
- `NPS = %Promoters - %Detractors`

**CSAT (Customer Satisfaction)**: usually post-support-interaction, 1-5 rating.
- `CSAT = % Satisfied (4-5) / Total Responses`

Sources:
- Medallia — primary NPS surveys (relationship + transactional)
- Qualtrics — supplementary surveys (specific programs, events)
- Zendesk — post-ticket CSAT
- Workday Community — informal "thumbs up/down" feedback

Models:
- `LOYALTY_ADVOCACY_PROD.MANAGED.NPS_RESPONSES` — raw + cleaned NPS responses
- `LOYALTY_ADVOCACY_PROD.AGGREGATIONS.NPS_BY_ACCOUNT` — NPS rollup per account per quarter
- `LOYALTY_ADVOCACY_PROD.AGGREGATIONS.NPS_TREND_BY_PRODUCT_LINE` — NPS trend by product

### 4.4 Churn risk score (predictive)

ML-based churn risk score (separate from rule-based health score):
- Features: usage trend, NPS trend, support tickets, support CSAT, contract characteristics, CSM-flagged risks
- Model: gradient-boosted classifier (XGBoost / LightGBM), retrained monthly
- Output: `churn_risk_score` (0-1 probability of not renewing)

Lives in: `LOYALTY_ADVOCACY_PROD.MANAGED.CHURN_RISK_SCORE`
- Built by ML team in Snowpark / external Python notebooks
- Joined into customer health dashboards

CS team uses churn risk + health score together — they capture different signals.

### 4.5 Gainsight CTAs (calls-to-action)

Gainsight surfaces "CTAs" — automated alerts to CSMs based on rules:
- "Account hasn't logged in for 30 days" → CTA created → CSM assigned to outreach
- "NPS dropped from 9 to 4" → CTA created → CSM investigates
- "Contract renewal in 90 days" → CTA created → CSM prepares renewal plan

CTAs lifecycle: Created → Assigned → In Progress → Resolved.

Models:
- `LOYALTY_ADVOCACY_PROD.MANAGED.GAINSIGHT_CTA_ACTIVITY` — CTA events + resolution
- `LOYALTY_ADVOCACY_PROD.AGGREGATIONS.CSM_CTA_RESOLUTION_RATE` — CSM performance metric

---

## §5. Sub-domain 3: PRODUCT_IMPLEMENTATION

### 5.1 Purpose
Track Workday Professional Services (PSO) engagements: implementation projects, milestones, time-to-value, project health.

### 5.2 Implementation lifecycle

```
Contract signed
   ↓
PSO project created (in Workday PS Automation)
   ↓
Discovery → Design → Build → Test → Deploy → Live → Hypercare
   ↓
Go-live milestone hit
   ↓
Customer transitions to CSM (Loyalty domain)
```

### 5.3 Key metrics

| Metric | Definition |
|---|---|
| **Time-to-go-live** | Days from contract sign → first production go-live |
| **Project health** | Composite: schedule, budget, scope, customer satisfaction |
| **% of projects on time** | At each milestone (Design / Build / Go-Live) |
| **% over budget** | Hours billed vs estimate |
| **Implementation NPS** | Customer NPS at go-live |
| **Resource utilization** | PSO consultant billable utilization % |

### 5.4 Key models

| Model | Schema | Grain |
|---|---|---|
| `WD_PSO_PROJECT_SCD2` | `MANAGED` | Project × snapshot |
| `WD_PSO_MILESTONE` | `MANAGED` | Milestone × project |
| `AGG_PROJECT_HEALTH_DAILY` | `AGGREGATIONS` | Project × day (health score) |
| `DASH_IMPLEMENTATION_TIME_TO_VALUE` | `DATA_PRODUCTS` | Aggregate trends |

---

## §6. Support analytics (cross-cutting)

Support sits primarily in ACTIVATION sub-domain but feeds health scoring too.

| Metric | Source |
|---|---|
| **Ticket volume per account** | Zendesk |
| **Avg time-to-resolution** | Zendesk |
| **% of tickets resolved on first contact** | Zendesk |
| **Post-ticket CSAT** | Zendesk satisfaction survey |
| **Incident frequency by product** | ServiceNow + Zendesk |
| **Escalation rate** | Zendesk (level-1 → level-2 → engineering) |

Models live in `ACTIVATION_USAGE_ADOPTION_PROD.MANAGED.WD_SUPPORT_TICKETS_SCD2`. Support team has their own dashboards reading directly from this.

---

## §7. Voice of Customer (VoC) — Medallia + Qualtrics + Community

Workday runs an integrated VoC program:

| Source | Type | Cadence |
|---|---|---|
| **Medallia** | Relationship NPS (overall sentiment) | Quarterly per account |
| **Medallia** | Transactional NPS (post-event) | Per event (training, support interaction, etc.) |
| **Qualtrics** | Product-specific surveys | Ad-hoc per product launch |
| **Workday Community** | Forum sentiment + idea voting | Continuous |

VoC unified view: `LOYALTY_ADVOCACY_PROD.MANAGED.VOC_UNIFIED_RESPONSE`
- Grain: response × source × account
- Themes extracted via Medallia AI (theme tagging) → joined to Workday product taxonomy

VoC themes drive product roadmap. Top themes reviewed monthly by Product Council.

---

## §8. Customer 360 (the "single pane")

Gainsight's "Customer 360" pulls together everything per account:
- ARR + contract details (from Finance)
- Health score (Loyalty)
- Open CTAs (Loyalty)
- Recent activity (Activation)
- Recent NPS (Loyalty)
- Open support tickets (Activation)
- Implementation status (Implementation)
- CSM owner + recent meetings (Loyalty)

CSMs use this view daily. We materialize an equivalent for analytics:
- `LOYALTY_ADVOCACY_PROD.DATA_PRODUCTS.CUSTOMER_360_VIEW`
- Joins data from all 3 CX sub-domains + cross-domain refs to Finance + Sales
- Updated daily

---

## §9. Renewal-risk-[REDACTED] ARR (cross-domain integration)

The handoff between CX and Finance for forecasting:

```
Finance: ARR by contract (`FINANCE_LINE_ANALYTICS`)
    +
CX: Churn risk score per account (`CHURN_RISK_SCORE`)
    +
CX: Health score per account (`CUSTOMER_HEALTH_SCORE`)
    │
    ▼
Renewal-adjusted ARR forecast
    "Expected ARR at end of next quarter = sum(arr × (1 - churn_risk))"
```

Lives in `FINANCE_PROD.DATA_PRODUCTS.ARR_FORECAST_RENEWAL_RISK_ADJUSTED` (built by Finance, consumes CX data).

This is the bridge between CX signals and FP&A forecasting.

---

## §10. Churn analysis (post-mortem)

When a customer actually churns:
1. **Detect**: agreement `Status = 'Terminated'` AND no SSR linkage
2. **Categorize**: voluntary (customer chose to leave) vs involuntary (acquired / went out of business)
3. **Attribute**: identify reasons (Gainsight churn surveys, CSM notes, support history)
4. **Quantify**: ARR lost (per contract, per account)
5. **Pattern**: what's the cohort / product / segment pattern?

Models:
- `LOYALTY_ADVOCACY_PROD.MANAGED.CHURN_EVENT` — actual churn events with attribution
- `LOYALTY_ADVOCACY_PROD.AGGREGATIONS.CHURN_REASONS_QUARTERLY` — top reasons
- `LOYALTY_ADVOCACY_PROD.DATA_PRODUCTS.DASH_CHURN_ANALYSIS` — executive churn review

---

## §11. Advocacy program

Top NPS Promoters are recruited into:
- **Reference program** — willing to be a Workday reference for prospects
- **Case study program** — featured in marketing materials
- **Customer Advisory Board** — provides product feedback to Workday execs
- **Workday Rising speaker program** — speaks at the user conference

Lives in `LOYALTY_ADVOCACY_PROD.MANAGED.ADVOCACY_PARTICIPATION`. Marketing taps this for case study sourcing.

---

## §12. Cross-domain dependencies

| Depends on | Why |
|---|---|
| `eda-dbt-base` | All raw source wrappers (Gainsight, Medallia, Zendesk, etc.) |
| `eda-dbt-common` | Fiscal calendar, currency, Reltio MDM |
| `eda-dbt-gtm` | Account dim (`WD_ACCOUNT_SCD2`), Opportunity context |
| `eda-dbt-em` | Agreement dim, ARR per account (for health scoring inputs) |

Consumed by:
| Downstream | Use case |
|---|---|
| `eda-dbt-em` | Customer health → renewal-risk-[REDACTED] ARR forecast |
| `eda-dbt-semantic-layer` | NPS / health / churn risk semantic metrics |
| Sigma BI | Direct queries to `DATA_PRODUCTS` views |

---

## §13. Common gotchas

- **Survey response bias** — Promoters more likely to respond than Detractors → adjust NPS calculation accordingly
- **Multi-tenant identity** — one customer = many user IDs; aggregate at account level for health scoring
- **Implementation projects with no go-live date** — some contracts never go live (cancelled, paused) → exclude from time-to-value averages
- **Test tenants** — Workday's internal QA tenants count as users; filter `is_internal_tenant = TRUE`
- **NPS by product line** — surveys ask "Workday overall" not "Workday HCM specifically"; for product-line NPS, use Qualtrics targeted surveys instead
- **Health score volatility** — health score can swing dramatically week-over-week if usage spikes/drops; smooth via 4-week moving average for executive reporting
- **CSM ownership changes** — `account_owner_csm_id` updates frequently; use SCD2 for historical analysis
- **Churn timing** — actual termination may be backdated months; align churn date to "effective termination date" not "system entry date"

---

## §14. Cross-references

- `domain-finance-billing.md` — ARR forecasting + renewal-risk integration
- `subscription-business-model.md` — customer lifecycle context
- `domain-sales-gtm.md` — account dim source
- `enterprise-data-products-catalog.md` — published CX data products
- `bi-semantic-consumption.md` — Sigma + semantic layer for CX metrics
