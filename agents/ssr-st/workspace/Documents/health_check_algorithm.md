# Health Check — full 4-model composite

_Last updated: June 19, 2026_

**One call that runs all four trading models on a ticker and returns 4 flags + a single VERDICT.**
Use it as the pre-trade "is this whole-body healthy?" scan before committing capital — instead of running STKK, STNOW, Three Good, and Whale Check separately and eyeballing them.

```
python3 market_data/health_check.py MARA HOOD ORCL SNOW MNDY
python3 market_data/health_check.py AVGO --to 2026-09-30
python3 market_data/health_check.py HOOD --live HOOD=109.4
```

---

## The four lenses it combines

| # | Model | Source | What it answers |
|---|---|---|---|
| 1 | **STKK** | cache (`market_history.md`) | Is the *chart* healthy? Regime (UP/RANGE/DOWN), RSI, R:R, entry/stop/target |
| 2 | **STNOW** | cache + whale | Is the *thesis* healthy? Trend + analyst upside + flow, with the **value-trap gate** |
| 3 | **Three Good** | whale IV | Is it a valid *put-credit-spread* candidate? (IV ≥ 50% & flow ≥ 0 & not breaking down) |
| 4 | **Whale Check** | live Nasdaq chain | Is *institutional flow* healthy? P/C vol, ATM IV, expected move, skew |

STKK + analyst targets come from the local cache. Whale Check hits the live Nasdaq option chain. Re-pull the cache (`fetch_history.py`) if the last bar is older than the prior trading day.

---

## How each flag is computed

### 1. STKK flag
- 🟢 **UP trend, room** — regime UP and R:R ≥ 1.5
- 🟡 **UP, thin R:R** — regime UP but R:R < 1.5 (limited upside to chart target → prefer a spread)
- 🟡 **DOWN, oversold** — regime DOWN but RSI < 35 (mean-reversion candidate)
- 🔴 **DOWN trend** — regime DOWN, RSI ≥ 35 (falling, no bounce signal)
- 🟡 **RANGE / RANGE, extended** — chop; "extended" if price > 15% above entry

### 2. STNOW (quant proxy, `raw = T + A + W`)
- **T (trend):** UP +2 · RANGE 0 · DOWN −2 · plus RSI < 35 → +1, RSI > 70 → −1
- **A (analyst):** upside to mean > 25% → +2 · 10–25% → +1 · 0–10% → 0 · above mean → −1 (**capped at +2** so deep-discount value traps can't inflate the score)
- **W (whale):** the Whale Check score (−2…+2)
- **Step 0.5 — value-trap gate 🔴TRAP:** trips when regime = DOWN **and** upside-to-mean > 40% **and** price < 200-day SMA. A deep discount on a falling stock is treated as guilty-until-proven: verdict forced to **WAIT** until a live news/catalyst check explains *why* it's cheap. (This is the gate we added after the ZS / VEEV / MNDY false-GOs.)

> STNOW's **News (N) lens is not automated.** The proxy covers trend, valuation, and flow; you must still confirm the live catalyst/news before entry. The gate exists specifically to stop "cheap = buy" mistakes.

### 3. Three Good flag
- ✅ **valid** — ATM IV ≥ 50% **and** whale score ≥ 0 **and** regime ≠ DOWN
- ⚠️ **IV ok, sell at support** — IV ≥ 50% & flow ≥ 0 but regime DOWN (only sell puts after it bases)
- ❌ **no** — IV < 50% (too thin to sell premium) or flow bearish
- ⚪ **IV n/a** — no chain / IV could not be computed

### 4. Whale flag
Passed straight through from Whale Check: 🟢 BULLISH (+2) / 🟢 lean-bull (+1) / 🟡 NEUTRAL (0) / 🔴 lean-bear (−1) / 🔴 BEARISH (−2). See `whale_check_algorithm.md`.

---

## Verdict logic (precedence order)

1. **🔴 WAIT — value-trap gate** — if Step 0.5 trips (overrides everything; flow can't save it)
2. **🔴 AVOID/WAIT** — whale score < 0 or STNOW raw < 0 (flow or thesis against you)
3. **🟢 GO on pullback** — price > 15% above entry or RSI > 68 (right name, wrong price — don't chase)
4. **🟢 GO — limited chart upside** — UP trend but R:R < 0.5 (monetize via spread, not shares)
5. **🟢 STRONG GO** — STNOW raw ≥ 5 and whale ≥ +1
6. **🟢 GO-on-confirmation** — STNOW raw ≥ 2 (wait for the chart trigger / level reclaim)
7. **🟡 NEUTRAL** — everything else; wait for a trigger

### IV-aware structure (appended to every GO verdict)
The verdict names the *right options structure* based on ATM IV, so you never sell cheap premium or buy expensive premium:

- **IV ≥ 50% → "sell put spread (rich IV)"** — get paid for the elevated premium.
- **IV < 50% → "call debit spread (low IV → buy, don't sell)"** — premium is cheap, so buy the move instead of selling it.
- **IV n/a → "shares"** — no usable options.

> This fixes the original bug where a low-IV name (e.g., GOOGL at IV 34%) was told to "sell a put spread" — wrong, because put-selling pays too little when IV is low. Low IV ⇒ buy (call debit spread); high IV ⇒ sell (put spread).

---

## Output format — 7 columns

The model prints one row per ticker with exactly these columns, then a CONTEXT block with the numbers behind the flags:

`Name · Price · STKK (chart) · STNOW (360°) · Three Good (put-sell) · Whale Check · VERDICT`

## Worked example — shortlist run (6/18 close)

| Name | Price | STKK (chart) | STNOW (360°) | Three Good (put-sell) | Whale Check | VERDICT |
|---|---|---|---|---|---|---|
| MARA | 14.22 | 🟡 UP, thin R:R | 🟢 STRONG raw+5 | ✅ IV 85% | 🟢 BULLISH | 🟢 GO — via put spread (chart target only +7%) |
| HOOD | 108.15 | 🟡 RANGE, extended | 🟡 raw+1 | ✅ IV 68% | 🟢 BULLISH | 🟢 GO on pullback (+24% extended) |
| ORCL | 184.29 | 🟡 DOWN, oversold | 🟢 GO raw+3 | ⚠️ at support | 🟢 BULLISH | 🟢 GO-on-confirmation (best clean long) |
| SNOW | 232.29 | 🟡 RANGE | 🟢 GO raw+4 | ✅ IV 55% | 🟢 BULLISH | 🟢 GO-on-confirmation (poor long R:R → spread) |
| MNDY | 71.53 | 🟡 DOWN, oversold | 🔴 TRAP raw+3 | ⚠️ at support | 🟢 BULLISH | 🔴 WAIT — value-trap gate (74% "upside", falling) |

MNDY is the teaching case: whale flow is +2 bullish and the raw score is +3, but the value-trap gate vetoes it because it's down hard with an implausibly large "upside to mean" and no confirmed reason — exactly the ZS/VEEV pattern.

---

## Limitations / honesty notes

- **News lens is manual.** The model cannot read live news; the value-trap gate is a guard, not a substitute for checking *why* a name moved.
- **Prices are cache (EOD).** STKK uses the cached last close unless you pass `--live SYM=PX`. Whale flow uses the prior completed session's volume (OI is T+1). Re-run at the open for fresh marks.
- **Analyst means can go stale** (e.g., HOOD ran past its $100 mean → the A-lens understates it). Refresh `ANALYST` in `stkk_from_cache.py` periodically.
- **STNOW here is a proxy**, not the full 7-lens write-up. For high-conviction sizing, still run the full STNOW skill on the finalists.

---

## Relationship to the other models

Health Check does not replace the individual models — it **orchestrates** them:
- `stkk_from_cache.py` → chart
- `whale_check.py` → flow + IV
- STNOW proxy (inline) + value-trap gate → thesis
- Three Good eligibility (inline) → premium-selling structure

Run Health Check first to triage a list; then run the full STNOW skill + build option cards on the names that pass.
