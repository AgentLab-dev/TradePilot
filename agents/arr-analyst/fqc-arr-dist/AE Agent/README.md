# AE Agent -- FQC-ARR (Finance ARR Quarter Close)

Standalone home for the **Analytics-Engineering Agent** that drives Salesforce-to-finance dbt work in the `eda-dbt-em` repo. Lives **outside the dbt repo** so accumulated lessons survive a re-clone.

## Where this folder really is

```
Real location:   ~/Library/Application Support/AE Agent/
Symlink (UI):    ~/Documents/Cursor/AE Agent  ->  ~/Library/Application Support/AE Agent
```

The real location is `~/Library/Application Support/` for two reasons:

1. **`~/Documents/` is TCC-protected on macOS.** Background `launchd` jobs cannot read from `~/Documents/` without Full Disk Access (which we'd rather not grant to `bash`). `~/Library/Application Support/` has no TCC restriction, so the 9am/5pm scheduled learning passes can run cleanly.
2. **It's the macOS-blessed location for per-user app data**, the same place Slack, Cursor, dbt Cloud Desktop, etc. store their state.

You can `cd "~/Documents/Cursor/AE Agent"` from Finder/Cursor as expected — the symlink resolves transparently.

## Layout

```
~/Library/Application Support/AE Agent/        <- $FQC_ARR_HOME
├── README.md                                  <- this file
├── agents/
│   └── arr_quarter_close/                     <- the 13 sub-agents + supervisor
│       ├── supervisor.py
│       ├── cli.py
│       ├── contracts.py
│       ├── lessons.py
│       ├── notifier.py
│       ├── core.py                             <- legacy ARRCloseOrchestrator
│       ├── subagents/                          <- jira-intake, requirements-analyzer,
│       │   ├── ...                             |   code-data-validator, clarifier,
│       │   └── daily_reflection.py             |   implementer, test-runner, pr-author,
│       └── data/                               |   ci-monitor, cd-monitor, qa-handoff,
│           ├── lessons/                        |   debugger, quarter-close-runner,
│           │   ├── _global.jsonl               |   daily-reflection.
│           │   ├── _stable.jsonl                <- promoted (occurrence_count >= 3)
│           │   ├── _reflection_log.jsonl        <- audit trail of every reflection pass
│           │   ├── <role>.jsonl x 13            <- per-role lessons
│           │   └── README.md
│           ├── seed_lessons.py                  <- 13 operational lessons
│           ├── seed_self_lessons.py             <- 29 self-knowledge lessons
│           ├── seed_refactor_lessons.py         <- 22 IA-refactor lessons
│           └── slack_directory.json             <- cached user-id lookup
├── bin/
│   ├── fqc-arr                                 <- launcher (put on PATH)
│   ├── fqcarr_learn.sh                          <- twice-daily wrapper
│   ├── watch_pr_ci.py                           <- async CI watcher
│   ├── watch_pr_ci.sh
│   └── watch_dbt_run.py
├── runs/
│   ├── learning/                                <- audit reports (one per learn pass)
│   │   ├── <UTC_ts>.md
│   │   ├── <UTC_ts>.log
│   │   ├── launchd_am.{out,err}
│   │   └── launchd_pm.{out,err}
│   └── thinking/                                <- mirror of any local thinking logs
└── launchd/                                     <- canonical copies of the launchd plists
    ├── com.example.fqcarr.learn-am.plist       <- 09:00 local
    └── com.example.fqcarr.learn-pm.plist       <- 17:00 local
```

The *active* launchd plists live at `~/Library/LaunchAgents/`. The copies under `launchd/` here are a backup so a fresh machine can be reconstructed quickly.

## Environment variables (set in `~/.zshrc`)

```bash
export FQC_ARR_HOME="$HOME/Library/Application Support/AE Agent"
export FQC_ARR_LESSONS_DIR="$FQC_ARR_HOME/agents/arr_quarter_close/data/lessons"
export FQC_ARR_PROJECT_DIR="$HOME/Documents/Cursor/eda-dbt-em"
export PATH="$FQC_ARR_HOME/bin:$PATH"
```

`bin/fqc-arr` reads `FQC_ARR_PROJECT_DIR` if you don't pass `--project-dir`. Override per-call:

```bash
fqc-arr --ticket EDAEM-3725 --project-dir ~/Documents/Cursor/eda-dbt-em-edaem-3725
```

## Common commands

```bash
# Run a ticket end-to-end (smart-gated, with stakeholder notifications)
fqc-arr --ticket EDAEM-3725 --auto --slack-channel <YOUR_SLACK_USER_ID> \
        --notify jane.doe --notify jane.doe

# Continuous learning -- manual one-off (same thing launchd runs at 9am/5pm)
fqc-arr --learn

# Inspect lessons
fqc-arr --show-lessons              # all roles, table
fqc-arr --show-lessons debugger     # one role

# Run only the daily-reflection pass (no DAG)
fqc-arr --reflect

# Quarter close (scheduled mode + on-demand quarter-close-runner)
fqc-arr --as-was-date 2026-02-11 --target qa --quarter-close
```

## Twice-daily continuous learning

Two macOS launchd jobs scan every learning source we capture (thinking logs + run logs), distill new lessons, promote anything that's been seen >=3 times, and DM the operator on Slack when there's something to report.

| Job label | Time (local) | Plist |
|---|---|---|
| `com.example.fqcarr.learn-am` | 09:00 | `~/Library/LaunchAgents/com.example.fqcarr.learn-am.plist` |
| `com.example.fqcarr.learn-pm` | 17:00 | `~/Library/LaunchAgents/com.example.fqcarr.learn-pm.plist` |

Audit reports land at `runs/learning/<UTC_ts>.md`.

### Manage the schedule

```bash
# status
launchctl print gui/$(id -u)/com.example.fqcarr.learn-am

# force-run now
launchctl kickstart -k gui/$(id -u)/com.example.fqcarr.learn-am

# stop scheduling (until next reboot or re-bootstrap)
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.example.fqcarr.learn-am.plist

# (re)install after edit
launchctl bootout   gui/$(id -u) ~/Library/LaunchAgents/com.example.fqcarr.learn-am.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.example.fqcarr.learn-am.plist
```

### Disable Slack DM for one run

```bash
FQC_LEARN_NO_SLACK=1 bin/fqcarr_learn.sh
```

### Always ping (even when no new lessons)

```bash
FQC_LEARN_ALWAYS_PING=1 bin/fqcarr_learn.sh
```

## Re-cloning the dbt repo is now safe

Before this move:
- The agent code and lessons lived inside `eda-dbt-em/agents/arr_quarter_close/`
- A `rm -rf eda-dbt-em && git clone ...` would wipe the entire agent

After this move:
- The agent home is in `~/Library/Application Support/` (independent of any git repo)
- Re-cloning `eda-dbt-em` is harmless -- the agent doesn't live there
- The agent's `bin/fqc-arr` reads `FQC_ARR_PROJECT_DIR` to find the dbt project, so it just keeps working against the fresh clone

What still needs the dbt project to exist somewhere:
- The implementer / test-runner / ci-monitor / cd-monitor / quarter-close-runner sub-agents run dbt commands and need the models on disk.
- Thinking logs (`runs/thinking/*.md`) are written under `$FQC_ARR_PROJECT_DIR/runs/thinking/` by default -- they're regenerable, so it's fine if a re-clone wipes them.

## Backup tiers (defense in depth)

There are three independent backups; any one of them is sufficient to restore the agent.

| Tier | Where | How often | Source of truth for |
|---|---|---|---|
| **1. Live working set** | `~/Library/Application Support/AE Agent/` | continuous (every run) | code, lessons, runs/, plist mirror |
| **2. Local tarball** | `~/Backups/ae-agent-YYYYMMDDTHHMMSSZ.tar.gz` | ad-hoc / manual | full home + active plists, single file |
| **3. Remote git branch** | `feature/ae-agent-backup` on `workday-inc/eda-dbt-em` | every Sunday at 02:00 local | full home, version-controlled (commit per week) |

Tier 3 means even total disk loss is recoverable from GitHub.

### Tier 3 -- weekly git backup to `feature/ae-agent-backup`

- Script: `bin/fqcarr_backup_weekly.sh`
- Schedule: `~/Library/LaunchAgents/com.example.fqcarr.backup-weekly.plist`
- Mechanics:
    1. Maintains a *bare* clone of `eda-dbt-em` at `~/Backups/eda-dbt-em-backup.git` (lives outside `~/Documents/`, so launchd is not blocked by macOS TCC).
    2. Adds a git worktree at `~/Backups/ae-agent-worktree` on branch `feature/ae-agent-backup`.
    3. `rsync`s the full agent home into `<worktree>/.ae-agent-backup/` (excludes `__pycache__`, `.DS_Store`, `*.pyc`, and the backup job's own `runs/backups/` audit folder).
    4. Also snapshots the live `~/Library/LaunchAgents/com.example.fqcarr.*.plist` files into `<worktree>/.ae-agent-backup/launchd_live/` so disaster recovery is self-contained.
    5. `git add` + `git commit` (no-op if nothing changed; never force-pushes).
    6. `git push origin feature/ae-agent-backup` (fast-forward only).
    7. Writes an audit report to `runs/backups/<UTC-ts>.{log,md}` and DMs the operator on Slack with the commit SHA + counts.
- Your live `~/Documents/Cursor/eda-dbt-em` working tree is *never* touched. All git activity happens against the dedicated bare clone.

#### Manage the weekly backup

```bash
launchctl print gui/$(id -u)/com.example.fqcarr.backup-weekly | head -20
launchctl kickstart -k gui/$(id -u)/com.example.fqcarr.backup-weekly      # run now
launchctl bootout   gui/$(id -u) ~/Library/LaunchAgents/com.example.fqcarr.backup-weekly.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.example.fqcarr.backup-weekly.plist
```

#### Inspect the backup branch on GitHub

- Branch: <https://github.com/workday-inc/eda-dbt-em/tree/feature/ae-agent-backup>
- Backup contents: <https://github.com/workday-inc/eda-dbt-em/tree/feature/ae-agent-backup/.ae-agent-backup>
- Commit history (one commit per week): <https://github.com/workday-inc/eda-dbt-em/commits/feature/ae-agent-backup>

### Tier 2 -- ad-hoc local tarball

```bash
tar -czf ~/Backups/ae-agent-$(date +%Y%m%dT%H%M%SZ).tar.gz \
    -C "$HOME/Library/Application Support" "AE Agent" \
    -C "$HOME/Library/LaunchAgents" \
        "com.example.fqcarr.learn-am.plist" \
        "com.example.fqcarr.learn-pm.plist" \
        "com.example.fqcarr.backup-weekly.plist"
```

## How to restore on a fresh machine

### Option A -- from the weekly git backup (tier 3, preferred)

```bash
# 1. Clone the repo and switch to the backup branch
git clone https://github.com/workday-inc/eda-dbt-em.git ~/Documents/Cursor/eda-dbt-em
cd ~/Documents/Cursor/eda-dbt-em
git checkout feature/ae-agent-backup

# 2. Move the backup subdir to its canonical home
mkdir -p "$HOME/Library/Application Support"
cp -R .ae-agent-backup "$HOME/Library/Application Support/AE Agent"

# 3. Re-create the convenience symlink
ln -s "$HOME/Library/Application Support/AE Agent" \
      "$HOME/Documents/Cursor/AE Agent"

# 4. Restore + bootstrap the launchd jobs
cp "$HOME/Library/Application Support/AE Agent/launchd_live/"*.plist \
   "$HOME/Library/LaunchAgents/"
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.example.fqcarr.learn-am.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.example.fqcarr.learn-pm.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.example.fqcarr.backup-weekly.plist

# 5. Re-source the FQC_ARR_* env block in ~/.zshrc, then `source ~/.zshrc`
```

### Option B -- from a local tarball (tier 2)

```bash
# 1. Extract
tar -xzf ~/Backups/ae-agent-YYYYMMDDTHHMMSSZ.tar.gz \
    -C "$HOME/Library/Application Support/"
# 2. Re-link plists
cp "$HOME/Library/Application Support/AE Agent/launchd/"*.plist ~/Library/LaunchAgents/
# 3. Re-create the symlink
ln -s "$HOME/Library/Application Support/AE Agent" "$HOME/Documents/Cursor/AE Agent"
# 4. Re-source ~/.zshrc env block
# 5. Bootstrap launchd
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.example.fqcarr.learn-am.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.example.fqcarr.learn-pm.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.example.fqcarr.backup-weekly.plist
```

## Reference docs (live in `agents/arr_quarter_close/`)

- `agents/arr_quarter_close/README.md` -- canonical command reference for every sub-agent
- `agents/arr_quarter_close/data/lessons/README.md` -- lessons store schema
- `agents/arr_quarter_close/subagents/` -- one Python file per sub-agent
- `agents/arr_quarter_close/contracts.py` -- typed input/output for every sub-agent

## Why this split exists

- **Code (`agents/`, `bin/`)**: the agent's "operating system." Slow-changing, edit when adding sub-agents.
- **Data (`agents/.../data/lessons/`)**: accumulated knowledge. Grows daily through the twice-daily learning pass.
- **State (`runs/learning/`, `runs/thinking/`)**: per-run audit + transcripts. Append-only, regenerable.
- **Schedule (`launchd/`)**: ops glue. Lives outside the agent code so changing the schedule doesn't require touching Python.

Edit each layer independently. The Python code never reaches into `~/Library/LaunchAgents/` and the plists never reach into the Python code.
