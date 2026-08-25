# Growth Sleeve — $300 risk / $1,000 return mandate

**Status: PLAN ONLY. No orders placed, no orders staged.**
Prepared Sun Aug 9, 2026 · prices are Fri Aug 7 close (19:59:59 UTC snapshot)
Review this, then say go.

---

## 1. The headline you need before anything else

**The mandate supports four strong tickets, not six.**

I ran 36 names through the full battery. Four cleared everything — liquidity,
event gate, ratio, and a positive expectancy that survives path simulation.
A fifth (MPC) clears on math but is thin in the option book. A sixth does not
exist in this tape at this risk budget without lowering a standard.

I am showing you the four, plus the fifth as conditional, plus an empty sixth
slot and what it would cost to fill it. Padding a list to a round number is
the exact behavior that has cost money in this book before, so I am not doing
it silently.

**Second thing you need to know:** all six candidate structures are long-delta
call debit spreads. That is not laziness — your mandate mathematically excludes
credit spreads (a put credit spread that risks $300 can never pay $1,000). But
it means the sleeve is **one bet expressed six times**. If CPI runs hot
Wednesday and the tape sells off, every ticket loses together. The income book
never had that property. Sizing below assumes you accept it.

---

## 2. The mandate, and what it actually forces

You asked for ≤$300 risk and ≥$1,000 return per transaction. That is a
**3.34:1 reward-to-risk ratio**, and the ratio is the binding constraint.

| Structure | Can it reach 3.34:1? | Verdict |
|---|---|---|
| Put credit spread | No — max gain is the credit, always < width | Excluded by arithmetic |
| Covered call | No — capped at strike + premium | Excluded |
| Cash-secured put | No | Excluded |
| **Call debit spread** | Yes — 4:1 to 7:1 available | **The workhorse** |
| Long call (uncapped) | Yes — unbounded | Available, worse expectancy |
| Diagonal / calendar | Sometimes | Liquidity-limited here |

The income book (put credits on MS/DELL/HPE/UNH) does not disappear — it just
cannot live in this sleeve. Run them as two separate sleeves with separate
scorecards.

### The $1,000-per-contract trap

My first screen demanded $1,000 of gain **per contract**, which silently
deleted every stock under about $60 — MARA, NNE, SMCI, CELH and OKLO all
vanished without a line of explanation. That was a bug in my screener, not a
finding about those names. $1,000 on $300 is a *ratio* requirement; you get
there by sizing contracts to the budget. Fixed, re-run, and the low-priced
names are back in the table below with real verdicts.

---

## 3. Method — what actually ran

| Phase | What it did | Outcome |
|---|---|---|
| 1. Cross-Sector Gate | 11 GICS ETFs ranked over 1d / 1w / 1mo | No sector excluded on a single day's print this time |
| 2. Universe | 36 names with full sector coverage, incl. energy, nuclear, chips, software | Energy is back in, permanently |
| 3. SelfIDB50 | FFTY proxy + RS screen + your four IBD pastes + OKTA | Feeds candidates, does not rank them |
| 4. Price vs volume | `rs_multi.py` flags ACCUM / DISTRIB / weak-up on relative volume | Filters unconfirmed moves |
| 5. Per-name battery | Event gate, liquidity, IV routing | **Killed 4 of 7 first-round finalists on liquidity alone** |
| 6. Fresh OI | volume ÷ open interest on every quoted strike | CCJ flagged, see below |
| 7. Structure | Direction × IV, ≤$300 risk, ≥3.34:1 | Call debit spreads |
| 8. Backtest | `debit_sim.py` — day-by-day repricing, real fills, managed exits | Ranked and disqualified |
| 9. Validation | Earnings dates confirmed per name | All clean through Sep 18 |

### The liquidity gate did most of the work

This is the single most useful result of the run. Names that looked excellent
on price action and failed on the option book:

| Name | What the chain looked like | Verdict |
|---|---|---|
| EXPE | $350 call: $3.90 bid / $7.30 ask, 3 contracts | Reject |
| SCCO | Same pattern | Reject |
| TER | Same pattern | Reject |
| GKOS | **Zero** open interest on the $185 strike | Reject |
| HWM | $320 call: $1.40 bid / $2.75 ask (96% spread), 3 contracts traded | Reject — and it ranked #3 on the screen |
| MPC | OI 341–773, volume 2–24, spreads 13–27% | Conditional only |

HWM is the instructive one: it scored +18% expectancy and would have been a
top-three ticket on the numbers. The chain says you could not get out of it.
That is the NTAP / HON lesson landing for the third time, and it is now a hard
pre-filter rather than a post-hoc check.

### Backtest design

Two years of daily bars (476 overlapping six-week windows per name). Each
window reprices **both legs** with Black-Scholes every day and applies the real
rules: take profit at +100% of debit, stop at −50%, otherwise settle at expiry.
Debits are built from `high_fill_rate_buy` / `high_fill_rate_sell`, not mids —
mid-price fills are a fiction that flatters every number.

Caveats stated up front rather than buried: IV is held constant along each
path, so vol expansion and crush are both unmodeled. And PLTR's sample ran
+559% over the two years, so its hit rate is partly a statement about the tape.

---

## 4. The tickets

### Tier 1 — clears everything

| # | Ticket | Risk | Max gain | R:R | Breakeven | Sim win% | Expectancy | Sector |
|---|---|---|---|---|---|---|---|---|
| 1 | **HOOD** Sep18 105/120c @ $2.49 | $249 | $1,251 | 5.0x | $107.49 (+15.2%) | 53% | **+30%** | Fintech |
| 2 | **NEM** Sep18 120/135c @ $2.95 | $295 | $1,205 | 4.1x | $122.95 (+8.8%) | 52% | **+27%** | Gold / materials |
| 3 | **PLTR** Sep18 195/210c @ $2.29 | $229 | $1,271 | 5.6x | $197.29 (+14.7%) | 51% | **+27%** | Software / AI |
| 4 | **CCJ** Sep18 105/120c @ $2.76 | $276 | $1,224 | 4.4x | $107.76 (+10.7%) | 43% | **+14%** | Nuclear energy |

**Tier 1 total: $1,049 risk → $4,951 if all four reach max.**

### Tier 2 — conditional

| # | Ticket | Risk | Max gain | R:R | Breakeven | Sim win% | Expectancy | Condition |
|---|---|---|---|---|---|---|---|---|
| 5 | **MPC** Sep18 330/350c @ $3.03 | $303 | $1,697 | 5.6x | $333.03 (+11.7%) | 37% | +6% | Only if Monday's chain shows tighter than $0.50 wide |
| 6 | — empty — | — | — | — | — | — | — | See below |

### Per-ticket detail

**1 · HOOD — Sep 18 $105 / $120 call debit @ $2.49**
Spot $93.29. Buy the $105 (delta 0.334, OI 5,830), sell the $120 (delta 0.154,
OI 7,317). Spreads 3–7% across the chain, thousands of contracts of volume —
the cleanest book of any candidate. IV 64.6%. Q2 beat big ($0.62 vs $0.41
estimate), next report **Nov 4**, well past expiry. Highest simulated
expectancy in the set at +30%, and the highest 2-week base rate at 62%.
*Against it:* needs +15.2% in six weeks, and it is a high-beta name that will
lead the downside if the tape turns.

**2 · NEM — Sep 18 $120 / $135 call debit @ $2.95**
Spot $112.98. IV 44.5%, OI 7,700 / 14,571. Next earnings **Oct 22**. Lowest
hurdle in the book at +8.8%, which is why it survives a stop-heavy path.
Gold was the strongest sector on the 1-month window. *Against it:* Q2 was the
first EPS **miss** in eight quarters ($2.10 vs $2.18) — the move is metal-driven,
not company-driven, so this is really a gold trade wearing an equity ticker.

**3 · PLTR — Sep 18 $195 / $210 call debit @ $2.29**
Spot $172.01. The interesting one. **Implied vol is 52.6% while realized vol is
92%** — the options are priced for roughly half the movement the stock actually
delivers. That is precisely what the IV-routing matrix says to buy, and it is
why my synthetic screen (which priced off realized vol) scored PLTR at −6%
while the real chain scores +27%. Book is superb: OI 2,335 / 6,778, 1–3%
spreads. Next earnings past expiry. *Against it:* the +559% sample run inflates
the backtest, and +14.7% is a real hurdle.

**4 · CCJ — Sep 18 $105 / $120 call debit @ $2.76**
Spot $97.39. **Fresh-OI signal is the strongest in the book:** the $110 call
traded 7,413 contracts against 11,571 open interest (0.64 ratio) and the $100
traded 5,118 against 8,988 (0.57). That is heavy new positioning, not residual
open interest. Next earnings Oct 30. *Against it:* Q2 EPS missed badly — $0.13
against a $0.36 estimate, a 64% miss — so the flow is betting on uranium, not
on the company. Lowest win rate of the tier at 43%. The long leg ($105,
OI 1,338) and short leg ($120, OI 1,693) are thinner than the strikes the
whales are actually in; if you want the liquid strikes you would trade
$100/$110, but that is only 2:1 and fails your mandate.

**5 · MPC — conditional.** +6% expectancy is thin, and the book (volume 2–24
contracts) is the weakest of anything I am still willing to name. It is here
only because it holds the energy-refining slot. My own rule says a name found
while correcting my own blind spot starts on the watchlist, not in the lineup —
that rule applies to MPC and this is its second session, so it is eligible, but
it earns Tier 2, not Tier 1.

**6 · The empty slot.** To fill it I would have to take one of:
- **NVDA** Sep18, +4% simulated expectancy — real, positive, but barely
- **AVGO** Sep18, +5% — same story
- **WMT** Sep18, +8%, IV 27% — genuinely diversifying (consumer staples, low
  beta, the only candidate that would *not* lose with the others on a CPI
  shock), but I have not pulled its real chain yet
- a second structure on HOOD or PLTR — concentrates rather than diversifies

**My recommendation: leave it empty, or let me pull WMT's chain Monday.**
WMT is the only one that reduces the all-long-delta problem instead of
compounding it.

---

## 5. What got rejected, and why

Keeping these visible so the rejections are auditable rather than invisible.

| Name | Simulated expectancy | Reason |
|---|---|---|
| MSFT Sep18 560/590c | **−18%** | 12.9:1 ratio looks great; only 7% of windows reached breakeven. A lottery ticket wearing a spread's clothing |
| NOW Sep18 135/150c | **−13%** | 16% reach rate, IV 57.9% (expensive to buy), and the 2-year sample is **down 23%** |
| OKTA Aug21 155/170c | **−10%** | IBD Stock of the Day, but only 24% of 2-week windows clear a +6.5% hurdle. The pre-earnings vol ramp is a real unmodeled tailwind — it is not enough to flip −10% |
| HWM | +18% on math | Liquidity. 96% bid-ask spread |
| EXPE, SCCO, TER, GKOS | n/a | Liquidity |
| SMCI (−3%), MARA (−6%), CELH (−18%) | negative | Screened properly this time, and they fail |
| MU, LLY, GS, DELL, AMD, GEV | no structure | Debit for any ≥3.34:1 structure exceeds the $300 cap |

**On chips specifically, since you asked:** the semiconductor complex does not
support this mandate right now. NVDA +4% and AVGO +5% are the best of them, MU
and AMD cannot produce a qualifying structure inside $300, and SMCI is negative.
That is an answer, not an omission.

---

## 6. Your "80% positive growth in two weeks" — three honest versions

There is no structure that gives an 80% chance of a gain over two weeks. The
base rate for any liquid US equity is 52–55%, and nothing in this universe
exceeds 62%. Here is what *is* measurable, three ways:

| Name | (a) 80%-hold level | (b) 2-week win rate | (c) 10-week win rate |
|---|---|---|---|
| **HOOD** | $75.71 (−18.8%) | **62%** | **70%** |
| NEM | $98.35 (−12.9%) | 60% | 67% |
| PLTR | $145.65 (−15.3%) | 60% | 65% |
| **WMT** | $103.11 (−7.8%) | 60% | **73%** |
| MPC | $265.46 (−11.0%) | 58% | 66% |
| CCJ | $83.58 (−14.2%) | 57% | 65% |
| NVDA | $198.58 (−11.3%) | 57% | 64% |

- **(a)** is the level with ~80% odds of holding, implied by each name's own IV
  over six weeks. This is the closest real thing to "80% confidence."
- **(b)** is the honest read on your question, measured over 476 overlapping
  windows. **HOOD at 62% is the best available and it is not 80%.**
- **(c)** shows the odds improve materially with time. WMT at 73% over ten weeks
  is the highest-probability holding in the set.

**If the goal is one high-probability holding rather than a spread:** WMT
shares, or a WMT call debit spread, is the honest answer — 73% over ten weeks,
−7.8% downside cushion, lowest IV in the book. It will not make $1,000 on $300
quickly. The mandate and the probability target pull in opposite directions and
you should pick which one is binding.

---

## 7. Sequencing around CPI

CPI lands **Wednesday Aug 12**. All six tickets are long delta, so CPI is a
single point of failure for the whole sleeve.

| When | Action |
|---|---|
| **Mon Aug 10** | Enter **two only** — HOOD and NEM. Lowest hurdle plus best book. Total risk $544 |
| **Tue Aug 11** | Nothing new. Confirm fills, set GTC exits |
| **Wed Aug 12** | CPI. **No new entries.** If the tape breaks, the two live tickets are the whole exposure |
| **Thu Aug 13** | If CPI was benign, add PLTR and CCJ. Total risk rises to $1,049 |
| **Fri Aug 14** | MPC only if its chain has tightened. Decide on the 6th slot |

**Management, identical on every ticket:**
- GTC sell at **+100% of debit** — this is the exit the backtest is built on,
  not max gain. Holding for the full $1,000 was modeled and is negative-EV
- Stop at **−50% of debit**
- Hard close by **Sep 11** (one week before expiry) to avoid gamma
- If the S&P closes below its 20-day after CPI, close the whole sleeve rather
  than manage ticket by ticket — they are correlated, so treat them as one

---

## 8. Honest limits of this analysis

1. **Prices are Friday's close.** Everything re-prices Monday morning; the
   debits above will move and the ratios with them.
2. **IV constant in simulation.** Overstates gains into a crush, understates
   them into an expansion.
3. **Two-year sample is mostly a bull tape.** HOOD, PLTR and NEM all rose hard.
   The win rates are real but they were earned in a friendly regime.
4. **I have not verified today's WSJ / MarketWatch headlines.** The event gate
   is verified from earnings data; the news read is not fresh as of tonight.
5. **CCJ's fresh-OI signal shows size, not direction.** Large call volume can
   be an opening buy or a covered-call seller. I cannot distinguish them from
   the data available.

---

## 9. What I need from you

1. **Four tickets or six?** I recommend four, plus WMT if you want a fifth that
   diversifies rather than doubles down.
2. **Is the all-long-delta concentration acceptable** for a $1,049 sleeve
   against CPI on Wednesday?
3. **Which is binding — the $1,000 target or the high-probability holding?**
   They are different trades.
4. **Approve the Monday-only-two sequencing**, or say you want all of them on
   Monday.

Say go and I will re-pull the chains at the open, recompute the debits against
live quotes, and place them one at a time with confirmation on each.
