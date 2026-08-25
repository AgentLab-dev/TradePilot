# MetricFlow & dbt Semantic Layer

Reference companion to `dbt-architect/SKILL.md` §3 (cross-team) and the
`analytics-engineering-architect/semantic-layer-architecture.md` deep dive.

## 1. Why a semantic layer

Without it, every BI tool / notebook / report defines metrics independently:

| Consumer | Their definition of "ARR" |
|---|---|
| Sigma dashboard A | `sum(arr_usd_current) where as_was_date = max` |
| Sigma dashboard B | `sum(arr_usd_hist) where fiscal_quarter_name = 'FY26Q1'` |
| Finance Excel | `sum(amount) where stage_code = '9'` |
| ML feature | `sum(arr_usd_actual) where is_active` |

Four "ARRs", four numbers, four meetings to reconcile. The semantic layer is **one definition, many consumers**.

## 2. MetricFlow — the dbt semantic layer (GA 2026)

MetricFlow is dbt's metric definition engine. It compiles metric requests (e.g., "ARR by fiscal_quarter, by product_l1") into Snowflake SQL on-the-fly.

### Architecture

```
                          ┌────────────────┐
   BI tool (Sigma, Hex,  │                 │
   Tableau, Cube, etc.)  │   MetricFlow    │   Snowflake
        │                ─►│  (in dbt Cloud  │─►   (executes
        │                  │  or self-host)  │     compiled SQL)
        │                  └────────┬───────┘
        ▼                           │
   API request:           Reads from:
   {metric: arr,           - semantic_models
    group_by: [date, product_l1]}    - metrics
                           - saved_queries
                          definitions in dbt project
```

The BI tool sends a high-level request. MetricFlow:
1. Resolves which semantic model(s) hold the measure
2. Determines the join graph to bring in dimensions
3. Compiles to Snowflake SQL
4. Returns the result

## 3. Semantic models — the foundation

A semantic model wraps a dbt model (typically a `bt_*` fact table) and exposes its **entities**, **dimensions**, and **measures**.

```yaml
# models/finance/_semantic_models.yml
semantic_models:
  - name: arr_line_categories
    description: "ARR at agreement-line-item grain"
    model: ref('arr_line_categories')

    # Entities: foreign keys / primary keys this model exposes
    entities:
      - name: agreement_line_item
        type: primary
        expr: agreement_line_item_id
      - name: account
        type: foreign
        expr: account_id
      - name: opportunity
        type: foreign
        expr: opportunity_id
      - name: agreement
        type: foreign
        expr: agreement_id

    # Dimensions: attributes for grouping / filtering
    dimensions:
      - name: as_was_date
        type: time
        type_params: {time_granularity: day}
      - name: fiscal_quarter_name
        type: categorical
      - name: arr_category
        type: categorical
      - name: product_code_l1
        type: categorical
      - name: term_end_date
        type: time
        type_params: {time_granularity: day}

    # Measures: aggregatable values
    measures:
      - name: arr_amount
        description: "ARR in USD"
        agg: sum
        expr: arr_usd_current
        agg_time_dimension: as_was_date
      - name: arr_count
        description: "Count of ARR rows"
        agg: count
        expr: agreement_line_item_id
        agg_time_dimension: as_was_date
```

### Entity types

| Type | Meaning | Example |
|---|---|---|
| `primary` | The grain of this semantic model | `agreement_line_item` for ALI grain |
| `foreign` | A reference to another semantic model's primary | `account` (joins to account semantic model) |
| `unique` | Unique within this model but not the grain | `external_id` |
| `natural` | Natural key (often used in SCD2) | `business_key` |

### Dimension types

| Type | Use |
|---|---|
| `categorical` | Strings, booleans, enums |
| `time` | Date / timestamp; requires `time_granularity` |

## 4. Metrics — the unit of consumer API

Five metric types. Pick based on the math you need.

### Simple metric

```yaml
metrics:
  - name: arr
    description: "Total ARR in USD"
    type: simple
    label: ARR
    type_params:
      measure: arr_amount
```

### Ratio metric (denominator)

```yaml
metrics:
  - name: net_dollar_retention
    description: "NDR = ending ARR / beginning ARR"
    type: ratio
    label: NDR
    type_params:
      numerator: arr_ending
      denominator: arr_beginning
```

### Derived metric (formula across other metrics)

```yaml
metrics:
  - name: ndr_minus_gross_retention
    description: "Pure expansion contribution"
    type: derived
    label: Expansion Contribution
    type_params:
      expr: net_dollar_retention - gross_retention
      metrics:
        - name: net_dollar_retention
        - name: gross_retention
```

### Cumulative metric (time window aggregation)

```yaml
metrics:
  - name: arr_quarter_to_date
    description: "Sum of ARR additions QTD"
    type: cumulative
    type_params:
      measure: arr_delta
      window: 1 quarter
      grain_to_date: quarter
```

### Conversion metric (funnel / cohort)

```yaml
metrics:
  - name: opportunity_to_close_rate
    description: "Rate of opps that closed within 90 days of creation"
    type: conversion
    type_params:
      entity: opportunity
      base_measure:
        name: opp_created_count
      conversion_measure:
        name: opp_closed_count
      window: 90 days
```

## 5. Time spines — the bedrock of time-based metrics

A time spine is a model with one row per date (or per hour, week, etc.). Required for:
- Cumulative metrics
- Period-over-period comparisons
- Filling in dates with no facts ("show 0 for missing days")

```yaml
# models/_semantic/time_spine.yml
models:
  - name: time_spine_daily
    description: "One row per day from 2020 to 2030"

# models/_semantic/time_spine_daily.sql
{{ config(materialized='table') }}
with date_spine as (
    {{ dbt_utils.date_spine(
        datepart='day',
        start_date="cast('2020-01-01' as date)",
        end_date="cast('2030-12-31' as date)"
    ) }}
)
select
    date_day as ts,
    extract(year from date_day) as year,
    extract(quarter from date_day) as quarter,
    extract(month from date_day) as month,
    extract(week from date_day) as week
from date_spine
```

Register the time spine globally:

```yaml
# semantic_models.yml
semantic_models:
  - name: time_spine_daily
    defaults:
      agg_time_dimension: ts
    model: ref('time_spine_daily')
    node_relation:
      alias: time_spine_daily
      schema: '{{ target.schema }}'
    primary_time_dimension: ts
    dimensions:
      - name: ts
        type: time
        type_params: {time_granularity: day}
```

## 6. Saved queries — pre-defined consumer views

A saved query is a named MetricFlow request. Useful for:
- Dashboards that always pull the same shape
- Cached / materialized BI extracts
- Documenting "this is how the CFO measures the business"

```yaml
saved_queries:
  - name: cfo_quarterly_arr
    description: "ARR by product L1 by fiscal quarter for CFO review"
    query_params:
      metrics:
        - arr
        - new_logo_arr
        - expansion_arr
        - churn_arr
      group_by:
        - TimeDimension('arr_line_categories__as_was_date', 'quarter')
        - Dimension('arr_line_categories__product_code_l1')
      where:
        - "{{ Dimension('arr_line_categories__fiscal_year') }} >= 'FY26'"
    exports:
      - name: cfo_quarterly_arr_export
        config:
          export_as: table
          schema: finance_published
```

`exports` materializes the saved query as a regular table — useful when MetricFlow's on-the-fly SQL is too slow for sub-second BI.

## 7. Consumer access patterns

### dbt Cloud Semantic Layer API

```python
# Python SDK
from dbtsl import SemanticLayerClient
client = SemanticLayerClient(host='...', environment_id=...)
df = client.query(
    metrics=['arr'],
    group_by=['fiscal_quarter_name', 'product_code_l1'],
    where=["{{ Dimension('arr_line_categories__fiscal_year') }} >= 'FY26'"]
)
```

### CLI

```bash
mf query --metrics arr,new_logo_arr \
         --group-by metric_time__quarter,product_code_l1 \
         --where "metric_time >= '2026-01-01'"
```

### GraphQL (BI tools)

```graphql
query {
  query(
    metrics: [{name: "arr"}]
    groupBy: [
      {name: "metric_time", grain: QUARTER}
      {name: "product_code_l1"}
    ]
  ) {
    queryId
  }
}
```

### Native integrations (no SQL needed)

| BI tool | Integration |
|---|---|
| Sigma | Connect via JDBC; Sigma sends metric requests as SQL queries that MetricFlow rewrites |
| Hex | Native dbt Semantic Layer cell |
| Tableau | JDBC driver; metrics appear as measures |
| Cube | dbt SL as a data source |
| Looker | LookML wrapper using dbt SL as backend (preview) |
| ThoughtSpot | Native dbt SL integration |
| Mode | dbt SL integration |

## 8. Versioning metrics

Metrics change. Use the same versioning pattern as models:

```yaml
metrics:
  - name: arr
    type: simple
    type_params: {measure: arr_amount}
    deprecation_date: 2026-12-31      # signals consumers to migrate

  - name: arr_v2
    type: simple
    type_params: {measure: arr_amount_with_corrections}
```

Consumers request `arr` or `arr_v2` explicitly. After the deprecation date, `arr` errors at query time.

## 9. Governance — who owns what

| Asset | Owner | Approval to change |
|---|---|---|
| Semantic model (entity/dim list) | Producing team (e.g., AE) | Team lead + 1 reviewer |
| Measure definition (SQL expr) | Producing team | Team lead + 1 reviewer |
| Metric definition | Domain owner (e.g., Finance) | Domain owner + AE lead |
| Saved query | Consumer team (e.g., FP&A) | Consumer team lead |
| Time spine | Platform team | Platform lead |

Use `meta:` blocks to encode this in YAML and enforce via CI:

```yaml
metrics:
  - name: arr
    meta:
      owner: finance_analytics
      slack_channel: '#finance-metrics'
      sla_freshness_hours: 24
      data_source_jira: PROJ-123
```

## 10. Performance — when MetricFlow is slow

MetricFlow compiles to Snowflake SQL on every request. For high-traffic dashboards, this can be costly.

### Optimization options

| Option | When | How |
|---|---|---|
| **Saved query → exports** | Same query hits 100+ times/day | Add `exports:` block; materialize to table; BI queries the table directly |
| **MetricFlow cache** | Repeated queries with small variations | Enable Cloud cache in dbt Cloud settings |
| **Pre-aggregated facts** | Metric grain is coarser than fact grain | Build `bt_arr_quarterly` and point metric at it instead of `bt_arr_daily` |
| **Larger warehouse for MF** | Compile-time SQL is heavy | Set `snowflake_warehouse` on the semantic model |

### Anti-patterns

- Using MF for high-cardinality cross-joins ("ARR by every account by every day") — pre-aggregate first.
- Using MF for transactional lookups ("get the ARR for account X") — that's not a metric, that's a query.
- Defining a metric that only one consumer uses — just write the SQL in the consumer.

## 11. Failure modes — semantic layer

| Symptom | Root cause | Fix |
|---|---|---|
| `Metric not found: arr` | Metric defined but `dbt parse` not run | `dbt parse`; check `manifest.json` for the metric |
| `Cannot find join path between X and Y` | Missing entity in one of the semantic models | Add entity to both models; share a common foreign key |
| Metric returns 0 rows | Time spine doesn't cover the requested date range | Extend time spine; rebuild |
| BI tool sees stale data | MF cache hit | Disable cache for the dashboard or invalidate manually |
| Compile takes 30+ seconds | Too many joins computed at query time | Pre-aggregate; use `saved_query` with `exports` |
| Wrong currency in metric output | Measure expr uses `arr_usd_current` but consumer expected `arr_usd_hist` | Define two metrics: `arr_current` and `arr_hist` — never let the consumer guess |

## 12. Migration playbook — adopting the semantic layer

Phase 1 (week 1-2): inventory existing metrics
- List every "ARR" / "ACV" / "TCV" definition across BI tools
- Find duplicates / inconsistencies
- Propose one canonical definition

Phase 2 (week 3-4): build semantic models
- Pick the top 5 facts (e.g., `arr_line_categories`, `arr_product_categories`, `bt_acv_sku`)
- Define entities, dimensions, measures
- Validate with `mf validate-configs`

Phase 3 (week 5-6): build metrics
- Define ARR, ACV, TCV, NDR, GRR — the universal metrics
- Add ownership metadata
- Smoke test via CLI

Phase 4 (week 7-8): consumer migration
- Sigma: connect dbt SL as a data source
- Pick one dashboard; rewrite it on top of metrics
- Compare numbers against the old SQL — should match to the cent

Phase 5 (week 9+): deprecate old SQL definitions
- Mark old direct-table dashboards as deprecated
- Set sunset date
- Track migration progress (% of dashboards using SL vs direct SQL)

Done when 100% of finance dashboards consume via metrics, and the next "what is ARR?" question gets one answer.
