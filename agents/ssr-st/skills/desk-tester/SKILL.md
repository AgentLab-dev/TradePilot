---
name: desk-tester
description: >-
  Desk tester. Backtest + strategy test + score 1–10 before desk-publish.
  Shows best-scoring strategies. Fail (<6 or a hard gate) returns to the
  supervisor for one recross, then this role runs again. Second fail publishes
  the score to the desk for user review (no go). Use on FULL CHECK, FLAGS, NBT.
---

# Desk tester

Last gate before `desk-publish`. Roles never call each other. The supervisor
dispatches this role, reads the `RoleResult`, and may recross once.

Pack script: `agents/ssr-st/workspace/Documents/market_data/backtest_strategies.py`  
Companion: `trading-continuous-learning` step 11. Human checklist still names
that step; this role is the machine run.

## When

Every graph, after `rank-next-best` (FULLCHECK / NBT) or after `flags` (FLAGS),
and **before** `desk-publish`. Do not skip. Do not publish a 🟢 / 🟡 ticket
that this role has not scored.

## Inputs (from supervisor state)

| Graph | Required state |
|---|---|
| `FULLCHECK` / `NBT` | `ranked_plan` + `flags_table` + `event_gates` + `nbt_five` |
| `FLAGS` | `flags_table` (no new structures — score the 4-model table only) |

Also use `business_tape`, `readthrough`, `list_tickets` when present.

## What to run

1. **Backtest** — on the ranked / flagged tickers (else the cached universe):

```text
python3 agents/ssr-st/workspace/Documents/market_data/backtest_strategies.py TICKER [...] --md
```

`--md` overwrites `agents/ssr-st/workspace/Documents/backtest_multistrategy.md`.
If history is missing, run `fetch_history.py` on those names once, then retry
the script. A script miss is `warn` (−2), not an automatic fail, unless a
**new** structure is being promoted (then it is fail).

2. **Strategy test** — map each 🟢 / 🟡 row’s structure to one of:

| Structure | Backtest key |
|---|---|
| Put credit | `put_credit` |
| Call debit | `call_debit` |
| Call credit | `call_credit` |
| Put debit | `put_debit` |
| Iron condor | `iron_condor` |
| Calendar | `calendar` |

Compare that key’s RoR expectancy to the **v2 router (confirm + event gate)**
row. Credit through a print / CPI / PCE / FOMC is a hard fail regardless of RoR.

3. **Score 1–10** (integer). Start at 10. Apply the rubric. **1 = low, 10 = high.**

4. **Best strategies** — rank the six structures + v2 router by RoR expectancy.
Print the top three. Say whether the ranked plan uses one of those three.

## Score rubric

| Deduct | When |
|---|---|
| set to **1** | Credit through print / CPI / PCE / FOMC |
| set to **1** | Reddit-alone 🟢 |
| set to **1** | Hard standing-rule break the supervisor already listed |
| −3 | Ranked take/arm missing STKK · STNOW · 3Good · Whale |
| −3 | Mix: all five are prints + book manage |
| −2 | Hard NBT slot with EM ≤ 15% |
| −2 | Analog ≥1.5× EM with no second-name ticket |
| −2 | 0d AMC/BMO and `readthrough` missing |
| −2 | Capture ran and `business_tape` missing |
| −2 | Proposed structure RoR is negative while v2 router is not |
| −2 | STKK/STNOW ⚪ stale-cache treated as a pass |
| −2 | Backtest script could not run (no history) on a **new** structure |
| −1 | Proposed structure is not in the top-3 RoR list for this universe |
| −1 | FLAGS row missing a model |

Floor is 1. Do not invent a 10 when any deduct fired.

## Pass / fail

| Score | Status | Meaning |
|---|---|---|
| **7–10** | `ok` | Publish may proceed (still wait for **go**) |
| **6** | `warn` | Publish may proceed; print the deducts |
| **1–5** | `fail` | First fail: supervisor recross, then this role again. Second fail: `desk-publish` score-review |

Hard-fail lines (score forced to 1) also set `status=fail` even if you would
have scored higher.

## Fail → supervisor recross (once)

On `fail`:

1. Return `RoleResult` with `payload.strategy_test.recheck = true`.
2. Do **not** call `desk-publish`. Do **not** call another role.
3. Supervisor re-reads standing rules vs state (see supervisor skill).
4. Supervisor re-dispatches **this role once** (`recheck_count` 0 → 1).
5. Second `fail` → supervisor sends `strategy_test` to **`desk-publish` in
   score-review mode**. Print the score, best strategies, and deducts on the
   desk. Do **not** treat 🟢 as go-ready. Wait for the user to review.

This role never recrosses itself.

## Payload

```text
strategy_test: {
  score: 1-10,
  verdict: pass|warn|fail,
  recheck: bool,
  recheck_count: 0|1,
  best_strategies: [{ name, ror_exp, win_pct, rank }],
  plan_vs_best: [{ ticker, structure, in_top3, ror_exp }],
  deducts: [string],
  script: ok|warn|skip
}
```

## Required output block

```markdown
## Desk tester
Score: <1-10>/10 (<pass|warn|fail>)
Best strategies:
1. <name> — RoR <x%> · win <y%>
2. …
3. …
Plan vs best: <TICKER structure in_top3|not>
Deducts: <list or none>
Recheck: <no | supervisor recross then re-test>
```

## Fail lines

- Score **1–5** on the first pass (triggers recross, not a silent skip)
- `desk-publish` reached without this payload
- Role tried to recross itself or place an order
- Score-review publish treated as **go**

Wait for the user to review a failing score. A passing score still waits for **go**. Defined-risk only.
