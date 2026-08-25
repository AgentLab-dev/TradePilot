---
name: ci-monitor
description: Watch the CI checks on the FQC-ARR pull request until they conclude, and re-run the ValidationMatrix against finance_dev to confirm the CI build reproduces the expected ARR numbers. Surfaces failures with logs. Use as role 8 of the FQC-ARR DAG after pr-author. Read-only against CI + Snowflake.
license: Proprietary-Internal
compatibility: Requires fqc-github (pr_checks, read-only) and fqc-snowflake (read-only). Optional fqc-slack notify.
metadata:
  role_order: "8"
  status_values: "ok | warn | fail"
allowed-tools: fqc-github.pr_checks fqc-snowflake.run_query fqc-slack.notify fqc-lessons.load_for
---

# ci-monitor

Confirm the PR is green in CI and that the CI-built models still tie out.

## Steps
1. Poll `fqc-github.pr_checks(pr_number)` until all required checks conclude (success / failure / timeout).
2. On green, re-run the `payload.validation` SQL against the CI/`finance_dev` build via `fqc-snowflake.run_query`; confirm verdicts still pass/warn.
3. On failure, capture the failing check name + log excerpt into `payload.ci_report`.
4. Optionally post a status line to the pinned Slack channel via `fqc-slack.notify` (channel is set once in agent config — no per-run gate).

## Output — `payload.ci_report`
`checks[]{name,conclusion}, validation_recheck, failing_logs[], overall`.
- `status = ok` if CI green and verdicts hold; `warn` on warn-tolerance drift; `fail` if any required check fails → supervisor halts + dispatches `debugger`.

## Hard rules
- Read-only — never re-trigger prod, never write to Jira/GitHub here.
- Slack channel is pinned once (config), not chosen per run.
