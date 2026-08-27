# Momentum Watchlist & Discovery Screen

> **FULLCHECK — Tue Aug 25 ~5:15 PM PT:** INTU beat-and-dump **AH ~−10%** (FY27 9–10% guide) — **arm 320/310 put debit** for Wed first 15–30, cap $4.00. ZM secondary put. DKS miss **kill** (clock gone). PCE 8:30 then NVDA/CRWD/CRM AMC — **no new credit**. SMCI **+9.4%** = do not chase T+1. FFTY top-25 still healthcare/fintech (HNGE/TER/OSCR/KNSA/ENVA/NTRA as of 8/13 holdings). XLK/XLC led; XLE lagged. Live = **MS manage** (cushion 3.1%).

> **Prior FULLCHECK — Thu Aug 20 ~11:22 ET:** HOOD 85/80 ×3 **closed +$198** at the 9:30 GTC. DE/WMT killed (first 30 missed). Live = **MS manage** (cushion 1.2%, abort $210 / mid ≥ $4.50). Tonight arm **BJ** Fri BMO (WMT −9% is the bellwether). XLE +1.25% still leads; XLY/XLP follow WMT. Do not chase MARA +10%, MRVL T+1, or COST. Write-up: `/Users/koteswararao.venkata/Documents/Cursor/Documents/fullcheck_2026-08-20.md`.

_Created July 9, 2026. **Purpose: close the discovery gap that let ALAB (+376% in a year) stay invisible.** This file is the market-wide momentum layer — the leaders that DON'T live in MANGOS / the semis-10 / the whale watchlist. Refreshed by the strategy-battery loop (momentum-discovery step) and re-screened weekly._

> **Why this exists:** the agent was scanning a hardcoded 10-name semis list + MANGOS, so multi-month 2–3x movers outside those buckets (ALAB, SNDK, WDC, STX, PENG, LITE, CIEN, Bloom) never surfaced. The fix = screen the whole momentum factor, not a fixed list.

---

## ⚡ Command: `FULL CHECK` (a.k.a. fullcheck)

**The everything-command.** Runs the complete 12-step battery on demand (same engine as the 8/11/1 loop): tape/macro → cross-sector gate → book health check → **Health Check** 4-model composite → event gate → STKK/STNOW/Three Good → **Whale Watch** → **SelfIDB50** → WSJ/MW → IV-matrix routing → **backtest new structures** → ranked plan (🟢 take / 🟡 arm / 🔴 stand-down), options-book vs $1k sleeve. Full spec in `trading-continuous-learning/SKILL.md`. **Read-only by default** — surfaces action tickets, waits for the user's go. `SelfIDB50` below is the momentum-discovery slice inside it.

## ⚡ Command: `SelfIDB50` (a.k.a. selfidb50, Self-IDB-50)

**Trigger:** user types `SelfIDB50` / `selfidb50` (any casing). = the self-serve, no-login replacement for IBD's paywalled lists. Run it end-to-end, no manual paste required:

1. **FFTY holdings** — fetch `https://stockanalysis.com/etf/ffty/holdings/` (public IBD-50 proxy). Grab the full ~50-name holdings.
2. **Own RS screen** — pull the `rs_screen.py` universe via `get_equity_historicals` (start 3mo back, interval=day), then `python3 rs_screen.py <dumps>` → rank by 3-month return + %-from-high (anti-chase) + 1-month momentum.
3. **Top-gainers web check** — search "best performing stocks YTD 2026" as cross-check for names outside the fixed universe.
4. **Apply the full battery** to the merged/deduped candidates: earnings gate (before next expiry?) → concentration cap (no 4th correlated semi) → anti-chase parabolic gate → correlation-to-book → option liquidity.
5. **Output** — a ranked cross-sector shortlist (prefer non-tech diversifiers when the book is tech-heavy), each with sector, gate, IV-routed structure, and take/arm/stand-down label. Update this file's shortlist + universe.

_Validated Jul 9 2026: FFTY had ALAB #1; the RS screen ranked ALAB #1 (+212% 3mo) with zero IBD input._ If the user also pastes fresh IBD lists, merge them in as an extra (higher-signal) source.

---

## 🔄 Aug 8 (Sat) refresh — SelfIDB50 + real IBD lists merged

**Regime call: leadership rotated OUT of AI-hardware INTO healthcare + financials.** Confirmed three independent ways.

**1. FFTY (IBD-50 proxy) top-25 flipped.** In July it was ALAB/AI-hardware top to bottom. As of Aug 6 the top 25 holds only **two** tech names (DDOG #18, NET #23). #1–#14 = fintech, pharma, biotech, regional bank, consumer, shipping. FFTY itself closed **−0.84% Fri while SPY +0.60%** — growth momentum lagged the index.

**2. My own RS screen agrees** (weekly bars + daily tail through Fri Aug 7, 50 names):
LQDA +113% · AGL +76% · GH +76% · DELL +74% · HPE +70% · SN +66% · NTRA +66% · HALO +61% · NET +53% · ENVA +44%. Six of the top ten are non-tech.

**3. The real IBD 50 (user paste, 8/7) confirms it.** Healthcare/diagnostics = 12 of 50; financials/fintech = 11 of 50 → **46% combined**. Tech is 32% but IBD frames it as *"bouncing from the chip sell-off"* / *"setting up in bases"* — repair, not leadership.

### ✅ SelfIDB50 validation vs the real list
Third clean validation of the self-serve flow. **My RS screen ranked LQDA #1 with zero IBD input — LQDA is IBD 50's actual #1.** (Prior: ALAB #1 on Jul 9.) ~16 of FFTY's 25 names appear on the real IBD 50: KNSA #2, ENVA #8, CARE #10, GKOS #13, SN #14, VCTR #15, EXPE #20, SKWD #22, ECO #23, STT #24, NET #28, LLY #29, PAY #38, HWM #40, MS #46.

### ⚠️ Structural blind spot found — FFTY paywall
stockanalysis.com shows only **25 of FFTY's 53 holdings**; 26–53 are subscriber-gated. So the proxy has a **~50% blind spot**, and it cost real names this run:
- **Healthcare diagnostics cluster missed entirely** — NTRA (#5, +21.4% Fri), HALO (#12, +20.2%, record high), GH (#6), URGN (#9), HNGE (#11), ADPT (#25), LGND (#32), DXCM (#43)
- **Copper missed entirely** — ERO (#16, +10.3% Fri, also Sector Leader #21), SCCO (#34)
- **Semi-repair names missed** — SITM (#3), CRDO (#7), TER (#19), APH (#31, Sector Leader #3)

**Fix applied:** these names added to the `rs_screen.py` universe. **Mitigation going forward:** treat FFTY top-25 as a *starting* signal only; always pair with the RS screen on a widened universe, and ask the user for an IBD paste when one is available — it materially outperformed the proxy this run.

### ⚠️ Second blind spot — ENERGY was cut from the universe entirely
Caught by the user, not by the process. When the universe was trimmed 49 → 40 names to save data cost, XOM/CVX/COP were dropped and only TRGP survived — energy held **1 of 40 slots**. Compounding it, energy was written off on a *single day's* sector tape (XLE −1.14% Fri, worst sector). The one-month numbers say the opposite:

| Window | Energy reads |
|---|---|
| 1-month | OXY +14.3% · COP +12.3% · SLB +12.0% · MPC +12.0% · VLO +11.4% · CVX +10.3% — **every oil name up double digits** |
| 3-month | **VLO +23.7% · MPC +21.8%** — refiners are the real leaders; both only 7–9% off highs |

**Rule added: never exclude a sector on a one-day ETF print.** Sector tape is a same-day tell, not a leadership read; leadership needs the 1mo/3mo RS window. XLE is also ~40% XOM+CVX, so it says little about refiners.

**Nuclear ≠ energy leadership.** Last week's fireworks (XE +39%, OKLO +25%, SMR +16%, CCJ +14%) are a bounce inside broken charts — XE −25% / OKLO −33% / SMR −22% / CCJ −17% over 3 months, all 20–39% below highs. That is the ORCL profile the backtest already disqualified. CCJ **FAILS** the breach test outright (29% breach over 21 windows). Do not sell puts into these.

**XE (X-energy — Xe-100 reactors + TRISO fuel) fails every gate at once:** −33.8% from high, +31% in a month (anti-chase), earnings **Thu 8/13** before any near expiry, ~120% IV. Highest-risk configuration on the board — not a buy, and the existing $12.50 short put should still be closed.

**Data-quality bug found while fixing this:** Robinhood returned XOM with **21 of 26 weekly bars interpolated**, so `close_on_or_before` silently fell back to the oldest clean bar and reported a 35-day window as a "3-month return." `rs_screen.py` now prints the true lookback and flags anything under 60 days. XOM's RS number this run is unusable; XE's (15/26 clean) is directionally OK.

### 🎯 Aug 15 FULLCHECK overlay (weekend → Mon 8/17)

Friday close: **XLE +1.39%** still leads 11 GICS; XLK/XLV last. FFTY top-25 unchanged (HNGE/TER/healthcare-fintech as of 8/11) — tape and the IBD proxy still disagree. **Do not chase SNDK T+2, AMD +6.5% T+1, or TER on an AMAT hangover.** Live diversifier remains energy: **XOM Sep 160/165 call debit** if Monday holds ~$159.30. XE/U/HPE are not Monday tickets (dump / extended+bearish / structure+event fail). FN Mon AMC is the catalyst-day debit.

### 🎯 Aug 14 FULLCHECK overlay

Tape rotated: **XLE +1.5%** leads, SMH −0.8%, AMAT −5.2% after a beat. FFTY still healthcare/fintech (HNGE/TER/KNSA/ENVA/NTRA). **Do not chase SNDK T+1 or AMAT dump.** Energy is the live diversifier — **XOM Sep 160/165 call debit** armed for Monday, not Friday. TER (#2 FFTY) is ATE; do not buy it on an AMAT dump day. MARA put-credit GO remains overridden (long shares).

### 🎯 Aug 13 FULLCHECK overlay

Tape = chips/memory (SMH +1.6%, SNDK +15%, WDC +8%). FFTY still healthcare/fintech. **Do not chase SNDK/SMCI/HPE/DELL today.** Preferred non-tech arm = **MPC call debit** (IV ~40%, earn 11/3). NVDA Aug21 225/230 debit only ≤$1.80 (mark $2.06). ORCL put-credit killed (STKK downtrend). MARA: close the $10.50C, do not sell puts on the shares.

### 🎯 Merged shortlist (gate-clean · liquid options · not parabolic)
| Rank | Name | Sector | RS (3mo/1mo/from-high) | Gate | Route | Call |
|---|---|---|---|---|---|---|
| 1 | **LLY** | Pharma | +25% / −2% / −5% | ✅ reported 8/5, next 10/29 | **IV only 34%** → low-IV = call debit, NOT premium selling | 🟢 best non-tech diversifier; IBD 50 #29 + Sector Leader #9 |
| 2 | **DELL** | Tech hardware | +74% / +15% / −7% | ✅ next **9/3** | IV **80%** — $410/$400 Aug21 pays $2.30/$10 but cushion is only **0.62× expected move** | 🟡 **arm, don't fire** — best momentum, worst option math |
| 3 | **HPE** | Tech hardware | +70% / +29% / −17% | ✅ next ~9/2 | rich IV → put credit | 🟢 confirmed from Fri plan |
| 4 | **EXPE** | Travel/consumer | +35% / +16% / −6% | ✅ reported | route on live IV | 🟢 new diversifier, IBD 50 #20 |
| 5 | **ERO / SCCO** | Copper | ERO +21% / **+31%** / −0.1% | ✅ | ERO at highs → arm | 🟡 brand-new theme; SCCO is the liquid way to play it |
| ➕ | **MPC** | Refining (energy) | +21.8% / +12.0% / −8.8% | ✅ reported **8/4**, next 11/3 | IV 40% → put credit; Sep18 $270/$260 ≈ $1.85–2.00 credit | 🟢 **best backtest on the board** — 0/21 breach, worst 6-wk −3.4% vs −9.5% cushion, zero event risk to expiry |
| ➕ | **VLO** | Refining (energy) | **+23.7%** / +11.4% / −6.8% | ✅ reported **7/30**, next 10/22 | same route; $270/$260 ≈ $1.30–1.50 | 🟡 same setup, but short $270 quotes $4.50/$5.80 (**25% wide**) — MPC is the cleaner fill |

**At-highs / anti-chase (arm only):** SN (−1.1% from high), NTRA (−0.3%), HALO (−0.2%), ERO (−0.1%), GKOS (−2.2%), LQDA (−1.5% **and earnings 8/12 → 🔴 gated**).

**Broken — do not sell puts into these:** SEZL (FFTY's #1 holding, **−34% in one day Fri**, −40% from high), SNDK (−48% from high), MXL (−42%), ORCL (−41%), COIN (−31%), DAVE (−31%), AGX, RSI.

### 📋 FULL IBD ROSTER — captured 8/7/2026 close (user paste)

_Source of truth for the week. `RS` columns are from my own screen (weekly bars + daily tail through Fri 8/7); blank = not yet in the screen universe. **Liquidity column is VERIFIED ONLY where I actually pulled the chain** — everything marked `?` must be checked before it becomes a trade (NTAP looked investable on price and failed badly on chain depth)._

#### IBD 50
| # | Sym | Sector | Price | Fri% | RS 3mo | RS 1mo | From hi | Opt liq | Note |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **LQDA** | Pharma | 90.22 | +0.89 | **+113%** | +14% | −1.5% | ? | 🔴 **earnings 8/12** · my screen's #1 too |
| 2 | **KNSA** | Biotech | 76.06 | +0.59 | +30% | +18% | −8.3% | ? | |
| 3 | **SITM** | Semis | 725.28 | +5.50 | −13% | +21% | −20% | ? | Violent — 519→725 in a week |
| 4 | **ATI** | Aerospace | 227.84 | +1.97 | — | — | — | ? | Earnings breakout w/ HWM |
| 5 | **NTRA** | Diagnostics | 322.10 | **+21.4** | +66% | +15% | −0.3% | ? | 🟡 at highs post-print |
| 6 | **GH** | Diagnostics | 168.48 | +6.92 | **+76%** | +0.3% | −4.6% | ? | |
| 7 | **CRDO** | Semis | 249.89 | +8.45 | +33% | +3% | −19% | ? | IBD entry 308.67 (late-stage base) |
| 8 | **ENVA** | Fintech | 252.64 | +1.30 | +44% | +7% | −4.9% | ? | |
| 9 | **URGN** | Pharma | 46.96 | +2.98 | — | — | — | ? | |
| 10 | **CARE** | Regional bank | 33.00 | +2.65 | +25% | −0.4% | −8.5% | ? | |
| 11 | **HNGE** | Digital health | 89.33 | +11.55 | — | — | — | ? | |
| 12 | **HALO** | Biotech | 103.12 | **+20.2** | +61% | +30% | −0.2% | ? | 🟡 record high |
| 13 | **GKOS** | Medtech | 180.02 | +5.28 | +35% | +21% | −2.2% | ? | 🟡 at highs |
| 14 | **SN** | Consumer | 185.52 | +3.11 | +66% | +23% | −1.1% | ? | 🟡 at highs |
| 15 | **VCTR** | Asset mgmt | 108.16 | +1.28 | — | — | — | ? | |
| 16 | **ERO** | Copper | 34.31 | +10.32 | +21% | **+31%** | −0.1% | ? | 🟡 new theme, at highs |
| 17 | **WT** | Asset mgmt | 21.25 | +1.07 | — | — | — | ? | |
| 18 | **OUST** | Lidar | 43.40 | +4.78 | — | — | — | ? | |
| 19 | **TER** | Semi equip | 379.31 | +1.45 | +5% | +3% | −22% | ? | IBD cup base, entry 487.91 |
| 20 | **EXPE** | Travel | 310.68 | +1.34 | +35% | +16% | −6.2% | ? | 🟢 shortlist |
| 21 | **XMTR** | Industrial tech | 93.15 | +6.95 | — | — | — | ? | |
| 22 | **SKWD** | Insurance | 63.67 | +2.99 | — | — | — | 🔴 thin (Jul) | Sector Leader · entry 63.03, zone→66.18 |
| 23 | **ECO** | Tankers | 61.86 | +3.01 | +10% | +17% | −3.7% | ? | |
| 24 | **STT** | Financials | 184.68 | +0.13 | — | — | — | ? | |
| 25 | **ADPT** | Diagnostics | 24.93 | +5.64 | — | — | — | ? | |
| 26 | **ZETA** | Ad tech | 26.64 | +4.23 | — | — | — | ? | |
| 27 | **SNOW** | Software | 330.49 | +3.93 | — | — | — | 🟢 traded before | |
| 28 | **NET** | Software | 300.27 | +5.57 | +53% | +24% | −7.5% | ? | Fri reversal: hi 324.73 → close 300.27 |
| 29 | **LLY** | Pharma | 1185.71 | +0.52 | +25% | −2% | −5.1% | 🟡 wide | 🟢 **call debit — see ticket** |
| 30 | **CGNX** | Machine vision | 66.89 | +0.73 | — | — | — | ? | |
| 31 | **APH** | Components | 169.18 | +0.84 | +32% | +3% | −5.2% | ? | Sector Leader #3 |
| 32 | **LGND** | Pharma | 293.15 | +2.33 | — | — | — | ? | |
| 33 | **GRMN** | Consumer tech | 310.89 | +2.99 | — | — | — | ? | |
| 34 | **SCCO** | Copper | 199.06 | +3.12 | +7% | +16% | −2.0% | ? | Liquid way to play copper · entry 221.67 |
| 35 | **ATEYY** | Semi equip ADR | 206.66 | +0.38 | — | — | — | 🔴 ADR | |
| 36 | **NAVN** | Travel tech | 29.08 | +4.38 | — | — | — | ? | |
| 37 | **NTAP** | Storage | 189.52 | −1.02 | — | — | — | 🔴 **VERIFIED THIN** | $175P 1.40/2.00, OI 60, vol 1 → **reject** · buy pt 192.83 · ER 9/2 |
| 38 | **PAY** | Fintech | 38.57 | +3.86 | — | — | — | ? | |
| 39 | **RBRK** | Software | 90.07 | +6.47 | — | — | — | ? | |
| 40 | **HWM** | Aerospace | 281.88 | +2.66 | +4% | +4% | −9.1% | ? | Big Cap 20 · **buy zone 280.74→294.77** |
| 41 | **CPAY** | Fintech | 392.94 | +1.34 | — | — | — | ? | |
| 42 | **MGNI** | Ad tech | 24.72 | +1.64 | — | — | — | ? | |
| 43 | **DXCM** | Medtech | 84.75 | +2.08 | — | — | — | ? | |
| 44 | **FLYW** | Fintech | 17.78 | +2.31 | — | — | — | ? | |
| 45 | **S** | Cyber | 21.40 | +3.08 | — | — | — | ? | Whale 8/7: $160K sweep 2,000× Aug21 $19C |
| 46 | **MS** | Financials | 216.33 | +1.21 | +12% | +1% | −6.9% | 🟢 good | 🟢 **Mon ticket** |
| 47 | **FIVE** | Retail | 244.37 | +5.73 | — | — | — | ? | |
| 48 | **NTRS** | Financials | 185.50 | +0.74 | — | — | — | ? | |
| 49 | **BURL** | Retail | 368.96 | +0.59 | — | — | — | ? | |
| 50 | **IOT** | Software | 40.88 | +6.96 | — | — | — | ? | |

#### IBD Sector Leaders (the most stringent screen — 33 sectors)
| Sym | Rank | Price | Fri% | EPS% | Sales% | Note |
|---|---|---|---|---|---|---|
| **APH** | 3 | 169.18 | +0.84 | 67 | 55 | Highest-ranked leader |
| **LLY** | 9 | 1185.71 | +0.52 | 33 | 48 | 🟢 on our shortlist |
| **SKWD** | 11 | 63.67 | +2.99 | 46 | 27 | Insurance sector head · Uber partnership |
| **ERO** | 21 | 34.31 | +10.32 | 80 | 74 | Copper |
| **PAYS** | 23 | 12.48 | +0.65 | 450 | 48 | Micro-cap — watch only |
| **WT** | 23 | 21.25 | +1.07 | 72 | 57 | |

#### IBD Big Cap 20 + list-move news (8/5–8/7)
- **HWM** in focus — Composite 98, +43% YTD, Q2 EPS +46% to $1.33 (est $1.24), rev +24% to $2.55B; gas-turbine sales **+38%** on datacenter power demand. **Buy point 280.74, zone to 294.77 — actionable now** at 281.88.
- **NVDA** added to Big Cap 20, above its latest buy point.
- **PLTR** +39% on the week, led 27 names onto best-stock lists.
- Also cited at record highs: **DELL**, JPM, PAY.

#### 🥤 CELH (Celsius Holdings) — WATCH ONLY, not a leader
Not on the IBD 50, not on Sector Leaders, not on Big Cap 20, not in FFTY's top 25 — **zero of four lists.** My RS screen ranks it **45th of 50: −14.0% 3mo, −16.3% 1mo, −18.8% from high**, RSI 46.7.
- **Earnings 8/6 AM: MISSED** ($0.36 vs $0.43 est) — first miss after four straight beats. Next report ~**11/5** → gate clean for all Aug/Sep expiries.
- Tape: 8/5 close $29.15 → 8/6 close **$23.77 (−18.5%)** → 8/7 close **$27.77 (+16.8%)**. Still **−4.7% vs pre-earnings**.
- A +16.8% day is multiples of its ATR → **anti-chase = automatic stand-down.**
- **Only defensible structure:** put credit with the short strike **below the 8/6 low of $23.55**, and only after CELH **holds above ~$27 for 2–3 sessions**. At a $27.77 share price the premium is thin — poor use of collateral vs the rest of the board.
- 🟡 **Verdict: arm, don't fire.**

#### 🔧 HON (Honeywell) — TRACKED, blocked on chain depth only
Not on any IBD list, but tracked by request. **The thesis is fine; the chain is the blocker.**
- **Spot $246.21** (8/7) · RSI **56.4** · IV **42%** · RS screen **+10.2% 3mo / −0.4% 1mo / −17.2% from high** — mid-pack, constructive, well off its high so there's room, but no thrust.
- **Earnings 7/23 already reported** (big beat: $4.52 vs $2.42 est). Next ~**10/22** → **gate clean for every Aug and Sep expiry.** This is HON's main advantage: a long, clean runway.
- 🔴 **Rejected 8/7 on liquidity** — Aug 21 puts quoted **$0.85 bid / $3.00 ask**. A 112% spread means you surrender more to the market maker than the trade earns. Same failure mode as NTAP.
- Sector fit: industrial/aerospace — a genuine **non-tech, non-healthcare diversifier**, which is scarce right now. Worth the re-check.
- **Re-check trigger (any Monday or post-CPI scan):** pull the Aug 21 / Sep 18 put chain and require **bid/ask within ~10% of mark** and **OI in the hundreds**. If it tightens, route as a put credit (IV 42% is mid-range → sell, but only on a hold, per the IV matrix). If it stays wide, HON is a **stock-only or no-trade name** — do not force an options structure onto a broken chain.
- 🟡 **Status: tracked, not actionable.** Re-verify chain before every consideration; never re-reject from memory.

#### ⚠️ Liquidity discipline (the NTAP/HON lesson)
Price and market cap do **not** predict chain depth. NTAP is a ~$38B name at $189/share and its Aug 21 $175 put quoted **$1.40/$2.00 on 60 open interest and 1 contract of volume** — a 35% spread. HON failed the same way on 8/7. **Rule: pull the actual chain and require a bid/ask inside ~10% of mark, OI in the hundreds+, and non-trivial volume, before any name on this roster becomes a ticket.**

### 🔴 ORCL reframe — correction to the Fri Aug 7 plan
The RS screen ranks **ORCL dead last: −25% over 3 months, −41.3% below its 3-month high.** Friday's plan called it a healthy uptrend off RSI 56.7. That was wrong — RSI 57 there is a bounce off a deep hole, not trend. The $135/$130 put credit can still pay (it only needs ORCL above $135), but the correct framing is **selling a washed-out base, not trend continuation** — so size smaller and abort on a close back below $138 rather than riding it.

---

## 🔍 Discovery method (run every strategy-battery tick)

Screen the **whole market** (not a fixed list) four ways, then keep the overlap:
1. **IBD lists (curated RS+fundamentals):** IBD 50 (flagship growth) + IBD Big Cap 20 (large-cap, best option liquidity) + optional Sector Leaders. Best signal when the user pastes them, **but NOT required** — see the self-serve fallback below. These are the highest-signal starting universe when fresh.

   **🔁 SELF-SERVE FALLBACK (no IBD paste needed — the agent can run this alone):**
   - **FFTY holdings** = free public IBD-50 proxy → `https://stockanalysis.com/etf/ffty/holdings/` (also Yahoo/TipRanks). _Validated Jul 9 2026: **ALAB was FFTY's #1 holding** — reading this alone catches the leaders._
   - **Own RS screen** (fully independent, most robust): pull the ~50-name cross-sector universe in `rs_screen.py` via `get_equity_historicals` (start 3mo back, interval=day), then `python3 rs_screen.py <dumps>` ranks by 3-month return + %-from-high (anti-chase) + 1-month momentum. _Validated Jul 9 2026: **this screen ranked ALAB #1 at +212% 3mo with zero IBD input.**_
   - **Web top-gainers** cross-check: search "best performing stocks YTD 2026" (StatMuse/Barchart/Finviz).
   - ⚠️ The official IBD lists are login-gated — WebFetch can't authenticate, so don't rely on scraping them. Use FFTY + own RS screen instead.
2. **Top YTD / 3-month gainers** — the names up the most (web: StatMuse/CSIMarket "best performing stocks YTD", or a Robinhood top-gainers scan).
3. **Relative-strength leaders** — outperforming SPX over ~3–12 mo (MTUM factor; names making 52-wk highs).
4. **Fresh catalyst + volume** — earnings blowouts, deal news, sector supercycle, with volume ≥ OI / above-average.

**Prefer non-tech survivors** when the book is already tech/semi-heavy — the IBD lists skew tech, so a name passing the gate that's in aerospace/healthcare/energy/consumer is worth more than a 4th correlated chip.

Cross-check each survivor against the **event gate** (earnings before expiry?) and the **IV-routing matrix** before it becomes a trade.

---

## 🚦 Anti-chase rule (parabolic gate — apply to EVERY momentum name)

A momentum name is **STAND-DOWN / arm-only** (do NOT sell premium into it or buy it) — **regardless of share price** — if **any two** are true:
- up **> 1 ATR (>~4%)** on the day (spiking, not basing),
- **RSI > 70** or making a fresh intraday high,
- **short-strike cushion < 1× the expected move** to expiry.

**Share price ($1,935 SNDK vs $85 PENG) and single-day % are NOT principled disqualifiers** — extension %, RSI, and cushion-vs-expected-move are. On 100–120% IV names, the expected move usually **exceeds** any cushion that still pays a real credit → that's the tell to arm-for-pullback, not fire.

**Trade momentum the disciplined way:** sell the put credit on a **pullback that HOLDS** (red→green reclaim or a 2–3 day base), when IV is still rich but price isn't vertical. Or take **shares** on the pullback for the $1k sleeve.

---

## 🔄 Jul 27 (Mon AM) FULLCHECK — regime refresh

**Catalyst:** WSJ — NVDA talks to finance/guarantee ~$250B OpenAI data-center buildout → **AI circular-financing scare**. NVDA −5%, AMD −8%, SMH −3%, MU −6%.

**Leadership today (cross-sector gate):** **XLP · XLV · XLY · XLF** (defensive + payments). **GOOGL / MSFT / V** green as “real cashflow” vs vendor-financed AI. Energy (XLE) faded; power (VST) sold hard.

**Momentum stand-downs:** entire semi/AI-hardware stack (NVDA/MU/AMD/AVGO/SMH/ARM) — event-gated (ARM Wed) + anti-chase into selloff (don’t buy the knife; don’t sell puts into it either). **U** ripping +7% into Aug 6 earnings → shares-only, no CC.

**Shortlist for income (post-GS abort):** **JNJ** (XLV leader, clean gate to Oct) · **MS** (XLF, clear to Oct) if banks hold. Skip SLB gap-chase; skip XOM/CVX until after Fri 7/31 prints.

---

## 🚀 Momentum universe — 2026 leaders (live screen Jul 9, 2026)

_The AI-infrastructure stack IS the 2026 leadership. Grouped by layer. Gate = earnings before Jul 31._

| Layer | Names (YTD) | Gate (Jul 31) |
|---|---|---|
| **Memory / storage** | SNDK +500%+ · MU +200–270% · WDC +194% · STX +196% | SNDK/MU clean · **WDC Jul29, STX Jul28 OUT** |
| **Servers / systems** | DELL +241% · PENG +259% · SMCI | DELL/PENG/SMCI clean |
| **Connectivity / optical** | **ALAB +159%** · MRVL +141% · LITE +111% · CIEN +148% · CRDO · COHR | all clean (report Aug+) |
| **AI cloud / neocloud** | NBIS +128% · CRWV · DDOG | clean |
| **Compute** | AMD +141% · ARM +168% · AVGO · NVDA | AMD/AVGO/NVDA clean · **ARM Jul29 OUT** |
| **Power (non-semi)** | Bloom (BE) +169% · SMR · nuclear | **BE Jul28, VRT Jul29 OUT** |
| **Spec biotech (watch only)** | Erasca +436% · ImmunityBio +350% · Absci +201% | binary — not income candidates |

**All are parabolic per the anti-chase rule → none is a "sell into today's spike."** Trade on pullbacks.

---

## 🔄 Jul 14 (Tue eve) refresh — SelfIDB50 + health check

**Regime:** cool CPI → risk-[REDACTED] grind (Warsh capped the melt-up), IV crushed. **Leadership = MEMORY / HBM.**

**RS ranking (today's move + theme):**
- 🥇 **Memory/HBM supercycle** — **MU +4.9% ($983)**, **SNDK +5.0% ($1,758)**, STX +2%, WDC +1.4%. Web-confirmed structural story: DRAM +600% in months, prices +80–90%/qtr, Big-3 triopoly (SK Hynix/Samsung/Micron = 95% DRAM), **HBM sold out through 2027**, pricing power shifted to suppliers → decoupled from the old boom-bust cycle. **The highest-conviction 2026 theme.**
- 🥈 **Power/datacenter infra** — **AGX +3.6% ($621)**, **FIX +2.4% ($1,773)** at highs; nuclear OKLO/SMR quiet. The "power bottleneck" theme.
- **Compute/connectivity** — MRVL +2.3%, ANET +0.8%, PLTR +2.9%; ALAB/CRDO/CLS/TSM flat (TSM earnings Thu).
- 🔻 **AI-cloud/neocloud WEAK** — **NBIS −7.8% ($194)**, **CRWV −4%**; **ARM −6.1%** (laggard).
- **SKHY $189 (+24%)** — SK Hynix; institutions accumulating $150–155; same HBM theme, shares-only (no seasoned options).

**Armed-alert updates:**
- **NBIS → 🔴 STAND DOWN / DISARM** — hit the **$194 stand-down line** exactly. Momentum broken, no entry.
- **ALAB** — $361, still **below the $383 base** → no reclaim, no entry.
- **SKHY** — new watch: buy a *pullback* toward $150–160 (offer zone), not the +24% rip.

**Forward-looking income idea:** **MU put credit** on a hold/pullback = the model-consistent way to play the memory theme (rich IV, clean earnings gate — next report ~late Sept, large-cap liquid). Parabolic → sell on a hold, don't chase.

## 🔄 Jul 12 (Sun) refresh — SelfIDB50 re-run
- **Regime flipped defensive/risk-[REDACTED]** into CPI (Tue 7/14 8:30 ET). Sun-night: SMH −2.6%, XLK −1.8% (semis/tech lead down); **energy the only green (XOP +2.1%, XLE +1.6%)** on Iran/Hormuz oil bid.
- **TRGP moves UP the queue** — its Jul 9 "needs green confirm" condition is now met (energy leads overnight). Best non-tech long if energy holds post-CPI.
- **FFTY power/datacenter-infra names confirmed:** **AGX** (#14), **FIX** (#13), **DY** (#19) — non-tech AI-buildout diversifiers, already in rs_screen universe. Track for post-CPI entries.
- **No armed alert triggered** (ALAB/NBIS green Fri). **CPI Tuesday could be the pullback catalyst** — watch ALAB $390–400 / NBIS $205–210 holds Tue/Wed.
- **Gate:** everything blocked until CPI clears — no new premium sells Mon; re-engage Wed+.

## 📋 Multi-list cross-sector shortlist (IBD 50 + IBD Big Cap 20, screened Jul 9 2026)

_Combined both IBD lists, de-duplicated, run through the full battery: earnings gate (Jul 31 expiry) → concentration cap (3 semis live: NVDA/SNOW/AVGO) → anti-chase → correlation-to-book → option liquidity. **The discipline finding: today's momentum is almost entirely tech/cyber — all correlated to the current book. The value is in the non-tech survivors.**_

### 🟢 8 AM priority queue — gate-clean, non-tech DIVERSIFIERS (price these first)
| Rank | Name | Sector | Live gate | Structure (route on live IV) | Note |
|---|---|---|---|---|---|
| 1 | **HWM** | Aerospace/industrial | clean (~Aug 5) | Low IV ~38% → **call debit $275/$285**; put-credit $255/$245 only if it breaks lower | Consolidating $268–278; zero tech correlation |
| 2 | **LLY** | Pharma | clean (~Aug 7) | Confirm IV → call debit if <50% | ⭐ **Triple-list conviction** (IBD 50 + Big Cap 20 #1 + Sector Leaders). Cleanest uptrend, mega-cap liquid, 1 ct (｜$1,216 underlying) |
| 3 | **SN** | Consumer disc | clean (~Aug 8) | Confirm IV/route | Orderly uptrend $102→$154; mid-cap, check option depth |
| 4 | **TRGP** | Energy midstream | clean | Route on IV; **needs green confirm** | Energy was RED today (XLE −1.4%) — only if sector turns |
| 5 | **RPRX** | Pharma royalty | clean | Likely low IV → call debit or skip | Stable, low-vol diversifier; thin premium |

### 🟡 Tech/semi bucket — gate-clean but CONCENTRATION/CORRELATION-blocked (only if a semi comes off)
CRWD, PANW, ANET, DELL, AMD, OKTA, NTAP, CRDO, LRCX — all correlated to NVDA/SNOW/AVGO. Several spiking today (AMD +5.7%, PANW +5.5%, DELL +4.2%). Do **not** add a 4th correlated tech leg.

### 🔴 Gated out (report before Jul 31 — no premium sell for a Jul 31 expiry)
TRV (7/17), IBKR (7/21), WELL (7/27), FFIV (7/27), CLS (7/27), INCY (7/28), NBIX (7/29), FTNT (7/29), APH (7/29), CRS (7/30), AMG (7/30), ILMN (7/30). _Re-open once they report or for an Aug+ expiry._

_Watch-only (too small/thin for spreads): **SKWD** (~$3B insurance, non-tech but illiquid options), **SEZL** (small-cap fintech, spiking). Confirm gate per-symbol at 8 AM — the high-cap calendar doesn't cover them._

**3-list coverage note (Jul 9):** screened IBD 50 + Big Cap 20 + Sector Leaders. All three converge on the same conclusion — 2026 momentum is overwhelmingly tech/semi (correlated to the book), so the tradeable edge is the handful of gate-clean **non-tech** names: HWM, LLY, SN, TRGP, RPRX. Sector Leaders added no new liquid diversifier (CLS gated, SKWD/SEZL too thin).

---

## 🔔 ACTIVE PULLBACK ALERTS (armed, awaiting trigger)

### ALAB (Astera Labs) — $420 · IV ~120% · clean gate (reports early Aug)
_Structure: ATH $499 (6/30) → $367 low (7/7, −26%) → bounced to $420. Base $340–372. IV 120% = 22-day expected move ~±29%; keep short strike BELOW the $367 low + size tiny._

| # | Trigger | Action |
|---|---|---|
| **A** | Dips to **$390–400** and **holds** (green reclaim, doesn't break $383) | Sell **$350/$340 put credit Jul 31**, **1 ct** (short strike below the $367 low). Re-price at trigger. |
| **B** | Dips to **$367–375** and holds (retest the low) | Sell **$330/$320 put credit**, 1 ct — OR buy a few **shares** for the $1k sleeve (momentum long) |
| 🔴 | Daily **close < $360** (loses the base) | Stand down — momentum broken, no entry |
| ⚠️ | ALAB **up >4% / fresh high** (like today +6.85%) | **Do NOT sell into it** — wait for the pullback |

### NBIS (Nebius) — $223 · AI cloud · clean gate
_Structure: high $298 (6/17) → $194 low (7/7, −35%) → bounced to $223. Base $206–216. Calmer than ALAB (+3% today) but big corrections — keep short strike below the $194 low._

| # | Trigger | Action |
|---|---|---|
| **A** | Dips to **$205–210** and **holds** (retest the base, doesn't break $194) | Sell **$175/$165 put credit Jul 31**, 1 ct. Re-price + confirm IV at trigger. |
| 🔴 | Daily **close < $194** (loses the low) | Stand down |

### ~~HCSG (Healthcare Services Group)~~ — 🔴 RETIRED 7/23
_Post-earnings: printed Wed 7/22, stock **$22.31 (−5.3%)** on Thu 7/23 — failed the >$25.75 breakout trigger and broke the ~$24 base. **Stand down — no entry.**_

---

## Refresh cadence
- **Every strategy-battery tick (8/11/1 PT):** run the discovery screen (step above), refresh the universe, check if any armed alert triggered.
- **Weekly:** re-rank the universe vs a fresh top-gainers/RS pull; retire names that lost momentum, add new leaders.
- **Event gate:** re-check earnings dates as expiries roll.
