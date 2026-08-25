# Trading Watchlist & Playbook

_Last updated: June 22, 2026 (4:25 PM PT) — **+5 watchlist adds (full Health Check): MARA 🟢 sell-put GO · ANET 🟢 GO (BE-in-range, wait for pullback) · PLTR 🔴 AVOID (52w-low knife) · ABBV 🟡 defensive watch · VZ 🟡 yield-hit defensive watch.** Earlier today: **NNE put credit OPEN** (5× $23/$20 Jul 17, $0.80, −9% day but only −$25, hold; stop = close <$22); **ANET/CRM** added off the SPX/Mag-7 rotation check (AMD passed). Prior: **GOOGL $370/$390 call debit (PAUSED — broke $360 to $348)**; **AVGO $410/$440** trigger >$410; Health Check IV-routing fix; TGTX card._

_Generated using session skills: Stock Analyst · Finance Analyst · Market Analysis · Stock Trading · Options Trading._

> **Disclaimer:** Personal trading notes for my own use. Not investment advice. Prices are snapshots and go stale fast — always re-pull live before acting.

---

## 🥭 MANGOS — daily AI-leadership cross-check

> **Standing rule:** cross-check this basket **every day**, and **always** when I ask
> *"what's today's plan."* It's the AI-leadership pulse + the "policy-put / top-20" tell —
> when these diverge from the broad tape, that's the breadth signal.

| | Name | Trade? | Ticker | What it anchors |
|---|---|---|---|---|
| **M** | Meta | ✅ | **META** | Llama (open-source AI) + AI-infra capex |
| **A** | Anthropic | ❌ private | proxy **GOOGL / AMZN** | Claude; read via its lead investors |
| **N** | Nvidia | ✅ | **NVDA** | the kingpin — everyone's AI hardware |
| **G** | Google | ✅ | **GOOGL** | TPUs + Gemini + cloud (vertically integrated) |
| **O** | OpenAI | ❌ private | proxy **MSFT** | ChatGPT; read via its partner |
| **S** | SpaceX | ✅ | **SPCX** | post-IPO; Starlink, infra scarcity |

**Daily cross-check = pull live px/%, RSI, and note divergence from QQQ.** Tradeable
options ideas only from the public four (META · NVDA · GOOGL · SPCX). Anthropic/OpenAI are
private → sentiment only via GOOGL/AMZN and MSFT.

---

## ✅ MONDAY 6/22 READY-LIST (check at the open)

> Markets were **closed Fri 6/19 (Juneteenth)** → all prices below are **6/18 close**. **Next session = Mon 6/22.**
> **First step:** open the **`ssr-analyst` workspace** so Robinhood MCP loads → re-pull live quotes before doing anything.

### Pre-open checklist (in order)
1. [ ] **Switch to `ssr-analyst` workspace** (Robinhood live + chains).
2. [ ] **Re-run live quotes** for AVGO / META / AMZN (6/18 prices will reprice on the 3-day gap).
3. [ ] **Re-scan AVGO whale-flow** (OptionStrat Flow, free 15-min, or re-run the Vol/OI script) — confirm calls still leading.
4. [ ] **Macro check:** no major US data Mon 6/22; watch oil/Iran headlines (oil↑ = risk-[REDACTED]). Tariff 7/6 + CPI 7/14 still ahead → **stage, don't full-send.**
5. [ ] **Tape gate:** if QQQ opens red >1–2%, WAIT for stabilization — buy the dip into the staged plan, don't chase a gap-up.

### The 3 GO trades (STNOW-qualified)
| # | Name | 6/18 px | STNOW | Trade (Jul 17 call debit spread) | Debit | Max profit | Max loss | Breakeven | Trigger |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **AVGO** | $411.35 | 🟢 +6 STRONG GO | **Buy $410C / Sell $440C** | ~$11.50 | $1,850 | $1,150 | $421.50 | hold >$410; add on dip $405–410 |
| 2 | **META** | $577.22 | 🟢 +3 GO | **Buy $575C / Sell $610C** | ~$13.30 | $2,170 | $1,330 | $588.30 | **reclaim $600** |
| 3 | **AMZN** | $244.39 | 🟢 +2 GO (best R:R, smallest) | **Buy $245C / Sell $260C** | ~$5.25 | $975 | $525 | $250.25 | reclaim $250 / AWS reaccel |

**Whale Check (6/18) — all 🟢 BULLISH (+2), and each target sits inside the 1σ expected move:**
| Name | Whale flag | P/C vol | ATM IV | Exp move (Jul 17) | Target vs EM |
|---|---|---|---|---|---|
| AVGO | 🟢 +2 | 0.44 | ~48% | ±$55 (±13.4%) | $440 = +$29 → **within 1σ** ✅ |
| META | 🟢 +2 | 0.45 | ~34% | ±$55 (±9.5%) | $610 = +$33 → **within 1σ** ✅ |
| AMZN | 🟢 +2 | 0.29 | ~32% | ±$22 (±8.8%) | $260 = +$16 → **within 1σ** ✅ |

_All three IVs < 50% → debit spreads (not put-selling) are the correct structure. Re-run `python3 market_data/whale_check.py AVGO META AMZN` Monday for fresh confirmation before entry._

**Execution (all 3):** single **spread/combo ticket** (not two legs) · **LIMIT at net mid**, bump $0.05 until filled · stage **½ now, ½ on the 7/6 or 7/14 dip**.
**Sizing:** AMZN ($525) fits the $1k agent acct; AVGO/META = **personal-acct** size.
**Manage:** take profit ~70–80% of max · cut if AVGO<$400 / META<$560 / AMZN<$237 · time-stop ~Jul 10 if flat.

### AVGO whale-flow (6/18) — bullish, confirms the trade
- Call vol 112,905 vs put vol 47,314 → **P/C 0.42** (2.4 calls/put). Fresh OTM call sweeps $415–450; standing call OI walls at **$500C (18.8k)** Jul, **$600C / $450C** Sep. Puts are all far-OTM crash hedges ($250–340), not bear bets.
- → Long $410 = where sweeps buy; short $440 = where crowd caps. Strikes validated.

### ❌ Rejected (do NOT long — logged for tracking)
| Name | STNOW | Why rejected | Re-look trigger |
|---|---|---|---|
| **NOW** $95.04 | 🔴 −3 WAIT (value-trap gate) | −51% on growth decel + margin cut; targets being cut; ~Jul 22 earnings binary | Jul 22 earnings: CC growth holds 18–19% + margins stabilize |
| **CRWD** $684.86 | 🔴 −2 AVOID long | Trading **at/above** target ($674–712); valuation downgrades (Berenberg→Hold) | Pullback to <$600 or fresh upgrade cycle |

---

## 🐋 Whale Check + IV — full watchlist (6/18 close, exp Jul 17 ~28DTE)

_Flow = P/C volume + fresh unusual activity; IV-mod folds in ATM IV & put-skew. Score −2…+2. Run `python3 market_data/whale_check.py <TICKER> --to 2026-09-30` to refresh._

### 🟢 Bullish / lean-bull (flow + IV agree — favor longs / call spreads; OK to sell puts if IV ≥ 50%)
| Name | Flag | Score | P/C vol | ATM IV | Exp move (Jul 17) | Skew |
|---|---|---|---|---|---|---|
| MARA | 🟢 BULLISH | +2 | 0.11 | ~85% | ±$3.34 (±23.5%) | +2.8 |
| INTC | 🟢 BULLISH | +2 | 0.62 | ~87% | ±$32.25 (±24.1%) | −1.1 |
| ORCL | 🟢 BULLISH | +2 | 0.40 | ~52% | ±$26.31 (±14.3%) | +1.6 |
| HOOD | 🟢 BULLISH | +2 | 0.30 | ~68% | ±$20.27 (±18.7%) | +1.1 |
| HPE | 🟢 BULLISH | +2 | 0.49 | ~68% | ±$8.95 (±18.9%) | +2.8 |
| SMCI | 🟢 BULLISH | +2 | 0.29 | ~82% | ±$6.93 (±22.6%) | −0.6 |
| STX | 🟢 BULLISH | +2 | 0.65 | ~90% | ±$266.85 (±24.9%) | +2.4 |
| IBM | 🟢 BULLISH | +2 | 0.35 | ~39% | ±$27.08 (±10.9%) | −0.3 |
| SNOW | 🟢 BULLISH | +2 | 0.50 | ~55% | ±$35.61 (±15.3%) | +0.7 |
| MNDY | 🟢 BULLISH | +2 | 0.36 | ~66% | ±$13.16 (±18.4%) | +0.1 |
| NOW | 🟢 BULLISH | +2 | 0.41 | ~56% | ±$14.83 (±15.6%) | −2.9 |
| TLN | 🟢 lean-bull | +1 | 0.40 | ~60% | ±$72.18 (±16.5%) | +3.1 |
| NNE | 🟢 lean-bull | +1 | 0.37 | ~101% | ±$7.93 (±28.1%) | +9.5 |
| NTAP | 🟢 lean-bull | +1 | 0.66 | ~45% | ±$19.96 (±12.5%) | +0.7 |

### 🟡 Neutral (no edge — wait for chart trigger)
| Name | Flag | Score | P/C vol | ATM IV | Exp move (Jul 17) | Skew |
|---|---|---|---|---|---|---|
| TSLA | 🟡 NEUTRAL | 0 | 0.73 | ~43% | ±$47.19 (±11.8%) | +0.2 |
| ANET | 🟡 NEUTRAL | 0 | 0.71 | ~53% | ±$24.79 (±14.6%) | +1.1 |
| WDC | 🟡 NEUTRAL | 0 | 0.77 | ~98% | ±$202.65 (±27.2%) | +1.3 |
| VEEV | 🟡 NEUTRAL | 0 | 0.96 | ~43% | ±$18.27 (±11.9%) | +0.8 |

### 🔴 Bearish / lean-bear (flow against longs — do NOT sell puts; avoid fresh longs)
| Name | Flag | Score | P/C vol | ATM IV | Exp move (Jul 17) | Skew |
|---|---|---|---|---|---|---|
| IREN | 🔴 BEARISH | −2 | 1.40 | ~104% | ±$17.32 (±28.9%) | +2.8 |
| ASML | 🔴 BEARISH | −2 | 1.63 | ~60% | ±$319.70 (±16.6%) | −1.2 |
| MU | 🔴 BEARISH | −2 | 1.87 | ~105% | ±$331.19 (±29.2%) | +1.3 |
| DELL | 🔴 BEARISH | −2 | 0.97 | ~73% | ±$82.98 (±20.3%) | +0.8 |
| SNDK | 🔴 BEARISH | −2 | 1.76 | ~105% | ±$636.71 (±29.1%) | −0.0 |
| DDOG | 🔴 BEARISH | −2 | 1.08 | ~59% | ±$36.21 (±16.2%) | +3.0 |
| CRWD | 🔴 BEARISH | −2 | 2.13 | ~50% | ±$94.99 (±13.9%) | −0.6 |
| CRWV | 🔴 lean-bear | −1 | 0.77 | ~88% | ±$28.68 (±24.3%) | +4.5 |
| ZS | 🔴 lean-bear | −1 | 0.78 | ~56% | ±$19.21 (±15.4%) | +4.3 |

**Read-throughs:**
- **Memory/storage flashing red:** MU, SNDK, WDC, DELL all bearish/neutral with 90–105% IV → market pricing big down moves; do not sell puts here.
- **NNE skew +9.5** = extreme put demand (crash-hedge / event) even though net flow leans bull — size small, spreads only.
- **NOW skew −2.9 + bullish flow** but STNOW still 🔴 WAIT (value-trap gate) → flow ≠ permission to long ahead of Jul 22 earnings.
- **ASML/MU/IREN bearish flow** confirms staying away from chip-equipment / memory longs until flow flips.

---

## Macro gate for EVERYTHING

**CPI (May) printed June 10: headline +4.2% YoY (hot, energy-driven) but CORE +0.2% MoM / +2.9% YoY (cooler than est).** Market looked through it (flat day), then sold off intraday on Iran-war + tech rotation, then bounced June 11. **Net: gate is open-ish but choppy — no chasing.**

- **Next catalysts:** Iran/energy headlines (driving the hot headline), Fed meeting, July CPI (Jul 14).
- **ORCL earnings (Jun 10 AMC):** beat but −12% on AI-capex/debt worry → negative sentiment read-through for AI-infra group.

No bullish trigger fires on a heavy red-tape day (e.g., QQQ down >2%). Buy stabilization + relative strength, never the knife.

---

## Core discipline rules

1. **Don't catch falling knives.** Buy stabilization / strength, not the bounce off the lows.
2. **Buy the relative-strength leader** — on a red day, what falls *least* is what the market wants *most*.
3. **Bitcoin + QQQ are the lead signals** for the AI-infra/crypto-proxy group. They turn first; the group follows.
4. **Wait for the green reclaim** of a prior level — not the first green candle.
5. **Size for a $1k account** — favor capital-efficient names; one bad knife shouldn't blow up the account.

---

## AI-Infrastructure / Power-Compute group

_All four move together with the tape + their own catalysts. The whole group turns together; trade the leader._

| Ticker | Ref price (6/5) | 🟢 Bullish entry trigger | 🔴 Bearish trigger | Notes |
|---|---|---|---|---|
| **TLN** (Talen) | $365 | Green day, holds >$365, reclaims $378 | Loses $365 → next leg down | Quality leader (real power plants, Amazon nuclear deal). ~$475–499 consensus. **$365/share = pricey for $1k acct** |
| **CRWV** (CoreWeave) | $100 | Holds $95–100, green close >$108 | Loses $95 → toward $63 low | Purest AI-neocloud. Q1 rev +112% YoY, $99B backlog, Nvidia-backed. **High debt (D/E ~10.7), ~12% short int.** Most capital-efficient for me |
| **IREN** | $54 | **BTC bases first**, then reclaims ~$60 | Stays weak with BTC → new lows | Closest MARA comp — proves the miner→AI pivot. B.Riley PT $96 |
| **MARA** | $12.28 | **BTC bases/turns** + reclaims ~$14; OR AI tenant signed at Hannibal | Breaks ~$11.50 → toward $10, then $6.66 | Bitcoin proxy (beta 5.38) + AI-pivot lottery ticket. See pivot notes below |

**Group rule:** leading signal = **Bitcoin + Nasdaq (QQQ) stabilizing.** When the tape turns (likely needs cool CPI), buy the relative-strength leader, not the hardest bouncer.

---

## Chip supply chain — the "Terafab thread"

_Elon Musk's Terafab (Tesla + SpaceX + xAI) chip megaproject in Texas ($55B → $119B). The supply chain runs upward: Terafab needs **Intel** (foundry, 18A/14A) → which needs **ASML** (only maker of EUV machines). SpaceX is private (not buyable)._

| Ticker | Ref price (6/5) | 🟢 Bullish entry trigger | 🔴 Bearish trigger | Notes |
|---|---|---|---|---|
| **ASML** | $1,641 | Cool CPI + green stabilization candle; reclaim $1,757 | Loses Friday low with semis | **Best business / picks-&-shovels.** EUV monopoly, €38.8B backlog. Wins regardless of which fab wins. Pricey ($1,641 → buy fractional), ~45x earnings |
| **INTC** | $99 | Cool CPI + holds ~$95, green reclaim of $112 | Loses $95 → turnaround doubt | **High-risk turnaround swing.** Terafab anchor customer, 18A yields +7–8%/mo. Most accessible price, most Terafab leverage — but unproven, −11.5% Fri. Size small |
| **TSLA** | $391 | (not a focus — Musk/everything bet, Terafab incidental) | — | Buying TSLA for Terafab is indirect; you get the whole Musk story |

**Key insight:** ASML is the bottleneck the entire pyramid depends on (order book full through 2027). The indispensable supplier is usually where the durable investment sits — not the flashy end-customer.

---

## Semiconductors — memory & broad chip ETFs

_Added June 8 after a big green chip day (SMH +4.7%, SOXX +5.7%, SOXL +15.4%, MU +8.5%). **All three are extended — these are pullback-buys, not chase-here.**_

| Ticker | Ref price (6/8) | 🟢 Bullish entry trigger | 🔴 Bearish trigger | Notes |
|---|---|---|---|---|
| **MU** (Micron) | $938 | **Only on a pullback** to ~$860 (rising 20-day), green reclaim, RSI resets | Loses SMA20 ($860) → toward SMA50 ($630) | HBM/AI-memory leader, +25% in a month. **⚠️ Analyst mean $739 / median $575 — both BELOW price.** Street sees 21–39% downside. **No long here — chasing a parabolic move** |
| **SMH** | $597 | Pullback to ~$586 (20-day), green reclaim; cleanest of the three | Loses $586 → toward 50-day ($511) | VanEck bellwether semis ETF. Lowest vol (32%). Best *quality* entry if it dips |
| **SOXX** | $570 | Pullback to ~$548 (20-day), green reclaim | Loses $548 → toward 50-day ($467) | iShares semis ETF — same trade as SMH, pick one |
| **SOXL / SOXS** | — | (tactical only — see Inverse ETFs note) | — | 3× leveraged bull/bear. Day-trade/swing only, never hold. SOXL +15% today = blow-off, don't chase |

**Read:** chips are ripping but all near swing highs — reward-to-target is thin vs. the volatility stop. STKK says **WAIT for the 20-day pullback** on SMH/SOXX; **avoid MU long entirely** (trading well above analyst consensus). Re-run `STKK` after any 5–8% dip.

---

## STKK computed levels (algorithm output — June 11, 6:42 PM PT, EOD)

_Ranked by R:R. Live quotes from Yahoo. **Re-run `STKK` daily — these go stale fast.**_
_Note: %abv = how far price sits ABOVE the entry zone (you want it AT or below, on a green reclaim). **Market: QQQ +3.4% — big risk-[REDACTED] melt-up day.**_

| Rank | Ticker | Regime | Price | 1d | Entry | Stop | Target | R:R | %abv | RSI | Note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **NNE** | 🔴 DOWN | 23.55 | +6.5% | 22.63 | 17.47 | 40.08 | 3.38 | +4.1% | 47 | lottery (n=3, beta 3.87); still **<$24** |
| 2 | **TLN** | 🔴 DOWN | 344.80 | +2.4% | 339 | 294 | 471 | 2.89 | +1.6% | 43 | strong-buy mean $473 (+37%); **best quality high-R:R — needs reclaim** |
| 3 | **CRWV** | 🔴 DOWN | 95.74 | **+0.1%** | 93 | 65 | 149 | 1.98 | +2.8% | 40 | buy n=33 $140; **laggard AGAIN (+0.1% on +3.4% QQQ)** → green reclaim >$95 |
| 4 | **NTAP** | UP | 160.47 | −0.1% | 154.7 | 137.3 | 187.75 | 1.90 | +3.7% | 69 | quality, **low beta 1.38**, buy $172; **RSI 69 extended — buy the dip** |
| 5 | **ORCL** | 🔴 DOWN | 184.10 | −8.5% | 179 | 130 | 265* | 1.74 | +2.6% | 48 | bounced off $177 low to $184 but still red; **let it base** |
| 6 | SMH | UP | 609.45 | +6.8% | 594 | 549 | 638 | 0.96 | +2.5% | 58 | near swing high — no edge |
| 7 | SOXX | UP | 586.93 | +8.4% | 570 | 517 | 616 | 0.88 | +3.1% | 61 | near swing high — no edge |
| 8 | IREN | Range | 56.71 | +10.1% | 56.7 | 28.6 | 80.3 | 0.84 | 0.0% | 49 | ripped +10%, at entry — chasing |
| 9 | HOOD | Range | 92.23 | +6.8% | 88.9 | 61.8 | 104 | 0.57 | +3.7% | 64 | reclaimed $92 but R:R thin now; see call-debit idea |
| 10 | MARA | Range | 13.61 | +7.8% | 13.5 | 7.2 | 16.3 | 0.44 | +0.6% | 50 | fails gate |
| 11 | ASML | UP | 1,899 | +9.5% | 1,856 | 1,725 | 1,701 | −1.19 | — | 72 | ❌ above mean $1,701, parabolic |
| 12 | MU | UP | 995.87 | +11.7% | 953 | 823 | 789 | −1.27 | — | 64 | ❌ above mean $789, parabolic |
| 13 | INTC | UP | 116.96 | +9.3% | 113 | 98 | 93 | −1.34 | — | 49 | ❌ above mean $93 |

\***ORCL target $265 = analyst mean (n=39) likely still pre-crash/STALE.** Treat R:R 1.74 as optimistic until targets reset post-earnings. DOWN regime + −8.5% day = knife; wait for a base.

**Reads (June 11 EOD):** Big melt-up — **QQQ +3.4%**, names ripped 6–12%. **Only NNE & TLN clear the 2:1 gate, both DOWN regime → no chase.** **TLN is the cleanest quality setup** (strong-buy $473, low vol, +1.6% above entry) but needs a green reclaim to confirm. **CRWV red flag:** +0.1% while the tape ripped +3.4% = laggard again; wait for a green reclaim >$95, don't buy the dripper. **NTAP** = only clean uptrend, RSI 69 → buy the pullback. **ORCL** bounced off its low but still a knife. **Chips/memory (MU +12%, ASML +9.5%, INTC +9.3%) all parabolic + above analyst fair value → avoid longs.** NNE/MARA/HOOD extended after the spike (see Three Good — all "wait").

---

## ORCL · HOOD · NNE — new adds (stocks + options)

_Added June 11. Stock triggers + options expression for each. **All three carry high IV (~89–101%) → options favor SELLING premium (spreads), not buying naked.**_

| Ticker | Px (6/11) | 🟢 Stock entry trigger | 🔴 Bearish trigger | Options idea (high IV → sell/spread) |
|---|---|---|---|---|
| **ORCL** | $177.52 | **Wait** — post-earnings knife (−12%). Need a daily close that stabilizes + reclaims ~$190 | Loses $175 → toward $140 (SMA fill) | IV 89%. **Don't buy calls into the bleed.** If it bases >$175: bull **put credit spread** ~$165/$155 (sell the fear). Aggressive only |
| **HOOD** | $89.50 | Pullback to ~$83 (20-day) OR green reclaim > $92 | Loses $80 → toward $69 | IV 91%, beta 3.19. **Put credit spread** ~$80/$75 on a dip-and-hold; or $85/$95 call debit spread if it reclaims $92 with conviction |
| **NNE** | $22.24 | Reclaim + hold **$24** (it broke $23 — strike shifts down now) | Loses $21.50 → toward $18 / $14.8 | IV 101%. See full play card in `options_watchlist.md`. **$23 not yet confirmed — wait for reclaim**; strikes now ~$21/$18 |

**ORCL context:** beat Q4 (EPS $2.11 vs $1.96, IaaS +93%) but sold off −12% on "AI capex exceeds forecast / debt worry." Analyst mean $255 (n=39) is pre-crash and stale. Quality franchise, but **don't catch it falling** — let it base.
**HOOD context:** your broker's stock 🙂. RANGE regime, beta 3.19 (very volatile), buy-rated mean $100 (+12%). Clears the 2:1 gate but sits 6.8% above entry — wait for the pullback or a clean reclaim.
**NNE context:** see `options_watchlist.md` for the full credit-spread vs debit-spread play cards. Still a quarter-size lottery.

---

## NTAP (NetApp) — quality data-infrastructure / AI-storage

_Added June 11. **Different profile from the rest of this list:** a profitable, low-beta (1.38) large-cap in a clean uptrend — not a high-vol lottery. AI tailwind = all-flash + data pipelines feeding AI workloads._

| Ticker | Px (6/11) | 🟢 Bullish entry trigger | 🔴 Bearish trigger | Notes |
|---|---|---|---|---|
| **NTAP** | $160.00 | **Pullback to ~$150–154** (rising 20-day) + green reclaim; RSI resets from 69 | Loses SMA20 ($150) → toward SMA50 ($124) | UP regime (px > 20>50>200 SMA). Buy-rated, mean $172 / median $175 (n=16) = **+7–10% upside**. R:R 1.93 (just under 2:1). Vol only 7% → calmer, can size larger. **Extended here (RSI 69) — wait for the dip, don't chase $160** |

**Read:** NTAP is the *quality* name on the list — clean uptrend, real earnings, low beta, modest but real analyst upside ($172 mean). It's **extended at $160 (RSI 69, near the $181 swing high)** and sits only ~$6 above its entry zone. STKK R:R is 1.93 — a hair under the 2:1 gate, so it's a **buy-the-pullback to ~$150–154**, not a chase. Because vol is low (~7% vs 80–110% on the lottery names), position size can be larger for the same dollar risk.

---

## Other names

| Ticker | 🟢 Bullish trigger | 🔴 Bearish trigger |
|---|---|---|
| **GDX** (gold miners) | Holds base, gold firm → defensive bid | Breaks support with gold |
| **DDOG** | Real base + green reclaim of resistance | Lower highs continue |
| **Semis** (MU / SMH / SOXX) | → see dedicated **Semiconductors** section above | Breaks 20-day |

---

## New adds — AVGO · SNOW · SPCX (June 19)

_Added to the cache + STKK universe June 19. Prices as of 6/18 close (feed lag). Re-run `STKK` for live levels._

| Ticker | Px (6/18) | 🟢 Bullish entry trigger | 🔴 Bearish trigger | Notes |
|---|---|---|---|---|
| **AVGO** (Broadcom) | $410.79 | Holds >$400, green reclaim of **$420** → run toward 52-wk high **$495** | Loses post-earnings low **$372** → deeper flush | AI custom-silicon (XPU) + VMware. Q2 FY26 (Jun 3): AI semi rev **$10.8B**, Q3 AI guide **$16B (+200% YoY)**, $30B AI bookings — **sold off −12%** (didn't raise FY27 AI guide), now recovering. Consensus **Moderate/Strong Buy, mean ~$490** (range $375–630), **92% bullish**, 33 analysts. STKK: RANGE, RSI 43, beta **2.11**, +19% to mean. **$411/share = pricey for $1k acct → fractional/options.** ⚠️ **Never sell premium into AVGO earnings** (see −$1,717 lesson below) |
| **SNOW** (Snowflake) | $232.33 | Holds **$225–230**, green reclaim of **$240** | Loses **$225** → toward **$200** (Macquarie low / support) | Data + AI cloud (Cortex AI). Next earnings **Aug 25** (Q2 FY27): est EPS $0.45, rev **$1.51B**. Consensus **Strong Buy, mean ~$291** (range $200–370), **83–90% buy**, 48–58 analysts. STKK: RANGE, RSI **38** (washed out), beta **1.39** (calmer), **+25% to mean**. Target $285. Quality data-infra add |
| **SPCX** (SpaceX) | $184.97 | **Watch-only** — needs a base; <60 bars of history | — | IPO'd at **$135** (you had the allocation — see STNOW notes). Ran to ~$192, now $185 (−3.6% on 6/18). **Only ~5 trading days of data → no STKK levels yet** (algo needs 60+ bars). High vol, lock-up dynamics ahead. Track daily; STKK levels unlock once ~3 mo of history accrues |

**Reads:**
- **AVGO** — best *quality* of the three: AI-silicon franchise, street mean $490 (+19%) sits above the 52-wk high after a −12% earnings dip. RSI 43 = room. Not a chase at $411; **buy a hold of $400 or a $420 reclaim.** Beta 2.11 → size accordingly.
- **SNOW** — washed-out (RSI 38) with +25% to a $291 mean and the calmest beta (1.39). **Buy a hold of $225–230**, target $285; Aug 25 earnings is the catalyst. Stop below $200.
- **SPCX** — your IPO name; just **watch** until it builds enough history for STKK and the lock-up picture clears.

---

## New adds — ANET · CRM (June 22, off the SPX/Mag-7 rotation check)

_SPX 7,469 (+0.5%, ~2% off ATH), VIX 17.4 (cheap premium). **Mag-7 breadth is narrow:** AAPL +2.8% / NVDA +1.6% leading, while MSFT −5.2% (52w low), GOOGL −3.3%, AMZN −1.5%, META flat. **Clean rotation OUT of software → INTO AI-hardware/semis.** Two new options expressions; full cards in `options_watchlist.md`._

| Ticker | Px (live 6/22) | 🟢 Bullish entry trigger | 🔴 Bearish trigger | Health Check / options |
|---|---|---|---|---|
| **ANET** (Arista) | $173.59 (+6.3%) | ✅ **GO now** — leader near 52w high $180; sell into strength or a small dip | Closes < $160 (short strike) / tape rolls over | AI-networking leader. STKK 🟡 UP RSI 57 · STNOW 🟢 STRONG +5 · IV **57% rich** · Whale 🟢 BULL +2 (CALL skew). **VERDICT 🟢 GO — sell put spread.** Play: **Jul 17 $160P/$150P credit ~$2.10**, maxL $790, cushion 7.8%, RoR 27% |
| **CRM** (Salesforce) | ~$150 (−10%) | **Daily CLOSE > $158** (proof the knife stopped) → buy call debit spread | Loses $148 → next leg lower | Software wreck at 52w low, RSI **24** oversold, IV **44% cheap**, Whale 🟢 BULL +2 (dip-buying), R:R 6.71. **VERDICT 🟡 WAIT for trigger** (value-trap discipline). Play on trigger: **Jul 17 $155C/$170C debit ~$3.15 (cap ≤$5)**, maxP ~$1,185, maxL ~$315, R:R ~3.8:1 |

**Reads:**
- **ANET** — the clean *sell* of the day: rich IV (57%), bullish whale flow with call skew, strong STNOW. The credit spread doesn't need more upside, just for ANET to hold above $160 (7.8% cushion). Take 50–70% profit, stop on a close below $160.
- **CRM** — a *bounce* trade, not a trend trade. Smart money is buying the −10% dump (P/C vol 0.36) and IV is cheap, but it's still a falling knife at a 52w low. **Arm it, don't catch it** — only enter on a daily close back above $158, reprice the debit at entry. Software is the weak sector, so take profit faster (~50–60%).
- **AMD** — checked, **passed.** +6.7% rip to near-ATH but whale 🔴 **BEARISH −2** (heavy near-money put buying *into* the rally) and IV 74% rich. Don't chase; revisit if it bases with calmer flow.

---

## Watchlist adds — MARA · ANET · PLTR · ABBV · VZ (June 22, 4:25 PM PT)

_Full Health Check on live prices. **Theme:** breadth deteriorated today (yields↑, spec/software risk-[REDACTED]) — the board splits into high-IV momentum **sells** (MARA/ANET), a falling **knife to avoid** (PLTR), and low-IV **defensives to watch** (ABBV/VZ). MARA/ANET also have option cards in `options_watchlist.md`._

| Ticker | Px (live 6/22) | STKK | STNOW | IV | Whale | VERDICT | Play / trigger |
|---|---|---|---|---|---|---|---|
| **MARA** | $14.85 (+5.5%) | UP, thin R:R | 🟢 STRONG +5 | 89% | 🟢 BULL | 🟢 **GO — sell put spread** | Jul 17 **$13/$11 put credit** (base $12–15). Arm at open **if BTC stable**. Card in options doc |
| **ANET** | $174.56 (+6.9%) | UP, thin R:R | 🟢 GO +4 | 56% | 🟢 lean-bull | 🟢 GO (⚠️ BE-in-range) | **Wait for pullback to $165–168 that holds** → $150/$140 put credit. Don't chase the +14% rip |
| **PLTR** | $119.50 (−6.6%) | DOWN, oversold | 🔴 −1 | 51% | 🟡 NEUT | 🔴 **AVOID/WAIT** | 52w low, RSI 24 knife, no flow edge. **Needs base + reclaim $125** before any bullish play. Watch-only |
| **ABBV** | $230.01 (+1.0%) | RANGE | 🟡 +1 | 26% low | 🟢 lean-bull | 🟡 NEUTRAL — wait | Defensive quality holding up in risk-[REDACTED], near 52w high $245. IV too low to sell → **buy-the-dip / call-debit** on a pullback. R:R 0.80 (near fair value) |
| **VZ** | $45.36 (−5.7%) | RANGE | 🟡 +1 | 28% low | 🟢 lean-bull | 🟡 NEUTRAL — wait | Dividend defensive **hit by rising yields** (bond proxy), RSI 37. IV too low to sell → **dividend buy-the-dip on a base + yield stabilization**. R:R 2.52 |

**Reads:**
- **MARA / ANET** — the two high-IV *sells*. MARA is the cleaner structure (basing, IV 89%); ANET's breakeven sits inside last week's range, so wait for a pullback-that-holds rather than chasing. Sizing + cards in `options_watchlist.md`.
- **PLTR** — the model's lone 🔴 **AVOID.** Falling knife at a 52-week low (RSI 24) with neutral flow = no edge yet. Big R:R (4.06) *if* it bases, but don't catch it — wait for a reclaim of $125 + a flow turn.
- **ABBV / VZ** — the **defensive rotation** names. Both low-IV (26–28%) → *buy-the-dip / shares*, not premium sells. ABBV holds near its high (quality defensive bid); VZ got hit −5.7% on rising yields (classic bond-proxy reaction) — a higher yield = a better dividend entry *if* yields stabilize and it bases. Neither trades today; both go on the watch shelf.

---

## TGTX (TG Therapeutics) — biotech catalyst, buy-the-dip (June 21)

_Health Check 6/18 close ($53.22). Quality commercial biotech (not a micro-cap): PE 18.6, EPS $2.86, $8B cap. **Love the company, hate the entry** — RSI 91, parabolic._

**Health Check flags:** STKK 🟡 UP (RSI **91** 🚨 extended) · STNOW 🟢 GO +3 (only +3% to $55 mean) · Three Good ✅ IV 55% · Whale 🟢 BULLISH +2 → **VERDICT: 🟢 GO on pullback, do NOT chase.**

### Thesis — why it's worth tracking
- **BRIUMVI** (anti-CD20 for MS) ramping: FY26 guidance **raised to ~$925M global / $885–900M US** (from $825–850M), record new patient starts, "early in adoption curve."
- **June 3: positive Phase 1 subcutaneous BRIUMVI data** — at-home quarterly injection could **nearly double the addressable market.**
- Up **76% YTD**, at 52-wk high $54.07; consensus mean ~$52–55 (likely lagging the guidance raise), **high target $70 (+31%)**.

### 🔔 Levels & alerts
| Trigger | Level | Action |
|---|---|---|
| 🔴 **Pullback-buy alert** | **$46–48** with **RSI < 60** | Primary entry zone — buy shares / call spread, or sell puts (below) |
| Deeper support | ~$44 (prior consolidation) | Add / better put-sell strike |
| 🟢 Momentum invalidation of "wait" | new high >$54 on Phase 3 news | Only chase on a *fresh catalyst* breakout, small |
| ⚠️ Don't | buy at $53 / RSI 91 | Chasing parabolic = 15–20% drawdown risk |

### Options plan (deploy ON the pullback, NOT now)
- **Put credit spread:** sell **$45 / buy $40** put (Jul/Aug). *Right now it pays only ~$0.40 (far OTM, wide bid/ask).* On a dip to $46–48 the $45 strike goes near-money + IV pops → credit meaningfully richer. Sell **then**, not today.
- Options are **moderately thin** ($5-wide strikes, modest OI) → use **limit orders at mid**, don't pay the ask.

### Catalysts
- **Aug 3, 2026** — Q2 earnings (BRIUMVI revenue vs. raised guide).
- **Late 2026 / early 2027** — **Phase 3 subcutaneous BRIUMVI topline** (the big binary; potential 2028 approval).

---

## GOOGL (Alphabet) — quality GO, buy (low IV) (June 21)

_Health Check 6/18 ($368.03). **Cleanest setup checked this session** — quality mega-cap, NOT extended (RSI 43), real upside, bullish flow. Low IV → **buy, don't sell premium.**_

**Health Check flags:** STKK 🟡 UP (RSI 43, room) · STNOW 🟢 **STRONG +5** (+14% to $420 mean) · Three Good ❌ IV 34% (too low to sell puts) · Whale 🟢 BULLISH +2 → **VERDICT: 🟢 STRONG GO via call debit spread (low IV → buy).**

### Thesis
- **Google Cloud +63% YoY**, **$462B backlog** (≈2x QoQ), 33% Cloud margins, Gemini traction. Analysts keep *raising* targets ($413–433 mean, high $475–515) while the stock drifts ~9% below its 52-wk high ($408.61).
- RSI 43 + 14% to mean = **room to run, not a chase** (unlike TGTX/AMC).

### 🔔 Levels & alerts
| Trigger | Level | Action |
|---|---|---|
| 🟢 Entry (now-ish) | holds **$360**, reclaim **$372** | Buy shares / call debit spread (below) |
| 🟢 Add | dip to **$350–355** | Better entry (RSI cooler) |
| 🔴 Invalidation | loses **$345** | Step aside |
| ⚠️ Tail risk | antitrust appeal headlines | DC Circuit (late-26/27) + AdX case = **$300 bear case** |

### 🎯 TRADE OF RECORD — Jul 17 $370/$390 CALL DEBIT SPREAD
_4-week window (26 DTE), target $390 (top of the proven 30-day range, not the $400 ceiling). Low IV 34% → **buy the move, don't sell premium.** Marks 6/17 close, liquid chain._

| Leg | Strike | Mark |
|---|---|---|
| **BUY** | Jul 17 **$370 call** (~ATM, real delta) | ~$12.40 |
| **SELL** | Jul 17 **$390 call** (= range top, touched ~6/30 sessions) | ~$5.28 |

- **Net debit ~$7.12 → $712/spread** · enter as **single combo ticket, LIMIT at net mid**, bump $0.05 if unfilled (don't pay the ask).
- **Max loss = $712 (debit, fully defined)** · **Max profit = $1,288** if GOOGL ≥ $390 at expiry · **R:R 1.81:1**
- **Breakeven $377.12 (+2.5%)** — long leg ~ATM means it works as soon as GOOGL drifts up; not betting everything on the back leg.

**Expiry P&L (per spread):** ≤$370 → −$712 · $377 → $0 · $380 → +$288 · $385 → +$788 · ≥$390 → **+$1,288**

> **Why $390 over $400:** last 30 closes clustered $356–395; $400 tagged only 3/30 (early May). Crossover ≈ $392 — below it the $390 spread wins (cheaper, lower BE, loses less if wrong, higher profit at $390). $400 only wins if GOOGL pushes the range ceiling. Higher-probability choice.

**Management:**
- 🟢 **Profit-take at ~75–80% of max (~$1,600)** — don't squeeze the last bit.
- 🔴 **Stop:** GOOGL closes < **$360**, OR spread loses ~50% of debit (whichever first).
- ⏱ **Time stop:** if not working with **~5 trading days left**, close (theta cliff).

**Caveat:** ~26-day expected move ≈ ±9–10%, so **$400 = the +1σ line** — full max profit needs a 1-sigma up move (realistic, not base case). You're green by +3%, max needs +8.7%. Jul 17 **expires just before Q2 earnings (~late July)** = clean swing, no earnings gamble.

### Catalyst
- **~Late July 2026** — Q2 earnings (Cloud growth + backlog conversion). Jul 17 spread expires *before* it (no binary risk); an Aug spread would capture it if you want the catalyst.

---

## ⭐ HOOD — DEDICATED FOCUS (primary trade)

_Added June 19. The "rich-cash-flow / betting" thesis, tracked. Ref price **$108.16** (6/18 close, +2.8%). Re-run `STKK` for live levels._

### Thesis — why HOOD is the focus
A high-margin, cash-rich retail-finance flywheel with a genuine new growth engine:
- **Prediction Markets** (the "betting"): 12B event contracts in 2025 → **16B+ in 2026**; April ~$3B volume. CEO: *"prediction-market supercycle… tens of billions → trillions."*
- **Rothera** = HOOD's **own CFTC-licensed exchange** (JV w/ Susquehanna, via MIAXdx). Launched Q2 2026. **Captures full economics** vs. splitting fees with Kalshi. World Cup = first mainstream test. *Not separately tradable — exposure is via HOOD shares only.*
- **Gold subs** (40% new-customer attach), **options** (200M, +20%), **margin book** (+121% YoY → $18.4B), short selling, equities (+57%).
- **~50% adj. EBITDA margins; FCF $1.62B (2025) → ~$2.75B consensus (2026).** Risk = crypto softness + prediction-market regulatory scrutiny.

### Stock levels & alerts
| Trigger | Level | Action |
|---|---|---|
| 🟢 First pullback buy | **$100** | round + analyst mean + breakout retest |
| 🟢 Back-up-truck | **$92–95** | prior base |
| 🔴 Stop | **< $88** | thesis-intact invalidation |
| 🎯 Target | **$124** (STKK), then prior highs | |
| ⚠️ Don't chase | **$108 now** | +24% above STKK entry, above $100 mean, RSI 63, beta 3.10 |

### 🔔 ACTIVE ALERTS (set June 19) — armed, awaiting trigger
| # | Watch for | Trigger price | When it fires → do this |
|---|---|---|---|
| **1** | **Pullback to deploy "safe squeeze"** | dips into **$100–102** and holds intraday | Deploy **Card A: 7/31 $100/$95 put credit spread** (~$1.38 credit, no earnings risk). The cleanest "squeeze before Aug 5." |
| **2** | **Back-up-truck share add** | **$92–95** zone | Add shares (prior base); stop < $88. Accumulation, not a spread. |
| **3** | **Invalidation / cut** | **close < $88** | Thesis-intact stop — exit shares, stand down on new spreads. |
| **4** | **Momentum confirm (optional)** | reclaim + hold **> $112** on volume | Only then consider **Card B 8/21 call debit spread** for the through-earnings beat. Small size (binary). |

_Note: at ~$108 now you're in the "don't chase" zone — alerts 1 & 2 are the disciplined entries. Re-run `STKK HOOD` for a live price before acting; marks above are 6/18 close._

### 🔑 Aug 5, 2026 — Q2 earnings (the catalyst). Metrics to watch:
- **Gold attach rate** — **>18% of funded accounts = recurring-revenue thesis confirmed**
- **Event-contract volume + Rothera ramp** (revenue take-rate)
- Net deposits growth, options/equities volume, crypto trend (the risk)
- ⚠️ **Note: Q1 2026 fell −13% *on a beat*** — at $108 (above mean) it may be priced for perfection. **Beat ≠ pop.**

### Options play cards (real marks as of 6/18 close, IV ~70%, multiplier 100)

**A) Pre-earnings "safe squeeze" — Put Credit Spread, exp 7/31 (NO earnings risk)**
- On a dip toward ~$100–102: **Sell $100 put / Buy $95 put**
- Marks: $5.68 / $4.30 → **net credit ~$1.38** · width $5 · **max profit $138** · max loss $362 · breakeven **$98.62** · POP ~**69%**
- Bullish/neutral. Collect premium + theta on the run-up; **closes before Aug 5 → no binary.** This is the cleanest "squeeze before Aug 5."

**B) Through-earnings, high-conviction beat — Call Debit Spread, exp 8/21**
- **Buy $110 call / Sell $125 call**: $12.15 / $6.98 → **debit ~$5.17** · width $15 · **max profit $983 (+190%)** · max loss $517 · breakeven **$115.17** (needs +6.6%)
- _Lower-breakeven alt:_ **Buy $105 / Sell $120**: debit ~$5.93 · max profit $907 · breakeven **$110.93** (needs +2.7%)
- This is the *correct* vehicle if you believe it **beats AND pops** — captures the gap-up with defined risk. Size **small** (binary).

**C) Through-earnings, income tilt — Put Credit Spread, exp 8/21**
- **Sell $100 / Buy $90**: $8.23 / $4.78 → **credit ~$3.45** · width $10 · **max profit $345** · max loss $655 · breakeven **$96.55** · POP ~**67%**
- Wins if HOOD stays > $100 through earnings; benefits from post-earnings IV crush. **Caps upside** — doesn't capture a big beat.

### The honest call on "squeeze before Aug 5"
- **Cleanest = Card A** (7/31 put credit spread on a dip): get paid for the run-up, exit before the binary.
- If you *insist* on playing the beat → **Card B (call debit spread)**, NOT a put credit spread — only the debit spread profits from a gap-up. Size small; remember Q1 fell on a beat.
- **Shares plan:** accumulate $92–100 on dips, trim into late-July strength, keep a core through earnings if conviction holds. Stop < $88.

---

## 📈 Growth screen — projected index-beaters (ZS · VEEV · MNDY)

_Added June 19. Screen: consensus upside > SPX bottom-up (+29% / 12mo). STNOW-scored, STKK-leveled, cached. **Personal account** ($25k–$100k, ~10% baseline per-trade, swing/income). Prices 6/18 close — re-run `STKK ZS VEEV MNDY` live before acting._

| Ticker | Price | Target | Upside | STNOW | Regime/RSI | Beta | Structural stop |
|---|---|---|---|---|---|---|---|
| **ZS** (Zscaler) | $124.72 | $200 | +60% | **+5 STRONG GO** | DOWN / RSI 38 | 0.99 | $103.78 |
| **VEEV** (Veeva) | $153.32 | $235 | +44% | **+5 STRONG GO** | DOWN / RSI 32 | 0.72 | $136.65 |
| **MNDY** (Monday) | $71.52 | $124.59 | +74% | +2 GO on trigger | DOWN / RSI 34 | 0.98 | $57.50 |

**Thesis:** beaten-down, **low-beta** quality software trading at deep discounts to Strong-Buy/Buy consensus. Oversold (RSI low-30s) in a downtrend → **buy stabilization (green reclaim), not the falling knife.**

### Entries, sizing & alerts (personal account)
| # | Ticker | Trigger to buy | Size (≈10% baseline) | Stop | Notes |
|---|---|---|---|---|---|
| 1 | **VEEV** | here / dip to ~$150 **that holds** | ~10% (lowest-vol → can go full) | $136.65 (−11%) or tighter ATR | "Sleep-at-night" core; best risk-[REDACTED] |
| 2 | **ZS** | here / dip to ~$120 **that holds** | ~10% | $103.78 (−17%) | Best STNOW + quality; durable 20%+ growth |
| 3 | **MNDY** | green reclaim **> $75** on volume | ~5–7% (higher vol 65%) | $57.50 (−20%) | Highest upside (+74%) but no trend yet; **exit before 8/10 earnings** unless conviction |

- ⚠️ **All DOWN-regime** → none are confirmed uptrends. The R:R (5×+) is real, but you're early; **scale in** (half now / half on reclaim) rather than full-size into a downtrend.
- 🔴 **Macro:** July 14 CPI · July 7 USTR tariff hearing — software is rate-sensitive; a hot CPI pressures multiples.
- 🎟️ Income tilt (optional): on a VEEV/ZS stabilization, a bull **put credit spread** below the structural stop expresses the same view with theta — ask for live strikes.

---

## Closed trades (record)

| Trade | Result | Notes |
|---|---|---|
| **AVGO put credit spread** $390/$387.5 · 13 contracts | **−$1,717** (closed 6/11 @ $1.80 debit) | Sold for $0.48 credit, bought back $1.80. AVGO crashed $481→$372 on earnings. **Closed Thu via GTC limit — beat the $2.03 mid, saved ~$909 vs $2,626 max loss, avoided assignment.** Lesson: never sell premium into a binary event a stock can gap through. |

---

## MARA pivot notes (Bitcoin → AI infrastructure)

**Thesis (their words):** "We started as a Bitcoin miner that purchased power. We are becoming a digital infrastructure company that owns power and deploys it across the highest-value applications: AI training/inference, critical IT, and flexible compute including Bitcoin mining."

Concrete moves:
1. **$1.5B Long Ridge acquisition** (Apr 30, 2026) — 505 MW gas plant + 1,600 acres in Hannibal, Ohio (PJM). Owned power +65% → ~2.2 GW. +$144M EBITDA. Closes 2H 2026.
2. **Sold ~$1.5B of Bitcoin** in Q1 (dropped #2 → #4 public BTC holder) to de-lever and fund the pivot.
3. **Starwood partnership** + acquired **Exaion** (French data-center unit).

Timeline: deal closes 2H 2026 → construction 1H 2027 → first AI capacity **mid-2028**.

**Re-rate comps (the playbook MARA wants to follow):**
- **Talen (TLN):** utility → "AI power landlord" after Amazon nuclear deal.
- **IREN:** Bitcoin miner → AI cloud (the direct proof of concept).
- **CoreWeave (CRWV):** pure-play AI neocloud (the end-state valuation).

**Catalyst to watch for MARA re-rate:** headline like _"MARA signs [hyperscaler] for X MW at Hannibal."_ Until then it trades as a Bitcoin proxy.

---

## Options cheat-sheet (quick reference)

| Concept | Plain English |
|---|---|
| **Sell puts below price** | "I bet it stays up" (bullish/neutral) — collect premium |
| **Buy puts** | "I bet it goes down" (bearish) |
| **Sell calls above price** | "I bet it doesn't rip" (bearish/neutral) |
| **Buy calls** | "I bet it goes up" (bullish) |
| **Put credit spread** | Sell a put + buy a lower put. Bullish/neutral, defined risk. Win if price stays above short strike |
| **Call debit spread** | Buy a call + sell a higher call. Bullish, defined risk, cheaper than long call |
| **Breakeven (put credit spread)** | Short strike − credit received |
| **IV crush** | Implied volatility collapses after earnings → options lose value fast |
| **Theta** | Time decay — works *for* you when selling, *against* you when buying |
| **Delta** | ~How much option moves per $1 of stock; rough probability of finishing ITM |

---

## Inverse / hedge ETFs (the "reverse" plays — go UP when market goes DOWN)

_Express a bearish view or hedge. Map each bearish trigger to its inverse ETF._

| If your bearish trigger fires... | The "reverse" expression |
|---|---|
| Semis break down (AVGO / SMH) | **SOXS** (−3x semis) |
| Nasdaq / AI rolls over | **SQQQ** (−3x Nasdaq) or **PSQ** (−1x, gentler) |
| Broad market risk-[REDACTED] | **SH** (−1x, safest) or **SDS** (−2x) |
| Volatility spike / crash | **UVXY** (decays fastest — hours/days only) |

**⚠️ Decay warning — these are TRADING tools, NOT buy-and-hold:**
- They reset leverage **daily** → **volatility decay** eats value over time, even if you're right on direction.
- Example: market −10% then +10% back to even → a −3x ETF ends **down**, not flat.
- **Hold days-to-weeks, never months.**

**Timing trap:** buying inverse ETFs *after* a big down day = catching a knife in reverse (you're buying the spike; markets often bounce). Best entry is **early in a decline / on a green day near resistance**, not after a −5% puke.

**For a $1k account:** prefer the **−1x versions (SH, PSQ)** — far less decay and reversal risk than the −3x rockets (SQQQ, SOXS, SPXU), which are tight-stop day-trades only.

---

## Next checkpoints

- [x] ~~June 10 — CPI~~ → headline hot (4.2%), core cooler (0.2%). Choppy, no clean trend.
- [x] ~~June 10–11 — ORCL earnings~~ → beat but −12% on AI-capex/debt worry. Bearish AI-infra read-through.
- [x] ~~June 12 — AVGO spread~~ → **CLOSED June 11 for −$1,717** (see Closed trades).
- [ ] **CRWV — primary entry alert:** green reclaim + close **above ~$95** off the $91–93 zone = first real long trigger.
- [x] **NNE — ✅ TRIGGER HIT (Jun 22):** reclaimed $24 → $26.36. **ARMED: Sell $23/$20 put credit (Jul 17), $0.82 credit / $217 max / BE $22.18 / RoR 38%.** GTC close @ $0.16 (80%); stop on close <$22; time-stop expiry wk. 1 contract (quarter-size). See options_watchlist.md.
- [ ] **HOOD — 🔔 ALERTS ARMED (Jun 19):** ① dip to **$100–102** → deploy 7/31 $100/$95 put credit spread (Card A); ② **$92–95** → add shares; ③ close **< $88** → cut; ④ reclaim **> $112** → consider 8/21 call debit spread. (Don't chase at $108.)
- [ ] **ORCL** — let it base post-earnings; no entry while it's a falling knife.
- [ ] **NTAP** — buy the pullback to ~$150–154 (don't chase $160 / RSI 69). Quality, low-beta.
- [ ] **📈 Growth screen (index-beaters):** **ZS** buy ≤$120 hold · **VEEV** buy ≤$150 hold (lowest-vol core) · **MNDY** reclaim >$75 then buy (exit before 8/10). All DOWN/oversold → buy stabilization, scale in.
- [ ] **TGTX — 🔔 PULLBACK ALERT (Jun 21):** at RSI 91 / $53 — **do NOT chase.** Buy the dip to **$46–48 (RSI<60)**; sell **$45/$40 put spread** on the dip (not now — far OTM pays ~$0.40). Catalysts: Aug 3 earnings; Phase 3 SC topline late-2026/early-2027.
- [ ] **GOOGL — 🟢 TRADE OF RECORD (Jun 21):** **Jul 17 $370/$390 call debit spread**, ~$712 debit / $1,288 max / BE $377 (+2.5%) / R:R 1.81:1. Target $390 (range top, ~6/30 sessions). Profit-take ~$1,000 (~80%); stop < $360 or −50%; time-stop 5 DTE. Low IV → buy. Tail risk = antitrust appeal ($300 bear case).
- [ ] **AVGO — 🟢 TIER-2 (Jun 21, math confirmed live):** **Jul 17 $410/$440 call debit**, $1,153 debit / $1,847 max / BE $421.52 / R:R 1.60:1. RSI 43, no earnings in window (next ~Sept). **Trigger: hold >$410** (breakout above post-crash $372–411 range); dip-add $405–410. Personal-acct size.
- [ ] **📝 META & AMZN — PAPER-TEST candidates (Jun 21, not live yet):** revisit + validate vs live chain before any real entry.
  - **META** Jul 17 **$575/$610** call debit · ~$13.30 debit / $2,170 max / BE $588.30 · **trigger: reclaim $600** (at $577 → needs +4%, likely won't trigger Mon).
  - **AMZN** Jul 17 **$245/$260** call debit · ~$5.25 debit / $975 max / BE $250.25 · **trigger: reclaim $250** (best R:R, smallest — fits $1k acct). _Marks are 6/18 close — re-pull live for the paper test._
- [ ] Watch **BTC + QQQ** daily for the AI-infra group turn.
- [ ] **July 7 — USTR tariff hearing** (Section 301). **July 14 — June CPI.** Headline risk.
