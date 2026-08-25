# Domain — Finance & Billing

Owner: Finance Analytics Engineering team.
Project: `eda-dbt-em` (writes to `FINANCE_PROD` + `FINANCE_INT_PROD`).
Primary sources: Salesforce (Apttus CPQ), Zuora (billing), Workday Financial Management (GL), Workday Adaptive Planning (FP&A).

---

## §1. What this domain owns

| Area | Examples |
|---|---|
| ARR / ACV / TCV | The canonical metric grain — see `finance-metrics-canonical.md` |
| Retention metrics | NRR / GRR / NDR / LRR — at product, SKU, account, region |
| ARR waterfall | NEW_LOGO, EXPANSION, CONTRACTION, CHURN, SKU_CHANGE, etc. |
| Agreement lifecycle | SCD2 history of Agreement + AgreementLineItem |
| Billings (Zuora) | Invoice events, payment schedules, deferred revenue |
| Revenue recognition | GAAP-recognized revenue (Workday FM-sourced) |
| Currency conversion | DatedConversionRate + 3 variants (USD_CURRENT, USD_HIST, USD_ACTUAL) |
| SSR resolution | Old agreement ↔ new agreement renewal mapping |
| Product hierarchy | Product → SKU → Family + acquired-product re-baselining |
| Forecasting inputs | Renewal-risk-[REDACTED] ARR for FP&A scenarios |
| Period close | Quarter-end snapshots (immutable post-close) |

What this domain does NOT own:
- ❌ Pipeline / unsold opportunities — that's `domain-sales-gtm.md`
- ❌ Marketing attribution / lead source — that's `domain-marketing.md`
- ❌ Customer health / churn risk score — that's `eda-dbt-cx`
- ❌ Product usage analytics — that's `eda-dbt-cx`

---

## §2. Source systems

| System | Connector | Refresh | Primary tables |
|---|---|---|---|
| **Salesforce (Apttus CPQ)** | Fivetran | 1 hr CDC | `APTTUS__APTS_AGREEMENT__C`, `APTTUS__AGREEMENTLINEITEM__C`, `APTTUS__APTS_RELATED_AGREEMENT__C`, `APTTUS_PROPOSAL__PROPOSAL__C`, `APTTUS_PROPOSAL__PROPOSAL_LINE_ITEM__C`, `OPPORTUNITY`, `ACCOUNT`, `DATEDCONVERSIONRATE`, `CURRENCYTYPE` |
| **Salesforce (Apttus billing)** | Fivetran | 1 hr CDC | `APTS_INVOICE_DETAIL__C`, `PAYMENT_SCHEDULE__C` |
| **Zuora** | Fivetran | 15 min CDC | `SUBSCRIPTION`, `RATE_PLAN`, `INVOICE`, `INVOICE_ITEM`, `PAYMENT`, `AMENDMENT`, `BILL_RUN` |
| **Workday FM** | Fivetran | Daily | `JOURNAL_ENTRY`, `JOURNAL_LINE`, `GL_ACCOUNT`, `COMPANY`, `BUSINESS_UNIT` |
| **Workday Adaptive Planning** | Fivetran / custom | Daily | Plan / Forecast / Actual snapshots |
| **Google Sheets** | Fivetran | 15 min | `REF_FIN_CUSTOMIZED_DATA`, `REF_PRODUCT_HIERARCHY`, `REF_ACQUISITION_MAPPING`, `REF_FX_OVERRIDE`, `REF_TCV_CORRECTION` |

---

## §3. The canonical model lineage (ARR / ACV / TCV)

```
BASE_PROD.SALESFORCE.APTTUS__AGREEMENTLINEITEM__C
    │ (raw)
    ▼
eda-dbt-base: base_apttus__agreementlineitem__c
    │ (typed wrapper)
    ▼
eda-dbt-gtm: WD_AGREEMENT_LINE_SCD2 (in SALES_PROD.MANAGED)
    │ (SCD2 dim, contracted + public)
    ▼
eda-dbt-em (cross-project ref to gtm):
    stg_em_agreement_line_item_scd2 (in FINANCE_INT_PROD.STAGE)
    │ (em-local view of the SCD2 dim with finance-specific filtering)
    │
    │ joins with:
    │   - stg_em_account_scd2 (account context)
    │   - stg_em_opportunity_scd2 (opp context, deal motion)
    │   - stg_em_proposal_scd2 + stg_em_proposal_line_scd2 (quote context)
    │   - stg_em_apttus_related_agreement_scd2 (SSR linking)
    │   - stg_em_lkp_wd_fin_tcv_correction (TCV correction overrides)
    │   - stg_em_int_strategic_program_flag (program tagging)
    │   - stg_em_int_acquisition_mapping (acquired product rebasing)
    │   - vw_ref_product_hierarchy (product L3/L4/L5)
    ▼
stg_em_int_agree_enriched (in FINANCE_INT_PROD.STAGE)
    │ (enriched line + agreement context, one row per ALI per as_was_date)
    ▼
stg_em_int_arr_line_base (in FINANCE_INT_PROD.STAGE)
    │ (applies get_arr_line_base_fn UDTF)
    │  - Categorizes each ALI as NEW_LOGO / EXPANSION / CONTRACTION / CHURN / etc.
    │  - Compares current as_was_date to prior as_was_date for delta
    │  - Resolves SSR via SSR_AGREEMENT_RELATIONSHIP
    │  - Applies currency conversions (3 variants)
    ▼
FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS
    │ (canonical fact: ARR / ACV / TCV at ALI × as_was_date grain)
    │ Incremental table (merge by (agreement_line_item_id, as_was_date))
    │ Partitioned-style clustered by as_was_date
    ▼
    ├── FINANCE_PROD.AGGREGATIONS.ARR_LINE_CATEGORIES         (rollup at line × category)
    ├── FINANCE_PROD.AGGREGATIONS.ARR_PRODUCT_CATEGORIES      (rollup by product L3/L4/L5)
    ├── FINANCE_PROD.AGGREGATIONS.ARR_SKU_CATEGORIES          (rollup by SKU)
    ├── FINANCE_PROD.AGGREGATIONS.ARR_ACCOUNT_CATEGORIES      (rollup by account)
    ├── FINANCE_PROD.AGGREGATIONS.ARR_REGION_SEGMENT_CATEGORIES
    ├── FINANCE_PROD.AGGREGATIONS.ARR_INDUSTRY_CATEGORIES
    └── FINANCE_PROD.AGGREGATIONS.ARR_STRATEGIC_PARTNER_CATEGORIES
    ▼
FINANCE_PROD.DATA_PRODUCTS.ARR_PRODUCT_NET_DOLLAR_RETENTION_DASH_V2
FINANCE_PROD.DATA_PRODUCTS.ARR_SKU_TRENDS_DASHBOARD
FINANCE_PROD.DATA_PRODUCTS.ARR_GROWTH_DECOMPOSITION_DASH
(etc.)
    ▼
[Sigma workbooks / executive dashboards]
```

For metric formulas: `finance-metrics-canonical.md`. For business context: `subscription-business-model.md`.

---

## §4. The Apttus agreement model in detail

### 4.1 Agreement (`APTTUS__APTS_AGREEMENT__C`)

The contract / agreement header.

Key fields:
| Field | Meaning |
|---|---|
| `NAME` | Agreement name (typically `ACCOUNT - PRODUCT - QUARTER`) |
| `APTTUS__STATUS_CATEGORY__C` | Lifecycle: `In Authoring` → `In Signatures` → `Activated` → `Amended` / `Renewed` / `Terminated` |
| `APTTUS__STATUS__C` | Sub-status within the category |
| `APTTUS__ACCOUNT__C` | Account ID |
| `APTTUS__RELATED_OPPORTUNITY__C` | Linked opportunity |
| `APTTUS__START_DATE__C` | Contract start |
| `APTTUS__END_DATE__C` | Contract end |
| `APTTUS__TOTAL_AGREEMENT_VALUE__C` | TCV (sum of all lines) |
| `CURRENCYISOCODE` | Local currency |
| `APTTUS__PARENT_AGREEMENT__C` | Parent agreement (for amendments / renewals) |

### 4.2 Agreement Line Item (`APTTUS__AGREEMENTLINEITEM__C`)

The financial grain. One row per contracted product line.

Key fields:
| Field | Meaning |
|---|---|
| `APTTUS__AGREEMENT__C` | Parent agreement ID |
| `APTTUS_CMCONFIG__LINESTATUS__C` | Line status (New / Amended / Renewed / Cancelled) |
| `APTTUS__QUANTITY__C` | Number of units (seats, etc.) |
| `APTTUS__PRODUCT_ID__C` | Product (links to Product2) |
| `APTTUS__NETPRICE__C` | Net price per unit |
| `TOTAL_FEES__C` | Total fees for this line (= TCV per line) |
| `ADJ_AL_TOTAL_FEES__C` | Adjusted total (post-corrections) |
| `ACV__C` | Annual contract value (year-1) |
| `TCV__C` | Total contract value (full term) |
| `SALES_ACV__C` | Sales-attributed ACV (for attainment) |
| `APTS_TERM_START_DATE__C` | Line start date |
| `APTS_TERM_END_DATE__C` | Line end date |
| `BILLINGFREQUENCY__C` | Billing frequency (Annual / Quarterly / Monthly) |
| `BILLINGRULE__C` | Billing rule (Bill in Advance / Bill in Arrears) |
| `SKU_ADDED_VIA_AMENDMENT__C` | TRUE if added via amendment |
| `AMENDED_QUANTITY__C` | Quantity delta for amendments |

### 4.3 Related Agreement (SSR linkage)

`APTTUS__APTS_RELATED_AGREEMENT__C` links related agreements:

```
related_agreement_id  | source_agreement_id | target_agreement_id | relationship_type
123                   | OLD_AGR_001         | NEW_AGR_002         | "Supersede"
124                   | NEW_AGR_002         | OLD_AGR_001         | "Renewed By"
```

Resolved via canonical view: `FINANCE_PROD.MANAGED.SSR_AGREEMENT_RELATIONSHIP`.

---

## §5. The TCV correction pattern

Sometimes the raw `TOTAL_FEES__C` in Apttus is wrong (data entry, currency mishap, contract amendment edge case). Finance Ops maintains a Google Sheet of corrections:

`BASE_PROD.GOOGLE_SHEETS.REF_TCV_CORRECTION`:
```
agreement_line_item_id | corrected_tcv_local_currency | corrected_tcv_usd | reason | corrected_by | corrected_date
```

Applied via `stg_em_lkp_wd_fin_tcv_correction` model. In `FINANCE_LINE_ANALYTICS`:

```sql
COALESCE(corrected_tcv_usd_current, raw_tcv_usd_current) AS tcv_usd_current
```

NEVER overwrite the raw value — always preserve both raw and corrected (for audit trail).

---

## §6. Currency conversion — the canonical pattern

Three variants for every monetary column:

### 6.1 USD_CURRENT

Apply latest published FX rate at query time.

```sql
amount_local
  * (
    SELECT conversion_rate FROM FOUNDATIONAL_ASSETS_PROD.MANAGED.WD_FX_RATES
    WHERE from_currency = local_currency
      AND to_currency = 'USD'
      AND effective_date = (
          SELECT MAX(effective_date) FROM ... WHERE effective_date <= CURRENT_DATE()
      )
  )
```

### 6.2 USD_HIST

Apply FX rate at transaction date.

```sql
amount_local
  * (
    SELECT conversion_rate FROM FOUNDATIONAL_ASSETS_PROD.MANAGED.WD_FX_RATES
    WHERE from_currency = local_currency
      AND to_currency = 'USD'
      AND effective_date <= agreement_signed_date
    ORDER BY effective_date DESC LIMIT 1
  )
```

### 6.3 USD_ACTUAL

No conversion. Raw local-currency value, surfaced as `_usd_actual` for naming consistency (the "USD_" prefix is a misnomer; treat as "transaction currency, no conversion").

```sql
amount_local AS amount_usd_actual
```

### 6.4 FX source

`BASE_PROD.SALESFORCE.DATEDCONVERSIONRATE` → `FOUNDATIONAL_ASSETS_PROD.MANAGED.WD_FX_RATES`

DatedConversionRate has effective-date ranges. Workday's standard Treasury process publishes monthly FX rates; daily-grained rates also available from `BASE_PROD.SALESFORCE.CURRENCY_DAILY_RATE` (custom object).

For period-end (quarter-close), Treasury locks an FX rate per currency pair. These locked rates are uploaded via `REF_FX_OVERRIDE` Google Sheet for period-close-locked calculations.

---

## §7. Product hierarchy (Workday product taxonomy)

Workday products are taxonomized hierarchically:

```
Product Family (e.g., "HCM")
  └── Product Code L3 (e.g., "Core HCM")
        └── Product Code L4 (e.g., "Talent")
              └── Product Code L5 (e.g., "Talent Optimization")
                    └── SKU (e.g., "HCM-TALENT-OPT-ENT")
```

Reference data:
- `BASE_PROD.GOOGLE_SHEETS.REF_PRODUCT_HIERARCHY` — controlled by Product Marketing
- `FOUNDATIONAL_ASSETS_PROD.MANAGED.VW_REF_PRODUCT_HIERARCHY` — canonical view

Used in:
- `ARR_PRODUCT_CATEGORIES` — rolled up to L3 / L4 / L5
- `ARR_SKU_CATEGORIES` — at SKU grain

Maintenance: when a new product launches, Product Marketing updates the Google Sheet → propagates to all dashboards via the next batch.

Acquired products: legacy SKUs from acquisitions (Adaptive, Scout, Peakon, VNDLY) need re-mapping to Workday hierarchy. Handled by `REF_ACQUISITION_MAPPING` Google Sheet → `stg_em_int_acquisition_mapping` model.

---

## §8. The fiscal calendar (canonical)

Workday FY = Feb 1 - Jan 31.

```
FY26 = Feb 1, 2025 - Jan 31, 2026
  FY26Q1 = Feb-Apr 2025
  FY26Q2 = May-Jul 2025
  FY26Q3 = Aug-Oct 2025
  FY26Q4 = Nov 2025-Jan 2026
```

Standard period-end snapshot dates (week-aligned to Fridays for `as_was_date`):
- Q1 close → `2025-04-30` snapshot → published as `2025-05-06` (next business day)
- Q2 close → `2025-08-06` snapshot
- Q3 close → `2025-11-06` snapshot
- Q4 close → `2026-02-06` snapshot

Source: `FOUNDATIONAL_ASSETS_PROD.MANAGED.WD_FISCAL_CALENDAR`.

Macros (in `eda-dbt-common`):
- `get_fiscal_quarter(date_col)` → 'FY26Q1'
- `get_fiscal_year(date_col)` → 'FY26'
- `get_fiscal_attributes(date_col)` → struct(year, quarter, month, period_end_date, week_ending_friday)

Never hardcode. Always use the macros.

---

## §9. The `as_was_date` pattern — period-in-time accounting

`FINANCE_LINE_ANALYTICS` has one row per (ALI × as_was_date). Common `as_was_date` values:
- Weekly snapshots (week-ending Friday) for live dashboards
- Period-end snapshots (Q1 close, Q2 close, ...) for executive reporting
- Mid-quarter checkpoints for FP&A

Snapshot policy:
- New snapshots added incrementally
- Existing snapshots are **immutable** — once `as_was_date < CURRENT_DATE() - 30 days`, no edits without SOX approval
- The current week's snapshot can be re-computed (within the week) for late-arriving data

Backfill mechanics:
- For historical reload (rare): `dbt run --vars '{"arr_refactor_as_was_date_list": [list of dates]}'`
- The `on-run-start` hook in `dbt_project.yml` will purge + reload listed dates
- DO NOT use for closed quarters; needs SOX sign-off

For deep mechanics, see `enterprise-metrics-finance-architect` skill.

---

## §10. Zuora — the billing data

Zuora handles subscription billing — separate from CPQ (which handles signing).

```
[Apttus Agreement (signed)]
        ↓ daily / weekly sync (BillingPlatform integration)
[Zuora Subscription created]
        ↓ generates
[Zuora Subscription + RatePlan + Charges]
        ↓ on bill run (cycle date)
[Zuora Invoice + InvoiceItem]
        ↓
[Zuora Payment + PaymentApplication]
```

Key Zuora tables in `BASE_PROD.ZUORA`:
- `SUBSCRIPTION` — top-level subscription record
- `RATE_PLAN` — pricing plan attached to subscription
- `RATE_PLAN_CHARGE` — individual charges (recurring, one-time, usage)
- `INVOICE` — issued invoice
- `INVOICE_ITEM` — line item on an invoice (links back to subscription charge)
- `PAYMENT` — payment received
- `AMENDMENT` — subscription amendment (added charges, changed term, etc.)

Workday's Zuora coverage in EDH: lightweight (mostly raw views + a few stage models for AR aging + cash forecast).

Linkage between Zuora and Apttus:
- `Zuora.Subscription.ExternalKey__c` ↔ `Apttus.Agreement.AgreementNumber__c`
- Joined in `FINANCE_INT_PROD.STAGE.stg_em_int_billing_to_agreement_link` for reconciliation

---

## §11. Workday Financial Management (GL)

Workday FM is the **GL system** — where revenue is officially recognized per GAAP.

Key tables in `BASE_PROD.WORKDAY_FINANCIAL_MANAGEMENT`:
- `JOURNAL_ENTRY` — header for journal entries
- `JOURNAL_LINE` — line-level GL postings
- `GL_ACCOUNT` — chart of accounts
- `COMPANY` / `BUSINESS_UNIT` — org hierarchy
- `BUDGET_CHECK` / `BUDGET_LINE` — budget data (also see Adaptive)

EDH coverage: very light. Revenue recognition data flows into:
- `FINANCE_INT_PROD.STAGE.stg_em_wfm_gl_journal_lines`
- `FINANCE_PROD.MANAGED.GL_REVENUE_RECOGNIZED` (used for matching ARR-derived revenue to GAAP)

SOX-controlled: anything that touches recognized revenue / public disclosure metrics must flow through `BASE_SOX_PROD` variant (separate Fivetran connector with stricter audit).

---

## §12. Adaptive Planning (FP&A)

Workday Adaptive is the **FP&A planning tool** — used for budget + forecast + scenario planning.

Key data:
- Plan / Forecast / Actual snapshots (per fiscal period × dimension)
- Variance analysis (Actual vs Plan)
- Scenarios (best case / worst case / base case)

EDH coverage: lightweight. Adaptive data feeds:
- `FINANCE_INT_PROD.STAGE.stg_em_adaptive_*`
- `FINANCE_PROD.MANAGED.PLAN_VS_ACTUAL` (variance analysis)

For executive reporting, FP&A team uses Adaptive directly; EDH provides supporting data only.

---

## §13. Revenue recognition — high-level

GAAP-compliant rev rec (ASC 606):
- Subscription revenue → recognized **ratably** over the service period
- Implementation / professional services → recognized at **completion** (or % completion)
- Usage-based → recognized **as consumed**
- One-time fees → recognized on **invoice date**

ARR is NOT revenue. ARR is annualized recurring contract value at a point in time. Revenue is what GAAP recognizes per period.

The relationship:
```
ARR-derived revenue (estimated) ≈ Revenue (GAAP-recognized)
  for clean, single-year subscriptions without amendments

For multi-year, ramped, amended contracts: estimates diverge significantly.
GAAP revenue is the ground truth for SEC reporting.
ARR is the ground truth for investor "growth" metrics.
```

Reconciliation view: `FINANCE_PROD.MANAGED.ARR_TO_REVENUE_RECONCILIATION` (variance < 2% target).

---

## §14. Period close mechanics

Quarterly close process (FP&A + Finance Ops + Analytics Engineering):

1. **Source freeze (T-2 days)**:
   - Salesforce admin freezes Apttus updates
   - Zuora bill run completes
   - Workday FM closes the period
2. **Data validation (T-1 day)**:
   - Validate `_fivetran_synced` timestamps on all source tables
   - Validate row counts vs prior quarter (anomaly detection)
   - Run `dbt test` across all finance models
3. **Snapshot generation (T-0)**:
   - Trigger period-end `as_was_date` snapshot
   - Apply quarter-end FX rate locks (from `REF_FX_OVERRIDE`)
   - Generate `FINANCE_LINE_ANALYTICS` for the close `as_was_date`
4. **Validation + sign-off**:
   - Reconciliation queries: ARR walk balances?
   - FP&A reviews + signs off
   - Snapshot locks (no further edits)
5. **Publication**:
   - Update all `DATA_PRODUCTS` views to point at the new snapshot
   - Refresh Sigma dashboards
   - Generate executive deck

Anti-pattern: rerunning a closed `as_was_date` snapshot. Requires SOX approval + executive sign-off. Don't.

---

## §15. SOX-compliant pipelines

A subset of pipelines is SOX-compliant (relevant to financial reporting):

| Tier | Definition | Examples |
|---|---|---|
| **SOX Tier 1** | Direct input to financial statements | GL data, Zuora revenue, Workday FM journals |
| **SOX Tier 2** | Used in management reporting / investor metrics | ARR, ACV, NRR, GRR |
| **SOX Tier 3** | Used in operational decisions only | Pipeline, marketing-sourced, etc. |

SOX Tier 1 + Tier 2 pipelines:
- Land in `BASE_SOX_PROD` (separate from `BASE_PROD`) — additional audit controls
- Have approval gates on every CI/CD deploy (CFO designate sign-off)
- Have audit logging on every read / write (Snowflake `ACCESS_HISTORY`)
- Have stricter retention (90+ days raw history, 7-year curated)
- Modifications require SOX approval workflow (Jira ticket → Compliance → Executive sign-off)

For any new model that feeds public reporting: confirm SOX classification BEFORE building.

---

## §16. The 7+ ARR view families

Built from `FINANCE_LINE_ANALYTICS`, aggregated multiple ways:

| View | Grain | Use case |
|---|---|---|
| `ARR_LINE_CATEGORIES` | ALI × as_was_date × category | Most granular; audit / drill-down |
| `ARR_PRODUCT_CATEGORIES` | Product L3/L4/L5 × as_was_date × category | Product retention |
| `ARR_SKU_CATEGORIES` | SKU × as_was_date × category | SKU-level analysis |
| `ARR_ACCOUNT_CATEGORIES` | Account × as_was_date × category | Account NDR |
| `ARR_REGION_SEGMENT_CATEGORIES` | Region × Segment × as_was_date × category | GTM territory |
| `ARR_INDUSTRY_CATEGORIES` | Industry × as_was_date × category | Vertical analysis |
| `ARR_STRATEGIC_PARTNER_CATEGORIES` | Partner-flag × as_was_date × category | Partner-channel ARR |

Each category column is a `SUM(arr_usd_*) WHERE category = 'X'` over the rollup grain. The columns are:
- `begin_arr_usd_*`
- `new_logo_arr_usd_*`
- `expansion_arr_usd_*`
- `contraction_arr_usd_*`
- `churn_arr_usd_*`
- `sku_change_arr_usd_*`
- `end_arr_usd_*`

Plus the deeper attribution columns (volume, price, mix).

---

## §17. The "5 levels of validation" pre-deploy

Before deploying any change to `FINANCE_LINE_ANALYTICS` or downstream ARR views:

1. **dbt tests pass**: unique + not_null + relationships + expression_is_true
2. **Recon query: ARR walk balances**: `BEGIN_ARR + Δs = END_ARR` within $1
3. **Recon query: Total ARR matches prior version**: < 0.1% variance on unchanged categories
4. **SCD2 row count delta in expected range**: <5% week-over-week
5. **Sigma reconciliation**: hand-validate top-5 dashboards against prior-published numbers

For deep mechanics, see `finance-bsa-data-analyst` skill.

---

## §18. Common gotchas

- **Mixing currency variants** in a single sum — produces nonsense
- **Forgetting `as_was_date` filter** — explodes row count
- **Re-implementing SSR categorization** — use `SSR_AGREEMENT_RELATIONSHIP`, never DIY
- **Querying non-primary proposals** for ARR — only primary become agreements
- **Forgetting `is_arr_eligible` filter** — captures pilots / non-recurring fees you don't want
- **Stale `vw_ref_product_hierarchy`** — new product launches without sheet update result in NULL product mapping
- **Acquired-product mapping missing** — newly-acquired SKUs without `REF_ACQUISITION_MAPPING` entries show as NULL hierarchy
- **TCV correction missed** — Finance Ops adds a correction in the sheet but the next batch hasn't run → ARR off
- **Backdated agreement amendment** — agreement amended with prior-quarter effective date; CAREFUL — discuss with SOX before re-running snapshot
- **Partner double-count** — use `get_partner_reporting()`, never sum direct + partner manually

---

## §19. Cross-domain dependencies

| Depends on | Why |
|---|---|
| `eda-dbt-base` | Raw Apttus, Zuora, Workday FM wrappers + SCD2 history |
| `eda-dbt-common` | Fiscal calendar, FX rates, Reltio MDM, product hierarchy |
| `eda-dbt-gtm` | Cross-project ref to `WD_AGREEMENT_LINE_SCD2`, `WD_OPPORTUNITY_SCD2`, `WD_PROPOSAL_*_SCD2` |
| `eda-dbt-cx` | (selectively) — uses customer health for renewal-risk forecasting |

Consumed by:
| Downstream | Use case |
|---|---|
| `eda-dbt-cx` | ARR by customer for health / risk calculation |
| `eda-dbt-semantic-layer` | All canonical ARR/ACV metrics |
| Sigma BI | Direct queries to `FINANCE_PROD.DATA_PRODUCTS.*` |

---

## §20. Cross-references

- `finance-metrics-canonical.md` — formal metric definitions
- `subscription-business-model.md` — quote-to-cash + SSR business context
- `enterprise-metrics-finance-architect` skill — finance-architect deep dive
- `finance-functional-architect` skill — translating business requirements
- `finance-bsa-data-analyst` skill — profiling + validation queries
- `finance-functional-analytics` skill — analytical query patterns
- `salesforce-bsa-finance-analyst` skill — SFDC finance objects
- `salesforce-bsa-agreements-contracts` skill — Apttus deep dive
