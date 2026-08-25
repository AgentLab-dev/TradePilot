# Advanced Macros, Custom Materializations, and Adapter Dispatch

Reference companion to `dbt-architect/SKILL.md` §1 and §5.

## 1. Jinja — what every principal needs to know

dbt is two passes: **parse** (Jinja → SQL with refs/sources resolved) and **execute** (run SQL in the warehouse). Most Jinja gotchas come from confusing the two.

### Compile-time vs runtime

```sql
-- Compile-time (Jinja runs locally; SQL is fixed at parse time)
{% set columns = ['arr_usd_current', 'arr_usd_hist', 'arr_usd_actual'] %}
select
    {% for col in columns %}
        {{ col }} {% if not loop.last %},{% endif %}
    {% endfor %}
from {{ ref('finance_line_analytics') }}

-- Runtime (Jinja + adapter call to warehouse, then SQL is fixed)
{% set cols_query %}
    select column_name from information_schema.columns
    where table_name = 'FINANCE_LINE_ANALYTICS'
{% endset %}
{% set results = run_query(cols_query) %}
{% if execute %}
    {% set columns = results.columns[0].values() %}
{% else %}
    {% set columns = [] %}
{% endif %}
select {{ columns | join(', ') }} from {{ ref('finance_line_analytics') }}
```

### The `execute` guard (essential)

```jinja
{% if execute %}
    {{ log("Running this only during execute phase, not during parse", info=True) }}
    {% set result = run_query("...") %}
{% endif %}
```

Without `{% if execute %}`, your `run_query` runs at parse time too — when `dbt parse` is invoked, the table might not exist yet, breaking the parse.

### Common Jinja idioms

```jinja
{# Default values #}
{{ var('as_was_date', 'CURRENT_DATE()') }}

{# Conditional config #}
{{ config(
    materialized='incremental' if var('incremental', true) else 'table',
    on_schema_change='append_new_columns'
) }}

{# Loop with separator #}
{% for item in items %}
    {{ item }}{{ ',' if not loop.last }}
{% endfor %}

{# Dict comprehension via namespace #}
{% set ns = namespace(rows=[]) %}
{% for row in results %}
    {% if row.col_a > 0 %}
        {% set ns.rows = ns.rows + [row] %}
    {% endif %}
{% endfor %}

{# Macro context: pass a model name as a string #}
{% set my_model_name = 'finance_line_analytics' %}
{{ ref(my_model_name) }}

{# Dispatch based on target #}
{% if target.name == 'prod' %}
    -- prod-only logic
{% elif target.name == 'qa' %}
    -- qa-only logic
{% endif %}
```

## 2. Adapter dispatch (the cross-database pattern)

When you write a macro that should behave differently per warehouse:

```jinja
{% macro current_timestamp() %}
    {{ return(adapter.dispatch('current_timestamp', 'my_package')()) }}
{% endmacro %}

{% macro default__current_timestamp() %}
    current_timestamp::timestamp
{% endmacro %}

{% macro snowflake__current_timestamp() %}
    convert_timezone('UTC', current_timestamp())
{% endmacro %}

{% macro bigquery__current_timestamp() %}
    current_timestamp()
{% endmacro %}
```

`adapter.dispatch('macro_name', 'my_package')` looks up:
1. `snowflake__current_timestamp` (if target adapter is Snowflake)
2. Falls back to `default__current_timestamp`

This is how `dbt-utils` ships one macro that works across all adapters.

### When to dispatch

- Writing a package for reuse across warehouses
- A function in your own codebase that you may want to port

### When NOT to dispatch

- A model-specific macro that will only run in Snowflake (just write the Snowflake SQL)
- A finance UDF (`udf_arr_category`) where business logic is the same across warehouses (dispatch only the adapter-specific bits)

## 3. Macro design principles

### Single responsibility

```jinja
{# Bad: macro does too much #}
{% macro build_arr_table(model_name, ...) %}
    create table {{ model_name }} as (
        select ... case ... join ... where ... group by ...
    )
{% endmacro %}

{# Good: split into composable pieces #}
{% macro udf_arr_category(input_col) %}
    case
        when {{ input_col }} = 'A' then 'Net New'
        when {{ input_col }} = 'B' then 'Renewal'
        else 'Other'
    end
{% endmacro %}

{% macro udf_currency_to_usd(amount_col, currency_col, date_col) %}
    {{ amount_col }} * (
        select usd_rate from {{ ref('currency_constant') }}
        where currency_iso_code = {{ currency_col }}
          and rate_date = {{ date_col }}
    )
{% endmacro %}
```

### Parameterize column names, not table names

```jinja
{# Bad: hardcoded table #}
{% macro get_arr(category) %}
    select sum(arr_usd_current) from finance.bt_arr_line_categories
    where arr_category = '{{ category }}'
{% endmacro %}

{# Good: parameterize #}
{% macro get_arr(model, category_col, category_value, amount_col) %}
    select sum({{ amount_col }}) from {{ model }}
    where {{ category_col }} = '{{ category_value }}'
{% endmacro %}

{# Usage: #}
{{ get_arr(
    model=ref('arr_line_categories'),
    category_col='arr_category',
    category_value='Renewal',
    amount_col='arr_usd_current'
) }}
```

### Return SQL fragments, not full queries

```jinja
{# Bad: macro returns full query that limits reuse #}
{% macro get_active_arr() %}
    select sum(arr_usd_current) from {{ ref('arr_line_categories') }}
    where as_was_date = (select max(as_was_date) from {{ ref('arr_line_categories') }})
{% endmacro %}

{# Good: macro returns a fragment that callers compose #}
{% macro filter_to_latest_as_was(model, date_col='as_was_date') %}
    {{ date_col }} = (select max({{ date_col }}) from {{ model }})
{% endmacro %}

{# Usage: #}
select sum(arr_usd_current) from {{ ref('arr_line_categories') }}
where {{ filter_to_latest_as_was(ref('arr_line_categories')) }}
```

## 4. Custom materializations

A custom materialization is a macro that defines the **physical write strategy** for a model. Use cases:

- Domain-specific incremental logic (e.g., partition-by-fiscal-quarter snapshot)
- Specialized refresh patterns (e.g., refresh only weekday data)
- Wrap a non-dbt-native object (e.g., Snowflake hybrid table, Iceberg table)

### Minimal custom materialization

```sql
{% materialization my_custom_table, adapter='snowflake' %}

    {%- set target_relation = this %}
    {%- set existing_relation = load_relation(target_relation) %}

    {{ run_hooks(pre_hooks, inside_transaction=False) }}
    {{ run_hooks(pre_hooks, inside_transaction=True) }}

    {% if existing_relation is none %}
        {% set build_sql = create_table_as(False, target_relation, sql) %}
    {% else %}
        {% set build_sql -%}
            insert into {{ target_relation }}
            select * from ({{ sql }})
            where created_at > (select max(created_at) from {{ target_relation }})
        {%- endset %}
    {% endif %}

    {% call statement('main') %}
        {{ build_sql }}
    {% endcall %}

    {{ run_hooks(post_hooks, inside_transaction=True) }}
    {{ run_hooks(post_hooks, inside_transaction=False) }}

    {{ return({'relations': [target_relation]}) }}

{% endmaterialization %}
```

### Usage in a model

```sql
{{ config(materialized='my_custom_table') }}
select ...
```

### When to write your own vs use built-in

| Need | Built-in option | Custom needed? |
|---|---|---|
| Upsert by PK | `incremental` `merge` | No |
| Full table rebuild daily | `table` | No |
| Append new rows daily | `incremental` `append` | No |
| Snowflake Hybrid Table (transactional + analytical) | None | Yes |
| Snowflake Iceberg (with custom catalog) | `iceberg` (1.10+) | Maybe |
| Custom multi-write to S3 + Snowflake | None | Yes |
| Partition-and-overwrite per fiscal quarter | `delete+insert` close, but ALI grain not partitionable | Yes |

## 5. Hooks — the pre/post-model escape hatch

```sql
{{ config(
    pre_hook=[
        "ALTER SESSION SET TIMEZONE = 'UTC'",
        "ALTER SESSION SET QUERY_TAG = 'model:finance_line_analytics'"
    ],
    post_hook=[
        "GRANT SELECT ON {{ this }} TO ROLE ROLE_ANALYTICS_READER",
        "ALTER TABLE {{ this }} SET DATA_RETENTION_TIME_IN_DAYS = 30",
        "ALTER TABLE {{ this }} CLUSTER BY (as_was_date)"
    ]
) }}
```

### Hook execution order

```
pre_hook (transaction OFF)
  pre_hook (transaction ON)
    main statement (the model build)
  post_hook (transaction ON)
post_hook (transaction OFF)
```

Use `inside_transaction=False` for DDL (`GRANT`, `ALTER TABLE`) — these can't run inside the build transaction.

### on-run-start / on-run-end (project-level)

```yaml
# dbt_project.yml
on-run-start:
  - "{{ create_udfs_if_not_exists() }}"
  - "ALTER WAREHOUSE COMPUTE_WH SET WAREHOUSE_SIZE = 'LARGE'"

on-run-end:
  - "{{ apply_column_tags() }}"
  - "ALTER WAREHOUSE COMPUTE_WH SET WAREHOUSE_SIZE = 'SMALL'"
```

Common patterns:
- Create/refresh Snowflake UDFs (TVFs) before any model runs
- Apply tag-based column-level governance (`apply_column_tags`)
- Resize warehouse for the batch then back down
- Compute pipeline-wide metrics (row counts, freshness) at the end

### Hooks anti-patterns

- Running `dbt CLI` from a hook — not supported; hooks are SQL only.
- Running expensive queries on `on-run-start` — runs on EVERY dbt invocation, including `dbt list`.
- Granting on every run — slow + unnecessary; use future grants on the schema instead.

## 6. UDFs (Snowflake user-defined functions)

dbt can manage UDFs via `on-run-start`:

```sql
{% macro create_udf_arr_category() %}
    create or replace function {{ target.database }}.{{ target.schema }}.udf_arr_category(
        arr_amount number, term_end_date date, ...
    )
    returns varchar
    language sql
    as $$
        case ...
    $$;
{% endmacro %}
```

```yaml
# dbt_project.yml
on-run-start:
  - "{{ create_udf_arr_category() }}"
```

### When to use UDFs

| Need | UDF? | Alternative |
|---|---|---|
| Logic used in 5+ models, all in one warehouse | Yes (UDF) | Macro (compile-time inlined) |
| Logic that downstream BI tools also need | Yes (UDF) | Materialize the result in a column |
| Logic with conditional branching that's hard to read inline | Yes (UDF) | Macro |
| Complex aggregation across rows | Use UDTF (table function) | Window function |
| Logic that changes weekly | Avoid UDF (DDL coupling) | Macro |

### UDF vs macro tradeoffs

| | UDF | Macro |
|---|---|---|
| Where evaluated | Snowflake | dbt parse time (inlined into SQL) |
| Version-controlled | If managed via dbt `on-run-start` | Always |
| Visible in SQL profile | Yes (as a function call) | No (inlined as raw SQL) |
| Performance | Slower for trivial logic (function call overhead) | Faster (raw SQL) |
| Reusability outside dbt | Yes (BI tools can call) | No |
| Testability | Limited (UDF unit tests are awkward) | Easy (dbt unit tests, macro `run_query`) |

## 7. UDTFs (table functions) — the principal pattern for cross-row logic

UDTFs (User-Defined Table Functions) take a row and return a TABLE of rows. Pattern for SCD2 wrappers, ARR categorization expansion, etc.

```sql
create or replace function get_arr_line_base_fn(
    as_was_date date,
    agreement_line_item_id varchar,
    ...
)
returns table (
    arr_category varchar,
    arr_usd_current number,
    is_pre_acquisition boolean,
    ...
)
as $$
    select
        case when ... then 'Net New' else 'Other' end as arr_category,
        ...
$$;
```

```sql
-- Use in dbt model
select base.*
from {{ ref('stg_em_agreement_line_item_scd2') }} ali,
     table(get_arr_line_base_fn(ali.as_was_date, ali.agreement_line_item_id, ...)) base
```

### Why UDTFs over inline SQL

- Logic is testable in isolation (call the UDTF directly with literal args)
- Centralized — change once, all callers update
- Snowflake plans them efficiently (no row-by-row overhead like a UDF would have)

### Anti-patterns

- Putting a UDTF in front of every join — function-call overhead × millions of rows
- Using UDTFs to wrap a single CASE statement — just inline it
- UDTFs that depend on session state (`current_timestamp`, `current_user`) — they break unit tests and audit determinism

## 8. run_query — the macro-time data access pattern

```jinja
{% macro get_active_partitions(model_name) %}
    {% set query %}
        select distinct as_was_date
        from {{ ref(model_name) }}
        where as_was_date >= dateadd('day', -7, current_date())
        order by as_was_date desc
    {% endset %}

    {% set results = run_query(query) %}
    {% if execute %}
        {% set partitions = results.columns[0].values() %}
    {% else %}
        {% set partitions = [] %}
    {% endif %}
    {{ return(partitions) }}
{% endmacro %}
```

Use cases:
- Dynamic incremental filters (which partitions to rebuild based on warehouse state)
- Schema introspection (`information_schema.columns` lookup)
- Adapter-side dispatch (different paths based on warehouse capacity)

### `run_query` gotchas

- Only call inside `{% if execute %}` — calling at parse time can break `dbt parse`.
- Returns an `agate.Table` object — `.columns[0].values()` for column extraction.
- Slows every dbt invocation (extra warehouse round trip) — use sparingly.

## 9. The `adapter.get_columns_in_relation` pattern (view-vs-table safety)

If a model `ref('upstream')` and `upstream` is materialized as a view, the view doesn't exist yet when the parent is parsed during slim CI deferral. Fall back to compile-time column list:

```jinja
{% set upstream_relation = ref('upstream_model') %}
{% set columns = [] %}

{% if execute %}
    {% set try_cols = adapter.get_columns_in_relation(upstream_relation) %}
    {% if try_cols %}
        {% set columns = [c.name for c in try_cols] %}
    {% endif %}
{% endif %}

{% if not columns %}
    {# Fall back to hardcoded list when relation doesn't exist yet #}
    {% set columns = ['col_a', 'col_b', 'col_c'] %}
{% endif %}

select {{ columns | join(', ') }} from {{ upstream_relation }}
```

This pattern saved us during the IA migration when staging views were deployed after their consumers.

## 10. Macro testing patterns

### Compile + diff

```bash
# Generate compiled SQL for one model
dbt compile --select my_model
cat target/compiled/<proj>/<path>/my_model.sql

# Compile with different vars
dbt compile --select my_model --vars '{"as_was_date": "2026-01-01"}'
```

### `dbt run-operation` for standalone macro execution

```bash
dbt run-operation create_udf_arr_category
```

### Macro unit test (custom pattern)

```yaml
unit_tests:
  - name: test_udf_arr_category_macro
    model: my_test_harness_model
    overrides:
      macros:
        udf_arr_category: "case when arr_usd_current > 0 then 'PositiveTest' else 'OtherTest' end"
    expect: [...]
```

## 11. Anti-patterns to refuse in code review

| Anti-pattern | Why it's bad | Refusal script |
|---|---|---|
| Macro with 10+ parameters | Unmaintainable; positional confusion | "Group params into a dict or split into 2 macros" |
| Macro that does both compile-time logic AND `run_query` | Mental model is split; bugs are confusing | "Split into 2 macros — one parse-time, one execute-time" |
| Hook running `GRANT` on every model | Snowflake load + slow | "Use future grants at the schema level: `grant select on future tables in schema X to role Y`" |
| `ephemeral` materialization on a model used by 10+ consumers | Compile time blow-up | "Convert to `table`; ephemeral makes sense only for 1-3 consumers" |
| Custom materialization that doesn't use `load_relation` | Will create duplicate tables if existing relation isn't found | "Use `load_relation(target_relation)` to check for existing" |
| UDF defined in 3 places (dbt + Snowflake SP + Sigma) | Drift inevitable | "Pick one source of truth; create UDF via dbt `on-run-start` only" |
| `run_query` without `{% if execute %}` guard | Breaks `dbt parse` | "Wrap in `{% if execute %}`; provide fallback when not executing" |
| Adapter dispatch but only one adapter implemented | Dead code, confusing | "If you only target Snowflake, drop the dispatch wrapper" |

## 12. Reference — patterns we ship in our project

| Macro | File | Purpose |
|---|---|---|
| `udf_arr_category` | `macros/em/udf_arr_category.sql` | ARR category classification (NetNew, Renewal, Expansion, Contraction, Churn) |
| `udf_currency_to_usd` | `macros/em/udf_currency_to_usd.sql` | Three-variant currency conversion |
| `udf_is_strategic_program` | `macros/em/udf_is_strategic_program.sql` | Strategic program flag |
| `udf_product_mix` | `macros/em/udf_product_mix.sql` | HCM/FIN array-based mix classification |
| `udf_acquisition_flags` | `macros/em/udf_acquisition_flags.sql` | `is_pre_acquisition` / `is_acquired_sku` derivation |
| `get_arr_line_base_fn` | `functions/managed/get_arr_line_base_fn.sql` | The ARR core UDTF (used by FLA, all `arr_*_categories`) |
| `run_historical_chains_standalone` | `macros/em/run_historical_chains_standalone.sql` | Backfill orchestration hook (replaces retired `adhoc_pipeline_runner_config.sql`) |
| `apply_column_tags` | `macros/em/apply_column_tags.sql` | Tag-based column-level governance |
