---
name: trading-continuous-learning
description: >-
  Continuous-learning loop for the ssr-analyst options/income trading agent.
  Captures misses and wins as dated lessons, refines strategy from backtests,
  enforces the earnings/event gate, and surfaces at least one vetted defined-risk
  idea per trading day. Use at the start of every trading session, whenever the
  user asks to "check" the market / find trades, after any notable miss or win
  (e.g., a missed earnings move), or when reconciling monthly trade cadence.
---

# Trading — Continuous Learning

Make the trading agent get measurably better over time: never miss the same setup
twice, keep the strategy backtest-validated, and produce a steady cadence of
*vetted* trades — not forced ones.

## ⭐ Standing goal — 1–2 green closes per trading day (learning mode always ON)

The north star: **realize 1–2 *green* (profitable) closes every trading day.** Learning
mode is permanently on — every session reads the log, every notable event writes a lesson.

**How to actually hit it (the mechanism, not a quota):**
- Run a **rolling book** — keep 6–8 staggered positions open so something is hitting its
  profit target most days.
- **Take profit fast:** GTC close at **50%** of max on high-IV put-credit spreads (they
  reach it in days via theta + IV crush) → frequent green closes, capital recycles.
- **Stagger entries** across the week so expiries/targets land on different days.
- Favor **high-probability structures** (put credit on a confirmed hold) for the steady
  green; use call-debit for the occasional fat-tail winner.

**The honest guardrail (this protects the goal, doesn't weaken it):**
- No strategy closes green *every* day — an ~80% win rate still loses ~1 day in 5, and
  markets are shut on weekends/holidays. The commitment is the **process**, not a
  fabricated daily win.
- **Never force a trade to "make the number."** One forced max-loss erases a week of green
  closes (the AVGO / backtest lesson). A logged **stand-down** on a hostile tape *protects*
  the streak — it counts as doing the job.
- Measure the goal over a **rolling 5-day window**, not a rigid single day.

## System files (read these at session start)

| File | Role |
|---|---|
| `ssr-analyst/Documents/agent_learning_log.md` | **Lessons + month tally + tomorrow's first-check.** Read FIRST, append after every notable event. |
| `ssr-analyst/Documents/monthly_income_plan.md` | The operating system (cadence, sizing, exits, strategy matrix). |
| `ssr-analyst/Documents/options_watchlist.md` | Live play cards + armed trades + backtests. |
| `ssr-analyst/Documents/backtest_multistrategy.md` | Strategy expectancy (regenerate to validate changes). |
| `ssr-analyst/Documents/momentum_watchlist.md` | **Momentum/discovery layer** — leaders outside MANGOS/semis-10, armed pullback alerts, and the `SelfIDB50` command. |
| `ssr-analyst/Documents/catalyst_cards.md` | **T+0/T+1 armed tickets** — one card per earnings / investor day / mapped peer. Overwrite every evening wrap + FULLCHECK. Missing card on a known event = miss (XE/SNDK 8/13). |

## Named commands (user can invoke anytime)

| Command | What it runs |
|---|---|
| `FULL CHECK` (a.k.a. fullcheck, full check) | **The everything-command — the complete battery on demand.** Same engine as the 8/11/1 strategy-battery loop, run interactively. See the full 12-step spec below. Ends with a ranked plan (🟢 take / 🟡 arm / 🔴 stand-down), options-book vs $1k-sleeve split, **catalyst cards for every T+0/T+1 event**, and updates `catalyst_cards.md` + `next_day_prep.md` + `momentum_watchlist.md`. **Read-only by default** — surfaces action tickets (e.g. an NNE close), waits for the user's go before placing. |
| `SelfIDB50` (a.k.a. selfidb50, Self-IDB-50) | **Self-serve, no-login replacement for IBD's paywalled lists** (the momentum-discovery *slice* inside FULL CHECK). Full spec in `momentum_watchlist.md`. Steps: (1) fetch FFTY holdings `stockanalysis.com/etf/ffty/holdings` (public IBD-50 proxy); (2) run own RS screen via `rs_screen.py` (get_equity_historicals 3mo → rank by 3mo return + %-from-high + 1mo momentum); (3) top-gainers web check; (4) apply full battery (earnings gate → concentration cap → anti-chase → correlation → liquidity); (5) output ranked cross-sector shortlist, prefer non-tech diversifiers. _Validated Jul 9 2026: caught ALAB #1 with zero IBD input._ |

### `FULL CHECK` — the 12-step spec (run in order)

1. **Tape / macro** — SPY · QQQ · SMH · VXX · 10Y live; regime read.
2. **Cross-sector gate** — rank all 11 GICS ETFs (no tech-first bias); identify leaders/laggards.
3. **Book health check** — every open position: cushion %, short-leg delta, hold/manage/close call, GTC status.
4. **Health Check model (4-model composite)** — STKK + STNOW + Three Good + Whale → direction × IV score per candidate.
5. **Event gate (two outputs, not one)** — earnings + CPI/PPI/PCE/FOMC + **investor / analyst / capital-markets days** before the next expiry. Output (a) is the hard "no new credit sells into X" line. Output (b) is a **T+0/T+1 catalyst card** for every named event (take / arm / stand-down **with structure, trigger, same-day exit**) per `catalyst-overnight-plan`. **"No XE anything" / "don't chase" is not output (b).** Fail the FULLCHECK if any 0d/1d event has no card. Calendar = Nasdaq radar ∪ Robinhood `get_earnings_calendar` ∪ fundamentals next-earnings on book/watch/peers ∪ web search for investor days (radar missed XE 8/13; investor days never appear on radar).
6. **STKK** (trend/historicals) + **STNOW** (fundamentals) + **Three Good** on top candidates.
7. **Whale Watch** — option volume vs OI on busy strikes for candidates + book names (fresh institutional flow; disregard on a live catalyst — flow is prior-session/stale).
8. **SelfIDB50** — momentum discovery (FFTY + RS screen + armed-alert check + anti-chase parabolic gate).
9. **WSJ + MarketWatch** — headline / regime / catalyst read. **Required query every run:** `"investor day" OR "analyst day" OR "capital markets day"` on book + SMH/memory/AI + READTHROUGH peers (the 8/13 SNDK miss).
10. **Route** each survivor through the direction × IV matrix (bull+lowIV→call debit · bull+highIV→put credit · bear+highIV→call credit · bear+lowIV→put debit · range+highIV→iron condor).
11. **Backtest** — run `python3 market_data/backtest_strategies.py --md` on any *new* proposed structure before promoting it; only advance if it improves expectancy (RoR).
12. **Output** — ranked plan (🟢 take · 🟡 arm/wait-for-trigger · 🔴 stand-down), each with structure/strikes/sizing/entry-trigger/stop-target; split options-book vs $1k agentic sleeve; **lead with today's catalyst cards** (confirm / fire / kill from overnight `catalyst_cards.md`); write/overwrite `catalyst_cards.md` + `next_day_prep.md` + `momentum_watchlist.md`. **Read-only by default: surface action tickets, wait for the user's go.**

## Session-start ritual (do this on the first "check" of the day)

**ONE command runs the whole pipeline:** `python3 market_data/daily.py` — it does steps 2–5
below (refresh, macro + Tomorrow tilt, MANGOS, earnings gate, full Health Check composite) and
ranks the GO verdicts into today's candidate(s). Flags: `--quick` (skip refresh/earnings),
`--all` (scan universe), `daily.py SYM …` (specific names), `--to YYYY-MM-DD` (whale expiry).
Read the log first (step 1), then run it, then interpret + manage the book.

```
- [ ] Read agent_learning_log.md (lessons + open watch items + tomorrow's first-check)
- [ ] Read catalyst_cards.md — lead the session with confirm/fire/kill on overnight cards (if missing on a 0d/1d event, that is already a miss)
- [ ] Run: python3 market_data/daily.py   ← refresh + macro + MANGOS + earnings gate + Health Check + candidate
- [ ] Manage open book (stops, GTC targets)
- [ ] Interpret daily.py output → surface ≥1 vetted idea (strikes/sizing/stop) OR an explicit stand-down
```

Manual fallback if `daily.py` errors: pull macro (SPX/VIX/QQQ/10Y/BTC), MANGOS (META·NVDA·GOOGL·SPCX
+ proxies AMZN/MSFT), regenerate `earnings_radar.md`, then `health_check.py <focus list>`.

**On "what's today's plan":** the MANGOS cross-check is mandatory — lead the plan with the
AI-leadership pulse, then the open book, then the day's vetted idea(s).

## Daily-idea routine — one *vetted* idea per day

1. **Scan** the cached universe with Health Check; rank by verdict.
2. **Route** each candidate by the **direction × IV matrix** (see monthly_income_plan §3.5):
   bull+lowIV→call debit · bull+highIV→put credit · bear+highIV→call credit ·
   bear+lowIV→put debit · range+highIV→iron condor.
3. **Gate**: drop anything with earnings/CPI/PCE/FOMC in the window (for credit sells),
   thin liquidity, cushion <8%, or credit/width <25%.
4. **Confirm**: require a held level / first-hour hold — never enter into a slide or a gap.
5. **Surface ≥1** defined-risk idea with strikes, sizing (to the $300–500 target), and a
   stop. If nothing passes, **say "stand down" and why** — see the cadence rule.

## The cadence rule (quality > quota)

The user wants ~10–15 closes/month and ideally one trade/day. **Honor the spirit, not a
blind quota.** The v2 backtest proved forcing trades loses: the disciplined router won by
**standing down 27% of the time**. So:

- **Always surface a candidate daily**, but label it honestly: 🟢 take · 🟡 wait-for-trigger · 🔴 stand-down.
- **Never force a credit sell into an event** (the AVGO −$1,717 / MU lessons).
- A "stand-down day" with a logged reason **counts as doing the job** — it protects the month.
- Prefer **small defined-risk** entries to keep cadence without betting the book.

## Lesson capture (append after every notable event)

After a miss, a notable win, a rule change, or a backtest result, append a dated entry to
`agent_learning_log.md` using this template — newest first:

```markdown
### YYYY-MM-DD — <short title>  [MISS | WIN | RULE | BACKTEST]
- **What happened:** <facts, prices, the setup>
- **Root cause:** <why it was missed / what worked>
- **Rule / fix:** <the durable change to behavior or the system>
- **Status:** <pending build | adopted | validated>
```

Triggers that REQUIRE a new entry:
- A move the agent should have flagged but didn't (e.g., a missed earnings run).
- A user **hint** about a name that wasn't fully chased → log "treat hints as a full-check directive."
- Any change to gates, sizing, or the strategy matrix (cross-link the backtest).

## Strategy refinement loop

- Re-run `python3 market_data/backtest_strategies.py --md` when a gate/rule changes.
- Only promote a change into the plan/watchlist if it **improves expectancy (RoR)**, not win rate alone.
- Keep the four models (STKK, STNOW, Three Good, Whale) and the matrix as the decision spine.

## Hard-won rules (keep enforcing)

1. **Earnings/event gate is the #1 edge** — never sell premium through earnings/CPI/PCE/FOMC.
2. **A user hint about a ticker = run a full Health Check including the earnings calendar.**
2b. **Bellwether read-through (the MU→SNDK lesson):** when a sector bellwether gaps on
    earnings/guidance **or a mapped peer is already ripping**, **scan its sympathy peers the SAME session**
    and play it as a **catalyst-day momentum trade with a same-day exit** — not a hold or a
    credit sell. Fire the radar if the **bellwether is ≥5% OR any mapped peer is ≥7%** (8/13:
    MU +5.8% did not trip the old 7% gate while SNDK was +15%). Investor days / guidance days
    count as catalysts. The Whale flag uses *prior-session* volume, so it's **stale on a live
    catalyst — disregard it** and read the live tape + IV. Map: **MU**→SNDK/WDC/STX/NTAP/semis ·
    **NVDA**→AVGO/AMD/TSM/SMCI/CRWV · **AVGO**→NVDA/AMD/MRVL · **TSLA**→RIVN/CHPT. Catch it *on*
    the catalyst day — chasing the next day is where the loss is (SNDK +22% on 6/25 → −10.5% on 6/26).
2c. **T+1 catalyst card (the XE / SNDK 8/13 miss):** every FULLCHECK and evening wrap must
    output an armed ticket (or explicit stand-down **with the structure you would have used**)
    for **each** earnings, investor day, and mapped-sympathy name in the next session. See
    `catalyst-overnight-plan`. "Stand down / no XE anything" is the event gate, not the plan.
    Anti-chase applies at **entry after the move**; it does **not** cancel overnight arming.
    If a leftover short put sits into the print, **close it T−1**. Nasdaq `earnings_radar` ∩
    universe is not sufficient — UNION Robinhood calendar + fundamentals + investor-day search.
3. **Don't chase a post-earnings gap as a HOLD or with a credit sell** — high IV crush after
    the print is a put-spread-on-a-hold setup, not a call you sleep in. A **same-day defined-risk
    debit armed T−1 and confirmed in the first 15–30 min** is allowed. Unarmed chase after the
    name is already +7% this morning = stand down (6/26 SNDK, 8/13 SNDK 9:10 AM).
4. **One max loss erases ~3–6 wins** — size for the tail, stops are non-negotiable.
5. **Bullish core (put-credit + call-debit); bearish only on confirmed breakdowns.**
