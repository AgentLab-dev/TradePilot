# Domain — Sales / GTM

Owner: GTM Analytics Engineering team.
Project: `eda-dbt-gtm` (writes to `SALES_PROD` + `SALES_INT_PROD`).
Primary source: Salesforce (core org + GTM-Next org via Fivetran).

---

## §1. What this domain owns

| Area | Examples |
|---|---|
| Pipeline analytics | Open opportunities, pipeline coverage, stage progression |
| Forecasting | AE / RVP / GVP / SVP roll-ups, gap-to-quota |
| Quota & attainment | Quota allocations, attainment %, accelerator earnings |
| Territory / hierarchy | Account ownership, sales hierarchy SCD2 |
| Win/Loss | Win rate, sales cycle length, deal velocity |
| CPQ flow | Opportunity → Proposal → Agreement booking handoff to finance |
| Activity | Outreach sequences, Gong call counts, meetings booked |
| Partner / channel | Co-sell opportunities, partner-sourced pipeline |

What this domain does NOT own:
- ❌ ARR / ACV computation — that's `eda-dbt-em` (Finance domain)
- ❌ Marketing-sourced pipeline attribution — that's `domain-marketing.md`
- ❌ Customer health — that's `eda-dbt-cx`
- ❌ Billing — that's Zuora pipelines (Finance)

---

## §2. Source systems

| System | Connector | Refresh | Primary tables |
|---|---|---|---|
| **Salesforce (core org)** | Fivetran | 1 hr CDC | `OPPORTUNITY`, `OPPORTUNITYHISTORY`, `OPPORTUNITYFIELDHISTORY`, `OPPORTUNITYSPLIT`, `ACCOUNT`, `USER`, `OPPORTUNITYSTAGE`, `OPPORTUNITYLINEITEM` |
| **Salesforce (GTM-Next org)** | Fivetran | 1 hr CDC | Same object model, separate org (migration target) |
| **Apttus CPQ** | (within SFDC) | 1 hr CDC | `APTTUS_PROPOSAL__PROPOSAL__C`, `APTTUS_PROPOSAL__PROPOSAL_LINE_ITEM__C`, `APTTUS_CONFIG2__LINEITEM__C` |
| **Outreach** | Fivetran | 1 hr | `SEQUENCE`, `SEQUENCESTATE`, `PROSPECT`, `ACCOUNT`, `MAILING`, `CALL`, `MEETING` |
| **Gong** | Fivetran | 4 hr | `CALLS`, `INTERACTIONS`, `CALL_PARTICIPANTS`, `KEY_POINTS` |
| **Clari** | Fivetran | 1 hr | `OPPORTUNITY_FORECASTS`, `FORECAST_SUBMISSIONS`, `QUOTA` |
| **Highspot** | Fivetran | 4 hr | `CONTENT_ENGAGEMENT`, `PITCH` |
| **Mediafly** | Fivetran | 4 hr | `CONTENT_ANALYTICS` |
| **Google Sheets** | Fivetran | 15 min | `REF_TERRITORY_OWNERSHIP`, `REF_QUOTA_FY26_DETAIL` |

---

## §3. Core Salesforce object model

```
Account
  │
  ├── Opportunity (1:N) ──────────────┐
  │      │                            │
  │      ├── OpportunityStage         │
  │      ├── OpportunityHistory       │
  │      ├── OpportunityFieldHistory  │  ← stage progression audit
  │      ├── OpportunitySplit         │  ← multi-AE attribution
  │      ├── ForecastDetail__c         │  ← per-level forecasts
  │      │                            │
  │      ├── Apttus_Proposal__c (1:N) │  ← Quotes (only PRIMARY counts)
  │      │      └── Apttus_ProposalLineItem__c (1:N)
  │      │              └── Apttus_ConfigLineItem__c
  │      │
  │      └── Apttus_Agreement__c (0:1) ← Contract (if quote signed)
  │             └── AgreementLineItem__c → Finance owns
  │
  ├── Campaign / CampaignMember
  ├── Lead
  └── Contact
```

---

## §4. SCD2 dimension wrappers (in `SALES_PROD.MANAGED`)

Built by `eda-dbt-gtm` to provide point-in-time history:

| Model | Source | Notes |
|---|---|---|
| `WD_ACCOUNT_SCD2` | `BASE_PROD.SALESFORCE.ACCOUNT` | Account hierarchy + Reltio MDM enrichment |
| `WD_OPPORTUNITY_SCD2` | `BASE_PROD.SALESFORCE.OPPORTUNITY` | Stage, amount, close date history |
| `WD_PROPOSAL_SCD2` | `BASE_PROD.SALESFORCE.APTTUS_PROPOSAL__PROPOSAL__C` | Quote SCD2 (only primary proposals matter for finance) |
| `WD_PROPOSAL_LINE_SCD2` | `BASE_PROD.SALESFORCE.APTTUS_PROPOSAL__PROPOSAL_LINE_ITEM__C` | Quote line history |
| `WD_USER_SCD2` | `BASE_PROD.SALESFORCE.USER` | AE / RVP / leadership SCD2 |
| `WD_OPPORTUNITY_EXTENSION_SCD2` | `BASE_PROD.SALESFORCE.OPPORTUNITY_EXTENSION__C` | Workday-custom opp extension fields |
| `WD_OPP_STAGE_HISTORY` | `BASE_PROD.SALESFORCE.OPPORTUNITYHISTORY` | Stage transitions |

SCD2 is implemented via dbt `snapshots/` + custom merge logic. Snapshot dates align to daily cadence; closed quarters are immutable.

---

## §5. Opportunity stages — canonical mapping

| Stage code (SFDC) | Stage name | Category | Won? |
|---|---|---|---|
| 1 | Develop / Identify | Pipeline (Early) | No |
| 2 | Qualify | Pipeline (Early) | No |
| 3 | Strategize | Pipeline (Mid) | No |
| 4 | Propose | Pipeline (Mid) | No |
| 5 | Negotiate | Pipeline (Late) | No |
| 6 | Close (Verbal) | Pipeline (Late) | No |
| 7 | Closed/Won | Won | Yes |
| 8 | Closed/Lost | Lost | No |
| 9 | Closed/No Decision | Lost | No |

Stage rationalization view: `SALES_PROD.MANAGED.VW_REF_ACV_STAGE_CLASSIFICATION` (or equivalent in eda-dbt-em — historically `stg_em_vw_ref_acv_stage_classification`).

NEVER hardcode stage strings — always join to the rationalization view.

---

## §6. Forecast hierarchy

Workday uses a **6-level forecast hierarchy**:

```
AE (account exec)
   ↓ aggregates to
RSD (regional sales director)
   ↓ aggregates to
RVP (regional vice president)
   ↓ aggregates to
AVP (area vice president)
   ↓ aggregates to
GVP (group vice president)
   ↓ aggregates to
SVP (senior vice president)
```

Each Opportunity has fields for each level: `ae_forecast`, `rsd_forecast`, `rvp_forecast`, `avp_forecast`, `gvp_forecast`, `svp_forecast`. Stored as picklists: `OMITTED`, `PIPELINE`, `BEST_CASE`, `COMMIT`, `CLOSED`.

Dashboards typically aggregate forecast at the GVP or SVP level for executive review.

Source: `OPPORTUNITY.<level>_forecast__c` + `ForecastDetail__c`. Clari aggregates submitted forecasts independently.

---

## §7. CPQ — the proposal/agreement handoff

The handoff from sales (proposal) to finance (agreement):

```
Opportunity                    ← Sales reports here
  ↓
Apttus_Proposal__c (PRIMARY)   ← Primary quote — what's actively being negotiated
                                  - `IS_PRIMARY__C = TRUE` filter is essential
                                  - Multiple proposals per opp; only primary becomes agreement
  ↓
Apttus_Agreement__c            ← When signed
  ↓
AgreementLineItem__c           ← Finance grain (FINANCE_LINE_ANALYTICS)
```

Rules:
- **Only primary proposals** become agreements. Always filter `IS_PRIMARY__C = TRUE` on proposal joins.
- The handoff happens via `Opportunity.Id → Proposal.Apttus_Proposal__Opportunity__c → Agreement.Opportunity__c`.
- **Booking ACV** (sales-attainment) is calculated from `Apttus_Proposal_Line_Item__c` (sales-side, pre-signing).
- **Activated ARR** (finance) is calculated from `AgreementLineItem__c` (finance-side, post-signing).
- Both should match within signing-period precision (slight differences for amendments).

Sales-side bookings view: `SALES_PROD.AGGREGATIONS.BT_ACV_SKU`
Finance-side ARR view: `FINANCE_PROD.AGGREGATIONS.ARR_SKU_CATEGORIES`

---

## §8. Quota + attainment

Quota is allocated to sales reps annually (per fiscal year), often broken by quarter.

Sources:
- Google Sheets `REF_QUOTA_FY26_DETAIL` (Fivetran-synced)
- Apttus Quota object (if used; varies by team)

Quota table layout:
```
quota_owner_user_id  | fiscal_quarter | quota_acv_usd | quota_total_pipeline_usd
```

Attainment view: `SALES_PROD.AGGREGATIONS.QUOTA_ATTAINMENT`
- Joins `BT_ACV_SKU` (closed bookings) to `REF_QUOTA_FY26_DETAIL`
- Calculates `attainment_pct = sum(closed_won_acv) / quota_acv_usd`

Accelerator earnings: above 100% attainment, accelerated commission rates kick in. (Comp team owns the calc; we provide attainment data.)

---

## §9. Pipeline metrics — canonical definitions

| Metric | Formula | Use |
|---|---|---|
| **Open pipeline ($)** | `SUM(amount)` where `stage IN (1..6)` | Total open deals |
| **Pipeline coverage** | `open_pipeline / remaining_quota` | Is there enough pipeline to hit quota? |
| **Pipe-to-bookings ratio** | `pipeline_created_in_period / bookings_in_period` | Pipeline efficiency |
| **Sales velocity** | `(num_open_opps × avg_deal_size × win_rate) / avg_sales_cycle_days` | Forward-looking bookings projection |
| **Win rate** | `count(closed_won) / (count(closed_won) + count(closed_lost))` | Conversion |
| **Avg sales cycle** | `AVG(close_date - created_date)` | Velocity |

Canonical model: `SALES_PROD.AGGREGATIONS.PIPELINE_SUMMARY` (or similar).

---

## §10. Stage-progression tracking (the SCD2 pattern)

OpportunityFieldHistory tracks every stage change. Use this for:
- Average days in stage
- Stage skip detection (e.g., 1 → 5 = skipped qualification)
- Stage regression detection (5 → 3 = pulled back)
- Slipped opportunities (close date moved forward by > 30 days)

Canonical SQL pattern:
```sql
WITH stage_changes AS (
    SELECT
        opportunity_id,
        new_stage,
        old_stage,
        change_date,
        LEAD(change_date) OVER (PARTITION BY opportunity_id ORDER BY change_date) AS next_change_date,
        DATEDIFF(day, change_date, COALESCE(
            LEAD(change_date) OVER (PARTITION BY opportunity_id ORDER BY change_date),
            CURRENT_DATE()
        )) AS days_in_stage
    FROM SALES_PROD.MANAGED.WD_OPP_STAGE_HISTORY
)
SELECT opportunity_id, new_stage, AVG(days_in_stage) AS avg_days_in_stage
FROM stage_changes
GROUP BY 1, 2;
```

---

## §11. Multi-AE attribution (Opportunity Splits)

When multiple AEs work the same deal, `OpportunitySplit` allocates the credit:

```
OpportunitySplit
  ├── opportunity_id
  ├── split_owner_id  (AE)
  ├── split_percentage  (0-100, total per opp = 100%)
  └── split_type  (Revenue Split | Overlay Split | Custom)
```

For accurate per-AE attainment:
```sql
SELECT
    split_owner_id,
    SUM(opportunity_amount * (split_percentage / 100.0)) AS attributed_amount
FROM SALES_PROD.MANAGED.WD_OPPORTUNITY_SCD2 o
JOIN BASE_PROD.SALESFORCE.OPPORTUNITYSPLIT s ON o.id = s.opportunityid
WHERE o.is_current = TRUE
  AND o.stage = 'Closed/Won'
  AND s.split_type = 'Revenue Split'
GROUP BY 1;
```

---

## §12. Outreach + Gong (activity data)

Activity-to-pipeline correlation:

| Source | Grain | Used for |
|---|---|---|
| **Outreach** | Email / call / meeting per prospect | SDR / AE activity volume, sequence effectiveness |
| **Gong** | Call recording per opp | Call-to-close ratio, deal sentiment, keyword tracking |
| **Highspot** | Content engagement per opp | Content-stage correlation |

Common queries:
- "Which AEs have lowest call volume but highest close rate?" (efficiency)
- "Which content correlates with closed-won?" (sales enablement)
- "Which sequences have highest reply rate?" (SDR optimization)

Canonical activity rollup: `SALES_PROD.AGGREGATIONS.SALES_ACTIVITY_SUMMARY`.

---

## §13. GTM-Next migration (in-flight)

Workday is migrating from the **core SFDC org** to a **GTM-Next org** — a re-architected Salesforce org with new object model, cleaner data, modern CPQ.

Status (as of 2026): in flight. Phased rollout by region + product line.

Data implications:
- `BASE_PROD.SALESFORCE.*` — core org (legacy, still primary for most products)
- `BASE_PROD.SALESFORCE_GTMNEXT.*` — new org (selective, growing scope)
- Dual-write period: same opportunity may exist in both orgs during migration
- Unification: `SALES_PROD.MANAGED.WD_OPPORTUNITY_UNIFIED_SCD2` merges both (with `source_org` flag)

If you're querying a specific account / opportunity, check both orgs. The migration team maintains a mapping table: `LKP_GTMNEXT_MIGRATED_ACCOUNTS`.

---

## §14. Reltio MDM — Account hierarchy resolution

Salesforce account hierarchy is messy (duplicates, M&A complexity). **Reltio** provides golden-record MDM:

- `BASE_PROD.RELTIO.ACCOUNT_GOLDEN` — canonical account records
- `BASE_PROD.RELTIO.ACCOUNT_HIERARCHY` — parent/child links
- `BASE_PROD.RELTIO.ACCOUNT_LINKS_TO_SFDC` — Reltio ID ↔ SFDC ID mapping

Workflow:
1. SFDC accounts → Reltio for de-duplication + hierarchy resolution
2. Reltio enriches with firmographic data (D&B, ZoomInfo)
3. Enriched account → `SALES_PROD.MANAGED.WD_ACCOUNT_SCD2` (joins Reltio data back)

When debugging "account X is reported twice" or "missing parent": check Reltio first.

---

## §15. Customer Data Platform (CDP)

CDP unifies customer profiles across SFDC + Marketo + Gainsight + product usage. Lives in `BASE_PROD.CDP.*`.

Used mostly by Marketing (attribution + ABM), but Sales analytics tap into it for:
- Account intent signals (CDP infers intent from web/marketing behavior)
- Engagement scoring (combines SFDC + Marketo + Gainsight signals)

Talk to the CDP / data engineering team if you need CDP fields — schema evolves frequently.

---

## §16. The "first-touch / last-touch / multi-touch" attribution debate

Sales-side attribution is single-touch (the AE who closed gets the credit, modulo Opp Splits). Marketing-side attribution is multi-touch (Bizible). Both coexist; don't confuse.

| Term | What it credits | Where |
|---|---|---|
| **Opportunity Owner** | AE who closed | Sales attainment |
| **Opportunity Splits** | Multiple AEs (revenue / overlay) | Sales attainment |
| **Lead Source** | First marketing touch | Marketing-sourced pipeline (single-touch) |
| **Bizible Multi-Touch** | All marketing touches (first / lead conversion / opp creation / closed) | Marketing attribution analytics |

For Marketing attribution detail: `domain-marketing.md`.

---

## §17. Key model patterns + naming

| Pattern | Examples |
|---|---|
| Source wrappers | `base_apttus_proposal__proposal__c` (in `eda-dbt-base`) |
| Stage models | `stg_em_apttus__proposal__c`, `stg_em_opportunity_scd2` |
| Intermediate | `int_em_opportunity_stage_progression`, `int_em_proposal_primary_only` |
| Managed dim | `wd_account_scd2`, `wd_opportunity_scd2` |
| Aggregations | `pipeline_summary`, `quota_attainment`, `bt_acv_sku` |
| Data products | `dash_pipeline_health`, `dash_forecast_accuracy` |

---

## §18. Cross-domain dependencies

| Depends on | Why |
|---|---|
| `eda-dbt-base` | All raw SFDC wrappers + base SCD2 |
| `eda-dbt-common` | Fiscal calendar, currency, Reltio MDM dims |
| `eda-dbt-em` | Some shared SSR / agreement-relationship lookups |

Consumed by:
| Downstream | Use case |
|---|---|
| `eda-dbt-em` | Pulls `WD_ACCOUNT_SCD2`, `WD_OPPORTUNITY_SCD2`, `WD_PROPOSAL_*_SCD2` for finance enrichment |
| `eda-dbt-cx` | Pulls account + agreement context for customer health |
| `eda-dbt-semantic-layer` | Semantic metrics (pipeline coverage, win rate, attainment) |

---

## §19. Common gotchas

- **Primary proposal filter** — always filter `IS_PRIMARY__C = TRUE` on proposal joins; multiple proposals exist per opp
- **Currency** — opportunities have `currency_iso_code`; always convert before summing
- **Closed-Lost-No-Decision** — separate from Closed-Lost in some dashboards; check stage rationalization
- **Stale OpportunityHistory** — has a 90-day SFDC retention quirk; for pre-90-day history, use SCD2 dim instead
- **Renaming Opp** — opportunity name changes are tracked in `OpportunityFieldHistory`; the SCD2 dim preserves the current name only
- **Multi-currency forecast** — RVP-level forecasts can be in non-USD; always check `currency_iso_code` field
- **Test opportunities** — sales team creates test opps; filter `is_test = FALSE` or `name NOT LIKE 'TEST%'`

---

## §20. Cross-references

- `salesforce-bsa-close` skill — opportunity close + CPQ deep dive
- `salesforce-bsa-agreements-contracts` skill — Apttus deep dive
- `subscription-business-model.md` — quote-to-cash flow
- `finance-metrics-canonical.md` — ARR / ACV definitions
- `domain-marketing.md` — marketing attribution + lead source
- `enterprise-data-products-catalog.md` — published sales data products
