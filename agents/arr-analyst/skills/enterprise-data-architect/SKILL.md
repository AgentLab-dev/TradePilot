---
name: enterprise-data-architect
description: >-
  Principal Enterprise Data Architect for Workday's EDH/EDW supporting the
  subscription business — combined architecture across SFDC (core + GTM-Next) +
  Fivetran + Snowflake (BASE_PROD landing + 7 domain DBs in MANAGED/AGGREGATIONS/
  DATA_PRODUCTS pattern + INT staging) + dbt mesh (eda-dbt-base, common, gtm,
  em, cx, semantic-layer) + Sigma BI + MetricFlow semantic layer. Covers
  domain expertise across Sales/GTM, Marketing, Finance, and CX/Customer
  Success. Owns canonical subscription metrics (ACV, ARR, TCV, NRR, GRR, NDR,
  churn / expansion / contraction) and enterprise data product governance.
  Use when designing cross-domain data products, picking which domain owns
  what, defining metric canonical definitions, planning end-to-end pipelines
  from source system to BI, debugging cross-team data flow issues, onboarding
  a new source / domain, or making any platform-level architecture decision
  for the Workday enterprise analytics stack.
---

# Enterprise Data Architect — Workday EDH/EDW (2026)

Role: Principal Enterprise Data Architect for Workday's enterprise analytics
platform. You own the end-to-end view from source systems → Snowflake EDH →
dbt mesh → semantic layer → BI consumption. You arbitrate cross-domain data
products, set canonical metric definitions, design for SOX + audit readiness,
and orchestrate the platform that powers Workday's subscription business —
ARR, ACV, NRR, GRR, churn, expansion, attribution, customer health, the lot.

This SKILL.md is the index + decision framework. Deep companion files:

- [`platform-architecture.md`](platform-architecture.md) — Full E2E architecture: SFDC + Fivetran + Snowflake EDH (BASE_PROD + 7 domain DBs) + dbt mesh (6 repos) + Sigma + semantic layer
- [`subscription-business-model.md`](subscription-business-model.md) — Workday's subscription business: bookings → billings → revenue → renewal lifecycle, SSR, deal motions, quote-to-cash
- [`finance-metrics-canonical.md`](finance-metrics-canonical.md) — ACV, ARR, TCV, NRR, GRR, NDR, churn / expansion / contraction — formal definitions, formulas, currency variants, grain
- [`domain-sales-gtm.md`](domain-sales-gtm.md) — Sales/GTM analytics: pipeline, forecasting, CPQ (Apttus), quota, attainment, territory, win rate, deal motions, GTM-Next migration
- [`domain-marketing.md`](domain-marketing.md) — Marketing analytics: Marketo, Bizible attribution, MQL, ABM, campaign ROI, marketing-sourced pipeline
- [`domain-finance-billing.md`](domain-finance-billing.md) — Finance: Zuora billing, Workday Financial Management, Adaptive planning, revenue recognition, FX, period close, SOX audit
- [`domain-cx-customer-success.md`](domain-cx-customer-success.md) — CX: Gainsight (success), Medallia / Qualtrics (voice of customer), support analytics, health scoring, churn risk
- [`enterprise-data-products-catalog.md`](enterprise-data-products-catalog.md) — Named data products per domain with owners, consumers, SLAs, grain
- [`bi-semantic-consumption.md`](bi-semantic-consumption.md) — Sigma + MetricFlow semantic layer + governance + self-service patterns

---

## §1. The 2026 platform at a glance

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│  SOURCE SYSTEMS (~30+ SaaS + on-prem)                                                     │
│  SFDC (core+GTM-Next) │ Zuora │ Workday FM │ Adaptive │ Marketo │ Bizible │ Gainsight    │
│  Medallia │ Qualtrics │ Outreach │ Gong │ Clari │ Highspot │ Jira │ Reltio (MDM) │ ...   │
└────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                         │  Fivetran (managed CDC + batch)
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│  SNOWFLAKE EDH — RAW / LANDING TIER                                                       │
│  BASE_PROD (~55 schemas) — Fivetran landing tables, untransformed                        │
│  REDSHIFT_HISTORY — legacy SCD2 history (pre-Snowflake migration archive)                │
│  BASE_SOX_PROD — SOX-compliant variant for audit-controlled sources                      │
└────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                         │  eda-dbt-base — SCD2 wrappers, base curation
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│  SNOWFLAKE EDW — CURATED DOMAIN TIER (data mesh by domain)                                │
│  Per-domain DB pattern: <DOMAIN>_PROD.{MANAGED,AGGREGATIONS,DATA_PRODUCTS}                │
│                       + <DOMAIN>_INT_PROD.STAGE  (intermediate)                          │
│                                                                                            │
│  FOUNDATIONAL_ASSETS  → shared dims (calendar, fiscal, currency, MDM)  ← eda-dbt-common   │
│  SALES              → pipeline, opportunity, proposal, quota          ← eda-dbt-gtm      │
│  MARKETING          → lead, campaign, attribution, MQL                ← eda-dbt-gtm      │
│  FINANCE            → agreement, ARR, ACV, TCV, billing               ← eda-dbt-em       │
│  ACTIVATION_USAGE_ADOPTION → product usage / feature adoption          ← eda-dbt-cx       │
│  LOYALTY_ADVOCACY   → NPS, customer health, success                   ← eda-dbt-cx       │
│  PRODUCT_IMPLEMENTATION → implementation services, time-to-value      ← eda-dbt-cx       │
└────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                         │  eda-dbt-semantic-layer (MetricFlow)
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│  SEMANTIC LAYER                                                                            │
│  Canonical metrics (ARR, ACV, NRR, GRR, …) defined once, served many times                │
└────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│  CONSUMPTION                                                                               │
│  Sigma (primary BI) │ Tableau │ Hex (data science) │ Hightouch (reverse ETL → SFDC)      │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

For full architecture detail see [`platform-architecture.md`](platform-architecture.md).

---

## §2. The 6 dbt project repos (the mesh)

| Repo | Project name | Branch | Outputs to (Snowflake DB) | Owns |
|---|---|---|---|---|
| `workday-inc/eda-dbt-base` | `eda_dbt_base` | qa | `BASE_PROD.{adaptive,salesforce,zuora,...}` + `REDSHIFT_HISTORY` SCD2 | Fivetran landing wrappers + base SCD2 history |
| `workday-inc/eda-dbt-common` | `eda_dbt_common` | qa | `FOUNDATIONAL_ASSETS_PROD` + `FOUNDATIONAL_ASSETS_INT_PROD` | Shared dims (calendar, fiscal, currency, MDM) |
| `workday-inc/eda-dbt-gtm` | `eda_dbt_gtm` | qa | `SALES_PROD` + `SALES_INT_PROD`, `MARKETING_PROD` + `MARKETING_INT_PROD` | Sales + Marketing domain models |
| `workday-inc/eda-dbt-em` | `eda_dbt_em` | qa | `FINANCE_PROD` + `FINANCE_INT_PROD` (post-IA) | Finance / enterprise metrics (ARR/ACV/TCV) |
| `workday-inc/eda-dbt-cx` | `eda_dbt_cx` | qa | `ACTIVATION_USAGE_ADOPTION_*`, `LOYALTY_ADVOCACY_*`, `PRODUCT_IMPLEMENTATION_*` | CX (3 sub-domains) |
| `workday-inc/eda-dbt-semantic-layer` | `eda_dbt_semantic_layer` | qa | MetricFlow metric definitions | Canonical semantic layer |

**Cross-project dependency graph:**

```
                         eda-dbt-base
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
       eda-dbt-common   eda-dbt-gtm     eda-dbt-em
              │               │               │
              └───────┬───────┴───────┬───────┘
                      ▼               ▼
                eda-dbt-cx     eda-dbt-semantic-layer
```

Notes:
- `eda-dbt-common` and `eda-dbt-gtm` both depend on `eda-dbt-em` (for shared metric inputs) — careful with cycle avoidance via manifest pinning.
- `eda-dbt-cx` depends on `base + common + gtm + em` — most downstream domain project.
- `eda-dbt-semantic-layer` depends on `common + gtm + em + cx` — wraps all 4 with metric definitions.

For mesh details, see `dbt-architect/mesh-and-contracts.md`.

---

## §3. The standard domain DB pattern (every domain)

Every business domain follows the same 4-DB pattern:

```
<DOMAIN>_PROD                              ← analytics / consumer-facing
├── MANAGED                                  ← curated facts + dims (e.g., FINANCE_LINE_ANALYTICS)
├── AGGREGATIONS                             ← rollups (e.g., ARR_PRODUCT_CATEGORIES)
└── DATA_PRODUCTS                            ← published, BI-facing (dashboard-driving)

<DOMAIN>_INT_PROD                          ← intermediate
└── STAGE                                    ← staging models (stg_*, int_*)

(plus _DEV and _QA variants for each)
```

This is enforced by Terraform; consistent across all 7 analytics domains.

| Schema | Audience | Material | Examples |
|---|---|---|---|
| `STAGE` (in `_INT`) | dbt internals | view / ephemeral / table | `stg_em_agreement_line_item_scd2`, `int_agree_enriched` |
| `MANAGED` | Analytics engineers, downstream domains | incremental table | `FINANCE_LINE_ANALYTICS`, `WD_AGREEMENT_SCD2`, `WD_ACCOUNT_SCD2` |
| `AGGREGATIONS` | Analysts | table | `ARR_PRODUCT_CATEGORIES`, `ARR_LINE_CATEGORIES`, `ARR_SKU_CATEGORIES` |
| `DATA_PRODUCTS` | BI tools (Sigma), executives | table / view | `ARR_PRODUCT_NET_DOLLAR_RETENTION_DASH_V2`, `ARR_SKU_TRENDS_DASHBOARD` |

---

## §4. When to use this skill (decision tree)

```
Enterprise platform question
├── Architectural overview / onboarding new engineer        → §1 + platform-architecture.md
├── Source system integration (new SaaS / on-prem)          → platform-architecture.md §3
├── "Which domain owns this?" / data product placement      → §3 + enterprise-data-products-catalog.md
├── Canonical metric definition (what IS ARR?)              → finance-metrics-canonical.md
├── Subscription business question (SSR? renewal mechanics?)→ subscription-business-model.md
├── Pipeline / forecasting / CPQ                             → domain-sales-gtm.md
├── Lead source / attribution / campaign ROI                 → domain-marketing.md
├── Billing / rev rec / period close / FX                    → domain-finance-billing.md
├── Customer success / NPS / health / churn risk             → domain-cx-customer-success.md
├── BI / Sigma / governance / self-service                   → bi-semantic-consumption.md
└── Cross-domain data flow debugging                          → §5 + platform-architecture.md
```

---

## §5. The canonical "did the right number land in the right dashboard?" framework

When an executive says "ARR is wrong on the dashboard", trace this path:

```
Sigma dashboard
   ↓ consumes
FINANCE_PROD.DATA_PRODUCTS.ARR_PRODUCT_NET_DOLLAR_RETENTION_DASH_V2 (or similar)
   ↓ derived from
FINANCE_PROD.AGGREGATIONS.ARR_PRODUCT_CATEGORIES
   ↓ aggregates
FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS  ← the canonical grain (ALI × as_was_date)
   ↓ derived via get_arr_line_base_fn UDTF from
FINANCE_INT_PROD.STAGE.stg_em_int_strategic_program_flag
   ↓ enriches
FINANCE_INT_PROD.STAGE.stg_em_int_agree_enriched
   ↓ joins
FINANCE_INT_PROD.STAGE.stg_em_agreement_line_item_scd2 (via ref to GTM project)
   ↓ wraps via eda-dbt-gtm cross-project ref
SALES_PROD.MANAGED.WD_PROPOSAL_LINE_SCD2 + WD_AGREEMENT_LINE_SCD2
   ↓ derived via eda-dbt-base
BASE_PROD.SALESFORCE.APTTUS__AGREEMENTLINEITEM__C (raw)
   ↓ landed by
Fivetran (Salesforce connector, 1-hour incremental)
   ↓ extracted from
Salesforce (CPQ + Apttus + Account/Opportunity objects)
```

Common breakdown points:
| Layer | Failure mode |
|---|---|
| Sigma dashboard | Wrong filter, wrong measure choice |
| `DATA_PRODUCTS.*` view | Wrong aggregation / join in publishing layer |
| `AGGREGATIONS.*` table | Boolean rollup wrong (`boolor_agg` vs `sum`); category misclassification |
| `MANAGED.FINANCE_LINE_ANALYTICS` | UDTF logic bug; SCD2 join wrong window; categorization edge case |
| `STAGE.*` | Wrong source filter; stale `_fivetran_synced` cutoff |
| Cross-project `ref()` | Stale manifest; defer pointing at wrong branch |
| `BASE_PROD` source | Fivetran connector down / behind |
| Salesforce | Source data wrong (admin needs to fix) |

---

## §6. The fiscal calendar (Workday-specific)

Workday's fiscal year runs **February 1 → January 31**:
- FY26 = Feb 1, 2025 → Jan 31, 2026
- FY26Q1 = Feb-Apr 2025
- FY26Q2 = May-Jul 2025
- FY26Q3 = Aug-Oct 2025
- FY26Q4 = Nov 2025-Jan 2026

Never hardcode fiscal boundaries. Always use `get_fiscal_quarter()` / `get_fiscal_attributes()` macros which read from `FOUNDATIONAL_ASSETS_PROD.MANAGED.WD_FISCAL_CALENDAR`.

---

## §7. Currency variants (canonical)

Every financial metric exists in 3 currency variants:

| Variant | When to use | Example column |
|---|---|---|
| **USD_CURRENT** | Live dashboards, trending over time | `arr_usd_current` |
| **USD_HIST** | Period-over-period comparisons with fixed FX | `arr_usd_hist` |
| **USD_ACTUAL** | Billing / invoicing — raw transaction currency, NO conversion | `arr_usd_actual` |

Every metric you report MUST specify which variant. "ARR is $X" without variant context is ambiguous.

For deep mechanics, see `finance-metrics-canonical.md` §3.

---

## §8. SOX-compliant pipelines (audit-controlled)

A subset of pipelines is **SOX-compliant** (relevant to financial reporting):
- Lands in `BASE_SOX_PROD` (separate from `BASE_PROD`)
- Has additional approval gates in CI/CD
- Has audit logging on every read / write
- Has stricter retention (90+ days)

Anything that feeds revenue recognition / public disclosure metrics must flow through SOX-compliant pipes. Talk to the SOX compliance lead before touching anything in `BASE_SOX_PROD`.

---

## §9. Adoption guardrails

When designing a new data product or pipeline:

1. **Source first**: confirm the source data exists in `BASE_PROD` (or schedule a Fivetran connector). Don't build downstream until upstream is reliable.
2. **Domain placement**: put the data product in the right domain DB. Cross-domain reuse via dbt-mesh `ref('upstream_project', 'model')`.
3. **Naming**: domain prefix (`bt_finance_*`, `bt_sales_*`); follow the `MANAGED` / `AGGREGATIONS` / `DATA_PRODUCTS` placement rules.
4. **Contract before going public**: any model consumed cross-domain MUST have `contract: enforced` + `meta.owner` + `meta.sla_freshness_hours`.
5. **Semantic-layer metric** if 3+ consumers will compute the same aggregation.
6. **Documentation in catalog** (Atlan / DataHub / `meta.description`) before the first PR ships to prod.
7. **Test for SOX**: if it touches revenue recognition, get SOX approval BEFORE merging.

For 2026 platform features (Gen2, Optima, Dynamic Tables, Iceberg, Cortex), see `snowflake-architect` skill.

---

## §10. The Sigma + semantic layer pattern

Sigma is the primary BI tool. Pattern:

```
Sigma workbook
   ↓ consumes via JDBC
MetricFlow (eda-dbt-semantic-layer)
   ↓ compiles to SQL against
FINANCE_PROD / SALES_PROD / etc. DATA_PRODUCTS schema
```

Anti-pattern: Sigma workbook reads directly from `MANAGED` or `AGGREGATIONS`, defines its own metric. Drift inevitable.

Correct pattern: Sigma reads from `DATA_PRODUCTS` views OR from MetricFlow metric API. Metric definition lives ONCE in `eda-dbt-semantic-layer`.

For Sigma + semantic layer deep dive: `bi-semantic-consumption.md`.

---

## §11. Roles + ownership (the org)

| Function | Repo | Team | Snowflake role |
|---|---|---|---|
| Base SCD2 / Fivetran wrappers | `eda-dbt-base` | Platform Data Engineering | `ROLE_DATA_ENG_*` |
| Shared dimensions | `eda-dbt-common` | Platform Data Engineering | `ROLE_DATA_ENG_*` |
| Sales + Marketing models | `eda-dbt-gtm` | GTM Analytics Engineering | `ROLE_GTM_AE_*` |
| Finance / EM models | `eda-dbt-em` | Finance Analytics Engineering | `ROLE_FINANCE_AE_*` |
| CX models | `eda-dbt-cx` | CX Analytics Engineering | `ROLE_CX_AE_*` |
| Semantic layer | `eda-dbt-semantic-layer` | Semantic Layer Team | `ROLE_SL_AE_*` |
| Platform infra | n/a (Terraform) | Platform / DevOps | `ROLE_SYSTEM_ADMIN_*` |
| Governance | n/a | Governance | `ROLE_GOVERNANCE_ADMIN` |

---

## §12. Quick reference — where things live

| Need | Where |
|---|---|
| Raw Salesforce CPQ data | `BASE_PROD.SALESFORCE.APTTUS_*` |
| Raw Salesforce GTM-Next data | `BASE_PROD.SALESFORCE_GTMNEXT.*` |
| Raw Zuora billing data | `BASE_PROD.ZUORA.*` |
| Raw Workday FM data | `BASE_PROD.WORKDAY_FINANCIAL_MANAGEMENT.*` |
| Raw Marketo data | `BASE_PROD.MARKETO.*` |
| Raw Bizible attribution | `BASE_PROD.BIZIBLE.*` |
| Raw Gainsight customer success | `BASE_PROD.GAINSIGHT.*` |
| Raw Medallia VoC | `BASE_PROD.MEDALLIA.*` |
| Raw Outreach engagement | `BASE_PROD.OUTREACH.*` |
| Raw Clari forecasting | `BASE_PROD.CLARI.*` |
| Reltio MDM | `BASE_PROD.RELTIO.*` |
| Customer Data Platform | `BASE_PROD.CDP.*` |
| Legacy Redshift SCD2 | `BASE_PROD.REDSHIFT_HISTORY.*` |
| Account SCD2 (current) | `SALES_PROD.MANAGED.WD_ACCOUNT_SCD2` |
| Agreement SCD2 (current) | `FINANCE_PROD.MANAGED.WD_AGREEMENT_SCD2` |
| Agreement Line SCD2 | `FINANCE_PROD.MANAGED.WD_AGREEMENT_LINE_SCD2` |
| Opportunity SCD2 | `SALES_PROD.MANAGED.WD_OPPORTUNITY_SCD2` |
| Proposal SCD2 | `SALES_PROD.MANAGED.WD_PROPOSAL_SCD2` + `WD_PROPOSAL_LINE_SCD2` |
| ARR at ALI grain | `FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS` |
| ARR by product | `FINANCE_PROD.AGGREGATIONS.ARR_PRODUCT_CATEGORIES` |
| ARR by SKU | `FINANCE_PROD.AGGREGATIONS.ARR_SKU_CATEGORIES` |
| Net Dollar Retention dashboard | `FINANCE_PROD.DATA_PRODUCTS.ARR_PRODUCT_NET_DOLLAR_RETENTION_DASH_V2` |

---

## See also

- `dbt-architect` skill — dbt project + mesh + contracts + semantic layer
- `snowflake-architect` skill — Snowflake platform decisions (Gen2, Optima, DT, Iceberg, Cortex)
- `dbt-platform-architect` skill — multi-project topology + env promotion
- `analytics-engineering-architect` skill — modern data stack + data mesh patterns
- `enterprise-metrics-finance-architect` skill — finance-domain enterprise modeling
- `finance-functional-architect` / `finance-functional-analytics` skills — finance business definitions
- `salesforce-bsa-*` skills — SFDC object model deep dives
- `sigma-computing-analyst` skill — Sigma workbook patterns
- `eda-pipeline-refresh-schedule` skill — pipeline refresh + freshness data
