# ARR Quarter Close - Validation

Two layers of validation are required for every close. A third (Sigma tie-out)
is performed by finance outside this repo.

## Layer 1 - Waterfall integrity (in-repo, dbt test)

**Test:** `test_arr_waterfall_balance` (singular test, severity=warn,
`store_failures=true`, schema `stage`).

**What it checks:** for every `(as_was_date, fiscal_quarter_name, buying_center)`
in `arr_product_categories`:

```
Begin Balance + (Net New + Add On + Product Add On
              + Expansion + Contraction
              + Customer Churn + Logo Churn
              + Product Churn + SKU Churn)   =  End Balance      (within $0.01)

End_arr(this quarter)  =  Begin_arr(next quarter)                (within $0.01)
```

When you read failing rows, group by `fiscal_quarter_name` and `buying_center`
to localize - drift is usually one fiscal-quarter wide.

## Layer 2 - IA cutover recon (in-repo, dbt test)

**Tests:** five `test_finance_prod_vs_certified_prod_arr_*.sql`, tagged
`ia_migration` and `data_quality`. Tolerance: exact row / account /
agreement counts; `abs(delta) > 1.00 USD` on FLOAT sums.

Run them as a group:

```bash
dbt test --select tag:ia_migration --vars '{"as_was_date": "'\''<DATE>'\''"}'
```

Or individually:

```bash
dbt test --select test_finance_prod_vs_certified_prod_arr_line --vars '{"as_was_date": "'\''<DATE>'\''"}'
dbt test --select test_finance_prod_vs_certified_prod_arr_product --vars '{"as_was_date": "'\''<DATE>'\''"}'
dbt test --select test_finance_prod_vs_certified_prod_arr_sku --vars '{"as_was_date": "'\''<DATE>'\''"}'
dbt test --select test_finance_prod_vs_certified_prod_arr_subproduct --vars '{"as_was_date": "'\''<DATE>'\''"}'
dbt test --select test_finance_prod_vs_certified_prod_arr_account_product_corp_report --vars '{"as_was_date": "'\''<DATE>'\''"}'
```

Failing rows land at (QA shown):

```text
certified_qa.stage.test_finance_prod_vs_certified_prod_arr_line
certified_qa.stage.test_finance_prod_vs_certified_prod_arr_product
certified_qa.stage.test_finance_prod_vs_certified_prod_arr_sku
certified_qa.stage.test_finance_prod_vs_certified_prod_arr_subproduct
certified_qa.stage.test_finance_prod_vs_certified_prod_arr_account_product_corp_report
```

Each row contains `row_delta`, `acct_delta`, `agr_delta` (where applicable),
and per-measure deltas. For `arr_product_categories`, rows with
`check_level = 'arr_category'` pinpoint waterfall-category drift, vs
`check_level = 'overall'` for the full-table aggregate.

## Layer 3 - Sigma tie-out (external)

The finance team performs the customer-facing tie-out in Sigma. This skill
does not run that tie-out, but it should flag when a close lands so finance
can start. Reference workbook: `4NZDtGiTlqFm0Mtbv52HNH` (ACV CertPROD
Validation FY26Q4 - ACV-focused, but the same workbook pattern is used for
ARR by finance).

## Quick recon SQL (Snowflake MCP)

When validation warns and you need a fast read on which aggregate diverged,
use these queries via the Snowflake MCP (substitute `<DATE>`):

```sql
-- Layer 1: scan failing waterfall rows
select fiscal_quarter_name, buying_center,
       incremental_delta, qoq_buying_center_delta
from certified_qa.stage.test_arr_waterfall_balance
order by abs(incremental_delta) desc nulls last
limit 20;

-- Layer 2: which aggregate diverged most (sum of |row_delta|)
select 'arr_line'        as agg, sum(abs(row_delta)) as drift
  from certified_qa.stage.test_finance_prod_vs_certified_prod_arr_line
union all
select 'arr_product',     sum(abs(row_delta))
  from certified_qa.stage.test_finance_prod_vs_certified_prod_arr_product
union all
select 'arr_sku',         sum(abs(row_delta))
  from certified_qa.stage.test_finance_prod_vs_certified_prod_arr_sku
union all
select 'arr_subproduct',  sum(abs(row_delta))
  from certified_qa.stage.test_finance_prod_vs_certified_prod_arr_subproduct
union all
select 'corp_report',     sum(abs(row_delta))
  from certified_qa.stage.test_finance_prod_vs_certified_prod_arr_account_product_corp_report
order by drift desc;
```

## Sign-off criteria

A close is sign-off ready when **all** of:

- Steps 1-4 (build) returned `success`.
- `test_arr_waterfall_balance` produced zero failing rows for the
  current `as_was_date`.
- `tag:ia_migration` (during cutover) produced zero failing rows or
  produced only rows within agreed tolerance, documented in the close
  summary.

Anything else needs a follow-up before the next quarter close.
