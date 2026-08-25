---
name: code-data-validator
description: Pre-flight an ARR change by scanning the eda-dbt-em repo for affected models/macros and building a ValidationMatrix of Snowflake tie-out checks (Salesforce source vs finance_prod baseline vs finance_dev/qa target). Emits auditable SQL templates; never opens a Snowflake connection. Use as role 3 of the FQC-ARR DAG after requirements-analyzer.
license: Proprietary-Internal
compatibility: Requires fqc-snowflake (read-only) to populate the matrix; repo scan via ripgrep. Read-only.
metadata:
  role_order: "3"
  status_values: "ok | warn"
allowed-tools: fqc-snowflake.run_query fqc-lessons.load_for
---

# code-data-validator

Build the baseline validation matrix and the affected-object inventory before any code changes.

## Steps
1. From `payload.requirements`, resolve affected dbt models + macros (repo scan).
2. Build a `ValidationMatrix` (target_db = `finance_prod` baseline). Each `ValidationCheck` row has 9 columns: `check_name, grain, source_salesforce, baseline_prod, target_dev_qa, expected, actual, business_logic, verdict`, plus an auditable CTE-based `sql_template` (`sf_source`, `prod_baseline`, `dev_target` CTEs).
3. Populate value columns by running each `sql_template` via `fqc-snowflake.run_query` (SELECT only). Until run, `verdict = pending`.

## Standard checks (additive to existing dbt tests)
`waterfall_balance_per_category`, `total_arr_at_snapshot`, `*_row_parity` (line/sku/account), `currency_variant_tie_out`, `active_account_continuity`.

## Verdict tolerances
Numeric: `<0.1% pass / <1% warn / else fail`. Row-count: `<1% pass / <5% warn / else fail`. Structural checks have no Salesforce source — leave `source_salesforce` blank, never invent one.

## Output — `payload.validation` (ValidationReport with the ValidationMatrix)
`status = ok` if all checks pass/warn within tolerance; `warn` if any need review. The matrix flows downstream verbatim (ci-monitor rebuilds vs finance_dev, cd-monitor vs finance_qa).

## Hard rules
- Never open a Snowflake connection — only `fqc-snowflake.run_query` (readOnlyHint).
- Never replace a `pending` verdict with a fabricated value.
