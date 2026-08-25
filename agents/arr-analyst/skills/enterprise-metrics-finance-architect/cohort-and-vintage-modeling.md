# Cohort and Vintage Modeling — Architecture at Scale

Cohort retention is mathematically straightforward but architecturally
challenging at enterprise scale. Doing it naively means quadratic compute
(every cohort × every snapshot). Doing it right means incremental cohort
tables, immutable cohort definitions, and pre-aggregated retention curves.

This doc covers the architecture patterns for cohort + vintage analytics.

---

## §1. Cohort types — what we model

| Cohort | Definition | Use |
|---|---|---|
| **Vintage** | Customers acquired in a specific fiscal year/quarter | Year-over-year cohort quality |
| **Tenure** | Customers by months-since-acquisition bucket | "How does expansion vary by maturity?" |
| **Segment** | Customers by industry / size / region | Compare retention across segments |
| **Product** | Customers by first product purchased | "Which entry product → best retention?" |
| **Channel** | Customers by acquisition channel (Direct / Partner / Marketing-sourced) | Channel-specific NRR |
| **Acquisition** | Customers from a specific Workday-acquired company | Native vs acquired customer dynamics |

Each cohort type has its own architectural patterns.

---

## §2. The cohort definition table (immutable)

Every cohort has a definition table:

```sql
-- ARR_VINTAGE_COHORT_DEFINITION
CREATE TABLE FINANCE_PROD.MANAGED.ARR_VINTAGE_COHORT_DEFINITION (
    account_id VARCHAR,
    vintage_fiscal_year VARCHAR,
    vintage_fiscal_quarter VARCHAR,
    first_contract_date DATE,
    acquisition_channel VARCHAR,
    initial_product_l3 VARCHAR,
    initial_arr_usd_hist NUMBER(38,2),
    
    PRIMARY KEY (account_id, vintage_fiscal_year)
);

-- Once an account is in a cohort, never moves out (immutability principle)
```

Pattern:
- Append-only (no updates)
- Definition based on first contract date (deterministic)
- Re-derivable from `FINANCE_LINE_ANALYTICS` if rebuilt

Build:
```sql
{{ config(materialized='incremental', incremental_strategy='append') }}

WITH first_contracts AS (
    SELECT
        account_id,
        MIN(term_start_date) AS first_contract_date
    FROM {{ ref('finance_line_analytics') }}
    WHERE is_arr_eligible = TRUE
    GROUP BY 1
)
SELECT
    fc.account_id,
    {{ get_fiscal_year('fc.first_contract_date') }} AS vintage_fiscal_year,
    {{ get_fiscal_quarter('fc.first_contract_date') }} AS vintage_fiscal_quarter,
    fc.first_contract_date,
    a.acquisition_channel,
    line.product_code_l3 AS initial_product_l3,
    line.arr_usd_hist AS initial_arr_usd_hist
FROM first_contracts fc
JOIN {{ ref('stg_em_account_scd2') }} a ON fc.account_id = a.account_id AND a.is_current = TRUE
JOIN {{ ref('finance_line_analytics') }} line 
  ON fc.account_id = line.account_id 
  AND fc.first_contract_date = line.term_start_date
  AND line.is_arr_eligible = TRUE
{% if is_incremental() %}
WHERE NOT EXISTS (SELECT 1 FROM {{ this }} WHERE account_id = fc.account_id)
{% endif %}
```

---

## §3. The cohort retention table (incremental, scaled)

Pre-aggregated cohort ARR over time:

```sql
-- ARR_VINTAGE_COHORT_RETENTION
{{ config(
    materialized='incremental',
    unique_key=['vintage_fiscal_year', 'as_was_date'],
    incremental_strategy='merge',
    cluster_by=['as_was_date']
) }}

WITH cohort_snapshots AS (
    SELECT
        c.vintage_fiscal_year,
        a.as_was_date,
        SUM(a.arr_usd_hist) AS cohort_arr_usd_hist,
        SUM(a.arr_usd_current) AS cohort_arr_usd_current,
        COUNT(DISTINCT a.account_id) AS active_account_count,
        COUNT(DISTINCT c.account_id) AS cohort_size_at_acquisition
    FROM {{ ref('arr_vintage_cohort_definition') }} c
    JOIN {{ ref('finance_line_analytics') }} a 
      ON c.account_id = a.account_id
    WHERE a.is_arr_eligible = TRUE
      {% if is_incremental() %}
        AND a.as_was_date >= (SELECT DATEADD(week, -1, MAX(as_was_date)) FROM {{ this }})
      {% endif %}
    GROUP BY 1, 2
),
baselines AS (
    SELECT
        c.vintage_fiscal_year,
        SUM(c.initial_arr_usd_hist) AS baseline_arr_usd_hist
    FROM {{ ref('arr_vintage_cohort_definition') }} c
    GROUP BY 1
)
SELECT
    cs.vintage_fiscal_year,
    cs.as_was_date,
    cs.cohort_arr_usd_hist,
    cs.cohort_arr_usd_current,
    b.baseline_arr_usd_hist,
    cs.cohort_arr_usd_hist / NULLIF(b.baseline_arr_usd_hist, 0) AS cohort_nrr,
    cs.active_account_count,
    cs.cohort_size_at_acquisition,
    cs.active_account_count * 1.0 / NULLIF(cs.cohort_size_at_acquisition, 0) AS cohort_lrr,
    DATEDIFF(month, 
             DATE(LEFT(cs.vintage_fiscal_year, 2) || '24-02-01'),  -- approximate vintage start
             cs.as_was_date) AS tenure_months
FROM cohort_snapshots cs
JOIN baselines b ON cs.vintage_fiscal_year = b.vintage_fiscal_year;
```

Output:
| vintage_fiscal_year | as_was_date | cohort_arr | baseline_arr | cohort_nrr | active_accounts | cohort_lrr | tenure_months |
|---|---|---|---|---|---|---|---|
| FY24 | 2024-02-06 | 100M | 100M | 100% | 500 | 100% | 0 |
| FY24 | 2024-05-06 | 102M | 100M | 102% | 498 | 99.6% | 3 |
| FY24 | 2024-08-06 | 108M | 100M | 108% | 496 | 99.2% | 6 |
| ... | ... | ... | ... | ... | ... | ... | ... |

---

## §4. The tenure-cohort architecture

Different from vintage: tenure cohort assignment is **moving** (an account moves from "0-12 mo" to "12-24 mo" as it ages).

```sql
-- ARR_TENURE_COHORT_ASSIGNMENT (rebuilt every snapshot)
WITH first_contracts AS (
    SELECT account_id, MIN(term_start_date) AS first_contract_date
    FROM {{ ref('finance_line_analytics') }}
    WHERE is_arr_eligible = TRUE
    GROUP BY 1
)
SELECT
    fc.account_id,
    fla.as_was_date,
    DATEDIFF(month, fc.first_contract_date, fla.as_was_date) AS tenure_months,
    CASE
        WHEN DATEDIFF(month, fc.first_contract_date, fla.as_was_date) <= 12 THEN '0-12 mo'
        WHEN DATEDIFF(month, fc.first_contract_date, fla.as_was_date) <= 24 THEN '12-24 mo'
        WHEN DATEDIFF(month, fc.first_contract_date, fla.as_was_date) <= 36 THEN '24-36 mo'
        WHEN DATEDIFF(month, fc.first_contract_date, fla.as_was_date) <= 60 THEN '36-60 mo'
        ELSE '60+ mo'
    END AS tenure_bucket
FROM first_contracts fc
CROSS JOIN (SELECT DISTINCT as_was_date FROM {{ ref('finance_line_analytics') }}) dates
LEFT JOIN {{ ref('finance_line_analytics') }} fla 
  ON fc.account_id = fla.account_id AND fla.as_was_date = dates.as_was_date;
```

Then aggregate by tenure bucket:
```sql
-- ARR_TENURE_COHORT_CATEGORIES
SELECT
    t.tenure_bucket,
    a.fiscal_quarter,
    a.arr_category,
    SUM(a.arr_usd_hist) AS arr_usd_hist
FROM ARR_ACCOUNT_CATEGORIES a
JOIN ARR_TENURE_COHORT_ASSIGNMENT t 
  ON a.account_id = t.account_id 
  AND DATE(a.fiscal_quarter_start_date) = t.as_was_date
GROUP BY 1, 2, 3;
```

---

## §5. The "cohort retention curve" visualization model

For dashboards, you often need a "curve" view:

```sql
-- ARR_VINTAGE_COHORT_CURVE
SELECT
    vintage_fiscal_year,
    tenure_months,
    cohort_nrr,
    cohort_lrr,
    AVG(cohort_nrr) OVER (PARTITION BY tenure_months) AS avg_nrr_at_tenure,
    cohort_nrr - AVG(cohort_nrr) OVER (PARTITION BY tenure_months) AS vintage_vs_avg
FROM ARR_VINTAGE_COHORT_RETENTION
ORDER BY 1, 2;
```

Renders as the classic retention curve:
- X-axis: tenure_months
- Y-axis: cohort_nrr
- One line per vintage

---

## §6. The segment-cohort architecture

Combining segment + vintage:

```sql
-- ARR_SEGMENT_VINTAGE_COHORT
-- Grain: (vintage_fiscal_year, segment, as_was_date)
WITH segmented_cohorts AS (
    SELECT
        c.vintage_fiscal_year,
        a.segment,  -- from SCD2 lookup
        a.as_was_date,
        SUM(a.arr_usd_hist) AS arr_usd_hist
    FROM {{ ref('arr_vintage_cohort_definition') }} c
    JOIN {{ ref('finance_line_analytics') }} a ON c.account_id = a.account_id
    JOIN {{ ref('stg_em_account_scd2') }} acc 
      ON c.account_id = acc.account_id 
      AND acc.dbt_valid_from <= a.as_was_date 
      AND COALESCE(acc.dbt_valid_to, '9999-01-01') > a.as_was_date  -- as-was segment
    GROUP BY 1, 2, 3
)
SELECT * FROM segmented_cohorts;
```

Key: use as-was segment via SCD2 (not current segment) for true historical cohort tracking.

---

## §7. Performance considerations

### 7.1 Cross-product joins (the trap)

Naive cohort modeling:
```sql
-- BAD: O(cohorts × snapshots × accounts)
SELECT ... FROM accounts CROSS JOIN snapshots ...
```

This balloons quickly. Workday has ~10K accounts × 4 years × 200 snapshots = 8M rows just for the cross product, before joining facts.

Fix: aggregate first, then join:
```sql
-- GOOD: pre-aggregate per (account, as_was_date), then join cohort definition
WITH per_account_per_date AS (
    SELECT account_id, as_was_date, SUM(arr_usd_hist) AS arr
    FROM finance_line_analytics
    WHERE is_arr_eligible = TRUE
    GROUP BY 1, 2
)
SELECT 
    c.vintage_fiscal_year,
    pad.as_was_date,
    SUM(pad.arr) AS cohort_arr
FROM per_account_per_date pad
JOIN cohort_definition c ON pad.account_id = c.account_id
GROUP BY 1, 2;
```

### 7.2 Incremental cohort rebuilds

Cohort retention tables incremental on `as_was_date`. Pattern:
```sql
{% if is_incremental() %}
    WHERE as_was_date >= (SELECT DATEADD(week, -1, MAX(as_was_date)) FROM {{ this }})
{% endif %}
```

When a cohort definition changes (rare): full rebuild required.

### 7.3 Materialization strategy

| Model | Materialization | Cluster |
|---|---|---|
| `ARR_VINTAGE_COHORT_DEFINITION` | Incremental table (append) | `(vintage_fiscal_year)` |
| `ARR_VINTAGE_COHORT_RETENTION` | Incremental table (merge) | `(as_was_date)` |
| `ARR_TENURE_COHORT_ASSIGNMENT` | Table (rebuilt each run) | `(as_was_date)` |
| `ARR_VINTAGE_COHORT_CURVE` | View | — |

---

## §8. Cohort metric examples

### 8.1 "How does FY24 cohort compare to FY23 cohort at 12-month tenure?"

```sql
SELECT
    vintage_fiscal_year,
    cohort_nrr AS nrr_at_12mo
FROM ARR_VINTAGE_COHORT_RETENTION
WHERE tenure_months = 12
  AND vintage_fiscal_year IN ('FY23', 'FY24')
ORDER BY 1;
```

### 8.2 "Which segment had best cohort retention in FY25?"

```sql
SELECT
    segment,
    AVG(cohort_arr_usd_hist / baseline_arr_usd_hist) AS avg_cohort_nrr
FROM ARR_SEGMENT_VINTAGE_COHORT
WHERE vintage_fiscal_year = 'FY25'
  AND tenure_months BETWEEN 6 AND 12
GROUP BY 1
ORDER BY 2 DESC;
```

### 8.3 "What's the long-term value of an Enterprise customer vs SMB?"

```sql
WITH long_term AS (
    SELECT
        v.segment_initial,
        AVG(v.cohort_arr_usd_hist / v.baseline_arr_usd_hist) AS avg_nrr_at_36mo
    FROM ARR_SEGMENT_VINTAGE_COHORT v
    WHERE v.tenure_months BETWEEN 30 AND 36
    GROUP BY 1
)
SELECT
    segment_initial,
    avg_nrr_at_36mo,
    -- 3-year cumulative value (approximate)
    avg_nrr_at_36mo * 3 AS approx_3yr_arr_multiple
FROM long_term;
```

---

## §9. Validation tests for cohort models

```yaml
- dbt_utils.expression_is_true:
    name: cohort_nrr_in_reasonable_range
    expression: "cohort_nrr BETWEEN 0.3 AND 3.0"

- dbt_utils.expression_is_true:
    name: cohort_lrr_in_reasonable_range
    expression: "cohort_lrr BETWEEN 0.3 AND 1.0"

- dbt_utils.expression_is_true:
    name: cohort_size_immutable
    expression: |
      cohort_size_at_acquisition = (
        SELECT COUNT(DISTINCT account_id) 
        FROM {{ ref('arr_vintage_cohort_definition') }}
        WHERE vintage_fiscal_year = '{{ vintage_fiscal_year }}'
      )

- dbt_utils.expression_is_true:
    name: vintage_year_consistent
    expression: "vintage_fiscal_year ~ '^FY[0-9]{2}$'"
```

---

## §10. The "cohort definition rebuild" SOP

When you need to rebuild cohort definitions (rare, requires careful planning):

1. **Validate that change is needed** (e.g., changed definition of "first contract")
2. **Side-by-side build**: `arr_vintage_cohort_definition_v2`
3. **Reconcile**: account-level diff vs v1
4. **Notify consumers**: dashboards may shift
5. **SOX approval** if affects reported NRR
6. **Cutover**: 30-day shadow
7. **Sunset v1**

---

## §11. Cross-references

- `metric-portfolio-architecture.md` — base layer architecture
- `finance-functional-analytics/retention-deep-dive.md` — retention math
- `dbt-architect/microbatch-and-state.md` — incremental patterns
- `snowflake-architect/performance-deep-dive.md` — performance
