# Sub-agent 4: clarifier

**Module**: `agents/arr_quarter_close/subagents/clarifier.py`
**Skills**: `professional-writing`; pattern from `scripts/update_jira_desc.py`
(ADF helpers)
**Rule**: `jira-api-access.mdc`

## Responsibility

Generate a single clarifying-questions comment for the Jira ticket, built
from `RequirementsSpec.questions` + KPI-level `open_questions` + risk-[REDACTED]
items from the validator.

## Pause behavior (smart-gates default)

Returns `status="needs_input"` with the ADF payload in `payload.clarification.adf_payload`.
Posts to Jira automatically only under `auth_mode=full_auto`.

## Inputs

```json
{
  "ticket": <TicketSpec>,
  "requirements": <RequirementsSpec>,
  "validation": <ValidationReport>,
  "auth_mode": "smart_gates"
}
```

## Outputs (RoleResult)

```json
{
  "role": "clarifier",
  "status": "ok|needs_input|fail",
  "pause_reason": "Approve to post clarifier comment to Jira",
  "payload": {
    "clarification": {
      "ticket_key": "EDAEM-3725",
      "question_block_markdown": "**Clarifications needed...**\n1. ...",
      "adf_payload": { "body": {...ADF doc...} },
      "posted": false,
      "comment_id": null
    }
  }
}
```

## Resuming after approval

Either call the sub-agent again with `auth_mode=full_auto`, or post the
comment manually with the `adf_payload`:

```bash
curl -sS -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  -X POST -H "Content-Type: application/json" \
  --data "@adf.json" \
  "$JIRA_BASE_URL/rest/api/3/issue/EDAEM-3725/comment"
```

## When delegated as a Cursor Task

```text
subagent_type: generalPurpose
description: "Clarifier EDAEM-XXXX"
prompt: |
  Read .cursor/skills/arr-quarter-close/subagents/04_clarifier.md and
  .cursor/rules/jira-api-access.mdc. Generate the ADF payload only; do NOT
  POST unless the user has approved (auth_mode=full_auto).
```
