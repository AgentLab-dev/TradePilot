---
name: arr-quarter-close
description: Run the eda-dbt-em ARR quarter close end-to-end - stage the stg_arr_categories chain, build arr_line_categories and the SKU/subproduct/product rollups, refresh the corp report, then validate with the waterfall test and the IA-migration recon. Use when the user asks to run, drive, schedule, validate, or rerun an ARR close for a given as_was_date (typically a fiscal quarter-end snapshot like 2026-02-11), or asks to refresh ARR for a specific snapshot date.
---

# ARR Quarter Close

This skill encodes the eda-dbt-em ARR close runbook so the agent can drive
a full close - build + validate - with one ask.

## When this skill fires

Trigger phrases (and close cousins):

- "run the ARR close for `<date>`"
- "ARR quarter close as_was_date `<date>`"
- "refresh ARR for `<YYYY-MM-DD>`"
- "rerun ARR aggregations for the FY26Q3 snapshot"
- "validate the ARR waterfall for `<date>`"
- "fcq-arr regression test"
- "regression test before tonight's prod load"
- "validate source changes in dev before prod refresh"
- "check if gsheet changes are safe for production"

If the user mentions ACV, switch to the (forthcoming) `acv-quarter-close` skill
instead. ARR and ACV pipelines diverge at the line layer.

For **regression test** requests, route to the regression-tester sub-agent
(sub-agent 11). See [subagents/11_regression_tester.md](subagents/11_regression_tester.md)
and the command spec at [../../commands/fcq-arr-regression-test.md](../../commands/fcq-arr-regression-test.md).

## Prerequisites (verify before running)

1. **`as_was_date` is known.** Required. Default canonical FY close dates live
   in `dbt_project.yml::arr_refactor_as_was_date_list`:
   `2025-05-08, 2025-08-11, 2025-11-10, 2026-02-11`.
2. **dbt deps + stubs are in place.** Run `make deps` if `dbt parse` would
   fail with cross-project resolution errors (see README).
3. **dbt target is correct.** `qa` for QA validation runs, `prod` for the
   real close, `dev` for local sanity checks. Never run unattended against
   `prod` without explicit user approval.
4. **dbt MCP is available.** Prefer the `dbt` MCP server (`run` / `test` /
   `compile` / `list`) over raw shell. Fall back to shell only when MCP is
   unavailable, and announce the fallback.

## What to run (in order)

Always pass `--exclude '*_scd2'` on run steps and
`--vars '{"as_was_date":"\'YYYY-MM-DD\'"}'` (note the inner single quotes -
Snowflake needs the date literal quoted for the cast).

| # | Step | Selector | Tool |
|---|------|----------|------|
| 1 | Staging chain | `path:models/finance/int/stage/table/tmp_tbls_of_bt_arr_categories_optimized` | `dbt run` |
| 2 | Line aggregate | `+arr_line_categories` | `dbt run` (heavy; use `em_heavy_warehouse` if available) |
| 3 | Rollups | `arr_sku_categories arr_subproduct_categories arr_product_categories` | `dbt run` |
| 4 | Corp report | `+arr_account_product_corp_report` | `dbt run` |
| 5 | Dashboards (optional) | `path:models/finance/modeled/data_product/view` | `dbt run` |
| 6 | Waterfall test | `test_arr_waterfall_balance` | `dbt test` |
| 7 | IA migration recon | `tag:ia_migration` | `dbt test` |

Stop on the first hard failure in steps 1-4. Validation tests (6, 7) have
`severity='warn'` and `store_failures=true` - report warnings, do not stop.

## Run flow

```
Task Progress:
- [ ] Confirm as_was_date and target
- [ ] Stage: stg_arr_categories chain
- [ ] Build: arr_line_categories
- [ ] Build: arr_sku/subproduct/product_categories
- [ ] Build: arr_account_product_corp_report
- [ ] (Optional) Refresh dashboards
- [ ] Validate: test_arr_waterfall_balance
- [ ] Validate: tag:ia_migration (skip if user opted out)
- [ ] Summarize: overall status + per-step durations + any failing test rows
```

## Two execution paths

### Path A - delegate to the orchestrator (recommended)

The portable Python orchestrator already encodes this runbook. Use it when
the user wants a deterministic, reproducible close:

```bash
python -m agents.arr_quarter_close.cli \
  --as-was-date <YYYY-MM-DD> \
  --project-dir . \
  --target qa
```

Add `--dry-run` to print planned commands without executing,
`--refresh-dashboards` to include step 5, `--no-ia-migration-tests` to skip
step 7, and `--json` for a machine-readable result.

### Path B - drive dbt MCP directly

Use when the user wants per-step interactivity or wants the agent to make
judgment calls between steps (e.g. inspect failing rows before proceeding).
Issue each step's dbt command via the `dbt` MCP `run` / `test` tools.

## When validation warns

Validation tests warn (not fail) by design. Locations of failing rows:

- `test_arr_waterfall_balance` -> `<env>.stage.test_arr_waterfall_balance`
- `tag:ia_migration` tests -> see `tests/README_finance_prod_validation_tests.md`
  (per-test names like `test_finance_prod_vs_certified_prod_arr_line`).

If failures appear:

1. Read the failing-rows table via Snowflake MCP.
2. Group by `fiscal_quarter_name` / `buying_center` / `check_level` to
   localize.
3. For waterfall: confirm `arr_product_categories` for the snapshot is the
   one just built (`as_was_date` matches input).
4. For IA recon: confirm the legacy `certified_prod.finance.*` table is at
   the same snapshot date.

## Additional resources

- Full runbook with command transcripts: [runbook.md](runbook.md)
- Validation checks and tie-out queries: [validation.md](validation.md)
- Plan-only utility (no execution): [scripts/plan_close.py](scripts/plan_close.py)
