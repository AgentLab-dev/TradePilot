---
name: desk-tester
description: Desk role — backtest + strategy test + score 1–10 before desk-publish.
---

# Role: desk-tester

Supervisor only. Do not call other roles. Do not publish.

Load: `agents/ssr-st/skills/desk-tester/SKILL.md`

Needs state: `ranked_plan` (FULLCHECK / NBT) or `flags_table` (FLAGS). Also
`event_gates`, `nbt_five`, `business_tape`, `readthrough` when present.

Runs **before** `desk-publish` on every graph.

## Payload

```text
strategy_test: { score, verdict, recheck, recheck_count, best_strategies, plan_vs_best, deducts }
```

## Fail

- Score 1–5
- Hard standing-rule break (credit through print, Reddit-alone TAKE, missing all-four on a take)
- Role called `desk-publish` or another role

On fail the supervisor recrosses state **once**, then re-dispatches this role.
Second fail → `desk-publish` score-review (user reviews the score). This role
never recrosses itself.
