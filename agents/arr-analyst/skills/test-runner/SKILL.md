---
name: test-runner
description: Build and test the implementer's feature branch against finance_dev — run dbt build/test on the changed models plus the FQC-ARR validation suite (waterfall balance, row parity, currency tie-out) and re-run the ValidationMatrix SQL to fill actual values and verdicts. Use as role 6 of the FQC-ARR DAG after implementer. Dev-target only; no prod, no writes to human systems.
license: Proprietary-Internal
compatibility: Requires fqc-dbt (dev/qa build+test) and fqc-snowflake (read-only re-check). No prod runs here.
metadata:
  role_order: "6"
  status_values: "ok | warn | fail"
allowed-tools: fqc-dbt.build fqc-dbt.test fqc-snowflake.run_query fqc-lessons.load_for
---

# test-runner

Prove the change is correct in `finance_dev` before it can become a PR. This role turns the `pending` ValidationMatrix into real verdicts.

## Steps
1. `fqc-dbt.build` the changed models + downstream on `--target dev`, then `fqc-dbt.test` the affected models and the FQC-ARR test suite.
2. Re-run each `sql_template` from `payload.validation` via `fqc-snowflake.run_query` against `finance_dev`; fill `actual` and compute `verdict` using the standard tolerances.
3. Collect dbt test failures + any `verdict=fail` rows into a `test_report`.

## Output — `payload.test_report`
`dbt_results[]{node,status}, validation_matrix (verdicts filled), failures[], overall`.
- `status = ok` if dbt tests pass and all matrix verdicts pass/warn.
- `warn` if only warn-tolerance drift.
- `fail` if any dbt test fails or any matrix verdict fails → supervisor halts and dispatches `debugger`.

## Hard rules
- Dev target only (`--target dev`); never `prod`.
- Do not fabricate a passing verdict — a matrix row without a real Snowflake result stays `pending` and counts as not-yet-passed.
- Read Snowflake only via `fqc-snowflake.run_query` (readOnlyHint).
