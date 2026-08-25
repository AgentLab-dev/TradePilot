# BI + Semantic Layer + Consumption

How data products are exposed to humans — Sigma (primary BI), MetricFlow
(semantic layer), Tableau (legacy), Hex (data science), Hightouch (reverse
ETL).

The goal: **the same metric, defined ONCE, served to MANY tools** with
governance, lineage, and audit. The semantic layer is what makes this
possible.

---

## §1. The consumption stack at Workday

```
                 ┌──────────────────────────────────────────────┐
                 │  USERS                                         │
                 │  Executives │ Analysts │ Data Sci │ Ops      │
                 └────────────────────┬─────────────────────────┘
                                      ▼
        ┌──────────────────────────────────────────────────────────┐
        │  TOOLS                                                     │
        │  Sigma (primary BI)      Tableau (legacy)                │
        │  Hex (notebooks)          Hightouch (reverse ETL)        │
        │  Custom apps (APIs)                                       │
        └──────────────────────────────────────────────────────────┘
              │            │              │            │
              ▼            ▼              ▼            ▼
        ┌───────────────────────────────────────────────────────────┐
        │  SEMANTIC LAYER (eda-dbt-semantic-layer / MetricFlow)     │
        │  Canonical metrics: ARR, ACV, NRR, GRR, MQL, NPS, ...    │
        │  Defined ONCE, queryable via JDBC by all tools           │
        └────────────────────────┬──────────────────────────────────┘
                                 ▼
        ┌───────────────────────────────────────────────────────────┐
        │  DATA PRODUCTS (Snowflake DATA_PRODUCTS schemas)          │
        │  Contracted, governed, SLA-bearing models                │
        └───────────────────────────────────────────────────────────┘
```

---

## §2. Sigma — primary BI tool

Sigma is the default BI tool at Workday. ~80% of dashboards are in Sigma.

### 2.1 Sigma instance

- **Org**: `workday-prod`
- **UI**: `https://app.sigmacomputing.com/workday-prod/`
- **Auth**: SSO via Okta
- **Snowflake connection**: Read-only, dedicated role + warehouse (`BI_WH`)

### 2.2 Sigma object hierarchy

```
Workspace (team-level)
  └── Folder
        └── Workbook
              ├── Page (dashboard tab)
              │     └── Element (chart, table, KPI)
              ├── Dataset (cached source query)
              └── Data Sources (Snowflake table/view ref)
```

### 2.3 Sigma access patterns

| Pattern | When | Pros | Cons |
|---|---|---|---|
| **Direct DB read** | Workbook reads `FINANCE_PROD.DATA_PRODUCTS.X` directly | Simple, low latency | No reusable metric layer |
| **MetricFlow via JDBC** | Workbook reads from `dbt-semantic-layer-jdbc` connection | Single metric definition; consistent across workbooks | Setup complexity, JDBC limits |
| **Sigma Dataset** | Cached materialized query atop DB or MetricFlow | Pre-aggregated, fast | Cache staleness; another layer |

**Best practice**: For canonical metrics (ARR / NRR / etc.) — use MetricFlow. For ad-hoc exploration — Sigma datasets backed by `DATA_PRODUCTS`.

### 2.4 Sigma — read-only access

Workbook readers can:
- View dashboards
- Filter / drill within workbook scope
- Export to CSV / PDF
- Schedule email delivery

Workbook editors can:
- Edit workbooks they own / co-own
- Create new workbooks
- Manage workspace permissions (if workspace admin)

Snowflake permissions: Sigma uses one service account role per env (`ROLE_SIGMA_READER_PROD`). All Sigma users SQL-as-Sigma-service-account; per-row access is enforced by Sigma user-context (not Snowflake row-level security).

### 2.5 Sigma anti-patterns

- ❌ Define metric logic in Sigma calculated columns when 3+ workbooks need the same metric
- ❌ Read directly from `MANAGED` or `STAGE` schemas (not contracted, no SLA)
- ❌ Build workbooks against raw SFDC tables (`BASE_PROD.SALESFORCE.*`)
- ❌ Use Sigma for ETL — it's a viz tool
- ❌ Skip access controls (workbook with no workspace owner → orphaned)

For Sigma deep-dive: `sigma-computing-analyst` skill.

---

## §3. Semantic layer — dbt MetricFlow

`eda-dbt-semantic-layer` defines canonical metrics that all BI tools consume.

### 3.1 Why a semantic layer

Without semantic layer:
```
Sigma workbook A: ARR = sum(amount) where stage = 'Closed Won' AND is_recurring = true
Sigma workbook B: ARR = sum(arr_usd_current) from FINANCE_LINE_ANALYTICS
Hex notebook:    ARR = sum(annualized_value) from custom-derived view
                                                                  ← All produce different numbers
```

With semantic layer:
```
metric: total_arr
  source: FINANCE_LINE_ANALYTICS
  measure: arr_usd_current
  filter: is_arr_eligible = true AND as_was_date = (max as_was_date)
  
                                                                  ← Defined ONCE, served to all tools
                                                                    Sigma / Hex / Hightouch all consume same metric
```

### 3.2 MetricFlow structure

```yaml
# semantic_models/finance/finance_line_analytics.yml
semantic_models:
  - name: finance_line_analytics
    description: "Per-line ARR/ACV/TCV facts at ALI × as_was_date grain"
    model: ref('finance_line_analytics')

    entities:
      - name: agreement_line_item
        type: primary
        expr: agreement_line_item_id
      - name: account
        type: foreign
        expr: account_id
      - name: product_l3
        type: foreign
        expr: product_code_l3

    dimensions:
      - name: as_was_date
        type: time
        type_params: { time_granularity: day }
      - name: fiscal_quarter
        type: categorical
      - name: arr_category
        type: categorical

    measures:
      - name: arr_usd_current_sum
        agg: sum
        expr: arr_usd_current
      - name: acv_usd_current_sum
        agg: sum
        expr: acv_usd_current

# metrics/finance/arr.yml
metrics:
  - name: total_arr_usd_current
    type: simple
    label: "Total ARR (USD Current)"
    description: |
      Sum of arr_usd_current at the latest as_was_date.
      Filters to is_arr_eligible = true.
    type_params:
      measure: arr_usd_current_sum
    filter: |
      {{ Dimension('agreement_line_item__is_arr_eligible') }} = true
      AND {{ Dimension('agreement_line_item__as_was_date') }} = (
        SELECT MAX(as_was_date) FROM {{ ref('finance_line_analytics') }}
      )

  - name: ndr_pct
    type: ratio
    label: "Net Dollar Retention %"
    type_params:
      numerator:
        name: net_retained_arr  # = begin_arr + expansion - churn - contraction
      denominator:
        name: begin_arr
    filter: |
      {{ Dimension('agreement_line_item__arr_category') }} IN ('BEGIN_ARR', 'EXPANSION', 'CHURN', 'CONTRACTION')
```

### 3.3 Metric types

| Type | Use case | Example |
|---|---|---|
| `simple` | Direct measure | ARR, ACV, count of opps |
| `ratio` | Numerator / denominator | NDR, win rate, conversion rate |
| `derived` | Combination of metrics | ARR growth (this_quarter - last_quarter) |
| `cumulative` | Running total over time | Cumulative pipeline created YTD |
| `conversion` | Funnel conversion between events | Lead → MQL → SQL → Opp |

### 3.4 Consumer access

**Via JDBC** (Sigma, Tableau, Hex):
```
JDBC URL: jdbc:semanticlayer://?environmentId=<id>
Auth: service token (per consumer)
SQL: SELECT * FROM {{ semantic_layer.metrics(["total_arr_usd_current"], group_by=["fiscal_quarter"]) }}
```

**Via Python** (Hex, custom apps):
```python
from dbt.semantic_layer.client import SemanticLayerClient

client = SemanticLayerClient(host="...", token="...")
df = client.query(
    metrics=["total_arr_usd_current"],
    group_by=["fiscal_quarter", "product_l3"],
    where="fiscal_year IN ('FY25', 'FY26')"
)
```

**Via REST**:
```bash
curl -X POST https://semantic-layer.cloud.getdbt.com/api/graphql \
  -H "Authorization: Bearer <token>" \
  -d '{ "query": "{ metric(name: \"total_arr_usd_current\") { value } }" }'
```

### 3.5 Versioning + governance

Canonical metric definitions are versioned via dbt's `version:` mechanism:
- Breaking change → bump version, deprecate old
- Additive change (new dimension) → no bump needed
- Renaming → use `previous_aliases` for graceful transition

For deep dive: `dbt-architect/semantic-layer.md`.

---

## §4. Tableau (legacy)

Tableau is being phased out but still serves:
- Select finance reports (board pack, audit reports)
- Legacy executive dashboards (pre-Sigma migration)

Pattern:
- Tableau Server reads from `FINANCE_PROD.DATA_PRODUCTS.*` via Snowflake connector
- Workbooks extract data nightly (Tableau Extract Refresh)
- No semantic layer integration (gap; not invested in for legacy tool)

Migration target: Move all Tableau workbooks to Sigma by end of FY27 (per BI strategy).

---

## §5. Hex (data science notebooks)

Hex is Workday's data science notebook platform — Snowflake-native.

Use cases:
- Ad-hoc analytics that don't fit in Sigma (Python ML, statistical tests)
- Prototype dashboards before formal Sigma build
- Data exploration during model development

Access:
- Reads from same `DATA_PRODUCTS` schemas as Sigma
- Service account: `ROLE_HEX_READER_PROD`
- Can call MetricFlow via Python SDK (best practice — keep metric definitions consistent with Sigma)

Anti-pattern: Hex notebook becomes a "shadow dashboard" with custom metric logic. Migrate to Sigma or escalate to formal data product.

---

## §6. Hightouch (reverse ETL)

Hightouch syncs Snowflake data BACK to operational tools.

### 6.1 Common syncs

| Source (Snowflake) | Destination | Use case |
|---|---|---|
| `SALES_PROD.MANAGED.WD_ACCOUNT_SCD2` (enriched fields) | Salesforce Account | Push account ARR, health score, segment back to SFDC for sales |
| `LOYALTY_ADVOCACY_PROD.MANAGED.CUSTOMER_HEALTH_SCORE` | Salesforce + Gainsight | Sync health score to CSM tools |
| `MARKETING_PROD.AGGREGATIONS.ABM_PENETRATION` | Marketo + 6Sense | Push ABM target list updates |
| `FINANCE_PROD.AGGREGATIONS.ARR_ACCOUNT_CATEGORIES` | Salesforce Account.ARR_USD__c | Show ARR in SFDC for sales context |
| `CDP person profiles` | Drift / Outreach / Marketo | Personalization signals |

### 6.2 Cadence

Most Hightouch syncs run hourly. Critical syncs (e.g., ABM list) run every 15 min.

### 6.3 Failure handling

Hightouch reports sync failures via Slack + email. Data engineering monitors sync health on dashboard `BI_WH_TOOLS.HIGHTOUCH_SYNC_STATUS`.

---

## §7. Custom apps / APIs

Some operational tools query Snowflake directly via custom microservices:
- Internal sales playbook tool reads ARR per account
- Internal CSM workspace reads customer 360 view
- Internal finance reporting app reads quarterly close metrics

Pattern:
- Microservice uses dedicated service account per app (auditable)
- Reads only from `DATA_PRODUCTS` schemas
- Uses Snowflake result caching for read-heavy queries
- For real-time: consider Snowflake Hybrid Tables (Unistore) — currently exploratory

---

## §8. Governance — who can publish, who can consume

### 8.1 Publication

Only the **domain-owning team** can publish to a domain's `DATA_PRODUCTS` schema:
- Finance team → `FINANCE_PROD.DATA_PRODUCTS.*`
- GTM team → `SALES_PROD.DATA_PRODUCTS.*`, `MARKETING_PROD.DATA_PRODUCTS.*`
- CX team → `*_PROD.DATA_PRODUCTS.*` (three sub-domains)
- Platform team → `FOUNDATIONAL_ASSETS_PROD.DATA_PRODUCTS.*`

Cross-domain publishing requires the producing team's approval + a contract.

### 8.2 Consumption

| Audience | Default access |
|---|---|
| BI tools (Sigma, Tableau, Hex) | Read access to all `DATA_PRODUCTS` schemas |
| Other dbt projects | Cross-project ref via `+access: public` |
| Custom apps | Read access via service account, scoped to needed schemas |
| Ad-hoc analyst SQL | Read via personal role (`ROLE_ANALYST_*`) |
| External (vendors, partners) | NOT allowed direct Snowflake access; use API layer |

### 8.3 Sensitive data

PII / sensitive fields tagged via Snowflake object tags:
- `data_classification: confidential` — restricted to specific roles
- `data_classification: restricted` — masked for most consumers
- `data_classification: public` — open access

Masking policies enforce automatically. For new sensitive data: tag at the source-table level; mask propagates downstream.

For governance deep-dive: `snowflake-architect/security-and-governance.md`.

---

## §9. Discovery + lineage

### 9.1 Atlan (primary catalog)

- Auto-ingested from Snowflake + dbt
- Searchable: tables, columns, metrics
- Lineage: source → BI dashboard
- Owner / domain / SLA visible
- Used by analysts to find data before building dashboards

### 9.2 dbt docs

- Per-project documentation
- Auto-generated from YAML
- Includes graph view of model dependencies
- Used by AEs for development

### 9.3 Discovery flow for analysts

```
1. Q: "Where can I find ARR by region?"
2. Search Atlan: "ARR region"
3. Find: ARR_REGION_SEGMENT_CATEGORIES + ARR_PRODUCT_NDR_DASH_V2
4. Click → see owner, SLA, lineage, sample SQL
5. Request Snowflake access (if needed) via standard access flow
6. Build Sigma workbook
```

---

## §10. Self-service patterns (and limits)

Self-service BI works when:
- ✅ The metric is canonical (in semantic layer or `DATA_PRODUCTS`)
- ✅ The data is well-documented
- ✅ The analyst is using approved tools (Sigma, Hex)

Self-service BI **breaks** when:
- ❌ Analyst reinvents a metric in workbook (drift)
- ❌ Analyst reads from `STAGE` or `MANAGED` schemas (not contracted)
- ❌ Analyst joins disparate sources without understanding grain
- ❌ Analyst builds "production-critical" workbook without going through governance

Guardrails:
- Sigma read access to `STAGE` / `MANAGED` is restricted to a small AE/analyst group, not org-wide
- Workbook usage analytics in Sigma — alert on high-traffic workbook that bypasses semantic layer
- Quarterly review: identify shadow metrics and either canonicalize or sunset

---

## §11. Performance + cost

### 11.1 BI query cost attribution

BI queries hit Snowflake `BI_WH` (dedicated warehouse). Cost attribution:
- Tag every BI query with workbook ID (Sigma adds `comment` to SQL)
- Roll up via `QUERY_HISTORY` → cost per workbook / per dashboard
- Top-N expensive dashboards reviewed monthly

### 11.2 Caching strategy

| Layer | Cache type | TTL |
|---|---|---|
| Snowflake | Result cache | 24 hr (or until data change) |
| Sigma | Dataset cache (materialized) | 1-4 hr (configurable) |
| MetricFlow | Query cache | 15 min |

For high-traffic dashboards (CFO daily pack): pre-warm cache via scheduled query.

### 11.3 Concurrency

`BI_WH` is multi-cluster (auto-scale out): handles 100+ concurrent users. Avoid putting heavy ETL workloads on `BI_WH` — dedicated `PROD_BATCH_WH` for that.

---

## §12. Anti-patterns + recovery

### 12.1 Anti-patterns

| Anti-pattern | Recovery |
|---|---|
| Metric defined 3+ places (Sigma, dbt, Hex) | Canonicalize in `eda-dbt-semantic-layer`; deprecate copies |
| Dashboard reads from raw SFDC table | Refactor to read from `MANAGED` SCD2 wrapper |
| 100+ workbooks bypass semantic layer | Office hours + migration push; track adoption % |
| Shadow data products in Hex notebooks | Identify, escalate to enterprise data product if widely-used |
| Cost spike on `BI_WH` | Identify top-N queries via QUERY_HISTORY; optimize / restrict |
| Dashboard out of sync with executive deck | Both should consume semantic layer; if not, reconcile + migrate |
| Tableau workbook with custom SQL | Migrate to Sigma; encode logic in dbt + semantic layer |

### 12.2 Recovery patterns

For a major metric divergence (executive notices "ARR is wrong"):

```
1. Identify all consumers of the metric (Sigma + Tableau + Hex + apps)
2. Identify the variants currently in production (canonical vs shadow)
3. Reconcile: which is correct? Update canonical if needed.
4. Migration plan:
    a. Canonicalize in eda-dbt-semantic-layer
    b. Update top-3 dashboards to use canonical
    c. Announce: "Old metric X deprecated; migrate to canonical"
    d. Sunset deprecated copies after 60-90 days
5. Postmortem: how did divergence happen? Strengthen guardrails.
```

---

## §13. Roadmap items (2026-2027)

| Initiative | Status |
|---|---|
| Migrate all Tableau → Sigma | In progress (target FY27) |
| Adopt dbt Semantic Layer broadly (currently selective) | In progress |
| Hightouch sync expansion (more reverse-ETL endpoints) | Ongoing |
| Snowflake Hybrid Tables for operational reads | Exploratory |
| Cortex AI for natural-language queries on metrics | Exploratory |
| Atlan as primary catalog (vs DataHub) | Live, expanding |
| Real-time dashboards (Snowflake Dynamic Tables) | Selective use |

---

## §14. Cross-references

- `enterprise-data-products-catalog.md` — what gets consumed
- `platform-architecture.md` — where BI fits in the stack
- `dbt-architect/semantic-layer.md` — MetricFlow deep dive
- `sigma-computing-analyst` skill — Sigma workbook patterns
- `analytics-engineering-architect/semantic-layer-architecture.md` — semantic layer principles
- `snowflake-architect/security-and-governance.md` — access control
