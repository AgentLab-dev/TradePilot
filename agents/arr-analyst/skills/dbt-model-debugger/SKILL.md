---
name: dbt-model-debugger
description: Debug dbt model data quality issues by tracing upstream lineage, identifying root causes like join inflation or incremental logic errors, and providing corrected SQL with regression tests. Use when investigating duplicate counts, unexpected row counts, NULL-related bugs, or any data discrepancy in a dbt project.
---

# dbt Model Debugger

Role: Expert Analytics Engineer / L2 Support Specialist for dbt projects with large model graphs (400+ models).

## Debugging Workflow

When given a data quality issue (e.g., "duplicates in `mart_monthly_metrics.active_users` for February"), follow these four phases in order. Copy the checklist and track progress:

```
Debugging Progress:
- [ ] Phase 1: Discovery — map the model and its upstream parents
- [ ] Phase 2: Impact Analysis — trace the problem column upstream
- [ ] Phase 3: Root Cause — identify the logic failure
- [ ] Phase 4: Proposed Fix — provide corrected SQL + regression test
```

---

### Phase 1: Discovery

1. Locate the target model file:
   ```bash
   rg -l "model_name" models/
   ```
2. Open the model and list every `ref()` and `source()` call.
3. Sketch the immediate lineage (one level up). If the issue isn't visible at this level, recurse into the parent that defines or transforms the problem column.

**Output a brief lineage summary**, e.g.:
```
mart_monthly_metrics
  ├── ref('int_user_sessions')
  ├── ref('int_billing_events')
  └── ref('stg_users')
```

---

### Phase 2: Impact Analysis

1. Find where the problem column is **first defined** in the upstream chain:
   ```bash
   rg "problem_column" models/ --type sql
   ```
2. Trace every transformation (aggregation, join, window function) applied to it between origin and the target model.
3. Note the grain (primary key) at each layer — grain changes across joins are the most common inflation source.

---

### Phase 3: Root Cause

Check for these failure patterns (see [anti-patterns.md](anti-patterns.md) for detailed examples):

| Pattern | Symptom | Quick Check |
|---------|---------|-------------|
| Many-to-many join | Row inflation / duplicates | Compare `COUNT(*)` vs `COUNT(DISTINCT pk)` on each side of the join |
| Incorrect incremental strategy | Duplicates in incremental models | Review `unique_key` and `incremental_strategy` config |
| Missing COALESCE / NULL handling | Fanout on NULL join keys | Check for `WHERE key IS NOT NULL` or `COALESCE(key, ...)` |
| Wrong join type | Unexpected NULLs or dropped rows | Verify LEFT vs INNER vs FULL OUTER intent |
| Missing GROUP BY | Aggregation returning too many rows | Confirm all non-aggregate columns are in GROUP BY |
| Window function without PARTITION BY | Incorrect running totals / ranks | Verify PARTITION BY matches intended grain |

---

### Phase 4: Proposed Fix

1. **Provide the corrected SQL block** following CTE-first styling:
   ```sql
   with

   source_data as (
       select ...
   ),

   deduplicated as (
       select
           *,
           row_number() over (
               partition by primary_key
               order by updated_at desc
           ) as row_num
       from source_data
   ),

   final as (
       select ...
       from deduplicated
       where row_num = 1
   )

   select * from final
   ```

2. **Suggest a dbt test** to prevent regression:
   ```yaml
   models:
     - name: target_model
       columns:
         - name: primary_key_column
           tests:
             - unique
             - not_null
         - name: problem_column
           tests:
             - not_null
   ```

3. If the fix involves a join change, suggest a `dbt_utils.equality` or `relationships` test to validate referential integrity.

---

## Constraints

- Follow the project's **CTE-first** styling convention.
- **Do not modify staging models** unless the error originates there.
- Keep all `ref()` and `source()` calls intact — never hardcode table names.
- Prefer additive fixes (add a dedup CTE, add a filter) over restructuring the DAG.

## Additional Resources

- For common anti-patterns with detailed SQL examples, see [anti-patterns.md](anti-patterns.md).
