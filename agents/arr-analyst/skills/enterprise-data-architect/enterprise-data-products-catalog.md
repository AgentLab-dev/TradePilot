# Enterprise Data Products Catalog

The named, governed, contract-bearing data products that the EDH delivers to
the rest of Workday. This is the catalog — what's published, who owns it,
who consumes it, what the SLAs are.

If you're proposing a new data product, model it after these. If you're
consuming one, this is the directory. If you can't find what you need here,
it's a request for a new data product (file a request → product domain
owner → design → publish).

---

## §1. What is a data product?

A **data product** in this catalog is a Snowflake model (in `DATA_PRODUCTS`
schema of a domain DB) that:

1. Has a **declared owner** (`meta.owner` in the YAML schema)
2. Has a **contract** (`contract: enforced`) — schema can't change without versioning
3. Has a **defined SLA** (`meta.sla_freshness_hours`)
4. Has **documentation** (column descriptions + grain + use case)
5. Is **discoverable** (listed in this catalog + Atlan / DataHub)
6. Has **tests** that block bad data from publication
7. Has **observability** (freshness + quality monitoring)
8. Has **versioning** for breaking changes (`v1`, `v2`)

If a model doesn't meet ALL 8 criteria, it's not a data product — it's an
internal model. Demote it from `DATA_PRODUCTS` to `MANAGED` / `AGGREGATIONS`.

---

## §2. Data product directory

### 2.1 FOUNDATIONAL_ASSETS_PROD (shared dims)

| Data product | Grain | Owner | SLA | Primary consumers |
|---|---|---|---|---|
| `WD_FISCAL_CALENDAR` | Day | Platform Data Eng | 24 hr (static) | All domains, Sigma |
| `WD_FX_RATES` | Currency pair × date | Platform Data Eng | 24 hr | Finance, Sales |
| `VW_REF_PRODUCT_HIERARCHY` | Product code L3/L4/L5 | Platform Data Eng | 24 hr | Finance, Sales, CX |
| `VW_REF_ACQUISITIONS` | Acquired entity | Platform Data Eng | 24 hr (low-churn) | Finance |
| `RELTIO_ACCOUNT_MASTER` | Account (golden record) | Platform Data Eng | 1 hr | Sales, Finance, Marketing, CX |

### 2.2 SALES_PROD (sales / GTM)

| Data product | Grain | Owner | SLA | Primary consumers |
|---|---|---|---|---|
| `WD_ACCOUNT_SCD2` | Account × validity period | GTM AE | 4 hr | All domains, Sigma |
| `WD_OPPORTUNITY_SCD2` | Opp × validity period | GTM AE | 4 hr | Finance, CX, Marketing, Sigma |
| `WD_PROPOSAL_SCD2` | Proposal × validity | GTM AE | 4 hr | Finance, Sigma |
| `WD_PROPOSAL_LINE_SCD2` | Proposal line × validity | GTM AE | 4 hr | Finance, Sigma |
| `WD_OPPORTUNITY_EXTENSION_SCD2` | Opp × validity | GTM AE | 4 hr | Finance, Sigma |
| `WD_USER_SCD2` | User × validity | GTM AE | 24 hr | All domains, Sigma |
| `BT_ACV_SKU` | Opp/proposal × SKU × close-quarter | GTM AE | 4 hr | Finance, Comp Plan, Sigma |
| `DASH_PIPELINE_HEALTH` | Pipeline summary by quarter/segment | GTM AE | 4 hr | Sales leadership, Sigma |
| `DASH_FORECAST_ACCURACY` | Forecast level × quarter | GTM AE | 4 hr | Sales ops, Sigma |
| `DASH_QUOTA_ATTAINMENT` | AE/RVP/GVP × quarter | GTM AE | 4 hr | Sales ops, Comp Plan, Sigma |
| `DASH_WIN_RATE_BY_SEGMENT` | Segment × quarter | GTM AE | 4 hr | Sales leadership, Sigma |

### 2.3 MARKETING_PROD (marketing)

| Data product | Grain | Owner | SLA | Primary consumers |
|---|---|---|---|---|
| `LEAD_SOURCE_RATIONALIZATION` | Raw source → canonical category | Marketing AE | 24 hr | All marketing dashboards |
| `MQL_BY_QUARTER` | MQL event × quarter | Marketing AE | 4 hr | Marketing ops, Sigma |
| `MARKETING_SOURCED_PIPELINE` | Opp × quarter (marketing-sourced flag) | Marketing AE | 4 hr | Marketing leadership, FP&A |
| `MARKETING_INFLUENCED_PIPELINE` | Opp × quarter (touched flag) | Marketing AE | 4 hr | Marketing leadership |
| `CAMPAIGN_PERFORMANCE` | Campaign × quarter | Marketing AE | 4 hr | Marketing ops |
| `ABM_PENETRATION` | ABM target account × quarter | Marketing AE | 4 hr | ABM team, marketing leadership |
| `LEAD_FUNNEL_CONVERSION` | Lifecycle stage × quarter | Marketing AE | 4 hr | Marketing ops |
| `CHANNEL_PERFORMANCE_BY_QUARTER` | Channel × quarter | Marketing AE | 4 hr | Marketing ops, CMO |
| `DASH_MARKETING_PERFORMANCE_QUARTERLY` | Executive summary | Marketing AE | 4 hr | CMO, Sigma |
| `ATTRIBUTION_FALLBACK_ANALYSIS` | Opp × attribution-source | Marketing AE | 24 hr | Marketing ops |

### 2.4 FINANCE_PROD (finance / EM)

| Data product | Grain | Owner | SLA | Primary consumers |
|---|---|---|---|---|
| `FINANCE_LINE_ANALYTICS` | ALI × as_was_date | Finance AE | 4 hr | All ARR aggregations, Finance, FP&A |
| `WD_AGREEMENT_SCD2` | Agreement × validity | Finance AE | 4 hr | All Finance + CX |
| `WD_AGREEMENT_LINE_SCD2` | ALI × validity | Finance AE | 4 hr | All Finance + CX + GTM |
| `SSR_AGREEMENT_RELATIONSHIP` | Old agr × new agr × relationship | Finance AE | 4 hr | All ARR models, FP&A |
| `LKP_STRATEGIC_PARTNERS` | Account × partner-flag | Finance AE | 24 hr | All ARR by-partner views |
| `ARR_LINE_CATEGORIES` | ALI × as_was_date × category | Finance AE | 4 hr | Sigma, FP&A, audit |
| `ARR_PRODUCT_CATEGORIES` | Product L3/L4/L5 × as_was × category | Finance AE | 4 hr | Sigma, FP&A, product strategy |
| `ARR_SKU_CATEGORIES` | SKU × as_was × category | Finance AE | 4 hr | Sigma, FP&A |
| `ARR_ACCOUNT_CATEGORIES` | Account × as_was × category | Finance AE | 4 hr | Sigma, CX (renewal forecasting) |
| `ARR_REGION_SEGMENT_CATEGORIES` | Region × Segment × as_was | Finance AE | 4 hr | Sigma, GTM |
| `ARR_INDUSTRY_CATEGORIES` | Industry × as_was × category | Finance AE | 4 hr | Sigma, Vertical strategy |
| `ARR_STRATEGIC_PARTNER_CATEGORIES` | Partner-flag × as_was × category | Finance AE | 4 hr | Sigma, Partner Ops |
| `ARR_PRODUCT_NET_DOLLAR_RETENTION_DASH_V2` | Product × quarter | Finance AE | 4 hr | CFO, Sigma |
| `ARR_SKU_TRENDS_DASHBOARD` | SKU × quarter | Finance AE | 4 hr | Product strategy, Sigma |
| `ARR_GROWTH_DECOMPOSITION_DASH` | Quarter × growth-category | Finance AE | 4 hr | Board reporting, Sigma |
| `ARR_FORECAST_RENEWAL_RISK_ADJUSTED` | Account × forward-quarter | Finance AE | 24 hr | FP&A, CX |
| `GL_REVENUE_RECOGNIZED` | GL account × period | Finance AE | 24 hr | FP&A, Audit (SOX Tier 1) |
| `ARR_TO_REVENUE_RECONCILIATION` | Account × period × variance | Finance AE | 24 hr | Audit, SOX (SOX Tier 1) |
| `PLAN_VS_ACTUAL` | BU × period × variance | Finance AE | 24 hr | FP&A |

### 2.5 ACTIVATION_USAGE_ADOPTION_PROD (CX sub-domain 1)

| Data product | Grain | Owner | SLA | Primary consumers |
|---|---|---|---|---|
| `WD_TENANT_ACTIVATION_SCD2` | Tenant × validity | CX AE | 4 hr | CX dashboards, Loyalty health |
| `BT_FEATURE_ADOPTION` | Tenant × feature × day | CX AE | 24 hr | Product, CX |
| `AGG_TENANT_ACTIVITY_DAILY` | Tenant × day | CX AE | 24 hr | CX, Product, Loyalty health |
| `AGG_TENANT_ACTIVITY_WEEKLY` | Tenant × week | CX AE | 24 hr | CX, Sigma |
| `WD_SUPPORT_TICKETS_SCD2` | Ticket × validity | CX AE (support) | 4 hr | Support, Loyalty health |
| `DASH_TENANT_USAGE_TRENDS` | Executive | CX AE | 24 hr | Product, CX leadership, Sigma |

### 2.6 LOYALTY_ADVOCACY_PROD (CX sub-domain 2)

| Data product | Grain | Owner | SLA | Primary consumers |
|---|---|---|---|---|
| `CUSTOMER_HEALTH_SCORE` | Account × snapshot_date | CX AE | 24 hr | CSM team, Finance (forecasting), Sigma |
| `CHURN_RISK_SCORE` | Account × snapshot_date | CX AE + ML | 24 hr | CSM team, Finance, Sigma |
| `NPS_RESPONSES` | Response × respondent | CX AE | 24 hr | CX leadership, Product |
| `NPS_BY_ACCOUNT` | Account × quarter | CX AE | 24 hr | CSM, CX leadership, Sigma |
| `NPS_TREND_BY_PRODUCT_LINE` | Product × quarter | CX AE | 24 hr | Product, Sigma |
| `VOC_UNIFIED_RESPONSE` | Response × source × account | CX AE | 24 hr | Product Council |
| `GAINSIGHT_CTA_ACTIVITY` | CTA × event | CX AE | 4 hr | CSM ops |
| `CSM_CTA_RESOLUTION_RATE` | CSM × quarter | CX AE | 24 hr | CSM ops, Sigma |
| `CHURN_EVENT` | Churn event × account | CX AE | 24 hr | Audit, Finance, Sigma |
| `CHURN_REASONS_QUARTERLY` | Reason × quarter | CX AE | 24 hr | CX leadership |
| `DASH_CHURN_ANALYSIS` | Executive | CX AE | 24 hr | CRO, CFO, Sigma |
| `CUSTOMER_360_VIEW` | Account (single pane) | CX AE | 4 hr | CSM team, exec briefings |
| `ADVOCACY_PARTICIPATION` | Account × program | CX AE | 24 hr | Marketing (case studies), Customer Advisory Board |

### 2.7 PRODUCT_IMPLEMENTATION_PROD (CX sub-domain 3)

| Data product | Grain | Owner | SLA | Primary consumers |
|---|---|---|---|---|
| `WD_PSO_PROJECT_SCD2` | Project × validity | CX AE (PSO) | 4 hr | PSO ops, CX, Sigma |
| `WD_PSO_MILESTONE` | Milestone × project | CX AE (PSO) | 4 hr | PSO ops |
| `AGG_PROJECT_HEALTH_DAILY` | Project × day | CX AE (PSO) | 24 hr | PSO ops, CX |
| `DASH_IMPLEMENTATION_TIME_TO_VALUE` | Executive | CX AE (PSO) | 24 hr | PSO leadership, CX |

---

## §3. SLA tiers (canonical)

| Tier | Freshness | Failure response | Examples |
|---|---|---|---|
| **P0** | < 1 hr | Page on-call within 15 min | (Reserved — none currently classified) |
| **P1** | < 4 hr | Page on-call within 30 min, daily review if >24 hr stale | `FINANCE_LINE_ANALYTICS`, `ARR_*`, `WD_ACCOUNT_SCD2`, `WD_AGREEMENT_LINE_SCD2`, `CUSTOMER_360_VIEW` |
| **P2** | < 24 hr | Slack alert, daily review | Health scores, churn risk, NPS aggregations, most aggregations |
| **P3** | < 7 days | Weekly review | Low-churn reference data (acquisitions, product hierarchy) |

SLA breach handling:
- P1 breach: triage within 30 min; restore within 4 hr; postmortem within 48 hr
- P2 breach: triage within 4 hr; restore within 24 hr; postmortem if recurring
- P3 breach: triage within 1 day; restore within 3 days

---

## §4. Contract template (every data product needs this YAML)

```yaml
models:
  - name: arr_product_net_dollar_retention_dash_v2
    description: |
      Net Dollar Retention by product, by fiscal quarter.
      Used in CFO board pack + Sigma executive dashboards.

      Grain: one row per product (L3/L4/L5) per fiscal quarter.

    config:
      contract: { enforced: true }

    meta:
      owner: "@finance-ae-team"
      sla_freshness_hours: 4
      sox_tier: 2
      domain: finance
      consumers:
        - sigma: "ARR Dashboard - NDR"
        - downstream_dbt: ["eda-dbt-semantic-layer"]
      data_classification: confidential
      atlas_category: "Enterprise Metric"

    columns:
      - name: product_code_l3
        data_type: varchar(64)
        constraints: [ { type: not_null } ]
        description: Workday product hierarchy L3 (e.g., "Core HCM")

      - name: fiscal_quarter
        data_type: varchar(8)
        constraints: [ { type: not_null } ]
        description: Workday fiscal quarter (e.g., 'FY26Q1')

      - name: ndr_pct
        data_type: number(10, 4)
        description: |
          Net Dollar Retention as decimal (e.g., 1.04 = 104%).
          Formula: (BEGIN_ARR + EXPANSION - CHURN - CONTRACTION) / BEGIN_ARR
          Currency variant: USD_HIST (FX at transaction date)

      - name: begin_arr_usd_hist
        data_type: number(38, 2)
        description: Starting ARR for the quarter (USD_HIST)

      # (etc. for all columns)

    tests:
      - unique: { columns: [product_code_l3, fiscal_quarter] }
      - dbt_utils.expression_is_true:
          expression: "ndr_pct BETWEEN 0.5 AND 2.0"
          name: ndr_in_reasonable_range

    # Cross-project access
    access: public
    group: common_group
```

---

## §5. Lifecycle (proposing a new data product)

```
┌──────────────────────────────────────────────────────────────┐
│ 1. Need identified (3+ teams asking similar question)        │
│    "We need ARR by industry segment for Vertical strategy"    │
└────────────────────────┬─────────────────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. Domain placement determined                                │
│    → Industry rollup of ARR → owned by Finance domain        │
│    → New data product: ARR_INDUSTRY_CATEGORIES                │
└────────────────────────┬─────────────────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. Owner assigned + design doc                                │
│    Grain: industry × as_was_date × category                  │
│    SLA: P1 (4 hr)                                             │
│    Consumers: Vertical strategy team, FP&A, Sigma            │
└────────────────────────┬─────────────────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. Implementation (dbt PR)                                    │
│    - Build model in `FINANCE_PROD.AGGREGATIONS.*`            │
│    - Add YAML with contract + meta + tests                   │
│    - Update this catalog                                      │
│    - Add to Atlan / DataHub                                  │
└────────────────────────┬─────────────────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────────────┐
│ 5. CI passes + cross-domain review (if cross-domain)         │
│    - Owner reviews                                            │
│    - Consumers review                                         │
│    - Platform reviews (governance)                            │
└────────────────────────┬─────────────────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────────────┐
│ 6. Merge to qa → prod                                         │
└────────────────────────┬─────────────────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────────────┐
│ 7. Announce + onboard consumers                               │
│    Slack #eda-data-products: "New data product live..."      │
│    Office hours session for major consumers                  │
└──────────────────────────────────────────────────────────────┘
```

---

## §6. Deprecating a data product

```
┌──────────────────────────────────────────────────────────────┐
│ 1. Identify replacement (v1 → v2, or merging into another)   │
└────────────────────────┬─────────────────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. Announce deprecation (Slack + email to consumer owners)   │
│    Deprecation date: T + 90 days minimum                     │
└────────────────────────┬─────────────────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. Add deprecation banner in YAML                             │
│    meta.deprecated_at: '2026-09-01'                          │
│    meta.replacement: 'ARR_PRODUCT_NDR_DASH_V3'               │
└────────────────────────┬─────────────────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. Monitor consumer migration (BI query analytics)           │
│    All consumers migrated by T + 60 days                     │
└────────────────────────┬─────────────────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────────────┐
│ 5. Drop at T + 90 days                                        │
│    Verify zero queries in last 7 days, then DROP             │
└──────────────────────────────────────────────────────────────┘
```

---

## §7. Versioning data products

For **breaking changes** (schema rename, semantic change), bump version:

```
ARR_PRODUCT_NET_DOLLAR_RETENTION_DASH_V1   (deprecated, sunset planned)
ARR_PRODUCT_NET_DOLLAR_RETENTION_DASH_V2   (current production)
ARR_PRODUCT_NET_DOLLAR_RETENTION_DASH_V3   (in development)
```

Both v1 + v2 live in parallel during transition (90-day deprecation window). Consumers migrate at their own pace; new dashboards use v_latest.

dbt-mesh supports `versions:` in YAML; use them for canonical versioning. See `dbt-architect/mesh-and-contracts.md`.

---

## §8. Discovery — where to find data products

| Channel | Purpose |
|---|---|
| **This catalog** | Authoritative list |
| **Atlan / DataHub** | Searchable web catalog with lineage |
| **dbt docs** | Per-project docs with column-level info |
| **Sigma** | Discover by browsing dashboards (downstream of products) |
| **#eda-data-products Slack** | Announce + Q&A |

Onboarding new consumer:
1. Find product in this catalog or Atlan
2. Review schema in dbt docs
3. Request `read` access to the specific `DATA_PRODUCTS` schema via Snowflake access request
4. Build dashboard / consume; raise issues via #eda-data-products

---

## §9. Data product anti-patterns (do NOT do)

- ❌ Build a model in `DATA_PRODUCTS` without contract / owner / SLA
- ❌ Make breaking schema changes to a contracted model without version bump
- ❌ Skip `meta.owner` — every product needs a team / human
- ❌ Add new columns to a contracted model without consumer notification
- ❌ Allow Sigma to bypass DATA_PRODUCTS and read MANAGED directly
- ❌ Build a "personal" data product (one consumer, no governance) — that should be a Sigma dataset, not an enterprise data product
- ❌ Duplicate functionality (yet-another-ARR-rollup) — extend the canonical one
- ❌ Skip data quality tests — every product MUST have unique + not_null on PK

---

## §10. Cross-references

- `platform-architecture.md` — where products fit in the platform
- `dbt-architect/mesh-and-contracts.md` — dbt-mesh contract mechanics
- `analytics-engineering-architect/data-mesh-and-products.md` — data product principles
- `analytics-engineering-architect/slo-and-observability.md` — SLA monitoring
- `finance-metrics-canonical.md` — canonical metrics behind products
- `bi-semantic-consumption.md` — Sigma + semantic-layer consumption patterns
