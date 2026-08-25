# Market Data Snapshot — Fri Aug 7, 2026 close

> **Purpose:** frozen reference so the agent does not re-pull quotes/chains/RSI for the week of Aug 10.
> **Captured:** Sat Aug 8, 2026 ~5:10 PM PT · **All prices are the Fri Aug 7 regular-session close**; "prev" = official Thu Aug 6 close.
> **Staleness rule:** valid through **Mon Aug 10 open**. Re-pull only the specific contract you are about to trade, and only right before sending the order. Everything else below can be reused all week for context, sizing, and structure math.
> Source: Robinhood MCP (`get_equity_quotes`, `get_option_quotes`, `get_option_instruments`, `get_equity_technical_indicators`, `get_earnings_calendar`, `get_portfolio`, `get_option_positions`, `get_equity_orders`) + web (CNBC / IG / Morningstar / Kalkine / Benzinga / MarketBeat).

---

## 1. Account — Individual `••••5611`

| Field | Value |
|---|---|
| Total value | **$61,016.95** |
| Cash | **$61,480.68** |
| Equity value | $26.27 (fractional dust only) |
| Options value | **−$490.00** |
| Buying power | $228,000.49 (margin) · **$57,000.12 unleveraged** |
| Crypto / futures / MF / FI | $0 |

### Open option positions

| Chain | Side | Qty | Avg price | Exp | Opened | Option UUID | Pending |
|---|---|---|---|---|---|---|---|
| **UNH** $400P | short | 2 | −$302.00 | 2026-08-21 | 2026-07-21 | `d6268f2e-d902-48e6-b7e2-70e09c71335d` | pending_buy 2 |
| **UNH** $390P | long | 2 | +$202.00 | 2026-08-21 | 2026-07-21 | `b18c17bf-2749-4f61-aa7d-cb510e776ac0` | pending_sell 2 |
| **XE** $12.50P | short | 2 | −$65.00 | 2026-08-21 | 2026-07-20 | `46a7277f-9ccc-41cb-a8d7-b8456bca58cb` | — |

Net UNH basis = **$1.00 credit** ($3.02 short − $2.02 long). XE basis = **$0.65 credit**.
⚠️ The pending buy/sell quantities on the UNH legs indicate a live GTC close order — verify it isn't stale before placing anything new on UNH.

### Equity positions (all fractional dust, ignore for sizing)

| Sym | Qty | Avg cost | | Sym | Qty | Avg cost |
|---|---|---|---|---|---|---|
| NIO | 0.776119 | $6.94 | | SKIL | 0.064474 | $15.51 |
| MARA | 0.076631 | $13.44 | | HPE | 0.018083 | $55.30 |
| MED | 0.053676 | $17.89 | | SMH | 0.001633 | $612.37 |
| HOOD | 0.046392 | $21.56 | | SMCI | 0.021184 | $47.21 |
| NNE | 0.040724 | $24.56 | | QNT | 0.017461 | $57.27 |
| MU | 0.011494 | $89.61 | | OKLO | 0.020218 | $49.46 |
| WDAY | 0.004073 | $245.52 | | | | |

### Closed this week

| Order | Detail |
|---|---|
| **U — sell 200 sh** | Limit $40.50, filled **avg $40.71**, fees $0.21, 2026-08-06 20:12:58 UTC, extended hours, placed_agent `user`, id `6a74eaca-6c96-48be-8617-53b50cd600a8` |
| **U realized** | Cost $29.88 × 200 = $5,976 → proceeds $8,141.79 = **+$2,165.79** |
| U campaign total | ≈ **+$2,296** including the previously harvested covered-call credit (+$130) |

---

## 2. Index / sector tape — Fri Aug 7 close

| Symbol | Close | Prev (8/6) | Chg |
|---|---|---|---|
| SPY | 773.20 | 768.56 | **+0.60%** |
| QQQ | 723.04 | 714.65 | **+1.17%** |
| IWM | 301.53 | 298.25 | +1.10% |
| DIA | 539.62 | 538.19 | +0.27% |
| VXX | 20.315 | 20.23 | +0.42% |
| **SMH** | 582.74 | 571.48 | **+1.97%** |
| XLY | 119.83 | 118.10 | +1.46% |
| XLK | 187.96 | 185.33 | +1.42% |
| XLB | 52.858 | 52.17 | +1.32% |
| XLV | 165.67 | 164.45 | +0.74% |
| XLU | 43.61 | 43.38 | +0.53% |
| XLRE | 44.99 | 44.81 | +0.40% |
| XLI | 185.15 | 184.76 | +0.21% |
| XLC | 111.255 | 111.18 | +0.07% |
| XLP | 85.12 | 85.11 | +0.01% |
| **XLF** | 57.62 | 57.81 | **−0.33%** |
| **XLE** | 57.495 | 58.16 | **−1.14%** |
| **GLD** | 398.485 | 389.67 | **+2.26%** |
| TLT | 82.745 | 82.52 | +0.27% |
| USO | 118.04 | 118.87 | −0.70% |

---

## 3. Single-name quotes — Fri Aug 7 close

### Tech / semis / mega-cap

| Sym | Close | Prev | Chg |
|---|---|---|---|
| NVDA | 223.90 | 218.99 | +2.24% |
| AMD | 483.50 | 489.28 | −1.18% |
| AVGO | 427.49 | 420.565 | +1.65% |
| MU | 877.56 | 881.47 | −0.44% |
| AMAT | 539.30 | 527.48 | +2.24% |
| LRCX | 311.43 | 305.77 | +1.85% |
| ORCL | 146.935 | 143.47 | **+2.42%** |
| CSCO | 121.42 | 120.88 | +0.45% |
| DELL | 453.775 | 437.65 | **+3.68%** |
| HPE | 53.220 | 52.43 | +1.51% |
| ANET | 188.635 | 192.32 | −1.92% |
| SMCI | 31.11 | 29.38 | **+5.89%** |
| MSFT | 499.89 | 499.86 | +0.01% |
| GOOGL | 354.24 | 357.75 | −0.98% |
| META | 592.08 | 589.90 | +0.37% |
| AAPL | 313.30 | 312.41 | +0.28% |
| AMZN | 274.45 | 272.26 | +0.80% |
| TSLA | 328.55 | 319.53 | +2.82% |
| NFLX | 74.12 | 73.69 | +0.58% |
| CRM | 192.73 | 186.77 | **+3.19%** |

### Financials / healthcare / industrials

| Sym | Close | Prev | Chg |
|---|---|---|---|
| MS | 216.25 | 213.75 | +1.17% |
| GS | 1039.46 | 1032.58 | +0.67% |
| JPM | 357.525 | 356.30 | +0.34% |
| BAC | 63.155 | 63.00 | +0.25% |
| C | 134.96 | 133.82 | +0.85% |
| SCHW | 107.58 | 107.66 | −0.07% |
| **UNH** | **407.10** | 403.97 | +0.77% |
| LLY | 1185.335 | 1191.94 | −0.55% |
| JNJ | 259.27 | 256.98 | +0.89% |
| ABBV | 245.89 | 243.87 | +0.83% |
| MRK | 128.57 | 128.37 | +0.16% |
| BA | 234.41 | 232.19 | +0.96% |
| CAT | 842.23 | 856.96 | −1.72% |
| GE | 370.115 | 374.55 | −1.18% |
| HON | 246.18 | 240.74 | +2.26% |
| UBER | 75.00 | 70.47 | **+6.43%** |
| RTX | 222.97 | 223.25 | −0.13% |
| DE | 620.92 | 614.84 | +0.99% |
| LMT | 587.79 | 582.85 | +0.85% |
| V | 362.39 | 370.47 | **−2.18%** |

### Energy / materials / utilities / consumer / crypto

| Sym | Close | Prev | Chg |
|---|---|---|---|
| XOM | 152.94 | 154.84 | −1.23% |
| CVX | 186.565 | 189.23 | −1.41% |
| COP | 117.61 | 116.76 | +0.73% |
| SLB | 50.52 | 51.54 | −1.98% |
| **NEM** | 112.99 | 105.43 | **+7.17%** |
| FCX | 69.615 | 68.18 | +2.10% |
| **AEM** | 178.83 | 167.92 | **+6.50%** |
| CEG | 269.98 | 261.10 | +3.40% |
| VST | 140.69 | 141.38 | −0.49% |
| **OKLO** | 48.43 | 42.19 | **+14.79%** |
| SMR | 9.83 | 9.47 | +3.80% |
| HOOD | 93.28 | 90.71 | +2.83% |
| COIN | 153.62 | 145.41 | **+5.65%** |
| MARA | 10.105 | 10.65 | −5.12% |
| WMT | 111.82 | 112.07 | −0.22% |
| COST | 947.78 | 949.15 | −0.14% |
| HD | 355.66 | 349.52 | +1.76% |
| NKE | 41.705 | 42.00 | −0.70% |
| SBUX | 105.60 | 105.16 | +0.42% |
| **XE** | **22.68** | 20.82 | **+8.93%** |

---

## 4. RSI(14), daily bars

| Symbol | Aug 5 | Aug 6 | **Aug 7** | Read |
|---|---|---|---|---|
| MS | 54.18 | 49.07 | **51.86** | Neutral, room |
| HPE | 64.94 | 62.44 | **63.93** | Bullish, mildly extended |
| ORCL | 54.84 | 54.03 | **56.68** | Healthy uptrend |
| HON | 59.28 | 52.22 | **56.37** | Healthy |
| CEG | 51.73 | 48.71 | **54.90** | Turning up |
| NVDA | 61.63 | 61.41 | **64.45** | Bullish, extended |
| NEM | 63.68 | 65.00 | **72.18** | 🔴 Overbought |
| UNH | 46.77 | 41.81 | **44.07** | 🔴 Downtrend |

---

## 5. Option chain IDs (stable — never need re-pulling)

| Underlying | chain_id |
|---|---|
| UNH | `0f76daa5-7cdc-4405-831d-3d430491fb1b` |
| XE | `c0d5c4f0-f855-4546-9b4e-f5f5dd597bb6` |
| MS | `962effc1-0b52-4648-b577-846096301fa7` |
| CEG | `047c6ef8-b036-4e7b-ba9c-224baefedf68` |
| NVDA | `8d629e37-6050-47e4-906e-1c0c4de93f71` |
| HPE | `87089e8e-93e0-44cb-a967-1e162498b0cf` |
| ORCL | `77540b42-f03d-446f-bd10-21433e57a086` |
| HON | `41675c7c-df9b-4705-a55d-cd5df72b1f6b` |

---

## 6. Option contract quotes — Fri Aug 7 close

**Contract UUIDs are permanent** — reuse them directly as `leg.option_id` in any order; only the prices go stale.

### Open book

| Contract | UUID | Bid | Ask | Mark | IV | Δ | OI | Vol | POP short |
|---|---|---|---|---|---|---|---|---|---|
| UNH Aug21 400P | `d6268f2e-d902-48e6-b7e2-70e09c71335d` | 4.50 | 5.20 | **4.850** | 26.8% | −0.345 | 2,150 | 180 | 72.4% |
| UNH Aug21 390P | `b18c17bf-2749-4f61-aa7d-cb510e776ac0` | 2.23 | 2.58 | **2.405** | 28.4% | −0.196 | 4,074 | 130 | 82.2% |
| XE Aug21 12.50P | `46a7277f-9ccc-41cb-a8d7-b8456bca58cb` | 0.00 | 0.05 | **0.025** | 130.8% | −0.005 | 2,831 | 64 | 99.0% |

UNH spread mark = **$2.445** vs $1.00 basis → **−$289** on 2. Greeks on UNH 400P: γ .0180, θ −.279, ν .281.
XE adjusted mark $0.010; θ −.0033. Prior close $0.01.

### Candidates

| Contract | UUID | Bid | Ask | Mark | IV | Δ | OI | Vol | POP short |
|---|---|---|---|---|---|---|---|---|---|
| **ORCL Aug21 135P** | `2cb1e7bf-9d64-4f57-87ff-c3bfc8a804c6` | 2.06 | 2.19 | **2.125** | 61.4% | −0.210 | 8,292 | 1,466 | 79.6% |
| **ORCL Aug21 132P** | `eea00c85-bd83-4f65-bfa9-a80d59f3be12` | 1.45 | 1.61 | **1.530** | 62.1% | −0.161 | 180 | 95 | 83.5% |
| **ORCL Aug21 130P** | `a7e62b62-0692-45b6-b2e2-d0381bf9a288` | 1.14 | 1.23 | **1.185** | 62.2% | −0.131 | 11,969 | 2,099 | 86.0% |
| **MS Sep18 200P** | `305b81d2-1951-4824-8c2c-15ef538fa4fb` | 2.60 | 2.90 | **2.750** | 31.7% | −0.204 | 4,459 | 21 | 80.4% |
| **MS Sep18 195P** | `445ca6bd-e0a7-404f-96ee-e1ebe804af6d` | 1.75 | 2.01 | **1.880** | 32.4% | −0.148 | 1,364 | 19 | 84.8% |
| **MS Sep18 190P** | `a67f39c0-fe12-4c4a-910b-2913ceaa19be` | 1.14 | 1.40 | **1.270** | 33.4% | −0.105 | 2,240 | 22 | 88.5% |
| **CEG Sep18 240P** | `590fb422-adbe-4ad5-aaf3-adf8982c5e10` | 4.40 | 5.30 | **4.850** | 46.4% | −0.194 | 2,200 | 409 | 80.0% |
| **CEG Sep18 230P** | `a199edfe-f5bf-4c56-87b2-e599349992ff` | 2.80 | 3.70 | **3.250** | 48.4% | −0.136 | 2,060 | 34 | 84.7% |
| **HPE Aug21 48P** | `007c5d97-5d1e-4326-9064-6761a2ba1941` | 0.66 | 0.90 | **0.780** | 69.3% | −0.192 | 1,036 | 32 | 80.7% |
| **HPE Aug21 45P** | `89f925e7-f415-40ad-81df-7eebffa248da` | 0.29 | 0.38 | **0.335** | 72.5% | −0.095 | 3,756 | 43 | 89.1% |
| NVDA Aug21 205P | `175f1562-67b6-4644-b0e8-949644c8bfea` | 0.84 | 0.88 | **0.860** | 39.3% | −0.105 | 24,764 | 3,781 | 89.1% |
| NVDA Aug21 195P | `b3244551-74a9-4749-a05c-30c2b278b6b7` | 0.37 | 0.38 | **0.375** | 45.5% | −0.047 | 25,709 | 2,212 | 94.7% |
| 🔴 HON Aug21 230P | `97387960-314e-4d45-b7d4-fbc048965c75` | 0.85 | 3.00 | 1.925 | 41.8% | −0.178 | 523 | **3** | 82.9% |
| 🔴 HON Aug21 220P | `c001fc5b-9d7d-46f6-8f5f-4e681e85c0b3` | 0.00 | 0.75 | 0.375 | 22.4% | −0.003 | 1,142 | **0** | 99.6% |
| UNH Sep18 390P (roll) | `4026f902-58e0-4d73-b71d-273ae0f6d20b` | 8.20 | 8.95 | **8.575** | 30.6% | −0.306 | 2,260 | 204 | 73.4% |
| UNH Sep18 380P (roll) | `4b0f62ce-d0c4-437a-b8f6-8bc074ad1d52` | 5.40 | 5.70 | **5.550** | 30.5% | −0.222 | 1,869 | 196 | 79.1% |

### Derived spread math (from the marks above)

| Spread | Credit | Width | Max loss | Credit/width | RoR | Cushion | Breakeven |
|---|---|---|---|---|---|---|---|
| **ORCL Aug21 135/130** | **$0.940** | $5 | $406 | 18.8% | **23.2%** | 8.1% | $134.06 |
| ORCL Aug21 135/132 | $0.595 | $3 | $240 | 19.8% | 24.7% | 8.1% | $134.41 |
| **MS Sep18 200/195** | **$0.870** | $5 | $413 | 17.4% | **21.1%** | 7.5% | $199.13 |
| MS Sep18 200/190 | $1.480 | $10 | $852 | 14.8% | 17.4% | 7.5% | $198.52 |
| **CEG Sep18 240/230** | **$1.600** | $10 | $840 | 16.0% | 19.0% | **11.1%** | $238.40 |
| **HPE Aug21 48/45** | **$0.445** | $3 | $255 | 14.8% | 17.4% | 9.8% | $47.56 |
| 🔴 NVDA Aug21 205/195 | $0.485 | $10 | $952 | **4.9%** | 5.1% | 8.4% | $204.52 |
| UNH roll 400/390 → Sep 390/380 | close $2.445 debit, open $3.025 credit = **+$0.58 net** | | new maxL $842/spread | | | 4.2% | $388.42 |

**Rejected on the numbers:** NVDA credit (4.9% credit-to-width — IV 39% says buy, not sell) · HON (bid/ask $0.85–$3.00 on 3 contracts of volume; long leg has no bid at all).

---

## 7. Earnings — Aug 10–14 (tradable / large-cap only)

| Date | AM | PM |
|---|---|---|
| **Mon 8/10** | MNDY, FERG, CAMT, CRC, AXSM, SNDA, DNB | SPG, HIMS, ACHR, RKLB, ACM, ASTS, PLUG, ALC, AAON, BBIO, DJT, UPWK, NIQ |
| **Tue 8/11** | SE, CAH, ONON, MIDD, LEGN, ARMK, ESLT, TME, RXT, ETOR, VG, SFD, YPF, VSTS | ⚠️ **SMCI**, ⚠️ **CRWV**, CAVA, LITE, FNV, HRB, PAGS, ATRO, NN, IFS, EVLV |
| **Wed 8/12** | AMCR, TRMB, NBIS, EAT, PFGC, GLBE, KTB, MSGE, ITRN, MRX, ASM | ⚠️ **CSCO**, COHR, HLIT, STAA, CAE, ENS, REZI, PAAS, STN, SUZ, PLGO |
| **Thu 8/13** | ⚠️ **XE**, JD, TPR, BIRK, MSGS, ASND, CLBT, PS, LUNR, BLSH, WWW, GDS, BN, YETI, AIT, MH | ⚠️ **AMAT**, NU, GLOB, CELC, DLO, HAWK, NKTR, QXO, STNE, BAP, JCAP |
| **Fri 8/14** | SIND, SGML, RLX, RMIX, MSADY, VOR, CVAC | CSAN, SKYT |

**Gated for the Aug 21 expiry but outside this window:** HD ~8/18 · TGT ~8/19 · WMT ~8/20 · **NVDA ~8/26** (Aug 21 clear, Sep 18 gated) · HPE ~9/2 (Aug 21 clear) · ORCL ~9/10 (Aug 21 clear) · MS next ~Oct · CEG next ~Nov.

---

## 8. Macro calendar & the week's facts

| When (ET) | Release | Consensus | Prior |
|---|---|---|---|
| Tue 8/11 | July existing home sales | 4,073K | 4,090K |
| **Wed 8/12 08:30** | **July CPI m/m** | **+0.1%** | −0.4% |
| **Wed 8/12 08:30** | **July CPI y/y** | **3.4%** | 3.5% |
| Wed 8/12 08:30 | Core CPI m/m · y/y | +0.2–0.3% · **2.5%** | 0.0% · 2.6% |
| Thu 8/13 08:30 | July PPI m/m · core | +0.1–0.2% · +0.3% | −0.3% · +0.1–0.2% |
| Thu 8/13 08:30 | Initial claims | 203–205K | 199K |
| Fri 8/14 08:30 | Retail sales · ex-autos | +0.1% · +0.2% | +0.2% · −0.2% |
| Fri 8/14 10:00 | UMich sentiment prelim | 54.5 | 54.2 |

**Hard facts as of Aug 7:**
- **July payrolls −23,000** vs +80,000 expected. May+June revised down a combined **103,000**. Unemployment **4.1%**. 264,000 left the labor force.
- **September rate-HIKE odds fell 67% → 44%** on the jobs miss (Kalkine cites ~60% still embedded in futures — sources disagree, treat 44–60% as the range). Next FOMC **Sept 15–17**.
- **S&P 500 closed 7,757.64 — record high, +3.6% on the week.** Dow also at a record.
- NDX rebounded **>10%** off the prior week's clearing-event low.
- **SOX +70% YTD but still ~17% below its late-June peak.**
- Oil fell **below $80**, easing yields and inflation caution.
- S&P is **+12% YTD**.

---

## 9. Whale / unusual options flow — Fri Aug 7

| Symbol | Type | Trade | Sentiment | Exp | Strike | Premium | OI | Volume |
|---|---|---|---|---|---|---|---|---|
| **NVDA** | PUT | SWEEP | **BULLISH** | 08/07 | $222.50 | $46.2K | 6.3K | **157.1K** |
| MSFT | PUT | SWEEP | Neutral | 08/07 | $500.00 | $37.8K | 1.8K | 29.7K |
| **NOW** | CALL | SWEEP | **BULLISH** | 08/21 | $125.00 | $52.4K | 7.0K | 3.7K |
| SKHY | CALL | TRADE | Bearish | 08/21 | $160.00 | $708.0K | 3.3K | 3.4K |
| HUBS | CALL | TRADE | Bearish | 08/21 | $240.00 | $689.9K | 209 | 3.0K |
| **AAL** | CALL | SWEEP | **BULLISH** | 09/18 | $17.00 | $34.0K | 34.4K | 2.6K |
| **UBER** | PUT | SWEEP | **BULLISH** | 09/18 | $82.50 | $25.5K | 431 | 71 |
| BE | PUT | SWEEP | Bearish | 08/21 | $180.00 | $29.9K | 3.3K | 380 |
| RUN | CALL | SWEEP | Bearish | 01/15/27 | $15.00 | $31.1K | 6.8K | 339 |
| RDW | CALL | TRADE | Bearish | 11/20 | $15.00 | $26.0K | 1.9K | 244 |
| QXO | CALL | TRADE | Neutral | 10/16 | $14.00 | $30.5K | 1.4K | 106 |
| ETN | PUT | SWEEP | Bearish | 08/28 | $415.00 | $26.6K | 1 | 99 |
| MOD | PUT | SWEEP | Bearish | 11/20 | $140.00 | $42.6K | 4 | 46 |
| RKLB | PUT | TRADE | Bearish | 08/14 | $89.00 | $30.1K | 6 | 31 |
| GEV | CALL | TRADE | Neutral | 12/15/28 | $400.00 | $66.4K | 93 | 30 |

**SentinelOne (S) — cleanest conviction print of the day.** 22,967 calls bought, **+54%** vs the 14,948 average. Includes a single **$160,000 sweep of 2,000 contracts, Aug 21 $19 calls at $0.80**. Stock $21.27 (+$0.51), 52-week range $11.81–$21.51, 50-dma $17.36, 200-dma $15.42, market cap $7.29B. Revenue +20.8% y/y, EPS $0.04 beat. Consensus Moderate Buy, PT $19.93. Volume 2.09M vs 7.98M average.

**Twilio (TWLO):** 11,953 calls, **+96%** vs the 6,091 average.

**Net read:** bullish tech (NVDA put-selling into strength, NOW/S/TWLO call buying) and bullish transport (AAL, UBER put-selling). Bearish tail confined to BE, ETN, MOD, RKLB and call-selling in HUBS/SKHY.

---

## 10. Reuse guide

| Question | Answer from this file |
|---|---|
| What's my book worth? | §1 — marks are Fri close, UNH spread $2.445, XE $0.025 |
| What are the option UUIDs to place an order? | §6 — permanent, never re-pull |
| Which chain_id for a new strike lookup? | §5 |
| Is name X gated by earnings? | §7 |
| What's the RoR on spread Y? | §6 derived table |
| Is the tape risk-[REDACTED]? | §2 |
| What's the macro binary? | §8 — **CPI Wed 8/12 08:30 ET** |
| Whale posture? | §9 |

**Must re-pull before sending any order:** the exact contract marks for the legs you're trading (§6 prices only). Everything else in this file holds for the week.
