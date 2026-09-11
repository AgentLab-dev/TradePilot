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
| `SelfIDB50` (a.k.a. selfidb50, Self-IDB-50) | Momentum-discovery slice. **First** run `ibd-wsj-capture` (live IBD 50 + other Stock Lists). FFTY + `rs_screen.py` is fallback if Sign In blocks. Then earnings gate → concentration → anti-chase → liquidity. Prefer non-tech when the book is tech-heavy. |

### `FULL CHECK` — the 12-step spec (run in order)

1. **Tape / macro** — SPY · QQQ · SMH · VXX · 10Y live; regime read; **MANGOS** pulse (META·NVDA·GOOGL·SPCX + proxies AMZN/MSFT). Fail if MANGOS is omitted or left n/a with no live-quote fallback.
2. **Cross-sector gate** — rank all 11 GICS ETFs (no tech-first bias) **and** industry sleeves (GDX · IGV · SMH · XOP · KRE); identify leaders/laggards. Fail if only the 11 GICS ETFs are ranked (gold/miners vs XLB, 9/3).
3. **Book health check** — every open position: cushion %, short-leg delta, hold/manage/close call, GTC status, abort. Fail if any open position lacks a GTC status and abort line (abort fired → same-session BTC, not "watch").
4. **Health Check model (4-model composite)** — STKK + STNOW + Three Good + Whale → direction × IV score per candidate. Fail if any candidate / NBT / book row omits STKK · STNOW · 3Good · Whale (3Good does not veto a debit).
5. **Event gate + miss-fix skills:** (a) no new credit into X. (b) T+0/T+1 catalyst card per `catalyst-overnight-plan`. (c) **PPS-T7** flag + week monitor per `pre-print-screen/t7.md` for category names 2–7d out. (d) **PPS-T1** flag + into-print score per `pre-print-screen/t1.md` for 0d/1d. (e) last-90 EM recapture (`pps-t1-em-recalibrate`) — whale IV×√T is not EM. (f) 0d AMC guesstimate (`print-ah-guesstimate`). (g) analog ≥1.5× EM → ARM + second-name ticket (`print-analog-vs-em`). (h) AH ≥±7% unfilled → STAND, screen next (`post-print-gap-capture` + `next-25-print-screen`). (i) every debit passes `option-chain-liquidity-gate`. Fail if the ranked table omits **PPS-T7** or **PPS-T1**, if a ≥+7% AH name is ranked as a chase, or if analog has no second-name card. Calendar = Nasdaq radar ∪ Robinhood `get_earnings_calendar` ∪ fundamentals ∪ investor-day search.
6. **STKK** (trend/historicals) + **STNOW** (fundamentals) + **Three Good** on IBD unique + GICS/sleeve unique + book + 0d/1d — not only on print finalists. Fail if a finalist skips this pass because Health Check already ran, or if 3Good vetoes a call debit. Fail if STKK/STNOW are ⚪ stale-cache on every ranked row (HPE 9/2) — refresh cache or run `daily.py`; ⚪ is a skip, not a pass.
7. **Whale Watch** — option volume vs OI on busy strikes for candidates + book + NBT **and** IBD/sleeve unique names (fresh institutional flow; disregard on a live catalyst — flow is prior-session/stale). Fail if `daily.py` whale n/a is treated as skip — run `whale_check.py` on that set, not only 0d/1d prints (8/26).
8. **SelfIDB50 + IBD lists** — load `ibd-wsj-capture` (this repo’s desk-sources path is `news-portals` + `ibd-wsj-capture`; there is no `desk-sources-capture` folder). **SSO (confirmed 2026-09-09):** Log in **once at WSJ** (`https://www.wsj.com/`). Then open **IBD from the WSJ header**. That autologins IBD + MarketWatch + Barron's. Do **not** start at `https://www.investors.com/?ibdsilentlogin=true` unless the WSJ header IBD link is missing. Pull live IBD 50 / Sector Leaders / Big Cap 20 / Spotlight / New Highs / RS at New High / IPO Leaders / Funds Buying. Playwright MCP is valid; Cursor Browser Tab is optional. Open MarketTrend (page required; % optional). **Do not ask the user to paste.** Overwrite `ibd_stock_lists.md` dated today. FFTY + `rs_screen.py` only if Sign In still blocks after Take Control / **done**. Anti-chase still applies. **Fail if** IBD 50 is not live today (and Sign In was not the blocker), if a listed Stock List URL was not opened, or if the agent asked for a paste.
9. **WSJ + MarketWatch + Barron's + Reddit SOCIAL-ONLY** — load `news-portals` + `ibd-wsj-capture` (Playwright MCP → optional Cursor Browser Tab → Safari/Chrome tail → RSS). Same SSO as step 8: WSJ first, then IBD from the WSJ header; then MW / Barron's from the Dow Jones hat if needed. RSS is the floor, not a substitute (WSJ RSS is months stale). Headline / regime / catalyst read. **Required query every run:** `"investor day" OR "analyst day" OR "capital markets day"` on book + SMH/memory/AI + READTHROUGH peers (the 8/13 SNDK miss). **Also required:** `{TICKER} earnings` on every 0d/1d name (the 8/26 OKTA miss — homepage was NVDA) **and** on every PPS-T7 2–7d category name. Calendar UNION from step 5 still applies here: Nasdaq radar ∪ Robinhood `get_earnings_calendar` ∪ fundamentals ∪ investor-day. **Reddit SOCIAL-ONLY (required, additional):** open + scan r/algotrading, r/Quant, r/stocks, r/investing, r/StockMarket, r/wallstreetbets, r/options, r/semiconductors (public, no login). Optional: r/spacs, r/pennystocks, ApeWisdom, SwaggyStocks. Never Reddit-alone TAKE. IBD capture does not scrape Reddit. **Fail if** WSJ, header IBD, MW, or Barron's was not actually opened, if the Reddit check was skipped, if the investor-day query was not run, if a 0d/1d name has no `{TICKER} earnings` line, if a PPS-T7 ON name has no ticker-earnings line, or if any calendar-UNION leg is missing. Zapier has no WSJ/MW app — not a substitute. Do not skip news because Sign In is showing.
10. **Route and mix the five.** Route each survivor through the direction × IV matrix (bull+lowIV→call debit · bull+highIV→put credit · bear+highIV→call credit · bear+lowIV→put debit · range+highIV→iron condor). Fail if a credit (put or call) is routed through a print / CPI / PCE / FOMC window.
    After steps 8–9, STKK · STNOW · 3Good · Whale **must** run on a **fresh universe**: IBD 50 + Sector Leaders + Big Cap 20 + GICS/sleeve unique (GDX · IGV · SMH · XOP · KRE) + NEWS/Reddit-named tickers + book. Fail if those models ran only on tonight/tomorrow prints.
    **Standing mix:** at most **two** 0d/1d print ARMs; at least **two** names from non-calendar strategies (STKK, STNOW, 3Good, Whale, IBD 50 / list leadership, industry sleeve GDX/IGV/SMH/XOP/KRE) that are **not** on tonight/tomorrow’s earnings calendar; open-book MANAGE may take **one** slot. Fail if all five are prints + book manage (9/9). Fail if leftover-five is only a ban list while unique-sleeve winners sit on the board. Fail if STKK/STNOW are ⚪ stale-cache on every ranked row. **List → ticket:** every IBD 50 / Sector Leader / Big Cap 20 / PPS-T7 ON / ALWAYS name gets TICKET or SKIP (gate) the same session — board is a fail (OKTA/SNOW/CRM/HPE). Leading with catalyst cards is the overnight plan, not an earnings-only five.
11. **Backtest** — run `python3 market_data/backtest_strategies.py --md` on any *new* proposed structure before promoting it; only advance if it improves expectancy (RoR).
12. **Output** — ranked plan (🟢 take · 🟡 arm/wait-for-trigger · 🔴 stand-down), each with structure/strikes/sizing/entry-trigger/stop-target **and flags STKK · STNOW · 3Good · Whale · PPS-T7 · PPS-T1**; split options-book vs $1k agentic sleeve; **lead with today's catalyst cards**; write/overwrite `catalyst_cards.md` + `next_day_prep.md` + `momentum_watchlist.md` + `print_monitor.md`. Fail if any ranked row omits STKK · STNOW · 3Good · Whale. Fail if the five recycle last session's unused names without a live unique-sleeve win **in the five** (rewrite `NBT.md`; leftover five 9/2). A ban list plus board names is not a unique-sleeve win (AUGO/ECO 9/9). PPS-T1 is **one** fill; analog second-name is a written card, not three print slots. Book MANAGE is allowed; it does not pad remaining slots with more 0d/1d names. Leading with catalyst cards is the overnight plan, not an earnings-only five. Fail `list-to-ticket` if a listed name has neither TICKET nor SKIP. Near 10:00 AM PT or 3:00 PM PT, write `daily_lessons/YYYY-MM-DD.md` (`daily-mover-lesson`): listed names up/down, what helped the move, next-pick strategy. Fail if Sheet or BQ `daily_top5` is skipped or prior `is_latest=Y` rows are not flipped to N. **Read-only by default: surface action tickets, wait for the user's go.**

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
    **NVDA**→AVGO/AMD/TSM/SMCI/CRWV · **AVGO**→NVDA/AMD/MRVL · **TSLA**→RIVN/CHPT ·
    **CRWD**→OKTA/PANW/ZS/FTNT/NET/S. Catch it *on*
    the catalyst day — chasing the next day is where the loss is (SNDK +22% on 6/25 → −10.5% on 6/26).
2c. **T+1 catalyst card (the XE / SNDK 8/13 miss):** every FULLCHECK and evening wrap must
    output an armed ticket (or explicit stand-down **with the structure you would have used**)
    for **each** earnings, investor day, and mapped-sympathy name in the next session. See
    `catalyst-overnight-plan`. "Stand down / no XE anything" is the event gate, not the plan.
    Anti-chase applies at **entry after the move**; it does **not** cancel overnight arming.
    If a leftover short put sits into the print, **close it T−1**. Nasdaq `earnings_radar` ∩
    universe is not sufficient — UNION Robinhood calendar + fundamentals + investor-day search.
2d. **PPS-T7 (pre-print screen, week monitor):** category names 2–7d from a print
    (ALWAYS ∪ history groups ∪ book ∪ IBD ∪ industry map) get a daily WSJ/MW/peer/EM
    watch on `print_monitor.md`. **No fill.** Flag **PPS-T7** 🟢 ON / 🟡 THIN / ⚪ / ⬛ DONE.
2e. **PPS-T1 (pre-print screen, into-print fill):** separate strategy. On 0d / last 90 min,
    cheap OTM debit if EM% ≥15% and beat/theme/cluster fire (OKTA would have been 160/170).
    Flag **PPS-T1** 🟢 TAKE / 🟡 ARM / 🔴 STAND / ⚪ / ⬛ MISS. Do not buy ATM a week early
    (8/9 2-week reject). Do not rank by mega-cap. Whale does not veto. OKTA 8/26 was
    PPS-T7 never-on and PPS-T1 ⬛ MISS.
3. **Don't chase a post-earnings gap as a HOLD or with a credit sell** — high IV crush after
    the print is a put-spread-on-a-hold setup, not a call you sleep in. A **same-day defined-risk
    debit armed T−1 and confirmed in the first 15–30 min** is allowed. Unarmed chase after the
    name is already +7% this morning = stand down (6/26 SNDK, 8/13 SNDK 9:10 AM).
4. **One max loss erases ~3–6 wins** — size for the tail, stops are non-negotiable.
5. **Bullish core (put-credit + call-debit); bearish only on confirmed breakdowns.**
