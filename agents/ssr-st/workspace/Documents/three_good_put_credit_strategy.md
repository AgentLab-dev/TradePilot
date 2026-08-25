# "Three Good" — Put Credit Spread Strategy & Algorithm

_High-IV bullish/neutral put-credit-spread system for **MARA · NNE · HOOD**._
_Last updated: **Jun 11, 2026** · Trigger: type `Three Good` to re-run with live data._
_Companion skill: `~/.cursor/skills/three-good-put-credit/SKILL.md` · Levels engine: STKK (`trade-entry-exit-pricing`)._

> ⚠️ **Educational / personal trading notes — not financial advice.** Options carry risk
> of total loss. Re-pull the live chain before sending any order; quoted premiums are
> indicative midpoints and move constantly.

---

## 1. What this strategy is (plain English)

A **bull put credit spread** = **SELL** a put + **BUY** a lower put (same expiry).
You collect a **credit** up front and **win if the stock simply stays ABOVE your short
strike** — flat, up, or even slightly down all win. It is a **bullish / neutral** bet,
**not** a bet the stock falls.

We do this only on **high-IV names** (richer premium + IV-crush & theta tailwinds), with
the short strike placed **below a 10-week weekly-support floor** the stock rarely closes under.

```
        profit
          │   ┌──────────────  (keep full credit if stock ≥ short strike)
   credit │  /
        0 │─/────────┬──────────────►  stock price at expiry
          │/         │
   −maxL  ┘  breakeven = short − credit
             └ short strike   └ long strike (defines max loss)
```

---

## 2. The algorithm (5 steps)

```
STEP 1 — REGIME (from STKK): pull trend, RSI, ATR vol, beta. 
         Require bullish/neutral (RANGE or UP, or a confirmed reclaim) AND ATM IV ≥ ~50%.

STEP 2 — 10-WEEK WEEKLY SUPPORT: for the last 10 completed weeks, compute each week's
         LOW and FRIDAY CLOSE. The "support floor" = a level the weekly low held above
         in ≥8 of 10 weeks AND that no Friday close broke.

STEP 3 — SHORT STRIKE = at/just below the support floor (~0.20–0.30 delta ≈ 70–80% OTM).
         Prefer a strike with real open interest (liquid).

STEP 4 — LONG STRIKE = $2–5 below the short (defined risk).
         Tune width so MAX LOSS = (width − credit) × 100 fits the account budget.

STEP 5 — EXPIRY = ~10–20 days. Compute credit (mid), breakeven = short − credit,
         max loss, max profit, RoR = credit / max-loss, cushion% = (spot − short)/spot.
```

### Global gates (ALL must pass before selling)

| Gate | Rule |
|---|---|
| **Direction** | Bullish/neutral only, RANGE/UP regime or confirmed reclaim. Never sell into an active slide. |
| **Whale flow** | **`Whale Check` flag must be NEUTRAL or better (≥ 0).** Selling puts is a bullish/neutral bet — a 🔴 bearish flag (near-money put buying) **vetoes** the trade. Don't sell puts into bearish institutional flow. |
| **IV** | ATM IV ≥ ~50% (premium worth selling). |
| **Event** | No earnings / binary catalyst before expiry. |
| **Credit-to-width** | Credit ≥ **25–30%** of spread width (else too thin — widen, move strike, or skip). |
| **Account** | Max loss per spread ≤ 15–20% of account; 1 contract for high-beta names. |

> **Whale Check (Jun 18/19, 2026):** MARA 🟢 +2 (P/C 0.11) · NNE 🟢 +2 (P/C 0.37) · HOOD 🟢 +2 (P/C 0.30) — all confirm bullish flow → put-credit direction gate **PASSES** on all three. Re-run `python3 market_data/whale_check.py MARA NNE HOOD` before selling.

---

## 3. Entry timing & exit plan

**Entry:** sell into a **confirmed hold or reclaim** of the support floor — ideally a
fear-dip that stabilizes (fatter premium). Place as a **single combo LIMIT at the mid**.
Don't chase a far-OTM low-credit spread after a big green candle — wait for the pullback-and-hold.

**Exit:**
| Trigger | Action |
|---|---|
| ✅ **Profit** | Buy back at **50% of credit** — don't milk the last nickels. |
| 🛑 **Stop (trend names)** | Underlying **CLOSES below the short strike** (judge the close, not an intraday touch). |
| 🛑 **Stop (whippy high-beta, e.g. NNE)** | Use a **$-stop (≈2× credit)** instead — hard close-stops get whipsawed (see backtest). |
| ⏰ **Time** | Close/roll before the expiry **week** (gamma + pin risk). |

**"Judge the close, not the touch":** high-beta names pierce the short strike intraday
and recover by the close. Set alerts on the **daily/Friday close**, accept a scary path,
and size small enough that intraday noise doesn't force a panic exit.

---

## 4. 10-week weekly support analysis (Jun 11, 2026)

Last 10 completed weeks — Monday open, Wed, Friday close, weekly Low/High, Friday position in range, week change:

### MARA — current $13.46 · 7/10 up weeks
| Wk start | Mon | Wed | Fri | Lo | Hi | Fri pos | Chg% |
|---|---|---|---|---|---|---|---|
| Mar 30 | 7.80 | 8.04 | 8.71 | 7.63 | 8.77 | 95% | +6.6 |
| Apr 06 | 8.85 | 9.50 | 9.54 | 8.20 | 10.02 | 74% | +8.3 |
| Apr 13 | 10.36 | 10.47 | 11.60 | 9.18 | 12.12 | 82% | +25.1 |
| Apr 20 | 11.63 | 11.84 | 11.64 | 11.02 | 12.22 | 52% | +3.0 |
| Apr 27 | 11.18 | 10.72 | 11.46 | 10.27 | 12.37 | 57% | −0.8 |
| May 04 | 11.83 | 13.03 | 12.94 | 11.26 | 13.35 | 80% | +13.2 |
| May 11 | 13.39 | 12.75 | 12.44 | 11.73 | 13.80 | 34% | −4.0 |
| May 18 | 12.18 | 13.15 | 13.81 | 11.53 | 14.11 | 88% | +14.3 |
| May 26 | 14.28 | 14.33 | 14.38 | 13.58 | 14.87 | 62% | +1.0 |
| Jun 01 | 14.85 | 13.96 | 12.32 | 11.84 | 15.32 | 14% | −12.3 |

Recent weekly-low cluster ≈ **$11.5–11.8** · min Friday close $8.71 (old).

### NNE — current $22.83 · 4/10 up weeks
| Wk start | Mon | Wed | Fri | Lo | Hi | Fri pos | Chg% |
|---|---|---|---|---|---|---|---|
| Mar 30 | 19.00 | 20.40 | 21.38 | 18.93 | 21.98 | 80% | +6.7 |
| Apr 06 | 21.51 | 22.49 | 20.76 | 19.16 | 22.59 | 47% | −3.0 |
| Apr 13 | 21.87 | 24.29 | 25.85 | 19.88 | 27.05 | 83% | +26.4 |
| Apr 20 | 25.53 | 27.39 | 24.50 | 23.64 | 28.33 | 18% | −2.0 |
| Apr 27 | 25.76 | 22.42 | 23.41 | 21.77 | 25.99 | 39% | −2.6 |
| May 04 | 23.32 | 29.07 | 27.45 | 22.10 | 29.27 | 75% | +18.4 |
| May 11 | 28.35 | 27.05 | 24.92 | 24.77 | 29.73 | 3% | −6.4 |
| May 18 | 24.15 | 24.31 | 26.73 | 21.72 | 27.48 | 87% | +7.3 |
| May 26 | 29.07 | 27.36 | 28.88 | 26.43 | 31.48 | 49% | −0.7 |
| Jun 01 | 29.70 | 26.37 | 23.56 | 22.76 | 31.59 | 9% | −17.1 |

Weekly-low floor ≈ **$20** (only 1/10 weeks dipped below; **no Friday ever closed below $20.76**).

### HOOD — current $91.28 · 5/10 up weeks
| Wk start | Mon | Wed | Fri | Lo | Hi | Fri pos | Chg% |
|---|---|---|---|---|---|---|---|
| Mar 30 | 65.16 | 70.11 | 68.90 | 63.51 | 71.55 | 67% | +3.1 |
| Apr 06 | 69.78 | 71.83 | 69.19 | 66.62 | 77.87 | 23% | −0.2 |
| Apr 13 | 71.67 | 87.32 | 90.75 | 67.80 | 93.32 | 90% | +33.1 |
| Apr 20 | 91.28 | 88.43 | 84.71 | 81.75 | 92.38 | 28% | −5.6 |
| Apr 27 | 83.95 | 71.20 | 73.66 | 69.93 | 85.70 | 24% | −12.6 |
| May 04 | 76.55 | 79.05 | 77.03 | 74.25 | 79.49 | 53% | +3.1 |
| May 11 | 80.78 | 76.75 | 77.14 | 74.80 | 81.93 | 33% | +0.5 |
| May 18 | 77.15 | 75.76 | 73.64 | 73.18 | 79.92 | 7% | −3.1 |
| May 26 | 74.09 | 76.23 | 94.30 | 73.45 | 94.40 | 100% | +26.6 |
| Jun 01 | 90.73 | 82.85 | 82.47 | 79.49 | 92.40 | 23% | −8.3 |

Recent weekly-low floor ≈ **$77–79** · min Friday close $68.90 (old).

---

## 5. Computed spreads (live chain, Jun 26 2026 expiry · ~15 days)

| Name | Spot | Spread (sell / buy) | Credit | Max profit | Max loss | Breakeven | Cushion | IV | Credit/Width |
|---|---|---|---|---|---|---|---|---|---|
| **NNE** | $22.89 | **Sell $20P / Buy $18P** | ~$0.45 | ~$45 | ~$155 | $19.55 | 12.6% | **112%** | 22% ✅ |
| **HOOD** | $91.85 | **Sell $77P / Buy $74P** | ~$0.36 | ~$36 | ~$264 | $76.64 | 16% | 79% | 12% ⚠️ thin |
| **MARA** | $13.46 | **Sell $11.5P / Buy $9.5P** | ~$0.27 | ~$27 | ~$173 | $11.23 | 14.6% | 98% | 13.5% ⚠️ thin |

### Entry triggers (none fired yet — wait)
| Name | Wait for | Then sell |
|---|---|---|
| **NNE** | Reclaim **& hold $24** (close above, not a wick) | $20 / $18 put spread |
| **HOOD** | Close **> $92** OR pullback to **~$83 that holds** | $77 / $74 (or closer strike for ≥25% credit) |
| **MARA** | Hold **> $12** with BTC stable (lowest priority) | $11.5 / $9.5 put spread |

---

## 6. Backtest (50 weekly 2-week trades / name · ~12 months · no lookahead)

Short strike set by the rule using only data **before** each entry; results shown
held-to-expiry vs with the close-stop applied.

| Name | Win rate | Avg win | Avg loss | Net (held to expiry) | Net (close-stop) |
|---|---|---|---|---|---|
| **NNE** | 82% | +$44 | −$106 | **+$849** | +$656 |
| **HOOD** | 84% | +$36 | −$264 | **−$600** | −$496 |
| **MARA** | 86% | +$27 | −$115 | +$356 | **+$1,019** |

### The 5 lessons (these shape the rules above)
1. **A high win rate can still lose money.** HOOD won 84% and lost $600 — avg loss was **7× avg win**. A few gap-downs erased dozens of small wins.
2. **Credit-to-width ≥ 25% is mandatory.** HOOD's 12% credit/width needs ~89% win rate just to break even → structurally a loser at far-OTM. Sell closer or use a call debit spread.
3. **Close-stop helps trend names, hurts whippy ones.** MARA +$356 → +$1,019 (trends, cut losers early). NNE +$849 → +$656 (mean-reverts; hard stop gets whipsawed) → use a $-stop instead.
4. **Every blow-up was a news/earnings gap.** The event gate is the #1 loss-avoider.
5. **One max loss erases 6–10 wins.** Size for the tail, not the win rate.

### Per-name handling
- **MARA** — best risk-[REDACTED]; trends cleanly; keep the close-stop. Standard rules.
- **NNE** — richest IV, rewards patience; use a **$-stop (2× credit)** + smaller size, take 50% profit fast.
- **HOOD** — weak put-credit candidate far-OTM (thin credit/width); sell a closer strike for ≥25% credit, or trade it as a **call debit spread** (bullish) instead.

---

## 7. Position sizing ($1k account example)

- 1 contract each, max. Max loss: NNE $155 · MARA $173 · HOOD $264.
- **Do not run all three at once** — combined max loss ~$590 ≈ 59% of a $1k account.
- Pick the **1–2** names with a confirmed trigger; keep total open risk ≤ ~30–35% of account.

---

## 8. Pre-trade checklist

- [ ] STKK regime bullish/neutral + ATM IV ≥ 50%
- [ ] 10-week weekly lows + Friday closes tabulated; support floor identified
- [ ] Short strike at/below floor (~0.20–0.30 delta); long strike $2–5 below
- [ ] **Credit ≥ 25–30% of width** (skip HOOD-style thin spreads)
- [ ] No earnings/catalyst before expiry (event gate)
- [ ] Entry on a **confirmed hold/reclaim** — not into a slide; combo limit at mid
- [ ] Exit set: 50% profit · correct stop per name (close-stop trend / $-stop whippy) · pre-expiry-week time stop
- [ ] Max loss ≤ 15–20% of account; not all three stacked
