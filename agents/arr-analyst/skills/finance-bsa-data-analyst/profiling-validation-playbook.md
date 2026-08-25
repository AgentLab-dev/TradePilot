# Profiling & Validation Playbook

Standard patterns for profiling new datasets, validating canonical metrics,
and running reconciliation queries.

This is your day-to-day toolkit.

---

## §1. Dataset profiling — the 7-step process

When you encounter a new table:

### Step 1: Row count + identity

```sql
SELECT 
    COUNT(*) AS total_rows,
    COUNT(DISTINCT primary_key_col) AS distinct_keys,
    COUNT(*) - COUNT(DISTINCT primary_key_col) AS duplicate_rows
FROM <table>;
```

Red flags:
- `duplicate_rows > 0` → table not unique on stated PK
- `total_rows = 0` → empty table or wrong filter
- `total_rows < 100` → too small for typical aggregate analysis

### Step 2: Column inventory

```sql
SELECT 
    column_name,
    data_type,
    is_nullable,
    comment
FROM INFORMATION_SCHEMA.COLUMNS
WHERE table_catalog = '<DB>'
  AND table_schema = '<SCHEMA>'
  AND table_name = '<TABLE>'
ORDER BY ordinal_position;
```

### Step 3: Per-column null distribution

```sql
SELECT 
    'col1' AS column_name, 
    COUNT(*) AS total,
    SUM(CASE WHEN col1 IS NULL THEN 1 ELSE 0 END) AS null_count,
    SUM(CASE WHEN col1 IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS null_pct,
    COUNT(DISTINCT col1) AS distinct_count
FROM <table>
UNION ALL
-- repeat for each column
SELECT 'col2', COUNT(*), SUM(CASE WHEN col2 IS NULL THEN 1 ELSE 0 END), ...
```

Red flags:
- `null_pct > 50%` → column may not be reliably populated
- `null_pct > 95%` → column is essentially unused
- `distinct_count = 1` → column has no variation, may be dropped

### Step 4: Categorical distribution (top-N + tail)

```sql
SELECT category_col, COUNT(*), COUNT(DISTINCT primary_key)
FROM <table>
GROUP BY 1
ORDER BY 2 DESC;
```

Or for top + tail visualization:
```sql
SELECT 
    category_col,
    COUNT(*) AS row_count,
    RANK() OVER (ORDER BY COUNT(*) DESC) AS rank
FROM <table>
GROUP BY 1
ORDER BY 2 DESC
LIMIT 20;
```

Red flags:
- Unexpected categories (e.g., "test_001", "DELETE_ME")
- Top-1 category > 50% (skew)
- Tail has thousands of low-count categories (free-text issue)

### Step 5: Numeric distribution

```sql
SELECT 
    MIN(numeric_col) AS min_val,
    MAX(numeric_col) AS max_val,
    AVG(numeric_col) AS avg,
    MEDIAN(numeric_col) AS median,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY numeric_col) AS p95,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY numeric_col) AS p99,
    STDDEV(numeric_col) AS stddev,
    SUM(numeric_col) AS sum
FROM <table>
WHERE numeric_col IS NOT NULL;
```

Red flags:
- `MIN < 0` for amount columns (negative ARR?)
- `MAX` is an outlier (one row dominates the sum)
- `p99 / median > 100` (long tail or bad data)

### Step 6: Time distribution

```sql
SELECT 
    MIN(date_col) AS earliest,
    MAX(date_col) AS latest,
    DATE_PART('year', MIN(date_col)) AS min_year,
    DATE_PART('year', MAX(date_col)) AS max_year,
    COUNT(DISTINCT DATE_TRUNC('month', date_col)) AS distinct_months
FROM <table>;

-- Distribution by year/month
SELECT 
    DATE_TRUNC('month', date_col) AS month,
    COUNT(*) AS row_count
FROM <table>
GROUP BY 1
ORDER BY 1;
```

Red flags:
- Future dates (data entry error or forward-dated contracts)
- Gaps (months with zero rows)
- Old dates beyond expected history
- Single-month spike (potential reload)

### Step 7: Sample rows

```sql
SELECT *
FROM <table>
ORDER BY date_col DESC NULLS LAST
LIMIT 5;
```

Eyeball check — do the values look sane?

---

## §2. The "is this canonical?" check

Before using a dataset for analysis, confirm it's a canonical source (not a raw table or stale snapshot):

```sql
-- Check Atlan / catalog metadata
SELECT 
    table_name,
    comment AS description,
    created AS created_date,
    last_altered
FROM INFORMATION_SCHEMA.TABLES
WHERE table_catalog = '<DB>'
  AND table_schema = '<SCHEMA>'
  AND table_name = '<TABLE>';
```

Indicators it's canonical:
- ✓ In `MANAGED` / `AGGREGATIONS` / `DATA_PRODUCTS` schemas
- ✓ Recent `last_altered` (refreshed in last 24-48 hrs)
- ✓ Has a Confluence / Atlan documentation entry

Indicators it might NOT be canonical:
- ✗ In `RAW_PROD` / `BASE_PROD` directly (raw source)
- ✗ In a `_TEMP` / `_BACKUP` / `_OLD` schema
- ✗ In someone's personal sandbox schema
- ✗ Not refreshed in weeks

When in doubt: ask the table owner (Atlan owner field).

---

## §3. The ARR walk validation (every quarter close)

```sql
-- ARR walk balances
WITH walk AS (
    SELECT
        fiscal_quarter,
        SUM(CASE WHEN arr_category = 'BEGIN_ARR'   THEN arr_usd_hist ELSE 0 END) AS begin_arr,
        SUM(CASE WHEN arr_category = 'NEW_LOGO'    THEN arr_usd_hist ELSE 0 END) AS new_logo,
        SUM(CASE WHEN arr_category = 'EXPANSION'   THEN arr_usd_hist ELSE 0 END) AS expansion,
        SUM(CASE WHEN arr_category = 'CONTRACTION' THEN arr_usd_hist ELSE 0 END) AS contraction,
        SUM(CASE WHEN arr_category = 'CHURN'       THEN arr_usd_hist ELSE 0 END) AS churn,
        SUM(CASE WHEN arr_category = 'SKU_CHANGE'  THEN arr_usd_hist ELSE 0 END) AS sku_change,
        SUM(CASE WHEN arr_category = 'END_ARR'     THEN arr_usd_hist ELSE 0 END) AS end_arr
    FROM FINANCE_PROD.AGGREGATIONS.ARR_PRODUCT_CATEGORIES
    WHERE fiscal_year = 'FY26'
    GROUP BY 1
)
SELECT
    fiscal_quarter,
    begin_arr,
    new_logo, expansion, contraction, churn, sku_change,
    end_arr,
    (begin_arr + new_logo + expansion + contraction + churn + sku_change) AS computed_end,
    end_arr - (begin_arr + new_logo + expansion + contraction + churn + sku_change) AS variance
FROM walk
ORDER BY 1;
```

Acceptance: variance < $1 per quarter.

---

## §4. The cross-domain reconciliation (sales bookings → finance ARR)

Booking ACV (sales-side) should equate to NEW_LOGO + EXPANSION (finance-side):

```sql
WITH sales_bookings AS (
    SELECT 
        fiscal_quarter_closed AS fiscal_quarter,
        SUM(acv_usd_current) AS booked_acv_total
    FROM SALES_PROD.AGGREGATIONS.BT_ACV_SKU
    WHERE fiscal_quarter_closed = 'FY26Q1'
    GROUP BY 1
),
finance_arr_added AS (
    SELECT 
        fiscal_quarter,
        SUM(CASE WHEN arr_category IN ('NEW_LOGO', 'EXPANSION') THEN arr_usd_hist ELSE 0 END) AS arr_added
    FROM FINANCE_PROD.AGGREGATIONS.ARR_PRODUCT_CATEGORIES
    WHERE fiscal_quarter = 'FY26Q1'
    GROUP BY 1
)
SELECT 
    sb.fiscal_quarter,
    sb.booked_acv_total,
    far.arr_added,
    sb.booked_acv_total - far.arr_added AS variance,
    ROUND((sb.booked_acv_total - far.arr_added) / NULLIF(sb.booked_acv_total, 0), 4) AS variance_pct
FROM sales_bookings sb
JOIN finance_arr_added far ON sb.fiscal_quarter = far.fiscal_quarter;
```

Expected variance: < 5% (timing of activation, multi-year ramps, etc.)
Variance > 5%: investigate.

---

## §5. The currency-variant validation

```sql
-- USD_CURRENT vs USD_HIST: difference should be small + explained by FX
SELECT 
    SUM(arr_usd_current) AS total_usd_current,
    SUM(arr_usd_hist) AS total_usd_hist,
    SUM(arr_usd_current) - SUM(arr_usd_hist) AS fx_impact,
    ROUND((SUM(arr_usd_current) - SUM(arr_usd_hist)) / NULLIF(SUM(arr_usd_hist), 0), 4) AS fx_impact_pct
FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS
WHERE as_was_date = (SELECT MAX(as_was_date) FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS)
  AND is_arr_eligible = TRUE;
```

Expected: ±2% typical FX impact. > ±5% suggests FX move is material → flag in next exec update.

---

## §6. The SSR coverage validation

```sql
-- Every CHURN line should either be true churn OR SSR-resolved
WITH churn_lines AS (
    SELECT 
        agreement_line_item_id, 
        agreement_id, 
        account_id, 
        arr_usd_hist AS churn_amount
    FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS
    WHERE as_was_date = '2026-04-30'
      AND arr_category = 'CHURN'
)
SELECT
    COUNT(*) AS total_churn_lines,
    SUM(CASE WHEN ssr.new_agreement_id IS NOT NULL THEN 1 ELSE 0 END) AS ssr_resolved_count,
    SUM(CASE WHEN ssr.new_agreement_id IS NULL THEN 1 ELSE 0 END) AS true_churn_count,
    SUM(churn_amount) AS total_churn_arr,
    SUM(CASE WHEN ssr.new_agreement_id IS NULL THEN ABS(churn_amount) ELSE 0 END) AS true_churn_arr
FROM churn_lines cl
LEFT JOIN FINANCE_PROD.MANAGED.SSR_AGREEMENT_RELATIONSHIP ssr 
  ON cl.agreement_id = ssr.old_agreement_id;
```

Red flag: if `ssr_resolved_count` is unusually low → SSR data not refreshing.

---

## §7. The dimension-current vs as-was validation

```sql
-- Compare current account dimension vs as-was account dimension at past period
WITH current_dim AS (
    SELECT account_id, segment, industry 
    FROM SALES_PROD.MANAGED.WD_ACCOUNT_SCD2 
    WHERE is_current = TRUE
),
as_was_dim AS (
    SELECT 
        account_id, 
        segment AS as_was_segment, 
        industry AS as_was_industry
    FROM SALES_PROD.MANAGED.WD_ACCOUNT_SCD2
    WHERE dbt_valid_from <= '2025-02-06'
      AND COALESCE(dbt_valid_to, '9999-01-01') > '2025-02-06'
)
SELECT 
    COUNT(*) AS total_accounts,
    SUM(CASE WHEN c.segment != a.as_was_segment THEN 1 ELSE 0 END) AS segment_changed_count,
    SUM(CASE WHEN c.industry != a.as_was_industry THEN 1 ELSE 0 END) AS industry_changed_count
FROM current_dim c
JOIN as_was_dim a ON c.account_id = a.account_id;
```

Validates SCD2 is capturing changes.

---

## §8. The "snapshot freshness" check

```sql
-- Has FINANCE_LINE_ANALYTICS been refreshed recently?
SELECT 
    MAX(as_was_date) AS latest_snapshot,
    DATEDIFF(day, MAX(as_was_date), CURRENT_DATE) AS days_since_latest,
    COUNT(DISTINCT as_was_date) AS total_snapshots,
    MIN(as_was_date) AS earliest_snapshot
FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS;
```

Red flag: `days_since_latest > 14` → snapshot not refreshing (job stuck?).

---

## §9. The "metric reasonableness" range check

```sql
-- Are core metrics in sane ranges?
WITH metrics AS (
    SELECT
        SUM(arr_usd_current) AS total_arr,
        COUNT(DISTINCT account_id) AS account_count,
        COUNT(*) AS line_count,
        AVG(arr_usd_current) AS avg_arr_per_line
    FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS
    WHERE as_was_date = (SELECT MAX(as_was_date) FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS)
      AND is_arr_eligible = TRUE
)
SELECT *,
    CASE WHEN total_arr BETWEEN 5000000000 AND 12000000000 THEN 'OK' ELSE 'OUT_OF_RANGE' END AS total_arr_check,
    CASE WHEN account_count BETWEEN 8000 AND 15000 THEN 'OK' ELSE 'OUT_OF_RANGE' END AS account_check,
    CASE WHEN avg_arr_per_line BETWEEN 10000 AND 200000 THEN 'OK' ELSE 'OUT_OF_RANGE' END AS avg_check
FROM metrics;
```

Adjust ranges per current expected values. Trip wires for unusual states.

---

## §10. The "category coverage" check

```sql
-- All lines should be categorized; none uncategorized
SELECT 
    arr_category,
    COUNT(*) AS line_count,
    SUM(arr_usd_current) AS total_arr
FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS
WHERE as_was_date = (SELECT MAX(as_was_date) FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS)
GROUP BY 1
ORDER BY 2 DESC;
```

Expected categories: BEGIN_ARR, NEW_LOGO, EXPANSION, CONTRACTION, CHURN, SKU_CHANGE, END_ARR, FLAT, NULL.

Red flag: `NULL` or `UNKNOWN` category > 0 lines.

---

## §11. The reconciliation patterns at a glance

| Reconciliation | Source A | Source B | Expected variance |
|---|---|---|---|
| ARR walk balances | BEGIN + Δs | END | < $1 |
| Sales bookings → Finance NEW_LOGO + EXPANSION | BT_ACV_SKU | ARR_*_CATEGORIES | < 5% |
| USD_CURRENT vs USD_HIST | arr_usd_current | arr_usd_hist | ±5% (FX) |
| FINANCE_LINE_ANALYTICS total vs ARR_*_CATEGORIES total | per-line sum | aggregation sum | < $1 |
| Sigma dashboard vs canonical | dashboard view | canonical model | 0 |
| Account count vs Salesforce | SCD2 distinct | SFDC active account count | ±1% |
| ARR by region vs by segment | sum across regions | sum across segments | 0 |

---

## §12. Common "false alarms" (look like bugs but aren't)

| Observation | Often is... | Investigate by... |
|---|---|---|
| ARR dropped Q/Q | FX revaluation or one large customer churn | Walk the categories |
| New logo count looks low | Slipped deals to next quarter | Check stage 8/9 opps |
| Churn spike | M&A consolidation | Check churn reason codes |
| NDR dropped | Single large contraction | Walk top contributors |
| Snapshot count jumped | Backfill run | Check audit log |
| Account count jumped | New SCD2 syncs | Check sync history |

---

## §13. The "I found a bug" SOP

When you confirm a bug:

1. **Quantify**: how big is the impact? Which periods? Which dashboards?
2. **Don't make a noise** until you've verified
3. **Write up cleanly**:
   - What's the expected behavior?
   - What's the actual behavior?
   - Reproduction SQL
   - Impact assessment
4. **File Jira**: assign to data engineering
5. **Notify** Functional Architect (so they can communicate to stakeholders)
6. **Track** through fix + validation

Don't fix it yourself unless it's your model. Escalate to architect.

---

## §14. Cross-references

- `analysis-deliverables.md` — write-up patterns
- `stakeholder-communication.md` — communicating findings
- `finance-functional-analytics/metric-recipes.md` — query templates
