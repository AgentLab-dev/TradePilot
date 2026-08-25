# Data SLOs and Observability

Reference companion to `analytics-engineering-architect/SKILL.md` §4 and §6.

## 1. SLA / SLI / SLO — the formal vocabulary

| Term | Definition | Example |
|---|---|---|
| **SLI** (Service Level Indicator) | A measurable quality dimension | "Freshness = time since last update" |
| **SLO** (Service Level Objective) | Target value for an SLI | "Freshness < 1 hour, 99% of the time" |
| **SLA** (Service Level Agreement) | Contractual commitment with consequences | "If SLO breached, consumer credit refunded" |

In internal data platforms: usually SLOs, sometimes SLAs.

## 2. The 4 essential data SLIs

| SLI | What | Why |
|---|---|---|
| **Freshness** | Time since last successful update | Consumers need recent data |
| **Completeness** | % of expected rows / columns present | Missing data = wrong decisions |
| **Accuracy** | Variance vs ground truth | Numbers must be right |
| **Availability** | Query endpoint uptime | Dashboards must load |

Optional (depending on product):
- **Latency** — query response time (for sub-second BI)
- **Consistency** — replica agreement (for multi-region)

## 3. Measuring freshness

### Definition

```
freshness = current_time - max(load_completed_at) from the data product
```

### Implementation

```sql
-- Add a load tracking column
CREATE TABLE finance_line_analytics (
    ...,
    _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- Compute freshness
SELECT
    'finance_line_analytics' AS data_product,
    MAX(_loaded_at) AS last_load,
    DATEDIFF('hour', MAX(_loaded_at), CURRENT_TIMESTAMP()) AS hours_stale
FROM finance_line_analytics;
```

### dbt source freshness

```yaml
sources:
  - name: salesforce
    tables:
      - name: opportunity
        loaded_at_field: _fivetran_synced
        freshness:
          warn_after: {count: 4, period: hour}
          error_after: {count: 12, period: hour}
```

Run with `dbt source freshness`. Failures stop the build.

### Alerting

```sql
-- Schedule this every 30 min via task
SELECT 'FRESHNESS BREACH' AS alert,
       data_product, hours_stale, target_hours
FROM data_product_freshness
WHERE hours_stale > target_hours;
```

Pipe results to Slack / PagerDuty.

## 4. Measuring completeness

### Definition

```
completeness = actual_rows / expected_rows
```

Where `expected_rows` comes from the source / a prior period / a model.

### Pattern: row count comparison

```sql
-- Track row counts daily
INSERT INTO row_count_history
SELECT 'finance_line_analytics' AS data_product,
       CURRENT_DATE() AS check_date,
       (SELECT COUNT(*) FROM finance_line_analytics) AS actual_rows,
       (SELECT AVG(row_count) FROM row_count_history
        WHERE data_product = 'finance_line_analytics'
          AND check_date BETWEEN DATEADD('day', -8, CURRENT_DATE()) AND DATEADD('day', -1, CURRENT_DATE())
       ) AS expected_rows;

-- Alert when actual < 90% of expected
SELECT * FROM row_count_history
WHERE check_date = CURRENT_DATE()
  AND actual_rows / NULLIF(expected_rows, 0) < 0.90;
```

### Pattern: source-to-target row count

```sql
SELECT
    (SELECT COUNT(*) FROM base_prod.salesforce.opportunity
     WHERE _fivetran_synced > DATEADD('day', -1, CURRENT_TIMESTAMP())) AS source_rows,
    (SELECT COUNT(*) FROM finance_prod.managed.stg_em_opportunity
     WHERE _loaded_at > DATEADD('day', -1, CURRENT_TIMESTAMP())) AS target_rows;
```

Source rows >> target rows → ingestion broke. Target > source → duplicate.

## 5. Measuring accuracy

### Definition

```
accuracy = 1 - |our_value - ground_truth| / ground_truth
```

### Patterns

#### Variance check vs known source

```sql
-- Recon dbt ARR against Salesforce Opportunity Amount
WITH dbt_arr AS (
    SELECT fiscal_quarter_name, SUM(arr_usd_current) AS arr_sum
    FROM finance_line_analytics
    WHERE as_was_date = (SELECT MAX(as_was_date) FROM finance_line_analytics)
    GROUP BY 1
),
sf_arr AS (
    SELECT fiscal_quarter_name, SUM(amount_usd) AS arr_sum
    FROM stg_em_opportunity
    WHERE stage_code = '9'
    GROUP BY 1
)
SELECT d.fiscal_quarter_name,
       d.arr_sum AS dbt_sum,
       s.arr_sum AS sf_sum,
       ABS(d.arr_sum - s.arr_sum) AS variance,
       ABS(d.arr_sum - s.arr_sum) / NULLIF(s.arr_sum, 0) AS variance_pct
FROM dbt_arr d JOIN sf_arr s USING (fiscal_quarter_name)
WHERE ABS(d.arr_sum - s.arr_sum) > 1;     -- $1 tolerance
```

If this returns rows, accuracy SLO is breached. Alert.

#### Anomaly detection on metrics

Track metric values over time; alert on outliers.

```sql
WITH daily_arr AS (
    SELECT as_was_date, SUM(arr_usd_current) AS arr
    FROM finance_line_analytics
    GROUP BY 1
),
stats AS (
    SELECT
        AVG(arr) AS mean_arr,
        STDDEV(arr) AS stddev_arr
    FROM daily_arr
    WHERE as_was_date BETWEEN DATEADD('day', -30, CURRENT_DATE()) AND DATEADD('day', -1, CURRENT_DATE())
)
SELECT today.as_was_date, today.arr, s.mean_arr,
       ABS(today.arr - s.mean_arr) / NULLIF(s.stddev_arr, 0) AS z_score
FROM daily_arr today, stats s
WHERE today.as_was_date = CURRENT_DATE()
  AND ABS(today.arr - s.mean_arr) / NULLIF(s.stddev_arr, 0) > 3;   -- > 3 sigma
```

## 6. Measuring availability

### For SQL data products

```sql
-- Run a heartbeat query every minute
SELECT 1 FROM finance_prod.managed.finance_line_analytics LIMIT 1;
```

Track success rate over 24h. Alert if < 99.9%.

### For semantic-layer / API endpoints

Standard SRE patterns: HTTP 200 rate, P99 latency.

## 7. Observability tooling — selecting

| Tool | What | Pricing | Best for |
|---|---|---|---|
| **Monte Carlo** | Auto-monitored schema/freshness/volume/quality; lineage; incident management | $50k-500k/yr | Enterprise; comprehensive |
| **Sifflet** | Similar to MC; dbt-native | Mid-tier | dbt-heavy shops |
| **Datafold** | Data diff (between dev / prod), monitoring | Per dev seat | Refactor-heavy teams |
| **Bigeye** | ML-based anomaly detection | Mid-tier | Data with strong patterns |
| **Soda** | OSS quality testing framework | Free / Cloud | OSS-first |
| **Great Expectations** | OSS quality testing framework | Free | DIY orgs |
| **dbt source freshness** | Built-in freshness | Free | Bare minimum |
| **dbt tests** | Built-in quality | Free | Bare minimum |
| **DataHub** | Catalog + lineage + monitoring | OSS / Acryl SaaS | Catalog + observability bundle |

### Selection criteria

1. **Auto-detection** — does it auto-monitor without manual config?
2. **Lineage** — column-level lineage for impact analysis
3. **dbt integration** — does it auto-pull dbt tests / manifest?
4. **BI integration** — does it know which dashboards depend on which models?
5. **Alert routing** — Slack, PagerDuty, email, JIRA
6. **Incident workflow** — ack, resolve, postmortem
7. **Cost vs scale** — many vendors price per warehouse / per table

### Bootstrap strategy

Start with **dbt source freshness + dbt tests** (free, built-in). When you outgrow:

| Symptom | Add |
|---|---|
| "Same incident keeps happening" | Anomaly detection (Monte Carlo / Bigeye) |
| "We didn't know X depended on Y" | Lineage (DataHub / Monte Carlo) |
| "Schema changed silently" | Schema monitoring (any of above) |
| "Refactor broke prod" | Datafold (data diff) |

## 8. Observability architecture pattern

```
[Data product]
       │
       ▼
[Auto-monitor]              ← Monte Carlo / Sifflet
[Custom assertions]         ← dbt tests, Soda, GE
[Schema drift]              ← any observability tool
[Volume anomaly]            ← any observability tool
[Freshness check]           ← dbt source freshness
       │
       ▼
[Alert]                     ← Slack channel, PagerDuty
       │
       ▼
[Incident]                  ← Pager, Jira ticket auto-created
       │
       ▼
[Triage]                    ← on-call investigates via lineage
       │
       ▼
[Resolve]                   ← fix; document in runbook
       │
       ▼
[Postmortem]                ← within 5 business days
       │
       ▼
[Preventive test]           ← added to prevent recurrence
```

## 9. Alert design

### Good alerts

- Actionable: there's something the on-call can do
- Symptomatic of user impact: end users are affected (or will be soon)
- Specific: alert message tells you what + where + how bad
- Single-fire: deduplicated; same issue alerts once until resolved

### Bad alerts

- "Disk 80% full" (not yet impacting; can wait)
- "Query took 5.1 seconds" (when threshold was 5.0; noise)
- "All 100 models failed" (single root cause; need one alert with details)

### Alert hygiene

- Review alerts weekly: which fired, which were actionable, which were noise
- Mute / tune noisy alerts within 24h
- Document every alert with a runbook link

## 10. The postmortem template

After every significant data incident:

```markdown
# Postmortem: <one-line description>

## Summary
What happened, when, who/what was affected.

## Impact
- Users affected: X
- Duration: Y
- Dashboards down: Z
- Estimated dollar impact: ...

## Timeline (UTC)
- 10:00 — root cause introduced (PR #1234)
- 11:00 — alert fired
- 11:30 — on-call ack'd
- 12:00 — root cause identified
- 13:00 — fix deployed
- 13:30 — alert cleared
- 14:00 — verified end-to-end

## Root cause
The bug was caused by X. The condition that exposed it was Y.
Chain of events: ...

## Resolution
- Code change: link to PR
- Tests added: link
- Lineage / catalog updates: link

## Why didn't we catch it sooner?
- Test we wish we had: ...
- Monitor we wish we had: ...
- Process we wish we had: ...

## Action items
- [ ] Add test for the condition (assignee, due date)
- [ ] Update runbook
- [ ] Add monitor for X
- [ ] Train team on Y

## Lessons
What we learned that applies elsewhere.
```

## 11. SLO/SLI implementation playbook

Phase 1 (weeks 1-2): inventory + definition

- List all data products (output of mesh exercise)
- For each: define freshness / completeness / accuracy / availability SLOs
- Document in catalog (Atlan, DataHub) or in `data_product.yml`

Phase 2 (weeks 3-4): measurement

- Implement freshness via dbt source freshness + `_loaded_at` columns
- Implement completeness via row-count comparison tests
- Implement accuracy via recon tests
- Build a dashboard showing SLI vs SLO per data product

Phase 3 (weeks 5-6): alerting

- Configure alerts for each SLI breach
- Route alerts to data-product owners (Slack channel + PagerDuty)
- Document runbooks per data product

Phase 4 (weeks 7+): culture

- Weekly SLO review with each domain team
- Incident postmortems within 5 business days
- Track MTTR; aim for < 4 hours for P1 data incidents
- Track SLO attainment per quarter; aim for ≥ 99% of SLOs met

## 12. Anti-patterns

| Anti-pattern | Why bad | Better |
|---|---|---|
| No SLOs ("we'll know if it breaks") | Reactive | Define before incident |
| SLOs without measurement | Hand-wavy | Implement the SLI calculation |
| 100 alerts firing daily | Alarm fatigue | Tune; auto-resolve; combine |
| Alert that has no runbook | On-call can't act | Every alert has a runbook link |
| Postmortem without action items | Just an essay | Tracked tasks with due dates |
| Same incident postmortemed twice | Action item didn't get done | Track action item closure |
| Observability tool with no owner | Stale config; alerts ignored | Single team owns + tunes |
| Catalog with no lineage | "Why did X break Y?" requires manual archaeology | Catalog + lineage from day 1 |
| SLO targets too tight | Constant breaches → desensitization | Set achievable targets first, raise over time |
| SLO targets too loose | Doesn't drive improvement | Tighten when you consistently exceed |
