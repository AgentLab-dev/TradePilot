# Iceberg, Polaris Catalog, Hybrid Tables, External Tables

Reference companion to `snowflake-architect/SKILL.md` §4.

## 1. The 2026 storage landscape

Snowflake offers 4+ table types. Pick by openness, performance, and cost.

| Table type | File format | Open / portable | Best for |
|---|---|---|---|
| Native | Proprietary FDN | No | Internal warehouses; max perf |
| Iceberg (Snowflake-managed) | Apache Iceberg + Parquet | Yes (any Iceberg reader) | Cross-engine sharing |
| Iceberg (External catalog) | Apache Iceberg + Parquet | Yes | Already-Iceberg data in S3/GCS |
| External table | Parquet/CSV/JSON (read-only) | Yes (any reader of the format) | Legacy data lakes; read-only |
| Hybrid table (Unistore) | Row-store + columnar | No | OLTP + analytical on same data |

## 2. Apache Iceberg in Snowflake

Iceberg is an open table format originally from Netflix, now widely adopted. Snowflake's Iceberg integration lets you:
- Read Iceberg tables managed by any catalog (Snowflake, AWS Glue, Hive)
- Write to Iceberg tables in Snowflake-managed storage
- Share Iceberg tables cross-engine (Spark, Trino, DuckDB, Athena can all read)

### Snowflake-managed Iceberg (the "best of both" option)

```sql
-- Set up external volume (one-time per region)
CREATE OR REPLACE EXTERNAL VOLUME my_iceberg_vol
    STORAGE_LOCATIONS = (
        (
            NAME = 'us-west-2-loc',
            STORAGE_PROVIDER = 'S3',
            STORAGE_BASE_URL = 's3://my-iceberg-bucket/',
            STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::xxx:role/snowflake_iceberg',
            ENCRYPTION = (TYPE = 'AWS_SSE_KMS', KMS_KEY_ID = 'aws-kms-key')
        )
    );

-- Create Iceberg table
CREATE OR REPLACE ICEBERG TABLE my_open_data (
    as_was_date DATE,
    account_id VARCHAR,
    arr NUMBER(38,2)
)
CATALOG = 'SNOWFLAKE'                         -- Snowflake manages metadata
EXTERNAL_VOLUME = 'my_iceberg_vol'
BASE_LOCATION = 'finance_data/';

-- Read like any table
SELECT * FROM my_open_data WHERE as_was_date = CURRENT_DATE();

-- Write like any table
INSERT INTO my_open_data SELECT ...;

-- Other engines can read this table via Iceberg REST API
```

### Externally-managed Iceberg

```sql
-- Catalog integration (e.g., AWS Glue)
CREATE OR REPLACE CATALOG INTEGRATION glue_catalog_int
    CATALOG_SOURCE = GLUE
    CATALOG_NAMESPACE = 'my_namespace'
    TABLE_FORMAT = ICEBERG
    GLUE_AWS_ROLE_ARN = 'arn:aws:iam::xxx:role/glue_role'
    GLUE_CATALOG_ID = 'xxx'
    GLUE_REGION = 'us-west-2'
    ENABLED = TRUE;

CREATE OR REPLACE ICEBERG TABLE external_data
    CATALOG = 'glue_catalog_int'
    CATALOG_TABLE_NAME = 'my_table'
    EXTERNAL_VOLUME = 'my_iceberg_vol';
```

In external mode, Snowflake reads the data via the external catalog (Glue, Hive, etc.) but doesn't manage the metadata.

### Iceberg performance vs native

| Operation | Native | Iceberg (Snowflake-managed) |
|---|---|---|
| Bulk read | 1.0× | 0.92-0.98× |
| Indexed lookup | 1.0× | 0.85-0.95× |
| MERGE / UPDATE | 1.0× | 0.75-0.90× (more file rewrite overhead) |
| Storage cost | 1.0× | 0.6-0.9× (Parquet often compresses better) |
| Time travel | 90 days | 90 days |
| Fail-safe | Yes (7 days, permanent) | Yes (7 days, permanent) |

### When to use Iceberg vs native

| Need | Iceberg | Native |
|---|---|---|
| Share dataset with Spark / Trino / Athena | Yes | No (Snowflake-only) |
| Lock-in concern | Yes (open format) | No (proprietary) |
| Best raw analytical performance | No | Yes |
| Best DML performance | No | Yes |
| Lowest storage cost | Yes (Parquet compresses better) | No |
| Snowflake-only access | No | Yes |

**Rule:** internal-only warehouses stay on native. Cross-engine / cross-team sharing goes to Iceberg.

## 3. Polaris Catalog

Polaris is Snowflake's open-source Iceberg catalog (Apache 2.0 license). Lets ANY engine — not just Snowflake — manage Iceberg tables centrally.

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Snowflake  │    │    Spark    │    │   Trino     │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                   │
       ▼                  ▼                   ▼
       ┌───────────────────────────────────────┐
       │         Polaris Catalog (REST)          │
       │  (table metadata, permissions, lineage)  │
       └───────────────────┬───────────────────┘
                           │
                           ▼
                   ┌───────────────┐
                   │  S3 / GCS /   │
                   │  Azure Blob   │
                   │  (Iceberg     │
                   │   files)      │
                   └───────────────┘
```

### Setup

```sql
-- Connect Snowflake to Polaris
CREATE OR REPLACE CATALOG INTEGRATION polaris_int
    CATALOG_SOURCE = POLARIS
    CATALOG_NAMESPACE = 'finance'
    REST_CONFIG = (
        CATALOG_URI = 'https://polaris.example.com/api/catalog'
        WAREHOUSE = 'my_polaris_warehouse'
    )
    REST_AUTHENTICATION = (
        TYPE = OAUTH
        OAUTH_CLIENT_ID = 'xxx'
        OAUTH_CLIENT_SECRET = 'xxx'
        OAUTH_ALLOWED_SCOPES = ('PRINCIPAL_ROLE:ALL')
    )
    ENABLED = TRUE;
```

### Use cases

- **Cross-tenant data sharing** — multiple Snowflake accounts read the same Iceberg tables via Polaris.
- **Cross-engine analytics** — data scientists use Spark, analysts use Snowflake, both read the same canonical tables.
- **Lakehouse strategy** — keep one source of truth in S3, query from anywhere.

## 4. Hybrid Tables (Unistore) — OLTP + Analytical in one

A Hybrid Table has both row-store and columnar storage. Use case: sub-millisecond point lookups + sub-second analytical aggregation on the same table.

### Creating

```sql
CREATE OR REPLACE HYBRID TABLE user_session (
    user_id VARCHAR PRIMARY KEY,
    session_id VARCHAR,
    last_activity TIMESTAMP,
    page_views NUMBER,
    INDEX idx_session (session_id)
);

-- Sub-ms point lookup (row-store)
SELECT * FROM user_session WHERE user_id = 'U123';

-- Sub-second aggregation (columnar)
SELECT DATE_TRUNC('hour', last_activity) AS hr, COUNT(*)
FROM user_session
GROUP BY 1;
```

### When to use Hybrid Tables

| Need | Hybrid Table? | Alternative |
|---|---|---|
| Point lookup < 10ms | Yes | External cache (Redis), but data duplication |
| User-facing app reading per-user data | Yes | Separate OLTP DB |
| Analytical queries on operational data without ETL | Yes | Stream + DT (cheaper but stale) |
| Heavy DML (>1000 writes/sec) | Yes | RDBMS |
| Pure analytical workload | No | Native table |
| Read-only data | No | Native or Iceberg |

### Cost

Hybrid tables charge premium storage + compute. Not for bulk analytical data — use only when point lookup latency matters.

## 5. External tables (read-only data lakes)

For data already in S3/GCS/Azure that you don't want to copy into Snowflake.

```sql
-- One-time stage
CREATE OR REPLACE STAGE my_stage
    URL = 's3://my-bucket/data/'
    STORAGE_INTEGRATION = my_storage_int
    FILE_FORMAT = (TYPE = PARQUET);

-- External table
CREATE OR REPLACE EXTERNAL TABLE my_external_data (
    as_was_date DATE AS (CAST(SPLIT_PART(METADATA$FILENAME, '/', 3) AS DATE)),
    account_id VARCHAR AS (VALUE:account_id::VARCHAR),
    arr NUMBER AS (VALUE:arr::NUMBER)
)
PARTITION BY (as_was_date)
LOCATION = @my_stage
FILE_FORMAT = (TYPE = PARQUET);

-- Auto-refresh on new files
ALTER EXTERNAL TABLE my_external_data REFRESH;
```

### Auto-refresh patterns

```sql
-- S3 notification + SQS
CREATE NOTIFICATION INTEGRATION my_notif
    TYPE = QUEUE
    NOTIFICATION_PROVIDER = AWS_SQS
    AWS_SQS_ARN = 'arn:aws:sqs:us-west-2:xxx:my_queue';

ALTER EXTERNAL TABLE my_external_data SET
    AUTO_REFRESH = TRUE
    NOTIFICATION_INTEGRATION = 'my_notif';
```

### When to use External vs Iceberg

| | External Table | Iceberg Table |
|---|---|---|
| Read | Yes | Yes |
| Write | No | Yes |
| Time travel | No | Yes |
| Schema evolution | Limited | Strong |
| Performance | Slow (no indexes, no pruning beyond partition) | Faster |
| Best for | Legacy data lakes; ad-hoc one-time analysis | New cross-engine datasets |

**Rule:** External tables are legacy. For new datasets, use Iceberg.

## 6. Storage tiering & lifecycle

| | Active | Time Travel | Fail-Safe |
|---|---|---|---|
| Read-accessible | Yes | Yes (via AT() syntax) | No (only via Snowflake support) |
| Default duration | Indefinite | 1 day (Standard) / 90 days (Enterprise+) | 7 days (permanent only) |
| Cost | Standard storage rate | Same | Same |
| Adjustable | n/a | `DATA_RETENTION_TIME_IN_DAYS` | No (fixed 7 days) |
| Transient table | Yes | 0-1 day | No |
| Temporary table | Session only | 0 days | No |

### Lifecycle strategy

```sql
-- Hot raw data: keep 30 days time travel for backfill recovery
ALTER TABLE base_prod.salesforce.opportunity SET DATA_RETENTION_TIME_IN_DAYS = 30;

-- Staging models: transient (no fail-safe), short time travel
CREATE OR REPLACE TRANSIENT TABLE stg_em_my_model
    DATA_RETENTION_TIME_IN_DAYS = 1
AS SELECT ...;

-- Production marts: standard retention
ALTER TABLE finance_prod.managed.finance_line_analytics SET DATA_RETENTION_TIME_IN_DAYS = 7;
```

### Storage cost diagnostics

```sql
-- Top time-travel cost
SELECT table_catalog, table_schema, table_name,
       ROUND(time_travel_bytes / POWER(1024, 4), 2) AS tt_tb,
       ROUND(active_bytes / POWER(1024, 4), 2) AS active_tb
FROM snowflake.account_usage.table_storage_metrics
WHERE time_travel_bytes > POWER(1024, 4)    -- >1TB time travel
ORDER BY time_travel_bytes DESC
LIMIT 20;
```

If a table has time-travel bytes > active bytes, you're paying double for the table. Either reduce retention or reduce write churn.

## 7. Iceberg migration playbook

Migrating a Snowflake native table to Iceberg:

```sql
-- Step 1: create the Iceberg version
CREATE OR REPLACE ICEBERG TABLE my_data_iceberg
    CATALOG = 'SNOWFLAKE'
    EXTERNAL_VOLUME = 'my_iceberg_vol'
    BASE_LOCATION = 'my_data/'
AS
SELECT * FROM my_data_native;

-- Step 2: validate row count + checksum
SELECT (SELECT COUNT(*) FROM my_data_native) = (SELECT COUNT(*) FROM my_data_iceberg) AS counts_match;

SELECT
    (SELECT HASH_AGG(*) FROM my_data_native) AS native_hash,
    (SELECT HASH_AGG(*) FROM my_data_iceberg) AS iceberg_hash;

-- Step 3: swap name (atomic via SWAP)
ALTER TABLE my_data_native SWAP WITH my_data_iceberg;

-- Step 4: drop the old
DROP TABLE my_data_iceberg;    -- now holds old native data; safe to drop
```

### Risks during migration

- **DML performance regression** — Iceberg MERGEs are slower; test before swap.
- **Cross-engine consumers** — confirm any non-Snowflake consumer can read Iceberg before swap.
- **Time travel reset** — Iceberg table starts with fresh time travel; old time travel of native is lost on swap.
- **Auto-clustering** — Iceberg has different clustering semantics; review SYSTEM$CLUSTERING_INFORMATION post-swap.

## 8. Anti-patterns

| Anti-pattern | Why it's bad | Refusal script |
|---|---|---|
| Iceberg for internal warehouses | Slower DML; no cross-engine benefit | "Use native; Iceberg is for cross-engine sharing" |
| Hybrid table for bulk analytics | Expensive storage, no benefit | "Use native; hybrid is for point lookups" |
| External table on data you can copy in | Slow reads, no time travel | "Copy to native; only use external for never-changing legacy data" |
| Long time-travel on high-write tables | Storage cost > value | "Reduce to 1-7 days; fail-safe handles recovery anyway" |
| Multiple catalogs for the same data | Drift inevitable | "Pick one — Snowflake or Polaris — not both" |
| Iceberg with no `EXTERNAL_VOLUME` defined | Snowflake won't know where files go | "Define external volume first; check storage integration" |
