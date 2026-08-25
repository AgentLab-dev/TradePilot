# Modern Data Stack — ELT, Lakehouse, Vendor Selection

Reference companion to `analytics-engineering-architect/SKILL.md` §1 and §2.

## 1. ELT vs ETL — the principal-level decision

| | ETL (traditional) | ELT (modern) |
|---|---|---|
| Order | Extract → Transform (in tool) → Load (warehouse) | Extract → Load (warehouse) → Transform (in warehouse) |
| Where transformation runs | Custom servers (Informatica, Talend) | The warehouse itself |
| Schema rigidity | Schema-on-write | Schema-on-read OR schema-on-write |
| Reprocessing | Slow (full re-extract) | Fast (re-run SQL) |
| Latency | High (multi-step) | Low (single hop to warehouse) |
| Cost driver | License + compute servers | Warehouse compute |
| Best for (2026) | Legacy systems already on ETL | Everything new |

The 2026 reality: ELT won. The warehouse / lakehouse is the transformation engine; pure ETL is legacy.

### The ELT formula

```
Source → CDC / batch extract → Land in warehouse (bronze) → Transform with dbt (silver/gold) → Serve via BI / SL
```

Why this won:
- Warehouses scaled to handle transformation cheaply (Snowflake auto-scale)
- SQL skills are universal; Talend/Informatica are not
- dbt + git made transformation code reviewable + testable
- Schema-on-read in the bronze layer reduces ingestion fragility

## 2. Lakehouse vs Warehouse

| | Warehouse (Snowflake, BigQuery) | Lakehouse (Databricks, Iceberg) |
|---|---|---|
| Storage | Proprietary | Open formats (Iceberg, Delta) |
| Compute | Built-in | Built-in (multi-engine option) |
| Schema flexibility | Structured + semi-structured | All including unstructured |
| ML | Snowpark (good) | Native (best in class) |
| BI | Strong | Improving |
| Cost | Predictable | Highly variable |
| Open / portable | Less (improving with Iceberg) | Yes |
| Best for | SQL-first analytics + light ML | ML-first + multi-engine + big data |

### Convergence (2026)

The boundary is blurring:
- Snowflake added Iceberg, Hybrid Tables, Snowpark Container Services
- Databricks improved SQL endpoint, added Unity Catalog (governance)
- Both support semantic layers

### Decision framework

| Need | Choose |
|---|---|
| SQL-first analytics | Warehouse (Snowflake) |
| ML/DL heavy | Lakehouse (Databricks) |
| Cross-engine open data | Iceberg-on-anything |
| Cost predictability critical | Warehouse |
| Multi-cloud required | Lakehouse (Databricks) or BigQuery + Snowflake (multi) |
| Cost minimization (small scale) | DuckDB + open formats |

## 3. Ingestion — selecting CDC / ELT tools

### Tools matrix

| Tool | Pricing | Best for | Skip when |
|---|---|---|---|
| **Fivetran** | Volume-based, premium | SaaS sources (Salesforce, NetSuite); reliability | Cost sensitive; need low-volume sources |
| **Airbyte** | Free (OSS) or Cloud | OSS-first orgs; long-tail connectors | Need enterprise SLAs without paying |
| **Stitch** | Per row | Smaller scale | High-volume; deeper transforms |
| **Debezium** | Free (OSS) | Database CDC (Postgres, MySQL, SQL Server) | Non-DB sources |
| **AWS DMS** | AWS-only pricing | AWS shops | Multi-cloud |
| **Custom Python** | Engineering time | Unique source; tight budget | Standard SaaS sources |

### Selection criteria

1. **Connector availability** — does the tool support your sources today?
2. **Connector reliability** — how often do connectors break? (Check vendor changelogs)
3. **Cost model** — volume-based (Fivetran) vs flat (OSS) — model your actual usage
4. **Operational burden** — managed (Fivetran) vs self-hosted (Airbyte OSS)
5. **CDC vs batch** — most analytical needs are fine with batch; CDC for sub-minute SLA

### Fivetran-specific patterns

For Salesforce / Apttus (our env):
- Fivetran handles ~300 tables, ~1-2 min latency for incremental
- Stages into `BASE_PROD.SALESFORCE.*` with `_FIVETRAN_SYNCED` timestamp
- Failures alert via `account_usage` or Fivetran's own alerts

### Custom connector decision

Build custom only if:
- Source is unique (proprietary internal system)
- Existing connectors have a deal-breaker (missing field, broken auth)
- Volume is low + engineering capacity exists

For everything else, buy.

## 4. Transformation — dbt is the answer (almost always)

In 2026, dbt is the de facto standard for warehouse transformation:

| Need | Tool |
|---|---|
| Standard ELT transforms | dbt Core or dbt Cloud |
| SQL-first with strict typing | SQLMesh (better backfill semantics) |
| Visual transformation (no SQL skills) | Coalesce |
| Enterprise legacy (Informatica) | Migrate to dbt |

### dbt Core vs dbt Cloud

| | dbt Core | dbt Cloud |
|---|---|---|
| Pricing | Free (OSS) | Paid (per dev seat) |
| Hosting | Self-hosted | Fully managed |
| IDE | Local (VS Code) | Browser-based |
| CI/CD | Build yourself (GitHub Actions) | Built-in jobs + UI |
| Semantic Layer | Yes (CLI) | Yes (with API access) |
| Best for | Small teams, low budget | Teams > 5, want managed |

### SQLMesh — the contender (2026 maturity)

SQLMesh is dbt-compatible with stronger semantics:
- **Virtual environments** — preview changes without running
- **State-based** — knows what's changed; rebuilds correctly
- **Backfill-friendly** — better semantics for re-processing windows
- **Forward-only schema migrations** — first-class

When SQLMesh wins: large-scale backfills, very large DAGs (> 1000 models). Otherwise dbt.

## 5. Semantic layer — see dedicated file

See [`semantic-layer-architecture.md`](semantic-layer-architecture.md).

## 6. Catalog / Lineage — selecting tools

| Need | Tool |
|---|---|
| Lineage + discovery + ownership | Atlan, DataHub, Alation |
| OSS / self-host | DataHub (Acryl OSS), OpenMetadata, Marquez |
| Compliance / classification | Collibra, Alation |
| Snowflake-native | Snowflake Horizon (built-in) |

### Selection criteria

1. **Auto-extraction** — does it auto-parse dbt manifest + Snowflake metadata + BI metadata?
2. **Column-level lineage** — not just table-level (essential for impact analysis)
3. **Search quality** — finding the right dataset by description
4. **BI integration** — does it pull from Sigma / Tableau / Looker?
5. **Workflow integration** — Slack notifications, Jira tickets

### Bootstrap pattern

Start with Snowflake Horizon (built-in, free). When you need:
- Cross-cloud lineage (Snowflake + Databricks)
- Better BI integration
- Manual annotations

Add a dedicated catalog (DataHub OSS or Atlan).

## 7. Observability — selecting tools

See [`slo-and-observability.md`](slo-and-observability.md).

## 8. BI tools — selecting

| Tool | Strengths | Weaknesses | Best for |
|---|---|---|---|
| **Sigma** | Spreadsheet-like, fast, scales to BB rows | Newer, less mature | Finance / business analytics |
| **Tableau** | Visualization quality, mature | Expensive, complex governance | Visualization-heavy analytics |
| **Looker** | LookML semantic layer, strong governance | Expensive, learning curve | Enterprise with consistent metrics |
| **Hex** | Notebooks + dashboards, dbt SL native | Newer, smaller install base | Data team + analyst hybrid |
| **ThoughtSpot** | Search-based, AI-first | Different paradigm | Self-service for non-data users |
| **Power BI** | MS shop default, low cost | Single-cloud (Azure-leaning) | MS enterprise environments |
| **Mode** | SQL-native, modern | Smaller than competitors | SQL-fluent analyst teams |
| **Superset (OSS)** | Free, decent | Operationally heavy | OSS-first orgs |
| **Metabase (OSS)** | Free, easy to use | Limited scale | Startups, smaller teams |

### Selection criteria

1. **Performance at your scale** — test with your actual data sizes
2. **Semantic layer integration** — does it consume dbt SL / Cube / LookML cleanly?
3. **Governance** — who can publish, who can edit, version control on dashboards
4. **User adoption** — IT-friendly vs business-user-friendly
5. **Total cost of ownership** — license + admin time + training

### Anti-pattern: one BI to rule them all

Different consumers have different needs. It's OK to have:
- Looker for executive dashboards (governed)
- Hex for exploratory analyst work
- Tableau for product analytics

As long as ALL of them consume the same semantic layer metrics.

## 9. Orchestration — Airflow vs Prefect vs Dagster

| | Airflow | Prefect | Dagster |
|---|---|---|---|
| Maturity | Most mature | Mature | Less mature |
| Learning curve | Steep | Moderate | Moderate |
| Hybrid cloud | OK | Strong | Strong |
| Python-native | Yes | Yes (modern Python) | Yes (data-centric) |
| dbt integration | Plugin | Strong | First-class (Software-Defined Assets) |
| Best for | Standard ETL pipelines | Modern Python apps | dbt-heavy / data-asset-centric |

### When you don't need orchestration

If your entire pipeline is dbt + Snowflake tasks, you may not need a separate orchestrator. dbt Cloud has built-in scheduling.

You need a real orchestrator when:
- Multi-tool pipelines (dbt + Python + Spark + ML)
- Complex dependencies across teams / tools
- Need fine-grained retry / backfill control

## 10. The reference architectures (2026)

### Reference A: Pure modern data stack (most common)

```
Salesforce / NetSuite / etc.
    │  Fivetran (batch, 1 hr)
    ▼
Snowflake (BASE_PROD)
    │  dbt Cloud (daily build)
    ▼
Snowflake (FINANCE_PROD, marts)
    │  dbt Semantic Layer
    ▼
Sigma / Hex / Tableau
```

Cost driver: Snowflake compute + Fivetran rows + dbt Cloud seats.
Annual budget: $200k-$2M depending on scale.

### Reference B: Lakehouse-centric

```
Sources → Kafka → Databricks (Bronze Delta)
              → Databricks (Silver, dbt)
              → Databricks (Gold, dbt)
              → Tableau / dashboards
```

Cost driver: Databricks DBUs (compute) + storage.
Annual budget: $300k-$3M.

### Reference C: Hybrid (multi-tool)

```
Operational data (CDC) → Snowflake
ML / unstructured → Databricks (Iceberg)
Both → dbt SL → Sigma + Hex
```

Cost driver: both warehouses. Complexity premium ~30%.

### Reference D: Open / cost-conscious

```
Sources → Airbyte (self-hosted) → DuckDB / Postgres
                                → dbt Core
                                → Superset / Metabase
```

Cost driver: engineering time (high) + infra (low).
Annual budget: $50k-$200k + 1-2 FTE engineering.

## 11. Build vs Buy framework

| Question | Build | Buy |
|---|---|---|
| Is this our core differentiator? | Yes | No |
| Will requirements change in 6 months? | Maybe | No |
| Does an existing tool meet 80%+ of needs? | No | Yes |
| Can we afford 2-5× the build estimate? | Yes | No |
| Do we have 2+ FTE to maintain it? | Yes | No |
| Is the buy option vendor-locking us? | Less risk | Yes (acknowledge) |

Default: BUY for everything in the modern data stack. The cost of vendor lock-in is rarely worse than the cost of maintaining DIY infrastructure.

Build only for: bespoke business logic, unique competitive advantage, very high scale / low margin where vendor cost > engineering cost.

## 12. Migration patterns

### Migrating from ETL to ELT

Phase 1: Land raw data in warehouse (no transformation yet)
Phase 2: Run old ETL + new dbt in parallel; reconcile
Phase 3: Switch consumers to dbt outputs
Phase 4: Decommission ETL

### Migrating between warehouses (Snowflake ↔ BigQuery ↔ Databricks)

Phase 1: Set up dual-write (both warehouses ingest the same sources)
Phase 2: Port dbt models (most dbt SQL is portable with minor tweaks)
Phase 3: Reconcile model outputs (row count + sum + sample compare)
Phase 4: Migrate consumers (BI tools, semantic layer)
Phase 5: Decommission old warehouse

Budget 6-18 months for a full warehouse migration of an enterprise platform.

### Migrating from monolith to mesh

See `data-mesh-and-products.md`.

## 13. Anti-patterns

| Anti-pattern | Why bad | Better |
|---|---|---|
| Picking tools because they're trendy | Tech debt | Pick tools the team can maintain |
| 7+ tools in the stack | Integration hell | Consolidate; one tool per layer |
| Custom ETL when SaaS exists | Engineering burn | Buy unless truly unique |
| No semantic layer ("we'll add later") | Metric drift entrenched | Adopt early |
| No catalog ("we know where things are") | Tribal knowledge brittle | Add catalog before team > 10 |
| Snowflake as the only environment (no dev) | Untested changes hit prod | dev/qa/prod isolation |
| Migrating everything in one go | Bet-the-company risk | Strangle-fig pattern |
| Tool selection without POC | Bad fit discovered late | 4-week POC with real data |
