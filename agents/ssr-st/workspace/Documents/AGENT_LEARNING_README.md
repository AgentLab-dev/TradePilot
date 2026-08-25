# Agent Learning System — README

_How this trading agent learns and keeps getting better. The agent reads this + the
learning log at the start of every session._

## What this is

A closed feedback loop so the agent **never misses the same setup twice**, keeps its
strategy **backtest-validated**, and surfaces a steady cadence of **vetted** trades.
Driven by the `trading-continuous-learning` skill (`~/.cursor/skills/`).

## The files (and what each does)

| File | Purpose | Cadence |
|---|---|---|
| `agent_learning_log.md` | **The separate lessons file** — dated lessons (misses/wins/rules/backtests), month tally, tomorrow's first-check, earnings radar pointer. | Read first every session; **append after every notable event**. |
| `earnings_radar.md` | Names reporting in the next 1–2 weeks, tagged 🔴 sell-gate / 🟢 directional. | Regenerate daily. |
| `monthly_income_plan.md` | Operating system: cadence, sizing, exits, the direction×IV strategy matrix. | Update when a rule changes. |
| `options_watchlist.md` | Live play cards, armed trades, backtests. | Update intraday. |
| `backtest_multistrategy.md` | Strategy expectancy (RoR). | Regenerate when a gate/rule changes. |

## Scripts (`market_data/`)

| Script | Does |
|---|---|
| `fetch_history.py` | Cache ~2y daily OHLCV. |
| `fetch_earnings.py` | **Earnings radar** → `earnings_radar.md` (the MU-miss fix). |
| `backtest_strategies.py` | Multi-strategy backtest → `backtest_multistrategy.md`. |
| `health_check.py` / `whale_check.py` / `stkk_from_cache.py` | The four decision models. |

## The auto-learning loop

```
Session start ──► read agent_learning_log.md + earnings_radar.md
     │
     ├─ macro + breadth + manage open book
     ├─ EARNINGS GATE (fetch_earnings.py): tag reporters 🔴 sell-gate / 🟢 directional
     ├─ daily-idea routine: scan ► route by matrix ► gate ► confirm ► surface ≥1 idea (or stand-down)
     │
Notable event (miss / win / rule / backtest)
     └─► append a dated lesson to agent_learning_log.md
              └─► if it changes a gate/rule ► re-run backtest ► promote only if RoR improves
```

## How to add a learning (the only format)

Append to `agent_learning_log.md`, newest first:

```markdown
### YYYY-MM-DD — <title>  [MISS | WIN | RULE | BACKTEST]
- **What happened:** ...
- **Root cause:** ...
- **Rule / fix:** ...
- **Status:** pending build | adopted | validated
```

## Triggers that REQUIRE a new lesson

- A move the agent should have flagged but didn't (e.g., a missed earnings run → MU).
- A user **hint** about a ticker that wasn't fully chased.
- Any change to gates, sizing, or the strategy matrix.

## Standing rules (enforced every session)

1. Earnings/event gate is the #1 edge — never sell premium through earnings/CPI/PCE/FOMC.
2. A user hint about a ticker = run a full Health Check **including the earnings calendar**.
3. Don't chase a post-earnings gap — high IV → sell a put spread on a hold, don't buy calls.
4. One max loss erases ~3–6 wins — size for the tail; stops are non-negotiable.
5. Bullish core (put-credit + call-debit); bearish only on a confirmed breakdown.
6. Quality > quota — a logged stand-down counts; never force a trade into a bad tape.
