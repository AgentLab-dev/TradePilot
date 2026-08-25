# ARR Quarter Close - Runbook

Step-by-step commands the agent should run. All commands assume `cwd` is the
`eda-dbt-em` repo root and that `make deps` has been run at least once.

`<DATE>` is the canonical FY snapshot - one of `2025-05-08`, `2025-08-11`,
`2025-11-10`, `2026-02-11` (current FY27Q1 set).

`<TARGET>` is one of `dev` / `qa` / `prod`.

## 0. Sanity check (parse + plan)

Confirm the DAG parses and the selectors resolve before any heavy run:

```bash
make parse
python -m agents.arr_quarter_close.cli \
  --as-was-date <DATE> --project-dir . --dry-run
```

Or via dbt MCP:

```text
dbt MCP `list` with select=tag:arr
dbt MCP `compile` with select=+arr_line_categories
```

## 1. Staging chain

```bash
dbt run \
  --select path:models/finance/int/stage/table/tmp_tbls_of_bt_arr_categories_optimized \
  --exclude '*_scd2' \
  --target <TARGET> \
  --vars '{"as_was_date": "'\''<DATE>'\''"}'
```

This refreshes the `stg_arr_categories_*` intermediates. They are
`transient=true` + `cluster_by=['as_was_date']`; the table footprint stays
small per snapshot.

## 2. arr_line_categories (heavy)

```bash
dbt run \
  --select +arr_line_categories \
  --exclude '*_scd2' \
  --target <TARGET> \
  --vars '{"as_was_date": "'\''<DATE>'\''", "em_heavy_warehouse": "ANALYTICS_HEAVY_WH"}'
```

Drop `em_heavy_warehouse` if the env does not have a heavy warehouse
provisioned. The model is incremental `delete+insert` on `as_was_date`,
so re-running for the same snapshot is safe.

## 3. Rollups (SKU / subproduct / product)

```bash
dbt run \
  --select arr_sku_categories arr_subproduct_categories arr_product_categories \
  --exclude '*_scd2' \
  --target <TARGET> \
  --vars '{"as_was_date": "'\''<DATE>'\''"}'
```

These three are siblings in the DAG; dbt runs them in parallel up to the
configured `threads` count.

## 4. Corp report

```bash
dbt run \
  --select +arr_account_product_corp_report \
  --exclude '*_scd2' \
  --target <TARGET> \
  --vars '{"as_was_date": "'\''<DATE>'\''"}'
```

## 5. Refresh dashboards (optional)

Run this when downstream consumers (Sigma, finance dashboards) need to see
the new snapshot immediately. The views contain no business logic; the
"refresh" simply recreates the view DDL.

```bash
dbt run \
  --select path:models/finance/modeled/data_product/view \
  --exclude '*_scd2' \
  --target <TARGET> \
  --vars '{"as_was_date": "'\''<DATE>'\''"}'
```

## 6. Waterfall test

```bash
dbt test \
  --select test_arr_waterfall_balance \
  --target <TARGET> \
  --vars '{"as_was_date": "'\''<DATE>'\''"}'
```

The test passes silently when, for every `(buying_center, fiscal_quarter)`:

- `|incremental_delta|` < $0.01 (Begin + incrementals = End Balance)
- `|qoq_buying_center_delta|` < $0.01 (prior End = next Begin)

Failures land in `<env>.stage.test_arr_waterfall_balance` (severity=warn,
store_failures=true).

## 7. IA migration recon (skip after cutover)

```bash
dbt test \
  --select tag:ia_migration \
  --target <TARGET> \
  --vars '{"as_was_date": "'\''<DATE>'\''"}'
```

Compares `certified_prod.finance.arr_*` (legacy) vs `finance_prod.aggregations.arr_*`
(IA) across all five aggregates. Tolerance: exact row / account / agreement
counts; $1 USD on FLOAT sums. Failing rows are stored per test - see
`tests/README_finance_prod_validation_tests.md`.

## 8. Reporting

If the close was driven via the orchestrator, the result is already a
`CloseResult` JSON. When driving step-by-step, the agent should emit:

```text
ARR Quarter Close - as_was_date=<DATE>
Status: SUCCESS | WARN | FAIL  (duration Xs, N steps)
  [success]  stage_arr_categories_chain          120.4s
  [success]  arr_line_categories                  632.1s
  [success]  arr_rollups                          184.7s
  [success]  arr_account_product_corp_report       58.0s
  [warn]     validate_arr_waterfall                 3.2s   (2 rows in failing table)
  [success]  validate_ia_migration_recon           12.6s
```

## Backfilling a historical quarter

Use the macro path rather than the close runbook:

```bash
dbt run-operation run_arr_historical_chain_standalone \
  --vars '{"arr_refactor_as_was_date_list": ["'\''2025-05-08'\''::date", "'\''2025-08-11'\''::date"]}'
```

This skill should defer historical chains to the user - it is a different
shape (loop of snapshots) and may need extended warehouse time.
