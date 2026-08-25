# Security, Governance, Replication, DR

Reference companion to `snowflake-architect/SKILL.md` §5 and Horizon Catalog.

## 1. RBAC architecture — beyond the basics

The Snowflake permission graph:

```
ACCOUNTADMIN  (god mode; for break-glass only, not daily use)
├── SECURITYADMIN  (creates roles, grants permissions)
├── USERADMIN      (creates users)
├── ORGADMIN       (manages organization-level objects)
└── SYSADMIN
    ├── PROD_ADMIN          (database admin for prod)
    │   ├── PROD_TRANSFORM  (R/W for dbt service)
    │   └── PROD_READ       (R for BI tools)
    ├── QA_ADMIN
    │   ├── QA_TRANSFORM
    │   └── QA_READ
    └── DEV_ADMIN
        ├── DEV_TRANSFORM
        └── DEV_READ
```

### Functional vs access roles (the principal pattern)

**Access roles** (granular permissions on objects):
```sql
CREATE ROLE acc_finance_prod_r;     -- read finance_prod
CREATE ROLE acc_finance_prod_rw;    -- read+write finance_prod
CREATE ROLE acc_finance_int_prod_r;
GRANT USAGE ON DATABASE finance_prod TO ROLE acc_finance_prod_r;
GRANT USAGE ON ALL SCHEMAS IN DATABASE finance_prod TO ROLE acc_finance_prod_r;
GRANT SELECT ON ALL TABLES IN SCHEMA finance_prod.managed TO ROLE acc_finance_prod_r;
GRANT SELECT ON FUTURE TABLES IN SCHEMA finance_prod.managed TO ROLE acc_finance_prod_r;
```

**Functional roles** (job-based; grant access roles to functional roles):
```sql
CREATE ROLE role_finance_analyst;
GRANT ROLE acc_finance_prod_r TO ROLE role_finance_analyst;
GRANT ROLE acc_finance_int_prod_r TO ROLE role_finance_analyst;

CREATE ROLE role_finance_engineer;
GRANT ROLE acc_finance_prod_rw TO ROLE role_finance_engineer;
GRANT ROLE acc_finance_int_prod_rw TO ROLE role_finance_engineer;
```

**Grant functional roles to users:**
```sql
GRANT ROLE role_finance_analyst TO USER jane_smith;
```

### Why this two-layer model

| Problem | One-layer (user → permission) | Two-layer (user → functional → access) |
|---|---|---|
| New user joins | Grant 50 permissions | Grant 1 functional role |
| New table in schema | Update every user's grants | Future grants pick it up |
| User changes team | Revoke 50 + grant 50 | Revoke 1 + grant 1 |
| Audit "who can read X?" | Trace through users | List `SHOW GRANTS ON ROLE acc_x_r` |
| Org restructure | Re-grant everything | Re-grant functional roles only |

### Future grants (essential for new objects)

```sql
GRANT SELECT ON FUTURE TABLES IN SCHEMA finance_prod.managed TO ROLE acc_finance_prod_r;
GRANT USAGE ON FUTURE SCHEMAS IN DATABASE finance_prod TO ROLE acc_finance_prod_r;
GRANT SELECT ON FUTURE VIEWS IN SCHEMA finance_prod.managed TO ROLE acc_finance_prod_r;
```

Without future grants, every `dbt run` creating a new table requires a manual `GRANT` — drift is inevitable.

### Service account pattern

```sql
CREATE USER dbt_service_prod
    PASSWORD = NULL                              -- no password; key auth only
    DEFAULT_ROLE = role_dbt_prod
    DEFAULT_WAREHOUSE = dbt_prod_wh
    LOGIN_NAME = 'dbt_service_prod'
    MUST_CHANGE_PASSWORD = FALSE
    DISPLAY_NAME = 'dbt prod service';

-- Key-pair auth
ALTER USER dbt_service_prod SET RSA_PUBLIC_KEY = '<base64-encoded-pubkey>';

-- Network policy
ALTER USER dbt_service_prod SET NETWORK_POLICY = dbt_only_policy;
```

Service accounts: dedicated user, key-pair auth (never password), network policy enforced.

## 2. Data classification & masking

### Tag-based governance

```sql
-- Define tags
CREATE TAG IF NOT EXISTS data_classification ALLOWED_VALUES
    'public', 'internal', 'confidential', 'restricted';

CREATE TAG IF NOT EXISTS pii_type ALLOWED_VALUES
    'email', 'phone', 'ssn', 'name', 'address', 'none';

-- Apply tags to columns
ALTER TABLE my_table MODIFY COLUMN email
    SET TAG data_classification = 'confidential',
            pii_type = 'email';
```

### Tag-based masking policies

```sql
CREATE OR REPLACE MASKING POLICY mask_email AS (val STRING) RETURNS STRING ->
    CASE
        WHEN CURRENT_ROLE() IN ('ROLE_PRIVILEGED') THEN val
        WHEN CURRENT_ROLE() IN ('ROLE_INTERNAL') THEN
            REGEXP_REPLACE(val, '(.)(.*)(@.*)', '\\1***\\3')
        ELSE '***MASKED***'
    END;

-- Bind to tag (auto-applies to any column tagged pii_type='email')
ALTER TAG pii_type SET MASKING POLICY mask_email FOR VARCHAR;
```

Now any column tagged `pii_type='email'` automatically gets the masking policy. New tables inherit it via future grants + tags.

### Row Access Policies (RAP)

```sql
CREATE OR REPLACE ROW ACCESS POLICY region_rap AS (region VARCHAR) RETURNS BOOLEAN ->
    CASE
        WHEN CURRENT_ROLE() = 'ROLE_GLOBAL' THEN TRUE
        WHEN CURRENT_ROLE() = 'ROLE_AMER' THEN region IN ('NA', 'LATAM')
        WHEN CURRENT_ROLE() = 'ROLE_EMEA' THEN region IN ('EMEA', 'EU')
        WHEN CURRENT_ROLE() = 'ROLE_APJ' THEN region IN ('APAC', 'JPN', 'INDIA')
        ELSE FALSE
    END;

ALTER TABLE finance_line_analytics ADD ROW ACCESS POLICY region_rap ON (region);
```

### Aggregation Policy (NEW — restrict raw row access while allowing aggregates)

```sql
CREATE OR REPLACE AGGREGATION POLICY count_min_5 AS () RETURNS AGGREGATION_CONSTRAINT ->
    AGGREGATION_CONSTRAINT(MIN_GROUP_SIZE => 5);

ALTER TABLE customer_data ADD AGGREGATION POLICY count_min_5;

-- Now SELECT * fails, but SELECT COUNT(*), AVG(salary) GROUP BY dept works
-- IF each group has >= 5 rows
```

Use case: let data scientists query aggregates without seeing individual rows.

## 3. Horizon Catalog (unified governance)

Horizon is Snowflake's enterprise governance layer covering:
- Data classification (PII detection)
- Lineage (column-level)
- Access tracking (who queried what when)
- Compliance reporting (HIPAA, GDPR, SOC2)
- Cross-account permissions
- Object tagging at scale

### Automatic PII classification

```sql
-- Snowflake auto-classifies a sample of rows
CALL SYSTEM$CLASSIFY('my_table', '{...}');

-- View results
SELECT * FROM TABLE(INFORMATION_SCHEMA.CLASSIFY_RESULT(JOB_ID => 'xxx'));
```

### Column-level lineage

```sql
SELECT * FROM TABLE(SNOWFLAKE.ACCOUNT_USAGE.GET_LINEAGE(
    OBJECT_NAME => 'FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS',
    OBJECT_DOMAIN => 'TABLE',
    DIRECTION => 'UPSTREAM'
));
```

Returns: every upstream column, the model that transforms it, the SQL fragment.

### Access tracking

```sql
SELECT user_name, role_name, query_text, query_start_time, base_objects_accessed
FROM snowflake.account_usage.access_history
WHERE base_objects_accessed::STRING ILIKE '%FINANCE_LINE_ANALYTICS%'
ORDER BY query_start_time DESC
LIMIT 100;
```

### Compliance reports

Pre-built reports for:
- PII access by role last 90 days
- Privileged role grants in last 30 days
- External data shares
- Network policy violations

## 4. Network security

### IP allowlisting (account-level)

```sql
CREATE OR REPLACE NETWORK POLICY corp_only
    ALLOWED_IP_LIST = ('10.0.0.0/8', '52.10.0.0/16')
    BLOCKED_IP_LIST = ()
    COMMENT = 'Corporate VPN + dbt Cloud IPs only';

ALTER ACCOUNT SET NETWORK_POLICY = 'corp_only';
```

### Per-user network policy

```sql
ALTER USER dbt_service_prod SET NETWORK_POLICY = 'dbt_only_policy';
```

Per-user policy overrides account-level — useful for service accounts that need restricted access from a specific IP range.

### PrivateLink

For dbt Cloud → Snowflake connectivity, use AWS PrivateLink (no public internet):

```sql
ALTER ACCOUNT SET INBOUND_PRIVATE_LINK_ALLOWED = TRUE;
```

Then in dbt Cloud account settings, configure the PrivateLink endpoint.

### Federation / SSO

```sql
-- SCIM for user provisioning from Okta / Azure AD
CREATE OR REPLACE SECURITY INTEGRATION my_scim
    TYPE = SCIM
    SCIM_CLIENT = 'okta'
    RUN_AS_ROLE = 'SCIM_ROLE';

-- OAuth for user authentication
CREATE OR REPLACE SECURITY INTEGRATION my_oauth
    TYPE = OAUTH
    OAUTH_CLIENT = CUSTOM
    OAUTH_CLIENT_TYPE = 'CONFIDENTIAL'
    OAUTH_REDIRECT_URI = 'https://app.workday.com/snowflake/callback'
    ENABLED = TRUE;

-- SAML for SSO
CREATE OR REPLACE SECURITY INTEGRATION my_saml
    TYPE = SAML2
    SAML2_ISSUER = '...'
    SAML2_SSO_URL = '...'
    SAML2_PROVIDER = 'OKTA'
    ENABLED = TRUE;
```

## 5. Replication & Disaster Recovery

### Replication types

| Type | Replicates | Frequency | Use case |
|---|---|---|---|
| Database replication | Schemas + tables + views | Configurable | Cross-region read replica |
| Account replication | Database + users + roles + warehouses + integrations | Configurable | Full DR / HA |
| Failover group | Account replication + automated failover | Configurable | High availability |

### Setup database replication

```sql
-- On primary account
ALTER DATABASE finance_prod ENABLE REPLICATION TO ACCOUNTS ('xy12345.us-east-1');

-- On secondary account
CREATE DATABASE finance_prod
    AS REPLICA OF xy12345.us-west-2.finance_prod;

-- Refresh manually OR auto-refresh
ALTER DATABASE finance_prod REFRESH;

-- Auto-refresh via task
CREATE TASK refresh_finance_prod_replica
    WAREHOUSE = compute_wh
    SCHEDULE = '5 MINUTE'
AS
    ALTER DATABASE finance_prod REFRESH;
```

### Failover group (automated failover)

```sql
-- On primary
CREATE FAILOVER GROUP finance_failover
    OBJECT_TYPES = (DATABASES, USERS, ROLES, WAREHOUSES, INTEGRATIONS)
    ALLOWED_DATABASES = (finance_prod, finance_int_prod)
    ALLOWED_ACCOUNTS = ('xy12345.us-east-1')
    REPLICATION_SCHEDULE = '5 MINUTE';

-- On secondary
CREATE FAILOVER GROUP finance_failover
    AS REPLICA OF prim_account.us-west-2.finance_failover;

-- Failover
ALTER FAILOVER GROUP finance_failover PRIMARY;
```

### RPO / RTO budgets

| | RPO | RTO |
|---|---|---|
| Manual database replication | 24h | 4h (manual promote) |
| Auto-refresh DB replication | 5-15 min | 4h (manual promote) |
| Failover group | 5-15 min | <30 min (automated) |
| Cross-cloud (AWS↔Azure) | 30 min - 2h | 1-2h |

Choose based on the cost of downtime vs cost of replication credits.

### Cross-cloud replication

Snowflake supports replication across AWS, Azure, and GCP. Useful for:
- Cloud-vendor risk diversification
- Customer requirements (e.g., EU customers need EU-residency)
- Latency optimization (replica closer to consumers)

Cost: ~3-5× single-region replication due to egress charges.

## 6. Auditing & compliance

### Login history

```sql
SELECT user_name, client_ip, first_authentication_factor, second_authentication_factor,
       reported_client_type, reported_client_version, is_success
FROM snowflake.account_usage.login_history
WHERE event_timestamp > DATEADD('day', -7, CURRENT_TIMESTAMP())
ORDER BY event_timestamp DESC;
```

### Privileged role usage

```sql
SELECT query_text, user_name, role_name, query_start_time
FROM snowflake.account_usage.query_history
WHERE role_name IN ('ACCOUNTADMIN', 'SECURITYADMIN', 'USERADMIN')
  AND query_start_time > DATEADD('day', -30, CURRENT_TIMESTAMP())
ORDER BY query_start_time DESC;
```

### Data egress

```sql
-- Outbound data shares
SHOW SHARES;

-- External stages (data leaving Snowflake)
SHOW STAGES;
```

### Compliance reports (Horizon)

- **HIPAA** — PHI tag coverage, masking policy enforcement
- **GDPR** — PII tag coverage, right-to-be-forgotten queries
- **SOC2** — Privileged role usage, access reviews
- **PCI** — Cardholder data identification

## 7. Secrets management

Don't hardcode secrets in models. Use Snowflake's secret store:

```sql
CREATE SECRET my_api_key
    TYPE = GENERIC_STRING
    SECRET_STRING = 'sk-[REDACTED]';

-- Use in external function
CREATE EXTERNAL ACCESS INTEGRATION my_api_access
    ALLOWED_NETWORK_RULES = (allowed_ips)
    ALLOWED_AUTHENTICATION_SECRETS = (my_api_key);

CREATE FUNCTION call_api(prompt STRING)
    RETURNS VARCHAR
    LANGUAGE PYTHON
    EXTERNAL_ACCESS_INTEGRATIONS = (my_api_access)
    SECRETS = ('cred' = my_api_key)
    HANDLER = 'call'
AS $$
import _snowflake, requests
def call(prompt):
    api_key = _snowflake.get_generic_secret_string('cred')
    return requests.post('https://api.com', headers={'Authorization': f'Bearer {api_key}'}, ...)
$$;
```

## 8. Anti-patterns to refuse in code review

| Anti-pattern | Why it's bad | Refusal script |
|---|---|---|
| Grant ACCOUNTADMIN to service account | Massive blast radius | "Service accounts get scoped functional roles only" |
| Skip future grants | New objects unreadable until manual grant | "Add `GRANT ... ON FUTURE TABLES`" |
| One role per user | Unmanageable at scale | "Use functional roles; share roles across users with same job" |
| Hardcoded API key in stored proc | Secret leakage | "Use Snowflake secrets API" |
| Allow `0.0.0.0/0` in network policy | Defeats network policy | "Restrict to corp IPs + service IP ranges" |
| No data classification on confidential columns | Cannot enforce masking | "Tag columns; bind masking policy to tag" |
| Failover group without testing | Untested DR plan is no DR plan | "Quarterly failover drill + documented runbook" |
| Replication enabled without RPO target | Drift between accounts | "Document RPO; alert when actual > target" |
| Granting USAGE on all schemas via SYSADMIN | Easy now, audit nightmare later | "Per-schema grants via access roles" |
