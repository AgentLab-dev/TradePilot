# Multi-Strategy Backtest

_Generated 2026-09-18 00:16Z by `market_data/backtest_strategies.py` on the cached 2-year daily OHLCV (5 names). Spreads priced with Black-Scholes using trailing 20-day realized vol as sigma (no historical option chains exist). Weekly entries, 21-trading-day expiry, close-stop ON. v2 router adds a confirmation filter (price decisively beyond a sloping SMA50 + SMA20 agreement) and an event gate (no premium selling through a detected earnings/guidance gap)._

> **Read RoR-expectancy, not win rate.** A high win rate with a big avg loss still bleeds (the HOOD lesson). `exp` = avg return-on-risk per trade; `$/ $1k` = dollars per $1,000 risked per trade.

## A) Per-strategy (every structure, every name, every week)

| Strategy | N | Win% | Avg win | Avg loss | Exp (RoR) | $/ $1k |
|---|---|---|---|---|---|---|
| Put credit (bull/highIV) | 439 | 55.6% | +34.7% | -32.9% | +4.68% | $+47 |
| Call debit (bull/lowIV) | 439 | 44.4% | +137.1% | -65.7% | +24.39% | $+244 |
| Call credit (bear/highIV) | 439 | 40.3% | +31.2% | -32.1% | -6.59% | $-66 |
| Put debit (bear/lowIV) | 439 | 27.6% | +111.8% | -63.1% | -14.88% | $-149 |
| Iron condor (range/highIV) | 439 | 49.0% | +24.1% | -27.8% | -2.38% | $-24 |
| Calendar (range/lowIV) | 439 | 44.4% | +66.2% | -56.2% | -1.80% | $-18 |

## B) Routers vs baselines

| Approach | N | Win% | Avg win | Avg loss | Exp (RoR) | $/ $1k |
|---|---|---|---|---|---|---|
| v1 naive router (no gate) | 439 | 49.2% | +77.2% | -46.3% | +14.48% | $+145 |
| **v2 router (confirm + event gate)** | 320 | 53.8% | +75.3% | -44.6% | +19.83% | $+198 |
| put-credit-only | 439 | 55.6% | +34.7% | -32.9% | +4.68% | $+47 |
| put-credit-only + event gate | 348 | 56.9% | +35.9% | -30.7% | +7.22% | $+72 |

_v2 stood down on **119** entries (no confirmed edge or an event in the window). v1 picks: call_debit=114, put_credit=111, call_credit=69, calendar=59, put_debit=50, iron_condor=36. v2 picks: call_debit=99, put_credit=72, iron_condor=65, call_credit=46, put_debit=38._

## Method & caveats

- **Pricing:** Black-Scholes, realized vol as IV proxy. Real IV is usually richer than realized for sellers (vol-risk-[REDACTED]), so live credit-spread edge is typically **better** than shown here; debit spreads slightly worse. Treat as *relative* ranking, not absolute $.
- **Strikes:** % -based (cushion 8%, width 5%) so names aggregate; live trades use real strikes/liquidity.
- **Stops:** credit = close beyond short strike; debit = spread −50%. Held to expiry otherwise.
- **No earnings gate** in the sim (live book always applies it) — so real tail losses are smaller than backtest.
- **Calendar** is a single-vol approximation (same sigma both expiries); real calendars depend on term-structure, so treat that row as indicative.
