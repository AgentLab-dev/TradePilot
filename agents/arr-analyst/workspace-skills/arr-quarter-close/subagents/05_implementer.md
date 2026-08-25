# Sub-agent 5: implementer

**Module**: `agents/arr_quarter_close/subagents/implementer.py`
**Skills**: `dbt-architect`, `dbt-model-debugger`, plus the existing
`arr-quarter-close` skill + rule
**Branch**: `feature/<ticket-key>-<slug>`

## Responsibility

1. Create the feature branch from `qa` (auto-attempted).
2. Emit an LLM prompt with the full change plan (in-scope models, KPI spec,
   validator risks/proposals, style constraints).
3. Signal `needs_snapshot_rebuild=True` if any `arr_*` or
   `stg_arr_categories` files are affected - the supervisor uses this to
   re-enter Mode A after testing.

The module does NOT apply the SQL edits itself. The Cursor IDE / coding
agent / human applies them based on the prompt.

## Inputs

```json
{
  "requirements": <RequirementsSpec>,
  "validation": <ValidationReport>,
  "project_dir": "...",
  "branch_prefix": "feature"
}
```

## Outputs (RoleResult)

```json
{
  "role": "implementer",
  "status": "needs_input",
  "pause_reason": "LLM-driven SQL edits required before test-runner",
  "payload": {
    "implementation": {
      "branch_name": "feature/edaem-3725-...",
      "edits": [{"path": "models/...", "summary": "..."}],
      "needs_snapshot_rebuild": true
    },
    "prompt": "<LLM prompt with KPI spec + style rules>",
    "branch_created": true|false,
    "branch_message": "..."
  }
}
```

## When delegated as a Cursor Task

```text
subagent_type: generalPurpose
description: "Implement EDAEM-XXXX"
prompt: |
  Read .cursor/skills/arr-quarter-close/subagents/05_implementer.md and
  .cursor/rules/arr-quarter-close.mdc. Apply the SQL edits per the change
  plan below; CTE-first, lowercase, 140 cols, 4-space indent. Pair every
  .sql with its .yml. Add or extend singular tests in tests/. Do NOT push -
  the pr-author sub-agent does that.

  Change plan: <paste from payload.prompt>
```

## Guardrails

- Never write to `models/finance/modeled/data_product/view/*.sql` other than
  view-shape changes (no business logic; per the supervisor rule).
- Never edit `dbt_project.yml::arr_refactor_as_was_date_list` without
  explicit user approval (close-date list).
