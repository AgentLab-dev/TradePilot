# dbt-mesh, Contracts, Versions, Groups, Access Modifiers

Reference companion to `dbt-architect/SKILL.md` §3.

## 1. Why dbt-mesh exists

A single dbt project that crosses 4+ teams and 400+ models hits scaling cliffs:

| Symptom | Root cause | Mesh fix |
|---|---|---|
| CI build > 30 min on every PR | `state:modified+` blast radius = whole project | Split by ownership boundary; CI on one project only |
| "Who owns this model?" requires `git blame` archaeology | Flat namespace, no groups | `groups:` + `meta.owner` |
| Producer changes a column → silent failure in 3 dashboards | No schema contract at the project boundary | `contract: enforced` on the boundary model |
| Two teams iterate on the same model and overwrite each other | Shared ownership | Group + `access: private` |
| "Can I rename this column safely?" requires manual consumer audit | No version tooling | `versions:` block + `deprecation_date` |

A mesh is a **graph of dbt projects** that `ref()` each other via `ref('upstream_project', 'model_name')`. Each project has its own `dbt_project.yml`, its own deploy schedule, its own ownership, and publishes a manifest that downstream projects defer against.

## 2. Project split criteria — the 5-rule test

Split into a separate project when **at least one** is true:

1. **Deploy cadence diverges by 2× or more.** E.g., raw SCD2 = hourly, finance daily.
2. **Ownership boundary** — different teams, different on-call, different review process.
3. **Consumer count ≥ 3** with breaking-change risk (any change to the producer might break the consumer).
4. **Blast radius** — `state:modified+` from typical PR exceeds 50% of total model count.
5. **CI time > 30 min** for typical PRs.

Conversely, **don't split** just because the project is "big" — splitting adds:
- Manifest pinning overhead (downstream project pins upstream manifest version)
- Cross-project `ref()` resolution at parse time (slows parse)
- Multi-repo PR coordination cost
- Mesh-level versioning (you now have a versioned API to maintain)

## 3. Cross-project reference syntax

In the **consumer** project:

```sql
-- models/finance/.../stg_em_account_as_was.sql
select * from {{ ref('eda_dbt_gtm', 'wd_account_scd2') }}
```

`'eda_dbt_gtm'` is the **dbt project name** (from upstream's `dbt_project.yml::name`), not the GitHub repo name. Always inspect upstream's `dbt_project.yml` before writing the ref.

### Required setup in the consumer's `dependencies.yml`

```yaml
projects:
  - name: eda_dbt_gtm
  - name: eda_dbt_common
  - name: eda_dbt_base
```

Run `dbt deps` to fetch upstream manifests. Without `dbt deps`, the parse fails with "model not found".

### Producer manifest publishing

The producer must publish its manifest somewhere the consumer can fetch:
- dbt Cloud: enable "Production environment publishes manifest" toggle.
- dbt Core / GitHub Actions: upload `target/manifest.json` as a release asset, S3 object, or artifact registry.

Consumer fetches via `dbt deps` (dbt Cloud) or a script that hits the publishing URL (dbt Core).

## 4. Model contracts — the principal-level guardrail

A **contract** is a YAML-level promise about the model's output schema. Enforced at compile time.

### Minimal contract

```yaml
models:
  - name: finance_line_analytics
    config:
      contract:
        enforced: true
    columns:
      - name: as_was_date
        data_type: date
        constraints:
          - type: not_null
      - name: agreement_line_item_id
        data_type: varchar
        constraints:
          - type: not_null
      - name: arr_usd_current
        data_type: number(38,2)
```

When `contract.enforced: true`, dbt:
- Compares the YAML column list against the SQL `select` projection.
- Fails compile if column counts mismatch, names mismatch, types mismatch, or constraints fail.
- Enforces `not_null`, `unique`, `primary_key`, `foreign_key`, `check` (Snowflake supports `not_null`, `unique`, `primary_key`, `foreign_key`).

### What contracts catch (real failure modes)

| Failure | Without contract | With contract |
|---|---|---|
| Producer renames a column | Silently breaks consumer at runtime | Build fails at compile time |
| Producer changes type from `varchar(10)` to `varchar(50)` | Consumer truncates silently | Build fails at compile time |
| Producer adds a column at position 3 | Consumer SELECT-by-position breaks | Build fails (column count mismatch) |
| Producer removes a NOT NULL guarantee | Downstream join nullifies silently | Build fails (constraint violation) |

### Where to apply contracts

| Layer | Contract? | Why |
|---|---|---|
| `source()` | No | Source schema is owned by upstream system, not dbt |
| `stg_*` | No | Iterates too fast; contracts would slow team velocity |
| `int_*` | No (private group) | Internal use only, no cross-project consumers |
| `bt_*` consumed within project only | Optional | Add when 5+ downstream `bv_*` views depend on it |
| `bt_*` consumed cross-project | **MANDATORY** | This is the mesh boundary |
| Public datamart (consumed by BI / Tableau / Sigma) | **MANDATORY** | BI tools have no schema-evolution tolerance |

## 5. Versions — for breaking changes

When you must change a contracted column, **version** the model instead of editing it:

```yaml
models:
  - name: finance_line_analytics
    latest_version: 2
    config:
      contract: {enforced: true}
    versions:
      - v: 1
        defined_in: finance_line_analytics    # default: same as model name
        deprecation_date: 2026-12-31
      - v: 2
        defined_in: finance_line_analytics_v2
        columns:
          # full v2 column list here (may differ from v1)
```

### Two physical model files

```
models/
  finance/
    finance_line_analytics.sql       # the v1 model
    finance_line_analytics_v2.sql    # the v2 model
```

### Consumer migration

```sql
-- Before migration: pin to v1
{{ ref('finance_line_analytics', v=1) }}

-- After migration:
{{ ref('finance_line_analytics', v=2) }}

-- Unversioned ref: uses latest_version
{{ ref('finance_line_analytics') }}
```

### Deprecation enforcement

When `deprecation_date` passes, dbt **fails parse** on any `ref()` to the deprecated version. This is your guardrail against indefinite tech debt accumulation.

### latest_version_pointer (dbt 1.10+)

```yaml
flags:
  state_modified_compare_more_unrendered_values: true   # for State accuracy
  source_freshness_run_project_hooks: false              # avoid hook fanout
  latest_version_pointer: true                            # auto-create unversioned alias
```

With `latest_version_pointer: true`, dbt creates a Snowflake view named `finance_line_analytics` that points at the latest-version physical model. Consumers can keep `ref('finance_line_analytics')` (unversioned) and they automatically get the latest version. Slow-migrating consumers pin `v=1` explicitly.

## 6. Groups + access modifiers

Groups answer "who can `ref()` this model?".

```yaml
# models/finance/_groups.yml
groups:
  - name: finance_internal
    owner:
      name: AE team
      email: [REDACTED_EMAIL]
      slack: "#ae-team"
  - name: finance_published
    owner:
      name: Finance Analytics
      email: [REDACTED_EMAIL]
```

```yaml
# Per model:
models:
  - name: int_agree_enriched
    group: finance_internal
    access: private              # only models in finance_internal group may ref()

  - name: finance_line_analytics
    group: finance_published
    access: public                # any project may ref() this
    config:
      contract: {enforced: true}
```

### Access modifiers

| Access | Meaning | Use when |
|---|---|---|
| `private` | Only models within the **same group** may `ref()` | Helper / internal-only model |
| `protected` (default) | Models within the same **project** may `ref()` | Most internal models |
| `public` | Any project (including cross-project) may `ref()` | Mesh boundary models |

Combined with contracts, the access modifier gives you a typed, versioned, ownership-tagged public API for your data products.

## 7. The mesh-level governance checklist

Before publishing a mesh boundary model as `public`:

- [ ] Contract enforced (`contract.enforced: true`)
- [ ] All columns have `data_type`
- [ ] PK columns have `not_null` + `unique` + `primary_key` constraints
- [ ] Grain documented in YAML `description`
- [ ] `meta:` block has `owner`, `slack`, `service_level_objective` (freshness target)
- [ ] Source freshness configured on upstream sources
- [ ] At least one `unit_test:` covering core business logic
- [ ] CI runs `dbt build --select +my_model+` on every PR
- [ ] Manifest pinned to a published, immutable version (not a moving tag)

## 8. Failure modes — mesh

| Symptom | Root cause | Fix |
|---|---|---|
| `Model 'X' not found in project 'Y'` at parse time | Stale upstream manifest | `dbt deps` to refresh; check upstream manifest URL |
| Cross-project ref breaks after upstream deploy | Upstream renamed model | Upstream should have versioned + deprecation_date'd, not renamed |
| Consumer build fails: "column count mismatch" | Producer added a column without contract update | Add the column to producer's YAML contract; re-build |
| Consumer build fails: "constraint primary_key violated" | Producer's source data has duplicates | This is the contract doing its job — fix the upstream data or relax the constraint |
| `state:modified+` rebuilds whole DAG after upstream parse | Upstream YAML formatting change (not logical) | Set `state_modified_compare_more_unrendered_values: true` in flags |
| Manifest version conflict between two upstream projects | Each upstream pinned different manifest version | Standardize manifest publishing schedule across all upstreams |
| `dbt deps` is slow (>30s) | Many upstream projects | Switch to manifest URLs instead of full project clones |

## 9. Real-world ownership matrix (annotated example)

```
┌──────────────────┬──────────────┬──────────────────────────────────────┐
│ Project          │ Cadence      │ Public boundary models                │
├──────────────────┼──────────────┼──────────────────────────────────────┤
│ eda_dbt_base     │ Hourly       │ base_unified_history_*_scd2 (35 models)│
│ eda_dbt_common   │ Hourly       │ wd_user_scd2, wd_calendar (8 models) │
│ eda_dbt_gtm      │ Daily 02:00  │ wd_account_scd2, wd_proposal_* (40)  │
│ eda_dbt_em       │ Daily 03:00  │ finance_line_analytics, arr_*_categ. │
│ eda_dbt_cx       │ Daily 03:30  │ cx_account_health, cx_renewal_risk   │
└──────────────────┴──────────────┴──────────────────────────────────────┘
```

Each row in this table is a mesh node. The boundary models in the right column are the public API of that node. Every one of them must have a contract + group + access: public.

## 10. Anti-patterns to refuse in code review

| Anti-pattern | Why it's bad | Refusal script |
|---|---|---|
| Cross-project `source()` directly (skip ref) | Bypasses mesh boundary; no contract enforcement | "Switch to `ref('upstream_project', '<model>')`. We don't `source()` across projects." |
| Public model with no contract | Silent breakage risk | "Public access requires `contract: enforced`. Add the YAML or make it `protected`." |
| Versioning without a contract | Just two copies of the same file with no API guarantee | "Versions enforce contracts. Add `contract: enforced` to the base model first." |
| `private` access on a model that's actually consumed by 3 groups | The team will hit `access denied` and just remove the modifier next sprint | "Either move the model to a shared group or make it `protected`. Don't paper over the boundary." |
| `latest_version` left pinned at v1 for >6 months | The whole reason for versioning is migration; if v1 is the latest, why version? | "Either remove the version (revert to single file) or commit to migrating consumers to v2 with a date." |
