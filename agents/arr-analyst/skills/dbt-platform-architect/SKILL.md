---
name: dbt-platform-architect
description: >-
  dbt platform architecture at enterprise scale covering multi-project design, cross-project
  dependencies, shared macro libraries, deployment topology, environment promotion strategies,
  Git branching models for dbt, warehouse orchestration, manifest/catalog management, and
  platform governance. Use when designing multi-project dbt platforms, planning environment
  promotion flows, managing cross-project refs, designing branching strategies, architecting
  shared infrastructure, or scaling dbt beyond single-project boundaries.
---

# dbt Platform Architect

## Multi-Project Topology

```
eda-dbt-base (sources, SCD2, raw staging)
    ↓ cross-project ref
eda-dbt-gtm (go-to-market staging, account/opportunity wrappers)
    ↓ cross-project ref
eda-dbt-em (enterprise metrics — finance models, ARR, ACV)
    ↓ consumed by
Dashboards / BI Tools / Snowflake Views
```

### Cross-Project Dependency Rules
- Downstream projects reference upstream via `{{ ref('project_name', 'model_name') }}`
- `packages.yml` pins upstream project revision (branch or tag)
- `dbt deps` must run before any build to fetch upstream manifests
- Never create circular cross-project references
- Upstream breaking changes require coordinated deployment

### Local Development with dbt Mesh — Stub Packages
When `dependencies.yml` declares Mesh projects (resolved by dbt Cloud), local
`dbt parse / compile / build` fails because `dbt deps` does NOT install Mesh deps.
Workaround: write minimal stub packages into `dbt_packages/<package>/` with one
ephemeral `.sql` per ref'd upstream model that points at the live Snowflake relation.
**Critical:** `dbt deps` wipes manually-placed stubs — always wrap with a script
(e.g., `make deps` running `dbt deps && scripts/cross-project-stubs/restore.sh`).

For full step-by-step instructions, mapping schema, and pitfalls, read
`~/.cursor/skills/dbt-platform-architect/cross-project-stubs.md`.

### packages.yml Pattern
```yaml
packages:
  - git: "https://github.com/org/eda-dbt-gtm.git"
    revision: main
  - git: "https://github.com/org/eda-dbt-base.git"
    revision: main
  - package: dbt-labs/dbt_utils
    version: ">=1.0.0"
```

## Environment Promotion Flow

```
feature branch → PR to qa → QA validation → PR to prod → Production deploy
```

| Stage | Branch | Database | Job Trigger |
|-------|--------|----------|-------------|
| Development | feature/* | CERTIFIED_DEV | dbt CLI / manual |
| QA | qa | CERTIFIED_QA | PR merge → dbt Cloud Job #20 |
| Production | prod | CERTIFIED_PROD | PR merge → dbt Cloud Job #22 |

### Promotion Checklist
1. Feature branch passes CI (`state:modified+`)
2. QA validation — data reconciliation queries pass
3. Stakeholder sign-off on metric changes
4. PR to prod with description of business impact
5. Post-deploy validation in prod

## Git Branching Strategy

```
prod (protected, requires review + CI pass)
  ↑ PR
qa (protected, requires review + CI pass)
  ↑ PR
feature/JIRA-ID-description (developer branches)
```

### Branch Protection Rules
- `qa` and `prod`: require PR, 1-2 approvals, CI status checks
- No direct pushes to protected branches
- Squash merge preferred for clean history

## Shared Macro Library Design

### Macro Namespacing
```
macros/
  em/           # Enterprise Metrics domain macros
    udf_*.sql   # Business logic (ARR calc, product mix, etc.)
  utils/        # Cross-cutting utility macros
  schema_tests/ # Custom test macros
```

### Macro Versioning Strategy
- Breaking changes: new macro name (e.g., `udf_arr_v2`)
- Additive changes: extend existing macro with new parameters (default values)
- Deprecation: add `{# DEPRECATED: use udf_xyz instead #}` comment

## Platform Governance

### Model Registry
- Every `bt_*` model registered in schema YAML with grain, owner, SLA
- `bv_*` views documented with consumer team and refresh cadence
- Unused models flagged quarterly for deprecation

### Data Contracts
```yaml
models:
  - name: bt_sku_analytics
    description: "Grain: one row per agreement line item per as_was_date"
    config:
      contract:
        enforced: true
    columns:
      - name: agreement_line_item_id
        data_type: varchar
        constraints:
          - type: not_null
```

### SLA Tiers
| Tier | Freshness | Availability | Models |
|------|-----------|-------------|--------|
| P0 | <4 hours | 99.9% | `bt_bzops_product_corp_report`, `bv_*` dashboards |
| P1 | <8 hours | 99.5% | `bt_*_arr_categories`, `bt_sku_analytics` |
| P2 | <24 hours | 99% | `int_*`, staging models |

## Orchestration Architecture

### Job Dependency Chain
```
SCD2 refresh (eda-dbt-base)
  → Staging wrappers (eda-dbt-em)
    → Finance transforms (bt_*)
      → Dashboard views (bv_*)
        → BI cache refresh
```

### Scheduling Strategy
- **Daily 3:15 AM PDT**: Full production pipeline (PROD-Refresh-EM-ARR-ACV)
- **On PR merge**: CI validation job
- **Ad-hoc**: Manual triggers for backfills, hotfixes

### Failure Handling
1. Alert on job failure (Slack/email via dbt Cloud notifications)
2. Identify failing model from run logs
3. Check upstream freshness (cross-project sources)
4. Fix and re-run only affected models + downstream

## Manifest & Catalog Management
- Production manifest stored as dbt Cloud artifact
- CI uses `--defer --state prod-manifest/` for slim builds
- Catalog generated on scheduled runs for documentation site
- `manifest.json` contains full DAG for lineage tools

## Scaling Patterns

### Large DAG Optimization (400+ models)
- Use `dbt ls` to preview selection before `dbt run`
- Tag models by domain for selective runs: `tag:finance`, `tag:acv`
- Split independent branches into separate jobs for parallelism
- Use `dbt retry` for transient failures instead of full re-run

### Multi-Warehouse Strategy
```yaml
# In dbt_project.yml
models:
  eda_dbt_em:
    stage:
      +snowflake_warehouse: "DEV_WH_S"
    finance:
      table:
        +snowflake_warehouse: "TRANSFORM_WH_M"
      view:
        +snowflake_warehouse: "DEV_WH_S"
```
