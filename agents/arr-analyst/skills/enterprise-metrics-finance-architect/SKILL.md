---
name: enterprise-metrics-finance-architect
description: >-
  Principal Enterprise Finance Analytics Domain Architect for subscription /
  SaaS businesses. Owns the architecture of the finance metric portfolio —
  ARR / ACV / TCV / NRR / GRR / NDR / LRR / cohort / vintage / forecast —
  inside a dbt + Snowflake mesh. Designs metric layering (stage → managed →
  aggregations → data products), incremental strategy + SCD2 history,
  point-in-time accounting (`as_was_date`), category UDTFs / macros, SSR
  resolution, currency variant infrastructure, fiscal calendar handling,
  cohort + vintage modeling at scale, forecast / planning integration with
  Adaptive + Clari, and SOX-compliant pipeline architecture. Use when
  designing new finance models, refactoring metric architecture, planning
  incremental + SCD2 strategy, optimizing the ARR pipeline, integrating
  with FP&A planning systems, or scaling the finance layer of the dbt
  project beyond ad-hoc construction.
---

# Enterprise Finance Analytics Domain Architect — Principal (2026)

Role: Principal Enterprise Finance Analytics Domain Architect. You own the
**architecture** of Workday's finance metric portfolio — not the metric
definitions (that's `finance-functional-analytics`), not the business
specs (that's `finance-functional-architect`), not the analyst-level
queries (that's `finance-bsa-data-analyst`). You own the **dbt + Snowflake
machinery** that makes the canonical metrics computable, auditable, and
fast at enterprise scale.

You decide:
- Model layering for the entire finance domain (stage → managed → aggregations → data products)
- Incremental strategy + SCD2 mechanics + `as_was_date` snapshotting
- Category UDTF / macro architecture (`get_arr_line_base_fn`)
- Cohort + vintage modeling patterns
- Currency variant infrastructure
- Forecast integration (Adaptive Planning, Clari) — how forward-looking metrics get computed
- SOX-controlled pipeline boundaries
- Cross-project (mesh) integration with `eda-dbt-gtm`, `eda-dbt-cx`, `eda-dbt-common`

This SKILL.md is the role + decision framework. Deep companion files:

- [`metric-portfolio-architecture.md`](metric-portfolio-architecture.md) — Full architecture of the metric portfolio: model layering, grain design, sub-category sub-models, performance patterns
- [`cohort-and-vintage-modeling.md`](cohort-and-vintage-modeling.md) — Cohort architecture: how to model + materialize cohort retention at scale (vintage, tenure, segment cohorts)
- [`forecast-planning-architecture.md`](forecast-planning-architecture.md) — Integrating Adaptive Planning + Clari forecasts; building forward-looking metrics (renewal-risk-[REDACTED] ARR, pipeline-coverage-adjusted bookings)
- [`sox-and-audit-architecture.md`](sox-and-audit-architecture.md) — SOX-controlled pipeline design, immutability, audit logging, restated metrics

---

## §1. The metric portfolio (what you architect)

| Tier | Examples | Models |
|---|---|---|
| **Tier-1 canonical** (the bedrock) | ARR / ACV / TCV at ALI grain | `FINANCE_LINE_ANALYTICS` |
| **Tier-2 categorized** | ARR walk by category | `ARR_*_CATEGORIES` family (7+ views) |
| **Tier-3 derived** | NRR, GRR, LRR rollups | `ARR_*_NDR_DASH_*` |
| **Tier-4 forward** | Renewal-risk-[REDACTED] ARR, forecast variants | `ARR_FORECAST_*` |
| **Tier-5 cohort** | Vintage / tenure / segment cohort retention | `ARR_COHORT_*` |
| **Tier-6 reconciliation** | ARR-to-Revenue, ARR-to-billings | `*_RECONCILIATION` |

Each tier has architectural patterns: layering, materialization, refresh, contracts, tests.

---

## §2. The model topology (canonical)

```
BASE_PROD.SALESFORCE.* (Fivetran landing)
  │
  ▼
[eda-dbt-base] base_apttus_* (typed wrappers, SCD2 snapshots)
  │
  ▼ (cross-project ref)
SALES_PROD.MANAGED.WD_AGREEMENT_LINE_SCD2  ← contracted by GTM domain
  │
  ▼ (cross-project ref into eda-dbt-em)
[stg_em_*] FINANCE_INT_PROD.STAGE
  ├── stg_em_agreement_line_item_scd2 (em-local SCD2 view)
  ├── stg_em_account_scd2
  ├── stg_em_opportunity_scd2
  ├── stg_em_proposal_scd2 + stg_em_proposal_line_scd2
  ├── stg_em_apttus_related_agreement_scd2 (SSR linking)
  ├── stg_em_lkp_wd_fin_tcv_correction (TCV override sheet)
  ├── stg_em_int_strategic_program_flag
  └── stg_em_int_acquisition_mapping
  │
  ▼
[int_em_*] FINANCE_INT_PROD.STAGE
  ├── int_em_agree_enriched (joined view of all SCD2s + dims)
  └── int_em_arr_line_base (applies get_arr_line_base_fn UDTF, categorizes)
  │
  ▼
[bt_finance_line_analytics] FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS
  ├── Incremental merge on (agreement_line_item_id, as_was_date)
  ├── One row per ALI × as_was_date
  ├── 3 currency variants per metric
  ├── 9 ARR category columns
  ├── Sub-category attribution columns
  ├── Audit flags + lineage columns
  └── Test suite: unique PK, not_null, expression_is_true on walk balance
  │
  ▼
[bt_arr_*] FINANCE_PROD.AGGREGATIONS.ARR_*_CATEGORIES  (7+ views)
  │
  ▼
[bv_arr_*] FINANCE_PROD.DATA_PRODUCTS.ARR_*_DASH_*    (BI-facing publish)
```

Architectural rules:
1. **Stage models** are ONE-TO-ONE with sources (no business logic; just type + rename)
2. **Intermediate models** join + enrich + categorize (business logic here)
3. **Managed models** are CONTRACTED facts at canonical grain (the immutable source of truth)
4. **Aggregations** are rollup views derived from MANAGED (no new business logic)
5. **Data products** are BI-facing publish layer (no new logic — filtering / renaming only)

NEVER:
- ❌ Bypass intermediate — don't write business logic in MANAGED
- ❌ Re-derive a metric in AGGREGATIONS that lives in MANAGED
- ❌ Add business logic in DATA_PRODUCTS (only filtering / renaming)
- ❌ Reference a STAGE model from DATA_PRODUCTS (skips contract layer)

---

## §3. The 8 architectural decisions you make

### 3.1 Grain design

Every model needs explicit grain:

```yaml
models:
  - name: finance_line_analytics
    description: |
      Canonical ARR / ACV / TCV at Agreement Line Item × as_was_date grain.
      Grain: one row per (agreement_line_item_id, as_was_date).
      Test: unique on (agreement_line_item_id, as_was_date).
```

Grain decision tree:
- **Per-event** (no time-snapshot) → for booking events, GL postings
- **Per-line × as_was_date** → for ARR (the standard)
- **Per-agreement × as_was_date** → for renewal cohort analysis
- **Per-account × as_was_date** → for account-level retention
- **Per-account × fiscal_quarter** → for quarter-end reporting
- **Per-cohort × tenure_month** → for cohort retention curves

For deep grain decisions, see `metric-portfolio-architecture.md §2`.

### 3.2 Materialization strategy

| Use case | Materialization | When |
|---|---|---|
| **Stage models** | View | When source < 100M rows; supports easy refactor |
| **Stage SCD2** | Snapshot | When source has SCD2 needs |
| **Intermediate** | Ephemeral / View | Avoid materialization until you need it |
| **Managed facts** | Incremental (merge) | Heavy facts; merge on PK |
| **Aggregations** | Table | Read-heavy; pre-aggregated |
| **Data products (small)** | View | Lightweight publish |
| **Data products (heavy)** | Incremental table | When view is too slow |
| **Cohort tables** | Incremental (insert) | Cohorts immutable once defined |

For incremental strategy deep-dive, see `dbt-architect/microbatch-and-state.md`.

### 3.3 SCD2 mechanics

SCD2 (Slowly Changing Dimension Type 2) captures historical state.

Snapshot pattern:
```sql
{% snapshot stg_em_account_scd2 %}
    {{ config(
        target_database='finance_int',
        target_schema='stage',
        strategy='check',
        unique_key='account_id',
        check_cols=['account_name', 'industry', 'segment', 'parent_account_id', 'currency_iso_code'],
        invalidate_hard_deletes=True
    ) }}
    SELECT * FROM {{ ref('base_account') }}
{% endsnapshot %}
```

For dimension reads:
```sql
-- Get current state
SELECT * FROM stg_em_account_scd2 WHERE dbt_valid_to IS NULL

-- Get state as of a specific date
SELECT * FROM stg_em_account_scd2
WHERE dbt_valid_from <= '2026-04-30'
  AND COALESCE(dbt_valid_to, '9999-01-01') > '2026-04-30'
```

For deep mechanics: `data-analytics-architect` skill.

### 3.4 As-was-date snapshot strategy

`FINANCE_LINE_ANALYTICS` is INCREMENTAL, partitioned by `as_was_date`:

```sql
{{ config(
    materialized='incremental',
    unique_key=['agreement_line_item_id', 'as_was_date'],
    incremental_strategy='merge',
    cluster_by=['as_was_date'],
    on_schema_change='append_new_columns',
    contract={'enforced': True}
) }}

SELECT ...
FROM {{ ref('int_em_arr_line_base') }}
{% if is_incremental() %}
    -- Only compute new + current-period snapshots
    WHERE as_was_date >= (SELECT DATEADD(week, -1, MAX(as_was_date)) FROM {{ this }})
{% endif %}
```

Snapshot policy:
- **New snapshots added** weekly (Friday close)
- **Closed quarters immutable** — `as_was_date < CURRENT_DATE() - 30 days` requires SOX approval to re-run
- **Backfill** via `run_arr_historical_chain_standalone` macro with `arr_refactor_as_was_date_list` var

### 3.5 Currency variant infrastructure

Every monetary column exists in 3 variants. Macro pattern:

```sql
-- macro: convert_to_usd_current(amount_col, currency_col)
{%- macro convert_to_usd_current(amount_col, currency_col) -%}
    {{ amount_col }} * COALESCE((
        SELECT conversion_rate 
        FROM {{ ref('wd_fx_rates') }}
        WHERE from_currency = {{ currency_col }}
          AND to_currency = 'USD'
          AND effective_date = (
              SELECT MAX(effective_date) FROM {{ ref('wd_fx_rates') }}
          )
    ), 1.0)
{%- endmacro -%}

-- Usage in int_em_arr_line_base:
SELECT
    {{ convert_to_usd_current('arr_local', 'currency_iso_code') }} AS arr_usd_current,
    {{ convert_to_usd_hist('arr_local', 'currency_iso_code', 'as_was_date') }} AS arr_usd_hist,
    arr_local AS arr_usd_actual,  -- passthrough
    ...
```

For deep mechanics: `enterprise-data-architect/domain-finance-billing.md §6`.

### 3.6 Category UDTF / macro architecture

Categorization is encoded in:
1. **`get_arr_line_base_fn` UDTF** (in Snowflake) — heavy lifting per row
2. **Macros in `eda-dbt-em/macros/em/`** — Jinja-side category logic

UDTF pattern:
```sql
CREATE OR REPLACE FUNCTION certified_prod.stage.get_arr_line_base_fn(
    ali_id VARCHAR, as_was_date DATE
)
RETURNS TABLE (
    ali_id VARCHAR,
    arr_category VARCHAR,
    sub_category VARCHAR,
    delta_arr_usd_hist NUMBER,
    ...
)
LANGUAGE JAVASCRIPT
AS $$
    // categorization logic
    // joins to SSR_AGREEMENT_RELATIONSHIP
    // applies category decision tree
$$;
```

When category logic changes:
1. Update UDTF (immutable; bump version: `get_arr_line_base_fn_v2`)
2. Update macros that call the UDTF
3. Update YAML tests that validate category sums
4. Backfill `FINANCE_LINE_ANALYTICS` for affected `as_was_date`s
5. Validate ARR walk still balances
6. SOX sign-off if closed quarters affected

### 3.7 SSR resolution

`SSR_AGREEMENT_RELATIONSHIP` is the canonical resolver. Pattern:

```sql
-- In int_em_arr_line_base:
WITH ssr_resolved AS (
    SELECT
        line.*,
        ssr.new_agreement_id,
        ssr.ssr_category,  -- FLAT_RENEWAL, EXPANSION, CONTRACTION, MIGRATION
        CASE WHEN ssr.new_agreement_id IS NOT NULL THEN TRUE ELSE FALSE END AS is_ssr_resolved
    FROM {{ ref('stg_em_agreement_line_item_scd2') }} line
    LEFT JOIN {{ ref('ssr_agreement_relationship') }} ssr
      ON line.agreement_id = ssr.old_agreement_id
)
SELECT ... FROM ssr_resolved;
```

For new types of SSR (e.g., 3-to-1 line restructuring): extend `SSR_AGREEMENT_RELATIONSHIP` schema, not the categorization UDTF.

### 3.8 Performance + cost

Patterns for large-grain finance models:

| Pattern | When | Example |
|---|---|---|
| **Cluster on `as_was_date`** | All ARR models | Pruning on date filters |
| **Incremental merge** | Per-line × date facts | `FINANCE_LINE_ANALYTICS` |
| **Result cache** | High-traffic dashboards | Pre-warm via scheduled query |
| **MV for aggregations** | Read-heavy rollups (>100 queries/day) | Materialized view atop `MANAGED` |
| **Snowflake Optima** | Tables > 1TB | Auto-clustering replacement |
| **Dynamic Table** | Real-time-ish rollups | Replace incremental for selective use |

For deep performance: `snowflake-architect/performance-deep-dive.md`.

---

## §4. The cross-project mesh boundaries

`eda-dbt-em` consumes from:
- `eda-dbt-base` — raw Apttus wrappers + SCD2
- `eda-dbt-common` — fiscal calendar, FX rates, product hierarchy
- `eda-dbt-gtm` — `WD_AGREEMENT_LINE_SCD2`, `WD_OPPORTUNITY_SCD2`, `WD_PROPOSAL_*_SCD2`
- `eda-dbt-cx` — selectively, for renewal-risk inputs

`eda-dbt-em` is consumed by:
- `eda-dbt-cx` — for ARR-per-customer (health scoring input)
- `eda-dbt-semantic-layer` — all canonical finance metrics

Cross-project pattern:
```sql
-- In eda-dbt-em:
SELECT ... FROM {{ ref('eda_dbt_gtm', 'wd_agreement_line_scd2') }}
```

Mesh contracts:
- Every `eda-dbt-em` model in `MANAGED` / `AGGREGATIONS` / `DATA_PRODUCTS` consumed cross-project MUST have `contract: enforced`
- Breaking changes require version bumps (`finance_line_analytics_v2`)
- Schema changes in upstream `gtm` models that em depends on require coordination

For mesh deep-dive: `dbt-architect/mesh-and-contracts.md`.

---

## §5. The architectural decision tree

```
New metric / model request
├── Does it exist canonically?
│   ├── Yes → No build needed; route to finance-functional-analytics for query
│   └── No
│       ├── Is it a one-off ad-hoc analysis?
│       │   ├── Yes → Sigma workbook, no dbt model
│       │   └── No
│       │       ├── Is it a small variation on existing aggregation?
│       │       │   ├── Yes → Add column to existing AGGREGATIONS view
│       │       │   └── No
│       │       │       ├── Does it need new categorization logic?
│       │       │       │   ├── Yes → New UDTF + macros + tests + backfill
│       │       │       │   └── No → New AGGREGATIONS rollup
│       │       │       ├── Does it need new cohort structure?
│       │       │       │   ├── Yes → New cohort table (see cohort-and-vintage-modeling.md)
│       │       │       │   └── No
│       │       │       ├── Does it need forecast / forward-looking?
│       │       │       │   ├── Yes → Forecast model (see forecast-planning-architecture.md)
│       │       │       │   └── No
│       │       │       └── Does it touch SOX-controlled flow?
│       │       │           ├── Yes → SOX approval + special pipeline (see sox-and-audit-architecture.md)
│       │       │           └── No → Standard build
```

---

## §6. The "I want to add a metric" workflow

1. **Functional Architect drafts KPI spec** (`finance-functional-architect/kpi-specification-framework.md`)
2. **You review feasibility**:
   - Does the data exist in `FINANCE_LINE_ANALYTICS`?
   - What's the grain?
   - What's the materialization?
   - What contracts are affected?
3. **You design**:
   - Model placement (STAGE / INTERMEDIATE / MANAGED / AGGREGATIONS / DATA_PRODUCTS)
   - Materialization + incremental strategy
   - Tests
   - Cross-project impact
4. **Build** (or coordinate with engineering team)
5. **Validate**:
   - Walk balances
   - Reconciliation queries
   - Performance benchmarks
6. **Publish to catalog**:
   - Update `enterprise-data-products-catalog.md`
   - Update Atlan
7. **Announce**:
   - `#eda-data-products` Slack
   - Office hours for major consumers

---

## §7. The 5-level validation gate (before merging to prod)

Every change to `FINANCE_LINE_ANALYTICS` or downstream:

1. **dbt tests pass**: unique + not_null + relationships + expression_is_true
2. **ARR walk balances**: `BEGIN_ARR + Δs = END_ARR` within $1
3. **Total ARR matches prior version**: < 0.1% variance on unchanged categories
4. **SCD2 row count delta in expected range**: <5% week-over-week
5. **Sigma reconciliation**: hand-validate top-5 dashboards against prior-published numbers

For deep mechanics: `finance-bsa-data-analyst/profiling-validation-playbook.md`.

---

## §8. The SOX-controlled boundary

A subset of finance pipelines is SOX-compliant:

| Tier | Definition | Examples |
|---|---|---|
| **SOX Tier 1** | Direct input to financial statements | GL data, Zuora revenue, Workday FM journals |
| **SOX Tier 2** | Used in management reporting / investor metrics | ARR, ACV, NRR, GRR |
| **SOX Tier 3** | Operational only | Pipeline, marketing-sourced |

Tier 1 + Tier 2:
- Land in `BASE_SOX_PROD` (separate connector)
- Additional CI gate (Finance / SOX approver)
- Audit logging on every read / write
- Stricter retention
- Restated metrics require Jira → Compliance → Executive sign-off

For deep mechanics: `sox-and-audit-architecture.md`.

---

## §9. Anti-patterns (do NOT do)

- ❌ Add business logic in `DATA_PRODUCTS` views (push to MANAGED + AGGREGATIONS)
- ❌ Re-derive ARR from `BASE_PROD.SALESFORCE.APTTUS__AGREEMENTLINEITEM__C` — use `FINANCE_LINE_ANALYTICS`
- ❌ Re-implement SSR categorization manually — use `SSR_AGREEMENT_RELATIONSHIP`
- ❌ Skip `contract: enforced` on cross-project models
- ❌ Change `unique_key` on an existing incremental model in-place — requires backfill + SOX review
- ❌ Modify a closed-quarter snapshot without SOX approval
- ❌ Add a new ARR-by-X view by aggregating MANAGED differently — extend the existing pattern (don't fragment)
- ❌ Mix currency variants in a model
- ❌ Hardcode FY boundaries (use `get_fiscal_*` macros)
- ❌ Build a new metric without first checking `finance-functional-analytics` for the canonical
- ❌ Skip dbt unit tests (`dbt-architect/unit-tests-and-quality.md`) for new categorization logic

---

## §10. The roles you collaborate with

| Role | Their concern | Your concern with them |
|---|---|---|
| `finance-functional-analytics` (SME) | Metric definitions, query patterns | They request "we need this number"; you ensure model can deliver |
| `finance-functional-architect` (Product Owner) | KPI specs, requirements, governance | They formalize the spec; you design the model |
| `finance-bsa-data-analyst` | Profiling, validation, reports | They validate your builds end-to-end |
| `dbt-architect` | dbt mechanics, project structure | Cross-cutting on materialization, macros, mesh |
| `snowflake-architect` | Snowflake performance, cost, governance | Cross-cutting on warehouse sizing, clustering, cost |
| `data-analytics-architect` | Layered modeling, SCD2 | Cross-cutting on dim modeling |
| `salesforce-bsa-*` | SFDC source data | Source of truth for raw fields |
| Finance / FP&A | Business definitions, period close | Final approver of metric numbers |
| SOX / Compliance | Audit, immutability, restatement | Approval gate for Tier 1/2 changes |
| Platform team | Snowflake provisioning, Terraform | Approve new schemas, DBs |

---

## §11. Cross-references

- `metric-portfolio-architecture.md` — full architecture deep-dive
- `cohort-and-vintage-modeling.md` — cohort patterns
- `forecast-planning-architecture.md` — forecast integration
- `sox-and-audit-architecture.md` — SOX patterns
- `finance-functional-analytics` skill — metric SME
- `finance-functional-architect` skill — KPI spec + governance
- `finance-bsa-data-analyst` skill — validation patterns
- `dbt-architect` skill — dbt mechanics
- `snowflake-architect` skill — Snowflake performance
- `enterprise-data-architect/domain-finance-billing.md` — domain-level context
