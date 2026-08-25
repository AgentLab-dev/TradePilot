---
name: health-check
description: "Health Check — the full 4-model composite. Runs STKK (chart), STNOW (360° thesis + value-trap gate), Three Good (put-spread eligibility), and Whale Check (live options flow + IV) on each ticker and returns 4 flags + ONE verdict per name. Invoke ONLY when the user types the trigger 'Health Check'. Do not auto-apply."
disable-model-invocation: true
---

> **Activation:** OFF by default. Run ONLY when the user types **`Health Check`** (optionally with tickers, e.g. `Health Check MARA HOOD ORCL`). Otherwise ignore.

# Health Check — full 4-model composite

One scan that fuses all four models into 4 flags + a single VERDICT per ticker, so you can triage a list before committing capital. Full spec: `Documents/health_check_algorithm.md`.

## How to run

The model is implemented as a script that orchestrates the other three. From the `ssr-analyst` workspace (Robinhood MCP + cache live there):

```
cd Documents/market_data
python3 health_check.py TICKER [TICKER ...] [--to YYYY-MM-DD] [--live SYM=PX]
```

- **STKK + analyst** come from the cache (`market_history.md`). If the last bar is older than the prior trading day, re-pull first: `python3 fetch_history.py`.
- **Whale Check** hits the live Nasdaq option chain (needs network).
- Pass `--live SYM=PX` to override the cached close with a live quote (from `get_equity_quotes`).

## What it returns

For each ticker: **STKK** flag (chart), **STNOW** raw score `T/A/W` + value-trap gate, **Three Good** flag (IV/flow eligibility), **Whale** flag — then a single **VERDICT**:

- 🔴 **WAIT — value-trap gate** (Step 0.5 tripped: DOWN + >40% "upside" + below 200DMA → flow can't override; needs live news)
- 🔴 **AVOID/WAIT** (flow or thesis against)
- 🟢 **GO on pullback** (right name, extended price — don't chase)
- 🟢 **GO — via put spread** (UP trend, thin chart R:R → monetize IV instead of buying shares)
- 🟢 **STRONG GO** / 🟢 **GO-on-confirmation**
- 🟡 **NEUTRAL** (wait for trigger)

## Rules / honesty

1. **News (N) lens is NOT automated.** The value-trap gate is a guard, not a news read — always confirm the live catalyst before entry, especially on any 🔴TRAP name.
2. **Marks are EOD cache** unless `--live` is passed; whale volume is prior session, OI is T+1. Re-run at the open for fresh marks before acting.
3. **Analyst means go stale** (a name can run past its mean → A-lens understates it). Refresh `ANALYST` in `stkk_from_cache.py` if a target looks wrong.
4. Health Check is a **triage** step. On the finalists, still run the full `STNOW` skill and build option cards before sizing.
5. Report the verdict with numbers (price, % to mean, IV, expected move, RSI, regime) — never a bare flag.
