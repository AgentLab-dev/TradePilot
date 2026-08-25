# Common dbt Anti-Patterns & Fixes

## 1. Many-to-Many Join (Row Inflation)

**Symptom**: Row count in the output is higher than either input table.

**Bad** — joining two tables that share a key but aren't 1:1:
```sql
select
    a.user_id,
    a.session_id,
    b.event_id
from sessions as a
inner join events as b
    on a.user_id = b.user_id
```
Each user with N sessions and M events produces N * M rows.

**Fix** — aggregate one side before joining, or add a second join key to restore 1:1 grain:
```sql
with

event_counts as (
    select
        user_id,
        count(event_id) as event_count
    from events
    group by user_id
),

final as (
    select
        s.user_id,
        s.session_id,
        ec.event_count
    from sessions as s
    left join event_counts as ec
        on s.user_id = ec.user_id
)

select * from final
```

**Regression test**:
```yaml
- name: primary_key_column
  tests:
    - unique
    - not_null
```

---

## 2. Incorrect Incremental Strategy

**Symptom**: Duplicates appear only in incremental runs, not full refreshes.

**Bad** — `unique_key` doesn't match the actual grain:
```sql
{{
    config(
        materialized='incremental',
        unique_key='user_id'
    )
}}

select
    user_id,
    session_date,
    session_count
from {{ ref('int_daily_sessions') }}
{% if is_incremental() %}
    where session_date > (select max(session_date) from {{ this }})
{% endif %}
```
The grain is `(user_id, session_date)` but `unique_key` is only `user_id`, so the merge/upsert overwrites rows incorrectly or creates duplicates depending on the adapter strategy.

**Fix** — match `unique_key` to the actual grain:
```sql
{{
    config(
        materialized='incremental',
        unique_key=['user_id', 'session_date'],
        incremental_strategy='merge'
    )
}}
```

---

## 3. NULL Key Fanout

**Symptom**: Unexpected row explosion when NULL values exist in join keys.

**Bad** — NULL joins to every other NULL:
```sql
select *
from orders as o
left join returns as r
    on o.return_id = r.return_id
```
If `return_id` is NULL on multiple orders and multiple returns, each NULL matches every other NULL (adapter-dependent).

**Fix** — filter NULLs or use COALESCE with a sentinel:
```sql
select *
from orders as o
left join returns as r
    on o.return_id = r.return_id
    and o.return_id is not null
```

---

## 4. Missing GROUP BY Column

**Symptom**: Aggregation returns more rows than expected, or query errors on strict SQL modes.

**Bad**:
```sql
select
    user_id,
    plan_type,
    sum(amount) as total_amount
from payments
group by user_id
```
`plan_type` isn't in GROUP BY — some warehouses pick an arbitrary value, others error.

**Fix**:
```sql
select
    user_id,
    plan_type,
    sum(amount) as total_amount
from payments
group by user_id, plan_type
```

---

## 5. Wrong Join Type

**Symptom**: Rows silently dropped or unexpected NULLs appear.

**Bad** — INNER JOIN drops users with no orders:
```sql
select
    u.user_id,
    o.order_id
from users as u
inner join orders as o
    on u.user_id = o.user_id
```

**Fix** — use LEFT JOIN when you want to preserve the left table's grain:
```sql
select
    u.user_id,
    o.order_id
from users as u
left join orders as o
    on u.user_id = o.user_id
```

---

## 6. Window Function Without Proper PARTITION BY

**Symptom**: Running totals, ranks, or dedup logic applies across the entire table instead of per-group.

**Bad**:
```sql
select
    user_id,
    event_date,
    row_number() over (order by event_date desc) as row_num
from user_events
```
This ranks across *all* users, not per user.

**Fix**:
```sql
select
    user_id,
    event_date,
    row_number() over (
        partition by user_id
        order by event_date desc
    ) as row_num
from user_events
```

---

## 7. Snapshot / SCD Logic Producing Overlapping Valid Ranges

**Symptom**: A `dbt_valid_from` / `dbt_valid_to` query returns multiple "current" rows for the same entity.

**Diagnosis**: Check for overlapping validity windows:
```sql
select entity_id, count(*)
from snapshot_table
where dbt_valid_to is null
group by entity_id
having count(*) > 1
```

**Fix**: Ensure the snapshot `unique_key` matches the natural key. If the source has late-arriving updates, add a dedup CTE before the snapshot selects from the source.
