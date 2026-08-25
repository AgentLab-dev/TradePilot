# L1/L2 Support Runbook

## Pipeline Failures

### dbt Compilation Error

**Symptoms:** `dbt run` fails during compilation (before any model executes).

**Diagnosis:**
1. Read the error message — it usually points to the exact file and line
2. Common causes:
   - Jinja syntax error (missing `}}`, unclosed `{% %}` block)
   - Invalid `ref()` or `source()` — model/source was renamed or deleted
   - YAML parsing error in schema files (indentation, missing colons)
   - Macro argument mismatch

**Resolution:**
```bash
# Validate compilation without running
dbt compile --select model_name

# Check if a ref target exists
rg -l "model_name" models/ --type sql

# Validate YAML syntax
dbt parse
```

### dbt Run Error (SQL Execution)

**Symptoms:** Model compiles but Snowflake returns an error during execution.

**Diagnosis:**
1. Check the compiled SQL: `target/compiled/eda_dbt_em/models/.../model_name.sql`
2. Run the compiled SQL directly in Snowflake worksheet to get full error context
3. Common causes:

| Error | Cause | Fix |
|-------|-------|-----|
| `Object does not exist` | Upstream model not built, wrong database/schema | Rebuild upstream: `dbt run --select +model_name` |
| `Ambiguous column name` | Same column name in multiple joined tables | Qualify column with table alias |
| `Division by zero` | Unguarded division | Use `NULLIF(divisor, 0)` or `IFF(divisor = 0, NULL, ...)` |
| `Numeric value is not recognized` | Type mismatch in cast/join | Check column types, add explicit `TRY_CAST()` |
| `SQL compilation error: ... is not a valid group by expression` | Missing column in GROUP BY | Add column or wrap in aggregate |
| `Insufficient privileges` | Role cannot access source/target | Check grants (see Snowflake access section) |

### Timeout / Long-Running Query

**Symptoms:** Model runs for abnormally long time, eventually times out.

**Diagnosis:**
1. Check the query profile in Snowflake's query history
2. Look for:
   - Spillage to disk → Warehouse too small
   - Exploding row count → Bad join (many-to-many)
   - Full table scan → Missing filter, no partition pruning
   - Data volume growth → Source table has grown significantly

**Resolution:**
```sql
-- Check if the model's query is still running
SELECT query_id, query_text, execution_status, total_elapsed_time/1000 as seconds
FROM TABLE(information_schema.query_history())
WHERE query_text ILIKE '%model_name%'
ORDER BY start_time DESC
LIMIT 5;

-- Cancel a stuck query
SELECT SYSTEM$CANCEL_QUERY('query_id');
```

- If spillage: scale up warehouse temporarily for the run
- If bad join: use `dbt-model-debugger` skill to trace join inflation
- If data growth: add tighter incremental filter or partition the source query

---

## Data Quality Issues

### Missing Data / Incomplete Results

**Diagnosis checklist:**
1. Check source freshness: `dbt source freshness --select source:base_prod`
2. Check if incremental filter is too restrictive
3. Check for new filter conditions added inadvertently
4. Check if upstream model was run in wrong order

```sql
-- Quick row count comparison across dates
SELECT as_was_date, COUNT(*) as row_count
FROM certified.stage.stg_em_opportunity_scd2
GROUP BY as_was_date
ORDER BY as_was_date DESC
LIMIT 10;
```

### Stale Data

**Diagnosis:**
1. Check when the model was last refreshed:
```sql
SELECT table_name, last_altered
FROM information_schema.tables
WHERE table_schema = 'FINANCE'
  AND table_name = 'BT_SKU_ANALYTICS';
```
2. Check the scheduler/orchestrator (Airflow, dbt Cloud) for failed or skipped runs
3. Check source freshness for upstream delays

**Resolution:**
- If scheduler issue: trigger manual run
- If source delay: coordinate with data engineering team
- If incremental model fell behind: consider `--full-refresh` for catch-up

### Data Discrepancies Between Models

Use the existing audit analyses to compare:

```bash
# Check available audit queries
ls analyses/audit/

# Run an audit comparison
dbt run-operation generate_base_model --args '{"source_name": "...", "table_name": "..."}'
```

For detailed data quality debugging (duplicates, join inflation, wrong aggregations), use the `dbt-model-debugger` skill.

---

## Performance Issues

### Slow Model Build

**Step-by-step investigation:**

1. **Identify the slow model:**
```bash
# Check dbt run timing in logs
rg "completed.*OK.*in" logs/dbt.log | sort -t'n' -k2 -rn | head 20
```

2. **Profile the query** in Snowflake query history:
   - Sort by `TOTAL_ELAPSED_TIME`
   - Check `BYTES_SCANNED`, `ROWS_PRODUCED`, `COMPILATION_TIME`

3. **Common fixes:**

| Finding | Action |
|---------|--------|
| Scanning too much data | Add tighter `WHERE` clause, improve incremental filter |
| Spillage | Scale up warehouse for this specific model |
| Too many joins | Break into intermediate models |
| Complex Jinja | Simplify macros, reduce dynamic SQL generation |
| Full table scan on large source | Add `cluster by` or filter on natural partition |

4. **Model-specific warehouse:**
```sql
{{ config(
    materialized='incremental',
    snowflake_warehouse='LARGE_WH'
) }}
```

### High Snowflake Credit Usage

**Investigation:**
```sql
-- Top credit consumers by warehouse (last 7 days)
SELECT warehouse_name, SUM(credits_used) AS credits
FROM snowflake.account_usage.warehouse_metering_history
WHERE start_time >= DATEADD(DAY, -7, CURRENT_TIMESTAMP())
GROUP BY warehouse_name
ORDER BY credits DESC;

-- Top credit consumers by query (last 7 days)
SELECT
    query_id,
    user_name,
    warehouse_name,
    total_elapsed_time / 1000 AS seconds,
    credits_used_cloud_services
FROM snowflake.account_usage.query_history
WHERE start_time >= DATEADD(DAY, -7, CURRENT_TIMESTAMP())
ORDER BY total_elapsed_time DESC
LIMIT 20;
```

**Reduction actions:**
1. Set auto-suspend to 60s on all non-production warehouses
2. Right-size warehouses based on actual utilization
3. Convert `full-refresh` models to `incremental` where possible
4. Drop unused development schemas and tables
5. Set up resource monitors with notification triggers

---

## Schema / Source Changes

### Upstream Column Added

**Symptoms:** New column appears in source, not yet in staging model.

**Resolution:**
1. If using `SELECT *` in staging: column appears automatically (but isn't documented)
2. If using explicit column list: add column to staging model
3. For incremental models: use `on_schema_change='append_new_columns'` config
4. Update YAML documentation with new column description

### Upstream Column Removed or Renamed

**Symptoms:** Model fails with `invalid identifier` or `column not found`.

**Resolution:**
1. Check with source team if change is intentional
2. If removed: remove from staging model, check downstream impact
3. If renamed: update staging model, keep downstream column name stable
4. Run downstream impact analysis:
```bash
# Find all models that use the affected column
rg "column_name" models/ --type sql
```

### Source Table Migrated

**Symptoms:** Source table moved to different database/schema.

**Resolution:**
1. Update `sources.yml` with new database/schema
2. No model SQL changes needed (if using `source()` correctly)
3. Verify with `dbt compile` that refs resolve correctly
4. Run `dbt test` to validate

---

## Incremental Model Issues

### Late-Arriving Data

**Symptoms:** Rows that should have been captured by incremental logic arrive after the cutoff.

**Resolution:**
- Add a lookback window to the incremental filter:
```sql
{% if is_incremental() %}
WHERE ref_date > DATEADD(DAY, -3, (SELECT MAX(ref_date) FROM {{ this }}))
{% endif %}
```
- For SCD2 models using `as_was_date`: ensure the variable accounts for processing delay

### Duplicate Rows in Incremental Model

**Symptoms:** `unique` test fails on incremental model.

**Diagnosis:**
1. Check `unique_key` matches actual grain
2. Check `incremental_strategy` — `merge` deduplicates on key, `append` does not
3. Check if source has duplicates within the incremental window

**Resolution:**
- Add dedup CTE before final select
- Fix `unique_key` to include all grain columns
- Switch from `append` to `merge` strategy if appropriate

### SCD2 Merge Conflicts

**Symptoms:** SCD2 model produces incorrect history after incremental run.

**Diagnosis:**
1. Check if `as_was_date` was set correctly for the run
2. Check if source `REF_DATE` has gaps
3. Check the `scd2_incremental_code` macro logic for edge cases

**Resolution:**
- Run `--full-refresh` to rebuild from scratch if history is corrupted
- Set `as_was_date` explicitly for backfill runs:
```bash
dbt run --select stg_em_account_scd2 --full-refresh --vars '{"as_was_date": "2025-01-01"}'
```

---

## Escalation Path

| Level | Handles | Escalates To |
|-------|---------|-------------|
| **L1** | Known issues with documented fixes, model reruns, access requests | L2 |
| **L2** | Root cause analysis, SQL fixes, performance tuning, schema changes | Engineering / Architecture |
| **Engineering** | DAG restructuring, macro changes, infrastructure changes | — |

### When to Escalate

- L1 → L2: Issue not in runbook, requires SQL investigation, or fix is unclear
- L2 → Engineering: Fix requires DAG changes, macro modifications, or Snowflake infrastructure changes
- Any level → P1: Pipeline fully blocked with downstream dashboard impact
