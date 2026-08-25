# Subscription Business Model — Workday EDH Context

Why the Workday data platform looks the way it does — the business model the
EDH supports. If you don't know how the business works, you'll model the data
wrong.

---

## §1. Workday is a subscription SaaS business

Core revenue model: customers pay an **annual subscription fee** for access to
Workday cloud applications (HCM, Financials, Adaptive, Spend, etc.). Contracts
are typically **multi-year** (2-5 years), with annual ramps and optional
renewal terms.

This makes Workday a "recurring revenue" business, and the entire analytics
platform exists to measure, forecast, and optimize the **recurring revenue
lifecycle**:

```
Acquire → Land → Expand → Retain → Renew
   │       │       │        │       │
   │       │       │        │       └─ Renewal (or churn)
   │       │       │        └─ Customer success keeps them happy
   │       │       └─ Sell more (cross-sell, upsell, expansion)
   │       └─ First contract signed (= "New Logo")
   └─ Marketing + Sales identify prospect
```

Every metric in the EDH ties to one of these lifecycle stages.

---

## §2. The "quote-to-cash" flow (and where data lives)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  STAGE                       SYSTEM                  PRIMARY OBJECT      │
├──────────────────────────────────────────────────────────────────────────┤
│  1. Lead                     Marketo / SFDC          Lead, Campaign      │
│  2. Lead → Account           SFDC                    Account (Reltio MDM)│
│  3. Opportunity created      SFDC                    Opportunity         │
│  4. Quote / Proposal built   SFDC + Apttus CPQ       Apttus_Proposal__c, │
│                                                       Apttus_ProposalLine │
│  5. Pricing approved         Apttus + Deal Desk      Approval_Process    │
│  6. Quote → Agreement        Apttus                  Apttus_Agreement__c,│
│     (booked)                                          AgreementLineItem  │
│  7. Order fulfillment        Workday Provisioning    Order, Activation  │
│  8. Billing schedule         Zuora                   Subscription,       │
│                                                       Invoice, Payment   │
│  9. Revenue recognition      Workday FM              GL Journal Entry    │
│  10. Customer success        Gainsight               CTAs, Health Score  │
│  11. Renewal motion          SFDC                    Opportunity (new!) │
│       (or churn)                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

At each stage, data lands in a system. EDH ingests via Fivetran → BASE_PROD →
domain DBs → metrics → BI.

---

## §3. The Apttus CPQ model (the heart of the data)

Apttus is the CPQ engine inside Salesforce. The object model that EVERYTHING
finance + GTM depends on:

```
Opportunity (1) ───┬─── (1..N) Apttus_Proposal__c            ← Quotes (one Opp can have many quotes)
                   │              │
                   │              └── (1..N) Apttus_ProposalLine__c  ← Line items in the quote
                   │
                   └─── (0..1) Apttus_Agreement__c                  ← When Quote becomes Contract
                                  │
                                  └── (1..N) AgreementLineItem__c   ← THE FINANCE GRAIN
                                  │              │
                                  │              └─ ARR, ACV, TCV computed here
                                  │
                                  └── (0..N) Apttus_Related_Agreement__c  ← SSR links (see §5)
```

**Key insight**: The Agreement Line Item (ALI) is the **canonical financial
grain**. Every ARR / ACV / TCV / NRR / GRR rollup ultimately aggregates ALIs.

Why this matters: many naive data models try to compute ARR from Opportunity
or from Proposal. Both are WRONG:
- Opportunity has `Amount` — but it's the salesperson's estimate, not signed
- Proposal has line items — but only the **primary** quote becomes an agreement; multiple proposals can exist per opp
- Agreement Line Item is what's actually **contracted** and signed

Canonical Snowflake locations:
- Raw: `BASE_PROD.SALESFORCE.APTTUS__AGREEMENTLINEITEM__C`
- SCD2 wrapper: `SALES_PROD.MANAGED.WD_AGREEMENT_LINE_SCD2`
- Enriched (joined w/ product + account): `FINANCE_INT_PROD.STAGE.stg_em_int_agree_enriched`
- Canonical metric grain: `FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS`

---

## §4. The "as_was" pattern — point-in-time accounting

SCD2 captures historical state, but finance needs **as-of-date** snapshots.
The `as_was_date` pattern:

- `FINANCE_LINE_ANALYTICS` has one row per `(agreement_line_item_id, as_was_date)`
- `as_was_date` represents "what was true on this date"
- Common as_was_dates: end of each fiscal month (`2026-02-06`, `2026-05-06`, etc.)
- Snapshots are built incrementally; old snapshots are immutable (closed quarters never change)

Why this matters:
- **Quarterly reporting** uses fixed `as_was_date` (e.g., `2026-04-30` for Q1 close)
- **Trend dashboards** unpack multiple `as_was_date`s
- **Restatement** (rare): change to historical snapshot requires SOX approval

Anti-pattern: querying `FINANCE_LINE_ANALYTICS` without filtering `as_was_date` — you'll get N × dates × ALIs of rows.

---

## §5. SSR (Supersede & Replace) — the renewal trap

When a customer renews / amends, the old agreement is **superseded** by a new one. The two are linked via `Apttus_Related_Agreement__c`.

**Wrong** interpretation (what naive systems do):
```
Old agreement: ARR_old = $100k (status = Superseded) → looks like CHURN
New agreement: ARR_new = $110k (new contract)        → looks like NEW LOGO
Net effect computed: -100k + 110k = +10k
```

This DOUBLE-COUNTS as both churn and new logo. Wrong.

**Right** interpretation (SSR-aware):
```
Customer has continuous service → this is a RENEWAL with $10k expansion
Net effect categorized as: EXPANSION_ARR = $10k
                           (no churn, no new logo)
```

The canonical resolver: `FINANCE_PROD.MANAGED.SSR_AGREEMENT_RELATIONSHIP`
- Maps `old_agreement_id` ↔ `new_agreement_id` ↔ `ssr_category`
- Categories: `FLAT_RENEWAL`, `EXPANSION`, `CONTRACTION`, `MIGRATION` (e.g., HCM v1 → HCM v2)
- Built by `bt_ssr_agreement_relationship` in `eda-dbt-em`

Every ARR category model in `FINANCE_PROD.AGGREGATIONS.ARR_*` must use this resolver. Never manually classify SSR.

---

## §6. The 7+ ARR view families

Built from `FINANCE_LINE_ANALYTICS`, aggregated multiple ways:

| View family | Grain | Use case |
|---|---|---|
| `ARR_LINE_CATEGORIES` | ALI × as_was_date | Most granular; auditing |
| `ARR_PRODUCT_CATEGORIES` | Product (L3/L4/L5) × as_was_date | Product-level retention |
| `ARR_SKU_CATEGORIES` | SKU × as_was_date | SKU-level analysis |
| `ARR_ACCOUNT_CATEGORIES` | Account × as_was_date | Account-level NDR |
| `ARR_REGION_SEGMENT_CATEGORIES` | Region × Segment × as_was_date | GTM territory |
| `ARR_INDUSTRY_CATEGORIES` | Industry × as_was_date | Vertical analysis |
| `ARR_STRATEGIC_PARTNER_CATEGORIES` | Partner-flag × as_was_date | Partner-channel ARR |

Each aggregates ARR into the canonical categories (BEGIN_ARR, NEW_LOGO, EXPANSION, CONTRACTION, CHURN, SKU_CHANGE, VOLUME, PRICE, MIX, END_ARR). Sum within each category to derive NDR / GRR.

---

## §7. The category waterfall (canonical)

```
BEGIN_ARR  (start of period — typically end-of-prior-quarter snapshot)
+  NEW_LOGO        ← brand-new customers
+  EXPANSION       ← existing customers, more revenue
-  CONTRACTION     ← existing customers, less revenue (downsell)
-  CHURN           ← lost customers (terminated, no renewal)
±  SKU_CHANGE     ← migrated to different SKU
±  VOLUME         ← seat/usage change
±  PRICE          ← list-price changes
±  MIX            ← currency / region rebalance
= END_ARR  (end of period)
```

This is the canonical "ARR walk" reported to executives. The categories MUST sum to a clean walk (BEGIN_ARR + Δs = END_ARR with <$1 variance).

For formulas + dbt mechanics: `finance-metrics-canonical.md`.

---

## §8. Bookings → Billings → Revenue (three different numbers)

A common source of business confusion. They're all "revenue-ish" but measure different things:

| Concept | Definition | System | Use case |
|---|---|---|---|
| **Booking** | Total contract value at signing | SFDC + Apttus | Sales attainment, quota |
| **Billing** | Amount invoiced to customer | Zuora | A/R, cash forecast |
| **Revenue (recognized)** | GAAP-recognized revenue (over service period) | Workday FM | Public reporting |

Example: 3-year contract for $300k signed in March 2026.
- **Bookings (FY26 Q4)**: $300k (the full TCV)
- **Billings (FY26)**: $100k (annual invoice cycle)
- **Recognized Revenue (FY26)**: ratable over service period (e.g., $25k if service starts April 1)

EDH supports all three:
- Bookings → `eda-dbt-em` (FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS)
- Billings → Zuora-sourced models (lighter coverage, mostly raw)
- Revenue → Workday FM-sourced models (lightest coverage; SOX-controlled)

Most public-facing metrics use **bookings** or **ARR** (not revenue). ARR is forward-looking; Revenue is GAAP-recognized.

---

## §9. The customer lifecycle (CX context)

Once a customer is signed, the CX domain takes over:

```
Onboarding ────→ Adoption ────→ Renewal/Expansion ────→ (Renewed) or (Churned)
   │                │                  │                            │
   │                │                  │                            │
   ▼                ▼                  ▼                            ▼
PRODUCT_       ACTIVATION_      LOYALTY_                     SSR or Churn
IMPLEMENTATION USAGE_ADOPTION   ADVOCACY                    (back to finance)
```

CX data products feed:
- **Customer health score** — composite of usage, NPS, support tickets, exec engagement
- **Churn risk score** — ML model predicting renewal probability
- **CSM playbook triggers** — Gainsight CTAs based on health signals
- **NPS / CSAT** — voice of customer (Medallia)
- **Time-to-value** — implementation milestones (PSO)

These feed back into the renewal motion (CSM works to retain at-risk accounts) and into finance forecasting (churn risk → renewal forecast adjustment).

For detail: `domain-cx-customer-success.md`.

---

## §10. The fiscal calendar (Workday-specific)

Workday's fiscal year is **Feb 1 → Jan 31**:

| Quarter | Months | FY26 dates |
|---|---|---|
| Q1 | Feb-Apr | Feb 1, 2025 – Apr 30, 2025 |
| Q2 | May-Jul | May 1, 2025 – Jul 31, 2025 |
| Q3 | Aug-Oct | Aug 1, 2025 – Oct 31, 2025 |
| Q4 | Nov-Jan | Nov 1, 2025 – Jan 31, 2026 |

Common period-end "as_was_date" snapshots:
- Q1 close: `2025-04-30` snapshot used as `2025-05-06` (week-end aligned)
- Q2 close: `2025-08-06` snapshot
- Q3 close: `2025-11-06` snapshot
- Q4 close: `2026-02-06` snapshot

Never hardcode. Use macros from `eda-dbt-common`:
- `get_fiscal_quarter(date_col)` → 'FY26Q1'
- `get_fiscal_year(date_col)` → 'FY26'
- `get_fiscal_attributes(date_col)` → struct with year, quarter, month, week_end

Source of truth: `FOUNDATIONAL_ASSETS_PROD.MANAGED.WD_FISCAL_CALENDAR`.

---

## §11. Partners + channel + indirect bookings

A material % of Workday revenue flows through **strategic partners** (system integrators, channel partners, co-sell):

- Direct deal: Workday sells to customer
- Indirect deal: Partner resells / co-sells with revenue share

The agreement reflects both via:
- `IS_PARTNER_DEAL__C` flag
- `PARTNER_ACCOUNT__C` lookup
- `PARTNER_REVENUE_SHARE__C` percentage

Critical: never double-count. Use `get_partner_reporting()` macro which canonically attributes ARR to either Workday-direct or partner-channel.

Canonical model: `FINANCE_PROD.MANAGED.LKP_STRATEGIC_PARTNERS` (via Google Sheets controlled by Partner Operations).

---

## §12. Acquisitions

When Workday acquires a company (recent: Adaptive Insights, Scout RFP, Peakon, VNDLY), the acquired customer base needs to be:
- Mapped into Workday Account hierarchy (Reltio MDM)
- Re-baselined into Workday product hierarchy
- Have ARR contributions counted "from acquisition date forward" (no retroactive history)

Lookup tables (Google Sheets controlled):
- `LKP_ACQUISITIONS` — acquired-company → Workday parent account mapping
- `LKP_ACQUISITION_PRODUCT_MAP` — acquired product SKU → Workday product hierarchy

Canonical view: `FOUNDATIONAL_ASSETS_PROD.MANAGED.VW_REF_ACQUISITIONS`.

---

## §13. Currency complexity

Workday operates globally. Three currency variants per metric:

| Variant | Conversion logic | Use case |
|---|---|---|
| `USD_CURRENT` | Latest published FX rate | Live dashboards, trending |
| `USD_HIST` | FX rate at transaction date | Period-over-period comparison (apples-to-apples) |
| `USD_ACTUAL` | NO conversion — raw transaction currency | Billing / invoicing / cash |

Source: `BASE_PROD.SALESFORCE.DATEDCONVERSIONRATE` → `FOUNDATIONAL_ASSETS_PROD.MANAGED.WD_FX_RATES` (a curated view).

Currency conversion macros:
- `convert_to_usd_current(amount_col, currency_col)`
- `convert_to_usd_hist(amount_col, currency_col, transaction_date_col)`
- `as_actual(amount_col)` (passthrough)

Every metric column in `FINANCE_LINE_ANALYTICS` exists in 3 variants:
- `arr_usd_current`, `arr_usd_hist`, `arr_usd_actual`
- `acv_usd_current`, `acv_usd_hist`, `acv_usd_actual`
- (and so on)

Anti-pattern: mixing variants in the same rollup. ALWAYS pick one variant per analysis.

---

## §14. Deal motions — pure new vs net new vs cross-sell vs upsell

Sales taxonomy (used in pipeline + booking analytics):

| Motion | Definition | ARR category |
|---|---|---|
| **Pure new logo** | First contract for a new customer (no prior agreement) | NEW_LOGO |
| **Net new logo** | Customer with prior agreement, but on a different product line | NEW_LOGO (sub-categorized) |
| **Cross-sell** | Existing customer, additional product family | EXPANSION (sub-categorized) |
| **Upsell** | Existing customer, more seats / volume on existing product | EXPANSION (sub-categorized) |
| **Renewal** | Same product, same customer, renewal term | FLAT_RENEWAL or EXPANSION (via SSR) |
| **Migration** | Existing customer, version upgrade (HCM v1 → v2) | SKU_CHANGE |
| **Downsell** | Existing customer, fewer seats / less volume | CONTRACTION |
| **Churn** | Customer terminates, no replacement | CHURN |

These are sales-team terms; finance categories are the data-modeled equivalents. Sales attainment dashboards use motion-level views; finance dashboards use ARR-category views.

---

## §15. Why this architecture exists (rationale)

Given the business model above, the platform exists to:

1. **Measure ARR + components weekly** (CFO + CEO dashboards) — drove the `FINANCE_LINE_ANALYTICS` + 7 ARR view family
2. **Predict renewal risk** (CSM + CRO) — drove the CX domain
3. **Attribute marketing to revenue** (CMO) — drove Bizible + multi-touch attribution
4. **Forecast pipeline → bookings → revenue** (FP&A) — drove Clari ingestion + pipeline models
5. **Close the quarter cleanly** (Finance, SOX) — drove `as_was_date` snapshots + immutability
6. **Govern data products** (Data Governance) — drove the mesh + contracts + Catalog

If you understand these 6 needs, every model name + grain + schema decision makes sense.

---

## §16. The "single source of truth" rule

For every business question, ONE model should be the canonical answer:

| Question | Canonical source |
|---|---|
| What is total ARR? | `FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS` (sum `arr_usd_current` for latest `as_was_date`) |
| What is ARR by product? | `FINANCE_PROD.AGGREGATIONS.ARR_PRODUCT_CATEGORIES` |
| Is this opp a renewal or new? | `FINANCE_PROD.MANAGED.SSR_AGREEMENT_RELATIONSHIP` |
| Who owns this account? | `SALES_PROD.MANAGED.WD_ACCOUNT_SCD2` (current row: `is_current = TRUE`) |
| What's the latest FX rate? | `FOUNDATIONAL_ASSETS_PROD.MANAGED.WD_FX_RATES` |
| Is this account a marketing-sourced lead? | `MARKETING_PROD.AGGREGATIONS.MARKETING_SOURCED_PIPELINE` |
| What's customer XYZ's health score? | `LOYALTY_ADVOCACY_PROD.MANAGED.CUSTOMER_HEALTH_SCORE` |
| When does this contract renew? | `SALES_PROD.MANAGED.WD_AGREEMENT_SCD2.term_end_date` |

If the question doesn't have a canonical answer, it's a request for a new data product (see `enterprise-data-products-catalog.md`).

---

## See also

- `finance-metrics-canonical.md` — formal metric definitions
- `domain-finance-billing.md` — Zuora + Workday FM
- `domain-sales-gtm.md` — pipeline + CPQ
- `domain-cx-customer-success.md` — health + churn
- `salesforce-bsa-agreements-contracts` skill — Apttus deep dive
- `salesforce-bsa-close` skill — opportunity close mechanics
- `salesforce-bsa-finance-analyst` skill — finance-side SFDC objects
