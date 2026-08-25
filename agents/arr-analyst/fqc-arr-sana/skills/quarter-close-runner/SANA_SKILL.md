---
name: quarter-close-runner
description: Run the eda-dbt-em ARR quarter close for a snapshot (as_was_date) — stage the stg_arr_categories chain, build arr_line_categories and the SKU/subproduct/product rollups, refresh the corp report, then validate with the waterfall test and the IA-migration recon. Dispatched on-demand for scheduled/snapshot closes ("task: quarter-close [date]"), not part of the ticket DAG. Prod runs always require approval.
license: Proprietary-Internal
compatibility: Requires fqc-dbt (build/test) + fqc-snowflake (read-only validation). Prod target is destructiveHint → always gated. Wraps the existing ARRCloseOrchestrator.
metadata:
  role_order: "on-demand"
  status_values: "ok | warn | fail | needs_input"
allowed-tools: fqc-dbt.build fqc-dbt.test fqc-dbt.run fqc-snowflake.run_query fqc-lessons.load_for
---

# quarter-close-runner

Run the scheduled/snapshot ARR close end-to-end. This is the non-ticket path; it maps to the existing `arr-quarter-close` skill / `ARRCloseOrchestrator`.

## Steps
1. Resolve `as_was_date` (snapshot). Never silently edit `dbt_project.yml::arr_refactor_as_was_date_list` — if the date list must change, return `needs_input`.
2. Stage the `stg_arr_categories` chain (`fqc-dbt.build`).
3. Build `arr_line_categories` → SKU / subproduct / product rollups.
4. Refresh the ARR corp report.
5. Validate: run the **waterfall balance** test and the **IA-migration recon** via `fqc-dbt.test` + `fqc-snowflake.run_query`.

## Targets & gating
- `dev` / `qa`: run freely (non-destructive).
- **`prod`: always `needs_input`** → requires an explicit approval card before any prod build/run. Never auto.

## Output — `payload.close_report`
`as_was_date, staged[], built[], report_refreshed (bool), waterfall_result, ia_recon_result, target, overall`.
`status = ok` if built + both validations pass; `warn` on tolerance drift; `needs_input` before any prod run or date-list change; `fail` on build/validation failure.

## Hard rules
- Prod runs are always gated — no unattended prod close.
- Waterfall test + IA-migration recon are mandatory gates on the result.
- Snowflake validation is read-only (`fqc-snowflake.run_query`).
