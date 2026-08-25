---
name: dbt-architect
description: >-
  Principal dbt Architect for enterprise platforms (400+ models, multi-project mesh,
  cross-team contracts, semantic layer). Covers dbt-mesh (groups, access modifiers,
  model versions, contracts), dbt-fusion engine, microbatch incremental, dbt State
  / defer mechanics, unit tests, MetricFlow / Semantic Layer, custom materializations,
  Jinja meta-programming, adapter dispatch, slim CI design, run-time tuning, and
  failure-mode catalogs. Use when designing a new dbt project, splitting an existing
  monolith into a mesh, adding model contracts, introducing the semantic layer,
  writing a custom materialization or adapter dispatch, debugging slim-CI false
  positives, sizing thread pools, or making any architecture-level dbt decision.
---

# dbt Architect — Principal Level (2026)

Role: Principal Data Architect for enterprise dbt platforms. You design the project
shape, the cross-team contracts, the semantic layer, and the build-time + run-time
properties. You make tradeoffs explicit (cost vs latency vs schema-evolution risk),
choose materializations from a quantitative basis, and write Jinja that other
engineers can read three years from now.

This SKILL.md is the index + decision frameworks. Deep companion files:

- [`mesh-and-contracts.md`](mesh-and-contracts.md) — dbt-mesh, groups, access modifiers, contracts, versions, governance
- [`microbatch-and-state.md`](microbatch-and-state.md) — microbatch incremental, dbt State, defer, slim CI mechanics
- [`unit-tests-and-quality.md`](unit-tests-and-quality.md) — unit tests, fixtures, custom generic tests, test generators
- [`semantic-layer.md`](semantic-layer.md) — MetricFlow, semantic models, metrics, saved queries, time spines
- [`macros-and-materializations.md`](macros-and-materializations.md) — custom materializations, adapter dispatch, advanced Jinja, run-time helpers

---

## When to use this skill (decision tree)

```
Architecture question raised
├── Project shape (folders, layers, naming)            → §1 + dbt-patterns.md
├── Cross-project / cross-team                          → §3 + mesh-and-contracts.md
├── Contracts / schema evolution / breaking changes     → mesh-and-contracts.md
├── Materialization choice (table / view / incr / DT)   → §2 + microbatch-and-state.md
├── Incremental strategy choice + late arrivals         → microbatch-and-state.md
├── Test design + refactor coverage                     → unit-tests-and-quality.md
├── Metric definition + reuse + BI integration          → semantic-layer.md
├── Custom Jinja / materialization / adapter behavior   → macros-and-materializations.md
├── CI/CD design (state:modified+, defer, manage_state) → microbatch-and-state.md
└── Performance (threads, ephemeral cost, defer ratios) → §5 + macros-and-materializations.md
```

For pure data-quality debugging (duplicates, fanout, NULL bugs), branch to the
`dbt-model-debugger` skill instead.

---

## §1. Project shape & DAG topology

### Layer boundaries (enforced)

```
source()  →  stg_*  →  int_*  →  fact_*/dim_*/bt_*  →  bv_* / metric_*
```

| Layer | Materialization default | Reads from | Writes to | Tests |
|---|---|---|---|---|
| `source()` | n/a | external (raw/landing) | — | `freshness`, schema |
| `stg_*` | view (or table if SCD2 anchor) | only `source()` or cross-project `ref()` | `int_*`, `bt_*` | `unique` + `not_null` on PK, rename validation |
| `int_*` | ephemeral (small) or table (re-used) | `stg_*` or other `int_*` | `bt_*` only | grain test |
| `bt_*` / `fact_*` / `dim_*` | incremental table | `int_*` (rarely `stg_*`) | `bv_*`, metrics | full PK + grain + business rules |
| `bv_*` | view | `bt_*` only, zero logic | BI / dashboards | none (lightweight) |

**Hard rules** (enforced by `state:modified+` CI tests):
- `stg_*` MUST NOT reference another `stg_*` or any `int_*` / `bt_*`.
- `bt_*` MUST NOT reference another `bt_*`. Fan-in at `int_*`, not at `bt_*`.
- `bv_*` MUST NOT contain `JOIN`, `WHERE`, `GROUP BY`, or `CASE`. View = projection only.
- Max 4 hops from `source()` to final `bt_*`. If you need more, fan-out an `int_*`.

### DAG shape patterns

| Pattern | When to use | How |
|---|---|---|
| **Fan-in funnel** | 5+ staging models → 1 fact | Collapse joins in a single `int_*`; never `JOIN` directly in `bt_*` |
| **Fan-out hub** | 1 `bt_*` powers 10+ views | `bt_*` as the wide table; many thin `bv_*` projections |
| **Slowly evolving star** | Dimension changes daily | SCD2 `stg_*_as_was`, joined at as-of-date in `int_*` |
| **Microbatch event stream** | High-volume facts (>10M/day) | `microbatch` incremental on `event_time` (see microbatch-and-state.md) |
| **Mesh boundary** | Cross-team handoff | Producer `bt_*` with `contract: enforced`, consumer ref via `ref('proj','model')` |

### Naming conventions

```
{type}_{domain}_{subject}_{modifier}

stg_em_int_agree_base.sql              # staging, em domain, intermediate group, agree subject
stg_em_agreement_as_was.sql            # staging, em domain, SCD2 as-of-date wrapper
bt_sku_arr_categories.sql              # business table, sku grain, arr_categories subject
arr_product_categories.sql             # aggregate, product grain (post-IA naming)
finance_line_analytics.sql             # business table, ALI grain (canonical name)
bv_product_net_dollar_retention.sql    # business view, product grain, NDR subject
```

For project-scale naming consistency, see `dbt-patterns.md` in `data-analytics-architect`.

---

## §2. Materialization decision matrix

Quantitative basis for choosing materialization. Pick the row that matches your
workload, then read the column.

| Pattern | Read freq | Write freq | Row count | Choose |
|---|---|---|---|---|
| Lookup table | Hourly+ | Daily | <100K | `table` (regular) |
| Reference data | Constant | Weekly | <10M | `table` |
| Slow dimension | Constant | Daily | <50M | `table` |
| Slow dimension SCD2 | Daily | Daily | <50M / valid | `incremental` `merge` on (surrogate_key, valid_from) |
| Append-only event fact | Daily | Streaming | >100M total | `microbatch` `event_time=event_ts batch_size=day` |
| Late-arriving event fact | Daily | Streaming | >100M total | `microbatch` with `lookback=N days` |
| Snapshot fact (point-in-time) | Daily | Daily | <100M / snapshot | `incremental` `delete+insert` partitioned on snapshot date |
| Heavy aggregate (re-built daily) | Hourly | Daily full refresh | <500M | `table` with `snowflake_warehouse=heavy` |
| Heavy aggregate (cumulative) | Hourly | Daily delta | >1B | `incremental` `merge` + clustering key |
| Shared product datamart (cross-team) | Hourly | Hourly | varies | `incremental` + `contract: enforced` |
| Dashboard view | On-demand | n/a | derived | `view` (no `bv_*` business logic ever) |
| Computed metric in BI | On-demand | n/a | derived | semantic layer `metric:` (no materialization at all) |
| Sub-second BI lookup | <100ms | Hourly | <10M | `view` over Snowflake `dynamic table` (let DT own refresh) |
| Cross-engine open data | Mixed | Hourly | >1TB | Iceberg-backed `table` (Snowflake-managed) |

**Materializations to AVOID by default:**
- `ephemeral` on anything queried by 5+ downstream models — re-compiles the SQL into each consumer, blowing up compile time and breaking the query profile.
- `materialized_view` (Snowflake MV) on dbt-managed objects — dbt has no native ownership of MVs and can't refresh-trigger; use Dynamic Tables instead.
- `dynamic_table` materialization (dbt 1.7+) for anything that needs lineage tests — DT refresh is decoupled from dbt run, so tests fire against stale data.

---

## §3. dbt-mesh & contracts (the principal-level shift)

dbt-mesh is the unit of cross-team organization. Read [`mesh-and-contracts.md`](mesh-and-contracts.md) for the full pattern reference. Quick framework here.

### When to split into projects

Split into a separate dbt project (mesh node) when **any one** of these is true:

- The model set has a distinct deploy cadence (e.g., raw SCD2 = hourly, finance = daily).
- The model set is owned by a different team with their own PR/review process.
- The model set is shared by 3+ downstream consumers with breaking-change risk.
- The model set's `state:modified+` blast radius is >50% of the monolith.
- CI build time on the monolith exceeds 30 minutes for typical PRs.

### Mesh ownership matrix (example from our env)

| Project | Owner | Schemas | Cross-project consumers |
|---|---|---|---|
| `eda_dbt_base` | Platform team | `base_prod.salesforce`, `base_prod.redshift_history` | `eda_dbt_gtm`, `eda_dbt_em`, `eda_dbt_cx` |
| `eda_dbt_common` | Platform team | `base_prod.common` | `eda_dbt_em`, `eda_dbt_gtm` |
| `eda_dbt_gtm` | GTM team | `sales_prod.managed` | `eda_dbt_em` |
| `eda_dbt_em` | Finance + AE | `finance_prod.{managed,aggregations,data_products}`, `finance_int_prod.stage` | external BI |
| `eda_dbt_cx` | CX team | `cx_prod.*` | external BI |

### Contracts (mandatory for cross-project handoffs)

```yaml
# In producer project: eda_dbt_em/models/finance/.../finance_line_analytics.yml
models:
  - name: finance_line_analytics
    config:
      contract:
        enforced: true
    columns:
      - name: as_was_date
        data_type: date
        constraints: [{type: not_null}, {type: primary_key}]
      - name: agreement_line_item_id
        data_type: varchar
        constraints: [{type: not_null}]
      - name: arr_usd_current
        data_type: number(38,2)
```

A contract enforcement makes dbt **fail compile** if the SQL output schema does not match the YAML — column count, names, types, constraints. This is your guardrail against silent downstream breakage.

### Versions for breaking changes

When you must change a contracted column (rename, drop, type change), version the model instead of editing it:

```yaml
models:
  - name: finance_line_analytics
    latest_version: 2
    versions:
      - v: 1
        deprecation_date: 2026-12-31
      - v: 2
        defined_in: finance_line_analytics_v2   # SQL file
```

Consumers `ref('finance_line_analytics', v=1)` until they migrate. After the deprecation date, the v1 alias errors at parse time.

### Groups + access modifiers

```yaml
# models/finance/_groups.yml
groups:
  - name: finance_internal
    owner: {name: AE team, email: [REDACTED_EMAIL]}

# Per model:
models:
  - name: int_agree_enriched
    group: finance_internal
    access: private    # only models within finance_internal group may ref()
```

Access values: `private` (group only), `protected` (project only — default), `public` (cross-project).
A `state:modified+` test enforces these at parse time.

---

## §4. Testing strategy (test pyramid)

| Level | Type | Purpose | Coverage |
|---|---|---|---|
| L1 — Static | `unique`, `not_null`, `relationships`, `accepted_values` | Schema sanity | 100% of PKs + key joins |
| L2 — Singular | `tests/assert_*.sql` | Specific business rule (one model, one rule) | All business-critical invariants |
| L3 — Generic custom | `tests/generic/test_*.sql` | Reusable rule across models | Schema-test parameterized |
| L4 — Unit tests | `unit_tests:` block in YAML | Logic test with mocked input | High-stakes transformations (currency conv, ARR categorization, SSR detection) |
| L5 — Snapshot comparison | dbt audit-helper macros | Refactor recon (before vs after) | Every refactor PR |

Unit tests deserve a dedicated companion file → [`unit-tests-and-quality.md`](unit-tests-and-quality.md).

---

## §5. Performance — quantitative basis

### Thread tuning

```
optimal_threads = min(
    warehouse_concurrency_limit,           # XS=8, S=16, M=32, L=64 typical
    cpu_count_local * 2,                   # only matters for ephemeral compile cost
    number_of_independent_dag_branches      # see `dbt ls --select state:modified+ --output json`
)
```

For `dbt-snowflake` with 400+ models on an L warehouse, set `threads: 24` for prod batch. Going higher does not help (warehouse becomes the bottleneck, not the dbt scheduler).

### Ephemeral cost math

An `ephemeral` model with N downstream consumers compiles the SQL **N times**, inlined as a CTE in each consumer. Cost:

```
total_query_chars(epehemeral_model) = ephemeral_chars × N_consumers
```

Snowflake has a 1MB query text limit. If `ephemeral_chars × N > 200KB`, the consumer query becomes hard to read in the profile UI and can cause planner regression. Convert to `table` when N ≥ 5.

### Defer + state-aware deploy ratio

In a 400-model DAG with `state:modified+ --defer --state ../prod-manifest`, the build set is typically **5-20%** of the full DAG. If your CI build time is not 5-20% of full-prod time, you have a problem. Common causes:

1. `state:modified+` is picking up too many models (often a YAML formatting churn — re-pin manifest).
2. Defer isn't actually deferring (missing `--state` flag or stale prod manifest).
3. `+` traversal is too greedy — switch to `--select +modified+` to limit upstream too.

See [`microbatch-and-state.md`](microbatch-and-state.md) for the full slim-CI design pattern.

---

## §6. 2026 features (adoption guardrails)

| Feature | Status | Adopt for | Skip for |
|---|---|---|---|
| **dbt-fusion engine** (Rust) | Preview | Speed wins on parse + compile in 1000+ model projects | Production until stable; semantic layer not yet supported |
| **dbt State / `manage_state`** | Preview | Cut compute on unchanged nodes in large DAG; auto-defer | First adoption — read the State docs carefully on cache-invalidation conditions |
| **Microbatch incremental** | GA | Replace hand-rolled `is_incremental()` with `event_time` filter | Models without a clean event-time column |
| **Unit tests** | GA | Currency conv, ARR categorization, SSR detection — anywhere logic is non-trivial | Pure passthrough projections |
| **Model contracts** | GA | All cross-project boundaries — mandatory | Internal `int_*` models (would slow iteration) |
| **MetricFlow / Semantic Layer** | GA | Metric definitions that drive 5+ BI dashboards | One-off ad-hoc metrics |
| **`latest_version` pointer** | GA | Versioned models that need a stable alias for slow-migrating consumers | n/a |

### Adoption guardrails

1. **Never** pilot a Preview feature on a production financial-metric path. Validate in dev first with the existing PVQ recon harness (< $1 variance).
2. **One ownership per relation** — a table is either dbt-managed OR a Dynamic Table, never both.
3. **Manifest discipline** — when you adopt State or defer, pin a manifest publishing job to your prod CI so consumers can defer.
4. **Contract first, version second** — add contracts to existing cross-project models BEFORE you need to version them. Versioning without a contract is just two copies of the same file.

---

## Quick reference commands

```bash
# Full prod build (parallel)
dbt build --threads 24 --select +bt_product_arr_categories+ --exclude '*_scd2'

# Slim CI (modified + downstream + defer to prod state)
dbt build --select state:modified+ --defer --state ../prod-manifest --threads 16

# Unit tests only
dbt test --select unit_test:*

# Run one microbatch window
dbt run --select my_event_fact --event-time-start 2026-01-01 --event-time-end 2026-02-01

# Generate + serve docs
dbt docs generate --no-compile && dbt docs serve --port 8088

# Mesh: see which downstream consumers ref a model across projects
dbt ls --select +my_model+ --resource-type model --output json | jq '.[]|{name,package_name}'

# Contract enforcement check (fails build if schema drifts)
dbt parse --select my_contracted_model
```

---

## See also

- `dbt-platform-architect` skill — multi-environment promotion, env-level config
- `dbt-system-admin` skill — dbt Cloud admin, scheduler, deployment ops
- `dbt-model-debugger` skill — data-quality debugging (duplicates, fanout, NULL bugs)
- `data-analytics-architect` skill — broader dbt+Snowflake decisions, L1/L2 triage
- `analytics-engineering-architect` skill — modern data stack, semantic layer architecture, data products
