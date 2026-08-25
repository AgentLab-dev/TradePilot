# Microbatch Incremental, dbt State, Defer, and Slim-CI Mechanics

Reference companion to `dbt-architect/SKILL.md` §2 and §5.

## 1. The five incremental strategies (quantitative tradeoffs)

| Strategy | When to use | unique_key | Backfill behavior | Concurrent safety |
|---|---|---|---|---|
| `append` | Append-only event log; no late arrivals | n/a | Re-runs are no-ops | Safe (rows just append) |
| `merge` (Snowflake default) | Updates allowed; small batch | natural PK | Re-runs upsert | Safe — Snowflake MERGE is atomic |
| `delete+insert` | Period reload (snapshot fact) | partition col (e.g. `as_was_date`) | Deletes the partition first, then inserts | Safe within a partition; unsafe across overlapping partitions |
| `insert_overwrite` (BQ/Spark) | Period reload on partitioned destination | partition col | Replaces partition wholesale | Safe |
| `microbatch` (1.9+ GA) | High-volume event facts | n/a (uses `event_time`) | Auto-batches by date; parallelizable | Safe; each batch is its own transaction |

### Strategy decision tree

```
Is the model a snapshot/point-in-time fact (e.g. as_was_date partition)?
├── Yes → delete+insert with unique_key = as_was_date partition column
└── No
    └── Is the source append-only (true event stream, no updates)?
        ├── Yes
        │   └── Row volume > 10M/day?
        │       ├── Yes → microbatch with event_time
        │       └── No  → append (simplest, lowest overhead)
        └── No (updates allowed)
            └── Late arrivals beyond 7 days possible?
                ├── Yes → merge with unique_key on natural PK + lookback window
                └── No  → microbatch with lookback=N days
```

## 2. Microbatch deep dive

Microbatch was introduced in dbt 1.9 (GA in 1.12 for Snowflake adapter). It replaces hand-rolled `is_incremental() + where date > max(date)` patterns with declarative batching.

### Minimal microbatch model

```sql
{{ config(
    materialized='incremental',
    incremental_strategy='microbatch',
    event_time='event_ts',
    batch_size='day',
    lookback=3,
    begin='2024-01-01'
) }}

select
    event_id,
    event_ts,
    account_id,
    revenue
from {{ ref('stg_em_events') }}
```

### Config parameters

| Param | Meaning | Typical value |
|---|---|---|
| `event_time` | Column dbt filters on to slice batches | `event_ts`, `created_at`, `as_was_date` |
| `batch_size` | Batch granularity | `day`, `hour`, `month`, `year` |
| `lookback` | How many batches back to re-process each run (catches late arrivals) | 3-7 days for SCD2 sources; 1 for true append-only |
| `begin` | Earliest batch dbt will ever process (model birth date) | First date in source data |
| `concurrent_batches` | Number of batches dbt runs in parallel | Default 1; set to 4-8 for fast backfill |

### What microbatch does at runtime

For an incremental run on `2026-06-25`:

1. dbt computes the **batch frontier** = `max(event_time) - lookback`. Say lookback=3, so frontier = `2026-06-22`.
2. dbt computes the batches to process = each day from `2026-06-22` to `2026-06-25` = 4 batches.
3. For each batch, dbt runs the model SQL with `event_time BETWEEN batch_start AND batch_end` injected automatically.
4. Each batch is its own atomic write (`delete + insert` of that batch's rows). Failures of one batch don't poison others.

### Backfill semantics

```bash
# Backfill a specific window (re-runs all batches in this range)
dbt run --select my_event_fact \
        --event-time-start 2026-01-01 \
        --event-time-end 2026-04-01

# Backfill a single batch
dbt run --select my_event_fact \
        --event-time-start 2026-03-15 \
        --event-time-end 2026-03-16

# Full refresh (drops the table, re-runs from `begin` to now)
dbt run --select my_event_fact --full-refresh
```

### Microbatch failure modes (the gotchas)

| Symptom | Root cause | Fix |
|---|---|---|
| Batches re-run forever even with no new data | `event_time` column has NULLs | Filter NULLs in source CTE before the model SQL |
| Concurrent batches deadlock | `concurrent_batches > 1` with `MERGE` on overlapping rows | Switch to `delete+insert` per batch (the microbatch default) or set `concurrent_batches: 1` |
| Late-arriving row never appears | Outside the lookback window | Increase `lookback` or run a manual backfill for that date |
| `lookback` too high → re-processes too much daily | `lookback > 7` is usually wrong | Tune based on actual late-arrival distribution; instrument with a `MAX(event_ts) - MIN(event_ts)` query |
| Full refresh runs out of memory | Single transaction trying to load entire history | Run with `--event-time-start / --end` to batch the backfill |

## 3. dbt State — the unchanged-node optimizer (Preview, 2026)

dbt State (different from `state:modified+`) is a Preview feature that uses cached node-fingerprints to **skip or zero-copy clone** unchanged nodes, instead of re-running them.

### Enabling

```yaml
# dbt_project.yml
flags:
  manage_state: true
```

Or per-run: `dbt build --manage-state` or `DBT_ENGINE_MANAGE_STATE=true dbt build`.

### What it does

For each node in the run:

1. Compute fingerprint = `hash(compiled_sql + macro_dependencies + var_values + node_config)`.
2. Look up fingerprint in `state cache` (stored in `target/state/` or a configured remote).
3. If fingerprint matches AND upstream data hasn't changed, **skip the node** entirely (or zero-copy clone the previous table).

### Cost savings (typical)

On a 400-model DAG with ~5% of models changed per PR, State reuse skips 380 model builds — typically a 10-20× compute reduction on slim CI.

### Caveats

- Preview feature — validate locally before enabling on production CI.
- Cache invalidation conditions are conservative — any change to a macro causes ALL nodes using that macro to invalidate.
- State cache must be shared across CI runners (use a remote backend or upload as artifact).
- Don't enable on the prod batch run — you want prod to always be a fresh build for audit purposes.

## 4. Defer — the "use prod state for unchanged upstream" pattern

`--defer --state <path>` tells dbt: "when you encounter a ref() to a model I'm not building in this invocation, use the prod manifest's relation instead of failing."

### The slim-CI canonical pattern

```bash
# Step 1: download prod manifest (one of these)
aws s3 cp s3://dbt-manifests/prod/manifest.json ./prod-manifest/manifest.json
# OR
gh release download prod-latest -p manifest.json -D ./prod-manifest/
# OR  
curl -L https://dbt-cloud-internal/api/v2/.../manifest.json -o ./prod-manifest/manifest.json

# Step 2: build only the modified models + their downstream, deferring to prod
dbt build \
    --select state:modified+ \
    --defer \
    --state ./prod-manifest \
    --target qa \
    --threads 24
```

### How defer resolves `ref()`

For each `ref('upstream_model')` in the build set:

1. Is `upstream_model` in the current build set? → use the dev-target relation.
2. Else: use the prod-manifest's relation (read-only, no rebuild).

This lets you build only what changed in a PR (5-20% of the DAG) while still having all upstream data available.

### Defer failure modes

| Symptom | Root cause | Fix |
|---|---|---|
| `Relation not found` when defer is on | Prod manifest is stale; new model was created but not yet in prod | Schedule the prod manifest publish to run on every successful prod build |
| `Permission denied` on prod relation | The dev target's role doesn't have `USAGE` on the prod schema | Grant `USAGE` on the prod database/schema to the dev service role (read-only is fine) |
| Wrong column count when deferring | Prod manifest has v1 schema, dev is testing v2 | Defer respects the prod schema by design; use `dbt build --no-defer` for v2 testing |

## 5. State:modified+ — the slim-CI selector

`state:modified+` selects:
- Models whose SQL has changed since the prod manifest
- Models whose YAML has materially changed (with the `state_modified_compare_more_unrendered_values` flag)
- `+` suffix: plus all downstream models

### What counts as "modified"

dbt compares the **compiled** SQL fingerprint and the **rendered** config between the current state and the prod manifest. Triggers:

- Direct SQL changes
- Macro changes (anywhere in the macro graph) that affect compiled SQL of this model
- Source YAML changes (data_type, freshness, columns) — affects the SCD2 / staging models that ref this source
- Config block changes (materialization, unique_key, partition_by)
- Contract changes (new column, type change)
- Test changes (NEW: 1.12+ flag `state_modified_compare_more_unrendered_values: true` includes YAML test changes)

### What does NOT count as "modified"

- Pure formatting whitespace
- Comments inside SQL
- YAML description text changes (descriptions don't affect compiled SQL)
- Tags / meta updates (unless `state_modified_compare_more_unrendered_values: true`)

### Diagnosing false positives

```bash
# Show every modified node + WHY it's modified
dbt list --select state:modified+ --state ./prod-manifest \
         --output json | jq '.[] | {name, original_file_path}'

# Compare compiled SQL between current + prod manifest
dbt compile --select my_model
diff target/compiled/<proj>/<path>/my_model.sql ./prod-manifest-compiled/<path>/my_model.sql
```

If a model shows as modified but the diff is empty, you have:
1. A macro change higher up that affects compiled SQL → check `dbt list --select +my_model --resource-type macro`.
2. A flag config drift → check `dbt_project.yml` flag differences between current branch and prod manifest.

## 6. Combining State + Defer + Slim-CI — the design pattern

The principal-level CI design for a 400-model project:

```yaml
# .github/workflows/ci.yml (excerpt)
- name: Download prod manifest
  run: aws s3 cp s3://dbt-manifests/prod/manifest.json ./prod-manifest/

- name: Slim build
  run: |
    dbt build \
      --select state:modified+ \
      --defer --state ./prod-manifest \
      --manage-state \
      --target qa \
      --threads 24
```

This combination delivers:

| Optimization | Mechanism | Typical saving |
|---|---|---|
| Skip unchanged models | `state:modified+` | 80-95% of nodes excluded from build |
| Skip ref'd upstream rebuilds | `--defer` | Avoids rebuilding hundreds of upstream models |
| Skip recompute of "modified but logically identical" models | `--manage-state` | Additional 30-50% savings on first PR run, more on iteration |
| Parallel execution within build set | `--threads 24` | 3-5× wall-clock speedup |

Net effect: a 40-minute monolith CI build becomes 3-5 minutes for typical PRs.

## 7. Failure modes — slim CI

| Symptom | Diagnosis | Fix |
|---|---|---|
| CI builds the whole DAG every PR | `state:modified+` is selecting everything | Check that `--state` points to a CURRENT prod manifest; check for global YAML formatting changes |
| CI passes locally but fails in CI | Different defer state | Pin the manifest version in CI; use `dbt deps` lock file |
| `Compilation Error: Could not find ref ...` | Defer is off OR prod manifest doesn't include the ref'd model | Confirm `--defer --state` is set; check that the ref'd model exists in prod (not just in dev) |
| Threads exhausted, scheduler idle | dbt thread count > warehouse concurrency | Lower `--threads` to match warehouse limit |
| State cache misses every run | State cache not persisted between CI runs | Upload `target/state/` as artifact; restore on next run |

## 8. Microbatch + Mesh interaction

If a microbatch model is a **mesh boundary** (consumed by another project):

- The consumer must defer to the producer's manifest.
- The consumer's `ref()` resolves to the producer's prod table (which contains all batches).
- The consumer should NOT try to filter on `event_time` — the producer already did.
- If the consumer is itself microbatch on a different `event_time`, ensure the batch alignment is compatible (don't filter on producer's `event_time` in a consumer with a different `event_time`).

## 9. Operational runbook

### Daily prod batch

```bash
dbt build --threads 32 --exclude '*_scd2'  # SCD2 in a separate hourly job
```

### Hourly SCD2 job

```bash
dbt build --threads 16 --select '*_scd2'
```

### Backfill window for one fact

```bash
dbt run --select my_event_fact \
        --event-time-start 2026-01-01 \
        --event-time-end 2026-04-01 \
        --threads 8
```

### Full refresh (rare; schema change or data corruption)

```bash
dbt run --select my_event_fact --full-refresh --threads 4
# Lower threads because a single full-refresh can saturate the warehouse
```

### Emergency: skip CI for a hotfix

```bash
# Build only the hotfix model + downstream, bypassing slim-CI selector
dbt build --select +my_hotfix_model+ --threads 16
```

## 10. Metrics to instrument

Track these as recurring dashboards (or alerts):

| Metric | Healthy range | Alert if |
|---|---|---|
| Slim CI wall-clock time | 3-8 min | > 15 min |
| Slim CI model count | 5-30 models | > 100 (likely selector bug) |
| Microbatch row count per batch | within 3× rolling-7-day median | > 5× (likely batch backlog) |
| Microbatch lookback re-process rate | < 10% of batch rows | > 25% (lookback too high or too many late arrivals) |
| Defer ref-resolution failures | 0 | > 0 (manifest drift) |
| State cache hit rate | > 60% on iteration runs | < 30% (cache invalidating too aggressively) |
