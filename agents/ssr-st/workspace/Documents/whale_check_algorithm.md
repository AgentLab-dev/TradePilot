# Whale Check — Institutional Options-Flow Model

_Reads the live Nasdaq option chain to surface where big money is positioned: standing open-interest (OI) walls, fresh "unusual" activity (Vol/OI), **implied volatility (ATM IV, expected move, skew)**, and put/call flow → one **🟢 BULLISH / 🟡 NEUTRAL / 🔴 BEARISH** flag with a **−2…+2 score**._
_Trigger: type **`Whale Check`** (optionally with tickers). Engine: `market_data/whale_check.py`._
_Last updated: June 19, 2026 — created; **added IV engine (BS inversion + Brenner–Subrahmanyam + skew + expected move)**; wired into STKK, STNOW, Three Good, Tomorrow._

> ⚠️ **Educational / personal use — not financial advice.** Flow is a *confirming* signal, not a standalone trade trigger. Re-pull live before acting.

---

## 1. What it is (plain English)

It replicates the paid "whale flow" / "unusual options activity" screens (FlowAlgo, OptionStrat Flow, Barchart UOA) **for free** from the Nasdaq options API. It answers one question:

> *"Is smart money positioned the SAME direction as my trade — or against it?"*

A chart can look bullish while institutions quietly load puts. Whale Check forces the options tape onto the scorecard so flow has to agree before you commit.

## 2. Data & metrics (from the Nasdaq chain)

| Metric | Meaning | Read |
|---|---|---|
| **P/C volume ratio** | today's put vol ÷ call vol | < 0.7 = bullish, > 1.3 = bearish |
| **P/C OI ratio** | open put ÷ open call positions | context; deep-OTM puts skew this (hedges) |
| **OI walls** | strikes with the biggest standing open positions | call walls *above* = upside targets; put walls *far below* = **hedges, not bears** |
| **Vol/OI > 2 (unusual)** | today's volume dwarfs existing OI = **fresh positioning** | the real "whale" tell — new bets, not old |
| **Near-money put vol** | put volume within −10%…+2% of spot | the *real* bear tell (vs deep-OTM hedges) |
| **ATM IV** | implied vol at the ~30-DTE ATM strike (BS-inverted from the mid) | how rich options are; **Three Good gate = IV ≥ 50%** |
| **Expected move** | `S × IV × √T` — the ±$ range the chain prices by expiry | sanity-check targets against it |
| **IV skew** | `IV(25Δ put) − IV(25Δ call)` | put skew = fear/hedging; call skew = upside chase |

### IV formulas used
```
ATM quick (Brenner–Subrahmanyam):  σ_ATM ≈ (C/S) × √(2π/T)
Precise (any strike):              invert Black–Scholes for σ via Newton–Raphson
                                   (bisection fallback), r = 4.5%
Expected move (1σ by expiry):      EM = S × σ × √T
Skew:                              σ(put ~7% OTM) − σ(call ~7% OTM)
```

**Hedge caveat (critical):** far-OTM puts ($20–40% below spot) are almost always **portfolio insurance**, not directional shorts. The model **down-weights deep-OTM put OI** — only near-the-money put buying counts as genuine bearishness.

## 3. Score → flag (−2 … +2)

```
flow = P/C vol:  <0.5 → +2 | 0.5–0.7 → +1 | 0.7–1.0 → 0 | 1.0–1.5 → −1 | >1.5 → −2
       + fresh-unusual split: ≥65% call → +1 | ≤35% call → −1 | else 0   (clamp −2..+2)

IV modifier:
       call-heavy flow AND call skew (skew ≤ −1 pt)  → +1   (whales paying UP = real conviction)
       put skew rising (skew ≥ +3 pts) or put-heavy + put skew → −1   (fear/hedging pressure)
       else 0     (mild put skew is NORMAL for equities → no penalty)

score = clamp(flow + IV-mod, −2, +2)
```

| Score | Flag |
|---|---|
| **+2** | 🟢 BULLISH |
| **+1** | 🟢 lean-bull |
| **0** | 🟡 NEUTRAL |
| **−1** | 🔴 lean-bear |
| **−2** | 🔴 BEARISH |

## 4. How it plugs into the other models

| Model | Whale Check role |
|---|---|
| **STNOW** | New **7th lens "W — Whale/Options flow"** (−2…+2). Confirms or contradicts the P/A/N read; a bearish W on a GO is a yellow flag → down-weight or wait for flow to turn. |
| **STKK** | **Confirmation overlay** — does flow agree with the chart's regime? Bullish chart + bullish whale = high-conviction entry; bullish chart + bearish whale = wait. |
| **Three Good** (put credit spreads) | **Direction gate** — selling puts is a bullish/neutral bet, so require Whale flag **NOT bearish** (≥ NEUTRAL). A near-money put-buying surge = veto (don't sell into bearish flow). |
| **Tomorrow** (next session) | **8th signal block** — run on SPY/QQQ; index call/put flow + 0DTE/weekly skew adds to the −14…+14 composite. |

## 5. Run instructions

```bash
cd market_data
python3 whale_check.py AVGO --spot 411.35        # one name (spot enables near-money/hedge tags)
python3 whale_check.py MARA NNE HOOD --to 2026-09-30   # several (prints a flag summary)
```

- Volume = prior completed session; OI updates T+1. Re-run after the open for live confirmation.
- Pair with OptionStrat Flow (free, 15-min delayed) to see sweep-vs-block + premium $ size the raw chain can't classify.

## 6. Latest run — June 18/19, 2026

### Three Good names (put-credit candidates) — all confirm bullish
| Ticker | P/C vol | ATM IV | Exp move | Skew | Whale flag | Three Good IV gate |
|---|---|---|---|---|---|---|
| **MARA** $14.22 | 0.11 | ~85% | ±23.5% | +2.8 | 🟢 BULLISH (+2) | ✅ IV ≥ 50% |
| **HOOD** $108.15 | 0.30 | ~68% | ±18.7% | +1.1 | 🟢 BULLISH (+2) | ✅ IV ≥ 50% |
| **NNE** $28.21 | 0.37 | (thin vol) | — | — | 🟢 BULLISH (+2) | confirm IV live |

### SPX top-3 swing names
| Ticker | P/C vol | ATM IV | Exp move | Skew | Whale flag | Note |
|---|---|---|---|---|---|---|
| **AVGO** $411.35 | 0.44 | ~48% | ±13.4% (±$55) | +2.8 | 🟢 BULLISH (+2) | IV <50% → **don't sell puts** (confirms Three Good SKIP); call debit spread is the right vehicle. Fresh $415–450 call sweeps; far-OTM puts = hedges |

## Cross-reference
- Levels: `STKK` · 360°: `stnow_algorithm.md` · Put spreads: `three_good_put_credit_strategy.md` · Next-day: `tomorrow_market_predictor.md`
