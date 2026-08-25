# Metric Portfolio Architecture

The architectural patterns for the full finance metric portfolio — model
layering, grain design, incremental strategy, performance, contracts.

This is the "how does the metric machinery actually work?" reference for
the Principal Architect.

---

## §1. The 6-tier metric architecture

```
Tier 6: RECONCILIATION       ← ARR-to-Revenue, ARR-to-Billings, audit reconciliations
Tier 5: COHORT               ← Vintage / tenure cohort retention models
Tier 4: FORWARD              ← Renewal-risk-[REDACTED] ARR, pipeline-adj bookings
Tier 3: DERIVED              ← NRR / GRR / LRR rollups (DATA_PRODUCTS)
Tier 2: CATEGORIZED          ← ARR_*_CATEGORIES (AGGREGATIONS)
Tier 1: CANONICAL            ← FINANCE_LINE_ANALYTICS (MANAGED — the source of truth)
        |
        ▼
[stg / int models in STAGE]
        |
        ▼
[upstream: BASE_PROD + WD_*_SCD2 from gtm domain]
```

Architectural rules:
- **Tier 1 is the bedrock**: every higher tier derives from Tier 1
- **No tier reaches across tiers** (no Tier 3 reading from Tier 5; no Tier 6 reading from Tier 2 directly)
- **Tier 1 is incremental + immutable** (closed snapshots never change without SOX approval)
- **Tiers 2-6 are rebuildable** from Tier 1 + dimensions (idempotent rebuilds)

---

## §2. Grain design for each tier

| Tier | Model | Grain |
|---|---|---|
| 1 | `FINANCE_LINE_ANALYTICS` | (agreement_line_item_id, as_was_date) |
| 2 | `ARR_LINE_CATEGORIES` | (agreement_line_item_id, as_was_date, arr_category) |
| 2 | `ARR_PRODUCT_CATEGORIES` | (product_code_l3, as_was_date, arr_category) |
| 2 | `ARR_SKU_CATEGORIES` | (sku_code, as_was_date, arr_category) |
| 2 | `ARR_ACCOUNT_CATEGORIES` | (account_id, as_was_date, arr_category) |
| 2 | `ARR_REGION_SEGMENT_CATEGORIES` | (region, segment, as_was_date, arr_category) |
| 2 | `ARR_INDUSTRY_CATEGORIES` | (industry, as_was_date, arr_category) |
| 2 | `ARR_STRATEGIC_PARTNER_CATEGORIES` | (is_partner_deal, as_was_date, arr_category) |
| 3 | `ARR_PRODUCT_NDR_DASH_V2` | (product_code_l3, fiscal_quarter) |
| 3 | `ARR_GROWTH_DECOMPOSITION_DASH` | (fiscal_quarter) |
| 4 | `ARR_FORECAST_RENEWAL_RISK_ADJUSTED` | (account_id, forward_fiscal_quarter) |
| 5 | `ARR_VINTAGE_COHORT` | (vintage_fiscal_year, tenure_quarter) |
| 5 | `ARR_TENURE_COHORT` | (account_id, tenure_bucket, fiscal_quarter) |
| 6 | `ARR_TO_REVENUE_RECONCILIATION` | (account_id, fiscal_quarter) |
| 6 | `ARR_TO_BILLINGS_RECONCILIATION` | (account_id, fiscal_quarter) |

Every grain documented in YAML:
```yaml
models:
  - name: arr_product_categories
    description: |
      Grain: one row per (product_code_l3, as_was_date, arr_category).
      Test: unique on (product_code_l3, as_was_date, arr_category).
```

---

## §3. The categorization layer architecture

The categorization is the most critical + most tested logic in the finance domain.

### 3.1 Where logic lives

```
get_arr_line_base_fn UDTF (Snowflake JavaScript UDTF)
   │
   ├── INPUT: ali_id, as_was_date
   │
   ├── PROCESSING:
   │   - Lookup prior_arr from prior as_was_date snapshot
   │   - Lookup SSR linkage from SSR_AGREEMENT_RELATIONSHIP
   │   - Apply decision tree (see categorization-framework.md)
   │   - Compute sub-category attribution (Volume / Price / Mix)
   │
   └── OUTPUT: arr_category, sub_category, delta_arr per variant

Jinja macros (eda-dbt-em/macros/em/)
   │
   ├── categorize_arr_line(...)
   │   - Calls UDTF
   │   - Handles edge cases (NULL, division-by-zero)
   │
   ├── compute_sku_change_delta(...)
   ├── compute_volume_price_mix(...)
   ├── apply_partner_attribution(...)
   └── apply_acquisition_baseline(...)
```

### 3.2 Versioning the UDTF

Categorization logic changes are HIGH RISK. Version the UDTF:

```sql
-- v1 (deprecated)
CREATE OR REPLACE FUNCTION certified.stage.get_arr_line_base_fn_v1(...) ...

-- v2 (current)
CREATE OR REPLACE FUNCTION certified.stage.get_arr_line_base_fn_v2(...) ...

-- v3 (in development)
CREATE OR REPLACE FUNCTION certified.stage.get_arr_line_base_fn_v3(...) ...
```

Migration:
1. New version built side-by-side
2. Backfill historical `as_was_date`s with v2 → v3 (parallel-write)
3. Reconcile v2 vs v3 outputs (variance acceptable < 0.01%)
4. Cutover (point `FINANCE_LINE_ANALYTICS` build at v3)
5. Sunset v2 after 90-day shadow period

---

## §4. The 3 currency variants — architectural pattern

### 4.1 Storage pattern

Every monetary column stored in 3 variants in `FINANCE_LINE_ANALYTICS`:

```sql
CREATE TABLE FINANCE_LINE_ANALYTICS (
    agreement_line_item_id VARCHAR,
    as_was_date DATE,
    
    -- ARR (3 variants)
    arr_usd_current NUMBER(38, 2),
    arr_usd_hist    NUMBER(38, 2),
    arr_usd_actual  NUMBER(38, 2),  -- local currency, no conversion
    
    -- ACV (3 variants)
    acv_usd_current NUMBER(38, 2),
    acv_usd_hist    NUMBER(38, 2),
    acv_usd_actual  NUMBER(38, 2),
    
    -- TCV (3 variants)
    tcv_usd_current NUMBER(38, 2),
    tcv_usd_hist    NUMBER(38, 2),
    tcv_usd_actual  NUMBER(38, 2),
    
    -- ... etc for each monetary column
);
```

Pros: no JOIN to FX at query time; pre-computed.
Cons: 3x storage; revaluation requires backfill.

### 4.2 Computation pattern

```sql
-- In int_em_arr_line_base:
SELECT
    line.*,
    
    -- USD_ACTUAL (passthrough)
    line.arr_local AS arr_usd_actual,
    
    -- USD_HIST (locked at transaction date)
    line.arr_local 
        * (SELECT conversion_rate FROM wd_fx_rates 
           WHERE from_currency = line.currency_iso_code AND to_currency = 'USD'
             AND effective_date = (SELECT MAX(effective_date) FROM wd_fx_rates 
                                   WHERE effective_date <= line.term_start_date))
        AS arr_usd_hist,
    
    -- USD_CURRENT (latest FX)
    line.arr_local 
        * (SELECT conversion_rate FROM wd_fx_rates 
           WHERE from_currency = line.currency_iso_code AND to_currency = 'USD'
             AND effective_date = (SELECT MAX(effective_date) FROM wd_fx_rates))
        AS arr_usd_current
FROM stg_em_agreement_line_item_scd2 line
```

### 4.3 Period-end FX locking

Treasury locks FX rates per quarter-end for SOX-compliant reporting:
- Lock published via `REF_FX_OVERRIDE` Google Sheet
- Applied via `stg_em_fx_locked_per_period` → `FINANCE_LINE_ANALYTICS` for the close `as_was_date`

For period-end snapshots: `USD_HIST` uses the **locked** rate (not the live `wd_fx_rates`).

---

## §5. Incremental strategy — `FINANCE_LINE_ANALYTICS`

### 5.1 Strategy choice

Incremental merge on `(agreement_line_item_id, as_was_date)`:

```sql
{{ config(
    materialized='incremental',
    unique_key=['agreement_line_item_id', 'as_was_date'],
    incremental_strategy='merge',
    cluster_by=['as_was_date'],
    on_schema_change='append_new_columns',
    contract={'enforced': True}
) }}

WITH new_rows AS (
    SELECT ...
    FROM {{ ref('int_em_arr_line_base') }}
    {% if is_incremental() %}
        WHERE as_was_date >= (SELECT DATEADD(week, -1, MAX(as_was_date)) FROM {{ this }})
    {% endif %}
)
SELECT * FROM new_rows;
```

### 5.2 Why this strategy

| Alternative | Why not |
|---|---|
| `append` | Closed-quarter snapshots can't be edited; but we DO need to rebuild current week's snapshot for late data |
| `delete+insert` | Wastes resources rebuilding closed quarters every run |
| `insert_overwrite` (partition replacement) | Snowflake doesn't have native partition replacement; requires custom logic |
| **`merge`** | Updates current snapshot in place; closed snapshots preserved | ✓ chosen |

### 5.3 Backfill mechanics

For historical reload (rare, SOX-approved):
- `dbt_project.yml` var: `arr_refactor_as_was_date_list: ['2025-05-06', '2025-08-06']`
- `on-run-start` macro `run_arr_historical_chain_standalone` purges those dates and reloads
- Triggered: `dbt run --vars '{"run_arr_historical_chain_standalone": true, "arr_refactor_as_was_date_list": [...]}'`

NEVER backfill closed-quarter snapshots without:
1. Jira ticket with reason
2. SOX approver sign-off
3. Validation that reconciliation queries pass post-reload

---

## §6. The aggregation pattern (Tier 2)

`ARR_*_CATEGORIES` views are derived from Tier 1.

### 6.1 Standard pattern

```sql
{{ config(materialized='table') }}

WITH walks AS (
    SELECT
        product_code_l3,  -- the slice dimension (varies per view)
        as_was_date,
        fiscal_quarter,
        arr_category,
        sub_category,
        SUM(arr_usd_current) AS arr_usd_current,
        SUM(arr_usd_hist)    AS arr_usd_hist,
        SUM(arr_usd_actual)  AS arr_usd_actual,
        COUNT(DISTINCT account_id) AS distinct_accounts,
        COUNT(*) AS line_count
    FROM {{ ref('finance_line_analytics') }}
    WHERE is_arr_eligible = TRUE
    GROUP BY 1, 2, 3, 4, 5
)
SELECT * FROM walks;
```

Materialize as **table** (read-heavy):
- Refreshed by orchestration after `FINANCE_LINE_ANALYTICS` completes
- Pre-aggregated for low-latency dashboard reads

### 6.2 Why not view?

For a single dashboard query: view is fine.
For 100+ daily dashboard queries: table is 10-100x cheaper (avoid re-aggregating).

### 6.3 New aggregation rollup pattern

When adding a new slice (e.g., `ARR_TENURE_COHORT_CATEGORIES`):
1. Copy template from `ARR_PRODUCT_CATEGORIES`
2. Replace slice column
3. Add to `dbt_project.yml` schemas
4. Test: unique on (slice, as_was_date, arr_category)
5. Reconciliation: sum of slice = total ARR

---

## §7. The contract layer (Tier 3 — Data Products)

Every model in `DATA_PRODUCTS` is **contracted**:

```yaml
models:
  - name: arr_product_net_dollar_retention_dash_v2
    config:
      contract: { enforced: true }
    meta:
      owner: "@finance-ae-team"
      sla_freshness_hours: 4
      sox_tier: 2
      consumers:
        - sigma: "ARR Dashboard - NDR"
        - downstream_dbt: ["eda-dbt-semantic-layer"]
    columns:
      - name: product_code_l3
        data_type: varchar(64)
        constraints: [ { type: not_null } ]
      - name: fiscal_quarter
        data_type: varchar(8)
        constraints: [ { type: not_null } ]
      - name: ndr_pct
        data_type: number(10, 4)
    tests:
      - unique: { columns: [product_code_l3, fiscal_quarter] }
      - dbt_utils.expression_is_true:
          expression: "ndr_pct BETWEEN 0.5 AND 2.0"
```

Breaking changes require version bump (`_v3`). Old version lives in parallel for 90+ days.

---

## §8. The performance toolkit

| Issue | Diagnostic | Fix |
|---|---|---|
| `FINANCE_LINE_ANALYTICS` build slow | Query profile shows full table scan | Add `cluster_by(['as_was_date'])` |
| Aggregation slow | Aggregation reads MANAGED uncached | Pre-aggregate as table; use result cache |
| Dashboard slow | Sigma query scans many rows | Add filter pushdown; use DATA_PRODUCTS publish |
| Backfill consumes excess credits | Full rebuild of all snapshots | Use incremental rebuild with `as_was_date` filter |
| FX revaluation expensive | All snapshots re-compute | Lock FX per quarter; revalue only current period |

For deep performance: `snowflake-architect/performance-deep-dive.md`.

---

## §9. Testing strategy

### 9.1 Test pyramid for finance models

| Level | Tests | Where |
|---|---|---|
| **L1: Schema** | unique, not_null, accepted_values | YAML schema |
| **L2: Business rules** | expression_is_true (ARR walk balances, NRR in range) | YAML |
| **L3: Reconciliation** | Compare to prior period; tie-out to source | Macros / analyses |
| **L4: Unit tests** | Test category UDTF on synthetic data | dbt unit tests |
| **L5: Integration** | End-to-end ARR walk validated | Manual + Sigma reconciliation |

### 9.2 Required tests for new categorization changes

```yaml
- dbt_utils.expression_is_true:
    name: arr_walk_balances_within_dollar
    expression: |
      ABS(
        (begin_arr + new_logo + expansion + contraction + churn + sku_change) - end_arr
      ) < 1.0
    
- dbt_utils.expression_is_true:
    name: nrr_in_reasonable_range
    expression: "nrr_pct BETWEEN 0.5 AND 2.5"

- dbt_utils.expression_is_true:
    name: grr_in_reasonable_range
    expression: "grr_pct BETWEEN 0.5 AND 1.0"

- dbt_utils.expression_is_true:
    name: no_negative_arr
    expression: "arr_usd_current >= 0"
```

### 9.3 Unit tests for categorization UDTF

```yaml
unit_tests:
  - name: test_new_logo_categorization
    model: int_em_arr_line_base
    given:
      - input: ref('stg_em_agreement_line_item_scd2')
        rows:
          - {ali_id: 'L1', account_id: 'A1', as_was_date: '2026-02-06', arr_usd_current: 100000}
      - input: ref('ssr_agreement_relationship')
        rows: []  # no SSR for this account
    expect:
      rows:
        - {ali_id: 'L1', arr_category: 'NEW_LOGO', sub_category: 'New New'}
```

For unit-test mechanics: `dbt-architect/unit-tests-and-quality.md`.

---

## §10. Reference data architecture (lookups)

Finance depends heavily on Google-Sheets-controlled reference data:

| Sheet | Purpose | Snowflake landing | Stage model |
|---|---|---|---|
| `REF_FIN_CUSTOMIZED_DATA` | ARR / ACV manual overrides | `BASE_PROD.GOOGLE_SHEETS.REF_FIN_CUSTOMIZED_DATA` | `stg_em_lkp_fin_customized_data` |
| `REF_PRODUCT_HIERARCHY` | Product L3/L4/L5 mapping | ... | `stg_em_int_product_hierarchy` |
| `REF_ACQUISITION_MAPPING` | Acquired product → Workday SKU | ... | `stg_em_int_acquisition_mapping` |
| `REF_FX_OVERRIDE` | Period-end FX locks | ... | `stg_em_fx_locked_per_period` |
| `REF_TCV_CORRECTION` | TCV correction sheet | ... | `stg_em_lkp_wd_fin_tcv_correction` |
| `REF_STRATEGIC_PARTNERS` | Strategic partner accounts | ... | `stg_em_lkp_strategic_partners` |

Architectural pattern:
1. Sheet maintained by Finance Ops in Google Sheets
2. Fivetran syncs every 15 min → `BASE_PROD.GOOGLE_SHEETS.*`
3. Stage model adds type-casting + audit
4. Consumed in `int_em_*` models via LEFT JOIN
5. COALESCE on override + raw values
6. Audit trail preserved (both raw + corrected stored)

Anti-pattern: ❌ overwrite raw value with override (loses audit trail)

---

## §11. The post-IA architecture (current state)

Post-IA, the architecture is:

```
[Old: certified_prod] — DEPRECATED
↓
[New: finance_prod + finance_int_prod] — current

Database split:
- finance_int_prod.stage  ← STAGE schema for intermediates
- finance_prod.managed    ← MANAGED schema for facts
- finance_prod.aggregations  ← AGGREGATIONS schema for rollups
- finance_prod.data_products  ← DATA_PRODUCTS schema for BI publishing
```

What's still in `eda-dbt-em` repo:
- Some `dbt_project.yml` literals still reference `certified` (legacy)
- Prod target overrides these to `finance_prod` (runtime correct)
- Macros + UDTFs in `eda-dbt-em/macros/em/` may have `certified.stage.*` UDTF references (need updating over time)

For new work: always target `finance_prod` directly. `certified_prod` is read-only legacy.

---

## §12. The "I'm refactoring an existing model" workflow

When refactoring a critical model (e.g., `FINANCE_LINE_ANALYTICS`):

1. **Quantify blast radius**: which downstream models depend?
   - `dbt ls --select +finance_line_analytics`
2. **Reconciliation harness**: build query that diffs old vs new outputs
   - Per `as_was_date`, per category, per dimension
3. **Build new model side-by-side** (e.g., `finance_line_analytics_v2`)
4. **Backfill new model** for full history
5. **Reconcile**: variance < 0.01% per slice
6. **Cutover**: point downstream models at v2
7. **Shadow period**: keep v1 alive for 30-60 days
8. **Sunset v1**

For refactor patterns: `dbt-architect/unit-tests-and-quality.md`.

---

## §13. Cross-references

- `cohort-and-vintage-modeling.md` — cohort architecture
- `forecast-planning-architecture.md` — forecast integration
- `sox-and-audit-architecture.md` — SOX patterns
- `dbt-architect/microbatch-and-state.md` — incremental strategies
- `snowflake-architect/performance-deep-dive.md` — performance
- `finance-functional-analytics/categorization-framework.md` — categorization logic
- `enterprise-data-architect/domain-finance-billing.md` — domain context
