# Sub-agent 6: test-runner

**Module**: `agents/arr_quarter_close/subagents/test_runner.py`

## Responsibility

Run pytest and dbt test, aggregate into a `TestReport` for the PR body and
the qa-handoff comment.

## What it runs

- `pytest -q --junitxml=.cursor/test-results/pytest.xml tests`
- `dbt test --select test_arr_waterfall_balance` (with `--vars as_was_date=...` if supplied)
- `dbt test --select tag:ia_migration` (same)

Selectors are configurable via `TestInput.dbt_test_selectors`.

## Outputs (RoleResult)

```json
{
  "role": "test-runner",
  "status": "ok|warn",
  "payload": {
    "test_report": {
      "pytest_passed": 12,
      "pytest_failed": 0,
      "pytest_skipped": 1,
      "dbt_test_results": [{"selector": "...", "status": "pass|fail", "tail": "..."}],
      "junit_xml_path": ".cursor/test-results/pytest.xml",
      "dbt_target_path": "target",
      "overall_passed": true
    }
  },
  "artifacts": {
    "junit_xml": ".cursor/test-results/pytest.xml",
    "dbt_target": "target"
  }
}
```

## When delegated as a Cursor Task

```text
subagent_type: shell
description: "Run tests EDAEM-XXXX"
prompt: |
  Run pytest and dbt test per the sub-agent module:
    python -m agents.arr_quarter_close.subagents.test_runner
  Return the TestReport JSON only. Do not interpret failures here - the
  qa-handoff sub-agent attaches the report verbatim.
```

## Quality bar

- pytest_failed > 0 -> WARN at sub-agent level; supervisor decides whether
  to halt the DAG before the pr-author.
- dbt waterfall / ia_migration failures -> WARN; they are `severity='warn'`
  by design and store failing rows in `<env>.stage.test_*`.
