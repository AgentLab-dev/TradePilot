# Finance ARR Quarter Close (FQC-ARR) supervisor

**Display name:** Finance ARR Quarter Close
**Short code:** FQC-ARR
**Aliases (interchangeable):** FQC, FQCARR, FQC-ARR
**Module path (stable):** `agents/arr_quarter_close/supervisor.py`

Wraps the existing `arr-quarter-close` skill with a 10-sub-agent topology
that drives a Jira ticket end-to-end (intake -> requirements -> validate ->
clarify -> implement -> test -> PR -> CI -> CD -> QA handoff).

## Two modes

| Mode | Trigger | What runs |
|---|---|---|
| `scheduled` | only `--as-was-date` | The original `ARRCloseOrchestrator` - build + validate. |
| `ticket` | `--ticket EDAEM-xxxx` | 10-sub-agent DAG. |
| `both` | both flags | Ticket DAG first; supervisor re-enters scheduled close if implementer flags `needs_snapshot_rebuild=True`. |

CLI: `python -m agents.arr_quarter_close.cli --ticket EDAEM-xxxx [--auto] [--slack-channel U03...]`

## Authorization (smart-gates default)

Smart gates pause before each WRITE step. The role's `RoleResult.status`
returns `needs_input` and the supervisor stops. To resume, re-invoke after
the user has approved (or apply changes manually).

| Pause point | Triggered by | Skip with |
|---|---|---|
| Post clarifier comment to Jira | `clarifier` returns `needs_input` | `--auto` (full_auto) |
| Push branch + open PR | `pr-author` returns `needs_input` | `--auto` |
| Pick Slack channel | `ci-monitor` returns `needs_input` if `--slack-channel` not set | always supply the channel up front |
| Post QA-readiness comment | `qa-handoff` returns `needs_input` | `--auto` |

## Slack notifications (per-role thread)

The supervisor opens one Slack thread per run and posts a threaded reply
after every sub-agent completes - including the pause/skip/fail cases.
Behavior summary:

| Flag combination | Effect |
|---|---|
| `--slack-channel U03... ` | Per-role thread enabled (default). |
| `--slack-channel U03... --no-slack` | Per-role thread disabled; CI/CD monitors still post their own heartbeats. |
| `--dry-run` | All Slack posting skipped, even with `--slack-channel`. |
| no `--slack-channel` | Per-role thread disabled. CI monitor will pause at its own slack-channel prompt. |

Posts use `slk send` for the parent message and `slackApi` over `node -e`
for threaded replies. If `slk` or `node` is missing, the notifier logs and
continues - Slack failures never block the run. Shape and icons documented
in `.cursor/rules/arr-close-supervisor.mdc`.

## Live thinking log (Markdown)

Every supervisor run writes a live, append-only Markdown trace at
`<project_dir>/runs/thinking/<UTC_ts>_<slug>.md` by default. Each
section is flushed + `fsync`'d so you can `tail -f` it from another
terminal while the run is happening and intervene with `task:` Slack
messages before the supervisor makes the wrong call.

| Flag | Effect |
|---|---|
| (default) | Live log enabled; path printed to stderr at run start. |
| `--thinking-log /path/to/file.md` | Override path (e.g. point at `~/Documents/Cursor/Documents/`). |
| `--no-thinking-log` | Disable the log entirely. |

The log captures: run metadata header, per-role "why running now" +
result + payload preview, side-tasks dispatched from Slack, supervisor
cancel/pause decisions, per-dbt-step status (Mode A), and a final
footer with queued side-tasks for follow-up.

Operator workflow:
1. Start the supervisor; copy the `Thinking log: <path>` line from stderr.
2. In another terminal: `tail -f <path>`.
3. Watch reasoning live. If a role is heading the wrong way, post
   `task: skip <role>` / `task: pause` / `task: cancel` in the Slack
   thread — the supervisor will pick it up between roles.

## Slack side-channel intake (`task:` messages)

Between every sub-agent the supervisor reads the parent thread and
treats any message starting with `task:` (case-insensitive) as an
operator-issued instruction. First-class commands run inline; anything
else is queued for later human / Cursor coding-agent action and surfaced
in the final-banner reply.

| Pattern | Effect |
|---|---|
| `task: skip <role>` | Adds `<role>` to `skip_roles` for upcoming sub-agents. |
| `task: pause` | Pauses after the current role; returns `needs_input`. |
| `task: cancel` | Aborts after the current role with `warn`. |
| `task: status` | Posts a one-line recap of the last 5 role statuses to the thread. |
| anything else | Queued on `SupervisorRunReport.side_tasks` and acked in-thread. |

Every recognized task gets a threaded ack of the form
`:incoming_envelope: side-task <action>: <result>`. The supervisor never
blocks on Slack: missing `slk` / `node`, a lost parent ts, or a Slack
API failure simply disables the drain for the remainder of the run.

## Sub-agent execution order

1. `01_jira_intake.md` - pull ticket + flatten ADF + extract AC
2. `02_requirements_analyzer.md` - KPI spec; emits LLM prompt
3. `03_code_data_validator.md` - repo scan + Snowflake validation queries
4. `04_clarifier.md` - generate Jira comment for open questions (PAUSE)
5. `05_implementer.md` - branch + LLM edit prompt (PAUSE for LLM)
6. `06_test_runner.md` - pytest + dbt test
7. `07_pr_author.md` - push + gh pr create + reviewers (PAUSE)
8. `08_ci_monitor.md` - poll every 10m + Slack heartbeat + finance_dev validation
9. `09_cd_monitor.md` - dbt Cloud run + Slack + finance_qa validation
10. `10_qa_handoff.md` - QA-ready ticket update + attachments (PAUSE)

### On-demand sub-agent (outside the canonical DAG)

11. `debugger` - dispatched whenever and wherever a failure or
    discrepancy surfaces. Walks the upstream lineage of a target model,
    builds a per-stage `ValidationMatrix`, ranks `RootCauseHypothesis`
    items, drafts a `ProposedFix` (file + LLM prompt; never writes the
    change itself), writes a dbt singular test + pytest wrapper to disk,
    and composes a Jira ADF comment **shaped by ticket type** (Bug ->
    "Root cause + reproducible fix" with repro steps; Story / Task /
    Sub-task / Epic -> "Debug findings" framing). Pauses before any Jira
    write unless `auth_mode=full_auto`. Triggers:

    | Trigger | How |
    |---|---|
    | `auto_failure` | Any DAG role returns `FAIL` and `debug_on_failure=True` (default). |
    | `side_channel` | Operator posts `task: debug` or `task: debug <model>` in the Slack thread. |
    | `cli` | `--debug-model <model>` or `--debug` on the CLI. |
    | `manual` | Direct SDK call: `debugger.run(DebugInput(...))`. |

12. `quarter-close-runner` - dispatched whenever the operator needs to
    actually run the ARR quarter close (or just the recon) for a
    snapshot. It wraps the existing `ARRCloseOrchestrator` for the
    pipeline phase (tmp_tbls -> arr_line_categories -> rollups ->
    arr_account_product_corp_report -> tests) and then builds a
    7-check ARR recon `ValidationMatrix`:

    | Check | What it ties out |
    |---|---|
    | `waterfall_balance_per_category` | Begin + sum(NEW/EXPANSION/CONTRACTION/CHURN/...) = End within tolerance. The headline ARR identity. |
    | `total_arr_at_snapshot` | Period-over-period total ARR vs prior snapshot. |
    | `arr_line_categories_row_parity` | Row count vs prior snapshot at the line grain. |
    | `arr_sku_categories_row_parity` | Row count vs prior snapshot at the SKU grain. |
    | `arr_account_product_corp_report_row_parity` | Row count vs prior snapshot at the account-product grain. |
    | `currency_variant_tie_out` | USD_CURRENT == USD_HIST for same-rate lines (catches `stg_em_datedconversionrate` regressions). |
    | `active_account_continuity` | No silently-dropped accounts (a drop without a CHURN row is a regression). |

    Triggers:

    | Trigger | How |
    |---|---|
    | `cli` | `--quarter-close` (with optional `--as-was-date`, `--quarter-close-baseline-date`, `--quarter-close-target-db`, `--quarter-close-skip-pipeline`, `--quarter-close-tolerance-pct`). When set together with `--ticket`, dispatches AFTER the DAG so the QA-handoff comment carries the recon matrix. When set alone with `--as-was-date`, replaces the standalone orchestrator path so the pipeline runs once and the matrix is built. |
    | `side_channel` | `task: quarter-close` (uses the latest known FY close from `KNOWN_FY_CLOSE_DATES`) or `task: quarter-close 2026-02-11` (explicit snapshot). |
    | `manual` | Direct SDK call: `quarter_close_runner.run(QuarterCloseInput(...))`. |

    Hard rules:

    - Never opens a Snowflake connection directly. Every recon check
      carries a `sql_template` the supervisor (or operator) runs via
      the Snowflake MCP, then re-attaches actuals with
      `quarter_close_runner._attach_actuals(report, actuals)`.
    - When the operator passes `--ticket --as-was-date --quarter-close`
      together, the inline scheduled-mode orchestrator pass is
      automatically skipped so the dbt pipeline runs exactly once.
    - When `--quarter-close-skip-pipeline` is set, the runner skips the
      dbt pipeline and only builds the recon matrix; use this when the
      snapshot is already loaded and you only want a fresh tie-out.
    - Pipeline `FAIL` is always `RoleStatus.FAIL` even if the recon
      matrix is `pending` - the matrix SQL won't be runnable until the
      tables exist.
    - The 7 checks are intentionally additive to (not a replacement
      for) `test_arr_waterfall_balance` and `tag:ia_migration` dbt
      tests that the orchestrator already runs.

13. `regression-tester` - pre-production regression test for ref-file and
    source-system updates. Detects recent changes in Google Sheet ref
    tables (`ref_strategic_partners`, `ref_product_hierarchy`,
    `ref_acquisitions`, etc.), rebuilds the full ARR pipeline in dev
    using production code, validates dev vs prod, and issues a verdict:

    - **PASS** → source updates validated; safe for tonight's prod load.
    - **PASS WITH NOTES** → expected flag changes only; proceed.
    - **FAIL** → unexpected regressions; alert business to rollback
      gsheet changes or source system updates before prod refresh.

    Triggers:

    | Trigger | How |
    |---|---|
    | `cli` | `fcq-arr regression test` or `--regression-test [--lookback 48]` |
    | `side_channel` | `task: regression-test` in Slack thread |
    | `manual` | Direct: read `subagents/11_regression_tester.md` |

    See `.cursor/commands/fcq-arr-regression-test.md` for the full
    5-phase workflow spec.

## When to use

- "drive EDAEM-3725 through ARR close" -> ticket mode.
- "run ARR close for 2026-02-11" -> scheduled mode (existing skill applies).
- "EDAEM-3725 needs to land for FY27Q1 snapshot 2026-02-11" -> both.
- "fcq-arr regression test" -> regression-tester (sub-agent 13).
- "validate gsheet changes before tonight's prod load" -> regression-tester.

## Validation matrix (7-column comparison shape)

Every validation-producing sub-agent (`code-data-validator`,
`test-runner`, `ci-monitor`, `cd-monitor`) attaches a
`ValidationMatrix` to its `RoleResult.payload`. The matrix is a list of
`ValidationCheck` rows, each with the same nine fields the operator
expects when reviewing a metric change:

| Column | Meaning |
|---|---|
| `check_name` | Human-friendly label (e.g. `arr_total_at_latest_snapshot`). |
| `grain` | Aggregation grain (e.g. `(as_was_date = max)`). |
| `source_salesforce` | Raw value from `base_prod.salesforce.*`. Empty for structural tests. |
| `baseline_prod` | Current production value (`finance_prod`) - the pre-change baseline. |
| `target_dev_qa` | New value in `finance_dev` (CI) or `finance_qa` (CD) - post-change. |
| `expected` | What the AC / business rule says the value should be. |
| `actual` | Measured value (usually equals `target_dev_qa`). |
| `business_logic` | One-line formula or rule being tested. |
| `verdict` | `pass` / `warn` / `fail` / `needs_review` / `pending`. |

The matrix carries an auditable `sql_template` per row (CTE-based, with
`sf_source`, `prod_baseline`, `dev_target` CTEs) that the supervisor
runs via the Snowflake MCP to populate the value columns. Until the SQL
is run, `verdict='pending'`.

- `code-data-validator` builds the baseline matrix (pre-flight against `finance_prod`).
- `test-runner` projects each pytest run + each dbt-test selector into one row.
- `ci-monitor` rebuilds the matrix against `finance_dev` after CI lands.
- `cd-monitor` rebuilds it again against `finance_qa` after CD merges.
- `qa-handoff` renders all three matrices as ADF tables in the QA Jira comment.
- The thinking log renders the matrix as a Markdown table at `role_end`.

## What the supervisor returns

A `SupervisorRunReport` JSON with `mode`, `overall_status`, `role_results`
(per-role status + summary), `pause_points`, and `side_tasks` (any
`task:` messages picked up from Slack during the run, including their
action and result). On pause, the report contains everything up to the
pause so the user can review before approving.

## Resuming after a pause

The supervisor is stateful per run only (no on-disk state by default). The
intended resume pattern: take the most recent `RoleResult.payload` for each
completed role from the report, hand it to the next `Supervisor` invocation
as `SupervisorState(...)`. The CLI doesn't expose this yet - drive resumes
from the SDK (`Supervisor(input, state=...).run()`).

## See also

- Per-sub-agent prompts: `subagents/01_*.md` ... `11_*.md`
- Regression test command: `.cursor/commands/fcq-arr-regression-test.md`
- Authorization rule: `.cursor/rules/arr-close-supervisor.mdc`
- Existing scheduled-close skill: `SKILL.md`
