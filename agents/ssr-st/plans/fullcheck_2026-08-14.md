# FULLCHECK — Fri Aug 14, 2026 ~9:20 AM PT

All strategies × all industries. Read-only. No orders placed.
Margin account ••••5611 · **$61,030** · cash $60,910 · options mark −$812 · BP $228k / unleveraged $57.1k
Agentic ••••1451 · $1,016 · 100 MARA @ $9.72 · cash $110 · no options

Write-up companion: [fullcheck-2026-08-14 canvas](/Users/koteswararao.venkata/.cursor/projects/Users-koteswararao-venkata-Documents-Cursor-ssr-analyst/canvases/fullcheck-2026-08-14.canvas.tsx)

---

## Bottom line

Tape is mixed after two friendly inflation prints: SPY −0.2%, QQQ −0.3%, SMH −0.8%. **Energy leads** (XLE +1.5%); tech/semis lag. Storage is still ripping **T+1** (SNDK +5.7% after Thu’s +15% Investor Day). AMAT beat-and-raised AMC and is **−5.2%** — the overnight debit window is dead.

**No new trades Friday.** Monthly rule: no new high-risk into the weekend. `daily.py --all` ranked MARA STRONG GO put-credit — **override** (already long 100 shares). First job is the book: **MS 210-short has 3.1% cushion and whale is bearish.**

---

## 1. Tape / macro

| | Last | vs Thu close |
|---|---|---|
| SPY | 776.45 | −0.18% |
| QQQ | 729.57 | −0.34% |
| SMH | 584.63 | −0.76% |
| VXX | 19.47 | −0.79% |
| GLD | 402.69 | +0.93% |
| VIX (daily.py 8:57) | 14.69 | +0.41% |
| 10Y | 4.69 | +0.97% |
| BTC | 62,938 | −0.76% |

PPI (Thu) and CPI (Wed) both cooled; hike odds for Sep 15–16 FOMC faded. Retail sales 8:30 ET already out. This is not a risk-[REDACTED] crash — equal-weight (RSP) is flat — it is a **rotation out of chips into energy/defensives**.

MANGOS: NVDA flat, MSFT +0.3%, META/GOOGL/AMZN slightly red. SPCX −2.9% (daily.py). AI leadership is not leading today.

---

## 2. Cross-sector gate (11 GICS, ranked)

| Rank | ETF | % | Read |
|---|---|---|---|
| 1 | **XLE Energy** | **+1.50%** | Leader. The Aug 9 miss (energy cut from the universe) is the live theme. |
| 2 | XLU Utilities | +0.56% | Defensive bid |
| 3 | XLC Comm svcs | +0.43% | |
| 4 | XLI Industrials | +0.33% | |
| 5 | XLB Materials | +0.33% | |
| 6 | XLRE Real estate | +0.28% | |
| 7 | XLP Staples | +0.21% | |
| 8 | XLF Financials | −0.05% | |
| 9 | XLY Discretionary | −0.14% | |
| 10 | XLV Health | −0.50% | |
| 11 | **XLK Tech** | **−0.56%** | Laggard with SMH |

---

## 3. Book health (••••5611)

NEM PCS and MARA Aug 21 $10.50C are **gone** vs yesterday’s book (not in open option positions). MARA **100 shares** remain. GTC 50% closes still rest on CRWD / HOOD / MS (pending buy on shorts, pending sell on longs). Marks from Nasdaq 12:20 ET (Robinhood option-quote MCP unauthorized this pass).

| Position | Spot | Short | Cushion | Open credit | Mid now | uPnL | Call |
|---|---|---|---|---|---|---|---|
| **CRWD** Aug 21 **210/200** PCS ×2 | 219.44 | 210 | **4.3%** | ~$1.65 | **$1.42** | **+$46** | Hold. 50% = $0.83. Whale **bearish** (P/C vol 1.30). STKK downtrend. Abort mid ≥$3.30 or close <$210. Expires **8/21 before earn 8/26**. |
| **HOOD** Sep 18 **85/80** PCS ×3 | 97.21 | 85 | **12.6%** | ~$1.31 | **$0.96** | **+$107** | Best line. 50% = $0.66 (GTC should catch it). Whale flipped **bearish** (near-money puts). Abort mid ≥$2.62. |
| **MS** Sep 18 **210/200** PCS ×1 | 216.79 | 210 | **3.1%** | $2.25 | **$2.53** | **−$28** | **At-risk.** Whale **bearish** P/C vol 1.85. ATM IV only 28%; 28D expected move ±7.8% **covers $210**. Abort if **$210 tags** or mid ≥**$4.50**. Do not add. |
| **MARA** 100 sh @ $9.89 | 9.07 | — | — | — | — | **−$82** | Weekly-close stop **<$9.00**. **Do not sell puts on top.** Covered call is flat. |
| Agentic MARA 100 @ $9.72 | 9.07 | — | — | — | — | ~−$65 | Same stop. Cash $110 — no add. |

CRWD/HOOD/MS all have resting 50% GTCs. Leave them.

---

## 4–7. Health Check + whale (`daily.py --all`, 72 names)

Ranked GO that **survive overlap + Friday + event gates**:

| Name | daily.py | Whale (live) | IV | Route | Verdict |
|---|---|---|---|---|---|
| MARA | STRONG GO put-credit | bullish / IV 77% | high | put credit | **OVERRIDE** — already long shares |
| TLN | GO-on-confirmation put-credit | **lean-bear −1** | 54% | put credit | **Kill** — whale flipped vs the model |
| NNE | GO on pullback put-credit | bullish / IV 89% | high | put credit | **Stand down** — extended, leftover shares |
| STX | GO-on-confirmation put-credit | lean-bull / IV 75% | high | put credit | **Stand down** — storage T+1 chase |
| XOM | GO-on-confirmation **call debit** | **lean-bull +1** | **27%** | call debit | **Arm Monday** — energy leader, cheap IV, liquid |
| MPC | GO on pullback call debit | **bullish +2** | 40% | call debit | **Arm Monday** — fills are wide; wait for a held dip |
| TGTX | GO-on-confirmation call debit | **bullish +2** | 49% | call debit | **Arm only** — FFTY-complex biotech; 50C bid/ask 18% wide |
| AMZN / GOOGL / NVDA | GO call debit | mixed | low | call debit | **Not Friday.** NVDA Aug 21 225/230 debit mark **$2.02** vs ≤$1.80 arm |
| ANET | GO call debit | neutral / IV 48% | mid | call debit | Thin R:R; skip Friday |
| ORCL / CRWD / HOOD / MS | AVOID/WAIT | bearish on the last three | — | — | Do not add puts |

SelfIDB50 (FFTY top-25 as of Aug 11): still **healthcare / fintech / biotech** (HNGE, TER, WT, OUST, KNSA, ENVA, NTRA, OSCR, GKOS…). TER is ATE — do not chase it on an AMAT dump day. Energy is the RS leader **today**; FFTY has not rotated into it yet.

---

## 8. Event gate

**Credit-sell block:** CRM / CRWD / NVDA / OKTA / VEEV **8/26 AMC**; IREN / MRVL / WDAY **8/27**. HPE ~9/2, DELL 9/3. No new Sep credits on those.

Nasdaq 0d list is micro-caps (SGML, USAS, CSAN…). Robinhood high-cap window adds **FN Mon AMC, XP Mon AMC, HD / BIDU / KEYS / TOL / JKHY Tue**. Investor-day search: **none** Mon–Tue on book/SMH/memory. SNDK day was yesterday.

Catalyst cards: `ssr-analyst/Documents/catalyst_cards.md`.

---

## 9. News

- AMAT Q3: rev $9.12B (+25%), n-GAAP EPS $3.50 beat; Q4 guide ~$10.25B vs ~$9.54B street. Stock still **−5%** (high bar). Source: Applied IR 8/13 AMC; Reuters/MarketScreener AH.
- SNDK Investor Day (Thu): FY28–30 model mid/high-teens rev growth, ~80% n-GAAP GM, ~50% FCF margin, NBMs covering ~50% of FY27 bits. Follow-through Fri. Source: Sandisk IR 8/13.
- PPI Jul unchanged m/m, +4.7% y/y (vs +0.2% / +4.9% est). Soft with CPI. Source: Barchart / FXStreet 8/14.

---

## 10–12. Ranked plan (direction × IV)

### Take (today — book only)

1. **No new opening trade.** Friday + mixed tape + no clean first-30-min catalyst left.
2. Leave **HOOD** 50% GTC (~$0.66). Best green in the book.
3. **MS:** do not average. Abort = $210 tag **or** mid ≥ $4.50, same session.

### Arm (Monday, not now)

| Idea | Structure | Trigger | Why |
|---|---|---|---|
| **XOM** | Sep 18 **160/165** call debit, cap **≤ $2.20** (mark $2.15 = 5.50−3.35). 1×. Max loss $215. | First 15–30 min Mon holds above Friday’s low (~$160.8 area) while XLE still leads | Bull + **27% IV** → buy. Whale lean-bull. Liquid (OI 12k/10k). Next earn not in the Sep window. |
| **MPC** | Call debit (IV ~40%), **not** the wide $360/$370. Prefer a held pullback. | Dip-hold, not $355 chase | Whale +2, earn 11/3, best non-tech from the week plan |
| **FN** | 1× defined-risk debit after **Mon AMC** print | 15–30 min hold of post-print range (AH or Tue open) | Semi-adjacent manufacturer; AMAT dump is the context |
| **HD** | 1× defined-risk debit **Tue only** | 15–30 min hold after **BMO 8/18** | Do not buy Friday into it |

### Stand-down

- **MARA / NNE / TLN put sells** — overlay, extended, or whale vs model
- **SNDK / WDC / STX / AMAT / AVGO** chase
- **ORCL** puts (STKK value-trap)
- **Cyber / NVDA Sep credits** (8/26)
- **HPE / DELL Sep** (~9/2–9/3)
- **NVDA 225/230** debit at $2.02 (limit was $1.80)
- **TGTX** until the 50C spread is tradable
- **HD / KEYS / BIDU** from the long side today

### $1k agentic sleeve

100 MARA, $110 cash. **Stand down.** Stop = weekly close <$9. Cannot size a defined-risk debit.

---

## Action tickets (wait for your go)

1. No new orders Friday.
2. Watch **MS $210** — abort same session if tagged or mid ≥ $4.50.
3. Confirm CRWD/HOOD/MS 50% GTCs still working.
4. MARA shares: weekly close stop <$9; no puts.
5. Monday: confirm XLE still leads, then XOM 160/165 debit only on a first-30-min hold.

_Sources: Robinhood positions/quotes; Nasdaq option chain 12:20 ET; `daily.py --all` 8:57 PT; whale_check.py; FFTY holdings 8/11; Applied / Sandisk IR; BLS-week PPI via Barchart/FXStreet._
