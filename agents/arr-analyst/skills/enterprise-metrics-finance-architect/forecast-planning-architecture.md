# Forecast & Planning Architecture

How forward-looking finance metrics (renewal-risk-[REDACTED] ARR,
pipeline-coverage-adjusted bookings, expected NRR) get computed and
integrated with FP&A planning tools (Adaptive Planning, Clari).

The architectural challenge: forecast metrics are derived from probabilistic
inputs (risk scores, win rates) joined to canonical-as-of-today metrics.
Output must be traceable, auditable, and re-computable when inputs change.

---

## §1. The forward-looking metric portfolio

| Metric | Inputs | Use |
|---|---|---|
| **Renewal-risk-[REDACTED] ARR** | Current ARR × (1 - churn_risk_score) | "Expected ARR in 12 months from existing customers" |
| **Pipeline-coverage-adjusted ACV** | Pipeline × win_rate × stage_weight | "Expected bookings this quarter" |
| **Slip-adjusted close-quarter ACV** | Forecast ACV × (1 - slip_rate) | "Realistic close-quarter forecast" |
| **Forecast NRR** | (Begin ARR + Expected expansion - Expected churn) / Begin ARR | "Where will NRR land?" |
| **Forecast bookings** | Per-rep / per-territory ACV forecast | "Where will sales land vs quota?" |
| **AOP (Annual Operating Plan)** | Manual plan from Adaptive | "What did we commit to?" |
| **Forecast variance** | Forecast - Actual | "How accurate is our forecast?" |

---

## §2. The forecast architecture

```
Inputs:
  - Canonical ARR (FINANCE_LINE_ANALYTICS)
  - Churn risk scores (CHURN_RISK_SCORE — from CX / ML)
  - Win rate (BT_WIN_RATE — from GTM)
  - Stage weights (forecast_method per stage)
  - Sales rep forecasts (ae_forecast / rsd_forecast / etc.)
  - Adaptive Planning AOP (from Adaptive sync)
  
Processing:
  - Forecast model: applies probabilistic adjustments
  - Forecast snapshot: stores point-in-time forecast for accuracy tracking
  - Forecast walk: reconciles forecast vs actual at period close

Outputs:
  - ARR_FORECAST_RENEWAL_RISK_ADJUSTED
  - ACV_FORECAST_PIPELINE_ADJUSTED
  - NRR_FORECAST_DASH
  - FORECAST_ACCURACY_DASH
```

---

## §3. Renewal-risk-[REDACTED] ARR (a forward-looking metric)

### 3.1 Definition

For each account, expected ARR 12 months from now:
```
Expected_ARR_12mo = SUM(line_arr × (1 - churn_risk_score) × expected_expansion_multiplier)
```

Where:
- `churn_risk_score` from CX team (Gainsight + ML model)
- `expected_expansion_multiplier` from sales / FP&A (per segment + tenure)

### 3.2 Architecture

```sql
{{ config(materialized='table', cluster_by=['as_of_date']) }}

WITH current_arr AS (
    SELECT
        account_id,
        SUM(arr_usd_current) AS current_arr
    FROM {{ ref('finance_line_analytics') }}
    WHERE as_was_date = (SELECT MAX(as_was_date) FROM {{ ref('finance_line_analytics') }})
      AND is_arr_eligible = TRUE
    GROUP BY 1
),
risk_scores AS (
    SELECT account_id, churn_risk_score
    FROM {{ ref('eda_dbt_cx', 'churn_risk_score') }}
    WHERE as_of_date = (SELECT MAX(as_of_date) FROM {{ ref('eda_dbt_cx', 'churn_risk_score') }})
),
expansion_assumptions AS (
    SELECT
        a.account_id,
        a.segment,
        DATEDIFF(month, MIN(line.term_start_date), CURRENT_DATE) AS tenure_months,
        ea.expected_expansion_multiplier
    FROM {{ ref('finance_line_analytics') }} line
    JOIN {{ ref('stg_em_account_scd2') }} a ON line.account_id = a.account_id AND a.is_current = TRUE
    LEFT JOIN {{ ref('ref_expansion_assumptions') }} ea  -- FP&A-maintained table
      ON ea.segment = a.segment 
      AND ea.tenure_bucket = CASE WHEN DATEDIFF(...) <= 12 THEN '0-12 mo' ELSE '12+ mo' END
    GROUP BY 1, 2, ea.expected_expansion_multiplier
)
SELECT
    CURRENT_DATE AS as_of_date,
    ca.account_id,
    ca.current_arr,
    rs.churn_risk_score,
    ea.expected_expansion_multiplier,
    -- forward-looking calculation
    ca.current_arr 
      * (1 - COALESCE(rs.churn_risk_score, 0.05))  -- default 5% churn risk if no score
      * (1 + COALESCE(ea.expected_expansion_multiplier, 0.10))  -- default 10% expansion if no assumption
      AS expected_arr_12mo
FROM current_arr ca
LEFT JOIN risk_scores rs ON ca.account_id = rs.account_id
LEFT JOIN expansion_assumptions ea ON ca.account_id = ea.account_id;
```

### 3.3 Validation

```sql
-- Forecast accuracy: 12-month-ago forecast vs today's actual
WITH forecast_a_year_ago AS (
    SELECT account_id, expected_arr_12mo
    FROM ARR_FORECAST_RENEWAL_RISK_ADJUSTED
    WHERE as_of_date = DATEADD(year, -1, CURRENT_DATE)
),
actual_now AS (
    SELECT account_id, SUM(arr_usd_current) AS actual_arr
    FROM FINANCE_LINE_ANALYTICS
    WHERE as_was_date = (SELECT MAX(as_was_date) FROM FINANCE_LINE_ANALYTICS)
      AND is_arr_eligible = TRUE
    GROUP BY 1
)
SELECT
    SUM(fya.expected_arr_12mo) AS forecasted_total,
    SUM(an.actual_arr) AS actual_total,
    SUM(an.actual_arr) - SUM(fya.expected_arr_12mo) AS variance,
    ROUND((SUM(an.actual_arr) - SUM(fya.expected_arr_12mo)) / NULLIF(SUM(fya.expected_arr_12mo), 0), 4) AS variance_pct
FROM forecast_a_year_ago fya
LEFT JOIN actual_now an ON fya.account_id = an.account_id;
```

Target: variance < 5% (excellent), < 10% (acceptable), > 10% (forecast model needs retraining).

---

## §4. Pipeline-coverage-adjusted ACV

For close-quarter bookings forecast:

```sql
-- For each opp, expected ACV = amount × stage_weight × additional_risk_factors
SELECT
    o.opportunity_id,
    o.account_id,
    o.close_date,
    o.fiscal_quarter_close,
    o.amount_usd_current,
    o.stage,
    sw.stage_weight,
    o.ae_forecast_category,  -- 'COMMIT', 'BEST_CASE', 'PIPELINE'
    afw.ae_forecast_weight,  -- per-stage adjusted weight from FP&A
    -- Expected ACV
    o.amount_usd_current * sw.stage_weight * afw.ae_forecast_weight AS expected_acv
FROM SALES_PROD.MANAGED.WD_OPPORTUNITY_SCD2 o
JOIN REF_STAGE_WEIGHTS sw ON o.stage = sw.stage
LEFT JOIN REF_AE_FORECAST_WEIGHTS afw ON o.ae_forecast_category = afw.category
WHERE o.is_current = TRUE
  AND o.fiscal_quarter_close = (SELECT current_fiscal_quarter FROM ref_fiscal_calendar)
  AND o.stage NOT IN ('Closed/Won', 'Closed/Lost');
```

---

## §5. Forecast accuracy tracking (the meta-metric)

For every period (monthly / quarterly), snapshot the forecast at period start, then compare to actual at period end:

```sql
-- FORECAST_SNAPSHOT (incremental)
{{ config(
    materialized='incremental',
    unique_key=['snapshot_date', 'fiscal_quarter_forecasted', 'metric_name'],
    incremental_strategy='merge'
) }}

SELECT
    CURRENT_DATE AS snapshot_date,
    'FY26Q2' AS fiscal_quarter_forecasted,
    'TOTAL_ACV' AS metric_name,
    SUM(expected_acv) AS forecasted_value,
    'PIPELINE_ADJUSTED' AS forecast_method
FROM ACV_FORECAST_PIPELINE_ADJUSTED
WHERE fiscal_quarter_close = 'FY26Q2';

-- At period close, compute actual
INSERT INTO FORECAST_ACTUAL
SELECT
    'FY26Q2' AS fiscal_quarter,
    'TOTAL_ACV' AS metric_name,
    SUM(acv_usd_current) AS actual_value
FROM BT_ACV_SKU
WHERE fiscal_quarter_closed = 'FY26Q2';

-- FORECAST_ACCURACY_DASH joins snapshots vs actuals
SELECT
    fs.snapshot_date,
    fs.fiscal_quarter_forecasted,
    fs.metric_name,
    fs.forecasted_value,
    fa.actual_value,
    fa.actual_value - fs.forecasted_value AS variance,
    (fa.actual_value - fs.forecasted_value) / NULLIF(fs.forecasted_value, 0) AS variance_pct,
    DATEDIFF(day, fs.snapshot_date, 
        (SELECT fiscal_quarter_end_date FROM ref_fiscal_calendar WHERE fiscal_quarter = fs.fiscal_quarter_forecasted)
    ) AS days_to_close
FROM FORECAST_SNAPSHOT fs
LEFT JOIN FORECAST_ACTUAL fa 
  ON fs.fiscal_quarter_forecasted = fa.fiscal_quarter 
  AND fs.metric_name = fa.metric_name;
```

Used for forecast model retraining + accountability tracking.

---

## §6. Adaptive Planning integration

Adaptive Planning is the FP&A planning system. Workday-owned (acquired 2018).

### 6.1 What Adaptive holds

- Annual Operating Plan (AOP) at multiple grain (region, segment, product)
- Quarterly re-forecasts
- Headcount + cost plans
- Revenue plan (driven from ARR projections)

### 6.2 Sync architecture

```
Adaptive Planning (FP&A authoring)
   │
   │ Daily Fivetran sync
   ▼
BASE_PROD.ADAPTIVE_PLANNING.* (raw)
   │
   ▼
[eda-dbt-base]
   │
   ▼
FINANCE_PROD.MANAGED.ADAPTIVE_PLAN
   ├── Plan version (e.g., 'AOP_FY26_v1', 'AOP_FY26_v2')
   ├── Plan period (e.g., 'FY26Q1', 'FY26Q2')
   ├── Plan dimension (region / segment / product)
   ├── Plan amount (ARR / ACV / etc.)
```

### 6.3 Plan vs Actual reporting

```sql
-- AOP_VS_ACTUAL_DASH
SELECT
    plan.plan_period AS fiscal_quarter,
    plan.plan_dimension AS segment,
    plan.plan_metric_name AS metric_name,
    plan.plan_amount AS aop_amount,
    act.actual_amount,
    act.actual_amount - plan.plan_amount AS variance,
    (act.actual_amount - plan.plan_amount) / NULLIF(plan.plan_amount, 0) AS variance_pct
FROM FINANCE_PROD.MANAGED.ADAPTIVE_PLAN plan
LEFT JOIN (
    SELECT fiscal_quarter, segment, 'ARR' AS metric_name, SUM(end_arr) AS actual_amount
    FROM ARR_REGION_SEGMENT_CATEGORIES
    GROUP BY 1, 2
    UNION ALL
    SELECT fiscal_quarter_closed, NULL, 'BOOKINGS_ACV', SUM(acv_usd_current)
    FROM BT_ACV_SKU
    GROUP BY 1, 2
) act 
  ON plan.plan_period = act.fiscal_quarter 
  AND COALESCE(plan.plan_dimension, '') = COALESCE(act.segment, '')
  AND plan.plan_metric_name = act.metric_name
WHERE plan.plan_version = 'AOP_FY26_v2';
```

---

## §7. Clari integration

Clari is the sales forecasting tool. Aggregates rep forecasts → manager forecasts → executive forecasts.

### 7.1 What Clari holds

- Per-rep forecast per quarter (commit / best-case / pipeline)
- Manager-rolled-up forecasts
- Forecast history (changes over the quarter)

### 7.2 Sync architecture

```
Clari (sales forecast)
   │
   │ Daily Fivetran sync
   ▼
BASE_PROD.CLARI.* (raw)
   │
   ▼
SALES_PROD.MANAGED.CLARI_FORECAST_SCD2
   ├── Forecast snapshot date
   ├── Rep / manager / executive level
   ├── Commit / best-case / pipeline amounts
```

### 7.3 Forecast vs actual reconciliation

```sql
SELECT
    cf.snapshot_date,
    cf.fiscal_quarter,
    cf.forecast_level,  -- AE / RSD / RVP / etc.
    cf.commit_amount,
    cf.best_case_amount,
    cf.pipeline_amount,
    act.actual_amount
FROM SALES_PROD.MANAGED.CLARI_FORECAST_SCD2 cf
LEFT JOIN (
    SELECT fiscal_quarter_closed, SUM(acv_usd_current) AS actual_amount
    FROM BT_ACV_SKU
    GROUP BY 1
) act ON cf.fiscal_quarter = act.fiscal_quarter_closed
WHERE cf.is_current = TRUE
ORDER BY 1 DESC, 2;
```

---

## §8. The forecast snapshot pattern (critical for accuracy tracking)

Forecasts ARE inherently time-varying — a forecast made at Day 1 differs from Day 30 forecast.

To enable accuracy tracking, snapshot the forecast EVERY day:

```sql
-- Each day, snapshot the current forecast state
INSERT INTO FORECAST_SNAPSHOT
SELECT
    CURRENT_DATE AS snapshot_date,
    fiscal_quarter,
    forecast_level,
    commit_amount,
    best_case_amount,
    pipeline_amount,
    CURRENT_TIMESTAMP AS snapshotted_at
FROM CLARI_FORECAST_SCD2
WHERE is_current = TRUE;
```

Then trends:
- "How did the forecast evolve through the quarter?"
- "Did the forecast converge to actual?"
- "Which forecast level was most accurate?"

---

## §9. The "what-if" / scenario modeling pattern

For executive analysis: "What if we lose customer X?"

Modeled as parameterized views with input scenarios:

```sql
CREATE OR REPLACE FUNCTION FINANCE_PROD.ANALYTICS.WHAT_IF_CHURN(
    accounts_to_remove ARRAY,
    additional_churn_pct NUMBER
) RETURNS TABLE (
    metric_name VARCHAR,
    baseline_value NUMBER,
    scenario_value NUMBER,
    delta NUMBER
)
AS $$
    WITH baseline AS (
        SELECT SUM(arr_usd_current) AS baseline_arr
        FROM FINANCE_LINE_ANALYTICS
        WHERE as_was_date = (SELECT MAX(as_was_date) FROM FINANCE_LINE_ANALYTICS)
          AND is_arr_eligible = TRUE
    ),
    scenario AS (
        SELECT SUM(arr_usd_current) * (1 - additional_churn_pct) AS scenario_arr
        FROM FINANCE_LINE_ANALYTICS
        WHERE as_was_date = (SELECT MAX(as_was_date) FROM FINANCE_LINE_ANALYTICS)
          AND is_arr_eligible = TRUE
          AND NOT ARRAY_CONTAINS(account_id::VARIANT, accounts_to_remove)
    )
    SELECT 'TOTAL_ARR', baseline_arr, scenario_arr, scenario_arr - baseline_arr
    FROM baseline, scenario
$$;
```

Usage:
```sql
SELECT * FROM TABLE(WHAT_IF_CHURN(ARRAY_CONSTRUCT('ACC_001', 'ACC_002'), 0.05));
```

---

## §10. Cross-references

- `metric-portfolio-architecture.md` — base layer
- `sox-and-audit-architecture.md` — SOX for forecast metrics
- `enterprise-data-architect/domain-finance-billing.md` — Adaptive Planning context
- `enterprise-data-architect/domain-sales-gtm.md` — Clari + forecast levels
- `finance-functional-analytics/metric-recipes.md` — forecast queries
