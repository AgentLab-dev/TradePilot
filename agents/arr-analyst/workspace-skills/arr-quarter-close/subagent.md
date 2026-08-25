# Running the ARR Quarter Close as a Subagent

Cursor's `Task` tool does not expose an on-disk "custom subagent" format
in this workspace. The closest stable pattern is: launch a
**generalPurpose** subagent (or **shell** for execution-heavy runs) and
pass it the close instructions verbatim. The subagent then reads the
skill + rule that already live in this repo and drives the close.

## Why use a subagent instead of running in-thread

- **Isolation**: the close emits a lot of dbt log output; running it in a
  subagent keeps the parent thread readable.
- **Parallelism**: when you need to close multiple snapshots back-to-back
  (e.g. quarter-end backfill), launch one subagent per snapshot.
- **Hand-off**: the close result is returned as a single structured
  summary the parent thread can post to Slack / Jira / a status doc.

## Launch convention

Use this `Task` invocation shape (parent thread):

```text
subagent_type: generalPurpose
description: "ARR close <DATE>"
prompt: |
  You are running the eda-dbt-em ARR quarter close for as_was_date=<DATE>
  on target <TARGET>. Follow this workflow exactly:

  1. Read `.cursor/skills/arr-quarter-close/SKILL.md` and follow it.
  2. Apply `.cursor/rules/arr-quarter-close.mdc` guardrails on every step.
  3. Prefer the orchestrator:
       python -m agents.arr_quarter_close.cli \
         --as-was-date <DATE> --project-dir . --target <TARGET> --json
     Use the dbt MCP only if the orchestrator is unavailable.
  4. Stop on the first hard failure in build steps. Validation steps
     (test_arr_waterfall_balance, tag:ia_migration) WARN; report and
     continue.
  5. Return: a single JSON object with overall_status, per-step status +
     duration, and the count of failing rows for each validation step.

  Do not edit any files. Do not commit. Do not run --target prod unless
  the parent thread explicitly authorized it (it has not unless you see
  the literal token "PROD_AUTHORIZED=<DATE>").
```

## When to use which subagent type

| Subagent | When |
|---|---|
| `generalPurpose` | Default. Reads the skill, drives dbt via MCP, summarizes. |
| `shell` | Use when the dbt MCP is unavailable and the close must run via the local CLI; the prompt should still reference the orchestrator. |
| Anything else | Not appropriate for this skill. |

## Parent-thread responsibilities

After the subagent returns:

- Verify the JSON summary parses and `overall_status` is one of
  `success` / `warn` / `fail`.
- If `warn`, surface the failing-row counts and ask the user whether to
  drill into them via Snowflake MCP.
- If `fail`, surface the failing step's `stderr_tail` and propose the
  smallest-possible rerun (e.g. only step 3 + validation).

## Anti-patterns

- Do **not** pass the full ARR runbook in the subagent prompt - reference
  the skill and rule paths instead. They are the source of truth.
- Do **not** authorize prod runs at the subagent level. Authorization
  always comes from the parent thread (and ultimately the user).
- Do **not** parallelize close steps across subagents. dbt already
  parallelizes inside one run; cross-subagent parallelism creates lock
  contention on shared incremental tables.

---

## Supervisor mode - per-role Task launch templates

When driving a Jira ticket end-to-end, the supervisor uses `Task` to delegate
each of the 10 roles. Each role has its own template; the supervisor never
inlines another role's prompt. Templates:

| Role | subagent_type | Per-role skill |
|---|---|---|
| 1 jira-intake | `generalPurpose` | `subagents/01_jira_intake.md` |
| 2 requirements-analyzer | `generalPurpose` | `subagents/02_requirements_analyzer.md` |
| 3 code-data-validator | `generalPurpose` | `subagents/03_code_data_validator.md` |
| 4 clarifier | `generalPurpose` | `subagents/04_clarifier.md` |
| 5 implementer | `generalPurpose` | `subagents/05_implementer.md` |
| 6 test-runner | `shell` | `subagents/06_test_runner.md` |
| 7 pr-author | `shell` | `subagents/07_pr_author.md` |
| 8 ci-monitor | `shell` | `subagents/08_ci_monitor.md` |
| 9 cd-monitor | `shell` | `subagents/09_cd_monitor.md` |
| 10 qa-handoff | `shell` | `subagents/10_qa_handoff.md` |

Every per-role skill file documents its own launch prompt. The supervisor
parent thread copies the launch prompt verbatim and substitutes only the
ticket key / PR number / run id.

## Supervisor pause points

The supervisor pauses (returns `needs_input` from the role) at four
predictable points; the parent thread must surface them as approval gates:

1. After clarifier renders the ADF payload (before Jira POST).
2. After pr-author drafts the PR (before `git push` + `gh pr create`).
3. Before ci-monitor starts (so the Slack channel can be pinned once).
4. After qa-handoff renders the ADF preview (before final Jira POST).

`--auto` (=`auth_mode=full_auto`) is the only way to skip these. Use
sparingly; document the authorization in the ticket.
