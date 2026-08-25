---
name: three-good-put-credit
description: "Put-credit-spread strategy for high-IV bullish/neutral names, using 10-week weekly-support analysis to place short strikes. Invoke ONLY when the user types the trigger 'Three Good' (or 'THREE GOOD'). Do not auto-apply."
disable-model-invocation: true
---

# Three Good — Put Credit Spread Algorithm

**Trigger:** runs ONLY when the user types **`Three Good`**. Otherwise stay off.
**Companion:** `trade-entry-exit-pricing` (STKK/TASP) for the underlying levels.

> Goal: get **paid** to be bullish/neutral on high-IV names by **selling** downside
> insurance below a support floor the stock rarely closes under. Always output
> **numbers** (strikes, credit, breakeven, max loss, R:R) — never vague advice.

## What it is (plain English)

A **bull put credit spread** = SELL a put + BUY a lower put. You collect a credit and
**win if the stock stays ABOVE your short strike** (flat / up / slightly down all win).
It is a **bullish/neutral** bet — NOT a bet the stock falls. High IV = richer credit +
IV-crush & theta tailwinds → ideal for elevated-vol names (the "Three Good": e.g.
MARA, NNE, HOOD — but applies to any high-IV name the user is bullish on).

## Global gates (must all pass)

1. **Direction:** only sell put spreads on names you're **bullish/neutral** on, in a
   RANGE or UP regime — OR a downtrend name that has **confirmed a reclaim** of support.
   NEVER sell into an active slide (the AVGO / "sell into earnings gap" mistake).
2. **IV gate:** ATM IV ≥ ~50% (rich premium worth selling). Below that, skip — credit too thin.
3. **Event gate:** no earnings / binary catalyst before expiry (IV-crush can't gap your strike).
4. **Credit gate:** collected credit ≥ ~25–33% of spread width. If thinner, widen DTE or skip.
5. **Account gate:** max loss per spread ≤ ~15–20% of account; 1 contract for high-beta names.

## The algorithm (5 steps)

```
STEP 1 — REGIME (from STKK): trend, RSI, vol, beta. Confirm bullish/neutral + IV≥50%.

STEP 2 — 10-WEEK WEEKLY SUPPORT: for the last 10 COMPLETED weeks, compute each
  week's LOW and FRIDAY CLOSE. Find the "support floor":
    floor = a level the weekly LOW held above in >=8 of 10 weeks
            AND that no Friday CLOSE broke (closing-basis support).
  This floor is where the stock's path repeatedly bottoms.

STEP 3 — SHORT STRIKE = at or just BELOW the support floor.
  Target ~0.20–0.30 delta (≈70–80% probability OTM). The wider below spot, the
  safer but smaller the credit. Prefer a strike with real open interest (liquid).

STEP 4 — LONG STRIKE = $2–5 below the short (defined risk).
  width tuned so MAX LOSS = (width − credit) × 100 fits the account budget.

STEP 5 — EXPIRY = ~10–20 days (2-week sweet spot): fast theta, past any event.
  Compute: credit (mid), breakeven = short − credit, max loss, max profit,
  RoR = credit / max-loss, cushion % = (spot − short)/spot.
```

## Entry timing

- Sell into a **confirmed hold or reclaim** of the support floor — ideally a fear-dip
  that stabilizes (you collect fatter premium on the dip).
- Place as a **single combo LIMIT at the mid** (never market on wide small-cap spreads).
- Do **not** chase: if price is far ABOVE the entry zone after a big green day, wait for
  the pullback-and-hold instead of selling a low-credit far-OTM spread.

## Exit plan (mirrors STKK Algo 4)

```
PROFIT: buy the spread back at 50% of max credit (don't milk the last nickels).
STOP:   underlying CLOSES below the short strike (use the CLOSE, not an intraday
        touch — high-beta names pierce intraday then recover), OR spread loss = 2× credit.
TIME:   close/roll before the expiry WEEK (gamma + pin risk).
```

## "Judge the close, not the touch" rule

High-beta names (beta >2.5) routinely **spike below the short strike intraday and
recover by Friday**. Backtests show the weekly LOW pierces support far more often than
the Friday CLOSE does. So: set alerts on the **daily/Friday close**, accept a scary
path, and size small enough that the intraday noise doesn't force a panic exit.

## Backtest findings (50 weekly trades/name, ~12 mo, recent-floor rule)

| Name | Win rate | Avg win | Avg loss | Net (held-to-expiry) | Net (close-stop) |
|---|---|---|---|---|---|
| NNE | 82% | +$44 | −$106 | **+$849** | +$656 |
| HOOD | 84% | +$36 | −$264 | **−$600** | −$496 |
| MARA | 86% | +$27 | −$115 | +$356 | **+$1019** |

**The five lessons that change how we trade this:**

1. **High win rate is a trap.** HOOD won 84% of the time and still **lost money** —
   because avg loss ($264) was ~7× avg win ($36). A few max-loss gaps erase dozens of
   small wins. **Always check credit-to-width, not just win %.**
2. **Credit-to-width gate is mandatory: ≥ ~25–30%.** HOOD's $3-wide for $0.36 (12%)
   is structurally a loser — break-even needs ~89% win rate. Sell a closer/fatter strike
   or skip the credit spread (use a call debit spread for far-OTM bullish names instead).
3. **The close-stop helps TREND names, hurts WHIPPY ones.** MARA (trends) went
   +$356 → +$1019 with the close-stop (cuts losers early). NNE (high-beta, mean-reverts)
   went +$849 → +$656 — it spikes below the short then recovers, so a hard close-stop
   locks in losses that would have come back. **→ Trend names: close-stop. Whippy
   high-beta names (NNE): use a wider $-stop (2× credit) or smaller size + ride the noise.**
4. **Max-loss hits cluster on event/news gaps.** Every blow-up was a gap week. The
   event gate (no catalyst before expiry) is the single biggest loss-avoider.
5. **Size for the tail, not the win rate.** One max loss = many wins. Keep per-trade
   max loss ≤ 15–20% of account; never stack all three at once.

## Refined per-name handling

- **MARA** — best fit: trends cleanly, close-stop adds big value. Standard rules.
- **NNE** — richest IV but whippy + lowest win rate. Use a $-stop (2× credit) not a hard
  close-stop, smaller size, and lean on its high held-to-expiry edge. Take 50% profits fast.
- **HOOD** — weak credit-spread candidate at far-OTM (thin credit/width). Either sell a
  closer short strike to clear the 25% credit gate, or trade it as a **call debit spread** (bullish) instead.

## Output checklist

- [ ] STKK regime + IV pulled (≥50%)
- [ ] 10-week weekly lows + Friday closes tabulated; support floor identified
- [ ] Short strike at/below floor (~0.20–0.30 delta), long strike $2–5 below
- [ ] Credit (mid), breakeven, max loss, max profit, RoR, cushion% computed
- [ ] Entry trigger (confirmed hold/reclaim) + event gate stated
- [ ] Exit: 50% profit, close-below-short stop, pre-expiry-week time stop
- [ ] Size ≤ 15–20% account max loss; 1 contract for high beta
