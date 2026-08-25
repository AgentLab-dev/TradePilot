"""Shared 7-column validation-matrix builder.

Used by code-data-validator (pre-flight against finance_prod), ci-monitor
(post-CI against finance_dev), and cd-monitor (post-CD against finance_qa).
Each emits a ``ValidationMatrix`` of ``ValidationCheck`` rows that compare:

  source_salesforce -> baseline_prod -> target_dev_qa
                                 vs.   expected
                                       actual
  with business_logic + verdict appended.

The SQL ``sql_template`` field of every check is the auditable query the
supervisor (or operator) runs via the Snowflake MCP to populate the actual
value columns. Until the SQL is run, ``verdict='pending'`` and the value
columns stay empty.
"""

from __future__ import annotations

from agents.arr_quarter_close.contracts import ValidationCheck, ValidationMatrix


# Default models the matrix covers when the requirements analyzer didn't
# pin a more specific list.
DEFAULT_ARR_MODELS: tuple[str, ...] = (
    "arr_line_categories",
    "arr_sku_categories",
    "arr_product_categories",
    "arr_subproduct_categories",
)


def build_matrix(
    *,
    matrix_name: str,
    target_db: str,
    baseline_db: str = "finance_prod",
    source_db: str = "base_prod.salesforce",
    in_scope_models: list[str] | None = None,
) -> ValidationMatrix:
    """Build the canonical 4-check validation matrix.

    The four checks the matrix carries:

    1. ARR total at latest snapshot (sf -> prod -> dev/qa, +/- tolerance)
    2. Line-vs-SKU rollup parity (structural; sf source = N/A)
    3. Waterfall balance (Begin + Categories = End; structural)
    4. Row-count parity vs baseline (structural)
    """
    models = list(in_scope_models or DEFAULT_ARR_MODELS)
    checks: list[ValidationCheck] = [
        _check_arr_total(target_db, baseline_db, source_db),
        _check_line_vs_sku(target_db, baseline_db),
        _check_waterfall_balance(target_db),
        _check_row_count_parity(target_db, baseline_db),
    ]
    return ValidationMatrix(
        matrix_name=matrix_name,
        target_db=target_db,
        baseline_db=baseline_db,
        source_db=source_db,
        checks=checks,
    )


# ---------------------------------------------------------------------------
# Per-check SQL builders
# ---------------------------------------------------------------------------

def _check_arr_total(target_db: str, baseline_db: str, source_db: str) -> ValidationCheck:
    sql = f"""\
-- check: arr_total_at_latest_snapshot
-- Columns: source_salesforce, baseline_prod, target_dev_qa, expected, actual, verdict
with sf_source as (
  -- Raw Salesforce annualized fees across active agreement lines.
  select coalesce(sum(al.adj_al_total_fees / nullif(al.term_yrs, 0)), 0) as v
  from {source_db}.apttus__agreementlineitem__c al
  where al.apts_term_end_date__c >= current_date()
    and al.linestatus__c <> 'Cancelled'
),
prod_baseline as (
  select coalesce(sum(arr_usd_current), 0) as v
  from {baseline_db}.aggregations.arr_line_categories
  where as_was_date = (
    select max(as_was_date) from {baseline_db}.aggregations.arr_line_categories
  )
),
dev_target as (
  select coalesce(sum(arr_usd_current), 0) as v
  from {target_db}.aggregations.arr_line_categories
  where as_was_date = (
    select max(as_was_date) from {target_db}.aggregations.arr_line_categories
  )
)
select
  'arr_total_at_latest_snapshot'                                         as check_name,
  '(as_was_date = max)'                                                  as grain,
  sf_source.v::string                                                    as source_salesforce,
  prod_baseline.v::string                                                as baseline_prod,
  dev_target.v::string                                                   as target_dev_qa,
  prod_baseline.v::string                                                as expected,
  dev_target.v::string                                                   as actual,
  'sum(arr_usd_current) at latest snapshot, line grain'                  as business_logic,
  case
    when prod_baseline.v = 0 then 'needs_review'
    when abs(dev_target.v - prod_baseline.v) / nullif(prod_baseline.v, 0) < 0.001 then 'pass'
    when abs(dev_target.v - prod_baseline.v) / nullif(prod_baseline.v, 0) < 0.01  then 'warn'
    else 'fail'
  end                                                                    as verdict,
  (dev_target.v - prod_baseline.v)                                       as variance_abs,
  round((dev_target.v - prod_baseline.v) / nullif(prod_baseline.v, 0) * 100, 4) as variance_pct
from sf_source, prod_baseline, dev_target;
"""
    return ValidationCheck(
        check_name="arr_total_at_latest_snapshot",
        grain="(as_was_date = max)",
        business_logic="sum(arr_usd_current) at latest snapshot, line grain",
        sql_template=sql,
        notes="Tolerance: <0.1% pass, <1% warn, else fail. SF source uses adj_al_total_fees / term_yrs.",
    )


def _check_line_vs_sku(target_db: str, baseline_db: str) -> ValidationCheck:
    sql = f"""\
-- check: line_vs_sku_rollup_parity
-- Salesforce source N/A for this structural test; baseline is prod parity.
with line_t as (
  select fiscal_quarter_name, sum(split_sku_line_arr_usd_current) as v
  from {target_db}.aggregations.arr_line_categories
  where as_was_date = (select max(as_was_date) from {target_db}.aggregations.arr_line_categories)
  group by 1
),
sku_t as (
  select fiscal_quarter_name, sum(split_arr_usd_current) as v
  from {target_db}.aggregations.arr_sku_categories
  where try_to_date(as_was_date) = (select max(try_to_date(as_was_date)) from {target_db}.aggregations.arr_sku_categories)
  group by 1
)
select
  'line_vs_sku_rollup_parity'                                            as check_name,
  'fiscal_quarter_name'                                                  as grain,
  ''                                                                     as source_salesforce,
  'parity required across all FQs in baseline'                           as baseline_prod,
  to_varchar(max(abs(line_t.v - sku_t.v)))                               as target_dev_qa,
  '0 (line == sku at every fiscal_quarter_name)'                         as expected,
  to_varchar(max(abs(line_t.v - sku_t.v)))                               as actual,
  'split_sku_line_arr_usd_current (line) == split_arr_usd_current (sku) per FQ' as business_logic,
  case
    when max(abs(line_t.v - sku_t.v)) < 1     then 'pass'
    when max(abs(line_t.v - sku_t.v)) < 1000  then 'warn'
    else 'fail'
  end                                                                    as verdict
from line_t join sku_t using (fiscal_quarter_name);
"""
    return ValidationCheck(
        check_name="line_vs_sku_rollup_parity",
        grain="fiscal_quarter_name",
        baseline_prod="parity required across all FQs in baseline",
        expected="0 (line == sku at every fiscal_quarter_name)",
        business_logic="split_sku_line_arr_usd_current (line) == split_arr_usd_current (sku) per FQ",
        sql_template=sql,
        notes="Tolerance: <$1 pass, <$1000 warn, else fail. Salesforce source N/A (structural).",
    )


def _check_waterfall_balance(target_db: str) -> ValidationCheck:
    sql = f"""\
-- check: waterfall_balance
-- Begin + sum(categories) = End per fiscal_quarter_name (structural test).
with snap as (
  select fiscal_quarter_name,
         sum(case when arr_category = 'Begin Balance' then split_arr_usd_current end) as begin_v,
         sum(case when arr_category = 'End Balance'   then split_arr_usd_current end) as end_v,
         sum(case when arr_category not in ('Begin Balance','End Balance')
                  then split_arr_usd_current end)                                     as delta_v
  from {target_db}.aggregations.arr_product_categories
  where as_was_date = (select max(as_was_date) from {target_db}.aggregations.arr_product_categories)
  group by 1
)
select
  'waterfall_balance'                                                    as check_name,
  'fiscal_quarter_name'                                                  as grain,
  ''                                                                     as source_salesforce,
  ''                                                                     as baseline_prod,
  to_varchar(max(abs((begin_v + delta_v) - end_v)))                      as target_dev_qa,
  '0 (begin + sum(categories) == end per FQ)'                            as expected,
  to_varchar(max(abs((begin_v + delta_v) - end_v)))                      as actual,
  'Begin Balance + sum(category deltas) = End Balance'                   as business_logic,
  case
    when max(abs((begin_v + delta_v) - end_v)) < 1     then 'pass'
    when max(abs((begin_v + delta_v) - end_v)) < 1000  then 'warn'
    else 'fail'
  end                                                                    as verdict
from snap;
"""
    return ValidationCheck(
        check_name="waterfall_balance",
        grain="fiscal_quarter_name",
        expected="0 (begin + sum(categories) == end per FQ)",
        business_logic="Begin Balance + sum(category deltas) = End Balance",
        sql_template=sql,
        notes="Structural test; tolerance: <$1 pass, <$1000 warn, else fail.",
    )


def _check_row_count_parity(target_db: str, baseline_db: str) -> ValidationCheck:
    sql = f"""\
-- check: row_count_parity_vs_baseline
-- Latest snapshot row counts must not differ from baseline by > 1%.
with t as (
  select count(*) as v from {target_db}.aggregations.arr_line_categories
  where as_was_date = (select max(as_was_date) from {target_db}.aggregations.arr_line_categories)
),
b as (
  select count(*) as v from {baseline_db}.aggregations.arr_line_categories
  where as_was_date = (select max(as_was_date) from {baseline_db}.aggregations.arr_line_categories)
)
select
  'row_count_parity_vs_baseline'                                         as check_name,
  '(as_was_date = max)'                                                  as grain,
  ''                                                                     as source_salesforce,
  b.v::string                                                            as baseline_prod,
  t.v::string                                                            as target_dev_qa,
  'within 1% of baseline'                                                as expected,
  t.v::string                                                            as actual,
  'count(*) at latest snapshot, arr_line_categories'                     as business_logic,
  case
    when b.v = 0 then 'needs_review'
    when abs(t.v - b.v) / nullif(b.v, 0) < 0.01 then 'pass'
    when abs(t.v - b.v) / nullif(b.v, 0) < 0.05 then 'warn'
    else 'fail'
  end                                                                    as verdict,
  (t.v - b.v)                                                            as variance_abs,
  round((t.v - b.v) / nullif(b.v, 0) * 100, 4)                           as variance_pct
from t, b;
"""
    return ValidationCheck(
        check_name="row_count_parity_vs_baseline",
        grain="(as_was_date = max)",
        expected="within 1% of baseline",
        business_logic="count(*) at latest snapshot, arr_line_categories",
        sql_template=sql,
        notes="Tolerance: <1% pass, <5% warn, else fail.",
    )
