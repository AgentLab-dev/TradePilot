# Growth Sleeve — Full Research Record
### Run date: Sun Aug 9, 2026 · Market data: Fri Aug 7, 2026 close (19:59:59 UTC snapshot)

Companion to `plan_300x1000_review.md`. That file is the decision document —
this one is the evidence behind it. Everything here is raw output, real quotes,
and the reasoning that turned 36 names into 4 tickets.

**Purpose: do not re-pull this data.** Quotes below are Friday's close and are
valid as a reference through the week. Re-pull only at the moment of execution.

---

## 1. Mandate

| Constraint | Value | Consequence |
|---|---|---|
| Max risk per ticket | $300 | Caps debit; excludes MU, LLY, GS, DELL, AMD, GEV entirely |
| Min return per ticket | $1,000 | With the risk cap, forces **R:R ≥ 3.34:1** |
| Binding constraint | **The ratio** | Not the dollar amounts — size contracts to the budget |

**Structures the mandate permits:** call debit spread (workhorse), long call
(uncapped, worse expectancy), diagonal/calendar (liquidity-limited here).

**Structures the mandate excludes by arithmetic:** put credit spread, covered
call, cash-secured put. Max gain on a credit structure is the credit received,
which is always less than the width — it cannot reach 3.34:1. The income book
still exists; it just cannot live in this sleeve.

---

## 2. Final tickets

### Tier 1 — clears every gate

| # | Ticket | Debit | Risk | Max gain | R:R | Breakeven | Sim win% | Expectancy |
|---|---|---|---|---|---|---|---|---|
| 1 | HOOD Sep18 $105/$120 call debit | $2.49 | $249 | $1,251 | 5.0x | $107.49 (+15.2%) | 53% | **+30%** |
| 2 | NEM Sep18 $120/$135 call debit | $2.95 | $295 | $1,205 | 4.1x | $122.95 (+8.8%) | 52% | **+27%** |
| 3 | PLTR Sep18 $195/$210 call debit | $2.29 | $229 | $1,271 | 5.6x | $197.29 (+14.7%) | 51% | **+27%** |
| 4 | CCJ Sep18 $105/$120 call debit | $2.76 | $276 | $1,224 | 4.4x | $107.76 (+10.7%) | 43% | **+14%** |

**Total: $1,049 risk → $4,951 at max.**

### Tier 2 — conditional

| # | Ticket | Debit | Risk | Max gain | R:R | Breakeven | Sim win% | Expectancy | Blocker |
|---|---|---|---|---|---|---|---|---|---|
| 5 | MPC Sep18 $330/$350 call debit | $3.03 | $303 | $1,697 | 5.6x | $333.03 (+11.7%) | 37% | +6% | Book too thin (OI 341–773, vol 2–24) |
| 6 | *empty* | — | — | — | — | — | — | — | No qualifying name exists at this budget |

### Alternate sizings priced and simulated

| Ticket | Risk | Max gain | R:R | Expectancy | Note |
|---|---|---|---|---|---|
| HOOD Sep18 105/125c @ $2.93 | $293 | $1,707 | 5.8x | +28% | More gain, slightly worse expectancy |
| HOOD Sep18 110/125c @ $1.87 | $187 | $1,313 | 7.0x | +26% | Cheapest entry, highest ratio, furthest breakeven (+19.9%) |
| PLTR Sep18 190/210c @ $3.40 | $340 | $1,660 | 4.9x | +28% | Over the $300 cap |
| NEM Sep18 115/130c @ $4.15 | $415 | $1,085 | 2.6x | +31% | Best expectancy in the book, but over cap and under ratio |

---

## 3. Per-ticket evidence

### HOOD — Robinhood Markets
- **Spot** $93.29 · **IV** 64.6% · **Sector** Financials / fintech
- **Long leg $105:** bid $3.85 / ask $4.00 (3.8% spread), delta 0.334, **OI 5,830**, volume 201
- **Short leg $120:** bid $1.46 / ask $1.53 (4.7% spread), delta 0.154, **OI 7,317**, volume 778
- **Fills used:** buy $3.966 (high_fill_rate_buy), sell $1.476 (high_fill_rate_sell) → **$2.49 debit**
- **Earnings:** Q2 reported Jul 29 — **$0.62 actual vs $0.41 est (+51% beat)**. Next: **Nov 4** (past expiry) ✓
- **Base rates:** 2-week win 62% (best in universe), 10-week win 70%
- **Chain quality:** best of any candidate — 3–7% spreads across all strikes, thousands of contracts of volume
- **Against it:** needs +15.2% in six weeks; high beta, will lead the downside

### NEM — Newmont
- **Spot** $112.98 · **IV** 44.5% · **Sector** Materials / gold
- **Long leg $120:** delta 0.379, **OI 7,700**
- **Short leg $135:** delta 0.147, **OI 14,571**
- **Fills used:** buy $4.088, sell $1.136 → **$2.95 debit**
- **Earnings:** Q2 reported Jul 23 — **$2.10 actual vs $2.18 est (MISS)**, first miss in 8 quarters. Next: **Oct 22** ✓
- **Base rates:** 2-week win 60%, 10-week win 67%
- **Lowest hurdle in the book at +8.8%** — why it survives a stop-heavy path
- **Against it:** the move is gold-price-driven, not company-driven. This is a metals trade wearing an equity ticker

### PLTR — Palantir
- **Spot** $172.01 · **IV 52.6%** · **Sector** Software / AI
- **Long leg $195:** bid $4.45 / ask $4.60 (3.3%), delta 0.270, **OI 2,335**, volume 1,234
- **Short leg $210:** bid $2.26 / ask $2.34 (3.5%), delta 0.156, **OI 6,778**, volume 1,334
- **Fills used:** buy $4.566, sell $2.278 → **$2.29 debit**
- **Earnings:** reported early Aug. Next past expiry ✓
- **Base rates:** 2-week win 60%, 10-week win 65%
- **THE KEY FACT — implied 52.6% vs realized 92%.** Options priced for roughly
  half the movement the stock actually delivers. This is the IV-routing matrix's
  textbook buy condition and the strongest single argument in the whole sleeve
- **Against it:** the 2-year sample ran **+559%**, so the backtest hit rate is
  partly a statement about the tape rather than the trade

### CCJ — Cameco
- **Spot** $97.39 · **IV** 48.7% · **Sector** Energy / nuclear
- **Long leg $105:** bid $3.40 / ask $3.60 (5.7%), delta 0.359, OI 1,338, volume 88
- **Short leg $120:** bid $0.73 / ask $1.00 (31%), delta 0.120, OI 1,693, volume 24
- **Fills used:** buy $3.550, sell $0.787 → **$2.76 debit**
- **Earnings:** Q2 reported Jul 31 — **$0.13 actual vs $0.36 est (−64% MISS)**. Next: **Oct 30** ✓
- **Base rates:** 2-week win 57%, 10-week win 65%
- **FRESH-OI SIGNAL — strongest in the book:**

| Strike | Volume | Open interest | Vol ÷ OI | Read |
|---|---|---|---|---|
| $100 | **5,118** | 8,988 | 0.57 | Heavy new positioning |
| $110 | **7,413** | 11,571 | 0.64 | Heavy new positioning |
| $105 | 88 | 1,338 | 0.07 | Quiet |
| $120 | 24 | 1,693 | 0.01 | Quiet |

  The whales are in the **$100 and $110** strikes. Our $105/$120 structure is
  *adjacent to* the flow, not in it. Trading $100/$110 would put you in the
  liquid strikes but yields only 2:1 — fails the mandate. This is a real
  tension, stated rather than hidden.
- **Against it:** the EPS miss was severe; the flow is a uranium bet, not a
  company bet. Lowest win rate in Tier 1. **Volume shows size, not direction** —
  large call volume can be an opening buy or a covered-call seller, and the data
  cannot distinguish them

### MPC — Marathon Petroleum (conditional)
- **Spot** $298.20 · **IV** 37.8% · **Sector** Energy / refining
- **Long leg $330:** bid $4.50 / ask $5.20 (14%), delta 0.236, OI 773, **volume 13**
- **Short leg $350:** bid $1.90 / ask $2.60 (31%), delta 0.125, OI 599, **volume 12**
- **Fills used:** buy $5.064, sell $2.035 → **$3.03 debit**
- Q2 beat EPS by 44% and the stock **fell 4.2%** — sold the news
- **Blocker:** volume of 12–13 contracts is not a market you can exit into

---

## 4. The liquidity gate — what it killed

This did more work than any other filter. Names that passed price and momentum
and died on the option book:

| Name | Chain evidence | Verdict |
|---|---|---|
| **HWM** | $320 call: **$1.40 bid / $2.75 ask (96% spread)**, 3 contracts traded, OI 386 | Reject — *and it scored +18% expectancy, ranked #3 overall* |
| EXPE | $350 call: $3.90 bid / $7.30 ask (60% spread), 3 contracts | Reject |
| SCCO | Same pattern | Reject |
| TER | Same pattern | Reject |
| GKOS | **Zero open interest** on the $185 strike | Reject |
| MPC | OI 341–773, volume 2–24, spreads 13–27% | Tier 2 only |
| NTAP, HON | Prior sessions, same failure | Already rejected |

**HWM is the cautionary case.** Full backtest, structure built, ranking slot
assigned — all spent on something you could not get out of. Six names across
three sessions is a pattern, so liquidity is now the **first** gate.

**Standing minimum bar to proceed to analysis:**
- bid-ask ≤ 15% of mid on **both** legs
- open interest ≥ 500 on both
- same-day volume > 0 on both

---

## 5. Backtest — method and full output

### Method
Two years of split-adjusted daily bars (Aug 2024 → Aug 2026), **476 overlapping
six-week windows** per name. Each window reprices **both legs** with
Black-Scholes every single day and applies the live rules:

- Take profit at **+100% of debit**
- Stop at **−50% of debit**
- Otherwise settle at expiry intrinsic

Debits built from `high_fill_rate_buy` / `high_fill_rate_sell` — **not mids.**
Mid-price fills are a fiction that flatters every result.

**Stated limitations:** IV is held constant along each path, so vol expansion
and crush are both unmodeled. The two-year sample is predominantly a bull tape.

### `debit_sim.py` output — real chain quotes

```
SYM   STRUCTURE                  risk  maxGain    R:R   win%   TP%  stop%     exp$    exp%     N
--------------------------------------------------------------------------------------------------------
NEM   Sep18 120/135c @ 2.95       295     1205   4.1x    52%   51%    48%      +81    +27%   476
PLTR  Sep18 195/210c @ 2.29       229     1271   5.6x    51%   51%    49%      +61    +27%   476
PLTR  Sep18 190/210c @ 3.40       340     1660   4.9x    52%   52%    48%      +97    +28%   476
HOOD  Sep18 105/120c @ 2.49       249     1251   5.0x    53%   53%    47%      +74    +30%   476
HOOD  Sep18 105/125c @ 2.93       293     1707   5.8x    52%   52%    48%      +83    +28%   476
HOOD  Sep18 110/125c @ 1.87       187     1313   7.0x    51%   51%    49%      +48    +26%   476
CCJ   Sep18 105/120c @ 2.76       276     1224   4.4x    43%   43%    57%      +40    +14%   476
MPC   Sep18 330/350c @ 3.03       303     1697   5.6x    37%   37%    63%      +18     +6%   476
OKTA  REJ Aug21 155/170c          292     1208   4.1x    28%   25%    71%      -28    -10%   496
NOW   REJ Sep18 135/150c          340     1160   3.4x    25%   23%    74%      -45    -13%   476
MSFT  REJ Sep18 560/590c          217     2783  12.9x    21%   21%    79%      -40    -18%   476
```

### `debit_test.py` output — reach/touch rates against sample trend

```
SYM   STRUCTURE                 BE%  reachBE   touch  2wkWin   hold80   sample   worst    N
------------------------------------------------------------------------------------------------
NEM   Sep18 120/135 @ 2.95     +8.8      43%     67%     60%    98.35  +128.0%  -29.4%  476
OKTA  Aug21 155/170 @ 2.92     +6.5      26%     43%     52%   133.76   +62.3%  -28.0%  496
PLTR  Sep18 195/210 @ 2.29    +14.7      38%     66%     60%   145.65  +559.5%  -33.0%  476
NOW   Sep18 135/150 @ 3.40    +10.8      20%     40%     47%   103.80   -23.0%  -34.9%  476
MPC   Sep18 330/350 @ 3.03    +11.7      27%     41%     58%   265.46   +72.2%  -21.3%  476
MSFT  Sep18 560/590 @ 2.17    +12.4       8%     15%     51%   458.57   +19.9%  -19.6%  476
```

Read every rate against the `sample` column. PLTR's 38% reach rate sits on a
+559% run — that is the tape talking, not the trade. NOW's 20% sits on a −23%
sample, which is the trade talking, and it says no.

### `screen_debit.py` output — full 32-name universe

Synthetic Black-Scholes structures priced off realized vol × 1.15, used for
**candidate generation only**. No name is ranked or rejected on a synthetic price.

```
SYM         spot  IVest        K1        K2  qty   risk$   gain$    R:R    BE%   win%    exp%     N
------------------------------------------------------------------------------------------------------------
HOOD       93.29   74%    107.31    111.05    3     259     863   3.3x +16.0%    52%    +28%   476
NEM       112.98   51%    125.41    134.45    1     175     729   4.2x +12.5%    47%    +20%   476
HWM       281.88   31%    301.62    312.90    1     230     898   3.9x  +7.8%    45%    +18%   476
OKLO       48.42  100%     53.75     66.36    1     276     985   3.6x +16.7%    44%    +16%   476
CCJ        97.39   49%    104.21    115.91    1     257     913   3.6x  +9.6%    44%    +15%   476
CRWD      214.42   64%    242.30    255.17    1     284    1003   3.5x +14.3%    42%    +13%   476
VLO       298.31   41%    331.14    343.08    1     218     976   4.5x +11.7%    41%    +11%   476
NNE        18.85   96%     22.04     24.04    6     267     933   3.5x +19.3%    39%     +9%   476
MPC       298.20   39%    325.02    336.94    1     244     948   3.9x  +9.8%    39%     +8%   476
WMT       111.85   27%    115.21    126.41    1     238     882   3.7x  +5.1%    38%     +8%   476
FCX        69.62   54%     77.27     82.83    2     229     883   3.9x +12.6%    37%     +5%   476
AVGO      427.76   50%    491.96    509.08    1     280    1432   5.1x +15.7%    37%     +5%   476
NVDA      223.96   45%    244.12    257.56    1     290    1054   3.6x +10.3%    36%     +4%   476
EXEL       54.07   46%     54.61     68.65    1     295    1109   3.8x  +6.4%    35%     +1%   476
VST       140.59   57%    158.86    164.48    2     238     886   3.7x +13.8%    32%     -2%   476
SMCI       31.13  109%     34.54     42.60    1     185     621   3.3x +16.9%    32%     -3%   476
PLTR      172.01  106%    208.13    215.01    1     157     531   3.4x +21.9%    30%     -6%   476
MARA       10.09  110%     10.19     15.19    2     230     770   3.4x +12.4%    30%     -6%   476
ANET      188.67   73%    216.95    224.49    1     174     580   3.3x +15.9%    28%     -7%   476
COIN      153.60   80%    179.70    185.84    2     273     955   3.5x +17.9%    28%     -8%   476
DELL      453.77   97%    585.43    603.59    1     299    1517   5.1x +29.7%    28%     -9%   476
OXY        55.91   44%     60.95     64.31    4     283    1061   3.7x +10.3%    26%    -11%   476
NBIX      163.41   49%    178.12    191.20    1     285    1023   3.6x +10.7%    26%    -12%   476
SLB        50.53   46%     54.07     60.13    2     252     960   3.8x  +9.5%    25%    -13%   476
LLY      1185.71   44%   1505.80   1576.93    1     250    6863  27.5x +27.2%    25%    -13%   476
OKTA      148.32   62%    167.62    173.56    2     269     919   3.4x +13.9%    24%    -13%   476
NTRA      322.10   76%    376.84    389.72    1     278    1010   3.6x +17.9%    24%    -13%   476
PANW      363.86   64%    425.74    440.30    1     270    1186   4.4x +17.7%    22%    -17%   476
CELH       27.77  105%     30.29     39.25    1     197     699   3.6x +16.2%    22%    -18%   476
GS       1039.61   52%   1320.28   1361.86    1     272    3886  14.3x +27.3%    20%    -20%   476
NOW       124.88   72%    141.13    151.13    1     228     772   3.4x +14.8%    16%    -26%   476
MSFT      499.99   58%    594.99    614.99    1     298    1702   5.7x +19.6%     7%    -40%   476
```

**Critical caveat on this table:** the IV estimates are realized-vol proxies and
diverge badly from quoted implied vol on high-beta names.

| Name | Synthetic IV | Actual quoted IV | Synthetic verdict | Real verdict |
|---|---|---|---|---|
| **PLTR** | 106% | **52.6%** | −6% (reject) | **+27% (Tier 1)** |
| NOW | 72% | 57.9% | −26% | −13% (still reject) |
| OKTA | 62% | 58.6% | −13% | −10% (still reject) |
| HOOD | 74% | 64.6% | +28% | +30% |
| NEM | 51% | 44.5% | +20% | +27% |

The PLTR row is why synthetic screens generate candidates and never rank them.

---

## 6. The "80% probability" question — three honest answers

**An 80% chance of a two-week gain does not exist.** The base rate for any
liquid US equity is 52–55%; nothing in this universe exceeds 62%. Three
measurable substitutes:

| Name | (a) 80%-hold level | Cushion | (b) 2-week win | (c) 10-week win | Best 2wk | Worst 2wk |
|---|---|---|---|---|---|---|
| **HOOD** | $75.71 | −18.8% | **62%** | 70% | +43.9% | −31.6% |
| NEM | $98.35 | −12.9% | 60% | 67% | +25.0% | −23.0% |
| PLTR | $145.65 | −15.3% | 60% | 65% | +56.9% | −32.3% |
| **WMT** | $103.11 | **−7.8%** | 60% | **73%** | +16.1% | −15.2% |
| MPC | $265.46 | −11.0% | 58% | 66% | +21.3% | −20.5% |
| CCJ | $83.58 | −14.2% | 57% | 65% | +24.2% | −18.8% |
| NVDA | $198.58 | −11.3% | 57% | 64% | +29.9% | −21.1% |

- **(a)** derived from each name's own IV over six weeks (20th percentile of a
  lognormal). The closest real thing to "80% confidence."
- **(b)** measured over 476 overlapping windows. **HOOD's 62% is the ceiling.**
- **(c)** odds improve materially with holding period.

**If probability is what you actually want, the answer is WMT** — 73% over ten
weeks, only −7.8% of downside cushion needed, lowest IV in the book at 27%. It
will not produce $1,000 on $300 quickly. **The mandate and the probability
target pull in opposite directions.**

---

## 7. Rejections — full audit trail

| Name | Expectancy | Reason |
|---|---|---|
| MSFT Sep18 560/590c | **−18%** | 12.9:1 ratio, but only **7%** of windows reached breakeven. A lottery ticket wearing a spread's clothing |
| NOW Sep18 135/150c | **−13%** | 16% reach rate, IV 57.9% (expensive to buy), 2-year sample **down 23%** |
| OKTA Aug21 155/170c | **−10%** | IBD Stock of the Day; only 24% of 2-week windows clear +6.5%. The pre-earnings vol ramp is a real *unmodeled* tailwind — not enough to flip −10% |
| HWM | +18% on math | **Liquidity** — 96% bid-ask spread |
| EXPE, SCCO, TER, GKOS | n/a | **Liquidity** |
| CELH | −18% | Negative; also failed the anti-chase gate in a prior session |
| MARA | −6% | Negative |
| SMCI | −3% | Negative |
| MU, LLY, GS, DELL, AMD, GEV | n/a | **No structure exists** — debit for any ≥3.34:1 spread exceeds the $300 cap |

### On chips specifically
The semiconductor complex **does not support this mandate right now.** NVDA
(+4%) and AVGO (+5%) are the best of them; MU and AMD cannot produce a
qualifying structure inside $300; SMCI is negative. That is a finding, not an
omission.

### On the names you named
| Name | Verdict |
|---|---|
| MARA | −6% expectancy — reject |
| NNE | +9% expectancy — marginal, screen-only, no chain pulled |
| HOOD | **+30% — Tier 1, ticket #1** |
| MU ("micro") | No qualifying structure inside $300 |
| SMCI | −3% — reject |
| OKLO | +16% screen-only — the best unpulled nuclear candidate after CCJ |
| OKTA (IBD SoD) | −10% — reject |

---

## 8. Event gate — earnings verified

| Name | Last report | Result | **Next report** | Clear of Sep 18 expiry? |
|---|---|---|---|---|
| HOOD | Jul 29 | $0.62 vs $0.41 est (**+51% beat**) | **Nov 4** | ✓ |
| NEM | Jul 23 | $2.10 vs $2.18 est (**miss**) | **Oct 22** | ✓ |
| CCJ | Jul 31 | $0.13 vs $0.36 est (**−64% miss**) | **Oct 30** | ✓ |
| PLTR | early Aug | — | past expiry | ✓ |
| MPC | early Aug | beat 44%, **stock fell 4.2%** | past expiry | ✓ |

For debit spreads the event gate is **inverted** relative to credit spreads —
a catalyst inside the window is welcome, IV crush is the risk. All five are
clean either way.

---

## 9. Concentration risk — read this before sizing

**All four Tier 1 tickets are long-delta call debit spreads.** This is forced by
the mandate, not chosen. The consequence:

> The sleeve is **one bet expressed four times.** If CPI runs hot Wednesday
> Aug 12 and the tape sells off, every ticket loses together. The income book
> (put credits on MS / DELL / HPE / UNH) never had this property.

**The only candidate that would genuinely diversify it is WMT** — consumer
staples, IV 27%, low beta, the one name that would not fall with the others on
a rate shock.

### Sequencing around CPI

| When | Action | Cumulative risk |
|---|---|---|
| **Mon Aug 10** | Enter **HOOD and NEM only** — lowest hurdle, best books | $544 |
| Tue Aug 11 | No new entries. Confirm fills, set GTC exits | $544 |
| **Wed Aug 12** | **CPI. No new entries.** Two live tickets are the whole exposure | $544 |
| Thu Aug 13 | If CPI benign, add PLTR and CCJ | $1,049 |
| Fri Aug 14 | MPC only if its chain tightened. Decide the 6th slot | $1,352 |

### Management — identical on every ticket
- **GTC sell at +100% of debit.** This is the exit the backtest is built on.
  Holding for full max gain was modeled separately and is **negative-EV**
- **Stop at −50% of debit**
- **Hard close by Sep 11** (one week before expiry) to avoid gamma
- **If the S&P closes below its 20-day after CPI, close the whole sleeve** —
  these are correlated, so manage them as one position, not four

---

## 10. Artifacts produced this run

### Scripts
| File | Purpose |
|---|---|
| `debit_sim.py` | Day-by-day BS repricing of both legs with managed exits. **The authoritative expectancy number** |
| `debit_test.py` | Reach/touch rates, 2-week base rates, IV-implied 80%-hold levels, sample trend |
| `screen_debit.py` | Synthetic universe screen. Candidate generation only |
| `rs_multi.py` | Multi-window RS (1d/1w/1mo/10w) + price-vs-volume ACCUM/DISTRIB flags |
| `rs_screen.py` | Relative-strength screen with true-lookback guard |
| `breach_test.py` | Path-aware breach test for **credit** structures (income book) |

### Cached data — do not re-pull
| File | Contents |
|---|---|
| `market_data/daily_6_2024-08_to_2026-08.json` | NEM, OKTA, PLTR, NOW, MPC, MSFT — 2y daily |
| `market_data/daily_chips.json` | SMCI, MU, MARA, NNE, HOOD, AMD, NVDA, AVGO, ANET, COIN |
| `market_data/daily_energy.json` | GEV, VST, OKLO, CCJ, VLO, OXY, SLB, FCX, HWM, AGX |
| `market_data/daily_health_fin.json` | LLY, EXEL, NBIX, NTRA, CRWD, PANW, DELL, GS, WMT, CELH |
| `market_data/week_2026-08-03_tail.json` | Synthesized weekly bars, w/e Aug 7 |
| `Documents/market_data_snapshot_2026-08-07.md` | Prior snapshot — account, indices, quotes, RSI, option UUIDs |

### Lessons logged this run (`agent_learning_log.md`)
1. **A screening threshold in the wrong units silently deleted a third of the
   universe** — `$1,000 per contract` vs `3.34:1 ratio`. Five named tickers
   vanished with no error. Screens must now print rejections with reasons.
2. **Realized vol is not implied vol, and the gap between them IS the trade** —
   PLTR at implied 52.6% vs realized 92%. Implied-minus-realized is now a
   ranking input, not a byproduct.
3. **Liquidity is now the FIRST gate, not the last** — six names across three
   sessions. Chain check happens before any backtest runs.

---

## 11. Watchlists — spec (NOT yet created in Robinhood)

Attempted to create these via the Robinhood MCP on Aug 9. **All watchlist tool
calls failed** with a client-side error (`Could not find bubble for toolCallId`),
five attempts. Equity quote and historical reads on the same server work fine,
so this is specific to the watchlist tools' approval flow, not the connection.

Create manually in the app, or retry the MCP after a Cursor restart.

### 🎯 Growth Sleeve Aug26
*Tier 1 call debit spreads — the four live tickets*

| Symbol | Structure | Risk | Target |
|---|---|---|---|
| HOOD | Sep18 $105/$120c @ $2.49 | $249 | $1,251 |
| NEM | Sep18 $120/$135c @ $2.95 | $295 | $1,205 |
| PLTR | Sep18 $195/$210c @ $2.29 | $229 | $1,271 |
| CCJ | Sep18 $105/$120c @ $2.76 | $276 | $1,224 |

### 📋 Growth Bench
*Screen-positive, chains not pulled — candidates for the empty 6th slot*

`MPC` `WMT` `OKLO` `NNE` `NVDA` `AVGO` `CRWD` `VLO`

WMT is the priority pull — the only one that diversifies the all-long-delta
concentration instead of compounding it.

### 🚫 Liquidity Rejects
*Passed price and momentum, failed the option book. Re-check only if spreads tighten*

`HWM` `EXPE` `SCCO` `TER` `GKOS` `NTAP` `HON`

### Options watchlist — the 8 Tier-1 legs

| Symbol | Expiry | Long leg | Short leg |
|---|---|---|---|
| HOOD | 2026-09-18 | $105 call | $120 call |
| NEM | 2026-09-18 | $120 call | $135 call |
| PLTR | 2026-09-18 | $195 call | $210 call |
| CCJ | 2026-09-18 | $105 call | $120 call |

---

## 12. Open limits of this analysis

1. **Prices are Friday's close.** Everything re-prices Monday; debits and ratios
   will move.
2. **IV constant in simulation.** Overstates gains into a crush, understates
   into an expansion.
3. **Two-year sample is mostly a bull tape.** HOOD, PLTR and NEM all rose hard;
   win rates were earned in a friendly regime.
4. **No fresh WSJ / MarketWatch headline read** as of this writing. Event gate
   is verified from earnings data; the news layer is not current.
5. **CCJ's fresh-OI signal shows size, not direction.** Cannot distinguish
   opening buyers from covered-call sellers.
6. **WMT, OKLO, NNE, NVDA, AVGO, CRWD chains not pulled** — screen-only verdicts.
