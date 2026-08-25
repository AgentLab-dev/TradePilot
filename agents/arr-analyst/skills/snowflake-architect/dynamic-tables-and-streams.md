# Dynamic Tables, Streams, Tasks, CDC Patterns

Reference companion to `snowflake-architect/SKILL.md` §1.

## 1. Dynamic Tables — declarative pipelines

A Dynamic Table (DT) is a Snowflake-managed table where you declare:
- The SQL that defines its contents
- The maximum staleness you tolerate (TARGET_LAG)

Snowflake handles refresh scheduling, incremental computation, and dependency ordering.

### Minimal Dynamic Table

```sql
CREATE OR REPLACE DYNAMIC TABLE arr_realtime_aggregate
    TARGET_LAG = '5 minutes'
    WAREHOUSE = compute_wh
    REFRESH_MODE = AUTO
AS
SELECT product_l1, SUM(arr_usd_current) AS arr
FROM finance_line_analytics
GROUP BY 1;
```

### TARGET_LAG semantics

- `TARGET_LAG = '5 minutes'` → DT is refreshed often enough so it's never more than 5 minutes stale.
- `TARGET_LAG = '1 hour'` → cheaper; refreshed less often.
- `TARGET_LAG = DOWNSTREAM` → refreshed only when a downstream DT needs it.

### Refresh modes

| Mode | Behavior | Cost |
|---|---|---|
| `AUTO` | Snowflake picks incremental or full refresh per run, whichever cheaper | Best general default |
| `INCREMENTAL` | Always incremental | Lower cost on appendy data |
| `FULL` | Always full refresh | Highest cost; use when source is small |

### Custom incremental (Preview, 2026)

```sql
CREATE OR REPLACE DYNAMIC TABLE my_dt
    TARGET_LAG = '10 minutes'
    WAREHOUSE = compute_wh
    REFRESH_MODE = CUSTOM_INCREMENTAL
    SCHEDULER = AUTO   -- or DISABLE for manual
AS (
    SELECT ...
)
ON_INCREMENTAL_REFRESH (
    MERGE INTO my_dt USING new_rows ON ...
    WHEN MATCHED THEN UPDATE ...
    WHEN NOT MATCHED THEN INSERT ...
);
```

Use `CUSTOM_INCREMENTAL` when:
- Default incremental doesn't capture all updates (e.g., late-arriving rows beyond the change tracking window)
- You need specific merge semantics (e.g., SCD2 valid_to handling)
- You want to add a custom audit log on each refresh

### Decoupling pipeline stages with `DYNAMIC_TABLE_REFRESH_BOUNDARY`

```sql
CREATE OR REPLACE DYNAMIC TABLE bronze_dt ...;

CREATE OR REPLACE DYNAMIC TABLE silver_dt
AS
SELECT ... FROM TABLE(DYNAMIC_TABLE_REFRESH_BOUNDARY(bronze_dt));

CREATE OR REPLACE DYNAMIC TABLE gold_dt
AS
SELECT ... FROM TABLE(DYNAMIC_TABLE_REFRESH_BOUNDARY(silver_dt));
```

`DYNAMIC_TABLE_REFRESH_BOUNDARY` reads bronze_dt's committed state (not pending). This prevents cascading rebuild storms when bronze churns rapidly.

### When to use DT vs dbt incremental

| | Dynamic Table | dbt Incremental |
|---|---|---|
| Target freshness control | Yes (TARGET_LAG) | No (whenever you run dbt) |
| Snowflake-managed orchestration | Yes | No (you orchestrate) |
| Observability via dbt CI | No | Yes |
| Test in CI before deploy | Limited | Yes |
| Cross-project / cross-tool | Yes (any consumer) | Yes (via dbt-mesh) |
| Custom backfill logic | Harder (need ON_INCREMENTAL_REFRESH) | Easy (--event-time-start) |
| Best for | Real-time aggregates, customer-facing freshness SLAs | Batch ETL, dev-test-deploy cycle |

**Rule of thumb:** if your team owns the orchestration and CI/CD, prefer dbt. If you need "always fresh, regardless of who triggers", prefer DT.

### Failure modes — Dynamic Tables

| Symptom | Diagnosis | Fix |
|---|---|---|
| Target lag breached | Source data spiking; refresh slower than incoming rate | Increase warehouse size or `MIN_CLUSTER_COUNT` |
| Full refreshes happening too often | `AUTO` mode picking full over incremental | Force `INCREMENTAL`; check if base table has many DELETEs |
| Stale data despite TARGET_LAG | DT refresh suspended | Check `SHOW DYNAMIC TABLES` for `scheduling_state` |
| Cost spike | DT cascading rebuilds | Use `DYNAMIC_TABLE_REFRESH_BOUNDARY` to decouple |
| Unable to query during refresh | Brief lock | Acceptable; <1s usually |

## 2. Streams — CDC on Snowflake tables

A stream tracks INSERTs, UPDATEs, DELETEs to a source table. Returns rows representing the changes since you last consumed.

### Creating a stream

```sql
CREATE OR REPLACE STREAM my_stream
    ON TABLE source_table
    APPEND_ONLY = FALSE;          -- TRUE = INSERTs only; FALSE = full CDC

-- Read pending changes (does NOT consume)
SELECT * FROM my_stream;

-- Consume the changes (sets the offset to "now")
INSERT INTO target_table SELECT col_a, col_b FROM my_stream;
```

### Stream types

| Type | What it captures | When to use |
|---|---|---|
| Standard | INSERTs, UPDATEs, DELETEs | Most CDC use cases |
| Append-only | INSERTs only | Pure event streams; cheaper |
| Insert-only | INSERTs only (on external tables) | Cloud storage event-driven |

### Stream metadata columns

Every stream row has:

| Column | Meaning |
|---|---|
| `METADATA$ACTION` | `INSERT` or `DELETE` (UPDATEs appear as DELETE+INSERT pair) |
| `METADATA$ISUPDATE` | TRUE if this is part of an UPDATE |
| `METADATA$ROW_ID` | Unique row identifier |

### CDC pattern: source → stream → target

```sql
-- One-time setup
CREATE TABLE source_orders (id INT, status VARCHAR, updated_at TIMESTAMP);
CREATE STREAM orders_stream ON TABLE source_orders;
CREATE TABLE order_history (id INT, status VARCHAR, valid_from TIMESTAMP, valid_to TIMESTAMP);

-- Per-task SQL: insert deltas into history with SCD2 semantics
INSERT INTO order_history (id, status, valid_from, valid_to)
SELECT id, status, updated_at, NULL
FROM orders_stream
WHERE METADATA$ACTION = 'INSERT';

-- Expire previous valid_to records
UPDATE order_history h
SET valid_to = s.updated_at
FROM orders_stream s
WHERE h.id = s.id
  AND h.valid_to IS NULL
  AND s.METADATA$ACTION = 'DELETE';
```

## 3. Tasks — scheduled SQL execution

```sql
CREATE OR REPLACE TASK my_task
    WAREHOUSE = compute_wh
    SCHEDULE = '5 MINUTE'
    WHEN SYSTEM$STREAM_HAS_DATA('my_stream')
AS
    INSERT INTO target_table
    SELECT col_a, col_b FROM my_stream;

-- Activate
ALTER TASK my_task RESUME;

-- Diagnose
SELECT * FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
    TASK_NAME => 'my_task',
    SCHEDULED_TIME_RANGE_START => DATEADD('hour', -24, CURRENT_TIMESTAMP())
));
```

### Schedule formats

```sql
SCHEDULE = '5 MINUTE'                   -- every 5 minutes
SCHEDULE = 'USING CRON 0 3 * * * UTC'   -- 3am UTC daily
SCHEDULE = '1 MINUTE'                   -- minimum interval
```

### Task DAGs (multi-task pipelines)

```sql
-- Root task
CREATE TASK root_task
    WAREHOUSE = compute_wh
    SCHEDULE = '5 MINUTE'
AS
    CALL extract_data();

-- Child depends on root
CREATE TASK transform_task
    WAREHOUSE = compute_wh
    AFTER root_task
AS
    CALL transform_data();

-- Grandchild
CREATE TASK load_task
    WAREHOUSE = compute_wh
    AFTER transform_task
AS
    CALL load_data();

ALTER TASK load_task RESUME;
ALTER TASK transform_task RESUME;
ALTER TASK root_task RESUME;    -- always resume root LAST
```

### Task vs Dynamic Table — when to pick which

| | Task | Dynamic Table |
|---|---|---|
| Trigger | Cron schedule OR stream-has-data | Target freshness lag |
| Operation | Arbitrary SQL (INSERT, MERGE, CALL proc) | SELECT defining the table |
| Use for | Custom ETL, calling stored procs, complex orchestration | Materialized aggregations with freshness SLA |
| Failure visibility | TASK_HISTORY | DYNAMIC_TABLE_REFRESH_HISTORY |
| Backfill | Manual SQL | `ALTER DYNAMIC TABLE ... REFRESH` |

## 4. Choosing the CDC pattern

```
Data change in source needs to propagate downstream
├── Pure aggregation, freshness < 10 min?
│   └── DYNAMIC TABLE with TARGET_LAG
├── Need to capture INSERTs only into a fact table?
│   └── APPEND-ONLY STREAM + TASK (cheaper than DT)
├── Need SCD2 history of source changes?
│   └── STANDARD STREAM + TASK (custom logic for valid_to)
├── Need event-driven (not time-driven) trigger?
│   └── STREAM (with WHEN SYSTEM$STREAM_HAS_DATA on the task)
├── Long pipeline with multiple stages?
│   └── TASK DAG (or chained DYNAMIC TABLES with REFRESH_BOUNDARY)
└── Cross-project dependency?
    └── DT + cross-project ref (consumer reads via select)
```

## 5. Streams + Snowflake Cortex — modern event-driven AI

```sql
-- Stream on incoming support tickets
CREATE STREAM ticket_stream ON TABLE support_tickets;

-- Task that classifies + summarizes on arrival
CREATE TASK ai_triage_task
    WAREHOUSE = compute_wh
    SCHEDULE = '5 MINUTE'
    WHEN SYSTEM$STREAM_HAS_DATA('ticket_stream')
AS
    INSERT INTO support_tickets_enriched (
        ticket_id, ai_category, ai_summary, ai_sentiment, processed_at
    )
    SELECT
        ticket_id,
        AI_CLASSIFY(ticket_text, ['Billing', 'Technical', 'Account'])::VARIANT:label::VARCHAR AS ai_category,
        AI_SUMMARIZE_AGG(ticket_text, 'one sentence summary') AS ai_summary,
        AI_SENTIMENT(ticket_text) AS ai_sentiment,
        CURRENT_TIMESTAMP()
    FROM ticket_stream
    WHERE METADATA$ACTION = 'INSERT';

ALTER TASK ai_triage_task RESUME;
```

This pattern: stream → task → Cortex AI function. No external orchestration. AI inference inside Snowflake.

## 6. Observability — DT and Task histories

### Dynamic Table refresh history

```sql
SELECT name, target_lag_sec, mean_lag_sec, maximum_lag_sec,
       last_completed_refresh_at, scheduling_state
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_GRAPH_HISTORY())
WHERE database_name = 'FINANCE_PROD'
ORDER BY mean_lag_sec DESC;
```

### Task history

```sql
SELECT name, scheduled_time, completed_time, state, error_message
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
    SCHEDULED_TIME_RANGE_START => DATEADD('day', -1, CURRENT_TIMESTAMP())
))
WHERE state != 'SUCCEEDED'
ORDER BY scheduled_time DESC;
```

### Stream offset / pending data

```sql
SELECT SYSTEM$STREAM_HAS_DATA('my_stream') AS has_data,
       SYSTEM$STREAM_GET_TABLE_TIMESTAMP('my_stream') AS oldest_offset;
```

### Alerting

Set up Snowflake Alerts:

```sql
CREATE ALERT lag_breach_alert
    WAREHOUSE = compute_wh
    SCHEDULE = '5 MINUTE'
    IF (EXISTS (
        SELECT 1 FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_GRAPH_HISTORY())
        WHERE name = 'MY_DT' AND maximum_lag_sec > 600
    ))
    THEN CALL SYSTEM$SEND_EMAIL('email_integration', '[REDACTED_EMAIL]',
                                'DT lag breach', 'MY_DT lag > 10 min');
```

## 7. Anti-patterns to refuse in code review

| Anti-pattern | Why it's bad | Refusal script |
|---|---|---|
| Dynamic Table over a dbt-managed table | Dual ownership; refresh order conflicts | "Pick one. Either DT or dbt, not both." |
| Stream over a Dynamic Table | Stream sees DT's full refresh as massive delete+insert | "Use append-only stream on the base table instead" |
| Task running every 1 minute on a 1TB table without filter | Saturates warehouse | "Add WHEN SYSTEM$STREAM_HAS_DATA condition; filter to recent partitions" |
| Multiple tasks on the same warehouse, no scheduling discipline | Concurrency contention | "Use task DAG or stagger schedules" |
| DT with TARGET_LAG = '1 minute' on a heavy aggregate | Cost prohibitive | "Set 5-10 min unless freshness SLA truly demands sub-minute" |
| Stream with `APPEND_ONLY=FALSE` on append-only source | Wastes change-tracking overhead | "Use APPEND_ONLY=TRUE; cheaper" |
| Task DAG with > 10 levels | Hard to debug, fragile | "Refactor into nested stored procs or DT chain with REFRESH_BOUNDARY" |
