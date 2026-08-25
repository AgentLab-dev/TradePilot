---
name: tomorrow-market-predictor
description: "Tomorrow — predicts the next trading session's market direction by fusing 7 signal blocks (today's tape & breadth, after-hours/futures, cross-asset, news & government/admin decisions from WSJ/MW/wires, tomorrow's calendar, global/overnight, positioning/seasonality) into a probabilistic UP/FLAT/DOWN call with an expected range, key levels, swing factors, and a logged track record. Invoke ONLY when the user types 'Tomorrow'. Do not auto-apply."
disable-model-invocation: true
---

> **Activation:** OFF by default. Run ONLY when the user types **`Tomorrow`**. Otherwise ignore.

# Tomorrow — Next-Session Market Direction Predictor

Fuses **7 signal blocks** into a **probabilistic next-day call** for the broad market
(SPY / QQQ / Dow), with an expected range, key levels, the swing factors that flip it, and a
**logged prediction** for calibration. Companion algos: `STKK` (levels), `STNOW` (single-name),
`Three Good` (spreads). Always output **numbers + probabilities**, never a vibe.

> Honest framing: next-day moves are ~55–60% predictable at best. The edge is **process +
> calibration**, not certainty. Every call is logged and scored so the model improves.

## The 7 signal blocks (score each −2 … +2; + = risk-[REDACTED]/up, − = risk-[REDACTED]/down)

```
1. TODAY (tape & breadth) : close vs open, % move, breadth (adv/dec), sector leaders,
                            volume, posture vs SMA20/50/200, intraday reversal pattern.
2. AFTER-HOURS / FUTURES  : ES/NQ overnight drift; AH earnings/guidance; AH news shocks.
3. CROSS-ASSET            : oil (USO/WTI), 10Y yield (TNX/IEF), VIX, dollar (DXY/UUP),
                            BTC, gold (GLD) — the risk-[REDACTED]/off tell that leads equities.
4. NEWS & GOVERNMENT      : WSJ/MW/wire headlines; admin/govt decisions (tariffs/USTR,
                            war/geopolitics, Fed speak, regulation, executive actions).
5. CALENDAR (tomorrow)    : scheduled data (CPI/PPI/jobs/retail), Fed events, big earnings.
                            ⇒ sets the EVENT-VETO flag (binary day = widen bands, cut confidence).
6. GLOBAL / OVERNIGHT     : Asia (Nikkei/HSI) + Europe (DAX/FTSE) direction; overnight gap.
7. POSITIONING/SEASONALITY: pre-FOMC drift, OpEx/triple-witching, day-of-week, month/
                            quarter-end rebalance, holiday-shortened weeks, sentiment extremes.
```

### Scoring rubric (apply to each block)

| Score | Meaning |
|---|---|
| **+2** | strong risk-[REDACTED] signal (e.g. broad green close on volume, falling VIX, soft oil, supportive govt headline) |
| **+1** | mild risk-[REDACTED] |
| **0** | neutral / mixed / no signal |
| **−1** | mild risk-[REDACTED] |
| **−2** | strong risk-[REDACTED] (e.g. breadth collapse, VIX spike, oil shock, hawkish Fed leak, war headline) |

### Composite → next-day lean (sum, −14 … +14)

| Score | Lean | Prob split (U / F / D) |
|---|---|---|
| **≥ +6** | 🟢 UP (strong) | ~60 / 25 / 15 |
| **+2 … +5** | 🟢 UP (lean) | ~50 / 30 / 20 |
| **−1 … +1** | ⚪ FLAT / coin-flip | ~38 / 34 / 28 |
| **−5 … −2** | 🔴 DOWN (lean) | ~20 / 30 / 50 |
| **≤ −6** | 🔴 DOWN (strong) | ~15 / 25 / 60 |

### 🚦 EVENT VETO (from block 5)
If a **binary event** (CPI, PPI, jobs, FOMC, major Fed speech, scheduled tariff/war decision)
lands in the next session: **cap confidence at LOW, widen the range band ×1.5, and do NOT make
a strong directional call** — the move is event-driven and bimodal. Name the event + time.

## Magnitude model (expected range)

- **VIX-implied 1σ daily move** = `VIX / √252 ≈ VIX / 15.9` (%). e.g. VIX 18 → ~1.13%.
- Expected SPY range = `close × (1 ± 1σ)`; widen ×1.5 on event-veto days.
- If VIX unavailable, use SPY ATR(14)% as the daily band.

## Data sources (pull these)

1. **Today's close + indices:** Robinhood MCP `get_equity_quotes` (SPY, QQQ, DIA) +
   `get_index_quotes` (e.g. ^SPX, ^NDX, ^VIX if available). Breadth/leaders from `WebSearch`.
2. **After-hours / futures:** SPY/QQQ `last_non_reg_trade_price` (RH) as overnight proxy;
   `WebSearch` for "stock futures tonight" (ES/NQ) + AH earnings movers.
3. **Cross-asset (ETF proxies via RH quotes):** USO (oil), TNX/IEF (rates), VIXY/^VIX (vol),
   UUP (dollar), GLD (gold), BITO/IBIT (BTC). Read the risk-[REDACTED]/off direction.
4. **News & government:** `WebSearch` WSJ + MarketWatch + wires; classify each catalyst
   risk-[REDACTED]/off; pull admin/govt items (tariffs, war, Fed, regulation, exec orders).
5. **Calendar (tomorrow):** `WebSearch` "economic calendar {date}" + Fed speakers + earnings.
6. **Global/overnight:** `WebSearch` Asia/Europe session direction.
7. **Cache:** `STKK` levels from `market_history.md` for SPY/QQQ support/resistance.

## Output format (mirror this)

```
Tomorrow — predicting {next session date}   (run {now})

1 Today ............ {±N}  SPY {c} ({%}), QQQ {c} ({%}), Dow {c} ({%}); breadth {x}; leaders {x}; vol {x}
2 AH/Futures ....... {±N}  ES/NQ {drift}; AH movers {x}
3 Cross-asset ...... {±N}  oil {x}, 10Y {x}, VIX {x}, DXY {x}, BTC {x} → risk {on/off}
4 News/Govt ........ {±N}  {freshest WSJ/MW + admin/geopolitical}
5 Calendar ......... {±N}  {tomorrow's data/Fed/earnings} | EVENT-VETO: {Y/N — what}
6 Global/overnight . {±N}  {Asia/Europe}
7 Positioning ...... {±N}  {pre-Fed/OpEx/day-of-week/month-end/holiday}
──────────────────────────
BIAS: {sum}/14  →  LEAN: {UP / FLAT / DOWN}   prob {U/F/D}
Expected SPY range: {lo}–{hi}  (±{x}% = {VIX}-implied 1σ{, ×1.5 event})
Key levels: SPY {sup}/{res} · QQQ {sup}/{res}
Swing factors (what flips it): {1–3 specific triggers}
Confidence: {high/med/low}   {event-veto note if any}
Watchlist/positioning read: {1–2 lines — what to do, esp. open positions}
```

## The plan to predict (calibration loop — this is what makes it work)

1. **Each evening** (after close / AH): run the 7 blocks, produce the call.
2. **LOG IT** — append to `tomorrow_predictions_log.md`: date, lean, prob, expected range,
   key levels, swing factors, the bias score.
3. **Next session close** — record the ACTUAL: SPY move, did direction hit? in range?
4. **Score it** — direction-correct (Y/N), range-correct (Y/N); update rolling hit-rate.
5. **Weekly review** — inspect misses; if one block keeps misleading (e.g. overnight futures
   faked the open), down-weight it. If one keeps nailing it (e.g. VIX/oil), up-weight it.
6. **Track record is the product** — report the rolling direction hit-rate with every call so
   confidence is earned, not asserted. Target: beat the ~53% naive "up tomorrow" base rate.

## Rules

- **Always show all 7 block scores** + the event-veto check. The number forces honesty.
- **Probabilities, not promises** — give the U/F/D split and the range; never say "it will".
- **Cross-asset leads equities** — oil/VIX/yields/dollar often tell you more than today's close.
- **Event days are bimodal** — on CPI/FOMC/jobs eve, predict the *reaction map* (if hot→X, if cool→Y), not a single direction.
- **Log every call** — an un-logged prediction is worthless; calibration is the whole edge.
- **End with the watchlist read** — what tomorrow's lean means for open positions (e.g. the HOOD spread into the Fed).

## Output checklist

- [ ] All 7 blocks scored with one-line evidence each
- [ ] Cross-asset (oil/VIX/yields/dollar/BTC) pulled
- [ ] Tomorrow's calendar checked → event-veto flag set
- [ ] Bias score → LEAN + U/F/D probability split
- [ ] Expected range (VIX-implied) + SPY/QQQ key levels
- [ ] Swing factors + confidence (lowered into events)
- [ ] Prediction LOGGED to tomorrow_predictions_log.md
- [ ] Watchlist/positioning read
