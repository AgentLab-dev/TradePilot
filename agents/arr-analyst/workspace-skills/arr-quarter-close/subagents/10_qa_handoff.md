# Sub-agent 10: qa-handoff

**Module**: `agents/arr_quarter_close/subagents/qa_handoff.py`
**Pattern**: `scripts/update_jira_desc.py` (ADF tables / headings / mentions)
**Rule**: `jira-api-access.mdc`

## Responsibility

When CI + CD are green and finance_dev / finance_qa validations have been
reviewed, post a "Ready for QA" comment to the ticket and attach test
artifacts. Pause unless `auth_mode=full_auto`.

## Comment shape

ADF document with:

- Bold lead "Ready for QA review."
- A heading + a 2-column table with: pytest passed/failed/skipped, dbt
  test count, CI final state, finance_dev validated, CD final state,
  finance_qa validated.
- A bullet list mirroring the acceptance criteria from the ticket.

## Attachments

Always attach (when present):

- `.cursor/test-results/pytest.xml` (junit)
- `target/run_results.json` (dbt run results)

## Inputs

```json
{
  "ticket": <TicketSpec>,
  "test_report": <TestReport>,
  "ci_report": <CIReport>,
  "cd_report": <CDReport>,
  "qa_ticket_key": null,
  "auth_mode": "smart_gates"
}
```

## Outputs (RoleResult)

```json
{
  "role": "qa-handoff",
  "status": "needs_input|ok|fail",
  "pause_reason": "Approve to post QA-readiness comment + attach artifacts",
  "payload": {
    "qa_handoff": {
      "ticket_key": "EDAEM-3725",
      "qa_ticket_key": "EDAEM-3725",
      "description_updated": false,
      "comment_posted": false,
      "transitions_applied": [],
      "attached_artifacts": [".cursor/test-results/pytest.xml", "target/run_results.json"]
    },
    "adf_preview": { "body": {...} }
  }
}
```

## When delegated as a Cursor Task

```text
subagent_type: shell
description: "QA handoff EDAEM-XXXX"
prompt: |
  Read .cursor/skills/arr-quarter-close/subagents/10_qa_handoff.md and
  .cursor/rules/jira-api-access.mdc. In auth_mode=smart_gates, return the
  ADF preview only. In auth_mode=full_auto, POST the comment + attach files.
  Return QAHandoffResult JSON.
```

## Optional transition

The module can transition the ticket to "Ready for QA" if you pass an
explicit transition id (see the Jira API rule for the discovery command).
Default: no transition - the user moves the ticket manually after review.
