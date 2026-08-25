# ARR Quarter Close Agent

**Supervisor display name:** Finance ARR Quarter Close
**Short code:** FQC-ARR
**Aliases (all interchangeable):** FQC, FQCARR, FQC-ARR
**Package path (stable):** `agents/arr_quarter_close/`

Orchestrates the eda-dbt-em ARR quarter close so the same logic can be
driven from a CLI, from a Cursor IDE / Cloud agent, from a Cursor
Automation, and (later) from Workday SANA - without rewriting the steps.

> **Agentic-AI naming.** The `Supervisor` class in `supervisor.py` is
> the **Manager** (OpenAI's "A Practical Guide to Building Agents",
> 2025) / **Supervisor** (LangGraph multi-agent docs) / **Orchestrator**
> (Anthropic's "Building Effective Agents", Dec 2024). Three published
> names for the same role: the central coordinator that holds state,
> dispatches sub-agents, and pauses for human approval at write
> boundaries. Canonical name in this codebase = "Supervisor". The
> 12 specialist sub-agents under `subagents/` are the **workers**
> (Anthropic) / **specialist agents** (OpenAI) the Supervisor delegates
> to. See `~/.cursor/skills/multi-agent-supervisor-pattern/SKILL.md`
> and `~/Documents/Cursor/Documents/fqc_arr_agentic_architecture_validation_report.md`
> for the full design + validation against the 12-Factor Agents and
> OWASP LLM Top 10 rubrics.

> Why the path doesn't match the name: the folder, module, class, rule
> filenames, and skill folder were created before the FQC-ARR brand was
> assigned. Renaming them would break every import / rule glob / data-agent
> reference; the public identity is FQC-ARR via the constants
> `SUPERVISOR_DISPLAY_NAME` / `SUPERVISOR_SHORT_CODE` in
> `supervisor.py`, all docs, all Slack banners, and all CLI output.

## Default LLM model

The supervisor itself runs no LLM (deterministic Python control flow). The
**3 LLM-driven leaf sub-agents** (`requirements_analyzer`, `clarifier`,
`implementer`) and the **Cursor SDK runner** (`cursor_runner.py`) all
advertise a single `preferred_model` on their pause result and prepend a
`[Preferred model: <slug>]` header to the prompt they emit.

| Default | Slug |
|---|---|
| **Opus 4.7 Extra High** | `claude-opus-4-7-thinking-xhigh` |

Source of truth: `contracts.DEFAULT_LLM_MODEL`. Override precedence
(highest first):

1. CLI flag: `--model claude-opus-4-8-thinking-high`
2. Env var: `export FQC_ARR_DEFAULT_MODEL=gpt-5.5-medium`
3. `DEFAULT_LLM_MODEL` constant in `contracts.py`

The same value flows through:

- `RoleResult.preferred_model` (typed field, returned by every LLM-leaf
  sub-agent on `NEEDS_INPUT`)
- `RoleResult.payload["preferred_model"]` (mirrored for JSON callers)
- `RoleResult.pause_reason` (human-readable, includes model in backticks)
- The first two lines of every emitted prompt:

  ```
  [FQC-ARR <role> prompt]
  [Preferred model: claude-opus-4-7-thinking-xhigh]
  ```

- `CursorRunOptions.model` (the Mode A Cursor SDK agent that drives the
  scheduled close runbook)

Callers (Cursor chat, Cursor SDK, SANA) read `preferred_model` and route
the emitted prompt to that model. The agent never authenticates against
or calls an LLM directly — model choice stays with the operator's
runtime, but the agent's "asks" are uniform across runtimes.

## Layout

| File | Purpose |
|---|---|
| `core.py` | Portable, framework-agnostic step manifest + orchestrator for scheduled-snapshot closes. No Cursor / SANA / cloud dependency. |
| `contracts.py` | Typed JSON in/out dataclasses for every sub-agent (Phase 1.5). |
| `supervisor.py` | Two-mode dispatcher: Mode A (scheduled-snapshot, delegates to `core`) and Mode B (10 sub-agent DAG for ticket-driven changes). |
| `subagents/` | Ten DAG sub-agents (jira_intake → qa_handoff) plus two **on-demand** sub-agents: `debugger` (root-causes failures; dispatched on FAIL, `task: debug`, or `--debug-model`) and `quarter_close_runner` (runs the ARR pipeline + builds the 7-check recon matrix; dispatched via `task: quarter-close`, `--quarter-close`, or direct SDK call). Each exposes `plan(input)` and `run(input)`. |
| `cli.py` | Command-line entrypoint over `core` + `supervisor`. |
| `../../bin/fqc-arr` | Shell wrapper around `cli.py` so you can run from any directory (no `cd` / `PYTHONPATH` needed). |
| `cursor_runner.py` | Wraps `core` with the Cursor SDK (`Agent.prompt` / `Agent.create`). |
| `sana_adapter.py` | Clearly-marked stub for Workday SANA integration; fills in once the SANA spec arrives. |
| `requirements.txt` | Optional extras (Cursor SDK). The core has no third-party deps. |

## Canonical commands (quick reference)

The most-used invocation patterns. Each row is a complete command; see
the Quickstart and §2a sub-sections below for full flag semantics.

| Scenario | Command |
|---|---|
| **Greenfield ticket, fully autonomous** | `fqc-arr --ticket EDAEM-XXXX --auto --slack-channel <YOUR_SLACK_USER_ID>` |
| **Greenfield ticket, smart-gated (pauses before writes)** | `fqc-arr --ticket EDAEM-XXXX --slack-channel <YOUR_SLACK_USER_ID>` |
| **With stakeholder notifications** | `fqc-arr --ticket EDAEM-XXXX --auto --slack-channel <YOUR_SLACK_USER_ID> --notify jane.doe --notify jane.doe` |
| **Attach to an existing manually-opened PR** | `fqc-arr --ticket EDAEM-XXXX --auto --pr-number 472 --dbt-cloud-run-id 151057 --slack-channel <YOUR_SLACK_USER_ID> --skip jira-intake --skip requirements-analyzer --skip code-data-validator --skip clarifier --skip implementer --skip test-runner --skip pr-author --skip ci-monitor` |
| **Re-run debugger after the DAG** | `fqc-arr --ticket EDAEM-XXXX --auto --debug-model arr_line_categories --slack-channel <YOUR_SLACK_USER_ID>` |
| **Quarter close (pipeline + 7-check recon)** | `fqc-arr --ticket EDAEM-XXXX --quarter-close --as-was-date 2026-04-30 --auto --slack-channel <YOUR_SLACK_USER_ID>` |
| **Scheduled-only (no ticket)** | `fqc-arr --as-was-date 2026-02-11 --target qa` |
| **Show accumulated lessons (continuous learning)** | `fqc-arr --show-lessons` (or `--show-lessons debugger`) |
| **Force a daily-reflection pass right now** | `fqc-arr --reflect` |
| **Run without lesson injection (clean-slate prompt)** | `fqc-arr --ticket EDAEM-XXXX --auto --no-inject-lessons --slack-channel <YOUR_SLACK_USER_ID>` |
| **Detached / survives terminal close** | `nohup fqc-arr --ticket EDAEM-XXXX --auto --slack-channel <YOUR_SLACK_USER_ID> > runs/fqc_arr_EDAEM-XXXX_$(date -u +%Y%m%dT%H%M%SZ).log 2>&1 & disown` |

Where to watch progress for any run:

| | |
|---|---|
| Live thinking log | `tail -f runs/thinking/<UTC_ts>_<slug>.md` — the supervisor prints the exact path at startup |
| Raw supervisor log | wherever you redirected stdout in the `nohup` command above |
| Slack heartbeats | the channel/DM passed to `--slack-channel`; additional stakeholders from `--notify` get fanned-out by sub-agents |
| Jira ticket | sub-agents post role-by-role progress + final QA validation matrix as comments |

Required env (one-time, expected in `~/.zshrc`):

```bash
# Jira (per ~/.cursor/rules/jira-api-access.mdc)
JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN
# dbt Cloud (for ci-monitor / cd-monitor / watchers)
DBT_CLOUD_HOST, DBT_CLOUD_ACCOUNT_ID, DBT_CLOUD_API_TOKEN
# Snowflake / Salesforce / Sigma MCPs already configured per workspace .cursor/mcp.json
```

---

## Quickstart

> If you see `ModuleNotFoundError: No module named 'agents'`, you're running
> `python -m agents.arr_quarter_close.cli` from a directory that isn't the
> repo root. Two fixes:
>
> 1. **One-time** — `cd /Users/.../eda-dbt-em` first, then run the command.
> 2. **Permanent** — use the wrapper at `bin/fqc-arr`, which resolves its
>    own location and works from any directory. Either run it by absolute
>    path, or symlink it into your `$PATH` once:
>
>    ```bash
>    ln -s $HOME/Documents/Cursor/eda-dbt-em/bin/fqc-arr \
>          /usr/local/bin/fqc-arr
>    # then anywhere on the box:
>    fqc-arr --ticket EDAEM-3725 --mode ticket --dry-run
>    ```
>
>    The wrapper also auto-defaults `--project-dir` to the repo root, so
>    `runs/thinking/...` files land inside the repo regardless of CWD.

### 1. CLI - dry-run (no execution, just shows the dbt commands)

```bash
# from the repo root:
python -m agents.arr_quarter_close.cli \
  --as-was-date 2026-02-11 \
  --project-dir . \
  --dry-run

# or from anywhere (after symlinking bin/fqc-arr into PATH):
fqc-arr --as-was-date 2026-02-11 --dry-run
```

### 2. CLI - real run against QA

```bash
python -m agents.arr_quarter_close.cli \
  --as-was-date 2026-02-11 \
  --project-dir . \
  --target qa
```

Exit codes: `0` success, `1` warn, `2` fail.

### 2a. CLI - ticket-driven Finance ARR Quarter Close (FQC-ARR) supervisor (Phase 1.5)

Plan-only dispatch of the 10 sub-agent DAG for a Jira ticket (no Jira /
Slack / Snowflake writes):

```bash
python -m agents.arr_quarter_close.cli \
  --ticket EDAEM-3725 \
  --project-dir . \
  --mode ticket \
  --dry-run
```

Real run, smart-gates authorization (pauses before each side-effecting
step):

```bash
python -m agents.arr_quarter_close.cli \
  --ticket EDAEM-3725 \
  --project-dir . \
  --mode ticket \
  --slack-channel <YOUR_SLACK_USER_ID>
```

Real run, full autonomy (no pauses; use only when explicitly authorized):

```bash
python -m agents.arr_quarter_close.cli \
  --ticket EDAEM-3725 \
  --project-dir . \
  --mode ticket \
  --auto \
  --slack-channel <YOUR_SLACK_USER_ID>
```

Combined (ticket + snapshot rebuild after implementer):

```bash
python -m agents.arr_quarter_close.cli \
  --ticket EDAEM-3725 \
  --as-was-date 2026-02-11 \
  --project-dir . \
  --slack-channel <YOUR_SLACK_USER_ID>
```

Authorization model and pause points: `.cursor/rules/arr-close-supervisor.mdc`.
Per-role behavior: `.cursor/skills/arr-quarter-close/subagents/01_*.md`-`10_*.md`.

#### Attach ci-monitor / cd-monitor to an existing PR

When the PR was opened outside the agent (manual `gh pr create`, or the DAG
paused before `pr-author`), bolt the monitors onto it directly:

```bash
fqc-arr --ticket EDAEM-3723 \
    --pr-number 472 \
    --pr-url https://github.com/workday-inc/eda-dbt-em/pull/472 \
    --check-name "dbtcloud-codevalidate" \
    --slack-channel <YOUR_SLACK_USER_ID> \
    --skip jira-intake --skip requirements-analyzer --skip clarifier \
    --skip code-data-validator --skip implementer --skip test-runner \
    --skip pr-author
```

Flags:

| Flag | Effect |
|---|---|
| `--pr-number INT` | Seeds `ci-monitor` / `cd-monitor` with the PR number |
| `--pr-url URL` | Full PR url (paired with `--pr-number`) |
| `--check-name STR` | Override the GitHub check context (default `ci/dbt_cloud`) |
| `--dbt-cloud-run-id INT` | Pin `cd-monitor` to a specific dbt Cloud run |

Standalone alternatives (no agent invocation needed, single PR or single dbt
Cloud run):

```bash
# Rich CI watcher - polls GitHub ci/dbt_cloud + dbt Cloud API, posts
# "X of N models complete" progress to Slack every 5 min.
bin/watch_pr_ci.py 472 <YOUR_SLACK_USER_ID> --poll-minutes 5 --max-hours 8

# Rich CD / ad-hoc dbt run watcher - same telemetry, PR-agnostic.
bin/watch_dbt_run.py 151057 <YOUR_SLACK_USER_ID> "PR #472 CD" --poll-minutes 5

# Legacy bash watcher - simpler heartbeat, no progress parsing.
bin/watch_pr_ci.sh 472 <YOUR_SLACK_USER_ID> --poll-minutes 10 --max-hours 8
```

#### Stakeholder notifications (`--notify`)

The supervisor ships with a small Slack user directory (built from
`#enterprise-data-and-analytics` channel scrapes plus manual additions)
so you can pass friendly names / emails instead of `U.../W...` ids:

```bash
fqc-arr --ticket EDAEM-3725 --auto \
    --slack-channel <YOUR_SLACK_USER_ID> \
    --notify jane.doe \
    --notify [REDACTED_EMAIL] \
    --notify <person>
```

What `--notify` accepts:

| Form | Example |
|---|---|
| Slack user id | `--notify U07EAT736HG` (passthrough) |
| Full handle | `--notify jane.doe` |
| Email | `--notify [REDACTED_EMAIL]` |
| First-name prefix | `--notify jane` |

Behavior:

1. At supervisor startup, each `--notify` entry resolves against
   `agents/arr_quarter_close/data/slack_directory.json` (auto-loaded).
2. Resolved ids land in `SupervisorInput.notify_user_ids` (tuple,
   de-duped).
3. Anything that can't be resolved lands in `SupervisorInput.notify_unresolved`
   so a downstream sub-agent can ping back asking you to add the id.
4. Sub-agents read `self.input.notify_user_ids` to fan-out heartbeats or
   `<@uid>` mentions to those people in addition to `--slack-channel`.

Manage the directory programmatically:

```python
from agents.arr_quarter_close.slack_directory import get_directory

sd = get_directory()
print(sd.summary())                  # SlackDirectory(20 users, 35 aliases, ...)
sd.resolve("jane")                   # -> 'U07EAT736HG'
sd.resolve("[REDACTED_EMAIL]")      # -> None  (not in directory)

# Learn-as-you-go: any sub-agent that discovers a new id (webhook
# payload, search hit, etc.) can persist it for next time.
sd.add("U09NEW123", name="alice.smith", email="[REDACTED_EMAIL]",
       channel="#enterprise-data-and-analytics")
sd.save()
```

Refresh the channel scrape (re-runs ~57 `slk search` queries):

```bash
python3 agents/arr_quarter_close/data/_scrape_eda_channel.py
```

Coverage caveat: only ACTIVE participants of the scraped channel are
captured. Silent lurkers can't be enumerated because the enterprise
workspace blocks `conversations.members` (`enterprise_is_restricted`).
For full-roster access, a Slack admin would need to provision a bot
token with `groups:read.members` scope.

#### Slack thread side-channel (`task:` commands + `ans:` answers)

While a ticket run is live and `--slack-channel` is set, the supervisor
polls its own Slack thread between sub-agents. Two message prefixes are
recognized — everything else is queued as a free-form side task and
surfaced in the final report.

**`task:` — steer the run** (read by `_drain_side_tasks`):

| Message | Effect |
|---|---|
| `task: skip <role>` | Add a role to the skip list |
| `task: pause` | Pause after the current role |
| `task: cancel` | Cancel after the current role |
| `task: status` | Post recent role results back to the thread |
| `task: debug [model]` | Dispatch the on-demand debugger |
| `task: quarter-close [date]` | Dispatch the quarter-close-runner |

**`ans:` — answer a clarifier** (read by `_try_slack_clarifier`):

When the clarifier has open questions it posts them to the thread and
waits (default 30 min, `--clarifier-slack-timeout`) for a reply that
starts with `ans:`. This is the **no-daemon Slack resume path** — the
wait runs inside the live supervisor process, so no separate listener is
needed. The agent absorbs the answers into `requirements.scope_summary`,
drops the answered questions, and continues the DAG **without** posting to
Jira.

```text
# Agent posts in-thread:
:question: Clarifications needed (3 question(s)) before I post to Jira.
1. Which currency variant?
2. Which as_was_date?
3. Output grain — account or account×product?

# You reply (any of these forms works):
ans: 1) USD_HIST  2) 2026-05-11  3) account grain     # one combined reply
ans: USD_HIST                                          # or one ans: line
ans: 2026-05-11                                        #    per question
ans: account grain
```

Resolution order for a clarifier pause: **(1)** terminal stdin
(`--clarifier-interactive-timeout`, default 10 min, tty only) → **(2)**
Slack `ans:` (`--clarifier-slack-timeout`, default 30 min) → **(3)** fall
back to posting the questions to Jira. In `--auto` (full-auto) the Slack
`ans:` window is still offered *before* the Jira post; if it times out the
run posts to Jira and continues (it does not pause). Disable with
`--no-clarifier-slack`; send `task: cancel` to skip the wait immediately.

#### On-demand debugger sub-agent

Dispatched **outside** the canonical DAG whenever something needs root-causing:

```bash
# Auto-dispatch on FAIL (default; disable with --no-debug-on-failure):
fqc-arr --ticket EDAEM-3725 --mode ticket --slack-channel <YOUR_SLACK_USER_ID>

# Run after a clean DAG against the first in-scope model:
fqc-arr --ticket EDAEM-3725 --mode ticket --debug --slack-channel <YOUR_SLACK_USER_ID>

# Pin a specific model:
fqc-arr --ticket EDAEM-3725 --mode ticket --debug-model arr_sku_categories

# From an in-progress Slack thread (side-channel):
#   task: debug
#   task: debug arr_subproduct_categories
```

What it produces (smart-gated; pauses before writing to Jira):

* `LineageNode[]` — upstream BFS walk of `target_model` (depth ≤ 5)
* `ValidationMatrix` — one `ValidationCheck` per lineage node (same 7-column shape used elsewhere)
* `ACAnalysis[]` — one row per acceptance criterion, cross-referenced to evidence
* `RootCauseHypothesis[]` — ranked (high/medium/low) with evidence citations
* `ProposedFix` — file path + LLM prompt (never writes the change itself)
* `PytestHarnessSpec` — `tests/test_debug_<model>_<ticket>.sql` + `tests/pytest/test_debug_<model>_<ticket>.py` (both `.gitignore`d)
* `jira_update_adf` — Jira ADF comment **shaped by ticket type**:
  * **Bug** → "Root cause + reproducible fix" + Repro steps + Regression test
  * **Story / Task / Sub-task / Epic** → "Debug findings" + Suggested investigation focus

Sub-agent definition: `agents/arr_quarter_close/subagents/debugger.py`.
Rule + skill: `.cursor/rules/arr-close-supervisor.mdc` (§ "On-demand debugger sub-agent") and `.cursor/skills/arr-quarter-close/supervisor.md`.

#### On-demand quarter-close-runner sub-agent

Dispatched **outside** the canonical DAG whenever a snapshot needs to be
loaded **and** reconciled:

```bash
# Scheduled mode: run pipeline + recon for a snapshot (replaces the
# bare ARRCloseOrchestrator path so the recon matrix is built once):
fqc-arr --as-was-date 2026-02-11 --quarter-close --slack-channel D03GVBRLU9F

# Ticket mode: run the DAG, then dispatch quarter-close-runner so the
# QA-handoff comment carries the recon matrix:
fqc-arr --ticket EDAEM-3725 --mode ticket --quarter-close \
    --as-was-date 2026-02-11 --slack-channel D03GVBRLU9F

# Recon-only (snapshot already loaded, just rebuild the matrix):
fqc-arr --as-was-date 2026-02-11 --quarter-close \
    --quarter-close-skip-pipeline --no-slack

# Tighten tolerance for a sensitive close:
fqc-arr --as-was-date 2026-02-11 --quarter-close \
    --quarter-close-tolerance-pct 0.25

# From an in-progress Slack thread (side-channel):
#   task: quarter-close
#   task: quarter-close 2026-02-11
```

What it produces:

* `CloseResult` (from `ARRCloseOrchestrator`) — every dbt step + duration + status.
* `ValidationMatrix` with 7 ARR-specific recon checks:
  * `waterfall_balance_per_category` — Begin + Categories = End (headline ARR identity)
  * `total_arr_at_snapshot` — period-over-period total
  * `arr_line_categories_row_parity` / `arr_sku_categories_row_parity` / `arr_account_product_corp_report_row_parity` — row-count tie-outs
  * `currency_variant_tie_out` — USD_CURRENT == USD_HIST for same-rate lines
  * `active_account_continuity` — no silently-dropped accounts (drop without a CHURN row = regression)
* `QuarterCloseReport` aggregating both phases + an `overall_verdict`.

The 7 checks are **additive** to `test_arr_waterfall_balance` and
`tag:ia_migration` that the orchestrator already runs — they don't
replace them. Verdicts default to `pending` until the supervisor (or
operator) runs each `sql_template` via the Snowflake MCP and re-attaches
actuals via `quarter_close_runner._attach_actuals(report, actuals)`.

Sub-agent definition: `agents/arr_quarter_close/subagents/quarter_close_runner.py`.
Rule + skill: `.cursor/rules/arr-close-supervisor.mdc` (§ "On-demand quarter-close-runner sub-agent") and `.cursor/skills/arr-quarter-close/supervisor.md`.

### 3. Cursor SDK runner

```python
from pathlib import Path
from agents.arr_quarter_close import ARRCloseConfig
from agents.arr_quarter_close.cursor_runner import (
    CursorRunOptions, run_close_via_prompt,
)

cfg = ARRCloseConfig(
    as_was_date="2026-02-11",
    project_dir=Path("."),
    target="qa",
)
out = run_close_via_prompt(cfg, CursorRunOptions(project_dir=Path(".")))
print(out)
```

Requires `CURSOR_API_KEY` and `pip install cursor-sdk`.

### 4. SANA adapter

Not wired yet - see `sana_adapter.py` for the seam. The portable `core` is
ready; only `sana_adapter.py` changes when SANA contracts arrive.

## Continuous learning (lessons learned, per-role)

The supervisor and every sub-agent share a lightweight, append-only
"lessons learned" ledger that grows across runs. Each lesson is a single
actionable sentence ("when X, do Y") tagged with a category (`failure` /
`tooling` / `best_practice` / `user_preference` / `ambiguity` /
`edge_case` / `correction` / `validation_gap` / `optimization`) and a
confidence (`low` / `medium` / `high`).

**Where it lives:** `agents/arr_quarter_close/data/lessons/`

| File | Contents |
|---|---|
| `<role>.jsonl` | Active lessons for one role (e.g. `debugger.jsonl`, `pr-author.jsonl`). |
| `_global.jsonl` | Cross-role lessons that apply everywhere (e.g. "never embed agent self-references in user-facing output"). |
| `_stable.jsonl` | Promoted lessons that have re-occurred ≥3 times — these are the highest-signal items. |
| `_reflection_log.jsonl` | One row per daily-reflection pass: timestamp, lessons added, lessons promoted. |

**How new lessons get added:**

1. **Auto, end-of-run** — at the end of every supervisor run (once per UTC day),
   the `daily-reflection` sub-agent scans `runs/thinking/*.md`, extracts any
   `fail` / `warn` / `needs_input` outcomes from role sections, and records
   them as `failure` / `edge_case` / `ambiguity` lessons. Disable with
   `--no-auto-reflect`.
2. **Manual, on-demand** — `fqc-arr --reflect` forces a fresh pass even if
   reflection already ran today.
3. **Seeded once from this README's domain knowledge** —
   `python -m agents.arr_quarter_close.data.seed_lessons` writes the
   hand-curated operational lessons (Snowflake MCP single-statement rule,
   `slk search` hang, grain-mismatch RCA pattern, no-agent-signatures rule,
   etc.). Re-running is safe — duplicates bump `occurrence_count` instead
   of inserting new rows.
4. **Seeded once from the agent's own design** —
   `python -m agents.arr_quarter_close.data.seed_self_lessons` distills
   the architecture into role-targeted invariants (DAG ordering, typed
   `RoleResult` contract, two-mode dispatcher, debug-on-failure default,
   pr-author FULL_AUTO gate, debugger lineage-walk depth, quarter-close
   7-check matrix, portability `runner` seam, etc.). Run once after a
   refactor or when on-boarding the lessons store. Also idempotent.
5. **Seeded once from the IA Refactor / refactoring-discussion thread** —
   `python -m agents.arr_quarter_close.data.seed_refactor_lessons` loads
   the hard-won learnings from the cross-session refactoring work:
   three-source PVQ/QA/Prod cross-validation pattern, dual-`term_end`
   fan-out anti-pattern in `up_for_renewal_fn`, PBU-Manual UNION-trick
   RCA shortcut, `finance_line_analytics` dev-vs-prod history gap,
   SSR off-cycle invariant, HCM/FIN/Platform account-categorization
   rule, `state:modified+` CI limitation + `adhoc_pipeline_runner_config`
   anchor, multi-repo (base/gtm/em/semantic-layer) scope rule, and the
   EDAEM↔EDADEV cross-ticket dependency pattern. Run once; idempotent.

**How lessons feed back into the agent:**

* The three LLM-driven sub-agents (`requirements-analyzer`, `implementer`,
  `debugger`) prepend a `## Lessons learned from prior runs (apply these)`
  block to their emitted prompt at run time. The block includes every
  promoted lesson for that role + recent active lessons + cross-role
  global rules, capped at `--max-lessons-per-role` (default 8).
* The supervisor itself records its decisions / overrides into
  `supervisor.jsonl` so it learns from its own failure modes (e.g.
  "`--debug-model` was silently aborted when `jira-intake` was skipped").

**Lifecycle:** a lesson auto-promotes from `active` → `promoted`
(written into `_stable.jsonl`) once `occurrence_count >= 3`. Confidence
bumps one tier on every dedupe hit. Old lessons (>90 days, no
re-occurrence) are eligible for archive in a future maintenance pass.

**Inspecting / pruning:**

```bash
fqc-arr --show-lessons                # all lessons, grouped by role
fqc-arr --show-lessons debugger       # one role
fqc-arr --reflect                     # force-extract from today's runs
cat agents/arr_quarter_close/data/lessons/_reflection_log.jsonl   # audit cadence
```

**Schema** (one JSON object per line in each `*.jsonl`):

```json
{
  "id": "stable_sha1_of_role_plus_lesson_text",
  "role": "debugger",
  "category": "best_practice",
  "lesson": "When two views compute the 'same' metric at different grains, ...",
  "evidence": "EDAEM-3772 root cause: ...",
  "tags": ["filter-scope", "grain-mismatch", "retention"],
  "confidence": "high",
  "occurrence_count": 1,
  "status": "active",
  "source_ticket": "EDAEM-3772",
  "source_run_ts": "2026-06-25T03:59:34+00:00",
  "first_seen": "2026-06-25T03:59:34+00:00",
  "last_seen": "2026-06-25T03:59:34+00:00"
}
```

**Why this, not LLM fine-tuning?** The agent runs against Cursor's hosted
models that we can't tune. A structured, auditable, version-controlled
ledger of actionable lessons gives most of the benefit (the LLM applies
them in-context every run) with none of the cost / governance overhead.
Lessons are reviewable in PRs, and the user can deprecate any lesson by
flipping its `status` to `deprecated` in the JSONL.

---

## What the manifest runs

The default manifest (see `core.build_default_manifest`) executes, in order:

1. `dbt run --select path:models/finance/int/stage/table/tmp_tbls_of_bt_arr_categories_optimized --exclude *_scd2`
2. `dbt run --select +arr_line_categories --exclude *_scd2`
3. `dbt run --select arr_sku_categories arr_subproduct_categories arr_product_categories --exclude *_scd2`
4. `dbt run --select +arr_account_product_corp_report --exclude *_scd2`
5. *(optional)* `dbt run --select path:models/finance/modeled/data_product/view --exclude *_scd2`
6. `dbt test --select test_arr_waterfall_balance`
7. *(optional)* `dbt test --select tag:ia_migration`

Every command receives `--vars '{"as_was_date":"\'YYYY-MM-DD\'"}'`. If
`--heavy-warehouse` is set, `em_heavy_warehouse` is added to the vars
payload for the heavy ARR steps.

## Known FY close snapshot dates

`core.KNOWN_FY_CLOSE_DATES` mirrors `arr_refactor_as_was_date_list` in
`dbt_project.yml`:

```text
2025-05-08, 2025-08-11, 2025-11-10, 2026-02-11
```

The CLI warns (does not block) when `--as-was-date` is not in the list,
so ad-hoc close-adjacent dates still work.

## Why the seam

`core.ARRCloseOrchestrator` accepts a `runner` callable
`(argv, cwd) -> CompletedProcess`. Substituting the runner is how other
runtimes plug in:

| Runtime | Runner |
|---|---|
| Local CLI | `core.default_runner` (subprocess to local `dbt`) |
| Cursor SDK | Wrap a dbt MCP call inside a `CompletedProcess`-compatible adapter |
| dbt Cloud / SANA | Wrap dbt Cloud's `POST /jobs/.../run/` API call |
| Tests | Lambda that returns canned CompletedProcess instances |

This is the entire portability story.
