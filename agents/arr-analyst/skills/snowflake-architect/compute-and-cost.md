# Compute, Cost, and Optima

Reference companion to `snowflake-architect/SKILL.md` §2.

## 1. Gen2 Standard Warehouses — what changed

Gen2 (GA late 2025, default in new accounts as of 2026) is a meaningful step up from Gen1.

| Metric | Gen1 | Gen2 | Improvement |
|---|---|---|---|
| MERGE / UPDATE / DELETE throughput | 1× | ~2.1× | DML-heavy workloads benefit most |
| Table scan rate | 1× | ~1.4× | Selects with full scans |
| Spin-up latency | 200ms-1s | 100ms-500ms | Snappier for ad-hoc |
| Credit cost | 1× | 1× | No premium |
| Optima support | No | Yes | Enables zero-cost pruning |
| Adaptive Compute support | No | Yes (Preview) | Future-proofing |

### Migration steps

```sql
-- Step 1: identify all Gen1 warehouses
SELECT warehouse_name, compute_generation
FROM snowflake.account_usage.warehouses
WHERE compute_generation IS NULL OR compute_generation = 'GEN1';

-- Step 2: switch to Gen2 (no downtime; takes effect on next query)
ALTER WAREHOUSE my_warehouse SET COMPUTE_GENERATION = 'GEN2';

-- Step 3: validate
SELECT
    DATE_TRUNC('hour', start_time) AS hr,
    AVG(execution_time / 1000) AS avg_query_seconds,
    SUM(credits_used) AS credits
FROM snowflake.account_usage.query_history
WHERE warehouse_name = 'MY_WAREHOUSE'
  AND start_time > DATEADD('day', -7, CURRENT_TIMESTAMP())
GROUP BY 1 ORDER BY 1;
```

Compare avg_query_seconds + credits before/after the cutover. Look for:
- Average query time down 20-40% for DML-heavy workloads
- Credit usage steady or slightly down

### Migration risks

| Risk | Mitigation |
|---|---|
| Query plan regression for very small queries (<100ms) | Acceptable; small queries are noise in the cost profile |
| Optima auto-pruning produces unexpected results on tables with extreme skew | Validate on a heavy table; revert if regression > 10% |
| Adaptive Compute (Preview) scales differently than expected | Don't enable Adaptive in the same migration window |

## 2. Snowflake Optima — zero-cost pruning

Optima continuously builds metadata that prunes micro-partitions WITHOUT requiring a clustering key.

### How it differs from clustering

| | Manual clustering | Optima |
|---|---|---|
| What is stored | min/max per column per micro-partition (Snowflake default) + cluster key index | Same defaults + adaptive metadata (column-specific) |
| Maintenance | Snowflake's Automatic Clustering background job — paid in credits | Built into Gen2 — no extra credits |
| When effective | Whenever query filters on cluster cols | Snowflake decides based on observed query patterns |
| Cardinality matters | Yes (low-card cols cluster better) | Less so (adaptive) |
| Best for | Stable, predictable filter patterns | Mixed / unpredictable filter patterns |

### When Optima helps

- Tables ≥ 100GB
- Multiple filter patterns (not just one or two cluster keys)
- High write rate (where manual clustering would be expensive to maintain)

### When clustering still wins

- ≥ 1TB table with ONE dominant filter column
- Query pattern is rigid (e.g., always `WHERE as_was_date = ?`)
- Cluster col is low-cardinality (date, region, segment)

### Diagnostic query

```sql
-- After 7+ days on Gen2 + Optima, check pruning effectiveness
SELECT
    table_name,
    SUM(partitions_scanned) AS scanned,
    SUM(partitions_total) AS total,
    1 - SUM(partitions_scanned) / NULLIF(SUM(partitions_total), 0) AS pruning_pct
FROM snowflake.account_usage.access_history a,
     LATERAL FLATTEN(input => a.base_objects_accessed) o
WHERE o.value:objectName = 'MY_DB.MY_SCHEMA.MY_TABLE'
  AND a.query_start_time > DATEADD('day', -7, CURRENT_TIMESTAMP())
GROUP BY 1
HAVING pruning_pct < 0.5;        -- alert if pruning < 50%
```

If Optima isn't producing > 50% pruning, add a manual clustering key on the dominant filter column.

## 3. Adaptive Compute (Preview, 2026)

Adaptive Compute lets Snowflake auto-select warehouse size, cluster count, and auto-suspend / resume based on observed workload.

### Enabling

```sql
CREATE WAREHOUSE adaptive_wh
    WAREHOUSE_TYPE = 'STANDARD'
    COMPUTE_GENERATION = 'GEN2'
    ADAPTIVE_COMPUTE = TRUE
    SCALING_POLICY = 'STANDARD';
```

### What Adaptive controls

- Warehouse size (XS to 4XL)
- Cluster count (1 to MAX_CLUSTER_COUNT)
- Auto-suspend (1-300 seconds)
- Resume on query arrival

You set bounds (`MIN_WAREHOUSE_SIZE`, `MAX_WAREHOUSE_SIZE`, `MAX_CLUSTER_COUNT`); Snowflake fills in the rest.

### When to use

| Workload | Adaptive | Manual |
|---|---|---|
| Spiky BI (50% peak / 50% idle) | Excellent | Always over-provisioned |
| Steady batch | Less benefit | Predictable; manual fine |
| Mixed ad-hoc + batch on same warehouse | Excellent | Compromise on size |
| Low query frequency, latency-tolerant | Good | Could be over-provisioned |
| High SLA (sub-second response) | Risky (warm-up time variability) | Predictable |

### Guardrails

- **Pilot in dev** for 2 weeks before promoting to prod.
- **Set tight `MAX_WAREHOUSE_SIZE`** — Adaptive can scale higher than you expect.
- **Set credit quota** via Resource Monitor — Adaptive doesn't enforce cost limits on its own.
- **Don't combine with manual `ALTER WAREHOUSE SET WAREHOUSE_SIZE`** — Adaptive owns the size.

## 4. Query Acceleration Service (QAS)

QAS offloads parts of expensive queries to serverless compute. Particularly effective for:
- Outlier expensive queries on otherwise-small warehouse
- Queries with heavy scan-then-filter patterns

### Enabling

```sql
ALTER WAREHOUSE my_wh SET
    QUERY_ACCELERATION_MAX_SCALE_FACTOR = 8;   -- 1-100, multiplier on warehouse size
```

### Cost model

QAS charges separately. Track via:

```sql
SELECT query_id, credits_used_cloud_services, credits_used_query_acceleration
FROM snowflake.account_usage.query_acceleration_history
WHERE start_time > DATEADD('day', -7, CURRENT_TIMESTAMP())
ORDER BY credits_used_query_acceleration DESC
LIMIT 50;
```

If a single query is using QAS heavily every day, refactor the query (or sized the warehouse properly) instead of paying for QAS recurring.

## 5. Cost attribution — query tags + chargeback

### Query tagging

```sql
-- Per session
ALTER SESSION SET QUERY_TAG = 'dbt:model:finance_line_analytics';

-- In dbt model
{{ config(
    pre_hook="ALTER SESSION SET QUERY_TAG = 'dbt:model:{{ this.name }}'"
) }}
```

### Chargeback query

```sql
SELECT
    REGEXP_SUBSTR(query_tag, 'dbt:model:([^,]+)', 1, 1, 'e', 1) AS model_name,
    SUM(credits_used_cloud_services) AS cloud_credits,
    SUM(credits_used_warehouse) AS warehouse_credits,
    COUNT(*) AS query_count
FROM snowflake.account_usage.query_history
WHERE start_time > DATEADD('day', -30, CURRENT_TIMESTAMP())
  AND query_tag LIKE 'dbt:model:%'
GROUP BY 1
ORDER BY warehouse_credits DESC;
```

### Project-level attribution

Tag every dbt project's queries:

```yaml
# dbt_project.yml
on-run-start:
  - "ALTER SESSION SET QUERY_TAG = 'project:eda_dbt_em,run_id:{{ invocation_id }}'"
```

Now you can answer "which dbt project costs us the most?" with a SQL query.

### Attribution to data products

Add data-product tags:

```sql
{{ config(
    pre_hook="ALTER SESSION SET QUERY_TAG = 'product:arr_metrics,model:{{ this.name }}'"
) }}
```

Roll up by `product:` tag to see cost per data product.

## 6. Resource monitors — credit quotas

```sql
CREATE OR REPLACE RESOURCE MONITOR finance_monitor
    WITH CREDIT_QUOTA = 1000
    FREQUENCY = MONTHLY
    START_TIMESTAMP = IMMEDIATELY
    TRIGGERS
        ON 75 PERCENT DO NOTIFY
        ON 90 PERCENT DO SUSPEND
        ON 100 PERCENT DO SUSPEND_IMMEDIATE;

ALTER WAREHOUSE compute_wh SET RESOURCE_MONITOR = finance_monitor;
```

### Best practices

- **One monitor per major workload** (dbt prod batch, BI, ad-hoc).
- **Set NOTIFY at 75%** to give engineering time to react before hard suspension.
- **SUSPEND (not SUSPEND_IMMEDIATE) at 90%** — let in-flight queries finish.
- **SUSPEND_IMMEDIATE at 100%** only if you're confident — interrupts in-flight queries.
- **Account-level monitor as a safety net** — catches anything not tagged to a specific warehouse.

## 7. Storage cost management

| Storage class | Pricing | Retention |
|---|---|---|
| Active storage | $23-$40/TB-month (region-dependent) | Always |
| Time travel | Included in active for up to 1 day | 1-90 days for permanent tables |
| Fail-safe | Included in active | 7 days (permanent only; not transient) |
| Transient table | Active storage only | 0-1 day time travel; no fail-safe |
| Temporary table | Active storage only, session-scoped | Auto-deleted on session end |

### Data retention tuning

```sql
-- Reduce retention for non-critical tables
ALTER TABLE my_table SET DATA_RETENTION_TIME_IN_DAYS = 1;

-- Transient (no fail-safe) for staging models
CREATE OR REPLACE TRANSIENT TABLE stg_em_my_table AS ...;
```

### Storage diagnostics

```sql
-- Top storage consumers
SELECT table_catalog, table_schema, table_name,
    ROUND(active_bytes/POWER(1024,3), 2) AS active_gb,
    ROUND(time_travel_bytes/POWER(1024,3), 2) AS tt_gb,
    ROUND(failsafe_bytes/POWER(1024,3), 2) AS fs_gb
FROM snowflake.account_usage.table_storage_metrics
WHERE active_bytes > POWER(1024, 4)    -- >1TB
ORDER BY active_bytes DESC
LIMIT 50;

-- Storage growth rate
SELECT usage_date, ROUND(SUM(average_database_bytes)/POWER(1024,4), 2) AS tb
FROM snowflake.account_usage.database_storage_usage_history
WHERE usage_date >= DATEADD('day', -90, CURRENT_DATE())
GROUP BY 1 ORDER BY 1;
```

## 8. Cost optimization checklist (quarterly review)

- [ ] All warehouses on Gen2 (no Gen1 left)
- [ ] Optima enabled (auto on Gen2)
- [ ] Auto-suspend ≤ 60s for dev / ≤ 300s for prod
- [ ] No idle warehouse > 5 min in last 30 days
- [ ] Top 10 most expensive queries identified + reviewed
- [ ] Top 10 largest tables: retention reviewed
- [ ] All transient candidates (staging) are TRANSIENT not PERMANENT
- [ ] Materialized Views: each one earns its keep (`MV maintenance credits < MV save vs base query × query count`)
- [ ] Query tagging coverage > 90%
- [ ] Resource monitors set on ALL warehouses
- [ ] Cost per data product trended (no >25% MoM growth without explanation)

## 9. Cost troubleshooting flowchart

```
"Snowflake bill spiked"
├── Compare warehouse credits vs storage cost
│   ├── Compute dominates
│   │   ├── New workload? → check `query_tag` for new tag
│   │   ├── Existing workload more expensive?
│   │   │   ├── Query plan regression → query profile diff
│   │   │   ├── Warehouse oversized → resize down
│   │   │   ├── Adaptive compute scaled up → cap MAX_WAREHOUSE_SIZE
│   │   │   └── Auto-suspend disabled → re-enable
│   │   └── Idle warehouse (running but no queries) → AUTO_SUSPEND tuning
│   ├── Storage dominates
│   │   ├── Time travel too long → reduce retention
│   │   ├── Fail-safe on transient candidates → switch to TRANSIENT
│   │   ├── Dropped tables in fail-safe → wait 7 days or UNDROP if mistake
│   │   └── Storage spikes on one table → check for full-refresh churn
│   └── Both grew
│       ├── New product launch → expected
│       └── Unexpected → flag to engineering
```

## 10. Performance + cost — the joint optimization

Reducing one often improves the other. The principal-level moves:

| Move | Performance | Cost |
|---|---|---|
| Migrate to Gen2 | ↑↑ (DML 2×) | → (no premium) |
| Enable Optima | ↑↑ (pruning) | → (no premium) |
| Add clustering on heavy-filter col | ↑↑ | ↑ (clustering credits) → net neutral if read >> write |
| Reduce data retention 7d → 1d on hot tables | → | ↓↓ |
| Convert PERMANENT staging to TRANSIENT | → | ↓ (no fail-safe) |
| Migrate cross-team sharing to Iceberg | → | ↓ (no duplication) |
| Right-size warehouses (down) | ↓ (slightly slower) | ↓↓ |
| Adopt Dynamic Tables for high-freq aggregates | ↑ (always-fresh) | → / ↑ depending on lag |
