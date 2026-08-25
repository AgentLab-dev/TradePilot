---
name: salesforce-bsa-finance-analyst
description: Salesforce BSA expertise for finance analytics — agreement lifecycle, ARR/ACV/TCV from Salesforce CPQ objects, revenue recognition, billing alignment, currency conversion, SSR agreements, and reconciliation between Salesforce and finance models. Use when investigating Salesforce-to-finance data flows, agreement/proposal discrepancies, CPQ billing issues, currency conversion problems, or reconciling Salesforce data against financial reports.
---

# Salesforce BSA — Finance Analyst

Role: Salesforce Business Systems Analyst specializing in the Salesforce-to-Finance data pipeline — CPQ agreement lifecycle, revenue metrics derivation from Salesforce objects, billing reconciliation, and Salesforce data quality for financial reporting.

## Raw Salesforce Data Source

All raw Salesforce tables reside in `BASE_PROD.SALESFORCE` (307+ tables via Fivetran sync). Key tables for finance:

| Raw Table (`BASE_PROD.SALESFORCE`) | SCD2 Table (`BASE_PROD.REDSHIFT_HISTORY`) | Purpose |
|-------------------------------------|-------------------------------------------|---------|
| `APTTUS__APTS_AGREEMENT__C` | `AGREEMENT_SCD2` / `UNIFIED_HISTORY_AGREEMENT_SCD2` | Contracts |
| `APTTUS__AGREEMENTLINEITEM__C` | `AGREEMENT_LINE_ITEM_SCD2` / `UNIFIED_HISTORY_AGREEMENT_LINE_ITEM_SCD2` | Line-level ARR/TCV |
| `APTTUS__APTS_RELATED_AGREEMENT__C` | `RELATED_AGREEMENT_SCD2` / `UNIFIED_HISTORY_RELATED_AGREEMENT_SCD2` | SSR links |
| `APTTUS_PROPOSAL__PROPOSAL__C` | `PROPOSAL_SCD2` / `UNIFIED_HISTORY_PROPOSAL_SCD2` | Quotes/pricing |
| `APTTUS_PROPOSAL__PROPOSAL_LINE_ITEM__C` | `PROPOSAL_LINE_ITEM_SCD2` / `UNIFIED_HISTORY_PROPOSAL_LINE_ITEM_SCD2` | Quote line items |
| `APTTUS_CONFIG2__LINEITEM__C` | `CONFIG_LINE_ITEM_SCD2` / `UNIFIED_HISTORY_CONFIG_LINE_ITEM_SCD2` | CPQ config |
| `OPPORTUNITY` | `OPPORTUNITY_SCD2` / `UNIFIED_HISTORY_OPPORTUNITY_SCD2` | Booking events |
| `DATEDCONVERSIONRATE` | — | FX rates |
| `CURRENCYTYPE` | — | Active currencies |
| `APTTUS__AGREEMENTLINEITEM__HISTORY` | — | Line item field changes |
| `APTTUS__APTS_AGREEMENT__HISTORY` | — | Agreement field changes |
| `APTS_INVOICE_DETAIL__C` | — | Invoice details |
| `PAYMENT_SCHEDULE__C` | — | Payment schedules |
| `ASSET` | — | Customer assets |
| `APTTUS_CONFIG2__ASSETLINEITEM__C` | — | Asset line items |

The `generate_base_salesforce_model` macro in `macros/governance/` creates views from `source('salesforce', table_name)` joining formula fields from `source('salesforce_quickstart', table_name)`.

## Salesforce CPQ Object Model for Finance

```
Opportunity (booking event)
  └── Proposal / Quote (CPQ pricing)
       └── Proposal Line Item (SKU-level pricing)
            └── Config Line Item (product configuration)

Agreement (executed contract)
  └── Agreement Line Item (contracted terms, ARR/ACV/TCV source)
       └── Related Agreement (SSR — supersede & replace)
```

### Object-to-Finance Metric Flow

```
Salesforce Object          →  Finance Metric
─────────────────────────────────────────────
Proposal Line Item         →  Booking ACV (at quote time)
Agreement Line Item        →  ARR, TCV (contracted)
Opportunity.Amount         →  Opportunity ACV (header level)
Agreement.Total_Fees       →  Agreement TCV
DatedConversionRate        →  Currency conversion (FX)
```

### Source-to-Model Chain

| Salesforce Object | Source | Staging | Intermediate | Finance Model |
|-------------------|--------|---------|--------------|---------------|
| Agreement Line Item | `UNIFIED_HISTORY_AGREEMENT_LINE_ITEM_SCD2` | `stg_em_agreement_line_item_scd2` | `stg_em_int_financial_metrics` | `bt_sku_analytics`, `finance_line_analytics` |
| Agreement | `UNIFIED_HISTORY_AGREEMENT_SCD2` | `stg_em_agreement_scd2` | `stg_em_agree_source_temp` | `bt_*_arr_categories` |
| Proposal | `UNIFIED_HISTORY_PROPOSAL_SCD2` | `stg_em_proposal_scd2` | — | `bt_acv_sku` |
| Proposal Line Item | `UNIFIED_HISTORY_PROPOSAL_LINE_ITEM_SCD2` | `stg_em_proposal_line_item_scd2` | — | `bt_acv_sku` |
| Opportunity | `UNIFIED_HISTORY_OPPORTUNITY_SCD2` | `stg_em_opportunity_scd2` | `stg_em_int_opp_base` | `bt_acv_sku`, `bt_sku_acv_categories` |
| DatedConversionRate | `base_salesforce_datedconversionrate` | `stg_em_datedconversionrate` | — | Currency conversion |

## Agreement Lifecycle for Finance

### Agreement States

```
Draft → Activated → Amended → Renewed → Terminated/Expired
                      ↓
               Superseded (SSR)
```

### Key Agreement Fields for Finance

| Field | Purpose | Finance Impact |
|-------|---------|----------------|
| `agreement_id` | Contract identifier | Join key for ARR/TCV |
| `agreement_line_item_id` | Line-level PK | Grain for ARR models |
| `total_fees` / `adj_al_total_fees` | Contracted value | TCV calculation |
| `start_date` / `end_date` | Contract term | ARR annualization, term calculation |
| `status` | Agreement lifecycle state | Active = counted in ARR |
| `auto_renew` | Auto-renewal flag | Renewal pipeline |
| `currency_iso_code` | Transaction currency | FX conversion input |

### TCV → ARR / ACV Derivation

Finance functions convert raw Salesforce values:

```sql
{{ tcv_to_arr('total_fees', 'start_date', 'end_date') }} as arr,
{{ tcv_to_acv('total_fees', 'start_date', 'end_date') }} as acv
```

- **TCV** = Total contract value (raw from Agreement Line)
- **ARR** = TCV annualized over contract term
- **ACV** = TCV normalized to first-year value

### Corrected TCV

Some lines need TCV corrections from external reference data:

```sql
-- TCV correction lookup
coalesce(
    correction.corrected_tcv,
    agreement_line.total_fees
) as final_tcv
```

- Source: `base_google_sheets_ref_wd_tcv_correction_ref_wd_tcv_correction`
- Staging: `stg_em_lkp_wd_fin_tcv_correction`

## Currency Conversion

### FX Rate Source

```
base_salesforce_datedconversionrate → stg_em_datedconversionrate
```

### Currency Variants Applied

| Variant | FX Rate | Use |
|---------|---------|-----|
| `USD_CURRENT` | Latest available rate | Dashboards, trending |
| `USD_HIST` | Rate on transaction date | Period comparisons |
| `USD_ACTUAL` | Contracted amount (no conversion) | Billing, invoicing |

### Conversion Pattern

```sql
agreement_line.total_fees * fx.conversion_rate as total_fees_usd_current
```

## Supersede & Replace (SSR) — Salesforce Mechanics

### How SSR Works in Salesforce

1. Old agreement status → `Superseded`
2. New agreement created with link to old via `Related Agreement`
3. Agreement Line Items carry over (possibly amended)

### SSR in dbt Models

| Model | Role |
|-------|------|
| `UNIFIED_HISTORY_RELATED_AGREEMENT_SCD2` | Raw SSR links |
| `ssr_agreement_relationship` | Resolved old ↔ new mapping |
| `bt_*_arr_categories` | ARR continuity (not churn + new) |

### SSR Validation

```sql
-- Verify SSR agreements have correct ARR category (never CHURN + NEW)
select
    agreement_id,
    related_agreement_id,
    arr_category
from {{ ref('ssr_agreement_relationship') }} ssr
inner join {{ ref('bt_product_arr_categories') }} arr
    on ssr.new_agreement_id = arr.agreement_id
where arr.arr_category in ('CHURN', 'NEW')
-- Should return 0 rows for properly categorized SSR
```

## Reconciliation Patterns

### Salesforce vs Finance Model Tie-Out

```sql
-- Compare Salesforce opportunity ACV to model ACV
select
    o.opportunity_id,
    o.amount as sf_amount,
    m.acv as model_acv,
    o.amount - m.acv as variance
from {{ ref('stg_em_opportunity_as_was') }} o
left join {{ ref('bt_acv_sku') }} m
    on o.opportunity_id = m.opportunity_id
where abs(o.amount - m.acv) > 1
```

### Agreement Line to Finance Line Tie-Out

```sql
-- Verify every active agreement line appears in finance model
select
    al.agreement_line_item_id,
    al.total_fees,
    f.tcv
from {{ ref('stg_em_agreement_line_as_was') }} al
left join {{ ref('finance_line_analytics') }} f
    on al.agreement_line_item_id = f.agreement_line_item_id
where f.agreement_line_item_id is null
    and al.status = 'Activated'
-- Should return 0 rows — all active lines accounted for
```

### Proposal Line to ACV Tie-Out

```sql
-- Verify primary proposal lines match ACV booking
select
    pl.proposal_id,
    sum(pl.net_price) as proposal_total,
    b.acv as booking_acv,
    sum(pl.net_price) - b.acv as variance
from {{ ref('stg_em_proposal_line_as_was') }} pl
inner join {{ ref('bt_acv_sku') }} b
    on pl.proposal_id = b.proposal_id
where pl.is_primary = true
group by pl.proposal_id, b.acv
having abs(variance) > 1
```

## SOQL Queries for Investigation

```sql
-- Check agreement line items and financial fields
SELECT Id, Apttus__AgreementId__c, Apttus__Quantity__c,
       Apttus__NetPrice__c, CurrencyIsoCode,
       Apttus__StartDate__c, Apttus__EndDate__c
FROM Apttus__AgreementLineItem__c
WHERE Apttus__AgreementId__c = 'a0GXXXXXXXXXXXX'

-- Check FX rates for a currency
SELECT Id, IsoCode, ConversionRate, StartDate
FROM DatedConversionRate
WHERE IsoCode = 'EUR'
ORDER BY StartDate DESC
LIMIT 10

-- Check SSR related agreements
SELECT Id, Apttus__ContractFrom__c, Apttus__ContractTo__c, Apttus__RelationshipType__c
FROM Apttus__APTS_Related_Agreement__c
WHERE Apttus__ContractTo__c = 'a0GXXXXXXXXXXXX'
```

## Common Issues

| Issue | Cause | Investigation |
|-------|-------|---------------|
| ARR doesn't match Salesforce TCV | TCV correction not applied | Check `stg_em_lkp_wd_fin_tcv_correction` |
| Missing lines in finance model | Agreement status not Activated | Filter on `status = 'Activated'` in staging |
| Currency conversion wrong | FX rate date mismatch | Verify `datedconversionrate` join uses correct date |
| ACV inflated | Non-primary proposal lines included | Filter `is_primary_proposal = true` |
| SSR showing as churn + new | SSR mapping not joined | Verify `ssr_agreement_relationship` is in the lineage |
| Agreement total != sum of lines | Amendment created new lines without deactivating old | Check for duplicate active lines per agreement |

## Constraints

- Salesforce is the system of record for contract data — staging models must reflect source exactly.
- TCV corrections are overrides — always apply `COALESCE(corrected_tcv, raw_tcv)`.
- Currency conversion must use `DatedConversionRate` (not static rates).
- SSR logic must flow through `ssr_agreement_relationship` — never manually classify.
- Every finance metric must trace back to a specific Salesforce object and field.
- Use SCD2 models for any historical or as-of-date analysis.
