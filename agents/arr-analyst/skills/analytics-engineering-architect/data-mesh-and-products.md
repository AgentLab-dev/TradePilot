# Data Mesh, Data Products, Contracts

Reference companion to `analytics-engineering-architect/SKILL.md` §3.

## 1. Why data mesh

The traditional pattern: central data team owns all pipelines. Consequences:

- Central team becomes the bottleneck (every new request waits in queue)
- Central team loses domain knowledge (sales knows sales better than data team)
- Central team's roadmap doesn't match every consumer's priority
- Quality is reactive (consumers report bugs after they hit dashboards)

Data mesh decentralizes: each business domain owns its data products. The central team becomes a platform team — providing infrastructure, standards, and tools.

## 2. Data mesh — Zhamak Dehghani's 4 principles

### Principle 1: Domain ownership

Data is owned by the team closest to the source / use. Example:

| Domain | Owns | Models |
|---|---|---|
| Salesforce admin team | `wd_account_scd2`, `wd_proposal_*` | Source-of-truth GTM tables |
| Finance team | `finance_line_analytics`, `arr_*_categories` | Revenue metrics |
| Marketing team | `mql_*`, `campaign_attribution_*` | Lead-source metrics |
| Customer support | `cx_account_health`, `cx_renewal_risk` | Customer-success metrics |

Each team has:
- Their own dbt project (or namespace in shared project)
- Their own deploy cadence
- Their own on-call
- Their own consumers + SLAs

### Principle 2: Data as a product

Each data set is a product, not a byproduct. Has:

- **Owner** (named person + team)
- **Purpose** (why does it exist?)
- **Consumers** (who uses it, for what?)
- **SLA** (freshness, completeness, accuracy)
- **Schema contract** (what columns, what types, what guarantees)
- **Documentation** (in the catalog)
- **Discoverable** (searchable)
- **Versioned** (breaking changes are versioned)
- **Observable** (monitored for breaches)
- **Trustworthy** (passes tests in CI)

### Principle 3: Self-serve platform

The central platform team provides:
- Snowflake account + warehouse provisioning
- dbt Cloud + CI/CD infrastructure
- Catalog (DataHub / Atlan)
- Observability (Monte Carlo / Sifflet)
- Shared macros + standards
- Onboarding docs

Domain teams provide:
- The actual models / data products
- Domain logic
- Documentation
- On-call coverage

### Principle 4: Federated governance

Global standards (enforced by platform team via CI):
- Naming conventions (snake_case, prefixes)
- Required tests on PK
- Contracts on public models
- Tag-based PII classification

Local autonomy (within standards):
- What models to build
- What tests to add beyond the minimum
- How to model the data
- When to refactor

## 3. When mesh is worth the complexity

| Indicator | Threshold | Mesh value |
|---|---|---|
| Distinct business domains | 5+ | High |
| Total data engineers (across all teams) | 50+ | High |
| Central team's PR queue depth | > 2 weeks | High |
| Cross-team coordination time | > 30% of dev time | High |
| Domain-specific bugs caught late | Frequent | High |
| ALL data engineers on one team | < 10 engineers | LOW (premature) |
| Single-source-of-truth requirement | Strong | LOW |
| Highly regulated / centralized governance | Strong | LOW |

### Wrong reasons to do mesh

- "It's the hot new architecture" (technology fashion)
- "Our central team is slow" (might be a process / capacity issue, not an architectural one)
- "We want to scale" (scaling without mesh is fine for years)

### Right reasons

- Different domains have different deploy cadences AND that's causing friction
- Central team's roadmap doesn't match the business need
- Domain teams have engineers ready to own data
- The cost of central-team coordination > the cost of distributed coordination

## 4. The hub-and-spoke vs full mesh tradeoff

| | Hub-and-spoke | Full mesh |
|---|---|---|
| Topology | Central platform + domain teams | Domains connect peer-to-peer |
| Coordination cost | Lower | Higher |
| Domain autonomy | Lower | Higher |
| Best for | 5-20 teams | 20+ teams |

Most real implementations are hub-and-spoke. Pure mesh works for very large orgs.

## 5. Implementation patterns

### Pattern A: shared dbt project with groups (light mesh)

Single dbt project, but:
- Each domain has its own folder + group + access modifiers
- Cross-team consumption via `access: public` + `contract`
- Each domain owns their own folder

Pros: simpler ops, one repo, one CI
Cons: shared deploy cadence

### Pattern B: separate dbt projects with mesh (full mesh)

Each domain has its own dbt project. Cross-project refs via dbt-mesh.

Pros: independent deploy cadence, independent CI
Cons: more ops overhead (multiple manifests, dependency management)

See `dbt-architect/mesh-and-contracts.md` for the technical pattern.

### Pattern C: virtual mesh (shared models, distributed ownership)

One project, but ownership is metadata only:
- `meta.owner` on every model
- PRs to a model require code-owner approval
- CI enforces ownership rules

Pros: no infra change, fast adoption
Cons: no operational separation (one bad deploy affects everyone)

## 6. Data products — the canonical definition

```yaml
# data_product.yml
data_product: finance_line_analytics
description: |
  Authoritative ARR at agreement-line-item grain per as_was_date.
  Drives all ARR aggregates and downstream finance dashboards.
owner:
  team: ae_team
  slack_channel: '#ae-team'
  primary: [REDACTED_EMAIL]
  secondary: [REDACTED_EMAIL]
consumers:
  - team: finance_analytics
    use_case: monthly ARR reporting
  - team: gtm_strategy
    use_case: territory planning
  - team: ml_team
    use_case: churn prediction features

sla:
  freshness:
    target: 24h
    measurement: max(current_time - last_load_time)
    alert_threshold: 30h
  completeness:
    target: 99.5%
    measurement: matched_rows / expected_rows
  accuracy:
    target: < $1 variance vs Salesforce
    measurement: see tests/finance/assert_arr_sum_matches_sf.sql

contract:
  enforced: true
  schema: see finance_line_analytics.yml columns block

versioning:
  current: v2
  deprecated_versions:
    - v: 1
      deprecation_date: 2026-12-31

operational:
  on_call: [REDACTED_EMAIL]
  runbook: https://wiki.workday.com/runbook/fla
  pagerduty: https://workday.pagerduty.com/services/abc123
  source_jira: PROJ-123
```

## 7. Data contracts — the technical enforcement

A contract is a schema promise. Three levels:

### Level 1: dbt YAML contract (compile-time)

```yaml
models:
  - name: finance_line_analytics
    config:
      contract: {enforced: true}
    columns:
      - name: as_was_date
        data_type: date
        constraints: [{type: not_null}, {type: primary_key}]
      - name: arr_usd_current
        data_type: number(38,2)
```

dbt fails the build if the model's actual schema doesn't match. See `dbt-architect/mesh-and-contracts.md` §4.

### Level 2: Schema registry / catalog enforcement

In catalog tools (Atlan, DataHub):
- Schema version stored on every dataset
- Consumers register their dependence
- Changes notify consumers
- Breaking changes block deploy unless consumers approve

### Level 3: Runtime contract validation

```python
# In consumer code (e.g., a BI tool or Python script)
from pydantic import BaseModel

class FinanceLineAnalyticsRow(BaseModel):
    as_was_date: date
    agreement_line_item_id: str
    arr_usd_current: Decimal

# Validate every row
for row in snowflake_result:
    validated = FinanceLineAnalyticsRow.model_validate(row)
```

If the producer breaks contract, consumer crashes loudly (much better than silent corruption).

## 8. Ownership boundaries — defining them well

| Boundary to define | Question |
|---|---|
| Source of truth | Which team is canonical for this metric? |
| Code ownership | Who can merge changes to this model? |
| Operational ownership | Who gets paged when it breaks? |
| Cost ownership | Whose budget is the warehouse credit charged to? |
| Consumer relationship | Who is the customer for this data? |

### Bad ownership patterns

- Shared ownership of a single model — "everyone owns it = no one owns it"
- Engineering owns business logic — "wait, was that intentional?"
- Pre-prod consumers — central team builds it, business teams "use" but don't own

### Good ownership patterns

- Single named owner per data product
- Domain team owns the business logic; platform team owns the infra
- Consumer teams know who their producer is + how to contact them

## 9. The migration playbook: monolith → mesh

Phase 1 (months 1-3): foundation

- Catalog all existing models; assign tentative owners
- Identify the natural domain boundaries
- Set up platform infrastructure (CI/CD, observability, catalog)
- Train domain teams on dbt + Snowflake + standards
- Pilot with ONE domain (e.g., GTM) — give them their own dbt project

Phase 2 (months 4-9): expansion

- Migrate 3-5 more domains
- Establish federated governance (review board, standards)
- Add contracts on cross-team boundaries
- Build observability + SLAs

Phase 3 (months 10-18): maturity

- All domains have their own projects
- Mesh boundaries are stable
- SLAs are tracked + met
- Domain teams operate independently

Phase 4 (year 2+): optimization

- Cost attribution complete
- Self-service onboarding for new domains
- Platform team focused on platform, not models

### Migration anti-patterns

- "Big bang" reorg — fails because teams aren't ready
- Mesh-by-decree (no team buy-in) — produces malicious compliance
- Skipping platform investment — domains get blocked on infra
- No contracts in the first wave — drift accumulates

## 10. Federated governance — the standards

Global standards (enforced by CI):

### Naming
- `snake_case` everywhere
- Model prefix per layer (`stg_`, `int_`, `bt_`, `bv_`)
- Domain prefix in model name (`bt_finance_*`, `bt_gtm_*`)

### Testing
- Every fact / dim has `unique` + `not_null` on PK
- Every source has freshness test
- Every public model has at least one unit test

### Contracts
- Every public model has `contract: enforced`
- Every public model has `meta.owner` + `meta.slack_channel`

### Documentation
- Every model has a `description`
- Every column on public models has a `description`

### Tag-based governance
- PII columns tagged `pii_type=<email|phone|ssn|name>`
- Confidential columns tagged `classification=confidential`
- Tags auto-apply masking + access policies

Local autonomy:
- What models to build
- How to structure internal logic
- When to refactor
- Beyond-the-minimum tests
- Domain-specific patterns

## 11. Operational considerations

### On-call

Each domain team has its own on-call rotation for their data products. The platform team has its own on-call for platform infra.

### Incident process

When a data product breaks:
1. On-call for that data product is paged
2. They triage; if it's a platform issue, escalate to platform team
3. They communicate to known consumers (Slack, status page)
4. They write a postmortem within 5 business days

### Cross-team incident

When multiple data products are affected (e.g., upstream source change):
1. The shared platform on-call coordinates
2. Each affected domain triages their own product
3. One postmortem with all teams' input

## 12. Anti-patterns

| Anti-pattern | Why bad | Better |
|---|---|---|
| Forming a "data mesh team" as if it's a single project | Mesh is organizational, not a team | Form a platform team; transition ownership over time |
| Demanding mesh adoption before teams are ready | Malicious compliance | Find willing partners; expand from successes |
| Skipping contracts | Drift inevitable | Contracts before going mesh-public |
| No ownership tracking | "Who owns this?" archaeology | Catalog with ownership; CI enforces meta.owner |
| Domain teams build their own ingestion / observability | Wheel reinvention | Platform provides; domains consume |
| Mesh without a catalog | Discoverability dies | Catalog is the mesh's nervous system |
| One enormous data product covering 50 use cases | Defeats decentralization | Split into multiple, each with clear scope |
| Refusing to deprecate old versions | Tech debt accumulates | Every version has a deprecation_date from birth |
