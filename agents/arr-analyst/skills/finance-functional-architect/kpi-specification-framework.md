# KPI Specification Framework

The formal template for documenting any business metric before it gets built.
No new model goes into prod without an approved KPI Spec.

This is the contract between business + engineering. Approved spec → engineering
builds; unapproved → engineering pushes back.

---

## §1. The KPI Spec template

```
═══════════════════════════════════════════════════════════════════════════════
KPI SPECIFICATION
═══════════════════════════════════════════════════════════════════════════════

METRIC NAME (canonical):           <e.g., "ARR — Net Dollar Retention, by Product L3">
METRIC NAME (display):              <e.g., "Product NDR">
METRIC CODE:                        <e.g., NDR_PRODUCT_L3>

VERSION:                            v1.0
STATUS:                             [Draft | In Review | Approved | Deprecated]
DATE:                               <YYYY-MM-DD>
APPROVED BY:                        <name + role + date>

───────────────────────────────────────────────────────────────────────────────
BUSINESS CONTEXT
───────────────────────────────────────────────────────────────────────────────

Business question this answers:
   "Are our customers expanding their use of [PRODUCT] over time?"

Business owner:                     <e.g., VP Product Marketing, Sara X>
Primary user audience:              <e.g., Product leadership, FP&A>
Decisions driven by this metric:
   - Product investment allocation
   - Cross-sell roadmap prioritization

───────────────────────────────────────────────────────────────────────────────
DEFINITION
───────────────────────────────────────────────────────────────────────────────

Plain English:
   For each product, the retention rate of revenue from customers who held
   that product at period start — measured as (begin + expansion - churn -
   contraction) / begin. Excludes new logos. Excludes pilots.

Formula (mathematical):
   NDR_product = (BEGIN_ARR_product + EXPANSION_product 
                  - CHURN_product - CONTRACTION_product) 
                 / BEGIN_ARR_product

Where:
   BEGIN_ARR_product   = SUM(arr) for accounts that held product at period start
   EXPANSION_product   = SUM(positive arr deltas) for same accounts
   CHURN_product       = SUM(arr lost from product termination)
   CONTRACTION_product = SUM(arr reductions on existing product lines)

───────────────────────────────────────────────────────────────────────────────
GRAIN
───────────────────────────────────────────────────────────────────────────────

Grain:                 One row per (product_code_l3, fiscal_quarter)
Primary key:           (product_code_l3, fiscal_quarter)
Granularity rationale: Product-level for roadmap decisions; quarterly for 
                       smoothing single-customer volatility.

───────────────────────────────────────────────────────────────────────────────
TIME PERIODICITY
───────────────────────────────────────────────────────────────────────────────

Periodicity:           Quarterly (computed at fiscal quarter close)
Refresh:               Within 24h of as_was_date snapshot landing
Historical:            Available back to FY15 (when our SCD2 history starts)
TTM variant:           Yes, computed as TTM_NDR_product (separate column)

───────────────────────────────────────────────────────────────────────────────
DIMENSIONS (sliceable)
───────────────────────────────────────────────────────────────────────────────

- product_code_l3      (primary slice)
- fiscal_quarter        (primary time)
- fiscal_year           (rollup time)
- segment              (Enterprise / Mid-Market / SMB)
- region               (NA / EMEA / APAC / LATAM)
- tenure_bucket        (0-12 mo / 12-24 / 24+ mo)

───────────────────────────────────────────────────────────────────────────────
CURRENCY
───────────────────────────────────────────────────────────────────────────────

Variant:               USD_HIST (FX locked at as_was_date)
Rationale:             Period-over-period comparability — USD_CURRENT would
                       create false retention swings from FX moves.

───────────────────────────────────────────────────────────────────────────────
INCLUSION / EXCLUSION
───────────────────────────────────────────────────────────────────────────────

INCLUSIONS:
   - Active agreements (status = Activated)
   - All product families
   - All regions
   - All segments
   - Partner-channel and direct-channel deals

EXCLUSIONS:
   - Pilots (is_arr_eligible = FALSE)
   - One-time fees / professional services
   - Internal accounts
   - Sandbox / test accounts

GREY AREA (decision needed before approval):
   - Acquired customer base (currently EXCLUDED; revisit decision)

───────────────────────────────────────────────────────────────────────────────
SOURCE OF TRUTH
───────────────────────────────────────────────────────────────────────────────

Canonical model:        FINANCE_PROD.AGGREGATIONS.ARR_PRODUCT_CATEGORIES
Materialization:        Table (incremental merge)
Refresh job:            dbt Cloud job "Finance Q-Close Refresh"
SLA freshness:          Within 4 hours of upstream completion

Lineage:
   BASE_PROD.SALESFORCE.APTTUS__AGREEMENTLINEITEM__C
   → BASE_PROD.SALESFORCE_SCD2.APTTUS__AGREEMENTLINEITEM__C
   → stg_em_agreement_line_item_scd2
   → int_em_arr_line_base (categorization)
   → FINANCE_LINE_ANALYTICS (canonical fact)
   → ARR_PRODUCT_CATEGORIES (rollup)
   → THIS METRIC (NDR_PRODUCT_L3)

───────────────────────────────────────────────────────────────────────────────
RECONCILIATION
───────────────────────────────────────────────────────────────────────────────

Reconcile against:     ARR walk balance at total
   Validation: SUM(ndr_product × begin_arr_product) ≈ TOTAL_NDR × TOTAL_BEGIN_ARR
   Tolerance: ± 0.1%

Reconcile against:     Investor-reported NDR
   Validation: Aggregated product NDR ≈ overall company NDR (after weighting)
   Tolerance: ± 0.5%

───────────────────────────────────────────────────────────────────────────────
TIER & GOVERNANCE
───────────────────────────────────────────────────────────────────────────────

SOX Tier:              Tier 2 (investor-facing aggregation)
Change approval:       Required from: Finance Controller + Investor Relations
Audit logging:         Required for changes
Restatement:           SOX-approved process required

───────────────────────────────────────────────────────────────────────────────
CONSUMERS
───────────────────────────────────────────────────────────────────────────────

Dashboard consumers:
   - Sigma workbook: "Product NDR Quarterly Review" (owner: Sara X)
   - Sigma workbook: "Investor Earnings Prep" (owner: IR team)

Downstream model consumers:
   - eda-dbt-semantic-layer: metric "ProductNDR" in MetricFlow
   - Reverse ETL: pushed to Hightouch → SFDC custom field "Account NDR"

Notification list (on schema change):
   - [REDACTED_EMAIL]
   - [REDACTED_EMAIL]
   - [REDACTED_EMAIL]

───────────────────────────────────────────────────────────────────────────────
ACCEPTANCE CRITERIA (for build sign-off)
───────────────────────────────────────────────────────────────────────────────

[ ] dbt tests pass: unique(product_code_l3, fiscal_quarter) + not_null on NDR
[ ] Reconciliation passes: < 0.1% variance vs ARR walk
[ ] Historical accuracy: FY24 numbers match prior published numbers (± 0.5%)
[ ] Performance: dashboard loads < 5 sec
[ ] Documentation: KPI Spec published in catalog
[ ] User training: 30-min walkthrough delivered to product team
[ ] Access: Sigma access granted to product-mktg, ir, fp-analytics groups

───────────────────────────────────────────────────────────────────────────────
CHANGE LOG
───────────────────────────────────────────────────────────────────────────────

v1.0 (2026-03-01): Initial spec, approved by Controller + IR
v1.1 (2026-05-15): Clarified acquired-customer-base exclusion

───────────────────────────────────────────────────────────────────────────────
SIGN-OFFS
───────────────────────────────────────────────────────────────────────────────

Business owner:        Sara X, VP Product Marketing       [signed 2026-03-15]
Finance Controller:    Mike Y, Controller                  [signed 2026-03-18]
Investor Relations:    Lisa Z, Director IR                 [signed 2026-03-19]
Data Engineering:      Pat Q, Sr DE Manager                [signed 2026-03-22]
Functional Architect:  [You]                               [signed 2026-03-22]
```

---

## §2. The simplified spec (for non-SOX metrics)

For operational metrics (SOX Tier 3), the spec can be shorter:

```
METRIC NAME:           Marketing-Sourced Pipeline Coverage
BUSINESS DEFINITION:   Open pipeline with lead_source IN ('Marketing-MQL', 'Marketing-Event')
                       divided by remaining quarter quota
FORMULA:               SUM(open_amount) / (quota - closed_won)
GRAIN:                 (fiscal_quarter)
CURRENCY:              USD_CURRENT
SOURCE OF TRUTH:       SALES_PROD.AGGREGATIONS.PIPELINE_COVERAGE_DASH
REFRESH:               Daily
SOX TIER:              3 (operational)
OWNER:                 CMO Office
CONSUMERS:             Marketing leadership dashboard
ACCEPTANCE:            Reconciles to overall pipeline coverage; deployed to Sigma
```

Minimum viable spec — but every field must be present.

---

## §3. The "what makes a good spec" checklist

Before submitting a spec for review, check:

- [ ] **Name is unambiguous** — someone reading the name knows what it is
- [ ] **Formula is precise** — math is rigorous, no English-language hedging
- [ ] **Grain is explicit** — "one row per X" stated clearly
- [ ] **Currency is named** — USD_CURRENT / USD_HIST / USD_ACTUAL
- [ ] **Period is named** — quarterly / monthly / TTM
- [ ] **Filters are listed** — inclusions + exclusions, no implicit assumptions
- [ ] **Source of truth is a real model path** — canonical model identified
- [ ] **Reconciliation is concrete** — "ties to X within Y tolerance"
- [ ] **Acceptance criteria are testable** — each criterion can be objectively passed/failed
- [ ] **SOX tier is classified** — 1 / 2 / 3
- [ ] **Owner is named** — single accountable business person
- [ ] **Consumers are listed** — who uses it
- [ ] **Sign-offs are captured** — actual approvals from named people

Specs failing this checklist get returned with comments.

---

## §4. The discovery questions per spec section

### To populate "Business Context":
- "What business question does this answer?"
- "What decision will be made based on this metric?"
- "Who in the company looks at this regularly?"
- "Is there a parent OKR or KR this rolls up to?"

### To populate "Definition":
- "How do you describe this in plain English?"
- "What's the math?"
- "Walk me through how you calculate this today (if at all)."

### To populate "Grain":
- "Per what — per account? Per product? Per quarter?"
- "What's the level of detail needed for your decisions?"
- "Can you slice this by other dimensions?"

### To populate "Time Periodicity":
- "How often do you look at this?"
- "Do you need rolling / trailing variants?"
- "How far back do you need history?"

### To populate "Currency":
- "Are you reporting to investors? (→ USD_HIST)"
- "Are you operating real-time? (→ USD_CURRENT)"
- "Local currency for any reason? (→ USD_ACTUAL)"

### To populate "Inclusion/Exclusion":
- "Should pilots count?"
- "Should partner deals count?"
- "Geography exclusions?"
- "Internal accounts excluded?"

### To populate "Source of Truth":
- "Does this exist anywhere today? Where?"
- "If it exists in a spreadsheet, where do those numbers come from?"
- "What's the master record vs the derived view?"

### To populate "Reconciliation":
- "What other number should this tie to?"
- "How close is 'close enough' — exact? 1%? 5%?"
- "What's a known difference (e.g., timing) that we should expect?"

### To populate "SOX Tier":
- "Is this reported externally?"
- "Is this in the management discussion / earnings?"
- "Is this used in financial statements?"

### To populate "Consumers":
- "Who else uses this besides you?"
- "What dashboard / report does this go to?"
- "Does anyone build models on top of this?"

### To populate "Acceptance Criteria":
- "How will you know this is right?"
- "What's the SLA expectation — how fresh, how fast?"
- "What's the success criterion you'll sign off on?"

---

## §5. The spec review process

1. **Draft created** (by you, post-discovery)
2. **Stakeholder review meeting** (30-60 min):
   - Walk through the spec
   - Confirm + amend
   - Capture sign-off intent
3. **Engineering review** (sync with `enterprise-metrics-finance-architect`):
   - Confirm feasibility
   - Identify dependencies + effort
   - Adjust spec if needed (e.g., grain change for performance)
4. **SOX classification** (if tier 1/2): coordinate with Finance Controller
5. **Sign-off collection**: written approvals from each named stakeholder
6. **Spec published**: stored in catalog (Atlan / Confluence)
7. **Backlog entry created**: feeds into roadmap

Estimated time: 1-2 weeks for new specs.

---

## §6. The "spec is in production; needs amendment" flow

Spec changes mid-life are common. Process:

1. **Identify the change** (new filter, new dimension, formula tweak)
2. **Impact assessment**:
   - Does it change published numbers?
   - Do downstream models / dashboards break?
3. **If material**: convene metric council (`metric-governance-and-controls.md`)
4. **If minor**: stakeholder sign-off only
5. **Update spec** with version bump (v1.0 → v1.1)
6. **Document change** in change log
7. **Update model + tests**
8. **Notify consumers** of the change

---

## §7. The "every published metric in our system" catalog

Maintain a master list of all KPI Specs. Catalog includes:

| Metric Code | Name | Owner | Status | SOX Tier | Last Reviewed |
|---|---|---|---|---|---|
| ARR_TOTAL | Total ARR | Controller | Approved | 2 | 2026-01-15 |
| ARR_PRODUCT | ARR by Product | Product PM | Approved | 2 | 2026-02-01 |
| NDR_COMPANY | Total NDR | CFO | Approved | 2 | 2026-01-15 |
| NDR_PRODUCT_L3 | Product NDR | Product PM | Approved | 2 | 2026-03-22 |
| GRR_COMPANY | Total GRR | CFO | Approved | 2 | 2026-01-15 |
| LRR | Logo Retention | CS Leader | Approved | 3 | 2026-02-10 |
| BOOKING_ACV | Quarterly Booking ACV | CRO | Approved | 2 | 2025-12-01 |
| ... | ... | ... | ... | ... | ... |

Live document. Audit twice a year.

---

## §8. Anti-patterns (spec smells to watch for)

- ❌ "Formula: TBD" — spec is not done; don't approve
- ❌ "Owner: TBD" — must have a named owner
- ❌ "Grain: per various dimensions" — pick the canonical grain
- ❌ "Acceptance: looks reasonable" — must be objectively testable
- ❌ "Source: spreadsheet" — must be a controlled data path
- ❌ "Reconciliation: not applicable" — every metric reconciles to something
- ❌ "Currency: USD" — must specify which variant
- ❌ Skipping SOX tier classification

---

## §9. Cross-references

- `requirements-to-models-workflow.md` — end-to-end intake
- `product-owner-playbook.md` — backlog mechanics
- `metric-governance-and-controls.md` — council ops
- `finance-functional-analytics/categorization-framework.md` — for category-related specs
- `enterprise-metrics-finance-architect/metric-portfolio-architecture.md` — model architecture
