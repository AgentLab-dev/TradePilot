---
name: salesforce-bsa-close
description: Salesforce BSA expertise for opportunity close processes, pipeline management, forecasting, win/loss analysis, CPQ (Apttus) quote-to-close workflows, and stage progression logic. Use when working with opportunity stages, close dates, forecast fields, pipeline snapshots, win rates, CPQ proposals, or sales process automation in Salesforce and dbt models.
---

# Salesforce BSA — Close & Pipeline

Role: Salesforce Business Systems Analyst specializing in opportunity close processes, pipeline management, sales forecasting, and CPQ (Apttus) quote-to-close workflows.

## Raw Salesforce Data Source

All raw Salesforce tables reside in `BASE_PROD.SALESFORCE` (307+ tables via Fivetran sync). Key tables for close/pipeline:

| Raw Table (`BASE_PROD.SALESFORCE`) | SCD2 Table (`BASE_PROD.REDSHIFT_HISTORY`) | Staging Model |
|-------------------------------------|-------------------------------------------|---------------|
| `OPPORTUNITY` | `OPPORTUNITY_SCD2` / `UNIFIED_HISTORY_OPPORTUNITY_SCD2` | `stg_em_opportunity_scd2` |
| `ACCOUNT` | `ACCOUNT_SCD2` / `UNIFIED_HISTORY_ACCOUNT_SCD2` | `stg_em_account_scd2` |
| `APTTUS_PROPOSAL__PROPOSAL__C` | `PROPOSAL_SCD2` / `UNIFIED_HISTORY_PROPOSAL_SCD2` | `stg_em_proposal_scd2` |
| `APTTUS_PROPOSAL__PROPOSAL_LINE_ITEM__C` | `PROPOSAL_LINE_ITEM_SCD2` / `UNIFIED_HISTORY_PROPOSAL_LINE_ITEM_SCD2` | `stg_em_proposal_line_item_scd2` |
| `OPPORTUNITY_EXTENSION__C` | `OPPORTUNITY_EXTENSION_SCD2` / `UNIFIED_HISTORY_OPPORTUNITY_EXTENSION_SCD2` | `stg_em_opportunity_extension_scd2` |
| `APTTUS_CONFIG2__LINEITEM__C` | `CONFIG_LINE_ITEM_SCD2` / `UNIFIED_HISTORY_CONFIG_LINE_ITEM_SCD2` | — |
| `OPPORTUNITYSTAGE` | — | — (reference table for stage definitions) |
| `OPPORTUNITYFIELDHISTORY` | — | — (field-level change tracking) |
| `OPPORTUNITYHISTORY` | — | — (stage change history) |
| `OPPORTUNITYSPLIT` / `OPPORTUNITYLINEITEMSPLIT` | — | — (deal splits) |
| `FORECAST_DETAIL__C` | — | — (forecast submissions) |

The `generate_base_salesforce_model` macro in `macros/governance/` creates views from `source('salesforce', table_name)` joining formula fields from `source('salesforce_quickstart', table_name)`.

## Salesforce Object Model — Close Process

```
Account
  └── Opportunity (pipeline, stage, close date, forecasts)
       ├── Opportunity Extension (custom fields, overrides)
       ├── Proposal / Quote (CPQ — Apttus)
       │    └── Proposal Line Item / Quote Line
       │         └── Config Line Item (CPQ configuration)
       ├── Related Opportunities (linked deals)
       └── Opportunity–Services Partner Junction (partner deals)
```

### Key SCD2 Sources

| Salesforce Object | Source Table | Staging Model |
|-------------------|-------------|---------------|
| Account | `UNIFIED_HISTORY_ACCOUNT_SCD2` | `stg_em_account_scd2` / `stg_em_account_as_was` |
| Opportunity | `UNIFIED_HISTORY_OPPORTUNITY_SCD2` | `stg_em_opportunity_scd2` / `stg_em_opportunity_as_was` |
| Opportunity Extension | `UNIFIED_HISTORY_OPPORTUNITY_EXTENSION_SCD2` | `stg_em_opportunity_extension_scd2` |
| Proposal (Quote) | `UNIFIED_HISTORY_PROPOSAL_SCD2` | `stg_em_proposal_scd2` / `stg_em_proposal_as_was` |
| Proposal Line Item | `UNIFIED_HISTORY_PROPOSAL_LINE_ITEM_SCD2` | `stg_em_proposal_line_item_scd2` / `stg_em_proposal_line_as_was` |
| Config Line Item | `UNIFIED_HISTORY_CONFIG_LINE_ITEM_SCD2` | — |
| Partner Junction | `UNIFIED_HISTORY_OPPORTUNITY_SERVICES_PARTNER_JUNCTION_SCD2` | `stg_em_opportunities_services_partner_junction_scd2` |

## Opportunity Stage Framework

### Stage Progression

```
Lead/Prospect → Qualification → Discovery → Proposal → Negotiation → Closed/Won | Closed/Lost
```

### Stage Classification Codes

| Code | Stage | Category |
|------|-------|----------|
| `7%` | Early pipeline | Open |
| `8%` | Mid pipeline | Open |
| `9%` | Closed/Won | Closed-Won |
| `35%` | Closed/Lost | Closed-Lost |

- Use `stg_em_vw_ref_acv_stage_classification` for the canonical stage-to-classification mapping.
- Stage filtering in models uses patterns like `stage_name LIKE '9-%'` for Closed/Won.

### Stage-Related Fields

| Field | Object | Purpose |
|-------|--------|---------|
| `stage_name` | Opportunity | Current pipeline stage |
| `close_date` | Opportunity | Expected or actual close date |
| `target_close_date__c` | Opportunity | Original planned close date (for slippage analysis) |
| `stage_classification` | Derived | Open / Closed-Won / Closed-Lost |

## Forecasting Fields

Multiple forecast levels exist on each Opportunity:

| Field | Level | Description |
|-------|-------|-------------|
| `ae_forecast` | AE (Rep) | Account Executive's commit/forecast |
| `rsd_forecast` | RSD | Regional Sales Director forecast |
| `rvp_forecast` | RVP | Regional VP forecast |
| `avp_forecast` | AVP | Area VP forecast |
| `gvp_forecast` | GVP | Group VP forecast |
| `svp_forecast` | SVP | Senior VP forecast (rollup) |

### Forecast Analysis Pattern

```sql
with forecast_comparison as (
    select
        opportunity_id,
        close_date,
        stage_name,
        ae_forecast,
        svp_forecast,
        case
            when ae_forecast != svp_forecast then 'OVERRIDE'
            else 'ALIGNED'
        end as forecast_alignment
    from {{ ref('stg_em_int_opp_base') }}
    where stage_classification = 'Open'
)
```

## CPQ (Apttus) Quote-to-Close Workflow

```
Opportunity created
  → Proposal (Quote) created
    → Proposal Line Items configured
      → Config Line Items (product configuration)
        → Quote approved → Agreement generated
          → Agreement Line Items (contracted terms)
            → Opportunity stage → Closed/Won
```

### CPQ Key Relationships

| Parent | Child | Join Key | Grain |
|--------|-------|----------|-------|
| Opportunity | Proposal | `opportunity_id` | Many proposals per opportunity |
| Proposal | Proposal Line Item | `proposal_id` | Many lines per proposal |
| Proposal Line Item | Config Line Item | `proposal_line_item_id` | Configuration details |
| Opportunity | Agreement | `opportunity_id` | Usually 1:1 for closed deals |
| Agreement | Agreement Line Item | `agreement_id` | Many lines per agreement |

### Primary vs Non-Primary Proposals

- An Opportunity can have multiple Proposals — only the **primary** one drives ACV/booking.
- Filter with `is_primary_proposal = true` or equivalent flag.
- `bt_acv_sku` joins Proposal + Proposal Line + Opportunity for the final ACV calculation.

## Pipeline Snapshot Pattern

For point-in-time pipeline analysis (how pipeline looked on a given date):

```sql
with pipeline_snapshot as (
    select
        opportunity_id,
        stage_name,
        close_date,
        acv,
        svp_forecast,
        as_was_date
    from {{ ref('stg_em_opportunity_as_was') }}
    where as_was_date = '{{ var("as_was_date") }}'
      and stage_classification = 'Open'
)
```

- SCD2 `as_was` models enable historical pipeline snapshots.
- `bt_acv_quoteline_new_hierarchy_day_five_snap` captures pipeline at day-5 of fiscal period.
- Always use `as_was_date` variable for consistent point-in-time queries.

## Win/Loss Analysis Pattern

```sql
with closed_opps as (
    select
        opportunity_id,
        account_id,
        stage_name,
        close_date,
        acv,
        lead_source,
        case
            when stage_name like '9-%' then 'WON'
            when stage_name like '35-%' then 'LOST'
        end as outcome
    from {{ ref('stg_em_int_opp_enriched') }}
    where stage_classification in ('Closed-Won', 'Closed-Lost')
),

win_rates as (
    select
        {{ get_fiscal_quarter('close_date') }} as fiscal_quarter,
        count(case when outcome = 'WON' then 1 end) as wins,
        count(case when outcome = 'LOST' then 1 end) as losses,
        count(*) as total_closed,
        wins / nullif(total_closed, 0) as win_rate
    from closed_opps
    group by fiscal_quarter
)
```

## SOQL Queries for Investigation

Use the Salesforce MCP tool (`run_soql_query`) to validate data directly:

```sql
-- Check opportunity stages and close dates
SELECT Id, StageName, CloseDate, Amount, ForecastCategoryName
FROM Opportunity
WHERE IsClosed = true AND CloseDate >= 2025-01-01

-- Check proposals linked to an opportunity
SELECT Id, Name, Apttus_Proposal__Opportunity__c, Apttus_Proposal__Primary__c
FROM Apttus_Proposal__Proposal__c
WHERE Apttus_Proposal__Opportunity__c = '006XXXXXXXXXXXX'

-- Pipeline snapshot for forecast
SELECT Id, StageName, CloseDate, Amount, SVP_Forecast__c, GVP_Forecast__c
FROM Opportunity
WHERE IsClosed = false AND CloseDate = THIS_FISCAL_QUARTER
```

## Common Issues

| Issue | Cause | Investigation |
|-------|-------|---------------|
| ACV mismatch between Opp and Quote | Non-primary proposal included | Filter `is_primary_proposal = true` |
| Pipeline inflated | Closed/Lost not excluded | Check stage classification filter |
| Forecast not rolling up | Wrong forecast field level | Verify which forecast level (AE vs SVP) is expected |
| Close date slippage invisible | Using current close_date, not target | Compare `close_date` vs `target_close_date__c` |
| Duplicate pipeline in snapshots | SCD2 not filtered to single as_was_date | Add `WHERE as_was_date = ...` |

## Constraints

- Always use SCD2 `as_was` models for historical/point-in-time analysis — never assume current state.
- Stage classifications must use the canonical mapping from `stg_em_vw_ref_acv_stage_classification`.
- Forecast analysis must specify which management level (AE through SVP).
- CPQ joins must account for primary vs non-primary proposals.
- Use `ref()` and `source()` exclusively — never hardcode Salesforce object API names in SQL.
