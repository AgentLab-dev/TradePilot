# FinOps for Data — Cost Attribution, Chargeback, Unit Economics

Reference companion to `analytics-engineering-architect/SKILL.md` §7.

## 1. Why FinOps for data

Without it: bill grows opaquely. Engineering can't justify costs. Business can't make informed tradeoffs.

With it:
- Attribute cost to consumers / models / data products
- Identify expensive consumers + optimize
- Chargeback to business units (turn cost into a controlled variable)
- Compute unit economics (cost per dashboard, cost per metric, cost per customer)

## 2. The cost dimensions

### Snowflake total cost

```
Total = Compute (warehouse credits)
      + Storage (active + time travel + fail-safe)
      + Cloud services (~1% of compute, free up to limits)
      + Data transfer (rare, but cross-cloud / cross-region)
      + Serverless features (Cortex, Optima, Snowpipe, etc.)
```

For most enterprise platforms, compute is 70-85% of the bill, storage 10-25%, other features 5-10%.

### dbt Cloud cost

```
Total = Developer seats × cost per seat
      + Job credits (compute) — usually consumed by Snowflake
      + Semantic Layer requests (volume-based)
```

dbt Cloud licensing is per seat. Compute happens in Snowflake (so counts as Snowflake cost).

### Other tooling

| Tool | Cost driver |
|---|---|
| Fivetran | Active rows ingested (MAR — Monthly Active Rows) |
| Catalog (Atlan, DataHub Cloud) | Per user OR per dataset |
| Observability (Monte Carlo, Sifflet) | Per table OR per warehouse |
| BI (Sigma, Hex, Tableau) | Per user / per viewer |

## 3. Cost attribution — the senior pattern

### Step 1: tag everything

```sql
-- In dbt models
{{ config(
    pre_hook="""
        ALTER SESSION SET QUERY_TAG = '{
          "project": "eda_dbt_em",
          "model": "{{ this.name }}",
          "product": "arr_metrics",
          "team": "ae_team",
          "env": "{{ target.name }}",
          "run_id": "{{ invocation_id }}"
        }'
    """
) }}
```

### Step 2: aggregate costs

```sql
-- Cost per model (last 30 days)
SELECT
    PARSE_JSON(query_tag):project::VARCHAR AS project,
    PARSE_JSON(query_tag):model::VARCHAR AS model,
    PARSE_JSON(query_tag):team::VARCHAR AS team,
    SUM(credits_used_cloud_services) AS cloud_credits,
    SUM(credits_used_query_acceleration) AS qas_credits,
    AVG(execution_time / 1000) AS avg_seconds,
    COUNT(*) AS query_count
FROM snowflake.account_usage.query_history qh
JOIN snowflake.account_usage.warehouse_metering_history wmh
    ON qh.warehouse_id = wmh.warehouse_id
    AND DATE_TRUNC('hour', qh.start_time) = wmh.start_time
WHERE qh.start_time > DATEADD('day', -30, CURRENT_TIMESTAMP())
  AND query_tag ILIKE '%project%'
GROUP BY 1, 2, 3
ORDER BY cloud_credits DESC;
```

### Step 3: unit economics

```sql
-- Cost per dashboard
SELECT
    dashboard_name,
    SUM(credits_used) AS total_credits,
    SUM(credits_used) / NULLIF(daily_view_count, 0) AS credits_per_view
FROM sigma_query_log s
JOIN snowflake.account_usage.query_history q ON s.query_id = q.query_id
WHERE q.start_time > DATEADD('day', -30, CURRENT_TIMESTAMP())
GROUP BY 1;
```

### Step 4: chargeback (or showback)

| Model | How | When |
|---|---|---|
| **Showback** | Report cost per team; no chargeback | Year 1 of FinOps |
| **Soft chargeback** | Cost reported with budget target | Year 2 |
| **Hard chargeback** | Cost charged to team budget | Year 3+ |
| **Reservation** | Team buys X credits/month; overage charged | Mature orgs |

Start with showback. Move to chargeback only when:
- Teams have budget authority
- Cost attribution coverage > 90%
- Chargeback adjudication process exists

## 4. The cost optimization toolkit

### Warehouse-level

| Lever | How | Saving |
|---|---|---|
| Auto-suspend | Set short timeouts (60s dev, 300s prod) | 20-40% |
| Right-size | Match warehouse to workload | 10-30% |
| Multi-cluster off when not needed | `MIN/MAX_CLUSTER_COUNT = 1` for batch | 10-20% |
| Gen2 migration | Per `snowflake-architect/compute-and-cost.md` | 10-20% on DML |
| Adaptive Compute (preview) | Auto-resize for spiky workloads | Variable |

### Model-level

| Lever | How | Saving |
|---|---|---|
| Convert PERMANENT → TRANSIENT for staging | `CREATE OR REPLACE TRANSIENT TABLE ...` | 10-20% storage |
| Reduce time travel retention | `ALTER TABLE ... SET DATA_RETENTION_TIME_IN_DAYS = 1` | 10-30% storage |
| Incremental instead of table | Re-materialize less data per run | 30-70% on heavy models |
| Cluster heavy-filter tables | Add clustering key | 20-50% on dependent queries |
| Optima enabled (Gen2 default) | Replaces some clustering | 10-30% |

### Query-level

| Lever | How | Saving |
|---|---|---|
| Use result cache | Identical queries hit cache | 100% on cache hits |
| Filter early in CTEs | Push down filters | 20-50% per query |
| QUALIFY instead of subquery dedup | Cleaner, equivalent perf | 0% perf, code quality |
| Avoid SELECT * in intermediates | Smaller intermediate data | 5-20% |
| BROADCAST hint for many-to-few joins | Avoid full join shuffle | 30-80% on skewed joins |

### Architectural

| Lever | How | Saving |
|---|---|---|
| Pre-aggregate hot tables | Materialize coarse-grain | 50-90% on coarse queries |
| Move shared data to Iceberg | Avoid duplication across accounts | 20-50% storage |
| Reverse ETL only when needed | Don't push everything to SF | Variable |
| Eliminate unused dashboards | Cancel queries to dead dashboards | Variable |

## 5. The senior cost review (monthly)

```sql
-- Top 10 most expensive models last 30 days
SELECT
    PARSE_JSON(query_tag):model::VARCHAR AS model,
    PARSE_JSON(query_tag):team::VARCHAR AS team,
    SUM(credits_used) AS credits
FROM snowflake.account_usage.query_history
WHERE start_time > DATEADD('day', -30, CURRENT_TIMESTAMP())
  AND query_tag ILIKE '%model%'
GROUP BY 1, 2
ORDER BY 3 DESC
LIMIT 10;
```

For each:
- Is this expected? (heavy model, fine)
- Can we reduce frequency? (every 5 min → hourly)
- Can we right-size warehouse? (M instead of L)
- Can we make it incremental? (table → incremental)
- Can we cache the result? (frequently same query)

Track quarterly cost-reduction wins.

## 6. Cost forecasting

```
Projected_cost(month_N) = base_cost
                       + growth_rate × month_N
                       + new_feature_load
                       + seasonal_adjustment
```

For Snowflake:
- Track credits_used per day; fit a trendline
- Adjust for: new ingest connectors, new dashboards, new BI users, fiscal-quarter close spike

### Budget allocation

| Tier | % of platform budget |
|---|---|
| Production ETL | 50-60% |
| BI / dashboards | 20-30% |
| Ad-hoc / dev | 10-15% |
| Experimentation (new models, ML) | 5-10% |

## 7. Cost-per-data-product (the metric to track)

```sql
-- Cost per data product per quarter
SELECT
    PARSE_JSON(query_tag):product::VARCHAR AS product,
    DATE_TRUNC('quarter', start_time) AS quarter,
    SUM(credits_used) AS credits,
    SUM(credits_used) * 3.0 AS approx_usd       -- assumes $3/credit
FROM snowflake.account_usage.query_history
WHERE query_tag ILIKE '%product%'
GROUP BY 1, 2
ORDER BY 1, 2;
```

Track quarter-over-quarter. Alert when MoM cost growth > 25% without a known driver.

## 8. Cost vs value framework

A data product's cost is half the picture. The other half is value:

| Indicator | Measurement |
|---|---|
| Consumer count | # of distinct users / dashboards / services |
| Query frequency | Queries per day |
| Decisions enabled | Survey-based: "how many decisions per week use this?" |
| Revenue attribution | Best-effort dollar attribution |

Then: ROI = value / cost. Low-ROI data products are candidates for retirement.

## 9. The "data product cost card"

For each data product, maintain:

```
Data Product: arr_line_categories
Owner: ae_team

Monthly cost:
  Compute: $X (Snowflake credits)
  Storage: $Y
  Total: $Z

Monthly value:
  Consumers: 5 teams, 8 dashboards
  Queries/day: ~1000
  Decisions enabled: ~50/quarter
  ROI: high

Optimization opportunities:
  - [ ] Move to incremental (currently table; would save ~$X/month)
  - [ ] Reduce time travel from 7d → 3d (would save ~$Y/month)

Trend: cost +10% QoQ; consumers +20% QoQ → good (cost growing slower than value)
```

## 10. Cost-aware engineering culture

Practices that move cost into the engineering decision:

1. **Show me the credits** — every PR description includes estimated cost delta
2. **Cost review in design docs** — every architectural decision considers cost
3. **Quarterly cost retrospective** — what costs grew? what saved? what surprised us?
4. **Reward cost wins** — public recognition for engineers who reduce cost meaningfully
5. **Cost in on-call runbooks** — "if this alerts, also check cost spike"

## 11. Common cost pitfalls

| Pitfall | Description | Fix |
|---|---|---|
| Idle warehouse running | Long auto-suspend; warehouse never sleeps | Tune AUTO_SUSPEND |
| Full refresh on a regular schedule | Daily `--full-refresh` on a fact table | Make it incremental |
| Wrong warehouse size | Running everything on XL | Right-size per workload |
| Multi-cluster always on | MIN_CLUSTER_COUNT > 1 for batch | Set to 1 for batch warehouses |
| Time travel on everything | 90-day retention everywhere | Tune per table |
| MV maintenance > MV savings | Materialized View on churny base | Drop MV; use DT or compute on read |
| Query Acceleration on a single query | QAS hit by one bad query | Refactor or right-size warehouse |
| Cortex AI in a high-volume model | AI_SUMMARIZE on every row | Move to a separate enrichment task |
| External function with no caching | Same call 1000× per query | Cache results |
| Catalog auto-extracting from every table every hour | Catalog tool generating heavy traffic | Tune catalog crawl schedule |

## 12. Anti-patterns

| Anti-pattern | Why bad | Better |
|---|---|---|
| No cost attribution | Bill grows opaquely | Tag everything, attribute weekly |
| Chargeback without infrastructure | Teams can't see their cost | Build showback first |
| Optimizing the wrong thing | Saving $10 while $10k bleeds elsewhere | Pareto: focus on top 10 cost items |
| Cost optimization as a one-time sprint | Cost rebounds in 6 months | Continuous discipline + quarterly review |
| Hiding cost from engineering | Engineers can't optimize what they can't see | Engineers see cost dashboards |
| Cost decisions made unilaterally by finance | Engineering won't comply | Joint engineering + finance ownership |
| Skipping cost in architecture decisions | "We'll deal with cost later" | Cost as a first-class constraint |
| Cost forecasting based on vibes | Surprises | Trendline + adjustments |
