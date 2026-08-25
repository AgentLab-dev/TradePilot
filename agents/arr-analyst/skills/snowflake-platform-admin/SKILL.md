---
name: snowflake-platform-admin
description: >-
  Snowflake platform administration covering account management, user provisioning, role
  hierarchy design, network policies, resource monitors, data sharing, replication, failover,
  storage management, Snowpark, and operational monitoring. Use when provisioning users/roles,
  configuring network policies, setting up resource monitors, managing data shares, configuring
  replication, monitoring account usage, or performing any Snowflake account-level administration.
---

# Snowflake Platform Admin

## Account Administration

### User Provisioning
```sql
CREATE USER svc_dbt_qa
  PASSWORD = '...'
  DEFAULT_ROLE = QA_TRANSFORM
  DEFAULT_WAREHOUSE = QA_WH
  DEFAULT_NAMESPACE = CERTIFIED_QA.FINANCE
  MUST_CHANGE_PASSWORD = FALSE;

GRANT ROLE QA_TRANSFORM TO USER svc_dbt_qa;
```

### Role Hierarchy Design
```
ACCOUNTADMIN
├── SYSADMIN
│   ├── PROD_ADMIN
│   │   ├── PROD_TRANSFORM (dbt service account)
│   │   └── PROD_READ (analysts, BI tools)
│   ├── QA_ADMIN
│   │   ├── QA_TRANSFORM
│   │   └── QA_READ
│   └── DEV_ADMIN
│       ├── DEV_TRANSFORM
│       └── DEV_READ
├── SECURITYADMIN (role/grant management)
└── USERADMIN (user management)
```

### Permission Grants Pattern
```sql
-- Database-level
GRANT USAGE ON DATABASE CERTIFIED_QA TO ROLE QA_TRANSFORM;
GRANT USAGE ON ALL SCHEMAS IN DATABASE CERTIFIED_QA TO ROLE QA_TRANSFORM;
GRANT CREATE TABLE ON ALL SCHEMAS IN DATABASE CERTIFIED_QA TO ROLE QA_TRANSFORM;
GRANT SELECT ON ALL TABLES IN SCHEMA CERTIFIED_QA.FINANCE TO ROLE QA_READ;

-- Future grants (auto-apply to new objects)
GRANT SELECT ON FUTURE TABLES IN SCHEMA CERTIFIED_QA.FINANCE TO ROLE QA_READ;
GRANT SELECT ON FUTURE VIEWS IN SCHEMA CERTIFIED_QA.FINANCE TO ROLE QA_READ;
```

## Network & Security

### Network Policies
```sql
CREATE NETWORK POLICY office_vpn_only
  ALLOWED_IP_LIST = ('10.0.0.0/8', '172.16.0.0/12')
  BLOCKED_IP_LIST = ();

ALTER ACCOUNT SET NETWORK_POLICY = office_vpn_only;
```

### PrivateLink
- AWS PrivateLink for private connectivity (no public internet)
- Endpoint format: `<account>.privatelink.snowflakecomputing.com`
- Requires VPC endpoint in AWS + Snowflake account configuration
- Used by dbt Cloud runners to connect without exposing Snowflake publicly

### Data Masking Policies
```sql
CREATE MASKING POLICY mask_pii AS (val STRING)
  RETURNS STRING ->
  CASE
    WHEN CURRENT_ROLE() IN ('PROD_ADMIN', 'SECURITYADMIN') THEN val
    ELSE '***MASKED***'
  END;

ALTER TABLE customers MODIFY COLUMN email SET MASKING POLICY mask_pii;
```

### Row Access Policies
```sql
CREATE ROW ACCESS POLICY region_filter AS (region_col VARCHAR)
  RETURNS BOOLEAN ->
  CURRENT_ROLE() = 'PROD_ADMIN'
  OR region_col = CURRENT_SESSION()::VARCHAR;
```

## Resource Management

### Resource Monitors
```sql
CREATE RESOURCE MONITOR qa_monitor
  WITH CREDIT_QUOTA = 100
  FREQUENCY = MONTHLY
  START_TIMESTAMP = IMMEDIATELY
  TRIGGERS
    ON 75 PERCENT DO NOTIFY
    ON 90 PERCENT DO NOTIFY
    ON 100 PERCENT DO SUSPEND;

ALTER WAREHOUSE QA_WH SET RESOURCE_MONITOR = qa_monitor;
```

### Warehouse Configuration
```sql
CREATE WAREHOUSE TRANSFORM_WH_M
  WITH WAREHOUSE_SIZE = 'MEDIUM'
  AUTO_SUSPEND = 300
  AUTO_RESUME = TRUE
  MIN_CLUSTER_COUNT = 1
  MAX_CLUSTER_COUNT = 3
  SCALING_POLICY = 'STANDARD'
  INITIALLY_SUSPENDED = TRUE;
```

## Monitoring & Observability

### Key System Views
| View | Purpose |
|------|---------|
| `SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY` | Credit consumption |
| `SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY` | Query performance |
| `SNOWFLAKE.ACCOUNT_USAGE.LOGIN_HISTORY` | Access auditing |
| `SNOWFLAKE.ACCOUNT_USAGE.STORAGE_USAGE` | Storage costs |
| `SNOWFLAKE.ACCOUNT_USAGE.DATABASE_STORAGE_USAGE_HISTORY` | Per-DB storage |
| `SNOWFLAKE.ACCOUNT_USAGE.TABLE_STORAGE_METRICS` | Per-table storage |
| `SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY` | Column-level access tracking |

### Health Check Queries
```sql
-- Failed queries (last 24h)
SELECT query_id, user_name, error_message, execution_status
FROM snowflake.account_usage.query_history
WHERE execution_status = 'FAIL'
  AND start_time >= DATEADD('hour', -24, CURRENT_TIMESTAMP())
ORDER BY start_time DESC;

-- Long-running queries (>5 min)
SELECT query_id, user_name, warehouse_name,
  DATEDIFF('second', start_time, end_time) as duration_sec, query_text
FROM snowflake.account_usage.query_history
WHERE DATEDIFF('second', start_time, end_time) > 300
  AND start_time >= DATEADD('day', -1, CURRENT_TIMESTAMP())
ORDER BY duration_sec DESC;

-- Warehouse utilization
SELECT warehouse_name,
  SUM(credits_used) as total_credits,
  COUNT(DISTINCT DATE_TRUNC('hour', start_time)) as active_hours
FROM snowflake.account_usage.warehouse_metering_history
WHERE start_time >= DATEADD('day', -30, CURRENT_TIMESTAMP())
GROUP BY 1 ORDER BY 2 DESC;
```

## Data Sharing & Replication

### Secure Data Sharing
```sql
CREATE SHARE finance_share;
GRANT USAGE ON DATABASE CERTIFIED_PROD TO SHARE finance_share;
GRANT USAGE ON SCHEMA CERTIFIED_PROD.FINANCE TO SHARE finance_share;
GRANT SELECT ON TABLE CERTIFIED_PROD.FINANCE.BV_ARR_DASHBOARD TO SHARE finance_share;
ALTER SHARE finance_share ADD ACCOUNTS = consumer_account;
```

### Database Replication
```sql
-- Primary account
ALTER DATABASE CERTIFIED_PROD ENABLE REPLICATION TO ACCOUNTS org.secondary_account;

-- Secondary account
CREATE DATABASE CERTIFIED_PROD_REPLICA AS REPLICA OF org.primary_account.CERTIFIED_PROD;
ALTER DATABASE CERTIFIED_PROD_REPLICA REFRESH;
```

## Storage Management

### Table Lifecycle
```sql
-- Check table size and clustering
SELECT * FROM TABLE(INFORMATION_SCHEMA.TABLE_STORAGE_METRICS)
WHERE TABLE_SCHEMA = 'FINANCE'
ORDER BY ACTIVE_BYTES DESC;

-- Reclustering
ALTER TABLE large_fact_table CLUSTER BY (as_was_date, account_id);
SELECT SYSTEM$CLUSTERING_INFORMATION('large_fact_table');

-- Transient tables for staging (no fail-safe, lower cost)
CREATE TRANSIENT TABLE stg_temp AS SELECT ...;
```

### Data Retention
```sql
-- Set retention for time travel (1 day = cheaper, 90 days = max)
ALTER TABLE bt_sku_analytics SET DATA_RETENTION_TIME_IN_DAYS = 7;

-- Enterprise edition: up to 90 days
ALTER TABLE critical_table SET DATA_RETENTION_TIME_IN_DAYS = 90;
```

## Troubleshooting

| Issue | Resolution |
|-------|-----------|
| User can't access table | `SHOW GRANTS TO ROLE`, check inheritance chain |
| Warehouse won't start | Check resource monitor limits, account credit balance |
| Query fails with "object not found" | Check role context, schema search path, case sensitivity |
| Slow queries across board | Check warehouse contention, consider multi-cluster |
| Storage costs rising | Audit `TABLE_STORAGE_METRICS`, drop temp tables, reduce retention |
| Login failures | Check network policy, IP allowlist, password expiry |
