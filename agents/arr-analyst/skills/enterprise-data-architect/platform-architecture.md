# Platform Architecture — Workday Enterprise Analytics Platform (2026)

End-to-end architecture: sources → Fivetran → Snowflake EDH (BASE_PROD) →
domain DBs → dbt mesh (6 repos) → semantic layer → Sigma BI.

This is the "where does everything live and how does data move?" reference.

---

## §1. Layer-by-layer architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 1: SOURCE SYSTEMS                                                              │
│  (30+ SaaS + on-prem, owned by business teams)                                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  ┌─ GTM / Revenue ─┐  ┌─ Marketing ──┐  ┌─ Finance ────┐  ┌─ CX / Success ──┐      │
│  │ SFDC (core)     │  │ Marketo      │  │ Zuora        │  │ Gainsight       │      │
│  │ SFDC (GTM-Next) │  │ Bizible      │  │ Workday FM   │  │ Medallia        │      │
│  │ Apttus CPQ      │  │ Drift / 6Sense│  │ Adaptive     │  │ Qualtrics       │      │
│  │ Outreach        │  │ Eloqua (lgcy) │  │ Coupa        │  │ Zendesk         │      │
│  │ Gong            │  │              │  │ Concur       │  │ ServiceNow      │      │
│  │ Clari           │  │              │  │              │  │ FullStory       │      │
│  │ Highspot        │  │              │  │              │  │ Mixpanel        │      │
│  │ Mediafly        │  │              │  │              │  │ Pendo           │      │
│  └─────────────────┘  └──────────────┘  └──────────────┘  └─────────────────┘      │
│  ┌─ Cross-cutting ──────────────────────────────────────────────────────────┐       │
│  │  Reltio (MDM)  │  CDP (Customer Data Platform)  │  Jira/BTJira (eng)    │       │
│  │  Google Sheets (controlled overrides, FY plans) │  Workday HCM (people) │       │
│  └──────────────────────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────┬───────────────────────────────────────┘
                                              │ Fivetran (~100 connectors, managed)
                                              │ + Airbyte (selective)
                                              │ + custom Snowpipe (Kafka, S3 drops)
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 2: INGESTION & LANDING (Snowflake RAW / BASE tier)                             │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  BASE_PROD (~55 schemas) — Fivetran landing, typically 1-hr CDC refresh              │
│  ├── SALESFORCE         (550+ SFDC objects, Apttus + core)                          │
│  ├── SALESFORCE_GTMNEXT (GTM-Next migration target, new SFDC org)                   │
│  ├── ZUORA              (billing, subscription, invoice, payment)                   │
│  ├── WORKDAY_FINANCIAL_MANAGEMENT (GL, AR, AP)                                      │
│  ├── ADAPTIVE_PLANNING  (FP&A budgets, forecasts)                                   │
│  ├── MARKETO            (lead, campaign, email engagement)                          │
│  ├── BIZIBLE            (multi-touch attribution touchpoints)                       │
│  ├── GAINSIGHT          (customer health, success plays, CTAs)                      │
│  ├── MEDALLIA           (NPS, CSAT surveys)                                         │
│  ├── QUALTRICS          (employee + customer experience surveys)                    │
│  ├── OUTREACH           (sales engagement sequences)                                │
│  ├── GONG               (call recording + analysis)                                 │
│  ├── CLARI              (forecast aggregation)                                      │
│  ├── HIGHSPOT           (sales content engagement)                                  │
│  ├── JIRA / BTJIRA      (engineering tickets)                                       │
│  ├── RELTIO             (master data — account, contact, hierarchy)                 │
│  ├── CDP                (unified customer profile)                                  │
│  ├── GOOGLE_SHEETS      (Fivetran-synced control / override sheets)                 │
│  └── ...                                                                             │
│                                                                                       │
│  BASE_SOX_PROD          ← SOX-controlled subset (rev-rec relevant sources)          │
│  REDSHIFT_HISTORY       ← legacy SCD2 history (pre-Snowflake migration)             │
└─────────────────────────────────────────────┬───────────────────────────────────────┘
                                              │ eda-dbt-base (1st transformation hop)
                                              │ - SCD2 wrappers
                                              │ - base type-casts & renames
                                              │ - audit / data-quality stubs
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 3: CURATED DOMAIN DATABASES (EDW tier, data mesh)                              │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  Every domain follows: <DOMAIN>_PROD.{MANAGED, AGGREGATIONS, DATA_PRODUCTS}           │
│                       + <DOMAIN>_INT_PROD.STAGE                                       │
│                                                                                       │
│  Domain databases (built by domain-owning dbt projects):                             │
│  ┌──────────────────────────────────────┬──────────────────────────────────────┐    │
│  │ FOUNDATIONAL_ASSETS_PROD             │ ← eda-dbt-common                    │    │
│  │   ├── MANAGED  (calendar, currency)  │ Shared dims used by all domains     │    │
│  │   ├── AGGREGATIONS                   │                                      │    │
│  │   └── DATA_PRODUCTS                  │                                      │    │
│  ├──────────────────────────────────────┼──────────────────────────────────────┤    │
│  │ SALES_PROD                           │ ← eda-dbt-gtm                       │    │
│  │   ├── MANAGED  (WD_ACCOUNT_SCD2, …)  │ Pipeline, opp, proposal, quota,     │    │
│  │   ├── AGGREGATIONS (pipeline_summary)│ forecast, win rate, territory       │    │
│  │   └── DATA_PRODUCTS                  │                                      │    │
│  ├──────────────────────────────────────┼──────────────────────────────────────┤    │
│  │ MARKETING_PROD                       │ ← eda-dbt-gtm                       │    │
│  │   ├── MANAGED  (LEAD, CAMPAIGN, …)   │ Marketing-sourced pipeline, MQL,    │    │
│  │   ├── AGGREGATIONS                   │ attribution, ABM, campaign ROI      │    │
│  │   └── DATA_PRODUCTS                  │                                      │    │
│  ├──────────────────────────────────────┼──────────────────────────────────────┤    │
│  │ FINANCE_PROD                         │ ← eda-dbt-em                        │    │
│  │   ├── MANAGED  (FINANCE_LINE_ANALYTICS, WD_AGREEMENT_*)                   │    │
│  │   │           Canonical ARR / ACV / TCV at ALI grain                       │    │
│  │   ├── AGGREGATIONS  (ARR_PRODUCT_CATEGORIES, ARR_SKU_CATEGORIES,           │    │
│  │   │                  ARR_LINE_CATEGORIES) — 7+ ARR views                  │    │
│  │   └── DATA_PRODUCTS (ARR_PRODUCT_NET_DOLLAR_RETENTION_DASH_V2,             │    │
│  │                      ARR_SKU_TRENDS_DASHBOARD, …)                          │    │
│  ├──────────────────────────────────────┼──────────────────────────────────────┤    │
│  │ ACTIVATION_USAGE_ADOPTION_PROD       │ ← eda-dbt-cx (sub-domain 1)         │    │
│  │   ├── MANAGED                        │ Feature usage, product adoption,    │    │
│  │   ├── AGGREGATIONS                   │ time-in-app, active users            │    │
│  │   └── DATA_PRODUCTS                  │                                      │    │
│  ├──────────────────────────────────────┼──────────────────────────────────────┤    │
│  │ LOYALTY_ADVOCACY_PROD                │ ← eda-dbt-cx (sub-domain 2)         │    │
│  │   ├── MANAGED                        │ NPS, CSAT, customer health,         │    │
│  │   ├── AGGREGATIONS                   │ advocacy program, references         │    │
│  │   └── DATA_PRODUCTS                  │                                      │    │
│  ├──────────────────────────────────────┼──────────────────────────────────────┤    │
│  │ PRODUCT_IMPLEMENTATION_PROD          │ ← eda-dbt-cx (sub-domain 3)         │    │
│  │   ├── MANAGED                        │ PSO engagements, time-to-value,     │    │
│  │   ├── AGGREGATIONS                   │ implementation milestones            │    │
│  │   └── DATA_PRODUCTS                  │                                      │    │
│  └──────────────────────────────────────┴──────────────────────────────────────┘    │
│                                                                                       │
│  Plus _INT_PROD variants for each (STAGE schema for intermediates).                  │
│  Plus _DEV / _QA / _PROD environment splits per DB.                                  │
└─────────────────────────────────────────────┬───────────────────────────────────────┘
                                              │ eda-dbt-semantic-layer
                                              │ (MetricFlow, post-IA)
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 4: SEMANTIC LAYER                                                              │
│  - dbt Semantic Layer (MetricFlow)                                                   │
│  - Canonical metric definitions: ARR, ACV, NRR, GRR, Churn, Expansion, …            │
│  - Served via JDBC to BI tools                                                       │
└─────────────────────────────────────────────┬───────────────────────────────────────┘
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 5: CONSUMPTION                                                                 │
│  - Sigma (primary BI, ~80% of dashboards)                                            │
│  - Tableau (legacy + select finance reports)                                         │
│  - Hex (data science notebooks)                                                      │
│  - Hightouch (reverse ETL → SFDC enriched fields, Marketo audiences)                │
│  - Operational APIs (custom microservices reading from Snowflake)                    │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## §2. The 6 dbt project repos — full topology

### 2.1 Repos at a glance

| Repo | Project name | dbt profile | Default branch | Primary output DBs |
|---|---|---|---|---|
| `workday-inc/eda-dbt-base` | `eda_dbt_base` | `eda_dbt_repo` | `qa` | `BASE` (per-target → BASE_DEV/QA/PROD) |
| `workday-inc/eda-dbt-common` | `eda_dbt_common` | `eda_dbt_repo` | `qa` | `FOUNDATIONAL_ASSETS` + `FOUNDATIONAL_ASSETS_INT` |
| `workday-inc/eda-dbt-gtm` | `eda_dbt_gtm` | `eda_dbt_repo` | `qa` | `SALES` + `SALES_INT`, `MARKETING` + `MARKETING_INT` |
| `workday-inc/eda-dbt-em` | `eda_dbt_em` | `eda_dbt_repo` | `qa` | `FINANCE` + `FINANCE_INT` (post-IA; legacy still references `certified`) |
| `workday-inc/eda-dbt-cx` | `eda_dbt_cx` | `eda_dbt_repo` | `qa` | `ACTIVATION_USAGE_ADOPTION` + `_INT`, `LOYALTY_ADVOCACY` + `_INT`, `PRODUCT_IMPLEMENTATION` + `_INT` |
| `workday-inc/eda-dbt-semantic-layer` | `eda_dbt_semantic_layer` | `default` | `qa` | Metric definitions (no Snowflake materialization) |

Plus: `workday-inc/eda-dbt-training` — sandbox / onboarding (main branch).

### 2.2 Cross-project dependency graph (`dependencies.yml`)

```
                              eda-dbt-base
                                    │
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                     ▼
      eda-dbt-common          eda-dbt-em            eda-dbt-gtm
              ╲                    │                    ╱
                ╲                  │                  ╱
                  ╲                ▼                ╱
                    ╲      eda-dbt-em uses     ╱
                      ╲   common + gtm too    ╱
                        ╲     │     │       ╱
                          ╲   │     │     ╱
                            ╲ ▼     ▼   ╱
                            eda-dbt-cx
                                  │
                                  ▼
                       eda-dbt-semantic-layer
```

Concrete from each repo's `dependencies.yml`:
- `eda-dbt-base` — no upstream deps (root)
- `eda-dbt-common` — depends on `eda_dbt_base`, `eda_dbt_em` (yes, common reaches into em for shared finance dims; manage carefully)
- `eda-dbt-gtm` — depends on `eda_dbt_base`, `eda_dbt_common`, `eda_dbt_em`
- `eda-dbt-em` — depends on `eda_dbt_base`, `eda_dbt_common`, `eda_dbt_gtm`, `eda_dbt_cx`
- `eda-dbt-cx` — depends on `eda_dbt_base`, `eda_dbt_gtm`, `eda_dbt_em`, `eda_dbt_common`
- `eda-dbt-semantic-layer` — depends on `eda_dbt_common`, `eda_dbt_gtm`, `eda_dbt_cx`, `eda_dbt_em`

**Cycle warning**: `em ↔ gtm` and `em ↔ common` are bidirectional. This is dbt-mesh-legal because cross-project `ref()` reads frozen manifests (not live recompiles), but in practice it means:

- Don't make `em` depend on a `gtm` model that itself depends on `em` — that IS a runtime cycle.
- Use a clear "primary direction" — gtm publishes upstream-of-em models (pipeline, account); em publishes downstream-only finance metrics. cx similarly publishes outputs em doesn't consume.

### 2.3 Materialization map by project

| Project | Materialization conventions |
|---|---|
| `eda-dbt-base` | Mostly **views** over Fivetran tables; **snapshots** for SCD2 history; **incremental** for heavy fact landings |
| `eda-dbt-common` | **Tables** for dims; **views** for utility wrappers |
| `eda-dbt-gtm` | **Views** in `_INT.STAGE`; **incremental tables** in `MANAGED`; **tables** in `AGGREGATIONS`; **views** in `DATA_PRODUCTS` |
| `eda-dbt-em` | Same as GTM. `MANAGED.FINANCE_LINE_ANALYTICS` is incremental-merge by `(agreement_line_item_id, as_was_date)` |
| `eda-dbt-cx` | Same pattern |
| `eda-dbt-semantic-layer` | No materialization — metric definitions only |

### 2.4 Schema configs (from each `dbt_project.yml`)

Snippet from `eda-dbt-gtm` (canonical example):

```yaml
models:
  eda_dbt_gtm:
    sales:
      int:
        +database: sales_int
        stage:
          +schema: stage
      modeled:
        +database: sales
        +access: public
        +group: common_group
        managed:
          +schema: managed
        data_product:
          +schema: data_products
        aggregate:
          +schema: aggregations
    marketing:
      int:
        +database: marketing_int
        stage:
          +schema: stage
      modeled:
        +database: marketing
        +access: public
        +group: common_group
        managed: { +schema: managed }
        data_product: { +schema: data_products }
        aggregate: { +schema: aggregations }
```

Same pattern in `eda-dbt-cx`:

```yaml
models:
  eda_dbt_cx:
    activation_usage_adoption:
      int: { +database: activation_usage_adoption_int }
      modeled:
        +database: activation_usage_adoption
        managed: { +schema: managed }
        data_products: { +schema: data_products }
        aggregations: { +schema: aggregations }
    loyalty_advocacy:
      int: { +database: loyalty_advocacy_int }
      modeled: { +database: loyalty_advocacy, ... }
    product_implementation:
      int: { +database: product_implementation_int }
      modeled: { +database: product_implementation, ... }
```

`eda-dbt-em` (FYI — IA migration still in progress in the repo):

```yaml
models:
  eda_dbt_em:
    +database: certified              # ← legacy reference still in repo
    finance:
      +schema: finance
    stage:
      +database: certified
      +schema: stage
```

Runtime (prod) targets these to `FINANCE_PROD.{managed,aggregations,data_products}` and `FINANCE_INT_PROD.STAGE`. The repo-level `certified` literal is overridden in env config.

### 2.5 Warehouse routing

From `eda-dbt-base` snippet (template for all):

```yaml
snapshots:
  eda_dbt_base:
    +snowflake_warehouse: '{{
      "NPROD_BATCH_WH" if target.name | lower == "qa"
      else "PROD_BATCH_WH" if target.name | lower == "prod"
      else "GOVERNANCE_WH" }}'
```

By target:
| Target | Warehouse |
|---|---|
| `dev` | `GOVERNANCE_WH` (XS / S) |
| `qa` | `NPROD_BATCH_WH` |
| `prod` | `PROD_BATCH_WH` |

Plus dedicated warehouses for orchestration:
- `INGESTION_WH` — Fivetran writes
- `ANALYTICS_ENGINEER_WH` — interactive dev
- `BI_WH` — Sigma / Tableau queries
- `SEMANTIC_LAYER_WH` — MetricFlow

### 2.6 Run order (orchestration in dbt Cloud)

Daily run sequence (~03:15 AM PDT main batch):

```
1. Fivetran (continuous, but cutoff ~02:00 AM)
       ↓
2. eda-dbt-base run            (~30 min — SCD2 + base wrappers)
       ↓
3. eda-dbt-common run          (~15 min — shared dims)
       ↓
4. eda-dbt-gtm run             (~45 min — sales + marketing)
       ↓
5. eda-dbt-em run              (~60 min — finance, heaviest)
       ↓
6. eda-dbt-cx run              (~20 min — CX 3 sub-domains)
       ↓
7. eda-dbt-semantic-layer run  (~5 min — metric compile)
       ↓
8. dbt tests run               (~30 min — all projects)
       ↓
9. Sigma cache warmup          (~10 min — dashboard pre-renders)
```

For detailed timing see `eda-pipeline-refresh-schedule` skill.

---

## §3. Source → BASE_PROD ingestion patterns

### 3.1 Fivetran (primary)

~100 active Fivetran connectors. Pattern:

| Connector type | Refresh cadence | Notes |
|---|---|---|
| **Salesforce (core)** | 1 hour, CDC | All 550+ objects landed |
| **Salesforce GTM-Next** | 1 hour, CDC | New org for GTM transformation |
| **Zuora** | 15 min, CDC | Billing — high freshness needed |
| **Workday FM** | Daily | GL data is daily-grain |
| **Marketo** | 1 hour | Lead + activity |
| **Bizible** | 1 hour | Touchpoint events |
| **Gainsight** | 1 hour | Customer health refreshes |
| **Medallia / Qualtrics** | Daily | Survey snapshots |
| **Outreach / Gong / Clari** | 1 hour | Sales activity |
| **Google Sheets** | 15 min | Override sheets for manual control |
| **Reltio** | 1 hour | MDM golden records |

Each connector writes to `BASE_PROD.<SOURCE>.<TABLE>`. Standard Fivetran metadata columns (`_fivetran_synced`, `_fivetran_deleted`, `_fivetran_id`) are present on every table.

### 3.2 Custom ingestion

Where Fivetran can't cover:

| Pattern | Use case | Tooling |
|---|---|---|
| **Snowpipe + S3** | Event-driven data (Kafka offloads, app event logs) | Snowpipe streaming, ~1-minute latency |
| **External tables** | Large slow-changing reference data | Iceberg / external stage |
| **dbt seeds** | Static reference data <1MB (FY plan, lookup tables) | Committed to git |
| **Python connectors** | API-only sources without Fivetran support | Custom Airflow / dbt Python models |

### 3.3 The "control sheet" pattern (very Workday-specific)

Finance and ops teams maintain **Google Sheets as system-of-record overrides**:
- `REF_FIN_CUSTOMIZED_DATA` — ACV/ARR manual adjustments
- `REF_PRODUCT_HIERARCHY` — SKU → product family mapping
- `REF_ACQUISITION_MAPPING` — Acquired-company account mapping
- `REF_FX_OVERRIDE` — Period-end FX rate locks
- `REF_TCV_CORRECTION` — TCV correction sheet

Each is Fivetran-synced as `BASE_PROD.GOOGLE_SHEETS.<TABLE>`, then wrapped by an `lkp_*` model in the consuming domain repo. Always check `_fivetran_synced` for freshness when debugging "the number changed" complaints.

---

## §4. The data flow — concrete: ARR end-to-end

A worked example — how ARR moves from source to dashboard:

```
[Salesforce Apttus]                                                    ← User: AE clicks "Activate" on agreement
        │
        │  Salesforce CDC fires; record updated in SFDC core org
        ▼
[Fivetran Salesforce connector]                                        ← ~5 min after source change
        │
        ▼
BASE_PROD.SALESFORCE.APTTUS__AGREEMENTLINEITEM__C                      ← landed in BASE_PROD; _fivetran_synced stamped
        │
        │  Within 1 hour: eda-dbt-base snapshot runs
        ▼
BASE_PROD.REDSHIFT_HISTORY.<historical SCD2 capture>                   ← (legacy SCD2; kept for back-compat)
        │
        │  eda-dbt-base also generates a base wrapper view
        ▼
BASE.SALESFORCE.base_apttus__agreementlineitem__c                      ← typed + renamed columns
        │
        │  eda-dbt-gtm consumes via ref
        ▼
SALES_INT_PROD.STAGE.stg_em_agreement_line_item_scd2                  ← SCD2 snapshot of ALI fields
        │
        │  ↓ joins with Account / Opportunity / Proposal (also SCD2 wrappers)
        ▼
SALES_PROD.MANAGED.WD_AGREEMENT_LINE_SCD2                              ← published SCD2 dim, contracted, public access
        │
        │  eda-dbt-em consumes via cross-project ref
        ▼
FINANCE_INT_PROD.STAGE.stg_em_int_agree_enriched                       ← join with Account + Opportunity + Proposal + Product hierarchy
        │
        │  apply get_arr_line_base_fn UDTF (categorization logic)
        ▼
FINANCE_INT_PROD.STAGE.stg_em_int_arr_line_base                        ← ARR per ALI per as_was_date with category
        │
        ▼
FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS                            ← canonical ARR/ACV/TCV at ALI × as_was_date grain
        │
        │  aggregated multiple ways
        ▼
FINANCE_PROD.AGGREGATIONS.ARR_PRODUCT_CATEGORIES                       ← rollup by product
FINANCE_PROD.AGGREGATIONS.ARR_SKU_CATEGORIES                           ← rollup by SKU
FINANCE_PROD.AGGREGATIONS.ARR_LINE_CATEGORIES                          ← rollup by line characteristics
        │
        ▼
FINANCE_PROD.DATA_PRODUCTS.ARR_PRODUCT_NET_DOLLAR_RETENTION_DASH_V2    ← BI-facing publish
        │
        │  Sigma workbook (or MetricFlow via JDBC)
        ▼
[Sigma "ARR — Net Dollar Retention" dashboard]                         ← Visible to CFO ~3-4 hrs after source change
```

End-to-end latency: ~3–4 hours from source edit → dashboard visible. The slowest link is the 03:15 AM batch — within a single batch, ~4 hours for the full mesh to complete + tests + Sigma warmup.

For SLA / freshness details: `eda-pipeline-refresh-schedule` skill.

---

## §5. The IA (Information Architecture) project — what changed in 2026

The IA project (completed mid-2026) was a data mesh migration:

**Before IA:**
```
Single CERTIFIED_PROD database
├── COMMON  (shared dims)
├── SALES   (GTM models)
├── FINANCE (em models)
├── CX      (CX models)
└── STAGE   (intermediates, mixed across domains)
```

**After IA:**
```
7 domain databases, mesh-aligned to dbt projects
├── FOUNDATIONAL_ASSETS_PROD              ← eda-dbt-common
├── SALES_PROD + SALES_INT_PROD           ← eda-dbt-gtm
├── MARKETING_PROD + MARKETING_INT_PROD   ← eda-dbt-gtm
├── FINANCE_PROD + FINANCE_INT_PROD       ← eda-dbt-em
├── ACTIVATION_USAGE_ADOPTION_PROD + _INT ← eda-dbt-cx
├── LOYALTY_ADVOCACY_PROD + _INT          ← eda-dbt-cx
└── PRODUCT_IMPLEMENTATION_PROD + _INT    ← eda-dbt-cx
```

What we DID NOT migrate:
- `BASE_PROD` — unchanged (Fivetran landing)
- `REDSHIFT_HISTORY` — unchanged (legacy SCD2 archive)
- `BASE_SOX_PROD` — unchanged (SOX-controlled)
- `CERTIFIED_PROD` is **deprecated** for current work — only legacy references remain; new lessons + designs should ignore it

What changed structurally:
- Schema split: every domain DB has the same 4 schemas (`MANAGED`, `AGGREGATIONS`, `DATA_PRODUCTS` in main; `STAGE` in `_INT`)
- Cross-domain `ref()` now happens via dbt-mesh project boundaries (cross-project refs)
- Contracts (`contract: enforced`) are now mandatory for any model in `DATA_PRODUCTS` consumed cross-domain
- Access modifiers (`+access: public` + `+group: common_group`) gate which models are exposed cross-project

For agent learnings: when seeing a `certified_prod.*` reference in lessons or docs, mentally map to the post-IA domain DB. See `lesson-audit` skill outputs for the canonical rename mapping.

---

## §6. Environment promotion (Git flow)

Each dbt repo follows the same flow:

```
feature/EDAEM-1234-add-arr-view-for-renewals  (developer branch)
       ↓ PR
qa branch  → triggers dbt Cloud Job #20 (QA build)
       ↓ promotion (cherry-pick or PR merge)
prod branch → triggers dbt Cloud Job #22 (PROD build)
       ↓ scheduled
Daily 03:15 PDT batch
```

CI on every PR runs `dbt build --select state:modified+ --defer --state ./prod-manifest`. The "slim CI" approach saves ~80% of CI compute by only building modified-and-downstream models.

Multi-project considerations:
- Each project has its own CI/CD; PRs scope to one project at a time
- Cross-project changes require sequenced PRs: upstream merges first, downstream re-runs CI against the new manifest
- Production manifest stored in S3 and pulled by all projects' CI

For platform topology + branch protection: `dbt-platform-architect` skill.

---

## §7. Failure modes (cross-project patterns)

| Symptom | Likely cause | Where to look first |
|---|---|---|
| Cross-project `ref()` not found | Stale manifest in dependent project | Re-run `dbt deps` + refresh manifest pin |
| New model not visible to downstream project | Missing `+access: public` or `+group` | Check `dbt_project.yml` of producing repo |
| CI passes in one project, breaks downstream | Schema change without `contract: enforced` | Add contract on the published model |
| Dashboard data delayed by hours | Upstream Fivetran connector behind | Check Fivetran connector status |
| Numbers off after IA migration | Lesson / SQL still references `certified_prod.*` | Rename to `<domain>_prod.*` per IA mapping |
| Metric drift between Sigma + dashboard | Sigma re-implementing the metric instead of semantic layer | Move metric to `eda-dbt-semantic-layer` |
| SCD2 row count exploded after deploy | Snapshot config changed `unique_key` / `check_cols` | Roll back snapshot config; never change in place |

---

## §8. Anti-patterns (do NOT do)

- ❌ Read from another domain's `_INT.STAGE` schema (internals — use their published `DATA_PRODUCTS`)
- ❌ Modify a model in someone else's repo without coordinating with the domain owner
- ❌ Define a metric in Sigma when 2+ workbooks need it (push to semantic layer)
- ❌ Hardcode FY boundaries (use `get_fiscal_quarter`)
- ❌ Add a new database without Terraform PR + RBAC review
- ❌ Land a new source via direct Snowpipe when Fivetran has a connector (manage operational burden)
- ❌ Skip SOX gating on a model that feeds revenue recognition
- ❌ Build "yet another ARR table" — extend the canonical `FINANCE_LINE_ANALYTICS` instead
- ❌ Use `CERTIFIED_PROD.*` in new code (deprecated post-IA)

---

## See also

- `dbt-platform-architect` — multi-project topology + env promotion
- `dbt-architect/mesh-and-contracts.md` — dbt-mesh deep dive
- `snowflake-architect` — Snowflake-specific architecture
- `subscription-business-model.md` — Why this architecture exists (business context)
- `bi-semantic-consumption.md` — Sigma + semantic layer patterns
