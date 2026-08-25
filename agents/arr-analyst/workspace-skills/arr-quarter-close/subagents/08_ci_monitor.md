# Sub-agent 8: ci-monitor

**Module**: `agents/arr_quarter_close/subagents/ci_monitor.py`
**Pattern**: `.cursor/cloud-agent/monitor_pr458_slack.sh` (poll + heartbeat)
**Skills**: `babysit`, `ci-investigator` subagent, `slack-enterprise`

## Responsibility

Loop on `gh pr checks <PR>` every 10 min, post a Slack heartbeat each poll,
stop at a terminal state. On success, emit (do not run) finance_dev
validation queries the supervisor runs via the Snowflake MCP.

## Slack channel pinning

`slack_channel` must be supplied before the monitor starts. If not, the
sub-agent pauses with `needs_input` so the supervisor can pin a channel
once per ticket. The user can hand any of:

- `C0123ABCD` - channel id
- `D0123ABCD` - DM id
- `U03GK3V2FQU` - user id (DM is opened on the fly)

## Inputs

```json
{
  "pr_url": "https://github.com/workday-inc/eda-dbt-em/pull/472",
  "pr_number": 472,
  "slack_channel": "U03GK3V2FQU",
  "poll_minutes": 10,
  "max_hours": 4.0,
  "check_name_pattern": "ci/dbt_cloud",
  "validation_db": "finance_dev",
  "validation_sql_paths": ["scripts/finance_prod_recon_harness.sql"]
}
```

## Outputs (RoleResult)

```json
{
  "role": "ci-monitor",
  "status": "ok|warn|fail",
  "payload": {
    "ci_report": {
      "pr_number": 472,
      "final_state": "pass|fail|timeout",
      "polls_sent": 12,
      "last_status_url": "...",
      "finance_dev_validation_passed": null,
      "validation_notes": ["Run via Snowflake MCP against finance_dev: ..."]
    }
  }
}
```

## When delegated as a Cursor Task

```text
subagent_type: shell
description: "CI monitor for PR #XXX"
prompt: |
  Run agents/arr_quarter_close/subagents/ci_monitor.py for PR #XXX.
  Use slk for Slack (per .cursor/skills/slack-enterprise/SKILL.md). Post
  one heartbeat per poll. Stop on terminal state. Return CIReport JSON.
```

## Failure recovery

If CI fails (not timeout), call the `ci-investigator` subagent for
root-cause; surface the summary in the qa-handoff comment.
