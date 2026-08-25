# FQC-ARR — Clean Team Distribution

This is a **sanitized, shareable copy** of the FQC-ARR Supervisor + 12 sub-agents, prepared for
teammates. It carries **no personal data** — no individual Slack IDs, emails, names, home paths,
or personal operator config.

## What was removed / reset vs the operator's working copy

| Item | Action |
|---|---|
| `data/slack_directory.json` | **Reset to an empty template** (all cached names/emails/Slack IDs removed) |
| Roster / stakeholder lessons | **Dropped 3** — PR "reviewer pool", author "leaderboard", and the stakeholder-SME contact map |
| Personal names/emails/IDs in lessons | **Scrubbed** to `<person>` / `[REDACTED_EMAIL]` / `<SLACK_USER_ID>` |
| Personal filesystem paths | **Scrubbed** to `${HOME}` |
| `runs/` (thinking + learning transcripts) | **Excluded** (regenerable, personal) |
| Mining/audit/scrape helper scripts (`_*.py`) | **Excluded** (personal tooling) |
| `_reflection_log.jsonl` (personal run audit) | **Excluded** |
| Code defaults (`--slack-channel`, `FQC_LEARN_SLACK_USER`, launchd labels) | **Genericized** (`com.example.*`, empty defaults) |
| launchd plists | Renamed to `com.example.fqcarr.*.plist.template`; absolute paths → `/Users/CHANGEME_USERNAME` |

## What was kept

- **All code** — supervisor, 12 sub-agents, CLI, contracts, notifier, seed scripts.
- **342 curated domain lessons** — snowflake / dbt / ARR / ACV / finance-metric / IA-refactor /
  validation / jira / PR / CI-CD knowledge. Only personal-roster lessons were dropped.
- **Re-seed scripts** (`data/seed_lessons.py`, `seed_self_lessons.py`, `seed_refactor_lessons.py`)
  so a teammate can reset to a curated baseline.

## Install

Follow **`fqc_arr_supervisor_installation_guide.md`** (in `~/Documents/Cursor/Documents/`). In short:

1. Copy this `AE Agent/` folder to `~/Library/Application Support/AE Agent/`.
2. Set the `FQC_ARR_*` env block in `~/.zshrc` (see the guide) and `source` it.
3. Make it yours: use your own `--slack-channel <YOUR_SLACK_USER_ID>` and `--notify` names;
   optionally re-seed lessons or keep the 342 curated ones.
4. Verify: `fqc-arr --show-lessons` then `fqc-arr --ticket EDAEM-XXXX --mode ticket --dry-run`.

## Note

If you enable the scheduled jobs, **rename** the `com.example.fqcarr.*` launchd labels to your own
prefix and fill in the `CHANGEME_USERNAME` / `<YOUR_SLACK_USER_ID>` placeholders first.
