---
name: evening-wrap-nextday-prep
description: >-
  Post-close EVENING WRAP + next-day prep for the ssr-analyst trading agent. Runs
  once after US after-hours closes (~6 PM PT). Sweeps the day: market close +
  after-hours moves, news (WSJ, MarketWatch, Yahoo Finance, Reuters/CNBC),
  options whale watch (unusual activity, volume vs OI), analyst rating changes,
  projections, and the next-day macro/earnings calendar — then writes tomorrow's
  game plan to next_day_prep.md so the morning loops start warm. Use at end of the
  trading day, when the user asks for an "evening wrap", EOD summary, or "prepare
  for next day".
---

# Evening Wrap & Next-Day Prep

The end-of-day counterpart to the morning battery. Goal: **close the loop on today and
pre-stage tomorrow** so the 8 AM strategy run and 8:30 AM portfolio check start with a thesis,
not a blank page.

## When
Once per weekday, **after US after-hours fully closes (8 PM ET / ~5 PM PT)** — default fire
**6:00 PM PT**. Skip weekends/holidays. It's a *review + prep* run, **not** a trading run — the
market is closed, so it places **no orders**; it produces analysis and stages tomorrow's plan.

## The sweep (do all eight, in order)

1. **Close + after-hours tape** — pull final closes for the book + the tape (SPX/QQQ/VIX proxies,
   10Y) and any notable after-hours movers among held/watch names. State % vs prior close.
2. **News watch** — load `news-portals` + `ibd-wsj-capture`. Capture IBD Stock Lists and WSJ homepage in the Cursor browser (**do not ask for a paste**). Run `news_portals.py` (RSS floor). Search
   **WSJ, MarketWatch, Yahoo Finance** (+ Reuters/CNBC as backup) for today's
   market-moving story, sector rotation, and book/watch names. **Required extra
   query every wrap:** `"investor day" OR "analyst day" OR "capital markets day"`
   on SMH/memory/AI + book + READTHROUGH peers (SNDK 8/13 was not on the earnings
   radar). Cite sources with dates. Do not store portal passwords.
3. **Options whale watch** — scan for **unusual options activity** into the close: high relative
   options volume, call/put skew, and **volume vs open interest** (vol ≈ OI or ≫ OI = freshly
   opened positioning). Flag fresh institutional bets; separate conviction from hedges and from
   binary M&A-rumor spikes.
4. **Analyst ratings** — note today's upgrades/downgrades, price-target changes, and initiations
   on book/watch names and sector bellwethers (source the firm + new PT + direction).
5. **Projections / levels** — for each held name and the top 2–3 watch names, set **next-day
   levels**: support/resistance, the recycle target(s), and the invalidation (stop) level.
6. **Next-day catalyst calendar + cards** — earnings (before/after), **investor / analyst /
   capital-markets days**, macro prints (CPI/PCE/PPI/jobs/FOMC), Fed speakers, and mapped
   sympathy peers of anything that moved ≥5% today. Calendar sources are a UNION: Nasdaq
   `earnings_radar.md` ∩ universe is **not enough** (missed XE 8/13). Also pull Robinhood
   `get_earnings_calendar`, `get_equity_fundamentals` next-earnings on book/watch/READTHROUGH
   peers, and web-search `"investor day" OR "analyst day" OR "capital markets day"`.
   **Feed the event gate** (no premium selling into a print) **and** write one **catalyst card**
   per T+1 name (take / arm / stand-down **with structure, first-30-min trigger, same-day exit**)
   into `catalyst_cards.md`. "No XE anything" is not a card. Anti-chase does not cancel overnight
   arming. Skill: `catalyst-overnight-plan`.
7. **Regime read** — one-line verdict: risk-[REDACTED] / risk-[REDACTED] / rotation, and what would flip it.
8. **Oversold-bounce offense scan** — the counter to playing only defense into a washout (see
   `agent_learning_log.md` 2026-07-21). Whale watch catches *single-name* flow; it is blind to a
   *broad sector reversal*, which is macro/positioning-driven overnight. So run a separate offense
   pass every evening:
   - **Trigger to arm:** a sector (semis/SMH, or any leadership group) is **down 3+ days into
     oversold** *and* positioning is **washed out** — record hedge-fund de-risking, spiking
     put/call, capitulation headlines. That combination = a mean-reversion snapback is
     statistically likely (and "everyone's dumping" is a *contrarian* buy tell, not a bearish one).
   - **What to produce:** pre-arm the group **leaders** (e.g., MU/AMD/SMCI/AVGO/SMH/NVDA) with a
     **"buy-the-confirmed-reclaim" trigger** — e.g., *SMH reclaims prior-day high*, or a leader
     *gaps up and holds the first 30 min*. Names + triggers armed the night before; **entry stays
     on confirmation** (a bounce can fade — pre-empting = knife-catching), but the offense is ready,
     not hindsight.
   - Pair this with the defensive book check: every evening ask **both** "what breaks my book?"
     *and* "what's the contrarian oversold-bounce setup I should be armed for?"

## Output — write `next_day_prep.md`

Write/overwrite `ssr-analyst/Documents/next_day_prep.md` (a rolling system file the morning loops
read). Structure:

```markdown
# Next-Day Prep — <weekday, date>  (generated <time> PT)

## TL;DR (3 lines)
- Regime: <risk-[REDACTED]/off/rotation + one driver>
- Book status: <GOOGL + options positions, any action needed at open>
- Tomorrow's #1 focus: <the one thing>

## 1. Today's close + after-hours
## 2. News that matters (WSJ / MW / Yahoo — cited)
## 3. Whale watch (fresh options flow, vol vs OI)
## 4. Analyst rating changes
## 5. Next-day levels (per name: support / resistance / recycle target / stop)
## 6. Catalyst calendar (earnings + investor/analyst days + macro + event-gate flags)
## 6b. Tomorrow's catalyst cards (one row per T+1 event: take/arm/stand-down + structure + trigger + same-day exit — "no credit sell" is not a row)
## 7. Oversold-bounce offense watch (armed leaders + confirm-the-reclaim triggers, or "none — no washout")
## 8. Pre-staged plan for the 8 AM battery (candidates to confirm at the open; **lead with the catalyst cards**)
```

Then append a 1-line pointer in `agent_learning_log.md`'s "Tomorrow's first-check" if the plan
changed materially.

## Hard rules
1. **No orders** — market is closed; this run analyzes and stages only.
2. **Cite news with source + date** — distinguish today's fresh catalyst from stale/13F data.
3. **Whale = volume vs OI**, not raw volume; skip negative-EV lotto and binary M&A spikes.
4. **Everything feeds the event gate AND a catalyst card** — surface tomorrow's earnings / investor days / macro prints explicitly, then write the directional ticket (or structured stand-down). Fail the wrap if a named T+1 event has no card (`catalyst-overnight-plan`; 8/13 XE + SNDK miss).
5. **Prep, don't predict theater** — concrete levels and if-then triggers, not vague calls.
6. **Run offense AND defense** — every wrap answers both "what breaks my book?" and "what oversold-bounce am I armed for?" Defense-only into a washout is the logged 2026-07-21 miss.
7. **Keep it re-usable** — overwrite `next_day_prep.md` **and** `catalyst_cards.md` each evening so the morning loops read current files.
