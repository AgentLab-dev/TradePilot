---
name: dbt-system-admin
description: >-
  dbt Cloud and dbt Core system administration, CI/CD pipelines, environment configuration,
  job orchestration, and operational management. Covers dbt Cloud API, job triggers, deployment
  environments, GitHub Actions integration, connection profiles, packages, cross-project refs,
  service tokens, webhooks, and production operations. Use when managing dbt Cloud jobs,
  configuring CI/CD, troubleshooting dbt run failures, setting up environments, managing
  connections, or administering dbt infrastructure.
---

# dbt System Admin

## dbt Cloud Architecture

### Environments
| Environment | Purpose | Trigger |
|-------------|---------|---------|
| Development | IDE, ad-hoc runs | Manual |
| CI/Staging | PR validation | PR webhook |
| QA | Pre-production testing | Merge to qa branch |
| Production | Live data | Merge to prod / scheduled |

### Job Types
| Type | Trigger | Use Case |
|------|---------|----------|
| CI Job | Pull request | `dbt build --select state:modified+` |
| Deploy Job | Merge / schedule | Full or selective model builds |
| Scheduled Job | Cron | Nightly full refresh, hourly incremental |

## dbt Cloud API

### Trigger a Job Run
```bash
curl -X POST "https://<host>/api/v2/accounts/{account_id}/jobs/{job_id}/run/" \
  -H "Authorization: Token $DBT_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cause": "Triggered via API",
    "steps_override": ["dbt run --select +model_name+ --vars {\"as_was_date\": \"2026-02-11\"}"],
    "git_branch": "qa"
  }'
```

### Key API Endpoints
| Action | Method | Endpoint |
|--------|--------|----------|
| Trigger run | POST | `/api/v2/accounts/{id}/jobs/{id}/run/` |
| Get run status | GET | `/api/v2/accounts/{id}/runs/{id}/` |
| List runs | GET | `/api/v2/accounts/{id}/runs/` |
| Get run artifacts | GET | `/api/v2/accounts/{id}/runs/{id}/artifacts/` |
| Cancel run | POST | `/api/v2/accounts/{id}/runs/{id}/cancel/` |

### Run Status Codes
| Status | Meaning |
|--------|---------|
| 1 | Queued |
| 2 | Starting |
| 3 | Running |
| 10 | Success |
| 20 | Error |
| 30 | Cancelled |

## GitHub Actions Integration

### Reusable Workflow Pattern
```yaml
on:
  pull_request:
    branches: [qa, prod]

jobs:
  validate:
    uses: org/shared-workflows/.github/workflows/dbt-validate.yml@main
    secrets: inherit
    with:
      dbt_project_id: "${{ vars.DBT_PROJECT_ID }}"
      dbt_job_id: "${{ vars.DBT_QA_JOB_ID }}"
```

### Runner Groups
- Self-hosted runners in private runner groups require workflow whitelisting
- Jobs in reusable workflows inherit the reusable workflow's whitelisting
- Direct jobs in calling workflows need separate whitelisting
- Check: Org Settings → Actions → Runner groups → Workflow access

### OIDC + NLB Pattern
1. GitHub OIDC → AWS IAM Role (trust policy on repo/branch)
2. AWS credentials → curl to NLB endpoint
3. NLB → Lambda/service → dbt Cloud API trigger

## Connection Profiles

### profiles.yml Structure
```yaml
eda_dbt_em:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      password: "{{ env_var('SNOWFLAKE_PASSWORD') }}"
      role: "{{ env_var('SNOWFLAKE_ROLE') }}"
      database: CERTIFIED_DEV
      warehouse: DEV_WH
      schema: FINANCE
      threads: 4
    qa:
      type: snowflake
      database: CERTIFIED_QA
      warehouse: QA_WH
    prod:
      type: snowflake
      database: CERTIFIED_PROD
      warehouse: PROD_WH
```

## Cross-Project References

### dbt_project.yml
```yaml
dispatch:
  - macro_namespace: dbt
    search_order: [eda_dbt_em, dbt]

on-run-start:
  - "{{ dbt_utils.grant_select(...) }}"
```

### packages.yml
```yaml
packages:
  - package: dbt-labs/dbt_utils
    version: ">=1.0.0"
  - git: "https://github.com/org/eda-dbt-gtm.git"
    revision: main
```

Cross-project refs: `{{ ref('eda_dbt_gtm', 'model_name') }}`

## Operational Runbooks

### Pipeline Failure Triage
1. Check dbt Cloud run logs for error message
2. Identify failing model and step
3. Check Snowflake `QUERY_HISTORY` for the failed SQL
4. Common causes: permissions, warehouse suspended, source freshness, schema drift

### Full Refresh Protocol
1. Verify warehouse size is adequate (scale up if needed)
2. Run: `dbt run --full-refresh --select model_name`
3. Monitor warehouse credit usage
4. Scale warehouse back down after completion
5. Verify row counts and data integrity

### Backfill Process
```bash
for date in 2026-02-06 2026-02-07 2026-02-08; do
  dbt run --select +model_name+ \
    --vars "{\"as_was_date\": \"$date\"}"
done
```

### Seed Management
- Seeds are CSV files in `seeds/` directory
- `dbt seed` loads them to Snowflake
- Use for reference data, overrides, mappings
- Keep seeds <1MB; larger data should be sources

## Service Tokens & Security
- dbt Cloud service tokens: scoped to specific permissions (read metadata, trigger runs)
- Store tokens as GitHub secrets, never in code
- Rotate tokens on team member departure
- Audit token usage via dbt Cloud admin panel

## Troubleshooting

| Issue | Resolution |
|-------|-----------|
| `connection` error in dbt CLI | Check profiles.yml, env vars, Snowflake network policy |
| Cross-project ref fails | Run `dbt deps` first, verify packages.yml |
| CI job runs wrong models | Check `state:modified` selector, ensure manifest artifact exists |
| Job stuck in queue | Check dbt Cloud environment, Snowflake warehouse availability |
| `--full-refresh` timeout | Scale up warehouse, consider partitioned refresh |
