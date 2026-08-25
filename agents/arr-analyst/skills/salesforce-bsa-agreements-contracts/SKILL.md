---
name: salesforce-bsa-agreements-contracts
description: Salesforce BSA expertise for Apttus CPQ agreement lifecycle, agreement line items, invoices, entitlements, contracts, deals, SSR (supersede and replace), order forms, asset management, billing schedules, and payment terms. Use when working with agreement objects, contract management, deal structuring, entitlement tracking, invoice details, billing configuration, amendment workflows, or renewal processes in Salesforce and dbt models.
---

# Salesforce BSA — Agreements, Invoices, Entitlements, Contracts & Deals

Role: Salesforce Business Systems Analyst specializing in Apttus CPQ contract management — agreement lifecycle, line item configuration, billing and invoicing, entitlement management, deal structuring, and amendment/renewal workflows.

## Raw Salesforce Data Source

All raw Salesforce tables are in `BASE_PROD.SALESFORCE` (307+ tables via Fivetran). Key tables for this domain:

### Agreement & Contract Objects

| Raw Table (`BASE_PROD.SALESFORCE`) | SCD2 Version | Purpose |
|-------------------------------------|-------------|---------|
| `APTTUS__APTS_AGREEMENT__C` | `AGREEMENT_SCD2` | Master agreement/contract record |
| `APTTUS__AGREEMENTLINEITEM__C` | `AGREEMENT_LINE_ITEM_SCD2` | SKU-level contracted terms (ARR/ACV/TCV grain) |
| `APTTUS__APTS_RELATED_AGREEMENT__C` | `RELATED_AGREEMENT_SCD2` | SSR links between old and new agreements |
| `APTTUS__APTS_AGREEMENT__HISTORY` | — | Agreement field change tracking |
| `APTTUS__AGREEMENTLINEITEM__HISTORY` | — | Line item field change tracking |
| `APTTUS_CMCONFIG__AGREEMENTRELATEDLINEITEM__C` | — | Cross-agreement line item relationships |
| `CONTRACT` | — | Standard Salesforce contract object |
| `WOH_ORDER_FORM__C` | — | Order form records |

### Deal & Proposal Objects

| Raw Table | SCD2 Version | Purpose |
|-----------|-------------|---------|
| `APTTUS_PROPOSAL__PROPOSAL__C` | `PROPOSAL_SCD2` | CPQ quotes/proposals |
| `APTTUS_PROPOSAL__PROPOSAL_LINE_ITEM__C` | `PROPOSAL_LINE_ITEM_SCD2` | Quote line items |
| `APTTUS_CONFIG2__LINEITEM__C` | `CONFIG_LINE_ITEM_SCD2` | CPQ product configuration |
| `APTTUS_CONFIG2__RELATEDLINEITEM__C` | — | Related config line items |
| `APTTUS_CONFIG2__RELATEDPRODUCT__C` | — | Related products in config |
| `APTTUS_APPROVAL__APPROVAL_REQUEST__C` | — | Deal approval requests |
| `DEAL_SUPPORT_REQUEST__C` | — | Deal support/exception requests |
| `APTTUS_QPCONFIG__PROPOSALRELATEDLINEITEM__C` | — | Proposal related line items |
| `PROPOSAL_EXTENSION__C` | — | Proposal custom extensions |

### Invoice & Billing Objects

| Raw Table | Purpose |
|-----------|---------|
| `APTS_INVOICE_DETAIL__C` | Invoice line details |
| `PAYMENT_SCHEDULE__C` | Payment schedule records |
| `APTS_SUBSCRIPTIONS_ANNUAL_FEE__C` | Annual subscription fee tracking |

### Entitlement & Asset Objects

| Raw Table | Purpose |
|-----------|---------|
| `ENTITLEMENT` | Customer service entitlements |
| `FEATURE_ENTITLEMENT__C` | Product feature entitlements |
| `TENANTUSAGEENTITLEMENT` | Tenant usage entitlements |
| `ASSET` | Customer assets (deployed products) |
| `ASSETRELATIONSHIP` | Asset-to-asset relationships |
| `APTTUS_CONFIG2__ASSETLINEITEM__C` | CPQ asset line items |
| `APTTUS_CONFIG2__ASSETLINEITEMHISTORY__C` | Asset line item change history |

### Pricing & Profitability Objects

| Raw Table | Purpose |
|-----------|---------|
| `APTTUS_CONFIG2__RELATEDPRICELISTITEM__C` | Price list items |
| `APTTUS_CONFIG2__RELATEDPRICERULESET__C` | Pricing rule sets |
| `APTS_PROFITABILITY_HIERARCHY__C` | Profitability hierarchy |
| `APTS_PROFITABILITY_HIERARCHY__HISTORY` | Profitability changes |

## Agreement Lifecycle

### State Machine

```
Draft
  → In Signatures (pending execution)
    → Activated (fully executed contract)
      ├── Amended (mid-term change → new version)
      ├── Renewed (end-of-term → new agreement)
      ├── Superseded (SSR → replaced by new agreement)
      └── Terminated / Expired
```

### Key Agreement Fields

| Field | API Name | Purpose |
|-------|----------|---------|
| Agreement Name | `NAME` | Contract identifier |
| Status | `APTTUS__STATUS__C` | Lifecycle state |
| Status Category | `APTTUS__STATUS_CATEGORY__C` | Grouped status |
| Start Date | `APTTUS__CONTRACT_START_DATE__C` | Contract effective date |
| End Date | `APTTUS__CONTRACT_END_DATE__C` | Contract expiry |
| Execution Date | `APTTUS__APTS_AGREEMENT_EXEC_DATE__C` | Signed date |
| Termination Date | `APTTUS__TERMINATION_DATE__C` | Early termination |
| Auto Renew | `APTTUS__AUTO_RENEWAL__C` | Auto-renewal flag |
| Account | `APTTUS__ACCOUNT__C` | Customer account |
| Parent Agreement | `APTTUS__PARENTAGREEMENTID__C` | Master agreement |
| Opportunity | `APTTUS__RELATED_OPPORTUNITY__C` | Source deal |
| Total Fees | `TOTAL_FEES__C` | Agreement-level TCV |
| Currency | `CURRENCYISOCODE` | Transaction currency |
| Order Form Number | `ORDER_FORM_NUMBER__C` | Order form reference |
| Contract Number in Workday | `CONTRACT_NUMBER_IN_WORKDAY__C` | Workday integration ID |

## Agreement Line Item — The Finance Grain

Agreement Line Item is the **primary grain** for all finance metrics (ARR, ACV, TCV). Key fields:

### Financial Fields

| Field | Purpose |
|-------|---------|
| `TCV__C` / `TOTAL_CONTRACT_VALUE__C` | Total Contract Value |
| `ACV__C` | Annual Contract Value |
| `SALES_ACV__C` | Sales-attributed ACV |
| `EYACV__C` | Exit Year ACV |
| `TOTAL_FEES__C` | Total fees for the line |
| `BOOKINGS__C` | Booking amount |
| `PEPY__C` | Per Employee Per Year |
| `UNIT_PRICE__C` | Unit price |
| `APTTUS__NETPRICE__C` | Net price after adjustments |
| `APTTUS__LISTPRICE__C` | List price before discounts |
| `APTTUS__QUANTITY__C` | Contracted quantity |
| `CURRENCYISOCODE` | Transaction currency |

### Term & Date Fields

| Field | Purpose |
|-------|---------|
| `APTTUS_CMCONFIG__STARTDATE__C` | Line start date |
| `APTTUS_CMCONFIG__ENDDATE__C` | Line end date |
| `APTS_TERM_START_DATE__C` | Term start |
| `APTS_TERM_END_DATE__C` | Term end |
| `APTS_SKU_START_DATE__C` | SKU-level start |
| `APTS_SKU_END_DATE__C` | SKU-level end |
| `SKU_TERMINATION_DATE__C` | SKU termination |
| `NET_START_DATE__C` / `NET_END_DATE__C` | Net effective dates |

### Product & SKU Fields

| Field | Purpose |
|-------|---------|
| `PRODUCT_SKU__C` | SKU identifier |
| `SKU_NAME__C` / `SKU_CODE__C` | SKU name and code |
| `PRODUCT_CODE_FINAL__C` | Final product code |
| `PRODUCT_FAMILY_TYPE__C` | Product family |
| `APTS_PRODUCT_FAMILY__C` | Apttus product family |
| `PURCHASE_TYPE__C` | New, Add-on, Renewal |
| `COMMERCIAL_LIFECYCLE_STAGE__C` | Lifecycle stage |

### Status & Amendment Fields

| Field | Purpose |
|-------|---------|
| `APTTUS_CMCONFIG__LINESTATUS__C` | New, Amended, Renewed |
| `STATUS_CATEGORY__C` | Status grouping |
| `SKU_ADDED_VIA_AMENDMENT__C` | Amendment flag |
| `AMENDED_QUANTITY__C` | Post-amendment quantity |
| `AMENDED_TOTAL_FEES__C` | Post-amendment fees |
| `APTS_EXPANSION_TYPE__C` | Upsell, Cross-sell |
| `APTS_EXPANSION_QUANTITY__C` | Expansion quantity |

## Staging-to-Finance Model Chain

```
BASE_PROD.SALESFORCE.APTTUS__APTS_AGREEMENT__C
  → BASE_PROD.REDSHIFT_HISTORY.AGREEMENT_SCD2
    → stg_em_agreement_scd2 / stg_em_agreement_as_was
      → stg_em_agree_source_temp / stg_em_int_agree_base
        → stg_em_int_agree_enriched
          → stg_em_int_agree_ssr_adjusted
            → bt_sku_analytics
              → bt_*_arr_categories / finance_line_analytics

BASE_PROD.SALESFORCE.APTTUS__AGREEMENTLINEITEM__C
  → BASE_PROD.REDSHIFT_HISTORY.AGREEMENT_LINE_ITEM_SCD2
    → stg_em_agreement_line_item_scd2 / stg_em_agreement_line_as_was
      → stg_em_int_financial_metrics (TCV→ARR/ACV derivation)
        → bt_sku_analytics
```

## SSR (Supersede & Replace) Mechanics

### How SSR Works

1. Old agreement → status changes to **Superseded**
2. New agreement created, linked via `APTTUS__APTS_RELATED_AGREEMENT__C`
3. `ssr_agreement_relationship` model resolves the old ↔ new mapping
4. SSR functions: `ssr_process`, `is_superseded`, `is_superseding`

### SSR Data Model

```
ssr_agreement_relationship columns:
  ├── agreement_id / agreement_name          (new agreement)
  ├── superseded_agreement_id / name         (old agreement)
  ├── account_id / account_name
  ├── contract_number_in_workday
  ├── order_form_number
  ├── agreement_start_date / end_date
  ├── superseded_agreement_start_date / end_date
  ├── execution_date / superseded_execution_date
  └── ssr_process                            (superseded status)
```

### SSR Rules

- SSR is a **continuity event** — ARR moves from old to new agreement.
- ARR category = FLAT_RENEWAL, EXPANSION, or CONTRACTION — **never** CHURN + NEW.
- The `stg_em_int_agree_ssr_adjusted` model applies SSR adjustments in the intermediate layer.

## Amendment Workflow

```
Original Agreement (Activated)
  → Amendment initiated
    → New line items created (SKU_ADDED_VIA_AMENDMENT__C = true)
    → Original lines may be updated (AMENDED_QUANTITY__C, AMENDED_TOTAL_FEES__C)
    → Agreement status → Amended
      → Activation of amended version
```

### Amendment Impact on Finance

- **Incremental ACV** = New line ACV - Original line ACV
- Mid-term amendments: annualize the delta for the remaining term
- Track via `APTTUS_CMCONFIG__LINESTATUS__C = 'Amended'`
- `PURCHASE_TYPE__C` distinguishes New vs Add-on vs Renewal lines

## Renewal Workflow

```
Active Agreement approaching end_date
  → up_for_renewal function identifies renewal candidates
    → Renewal opportunity created
      → New proposal/quote generated
        → New agreement activated
          → Old agreement expires / superseded
```

### Renewal-Related Functions

| Function | Purpose |
|----------|---------|
| `up_for_renewal` | Identifies agreements up for renewal |
| `get_pending_renewals` | Flags pending renewal ARR |
| `get_begin_balances` / `get_end_balances` | ARR balance calculations |
| `get_arr_categories` | Assigns ARR movement categories |

## Entitlement Tracking

### Entitlement Types

| Object | Scope |
|--------|-------|
| `ENTITLEMENT` | Service-level entitlements (support tiers, SLAs) |
| `FEATURE_ENTITLEMENT__C` | Product feature access rights |
| `TENANTUSAGEENTITLEMENT` | Tenant usage limits and quotas |
| `NUMBER_OF_LI_ENTITLEMENTS__C` (on ALI) | Line-item-level entitlement count |

### Entitlement-to-Agreement Link

```sql
-- Entitlements derive from Agreement Line Items
-- Each ALI can generate entitlements based on product configuration
SELECT
    ali.id as agreement_line_item_id,
    ali.product_sku__c,
    ali.number_of_li_entitlements__c,
    ali.apts_term_start_date__c,
    ali.apts_term_end_date__c
FROM BASE_PROD.SALESFORCE.APTTUS__AGREEMENTLINEITEM__C ali
WHERE ali.number_of_li_entitlements__c > 0
```

## Invoice & Billing

### Invoice Detail (`APTS_INVOICE_DETAIL__C`)

Stores line-level invoice details generated from agreement lines:
- Links back to Agreement Line Item
- Contains billing period, amount, tax, currency
- Used for billing reconciliation against contracted amounts

### Payment Schedule (`PAYMENT_SCHEDULE__C`)

Tracks payment milestones and schedules:
- Payment dates, amounts, status
- Links to agreements for installment-based contracts

### Billing Configuration on ALI

Key billing fields on Agreement Line Item:
- `APTTUS_CMCONFIG__BILLINGFREQUENCY__C` — Monthly, Quarterly, Annual
- `APTTUS_CMCONFIG__BILLINGRULE__C` — Billing rule applied
- `APTTUS_CMCONFIG__BILLINGPLANID__C` — Billing plan reference
- `APTTUS_CMCONFIG__BILLINGPREFERENCEID__C` — Billing preference
- `APTTUS_CMCONFIG__AUTOCREATEBILL__C` — Auto-create billing flag
- `APTTUS_CMCONFIG__READYFORBILLINGDATE__C` — Ready for billing date

## Asset Management

### Asset Lifecycle

```
Agreement Line Item (contracted)
  → Asset created upon activation
    → Asset Line Item tracks deployed product
      → Asset Relationship links parent/child assets
```

### Key Asset Objects

| Object | Purpose |
|--------|---------|
| `ASSET` | Deployed product instance |
| `ASSETRELATIONSHIP` | Parent-child asset links |
| `APTTUS_CONFIG2__ASSETLINEITEM__C` | CPQ asset line details |
| `APTTUS_CONFIG2__ASSETLINEITEMHISTORY__C` | Asset changes over time |

## SOQL Queries for Investigation

```sql
-- Agreement with all line items
SELECT Id, Name, Apttus__Status__c, Apttus__Status_Category__c,
       Apttus__Contract_Start_Date__c, Apttus__Contract_End_Date__c,
       (SELECT Id, Product_SKU__c, TCV__c, ACV__c, Apttus__Quantity__c,
               Apttus_CMConfig__LineStatus__c, Purchase_Type__c
        FROM Apttus__AgreementLineItems__r)
FROM Apttus__APTS_Agreement__c
WHERE Id = 'a0GXXXXXXXXXXXX'

-- SSR relationships for an agreement
SELECT Id, Apttus__ContractFrom__c, Apttus__ContractTo__c,
       Apttus__RelationshipType__c
FROM Apttus__APTS_Related_Agreement__c
WHERE Apttus__ContractTo__c = 'a0GXXXXXXXXXXXX'
   OR Apttus__ContractFrom__c = 'a0GXXXXXXXXXXXX'

-- Invoice details for an agreement
SELECT Id, Name, Amount, CurrencyIsoCode
FROM APTS_Invoice_Detail__c
WHERE Agreement__c = 'a0GXXXXXXXXXXXX'

-- Entitlements for an account
SELECT Id, Name, AccountId, Status, StartDate, EndDate, Type
FROM Entitlement
WHERE AccountId = '001XXXXXXXXXXXX' AND Status = 'Active'

-- Amendments on a line item
SELECT Id, Product_SKU__c, Apttus_CMConfig__LineStatus__c,
       Amended_Quantity__c, Amended_Total_Fees__c, SKU_Added_Via_Amendment__c
FROM Apttus__AgreementLineItem__c
WHERE Apttus__AgreementId__c = 'a0GXXXXXXXXXXXX'
  AND Apttus_CMConfig__LineStatus__c = 'Amended'

-- Assets for a customer
SELECT Id, Name, AccountId, Product2Id, Quantity, Status
FROM Asset
WHERE AccountId = '001XXXXXXXXXXXX'
```

## Common Issues

| Issue | Cause | Investigation |
|-------|-------|---------------|
| Missing ARR for active agreement | Line status not Activated | Check `APTTUS_CMCONFIG__LINESTATUS__C` and `STATUS_CATEGORY__C` |
| Duplicate lines after amendment | Old lines not deactivated | Check for multiple active lines per SKU per agreement |
| SSR not reflecting in ARR | Related Agreement record missing | Verify `APTTUS__APTS_RELATED_AGREEMENT__C` has the link |
| Invoice total != agreement TCV | Billing frequency mismatch | Compare `TOTAL_FEES__C` on ALI vs sum of invoice details |
| Entitlement expired but agreement active | Entitlement dates misaligned | Compare entitlement `EndDate` vs agreement `Contract_End_Date` |
| Short-term contract ARR inflated | Annualization on sub-year terms | Use `bv_short_term_contract_validations` view for diagnostics |
| Order form number missing | Not populated at agreement creation | Check `ORDER_FORM_NUMBER__C` on agreement, fallback to Workday contract number |

## Constraints

- Agreement Line Item is the **single source of truth** for ARR/ACV/TCV — never derive from Opportunity or Proposal for contracted values.
- SSR must flow through `ssr_agreement_relationship` — never manually reclassify superseded agreements.
- Amendments create new line versions — always check `APTTUS_CMCONFIG__LINESTATUS__C` to distinguish original vs amended lines.
- Billing fields on ALI control downstream invoicing — changes require Apttus admin coordination.
- Entitlements derive from Agreement Line Items — verify the link when entitlements appear missing.
- Use SCD2 models (`as_was`) for any historical or point-in-time agreement analysis.
- The `generate_base_salesforce_model` macro creates views from `source('salesforce', table_name)` for raw table access.
