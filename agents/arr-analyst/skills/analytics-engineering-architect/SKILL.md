---
name: analytics-engineering-architect
description: >-
  Principal Analytics Engineering Architect — full-stack data platform architecture
  across ELT, lakehouse, semantic layer, data products, governance, observability,
  and FinOps. Covers modern data stack (ELT vs ETL, lakehouse vs warehouse, vendor
  selection), data mesh + data products + data contracts, data SLOs (freshness,
  completeness, accuracy) + observability (Monte Carlo, Sifflet, DataHub),
  semantic-layer architecture (MetricFlow vs Cube vs AtScale, headless BI), cost
  attribution + chargeback (FinOps for data), reverse ETL, change data capture,
  schema evolution patterns. Use when designing a data platform from scratch,
  evaluating tools/vendors, defining data SLOs, designing the semantic layer,
  setting up data observability, designing cost attribution, planning data product
  ownership, or making any cross-cutting analytics-engineering decision.
---

# Analytics Engineering Architect — Principal Level (2026)

Role: Principal Analytics Engineering Architect. You design the full modern
data platform: ingestion → transformation → semantic layer → consumption.
You pick vendors, design ownership boundaries, define SLOs, instrument cost
attribution, and orchestrate the cultural shift from "central data team" to
"data products owned by domain teams."

This SKILL.md is the index. Deep companion files:

- [`modern-data-stack.md`](modern-data-stack.md) — ELT vs ETL, lakehouse, vendor landscape, build-vs-buy
- [`data-mesh-and-products.md`](data-mesh-and-products.md) — Data mesh, data products, contracts, ownership
- [`slo-and-observability.md`](slo-and-observability.md) — SLAs/SLIs/SLOs for data, observability tooling
- [`semantic-layer-architecture.md`](semantic-layer-architecture.md) — MetricFlow vs Cube vs AtScale, headless BI
- [`cost-and-platform-economics.md`](cost-and-platform-economics.md) — FinOps for data, chargeback, unit economics

---

## When to use this skill (decision tree)

```
Analytics platform question
├── New platform / re-architect                  → §1 + modern-data-stack.md
├── Single-team to multi-team transition          → data-mesh-and-products.md
├── "Who owns this data?" / accountability        → data-mesh-and-products.md
├── Data quality SLA / SLO / observability        → slo-and-observability.md
├── "We have 5 ARR definitions" problem            → semantic-layer-architecture.md
├── Cost attribution / chargeback                  → cost-and-platform-economics.md
├── Vendor selection (CDC, observability, catalog) → §2 + modern-data-stack.md
└── Scaling beyond 1 dbt project / 1 team          → data-mesh-and-products.md
```

---

## §1. The modern data stack — components

```
┌─────────────────────────────────────────────────────────────────┐
│  Source systems (SaaS, OLTP, events, files)                     │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
        ┌────────────────────────────┐
        │  Ingestion (Fivetran,        │   ← extract + load
        │  Airbyte, Stitch, Debezium)  │
        └─────────────┬──────────────┘
                      │
                      ▼
        ┌────────────────────────────┐
        │  Storage / Compute           │   ← warehouse / lakehouse
        │  (Snowflake, Databricks,     │
        │   BigQuery, Redshift)        │
        └─────────────┬──────────────┘
                      │
                      ▼
        ┌────────────────────────────┐
        │  Transformation (dbt,        │   ← T in ELT
        │  Coalesce, SQLMesh)          │
        └─────────────┬──────────────┘
                      │
                      ▼
        ┌────────────────────────────┐   ┌──────────────────┐
        │  Semantic layer (MetricFlow, │   │  Catalog +        │
        │  Cube, AtScale, dbt SL)      │   │  Lineage          │
        └─────────────┬──────────────┘   │  (DataHub, Atlan, │
                      │                   │  OpenMetadata)    │
                      ▼                   └──────────────────┘
        ┌────────────────────────────┐   ┌──────────────────┐
        │  Consumption                 │   │  Observability    │
        │  (BI: Sigma, Tableau, Hex,   │   │  (Monte Carlo,    │
        │  Looker; reverse ETL: Hightouch│   │  Sifflet, Datafold)│
        │  Census)                      │   └──────────────────┘
        └────────────────────────────┘
```

### Vendor landscape (2026 snapshot)

| Layer | Top vendors | Open-source | Build (rare) |
|---|---|---|---|
| Ingestion | Fivetran, Airbyte, Stitch | Airbyte (OSS), Meltano | Custom Python (when source is unusual) |
| Warehouse / Lakehouse | Snowflake, Databricks, BigQuery, Redshift | DuckDB, ClickHouse, Trino | n/a |
| Transformation | dbt Cloud, Coalesce | dbt Core, SQLMesh, DataForm | n/a |
| Semantic layer | dbt SL (MetricFlow), Cube, AtScale, Looker LookML | Cube (OSS), MetricFlow (OSS) | n/a |
| Catalog / Lineage | Atlan, DataHub (Acryl), Alation, Collibra | DataHub, OpenMetadata, Marquez | n/a |
| Observability | Monte Carlo, Sifflet, Datafold, Bigeye | Soda, GreatExpectations | n/a |
| BI | Sigma, Tableau, Hex, Looker, ThoughtSpot, Power BI | Apache Superset, Metabase | n/a |
| Reverse ETL | Hightouch, Census | n/a | Custom Python (rare) |
| Orchestration | Airflow, Prefect, Dagster, dbt Cloud | Airflow, Prefect, Dagster | n/a |
| CDC | Debezium, Fivetran HVR | Debezium | n/a |

See [`modern-data-stack.md`](modern-data-stack.md) for selection criteria per layer.

---

## §2. Architecture decision framework

When asked to design or evaluate, surface these questions:

### Foundational

- What are the data volumes (rows/sec, GB/day, total TB)?
- What's the freshness SLA per use case?
- How many consumers (people, dashboards, services)?
- How many producers (source systems, teams)?
- What's the regulatory context (PII, GDPR, HIPAA)?

### Tooling

- What does the team already use successfully?
- What's the budget (annual platform spend)?
- What's the in-house expertise (SQL, Python, Spark, Scala)?
- What's the build vs buy bias?

### Organizational

- How many data teams / data engineers?
- Centralized vs federated ownership?
- Maturity (greenfield vs migrating)?
- Risk tolerance (innovate vs stabilize)?

### The senior move

After surfacing constraints, present 2-3 reference architectures with tradeoffs:

```
Option A: "Modern data stack" (Fivetran + Snowflake + dbt + Sigma)
  Pros: fastest time-to-value, mature tooling
  Cons: vendor lock-in, monthly recurring cost

Option B: "Lakehouse" (Databricks + Delta Lake + dbt + Tableau)
  Pros: open formats, ML-native
  Cons: more engineering required, less SQL-friendly

Option C: "Open" (Airbyte + DuckDB / Trino + dbt + Superset)
  Pros: low cost, no lock-in
  Cons: high ops burden, less polished UX
```

---

## §3. Data mesh — the organizational pattern

Data mesh decentralizes data ownership to **domain teams**.

### Principles (Zhamak Dehghani's original)

1. **Domain ownership** — data is owned by the team closest to its source / use
2. **Data as a product** — datasets are products (have owners, SLAs, consumers, docs)
3. **Self-serve platform** — central team provides infra, domain teams build on it
4. **Federated governance** — global standards + local autonomy

### When mesh is worth the complexity

| Trigger | Mesh value |
|---|---|
| ≥ 5 distinct domains | High |
| ≥ 50 data engineers | High |
| Central team is bottleneck | High |
| Single team < 10 engineers | Low (premature) |
| All data centralized works fine | Low (don't fix it) |

See [`data-mesh-and-products.md`](data-mesh-and-products.md) for implementation patterns.

### Data products

A data product has:
- **Owner** (named person + team)
- **SLA** (freshness, completeness, accuracy)
- **Public API** (contracted schema, semantic layer metrics)
- **Documentation** (purpose, grain, fields)
- **Discoverable** (in the catalog)
- **Observable** (monitored for breaches)
- **Versioned** (breaking changes have a migration path)

---

## §4. Data SLOs (Service Level Objectives)

Treat data like software: define SLOs, measure SLIs, alert on breaches.

### The 4 SLIs every data product needs

| SLI | Definition | Example target |
|---|---|---|
| Freshness | Time since last successful update | < 1 hour for ARR aggregate |
| Completeness | % of expected rows present | 99.5% of source rows reflected within 24h |
| Accuracy | Variance against external truth | < 0.1% variance vs Salesforce |
| Availability | Uptime of query endpoint | 99.9% |

### Defining SLOs

```yaml
# data_product_sla.yml
data_product: arr_line_categories
owner: ae_team
slack_channel: '#ae-team'
slo:
  freshness:
    target: 24h
    measurement: max(current_time - last_load_time)
  completeness:
    target: 99.5%
    measurement: matched_rows / expected_rows
  accuracy:
    target: 99.9% within $1
    measurement: 1 - sum(variance) / sum(amount)
```

See [`slo-and-observability.md`](slo-and-observability.md) for measurement + alerting patterns.

---

## §5. Semantic layer — the unifier

Without a semantic layer, every consumer defines metrics independently. With one, you have one definition, many consumers.

### The 2026 semantic layer choices

| Tool | Strengths | Weaknesses | Best for |
|---|---|---|---|
| **dbt SL (MetricFlow)** | Native dbt; YAML; strong typing | Newer; BI integration uneven | dbt-native shops |
| **Cube** | OSS; strong caching; many BI integrations | Separate from dbt; another tool | Multi-tool BI environments |
| **AtScale** | Enterprise; OLAP cubes | Heavy; expensive | Legacy BI migrations |
| **LookML (Looker)** | Mature; deep BI integration | Vendor lock-in | Looker shops |
| **dbt Semantic Layer + Cube hybrid** | Best of both | Complex setup | Maturing analytics orgs |

See [`semantic-layer-architecture.md`](semantic-layer-architecture.md) for selection + adoption playbook.

---

## §6. Observability — the visibility layer

### Tools

| Tool | What | Free tier |
|---|---|---|
| Monte Carlo | Schema/freshness/volume/quality monitoring + lineage | No |
| Sifflet | Similar to MC, dbt-native | No |
| Datafold | Data diff + monitoring | Limited |
| Soda | Quality testing | Yes (OSS) |
| Great Expectations | Data quality framework | Yes (OSS) |
| dbt source freshness | Built-in freshness checks | Yes |
| dbt tests | Built-in data quality | Yes |

### The observability stack

```
[Production data]
       │
       ▼
[Auto-detected schema changes]   ← Monte Carlo / Sifflet
[Freshness checks]                 ← dbt + observability tool
[Volume anomaly detection]         ← observability tool
[Data quality tests]               ← dbt + GE / Soda
[Custom assertions]                ← singular dbt tests
       │
       ▼
[Alerts → on-call / Slack]
[Lineage → why broke]
[Postmortem → preventive test]
```

See [`slo-and-observability.md`](slo-and-observability.md) for tool deep-dives.

---

## §7. Cost attribution — FinOps for data

Without cost attribution, the platform bill grows opaquely. With it, you can:
- Identify expensive consumers / queries / models
- Chargeback to business units
- Optimize incentives (teams own their cost)

### The attribution model

```
Total Snowflake bill
  = warehouse credits
  + storage cost
  + cloud services
  + data transfer (rare)

Attribute warehouse credits by:
  - query_tag (model, project, user, BI tool)
  - role
  - warehouse

Attribute storage by:
  - schema / database
  - retention setting
  - growth rate
```

### Chargeback patterns

| Model | How |
|---|---|
| Showback | Report cost per team, no chargeback (start here) |
| Soft chargeback | Cost reported, team has cost target |
| Hard chargeback | Cost charged to team budget |
| Reservation | Team buys X credits/month, overage charged extra |

See [`cost-and-platform-economics.md`](cost-and-platform-economics.md) for FinOps deep-dive.

---

## §8. Schema evolution — the cross-team pattern

Schema changes break consumers. Manage with:

### The 3 strategies

1. **Versioned APIs** — new schema = new version (e.g., `arr_v2`); consumers migrate explicitly
2. **Backward compat** — only add columns, never rename/drop; old consumers ignore new columns
3. **Contracts + deprecation** — public schema is contracted; breaking changes have deprecation_date

### Snowflake schema evolution mechanics

```sql
-- Backward-compat: ADD COLUMN
ALTER TABLE my_table ADD COLUMN new_col VARCHAR;

-- Rename (breaking) — handle via versioning, not in-place
-- DON'T: ALTER TABLE my_table RENAME COLUMN old_col TO new_col
-- DO: Create my_table_v2 with new schema; deprecate v1
```

### dbt schema evolution

```yaml
# In producer model
models:
  - name: finance_line_analytics
    latest_version: 2
    versions:
      - v: 1
        deprecation_date: 2026-12-31
      - v: 2
```

See `dbt-architect/mesh-and-contracts.md` for the full version mechanics.

---

## §9. CDC + event-driven analytics

For freshness < 5 min, batch dbt isn't enough. Patterns:

### Stream-based ingestion

| Tool | Use |
|---|---|
| Fivetran HVR | Log-based CDC from MySQL/Postgres/SQL Server |
| Debezium | Open-source CDC; Kafka backbone |
| AWS DMS | CDC for AWS data sources |
| Snowflake Streams + Tasks | Within-Snowflake CDC after initial load |

### Stream processing

| Tool | Use |
|---|---|
| Snowflake Streams + Dynamic Tables | Snowflake-native, no extra infra |
| Kafka + Flink | High-throughput, complex transformations |
| Spark Structured Streaming | Databricks-native |

### Reverse ETL

Push data from warehouse back to operational systems (Salesforce, Hubspot, etc.):

| Tool | Use |
|---|---|
| Hightouch | Modern SaaS, dbt-native |
| Census | Similar to Hightouch |

Common use case: ML score in warehouse → push to Salesforce as a custom field.

---

## §10. The senior platform checklist (annual review)

- [ ] All data products have named owners
- [ ] All public data products have contracts + SLAs
- [ ] All data products are in the catalog
- [ ] Data lineage covers source → dashboard for top 50 metrics
- [ ] Cost attribution coverage > 90% of warehouse credits
- [ ] Cost per data product is trended; alert on > 25% MoM growth
- [ ] Observability covers freshness + volume + schema for top 20 tables
- [ ] Average MTTR for data incidents < 4 hours
- [ ] Top 10 most-queried tables have < 5 sec P99 latency
- [ ] Documentation coverage > 70%
- [ ] Quarterly DR drill (replication, restore)
- [ ] Annual cost optimization sprint (right-size warehouses, retention, etc.)
- [ ] Quarterly platform roadmap aligned with business priorities

---

## See also

- `dbt-architect` skill — dbt-specific patterns
- `snowflake-architect` skill — Snowflake-specific patterns
- `dbt-platform-architect` skill — dbt cross-project / multi-environment topology
- `sr-developer` skill — engineering craft for analytics engineers
- `enterprise-metrics-finance-architect` skill — finance-domain metric architecture
