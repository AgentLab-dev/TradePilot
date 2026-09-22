# DESK — FULLCHECK — Tuesday, Sep 22, 2026 (~10:16 AM PT)

Graph: `FULLCHECK`. Supervisor: `desk-supervisor`. Roles never call each other.
Read-only. **WAIT FOR GO.** No orders. RTH open. First 30 is over.

## Roles

| Role | Status | Summary |
|---|---|---|
| desk-sources | warn | IBD list still as-of 9/17. Yahoo refreshed. Reddit 403. Whale live. |
| business-tape | ok | Gold + chips paid. Financials pay. AZO beat already in. KBH tonight. |
| tape-macro | ok | GDX +2.0% · SMH +1.4% · XLB +1.2% · XLF −1.9% · VXX −2.9%. SPY flat. |
| book-health | ok | Agentic flat. Cash **$1,376.26**. MARA assignment settled. No GTC. |
| flags | warn | Cache last bar 9/16. Live prices used for the chase check. HOOD is the clear. |
| event-gate | ok | AZO out (beat). KBH tonight STAND. COST Thu STAND. HOOD no print. |
| print-screen | ok | AZO beat $56.05 vs $54.10, +6.3%, first-30 gone. HOOD 115/110 liquid. |
| print-readthrough | ok | AZO peers all < +7%. GPC is the least extended for Wed first-30. |
| list-to-ticket | ok | HOOD TICKET ARM. AZO SKIP chase. KBH SKIP credit. NEM SKIP EM. |
| five-new-nbt | ok | Hard five = **HOOD only**. Not padded. |
| rank-next-best | needs_input | HOOD ARM for Wed first-30. Agentic cannot sell the credit. Wait for **go**. |
| desk-tester | ok | Score **9/10**. Call debit · v2 · put-credit + gate. |
| desk-publish | needs_input | Pack written. Sheet/BQ skipped. No go. |

---

## 1. desk-sources

```
RoleResult { role: desk-sources, status: warn, summary: IBD stale 9/17; Reddit 403; Yahoo and whale live,
payload: { access_line: "IBD SKIP (as-of 9/17) | WSJ RSS stale | MW OK | Barron's SKIP | Yahoo OK | Whale OK | Reddit SKIP | ApeWisdom SKIP" },
artifacts: [desk_sources_2026-09-22.md, news_sweep.md] }
```

## 2. business-tape

```
RoleResult { role: business-tape, status: ok, summary: Gold and chips paid; financials pay; HOOD is the flag clear }
```

## Business tape
Regime: Midday Tue. Risk-on, narrow. VXX **−2.9%**.
Story: AZO BMO beat is already in the tape. KBH is the 0d AMC. COST is Thu.
Payer vs paid: Payer = XLF **−1.9%**, IGV **−0.7%**. Paid = GDX **+2.0%**, SMH **+1.4%**, XLB **+1.2%**.
Sleeve: Gold is the industry leader. The name that clears all-four is **HOOD**, not a miner.
Veto: No credit through KBH tonight or COST Thu Sep 24. No AZO chase.
Reddit: scan blocked | Nominated: **none**
IS vs CFS: AZO beat **$56.05 vs $54.10**. Raise not in the EPS line. KBH **n/a**.

## 3. tape-macro

```
RoleResult { role: tape-macro, status: ok, summary: Gold leads, financials lag, chips still bid }
```

Vs Mon Sep 21 close, ~10:12 AM PT:

| Name | Last | vs Mon |
|---|---|---|
| SPY | 773.23 | flat |
| QQQ | 745.22 | +0.5% |
| SMH | 604.29 | +1.4% |
| GDX | 96.30 | +2.0% |
| IGV | 106.39 | −0.7% |
| XOP | 184.53 | flat |
| KRE | 71.50 | −0.7% |
| XLF | 54.86 | −1.9% |
| XLB | 50.30 | +1.2% |
| XLK | 195.65 | +0.4% |
| VXX | 17.19 | −2.9% |
| HOOD | 124.25 | +0.8% |
| NEM | 125.10 | +1.7% |
| MARA | 13.78 | +3.7% |
| AZO | 2,979 | +6.3% |
| KBH | 48.63 | +1.6% |

## 4. book-health

```
RoleResult { role: book-health, status: ok, summary: Agentic flat, cash $1376.26, no abort,
payload: { book: { cash: 1376.26, equity: 0, options: 0, gtc: none } } }
```

Agentic ••••1451 is cash, shares and long options only. A put credit cannot be placed here. Personal ••••5611 is not tradable by this agent.

## 5. flags

```
RoleResult { role: flags, status: warn, summary: Cache 9/16; live chase check; HOOD clears,
payload: { flags_table: "HOOD pass / NEM EM fail / MARA late / WPM FNV INSW avoid" } }
```

| Ticker | STKK | STNOW | 3Good | Whale | EM | Note |
|---|---|---|---|---|---|---|
| HOOD | 🟡 UP | 🟢 raw+3 | ✅ IV 61% | 🟢 +2 | **±19%** | Only clear |
| NEM | 🟡 UP | 🟢 raw+4 | ❌ IV 43% | 🟢 +2 | ±13% | Call-debit map, no room |
| MARA | 🟡 RANGE | 🟢 raw+3 | ✅ IV 83% | 🟢 +1 | ±30% | +3.7% today, window was Monday |
| WPM | 🟡 extended | 🔴 | ❌ | 🟡 | ±13% | AVOID |
| FNV | 🟡 | 🟡 | ❌ | 🔴 | ±10% | AVOID |
| INSW | 🟡 RSI 84 | 🟡 | ❌ | 🔴 | ±11% | AVOID, −4.5% today |
| NTAP | 🟡 | 🟢 | ❌ IV 44% | 🟢 | ±11% | EM fail, −3.0% today |

## 6. event-gate

```
EVENT-GATE TEST AZO: NEWS=Tue Sep 22 BMO beat 56.05 vs 54.10 | VERDICT=STAND (first-30 gone, +6.3%)
EVENT-GATE TEST KBH: NEWS=Tue Sep 22 AMC est $0.90 | VERDICT=STAND (no credit)
EVENT-GATE TEST COST: NEWS=Thu Sep 24 AMC est $6.52 | VERDICT=STAND
EVENT-GATE TEST HOOD: NEWS=no print | VERDICT=ARM (Wed first-30)
EVENT-GATE TEST MARA: NEWS=no print | VERDICT=STAND (late)
```

## 7. print-screen

```
RoleResult { role: print-screen, status: ok, summary: AZO printed; HOOD 115/110 passes liquidity }
```

HOOD Oct 16 **115/110** put credit. 115P mark **$3.65** (3.60/3.70), OI **2,335**. 110P mark **$2.26** (2.23/2.29), OI **7,005**. Mid **$1.39**. Natural **$1.31**. Width $5. Max profit **$131** / max loss **$369**. Minimum credit to work: **$1.25**. Natural clears it.

## 8. print-readthrough

```
RoleResult { role: print-readthrough, status: ok, summary: AZO peers under +7%; GPC least extended }
```

| Printer | Result | Peer | Peer vs Mon | Verdict | Clock |
|---|---|---|---|---|---|
| AZO Tue BMO | beat 56.05 vs 54.10, +6.3% | GPC | +3.5% | watch | Wed first-30 |
| AZO | same | ORLY | +4.3% | watch | if GPC already ≥+7% |
| AZO | same | AAP | +5.4% | watch | third |
| KBH Tue AMC | not out, est $0.90 | TOL / PHM / DHI | +1.6% / +2.3% / +2.9% | if-then | Wed only if beat |

## 9–11. Tickets, hard five, rank

Hard NEW + all-four + EM>15% + liquid: **HOOD**. Empty slots stay empty.

| # | Verdict | Ticker | Structure | Why |
|---|---|---|---|---|
| 1 | 🟡 ARM | HOOD | Oct 16 115/110 PCS, natural $1.31, min $1.25 | Only clear. Wed first-30. Personal-sized. |
| 2 | watch | GPC | no legs | AZO peer, least extended |
| 3 | 🔴 STAND | NEM | — | Leading industry, EM 13%, R:R 0.20 |
| 4 | 🔴 STAND | MARA | — | Monday window missed, +3.7% today |
| 5 | 🔴 STAND | AZO / KBH / COST | — | Print chase or no-credit |

## 12. desk-tester

Score: **9/10** (pass)
Best strategies (HOOD NEM MARA NTAP, 21td):
1. Call debit — RoR **+15.83%** · win 39.3%
2. v2 router — RoR **+14.67%** · win 50.9%
3. Put-credit + event gate — RoR **+5.15%** · win 58.0%
Plan vs best: **HOOD put credit in_top3**
Deducts: cache last bar 9/16, live price labeled (−1)
Recheck: no

## 13. desk-publish

Sheet/BQ skipped. **WAIT FOR GO.**
