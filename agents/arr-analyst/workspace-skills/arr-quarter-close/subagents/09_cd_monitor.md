# Sub-agent 9: cd-monitor

**Module**: `agents/arr_quarter_close/subagents/cd_monitor.py`
**Reuses**: `.cursor/cloud-agent/monitor_dbt_run.py` (the full prior-quarter
flow: dbt Cloud API poll + Snowflake validation + Slack DM)
**Skills**: `dbt-system-admin`, `dbt-platform-architect`, `slack-enterprise`

## Responsibility

Poll the dbt Cloud run id that CD spawned, post Slack heartbeats, run
finance_qa validation when the run succeeds.

If `DBT_CLOUD_*` env vars are present and `monitor_dbt_run.py` exists, the
sub-agent delegates to that script (its production-tested heartbeat shape).
Otherwise it polls via `curl` against the dbt Cloud Administrative API.

## Inputs

```json
{
  "dbt_cloud_run_id": 121072,
  "pr_url": "...",
  "slack_channel": "U03GK3V2FQU",
  "poll_minutes": 10,
  "max_hours": 4.0,
  "validation_db": "finance_qa",
  "validation_sql_paths": ["scripts/finance_prod_recon_harness.sql"]
}
```

Env vars (if delegating to `monitor_dbt_run.py`):

- `DBT_CLOUD_API_TOKEN`, `DBT_CLOUD_ACCOUNT_ID`, `DBT_CLOUD_BASE_URL`
- `SNOWFLAKE_*` (for the script's validation step)
- `SLACK_BOT_TOKEN`, `SLACK_DM_USER_ID`

## Outputs (RoleResult)

```json
{
  "role": "cd-monitor",
  "status": "ok|warn|fail",
  "payload": {
    "cd_report": {
      "run_id": 121072,
      "final_state": "success|error|timeout",
      "finance_qa_validation_passed": null,
      "validation_notes": ["Run via Snowflake MCP against finance_qa: ..."]
    }
  }
}
```

## When delegated as a Cursor Task

```text
subagent_type: shell
description: "CD monitor for run XXXXX"
prompt: |
  Run agents/arr_quarter_close/subagents/cd_monitor.py for dbt Cloud run id
  XXXXX. Honor the existing monitor_dbt_run.py if env vars are set. Post
  Slack heartbeats per poll. Return CDReport JSON.
```

## How the run id is obtained

If the supervisor doesn't have a run id yet, it pauses (`needs_input`).
Typical sources:

- `gh pr view <merged-pr> --json mergeCommit` + dbt Cloud webhook log.
- dbt Cloud UI - find the most recent job run with `git_sha` matching the
  merge commit.
- The CD GitHub Action job log (it prints the dbt Cloud run url).
