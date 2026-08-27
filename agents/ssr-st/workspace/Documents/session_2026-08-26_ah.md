# Session notes — Wed Aug 26, 2026 ~5:15 PM PT

After-hours. FULL CHECK was started then pivoted to news-portal login; cards in `catalyst_cards.md` are still the **Tue 8/25** overnight table. This file is the live dump from this session. Defined-risk only. Wait for **go**.

## Login / portals

- **WSJ** — signed in in the Cursor browser (`My Account`, no Sign In). Lead was the Nvidia earnings article.
- **IBD MarketTrend** — signed in via Dow Jones SSO (`myibd.investors.com` after WSJ). Header: **My Account**. Newsletter `ibdsilentlogin=true` does **not** carry a session by itself.
- **MarketWatch** — not separately logged this turn; same Dow Jones SSO as WSJ.
- **Whale Watch** — not a website. Robinhood MCP + `whale_check.py`.
- Skill wiring added: `news-portals` (Cursor browser → Safari/Chrome tail → public RSS). IBD MarketTrend is on that ladder.

## IBD MarketTrend (signed in)

Source: `https://research.investors.com/markettrend.aspx` + The Big Picture (Scott Lehtonen, **6:05 PM ET** 8/26). Homepage exposure widget (~8:07 PM ET).

**Close (IBD, 8/26 market close)**

| Index | Close | Chg |
|---|---|---|
| S&P 500 | 7675.70 | −1.58 (−0.02%) |
| DJIA | 53463.88 | −113.52 (−0.21%) |
| Nasdaq | 26130.20 | −21.10 (−0.1%) |
| NYSE vol (mil) | 410,060 | −15,966 (−3.8%) |
| Nasdaq vol (mil) | 706,532 | −42,696 (−5.7%) |

**Stock-market exposure: 40%–60% invested.** S&P and Nasdaq testing 21-day EMAs. Nasdaq still holding the 50-day. IBD: stay a bit defensive, selective on breakouts, cut losers fast; more weakness → cut exposure further.

**Psych indicators:** VIX **15.21** · put/call **0.65** · high-low **1.68** · bulls **51.9** vs bears **17.3** · margin debt **38.6**.

**The Big Picture (summary)**

- Sticky PCE into Warsh at Jackson Hole **Fri**. Headline July PCE **+0.2%** vs **0.1%** est; **3.7%** y/y vs **3.6%**. Core **+0.2%** / **3.3%** y/y as expected.
- CME: **~36%** odds of a hike at Sep 15–16; **~51%** by Oct 28.
- Industrials **+1.1%** was the sector win. Healthcare / communication services / consumer discretionary moderate losses. Volume down vs Tuesday.
- WTI **$82.23** (−0.2%, third down day, lowest close since Aug 13). 10-year **>4.66%**.
- At **6:05 PM ET** they had **NVDA ~−2% AH** on a weaker GM forecast, then an AWS/AMZN contract. By **~8:07 PM ET** the homepage had flipped to futures up; NVDA / CRWD / CRM jumping. Treat the 6:05 NVDA take as stale.
- **INTU** tumbled **>3%** (Wed first-30 is dead). **FFTY** +0.2%. IBD 50 movers named: ANET, VCTR, ECO, WPM.
- MarketSurge: **0** breaking out today, **10** near pivot; **MNST** near **50.17** flat-base.
- Watch: IBKR slipped the **97.84** entry; FDX toward **341.69** cup-with-handle; JMKE IPO base **24.99** / early-buy **24.47**.

## Robinhood tape (this session, ~5:00 PM PT)

| Name | RTH | AH (approx) |
|---|---|---|
| SPY | 766.08 | 770.75 |
| QQQ | 711.37 | 719.60 |
| SMH | 555.77 | 569.52 |
| VXX | 18.54 | — |
| NVDA | 209.66 | ~219.50 (~+4.7%) |
| CRWD | 189.18 | ~208 (~+10%) |
| CRM | 205.62 | ~232 |
| OKTA | 134.42 | ~162 (~+21%) |
| VEEV | — | ~269 |
| SNPS | — | slightly down |
| INTU | 345.88 (recovered from ~$322 AH Tue) | — |
| ZM | 93.83 (held the dump) | — |

**Macro:** Jul PCE already printed 8:30 ET — headline **3.7%** y/y (est 3.6%), core **3.3%**. Jackson Hole: Warsh keynote **Fri 8/28 ~10:00 ET**.

**Investor days:** none this week. SNDK ID was 8/13. **MRVL ID Tue Oct 6**. **INTU ID Wed Sep 17**.

## Wed 8/26 AMC prints (live)

| Ticker | Print | Street | Tape |
|---|---|---|---|
| **NVDA** | EPS **$2.22** vs **$2.09**; rev **$96.22B**; Q3 guide **$108B ±2%** | $2.09 | RTH $209.66 → AH ~$219.50. IBD also flagged weaker GM forecast + AWS/AMZN contract |
| **CRWD** | **$0.31** vs **$0.24** | $0.24 | AH ~$208 vs RTH $189.18 |
| **CRM** | RH actual **$5.90** vs street **$3.09** — **definition mismatch**; Yahoo ~+14% AH | $3.09 | RTH $205.62 → AH ~$232 |
| **OKTA** | **$1.05** vs **$0.86** | $0.86 | AH ~$162 vs $134.42 |
| **VEEV** | **$2.35** vs **$2.10** | $2.10 | AH ~$269 |
| **SNPS** | **$3.91** vs **$3.47** | $3.47 | AH slightly down |

## Card status (not yet written into `catalyst_cards.md`)

Tue-night cards that needed confirm / fire / kill this session:

| Ticker | Was | Now |
|---|---|---|
| INTU | arm Wed first-30 put | **kill** — first-30 gone; recovered to RTH **$345.88**; IBD had INTU **>3%** down |
| ZM | arm Wed first-30 put | **kill** — clock gone; RTH **$93.83** held the dump |
| PCE | stand-down credits | **done** — printed 8:30 ET |
| NVDA / CRWD / CRM / OKTA | arm Thu first-30 debit | **still arm** — 1× Sep 18 10-wide debit after Thu first 15–30. Call if hold/rip; put if dump. Cap **$4.00** (CRWD **$4.50**). No credit. Recalibrate 7:00 AM PT |
| VEEV | arm if named | AH bid; prefer NVDA/CRWD/CRM/OKTA first |
| SNPS | arm if named | AH slightly down — only if named after first-30 |
| MRVL | arm later (Thu AMC) | **still later** — street **$0.87**; first-30 **Fri**. Investor Day Oct 6. No credit through 8/27 |
| WDAY / ADSK | Thu AMC | arm Thu night if named |
| DG / DLTR / BBY | Thu BMO | skip unless asked |
| Jackson Hole Fri | — | **stand-down** new credits |

## Book

- **Personal** `789725611` (margin — this agent does not trade it). MS Sep 18 **210/200 PCS ×1**. Spot was ~$214–$217; abort **$210 tag or mid ≥ $4.50**; GTC **$1.25** live. MARA 100 + Sep 4 **$11C**.
- **Agentic** `407271451` (cash, tradable). Cash **$176**. MARA 100 + Sep 18 **$12C**. Shares + long options only.
- HOOD PCS already closed **+$198**. Do not replace this week.
- CRWD credit already flat **−$340**. Do not replace with a new credit. Debit card only, Thu.
- No leftover short premium into NVDA / CRWD / CRM / OKTA / VEEV.

## `daily.py` Health Check (finished 17:15 local, exit 0)

Ran ~13 min on INTU ZM NVDA CRWD CRM OKTA VEEV SNPS MRVL MS MARA HOOD SMCI AMD WDAY ADSK GOOGL AMZN META MSFT NOW DDOG SNOW. **Stale-cache scan — do not trade off it.**

- Macro, MANGOS, Whale: all **n/a**.
- Earnings gate said **none in window** — **false** vs live (NVDA/CRWD already printed; MRVL still Thu).
- INTU, ZM, OKTA, SNPS, ADSK: insufficient history / no chain.
- Ranked GO (shares / IV n/a): **MARA**, **AVGO**, **MS**. CRWD and VEEV WAIT/AVOID.
- Read-through radar used cache prices that do not match the Robinhood AH tape (e.g. MARA **$9.20** vs book ~**$11.83**). Ignore those prints.

## Calendar (still ahead)

- **Thu 8/27 AMC:** MRVL, WDAY, ADSK. **BMO:** DG, DLTR, BBY.
- **Fri 8/28:** Warsh Jackson Hole ~10:00 ET. No new high-risk credits.
- **Sep 17:** INTU Investor Day. **Oct 6:** MRVL Investor Day.

## Rules

- Defined-risk only. No credit through prints. First 15–30 for catalyst debits.
- Wait for **go**. Agentic sleeve: shares + long options only.
- IBD 40–60% exposure + Jackson Hole Fri = do not sell new premium into the binary.
