---
description: Detect ref/source updates, rebuild ARR pipeline in dev, validate against prod, and issue PASS or FAIL + rollback alert before tonight's production load.
---

# FQC-ARR Regression Test

Detect recent Google Sheet ref-file or source-system updates, rebuild the full ARR
pipeline in `finance_dev` using production code, validate against `finance_prod`, and
issue a **PASS** (safe for tonight's prod load) or **FAIL + rollback alert** verdict.

## When to use

- "fcq-arr regression test"
- "regression test the ref updates before tonight's prod load"
- "validate source changes and rebuild dev before prod refresh"
- "check if gsheet changes are safe for production"
- Any pre-production-load sanity check after ref-file or source-system updates

## Inputs

| Parameter | Default | Description |
|---|---|---|
| `lookback_hours` | 48 | How far back to scan for source changes |
| `dev_db` | `finance_dev` | Non-prod target database for the rebuild |
| `prod_db` | `finance_prod` | Production baseline for comparison |
| `qa_db` | `finance_qa` | Optional second baseline (cross-check) |
| `as_was_dates` | auto-detect (latest 2 in prod) | Snapshot dates to validate |
| `slack_user` | `U03GK3V2FQU` | Slack DM target for verdict |
| `tolerance_pct` | `0.01` | Max acceptable % drift per metric |
| `tolerance_abs` | `1.00` | Max acceptable absolute $ drift |

## Phase 1: Detect Source Changes

Scan all Google Sheet ref tables that feed the ARR pipeline for recent updates.

### Ref tables to scan

```sql
-- Run via Snowflake MCP for each ref table
select
    '<TABLE_NAME>' as ref_table,
    count(*) as total_rows,
    max(_fivetran_synced) as last_synced,
    max(created_date) as latest_batch,
    count(case when _fivetran_synced >= dateadd(hour, -<LOOKBACK>, current_timestamp()) then 1 end) as rows_updated_in_window
from base_prod.google_sheets.<TABLE_NAME>;
```

### Known ref tables (check all)

| Ref View | Source Table | Downstream Impact |
|---|---|---|
| `stg_em_vw_ref_strategic_partners` | `base_prod.google_sheets.ref_strategic_partners_ref_strategic_partners` | `is_strategic_partner`, `partner_type`, `program_name` |
| `stg_em_vw_ref_product_hierarchy` | `base_prod.google_sheets.ref_product_hierarchy_ref_product_hierarchy` | All product codes L1-L5, `buying_center`, `financial_ai_category` |
| `stg_em_vw_ref_sku_swap` | `base_prod.google_sheets.ref_sku_swap_*` | SKU swap logic, ARR category reclassification |
| `stg_em_vw_ref_acquisitions` | `base_prod.google_sheets.ref_acquisitions_*` | Acquisition flags, pre-acquisition splits |
| `stg_em_vw_ref_ee_band_size` | `base_prod.google_sheets.ref_ee_band_size_*` | Employee band sizing |
| `stg_em_vw_ref_acv_strategic_partners` | `base_prod.google_sheets.ref_acv_strategic_partners_*` | ACV strategic partner flags |
| `stg_em_vw_ref_acv_country_company` | `base_prod.google_sheets.ref_acv_country_company_*` | Country/company mapping |
| `stg_em_vw_ref_acv_region_segment_summary` | `base_prod.google_sheets.ref_acv_region_segment_summary_*` | Region/segment rollup |
| `stg_em_vw_ref_acv_quote_reconciliation_override` | `base_prod.google_sheets.ref_acv_quote_reconciliation_override_*` | Quote recon overrides |
| `stg_em_vw_ref_acv_stage_classification` | `base_prod.google_sheets.ref_acv_stage_classification_*` | ACV stage classification |
| `stg_em_vw_ref_geo_hierarchy` | `base_prod.google_sheets.ref_geo_hierarchy_*` | Geo rollup hierarchy |
| `stg_em_vw_ref_industry_levels` | `base_prod.google_sheets.ref_industry_levels_*` | Industry hierarchy |

### Decision gate after Phase 1

- **No changes detected** → log "No source changes in last {lookback_hours}h. Production
  load is safe." → STOP (PASS).
- **Changes detected** → log which ref tables changed, row counts, batch dates → continue
  to Phase 2.

## Phase 2: Rebuild Pipeline in Dev

Rebuild the full ARR pipeline in `finance_dev` using the **production branch code** (main)
and the **updated source data** from `base_prod`.

### Step 2.1 — Confirm branch state

```bash
git status
git log --oneline -3
```

If on a feature branch, switch to `main` or confirm the user wants to test the feature
branch. Default: use `main` (production code).

### Step 2.2 — Parse and plan

```text
dbt MCP → parse
dbt MCP → list --select +arr_line_categories +finance_line_analytics --exclude '*_scd2'
```

### Step 2.3 — Rebuild the intermediate chain (target: dev)

Run in sequence. Stop on first hard failure.

| # | Step | dbt Selector | Notes |
|---|------|---|---|
| 1 | Ref views | `path:models/finance/int/stage/view` | Views auto-refresh; this confirms parse |
| 2 | SKU analytics intermediates | `path:models/finance/int/stage/table/tmp_tbls_of_bt_sku_analytics_optimized` `--exclude '*_scd2'` | Full table rebuilds; picks up latest ref data |
| 3 | FLA (finance_line_analytics) | `+finance_line_analytics --exclude '*_scd2'` | Incremental delete+insert on as_was_date |
| 4 | arr_line_categories | `+arr_line_categories --exclude '*_scd2'` | Heavy; use `em_heavy_warehouse` if available |
| 5 | Rollups | `arr_sku_categories arr_subproduct_categories arr_product_categories` | Siblings, run in parallel |
| 6 | Corp report | `+arr_account_product_corp_report --exclude '*_scd2'` | Final aggregate |

Pass `--vars '{"as_was_date":"'\''{LATEST_AS_WAS_DATE}'\''"}'` on steps 3-6 to target the
specific snapshot. If validating multiple as_was_dates, run once per date.

### Step 2.4 — Record build metadata

```sql
-- After rebuild, capture build timestamps
select table_schema, table_name, last_altered, row_count
from finance_dev.information_schema.tables
where table_name in (
    'ARR_LINE_CATEGORIES', 'ARR_SKU_CATEGORIES',
    'ARR_SUBPRODUCT_CATEGORIES', 'ARR_PRODUCT_CATEGORIES',
    'ARR_ACCOUNT_PRODUCT_CORP_REPORT', 'FINANCE_LINE_ANALYTICS'
)
order by table_name;
```

## Phase 3: Validate (Dev vs Prod)

### 3.1 — Row count and account/agreement parity

```sql
select
    '{ENV}' as env,
    as_was_date,
    count(*) as line_ct,
    count(distinct account_id) as accts,
    count(distinct agreement_id) as agrs
from {DB}.aggregations.arr_line_categories
where as_was_date in ({DATES})
group by 1, 2
order by 2;
```

Run for both `finance_dev` and `finance_prod`. Compute deltas.

### 3.2 — ARR totals by category

```sql
select
    '{ENV}' as env,
    as_was_date,
    arr_category,
    round(sum(split_product_line_arr_usd_current), 2) as arr_usd
from {DB}.aggregations.arr_line_categories
where as_was_date in ({DATES})
group by 1, 2, 3
order by 2, 3;
```

### 3.3 — Regression-specific checks (per changed ref table)

For each ref table that changed, run targeted validation:

#### `ref_strategic_partners` changed

```sql
-- Compare is_strategic_partner flag distribution
select
    '{ENV}' as env, as_was_date, is_strategic_partner,
    count(distinct account_id) as accts,
    count(distinct agreement_id) as agrs,
    count(*) as line_ct
from {DB}.aggregations.arr_line_categories
where as_was_date in ({DATES})
group by 1, 2, 3
order by 2, 3;
```

#### `ref_product_hierarchy` changed

```sql
-- Compare buying_center × product rollup
select
    '{ENV}' as env, as_was_date, buying_center,
    count(distinct account_id) as accts,
    round(sum(split_product_line_arr_usd_current), 0) as arr_usd
from {DB}.aggregations.arr_line_categories
where as_was_date in ({DATES})
group by 1, 2, 3
order by 2, 3;
```

#### `ref_acquisitions` changed

```sql
-- Compare acquisition/pre-acquisition splits
select
    '{ENV}' as env, as_was_date, is_acquisition,
    count(*) as line_ct,
    round(sum(split_product_line_arr_usd_current), 0) as arr_usd
from {DB}.aggregations.arr_line_categories
where as_was_date in ({DATES})
group by 1, 2, 3
order by 2, 3;
```

### 3.4 — Waterfall integrity

```sql
-- Run the waterfall balance check against dev
select fiscal_quarter_name, buying_center,
       sum(begin_balance_arr) as bb,
       sum(end_balance_arr) as eb,
       sum(net_change_arr) as net,
       abs(sum(begin_balance_arr) + sum(net_change_arr) - sum(end_balance_arr)) as imbalance
from {DB}.aggregations.arr_product_categories
where as_was_date in ({DATES})
group by 1, 2
having imbalance > 0.01
order by imbalance desc;
```

### 3.5 — Cross-environment account-level deep dive (for changed accounts)

```sql
-- For accounts affected by the ref change, compare dev vs prod line-level
with changed_accts as (
    select distinct account_id
    from {REF_TABLE}
    where _fivetran_synced >= dateadd(hour, -{LOOKBACK}, current_timestamp())
)
select
    '{ENV}' as env, a.as_was_date, a.account_id, a.agreement_id,
    a.is_strategic_partner, -- or relevant changed flag
    round(sum(a.split_product_line_arr_usd_current), 2) as arr_usd
from {DB}.aggregations.arr_line_categories a
inner join changed_accts c on a.account_id = c.account_id
where a.as_was_date in ({DATES})
group by 1, 2, 3, 4, 5
order by 2, 3, 4;
```

## Phase 4: Verdict

### Scoring matrix

| Check | Weight | PASS Criteria |
|---|---|---|
| Row count parity (dev vs prod) | 30% | Delta = 0 for unchanged as_was_dates |
| ARR total parity | 25% | `abs(dev - prod) < $1.00` per category |
| Flag distribution match | 20% | Changed flags align with ref delta direction |
| Waterfall balance | 15% | Zero imbalance rows (within $0.01) |
| No unexpected regressions | 10% | No accounts lost flags they shouldn't have |

### Verdict logic

```
IF all checks PASS:
    verdict = "PASS"
    action  = "Source updates validated in {dev_db}. Safe to proceed with tonight's
               {prod_db} production load. No business rollback needed."

ELIF only expected diffs (flag changes matching ref delta):
    verdict = "PASS WITH NOTES"
    action  = "Source updates validated. {N} accounts changed as expected per ref update.
               Proceed with production load. See detail below."

ELIF unexpected regressions found:
    verdict = "FAIL"
    action  = "ALERT: {N} unexpected regressions found. Recommend business team
               rollback the following changes from Google Sheet / source system
               BEFORE tonight's production load:
               - {ref_table}: revert {batch_date} entries
               - Affected accounts: {list}
               - Impact: {description}"
```

## Phase 5: Notify

### On PASS

```text
Slack DM to {slack_user}:
    ✅ *Regression Test PASSED* — {dev_db} as_was_date {dates}
    Source changes: {ref_tables_changed}
    Dev vs Prod: {row_delta} row delta, ${arr_delta} ARR delta
    Verdict: Safe to proceed with tonight's production load.
```

### On FAIL

```text
Slack DM to {slack_user}:
    🚨 *Regression Test FAILED* — {dev_db} as_was_date {dates}
    Source changes: {ref_tables_changed}
    Regressions: {count} unexpected account-level diffs
    Recommendation: ROLLBACK the following before tonight's prod load:
    {rollback_details}

    Full report: {document_path}
```

### Report document

Write a full validation report to:
`/Users/koteswararao.venkata/Documents/Cursor/Documents/fcq_arr_regression_test_{YYYYMMDD}.md`

Include:
- Source change summary (which ref tables, row counts, batch dates)
- Build log (dbt run results, durations)
- Validation results (all comparison tables)
- Verdict and recommended action
- Rollback instructions (if FAIL)

## Rollback Playbook (when verdict = FAIL)

### For Google Sheet ref changes

1. Notify the business owner of the sheet (include sheet name + tab).
2. Instruct: "Revert rows added on {batch_date} or mark `is_deleted = TRUE`."
3. Wait for Fivetran to sync the reverted sheet (typically < 15 min).
4. Re-run this regression test to confirm the rollback resolved the regression.

### For source system changes (SFDC, Workday, etc.)

1. Cannot rollback source systems directly — these are system of record.
2. Instead: add compensating overrides to the appropriate ref Google Sheet.
3. Or: create a dbt model fix (hotfix branch) that handles the edge case.
4. Escalate to the data engineering team if the override approach is insufficient.

### For dbt model code changes (feature branch)

1. Do NOT merge the feature branch.
2. Switch `finance_dev` back to `main` branch and rebuild.
3. Re-run the regression test to confirm baseline is restored.

## Quick-start (copy-paste)

```
fcq-arr regression test
```

Or with parameters:

```
fcq-arr regression test --lookback 24 --dates 2026-08-03,2026-08-04
```

## Dependencies

- Snowflake MCP (read queries against base_prod, finance_dev, finance_prod)
- dbt MCP (parse, list, run for rebuild)
- Slack MCP (verdict notification)
- Git (branch verification)
