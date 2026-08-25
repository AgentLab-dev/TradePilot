# Sub-agent 1: jira-intake

**Module**: `agents/arr_quarter_close/subagents/jira_intake.py`
**Skill / rule**: workspace rule `jira-api-access.mdc` (curl + env var pattern)

## Responsibility

Fetch a Jira ticket via REST API (no MCP - the Atlassian MCP is deprecated
for Jira per the rule), flatten the ADF description to plain text, harvest
labels / components / comments, and extract bullet-style acceptance criteria.

## Inputs

```json
{ "ticket_key": "EDAEM-3725", "include_comments": true, "include_changelog": false }
```

Env vars required: `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`.

## Outputs (RoleResult)

```json
{
  "role": "jira-intake",
  "status": "ok|fail",
  "payload": {
    "ticket": {
      "ticket_key": "EDAEM-3725",
      "summary": "...",
      "status": "Ready for Dev",
      "labels": [...],
      "components": [...],
      "description_text": "...",
      "acceptance_criteria": ["...", "..."],
      "comments": [{"author": "...", "created": "...", "body": "..."}],
      "raw_url": "https://workdaybt.atlassian.net/browse/EDAEM-3725"
    }
  }
}
```

## When delegated as a Cursor Task

```text
subagent_type: generalPurpose
description: "Jira intake EDAEM-XXXX"
prompt: |
  Run agents/arr_quarter_close/subagents/jira_intake.py for EDAEM-XXXX.
  Use $JIRA_EMAIL / $JIRA_API_TOKEN from the environment (per
  .cursor/rules/jira-api-access.mdc - DO NOT use the Atlassian MCP for Jira).
  Return the TicketSpec JSON only.
```

## Failure modes

- `fail` with "JIRA_EMAIL / JIRA_API_TOKEN not set" -> stop; ask the user.
- `fail` with 401/403 -> token refresh needed (rule has the smoke test).
- `ok` with empty `acceptance_criteria` -> requirements-analyzer will surface
  this as an open question to the clarifier.
