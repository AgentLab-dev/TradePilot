# Snowflake Architecture & Optimization

## Warehouse Sizing Guide

| Workload | Recommended Size | Auto-Suspend | Scaling |
|----------|-----------------|--------------|---------|
| dbt dev runs | XS | 60s | Single cluster |
| dbt CI (qa) | S–M | 60s | Single cluster |
| dbt prod batch | M–L (tune per model) | 120s | Single cluster |
| BI queries (Tableau, Looker) | S–M | 60-300s | Multi-cluster (1-3) |
| Ad-hoc analyst queries | XS–S | 60s | Single cluster |
| Large backfills / full-refresh | L–XL | 120s | Single cluster |

**Sizing rules of thumb:**
- Doubling warehouse size doubles compute and cost, but can halve query time
- Only scale up when query time is unacceptable AND the query is already optimized
- Multi-cluster scaling helps concurrency, not single-query speed
- Monitor `QUEUED` time — if queries queue often, consider multi-cluster or larger warehouse

**Gen2 warehouses (GA 2026):** Default new warehouses to **Standard Generation 2 (Gen2)** —
~2.1× faster for updates/deletes/merges/table scans, which directly benefits MERGE-based incrementals
and SCD2 builds. Gen2 is also a prerequisite for **Snowflake Optima** (automatic micro-partition
pruning, see Clustering Strategy below). For spiky ad-hoc/BI workloads, pilot **Adaptive Compute**
(Preview) to auto-select size, cluster count, and auto-suspend.

```sql
CREATE WAREHOUSE prod_wh
  WITH WAREHOUSE_TYPE = 'STANDARD'
  RESOURCE_CONSTRAINT = 'STANDARD_GEN_2'
  WAREHOUSE_SIZE = 'MEDIUM'
  AUTO_SUSPEND = 120;
```

---

## Query Optimization

### Snowflake Query Profile Checklist

When investigating slow queries, check the query profile for:

1. **Bytes scanned** — Is partition pruning effective? Compare to total table size
2. **Spillage to local/remote disk** — Indicates warehouse is too small for the data volume
3. **Exploding joins** — Row count balloons between join steps
4. **Network I/O** — Large result sets or remote spillage
5. **Compilation time** — Complex SQL with many CTEs can have high compile time

### Optimization Techniques

| Problem | Solution |
|---------|----------|
| Full table scan | Add `WHERE` filter on clustering key columns |
| Spillage to disk | Scale up warehouse OR reduce data scanned |
| Slow joins | Ensure join keys are the same data type; avoid functions on join keys |
| Repeated subqueries | Materialize as table/CTE; leverage result caching |
| Large MERGE operations | Filter source to only changed/new rows (`is_incremental()`) |
| Slow window functions | Ensure `PARTITION BY` is selective; avoid `ORDER BY` on high-cardinality columns |
| High compilation time | Break into smaller models; reduce CTE depth |

### Join Best Practices in Snowflake

```sql
-- Preferred: explicit join with matching types
select ...
from orders o
inner join customers c on o.customer_id = c.customer_id

-- Avoid: implicit type casting
select ...
from orders o
inner join customers c on o.customer_id = c.customer_id::varchar

-- Avoid: functions on join keys (prevents pruning)
select ...
from orders o
inner join customers c on upper(o.customer_name) = upper(c.customer_name)
```

---

## Clustering Strategy

### Try Optima before clustering (2026)

On **Gen2** warehouses, **Snowflake Optima** continuously analyzes workload patterns and builds
metadata to prune unused micro-partitions automatically — no clustering key to define or maintain,
and it survives `CREATE OR REPLACE`. Prefer it as the first lever, especially for churny tables that
are fully rebuilt by dbt. Add a manual clustering key only if Optima pruning is still insufficient
(verify with `SYSTEM$CLUSTERING_INFORMATION`).

### When to Cluster

Cluster only when ALL of these are true:
- Table is **>1 TB** (or >500M rows with wide columns)
- Queries consistently filter on the **same 1-3 columns**
- Query performance is **unacceptable** after Gen2 + Optima and other optimizations
- The table is not frequently fully overwritten (clustering is lost on `CREATE OR REPLACE`)

### Clustering Key Selection

| Query Pattern | Clustering Key |
|---------------|---------------|
| Filter by date range | `(date_column)` |
| Filter by date + category | `(date_column, category_column)` |
| Filter by high-cardinality ID | Generally not a good clustering candidate |
| Point lookups by ID | Use search optimization service instead |

### Monitoring Clustering

```sql
SELECT SYSTEM$CLUSTERING_INFORMATION('schema.table_name', '(cluster_col1, cluster_col2)');
```

Check `average_depth` — values close to 1.0 are well-clustered.

---

## Cost Management

### Credit Consumption Monitoring

```sql
-- Warehouse credit usage last 30 days
SELECT
    warehouse_name,
    SUM(credits_used) AS total_credits,
    SUM(credits_used) * 3.00 AS estimated_cost_usd
FROM snowflake.account_usage.warehouse_metering_history
WHERE start_time >= DATEADD(DAY, -30, CURRENT_TIMESTAMP())
GROUP BY warehouse_name
ORDER BY total_credits DESC;

-- Most expensive queries last 7 days
SELECT
    query_id,
    user_name,
    warehouse_name,
    execution_time / 1000 AS execution_seconds,
    bytes_scanned / POWER(1024, 3) AS gb_scanned,
    partitions_scanned,
    partitions_total
FROM snowflake.account_usage.query_history
WHERE start_time >= DATEADD(DAY, -7, CURRENT_TIMESTAMP())
ORDER BY execution_time DESC
LIMIT 20;
```

### Cost Reduction Strategies

| Strategy | Impact | Effort |
|----------|--------|--------|
| Auto-suspend (1 min for dev) | High | Low |
| Right-size warehouses | High | Medium |
| Incremental models (avoid full refresh) | High | Medium |
| Resource monitors with alerts | Medium | Low |
| Drop unused tables/schemas | Medium | Low |
| Use transient tables for staging | Low-Medium | Low |
| Result caching (don't disable) | Medium | None |
| Time-travel reduction (1 day for staging) | Low | Low |

### Resource Monitors

```sql
CREATE RESOURCE MONITOR prod_monitor
    WITH CREDIT_QUOTA = 1000
    FREQUENCY = MONTHLY
    START_TIMESTAMP = IMMEDIATELY
    TRIGGERS
        ON 75 PERCENT DO NOTIFY
        ON 90 PERCENT DO NOTIFY
        ON 100 PERCENT DO SUSPEND;

ALTER WAREHOUSE prod_wh SET RESOURCE_MONITOR = prod_monitor;
```

---

## Access Control

### Role-Based Access Pattern

```
ACCOUNTADMIN
└── SYSADMIN
    ├── ANALYTICS_ADMIN
    │   ├── ANALYTICS_WRITER (dbt service account)
    │   │   - USAGE on warehouse
    │   │   - CREATE TABLE/VIEW on certified schemas
    │   │   - SELECT on base_prod
    │   └── ANALYTICS_READER
    │       - USAGE on warehouse
    │       - SELECT on certified schemas
    └── DATA_ENGINEER
        - DDL on base_prod schemas
```

### Granting Access

```sql
-- Grant read access to a new schema
GRANT USAGE ON DATABASE certified TO ROLE analytics_reader;
GRANT USAGE ON SCHEMA certified.finance TO ROLE analytics_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA certified.finance TO ROLE analytics_reader;
GRANT SELECT ON FUTURE TABLES IN SCHEMA certified.finance TO ROLE analytics_reader;

-- Grant dbt service account write access
GRANT USAGE ON DATABASE certified TO ROLE analytics_writer;
GRANT ALL ON SCHEMA certified.stage TO ROLE analytics_writer;
GRANT ALL ON SCHEMA certified.finance TO ROLE analytics_writer;
```

### Troubleshooting Access Issues

```sql
-- Check what roles a user has
SHOW GRANTS TO USER 'username';

-- Check what privileges a role has on a table
SHOW GRANTS ON TABLE certified.finance.bt_sku_analytics;

-- Check if a role can access a warehouse
SHOW GRANTS ON WAREHOUSE analytics_wh;
```

---

## Snowflake-Specific dbt Configurations

### Transient Tables

Use for staging/intermediate models where time-travel is unnecessary:

```sql
{{ config(
    materialized='table',
    transient=true
) }}
```

### Query Tags

Tag dbt queries for cost attribution:

```yaml
# dbt_project.yml
models:
  eda_dbt_em:
    +query_tag: 'dbt_eda_em'
```

### Copy Grants

Preserve grants on table recreation:

```sql
{{ config(
    materialized='table',
    copy_grants=true
) }}
```

### Secure Views

For views exposed to external consumers:

```sql
{{ config(
    materialized='view',
    secure=true
) }}
```

---

## Newer Snowflake Building Blocks (2026)

### Dynamic Tables

Declarative, auto-refreshing tables — Snowflake manages scheduling, retries, and transactional
guarantees. 2026 additions make them viable for more pipeline shapes:

| Capability | Use |
|---|---|
| `CUSTOM_INCREMENTAL` refresh (Preview) | Supply your own `MERGE`/`INSERT` for patterns standard refresh can't express — stream-static joins, soft-deletes, stateful aggregation |
| `DYNAMIC_TABLE_REFRESH_BOUNDARY()` | Decouple upstream/downstream refreshes so each stage refreshes independently — avoids costly cascaded recompute in multi-stage pipelines |
| `SCHEDULER = DISABLE` | Manual-only refresh; manual refreshes don't cascade |
| `MIN_BY` / `MAX_BY` incremental | Now supported under incremental refresh (relevant to our `min_by(...)` source-company / acquisition logic) |

> **Ownership rule:** a relation is either dbt-managed **or** a Dynamic Table — never both. For
> `eda-dbt-em`, keep the core ARR/ACV math on dbt-managed tables (testable, version-controlled) and
> only evaluate Dynamic Tables for self-maintaining feed/staging layers where dbt orchestration adds
> little value.

### Apache Iceberg tables (Snowflake-managed storage, GA 2026)

Snowflake stores and manages the Iceberg files for you (no external cloud-storage setup), open format,
accessible via the Horizon Catalog; permanent tables get Fail-safe. Consider for **large,
externally-shared** finance datasets to reduce lock-in. Keep the latency-sensitive ARR engine on
native Snowflake tables for now.

### Search optimization for semi-structured columns

Point-lookup and substring queries on `ARRAY` / `OBJECT` / `MAP` columns can now be accelerated by the
search optimization service — relevant to product-mix array columns (e.g. `bb_product_mix`,
`eb_product_mix`) used in SKU / standalone classification.

### Cortex AI in SQL

`AI_FILTER`, `AI_AGG`, `AI_SUMMARIZE_AGG` bring set-based LLM inference into SQL. Out of scope for
deterministic ARR/ACV computation; potential for narrative commentary or data-quality triage. Size
warehouses no larger than MEDIUM for AI workloads and filter rows before calling AI functions.
