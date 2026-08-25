# Unit Tests, Generic Tests, and Quality Frameworks

Reference companion to `dbt-architect/SKILL.md` §4.

## 1. The dbt test pyramid (formalized)

```
                  ┌───────────────────────┐
                  │   L5: Recon harness    │  ← refactor PRs only
                  │  (audit-helper compare) │
                  └────────────┬──────────┘
                  ┌───────────────────────┐
                  │   L4: Unit tests        │  ← high-stakes logic
                  │  (mocked inputs in YAML)│
                  └────────────┬──────────┘
            ┌───────────────────────────────────┐
            │     L3: Custom generic tests        │  ← reusable rules
            │   (tests/generic/test_*.sql)        │
            └────────────────┬──────────────────┘
      ┌─────────────────────────────────────────────┐
      │       L2: Singular tests                     │  ← model-specific
      │   (tests/<role>/<model>/assert_*.sql)        │
      └────────────────┬────────────────────────────┘
┌──────────────────────────────────────────────────────────┐
│              L1: Schema tests (built-in)                  │  ← 100% PK + key joins
│   unique, not_null, accepted_values, relationships         │
└──────────────────────────────────────────────────────────┘
```

Coverage targets (for an enterprise dbt platform):

| Level | Coverage |
|---|---|
| L1 | 100% of PKs; 100% of FK joins; 80% of enum columns |
| L2 | 100% of business-critical invariants (no zero ARR rows, no future-dated events) |
| L3 | Reusable across 3+ models (e.g., `test_grain_is_one_row_per`) |
| L4 | 100% of currency conversion, ARR categorization, SSR detection, any transformation with ≥3 conditional branches |
| L5 | Every refactor PR; passes with < $1 variance |

## 2. L1 — Schema tests (the floor)

### Standard pattern for every `bt_*` / `dim_*` / `fact_*` model

```yaml
models:
  - name: finance_line_analytics
    description: "ARR at agreement-line-item grain per as_was_date"
    config:
      contract: {enforced: true}
    columns:
      - name: as_was_date
        data_type: date
        constraints: [{type: not_null}]
        tests:
          - not_null
      - name: agreement_line_item_id
        data_type: varchar
        constraints: [{type: not_null}]
      - name: arr_usd_current
        data_type: number(38,2)
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= 0 OR arr_category IN ('Churn', 'Contraction')"
              config:
                severity: error
    tests:
      - dbt_utils.unique_combination_of_columns:
          combination_of_columns:
            - as_was_date
            - agreement_line_item_id
```

### Severity tuning

```yaml
tests:
  - not_null:
      severity: error           # default — fails build
  - dbt_utils.expression_is_true:
      expression: "row_count > 1000"
      severity: warn            # emits warning, doesn't fail build
      warn_if: ">100"
      error_if: ">1000"
```

Use `warn` for thresholds you want to observe but not block on. Use `error` for true invariants.

## 3. L2 — Singular tests (model-specific assertions)

A singular test is a SQL file under `tests/` that returns rows when the assertion FAILS. Zero rows = pass.

### Pattern

```sql
-- tests/finance/assert_no_zero_arr_in_renewal_category.sql
select
    as_was_date,
    agreement_line_item_id,
    arr_category,
    arr_usd_current
from {{ ref('finance_line_analytics') }}
where as_was_date = (select max(as_was_date) from {{ ref('finance_line_analytics') }})
  and arr_category in ('Renewal', 'Expansion')
  and arr_usd_current = 0
```

### Best practices

- **One assertion per file.** Don't combine multiple invariants — when it fails, you want to know which one.
- **Name files by the assertion.** `assert_<positive_statement>.sql` reads cleanly in the test output.
- **Scope to recent data.** Always filter on `as_was_date = max(as_was_date)` or similar — testing historical data wastes credits and never catches the new bug.
- **Document the business rule in the SQL comment.** Future you (or the on-call engineer) needs to know WHY this assertion exists.

### Common singular test patterns

```sql
-- tests/finance/assert_arr_sum_matches_sf.sql
-- Recon: dbt-computed ARR must match SF.Opportunity.Amount sum within $1
with dbt_arr as (
    select fiscal_quarter_name, sum(arr_usd_current) as arr_sum
    from {{ ref('arr_line_categories') }}
    where as_was_date = (select max(as_was_date) from {{ ref('arr_line_categories') }})
    group by 1
),
sf_arr as (
    select fiscal_quarter_name, sum(amount_usd) as arr_sum
    from {{ ref('stg_em_opportunity_scd2') }}
    where ...
    group by 1
)
select
    d.fiscal_quarter_name,
    d.arr_sum as dbt_sum,
    s.arr_sum as sf_sum,
    abs(d.arr_sum - s.arr_sum) as variance
from dbt_arr d
join sf_arr s using (fiscal_quarter_name)
where abs(d.arr_sum - s.arr_sum) > 1     -- $1 tolerance
```

## 4. L3 — Custom generic tests (reusable)

When the same assertion applies to 3+ models, lift it to a generic test in `tests/generic/`.

### Pattern

```sql
-- tests/generic/test_grain_is_one_row_per.sql
{% test grain_is_one_row_per(model, partition_columns) %}
    with grain_check as (
        select
            {{ partition_columns | join(', ') }},
            count(*) as row_count
        from {{ model }}
        group by {{ partition_columns | join(', ') }}
        having count(*) > 1
    )
    select * from grain_check
{% endtest %}
```

### Usage

```yaml
models:
  - name: finance_line_analytics
    tests:
      - grain_is_one_row_per:
          partition_columns: [as_was_date, agreement_line_item_id]
```

### Common generic tests to ship

| Test | Purpose | Example use |
|---|---|---|
| `grain_is_one_row_per` | Enforce grain | Every fact/dim model |
| `row_count_within_threshold` | Catch sudden volume drops | All daily-snapshot facts |
| `column_value_change_below_threshold` | Catch logic regressions | Refactor recon |
| `monotonic_increase` | Sequence integrity | Surrogate-key SCD2 tables |
| `boundary_dates_within_range` | Catch future-dated data | Any model with `created_at` / `event_ts` |
| `currency_variants_sum_close` | Currency conversion sanity | FLA + ARR aggregates |

## 5. L4 — Unit tests (the principal-level addition)

Unit tests (GA in dbt 1.8+, hardened in 1.12) let you test model logic against **mocked inputs**, completely independent of warehouse data.

### Why unit tests are different from data tests

| | Data test (L1-L3) | Unit test (L4) |
|---|---|---|
| Tests | Output of a built model in the warehouse | Logic of a model SQL with mocked inputs |
| Speed | Slow (Snowflake query) | Fast (in-process compilation + assertion) |
| Coverage | Whatever is in the warehouse today | Every code path you explicitly mock |
| Catches | Data drift, source schema changes | Logic bugs (wrong CASE branches, off-by-one, wrong join key) |
| Refactor safety | Limited (depends on data being representative) | Strong (fixed inputs, fixed expected output) |

### Anatomy of a unit test

```yaml
unit_tests:
  - name: test_arr_category_net_new_logic
    model: arr_line_categories
    description: |
      When account begin balance = 0 and it's the first opp this FQ,
      arr_category should be 'Net New'.
    given:
      - input: ref('stg_em_int_strategic_program_flag')
        rows:
          - {agreement_line_item_id: 'ALI1', account_id: 'ACC1',
             agreement_id: 'AG1', opportunity_id: 'OPP1',
             fiscal_quarter_name: 'FY26Q1', as_was_date: '2026-01-01',
             arr_usd_current: 100, account_begin_balance: 0,
             opp_count_in_account_fq: 1}
    expect:
      rows:
        - {agreement_line_item_id: 'ALI1', as_was_date: '2026-01-01',
           arr_category: 'Net New', begin_category: 'Net New',
           arr_usd_current: 100}
```

### Test isolation strategies

```yaml
unit_tests:
  - name: test_currency_conversion
    model: finance_line_analytics
    given:
      - input: ref('stg_em_int_strategic_program_flag')
        rows: [...]
      - input: ref('currency_constant')   # mock the UDTF
        rows:
          - {currency_iso_code: 'EUR', usd_rate: 1.10, rate_date: '2026-01-01'}
      # No need to mock unused upstream models — dbt only loads what the model refs
    overrides:
      vars:
        as_was_date: '2026-01-01'
      macros:
        get_arr_categories_fn: "select 'Net New' as arr_category"
      env_vars:
        DBT_TARGET: dev
    expect:
      rows: [...]
```

### Format options for given/expect rows

```yaml
# Inline YAML (best for small fixtures)
given:
  - input: ref('upstream')
    rows:
      - {col_a: 1, col_b: 'X'}
      - {col_a: 2, col_b: 'Y'}

# CSV (best for >5 rows, reusable across tests)
given:
  - input: ref('upstream')
    format: csv
    fixture: my_fixture       # references tests/fixtures/my_fixture.csv

# SQL (best for complex generated rows)
given:
  - input: ref('upstream')
    format: sql
    rows: |
      select 1 as col_a, 'X' as col_b
      union all
      select 2, 'Y'
```

### Running unit tests

```bash
# All unit tests
dbt test --select unit_test:*

# Unit tests for one model
dbt test --select my_model,test_type:unit

# Unit tests as part of full build
dbt build --select state:modified+
```

### Unit-test best practices

1. **Test ONE code path per test.** A test named `test_arr_category_net_new` should ONLY exercise the Net New branch.
2. **Cover every CASE branch.** Use coverage as a checklist — every `WHEN` in `get_arr_categories_fn` should have at least one unit test.
3. **Mock upstream UDFs and macros.** Don't depend on warehouse-side function definitions during unit tests — use `overrides.macros` to inject deterministic outputs.
4. **Keep fixtures small.** 1-3 rows per fixture is ideal; larger fixtures hide which row triggers the assertion.
5. **Use `format: csv` for refactor harness fixtures.** Refactor PRs need many test cases — CSV scales better than inline YAML.

### Coverage tracking

dbt doesn't ship a coverage report. Build your own:

```bash
# Generate compiled SQL for one model
dbt compile --select my_model
# Count WHEN clauses
grep -c "WHEN " target/compiled/<proj>/<path>/my_model.sql
# Count unit tests
ls -1 tests/unit/my_model/ | wc -l
# Coverage % = unit-test count / WHEN count (rough heuristic)
```

For high-stakes models, target 1 test per `WHEN` branch + 1 per error path.

## 6. L5 — Recon harness (refactor PRs)

When refactoring a model, the L1-L4 tests prove the new model is internally consistent. The recon harness proves the new model produces the **same data** as the old.

### Pattern

Use `dbt_audit_helper.compare_relations()` or `compare_column_values()` in an `analyses/` SQL.

```sql
-- analyses/audit/finance_line_analytics/compare_column_values.sql
{{ audit_helper.compare_column_values(
    a_query="select * from " ~ ref('finance_line_analytics_v2') ~
            " where as_was_date = '2026-06-01'",
    b_query="select * from " ~ ref('finance_line_analytics') ~
            " where as_was_date = '2026-06-01'",
    primary_key='agreement_line_item_id',
    columns=['arr_usd_current', 'arr_category', 'fiscal_quarter_name']
) }}
```

Run with: `dbt compile --select compare_column_values; snowflake_query <compiled SQL>`.

### Recon best practices

1. **Always recon at the finest grain.** Aggregating before comparison hides row-level bugs.
2. **Filter to recent data.** Old as_was_dates are already validated in prod.
3. **Test on multiple as_was_dates.** A single date might pass by luck; test 5+ dates spanning a quarter boundary.
4. **$1 variance tolerance for currency.** Floating-point + rounding makes exact equality impossible.
5. **Categorize differences.** When you do find variance, classify: intentional design change, sourcing change with same intent, or true regression.

## 7. Custom test generators (meta-programming)

For very large projects, write a macro that GENERATES tests from a YAML config.

```yaml
# _test_config.yml
test_generation:
  fact_models:
    - finance_line_analytics
    - arr_line_categories
    - arr_product_categories
  required_tests:
    - grain_is_one_row_per
    - row_count_within_threshold
    - all_dates_in_valid_range
```

```sql
{% macro generate_fact_tests() %}
  {% for model in var('test_generation', {}).get('fact_models', []) %}
    {% for test in var('test_generation', {}).get('required_tests', []) %}
      -- generate the test YAML here
      ...
    {% endfor %}
  {% endfor %}
{% endmacro %}
```

This approach scales when you have 50+ similar fact models.

## 8. Test execution strategy

### Daily prod batch

```bash
dbt build --threads 32 --exclude '*_scd2'   # build + test in one pass
```

`dbt build` runs the test immediately after the model that defines it. Failure halts downstream models, preventing cascading bad data.

### Slim CI

```bash
dbt build --select state:modified+ --defer --state ../prod-manifest --threads 16
```

Tests run on modified models + downstream. Use `--store-failures` to capture failed rows in a Snowflake table for triage.

### Pre-merge gate

A failed test should block merge. Wire into GitHub Actions:

```yaml
- name: dbt build (slim CI)
  run: dbt build --select state:modified+ --defer --state ./prod-manifest --threads 16
  # Exit code 0 = pass; non-zero = fail; CI blocks merge on failure
```

### Test artifacts for analysis

```yaml
- name: Upload test results
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: dbt-test-results
    path: |
      target/run_results.json
      target/manifest.json
```

The `run_results.json` lets you build dashboards: most-failing tests, slowest tests, test-flakiness over time.

## 9. Failure modes — testing

| Symptom | Root cause | Fix |
|---|---|---|
| Unit test passes but data test fails in CI | Fixture doesn't represent real data shape | Generate fixture from real data via `dbt show --select my_model --limit 5` |
| `dbt test` takes longer than `dbt run` | Tests are running full table scans | Filter to recent as_was_date in every singular test |
| Refactor recon never converges | Tolerance too tight (sub-$1 floating point) | Set tolerance to $1; categorize the residual variance |
| Unit test mock format error | YAML schema typo | Run `dbt parse` first; fix YAML errors before runtime |
| Generic test catches false positives | Threshold tuned on old data | Re-baseline the threshold quarterly |
| Tests pass but data is wrong | Missing test coverage on the failing scenario | Add a new singular test that catches THIS bug; don't just fix the data |

## 10. The unit-test-first refactor pattern

When refactoring a high-stakes model:

1. **Before any code change**, write 5-10 unit tests covering the current behavior. Run; they should all pass.
2. **Refactor the model.** Tests will fail when behavior changes.
3. **For each failing test**, classify:
   - **Intentional behavior change** → update the expected output in the test.
   - **Bug in the refactor** → fix the code.
4. **Add new tests** for any new behavior the refactor introduces.
5. **Run the recon harness** to confirm row-level equivalence on real data (within tolerance).
6. **PR description** includes: tests added, tests modified, recon variance summary.

This pattern is the difference between "I think it works" and "I can prove it works" — the latter is the principal-level standard.
