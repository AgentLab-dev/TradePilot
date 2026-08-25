# Finance Metrics — Canonical Definitions

The authoritative reference for **ACV, ARR, TCV, NRR, GRR, NDR, churn,
expansion, contraction**, and the rules every Workday EDH model must follow.

If anyone (executive, analyst, engineer) defines one of these metrics
differently than what's here, this doc wins. Push the difference back to
this doc to evolve the definition — don't ship the alternative.

---

## §1. The 3 contract-value metrics

### 1.1 TCV — Total Contract Value

**Definition:** Total cash value of a contract over its **full term**.

**Formula:** `TCV = SUM(TotalFees per AgreementLineItem)` (no time-normalization)

**Grain:** Agreement Line Item (ALI)
**Source field:** `APTTUS__AGREEMENTLINEITEM__C.TOTAL_FEES__C` (or `ADJ_AL_TOTAL_FEES__C` post-corrections)

**Time treatment:** As-is (no annualization). A 3-year $300k contract has TCV = $300k.

**Currency variants:** `tcv_usd_current`, `tcv_usd_hist`, `tcv_usd_actual`

**Where to find it:**
- Per-line: `FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS.tcv_usd_*`
- Adjusted (with corrections): `COALESCE(corrected_tcv, raw_tcv)` — applied via `stg_em_lkp_wd_fin_tcv_correction`

**Common pitfall:** Mid-term amendments. If a contract is amended (added seats, extended term), the **delta** is captured as a new AgreementLineItem with `SKU_ADDED_VIA_AMENDMENT__C = TRUE`. Sum both original + amendment ALIs for true TCV.

**SQL pattern:**
```sql
SELECT
    SUM(COALESCE(corrected_tcv_usd_current, tcv_usd_current)) AS total_tcv_usd_current
FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS
WHERE as_was_date = '2026-04-30'
  AND agreement_status = 'Activated';
```

---

### 1.2 ARR — Annual Recurring Revenue

**Definition:** Annualized value of **active recurring** subscriptions.

**Formula:** `ARR = (TCV × 365) / contract_term_days`

Per-line, where contract_term_days = `DATEDIFF(day, term_start_date, term_end_date)`.

**Grain:** Agreement Line Item × `as_was_date`
**Source:** Derived from TCV via macro `{{ tcv_to_arr() }}`

**Time treatment:** Annualized — normalizes long/short contracts to a per-year basis.

**Examples:**
| Contract | TCV | Term | ARR |
|---|---|---|---|
| Annual subscription | $100k | 365 days | $100k |
| 3-year subscription | $300k | 1095 days | $100k |
| 18-month subscription | $150k | 540 days | $100k |
| 6-month pilot | $50k | 180 days | $101k (annualized — but watch for "pilots count as ARR" policy) |

**Currency variants:** `arr_usd_current`, `arr_usd_hist`, `arr_usd_actual`

**Where to find it:**
- Per-line: `FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS.arr_usd_*`
- By product: `FINANCE_PROD.AGGREGATIONS.ARR_PRODUCT_CATEGORIES`
- By SKU: `FINANCE_PROD.AGGREGATIONS.ARR_SKU_CATEGORIES`

**Inclusions:**
- ✅ Activated subscriptions
- ✅ Mid-term amendments (annualized delta)
- ✅ Renewals (counted from new agreement)

**Exclusions:**
- ❌ One-time fees (implementation, training, professional services)
- ❌ Pending / not-activated contracts
- ❌ Churned / terminated agreements (as of `as_was_date`)
- ❌ Usage-based revenue (if any)

**SQL pattern (latest snapshot):**
```sql
SELECT SUM(arr_usd_current) AS total_arr
FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS
WHERE as_was_date = (SELECT MAX(as_was_date) FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS)
  AND is_arr_eligible = TRUE;
```

---

### 1.3 ACV — Annual Contract Value

**Definition:** Total annualized value in the **first year** of the contract.

**Formula:** `ACV = SUM(TCV per line, normalized to 12 months)`

**Grain:** Agreement Line Item × `as_was_date`
**Source:** Derived from TCV via macro `{{ tcv_to_acv() }}`

**Key difference from ARR:** ACV captures **booking** value at contract sign; ARR captures **active running** value as-of a date.

**Subtle differences:**
| Scenario | ACV | ARR |
|---|---|---|
| 1-year contract, $100k | $100k | $100k |
| 3-year contract, $90k Y1 + $100k Y2 + $110k Y3 | $90k (year 1 only) | $100k (avg per year, annualized) |
| Ramp contract starting at $50k → $100k → $150k | $50k (year 1) | $100k (avg over term) |
| Mid-term amendment +$30k | $0 ACV (no new booking) | $30k ARR delta (after amendment date) |

**Use case:**
- **ACV** → sales attainment, quota retirement, "bookings"
- **ARR** → recurring revenue trending, retention analysis

**Currency variants:** `acv_usd_current`, `acv_usd_hist`, `acv_usd_actual`

**Where to find it:**
- Per-line: `FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS.acv_usd_*`
- Sales-attainment focused: `SALES_PROD.AGGREGATIONS.BT_ACV_SKU` (booking-grain ACV)

---

### 1.4 The relationship

```
TCV    = full contract value (no time normalization)
ACV    = year-1 contract value (annualized year 1 only)
ARR    = average annualized value over contract term (at as_was_date)
```

For a **flat (no ramp)** annual subscription contract: `TCV / years = ACV = ARR`.

For ramped or multi-year contracts: TCV ≠ ACV ≠ ARR.

---

## §2. Retention metrics

### 2.1 GRR — Gross Retention Rate

**Definition:** Percentage of recurring revenue retained from existing customers, **excluding any expansion**.

**Formula:**
```
GRR = (BEGIN_ARR - CHURN - CONTRACTION) / BEGIN_ARR
```

**Numerator:** What was retained (begin minus losses)
**Denominator:** What we started with

**Range:** 0% to 100% (cannot exceed 100% — no expansion counted)

**Worked example:**
```
Begin ARR (start of Q1):       $100M
- Churn during Q1:              $5M
- Contraction during Q1:        $3M
= Retained from begin cohort:   $92M

GRR = $92M / $100M = 92%
```

**Use case:** "How well do we keep our customers and their original spend?" Industry-standard SaaS health metric.

**Benchmark:** Best-in-class enterprise SaaS = 90%+

**Grain options:**
- Company-wide: rollup of all categories
- Per-product: filter `ARR_PRODUCT_CATEGORIES`
- Per-segment: filter `ARR_REGION_SEGMENT_CATEGORIES`

**Canonical SQL:**
```sql
WITH cohort AS (
    SELECT
        SUM(CASE WHEN category = 'BEGIN_ARR' THEN arr_usd_hist END) AS begin_arr,
        SUM(CASE WHEN category = 'CHURN'     THEN arr_usd_hist END) AS churn,
        SUM(CASE WHEN category = 'CONTRACTION' THEN arr_usd_hist END) AS contraction
    FROM FINANCE_PROD.AGGREGATIONS.ARR_PRODUCT_CATEGORIES
    WHERE fiscal_quarter = 'FY26Q1'
)
SELECT (begin_arr - ABS(churn) - ABS(contraction)) / begin_arr AS grr
FROM cohort;
```

---

### 2.2 NRR — Net Retention Rate (also called NDR — Net Dollar Retention)

**Definition:** Percentage of recurring revenue retained from existing customers, **including expansion**.

**Formula:**
```
NRR = (BEGIN_ARR + EXPANSION - CHURN - CONTRACTION) / BEGIN_ARR
```

(or equivalent: `NRR = (END_ARR - NEW_LOGO) / BEGIN_ARR`)

**Range:** Can exceed 100% if expansion outpaces losses (this is the "best" case).

**Worked example:**
```
Begin ARR (start of Q1):       $100M
+ Expansion during Q1:          $12M
- Churn during Q1:              $5M
- Contraction during Q1:        $3M
= Net retained:                 $104M

NRR = $104M / $100M = 104%
```

**Use case:** "Are our existing customers growing with us?" Most-watched SaaS metric by investors.

**Benchmark:** Best-in-class enterprise SaaS = 120%+

**Why NRR > 100% is great:**
- Customers love the product enough to buy more
- Compounds without needing to acquire new logos
- Indicates strong product-market fit

**Canonical SQL:**
```sql
WITH cohort AS (
    SELECT
        SUM(CASE WHEN category = 'BEGIN_ARR'   THEN arr_usd_hist END) AS begin_arr,
        SUM(CASE WHEN category = 'EXPANSION'   THEN arr_usd_hist END) AS expansion,
        SUM(CASE WHEN category = 'CHURN'       THEN arr_usd_hist END) AS churn,
        SUM(CASE WHEN category = 'CONTRACTION' THEN arr_usd_hist END) AS contraction
    FROM FINANCE_PROD.AGGREGATIONS.ARR_PRODUCT_CATEGORIES
    WHERE fiscal_quarter = 'FY26Q1'
)
SELECT
    (begin_arr + expansion - ABS(churn) - ABS(contraction)) / begin_arr AS nrr
FROM cohort;
```

**Canonical dashboard:** `FINANCE_PROD.DATA_PRODUCTS.ARR_PRODUCT_NET_DOLLAR_RETENTION_DASH_V2`

---

### 2.3 NDR vs NRR — same thing, different names

The industry uses these interchangeably:
- **NRR (Net Retention Rate)** — common in SaaS company reporting
- **NDR (Net Dollar Retention)** — common in investor decks, equivalent
- **NRR$ / DBNR (Dollar-Based Net Retention)** — same concept, different acronym

Workday EDH standardizes on **NDR** in column names + view names (`ARR_PRODUCT_NET_DOLLAR_RETENTION_DASH_V2`), but executive decks may use NRR. Treat as synonyms.

---

### 2.4 LRR — Logo Retention Rate

**Definition:** Percentage of customer **logos (accounts)** retained, regardless of ARR amount.

**Formula:**
```
LRR = (count of accounts at start that are still active at end) / count of accounts at start
```

**Use case:** Counterpoint to ARR-weighted metrics — captures "did we lose lots of small customers?" cases that NRR can hide.

**Canonical view:** `FINANCE_PROD.AGGREGATIONS.ARR_ACCOUNT_CATEGORIES` (logo-grain).

---

## §3. The 9-category ARR waterfall

Used by every ARR view family. Sums must balance:

```
BEGIN_ARR
+  NEW_LOGO           ← Brand-new customer (no prior ARR)
+  EXPANSION          ← Existing customer, more ARR
                          - More seats / users (volume up)
                          - Higher tier SKU (price up)
                          - New product family (cross-sell)
-  CONTRACTION        ← Existing customer, less ARR
                          - Fewer seats (volume down)
                          - Lower tier
                          - Dropped a product family (partial churn)
-  CHURN              ← Customer fully gone (no replacement contract)
±  SKU_CHANGE         ← Same customer, migrated to different SKU (HCM v1 → HCM v2)
                          - Often 0-sum (same value, different SKU)
                          - Or net+ / net- if pricing changed
±  VOLUME             ← Sub-category of EXPANSION/CONTRACTION isolating seat/usage change
±  PRICE              ← Sub-category isolating list-price changes
±  MIX                ← Currency rebasing or region rebalancing
= END_ARR
```

Notes:
- `EXPANSION` includes `VOLUME` + `PRICE` deltas (positive)
- `CONTRACTION` includes `VOLUME` + `PRICE` deltas (negative)
- `VOLUME` / `PRICE` / `MIX` are also reported separately for category attribution dashboards
- `SKU_CHANGE` is its own category — not counted in EXPANSION / CONTRACTION

The waterfall must balance:
```
BEGIN_ARR + NEW_LOGO + EXPANSION - CONTRACTION - CHURN + SKU_CHANGE_NET + VOLUME_NET + PRICE_NET + MIX_NET = END_ARR
```
(with <$1 rounding variance after currency conversion)

---

## §4. The categorization engine

ARR category is derived in `eda-dbt-em` via:

```
FINANCE_INT_PROD.STAGE.stg_em_int_arr_line_base
   │
   ├── Calls UDTF: get_arr_line_base_fn(ali_id, as_was_date)
   │
   ├── Resolves SSR via SSR_AGREEMENT_RELATIONSHIP
   │
   ├── Compares current snapshot to prior snapshot
   │
   └── Classifies into 9 categories using classification macros
```

Key classification rules (encoded in macros):

| Condition | Category |
|---|---|
| `prior_ali_arr IS NULL AND current_ali_arr > 0` AND `is_ssr = FALSE` AND `is_existing_customer = FALSE` | NEW_LOGO |
| `prior_ali_arr IS NULL AND current_ali_arr > 0` AND `is_ssr = FALSE` AND `is_existing_customer = TRUE` | EXPANSION (cross-sell) |
| `prior_ali_arr > 0 AND current_ali_arr > prior_ali_arr` | EXPANSION |
| `prior_ali_arr > 0 AND current_ali_arr < prior_ali_arr AND current_ali_arr > 0` | CONTRACTION |
| `prior_ali_arr > 0 AND current_ali_arr = 0 AND is_ssr = FALSE` | CHURN |
| `prior_ali_arr > 0 AND current_ali_arr = 0 AND is_ssr = TRUE` AND `new_agreement_arr ≈ prior_arr` | FLAT_RENEWAL (no category change) |
| `is_ssr = TRUE AND prior_sku ≠ new_sku AND arr_within_tolerance` | SKU_CHANGE |
| `is_ssr = TRUE AND new_arr > prior_arr` | EXPANSION (renewal expansion) |
| `is_ssr = TRUE AND new_arr < prior_arr` | CONTRACTION (renewal contraction) |

Edge cases get tagged with `audit_flags` for finance to manually review.

---

## §5. The currency variants — formal definitions

Every metric column exists in 3 variants:

### 5.1 USD_CURRENT — "What is this worth today?"

- Apply the **latest** FX rate at query time (or daily-snapshot FX)
- Used for: live trending dashboards, forecasting
- Logic: `amount_local × current_fx_rate_to_usd`
- Sensitive to FX swings — last week's ARR can change just because EUR moved

### 5.2 USD_HIST — "What was this worth when it happened?"

- Apply the FX rate **at transaction date**
- Used for: period-over-period comparisons (apples-to-apples)
- Logic: `amount_local × fx_rate_at(transaction_date)`
- FX-locked at booking — historical numbers don't change

### 5.3 USD_ACTUAL — "What did the customer actually pay (no conversion)?"

- Raw transaction currency, no conversion to USD
- Used for: billing reconciliation, invoice analysis
- Logic: `amount_local` (passthrough)
- Used in cash-flow models, A/R aging

**Critical rule:** NEVER mix variants in a single rollup. Document which variant you're using in every dashboard, query, and report.

For pipeline implementation: `domain-finance-billing.md` §3.

---

## §6. Reporting cadence (when do these numbers refresh?)

| Metric | Refresh frequency | Critical-window |
|---|---|---|
| ARR (current) | Daily (with 03:15 PDT batch) | T-1 freshness |
| ARR (period close) | At end of fiscal month | Locked snapshot, immutable |
| Bookings (ACV) | Real-time via Sigma cached views | T-2 hour freshness |
| GRR / NRR | Quarterly (per FY quarter) | Locked at quarter-end |
| Pipeline | Weekly (every Monday) | Sales weekly review |
| Forecast (Clari) | Daily | T-1 freshness |

Holiday / fiscal-quarter close: Snapshot at midnight on last day of fiscal month. Backfill / reload only with SOX approval.

---

## §7. ARR sub-metrics (less-common but used)

### CARR — Committed ARR

ARR-equivalent for contracts that are **signed but not yet active** (e.g., signed in March, service starts April).

`CARR = ARR + Contracted-but-not-yet-active deals`

### iARR — Implied ARR

For usage-based or hybrid pricing: annualize the **trailing 3-month run-rate**.

`iARR = (last_3_months_revenue / 90) × 365`

Typically not used at Workday (mostly subscription, not usage). Some product lines may use it.

### ARR — Bookings vs Activated

Some dashboards distinguish:
- **Activated ARR** — `agreement_status = 'Activated'` AND `as_was_date >= activation_date`
- **Booked ARR** — `agreement_status = 'Activated' OR 'Signed'`

For Workday standard reporting: Activated ARR is the canonical default.

---

## §8. The "growth ARR" decomposition (CFO-facing)

For board reporting, ARR growth is decomposed:

```
Y/Y ARR growth ($) = END_ARR (current year) - END_ARR (prior year)
                   = NEW_LOGO_y + EXPANSION_y - CHURN_y - CONTRACTION_y + SKU_CHANGE_y
                     (where _y = sum of all 4 quarters of fiscal year)
```

Quality-of-growth metrics:
- **% growth from new logo** (vs from existing): `NEW_LOGO / total_growth`
- **% expansion-driven growth**: `EXPANSION / (NEW_LOGO + EXPANSION)`
- **Net new logo ARR**: `NEW_LOGO - CHURN` (true new business)

Canonical view: `FINANCE_PROD.DATA_PRODUCTS.ARR_GROWTH_DECOMPOSITION_DASH`.

---

## §9. Quality / governance rules

Every metric in production MUST:

1. **Be derived from `FINANCE_LINE_ANALYTICS`** (or its upstream `stg_em_int_arr_line_base`) — never re-implement category logic
2. **Specify currency variant** in column name (`*_usd_current`, `*_usd_hist`, `*_usd_actual`)
3. **Filter `as_was_date`** explicitly (never default to all rows × all dates)
4. **Pass the reconciliation check**: `BEGIN_ARR + Δs = END_ARR` to within <$1 variance
5. **Be tested**: `dbt test` includes unique + not_null on PK, plus business-rule `expression_is_true` tests for category sums
6. **Be documented** in YAML: grain, currency, period, source-of-truth lineage
7. **Be classified for SOX**: tag with `meta.sox: true` if it feeds public disclosure

Anti-patterns to reject in code review:
- ❌ Re-deriving ARR from raw `APTTUS__AGREEMENTLINEITEM__C` (use FINANCE_LINE_ANALYTICS)
- ❌ Re-implementing SSR categorization (use SSR_AGREEMENT_RELATIONSHIP)
- ❌ Mixing currency variants in a sum
- ❌ Hardcoding FY boundaries
- ❌ Skipping `as_was_date` filter

---

## §10. Pitfalls + edge cases

### Mid-term amendments

When a contract is amended mid-term (e.g., added seats), the **new ALI rows** carry `SKU_ADDED_VIA_AMENDMENT__C = TRUE`. ARR delta is calculated only from the amendment date forward.

### Backdated contracts

If a contract is "signed" with an `effective_date` in the past (rare but happens for partner conversion), the ARR backfill must respect SOX rules — never silently rewrite a closed quarter. Talk to Finance Ops.

### Currency revaluation events

When the FX rate moves significantly (e.g., +5% USD strength), `USD_CURRENT` views can show a "fake" ARR change. Always include a "currency neutral" view (`USD_HIST`) alongside `USD_CURRENT` for executive reporting.

### Acquisition baseline

Newly-acquired customer base (Adaptive, Scout, Peakon, VNDLY) has ARR baselined at acquisition date — no retroactive history. Use `LKP_ACQUISITIONS` to filter or annotate.

### Partner double-count

Partner-channel deals: never sum direct + partner without filtering. Use `get_partner_reporting()` macro.

### Pilot contracts

Short pilots (1-3 months) annualized to ARR can artificially inflate (a $50k pilot = $100k+ "ARR"). Policy: pilots flagged `is_pilot = TRUE` excluded from canonical ARR unless converted to full contract.

---

## §11. Glossary

| Term | Definition |
|---|---|
| ALI | Agreement Line Item (canonical grain) |
| ARR | Annual Recurring Revenue |
| ACV | Annual Contract Value |
| TCV | Total Contract Value |
| GRR | Gross Retention Rate (excl. expansion) |
| NRR | Net Retention Rate (incl. expansion) |
| NDR | Net Dollar Retention (= NRR) |
| LRR | Logo Retention Rate |
| CARR | Committed ARR (incl. signed-but-not-active) |
| iARR | Implied ARR (usage-based, annualized run-rate) |
| SSR | Supersede & Replace (renewal mechanism) |
| FY | Fiscal Year (Workday: Feb 1 - Jan 31) |
| as_was_date | Snapshot date — "what was true on this date" |
| Bookings | Contract value at signing (ACV-derived) |
| Billings | Amount invoiced to customer (Zuora) |
| Revenue | GAAP-recognized revenue (Workday FM) |
| MRR | Monthly Recurring Revenue (= ARR / 12) — rarely used at Workday |

---

## §12. Cross-references

- `subscription-business-model.md` — business context for these metrics
- `platform-architecture.md` — where the data lives
- `domain-finance-billing.md` — billing + rev rec context
- `enterprise-data-products-catalog.md` — published data products
- `bi-semantic-consumption.md` — how metrics are exposed via semantic layer + Sigma
- `enterprise-metrics-finance-architect` skill — finance-architect deep dive
- `finance-functional-analytics` skill — query patterns for finance metrics
