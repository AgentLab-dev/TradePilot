# Monthly Income Plan — 10–15 closed trades/mo @ $300–500 each

_Calibrated to the **personal account ≈ $50k** (see `account_profiles.md`). Companion to `trading_watchlist.md` + `options_watchlist.md`. The watchlist sources names; this file is the **operating system** — cadence, sizing, exits, risk budget._
_Last updated: June 23, 2026._

> **This is a multi-strategy income engine — not a credit-selling-only book.** The structure is chosen from **direction × IV** (see §3.5), so it earns in up, down, *and* sideways tapes. It works on discipline, not prediction. The $300–500 is the *win-trade* target; survival depends on capping the loss-trades and never stacking correlated risk.

> **⭐ Standing goal: 1–2 GREEN closes per trading day.** Achieved via a **rolling book**
> (6–8 staggered positions) taking **50% profit fast** so something closes green most days.
> Measured over a rolling 5-day window (an ~80% strategy still loses ~1 day in 5). **Never
> force a trade to make the number** — a logged stand-down protects the streak.

---

## 0. The honest math

| | |
|---|---|
| Target | 10–15 **closed** trades/mo × $300–500 |
| Gross goal | **$3,000 – $7,500 / mo** |
| On $50k | **6–15% / month** — aggressive; achievable in normal months, **not** every month |
| Win-rate reality | ~80% win (backtest: NNE 82%, HOOD 84%, MARA 86%) **but avg loss 3–7× avg win** |
| Net expectation | A green month nets most of the gross; **2 max-losses can erase a month** → sizing + stops are the whole game |

**Mental model:** aim for the win number on each trade, plan the book so the loss number can't sink the month.

---

## 1. Capital map ($50k)

| Rule | Value |
|---|---|
| Max loss per trade | **≤ 3% = $1,500** (most trades sized to ~$1,000–1,300) |
| Max concurrent positions | **6–8** |
| Max collateral deployed at once | **≤ $12–15k (25–30%)** — keep dry powder |
| Per-sector / per-theme cap | **1–2** (NNE + MARA = both ultra-high-beta spec names that crater together on risk-[REDACTED] = ONE bet) |
| Monthly circuit breaker | **down 6% (−$3k) on the month → stop opening, manage only** |

---

## 2. The engine — how 3–4 opens/week becomes 10–15 closes/month

You don't open 15 monthlies and wait. You **roll capital**:

- **Open 3–4 new spreads/week** on confirmed triggers → ~14/mo
- **Close at target** — high-IV credit spreads usually hit 50% in **5–12 days** (theta + IV crush) → frees collateral → recycle
- Expiry sweet spot: **2–5 weeks out**
- Result: a steady stream of closes, not a monthly cliff

---

## 3. Weekly cadence

| Day | Action |
|---|---|
| **Mon** | Full-universe Health Check scan + Tomorrow/macro read → rank GO verdicts → build the week's shortlist |
| **Tue–Thu** | Open 3–4 spreads on confirmed triggers only (hold of support / chart reclaim). No forcing. |
| **Daily** | Manage book: GTC closes on winners, enforce close-below-strike stops |
| **Fri** | Log P&L, no new high-risk into the weekend |
| **Month-end** | KPI review → adjust next month's size |

---

## 3.5 Strategy selection matrix — pick structure from direction × IV

**The rule:** the models give a **direction** (STKK trend, STNOW, Tomorrow, whale flow); the chain gives **IV rank**. Cross them → the structure picks itself. Never force one structure onto every name.

| | **Low IV (≲40–50%) → BUY premium** | **High IV (≳50%) → SELL premium** |
|---|---|---|
| **Bullish** | **Call debit spread** (buy lower call / sell higher) — defined risk = debit; cheap because IV low. _e.g. CRM, GOOGL, AVGO_ | **Put credit spread** (sell put / buy lower) — get paid, IV-crush + theta tailwind. _e.g. NNE, DELL, HPE, ANET_ |
| **Bearish** | **Put debit spread** (buy higher put / sell lower) — directional downside, defined risk. _Use in red tapes / failed-breakout rolls_ | **Call credit spread / bear call** (sell call / buy higher) — fade extended-overbought names at resistance; get paid to be right or flat |
| **Neutral / range** | **Calendar / diagonal** (sell near, buy far) — harvest theta when stuck in a range, low IV | **Iron condor** (put credit + call credit) — sell BOTH sides of a rich-IV range-bound name; ~2× the premium, defined risk |

**Income comes from whichever quadrant the tape hands you:**
- **Up + cheap** → buy calls spreads (CRM-type bounce)
- **Up + rich** → sell put spreads (the NNE/DELL book)
- **Down + rich** → **sell call spreads** (this is the missing piece — fade leaders that crack support, or overbought names that stall). In a sustained red tape this is your bread-and-butter, *not* put credits.
- **Down + cheap** → buy put spreads (directional hedge / standalone short)
- **Range + rich** → iron condors (double premium on a pinned name)

> **Why this matters:** a credit-spread-only book is implicitly **long the market every day.** When QQQ rolls over (the exact tape that triggers your stops), the call-credit / put-debit side is what keeps the month green. Always have at least one **non-bullish** structure available when breadth turns down.

**Backtest-validated weighting** (see `backtest_multistrategy.md`, 58 names, 2y, ~4,900 trades/strategy):

| Structure | Backtest expectancy | Role in the book |
|---|---|---|
| **Call debit** | **+15.6% RoR** ($156/$1k), 39% win, huge winners | **Upside amplifier** — confirmed up-trends/oversold bounces; size smaller, let it run |
| **Put credit** | **+3.5% RoR** ($35/$1k), 62% win, steady | **The income core** — better live (vol-risk premium not modeled) |
| **Calendar** | ~flat (+0.9%) | Only genuinely pinned rich-IV ranges; rare |
| **Iron condor** | −3.1% | Situational; don't force |
| **Call credit** | −6.1% in a bull tape | **Bearish insurance** — only on *confirmed* breakdown + event gate |
| **Put debit** | −15.5% in a bull tape | Same — directional short, only on confirmed downtrend |

> **The finding that matters (v2 backtest):** discipline flips the result — multi-strategy **wins** once you add two gates:
> - **Event gate** (never sell premium through earnings/guidance) lifted put-credit **+3.53% → +5.18% RoR** alone — the single biggest edge, the AVGO lesson quantified.
> - **Confirmation + routing** on top → **+5.87% RoR, the best of any approach**, while trading 27% *less* (stands down when there's no confirmed edge).
> - Naive routing (no gates) *under-performed* (+2.57%) — proof that the **gates, not the structure count, are the edge.**
>
> **Playbook:** put-credit + call-debit as the bullish core · bearish quadrant **only on confirmed breakdowns** (price decisively below a falling trend, not a wiggle) · **never sell premium through an event.**

---

## 4. Selection filter (a trade must pass ALL)

- [ ] Sourced from the ranked scan (🟢 GO or 🔴 fade with a clear level)
- [ ] **Structure matches the matrix** (§3.5) — direction × IV, not "always a put credit"
- [ ] Cushion ≥ **8–10%** (credit) / R:R ≥ **2:1** (debit)
- [ ] Credit-to-width ≥ **25%** for credit spreads (the HOOD lesson: thin credit = 7× loss/win)
- [ ] Liquid chain (tight bid/ask, real OI)
- [ ] **No earnings / binary event in the window** (the AVGO −$1,717 rule)
- [ ] Not correlated to an already-open position (sector cap) — and **balance the book's net direction** (don't run 8 bullish credit spreads into a topping tape)

---

## 5. Sizing to hit $300–500 (size so max profit ≈ $400–650, close at 50–80%)

| Credit / contract | Example | Contracts | ~Max profit | ~Collateral | ~Max loss |
|---|---|---|---|---|---|
| ~$0.80 | NNE $3-wide | **5–6** | $400–480 | ~$1,500–1,800 | ~$1,100–1,300 |
| ~$0.81 | HPE $3-wide | **5–6** | $405–486 | ~$1,300 | ~$1,100–1,300 |
| ~$2.10 | ANET $10-wide | **2–3** | $420–630 | ~$2,000–3,000 | ~$1,580–2,370 ⚠️ trim to 2 |
| ~$3.10 | DELL $10-wide | **1–2** | $310–620 | ~$1,000–2,000 | ~$690–1,380 |
| ~$0.24 | MARA $1-wide | 20 | $480 | ~$1,500 | ~$1,520 ❌ too many lots — skip |
| ~$3.15 **debit** | CRM call debit $15-wide | 2 | ~$2,370 (target +$300–500 = close at 15–20%) | $630 (=debit) | $630 |
| ~$3–4 **call credit** | fade extended name $10-wide | 2 | $600–800 | ~$2,000 | ~$1,200–1,400 |
| ~$5–7 **iron condor** | range-bound rich-IV $10-wide each side | 1–2 | $500–1,400 | ~$2,000 (one side) | ~$1,300–1,500 |

**Sizing logic is the same for every structure:** size so the *win* (close at target) lands $300–500 and the *max loss* stays ≤ $1,500. **Debit spreads:** you don't hold to max — take +$300–500 (often 15–40% of width) and leave. **Iron condors:** collateral = one side only (both can't lose).

**Capital-efficiency ranking:** richer credit + wider spread = fewer lots, cleaner fills, less slippage. **DELL/ANET-type names beat MARA-type** for this goal.

---

## 6. Exit discipline (where the money is made or lost)

- 🎯 **Profit:** the moment you open, set a **GTC buy-to-close at 50–80% of max.** High-IV/whippy names (NNE) → take **50% fast.** Cleaner names (DELL) → 60–70%.
- 🛑 **Stop:** underlying **closes below the short strike** (credit) / spread **−50%** (debit). Judge the *close*, not an intraday wick.
- ⏰ **Time:** close or roll in the **expiry week** — never hold a short spread into final gamma.

---

## 7. Drawdown control (survival)

1. One max loss ≈ 3–5 wins gone → after **2 losses in a month, halve size.**
2. Hit the **−6% monthly circuit breaker** → stop opening, manage existing only.
3. Never exceed **6–8 open / $12–15k collateral.**
4. Re-pull live chain + confirm hold of support before EVERY send (no selling into a slide).

---

## 8. Event calendar gate (reduce/skip new credit sells around)

CPI · **PCE** · FOMC · monthly OpEx (3rd Fri) · any holding's earnings · major tariff/geopolitical prints.
_Currently live: HPE + DELL both gated behind **PCE** before arming._

---

## 9. Tracking (log every trade)

`Open date · Underlying · Structure · Credit · Qty · Close date · P&L · Win/Loss · Days held`

**Monthly KPIs:** win rate · avg win · avg loss · # closes · net $ · % of $300–500 target hit. Review last trading day → tune size.

---

## 10. This month — starting lineup (5 of ~14 already in motion)

| Trade | Status | Sized for | Toward target |
|---|---|---|---|
| **NNE** $23/$20 put credit ×5 | 🟢 OPEN — GTC @ $0.16 (+~$320) | $300–500 ✅ | 1 |
| **DELL** $390/$380 put credit | 🟡 ARMED — post-PCE, ⭐ best setup | 1–2 lots = $310–620 | queued |
| **HPE** $45/$42 put credit | 🟡 ARMED — post-PCE + holds $47–48 | 5–6 lots = $325 | queued |
| **ANET** $160/$150 put credit | 🟡 watch — needs $164–165 hold | 2 lots = $420 | queued |
| **CRM** $155/$170 call debit | 🟡 ARMED — close above $158 | ~$1,000 max profit | queued |

**Gap to fill:** the Monday full-universe scan feeds ~3–4 fresh GO names/week to keep the engine at 10–15 closes/mo. Don't stack: NNE and MARA are both ultra-high-beta spec names (they move together on risk appetite) — run only one at a time, so MARA stays benched while NNE is open.

---

## 11. Repeatable month template

```
Week 1: scan → open 3–4 (post any month-start data) · manage
Week 2: open 3–4 · close Week-1 winners at target · check OpEx
Week 3: open 3–4 · close winners · trim into OpEx Fri
Week 4: open 2–3 (shorter expiries) · close/roll expiry-week · month-end KPI review
Event weeks (CPI/PCE/FOMC): cut new opens in half, no fresh credit into the print
```

**The one-line rule:** _Read direction × IV, pick the matching structure (buy cheap / sell rich / fade extended / condor a range), size so the win is $300–500 and the loss is survivable, close winners early, balance the book's net direction, and never sell into a binary._
