# Multi-Strategy Backtest

_Generated 2026-07-07 18:17Z by `market_data/backtest_strategies.py` on the cached 2-year daily OHLCV (65 names). Spreads priced with Black-Scholes using trailing 20-day realized vol as sigma (no historical option chains exist). Weekly entries, 21-trading-day expiry, close-stop ON. v2 router adds a confirmation filter (price decisively beyond a sloping SMA50 + SMA20 agreement) and an event gate (no premium selling through a detected earnings/guidance gap)._

> **Read RoR-expectancy, not win rate.** A high win rate with a big avg loss still bleeds (the HOOD lesson). `exp` = avg return-on-risk per trade; `$/ $1k` = dollars per $1,000 risked per trade.

## A) Per-strategy (every structure, every name, every week)

| Strategy | N | Win% | Avg win | Avg loss | Exp (RoR) | $/ $1k |
|---|---|---|---|---|---|---|
| Put credit (bull/highIV) | 5602 | 62.2% | +26.1% | -32.8% | +3.87% | $+39 |
| Call debit (bull/lowIV) | 5602 | 39.3% | +142.3% | -64.8% | +16.52% | $+165 |
| Call credit (bear/highIV) | 5602 | 48.2% | +21.6% | -32.7% | -6.51% | $-65 |
| Put debit (bear/lowIV) | 5602 | 25.8% | +121.6% | -64.0% | -16.13% | $-161 |
| Iron condor (range/highIV) | 5602 | 51.5% | +22.5% | -30.3% | -3.11% | $-31 |
| Calendar (range/lowIV) | 5602 | 46.4% | +61.9% | -53.3% | +0.14% | $+1 |

## B) Routers vs baselines

| Approach | N | Win% | Avg win | Avg loss | Exp (RoR) | $/ $1k |
|---|---|---|---|---|---|---|
| v1 naive router (no gate) | 5602 | 46.0% | +68.3% | -49.9% | +4.44% | $+44 |
| **v2 router (confirm + event gate)** | 4056 | 49.3% | +66.6% | -48.3% | +8.32% | $+83 |
| put-credit-only | 5602 | 62.2% | +26.1% | -32.8% | +3.87% | $+39 |
| put-credit-only + event gate | 4639 | 64.3% | +25.5% | -30.5% | +5.47% | $+55 |

_v2 stood down on **1546** entries (no confirmed edge or an event in the window). v1 picks: call_debit=1405, put_credit=1108, call_credit=971, put_debit=768, calendar=753, iron_condor=597. v2 picks: call_debit=1159, iron_condor=875, put_credit=773, call_credit=643, put_debit=606._

## Method & caveats

- **Pricing:** Black-Scholes, realized vol as IV proxy. Real IV is usually richer than realized for sellers (vol-risk-[REDACTED]), so live credit-spread edge is typically **better** than shown here; debit spreads slightly worse. Treat as *relative* ranking, not absolute $.
- **Strikes:** % -based (cushion 8%, width 5%) so names aggregate; live trades use real strikes/liquidity.
- **Stops:** credit = close beyond short strike; debit = spread −50%. Held to expiry otherwise.
- **No earnings gate** in the sim (live book always applies it) — so real tail losses are smaller than backtest.
- **Calendar** is a single-vol approximation (same sigma both expiries); real calendars depend on term-structure, so treat that row as indicative.
