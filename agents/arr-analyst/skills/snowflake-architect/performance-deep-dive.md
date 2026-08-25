# Performance Deep Dive — Pruning, Profiling, Materialization Tradeoffs

Reference companion to `snowflake-architect/SKILL.md` §3.

## 1. The query profile — reading it like an architect

Open `Snowsight → History → click any query → Query Profile`. Read in this order:

### Step 1: Total time vs compilation time

```
Total elapsed time:  45s
Compilation time:    2s         ← if > 5s, plan is complex; consider rewrite
Execution time:      43s        ← the real work
Queued time:         0s         ← if > 0, warehouse concurrency issue
```

### Step 2: Most expensive operator

Look at the operator tree. The widest bars are the bottleneck.

| Operator | What it does | Common issue |
|---|---|---|
| TableScan | Read from a table | High = no pruning |
| Filter | Apply WHERE | High = no pushdown |
| JoinFilter | Apply join predicate | High = wrong join order |
| HashJoin | Build + probe a hash table | High = small side too big, spilling |
| Sort | ORDER BY / window function ordering | High = unbounded sort, no clustering |
| Aggregate | GROUP BY / DISTINCT | High = high-cardinality grouping |
| WindowFunction | ROW_NUMBER, SUM OVER | High = unbounded partition |

### Step 3: Statistics panel

| Stat | Meaning | Healthy |
|---|---|---|
| Bytes scanned | Total bytes read from storage | Match expectation |
| Partitions scanned | Micro-partitions read | < 50% of total = good pruning |
| Partitions total | Total micro-partitions in source | Reference value |
| Bytes spilled to local | Memory overflow to local disk | > 0 = warehouse too small |
| Bytes spilled to remote | Memory overflow to remote storage | > 0 = warehouse WAY too small |
| Bytes sent over network | Cross-cluster data movement | High = consider broadcast hint |
| Bytes written to result | Final result size | Compare to expected row count |

### Step 4: Profile interpretation

```
Symptom                                  Most likely cause
─────────────────────────────────────────────────────────────────
TableScan dominates                      Missing pruning predicate
Bytes spilled to remote > 0               Warehouse too small
Partitions scanned ≈ total                No clustering benefit
Sort dominates                            Add clustering / change query shape
HashJoin "Build" side scanning >100GB    Use BROADCAST hint or restructure
```

## 2. Micro-partition pruning — the math

A Snowflake table is stored as compressed columnar files (~16MB each), called micro-partitions. For each partition, Snowflake stores metadata:
- Min and max value per column
- Null count per column
- Number of distinct values per column

### How pruning works

For `WHERE event_date = '2026-06-01'`:

1. Snowflake reads partition metadata (cheap, in cloud services layer).
2. For each partition, checks if `[min_event_date, max_event_date]` contains `'2026-06-01'`.
3. Skips partitions where the predicate cannot possibly match.
4. Reads only surviving partitions.

### Pruning effectiveness — quantified

```
pruning_pct = 1 - (partitions_scanned / partitions_total)
```

| Pruning % | Verdict |
|---|---|
| < 25% | Almost no pruning; check predicate / consider clustering |
| 25-50% | Mediocre; investigate |
| 50-90% | Good |
| > 90% | Excellent |

### Why predicates don't prune

| Cause | Example | Fix |
|---|---|---|
| Function on indexed column | `WHERE DATE_TRUNC('month', event_date) = '2026-06-01'` | `WHERE event_date BETWEEN '2026-06-01' AND '2026-06-30'` |
| Type mismatch | `WHERE event_date = '2026-06-01'` against TIMESTAMP col | `WHERE event_date = '2026-06-01'::TIMESTAMP` |
| OR predicate with one side unselective | `WHERE event_date = '...' OR id IS NOT NULL` | Split into UNION ALL |
| Pattern with leading wildcard | `WHERE name LIKE '%smith'` | Reverse the column on insert + search reversed; or use search optimization |
| Column not in clustering AND no Optima | New column | Add to clustering key or wait for Optima to pick up |

### Clustering keys — when they pay off

```sql
ALTER TABLE my_table CLUSTER BY (as_was_date, region);
```

| Table size | Clustering cost | Read savings | Net |
|---|---|---|---|
| < 100GB | High (auto-clustering credits) | Low (table is small) | Net negative |
| 100GB - 1TB | Moderate | Moderate | Often net neutral; favor Optima |
| 1TB - 10TB | Moderate | High | Net positive if filter pattern stable |
| > 10TB | High but worth it | Very high | Net positive; manual clustering wins |

### Monitor clustering

```sql
SELECT SYSTEM$CLUSTERING_INFORMATION('my_table', '(as_was_date, region)');

-- Output (parse the JSON):
-- {
--   "cluster_by_keys": "(as_was_date, region)",
--   "total_partition_count": 12453,
--   "average_overlaps": 2.3,       ← > 4 = clustering degraded
--   "average_depth": 1.8,          ← > 5 = clustering degraded
--   "partition_depth_histogram": {...}
-- }
```

If `average_overlaps > 4` or `average_depth > 5`, manually re-cluster:

```sql
ALTER TABLE my_table RECLUSTER;
```

### Optima vs clustering decision

```
Table > 100GB AND high filter selectivity?
├── Predictable single-column filter pattern
│   ├── Yes → clustering key on that column
│   └── No  → enable Optima (Gen2 default)
├── Mixed / unpredictable filter pattern
│   └── Optima
├── Very high write rate (clustering would churn)
│   └── Optima (no maintenance credits)
└── Mostly read, rare writes
    └── Clustering (pays off; no maintenance churn)
```

## 3. Join optimization

### Join order

Snowflake's optimizer picks order automatically based on statistics. When stats are stale or skewed:

```sql
-- Hint: build hash table on the smaller table
SELECT /*+ BUILD = b */ ...
FROM big_table b
JOIN small_table s ON ...
```

### Broadcast hint for many-to-few joins

```sql
SELECT /*+ BROADCAST(s) */ ...
FROM huge_table h
JOIN small_dim s ON h.dim_id = s.id
```

When `small_dim` is < 1M rows and `huge_table` is > 100M, BROADCAST sends `small_dim` to every node instead of shuffling `huge_table`.

### Skewed join — the silent killer

If 80% of `huge_table` rows have `account_id = 'BIG_CORP'`, the join hot-spots on one node.

Diagnosis: in query profile, look at the JOIN operator → "max bytes per partition" vs "avg bytes per partition". If max is 10× avg, you have skew.

Fix:

```sql
-- Salt the skewed key
SELECT ...
FROM huge_table h
JOIN small_table s ON h.account_id = s.account_id
WHERE h.account_id = 'BIG_CORP'

UNION ALL

SELECT ...
FROM huge_table h
JOIN small_table s ON h.account_id = s.account_id
WHERE h.account_id != 'BIG_CORP'
```

## 4. Window functions and sorts

### Unbounded window — performance killer

```sql
-- Slow: full table sort
SELECT *,
       ROW_NUMBER() OVER (ORDER BY created_at DESC) AS row_num
FROM huge_table;

-- Faster: partition
SELECT *,
       ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY created_at DESC) AS row_num
FROM huge_table;
```

### QUALIFY vs subquery

```sql
-- Old pattern: subquery + WHERE
SELECT * FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY id ORDER BY ts DESC) AS rn
    FROM events
) WHERE rn = 1;

-- New pattern: QUALIFY (cleaner, same performance)
SELECT * FROM events
QUALIFY ROW_NUMBER() OVER (PARTITION BY id ORDER BY ts DESC) = 1;
```

### Window optimization with clustering

```sql
-- If table is clustered on (account_id), window functions partitioned on account_id are faster
ALTER TABLE events CLUSTER BY (account_id);
-- Now ROW_NUMBER() OVER (PARTITION BY account_id ...) runs much faster
```

## 5. Aggregation performance

### GROUP BY ALL vs explicit

```sql
-- New (1.10+): GROUP BY ALL groups by every non-aggregate column
SELECT a, b, c, COUNT(*), SUM(d) FROM t GROUP BY ALL;

-- Equivalent to:
SELECT a, b, c, COUNT(*), SUM(d) FROM t GROUP BY 1, 2, 3;
```

Same performance; cleaner code.

### Pre-aggregation for downstream re-use

If 5+ queries hit `SELECT product_l1, COUNT(*) FROM big_table GROUP BY product_l1`, materialize:

```sql
CREATE OR REPLACE TABLE product_l1_counts AS
SELECT product_l1, COUNT(*) AS cnt FROM big_table GROUP BY 1;

-- Or as a Materialized View (auto-maintained)
CREATE MATERIALIZED VIEW mv_product_l1_counts AS
SELECT product_l1, COUNT(*) AS cnt FROM big_table GROUP BY 1;
```

### High-cardinality aggregation

`GROUP BY user_id` on a billion-row table:
- Hash table for distinct user_ids fits in memory? → fine
- Doesn't fit? → spills to disk → slow

Mitigation:
- Sort the input on `user_id` first (clustering)
- Use approximate aggregation: `APPROX_COUNT_DISTINCT(user_id)` instead of `COUNT(DISTINCT user_id)`

## 6. Result cache — exploit it

Snowflake caches query results for 24h. Cache hit = zero compute.

### Conditions for cache hit

- Identical SQL text (whitespace doesn't matter; comments do)
- Same role
- Same warehouse (within the same Snowflake account)
- Underlying data hasn't changed (any DML on a source table invalidates)
- No time-volatile functions (`CURRENT_TIMESTAMP`, `RANDOM`, `CURRENT_USER` — usually)

### Make BI dashboards cache-friendly

```sql
-- BAD: time-volatile function defeats cache every second
SELECT * FROM finance_line_analytics
WHERE created_at > DATEADD('hour', -1, CURRENT_TIMESTAMP());

-- GOOD: stable predicate, cache lasts 24h or until data changes
SELECT * FROM finance_line_analytics
WHERE as_was_date = '2026-06-25';
```

### Disable cache (for performance tests)

```sql
ALTER SESSION SET USE_CACHED_RESULT = FALSE;
```

## 7. Concurrency & warehouse scaling

### Scale UP vs scale OUT

| | Scale UP (larger size) | Scale OUT (multi-cluster) |
|---|---|---|
| Helps | Single complex query | Many concurrent queries |
| Doesn't help | Many concurrent simple queries | Single huge query |
| Cost | Per-second proportional to size | Per cluster |
| Auto-scaling | n/a (manual ALTER) | `MIN_CLUSTER_COUNT` / `MAX_CLUSTER_COUNT` |

### Scaling policy

```sql
ALTER WAREHOUSE my_wh SET
    MIN_CLUSTER_COUNT = 1,
    MAX_CLUSTER_COUNT = 4,
    SCALING_POLICY = 'STANDARD';     -- aggressive scale-up
    -- or 'ECONOMY' = lazier scale-up (slight latency cost, lower total credits)
```

### Multi-cluster warehouse decision

| Concurrent users | MIN/MAX |
|---|---|
| 1-2 | 1/1 |
| 3-10 | 1/2 |
| 10-50 | 2/4 |
| 50+ | 4/8+ |

### Diagnosing concurrency queue

```sql
SELECT query_id, warehouse_name, total_elapsed_time, queued_overload_time
FROM snowflake.account_usage.query_history
WHERE queued_overload_time > 0
ORDER BY queued_overload_time DESC
LIMIT 100;
```

If `queued_overload_time` > 1000ms for many queries, scale OUT.

## 8. MV vs DT vs incremental — quantitative tradeoff

| | Materialized View | Dynamic Table | dbt Incremental Table |
|---|---|---|---|
| Maintenance trigger | DML on base | TARGET_LAG breach | dbt run |
| Maintenance owner | Snowflake background | Snowflake | dbt + warehouse |
| Source restriction | 1 table only | Multiple tables OK | Any SQL |
| UDFs/LATERAL allowed | No | Yes | Yes |
| Cost basis | Storage + maintenance credits | Per refresh | Per dbt run |
| When fresh | Always (lazy) | Within TARGET_LAG | After dbt run |
| Test in CI | Limited | Limited | Yes (dbt build) |
| Best for | Simple agg, base churns occasionally | Multi-step pipelines with freshness SLA | Standard dbt models |

### Decision matrix

```
Need to materialize a derived dataset
├── Source is 1 base table only?
│   ├── No → not MV. Choose DT or dbt incremental.
│   └── Yes:
│       ├── Read >> Write?
│       │   ├── Yes → MV (Snowflake handles refresh)
│       │   └── No  → not MV; reads don't justify maintenance cost
│       └── Need UDFs / LATERAL?
│           ├── Yes → not MV; use DT or dbt
│           └── No  → MV viable
├── Multiple sources, target freshness < 10 min?
│   ├── Yes → Dynamic Table with TARGET_LAG
│   └── No → dbt incremental
└── Custom backfill / orchestration needed?
    └── dbt incremental
```

## 9. Diagnostic playbook — "this query is slow"

```
Step 1: Get the query_id from the user
Step 2: SELECT * FROM snowflake.account_usage.query_history WHERE query_id = '...'
Step 3: Open Query Profile in Snowsight
Step 4: Look at the top 3 most expensive operators
Step 5: For each:
    - TableScan with partitions_scanned = partitions_total
      → no pruning. Check WHERE clause for non-prunable predicates.
    - HashJoin spilling
      → warehouse too small or join order wrong
    - Sort spilling
      → unbounded ORDER BY or window function
    - WindowFunction taking 40%+
      → consider clustering on PARTITION BY column
Step 6: If still unclear, run with profiling:
    EXPLAIN USING TABULAR <query>
    EXPLAIN USING JSON <query>
Step 7: Compare with EXPLAIN PLAN for hypotheses
```

## 10. Performance budget — set targets

For finance ARR pipeline:

| Workload | Target | Alert threshold |
|---|---|---|
| `dbt build --select state:modified+ ...` (slim CI) | < 8 min | > 15 min |
| Daily prod batch (full DAG) | < 90 min | > 180 min |
| `finance_line_analytics` incremental refresh | < 15 min | > 30 min |
| `arr_*_categories` refresh | < 10 min | > 25 min |
| Sigma dashboard query | < 5 sec | > 15 sec |
| Sub-second BI lookup | < 200 ms | > 500 ms |

When you hit alert threshold, follow the diagnostic playbook.
