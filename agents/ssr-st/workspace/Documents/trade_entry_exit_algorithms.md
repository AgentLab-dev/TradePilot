# Trade Entry & Exit Pricing — The 4 Algorithms

_Trigger codes: **TASP** or **STKK** (skill is off unless you type one of these)._
_Companion skill: `~/.cursor/skills/trade-entry-exit-pricing/`_

> Always output **numbers** (price levels), never vague advice. Every trade must
> clear the **Risk/Reward gate (≥ 2:1)** before it is valid.

---

## Global gates (apply to all four)

1. **Macro gate** — no long entry into a binary event (CPI, earnings, Fed).
2. **No falling knives** — require a confirmation candle, not the first touch.
3. **Risk/Reward gate** — `R:R = (Target − Entry) / (Entry − Stop) ≥ 2:1`.
4. **Whale-flow overlay** — run `Whale Check` (`market_data/whale_check.py`); options flow should **agree** with the chart's direction. Bullish chart + 🟢 bullish whale = high-conviction entry; bullish chart + 🔴 bearish whale (near-money put buying) = **wait for flow to turn**. OI walls also mark magnet support/resistance — fold them into the confluence in Algo 1/2.

## Regime filter (run FIRST)

```
trend = uptrend  if price>SMA50 and SMA50>SMA200
        downtrend if price<SMA50 and SMA50<SMA200
        else range
vol   = σ_ann (annualized);  beta = regression vs SPY
SIZE SCALER: if σ_ann>50% OR beta>2 → half risk budget ("size small")
→ uptrend uses Algo 1B (pullback-buy); downtrend uses Algo 1A (reclaim); range = fade extremes
```

---

## Algorithm 1 — Stock Entry Price

```
COMMON: build support candidates, cluster into confluence (within ~2%):
  swing lows · SMA20/50/200 + EMA20 · Fib 38.2/50/61.8% · round numbers
  · volume shelf · Bollinger lower band
  strongest support = most overlapping candidates

BRANCH 1A — REVERSAL/RECLAIM (downtrend/range):
  CONFIRM: close reclaims confluence zone from below AND RSI turns up from <35
           AND macro gate clear.   entry_price = zone_high on that close.

BRANCH 1B — PULLBACK-BUY (uptrend — trend continuation):
  CONFIRM: price pulls back into rising EMA20/SMA20 or Fib (38.2/50%) AND RSI
           dips toward 40 then turns UP AND a green reversal candle prints.
           entry_price = reversal-candle close. RE-ENTER on each clean pullback
           while the uptrend holds.
OUTPUT: entry_zone, entry_price, branch used, confluence reasons, trigger
```

## Algorithm 2 — Stock Exit Price (Risk / Stop Price)

```
STOP (risk) — primary:
  structure_stop = just below entry_zone_low (last swing low)
  atr_stop       = entry − (k × ATR), k = 1.5 (low vol) → 2.5 (high vol)
  stop_price     = LOWER of the two; verify loss ≤ risk budget
  position_size  = (account × risk%) / (entry − stop)   [shares]
                   × regime size scaler;  optional half-Kelly cap
TARGET — profit exit:
  resistance (prior swing highs) · Fib ext ×1.272/×1.618 · measured move
  SANITY: (target − entry) ≤ ~2× weekly expected move  (EM = S·σ_ann·√(t/252))
  target_price = nearest strong resistance giving R:R ≥ 2:1
  SCALE: T1 = first resistance (take 50%), T2 = extension, trail to breakeven
OUTPUT: stop_price, target(s), position_size, R:R
RULE: close below stop_price → EXIT, no exceptions.
```

## Algorithm 3 — Options Entry Price

```
INPUT: stock plan (dir, entry, target, stop, timeframe), IV regime, days-to-catalyst
  1. EXPIRY ≥ 1.5–2× expected time-to-target (avoid theta squeeze); past a
     catalyst to dodge IV crush, or before it to ride the move.
  2. STRUCTURE by IV:  low IV → debit (long call/put);  high IV → DEBIT SPREAD
     (cuts vega/IV-crush);  avoid naked long premium into elevated pre-event IV.
  3. STRIKE: directional long → ATM/slightly-ITM (delta 0.60–0.70); OTM = cheap
     high-risk leverage. Debit spread → long near entry, SHORT at stock TARGET.
  4. PREMIUM: limit = bid/ask MIDPOINT (never market).  breakeven = strike + prem.
     VALIDATE: breakeven < target; expected move ≥ (target − entry).
  5. TRIGGER: enter option only when the STOCK confirms (Algo 1).
OUTPUT: expiry, strike(s), limit premium (mid), breakeven
```

## Algorithm 4 — Options Exit Price

```
PROFIT exit (first to trigger):
  underlying: stock hits target → close
  premium:    long → +50–100% of entry premium;  credit spread → buy back at
              50% of max profit
  SCALE: take half at +50%, let rest run to underlying target
STOP exit (risk):
  underlying (primary): stock closes below stop_price → close option
  premium: long option −50% of entry premium → close
TIME stop:
  close/roll before expiry WEEK (theta + gamma + pin risk)
  if no move by ~50% of time-to-expiry → exit, capital is dead
OUTPUT: profit_exit, stop_exit, time_stop date
```

---

## Worked example — INTC

Entry $98.5, support $95–98 (= 38.2% Fib $94), target $115 (May resistance), stop $95:

- **Algo 1:** entry zone $95–98.5; trigger = green close > $98, RSI turning up, after CPI.
- **Algo 2:** stop $95, target $115 → **R:R = (115−98.5)/(98.5−95) = 4.7:1** ✅.
  INTC ann-vol 71% / beta 2.46 → **size small**. Weekly expected move ±$9.92.
- **Algo 3:** IV elevated pre-CPI → **$100/$115 call debit spread**, July, pay mid.
- **Algo 4:** profit = stock $115 OR +75% on spread; stop = stock closes < $95;
  time-stop = close before July expiry week.

## Output checklist

- [ ] Pulled live quote + daily/weekly history (range=2y)
- [ ] Ran regime filter (trend / vol / beta / size scaler)
- [ ] Listed support/resistance confluence with reasons
- [ ] Numeric entry zone, stop, target(s)
- [ ] R:R computed and ≥ 2:1
- [ ] Options: expiry, strike(s), mid premium, breakeven
- [ ] Stated confirmation trigger + macro gate
