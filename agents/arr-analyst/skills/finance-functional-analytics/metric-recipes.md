# Metric Recipes — Canonical SQL for Every Subscription Metric

Copy-paste-ready SQL for every metric. Each comes with grain, currency
variant, source-of-truth, expected output shape, and anti-pattern callouts.

If you're answering "what's our X right now?", find the recipe here first
before writing your own.

---

## §1. ARR — Total Annual Recurring Revenue (current)

**Use**: "What is total ARR right now?"
**Grain**: Single scalar
**Currency**: USD_CURRENT (live trending) or USD_HIST (period comparison)
**Source**: `FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS`

```sql
-- Total ARR (USD_CURRENT, latest snapshot, ARR-eligible only)
SELECT SUM(arr_usd_current) AS total_arr
FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS
WHERE as_was_date = (SELECT MAX(as_was_date) FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS)
  AND is_arr_eligible = TRUE;
```

**Anti-patterns**:
- ❌ Forgetting `is_arr_eligible` → includes pilots / one-time fees
- ❌ Not filtering `as_was_date` → multiplies by # snapshots
- ❌ Using `USD_CURRENT` for prior-period comparison → FX distorts trend

---

## §2. ARR by product

```sql
SELECT 
    product_code_l3,
    SUM(arr_usd_current) AS arr
FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS
WHERE as_was_date = (SELECT MAX(as_was_date) FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS)
  AND is_arr_eligible = TRUE
GROUP BY 1
ORDER BY 2 DESC;
```

Use `ARR_PRODUCT_CATEGORIES` for the category-decomposed version:
```sql
SELECT 
    product_code_l3,
    fiscal_quarter,
    SUM(CASE WHEN arr_category = 'BEGIN_ARR'   THEN arr_usd_hist END) AS begin_arr,
    SUM(CASE WHEN arr_category = 'NEW_LOGO'    THEN arr_usd_hist END) AS new_logo,
    SUM(CASE WHEN arr_category = 'EXPANSION'   THEN arr_usd_hist END) AS expansion,
    SUM(CASE WHEN arr_category = 'CONTRACTION' THEN ABS(arr_usd_hist) END) AS contraction,
    SUM(CASE WHEN arr_category = 'CHURN'       THEN ABS(arr_usd_hist) END) AS churn,
    SUM(CASE WHEN arr_category = 'SKU_CHANGE'  THEN arr_usd_hist END) AS sku_change,
    SUM(CASE WHEN arr_category = 'END_ARR'     THEN arr_usd_hist END) AS end_arr
FROM FINANCE_PROD.AGGREGATIONS.ARR_PRODUCT_CATEGORIES
WHERE fiscal_quarter = 'FY26Q1'
GROUP BY 1, 2;
```

---

## §3. ACV — Annual Contract Value (booking metric)

**Use**: "How much did sales book this quarter?"
**Grain**: Per quarter, aggregated
**Source**: `SALES_PROD.AGGREGATIONS.BT_ACV_SKU` (sales-side) or `FINANCE_LINE_ANALYTICS` (finance-side)

```sql
-- Sales bookings ACV for FY26 Q1
SELECT
    SUM(acv_usd_current) AS total_booking_acv,
    SUM(CASE WHEN deal_motion = 'NEW_NEW' THEN acv_usd_current END) AS new_new_acv,
    SUM(CASE WHEN deal_motion = 'NET_NEW' THEN acv_usd_current END) AS net_new_acv,
    SUM(CASE WHEN deal_motion = 'ADD_ON'  THEN acv_usd_current END) AS add_on_acv,
    SUM(CASE WHEN deal_motion = 'RENEWAL' THEN acv_usd_current END) AS renewal_acv
FROM SALES_PROD.AGGREGATIONS.BT_ACV_SKU
WHERE fiscal_quarter_closed = 'FY26Q1';
```

---

## §4. TCV — Total Contract Value (per agreement)

```sql
-- Top-10 largest contracts by TCV
SELECT
    a.agreement_id,
    a.agreement_name,
    a.account_name,
    a.term_start_date,
    a.term_end_date,
    SUM(line.tcv_usd_current) AS total_tcv
FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS line
JOIN FINANCE_PROD.MANAGED.WD_AGREEMENT_SCD2 a 
  ON line.agreement_id = a.agreement_id AND a.is_current = TRUE
WHERE line.as_was_date = (SELECT MAX(as_was_date) FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS)
  AND line.is_arr_eligible = TRUE
GROUP BY 1, 2, 3, 4, 5
ORDER BY 6 DESC
LIMIT 10;
```

---

## §5. NRR / NDR — Net Retention

```sql
-- NRR overall, FY26 Q1
WITH cohort AS (
    SELECT
        SUM(CASE WHEN arr_category = 'BEGIN_ARR'   THEN arr_usd_hist ELSE 0 END) AS begin_arr,
        SUM(CASE WHEN arr_category = 'EXPANSION'   THEN arr_usd_hist ELSE 0 END) AS expansion,
        SUM(CASE WHEN arr_category = 'CHURN'       THEN ABS(arr_usd_hist) ELSE 0 END) AS churn,
        SUM(CASE WHEN arr_category = 'CONTRACTION' THEN ABS(arr_usd_hist) ELSE 0 END) AS contraction
    FROM FINANCE_PROD.AGGREGATIONS.ARR_PRODUCT_CATEGORIES
    WHERE fiscal_quarter = 'FY26Q1'
)
SELECT ROUND((begin_arr + expansion - churn - contraction) / NULLIF(begin_arr, 0), 4) AS nrr
FROM cohort;
```

---

## §6. GRR — Gross Retention

```sql
WITH cohort AS (
    SELECT
        SUM(CASE WHEN arr_category = 'BEGIN_ARR'   THEN arr_usd_hist ELSE 0 END) AS begin_arr,
        SUM(CASE WHEN arr_category = 'CHURN'       THEN ABS(arr_usd_hist) ELSE 0 END) AS churn,
        SUM(CASE WHEN arr_category = 'CONTRACTION' THEN ABS(arr_usd_hist) ELSE 0 END) AS contraction
    FROM FINANCE_PROD.AGGREGATIONS.ARR_PRODUCT_CATEGORIES
    WHERE fiscal_quarter = 'FY26Q1'
)
SELECT ROUND((begin_arr - churn - contraction) / NULLIF(begin_arr, 0), 4) AS grr
FROM cohort;
```

---

## §7. The "ARR walk balances" reconciliation

```sql
-- Verify: BEGIN_ARR + Δs = END_ARR
WITH walk AS (
    SELECT
        SUM(CASE WHEN arr_category = 'BEGIN_ARR'   THEN arr_usd_hist ELSE 0 END) AS begin_arr,
        SUM(CASE WHEN arr_category = 'NEW_LOGO'    THEN arr_usd_hist ELSE 0 END) AS new_logo,
        SUM(CASE WHEN arr_category = 'EXPANSION'   THEN arr_usd_hist ELSE 0 END) AS expansion,
        SUM(CASE WHEN arr_category = 'CONTRACTION' THEN arr_usd_hist ELSE 0 END) AS contraction,
        SUM(CASE WHEN arr_category = 'CHURN'       THEN arr_usd_hist ELSE 0 END) AS churn,
        SUM(CASE WHEN arr_category = 'SKU_CHANGE'  THEN arr_usd_hist ELSE 0 END) AS sku_change,
        SUM(CASE WHEN arr_category = 'END_ARR'     THEN arr_usd_hist ELSE 0 END) AS end_arr
    FROM FINANCE_PROD.AGGREGATIONS.ARR_PRODUCT_CATEGORIES
    WHERE fiscal_quarter = 'FY26Q1'
)
SELECT
    begin_arr,
    new_logo,
    expansion,
    contraction,  -- already negative if stored as such
    churn,        -- already negative if stored as such
    sku_change,
    end_arr,
    (begin_arr + new_logo + expansion + contraction + churn + sku_change) AS computed_end,
    end_arr - (begin_arr + new_logo + expansion + contraction + churn + sku_change) AS variance
FROM walk;
-- Variance < $1 = OK. > $1 = bug.
```

---

## §8. Customer churn vs Product churn breakdown

```sql
-- Decompose CHURN into Customer vs Product churn
WITH churns AS (
    SELECT
        line.account_id,
        line.product_code_l3,
        line.agreement_line_item_id,
        line.arr_usd_hist AS churn_arr,
        CASE
            WHEN EXISTS (
                SELECT 1 FROM FINANCE_LINE_ANALYTICS active
                WHERE active.account_id = line.account_id
                  AND active.as_was_date = line.as_was_date
                  AND active.arr_usd_current > 0
                  AND active.is_arr_eligible = TRUE
            )
            THEN 'PRODUCT_CHURN'
            ELSE 'CUSTOMER_CHURN'
        END AS churn_type
    FROM FINANCE_LINE_ANALYTICS line
    WHERE line.as_was_date = '2026-04-30'
      AND line.arr_category = 'CHURN'
)
SELECT
    churn_type,
    COUNT(DISTINCT account_id) AS num_accounts,
    COUNT(*) AS num_lines,
    SUM(ABS(churn_arr)) AS total_churn_arr
FROM churns
GROUP BY 1;
```

---

## §9. Currency variant comparison

```sql
-- Show same metric in 3 variants to compare
SELECT
    SUM(arr_usd_current) AS arr_usd_current,
    SUM(arr_usd_hist)    AS arr_usd_hist,
    SUM(arr_usd_actual)  AS arr_usd_actual,  -- NOT in USD; sum of local currencies
    SUM(arr_usd_current) - SUM(arr_usd_hist) AS fx_impact_current_vs_hist
FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS
WHERE as_was_date = (SELECT MAX(as_was_date) FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS)
  AND is_arr_eligible = TRUE;
```

---

## §10. Pipeline coverage

```sql
-- Pipeline coverage = open pipeline / remaining quota for the quarter
WITH open_pipeline AS (
    SELECT SUM(amount_usd_current) AS pipeline_usd
    FROM SALES_PROD.MANAGED.WD_OPPORTUNITY_SCD2
    WHERE is_current = TRUE
      AND stage NOT IN ('Closed/Won', 'Closed/Lost', 'Closed/No Decision')
      AND fiscal_quarter_close_date = 'FY26Q2'
),
quota AS (
    SELECT SUM(quota_acv_usd) AS quota_usd
    FROM SALES_PROD.MANAGED.WD_QUOTA
    WHERE fiscal_quarter = 'FY26Q2'
),
closed_won AS (
    SELECT SUM(acv_usd_current) AS closed_acv
    FROM SALES_PROD.AGGREGATIONS.BT_ACV_SKU
    WHERE fiscal_quarter_closed = 'FY26Q2'
)
SELECT
    pipeline_usd,
    quota_usd - closed_acv AS remaining_quota,
    ROUND(pipeline_usd / NULLIF(quota_usd - closed_acv, 0), 2) AS coverage_ratio
FROM open_pipeline, quota, closed_won;
```

---

## §11. Win rate

```sql
-- Win rate for closed-out opps in FY26 Q1
SELECT
    fiscal_quarter,
    SUM(CASE WHEN stage = 'Closed/Won' THEN 1 ELSE 0 END) AS won_count,
    SUM(CASE WHEN stage IN ('Closed/Won', 'Closed/Lost') THEN 1 ELSE 0 END) AS decided_count,
    ROUND(SUM(CASE WHEN stage = 'Closed/Won' THEN 1 ELSE 0 END) * 1.0 
        / NULLIF(SUM(CASE WHEN stage IN ('Closed/Won', 'Closed/Lost') THEN 1 ELSE 0 END), 0), 4) AS win_rate
FROM SALES_PROD.MANAGED.WD_OPPORTUNITY_SCD2
WHERE is_current = TRUE
  AND fiscal_quarter_closed = 'FY26Q1'
GROUP BY 1;
```

---

## §12. Deal motion mix

```sql
-- For closed-won opps this quarter, % by deal motion
SELECT
    deal_motion,
    COUNT(*) AS opp_count,
    SUM(acv_usd_current) AS total_acv,
    ROUND(SUM(acv_usd_current) / SUM(SUM(acv_usd_current)) OVER (), 4) AS pct_of_total
FROM SALES_PROD.AGGREGATIONS.BT_ACV_SKU
WHERE fiscal_quarter_closed = 'FY26Q1'
GROUP BY 1
ORDER BY 3 DESC;
```

---

## §13. Cohort retention curve

```sql
-- FY24 new-logo cohort, retention at each quarter since
WITH cohort AS (
    SELECT DISTINCT account_id
    FROM FINANCE_PROD.AGGREGATIONS.ARR_ACCOUNT_CATEGORIES
    WHERE fiscal_year = 'FY24'
      AND arr_category = 'NEW_LOGO'
),
baseline AS (
    SELECT SUM(arr_usd_hist) AS baseline_arr
    FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS a
    JOIN cohort c ON a.account_id = c.account_id
    WHERE a.as_was_date = '2024-02-06'  -- FY24 Q4 close approximation
      AND a.is_arr_eligible = TRUE
),
over_time AS (
    SELECT
        a.as_was_date,
        SUM(a.arr_usd_hist) AS cohort_arr
    FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS a
    JOIN cohort c ON a.account_id = c.account_id
    WHERE a.as_was_date IN (
        '2024-05-06', '2024-08-06', '2024-11-06',
        '2025-02-06', '2025-05-06', '2025-08-06', '2025-11-06',
        '2026-02-06'
    )
      AND a.is_arr_eligible = TRUE
    GROUP BY 1
)
SELECT
    as_was_date,
    cohort_arr,
    (SELECT baseline_arr FROM baseline) AS baseline_arr,
    ROUND(cohort_arr / NULLIF((SELECT baseline_arr FROM baseline), 0), 4) AS cohort_nrr
FROM over_time
ORDER BY 1;
```

---

## §14. ARR growth decomposition (Y/Y)

```sql
-- Y/Y growth decomposition for FY25 → FY26
WITH walk AS (
    SELECT
        fiscal_year,
        SUM(CASE WHEN arr_category = 'BEGIN_ARR'   THEN arr_usd_hist ELSE 0 END) AS begin_arr,
        SUM(CASE WHEN arr_category = 'NEW_LOGO'    THEN arr_usd_hist ELSE 0 END) AS new_logo,
        SUM(CASE WHEN arr_category = 'EXPANSION'   THEN arr_usd_hist ELSE 0 END) AS expansion,
        SUM(CASE WHEN arr_category = 'CONTRACTION' THEN arr_usd_hist ELSE 0 END) AS contraction,
        SUM(CASE WHEN arr_category = 'CHURN'       THEN arr_usd_hist ELSE 0 END) AS churn,
        SUM(CASE WHEN arr_category = 'SKU_CHANGE'  THEN arr_usd_hist ELSE 0 END) AS sku_change,
        SUM(CASE WHEN arr_category = 'END_ARR'     THEN arr_usd_hist ELSE 0 END) AS end_arr
    FROM FINANCE_PROD.AGGREGATIONS.ARR_PRODUCT_CATEGORIES
    WHERE fiscal_year IN ('FY25', 'FY26')
    GROUP BY 1
)
SELECT
    fiscal_year,
    begin_arr,
    new_logo,
    expansion,
    contraction,
    churn,
    sku_change,
    end_arr,
    end_arr - begin_arr AS yoy_growth_arr,
    -- % decomposition
    ROUND(new_logo    / NULLIF(end_arr - begin_arr, 0), 4) AS pct_growth_from_new_logo,
    ROUND(expansion   / NULLIF(end_arr - begin_arr, 0), 4) AS pct_growth_from_expansion,
    ROUND(contraction / NULLIF(end_arr - begin_arr, 0), 4) AS pct_drag_from_contraction,
    ROUND(churn       / NULLIF(end_arr - begin_arr, 0), 4) AS pct_drag_from_churn
FROM walk
ORDER BY 1;
```

---

## §15. Renewal cohort analysis

```sql
-- Of the $X up for renewal in FY26 Q1, how much was retained?
WITH renewal_cohort AS (
    SELECT
        agreement_id,
        agreement_line_item_id,
        arr_usd_hist AS at_risk_arr
    FROM FINANCE_PROD.MANAGED.WD_AGREEMENT_LINE_SCD2
    WHERE is_current = TRUE
      AND term_end_date BETWEEN '2025-02-01' AND '2025-04-30'  -- FY26 Q1 renewal cohort
)
SELECT
    SUM(rc.at_risk_arr) AS up_for_renewal_arr,
    SUM(CASE WHEN ssr.new_agreement_id IS NOT NULL THEN rc.at_risk_arr ELSE 0 END) AS retained_arr,
    SUM(CASE WHEN ssr.new_agreement_id IS NULL THEN rc.at_risk_arr ELSE 0 END) AS churned_arr,
    ROUND(SUM(CASE WHEN ssr.new_agreement_id IS NOT NULL THEN rc.at_risk_arr END) 
        / NULLIF(SUM(rc.at_risk_arr), 0), 4) AS renewal_rate
FROM renewal_cohort rc
LEFT JOIN FINANCE_PROD.MANAGED.SSR_AGREEMENT_RELATIONSHIP ssr 
  ON rc.agreement_id = ssr.old_agreement_id;
```

---

## §16. Top accounts by ARR

```sql
SELECT
    a.account_id,
    a.account_name,
    a.industry,
    a.segment,
    SUM(line.arr_usd_current) AS account_arr
FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS line
JOIN SALES_PROD.MANAGED.WD_ACCOUNT_SCD2 a 
  ON line.account_id = a.account_id AND a.is_current = TRUE
WHERE line.as_was_date = (SELECT MAX(as_was_date) FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS)
  AND line.is_arr_eligible = TRUE
GROUP BY 1, 2, 3, 4
ORDER BY 5 DESC
LIMIT 20;
```

---

## §17. Net new ARR (NEW_LOGO minus CHURN)

```sql
-- "Net new ARR" = true new business growth
SELECT
    fiscal_quarter,
    SUM(CASE WHEN arr_category = 'NEW_LOGO' THEN arr_usd_hist ELSE 0 END) AS new_logo,
    SUM(CASE WHEN arr_category = 'CHURN'    THEN ABS(arr_usd_hist) ELSE 0 END) AS churn,
    SUM(CASE WHEN arr_category = 'NEW_LOGO' THEN arr_usd_hist ELSE 0 END) 
        - SUM(CASE WHEN arr_category = 'CHURN' THEN ABS(arr_usd_hist) ELSE 0 END) AS net_new_arr
FROM FINANCE_PROD.AGGREGATIONS.ARR_PRODUCT_CATEGORIES
WHERE fiscal_year = 'FY26'
GROUP BY 1
ORDER BY 1;
```

---

## §18. Logo Retention Rate

```sql
WITH logos AS (
    SELECT
        COUNT(DISTINCT CASE WHEN arr_category = 'BEGIN_ARR' AND arr_usd_hist > 0 THEN account_id END) AS begin_logos,
        COUNT(DISTINCT CASE WHEN arr_category = 'END_ARR'   AND arr_usd_hist > 0 
                            AND account_id IN (
                                SELECT account_id FROM FINANCE_PROD.AGGREGATIONS.ARR_ACCOUNT_CATEGORIES
                                WHERE fiscal_quarter = 'FY26Q1' AND arr_category = 'BEGIN_ARR' AND arr_usd_hist > 0
                            )
                       THEN account_id END) AS retained_logos
    FROM FINANCE_PROD.AGGREGATIONS.ARR_ACCOUNT_CATEGORIES
    WHERE fiscal_quarter = 'FY26Q1'
)
SELECT
    begin_logos,
    retained_logos,
    ROUND(retained_logos * 1.0 / NULLIF(begin_logos, 0), 4) AS lrr
FROM logos;
```

---

## §19. Forecast accuracy

```sql
-- Compare ae_forecast (early-quarter) to actual closed-won by end of quarter
SELECT
    o.fiscal_quarter_closed,
    SUM(CASE WHEN o.ae_forecast_category_at_start IN ('COMMIT', 'BEST_CASE') THEN o.amount_usd_current END) AS forecasted_acv,
    SUM(CASE WHEN o.stage = 'Closed/Won' THEN o.acv_usd_current END) AS actual_acv,
    ROUND(SUM(CASE WHEN o.stage = 'Closed/Won' THEN o.acv_usd_current END) 
        / NULLIF(SUM(CASE WHEN o.ae_forecast_category_at_start IN ('COMMIT', 'BEST_CASE') THEN o.amount_usd_current END), 0), 4) AS forecast_accuracy
FROM SALES_PROD.MANAGED.WD_OPPORTUNITY_SCD2 o
WHERE o.is_current = TRUE
  AND o.fiscal_quarter_closed = 'FY26Q1'
GROUP BY 1;
```

---

## §20. Bookings → ARR conversion

```sql
-- For a given quarter, compare booked ACV (sales-side) to ARR landed (finance-side)
WITH bookings AS (
    SELECT SUM(acv_usd_current) AS booked_acv
    FROM SALES_PROD.AGGREGATIONS.BT_ACV_SKU
    WHERE fiscal_quarter_closed = 'FY26Q1'
),
arr_landed AS (
    SELECT SUM(arr_usd_current) AS landed_arr
    FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS line
    JOIN FINANCE_PROD.MANAGED.WD_AGREEMENT_SCD2 a 
      ON line.agreement_id = a.agreement_id AND a.is_current = TRUE
    WHERE line.as_was_date = '2025-05-06'
      AND a.activation_date BETWEEN '2025-02-01' AND '2025-04-30'
      AND line.is_arr_eligible = TRUE
)
SELECT
    booked_acv,
    landed_arr,
    booked_acv - landed_arr AS variance,
    ROUND(landed_arr / NULLIF(booked_acv, 0), 4) AS arr_conversion_rate
FROM bookings, arr_landed;
-- Variance > 5% = data quality investigation needed
```

---

## §21. Period-over-period ARR change

```sql
-- Q/Q ARR change with category attribution
WITH q AS (
    SELECT
        fiscal_quarter,
        SUM(arr_usd_hist) AS total_arr
    FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS
    WHERE as_was_date IN ('2025-05-06', '2025-08-06', '2025-11-06', '2026-02-06')
      AND is_arr_eligible = TRUE
    GROUP BY 1
)
SELECT
    fiscal_quarter,
    total_arr,
    LAG(total_arr) OVER (ORDER BY fiscal_quarter) AS prior_arr,
    total_arr - LAG(total_arr) OVER (ORDER BY fiscal_quarter) AS qoq_delta,
    ROUND((total_arr - LAG(total_arr) OVER (ORDER BY fiscal_quarter)) 
        / NULLIF(LAG(total_arr) OVER (ORDER BY fiscal_quarter), 0), 4) AS qoq_growth_pct
FROM q
ORDER BY 1;
```

---

## §22. Implied lifetime value

```sql
-- Implied LTV = ARR × Avg contract length × Gross margin / (1 - retention rate)
-- Simplified version: ARR × (1 / churn rate)
WITH metrics AS (
    SELECT
        SUM(arr_usd_current) / COUNT(DISTINCT account_id) AS avg_arr_per_customer,
        0.95 AS gross_retention_estimate  -- replace with actual GRR
    FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS
    WHERE as_was_date = (SELECT MAX(as_was_date) FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS)
      AND is_arr_eligible = TRUE
)
SELECT
    avg_arr_per_customer,
    avg_arr_per_customer * (1 / (1 - gross_retention_estimate)) AS implied_ltv
FROM metrics;
```

---

## §23. Customer concentration (top-N customers as % of ARR)

```sql
-- Top-10 customer concentration risk
WITH ranked AS (
    SELECT
        account_id,
        SUM(arr_usd_current) AS account_arr,
        ROW_NUMBER() OVER (ORDER BY SUM(arr_usd_current) DESC) AS rank
    FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS
    WHERE as_was_date = (SELECT MAX(as_was_date) FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS)
      AND is_arr_eligible = TRUE
    GROUP BY 1
),
totals AS (
    SELECT SUM(account_arr) AS total_arr FROM ranked
)
SELECT
    SUM(CASE WHEN rank <= 10 THEN account_arr ELSE 0 END) AS top_10_arr,
    SUM(CASE WHEN rank <= 100 THEN account_arr ELSE 0 END) AS top_100_arr,
    (SELECT total_arr FROM totals) AS total_arr,
    ROUND(SUM(CASE WHEN rank <= 10  THEN account_arr ELSE 0 END) / (SELECT total_arr FROM totals), 4) AS top_10_pct,
    ROUND(SUM(CASE WHEN rank <= 100 THEN account_arr ELSE 0 END) / (SELECT total_arr FROM totals), 4) AS top_100_pct
FROM ranked;
```

---

## §24. SSR resolution validation

```sql
-- Sanity check: every "terminated" line within last quarter has an SSR resolution OR is a true churn
WITH terminated_lines AS (
    SELECT agreement_line_item_id, agreement_id, account_id, prior_arr
    FROM FINANCE_LINE_ANALYTICS
    WHERE as_was_date = '2026-04-30'
      AND arr_category = 'CHURN'
)
SELECT
    COUNT(*) AS total_churn_lines,
    SUM(CASE WHEN ssr.new_agreement_id IS NOT NULL THEN 1 ELSE 0 END) AS resolved_via_ssr,
    SUM(CASE WHEN ssr.new_agreement_id IS NULL THEN 1 ELSE 0 END) AS true_churn,
    ROUND(SUM(CASE WHEN ssr.new_agreement_id IS NULL THEN 1 ELSE 0 END) * 1.0 
        / NULLIF(COUNT(*), 0), 4) AS true_churn_pct
FROM terminated_lines tl
LEFT JOIN SSR_AGREEMENT_RELATIONSHIP ssr 
  ON tl.agreement_id = ssr.old_agreement_id;
-- If true_churn_pct seems too high, investigate SSR resolution gaps
```

---

## §25. The "explain this number" template

When you need to walk someone through where a number comes from:

```sql
-- Template: Reproduce the dashboard number with full lineage trace
WITH dashboard_view AS (
    -- What does the dashboard show?
    SELECT *
    FROM FINANCE_PROD.DATA_PRODUCTS.ARR_PRODUCT_NET_DOLLAR_RETENTION_DASH_V2
    WHERE fiscal_quarter = 'FY26Q1'
      AND product_code_l3 = 'Core HCM'
),
aggregation_layer AS (
    -- Where does that number come from in AGGREGATIONS?
    SELECT *
    FROM FINANCE_PROD.AGGREGATIONS.ARR_PRODUCT_CATEGORIES
    WHERE fiscal_quarter = 'FY26Q1'
      AND product_code_l3 = 'Core HCM'
),
managed_lines AS (
    -- What lines roll up into that aggregation?
    SELECT *
    FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS
    WHERE as_was_date BETWEEN '2025-02-01' AND '2025-04-30'
      AND product_code_l3 = 'Core HCM'
      AND is_arr_eligible = TRUE
)
SELECT 'Dashboard:'      AS layer, * FROM dashboard_view
UNION ALL
SELECT 'Aggregation:'    AS layer, * FROM aggregation_layer
UNION ALL
SELECT 'Managed (sample):', * FROM managed_lines LIMIT 100;
-- Step through each layer to find divergence
```

---

## §26. Common ARR by-X queries

| Question | View |
|---|---|
| ARR by product | `ARR_PRODUCT_CATEGORIES` |
| ARR by SKU | `ARR_SKU_CATEGORIES` |
| ARR by account | `ARR_ACCOUNT_CATEGORIES` |
| ARR by region/segment | `ARR_REGION_SEGMENT_CATEGORIES` |
| ARR by industry | `ARR_INDUSTRY_CATEGORIES` |
| ARR by partner | `ARR_STRATEGIC_PARTNER_CATEGORIES` |

Pattern (apply to any):
```sql
SELECT
    <slice_column>,
    fiscal_quarter,
    SUM(CASE WHEN arr_category = 'BEGIN_ARR'   THEN arr_usd_hist END) AS begin_arr,
    SUM(CASE WHEN arr_category = 'END_ARR'     THEN arr_usd_hist END) AS end_arr,
    SUM(CASE WHEN arr_category = 'NEW_LOGO'    THEN arr_usd_hist END) AS new_logo,
    SUM(CASE WHEN arr_category = 'EXPANSION'   THEN arr_usd_hist END) AS expansion,
    SUM(CASE WHEN arr_category = 'CHURN'       THEN ABS(arr_usd_hist) END) AS churn,
    SUM(CASE WHEN arr_category = 'CONTRACTION' THEN ABS(arr_usd_hist) END) AS contraction
FROM FINANCE_PROD.AGGREGATIONS.<view_name>
WHERE fiscal_quarter = 'FY26Q1'
GROUP BY 1, 2;
```

---

## §27. Cross-references

- `categorization-framework.md` — for any "what category is this?" question
- `retention-deep-dive.md` — for retention metric depth
- `churn-anatomy.md` — for churn classification
- `enterprise-data-architect/finance-metrics-canonical.md` — for canonical definitions
