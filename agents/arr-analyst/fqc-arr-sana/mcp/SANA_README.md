# FQC-ARR MCP servers (Sana port)

Six custom MCP servers wrap the existing FQC-ARR side-effect code. Each tool is a thin shim over a function that already exists in the Python agent — no business logic is rewritten. Annotation discipline drives Sana's human-in-the-loop behavior: `readOnlyHint=true` runs silently; `destructiveHint=true` triggers a Tasks-inbox approval card.

## Servers & annotation summary

| Server | Representative tools | reads | gated writes (destructiveHint) |
|---|---|---|---|
| `SANA_fqc-snowflake` | `run_query` (SELECT only) | ✅ read-only | — (never writes) |
| `SANA_fqc-jira` | `get_issue`, `search` / `add_comment`, `add_attachment`, `transition` | ✅ | ✅ all writes |
| `SANA_fqc-dbt` | `build`, `test`, `get_run_status`, `compile` / `run` | ✅ (status, compile) | ✅ **prod `run` only** |
| `SANA_fqc-github` | `get_pr`, `pr_checks`, `create_branch` / `push_branch`, `create_pr` | ✅ | ✅ push + PR |
| `SANA_fqc-slack` | `notify`, `post_thread` | n/a | — (status only, not a data write) |
| `SANA_fqc-lessons` | `load_for`, `search` / `record`, `promote`, `archive`, `reflect` | ✅ | — (own knowledge collection) |

## Reuse mapping (what each shim calls)

- `SANA_fqc-jira` → the same curl + `JIRA_API_TOKEN` calls in `jira_intake.py` / `clarifier.py` / `qa_handoff.py`. Never the Atlassian MCP.
- `SANA_fqc-snowflake.run_query` → executes the `sql_template` strings the sub-agents already emit (ValidationMatrix rows). SELECT-only guard.
- `SANA_fqc-dbt` → wraps `ARRCloseOrchestrator` / `test_runner` (local dbt CLI + dbt Cloud API).
- `SANA_fqc-github` → wraps the `gh` CLI calls in `pr_author.py` / `ci_monitor.py`.
- `SANA_fqc-slack` → wraps the `slk` CLI notify path; directory resolution replaces `slack_directory.json`.
- `SANA_fqc-lessons` → wraps the JSONL lessons store (`data/lessons/*.jsonl`, `_stable.jsonl`) + `--learn`.

## Agent-Ready Tools (Workday-governed) vs custom MCP

Anything with a Workday-governed equivalent (finance org / policy / entitlement context) should be read through a Workday **Agent-Ready Tool** so it inherits Workday governance + audit. Snowflake / dbt / Sigma have no Workday-governed equivalent, so they stay custom MCP; governance for those is enforced by (a) `readOnlyHint` on reads, (b) approval on prod writes, (c) Agent Passport attestation.

## Identity

Replace machine-local creds (`~/.zshrc` Jira token, `slk` Keychain, `gh` session) with Sana connector auth (OAuth2 `securityScheme` on each server). Sana holds the tokens and mirrors the invoking user's permissions — an upgrade over the single-identity `U03GK3V2FQU` model.

> Schemas here follow the MCP tool-annotation shape (`readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`). Reconcile field names against the final Sana/Workday GA connector schema before Phase 3.
