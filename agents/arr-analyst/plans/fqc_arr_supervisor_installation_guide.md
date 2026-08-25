# FQC-ARR Supervisor — Installation Guide (for the team)

How to install and run the **FQC-ARR** agent — a deterministic Python **Supervisor** that
dispatches **12 specialist sub-agents** to work an ARR finance ticket end-to-end
(intake → validation → testing → PR → CI/CD → QA hand-off) against the `eda-dbt-em` dbt repo.

---

## Is there a plugin for this? (read first)

**No — the Supervisor is a standalone Python application, not a Cursor plugin.** There are two
separate things, and a full setup uses both:

| | **ae-agent-toolkit** (Cursor plugin) | **FQC-ARR Supervisor** (this guide) |
|---|---|---|
| What | Skills, rules, `/`-commands, 2 read-only Cursor subagents (`arr-validator`, `finance-eda-triage`), MCP config | Deterministic Python Supervisor + 12 sub-agents + lesson store + `fqc-arr` CLI |
| Install | Cursor **Customize → Plugins** (from `eda-dbt-training @ fature/AI-AE`) | Clone the agent home, set env vars, put `fqc-arr` on PATH (below) |
| Runs where | Inside the Cursor IDE | A CLI on your machine; the LLM steps hand back to a Cursor session |
| Guide | `ae_agent_toolkit_getting_started.md` | **this file** |

They're complementary: install the **plugin** for the Cursor-side knowledge, and the
**Supervisor** for the orchestration. You can run one without the other, but they're best together.

---

## What you're installing

```
$FQC_ARR_HOME  (~/Library/Application Support/AE Agent/)
├── bin/fqc-arr                         ← the launcher you put on PATH
├── agents/arr_quarter_close/
│   ├── supervisor.py                   ← deterministic controller (no LLM)
│   ├── cli.py, contracts.py, lessons.py, notifier.py, cursor_runner.py
│   ├── subagents/                      ← the 12 sub-agents (+ helpers)
│   └── data/lessons/                   ← per-role JSONL lesson store (+ seed_*.py)
├── runs/{learning,thinking}/           ← audit + transcripts (regenerable)
└── launchd/                            ← optional scheduled jobs (learning/backup)
```

### The 12 sub-agents

**10-role ticket DAG (Mode B), in order:**
1. `jira-intake` — pull ticket, ACs, comments
2. `requirements-analyzer` ⟢ — prose → KPI spec + in-scope models
3. `code-data-validator` — grain checks, lineage, Snowflake baselines
4. `clarifier` ⟢ — surface open questions (terminal → Slack → Jira)
5. `implementer` ⟢ — **human boundary**: SQL written in the Cursor session
6. `test-runner` — dbt build + tests + pytest
7. `pr-author` — open PR to `qa`
8. `ci-monitor` — poll GitHub + dbt Cloud
9. `cd-monitor` — watch qa deploy
10. `qa-handoff` — update Jira + validation matrix

**On-demand (not in the linear DAG):**
11. `debugger` — lineage walk → matrix → ranked root cause → proposed fix (never writes it)
12. `quarter-close-runner` — runs the ARR pipeline + 7-check reconciliation

> ⟢ = LLM-driven leaf (emits a prompt + `preferred_model`, hands back to the runtime).
> A 13th pass, `daily-reflection`, powers the learning loop (scheduled, optional).

---

## Prerequisites

- **macOS** with `python3` (3.11+) — the core uses only the Python **standard library**; no pip install required to run the DAG.
- **Cursor IDE** + Claude access — the LLM sub-agents hand their prompts back to a Cursor session.
- **The `ae-agent-toolkit` plugin installed** (recommended companion — see the getting-started guide).
- **The `eda-dbt-em` dbt project** cloned locally, with `dbt` on PATH.
- **MCP servers configured** (Snowflake, dbt, Salesforce, Sigma) — used by the validation/monitor sub-agents. These come from the plugin's `mcp.json`; set the env vars in `~/.zshrc`.
- **Jira** REST access (`JIRA_BASE_URL` / `JIRA_EMAIL` / `JIRA_API_TOKEN`) and the **Slack desktop app** open (the notifier uses the `slk` CLI session).

---

## Step 1 — Get the agent code

The full agent home is version-controlled on the weekly backup branch.

```bash
# Clone eda-dbt-em (if you don't have it) and check out the backup branch in a temp worktree
git clone https://github.com/workday-inc/eda-dbt-em.git ~/Documents/Cursor/eda-dbt-em
cd ~/Documents/Cursor/eda-dbt-em
git fetch origin feature/ae-agent-backup
git worktree add /tmp/ae-agent-src feature/ae-agent-backup

# Copy the agent home to its canonical macOS location
mkdir -p "$HOME/Library/Application Support"
cp -R "/tmp/ae-agent-src/.ae-agent-backup" "$HOME/Library/Application Support/AE Agent"
git worktree remove /tmp/ae-agent-src
```

> The canonical home is `~/Library/Application Support/` (not `~/Documents/`) so macOS TCC
> doesn't block background jobs. Add a convenience symlink if you like:
> `ln -s "$HOME/Library/Application Support/AE Agent" "$HOME/Documents/Cursor/AE Agent"`

---

## Step 2 — Set environment variables (`~/.zshrc`)

```bash
# --- FQC-ARR core ---
export FQC_ARR_HOME="$HOME/Library/Application Support/AE Agent"
export FQC_ARR_LESSONS_DIR="$FQC_ARR_HOME/agents/arr_quarter_close/data/lessons"
export FQC_ARR_PROJECT_DIR="$HOME/Documents/Cursor/eda-dbt-em"   # your dbt project
export PATH="$FQC_ARR_HOME/bin:$PATH"
# export FQC_ARR_PYTHON="python3.12"   # optional: pin the interpreter

# --- Also needed (shared with the plugin) ---
#   SNOWFLAKE_*, DBT_*, SF_ORG, SIGMA_*  (see ae_agent_toolkit_getting_started.md)
#   JIRA_BASE_URL / JIRA_EMAIL / JIRA_API_TOKEN
```

Then `source ~/.zshrc`.

---

## Step 3 — Make it yours (per-user config)

The copied home carries the original operator's personal settings. Update these:

1. **Slack identity** — pass *your* Slack user ID on runs (`--slack-channel <YOUR_SLACK_USER_ID>`).
   Find it: Slack profile → **Copy member ID** (starts with `U…`).
2. **Stakeholder notifications** — set your own `--notify <name>` recipients per run.
3. **Slack directory** — `agents/arr_quarter_close/data/slack_directory.json` is a cached name→ID
   lookup; refresh entries for the people you'll tag.
4. **Lessons store** — the copied `data/lessons/` holds the original operator's accumulated lessons.
   Either **keep them** (inherit institutional memory) or **start fresh**:
   ```bash
   # optional: reset to just the curated seeds
   cd "$FQC_ARR_HOME/agents/arr_quarter_close"
   python3 data/seed_lessons.py          # 13 operational lessons
   python3 data/seed_self_lessons.py     # 29 self-knowledge lessons
   python3 data/seed_refactor_lessons.py # 22 IA-refactor lessons
   ```

---

## Step 4 — Verify

```bash
which fqc-arr                     # -> $FQC_ARR_HOME/bin/fqc-arr
fqc-arr --show-lessons           # prints the lessons table (proves imports + store work)
fqc-arr --ticket EDAEM-XXXX --mode ticket --dry-run   # dry-run: no writes, shows the DAG plan
```

A clean `--show-lessons` table and a dry-run that walks the roles without erroring means you're good.

---

## Step 5 — Run it

```bash
# Full ticket, smart-gated (pauses before each write), with notifications
fqc-arr --ticket EDAEM-3725 --auto \
        --slack-channel <YOUR_SLACK_USER_ID> \
        --notify <name1> --notify <name2>

# Point at a different dbt working tree (e.g. a per-ticket worktree)
fqc-arr --ticket EDAEM-3725 --project-dir ~/Documents/Cursor/eda-dbt-em-edaem-3725

# Debug a specific model on demand
fqc-arr --ticket EDAEM-3725 --debug-model arr_line_categories

# Scheduled quarter close (Mode A) + reconciliation
fqc-arr --as-was-date 2026-02-11 --target qa --quarter-close

# Inspect / learn
fqc-arr --show-lessons debugger   # one role
fqc-arr --reflect                 # run only the daily-reflection pass
fqc-arr --learn                   # full continuous-learning pass
```

**Authorization dial:** default is **smart-gated** — the agent pauses before every side-effecting
write (PR, Jira, code). `--auto` / full-auto is opt-in. The `implementer` step is always a human
boundary: the SQL is written in your Cursor session, never by a nested autonomous agent.

**Steer a live run from Slack** (the agent polls its own thread):
- `task: pause` · `task: skip clarifier` · `task: debug <model>` · `task: cancel`
- `ans: 1) USD_HIST  2) 2026-05-11  3) account grain` — answer the clarifier; it absorbs and continues.

---

## Step 6 (optional) — Scheduled jobs (learning + backup)

These are **per-user** macOS `launchd` jobs. If you want them, copy the plists and **rename the
label** to your own prefix so they don't collide with other installs:

```bash
# Example: rename com.<operator>.fqcarr.* -> com.<you>.fqcarr.*
cp "$FQC_ARR_HOME/launchd/"*.plist ~/Library/LaunchAgents/
# edit each plist: change the <string>com.<...>.fqcarr.*</string> Label + any absolute paths
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.<you>.fqcarr.learn-am.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.<you>.fqcarr.learn-pm.plist
```

- **learn-am / learn-pm** (09:00 / 17:00): mine thinking + run logs, distill lessons, promote any seen ≥3×, DM you on Slack.
- **backup-weekly** (Sun 02:00): rsync the agent home to `feature/ae-agent-backup` on `eda-dbt-em`.

Manage: `launchctl print|kickstart -k|bootout gui/$(id -u)/com.<you>.fqcarr.learn-am`.

---

## Team rollout notes (important)

The agent was built **single-operator**. For a team, mind what's **shared** vs **per-user**:

| State | Shared? | Guidance |
|---|---|---|
| **Code** (`agents/`, `bin/`) | Shared | Everyone runs the same version; pull updates from the backup branch. |
| **Lessons** (`data/lessons/`) | Choose | Inherit for shared memory, **or** reset to seeds per user. A shared lessons store needs a shared sync (not built yet — see below). |
| **Slack identity / notify** | Per-user | Each person uses their own `--slack-channel` + `--notify`. |
| **launchd jobs** | Per-user | Unique label prefix per machine; don't reuse `com.kvenkata.*`. |
| **Credentials** | Per-user | Everyone sets their own `~/.zshrc` env vars. Never commit tokens. |

**Not yet built for multi-user:** a central shared lesson store, a shared service account, and a
packaged installer. Today each teammate runs their own copy. If we want a true shared deployment,
the next step is to package the agent home (pip/uv installable) and point `FQC_ARR_LESSONS_DIR`
at a shared, version-controlled store.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `fqc-arr: command not found` | `PATH` missing `$FQC_ARR_HOME/bin`; `source ~/.zshrc` |
| `ModuleNotFoundError: agents...` | Launcher sets `PYTHONPATH`; run via `fqc-arr`, not `python cli.py` directly |
| `--show-lessons` empty | `FQC_ARR_LESSONS_DIR` unset or wrong; re-run the `seed_*.py` scripts |
| Snowflake/dbt/SF steps fail | MCP env vars not set — see `ae_agent_toolkit_getting_started.md` |
| Jira writes fail | Check `JIRA_*` vars; smoke-test `/rest/api/3/myself` (expect 200) |
| Slack DM/steering not working | Open the Slack desktop app so the `slk` Keychain session refreshes; use your own `U…` ID |
| Scheduled job never runs | Home must be under `~/Library/Application Support/` (not TCC-protected `~/Documents/`) |

---

## Reference

- `$FQC_ARR_HOME/README.md` — operator/maintainer reference (layout, backups, restore, schedule).
- `$FQC_ARR_HOME/agents/arr_quarter_close/README.md` — canonical command reference per sub-agent.
- `$FQC_ARR_HOME/agents/arr_quarter_close/contracts.py` — typed I/O for every sub-agent.
- Demo: `fqc_arr_30min_demo_talking_points.md` + `fqc_arr_demo_cheatsheet.md`.

Owner: **Workday ED&A — Analytics Engineering** (`[REDACTED_EMAIL]`).
