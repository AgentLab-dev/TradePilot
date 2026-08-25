---
name: snowflake-architect
description: >-
  Principal Snowflake Architect for enterprise data platforms (multi-TB warehouses,
  cross-cloud accounts, mesh consumers). Covers Gen2 Warehouses + Optima + Adaptive
  Compute, Dynamic Tables + Streams + Tasks, Apache Iceberg + Polaris catalog,
  Snowpark (Python UDFs, stored procs, container services), Cortex AI in SQL,
  Hybrid Tables (Unistore), Horizon governance + replication + DR, advanced RBAC,
  micro-partition pruning math, query profiling, MV vs DT vs incremental tradeoffs,
  and cost attribution at platform scale. Use when designing Snowflake account
  topology, picking a refresh pattern (table vs Dynamic Table vs incremental),
  adopting Iceberg / Cortex / Snowpark, troubleshooting query performance, sizing
  warehouses, designing replication / failover, or making any architecture-level
  Snowflake decision.
---

# Snowflake Architect — Principal Level (2026)

Role: Principal Snowflake Platform Architect for enterprise data warehouses.
You design account topology, pick the right compute primitive for each workload
from a quantitative basis, integrate open-table formats (Iceberg), embed AI in
SQL via Cortex, run governance + replication / DR at scale, and instrument
cost attribution down to the data product.

This SKILL.md is the index + decision frameworks. Deep companion files:

- [`compute-and-cost.md`](compute-and-cost.md) — Gen2, Optima, Adaptive Compute, Query Acceleration Service, cost attribution
- [`dynamic-tables-and-streams.md`](dynamic-tables-and-streams.md) — Dynamic Tables, Streams, Tasks, CDC pipelines
- [`iceberg-and-storage.md`](iceberg-and-storage.md) — Iceberg native + external, Polaris catalog, hybrid tables, storage tiers
- [`snowpark-and-ai.md`](snowpark-and-ai.md) — Snowpark Python, Stored Procs, Container Services, Cortex AI (LLM in SQL)
- [`security-and-governance.md`](security-and-governance.md) — Horizon, masking, row access, tag-based policies, replication, DR
- [`performance-deep-dive.md`](performance-deep-dive.md) — Micro-partition pruning math, MV vs DT vs incremental, query profile reading

---

## When to use this skill (decision tree)

```
Snowflake question raised
├── New workload — pick compute primitive             → §1 + dynamic-tables-and-streams.md
├── Warehouse sizing / cost                            → §2 + compute-and-cost.md
├── Performance tuning / slow query                    → §3 + performance-deep-dive.md
├── New table — pick storage format (native vs Iceberg)→ §4 + iceberg-and-storage.md
├── AI / LLM functionality in SQL                       → snowpark-and-ai.md
├── Custom Python / Java / Scala compute                → snowpark-and-ai.md
├── Security / governance / data classification         → security-and-governance.md
├── Replication / DR / HA                               → security-and-governance.md
├── Cost attribution / chargeback / FinOps              → compute-and-cost.md
└── Cross-cloud / cross-region                          → security-and-governance.md
```

For platform-administration topics (user provisioning, resource monitors at scale,
account-level monitoring), see the companion `snowflake-platform-admin` skill.

---

## §1. Compute primitives — pick the right one

Snowflake offers 6+ compute primitives. Picking wrong = 10× cost or wrong correctness.

| Primitive | Best for | Refresh model | Cost basis |
|---|---|---|---|
| **Table** (with dbt) | Stable transforms, batch ETL | Manual (dbt run) | Per-warehouse credits during run |
| **Incremental table** (dbt) | Append-only or late-arriving facts | Manual (dbt incremental) | Per-warehouse credits during run |
| **Dynamic Table** (DT) | Declarative pipelines with target freshness | Auto (Snowflake-managed) | Per-warehouse credits during refresh |
| **Materialized View** (MV) | Single-table aggregation on a churny base | Auto (Snowflake-managed background) | Compute + storage + maintenance overhead |
| **External Table** (Iceberg/Parquet) | Open-format datasets read by many engines | Underlying file changes drive freshness | Storage + read compute only |
| **Hybrid Table** (Unistore) | Sub-second point lookups + analytical aggregation on same data | Inherent (row-store + columnar) | Higher storage + compute, but eliminates dual systems |
| **Stream** + **Task** | Event-driven incremental on a table | Stream tracks deltas; task fires SQL | Per task execution |
| **Snowpark function** | Custom Python/Scala/Java logic embedded in SQL | n/a — invoked at query time | Per query credits |
| **Snowpark Container Service** | Long-running custom services (REST APIs, ML inference) | Always-on or scheduled | Per-second compute (separate from warehouses) |

### Decision matrix (refresh-pattern × scale × ownership)

| Workload | Best primitive | Why |
|---|---|---|
| dbt-managed ARR daily refresh | Incremental table | dbt orchestration is in your control |
| Real-time event aggregation, freshness ≤ 5 min | Dynamic Table (TARGET_LAG='5 minutes') | Hands-off, Snowflake manages |
| Customer-facing dashboard, sub-second response, 1B rows | Hybrid Table | Row-store backing eliminates the need for a separate OLTP cache |
| External team shares data weekly via Iceberg | Iceberg external table | No data copy; Snowflake reads files in-place |
| LLM summarization of support tickets | Cortex `AI_SUMMARIZE_AGG` in SQL | No external API; data stays in Snowflake |
| Custom Python ML model scoring | Snowpark Python UDF | Code runs inside Snowflake; secure |
| Long-running ML training service | Snowpark Container Service | Always-on compute; not query-bound |
| MV on a high-write table with rare reads | **Don't** — MV maintenance > read savings | Materialized View only when reads >> writes |

### Ownership rule

**Never let two primitives own the same table.** If a table is dbt-managed, it's not a Dynamic Table. If it's a Dynamic Table, dbt should `source()` it, not `ref()` it. If it's an Iceberg table, dbt may write to it but only one of `dbt` or `Snowpark` should hold the write lock.

---

## §2. Warehouse strategy — Gen2 + Optima + Adaptive

The 2026 Snowflake compute landscape is fundamentally different from 2023.

### Generation comparison

| Feature | Gen1 (legacy) | Gen2 (default 2026) |
|---|---|---|
| MERGE / UPDATE / DELETE speed | Baseline | ~2.1× faster |
| Optima support | No | Yes |
| Adaptive Compute support | No | Yes (preview) |
| Auto-scale spin-up | 200ms-1s | 100ms-500ms |
| Cost per credit | Same | Same (no premium) |
| Migration | Manual `ALTER WAREHOUSE ... SET COMPUTE_GENERATION = 'GEN2'` | One-line change |

**Action:** every new warehouse defaults to Gen2. Migrate existing prod warehouses to Gen2 in a maintenance window. Validate query times before/after.

### Snowflake Optima (Gen2-only, GA 2026)

Continuously builds metadata to **auto-prune micro-partitions** without requiring a clustering key.

| | Manual clustering | Optima |
|---|---|---|
| Setup cost | Define `CLUSTER BY (col1, col2)` + monitor | Zero |
| Maintenance cost | Automatic clustering — pays per credit, can be substantial | Built into Gen2 — no extra credit cost |
| When effective | Tables ≥ 1TB with predictable filter cols | Always-on for any Gen2 warehouse query |
| Limits | Max 4 cluster cols; cardinality matters | Snowflake decides which metadata to build |

**Rule:** before adding a clustering key, try Optima. If after a week of Optima, your `SYSTEM$CLUSTERING_INFORMATION` still shows high `average_overlaps`, add a clustering key on the most-filtered column.

### Adaptive Compute (Preview, 2026)

Automatically selects warehouse size, cluster count, auto-suspend, and resume policy based on workload.

| Workload | Adaptive Compute | Manual sizing |
|---|---|---|
| Spiky BI queries (50% idle / 50% peak) | Excellent | Always over-provisioned |
| Steady dbt batch | Less benefit | Predictable; manual fine |
| Mixed ad-hoc + batch on same warehouse | Excellent | Compromise — sized for the larger workload |

**Pilot in dev** before committing to Adaptive in prod. Watch for sudden cost spikes (Adaptive might scale UP a warehouse you didn't expect).

### Sizing decision matrix

| Workload | Size | Multi-cluster | Auto-suspend | Notes |
|---|---|---|---|---|
| Interactive dev / ad-hoc | XS-S | 1 cluster | 60s | Cheap; spin up fast |
| Slim CI (state:modified+) | S-M | 1 cluster | 60s | Short-lived; defer to prod state |
| dbt slim prod batch | M-L | 1 cluster | 300s | Auto-suspend long enough to absorb the next batch |
| dbt full prod batch (rare) | L-XL | 1 cluster | 300s | Sized for the heaviest model |
| BI concurrent users (>10) | M | 2-4 clusters | 60s | Scale OUT for concurrency, not UP |
| Real-time Dynamic Tables | M | 1 cluster | DT-managed | Don't share with batch warehouses |
| ML / Snowpark heavy | L-XL | 1 cluster | 300s | Snowpark benefits from larger single-cluster |

---

## §3. Performance — quantitative basis

### Query profile reading order

1. **Operator costs**: which operator (TableScan, Join, Aggregate, Sort) consumed most time?
2. **Bytes spilled to local / remote**: if > 0, warehouse is too small — bump up by 1 size.
3. **Partitions scanned / total**: if scanned ≈ total on a >1TB table, missing pruning predicate or need clustering.
4. **Bytes sent over network**: if large, reduce join sizes or use broadcast hints.
5. **Bytes read from remote storage**: if high, no result cache hit — confirm query is deterministic.

See [`performance-deep-dive.md`](performance-deep-dive.md) for the full diagnostic workflow.

### Micro-partition pruning — the math

A micro-partition is ~16MB of compressed data. Snowflake stores metadata per partition: min/max/null counts per column.

For a query `WHERE event_date = '2026-06-01'`, Snowflake:
1. Reads partition metadata for `event_date` (cheap).
2. Skips partitions whose min/max don't intersect the predicate.
3. Reads only the partitions that survive pruning.

```
pruning_effectiveness = 1 - (partitions_scanned / partitions_total)
```

- 0% (no pruning) = full table scan
- 90%+ = excellent
- < 50% on a >1TB table = problem (add cluster key or rewrite query)

### MV vs DT vs incremental — when to pick which

| | Materialized View | Dynamic Table | dbt Incremental |
|---|---|---|---|
| Best for | Single-table aggregation re-read constantly | Multi-table pipeline with target freshness | Custom batch / late-arrival logic |
| Refresh model | Auto background | Auto by TARGET_LAG | Manual (dbt run) |
| Source tables | 1 only | Many (any SQL) | Many |
| Restrictions | No UDFs, no LATERAL, no non-deterministic | Few restrictions | None (it's just SQL) |
| Cost | Storage + maintenance | Compute + storage | Compute only when triggered |
| Ownership | Snowflake | Snowflake | dbt |
| Failure mode | Silent stale data on errors | Lag SLA breach (visible in DT info) | Pipeline alert (dbt orchestration) |

**Default rule:** unless you have a strong reason to use MV or DT, use dbt incremental — it gives you control + observability via your existing dbt CI/CD.

### Result cache vs query history

| | Result cache | Query result reuse |
|---|---|---|
| TTL | 24h | n/a |
| Reset on | Underlying data change | n/a |
| Visible in | Query profile (no compute) | `query_history` shows `cached_result_id` |
| Disable for fresh runs | `ALTER SESSION SET USE_CACHED_RESULT = FALSE` | n/a |

For sub-100ms BI dashboards, design queries to hit the result cache: same SQL text, same role, same warehouse, no time-volatile functions.

---

## §4. Storage primitives

| | Native table | Iceberg (Snowflake-managed) | Iceberg (External catalog) | Hybrid Table |
|---|---|---|---|---|
| File format | Proprietary | Apache Iceberg + Parquet | Apache Iceberg + Parquet | Row-store + columnar (proprietary) |
| Open / portable | No | Yes (any Iceberg reader) | Yes | No |
| Time travel | 90 days max | 90 days (Snowflake-managed) | Catalog-dependent | Limited |
| Fail-safe | Yes (7 days) | Yes (7 days) on permanent | None | None |
| Write performance | Best | Slightly slower | Snowflake reads; external catalog writes | Slower (row-store overhead) |
| Read performance | Best | ~95% of native | ~90% of native | Optimized for point lookups |
| Cost | Snowflake storage | Snowflake storage (cheaper) | Your own object store | Snowflake storage + premium |
| Best for | Internal warehouses | Shared with external teams using open formats | Already-Iceberg datasets in S3/GCS | Sub-100ms OLTP-style lookups |

See [`iceberg-and-storage.md`](iceberg-and-storage.md) for migration paths and Polaris catalog setup.

---

## §5. Account topology

```
ACCOUNT (org-level)
├── REGION: us-west-2 (primary)
│   ├── DATABASE: BASE_PROD     (raw / landing)
│   ├── DATABASE: FINANCE_PROD  (curated marts)
│   └── DATABASE: SALES_PROD    (curated marts)
├── REGION: us-east-2 (replica)
│   └── Same databases — read-only failover replica
└── Cross-cloud
    └── AWS / GCP / Azure secondary accounts as needed
```

### Account-level features (require ACCOUNTADMIN)

- **Resource monitors** — credit quotas at account or warehouse level
- **Network policies** — IP allowlists at account or user level
- **Federation / SSO** — OAuth, SCIM, SAML providers
- **Data sharing** — share databases with other accounts read-only
- **Replication** — sync databases / users / roles across accounts
- **Failover groups** — automated failover of databases between accounts

---

## §6. 2026 features index (adoption guardrails)

| Feature | Status | Use when | Skip when |
|---|---|---|---|
| **Gen2 Warehouses** | GA | All new warehouses; migrate existing | n/a — migrate everything |
| **Snowflake Optima** | GA (Gen2) | Replace clustering keys on most tables | Tables with very predictable filters where clustering still wins |
| **Adaptive Compute** | Preview | Spiky / mixed workloads | Predictable batch workloads (use fixed size) |
| **Dynamic Tables — custom incremental** | Preview | Replace some dbt+Snowflake managed tables with declarative DT | Anywhere dbt orchestration is critical |
| **Iceberg (Snowflake-managed)** | GA | Cross-engine open data shared with Spark / Trino / Athena | Internal warehouses (native tables better) |
| **Polaris Catalog** | GA | Open Iceberg catalog accessible by any engine | Snowflake-only environments |
| **Hybrid Tables (Unistore)** | GA | Sub-second point lookups + analytical aggregation on same data | Analytical-only workloads |
| **Cortex AI** (`AI_FILTER`, `AI_AGG`, `AI_SUMMARIZE_AGG`, `AI_CLASSIFY`) | GA | LLM functionality in SQL — narrative, classification, summarization | Deterministic numeric metrics |
| **Cortex Search** | GA | Hybrid full-text + vector search | Pure SQL aggregation |
| **Snowpark Container Services** | GA | Long-running custom services (REST, ML inference, GPUs) | Standard query workloads |
| **Search optimization for ARRAY/OBJECT/MAP** | GA | Point lookups in semi-structured data | Aggregations |
| **Horizon Catalog** | GA | Cross-account governance, classification, lineage, access | Single-team / single-account |
| **Account replication + failover groups** | GA | DR / HA across regions | Single-region tolerable |
| **Cross-cloud auto-fulfillment** | GA | Data marketplace across AWS / Azure / GCP | Single cloud |

### Adoption guardrails

1. **Financial correctness first** — never pilot a Preview feature on a production ARR/ACV/TCV metric path.
2. **One ownership per relation** — dbt OR Dynamic Table OR Hybrid Table, never two.
3. **Cost-before-clustering** — Gen2 + Optima first, manual clustering only if necessary.
4. **AI for narrative, not numbers** — Cortex `AI_*` is great for summarization, not for revenue computation.
5. **Iceberg for sharing, native for internal** — native tables remain best for in-account workloads.

---

## §7. Quick reference SQL

```sql
-- Warehouse: switch to Gen2 + scale
ALTER WAREHOUSE COMPUTE_WH SET
    COMPUTE_GENERATION = 'GEN2',
    WAREHOUSE_SIZE = 'LARGE',
    AUTO_SUSPEND = 60,
    MIN_CLUSTER_COUNT = 1,
    MAX_CLUSTER_COUNT = 4,
    SCALING_POLICY = 'STANDARD';

-- Dynamic Table — target freshness 5 min
CREATE OR REPLACE DYNAMIC TABLE arr_realtime_aggregate
    TARGET_LAG = '5 minutes'
    WAREHOUSE = COMPUTE_WH
    REFRESH_MODE = AUTO
AS
SELECT product_l1, SUM(arr_usd_current) AS arr
FROM finance_line_analytics
WHERE as_was_date = CURRENT_DATE()
GROUP BY 1;

-- Iceberg table (Snowflake-managed)
CREATE OR REPLACE ICEBERG TABLE shared_finance_data (
    as_was_date DATE,
    account_id VARCHAR,
    arr NUMBER(38,2)
)
CATALOG = 'SNOWFLAKE'
EXTERNAL_VOLUME = 'my_s3_volume'
BASE_LOCATION = 'finance_data/';

-- Cortex AI — summarize support tickets
SELECT
    account_id,
    AI_SUMMARIZE_AGG(ticket_text, 'top 3 themes in 50 words') AS summary
FROM support_tickets
WHERE created_at > DATEADD('day', -30, CURRENT_DATE())
GROUP BY 1;

-- Time travel — query as of 1 hour ago
SELECT * FROM my_table AT(OFFSET => -3600);

-- UNDROP
UNDROP TABLE my_table;

-- Stream + Task
CREATE OR REPLACE STREAM my_stream ON TABLE source_table;
CREATE OR REPLACE TASK my_task
    WAREHOUSE = compute_wh
    SCHEDULE = '1 MINUTE'
    WHEN SYSTEM$STREAM_HAS_DATA('my_stream')
AS
    INSERT INTO target_table SELECT * FROM my_stream;
ALTER TASK my_task RESUME;

-- Cost — credits by warehouse last 30 days
SELECT warehouse_name, SUM(credits_used) AS credits
FROM snowflake.account_usage.warehouse_metering_history
WHERE start_time >= DATEADD('day', -30, CURRENT_TIMESTAMP())
GROUP BY 1 ORDER BY 2 DESC;

-- Pruning effectiveness
SELECT
    SYSTEM$CLUSTERING_INFORMATION('my_table', '(as_was_date)') AS clust_info;
```

---

## See also

- `snowflake-platform-admin` skill — account-level admin, user provisioning, resource monitors
- `data-analytics-architect` skill — broader dbt+Snowflake architecture decisions
- `dbt-architect` skill — dbt project-level decisions
