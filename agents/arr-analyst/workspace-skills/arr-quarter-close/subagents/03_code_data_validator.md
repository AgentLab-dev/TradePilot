# Sub-agent 3: code-data-validator

**Module**: `agents/arr_quarter_close/subagents/code_data_validator.py`
**Skills**: `dbt-model-debugger`, `snowflake-architect`, `finance-bsa-data-analyst`

## Responsibility

Two halves:

1. **Code scan** - ripgrep across `models/`, `tests/`, `macros/` for the
   `in_scope_models` from the requirements. Catalog affected files + flag
   grain/layering risks.
2. **Data proposals** - emit Snowflake SQL templates targeted at
   `finance_prod` (configurable) that the supervisor / user runs via the
   Snowflake MCP. No direct Snowflake connection from this module.

## Inputs

```json
{
  "requirements": <RequirementsSpec>,
  "project_dir": "/Users/.../eda-dbt-em",
  "snowflake_target_db": "finance_prod"
}
```

## Outputs (RoleResult)

```json
{
  "role": "code-data-validator",
  "status": "ok|warn",
  "payload": {
    "validation": {
      "code": {
        "affected_models": ["models/..."],
        "affected_macros": ["macros/..."],
        "grain_check_notes": "...",
        "layering_notes": "..."
      },
      "data": {
        "queries_run": ["select ... from finance_prod.aggregations.arr_product_categories ..."],
        "metric_baselines": {"max_as_was_date": "select ...", ...},
        "anomalies": []
      },
      "risks": [...],
      "proposed_changes": [...]
    }
  }
}
```

## When delegated as a Cursor Task

```text
subagent_type: generalPurpose
description: "Code+data validation EDAEM-XXXX"
prompt: |
  Read .cursor/skills/arr-quarter-close/subagents/03_code_data_validator.md.
  Run the module's heuristic scan, then run the proposed validation queries
  via the Snowflake MCP against finance_prod. Compare actuals to the
  RequirementsSpec; surface any anomaly as a risk and propose changes.

  RequirementsSpec input: <paste>
```

## Hard rules

- No direct Snowflake credentials in this sub-agent. Use the MCP.
- Read-only only. Any DDL/DML proposals go in `proposed_changes` for the
  implementer to apply, not executed here.
