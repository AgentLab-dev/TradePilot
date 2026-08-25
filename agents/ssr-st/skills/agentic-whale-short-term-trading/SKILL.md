---
name: agentic-whale-short-term-trading
description: >-
  Operating manual for the ssr-analyst AGENTIC Robinhood account (~$1k cash,
  options level 2) — short-term / overnight / swing trades driven by whale flow
  (unusual options activity) and the sector-rotation edge. Distinct from the
  options income book. Use when the user asks the agent to place its own trades,
  find a "buy now / sell tomorrow" pick, hunt whale / unusual-options flow, run a
  Robinhood scan, or trade shares on the agentic account. Pairs with
  trading-continuous-learning (options book) and equity_strategy.md (SSR-EQ shares).
---

# Agentic Account — Whale-Flow & Short-Term Trading

This is the **agent-operated sleeve**: a small account the agent trades directly. Different
account, different instruments, different discipline than the options income book. Read this
alongside `trading-continuous-learning` (the income book) and `equity_strategy.md` (SSR-EQ).

## 0. Account facts (verify with `get_accounts` each session)

| | |
|---|---|
| **Agentic account** | `••••1451` — **cash**, options **level 2**, ~**$1,000**, `agentic_allowed=true`. The agent CAN place orders here (`place_equity_order` / options). |
| **Personal margin** | `••••5611` — `agentic_allowed=false`. Agent **cannot** trade or read its saved web screeners. Recreate any screener as a scan on the agentic account. |
| **What level-2 cash allows** | **Single-leg LONG options** (buy calls/puts) + **shares** (incl. fractional for market orders). **No** multi-leg spreads, **no** shorting, **no** selling shares you don't own. |

**Mechanics that bite:**
- You **cannot post a SELL before the BUY fills** (broker reads it as a short). Sequence: buy fills → *then* place the GTC sell-limit / stop.
- Fractional shares work on **market** orders; **limit** orders generally need whole shares.
- ~$1k means **1–2 names max**; don't pretend the options-book %-risk rules scale — size by dollars available, keep a cash buffer.

## 1. The #1 discipline rule — no blind dip-limits into a slide (the paradox)

A resting **BUY limit below market** only fills if price **keeps falling to it** → it fills you
**exactly when the bears are proven right and downside is accelerating**, and **misses entirely
if the bounce you're betting on starts from here.** A falling-limit is *backwards* for a bounce
thesis: **fills on continuation, misses on reversal.**

- For a **mean-reversion long:** require a **confirmed reclaim** (base + reclaim of level/VWAP,
  first-hour hold) — then buy. Never a blind falling limit.
- **Always attach a stop** the moment the buy fills; prefer a **scaled exit** (e.g., half at T1, rest at T2).
- **Trade WITH the flow/tape,** not against it. Don't buy a long in a name we just flagged as
  bearish-flow on a risk-[REDACTED] tape (the 2026-07-07 TSLA lesson). If bullish → buy a **leader in a
  Leading sector** (see `equity_strategy.md` §1 rotation read), not a falling laggard.

## 2. Whale-flow / unusual-options-activity read

**Goal:** find *fresh, large, one-directional* institutional bets — then decide follow vs fade.

Signals, strongest first:
1. **Volume ≈ Open Interest, or Volume ≫ OI on a single strike** → the position was **opened this
   week** (not pre-existing). This is the cleanest "fresh whale" tell.
2. **Relative options volume** (today's total vs its own average) high → attention/positioning.
3. **Call vs put volume skew** → directional lean. Confirm it's *opening* (vol vs OI), not closing.
4. **Cross-check the tape + IV live** — the Whale flag uses *prior-session* volume, so it's **stale
   on a live catalyst; disregard it and read the live tape** (the MU→SNDK bellwether lesson).

**Don't get faked out:**
- **Deep-OTM lotto** (POP <1%, e.g., a $250 put with spot ~$400) is **negative-EV** — flag the
  signal, do **not** buy the same contract. If bearish, express it with a *near-the-money* structure.
- **M&A-rumor spikes** (e.g., GFL calls 45× volume) are **binary event bets**, not trend signal —
  size like a lottery or skip.
- **Hedge vs conviction:** big put buying in a name someone is long can be protection, not a bet.

## 3. Working Robinhood scans (saved on the agentic account)

Use `run_scan {scan_id}` to re-pull; `create_scan` / `update_scan_filters` to build. **Read the
tool JSON schema + `resources/Scanner_Filter_Specs.json` before editing** — the filter params are
picky. Hard-won param gotchas that make scans validate:

| Filter type | Required params that are easy to miss |
|---|---|
| `FILTER_TYPE_AVERAGE_VOLUME` | `interval="1d"`, `length=30` (else `candleCount` errors as 0) |
| `FILTER_TYPE_RELATIVE_OPTIONS_VOLUME` | `interval="1d"`, `length=30` (empty `candlePeriod` fails) |
| `FILTER_TYPE_TOTAL_CALL_VOLUME` / `..._PUT_VOLUME` | `interval="1d"`, `length=1` + `candleCount` |
| `FILTER_TYPE_PERCENT_CHANGE_FROM_CLOSE` | `plot="Close"`, `interval="1d"`, use `changeFromCloseAllDayRatio` (note capitalization) |

Saved scans (2026-07-07):
- **SSR-EQ Rotation Leaders** `cce44365-dc88-4aac-b082-c47452b7f81d` — mkt cap ≥$10B · avg vol ≥1M(30d) · price ≥$20 · RSI(14) 50–70 · fwd P/E ≤30. Rotation-leader universe for SSR-EQ.
- **SSR Whale Overnight** — high relative options volume + call skew, for short-term bullish flow.
- (Add a bearish/put-flow variant symmetrically.)

## 4. Trade workflow (agentic account)

1. **Session start:** read `agent_learning_log.md`; confirm account via `get_accounts` +
   `get_portfolio`; note cash + any open agentic positions.
2. **Regime:** pull the rotation read (`equity_strategy.md` §1) + MANGOS pulse. Which side is the tape on?
3. **Find candidates:** `run_scan` the relevant scan; for a named ticker, pull `get_option_quotes` /
   chains and compute **volume vs OI** on the busy strikes to confirm fresh flow.
4. **Direction check:** follow flow only if it agrees with the tape + rotation; otherwise fade or skip.
5. **Structure by level-2 cash rules:** shares (leaders) or single-leg long option (defined risk,
   near-the-money, enough time). **No spreads/shorts.**
6. **Entry = confirmed hold, not a falling limit.** Size to 1–2 names, keep a cash buffer.
7. **On fill:** immediately place the GTC target and set/log a stop. Scale the exit.
8. **Log** the outcome in `agent_learning_log.md` (same loop as the options book).

## 5. Hard rules (keep enforcing)

1. **No blind dip-limits into a slide** — confirm the reclaim first (§1).
2. **Trade with the rotation/flow**, not countertrend knives in flagged-bearish names.
3. **Pick the exit framework from the ACCOUNT'S PURPOSE, not the instrument** (the 2026-07-07 GOOGL
   miss). This $1k sleeve's job is **frequent small green closes + capital recycle** (the
   north-star goal) — so **default to the fast-recycle plan**: a small high-odds target
   (~+1.5–3%, which on a ~30%-vol large-cap fills ~45–75% within a week), take profit, re-enter on a
   pullback. Offer the swing "let winners run" (+8/+15%, trail) lens only when the user wants a
   position *hold*. **Don't promise a clean "N round trips" — that needs a saw-tooth tape; a trend
   gives one scalp then a rebuy-higher/cash choice.** RH equity is commission-free, so small recycles
   aren't fee-eaten.
3b. **The recycle loop is the constant; the levels are variables — RE-EVALUATE entry & exit every
   cycle** (user directive 2026-07-07). Don't hard-code a fixed buy/sell pair. Each cycle: (a) pull
   the **live quote + intraday range/VWAP**; (b) set the **sell target ~+1.2–1.8% but tucked just
   under the nearest resistance** (high-odds tag, not a stretch); (c) set the **rebuy off that
   session's pullback that holds** (VWAP / intraday support / prior-cycle low), never a stale number.
   **Halt the loop if the name closes below its stop** (thesis broke — don't recycle a downtrend);
   keep banking realized gains and track cumulative vs the weekly $ goal.
4. **Stops non-negotiable; scale winners** on a hold.
5. **Fresh flow = volume vs OI**, not raw volume; skip negative-EV lotto and binary M&A spikes.
6. **Respect the account:** cash + level-2 = long options + shares only; sell only after the buy fills.
7. **Small book:** 1–2 names on ~$1k; never all-in one overnight countertrend bet.
