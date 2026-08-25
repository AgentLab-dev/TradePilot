# Retention Deep Dive — NRR, NDR, GRR, LRR, NCR + Cohort + Product + Customer

The complete retention-metric playbook. Every variant, every formula, every
edge case, every pitfall.

Retention is the most-watched SaaS metric by investors + boards. Getting it
wrong wastes management's time + erodes trust. Getting it right requires
discipline around grain, cohort definition, currency variant, and
SSR-aware categorization.

---

## §1. The retention metric family — at a glance

| Metric | Full name | Formula | Range | Grain options |
|---|---|---|---|---|
| **NRR / NDR** | Net Retention / Net Dollar Retention | `(BEGIN + EXPANSION - CHURN - CONTRACTION) / BEGIN` | 0% – ∞ (can exceed 100%) | Overall, by product, by segment, by tenure cohort |
| **GRR** | Gross Retention Rate | `(BEGIN - CHURN - CONTRACTION) / BEGIN` | 0% – 100% | Same |
| **LRR** | Logo Retention Rate | `count(retained logos) / count(begin logos)` | 0% – 100% | Account / customer |
| **NCR** | Net Customer Retention | Weighted by customer count | 0% – ∞ | Customer-grain |
| **PRR** | Product Retention Rate | Per-product, customer-weighted | 0% – 100% | Per product |
| **NRR-cohort** | Cohort NRR | NRR over time for a specific acquisition cohort | 0% – ∞ | Cohort × tenure |
| **NRR-vintage** | Vintage NRR | NRR by quarter of first contract | 0% – ∞ | Vintage cohort |
| **Cust NRR** | Customer NRR | Account-weighted NRR (not ARR-weighted) | 0% – ∞ | Account |

---

## §2. NRR (Net Retention) — the primary metric

### 2.1 Formula

```
NRR = (BEGIN_ARR + EXPANSION - CHURN - CONTRACTION) / BEGIN_ARR
```

Or equivalently:
```
NRR = (END_ARR_from_existing_cohort) / BEGIN_ARR
    = (END_ARR_total - NEW_LOGO_ARR) / BEGIN_ARR
```

### 2.2 Grain decisions (the 4 questions)

1. **What's the cohort?**
   - "Customers active at period start"
   - SQL: `WHERE begin_arr > 0` filter on the rollup
2. **What's the period?**
   - Trailing 12 months (TTM)
   - Last fiscal quarter
   - Year-over-year (most common for reporting)
3. **What's the currency variant?**
   - `USD_HIST` for true period-over-period (recommended)
   - `USD_CURRENT` for live trending (caveat: FX-noisy)
4. **What's the slice?**
   - Overall (company-wide)
   - By product, segment, region, tenure cohort, etc.

### 2.3 Canonical SQL

```sql
-- NRR overall, fiscal-quarter grain, USD_HIST, all customers
WITH cohort AS (
    SELECT
        SUM(CASE WHEN arr_category = 'BEGIN_ARR'   THEN arr_usd_hist ELSE 0 END) AS begin_arr,
        SUM(CASE WHEN arr_category = 'EXPANSION'   THEN arr_usd_hist ELSE 0 END) AS expansion,
        SUM(CASE WHEN arr_category = 'CHURN'       THEN ABS(arr_usd_hist) ELSE 0 END) AS churn,
        SUM(CASE WHEN arr_category = 'CONTRACTION' THEN ABS(arr_usd_hist) ELSE 0 END) AS contraction
    FROM FINANCE_PROD.AGGREGATIONS.ARR_PRODUCT_CATEGORIES
    WHERE fiscal_quarter = 'FY26Q1'
)
SELECT
    begin_arr,
    expansion,
    churn,
    contraction,
    (begin_arr + expansion - churn - contraction) AS net_retained_arr,
    ROUND((begin_arr + expansion - churn - contraction) / NULLIF(begin_arr, 0), 4) AS nrr
FROM cohort;
```

### 2.4 NRR by product, segment, region

```sql
-- NRR by product L3, fiscal-quarter grain
WITH cohort AS (
    SELECT
        product_code_l3,
        SUM(CASE WHEN arr_category = 'BEGIN_ARR'   THEN arr_usd_hist ELSE 0 END) AS begin_arr,
        SUM(CASE WHEN arr_category = 'EXPANSION'   THEN arr_usd_hist ELSE 0 END) AS expansion,
        SUM(CASE WHEN arr_category = 'CHURN'       THEN ABS(arr_usd_hist) ELSE 0 END) AS churn,
        SUM(CASE WHEN arr_category = 'CONTRACTION' THEN ABS(arr_usd_hist) ELSE 0 END) AS contraction
    FROM FINANCE_PROD.AGGREGATIONS.ARR_PRODUCT_CATEGORIES
    WHERE fiscal_quarter = 'FY26Q1'
    GROUP BY 1
)
SELECT
    product_code_l3,
    ROUND((begin_arr + expansion - churn - contraction) / NULLIF(begin_arr, 0), 4) AS nrr_pct
FROM cohort
ORDER BY nrr_pct DESC;
```

### 2.5 NRR — common interpretation pitfalls

| Pitfall | What goes wrong | Fix |
|---|---|---|
| Including NEW_LOGO in numerator | Counts new customers as "retention" — wrong | NRR only counts the begin cohort's evolution |
| Using `USD_CURRENT` for both BEGIN and EXPANSION | FX moves create fake retention swings | Use `USD_HIST` for period-over-period |
| Forgetting SSR resolution | Renewals look like churn + new logo → wrong NRR | Use canonical `ARR_*_CATEGORIES` (SSR-resolved) |
| Wrong cohort filter | Begin cohort doesn't match end cohort | Use canonical aggregation; don't filter mid-query |
| Mixing fiscal periods | "TTM ending Q1" with Q4 boundary error | Use `get_fiscal_*` macros consistently |
| Including pilots / one-time fees | Inflates BEGIN, distorts ratio | Filter `is_arr_eligible = TRUE` |

### 2.6 NRR vs NDR (terminology)

| Term | Industry usage |
|---|---|
| **NRR (Net Retention Rate)** | Common in SaaS company reporting |
| **NDR (Net Dollar Retention)** | Common in investor decks |
| **DBNR (Dollar-Based Net Retention)** | Same concept, different acronym |
| **NRR$** | Sometimes used to distinguish from logo-based NRR |

Workday standardizes on **NDR** in column names (`ARR_PRODUCT_NET_DOLLAR_RETENTION_DASH_V2`), executives use **NRR** in conversation. Treat as synonyms.

### 2.7 NRR benchmarks (industry)

| NRR | What it means |
|---|---|
| > 130% | Best-in-class (e.g., Snowflake, Cloudflare) |
| 110% – 130% | Strong SaaS |
| 100% – 110% | Healthy SaaS (expansion offsets churn) |
| 90% – 100% | Concerning (need to monitor) |
| < 90% | Customer base shrinking — strategic problem |

Workday's reported NDR: historically in the 105-115% range (FY24-FY26).

---

## §3. GRR (Gross Retention Rate)

### 3.1 Formula

```
GRR = (BEGIN_ARR - CHURN - CONTRACTION) / BEGIN_ARR
```

Note: EXPANSION is NOT in the numerator. GRR caps at 100% (no positive contribution from existing customers).

### 3.2 Why both NRR and GRR?

| Metric | What it tells you |
|---|---|
| **GRR** | "How well do we KEEP what we have?" (cleanest health signal) |
| **NRR** | "Are our customers growing with us?" (growth signal + retention combined) |

A company can have:
- High GRR + low NRR → keeping customers but not expanding → may indicate product saturation
- Low GRR + high NRR → losing customers but expanding the survivors → may indicate poor fit + high upsell to top accounts

Best to report both together.

### 3.3 GRR canonical SQL

```sql
WITH cohort AS (
    SELECT
        SUM(CASE WHEN arr_category = 'BEGIN_ARR'   THEN arr_usd_hist ELSE 0 END) AS begin_arr,
        SUM(CASE WHEN arr_category = 'CHURN'       THEN ABS(arr_usd_hist) ELSE 0 END) AS churn,
        SUM(CASE WHEN arr_category = 'CONTRACTION' THEN ABS(arr_usd_hist) ELSE 0 END) AS contraction
    FROM FINANCE_PROD.AGGREGATIONS.ARR_PRODUCT_CATEGORIES
    WHERE fiscal_quarter = 'FY26Q1'
)
SELECT
    ROUND((begin_arr - churn - contraction) / NULLIF(begin_arr, 0), 4) AS grr_pct
FROM cohort;
```

### 3.4 GRR benchmarks

| GRR | What it means |
|---|---|
| > 95% | Best-in-class enterprise SaaS |
| 90% – 95% | Strong |
| 85% – 90% | Average |
| 80% – 85% | Concerning |
| < 80% | High churn — major problem |

Workday's reported GRR: historically 95%+ (enterprise SaaS gold standard).

---

## §4. LRR (Logo Retention Rate) — counterpoint to ARR-weighted metrics

### 4.1 Formula

```
LRR = count(retained logos at period end) / count(logos at period start)
```

### 4.2 Why LRR matters

NRR/GRR are ARR-weighted, so they hide cases like:
- Lost 50 small customers ($100k total ARR) → small NRR impact
- Gained $200k expansion from 1 large customer → large NRR positive impact
- LRR shows you lost 50 customers despite great NRR

For health: GOOD NRR + DECLINING LRR = concerning. You're losing small customers (could be product-fit issue cascading).

### 4.3 Canonical SQL

```sql
WITH logos AS (
    SELECT
        COUNT(DISTINCT CASE 
            WHEN begin_arr > 0 THEN account_id 
        END) AS begin_logo_count,
        COUNT(DISTINCT CASE 
            WHEN begin_arr > 0 AND end_arr > 0 THEN account_id 
        END) AS retained_logo_count,
        COUNT(DISTINCT CASE 
            WHEN begin_arr > 0 AND end_arr = 0 THEN account_id 
        END) AS churned_logo_count
    FROM FINANCE_PROD.AGGREGATIONS.ARR_ACCOUNT_CATEGORIES
    WHERE fiscal_quarter = 'FY26Q1'
)
SELECT
    begin_logo_count,
    retained_logo_count,
    churned_logo_count,
    ROUND(retained_logo_count / NULLIF(begin_logo_count, 0), 4) AS lrr_pct
FROM logos;
```

### 4.4 LRR benchmarks

| LRR | What it means |
|---|---|
| > 95% | Excellent (large enterprise customers stick) |
| 90% – 95% | Strong |
| 80% – 90% | Average |
| < 80% | Frequent customer turnover |

Workday LRR: typically very high (95%+) due to enterprise contracts being sticky.

---

## §5. NCR (Net Customer Retention) — customer-weighted

### 5.1 Definition

NCR is like NRR but at customer count grain (not ARR-weighted). Less common; useful when ARR mix is skewed.

```
NCR = count(customers with end_arr >= begin_arr) / count(begin cohort)
```

A customer who expanded counts once; a customer who churned counts as zero.

Less informative than NRR (no $ weighting); used selectively.

---

## §6. Cohort Retention (Vintage Analysis)

### 6.1 What's a cohort?

A cohort is a group of customers who became customers in the same time period (typically same fiscal quarter or year). Examples:
- "FY24Q1 cohort" — customers signed in Feb-Apr 2023
- "FY24 cohort" — customers signed in FY24 (Feb 2023 – Jan 2024)

### 6.2 Cohort NRR curve

Track each cohort's NRR over time:

```
Cohort     | Initial ARR | NRR @ 12 mo | NRR @ 24 mo | NRR @ 36 mo
FY22 cohort | $20M        | 108%        | 122%        | 135%
FY23 cohort | $25M        | 112%        | 130%        | (not yet)
FY24 cohort | $35M        | 115%        | (not yet)   | (not yet)
FY25 cohort | $40M        | (in progress)
```

This reveals:
- Cohort quality trend (are newer cohorts more durable?)
- Expansion trajectory (when do customers start expanding?)
- "Land and expand" effectiveness

### 6.3 Canonical SQL — Cohort NRR

```sql
-- For FY24 cohort, NRR at each subsequent quarter
WITH cohort_customers AS (
    SELECT DISTINCT account_id
    FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS
    WHERE as_was_date = '2024-02-06'  -- FY24 Q1 start
      AND arr_category = 'NEW_LOGO'
      AND is_arr_eligible = TRUE
),
cohort_baseline AS (
    SELECT
        c.account_id,
        SUM(fla.arr_usd_hist) AS initial_arr
    FROM cohort_customers c
    JOIN FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS fla
      ON c.account_id = fla.account_id
    WHERE fla.as_was_date = '2024-02-06'
      AND fla.is_arr_eligible = TRUE
    GROUP BY 1
),
cohort_over_time AS (
    SELECT
        fla.as_was_date,
        SUM(fla.arr_usd_hist) AS cohort_arr_at_date
    FROM cohort_customers c
    JOIN FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS fla
      ON c.account_id = fla.account_id
    WHERE fla.as_was_date IN ('2024-05-06', '2024-08-06', '2024-11-06', '2025-02-06', '2025-05-06', '2025-08-06')
      AND fla.is_arr_eligible = TRUE
    GROUP BY 1
)
SELECT
    cot.as_was_date,
    DATEDIFF(month, '2024-02-06', cot.as_was_date) AS tenure_months,
    cot.cohort_arr_at_date,
    (SELECT SUM(initial_arr) FROM cohort_baseline) AS baseline_arr,
    cot.cohort_arr_at_date / NULLIF((SELECT SUM(initial_arr) FROM cohort_baseline), 0) AS cohort_nrr
FROM cohort_over_time cot
ORDER BY 1;
```

### 6.4 Visualizing cohort retention

The classic "retention curve" — each cohort's NRR plotted over tenure months:

```
           NRR
           |
    150% --|              ___________
           |        _____/  (FY22 cohort, mature)
    130% --|       /
           |      /
    110% --|     /__________ (FY24 cohort, expanding)
           |    /
    100% --|---/-----------------------------
           |  /
     80% --| /
           |/______________________________
              0    6    12   18   24   30   36  Tenure months
```

Healthy SaaS cohorts:
- Drop slightly in first 6-12 months (some early-churn)
- Recover and expand by month 18-24
- Continue compounding (cohort NRR > 100% by month 24)

Unhealthy cohorts:
- Continuous decline (churn dominates expansion)
- Never recover to 100%

---

## §7. Product Retention vs Customer Retention

### 7.1 The distinction

| Metric | Definition | Use case |
|---|---|---|
| **Customer Retention** | Account-level (a customer is retained if account has ANY active ARR) | Customer success management |
| **Product Retention** | Per-product (a product is retained if customer has ARR in that product) | Product strategy, roadmap |

A customer can be:
- **Customer-retained AND product-retained** (kept everything)
- **Customer-retained, product-churned** (dropped a product, kept others)
- **Customer-churned** (lost everything → product-churned everywhere automatically)

### 7.2 Product retention SQL

```sql
-- Per-product retention rate for FY26Q1
WITH product_cohort AS (
    SELECT
        product_code_l3,
        COUNT(DISTINCT CASE WHEN begin_arr > 0 THEN account_id END) AS begin_customers,
        COUNT(DISTINCT CASE WHEN begin_arr > 0 AND end_arr > 0 THEN account_id END) AS retained_customers,
        SUM(CASE WHEN arr_category = 'BEGIN_ARR' THEN arr_usd_hist ELSE 0 END) AS begin_arr_amt,
        SUM(CASE WHEN arr_category = 'CHURN'     THEN ABS(arr_usd_hist) ELSE 0 END) AS churn_arr_amt
    FROM FINANCE_PROD.AGGREGATIONS.ARR_PRODUCT_CATEGORIES
    WHERE fiscal_quarter = 'FY26Q1'
    GROUP BY 1
)
SELECT
    product_code_l3,
    begin_customers,
    retained_customers,
    ROUND(retained_customers * 1.0 / NULLIF(begin_customers, 0), 4) AS product_logo_retention,
    ROUND((begin_arr_amt - churn_arr_amt) / NULLIF(begin_arr_amt, 0), 4) AS product_gross_retention
FROM product_cohort
ORDER BY product_logo_retention ASC;  -- worst-retention products first
```

### 7.3 Why product retention matters

If "HCM" has 98% product retention but "Adaptive" has 82% product retention → Adaptive has a product-fit or implementation problem. Roadmap signal.

Customer retention may look fine (customer keeps HCM), but you're hemorrhaging Adaptive. Without product-level breakdown, you'd miss it.

---

## §8. Tenure-Cohort NRR (How does NRR look by customer age?)

Different tenure buckets have different NRR dynamics:

| Tenure | Typical NRR | Why |
|---|---|---|
| 0-12 months | 100-105% | Early-stage; minimal expansion |
| 12-24 months | 105-115% | Land-and-expand kicks in |
| 24-36 months | 110-130% | Mature expansion phase |
| 36+ months | 105-115% (declining) | Saturated; harder to expand |

By segmenting NRR by tenure, you can identify:
- Are new customers expanding fast enough?
- Are mature customers saturating?
- Is there a "tenure cliff" where customers stop expanding?

### 8.1 Canonical SQL — NRR by tenure cohort

```sql
WITH customer_tenure AS (
    SELECT
        account_id,
        MIN(term_start_date) AS first_contract_date
    FROM FINANCE_PROD.MANAGED.WD_AGREEMENT_SCD2
    WHERE is_current = TRUE
    GROUP BY 1
),
classified AS (
    SELECT
        a.account_id,
        a.fiscal_quarter,
        a.arr_category,
        a.arr_usd_hist,
        CASE
            WHEN DATEDIFF(month, ct.first_contract_date, DATE(a.fiscal_quarter_start_date)) <= 12 THEN '0-12 mo'
            WHEN DATEDIFF(month, ct.first_contract_date, DATE(a.fiscal_quarter_start_date)) <= 24 THEN '12-24 mo'
            WHEN DATEDIFF(month, ct.first_contract_date, DATE(a.fiscal_quarter_start_date)) <= 36 THEN '24-36 mo'
            ELSE '36+ mo'
        END AS tenure_bucket
    FROM FINANCE_PROD.AGGREGATIONS.ARR_ACCOUNT_CATEGORIES a
    JOIN customer_tenure ct ON a.account_id = ct.account_id
    WHERE a.fiscal_quarter = 'FY26Q1'
)
SELECT
    tenure_bucket,
    SUM(CASE WHEN arr_category = 'BEGIN_ARR'   THEN arr_usd_hist ELSE 0 END) AS begin_arr,
    SUM(CASE WHEN arr_category = 'EXPANSION'   THEN arr_usd_hist ELSE 0 END) AS expansion,
    SUM(CASE WHEN arr_category = 'CHURN'       THEN ABS(arr_usd_hist) ELSE 0 END) AS churn,
    SUM(CASE WHEN arr_category = 'CONTRACTION' THEN ABS(arr_usd_hist) ELSE 0 END) AS contraction,
    ROUND(
        (SUM(CASE WHEN arr_category = 'BEGIN_ARR'   THEN arr_usd_hist ELSE 0 END)
       + SUM(CASE WHEN arr_category = 'EXPANSION'   THEN arr_usd_hist ELSE 0 END)
       - SUM(CASE WHEN arr_category = 'CHURN'       THEN ABS(arr_usd_hist) ELSE 0 END)
       - SUM(CASE WHEN arr_category = 'CONTRACTION' THEN ABS(arr_usd_hist) ELSE 0 END))
        / NULLIF(SUM(CASE WHEN arr_category = 'BEGIN_ARR' THEN arr_usd_hist ELSE 0 END), 0), 4
    ) AS nrr
FROM classified
GROUP BY 1
ORDER BY 1;
```

---

## §9. Vintage NRR (per cohort, plotted over time)

Long-term cohort analysis — for each acquisition vintage, track NRR over years.

```sql
-- For each fiscal year of first-contract, what's the cohort's TTM NRR each year since?
WITH first_contract_year AS (
    SELECT
        account_id,
        MIN(get_fiscal_year(term_start_date)) AS vintage
    FROM FINANCE_PROD.MANAGED.WD_AGREEMENT_SCD2
    WHERE is_current = TRUE
    GROUP BY 1
),
yearly_arr AS (
    SELECT
        fc.vintage,
        get_fiscal_year(a.as_was_date) AS measurement_year,
        SUM(a.arr_usd_hist) AS cohort_arr
    FROM first_contract_year fc
    JOIN FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS a
      ON fc.account_id = a.account_id
    WHERE a.is_arr_eligible = TRUE
      AND a.as_was_date IN (... per-fiscal-year-end snapshots ...)
    GROUP BY 1, 2
),
baseline AS (
    SELECT vintage, SUM(cohort_arr) AS baseline_arr
    FROM yearly_arr
    WHERE measurement_year = vintage  -- year 0 = vintage year
    GROUP BY 1
)
SELECT
    ya.vintage,
    ya.measurement_year,
    ya.measurement_year - ya.vintage AS years_since_acquisition,
    ya.cohort_arr,
    b.baseline_arr,
    ROUND(ya.cohort_arr / NULLIF(b.baseline_arr, 0), 4) AS cohort_nrr_vs_baseline
FROM yearly_arr ya
JOIN baseline b ON ya.vintage = b.vintage
ORDER BY 1, 2;
```

---

## §10. Segment NRR (by customer characteristics)

NRR sliced by customer segments:
- Industry (Healthcare, Manufacturing, Tech, Government, etc.)
- Region (NA, EMEA, APAC, LATAM)
- Size segment (Enterprise, Mid-Market, SMB)
- Tenure cohort (see §8)
- Acquisition source (Direct, Partner, Marketing-sourced)
- Customer success tier (Tier 1 white-glove, Tier 2 standard, Tier 3 self-serve)

Each segment reveals different patterns:
- Enterprise NRR typically higher than SMB (sticky)
- Healthcare NRR may be lower than Tech (regulatory cycles)
- Partner-sourced NRR may differ from direct-sourced

Pattern:
```sql
SELECT
    industry,  -- or region, segment, etc.
    -- NRR calculation per segment
FROM ARR_INDUSTRY_CATEGORIES  -- or ARR_REGION_SEGMENT_CATEGORIES, etc.
WHERE fiscal_quarter = 'FY26Q1'
GROUP BY 1;
```

---

## §11. The reconciliation rule for retention metrics

Every retention number reported MUST pass:

1. **Begin and end cohort match**: BEGIN_ARR in cohort A = sum of customers active at period start
2. **Walk balances**: BEGIN_ARR + EXPANSION - CHURN - CONTRACTION ≈ retained_arr (within $1 after FX)
3. **NRR formula consistency**: numerator and denominator use SAME currency variant + SAME period boundaries
4. **No NEW_LOGO in numerator**: NEW_LOGO is OUTSIDE the retention cohort (different customers)

Validation SQL template:
```sql
-- Validate: NRR computed via two methods should match within rounding
WITH method_a AS (
    -- (BEGIN + EXPANSION - CHURN - CONTRACTION) / BEGIN
    ...
),
method_b AS (
    -- (END - NEW_LOGO) / BEGIN
    ...
)
SELECT
    method_a.nrr AS method_a_nrr,
    method_b.nrr AS method_b_nrr,
    ABS(method_a.nrr - method_b.nrr) AS variance
FROM method_a, method_b;
-- Variance < 0.001 (0.1%) is acceptable
```

---

## §12. The "renewal cohort" vs "NRR cohort" distinction

These are NOT the same thing:

| Cohort | Definition | Use |
|---|---|---|
| **NRR cohort** | Customers with `begin_arr > 0` at period START | Retention metric (any customer present at start) |
| **Renewal cohort** | Customers whose contract is UP FOR RENEWAL in period | Renewal-specific analysis (only those who had to renew this period) |

A customer with a 3-year contract signed Q1 FY24:
- Is in **NRR cohort** for every quarter (they're active and contribute to BEGIN_ARR)
- Is NOT in **renewal cohort** for Q1 FY25 (contract has 2 years left; no renewal action)
- IS in **renewal cohort** for Q1 FY27 (contract ending, must renew)

Renewal-specific metrics:
- **Renewal rate** = `count(renewed customers) / count(renewal cohort)` — narrower than NRR
- **Renewal $ retention** = `(renewal_arr_renewed) / (renewal_arr_up_for_renewal)`

Useful when answering "of the $50M up for renewal this quarter, how much was retained?" — different than overall NRR.

---

## §13. New New Retention (retention of new-logo cohorts)

"New New Retention" = NRR for the cohort of customers who were New New (pure new logos) in a prior period.

Why measure: are our NEW logos sticky? Or are they early-churn risks?

```sql
-- For FY24 new-new cohort, retention over time
WITH new_new_cohort AS (
    SELECT DISTINCT
        a.account_id,
        a.fiscal_quarter AS acquisition_quarter
    FROM FINANCE_PROD.AGGREGATIONS.ARR_ACCOUNT_CATEGORIES a
    WHERE a.fiscal_year = 'FY24'
      AND a.arr_category = 'NEW_LOGO'
      AND a.sub_category = 'NEW_NEW'  -- pure new logo
)
SELECT
    nnc.acquisition_quarter,
    SUM(a.arr_usd_hist) AS retained_arr_at_q1_fy26
FROM new_new_cohort nnc
JOIN FINANCE_PROD.AGGREGATIONS.ARR_ACCOUNT_CATEGORIES a
  ON nnc.account_id = a.account_id
WHERE a.fiscal_quarter = 'FY26Q1'
  AND a.arr_category IN ('BEGIN_ARR', 'EXPANSION')  -- still active customers
GROUP BY 1;
```

A common KPI: "FY24 new-new cohort retention rate at 24-month tenure".

---

## §14. The "TTM" (Trailing Twelve Months) variant

Sometimes reported as TTM rather than quarter-over-quarter. Formula adapts:

```
TTM NRR = (Sum of EXPANSION over last 4 quarters) + (Sum of BEGIN at start of TTM window)
          - (Sum of CHURN over last 4 quarters) - (Sum of CONTRACTION over last 4 quarters)
          ÷ (Sum of BEGIN at start of TTM window)
```

Smoothing effect: less noise from any single quarter.

For Workday: typically board-reported as "TTM NRR ending Q4 FY25".

---

## §15. The implied vs reported NRR — when they diverge

Sometimes published NRR (in earnings call) differs from computed NRR. Reasons:
- Different cohort definition (TTM vs single-quarter)
- Different denominator (BEGIN_ARR_NET vs BEGIN_ARR_GROSS)
- Currency variant (CFO may use USD_HIST; internal models may use USD_CURRENT)
- Acquisition customer treatment (re-baselined vs included from day 1)
- One-time fees / pilots included or excluded

If asked to reconcile "why does our internal NRR differ from public NRR" → walk through these dimensions.

---

## §16. Quick reference — which retention metric for which question?

| Question | Metric to use |
|---|---|
| "How are we doing overall on retention?" | NRR + GRR together |
| "Are we keeping customers?" | LRR (logo count) |
| "Which products are losing customers?" | Product Retention Rate |
| "Are new cohorts as strong as old cohorts?" | Cohort NRR trend |
| "Do we have a tenure cliff?" | Tenure-cohort NRR |
| "Are we losing the bottom 50%?" | LRR vs NRR comparison (LRR low + NRR high = losing small customers) |
| "How much of FY26 ARR comes from existing customers?" | `(END_ARR - NEW_LOGO) / END_ARR` |
| "Of the $X up for renewal, how much retained?" | Renewal-specific cohort (§12) |
| "Are NEW LOGOS expanding?" | New New cohort retention (§13) |

---

## §17. Cross-references

- `categorization-framework.md` — what goes into BEGIN / EXPANSION / CHURN buckets
- `churn-anatomy.md` — Customer vs Product churn dynamics
- `metric-recipes.md` — copy-paste SQL templates
- `enterprise-data-architect/finance-metrics-canonical.md` — canonical formulas
- `enterprise-metrics-finance-architect/cohort-and-vintage-modeling.md` — cohort architecture
