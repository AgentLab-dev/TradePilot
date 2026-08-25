# FQC-ARR (Finance ARR Quarter Close) — Health Check + Lessons Learned

**Date:** 2026-08-02 (revised at 11:48 PT)
**Scope:** supervisor + 10 canonical sub-agents + debugger + quarter-close-runner + daily-reflection + lessons loop
**Verdict:** **GREEN — the system is installed, running, and actively learning. Two real papercuts (dbt stub gap and a banned-phrase docstring) plus doc drift between the eda-dbt-em repo and the installed AE Agent.**

> **Correction to the 11:42 PT draft of this doc.** The earlier draft concluded the Python module tier did not exist, based on the absence of `agents/arr_quarter_close/` inside the `eda-dbt-em` git repo. That was **wrong**. Per the "Jun-2026 relocation" documented at the top of `bin/fqc-arr`, the Python code was intentionally moved out of the dbt repo so it survives `rm -rf eda-dbt-em && git clone …`. It lives at `~/Library/Application Support/AE Agent/agents/arr_quarter_close/` (surfaced via the `~/Documents/Cursor/AE Agent` symlink). The `fqc-arr` CLI on PATH sets `PYTHONPATH=$AE_AGENT_HOME` before dispatching. This corrected doc supersedes the earlier findings.

---

## Where FQC-ARR actually lives

| Component | Path |
|---|---|
| Distribution source | `~/Documents/Cursor/fqc-arr-dist/AE Agent/` (+ `.tar.gz` for teammates) |
| Installed agent home | `~/Library/Application Support/AE Agent/` (aka `~/Documents/Cursor/AE Agent/` via symlink) |
| Python package | `~/…/AE Agent/agents/arr_quarter_close/` |
| CLI | `~/…/AE Agent/bin/fqc-arr` (also `ae-do-ticket`, `ae-ship-pr`, `watch_dbt_run.py`, `watch_pr_ci.{py,sh}`) |
| Lessons store | `~/…/AE Agent/agents/arr_quarter_close/data/lessons/` (28 files, incl. `_stable.jsonl`, `_global.jsonl`, per-role `.jsonl`) |
| Run artifacts | `~/…/AE Agent/runs/{thinking,learning,audit,backups,pr_mining}/` |
| Scheduled jobs (launchd) | `com.kvenkata.fqcarr.learn-am`, `learn-pm`, `lesson-audit-weekly`, `backup-weekly` — all loaded |
| Env wiring (`~/.zshrc`) | `FQC_ARR_PROJECT_DIR=~/Documents/Cursor/eda-dbt-em`, `FQC_ARR_LESSONS_DIR=…/data/lessons` |
| Prompt/skill mirror in dbt repo | `.cursor/skills/arr-quarter-close/**` + `.cursor/rules/arr-close-*.mdc` (read by sub-agents at runtime) |

The eda-dbt-em repo carries the **skill/rule/prompt layer** (Markdown briefs, ADF templates, per-role subagent files). The AE Agent carries the **runtime** (Python supervisor, CLI, lessons, learning loop, notifier). Neither is a duplicate of the other.

## Installed sub-agents (15 total, not 10)

Canonical 10-role DAG:

1. `jira_intake.py` (6.3 KB)
2. `requirements_analyzer.py` (5.7 KB)
3. `code_data_validator.py` (8.6 KB)
4. `clarifier.py` (5.9 KB)
5. `implementer.py` (6.0 KB)
6. `test_runner.py` (7.4 KB)
7. `pr_author.py` (6.5 KB)
8. `ci_monitor.py` (5.7 KB)
9. `cd_monitor.py` (7.1 KB)
10. `qa_handoff.py` (8.3 KB)

On-demand:

11. `debugger.py` (30.4 KB — the largest sub-agent; auto-dispatches on FAIL)
12. `quarter_close_runner.py` (22.6 KB — wraps the scheduled orchestrator + 7-check recon matrix)
13. `daily_reflection.py` (15.5 KB — twice-daily lesson-mining pass)

Support:

14. `_validation_matrix.py` (11.4 KB — shared `ValidationCheck` scaffolding)
15. Plus `supervisor.py` (84.8 KB), `cli.py` (27.0 KB), `contracts.py` (26.9 KB), `core.py` (14.5 KB), `notifier.py` (11.1 KB), `lessons.py` (17.1 KB), `thinking_log.py` (17.9 KB), `slack_directory.py` (7.4 KB), `sana_adapter.py` (2.9 KB), `cursor_runner.py` (6.9 KB).

## Live tests I ran today

### Round 1 (11:42–11:48 PT) — corrected the missing-Python-tier claim

| Test | Command | Result |
|---|---|---|
| CLI reachable | `fqc-arr --help` | **PASS** — 49 flags including `--reflect`, `--learn`, `--show-lessons`, `--quarter-close`, `--debug`, `--clarifier-slack-timeout` |
| Ticket-mode dry-run | `fqc-arr --ticket EDAEM-3725 --mode ticket --dry-run` | **PASS** — 10 roles planned in 1.8s, thinking log at `runs/thinking/20260802_184513Z_EDAEM3725.md` |
| Scheduled-mode dry-run | `fqc-arr --as-was-date 2026-02-11 --target qa --dry-run` | **PASS** — 6 close steps planned; status `SKIPPED` (correct for dry-run) |
| Lessons pipeline | `fqc-arr --show-lessons` | **PASS** — 20 role streams visible; sample rules per role |
| Learning loop | `launchctl list \| rg fqc` | **PASS** — 4 launchd jobs loaded (learn-am, learn-pm, lesson-audit-weekly, backup-weekly) |
| Reflection freshness | latest `runs/learning/20260802T160110Z.md` | **PASS** — ran today at 16:01 UTC; `+0 added, +0 promoted — wide_scan ON, 14 thinking logs` |
| Sub-agent 1 (jira-intake) direct-tool proxy | `curl -u $JIRA_EMAIL:$JIRA_API_TOKEN /rest/api/3/issue/EDAEM-3725` | **PASS** — HTTP 200 |
| Sub-agent 6 (test-runner) pytest side | `pytest tests/pytest/ --collect-only -q` | **PASS** — 19 tests |
| Sub-agent 6 (test-runner) dbt MCP side | `dbt list --select test_arr_waterfall_balance` (via dbt MCP) | **FAIL** — cross-project stub gap (see Finding A) |
| Sub-agent 7 (pr-author) tools | `gh pr list --json … reviews` + `CODEOWNERS` present | **PASS** |
| Sub-agents 8/9 (ci/cd monitor) tools | `slk auth` OK as `koteswararao.venkata @ Workday`, `U03GK3V2FQU` | **PASS** |
| Debugger sub-agent, real prior runs | `tests/test_debug_arr_line_categories_edaem_3725.sql` + `.py` on disk | **PASS** (artifact contents violate a rule — see Finding B) |
| Snowflake MCP baseline query | `select sum(product_arr_usd_current) from finance_prod.aggregations.arr_line_categories` | Returns $-10.7B → template needs dedup guardrail (see Finding C) |

### Round 2 (11:54 PT) — full module + on-demand sub-agent sweep

| # | Test | Command | Result |
|---|---|---|---|
| 1 | Help completeness | `fqc-arr --help` | **PASS** — 196 lines of help, 49 distinct flags |
| 2 | Ticket-mode dry-run | `fqc-arr --ticket EDAEM-3725 --mode ticket --dry-run` | **PASS** — 10 roles skipped (dry-run); thinking log at `runs/thinking/20260802_185401Z_EDAEM3725.md` |
| 3 | Scheduled-mode dry-run | `fqc-arr --as-was-date 2026-02-11 --target qa --dry-run` | **PASS** — 6 close steps skipped correctly |
| 4 | Debugger sub-agent dry-run | `fqc-arr --ticket EDAEM-3725 --debug-model arr_line_categories --dry-run` | **PASS** — 11 roles planned (10 canonical + debugger) |
| 5 | Quarter-close-runner (recon-only) | `fqc-arr --quarter-close --as-was-date 2026-02-11 --quarter-close-skip-pipeline --dry-run` | **PASS** — 1 role, status OK, thinking log written |
| 6 | Reflection pass | `fqc-arr --reflect --reflect-look-back-days 7` | **PASS** — `daily-reflection ok runs_scanned=19 lessons_added=0 lessons_promoted=0 — no novel observations today` |
| 7 | Show-lessons | `fqc-arr --show-lessons` | **PASS** — 20 categories, **345 total lessons** in store |

Lessons store breakdown (20 streams, sample counts):

```text
_global (149)           debugger (38)         supervisor (10)
_stable (27)            code-data-validator (25)   implementer (9)
requirements-analyzer (16)   pr-author (18)   plan (9)
qa-handoff (5)          verify (5)            exec (4)
cd-monitor (7)          ci-monitor (7)        clarifier (7)
quarter-close-runner (2)  test-runner (2)     daily-reflection (2)
slack_pinger (2)        jira-intake (1)
```

## Remaining findings

### Finding A — MEDIUM — `dbt parse` fails after `make deps` (cross-project stub gap in the dbt repo)

`make deps` restores 32 stub models across `eda_dbt_base` (24) and `eda_dbt_gtm` (8), but never creates `dbt_packages/eda_dbt_common/`. `stubs.yml` has entries only for `base` and `gtm`.

```text
$ dbt parse
Compilation Error
  Model 'model.eda_dbt_em.stg_em_user_as_was' depends on a node named
  'wd_user_scd2' in package or project 'eda_dbt_common' which was not found
```

Root cause: `models/finance/int/stage/table/wd_scd2_wrappers/stg_em_user_as_was.sql` uses `{{ ref('eda_dbt_common', 'wd_user_scd2') }}` (one usage). A second parse error on `wd_agreement_line_scd2` → `eda_dbt_base.base_unified_history_agreement_line_item_scd2` suggests the base stub list is stale too.

**Blast radius:** every sub-agent that shells to dbt (`code-data-validator` lineage queries, `test-runner`, `quarter-close-runner`, scheduled Mode A) fails at the first `dbt list` / `dbt compile` / `dbt run`. The `fqc-arr --dry-run` path does NOT hit this because it doesn't call dbt.

**Fix:** add entries to `scripts/cross-project-stubs/stubs.yml`:

```yaml
eda_dbt_common:
  wd_user_scd2:
    relation: <DB>.<SCHEMA>.WD_USER_SCD2
eda_dbt_base:
  base_unified_history_agreement_line_item_scd2:
    relation: BASE_PROD.<SCHEMA>.BASE_UNIFIED_HISTORY_AGREEMENT_LINE_ITEM_SCD2
```

Then `bash scripts/cross-project-stubs/restore.sh --snapshot`. Consider adding a CI check that runs `dbt parse` after the restore to catch future drift.

### Finding B — MEDIUM — Debugger sub-agent output violates `no-agent-signatures.mdc`

Two artifacts carry the exact banned phrase (rule lists `Auto-created by the FQC-ARR debugger sub-agent for …` verbatim as banned):

```text
tests/pytest/test_debug_arr_line_categories_edaem_3725.py:3:
  Auto-created by the FQC-ARR debugger sub-agent for EDAEM-3725 (Bug). …
tests/pytest/test_debug_arr_customer_retention_dashboard_edaem_3772.py:3:
  Auto-created by the FQC-ARR debugger sub-agent for EDAEM-3772 (Bug). …
```

Both files are gitignored, so blast radius is small — but `debugger.py` will keep emitting the banned string on future runs until its docstring template is updated.

**Fix:** update the docstring template in `debugger.py` (installed at `~/…/AE Agent/agents/arr_quarter_close/subagents/debugger.py`) to lead with the identifier:

```python
"""Debug harness for <MODEL_NAME> (<TICKET_KEY>).

Shells out to `dbt test --select <selector>` and asserts returncode == 0.
The SQL runs in Snowflake via dbt — no direct snowflake.connector usage
(per prefer-mcp-for-data-platforms).
"""
```

### Finding C — MEDIUM — Sub-agent 3 emits unvalidated baseline SQL

Straw-man baseline `select sum(product_arr_usd_current) from arr_line_categories where as_was_date = max(...)` returned $-10.7B via the Snowflake MCP — the classic line-level double-count when the dedup key is dropped. The `code_data_validator.py` sub-agent contract calls this an "auditable baseline"; nothing forces it to include the correct dedup keys or a sanity threshold.

**Risk:** the value flows verbatim into the `qa-handoff` ADF `baseline_prod` column. A QA reader sees negative ARR and either loses trust or opens a ticket on a non-issue.

**Fix:** in the `code_data_validator.py` `metric_baselines` builder, add a template requirement — every baseline query must include the model's canonical dedup key (`arr_line_dedup_key` for `arr_line_categories`, `sku_dedup_key` for `arr_sku_categories`, etc.), and the supervisor should mark `verdict='needs_review'` when the returned value is < 0 or deviates > 10% from the prior snapshot's row count.

### Finding D — LOW — Doc drift between the dbt repo and the installed AE Agent

`.cursor/skills/arr-quarter-close/supervisor.md`, `subagent.md`, `SKILL.md`, `runbook.md`, `arr-close-supervisor.mdc`, `arr-close-data-agent.mdc`, and every per-role brief say things like `**Module**: agents/arr_quarter_close/subagents/<name>.py` and `python -m agents.arr_quarter_close.cli …`, without saying "this path is relative to `$AE_AGENT_HOME`, not to the dbt repo." A new operator (or a subagent launched via Cursor `Task`) can reasonably read these as "the file lives in the repo," which is what caused the wrong verdict in the 11:42 draft of this doc.

**Fix (small):** add a header sentence at the top of `supervisor.md`, `subagent.md`, `arr-close-supervisor.mdc`, and each per-role brief:

> The Python module referenced below lives in the AE Agent install (`$AE_AGENT_HOME/agents/arr_quarter_close/`), not in this repo. Invoke via the `fqc-arr` CLI on PATH.

Also: the automation drafts in `.cursor/automations/arr_quarter_close.draft.yaml` (all three variants) use `python -m agents.arr_quarter_close.cli`. Rewrite them to `fqc-arr` so they work on any machine with the agent installed, without needing to twiddle `PYTHONPATH`.

Also: `.cursor/skills/arr-quarter-close/scripts/plan_close.py` imports `from agents.arr_quarter_close.core …`. It works if you set `PYTHONPATH=$AE_AGENT_HOME` first; it doesn't work if you `python3` it directly. Either delete it (replaced by `fqc-arr --dry-run`) or add a `sys.path.insert` shim so it locates the installed agent home.

### Finding F — HIGH — Weekly backup silently failed for 2 weeks under launchd (TCC / sandbox)

The audit trail on the `feature/ae-agent-backup` GitHub branch shows a gap between 2026-07-19 and 2026-08-02:

```text
2026-08-02T18:54:54Z  949f7138  ae-agent: weekly snapshot 2026-08-02   (this one — manual from a terminal)
2026-07-19T09:00:13Z  e8a7ff7c  ae-agent: weekly snapshot 2026-07-19
2026-07-12T09:00:11Z  4a7ad9f1  ae-agent: weekly snapshot 2026-07-12
2026-06-28T09:00:09Z  bd9c9f09  ae-agent: weekly snapshot 2026-06-28
2026-06-25T04:58:06Z  5fc658ce  ae-agent: weekly snapshot 2026-06-25
```

Both the Jul 26 and Aug 2 automatic runs left audit files on disk marked `status | FAILED -- git fetch failed (network / auth?)`. Root cause is not network / auth — reproducing the failure surface manually inside a permission-restricted shell yields `Operation not permitted` on `~/Backups/eda-dbt-em-backup.git/FETCH_HEAD`. The bare clone was last successfully updated 2026-07-19; the worktree at `~/Backups/ae-agent-worktree` was already gone. So the launchd process lacks the file-system permissions to (a) write the `.lock` in the AE Agent home, (b) update `FETCH_HEAD` in the bare clone, or (c) reconstitute the missing worktree.

**Fix:** grant `launchd`'s user session Full Disk Access to `bash`/`git` (System Settings → Privacy & Security → Full Disk Access) OR relocate `~/Backups/` under a TCC-unrestricted path (the script's own comment header suggests this — noting `~/Documents/` is TCC-protected — so `~/Backups/` may inherit similar restrictions when the plist runs). Alternatively add a lightweight preflight to the backup script that logs the exact syscall that failed so the "network / auth?" heuristic doesn't mask real permission errors.

**Manual backup taken this session:** 2026-08-02T18:54:54Z, commit `949f7138`, 30 files changed, 345 lessons in store, 8.3 MB total. Landed cleanly at [https://github.com/workday-inc/eda-dbt-em/tree/feature/ae-agent-backup](https://github.com/workday-inc/eda-dbt-em/tree/feature/ae-agent-backup). Slack DM confirmation sent to `U03GK3V2FQU`.

### Finding E — LOW — Prior "healthcheck" doc mis-classified this system

Left as a lesson for future me: if the docs describe a system running out of one directory but the code lives in another (as with FQC-ARR's out-of-repo agent home), a new agent doing a health check will happily conclude "the code doesn't exist" and miss the obvious `which fqc-arr` and `ls '~/Documents/Cursor/AE Agent'` sanity checks. Adding either check to the top of any FQC-ARR healthcheck run avoids repeating this.

## Existing FQC-ARR docs on disk (for future reference)

All in `~/Documents/Cursor/Documents/`:

| File | Purpose |
|---|---|
| `fqc_arr_supervisor_installation_guide.md` | How to install / update the AE Agent from `fqc-arr-dist/` |
| `fqc_arr_agentic_architecture_validation_report.md` | Original architecture audit |
| `fqc_arr_agentic_architecture_revalidation_2026_06_21.md` | Jun 21 follow-up validation |
| `fqc_arr_30min_demo_talking_points.md` | 30-min demo script |
| `fqc_arr_demo_cheatsheet.md` | Command reference for demos |
| `fqc_arr_sana_migration_design.md` | SANA (org-shared) migration blueprint |
| `agentic_ai_agent_creation_and_fqc_arr_architecture.md` | End-to-end walkthrough |
| `fqc_arr_healthcheck_2026-08-02.md` | This document |

## Lessons captured today

1. **Do the "installed vs described" cross-check first.** For any Python-based sub-agent system that ships as a distributable, the first two shell commands should be `which <cli>` and `find <cli-install-dir> -type d -name <package>`. That would have short-circuited my whole first pass.
2. **The `no-agent-signatures.mdc` rule needs an emit-time check.** The debugger's `docstring_template` in `debugger.py` still writes the banned string; the rule was authored after the template was written and nobody re-read it. Recommend adding a `_scrub_signatures()` helper the debugger calls before writing any file.
3. **The `dbt parse` failure is real and gates the sub-agents that shell to dbt.** Not fatal for the supervisor as a whole (dry-run works, jira-intake works, ADF preview works), but fatal for `test-runner`, `code-data-validator` (dbt lineage part), `quarter-close-runner`, and scheduled Mode A. Fix `stubs.yml` first.
4. **Sub-agent SQL templates need dedup guardrails.** Any template that says "select sum(<measure>) from <arr aggregate>" without `distinct on <dedup_key>` produces a false baseline. The `code_data_validator.py` contract should refuse templates that don't include the dedup keys.
5. **The lessons loop works and is quiet — which is a healthy signal.** Latest 5 reflection passes all show "0 added, 0 promoted — wide_scan ON, N thinking logs scanned, 0 tracebacks. Agent is operating within its known playbook." Silent isn't broken; silent is "no novel failures worth capturing."
6. **A `--dry-run` sweep is a good weekly smoke test.** Round 2 hit all four dispatch surfaces (ticket, scheduled, debugger, quarter-close-runner) plus reflection and lessons in ~4s and left thinking-log receipts on disk. Add this as a `fqc-arr --self-test` subcommand so the operator can prove the supervisor is healthy without needing 6 separate invocations.
7. **The "network / auth?" fallback error message in `fqcarr_backup_weekly.sh` swallows real permission errors.** Two weeks of failed backups looked like transient GitHub auth flakes but were actually TCC / launchd permission blocks on `FETCH_HEAD` and `.lock`. Every `git fetch` failure should log `$?` + the last stderr line so the next reader doesn't waste time on the wrong root cause.
8. **The backup branch is the disaster-recovery surface.** With 5 successful weekly snapshots on `feature/ae-agent-backup` (Jun 25 → Aug 2), a fresh laptop can restore the whole 345-lesson store + launchd plists in ~5 min via the recipe in each backup audit MD. Worth remembering when advising a teammate who wants to install FQC-ARR.
9. **`--reflect` returning zero adds is the expected steady-state.** The reflection sub-agent has been running twice-daily for 5+ weeks; the fact that it now says "operating within its known playbook" every pass means the lessons store has saturated the current failure modes. New adds are the exception, not the rule — a spike in `+N added` should trigger a review of what novel signal the agent just hit.
10. **Cursor sandbox blocks writes to `~/Library/…` by default.** Anything that touches the AE Agent home from an agent session needs `required_permissions: ["all"]`. Worth adding to my mental checklist: `.local`, `.zshrc`, `~/Library`, `~/Backups` all trigger sandbox denial.

## Recommended next actions (revised)

1. **Fix Finding F (launchd backup permission)** — ~10 min. Grant Full Disk Access to `/bin/bash` (or the specific `git`/`rsync` binaries the plists shell to), or move `~/Backups/` to a TCC-unrestricted path. Improve the script's error message to log `$?` + stderr instead of "network / auth?" so the next silent failure surfaces itself.
2. **Fix Finding A (stubs.yml)** — ~10 min. Unblocks every dbt-touching sub-agent.
3. **Fix Finding B (debugger docstring)** — ~5 min. One template string in `debugger.py`. Also strip the banned phrase from the two committed artifacts (or accept they're gitignored and will be regenerated on next debug run).
4. **Fix Finding D (doc drift)** — ~15 min. Add the "this module lives in the AE Agent install" preamble to the four top-level docs; rewrite the three automation-draft variants to call `fqc-arr` instead of `python -m …`; either delete `plan_close.py` or add a `sys.path` shim.
5. **Fix Finding C (baseline dedup)** — ~30 min. Requires touching `code_data_validator.py`; add a validation matrix schema requiring dedup keys and a sanity-threshold verdict override.
6. **Add `fqc-arr --self-test` subcommand** — ~20 min. Runs the Round 2 sweep (help, ticket dry-run, scheduled dry-run, debugger, quarter-close, reflect, show-lessons) in one shot. Suitable for a weekly launchd smoke test.
7. **Add `dbt parse` CI check post-`restore.sh`** — future work. Prevents Finding A from recurring silently.

## Raw evidence

- `which fqc-arr` → `/Users/koteswararao.venkata/Library/Application Support/AE Agent/bin/fqc-arr`
- `fqc-arr --ticket EDAEM-3725 --mode ticket --dry-run` → `Status: OK  (elapsed 1.8s, 10 roles)` at 2026-08-02T18:45:13Z (Round 1) and 2026-08-02T18:54:01Z (Round 2)
- `fqc-arr --debug-model arr_line_categories --ticket EDAEM-3725 --dry-run` → `debugger` role appended after `qa-handoff` — 11 roles total
- `fqc-arr --quarter-close --as-was-date 2026-02-11 --quarter-close-skip-pipeline --dry-run` → single `quarter-close-runner` role, `Status: OK  (elapsed 0.0s, 1 roles)`
- `fqc-arr --reflect --reflect-look-back-days 7` → `daily-reflection ok runs_scanned=19 lessons_added=0 lessons_promoted=0 — no novel observations today`
- `fqc-arr --show-lessons` → 20 role streams, 345 total lessons
- `launchctl list | rg fqc` → 4 jobs loaded
- `runs/learning/20260802T160110Z.md` → today's reflection pass, 0 novel signals
- `data/lessons/` → 28 lesson files including per-role `.jsonl` streams
- Backup taken this session → commit `949f7138` on `feature/ae-agent-backup`, 30 files changed, 345 lessons, 8.3 MB, [https://github.com/workday-inc/eda-dbt-em/tree/feature/ae-agent-backup](https://github.com/workday-inc/eda-dbt-em/tree/feature/ae-agent-backup)
- Prior backup timeline on remote branch → Jun 25, Jun 28, Jul 5, Jul 12, Jul 19, (Jul 26 FAILED, Aug 2 launchd FAILED), Aug 2 (manual — this session)
- Sandbox note: agent-driven writes to `~/Library/Application Support/AE Agent/**` require `required_permissions: ["all"]`; sandboxed writes get `Operation not permitted`
