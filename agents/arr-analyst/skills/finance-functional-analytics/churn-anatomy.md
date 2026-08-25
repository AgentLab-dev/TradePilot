# Churn Anatomy — Customer Churn vs Product Churn, Voluntary vs Involuntary, Attribution

Churn isn't a single number — it's a family of signals with different
operational implications. Customer churn means CS+Sales got beat. Product
churn often means product-market fit issue. Involuntary churn (M&A) is
unavoidable but shouldn't be lumped with voluntary churn.

This doc covers the full taxonomy, attribution, and "save" mechanics.

---

## §1. The 4 axes of churn classification

Every churn event gets classified across 4 dimensions:

| Axis | Values |
|---|---|
| **Scope** | Customer churn / Product churn / Partial contraction (line-level) |
| **Volition** | Voluntary / Involuntary |
| **Stage** | Pre-churn (at risk) / Active churn (terminated) / Confirmed churn (no renewal) |
| **Attribution** | Reason category (cost / fit / competition / M&A / etc.) |

Combined: a single churn event might be "Customer-level, Voluntary, Confirmed, Competition (lost to Workday competitor)".

---

## §2. Scope — Customer vs Product vs Partial

### 2.1 Customer Churn (full loss)

**Definition**: Entire customer terminates. All agreements end. No retained relationship.

**Detection**:
```sql
-- At current as_was_date, account has zero active ARR
SELECT account_id
FROM FINANCE_LINE_ANALYTICS
WHERE as_was_date = '2026-04-30'
  AND is_arr_eligible = TRUE
GROUP BY account_id
HAVING SUM(arr_usd_current) = 0  -- no active ARR

-- AND had non-zero ARR at prior as_was_date
INTERSECT

SELECT account_id
FROM FINANCE_LINE_ANALYTICS
WHERE as_was_date = '2026-01-31'
  AND is_arr_eligible = TRUE
GROUP BY account_id
HAVING SUM(arr_usd_current) > 0;  -- had active ARR
```

**Impact**: Strong operational signal — CS team has a save play running through to termination; renewal team failed.

**Annual rate**: typically 2-5% of customers per year for enterprise SaaS (95-98% LRR).

### 2.2 Product Churn (partial loss)

**Definition**: Customer drops a specific product but retains other products. Customer relationship preserved.

**Detection**:
```sql
-- Account has churn in product X but retains active ARR in other products
WITH product_churns AS (
    SELECT account_id, product_code_l3
    FROM ARR_PRODUCT_CATEGORIES
    WHERE fiscal_quarter = 'FY26Q1'
      AND arr_category = 'CHURN'
)
SELECT
    pc.account_id,
    pc.product_code_l3 AS churned_product,
    EXISTS (
        SELECT 1 FROM FINANCE_LINE_ANALYTICS active
        WHERE active.account_id = pc.account_id
          AND active.as_was_date = '2026-04-30'
          AND active.arr_usd_current > 0
          AND active.product_code_l3 != pc.product_code_l3
    ) AS has_other_active_products
FROM product_churns pc
WHERE has_other_active_products = TRUE;  -- product churn (not customer churn)
```

**Impact**: Product strategy signal. If "Adaptive" has high product churn while customers keep "HCM", that's a product-fit issue with Adaptive specifically.

**Why it matters separately**:
- Customer relationship preserved → CSM can investigate, possibly re-sell later
- Product roadmap signal → may indicate feature gap, UX issue, market mismatch
- Different remediation: product team vs CS team

### 2.3 Partial Contraction (line-level)

**Definition**: Customer kept the product but reduced seats / downsized / dropped to lower tier.

**Detection**: ARR delta on existing line, not full termination.

```sql
-- Line existed in both periods but ARR decreased
SELECT
    line.agreement_line_item_id,
    line.account_id,
    line.product_code_l3,
    prior.arr_usd_current AS prior_arr,
    line.arr_usd_current AS current_arr,
    line.arr_usd_current - prior.arr_usd_current AS delta
FROM FINANCE_LINE_ANALYTICS line
JOIN FINANCE_LINE_ANALYTICS prior
  ON line.agreement_line_item_id = prior.agreement_line_item_id
WHERE line.as_was_date = '2026-04-30'
  AND prior.as_was_date = '2026-01-31'
  AND prior.arr_usd_current > 0
  AND line.arr_usd_current > 0
  AND line.arr_usd_current < prior.arr_usd_current;
```

**Impact**: Customer health warning sign (downsizing often precedes full churn). CS investigates.

---

## §3. Volition — Voluntary vs Involuntary

### 3.1 Voluntary churn

**Definition**: Customer actively chose to leave. Could be:
- Cost / budget pressure
- Switched to a competitor
- Product didn't meet needs (fit issue)
- Implementation never completed (project failure)
- Leadership change (new CIO replaces incumbent stack)
- Lost executive sponsor

**Operational implication**: This is the CS/Sales-actionable category. Should drive process improvements.

### 3.2 Involuntary churn

**Definition**: Customer departed but not because they chose Workday's competitor. Common causes:
- Customer acquired by another company that uses different stack
- Customer went out of business
- Customer industry-shifted (e.g., became a SaaS company that no longer needs HCM)
- Forced regulatory exit (rare)

**Operational implication**: Not actionable by CS/Sales. Should be reported separately to avoid distorting renewal team's metrics.

### 3.3 Classification

In Gainsight (or churn capture form):
- CS team logs churn reason at termination
- Reason category: dropdown (Cost / Fit / Competition / M&A / Other)
- Sub-reason: free text

Stored in:
- `LOYALTY_ADVOCACY_PROD.MANAGED.CHURN_EVENT.churn_reason_category`
- `LOYALTY_ADVOCACY_PROD.MANAGED.CHURN_EVENT.churn_reason_subcategory`

For finance reporting:
- **Voluntary churn ARR** — subset of CHURN where `volition = 'VOLUNTARY'`
- **Involuntary churn ARR** — subset where `volition = 'INVOLUNTARY'`
- **Unclassified churn** — gaps in CS reason capture (typically < 5%)

---

## §4. The reason taxonomy (canonical)

Standardized churn reason categories at Workday:

| Category | Description | Examples |
|---|---|---|
| **COST** | Budget / cost-of-product issue | Reduced budget, found cheaper alternative |
| **FIT** | Product doesn't meet needs | Missing feature, wrong size, complexity |
| **COMPETITION** | Lost to competitor | Switched to SAP / Oracle / specialized vendor |
| **IMPLEMENTATION_FAILURE** | Project never went live | Implementation stalled, partner failure |
| **EXEC_CHANGE** | Leadership change at customer | New CIO doesn't want this stack |
| **MERGER_ACQUISITION** | Customer acquired or merged | Acquired by company using different stack |
| **BUSINESS_SHUTDOWN** | Customer ceased operations | Out of business |
| **DUPLICATE_ACCOUNT** | Data quality — was wrongly counted as customer | Should never have been counted |
| **STRATEGIC_PIVOT** | Customer's business model changed | No longer relevant use case |
| **OTHER** | Other (free-text required) | Unique circumstances |
| **UNCLASSIFIED** | Reason not captured | Should be < 5% of churns |

Categories mapped to volition:
- COST, FIT, COMPETITION, IMPLEMENTATION_FAILURE, EXEC_CHANGE → **Voluntary**
- MERGER_ACQUISITION, BUSINESS_SHUTDOWN, STRATEGIC_PIVOT → **Involuntary**
- DUPLICATE_ACCOUNT, UNCLASSIFIED → exclude from reporting (data quality)

---

## §5. Acquisition churn (special case)

Workday-acquired companies (Adaptive, Scout, Peakon, VNDLY) had their own
customer base at acquisition time. Some of those customers churn within
months of acquisition.

**Why it's special**: These customers were never originally Workday customers — they may not have wanted to be on Workday. Their churn shouldn't be lumped with native-Workday-customer churn.

Tracked separately:
- `IS_ACQUIRED_CUSTOMER_BASE` flag on Account (TRUE if customer came in via acquisition)
- `ACQUISITION_DATE` — when their relationship transferred to Workday

Churn rate reporting:
- **Native customer churn rate** — excludes acquired-base
- **Acquired-base churn rate** — separate metric
- **Combined churn rate** — both included, but typically reported separately

```sql
-- Native vs acquired-base churn rate, FY26 Q1
WITH classified AS (
    SELECT
        a.account_id,
        a.is_acquired_customer_base,
        a.arr_category,
        a.arr_usd_hist
    FROM ARR_ACCOUNT_CATEGORIES a
    WHERE a.fiscal_quarter = 'FY26Q1'
)
SELECT
    is_acquired_customer_base,
    SUM(CASE WHEN arr_category = 'BEGIN_ARR' THEN arr_usd_hist ELSE 0 END) AS begin_arr,
    SUM(CASE WHEN arr_category = 'CHURN'     THEN ABS(arr_usd_hist) ELSE 0 END) AS churn_arr,
    ROUND(SUM(CASE WHEN arr_category = 'CHURN' THEN ABS(arr_usd_hist) ELSE 0 END)
        / NULLIF(SUM(CASE WHEN arr_category = 'BEGIN_ARR' THEN arr_usd_hist ELSE 0 END), 0), 4) AS churn_rate
FROM classified
GROUP BY 1;
```

---

## §6. The pre-churn (early-warning) signals

Churn doesn't happen overnight. Health-score signals predict it 60-180 days out.

Pre-churn signals (in priority order):
1. **NPS dropped** from Promoter to Detractor (within 60 days)
2. **Login frequency dropped** by 50%+ (within 30 days)
3. **Support tickets surged** with CSAT < 3 (within 60 days)
4. **Exec sponsor changed** at customer (within 90 days)
5. **Implementation milestones missed** (any time)
6. **CSM-flagged risk** via Gainsight CTA
7. **Contract renewal approaching** without engagement signals
8. **Competitor RFP** (intel via CDP / Gong call analysis)

For agile CS response: scoring + CTAs in Gainsight.

For finance forecasting: Churn risk score → renewal-risk-[REDACTED] ARR (see `enterprise-data-architect/domain-cx-customer-success.md §4.4`).

---

## §7. "Save" mechanics (averting churn)

When CSM identifies at-risk customer, they engage a **save play**:

```
Customer flagged → Diagnostic call → Discount / extend / re-implementation offer → Decision
                                                                                       │
                                              ┌────────────────────────────────────────┘
                                              ▼
                              ┌──────────────────────────────────────┐
                              │ Outcome categorization                │
                              ├──────────────────────────────────────┤
                              │ Saved (full save) — no churn          │
                              │ Saved (with concession) — retained at lower ARR │
                              │ Delayed (extended term, churn later) │
                              │ Lost despite save attempt             │
                              └──────────────────────────────────────┘
```

"Save rate" KPI:
- `Save rate = count(customers saved) / count(at-risk customers engaged)`

Workday's typical save rate: 30-50% (industry varies)

Tracked in:
- `LOYALTY_ADVOCACY_PROD.MANAGED.SAVE_PLAY_OUTCOMES` (built from Gainsight CTA + agreement outcomes)

---

## §8. The "ARR lost to churn" decomposition

Total churn ARR in a period decomposed by reason:

```sql
-- FY26 Q1 churn decomposition
WITH churn_events AS (
    SELECT
        ce.account_id,
        ce.churn_reason_category,
        ce.volition,
        SUM(a.arr_usd_hist) AS churn_arr
    FROM LOYALTY_ADVOCACY_PROD.MANAGED.CHURN_EVENT ce
    JOIN ARR_ACCOUNT_CATEGORIES a
      ON ce.account_id = a.account_id
    WHERE a.fiscal_quarter = 'FY26Q1'
      AND a.arr_category = 'CHURN'
    GROUP BY 1, 2, 3
)
SELECT
    churn_reason_category,
    volition,
    COUNT(*) AS num_accounts,
    SUM(ABS(churn_arr)) AS total_churn_arr_usd,
    ROUND(SUM(ABS(churn_arr)) / SUM(SUM(ABS(churn_arr))) OVER (), 4) AS pct_of_total_churn
FROM churn_events
GROUP BY 1, 2
ORDER BY 4 DESC;
```

Typical output:
| Reason | Volition | Accounts | ARR | % |
|---|---|---|---|---|
| MERGER_ACQUISITION | Involuntary | 12 | $4.5M | 30% |
| COMPETITION | Voluntary | 8 | $3.0M | 20% |
| FIT | Voluntary | 15 | $2.5M | 17% |
| COST | Voluntary | 20 | $2.2M | 15% |
| EXEC_CHANGE | Voluntary | 5 | $1.8M | 12% |
| IMPLEMENTATION_FAILURE | Voluntary | 3 | $0.5M | 3% |
| Other / Unclassified | Mixed | 7 | $0.5M | 3% |

---

## §9. The "winback" pattern (customer churned, came back)

Customer churned → after months/years, signs new contract.

Categorization:
- The original churn IS still churn (immutable)
- The new contract is NEW_LOGO (treat as new customer)
- Account ARR went $X → 0 → $Y over the period

Some companies have a "winback" sub-category. Workday currently does NOT distinguish — but you can identify:

```sql
-- Winback candidates: NEW_LOGO accounts that had prior churn history
WITH new_logos AS (
    SELECT DISTINCT account_id
    FROM ARR_ACCOUNT_CATEGORIES
    WHERE fiscal_quarter = 'FY26Q1' AND arr_category = 'NEW_LOGO'
),
prior_churns AS (
    SELECT DISTINCT account_id, fiscal_quarter AS churn_quarter
    FROM ARR_ACCOUNT_CATEGORIES
    WHERE arr_category = 'CHURN'
      AND fiscal_year IN ('FY24', 'FY25')  -- prior 2 years
)
SELECT nl.account_id, pc.churn_quarter
FROM new_logos nl
JOIN prior_churns pc ON nl.account_id = pc.account_id;
```

If winback becomes operationally important, escalate to add a formal sub-category.

---

## §10. The "negative churn" goal (vendor aspiration)

"Negative churn" = expansion exceeds churn, so cohort grows even without new logos.

```
Net cohort movement = EXPANSION - CHURN - CONTRACTION
```

When > 0 → cohort grew. Cohort NRR > 100%.

Workday target: cohort NRR > 110% (industry-strong).

---

## §11. The "logo churn" vs "$ churn" divergence

Sometimes these tell different stories:

| Scenario | Logo churn | $ churn |
|---|---|---|
| Lost 100 small SMB customers, $50k total | 100 logos | $50k |
| Lost 1 enterprise customer, $5M | 1 logo | $5M |

For reporting: both should be presented. Logo churn captures relationship loss; $ churn captures financial impact.

---

## §12. Churn forecasting (predictive)

ML-driven prediction of churn risk per account.

Inputs (features):
- ARR (size matters — large customers churn less)
- Tenure (months as customer)
- Product mix (more products = stickier)
- NPS trend (declining = risk)
- Login frequency trend
- Support ticket volume + CSAT
- Days to next renewal
- CSM-flagged risk
- Industry / segment

Output: `churn_risk_score` (0-1 probability of not renewing within X months)

Used for:
- CS team prioritization (focus on highest-risk accounts)
- Finance forecasting (`expected_arr = arr × (1 - churn_risk)`)
- Sales territory planning (renewal team sizing)

Model owner: ML / data science team. Built in Snowpark or external Python notebooks. Lives in `LOYALTY_ADVOCACY_PROD.MANAGED.CHURN_RISK_SCORE`.

---

## §13. Churn rate (annualized) — the headline number

The most-reported churn metric:

```
Annual customer churn rate = customers lost in last 12 months / customers at start of period
Annual $ churn rate         = $ churn in last 12 months / $ ARR at start of period
```

Note: this is the inverse of GRR (sort of):
```
$ churn rate ≈ 1 - GRR (assuming small contraction)
```

For Workday: typically reported as "gross customer churn rate" and "gross ARR churn rate" in earnings calls.

---

## §14. The "churn cliff" pattern (vintage analysis)

Some cohorts have an early "churn cliff" — high churn in first 6-12 months.

Common at enterprise SaaS for:
- Pilots that didn't convert to multi-year
- Customers who bought during a hype cycle
- Implementations that failed early

Tracked via cohort retention curve (see `retention-deep-dive.md §6.4`).

If you see a cliff in FY25 cohort that prior cohorts didn't have → investigate that cohort's go-to-market motion.

---

## §15. The "death spiral" pattern (multi-quarter contraction → churn)

A customer that contracts for multiple consecutive quarters typically churns within 12 months.

Detection:
```sql
-- Accounts that have contracted for 3+ consecutive quarters
WITH contractions AS (
    SELECT
        account_id,
        fiscal_quarter,
        ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY fiscal_quarter) AS rn,
        DENSE_RANK() OVER (PARTITION BY account_id ORDER BY fiscal_quarter) AS dr
    FROM ARR_ACCOUNT_CATEGORIES
    WHERE arr_category = 'CONTRACTION'
)
SELECT account_id, COUNT(*) AS consecutive_contractions
FROM contractions
GROUP BY 1
HAVING consecutive_contractions >= 3;
```

Use this for proactive CS intervention.

---

## §16. The reporting cadence (who sees churn data when)

| Audience | Cadence | Granularity |
|---|---|---|
| **CSMs** | Daily | Per-account, with risk score |
| **CS leadership** | Weekly | Aggregate by segment, sub-category |
| **Sales leadership** | Monthly | Aggregate by region, deal motion |
| **CFO / FP&A** | Monthly + Quarterly | Aggregate $ churn, reason breakdown |
| **Board** | Quarterly | Headline churn rate, GRR, NRR |
| **Investors (earnings)** | Quarterly | Reported per disclosure rules |

Tailor the reporting to the audience.

---

## §17. Anti-patterns (do NOT do)

- ❌ Report churn without separating customer vs product churn — they're different signals
- ❌ Lump voluntary + involuntary churn — masks save-team performance
- ❌ Forget acquired-customer-base churn — distorts native churn rate
- ❌ Report churn rate from new-logo numerator (numerator is BEGIN cohort only)
- ❌ Use `USD_CURRENT` for churn$ — FX moves create fake churn deltas
- ❌ Ignore `is_arr_eligible` filter — pilots / one-time fees pollute
- ❌ Classify SSR transitions as CHURN — use SSR-aware logic
- ❌ Skip volition classification — leaves the actionability gap

---

## §18. Cross-references

- `categorization-framework.md` — how CHURN category is derived from line deltas
- `retention-deep-dive.md` — how churn fits into retention metrics
- `metric-recipes.md` — SQL templates
- `enterprise-data-architect/domain-cx-customer-success.md` — Gainsight + health scoring
- `enterprise-data-architect/finance-metrics-canonical.md` — canonical churn definition
