---
description: Test ref_product_hierarchy changes in dev/QA — rebuild FLA + downstream, reconcile against finance_prod, and report go/no-go.
---

# Product Hierarchy Recon Test

Test the latest `ref_product_hierarchy` changes in QA/dev using production stage tables as
sources, apply the new hierarchy, rebuild FLA and downstream categorization tables, and
reconcile the non-prod output against `finance_prod` (which still runs the old hierarchy).

## Original request (verbatim)

> test latest changes of ref_product_hierarchy chaanges in QA or dev using prod tables stage
> tables as sources and apply the ref product hierarchy changes and build the output for fla
> and downstream and compare output between non prod vs prod finace_prod after applying ref
> product hierarchy, basically, testing with production code, using production stage tables
> data and processing with latest ref product hierarchy changes and compare and confirm
> recon results

## Goal

Prove that adopting the newest `base_prod.google_sheets.ref_product_hierarchy` batch produces
correct, reconcilable output for `finance_line_analytics` (FLA) and the downstream
`arr_line_categories` / `arr_product_categories` / `arr_customer_categories` tables — before it
lands in production — by running **production code** over **production stage-table data** with the
**latest hierarchy**, then diffing against current `finance_prod`.

## Inputs / conventions

- Hierarchy source: `base_prod.google_sheets.ref_product_hierarchy_ref_product_hierarchy` (raw sheet view).
- Snapshot grain: latest `as_was_date` common to prod + certified (confirm before running).
- Prod baseline: `finance_prod.managed.finance_line_analytics` + `finance_prod.aggregations.arr_*_categories`.
- Currency: one variant per comparison (default `USD_CURRENT`).
- Recon tolerance: row-count delta = 0 and $ delta < $1 at the compared grain.

## Steps

1. **Capture the hierarchy delta.** Use Snowflake Time Travel on the raw sheet view to diff the
   latest batch vs the previously processed batch: new/removed SKUs, `created_date` re-dates, and
   attribute edits (`external_sku_code`, `sku_code`, `product_group`, `product_family`,
   `buying_center`, `financial_ai_category`, `ldp_partition`). Note `NULL` vs `'None'`
   inconsistencies. Record `_fivetran_synced` and when the batch physically landed in `base_prod`.
2. **Confirm prod's current hierarchy.** Verify which hierarchy version `finance_prod` was built
   against (compare build timestamps of the refresh jobs vs when the new batch landed). This tells
   you whether the diff will actually be meaningful.
3. **Build non-prod output with prod code + prod stage data + new hierarchy.** In QA/dev, run the
   production models for FLA and the categorization tables, sourcing production stage tables and the
   latest `ref_product_hierarchy`, at the chosen `as_was_date`. (If a QA build target/job is
   unavailable, run read-only equivalent SQL that applies the new hierarchy over prod stage data.)
4. **Reconcile non-prod vs `finance_prod`.** Compare at aligned grain:
   - FLA: `agreement_line_item_id` (+ finer keys as needed) — row counts, ARR/ACV/TCV sums.
   - `arr_line_categories`: `(agreement_line_item_id, fiscal_quarter_name)` grain, category splits.
   - `arr_product_categories`: waterfall balance per `buying_center` × `fiscal_quarter`.
   - Flag rows whose category/`product_group`/`financial_ai_category` changed purely due to the
     new hierarchy; those are expected diffs, not regressions.
5. **Classify diffs.** Separate expected hierarchy-driven remaps from unexpected regressions
   (duplicates, NULL fanout, waterfall imbalance beyond pre-existing characteristics).
6. **Report + notify.** Summarize: hierarchy delta, recon PASS/FAIL per table, expected vs
   unexpected diffs, and a go/no-go recommendation for prod adoption. DM the summary to Slack via
   `slk send U03GK3V2FQU` and post progress at each major step.

## Deliverables

- Hierarchy delta summary (SKUs added/removed, attribute edits, re-dates).
- Per-table recon table (row + $ deltas) non-prod vs `finance_prod`.
- Expected-vs-unexpected diff classification with root cause for any unexpected rows.
- Go/no-go recommendation.
