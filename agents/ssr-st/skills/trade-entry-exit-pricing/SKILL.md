---
name: trade-entry-exit-pricing
description: >-
  Determine concrete entry and exit prices for stock and options trades using
  four named algorithms — Stock Entry Price, Stock Exit Price (Risk/Stop Price),
  Options Entry Price, and Options Exit Price. INVOKE ONLY when the user
  explicitly types the trigger code "TASP" or "STKK". Do NOT auto-apply from
  ambient trading conversation. When triggered, pulls price history, computes
  support/resistance, moving averages, Fibonacci, ATR, RSI, beta and
  risk/reward, then outputs specific price levels.
disable-model-invocation: true
---

> **Activation:** This skill is OFF by default. Apply it only when the user types
> **`TASP`** or **`STKK`** in their message. Otherwise ignore it.

# Trade Entry & Exit Pricing

Four algorithms that turn price history into concrete buy/sell levels. Always
produce **numbers** (price levels), never vague advice. Every trade must clear
the **Risk/Reward gate** before it is valid.

## Data inputs (pull these first)

> **CACHE-FIRST RULE (do this before any network pull):** Daily history for the
> whole watchlist is cached at
> `/Users/koteswararao.venkata/Documents/Cursor/ssr-analyst/Documents/market_history.md`
> (one `## TICKER` section each, with a ```csv``` block of `date,open,high,low,close,volume`).
> 1. **Read history from that file** — do NOT re-pull Yahoo/Nasdaq for history if the
>    ticker is present and its last bar is today or the prior trading day.
> 2. **Compute levels with the bundled script** (no network, sub-second):
>    `python3 "/Users/koteswararao.venkata/Documents/Cursor/ssr-analyst/Documents/market_data/stkk_from_cache.py" HOOD NNE NTAP ...`
>    (or `--all`). It prints regime/SMA/RSI/ATR/beta/entry/stop/target/R:R ranked by R:R.
> 3. **Only re-pull when stale or missing:** run
>    `python3 ".../market_data/fetch_history.py" [SYMS]` (Nasdaq API via curl; writes
>    straight to disk so the bulk data never enters context). `fetch_history.py` with
>    no args refreshes the full universe; pass symbols to refresh just those.
> 4. **Known cache gaps:** `PSTG` (NYSE — not on Nasdaq's API) and freshly-IPO'd names
>    like `SPCX` (no history yet) — fetch those from Yahoo/RH when needed.

- **Live quote (current price only):** Robinhood MCP `get_equity_quotes` (authenticated,
  not rate-limited) — pass the handful of tickers you care about, then feed the prints
  into the script via `--live SYM=PRICE` to recompute `%abv` against the live print.
  Yahoo `chart/{SYM}?interval=1m&range=1d → meta.regularMarketPrice` is a backup but is
  IP-rate-limited (429) under bursts. Neither has an options chain — read the app for premiums.
- **History (only if cache miss):** Nasdaq API
  `https://api.nasdaq.com/api/quote/{SYM}/historical?assetclass={stocks|etf}&fromdate=&todate=&limit=9999`
  via `curl` (Python urllib fails SSL verify in this sandbox — shell out to curl).
- Compute from history: swing highs/lows, 20/50/200-day SMA, ATR(14),
  RSI(14), Fibonacci levels of the last major swing.

## Global gates (apply to all four)

1. **Macro gate** — no long entry into a binary event (CPI, earnings, Fed).
   Wait for the event or trade after it.
2. **No falling knives** — require a confirmation candle (green daily close
   holding support), not the first touch.
3. **Risk/Reward gate** — only take the trade if `R:R ≥ 2:1`:
   `R:R = (Target − Entry) / (Entry − Stop)`.

## Regime filter (run BEFORE picking an entry style)

Classify the stock first; it changes which entry rule to use and how big to size.

```
trend  = uptrend  if price>SMA50 and SMA50>SMA200
         downtrend if price<SMA50 and SMA50<SMA200
         else range/transition
vol    = σ_ann (annualized). high if >50%.   beta from regression vs SPY.
SIZE SCALER: if σ_ann>50% OR beta>2  → "size small" (½ normal risk budget).
```

- **Uptrend → use the PULLBACK-BUY branch** (Algo 1B). Do NOT wait for a full
  SMA20 reclaim — in strong trends price rides above it and you miss the move.
- **Downtrend → use the REVERSAL/RECLAIM branch** (Algo 1A) only; default to cash.
- **Range → fade Bollinger/z-score extremes.**

> Backtest lesson (INTC, 10 wks): a reclaim-only rule caught the first +22% leg
> then sat out a $58→$132 run because price never dropped back under SMA20. Trends
> need pullback-buys + re-entries, not a single reclaim. Hence the branch below.

## Quant & economics toolkit

Full PhD-level formula set (vol, Sharpe, beta/CAPM, ATR, RSI, z-score, Kelly,
Black–Scholes/Greeks, expected move, PV/CPI link) lives in
[reference-quant-formulas.md](reference-quant-formulas.md). Pull `range=2y` daily
data so SMA200 / beta / backtests have enough history.

---

## Algorithm 1 — Stock Entry Price

**Goal:** the price (or zone) to BUY shares.

```
INPUT:  daily OHLC, current price, regime (from filter above)
COMMON: BUILD support candidates, then CONFLUENCE-cluster (within ~2%):
       a. recent swing lows (last 10–20 weeks)
       b. 20 / 50 / 200-day SMA + EMA20
       c. Fibonacci retracement of last major swing (38.2 / 50 / 61.8 %)
       d. round numbers
       e. high-volume price shelf  + Bollinger lower band
     strongest support = zone with the MOST overlapping candidates.

BRANCH 1A — REVERSAL/RECLAIM (downtrend or range):
  CONFIRM: daily close reclaims confluence zone from below AND RSI turns up
  from <35 AND macro gate clear.  entry_price = zone_high on that close.

BRANCH 1B — PULLBACK-BUY (uptrend — the trend-continuation case):
  CONFIRM: price pulls back INTO rising EMA20/SMA20 or a Fib (38.2/50%) AND
  RSI dips toward 40 then turns UP AND a green reversal candle prints.
  entry_price = the reversal-candle close (you buy strength off support, and
  you may RE-ENTER on each clean pullback while the uptrend holds).
OUTPUT:
  entry_zone = [support_low, support_high];  entry_price per branch;
  state which branch + confluence reasons + the confirmation trigger.
```

---

## Algorithm 2 — Stock Exit Price (Risk / Stop Price)

**Goal:** where to GET OUT — both the protective STOP (risk) and the TARGET.

```
INPUT:  entry_price, entry_zone, daily OHLC, ATR(14), account risk budget
STOP (risk) — primary:
  1. structure_stop = just below entry_zone_low (last swing low)
  2. atr_stop       = entry_price − (k × ATR), k = 1.5 (low vol) to 2.5 (high vol)
  3. stop_price     = the LOWER of the two (gives the trade room),
                      but verify loss is within risk budget.
  4. position_size  = (account × risk%) / (entry_price − stop_price)   [shares]
     → apply the regime SIZE SCALER (½ for high-vol / high-beta names).
     → optional half-Kelly cap: f* = (p·b − q)/b, use f*/2 of account.
TARGET — profit exit:
  1. resistance candidates: prior swing highs / supply zones above
  2. fib_extension = entry swing × 1.272 and × 1.618
  3. measured_move = pattern height projected from breakout
  4. SANITY: distance (target − entry) should be ≤ ~2× the weekly expected move
     (EM = S·σ_ann·√(t/252)); if target needs more, extend timeframe or trim it.
  5. target_price  = nearest strong resistance giving R:R ≥ 2:1
  6. SCALE (optional): T1 = first resistance (take 50%), T2 = extension,
     then trail stop to breakeven after T1.
OUTPUT:
  stop_price, target_price (T1/T2), position_size, R:R, expected-move check
RULE: if price closes below stop_price → EXIT, no exceptions (the thesis is dead).
```

---

## Algorithm 3 — Options Entry Price

**Goal:** which option (expiry + strike) and what PREMIUM to pay.

```
INPUT:  stock plan from Algos 1–2 (direction, entry, target, stop, timeframe),
        implied volatility (IV) regime, days to catalyst
STEPS:
  1. EXPIRY: expiry ≥ 1.5–2× expected time-to-target (avoid theta squeeze).
     Choose past a catalyst to dodge IV crush, or before it to ride the move.
  2. STRUCTURE by IV:
       IV low      → debit (long call/put) for clean leverage
       IV high     → DEBIT SPREAD (cuts vega / IV-crush risk)
       (avoid naked long premium into elevated pre-event IV)
  3. STRIKE:
       directional long → ATM/slightly-ITM (delta 0.60–0.70) = responsive,
                          less theta; OTM only for cheap high-risk leverage
       debit spread     → long strike near stock entry; SHORT strike at the
                          stock TARGET (caps gain where you'd exit anyway = cheaper)
  4. PREMIUM (the entry price you pay):
       limit_premium = bid/ask MIDPOINT  (never market order)
       breakeven      = long_strike + limit_premium   (calls)
       VALIDATE: breakeven < target with margin; expected move ≥ (target − entry)
  5. TRIGGER: enter the option only when the STOCK confirms (Algo 1 trigger).
OUTPUT:
  expiry, strike(s), limit_premium (mid), breakeven
```

---

## Algorithm 4 — Options Exit Price

**Goal:** where to CLOSE the option — profit target, stop, and time-stop.

```
INPUT:  option position, entry_premium, underlying stop/target (Algos 1–2)
PROFIT exit (use the FIRST that triggers):
  1. underlying-based: when stock hits target_price → close
  2. premium-based:    long options → +50–100% of entry_premium
                       credit spreads → buy back at 50% of max profit
  3. SCALE: take half at +50%, let rest run to underlying target
STOP exit (risk):
  1. underlying-based (primary): stock closes below stop_price → close option
  2. premium-based: long option down −50% of entry_premium → close
TIME stop:
  - close/roll before expiry WEEK (theta + gamma accelerate; pin risk)
  - if thesis hasn't moved by ~50% of time-to-expiry → exit, capital is dead
OUTPUT:
  profit_exit (underlying trigger OR premium target),
  stop_exit (underlying break OR premium loss), time_stop date
```

---

## Worked example (format to mirror)

For **INTC**, entry $98.5, support $95–98, target $115 (prior resistance), stop $95:

- **Algo 1:** entry zone $95–98.5 (swing-low + round-number confluence); trigger =
  green daily close > $98 with RSI turning up, after CPI.
- **Algo 2:** stop $95 (below swing low); target $115 (May resistance);
  **R:R = (115 − 98.5) / (98.5 − 95) = 4.7:1** ✅.
- **Algo 3:** if IV elevated pre-CPI → **$100/$115 call debit spread**, July expiry,
  pay the mid; breakeven = long strike + debit.
- **Algo 4:** profit = stock $115 OR +75% on the spread; stop = stock closes < $95;
  time-stop = close before July expiry week.

## Output checklist

- [ ] Pulled live quote + daily/weekly history
- [ ] Listed support/resistance with confluence reasons
- [ ] Gave numeric entry zone, stop, and target(s)
- [ ] Computed R:R and confirmed ≥ 2:1
- [ ] For options: expiry, strike(s), mid premium, breakeven
- [ ] Stated the confirmation trigger and macro gate
