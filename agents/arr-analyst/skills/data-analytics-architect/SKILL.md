---
name: data-analytics-architect
description: Architect and support dbt + Snowflake analytics platforms. Covers dbt model design (staging/intermediate/marts), Snowflake optimization (warehouses, clustering, costs), data modeling (dimensional, SCD2, grain), CI/CD, testing strategy, data governance, latest dbt/Snowflake platform features (dbt 1.12 State, microbatch, unit tests; Snowflake Gen2 warehouses, Dynamic Tables, Iceberg, Optima, Cortex AI), and L1/L2 production support (pipeline failures, performance, freshness, schema changes, access issues). Use when designing new models, reviewing architecture decisions, adopting new platform features, troubleshooting production issues, optimizing queries, managing Snowflake costs, or triaging data platform incidents.
---

# Data Analytics Architect & L1/L2 Support

Role: Senior Data Analytics Architect with deep expertise in dbt, Snowflake, dimensional modeling, and production support for enterprise analytics platforms.

## When to Apply This Skill

- Designing or reviewing dbt model architecture
- Making Snowflake infrastructure decisions (warehouse sizing, clustering, materialization)
- Triaging production incidents (L1/L2 support)
- Optimizing query performance or Snowflake costs
- Implementing data governance (tagging, masking, access policies)
- Planning CI/CD and testing strategies
- Advising on data modeling (dimensional, SCD types, grain)

> **Note:** For debugging specific data quality issues (duplicates, row inflation, join problems), use the companion `dbt-model-debugger` skill instead.

---

## Part 1: Architecture Decision Framework

When asked to design or review architecture, evaluate along these dimensions:

### dbt Model Design

Follow the **staging → intermediate → marts** layering:

| Layer | Prefix | Materialization | Purpose |
|-------|--------|-----------------|---------|
| **Source** | `source()` | — | Raw data declaration via `sources.yml` |
| **Staging** | `stg_` | View (or table for SCD2) | 1:1 with source, rename, cast, filter deleted |
| **Intermediate** | `int_` | Ephemeral or table | Business logic, joins, aggregations |
| **Marts/Business** | `bt_` / `bv_` | Table / View | Consumer-facing, grain-documented |

**Key rules:**
- Staging models reference only `source()` — never other models
- Intermediate models reference staging or other intermediates
- Marts reference intermediates — avoid reaching back to staging
- Every model documents its grain in a YAML description or file header

For detailed patterns, naming conventions, and CTE structure, see [dbt-patterns.md](dbt-patterns.md).

### Snowflake Architecture

| Decision | Guidance |
|----------|----------|
| **Warehouse sizing** | Start XS, scale up for specific heavy models only |
| **Clustering keys** | Only for tables >1TB with predictable filter patterns |
| **Materialization** | Views for light transforms, tables for joins/aggregations, incremental for large fact tables |
| **Multi-cluster** | Use for concurrent user workloads, not batch dbt runs |
| **Auto-suspend** | 1 min for dev, 5 min for prod batch, 1-5 min for BI |

For Snowflake optimization, cost management, and query tuning details, see [snowflake-patterns.md](snowflake-patterns.md).

### Data Modeling

| Pattern | When to Use |
|---------|-------------|
| **Star schema** | BI-facing marts with known query patterns |
| **Wide denormalized** | Operational analytics, ML feature stores |
| **SCD Type 2** | Track full history of dimension changes |
| **SCD Type 1** | Current-state only, overwrite on change |
| **Snapshot** | Point-in-time fact tables (daily/monthly) |

**Grain design checklist:**
1. Define the grain explicitly (one row = what?)
2. Document the natural key and surrogate key
3. Validate with `unique` + `not_null` tests on the primary key
4. Verify grain is preserved through all joins (watch for fanout)

---

## Part 2: L1/L2 Support Triage

When triaging a production issue, classify severity and follow the appropriate runbook.

### Severity Classification

| Level | Description | Response |
|-------|-------------|----------|
| **P1 — Critical** | Pipeline fully blocked, downstream dashboards broken | Immediate investigation, notify stakeholders |
| **P2 — High** | Data quality issue affecting reports, partial pipeline failure | Investigate within 1 hour |
| **P3 — Medium** | Performance degradation, non-critical model failures | Investigate within 4 hours |
| **P4 — Low** | Documentation gaps, minor schema changes, optimization requests | Backlog |

### Triage Decision Tree

```
Issue reported
├── Pipeline failed?
│   ├── dbt compile/run error → Check error message, model SQL, ref/source changes
│   ├── Snowflake query error → Check warehouse availability, permissions, query size
│   └── Timeout → Check warehouse size, query complexity, data volume growth
├── Data looks wrong?
│   ├── Row count mismatch → Use dbt-model-debugger skill
│   ├── Missing data → Check source freshness, incremental logic, filter conditions
│   ├── Stale data → Check scheduler, source freshness tests, upstream dependencies
│   └── Wrong values → Trace column lineage, check join logic, transformation order
├── Performance issue?
│   ├── Slow model build → Profile query, check warehouse size, review joins
│   ├── Slow BI query → Check materialization, clustering, result caching
│   └── High credit usage → Review warehouse utilization, auto-suspend, query patterns
└── Access/permission issue?
    ├── Cannot query table → Check role grants, database/schema permissions
    ├── Cannot run dbt → Check service account roles, warehouse access
    └── Cannot see columns → Check masking policies, column-level security
```

For detailed resolution steps for each scenario, see [support-runbook.md](support-runbook.md).

---

## Part 3: Testing Strategy

### What to Test

| Test Type | When | Example |
|-----------|------|---------|
| `unique` | Every primary key | `unique` on `id` + `as_was_date` for SCD2 |
| `not_null` | Keys and critical business columns | `not_null` on `opportunity_id`, `amount` |
| `accepted_values` | Enum/status columns | `accepted_values` on `stage_name` |
| `relationships` | Foreign keys across models | `relationships` to parent model |
| `dbt_utils.expression_is_true` | Business rules | `amount >= 0`, `start_date <= end_date` |
| Source freshness | Every source | `loaded_at_field` with `warn_after` / `error_after` |
| Row count comparison | Migration / refactor | Custom `test_row_count` generic test |
| Column value comparison | Migration / refactor | Custom `test_compare_column_values` |

### Testing Priorities

1. **Always test:** Primary keys (`unique` + `not_null`), source freshness
2. **High value:** Referential integrity, business-critical columns
3. **Medium value:** Accepted values for enums, expression validations
4. **On refactor:** Row count and column value comparisons against legacy

---

## Part 4: CI/CD & Deployment

### Environment Strategy

| Environment | Database | Purpose |
|-------------|----------|---------|
| **dev** | `certified_dev` | Developer workspace |
| **qa** | `certified_qa` | PR validation, integration testing |
| **prod** | `certified_prod` | Production |

### CI Pipeline Checks

1. `dbt build --select state:modified+` — build only changed models and downstream
2. `sqlfluff lint` — SQL style enforcement
3. `dbt test --select state:modified+` — run tests on affected models
4. Row count / value comparison tests for critical model changes

### Deployment Best Practices

- Use `--defer` with a production manifest for slim CI
- Run `--full-refresh` only for SCD2 initial loads or schema changes
- Use `dbt build` (not `dbt run` + `dbt test` separately) for atomic model+test execution
- Tag critical path models and test them in CI even if not directly modified

---

## Part 5: Data Governance

### Column Tagging

Use `dbt_tags.apply_column_tags()` post-hook (already configured in project) to:
- Tag PII columns for masking policies
- Tag financial columns for audit
- Tag classification levels (public, internal, confidential)

### Documentation Standards

- `persist_docs` is enabled — write meaningful column descriptions in YAML
- Document grain, business logic, and refresh frequency in model descriptions
- Use `dbt docs generate` and publish to keep documentation current

### Access Control Pattern

```
ROLE HIERARCHY:
  SYSADMIN
  ├── ANALYTICS_ADMIN (DDL on certified)
  │   ├── ANALYTICS_WRITER (dbt service account)
  │   └── ANALYTICS_READER (BI tools, analysts)
  └── DATA_ENGINEER (DDL on base_prod)
```

Grant minimum required privileges. Use database roles for schema-level access.

---

## Part 6: Latest Platform Features (2026)

Evaluate these newer capabilities when designing or refactoring. Adopt deliberately — prefer features
that are GA for production-critical finance models; pilot Preview features in dev first.

### dbt (Core 1.12 / Cloud, as of 2026)

| Feature | Status | What it does | When to use in `eda-dbt-em` |
|---|---|---|---|
| **dbt State** | Preview (v1.12+) | Skips or zero-copy-**clones** nodes when logic + data are unchanged, instead of rebuilding; auto-defers to prod state without manual `--defer`/`--state` | Cut warehouse cost on the large ARR DAG — unchanged `stg_em_*`/`arr_*` nodes get reused. Opt-in via `--manage-state`, `DBT_ENGINE_MANAGE_STATE=true`, or `manage_state: true` in `dbt_project.yml` flags |
| **Microbatch incremental** | GA (Snowflake adapter) | Splits large incrementals into parallel, retryable batches via `event_time` + `batch_size` + `lookback`; auto-generates the time filters | Replace hand-rolled `is_incremental()` date filters on high-volume SCD2 / snapshot models. 1.12 fixed concurrent-batch deadlocks and retry-time bugs |
| **Unit tests** | GA | Test model logic against mocked inputs (not warehouse data); `unit_test:` selector; now parse macros and support sources with duplicate names | Lock down ARR category / SSR / currency-conversion logic in `functions/` and `arr_*` models with deterministic fixtures |
| **`state:modified` accuracy** | GA | Detects `.yml` UDF property changes (`arguments`, `returns`); fewer Slim-CI false positives from env-driven `database`/`schema` config | Directly improves our `state:modified+` CI — relevant given the 32 TVFs under `functions/` |
| **Versioned models + latest-version pointer** | GA | `latest_version_pointer` auto-creates an unsuffixed alias (e.g. `arr_product_categories`) for the current version | Useful for the IA migration to expose stable names while iterating versions |

> **Action item for our repo:** Snowflake is increasing the default string/binary column size (~May 2026).
> `dbt-snowflake` **below v1.10.6** can fail to build certain incremental models when this lands —
> confirm our adapter pin is ≥ 1.10.6 before that change deploys.

### Snowflake (2026)

| Feature | Status | What it does | When to use in `eda-dbt-em` |
|---|---|---|---|
| **Gen2 Standard Warehouses** | GA | ~2.1× faster for updates/deletes/merges/table scans; required for Snowflake Optima | Default new warehouses to Gen2 for the dbt prod batch and heavy MERGE-based incrementals |
| **Snowflake Optima** | GA (Gen2 only) | Continuously builds metadata to prune unused micro-partitions automatically — no clustering key needed | Lean on this before adding manual clustering keys; cheaper than maintaining cluster keys on churny tables |
| **Adaptive Compute** | Preview | Auto-selects cluster size, cluster count, and auto-suspend/resume | Pilot in dev for spiky ad-hoc/BI workloads before committing to fixed warehouse sizes |
| **Dynamic Tables — custom incremental** | Preview | `CUSTOM_INCREMENTAL` refresh runs your own MERGE/INSERT; `DYNAMIC_TABLE_REFRESH_BOUNDARY()` decouples pipeline stages; `SCHEDULER=DISABLE` for manual refresh; `MIN_BY`/`MAX_BY` supported incrementally | Candidate to replace some `bt_*`/`arr_*` table+macro orchestration with declarative refresh — evaluate against dbt-managed tables; don't mix ownership |
| **Apache Iceberg (Snowflake-managed storage)** | GA | Snowflake stores/manages Iceberg files; open format, Horizon Catalog access, Fail-safe on permanent tables | Consider for large, externally-shared finance datasets to avoid lock-in; keep ARR engine on native tables for now |
| **Cortex AI functions** (`AI_FILTER`, `AI_AGG`, `AI_SUMMARIZE_AGG`) | GA | In-SQL LLM inference; set-based AI aggregation; PII redaction | Out of scope for core ARR math; potential for narrative/commentary or data-quality triage, not metric computation |
| **Search optimization for ARRAY/OBJECT/MAP** | GA | Point-lookup/substring acceleration on semi-structured columns | Relevant for product-mix `ARRAY` columns (e.g. `bb_product_mix`) used in SKU/standalone logic |

### Adoption guardrails

- **Finance correctness first:** never pilot a Preview feature on a production ARR/ACV metric path. Validate in dev with the existing row-count / column-compare tests (< $1 variance) before promotion.
- **One ownership model per table:** a relation is either dbt-managed *or* a Dynamic Table — don't let both try to own it.
- **Cost before clustering:** try Gen2 + Optima before adding clustering keys; re-check `SYSTEM$CLUSTERING_INFORMATION` only if Optima is insufficient.
- **Pin discipline:** track the `dbt-snowflake` adapter version against the May 2026 column-size behavior change.

---

## Quick Reference Commands

```bash
# Full refresh SCD2 models
dbt run --full-refresh --select '*_scd2'

# Incremental SCD2 run
dbt run --select '*_scd2'

# Build ARR models (excluding SCD2)
dbt run --select +bt_product_arr_categories+ +bt_subproduct_arr_categories +bt_sku_arr_categories --exclude '*_scd2'

# Build ACV models (excluding SCD2)
dbt run --select +bt_acv_sku --exclude '*_scd2'

# Run tests on modified models
dbt test --select state:modified+

# Check source freshness
dbt source freshness

# Generate docs
dbt docs generate && dbt docs serve

# --- 2026 platform features ---

# Enable dbt State reuse/clone for a run (opt-in; cuts compute on unchanged nodes)
dbt build --select +arr_product_categories+ --manage-state

# Run only unit tests (mocked inputs, no warehouse data)
dbt test --select unit_test:*

# Backfill / run a specific microbatch window
dbt run --select my_event_model --event-time-start 2026-01-01 --event-time-end 2026-04-01
```

## Additional Resources

- For dbt model design patterns and CTE conventions, see [dbt-patterns.md](dbt-patterns.md).
- For Snowflake optimization and cost management, see [snowflake-patterns.md](snowflake-patterns.md).
- For L1/L2 support resolution steps, see [support-runbook.md](support-runbook.md).
- For data quality debugging (duplicates, join inflation), use the `dbt-model-debugger` skill.
