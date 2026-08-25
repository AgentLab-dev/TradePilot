# STNOW — 360° Pre-Trade Intelligence Model

_A single scored verdict from seven lenses: price/trend, blended analyst consensus (Yahoo + Robinhood), news (WSJ/MarketWatch/wires), historical-analog backtest, government/macro/geopolitical risk, and whale/options flow._
_Trigger: type **`STNOW`** (optionally with a ticker, e.g. `STNOW HOOD`). Skill: `~/.cursor/skills/stnow-360-check/`._
_Last updated: June 19, 2026 — added **Step 0.5 "Why Is It Cheap?" re-test** (value-trap gate)._

> ⚠️ **Educational / personal use — not financial advice.** Re-pull live data before acting.

---

## What STNOW answers

> *"What do I need to KNOW before I touch this?"*

It refuses to collapse a decision into a vibe. Each lens gets a **−2 … +2 score** with one line of evidence, the scores sum to a composite, and the composite maps to **GO / WAIT / AVOID** — with a macro veto, the single biggest risk, and the exact trigger to act.

The point: **a high-win-rate chart can still be AVOID** if analysts are negative, the news is bad, or a war/Fed/earnings event is in the window. STNOW makes all five of those argue it out on the same scorecard.

---

## Step 0 — INTAKE: ASK, don't assume (run FIRST, every time)

> **The SPCX lesson (why this exists):** a confirmed $135 IPO allocation was treated like a
> chase and the model said AVOID — the user cancelled a 200-share allocation that would have
> flipped for **~$5k+** on day one. The verdict depends entirely on context the model must ASK
> for, never guess.

Before scoring, ask (don't assume any of these):

1. **Account** — Personal / $1k agent account / Other → scopes the risk rules.
2. **Entry basis** — *Are you **guaranteed** the fixed allocation price?* Confirmed IPO
   allocation at offer / Buying in the open market / Already hold shares / Just evaluating.
3. **Intent / plan** — Flip for the day-1 pop / Short-term swing / Long-term hold / Evaluating.
   ("Do you want to exit into strength, or hold?")
4. **Exit goal** — Lock any green now / specific % or $ target / hold through catalysts / unsure.
5. **Size / risk** — how many shares/contracts and $ at risk.

The 6-lens score still runs, but the **action** must respect entry basis + intent + account.

---

## Step 0.5 — The "Why Is It Cheap?" RE-TEST (value-trap gate, run when a name looks like a bargain)

> **The ZS/VEEV lesson (why this exists):** both screened as +60% / +44% "upside to target" and
> were scored **+5 STRONG GO** — purely because they sat far below analyst targets. But they were
> cheap *because they sold off on real, unresolved problems* (ZS: −30% on a sales-leadership exit +
> FY27 growth cut to 16–17%; VEEV: −45% on Salesforce competition stealing pharma CRM deals).
> **A big discount to a target is NOT edge if the target is stale and the cause of the drop is
> unresolved.** That's the textbook value trap.

**Trigger this re-test whenever ANY of these is true:** price is in a **DOWN regime**, **>20% below its 52-week high**, RSI **< 40** (oversold), or the **A-lens upside is unusually large (≥ +35%)**. If a name "looks too cheap to ignore," you MUST answer all four questions before scoring lens A or N positive:

1. **WHY did it fall?** Name the specific catalyst — guidance cut, growth deceleration, competition, execution/management exit, fraud, litigation, macro de-rating. *"It just dropped"* is not an answer.
2. **Is the target STALE or POST-event?** If analyst targets/mean were set **before** the selloff catalyst, the "upside %" is **fake** — targets get cut next. Down-weight or discard a pre-event target. Use only post-event, revised targets for lens A.
3. **Has the CAUSE resolved, or is it structural/unresolved?**
   - *Resolved / one-off* (e.g., a clean guidance reset already digested) → discount may be real → lens A can stay positive.
   - *Unresolved / structural* (competition taking share, management still gone, secular decline) → **it's a value trap** → **cap lens A at 0** and the **composite verdict at WAIT**.
4. **Is there a DATED catalyst that resolves it?** (next earnings, product launch, a filled exec role). If yes, **the trigger to act is "wait for that catalyst to confirm the turn"** — not "buy the discount now." Buying *before* the event that caused the drop is resolved = catching the knife.

**Gate rule:** if Q3 = "unresolved/structural," STNOW is **capped at WAIT** regardless of how big the upside looks. A beaten-down chart + a fat target is the **most common false-GO** in the model — this gate is the antidote. _(See the AVGO −$1,717 and the ZS/VEEV over-call: cheapness and big targets both lied.)_

---

## The 7 lenses

| Lens | What it measures | Source |
|---|---|---|
| **P — Price & Trend** | regime (up/down/range), RSI, ATR vol, beta, R:R, %-above-entry | `STKK` (Yahoo 2y daily) |
| **A — Analysts (blended)** | Yahoo consensus **+** Robinhood ratings → combined target & direction | Yahoo `quoteSummary`; RH app "Analyst Ratings" card |
| **N — News & sentiment** | freshest WSJ / MarketWatch / wire headlines; catalyst bull/bear | `WebSearch` |
| **H — Historical analog** | how similar past setups (this name + comps) resolved | Python backtest on 2y history |
| **M — Macro / government** | Fed, CPI, tariffs/USTR, war/geopolitics, elections, regulation | `WebSearch` + watchlist macro gate |
| **W — Whale / options flow** | institutional positioning: P/C vol, OI walls, Vol/OI unusual, near-money put skew | `Whale Check` (`market_data/whale_check.py`) |

> **W-lens caveat:** far-OTM put OI is **hedging, not bearish** — only near-money put buying scores negative. A bearish W on an otherwise-GO name is a **yellow flag**: down-weight or wait for flow to turn before committing.

---

## Scoring rubric (each lens −2 … +2)

| Score | P (price/trend) | A (analysts) | N (news) | H (analog) | M (macro/govt) |
|---|---|---|---|---|---|
| **+2** | UP + R:R≥2, not extended | ≥15% below blended target + Buy | strong fresh bullish catalyst | similar setups resolved UP | risk-[REDACTED], no event before exit |
| **+1** | UP but extended / pullback-buy | below target / Buy-Hold | mild positive | mostly up | calendar clear-ish |
| **0** | RANGE / no edge | ≈ at target | neutral / none | mixed 50/50 | mixed |
| **−1** | DOWN, needs reclaim | above target | overhang / soft | mostly down | binary event ahead |
| **−2** | DOWN + breaking | above target + Sell-rated | fresh bearish catalyst | resolved DOWN | active war/tariff/shock window |

**W — Whale/options flow (−2…+2):** +2 P/C vol <0.5 + fresh call sweeps · +1 lean-bull · 0 neutral/mixed · −1 near-money put buying · −2 P/C vol >1.5 + fresh put sweeps. _(far-OTM put OI = hedge, ignore.)_ Composite range widens to **−12 … +14**; same verdict bands apply proportionally (a clean +2 W nudges a borderline name over its trigger; a −2 W caps a GO at WAIT until flow turns).

> **A-lens caveat (Step 0.5 gate):** a large "below target" upside only earns **+2/+1** if the target is **post-event** and the **cause of the discount is resolved**. If the target is **stale (pre-selloff)** or the drop is **structural/unresolved**, **cap lens A at 0** — fat upside to a stale target is a value trap, not edge.

### Composite → verdict (−10 … +10)

| Score | Verdict | Action |
|---|---|---|
| **≥ +5** | 🟢 STRONG GO | high-conviction long; run STKK for levels |
| **+2 … +4** | 🟢 GO (on trigger) | lean long; wait for confirmation candle |
| **−1 … +1** | ⏸️ WAIT | no edge; stand down |
| **−2 … −4** | 🔴 AVOID | no long; short-watch only |
| **≤ −5** | 🔴 STRONG AVOID | stay out |

### 🚦 Macro VETO (gate)
If a **binary event** (earnings, CPI, Fed, major tariff/war decision) lands **before the intended exit**, cap the verdict at **WAIT** regardless of score. Macro can veto down, but **never forces a GO** — a clear calendar doesn't make a bad setup good. _(The AVGO −$1,717 trade broke this rule by selling into earnings.)_

### 🎟️ IPO-allocation branch (overrides the open-market verdict)
The 6-lens score judges **buying in the open market**. It does NOT apply to a **confirmed IPO allocation at the offer price** — that's an *advantaged* entry (in below the open, day-1 demand working for you).

- Confirmed at-offer allocation → **NOT a chase.** Default = **sell into day-1 / early strength, lock the green.** The allocation discount + day-1 demand both **decay after day one** (fade, then lockup/unlock supply).
- Hold a runner **only if** it closes strong on heavy volume **above the opening print** AND intent is a swing/hold — even then, scale out most.
- A STRONG-AVOID open-market score means *"don't BUY more here,"* **not** *"dump an advantaged allocation."* Say which question you're answering.

### 🧭 Account context (scope every action)
- **$1k agent account:** capital-preservation — no chasing, R:R ≥ 2:1, 1 contract on high-beta, max loss ≤ 15–20% of account.
- **Personal account:** different size/risk/goals — **ask** for its parameters; never apply the $1k rules to it. IPO allocations here are flip candidates.
- Saved profiles: `account_profiles.md` (confirm/update with the user — don't assume).

---

## How the analyst blend works (P + Yahoo + Robinhood)

1. **Yahoo (programmatic):** mean, median, high, low targets + `recommendationKey` + # analysts.
2. **Robinhood (app card):** RH's MCP has **no ratings endpoint**, so read the "Analyst Ratings" card in the RH app (% Buy / Hold / Sell + RH's aggregated target) — or paste it in.
3. **Blend:** `blended_target = mean(Yahoo_mean, RH_target)`; direction = consensus of both rating sets.
4. **Edge flag:** `upside% = blended_target / price − 1`. If **price > blended target → negative edge** (the "trading above fair value" flag, e.g. MU/ASML/INTC/SNDK in June 2026).

---

## Output format

```
STNOW — {TICKER}  ${price} ({1d%})   {date/time}

P Price/Trend ...... {±N}  regime, RSI, R:R
A Analysts(blended)  {±N}  Yahoo $X (n) + RH $Y → blended $Z; ±%; rating
N News ............. {±N}  freshest catalyst + source
H Historical analog  {±N}  "similar setups: X% up, avg +Y% in 2wk"
M Macro/Govt ....... {±N}  next event + date; war/tariff/Fed risk
W Whale/Flow ....... {±N}  P/C vol; OI walls; fresh sweeps; ATM IV {x}% (EM ±${y}); skew (Whale Check)
─────────────────────────────
COMPOSITE: {sum}/14  →  {GO / WAIT / AVOID}
Macro veto: {none | capped at WAIT — {event} on {date}}

Biggest risk: {one line}
Trigger to act: {specific price/news condition}
Expression: {shares / STKK levels / Three Good spread / call debit}
```

---

## Worked example — SPCX (SpaceX), IPO day, Jun 12 2026

```
STNOW — SPCX  $167.81 (+24.3% vs $135 IPO)   Jun 12, 11:34 AM PT

P Price/Trend ...... -1   no history (IPO day); pure momentum, no MAs/RSI → no structure
A Analysts(blended)  -2   Yahoo $139 (n=3) SELL; Morningstar FV $780B ≈ 48% below mkt → price 21% ABOVE target
N News ............. +1   largest IPO ever, 4x oversubscribed, BlackRock $5B — but debut hype, fades
H Historical analog  -1   hot IPO-day pops (+20%+) historically fade into lockup; no name-specific history
M Macro/Govt ....... -1   richly valued into a choppy tape; lockup supply (180d) + Jul/Oct earnings windows
─────────────────────────────
COMPOSITE: -4/10  →  🔴 AVOID
Macro veto: n/a

Biggest risk: chasing a +24% debut into a SELL-rated, ~2x-overvalued name with no support levels.
Trigger to act: let it base ~20+ days; watch the $135 IPO floor. Below $135 = IPO buyers underwater.
Expression: none — watch-only until it builds structure.
```

---

## Worked example — ZS (Zscaler), the value-trap re-test, Jun 19 2026

```
STNOW — ZS  $124.72 (flat)   Jun 19   [Step 0.5 triggered: DOWN regime, RSI 38, +60% "upside"]

Why is it cheap? (re-test)
  Q1 WHY fell:   −30% on May 26 — FY27 growth guided to 16–17% (from 25%) + 2 sales leaders quit + FCF-margin cut
  Q2 target:     $200 mean is partly STALE/being trimmed post-print → "upside %" inflated → discard for lens A
  Q3 cause:      UNRESOLVED — sales leadership not refilled, SASE competition rising → structural "show-me"
  Q4 catalyst:   Q4 FY26 (~August) — organic net-new ARR ex-Red Canary + sales roles filled = the real test

P Price/Trend ...... 0    DOWN/range, "out of favor" per Evercore; oversold RSI 38 but no reclaim
A Analysts(blended)  +1   capped (Step 0.5): target stale/being cut → big discount is NOT clean edge
N News ............. -1   weak FY27 guide + leadership exits + downgrades = unresolved overhang
H Historical analog  0    post-guidance-cut software turnarounds are 50/50 until execution proves out
M Macro/Govt ....... -1   August Q4 is a binary that resolves the exact cause → event ahead
─────────────────────────────
COMPOSITE: -1/10  →  ⏸️ WAIT (show-me)
Macro veto: capped at WAIT — Q4 FY26 (~Aug) resolves the selloff cause

Biggest risk: buying a value trap — "cheap" because growth decelerated + sales org broke, not yet fixed.
Trigger to act: wait for the August Q4 → organic ARR holds + both sales roles filled = turn confirmed.
Expression: none now. Without the re-test this scored +5 STRONG GO — the gate corrected a false-GO.
```

---

## Rules

- **Always show all 6 lens scores** — the number forces honesty.
- **Run Step 0.5 ("Why Is It Cheap?") whenever a name looks like a bargain** (DOWN regime, >20% off highs, RSI <40, or A-lens upside ≥ +35%). A fat discount to a **stale** target on an **unresolved** problem is a **value trap → cap at WAIT** until a dated catalyst confirms the turn. Never score lens A positive on a pre-event target.
- **News must be fresh** (date + source). If analyst targets are being revised hard, down-weight the static mean.
- **Macro can VETO but never forces a GO.**
- **End with ONE action**, not a menu. If WAIT/AVOID, state exactly what would flip it.

## Cross-reference

- Levels engine: `STKK` / `trade_entry_exit_algorithms.md`
- Credit spreads: `three_good_put_credit_strategy.md`
- Live watchlists: `trading_watchlist.md`, `options_watchlist.md`, `ntap_list.md`
