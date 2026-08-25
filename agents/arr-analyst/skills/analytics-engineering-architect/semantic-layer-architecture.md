# Semantic Layer Architecture

Reference companion to `analytics-engineering-architect/SKILL.md` §5.

## 1. Why the semantic layer matters

Without it, every consumer defines metrics independently. With it, you have ONE definition served to MANY consumers.

```
Without SL:                     With SL:

[Snowflake table]              [Snowflake table]
       │                              │
   /───┴────────\                     ▼
   │            │             [Semantic layer]
[Tableau]   [Sigma]           │  (one metric def)
ARR = sum(x)  ARR = sum(y)    │
   different!                  │
                              ┌┴────────────────┐
                              │                  │
                          [Tableau]          [Sigma]
                          (same number)      (same number)
```

The senior insight: the semantic layer is **the canonical metric registry**. It's where business defines, owns, and governs metrics.

## 2. Tool comparison (2026)

| Tool | Architecture | Strengths | Weaknesses |
|---|---|---|---|
| **dbt Semantic Layer (MetricFlow)** | Compiles to SQL on-the-fly via MF service | Native dbt; YAML; strong typing; growing BI integration | Newer; some BI tools have weaker integration |
| **Cube** | Caching SL service; many BI connections | OSS option; strong caching; broad BI compat | Separate from dbt (sync overhead) |
| **AtScale** | OLAP cube generation; pre-aggregation | Enterprise scale; complex hierarchies | Heavy; expensive; learning curve |
| **Looker (LookML)** | LookML defines metrics; serves Looker | Mature; deep BI integration | Vendor lock-in (Looker-only) |
| **ThoughtSpot Liveboards** | Search-native semantic | Search/NLP-first UX | Different paradigm |
| **MicroStrategy** | Enterprise OLAP | Legacy enterprise scale | Old paradigm |

## 3. dbt Semantic Layer (MetricFlow) — deep dive

See `dbt-architect/semantic-layer.md` for the dbt-side configuration. Architecture:

```
dbt project
├── models/              (the data tables)
├── semantic_models.yml  (semantic models = wrappers over tables)
├── metrics.yml          (metric definitions)
└── saved_queries.yml    (pre-defined consumer queries)
        │
        ▼
dbt Cloud (or Core)
        │
        ▼
MetricFlow service (compiles requests to SQL)
        │
        ▼
Snowflake (executes SQL)
        │
        ▼
BI tools / APIs (consume metrics)
```

### Strengths

- Native to dbt (one project, one git repo)
- Metric definitions are version-controlled SQL+YAML
- Strong typing (enforced via dbt parser)
- Free tier for OSS via `mf` CLI
- Growing BI integrations (Sigma, Hex, Tableau via JDBC, ThoughtSpot)

### Weaknesses

- No caching out-of-the-box (uses Snowflake result cache)
- BI integrations vary in maturity (Tableau is awkward; Hex/Sigma native)
- Newer; smaller community

### When to choose dbt SL

- You already use dbt
- Your BI is Sigma / Hex (best integration)
- You value version-controlled metric definitions
- You don't need sub-second cache (Snowflake handles it OK)

## 4. Cube — deep dive

Cube is a SL service that sits between data warehouse and BI tools.

```
dbt (transforms)
   │
   ▼
Snowflake (tables)
   │
   ▼
Cube (caches + serves metric API)
   │
   ▼
BI tools (Tableau, Power BI, custom)
```

### Strengths

- OSS option (Cube Core) + Cloud
- Strong caching layer (sub-second response on cached queries)
- Many BI connections (SQL API + REST + GraphQL + WebSocket)
- Mature embedded analytics support

### Weaknesses

- Separate from dbt (you maintain dbt models + Cube schema)
- Sync overhead (when dbt schema changes, update Cube)
- Cube schema language is its own DSL

### When to choose Cube

- Multi-tool BI environment (each tool needs the same metrics)
- Embedded analytics in a customer-facing product
- Sub-second cache requirement
- You want a vendor-neutral semantic layer

## 5. AtScale — deep dive

OLAP cube generator. Pre-aggregates at multiple grains.

### Strengths

- Enterprise scale (handles BB rows)
- Complex hierarchies (custom drill-downs)
- Strong governance (metric approval workflows)

### Weaknesses

- Heavy + expensive
- Steep learning curve
- Pre-aggregation = potentially stale data

### When to choose AtScale

- Very large enterprise (Fortune 100)
- Need OLAP cube semantics (multi-dim drill-down)
- Legacy MicroStrategy / SAS migration

## 6. Looker LookML — the incumbent

If you already use Looker, LookML is your SL. It defines:
- Views (over tables)
- Explores (joinable views)
- Measures (aggregated metrics)
- Dimensions (filterable attributes)

Strengths: deep Looker integration, mature, governance built-in.
Weaknesses: vendor lock-in. Other BI tools can't easily consume LookML.

The 2026 trend: orgs adopting headless SL (dbt SL, Cube) + using Looker (or others) as the BI front-end only.

## 7. Headless BI — the architectural shift

Traditional BI: each tool has its own metric layer (Tableau measures, Looker LookML).

Headless BI: metric layer is separate from BI tool. Multiple BI tools consume the same metrics.

```
Traditional:               Headless:

dbt + Snowflake            dbt + Snowflake
       │                          │
       ├──► Tableau (own SL)      ▼
       ├──► Looker (LookML)       Headless SL (MF/Cube)
       └──► Sigma (own SL)        │
                                  ├──► Tableau
                                  ├──► Looker
                                  └──► Sigma
```

The headless approach:
- One metric definition serves all BI tools
- Easier to add/swap BI tools
- Governance lives with metrics, not tools

## 8. The senior architecture decision

### When you need a SL

- 5+ business-critical metrics
- 3+ consumers (dashboards, notebooks, services)
- "What is ARR?" question is answered differently by different teams

### When you don't need a SL

- < 3 metrics, all in one team
- Pure operational reporting (raw data → spreadsheet)
- BI tool's built-in measures suffice

### Selecting between dbt SL, Cube, etc.

```
Already on dbt + lightweight BI use?
├── Yes
│   └── dbt SL (MetricFlow) — natural extension
├── Need multi-tool BI?
│   └── Cube — broader integration
├── Need sub-second cache for embedded analytics?
│   └── Cube — strongest caching
├── Need OLAP cube semantics (multi-dim drill)?
│   └── AtScale or kept-LookML
└── Already on Looker?
    └── Stick with LookML; consider headless if leaving Looker
```

## 9. Metric definition discipline

Regardless of tool, every metric definition needs:

| Element | Why |
|---|---|
| **Business definition** | Plain English for non-data folks |
| **Formula** | The math |
| **Grain** | What level does it aggregate to? |
| **Filters** | What's included / excluded? |
| **Currency basis** | Which variant (current, hist, actual)? |
| **Owner** | Who decides what this means? |
| **Consumers** | Who uses it? |
| **Source of truth** | Which model produces it? |
| **Validation** | How do we know it's right? |

Example for ARR:

```yaml
metric:
  name: arr
  business_definition: |
    Annualized recurring revenue. Sum of all active contracts'
    annual value, with current FX rates.
  formula: SUM(arr_usd_current) WHERE as_was_date = latest
  grain: aggregable to any dimension
  filters:
    include: stage_code = '9' (Closed Won)
    exclude: arr_category = 'Churn'
  currency: USD_CURRENT (latest FX)
  owner: finance_analytics_team
  consumers:
    - sigma_arr_dashboard
    - tableau_executive_review
    - hex_ad_hoc_analyst
  source_of_truth: arr_line_categories model
  validation: |
    Tied out monthly to Salesforce Opportunity Amount sum,
    < $1 variance per fiscal quarter.
```

## 10. Adoption playbook

Phase 1 (weeks 1-2): inventory existing metrics

- List every "ARR" / "ACV" / "TCV" / "NDR" definition across BI tools
- Find duplicates and inconsistencies
- Propose ONE canonical definition per metric

Phase 2 (weeks 3-4): select tool + build foundation

- Decide: dbt SL, Cube, or other
- Build semantic models over the top 5 facts
- Define entities, dimensions, measures
- Validate via CLI / API

Phase 3 (weeks 5-6): define + smoke-test metrics

- Define ARR, ACV, TCV, NDR, GRR
- Run via CLI: `mf query --metrics arr --group-by fiscal_quarter`
- Compare against legacy SQL definition — should match

Phase 4 (weeks 7-10): consumer migration

- One dashboard at a time, migrate from raw SQL to metric API
- Validate numbers match
- Decommission the raw SQL definition

Phase 5 (months 4+): governance + expansion

- Quarterly metric review with finance / business teams
- Add new metrics as needs arise
- Track adoption: % of dashboards on SL vs direct SQL

Done when: 100% of finance dashboards consume via metrics, and every "what is ARR?" question returns the same number.

## 11. Anti-patterns

| Anti-pattern | Why bad | Better |
|---|---|---|
| Defining metrics in 3 places (dbt SL, Cube, LookML) | Drift inevitable | Pick ONE SL; deprecate others |
| Metrics in BI tool measure (Tableau) | Tied to one tool | Define in SL; consume via JDBC |
| 100+ metrics for a small org | Maintenance burden | Start with 10-20 critical metrics |
| Metric without an owner | No one to call when wrong | Every metric has `meta.owner` |
| Metric definition without business sign-off | Wrong = embarrassing | Finance owner signs every metric |
| Versioning every metric change | Reviewer fatigue | Only version breaking changes |
| Pre-aggregating before SL | Loses flexibility | Let SL aggregate; pre-agg only for cost |
| SL adoption without migration plan | Old SQL definitions stay alive | Deprecation timeline for legacy |

## 12. Operational considerations

### Performance

- For high-traffic dashboards: enable caching (Cube) or use `saved_queries.exports` (dbt SL)
- Pre-aggregate facts that are queried at coarse grain (e.g., `bt_arr_daily` for daily metric requests)
- Monitor SL query times; alert on regression

### Governance

- Metric changes go through PR review like code
- Finance owner signs off on metric changes
- Catalog metric definitions (DataHub, Atlan)
- Annual metric audit: which are unused? Which are wrong? Which need versioning?

### Documentation

- Metric definition in the SL
- Business definition in plain English
- Validation query for "is this right?"
- Owner contact
- Consumer list

### On-call

- When a metric returns 0 / NULL / wrong number, who's paged?
- The data product owner of the source fact, OR
- The metric owner (finance for ARR, marketing for MQL)
