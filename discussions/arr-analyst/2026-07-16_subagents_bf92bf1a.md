# Chat — You are auditing downstream impact in the **eda-dbt-cx** repo (Workday ED&A cust…

- **Agent bucket:** `arr-analyst`
- **Cursor project:** `Users-koteswararao-venkata-Documents-Cursor-eda-dbt-em`
- **Transcript id:** `subagents`
- **Last updated:** 2026-07-16T19:01:28
- **Turns kept:** 17 (user/assistant text only; tool payloads omitted)

---

## 1. user

<timestamp>Thursday, Jul 16, 2026, 6:56 PM (UTC-7)</timestamp>
<user_query>
You are auditing downstream impact in the **eda-dbt-cx** repo (Workday ED&A customer-experience dbt project) for an upstream base-layer PR.

## Background (critical, read carefully)
`eda-dbt-base` PR #491 ("fix contract mismatch") changes only the `data_type:` declarations in base-model YAML files. Base models are `select *` **passthrough** from Fivetran sources with `contract: enforced: true`. Changing the YAML `data_type` does NOT physically retype any Snowflake column — downstream physically reads the SAME bytes. The ONLY ways CX can break are:
  (a) a CX model with `contract: enforced: true` declaring one of these columns with a conflicting type, OR
  (b) CX SQL that depends on type behavior (arithmetic on a now-text column, boolean logic, type-sensitive join/compare). Note: CX is believed to CAST monetary amounts to NUMBER(18,2) defensively — verify this.

## The 52 changed columns (token : transition)
number→float: forecast_value, quota_value, global_pipeline, global_acv, calc_q_4_pct_ramp, tcv_hist_convert, sales_uplift_acv_hist_convert, acv_list_hist_convert, cash_upfront_hist_convert, foreign_to_usd_currency, sku_sales_acv_hist_convert, opp_amount_hist_convert, wam, cash_upfront__c, static_pepy_eg_ratio__c, apts_subscription_relationship_rollup__c, tcv_number__c, exit_year_acv__c, financial_acv_2__c, base_price__c, sync_list_price_services__c, list_price__c, quote_tcv_decimal__c, acv_list__c, planning_acv__c, net_price__c, quote_tcv__c, sync_tcv__c, net_baseline__c, total_disc_rate_pepy__c, prism_analytics_acv__c, education_tcv__c, tcv_no_discount__c, total_list_price__c
number→text: visit_search_engine, post_search_engine, ref_type
text→float: clm_quoteacvamount__c, clm_quotetcvamount__c, opm_acvamount__c, rate__c, total_workers_by_sku__c, pro_pkg_tier_price__c, apts_sourcing_quantity__c
text→boolean: opm_populaterenewalbaselineacv__c, opm_populateacvamount__c, cmn_copadoorgrecordidmatch__c, sales_reporting_sku__c, integrate_to_workday__c
text→number: apts_reporting_history_month_price__c, apts_total_reporting_months__c, apts_accounting_net_price__c

## Your tasks
1. Get repo on **prod** branch: reuse /tmp/eda-dbt-cx_prod if present and on prod, else `gh repo clone workday-inc/eda-dbt-cx /tmp/cx_prod_audit -- --depth 1 --branch prod`.
2. For EVERY column token, ripgrep ALL `.sql` and `.yml/.yaml` under `models/`. Record each hit: model, base column selected?, enforced-contract with declared `data_type`?, used in arithmetic/CAST/boolean/join?.
3. Specifically verify the churn/loyalty models (e.g., churn_risk_account_segmentation_detail) and whether they CAST amounts (insulating them).
4. Cross-check physical prod types via snowflake MCP (`user-snowflake`/`snowflake_query`) against relevant `*_prod` CX database `information_schema.columns`.
5. Optional compile-level e2e ONLY if no interactive SSO hang; else skip and say so.

## Deliverable (return exactly)
- One-line verdict: **SAFE** or **AT-RISK**.
- If AT-RISK: each risky model + column + reason.
- Table of columns actually consumed by CX (model → column → how used → CAST? → physical prod type).
- Explicitly confirm whether CX CASTs amounts (and thus is insulated).
Be concise, cite files/lines and query results. Do not assume.
</user_query>

## 2. assistant

I'm going to start the audit by setting up the repository and cloning it to begin the review process.

## 3. assistant

I need to pull the latest changes from the repo and verify it's running on prod, then get the ripgrep audit set up.

## 4. assistant

The repo is already on production and current. I'm going to search through all 52 columns by building a single ripgrep command with alternation to match multiple tokens at once, then write those tokens to a file for efficient searching.

## 5. assistant

I'm searching through the models directory for SQL and YAML files, doing a case-insensitive word-boundary match on each token and tallying the results.

## 6. assistant

I found only two tokens matching my search: `wam` with 3 hits and `exit_year_acv__c` with 1 hit, though `wam` is probably a false positive since it's likely part of another word. I should verify both of these and also check whether the word-boundary flag is accidentally filtering out any columns with the `__c` suffix.

The underscore is treated as a word character, so the word-boundary search on `exit_year_acv__c` correctly requires boundaries at the start and after the final `c`. This should work fine even for qualified column names like `agreement.list_price__c` since the dot acts as a boundary. The real question is whether I'm missing any hits — for instance, `list_price__c` and `total_list_price__c` both returned zero results, which seems odd. Let me look at the actual matches to understand what's happening.

## 7. assistant

The `wam` references are actually false positives—they're just column aliases like `wam_status` being renamed in the output, not actual references to a base `wam` column. Similarly, `a.wam_status` is a different column entirely, so `wam` isn't being used at all. For `exit_year_acv__c`, it's an alias for `r.acv_exit_year`, which means that column is being consumed through the aliasing.

Actually, wait—the base column `exit_year_acv__c` changed from number to float, but the CX model is pulling from `r.acv_exit_year`, not the base column directly. So the base column isn't actually being referenced. This pattern suggests none of the 52 changed base columns are actually consumed by CX models, which would make this safe. But I need to check whether CX models use `select *` from base sources, which would implicitly carry columns through without naming them explicitly. Even if they do, changing the YAML data type on the base doesn't retype the physical column, and if CX doesn't enforce contracts or do type-sensitive operations, it should still be safe. Let me verify whether any CX models have enforced contracts and whether they're selecting these columns implicitly through `select *`.

Now I'm looking at the churn model specifically since it's the flagged one—I need to check how it sources its data and whether it's doing any type casting on amounts.

## 8. assistant

I'm checking whether any of the 32 enforced-contract models have YAML files that declare conflicting data types for those 52 columns, though I already confirmed none of those tokens appear in the YAML files under models/. Let me verify this specifically in the YAML files to be certain.

Since the token counts were zero for all but two columns, and those two hits were only in SQL files, no YAML declares these columns, so condition (a) isn't met. Even if a CX enforced model reselected a base column, it would use the same name, and since none of the 52 names appear in any YAML, condition (a) is definitively ruled out.

For condition (b), only the churn model referenced anything related, but those were different columns like wam_status and acv_exit_year, not the 52 base columns themselves. I should check whether CX does broad select * operations from base sources that might implicitly carry these columns, and then examine the churn model's full SQL and its lineage to confirm whether any CASTs are involved.

## 9. assistant

Looking at the churn model's data sources, it pulls from several dbt models including account, opportunity, activity history, campaign member, proposal line, and proposal tables from the GTM layer, along with the customer SKU heatmap and Gainsight company data, plus one base layer reference for the Salesforce opportunity history.

The monetary amounts like `exit_year_acv__c` are explicitly cast to NUMBER(18,2) format, which confirms the defensive casting approach. Since the churn model doesn't directly consume the base models with those 52 columns, the changes in PR #491 won't impact it directly.

I need to check whether any CX models reference the eda_dbt_base tables directly or use select * patterns that would implicitly pull in the modified columns, since the token search only caught explicit column references and the two output aliases.

## 10. assistant

Now let me verify via Snowflake. First, I'll confirm the CX prod database name and check whether any CX-materialized table physically carries any of the 52 columns.

The main issue is that `select *` queries from base models could implicitly pull in those 52 columns, and then they get redeclared in enforced contracts or used in type-sensitive operations, creating conflicts. I need to trace which base source tables actually contain these 52 columns — they're coming from the PR #491 base YAML changes, particularly from tables like Salesforce opportunity with fields like forecast_value, quota_value, and exit_year_acv__c.

Looking at the CX models that reference these base tables directly, some do use `select *`, which means the columns would pass through. But here's the key: for this to actually break something, either the CX model would need to redeclare that column in an enforced contract with a conflicting type, or the CX SQL would need to reference the column by name in a type-sensitive operation. Since none of the 52 column tokens appear anywhere in the CX SQL or YAML files (except for the two aliases already identified), neither condition can occur — the columns just flow through unchanged without ever being explicitly named. Downstream consumers would also need to reference these columns by name to be affected, and nothing does. Let me verify the enforced-contract CX models to confirm none of them do broad selects from base tables containing the 52 columns — I'll query the CX production database's information schema to check if any of these columns physically materialized there, which would indicate passthrough via select *.

## 11. assistant

Looking at the CX database naming conventions, there are three main databases—activation_usage_adoption, loyalty_advocacy, and product_implementation—each with integration variants, and in production they're suffixed with _PROD, similar to how the em repo uses CERTIFIED_PROD.

I need to query Snowflake's information_schema across these production databases to discover the actual column definitions and their physical types for the 52 columns. Let me start by checking the dbt tool schema or using the Snowflake query tool to pull this metadata directly.

## 12. assistant

I'm querying the information_schema.columns across the production databases to find matches for those 52 column names, and I need to check whether the _INT production databases exist as well. Since these are separate databases, I'll query each one's information_schema directly rather than relying on account_usage, which has latency and privilege requirements.

## 13. assistant

I'm noticing the _INT databases follow a different naming convention in the dbt_project config, but my earlier search for loyalty_advocacy patterns didn't surface them, so I need to cast a wider net to find where these are actually defined.

## 14. assistant

I'm realizing there's no need for separate INT databases—the stage schemas can just live alongside the managed and data_products schemas within the existing PROD databases. So I'll query the information_schema.columns across all three PROD databases to find those 52 columns, which will cover everything across the different schema layers.

## 15. assistant

Zero of the 52 columns exist physically in any CX prod database. Let me confirm the base-source physical types (to validate the "bytes unchanged" premise) and check the CX `select *` base tables that could plausibly carry financial columns.

The query returned zero rows, which means none of these 52 columns actually exist in any of the three CX production databases—they're not materialized by any CX model, not even through select * operations, so they don't flow downstream either. This confirms the data is safe. The `exit_year_acv__c` field in the churn model is just an alias that gets renamed to `CLOSEST_UPCOMING_RENEWAL_EX` in the final output.

Looking more closely at the intermediate steps, `exit_year_acv__c` is defined in the query but never actually referenced downstream—the downstream CTEs use the renamed version instead, so it's a dead column that doesn't get materialized. Since none of these 52 columns exist in CX, I need to verify the physical types in the base source still match what CX actually reads from it, confirming that the YAML data_type changes didn't alter the physical columns themselves. The columns the churn model actually consumes are things like `customer_arr_amount_usd`, `realized_acv_usd`, `hcm_pepy`, and `acv_exit_year`—none of which are in the 52-column list. The Snowflake scan is definitive—zero of the 52 columns materialized in CX prod, so whether those base tables contain them or the select * models exclude them, the result is the same: no passthrough. I should verify the scan covered views too since they also appear in information_schema.columns, and then pull the base source physical types from BASE_PROD to document the "bytes unchanged" premise and fill in task 4's physical type column. I need to verify that the base tables themselves don't contain these 52 columns, and check a couple of the select-all models from potentially financial base tables to be thorough. Let me query the base prod database to confirm the physical column types and ensure CX's select-star models aren't inadvertently pulling in any of the affected columns.

## 16. assistant

So I'm looking at how PR #491 aligns the base-model YAML declarations with the actual physical types from the source systems—the 52 columns in BASE_PROD (Salesforce, Redshift history, Clari) that use NUMBER, FLOAT, TEXT, and BOOLEAN—to resolve the contract mismatch between what's declared and what physically exists.

The critical finding is that CX doesn't actually read any of these 52 columns. I scanned all three CX production databases and got zero rows, meaning none of the CX tables materialize them. I searched the entire eda-dbt-cx codebase for all 52 column tokens and found only 2 hits in a single file, both of which are output aliases sourced from different GTM columns rather than direct reads of the base columns—and one of those aliases is even dead code downstream. The other 50 tokens produced no matches at all, and no CX enforced contract declares any of these 52 columns. The base YAML types align with the physical column definitions without any actual retype happening. Now I'm compiling the final deliverable table showing which columns are actually consumed by CX—since none of the 52 are used, it'll be sparse except for noting the two alias false-positives. I'm skipping the optional end-to-end dbt compile since the static analysis and physical evidence are already conclusive, and I'll document that decision in the report.

## 17. assistant

# eda-dbt-cx downstream impact audit — base PR #491

**Repo state:** `/tmp/eda-dbt-cx_prod` on `prod`, HEAD `8e19485` (`EDADEV-QA-to-PROD-20260713 (#191)`, 2026-07-16), fetched fresh.

## Verdict: **SAFE**

None of the 52 changed base columns are consumed by any CX model — not by name, not via `select *` passthrough, not in any enforced contract, not in any type-sensitive expression. There is nothing PR #491 can break in eda-dbt-cx.

---

## Evidence

**1. Static scan — all 52 tokens, every `.sql`/`.yml`/`.yaml` under `models/`**
50 of 52 tokens: **0 hits**. Only 2 tokens hit, both in one file, and both are *output aliases* sourced from **different** columns (not reads of the base column):

- `wam` → aliases only, referencing a **different** column `wam_status`:

```26:30:models/loyalty_advocacy/modeled/data_products/table/churn_risk_account_segmentation_detail.sql
		a.wam_status as "hcm wam",
		a.additional_ae_name as "fins wam",
        a.super_industry as "super industry",
		a.account_tier as "account tier",
		a.wam_status as "wam status",
```

- `exit_year_acv__c` → an alias whose source is GTM's `acv_exit_year`, immediately CAST, and never referenced downstream (dead alias):

```102:106:models/loyalty_advocacy/modeled/data_products/table/churn_risk_account_segmentation_detail.sql
        r.acv_exit_year as exit_year_acv__c,
        ...
        CAST((r.acv_exit_year / conversion_rate) as NUMBER(18,2)) as "exit year acv converted",
```

Risk (a) — conflicting enforced-contract `data_type`: **0** of the 52 column names appear in any CX `.yml`/`.yaml`, so no enforced contract (32 exist) declares any of them. Impossible.
Risk (b) — type-sensitive SQL (arithmetic/boolean/join/CAST) on a changed column: **0** SQL references. Impossible.

**2. Snowflake physical cross-check (`user-snowflake`)** — scanned `information_schema.columns` of all three CX prod DBs (`ACTIVATION_USAGE_ADOPTION_PROD`, `LOYALTY_ADVOCACY_PROD`, `PRODUCT_IMPLEMENTATION_PROD`) for all 52 names → **0 rows**. No CX table or view materializes any of them, confirming there is no implicit `select *` passthrough into CX either.

**3. Base-source premise validated** — the 52 columns physically live in `BASE_PROD.*` sources with their real types (e.g. `SALESFORCE.OPPORTUNITY.EXIT_YEAR_ACV__C` = `NUMBER(35,17)`, `LIST_PRICE__C` = `NUMBER(35,17)`, `AGREEMENT_LINE_ITEM_SCD2.RATE__C` = `FLOAT`, `SALESFORCE_GTMNEXT.OPPORTUNITY.OPM_POPULATEACVAMOUNT__C` = `BOOLEAN`). PR #491 only aligns base YAML `data_type` to these physical types; no column is physically retyped, and CX reads the same bytes it always did.

---

## CX CAST insulation — confirmed

The churn/loyalty model (`churn_risk_account_segmentation_detail.sql`) CASTs **every** monetary amount to `NUMBER(18,2)` and sources those amounts from **GTM/`wd_*`** models, not the PR #491 base columns:

- `CAST((r.acv_exit_year / conversion_rate) as NUMBER(18,2))` (L106)
- `CAST((SUM(csh.realized_acv_usd)) as NUMBER(18,2))` and the two at-risk/SNI sums (L182–186)
- `CAST((pli.hcm_pepy / conversion_rate) as NUMBER(18,2))` (L229)
- final `CAST(... AS NUMBER(7,1))` / `NUMBER(26,8))` (L1178–1179)

Amount lineage is `eda_dbt_gtm` (`wd_opportunity`, `wd_proposal_line`, `wd_proposal`, `gtm_activity_unified_history`, `wd_campaign_member`) + `wd_customer_sku_heatmap` / `wd_gainsight_company`. The only `eda_dbt_base` ref that actually executes is `base_salesforce_opportunityhistory` (L268), which selects `opportunityid, createddate, stagename` — none of the 52. So CX is **doubly insulated**: it doesn't read the columns, and even the amounts it does read are defensively CAST.

---

## Columns actually consumed by CX

| Model | Column | How used | CAST? | Physical prod type |
|---|---|---|---|---|
| — | (none of the 52) | not referenced in any CX `.sql`/`.yml` | — | not present in any CX prod DB (0 rows) |
| churn_risk_account_segmentation_detail.sql:26,27,30 | `wam` *(false positive)* | output alias of a **different** column `wam_status` | n/a | base `wam` not read |
| churn_risk_account_segmentation_detail.sql:102 | `exit_year_acv__c` *(false positive)* | output alias of GTM `acv_exit_year`; dead downstream; value used is `CAST(... NUMBER(18,2))` | Yes | base `exit_year_acv__c` not read |

**Optional compile-level e2e:** skipped — not run. The static scan (0 real references) plus the physical Snowflake scan (0 materialized columns) are conclusive, so a compile adds no signal and I avoided any risk of an interactive SSO/long-run hang.
