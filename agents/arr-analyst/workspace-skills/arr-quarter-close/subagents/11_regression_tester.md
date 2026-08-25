# Sub-agent 11: regression-tester

## Responsibility

Pre-production regression test for ref-file and source-system updates. Detects recent
changes, rebuilds the ARR pipeline in dev, validates against prod, and issues a PASS
(proceed with tonight's prod load) or FAIL (alert business to rollback) verdict.

## Trigger phrases

- "fcq-arr regression test"
- "regression test before tonight's prod load"
- "validate source changes in dev"
- "check if gsheet changes are safe for production"
- "rebuild dev and compare with prod"

## Workflow

```
Phase 1: DETECT   → Scan ref tables for recent updates (last N hours)
    ↓
Phase 2: REBUILD  → dbt run in finance_dev (production code, updated sources)
    ↓
Phase 3: VALIDATE → Compare finance_dev vs finance_prod (rows, ARR, flags)
    ↓
Phase 4: VERDICT  → PASS / PASS WITH NOTES / FAIL
    ↓
Phase 5: NOTIFY   → Slack DM + report document
```

## Inputs

```json
{
  "lookback_hours": 48,
  "dev_db": "finance_dev",
  "prod_db": "finance_prod",
  "as_was_dates": ["2026-08-03", "2026-08-04"],
  "slack_user": "U03GK3V2FQU",
  "tolerance_pct": 0.01,
  "tolerance_abs": 1.00,
  "dbt_target": "dev",
  "branch": "main"
}
```

## Outputs (RoleResult)

```json
{
  "role": "regression-tester",
  "status": "pass|pass_with_notes|fail",
  "payload": {
    "source_changes": [
      {
        "ref_table": "ref_strategic_partners_ref_strategic_partners",
        "rows_changed": 80,
        "latest_batch": "2026-08-04",
        "last_synced": "2026-08-04T20:14:37Z"
      }
    ],
    "build_results": {
      "models_built": 15,
      "build_duration_s": 420,
      "failures": 0
    },
    "validation_results": {
      "row_parity": {"dev": 611808713, "prod": 611808713, "delta": 0, "status": "pass"},
      "arr_total": {"dev": -1334473.0, "prod": -1334473.0, "delta": 0.0, "status": "pass"},
      "flag_distribution": {"expected_changes": 9, "unexpected_regressions": 0, "status": "pass"},
      "waterfall_balance": {"imbalance_rows": 0, "status": "pass"}
    },
    "verdict": "pass",
    "action": "Source updates validated. Safe to proceed with tonight's production load.",
    "rollback_needed": false,
    "report_path": "/Users/.../Documents/Cursor/Documents/fcq_arr_regression_test_20260806.md"
  }
}
```

## When delegated as a Cursor Task

```text
subagent_type: generalPurpose
description: "Regression test ARR pipeline"
prompt: |
  Read .cursor/commands/fcq-arr-regression-test.md for the full workflow.
  Execute all 5 phases:
    1. Detect: scan ref tables via Snowflake MCP for recent changes
    2. Rebuild: run dbt models in finance_dev via dbt MCP
    3. Validate: compare dev vs prod via Snowflake MCP
    4. Verdict: score and classify
    5. Notify: Slack DM + write report document

  Parameters: {paste inputs}
```

## Key queries (Snowflake MCP)

### Phase 1 — detect changes across all ref tables

```sql
select table_name, row_count, last_altered
from base_prod.information_schema.tables
where table_schema = 'GOOGLE_SHEETS'
  and table_name like 'REF_%'
order by last_altered desc;
```

### Phase 3 — validate changed flags

```sql
-- Generic: compare a boolean flag between dev and prod
select
    d.as_was_date,
    d.{FLAG_COL} as dev_flag,
    p.{FLAG_COL} as prod_flag,
    d.accts as dev_accts,
    p.accts as prod_accts,
    d.accts - p.accts as acct_delta
from (
    select as_was_date, {FLAG_COL}, count(distinct account_id) as accts
    from finance_dev.aggregations.arr_line_categories
    where as_was_date in ({DATES})
    group by 1, 2
) d
full outer join (
    select as_was_date, {FLAG_COL}, count(distinct account_id) as accts
    from finance_prod.aggregations.arr_line_categories
    where as_was_date in ({DATES})
    group by 1, 2
) p on d.as_was_date = p.as_was_date and d.{FLAG_COL} = p.{FLAG_COL}
order by 1, 2;
```

## Verdict thresholds

| Metric | PASS | WARN | FAIL |
|---|---|---|---|
| Row count delta | 0 | 1–100 | > 100 |
| ARR total delta | < $1 | $1–$1000 | > $1000 |
| Flag mismatch | Matches ref delta direction | Minor miscount | Wrong direction |
| Waterfall imbalance | $0 | < $0.01 | > $0.01 |

## Rollback decision tree

```
FAIL verdict
├── Ref Google Sheet change caused regression
│   └── Ask business owner to revert rows or mark is_deleted = TRUE
│       └── Wait for Fivetran sync → re-run regression test
├── Source system change (SFDC/Workday) caused regression
│   └── Cannot rollback source → add compensating ref override
│       └── Or: create hotfix dbt branch → re-run regression test
└── dbt code change caused regression
    └── Do NOT merge feature branch → switch to main → rebuild
```

## Hard rules

- No direct Snowflake credentials. Use Snowflake MCP for all queries.
- No dbt shell commands. Use dbt MCP for all model runs.
- Read-only validation only — no DDL/DML changes to finance_prod.
- Always write the report document to the canonical Documents folder.
- Never skip Phase 3 validation even if the build succeeds.
