---
name: stnow-360-check
description: "STNOW — a 360° pre-trade intelligence model. Fuses 6 lenses (price/trend, blended Yahoo+Robinhood analyst consensus, news from WSJ/MarketWatch/wires, historical-analog backtest, and government/macro/geopolitical catalysts) into a single scored GO / WAIT / AVOID verdict. Invoke ONLY when the user types the trigger 'STNOW'. Do not auto-apply."
disable-model-invocation: true
---

> **Activation:** OFF by default. Run ONLY when the user types **`STNOW`** (optionally with a ticker, e.g. `STNOW HOOD`). Otherwise ignore.

# STNOW — 360° Pre-Trade Intelligence Model

Turns six independent lenses into ONE scored verdict. Always output **numbers** (price, %s,
scores) and a single **GO / WAIT / AVOID** call with the biggest risk + the trigger to act.
Companion algos: `STKK`/`TASP` (levels), `Three Good` (credit spreads).

> Goal: answer "what do I need to KNOW before I touch this?" — technicals, what the
> street expects, what just happened in the news, how similar setups resolved before,
> and what the government / macro calendar can do to it.

## STEP 0 — INTAKE: ASK, don't assume (MANDATORY, do this FIRST)

> **Hard rule (the SPCX lesson):** never run the verdict on assumptions about *which
> account*, *how the user is getting in*, or *what they intend to do*. A confirmed IPO
> allocation flipped for the day-1 pop is the OPPOSITE trade from chasing the same stock
> in the open market — and the right answer depends entirely on context I must ASK for.
> The −$5k SPCX miss happened because the chase-framework was applied to a $135
> allocation. Don't repeat it.

Before scoring, ask the user these (use the `AskQuestion` tool; skip only a question
whose answer the user already stated explicitly this turn). **Do not guess any of them.**

1. **Account** — *Which account is this for?* (Personal account / $1k agent account / Other)
   → scopes the sizing & risk rules (see "Account context" below).
2. **Entry basis** — *How are you getting in?*
   (Confirmed IPO allocation at the offer price / Buying in the open market / Already hold
   shares / Just evaluating). "Are you **guaranteed** the fixed allocation price?" is the
   key IPO question — a confirmed allocation is an advantaged entry, not a chase.
3. **Intent / plan** — *What's your plan?*
   (Flip for the day-1 / early pop / Short-term swing (days–weeks) / Long-term hold /
   Just evaluating). Ask it as "do you want to exit into strength, or hold?" — don't assume.
4. **Exit goal** — *What does a win look like?*
   (Lock any green now / A specific % or $ target / Hold through catalysts / Not sure).
5. **Size / risk** — *How many shares / contracts, and what $ are you risking?* (free text)

Then tailor the verdict to the answers. The 6-lens score still runs, but the **action**
it produces must respect entry basis + intent + account (see branches below).

## STEP 0.5 — "WHY IS IT CHEAP?" RE-TEST (value-trap gate)

> **Hard rule (the ZS/VEEV lesson):** a big "upside to target" is NOT edge if the name is
> cheap *because it sold off on an unresolved problem*. ZS (+60% to target) and VEEV (+44%)
> were scored **+5 STRONG GO** purely on the discount — but ZS had just dropped −30% on a
> sales-leadership exit + FY27 growth cut to 16–17%, and VEEV −45% on Salesforce stealing
> pharma CRM deals. The targets were **stale** and the causes **unresolved** → textbook value
> traps. The discount lied.

**Trigger this re-test whenever a name looks like a bargain** — i.e. ANY of: **DOWN regime**,
**>20% below 52-wk high**, **RSI < 40**, or **A-lens upside ≥ +35%**. Before scoring lens A or
N positive, answer all four (use `WebSearch` for the real reason — don't guess):

1. **WHY did it fall?** Name the specific catalyst (guidance cut, growth decel, competition,
   management exit, fraud, litigation, macro de-rating). "It just dropped" is not an answer.
2. **Is the target STALE or POST-event?** A target set **before** the selloff inflates a **fake**
   upside (it gets cut next). Use only **post-event, revised** targets for lens A; discard stale ones.
3. **Has the CAUSE resolved or is it structural/unresolved?**
   *Resolved/one-off* → discount may be real (lens A can stay positive).
   *Unresolved/structural* (share loss, exec still gone, secular decline) → **value trap → cap
   lens A at 0 and the composite at WAIT.**
4. **Is there a DATED catalyst that resolves it?** (next earnings, product launch, filled role).
   If yes, the **trigger to act is "wait for that catalyst to confirm the turn"** — not "buy the
   discount now." Buying before the cause resolves = catching the knife.

**Gate:** if Q3 = unresolved/structural, STNOW is **capped at WAIT** no matter how big the upside.
A beaten-down chart + a fat (often stale) target is the model's **most common false-GO** — this
is the antidote.

## The 6 lenses (score each −2 … +2)

```
P — PRICE & TREND     (from STKK): regime, RSI, ATR vol, beta, R:R, %-above-entry.
A — ANALYSTS BLENDED  : Yahoo consensus + Robinhood ratings, combined → target & direction.
N — NEWS & SENTIMENT  : latest WSJ / MarketWatch / wire headlines; catalyst bull/bear.
H — HISTORICAL ANALOG : backtest similar past setups (this name + comps) → forward outcome.
M — MACRO / GOVERNMENT: Fed, CPI, tariffs/USTR, war/geopolitics, elections, regulation.
```

### Scoring rubric per lens

| Score | P (price/trend) | A (analysts) | N (news) | H (analog) | M (macro/govt) |
|---|---|---|---|---|---|
| **+2** | UP regime + R:R≥2, not extended | ≥15% below blended target + Buy | strong fresh bullish catalyst | similar setups resolved UP (high hit-rate) | clear risk-[REDACTED], no event before exit |
| **+1** | UP but extended (RSI>70) / pullback-buy | below target / Buy-Hold | mild positive | mostly up, mixed | calendar clear-ish |
| **0** | RANGE / no edge | ≈ at target | neutral / no news | mixed 50/50 | mixed |
| **−1** | DOWN, needs reclaim | above target | overhang / soft | mostly down | binary event ahead (earnings/CPI/Fed) |
| **−2** | DOWN + breaking support | above target + Sell-rated | fresh bearish catalyst | similar setups resolved DOWN | active war/tariff/shock risk window |

> **A-lens caveat (Step 0.5):** a large "below target" upside earns **+2/+1 only if** the target is **post-event** AND the **cause of the discount is resolved**. Stale target or structural/unresolved cause → **cap lens A at 0** (value trap, not edge).

### Composite → verdict (sum, −10 … +10)

| Score | Verdict | Action |
|---|---|---|
| **≥ +5** | 🟢 **STRONG GO** | high-conviction long; size normal, run STKK for levels |
| **+2 … +4** | 🟢 **GO (on trigger)** | lean long; wait for the confirmation candle |
| **−1 … +1** | ⏸️ **WAIT** | no edge; stand down until something changes |
| **−2 … −4** | 🔴 **AVOID** | no long; short-watch only |
| **≤ −5** | 🔴 **STRONG AVOID** | stay out entirely |

### Macro VETO (gate, overrides the score upward-cap)
If a **binary event** (earnings, CPI, Fed, major tariff/war decision) lands **before the
intended exit**, cap the verdict at **WAIT** regardless of score — do not initiate a new
long into a gap-risk event (the AVGO −$1,717 lesson). State the event + date.

### 🎟️ IPO-ALLOCATION BRANCH (overrides the open-market verdict)
The 6-lens score is built to judge **buying in the open market**. It does NOT apply to a
**confirmed IPO allocation at the offer price** — that is an *advantaged* entry (you're in
**below** the opening print, with the day-1 demand wave working for you).

- **If the user holds a confirmed at-offer allocation → it is NOT a chase.**
  Default action = **SELL into day-1 / early strength and lock the green.** The edge is the
  allocation discount + day-1 demand, and **both decay after day one** (fade from the high,
  then the lockup/unlock supply). Take the pop; don't round-trip it.
- **Hold a runner ONLY if** it closes strong on heavy volume **above the opening print**
  AND the user's stated intent is a swing/hold (not a flip). Even then, scale out most.
- A **STRONG AVOID** open-market score (e.g. SPCX −5) means *"don't BUY more here,"* not
  *"dump an advantaged allocation."* Keep the two cases separate and say which one you're answering.

### 🧭 ACCOUNT CONTEXT (scope every action to the right account)
Advice must be tagged to the account from Intake Q1. Never bleed one account's rules into another.

- **$1k agent account** — capital-preservation rules: no chasing, R:R ≥ 2:1 gate, 1 contract
  on high-beta names, max loss ≤ 15–20% of account, STKK/Three Good gates apply.
- **Personal account** — different size / risk budget / goals. **Ask** for its parameters
  (size, per-trade risk %, goal); do NOT apply the $1k rules to it. IPO allocations here are
  flip candidates per the branch above.
- See `account_profiles.md` for the saved profiles (confirm/update with the user — don't assume).

---

## Data sources (pull these, in order)

1. **P — Price/Trend:** run `STKK` (Yahoo `chart?range=2y&interval=1d`): regime, SMA20/50/200,
   RSI(14), ATR, beta vs SPY, entry/stop/target, R:R.
2. **A — Analysts (BLENDED):**
   - **Yahoo (programmatic):** `quoteSummary?modules=financialData` → `targetMeanPrice`,
     `targetMedianPrice`, `targetHighPrice`, `targetLowPrice`, `recommendationKey`,
     `numberOfAnalystOpinions`.
   - **Robinhood (app card):** RH MCP has **no ratings tool** — read the "Analyst Ratings"
     card in the RH app (% Buy / Hold / Sell + RH aggregated target) or ask the user to paste it.
   - **Blend:** `blended_target = mean(Yahoo_mean, RH_target)`; direction = consensus of both
     rating sets. Flag upside/downside % = (blended_target / price − 1). If price > blended
     target → negative edge (the "above mean" flag).
3. **N — News:** `WebSearch` for "{TICKER} stock news {month year}" and "{company} WSJ
   MarketWatch latest". Pull the 3–5 freshest headlines; classify catalyst bull/bear/neutral;
   note any company event (earnings/upgrade/product/guidance).
4. **H — Historical analog:** Python on the 2y history — define the current pattern
   (regime + RSI bucket + %-vs-analyst-mean + recent move) and measure forward 2–4 wk returns
   of similar past instances (this name; optionally a comp). Report hit-rate + avg fwd move.
5. **M — Macro/government:** `WebSearch` for upcoming catalysts (Fed meeting, CPI date,
   USTR/tariff hearings, war/geopolitics, elections, sector regulation). Map to a window and
   score headline risk. Cross-check the macro gate in `trading_watchlist.md`.

---

## Output format (mirror this)

```
STNOW — {TICKER}  ${price} ({1d%})   {date/time}

P Price/Trend ...... {+/-N}  {one-line: regime, RSI, R:R}
A Analysts(blended)  {+/-N}  {Yahoo mean $X (n) + RH $Y → blended $Z; up/down %; rating}
N News ............. {+/-N}  {freshest catalyst + source}
H Historical analog  {+/-N}  {"similar setups: X% up, avg +Y% in 2wk"}
M Macro/Govt ....... {+/-N}  {next event + date; war/tariff/Fed risk}
─────────────────────────────
COMPOSITE: {sum}/10  →  {GO / WAIT / AVOID}
Macro veto: {none | capped at WAIT — event {name} on {date}}

Biggest risk: {one line}
Trigger to act: {the specific price/news condition}
Expression: {shares / STKK levels / Three Good spread / call debit — whichever fits}
```

## Rules

- **ASK before you score (Step 0).** Never assume account, entry basis, or intent. A
  confirmed IPO allocation + flip intent flips the action from "AVOID" to "sell the pop."
- **Run Step 0.5 ("Why is it cheap?") on any bargain-looking name** (DOWN / >20% off highs /
  RSI <40 / upside ≥ +35%). A fat discount to a **stale** target on an **unresolved** problem is
  a **value trap → cap at WAIT** until a dated catalyst confirms the turn. Never score lens A
  positive on a pre-event target.
- **Always show all 6 lens scores** — never collapse to a vibe. The number forces honesty
  (a high win-rate name can still be AVOID if analysts + macro are negative).
- **Say which question you're answering** — "don't BUY here" (open-market score) vs "what to
  do with shares you already hold / are allocated" (position management) are different answers.
- **News must be fresh** (cite date + source). Stale analyst means are a known trap — if
  targets are being revised hard (up or down), say so and down-weight the static mean.
- **Macro can VETO but not force a GO** — a clear calendar doesn't make a bad setup good.
- **End with one action**, not a menu. If WAIT/AVOID, state exactly what would change it.

## Output checklist

- [ ] Step 0 intake asked (account, entry basis, intent, exit goal, size) — nothing assumed
- [ ] Step 0.5 "Why is it cheap?" re-test run if the name is a bargain (DOWN/off-highs/oversold/big upside); lens A capped if target stale or cause unresolved
- [ ] IPO-allocation branch + account context applied if relevant
- [ ] All 6 lenses scored with one-line evidence each
- [ ] Yahoo + Robinhood analyst views explicitly blended (with n and rating)
- [ ] ≥3 fresh headlines pulled (WSJ/MW/wires) with dates
- [ ] Historical-analog backtest run (hit-rate + avg fwd move)
- [ ] Upcoming govt/macro catalyst named with date + risk window
- [ ] Composite score → single GO/WAIT/AVOID + macro-veto check
- [ ] Biggest risk + exact trigger + the expression to use
