# dbt Model Design Patterns

## CTE-First SQL Style

All models must follow the CTE-first pattern. No subqueries in FROM or WHERE clauses.

```sql
with

source_data as (
    select ...
    from {{ ref('stg_em_account_scd2') }}
),

transformed as (
    select
        account_id,
        account_name,
        upper(region) as region,
        coalesce(annual_revenue, 0) as annual_revenue
    from source_data
),

final as (
    select *
    from transformed
    where is_deleted = false
)

select * from final
```

**Rules:**
- Leading commas for column lists
- Lowercase SQL keywords
- One CTE per logical transformation step
- Final CTE named `final`
- `select * from final` as the last statement
- No `select *` in intermediate CTEs — explicitly list columns

---

## Naming Conventions

### Models

| Layer | Pattern | Example |
|-------|---------|---------|
| Staging table | `stg_{source}_{entity}` | `stg_em_account_scd2` |
| Staging view | `stg_{source}_vw_{entity}` | `stg_em_vw_ref_product_hierarchy` |
| As-was wrapper | `stg_{source}_{entity}_as_was` | `stg_em_account_as_was` |
| Intermediate | `stg_{source}_int_{entity}` or `int_{entity}` | `stg_em_int_opp_base` |
| Business table | `bt_{domain}` | `bt_sku_analytics` |
| Business view | `bv_{domain}` | `bv_acv_booking_new_hierarchy` |
| Lookup | `stg_{source}_lkp_{entity}` | `stg_em_lkp_strategic_partners` |

### Columns

- `snake_case` for all column names
- Suffix `_id` for identifiers: `account_id`, `opportunity_id`
- Suffix `_at` for timestamps: `created_at`, `updated_at`
- Suffix `_date` for dates: `close_date`, `start_date`
- Suffix `_amount` or `_amt` for monetary values: `total_amount`, `acv_amt`
- Prefix `is_` for booleans: `is_deleted`, `is_active`
- Prefix `has_` for boolean flags: `has_renewal`, `has_services`

---

## Materialization Decision Tree

```
Is the model a simple rename/cast/filter of a source?
├── Yes → VIEW (staging)
└── No
    ├── Is it used by many downstream models?
    │   ├── Yes → TABLE
    │   └── No
    │       ├── Is the source data >10M rows?
    │       │   ├── Yes → INCREMENTAL
    │       │   └── No → TABLE or EPHEMERAL
    │       └── Is it only used by one downstream model?
    │           └── Yes → EPHEMERAL (if simple) or TABLE (if complex)
```

### Incremental Model Pattern

```sql
{{
    config(
        materialized='incremental',
        unique_key=['id', 'as_was_date'],
        incremental_strategy='merge',
        on_schema_change='append_new_columns'
    )
}}

with

source_data as (
    select *
    from {{ source('base_prod', 'UNIFIED_HISTORY_ACCOUNT_SCD2') }}
    {% if is_incremental() %}
    where ref_date > (select max(ref_date) from {{ this }})
    {% endif %}
),

final as (
    select
        id,
        as_was_date,
        ...
    from source_data
)

select * from final
```

**Incremental checklist:**
- `unique_key` must match the actual grain
- `incremental_strategy='merge'` for SCD2 (upsert on key)
- Always have a `{% if is_incremental() %}` filter on the source
- Use `on_schema_change='append_new_columns'` to handle upstream additions
- Test with `--full-refresh` after any logic change

### Microbatch incremental (dbt 1.9+, GA on Snowflake)

For high-volume, time-series-shaped models, prefer the **microbatch** strategy over hand-rolled
`is_incremental()` date filters. dbt splits the load into independent, parallel, retryable batches and
auto-generates the time filters from `event_time` — no manual `where ref_date > max(...)` needed.

```sql
{{
    config(
        materialized='incremental',
        incremental_strategy='microbatch',
        event_time='ref_date',
        batch_size='month',
        lookback=1,
        unique_key=['id', 'as_was_date']
    )
}}

select id, as_was_date, ref_date, ...
from {{ source('base_prod', 'UNIFIED_HISTORY_ACCOUNT_SCD2') }}
-- no is_incremental() filter required: dbt derives the batch window from event_time
```

Backfill a specific window: `dbt run --select my_model --event-time-start 2026-01-01 --event-time-end 2026-04-01`.
1.12 fixed concurrent-batch deadlocks and ensures retries reuse the original invocation time.

### dbt State (v1.12+, Preview) — reuse instead of rebuild

`dbt State` compares each node's logic + data to prior builds and **skips** (reuses in place) or
zero-copy **clones** unchanged nodes, auto-deferring to prod without manual `--defer`/`--state`. On a
large DAG like the ARR engine this avoids rebuilding unchanged `stg_em_*` / `arr_*` nodes. Opt-in only:
`--manage-state` flag, `DBT_ENGINE_MANAGE_STATE=true`, or `manage_state: true` in the
`dbt_project.yml` flags block. Failed-test and externally-deleted tables are rebuilt automatically.

---

## SCD2 Patterns

### SCD2 Staging (from source)

Uses the `scd2_incremental_code` macro:
- Sources from `UNIFIED_HISTORY_*_SCD2` tables
- Grain: `(ID, AS_WAS_DATE)`
- `as_was_date` variable controls the point-in-time cutoff
- `REF_DATE` tracks the source load date

### As-Was Wrappers

Provide a current-state view of SCD2 data:

```sql
select *
from {{ ref('stg_em_account_scd2') }}
where as_was_date = {{ var('as_was_date') }}
```

### When to Use Each

| Need | Pattern |
|------|---------|
| Full history analysis | Query SCD2 table directly |
| Current-state snapshot | Use as-was wrapper |
| Point-in-time reporting | Override `as_was_date` variable |
| Trend analysis | Join SCD2 on date dimension |

---

## Cross-Project References

This project references models from `eda_dbt_base`:

```sql
{{ ref('eda_dbt_base', 'base_google_sheets_ref_product_hierarchy') }}
{{ ref('eda_dbt_base', 'base_salesforce_agreement') }}
```

**Rules:**
- Always use two-argument `ref()` for cross-project references
- Never hardcode database/schema names
- Document cross-project dependencies in model YAML

---

## Macro Patterns

### Override Logic

Category overrides use seed-driven column replacement:
- `override_replace_logic` — replaces column values from override seeds
- `override_exclude_logic` — excludes rows based on override criteria
- `get_override_*_columns` — dynamically retrieves override column lists

### Currency Conversion

Three currency table types used across finance models:
- `constant_currency_table` — fixed exchange rates for budget comparison
- `historical_currency_table` — rates at time of transaction
- `actual_currency_table` — current exchange rates

### UDF Pattern

Snowflake UDFs defined in `functions/` directory and referenced via macros:
- `udf_tcv_to_acv` — TCV to ACV conversion
- `udf_tcv_to_arr` — TCV to ARR conversion
- `udf_ssr_process` — SSR agreement processing

---

## Unit Tests (GA) — logic validation with mocked inputs

Unit tests validate transformation **logic** against fixed, mocked inputs (no warehouse data), so they
run fast in CI and catch regressions in complex business rules. Ideal for the ARR category / SSR /
currency-conversion logic and the `functions/` TVFs.

```yaml
# in a model's schema YAML
unit_tests:
  - name: test_arr_category_ssr_reclass
    model: arr_product_categories
    given:
      - input: ref('stg_arr_categories_up_for_renewal')
        rows:
          - {agreement_id: 'a1X...GAh8NUAT', fiscal_quarter_name: 'FY25-Q4', arr_category: 'Contraction'}
      - input: ref('stg_arr_categories_begin_balances')
        rows: []
    expect:
      rows:
        - {agreement_id: 'a1X...GAh8NUAT', arr_category: 'Product Churn'}
```

Run only unit tests: `dbt test --select unit_test:*`. As of 1.12 they parse macros, support sources
with duplicate names, and are skipped automatically when their model is disabled.

---

## Model Organization Checklist

When creating a new model:

1. **Choose the right layer** (staging / intermediate / mart)
2. **Follow naming conventions** (prefix, snake_case)
3. **Set materialization** (view / table / incremental / **microbatch** for large time-series)
4. **Write CTE-first SQL** with explicit column lists
5. **Create a YAML file** with:
   - Model description (including grain)
   - Column descriptions for key columns
   - `unique` + `not_null` tests on primary key
   - `relationships` tests for foreign keys
6. **Add a unit test** for any non-trivial business logic (category/SSR/currency rules)
7. **Add to the appropriate group** in `dbt_project.yml` if needed
8. **Run and test** locally before PR: `dbt build --select +model_name`
