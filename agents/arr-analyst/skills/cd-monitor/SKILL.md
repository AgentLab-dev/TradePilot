---
name: cd-monitor
description: After the FQC-ARR PR merges, watch the CD deployment to the finance_qa environment and re-run the ValidationMatrix against finance_qa to confirm the deployed models produce the expected ARR numbers. Use as role 9 of the FQC-ARR DAG after ci-monitor. Read-only against CD + Snowflake; does not deploy to prod.
license: Proprietary-Internal
compatibility: Requires fqc-dbt (read CD run status) and fqc-snowflake (read-only qa recheck). Optional fqc-slack notify.
metadata:
  role_order: "9"
  status_values: "ok | warn | fail"
allowed-tools: fqc-dbt.get_run_status fqc-snowflake.run_query fqc-slack.notify fqc-lessons.load_for
---

# cd-monitor

Confirm the merged change deployed cleanly to `finance_qa` and still ties out there.

## Steps
1. Track the CD/deploy run for the merged commit via `fqc-dbt.get_run_status` until it concludes.
2. Re-run each `payload.validation` `sql_template` against `finance_qa` via `fqc-snowflake.run_query`; recompute verdicts (qa is the pre-prod tie-out baseline).
3. Capture any deploy failure or `verdict=fail` into `payload.cd_report`.
4. Optionally notify the pinned Slack channel via `fqc-slack.notify`.

## Output — `payload.cd_report`
`deploy_status, validation_qa (verdicts), failures[], overall`.
- `status = ok` if deploy succeeded and qa verdicts pass/warn; `warn` on drift; `fail` on deploy failure or a failing verdict → halt + dispatch `debugger`.

## Hard rules
- Read-only — never trigger a **prod** dbt run here (that is gated + on-demand only).
- qa recheck uses `finance_qa`; never compare against prod as the target.
