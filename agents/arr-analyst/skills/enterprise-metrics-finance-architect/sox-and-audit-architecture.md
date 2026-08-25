# SOX & Audit Architecture

How to design finance pipelines that satisfy SOX (Sarbanes-Oxley) controls:
immutability, traceability, change management, restated metrics, audit logs.

Workday is a public company → financial-statement-impacting data is subject
to SOX. ARR / NRR / GRR all flow into investor-facing reporting → SOX Tier 2
at minimum. GL data + revenue recognition → SOX Tier 1.

This doc covers the architectural patterns for SOX-compliant pipelines.

---

## §1. SOX tiering

| Tier | Definition | Examples | Controls |
|---|---|---|---|
| **Tier 1** | Direct input to financial statements | GL journals, Zuora revenue, Workday FM postings | Strictest: locked schemas, audit logs, approver workflow |
| **Tier 2** | Investor-facing metrics + management reporting | ARR, ACV, NRR, GRR, bookings | Strict: change approval, immutable snapshots, restated metric logging |
| **Tier 3** | Operational metrics | Pipeline, marketing-sourced, churn risk | Standard data quality controls |

Tier classification documented per model in YAML:
```yaml
models:
  - name: finance_line_analytics
    meta:
      sox_tier: 2
      owner: "@finance-ae-team"
      approval_required_for_changes: TRUE
```

---

## §2. Immutability of closed periods

Once a fiscal quarter closes (typically 5-10 business days after period end), the metric snapshots for that quarter become IMMUTABLE.

### 2.1 What "immutable" means

- `as_was_date` snapshots in `FINANCE_LINE_ANALYTICS` for closed periods cannot be modified
- New `as_was_date` snapshots can be added (current week)
- Re-runs that would re-compute closed snapshots are BLOCKED by guard logic

### 2.2 Architectural enforcement

```sql
{{ config(
    materialized='incremental',
    unique_key=['agreement_line_item_id', 'as_was_date'],
    incremental_strategy='merge',
    pre_hook="{{ guard_no_closed_period_rebuild() }}"  -- custom macro
) }}
```

Where `guard_no_closed_period_rebuild` macro:
```sql
{% macro guard_no_closed_period_rebuild() %}
    {% if execute and target.name in ('prod', 'qa') %}
        {% set check_query %}
            SELECT COUNT(*) AS would_overwrite
            FROM {{ this }}
            WHERE as_was_date IN (
                SELECT as_was_date FROM {{ ref('int_em_arr_line_base') }}
                WHERE as_was_date < DATEADD('day', -30, CURRENT_DATE)
            )
        {% endset %}
        {% set result = run_query(check_query) %}
        {% if result.rows[0][0] > 0 %}
            {{ exceptions.raise_compiler_error(
                'BLOCKED: would overwrite closed-period snapshots. SOX approval required. '
                'Use override macro `force_rebuild_with_sox_approval` if approved.'
            ) }}
        {% endif %}
    {% endif %}
{% endmacro %}
```

### 2.3 Approved rebuild path

If a closed-period rebuild is needed (e.g., correcting a bug):

1. **File Jira** with reason, scope, expected variance
2. **SOX approver review** (Finance Controller)
3. **Compute expected variance** in non-prod first
4. **Use override flag**: `--vars '{"force_rebuild_with_sox_approval": "JIRA-XXXX"}'`
5. **Document the rebuild** in `FINANCE_AUDIT_LOG`
6. **Notify consumers**: Sigma dashboards may show changed numbers
7. **Restate impacted reports** if previously published

---

## §3. Audit logging

Every change to SOX-tier model is logged:

```sql
-- FINANCE_AUDIT_LOG (append-only)
CREATE TABLE FINANCE_PROD.MANAGED.FINANCE_AUDIT_LOG (
    log_id VARCHAR DEFAULT UUID_STRING(),
    log_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP,
    model_name VARCHAR,
    change_type VARCHAR,  -- 'INSERT', 'UPDATE', 'DELETE', 'REBUILD', 'BACKFILL'
    affected_period_start DATE,
    affected_period_end DATE,
    user_actor VARCHAR,
    jira_ticket VARCHAR,
    sox_approver VARCHAR,
    reason TEXT,
    pre_change_total NUMBER,
    post_change_total NUMBER,
    variance NUMBER
);
```

Pattern: every `dbt run` that touches SOX-tier models writes audit log row.

Macros:
```sql
{% macro audit_log_pre_run() %}
    {% set total_before %}
        SELECT SUM(arr_usd_current) FROM {{ this }}
    {% endset %}
    -- store in temp table
{% endmacro %}

{% macro audit_log_post_run() %}
    -- compute new total, compute variance, insert audit log row
{% endmacro %}
```

---

## §4. Change management

### 4.1 Approval workflow

Any change to a SOX Tier-2 model goes through:

```
1. Developer creates PR
2. CI: dbt tests pass
3. CI: ARR walk reconciliation
4. Reviewer 1: Engineering peer (technical correctness)
5. Reviewer 2: finance-functional-analytics SME (metric correctness)
6. Reviewer 3: Finance Controller (SOX approval, IF closed-period impact)
7. Merge to QA → validation
8. Merge to PROD → production
```

For Tier-1: add Compliance Officer + Executive sign-off.

### 4.2 Change documentation

Every SOX-impacting PR includes:
- Jira link
- KPI Spec (if new metric)
- Reconciliation report (before/after variance per dimension)
- SOX approver name (if applicable)
- Rollback plan

---

## §5. Restated metrics

When a published metric must be restated (correction):

### 5.1 Workflow

1. **Identify the error**: usually surfaced by reconciliation or audit
2. **Quantify the impact**: 
   - Which `as_was_date`s affected?
   - Which downstream dashboards affected?
   - What's the magnitude of restatement?
3. **Pre-restatement notice**: 
   - Notify Finance Controller + impacted consumers
   - Pause Sigma dashboards if material
4. **Restate the data**:
   - SOX-approved closed-period rebuild
   - Document in `RESTATEMENT_LOG`
5. **Publish restated numbers**:
   - Update Sigma dashboards
   - Issue corrected investor disclosures if material
6. **Root cause + prevention**:
   - Postmortem
   - New test / guard to prevent recurrence

### 5.2 Restatement log

```sql
CREATE TABLE FINANCE_PROD.MANAGED.RESTATEMENT_LOG (
    restatement_id VARCHAR DEFAULT UUID_STRING(),
    restatement_date DATE DEFAULT CURRENT_DATE,
    affected_metric VARCHAR,
    affected_period VARCHAR,
    original_value NUMBER,
    restated_value NUMBER,
    variance NUMBER,
    variance_pct NUMBER,
    reason TEXT,
    jira_ticket VARCHAR,
    sox_approver VARCHAR,
    investor_disclosure_required BOOLEAN,
    investor_disclosure_date DATE
);
```

---

## §6. Source data segregation

SOX-relevant source data lands in segregated databases:

| Database | Content | Access |
|---|---|---|
| `BASE_PROD` | All Fivetran sources | Read by all dbt projects |
| `BASE_SOX_PROD` | SOX-relevant sources (separate Fivetran connector) | Read only by SOX-approved jobs |

Rationale: independent control for SOX data lineage. Auditor can verify source data integrity separately.

Stage models for SOX flow:
```sql
-- stg_em_zuora_revenue_sox
SELECT * FROM {{ source('base_sox_prod_zuora', 'revenue_event') }}  -- not BASE_PROD
```

---

## §7. The 4 SOX-specific architectural rules

### 7.1 No silent overwrites

Every UPDATE / DELETE in a SOX-tier model logs to `FINANCE_AUDIT_LOG`. No invisible changes.

### 7.2 No upstream cascading failures

If a SOX-tier model fails, do NOT auto-rerun without notification. Page on-call. Manual review before reset.

### 7.3 Immutable schemas in closed periods

You cannot ALTER TABLE on a SOX-tier model in a way that retroactively changes closed data. Schema changes use:
- Add column (NULL for closed periods)
- Deprecate column (mark in YAML, do not delete)
- Version bump (new model `_v2`) for breaking changes

### 7.4 Tested validation pre-promotion

Every SOX-tier change requires PR-time tests:
- ARR walk balances within $1
- NRR / GRR within ±0.1% of prior baseline
- Reconciliation queries pass

---

## §8. The "annual SOX audit" preparation

Once a year, external auditors review SOX controls. You provide:

1. **Audit log**: full `FINANCE_AUDIT_LOG` for prior fiscal year
2. **Restatement log**: every restatement with full documentation
3. **Change log**: every git PR touching SOX-tier models
4. **Test history**: every dbt test pass/fail
5. **Access log**: who queried SOX-tier models (from Snowflake `ACCESS_HISTORY`)
6. **Approval evidence**: SOX-approver sign-offs (from Jira)
7. **Reconciliation evidence**: ARR-to-Revenue, ARR-to-Billings tie-outs at every quarter close

Architecture should make all of this easy to extract.

---

## §9. Revenue reconciliation (ARR ↔ Revenue)

ARR (forward-looking, annualized) ≠ Revenue (backward-looking, recognized). But they must reconcile.

### 9.1 The reconciliation

```sql
WITH arr_period AS (
    SELECT 
        fiscal_quarter,
        SUM(arr_usd_hist) / 4 AS avg_arr_for_period_quarterly  -- approximate quarterly revenue
    FROM FINANCE_LINE_ANALYTICS
    WHERE as_was_date = '2025-05-06'
      AND is_arr_eligible = TRUE
    GROUP BY 1
),
revenue_period AS (
    SELECT
        fiscal_quarter,
        SUM(recognized_revenue_usd) AS recognized_revenue
    FROM FINANCE_PROD.MANAGED.ZUORA_REVENUE_RECOGNIZED
    WHERE fiscal_quarter = 'FY26Q1'
    GROUP BY 1
)
SELECT
    ap.fiscal_quarter,
    ap.avg_arr_for_period_quarterly,
    rp.recognized_revenue,
    rp.recognized_revenue - ap.avg_arr_for_period_quarterly AS variance,
    ABS(rp.recognized_revenue - ap.avg_arr_for_period_quarterly) / NULLIF(ap.avg_arr_for_period_quarterly, 0) AS variance_pct
FROM arr_period ap
JOIN revenue_period rp ON ap.fiscal_quarter = rp.fiscal_quarter;
```

Expected variance: < 2-3% (timing differences + ramp-up + deferred revenue).
Variance > 5%: investigate.

This reconciliation runs every quarter close. Auditors review.

---

## §10. The "rollback if something goes wrong" architecture

When a SOX-tier change goes wrong:

### 10.1 Detection

- ARR walk fails to balance
- NRR / GRR shifts unexpectedly
- Sigma dashboard shows outlier

### 10.2 Rollback

Snowflake Time Travel:
```sql
-- Restore FINANCE_LINE_ANALYTICS to state at 2025-05-15 09:00 UTC
CREATE OR REPLACE TABLE FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS
AS SELECT * FROM FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS 
   AT (TIMESTAMP => '2025-05-15 09:00:00'::TIMESTAMP_NTZ);
```

### 10.3 Notification

- Slack `#eda-incidents` with severity
- Notify SOX approver
- Notify impacted consumers (e.g., FP&A team for AOP variance)

### 10.4 Postmortem

- Root cause documented
- Test added to prevent recurrence
- Architecture change if pattern (e.g., add guard macro)

---

## §11. Tools + integrations

| Tool | Purpose |
|---|---|
| Snowflake `ACCESS_HISTORY` | Who queried SOX-tier models |
| Snowflake Time Travel | Rollback within 90 days |
| Snowflake `ACCOUNT_USAGE.QUERY_HISTORY` | Audit trail of SQL execution |
| Jira | SOX approval workflow tracking |
| GitHub | PR review + approval evidence |
| Atlan | Data lineage for impact analysis |
| `FINANCE_AUDIT_LOG` (custom) | Application-level audit |
| `RESTATEMENT_LOG` (custom) | Restatement tracking |
| Sigma | Dashboard publish + restate |

---

## §12. The "I'm proposing a SOX-tier change" workflow

1. **Draft proposal**: KPI spec, model design, reconciliation plan
2. **Engineering review**: Peer code review
3. **SME review**: `finance-functional-analytics` validates metric definition
4. **Architect review**: `enterprise-metrics-finance-architect` validates implementation
5. **Test build in dev**: full reconciliation run
6. **SOX approver review**: Finance Controller
7. **Merge to QA**: validation in QA environment
8. **Stakeholder review**: dashboard owners review changes
9. **Merge to PROD**: production deploy
10. **Post-deploy validation**: reconciliation passes
11. **Audit log entry**: change documented in `FINANCE_AUDIT_LOG`
12. **Stakeholder notification**: changes announced

---

## §13. Cross-references

- `metric-portfolio-architecture.md` — base architecture
- `enterprise-data-architect/platform-architecture.md` — `BASE_SOX_PROD` segregation
- `enterprise-data-architect/domain-finance-billing.md` — period close + revenue context
- `finance-functional-architect/metric-governance-and-controls.md` — change management
- `snowflake-architect/security-and-governance.md` — Snowflake-level controls
