# SSR-EQ — Equity (Shares) Strategy

_Companion to `options_watchlist.md`. This is the **shares sleeve** of the ~$50k account — a separate engine from the options income book. Different instrument, different drivers, different risk rules._

_Created: July 7, 2026. Regime read sourced from WSJ-adjacent + MarketWatch + ETF-flow reporting (see §1 citations)._

> **Disclaimer:** Personal trading notes, not advice. Prices/levels decay fast — re-pull the live quote before acting.

---

## 0. Why a separate stock engine (and how it differs from options)

| | Options book (`options_watchlist.md`) | **Equity book (this doc)** |
|---|---|---|
| Instrument | Defined-risk spreads | **Shares** |
| Horizon | 2–4 weeks to expiry | **Weeks to months (swing/position)** |
| Drivers | IV, theta, strikes, event gate | **Trend, relative strength, sector rotation, fundamentals** |
| Edge | Premium / IV-crush / probability | **Ride where institutional capital is actually flowing** |
| Current tilt | Tech-heavy (DELL/SNOW/AVGO/HPE) + XOM | **Financials / healthcare / energy / industrials / value → diversifies the whole account away from tech** |

**Account-level point:** because the options book is concentrated in tech, the equity sleeve should deliberately **underweight tech/semis/software** and lean into the rotation. That balances total-account exposure instead of stacking correlated tech risk.

---

## 1. Current regime read (the tilt) — dated & sourced

**As of July 7, 2026: a broad rotation OUT of Big Tech/semis INTO defensives + cyclicals + value/dividend.** Drivers: soft jobs data → ~76% odds of a July Fed hold, AI-capex fatigue, stretched tech valuations, index-rebalance flows normalizing.

| Quadrant | Sectors | Stance | Evidence |
|---|---|---|---|
| **LEADING (overweight)** | Financials, Healthcare, Industrials, Utilities, Energy, Materials, Staples | 🟢 Buy the leaders on pullbacks | Healthcare entered Leading; $3.3B into cyclical/sector ETFs ([kalkine](https://kalkine.com/news/premium/us-sector-momentum-analysis-health-care-enters-leadership-as-technology-falls-into-lagging), [ainvest](https://www.ainvest.com/news/semiconductors-run-unloved-sectors-haven-don-rotation-2607/)) |
| **BROADENING** | Small/mid-caps, S&P equal-weight, dividend/value | 🟢 Tailwind | Equal-weight best relative start since 1992 ([Sharecafe](https://www.sharecafe.com.au/2026/07/07/global-investors-eye-major-capital-rotation/)) |
| **LAGGING (underweight)** | Technology (XLK), Semiconductors (SMH/SOX), heavy-AI-capex Mag 7, software | 🔴 Avoid chasing; only relative-strength survivors | Tech into lagging quadrant; $2.2B tech-ETF outflow ([kalkine](https://kalkine.com/news/premium/us-sector-momentum-analysis-health-care-enters-leadership-as-technology-falls-into-lagging), [Disruption Banking](https://www.disruptionbanking.com/2026/07/06/the-dows-record-52900-close-hides-a-bigger-story-wall-street-is-rotating-away-from-tech/)) |
| **EXTENDED (caution)** | Biotech (IBB up 14 of 17 sessions) | 🟡 Don't chase; buy the pullback | [thestreet](https://pro.thestreet.com/market-commentary/2-types-of-rotation-are-driving-this-market) |

**Catalysts to watch:** **bank earnings Jul 14** (financials confirmation), FOMC minutes, SOX support level (tells us if the tech rotation is structural or a dip). Geopolitical oil supply risk (Ukraine refinery strikes, Qatar LNG force majeure) = energy tailwind ([Stock Market Watch](https://www2.stockmarketwatch.com/stock-market-news/market-rotation-and-global-geopolitical-shifts-tech-rally-fatigue-and-nato-summit-in-focus/64289/)).

**Regime verdict:** the trend is your friend and the trend is **broadening away from tech**. Trade with it.

---

## 2. The equity scorer (SSR-EQ) — adapted from STKK/STNOW/Whale

Shares have no IV/theta/strikes, so the models are re-cast into **five equity factors**. Each scores **−2 … +2**; sum → verdict.

| # | Factor | What it measures | +2 | −2 |
|---|---|---|---|---|
| 1 | **Trend (STKK-EQ)** | Price vs 50/200-DMA, higher-highs, RSI band | Above rising 50 & 200-DMA, RSI 50–70 | Below falling 50-DMA, RSI <40 |
| 2 | **Relative Strength** ⭐ | Stock vs SPX **and** vs its sector, 1–3 mo | Outperforming both, new relative high | Lagging both |
| 3 | **Sector rotation lens** | Is the name in a **Leading** sector (§1)? | Leading + inflows | Lagging (tech/semis/software) |
| 4 | **Quality/value (STNOW-EQ)** | Analyst trend, earnings revisions, valuation vs sector, FCF/dividend | Upgrades + reasonable multiple + FCF | Downgrades + rich multiple |
| 5 | **Catalyst/news** | Upcoming earnings, upgrades, sector catalyst | Positive catalyst in window | Negative overhang / earnings landmine |

**Verdict bands** (sum of 5 factors, −10 … +10):

| Score | Verdict | Action |
|---|---|---|
| **+6 to +10** | 🟢 STRONG BUY | Full starter (stage ½, add on hold) |
| **+3 to +5** | 🟢 BUY | Half-size starter |
| **0 to +2** | 🟡 WATCH | Alert only; needs a trigger |
| **< 0** | 🔴 AVOID / short-watch | No long |

**Relative Strength (factor 2) is the tie-breaker in a rotation regime** — in a broadening tape, "what's already leading tends to keep leading." Weight it heaviest when scores are close.

---

## 3. Candidate universe

**Primary = the saved scan `SSR-EQ Rotation Leaders`** (`scan_id cce44365-dc88-4aac-b082-c47452b7f81d`, on the Agentic account ••••1451). Re-run anytime with `run_scan`. Filters: **mkt cap ≥ $10B · avg vol ≥ 1M (30d) · price ≥ $20 · RSI(14) 50–70 · fwd P/E ≤ 30**. Returned **279 matches** on 2026-07-07.

> Note: your original web screeners (`50f12444…`, `13867ed5…`) are saved on your **personal margin account ••••5611**, which this agent can't access (`agentic_allowed=false`). This scan replicates a rotation-leader screen on the account I *can* trade.

**Top SSR-EQ scored names from the 2026-07-07 run** (sector lens applied manually; RSI/%chg/PE live):

| Rank | Ticker | Sector | Last | RSI | Fwd P/E | %chg | SSR-EQ | Note |
|---|---|---|---|---|---|---|---|---|
| 1 | **JPM** | Financials (bank) | $339 | 65 | 15.4 | +0.4% | **+7** | Jul 14 earnings catalyst; cheap |
| 1 | **ADP** | Industrials | $247 | 65 | 19.7 | **+3.0%** | **+7** | Strongest momentum today |
| 1 | **MET** | Financials (insurer) | $92 | 66 | **9.9** | +1.4% | **+7** | Deep value |
| 4 | **HCA** | Healthcare | $420 | 65 | 13.8 | +0.7% | **+6** | Cheap hospital operator |
| 4 | **ELV** | Healthcare | $417 | 57 | 15.2 | +2.1% | **+6** | Room on RSI |
| 4 | **LNG** | Energy | $255 | 57 | 16.1 | +3.6% | **+6** | (energy already via XOM options) |
| 7 | **UNH** | Healthcare | $425 | 59 | 22.9 | +1.7% | **+5** | Turnaround, huge liquidity |
| 7 | **WFC** | Financials (bank) | $87 | 67 | 12.4 | −0.3% | **+5** | Cheap; Jul 14 catalyst |
| 7 | **WM** | Industrials (defensive) | $237 | 62 | 27.7 | +3.6% | **+5** | Pricey but strong |
| 7 | **KO** | Staples | $84 | 58 | 25.4 | +1.3% | **+4** | Pure defensive |

**Featured diversified starter basket (≤35%/sector cap):** JPM (bank) · UNH (healthcare) · ADP (industrials) · KO (staples) — spans 4 leading sectors, zero tech overlap with the options book.

**Regime shortlist (sourced, to validate with the scorer — do NOT buy blind):**

| Sector | Names the sources flag | Note |
|---|---|---|
| Energy | **XOM, CVX, COP** | Named for dividend safety / yield / value+growth; oil supply-risk tailwind. (You're already long XOM via options.) |
| Financials | Big banks (JPM/GS/BAC/WFC/C) | **Jul 14 earnings** = the confirmation catalyst |
| Healthcare | XLV leaders; biotech IBB (extended) | Healthcare entered Leading; biotech overbought → wait for pullback |
| Industrials / Materials | XLI / XLB leaders | Cyclical rotation beneficiaries |
| Broadening | S&P equal-weight (RSP), dividend/value | Structural tailwind, low-maintenance core |

---

## 4. Entry rules (shares)

1. **Buy leaders on pullbacks that HOLD, never chase a gap** (the GOOGL +4.8% skip lesson — a 4.8% gap already paid out the move).
2. **Stage in:** ½ position on the trigger, add the other ½ on a confirmed hold (higher low, or reclaim of a moving average).
3. **Trigger = a reclaim/hold, not a fresh breakout into resistance.** Prefer buying strength that's catching its breath.
4. **Sector-first:** prioritize Leading-sector names (factor 3 = +2) over lagging-sector "cheap" names.
5. **No buying below a falling 50-DMA** — that's a knife, not a pullback (the CRM falling-knife rule).

---

## 5. Risk management (different from options)

- **Sleeve size:** propose **$15k of the ~$50k** as the shares sleeve (confirm below). Keeps options collateral (~$8.8k tied up now) + dry powder intact.
- **Position size:** ≤ **8% of the sleeve per name** (~$1,200 starter), max **10 names**.
- **Per-name risk cap:** stop distance × shares ≤ **2% of the sleeve** (~$300). Size the share count off the stop, not the other way around.
- **Hard stop:** the **worse** of −8% from entry **or** a daily close below the 50-DMA (trend break).
- **Portfolio caps:** ≤ **35% in one sector**; **run a correlation check vs the options book** — the equity sleeve should tilt AWAY from tech to offset DELL/SNOW/AVGO/HPE.
- **Earnings:** shares survive earnings (no hard event gate like options), **but trim extended names into the print** and never add right before it.

---

## 6. Profit-taking / exits (let winners run — opposite of the options book)

- These are **trend/position trades**, so don't scalp the quick +50%. **Scale out:** sell ⅓ at **+15%**, ⅓ at **+25%**, **trail the rest** with a rising 50-DMA / a −10% trailing stop.
- Raise stop to **breakeven after +8%**.
- **Exit the thesis, not just the price:** if the rotation reverses (tech reclaims leadership, SOX breaks back out, financials fail Jul-14 earnings), cut the rotation-beneficiary names even if not stopped.

---

## 9. 📝 PAPER TRADES — SSR-EQ v1 basket (opened 2026-07-07)

_Validating the rotation-leader engine before real capital. Entries at live prices ~12:08 PT Jul 7. Sizing TBD (default plan: ~8% of sleeve each, equal-weight, 5 names ≈ 40% deployed). Tracked on **% return** until sleeve $ is set. Stops = worse of −8% or a daily close below the 50-DMA. Targets = scale ⅓ at +15%, ⅓ at +25%, trail the rest._

| Ticker | Sector | Entry | Stop (−8%) | T1 (+15%) | T2 (+25%) | SSR-EQ | Thesis |
|---|---|---|---|---|---|---|---|
| **JPM** | Financials · bank | $338.91 | $311.80 | $389.75 | $423.64 | +7 | Cheap bank (P/E 15), **Jul 14 earnings catalyst**, RSI 65 uptrend |
| **UNH** | Healthcare | $425.06 | $391.05 | $488.82 | $531.33 | +5 | Beaten-down managed-care turnaround, +1.7% on a red tape, deep liquidity |
| **ADP** | Industrials | $246.48 | $226.76 | $283.45 | $308.10 | +7 | Strongest momentum today (+2.9%), quality compounder, RSI 65 |
| **KO** | Staples | $84.07 | $77.34 | $96.68 | $105.09 | +4 | Pure defensive rotation anchor, low beta, dividend |
| **MET** | Financials · insurer | $91.60 | $84.27 | $105.34 | $114.50 | +7 | Deep value (P/E 9.9), RSI 66; **note: 2nd financials name → on live money pick JPM _or_ MET, not both (35%/sector cap)** |

**Basket logic:** 4 leading sectors (financials/healthcare/industrials/staples), **zero tech overlap** with the options book → diversifies the whole account. MET tracked as a 5th to compare bank vs insurer within financials.

**Grade at:** Jul 31 checkpoint + on any stop/target hit. Compare live path to the scorer's ranking to see if SSR-EQ predicts winners.

---

## 9b. 💵 LIVE POSITIONS — agentic account ••••1451 (real money)

| Ticker | Opened | Qty | Avg cost | Cost | Stop | Targets | Resting orders | Thesis |
|---|---|---|---|---|---|---|---|---|
| **XE** ⭐ | 2026-07-17 | **34.746 sh** | **$14.39** | ~$500 | mental line: **daily close < ~$12** (fresh low = base thesis broken; reassess, don't ride to $8) | **GTC sell 34 sh @ $16.50** (+14.7%, ~+$72) + 0.746 sh runner kept for the $37 PT tail | **GTC limit sell 34 sh @ $16.50 · GTC** (placed 7/17) | **Cathie Wood nuclear conviction play.** Amazon-backed SMR/nuclear-fuel developer; ARK accumulating daily (507K sh 7/16, ~$15M/wk across ARKK/ARKQ/ARKX). Analyst Buy, PT $37.86 (+168%). ⚠️ **Pre-revenue** (−$546M net loss, EPS −$24.87) → venture/lottery sizing. Bought near 52-wk low ($13.29) into a nuclear-group relief bounce (group green 7/17 after −8% 7/16). **Size caveat logged: $500 = ~50% of the $1k sleeve, well above the 15%/$150 venture cap — user's explicit conviction call, flagged at entry.** |
| ~~GOOGL~~ | 2026-07-07 | ~~2.000 sh~~ | ~~$366.17~~ | — | — | — | — | ✅ **CLOSED 7/15 — sold 2 sh @ $372** (~+$28 / +1.4% recycle target hit). Sleeve returned to cash. First live SSR-EQ trade; clean recycle win. |

**Sleeve state (7/17):** ~$500 in XE (34.746 sh @ $14.39), ~$500 dry powder on ••••1451. XE is ~50% of the sleeve — concentrated in one pre-revenue spec name; the GTC $16.50 harvests +$72, the runner keeps the re-rate tail. No adds unless XE confirms a base >$16 or dips to a scale-in level with the group stabilizing.
**Note (small-account sizing):** the §5 "≤8%/name" rule assumes a ~$15k sleeve; on a **$1k** sleeve that's $80 (< 1 share of most names), so it doesn't scale — practical reality is **1–2 names at a few hundred each**, keep a cash buffer (same small-account lesson as options sizing).

---

## 7. Process / cadence

- **Weekly (weekend):** re-pull the sector-rotation read; re-rank the screener universe with the SSR-EQ scorer; update this doc's watch table.
- **Daily (open):** check triggers on WATCH names; act only on holds, not chases.
- **Event-driven:** re-score around Jul 14 bank earnings + FOMC minutes.
- **Log outcomes** in `agent_learning_log.md` (same loop as options).

---

## 8. What I need from you to produce actual ranked picks

1. **The two screener ticker lists** (paste text or screenshot) — this is the universe I score.
2. **Confirm the sleeve size** — default **$15k**; tell me if you want more/less.
3. **Horizon** — default **swing/position (weeks–months)**; say if you want shorter momentum or longer buy-and-hold.
4. **Income tilt?** — do you want a dividend/value skew, or pure relative-strength momentum?

Give me those and I'll run the scorer live, rank the universe, and hand back a ranked buy list with entries/stops/targets — same format as the options cards.
