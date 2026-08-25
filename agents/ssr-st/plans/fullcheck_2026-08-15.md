# FULLCHECK — Sat Aug 15, 2026 ~10:25 AM PT

Weekend run for **Mon Aug 17**. All strategies × all industries. Read-only. No orders placed.
Robinhood MCP unauthorized this pass — book is Friday’s open positions, marked to Friday close + Nasdaq chain.
Margin ••••5611 last seen Fri ~**$61,030**. Agentic ••••1451: 100 MARA, cash ~$110.

Canvas: [fullcheck-2026-08-15](/Users/koteswararao.venkata/.cursor/projects/Users-koteswararao-venkata-Documents-Cursor-ssr-analyst/canvases/fullcheck-2026-08-15.canvas.tsx)

---

## What it is

There is **no XE / Unity / HPE ripper sitting on the tape for Monday**.

| Analog | Friday close | Why it is not Monday’s trade |
|---|---|---|
| **XE** | $20.98 **−7.7%** | Thu earn already happened. Fri was the dump. Monday is T+2 chop. Whale **bearish**. |
| **U** | $46.25 **+1.0%** | Reported **Aug 6**. At 90-day highs (+44% in 1 month). Whale **bearish**, STNOW raw −3. Chase. |
| **HPE** | $58.71 **−1.9%** | Model likes the *chart*. Structure fails: Aug 21 55/50 credit/width ~9% (need ≥25%). Sep credits **gated** by earn **9/2**. |

**What Monday actually is:**

1. **Energy rotation, not a print** — XLE **+1.39%** led all 11 GICS Friday. That is the live theme. Ticket = **XOM Sep 18 160/165 call debit ≤ $2.20** (Fri mid **$2.03**) if the first 15–30 min holds Friday’s low (~$159.30).
2. **The XE-style binary is FN Mon AMC** — known event, arm T−1, 1× debit *after* the print holds 15–30 min, flatten same session. Do not buy FN in Monday’s cash session.
3. **Book first** — CRWD Aug 21 210-short has **3.2%** cushion, 5 DTE, STKK downtrend, whale bearish. That is the risk, not a new idea.

`daily.py --all` (81 names) ranked **AVGO STRONG GO put-credit**. **Kill.** Selling puts into Friday’s −5.9% AMAT-sympathy dump is the falling-knife version of the model.

---

## 1. Tape / macro (Fri Aug 14 close)

| | Last | vs Thu |
|---|---|---|
| SPX | 7,785.76 | −0.17% |
| SPY | 776.34 | −0.20% |
| QQQ | 731.07 | −0.14% |
| SMH | 587.82 | −0.22% |
| VIX | 14.25 | −2.60% |
| 10Y | 4.70 | +1.19% |
| Oil | 82.40 | +1.42% |
| GLD | 401.48 | +0.63% |
| RSP | 222.77 | +0.02% |

Regime: **mixed / rotation**, not a crash. Soft CPI + PPI this week, weak Friday retail sales, oil bid. Equal-weight flat. MANGOS all red-to-flat (META −0.9%, AMZN −0.9%, NVDA flat). AI leadership is not leading.

Sources: Yahoo daily bars; Invezz / Barchart / AInvest 8/14 recap.

---

## 2. Cross-sector gate (11 GICS, Fri close)

| Rank | ETF | % | Read |
|---|---|---|---|
| 1 | **XLE Energy** | **+1.39%** | Leader. Oil +1.4%. The Aug 9 miss is still the live theme. |
| 2 | XLU Utilities | +0.61% | Defensive / power bid |
| 3 | XLB Materials | +0.44% | |
| 4 | XLI Industrials | +0.39% | |
| 5 | XLC Comm svcs | +0.36% | |
| 6 | XLRE Real estate | +0.33% | |
| 7 | XLP Staples | +0.10% | |
| 8 | XLF Financials | −0.17% | |
| 9 | XLY Discretionary | −0.21% | |
| 10 | XLK Tech | −0.40% | Laggard with SMH |
| 11 | **XLV Health** | **−0.60%** | Worst GICS Friday |

Inside tech: **storage still vertical** (SNDK +7.4%, STX +5.7%, WDC +4.4%) vs **semicap dump** (AMAT −5.1%, AVGO −5.9%) vs **AMD +6.5%** diverging. That split is why a blanket “buy chips” ticket is wrong.

---

## 3. Book health (Friday close marks)

Nasdaq chain labeled “as of Aug 13”; spots match Friday Yahoo closes. **Re-mark at Monday open** — CRWD/HOOD puts are probably *worse* than these mids after Friday’s −3.8% slides.

| Position | Spot | Short | Cushion | Open | Mid (wknd) | uPnL | Call |
|---|---|---|---|---|---|---|---|
| **CRWD** Aug 21 **210/200** ×2 | 216.95 | 210 | **3.2%** | ~$1.65 | **~$1.93** | **~−$56** | **At-risk.** STKK downtrend, whale bearish, value-trap flag. 5 DTE. Abort **$210 tag or mid ≥ $3.30**, same session. Do not add. |
| **HOOD** Sep 18 **85/80** ×3 | 95.56 | 85 | **11.1%** | ~$1.31 | **~$1.04** | **~+$81** | Best line. Whale now **neutral** (was bearish Fri AM). Leave 50% GTC ~$0.66. Abort mid ≥ ~$2.62. |
| **MS** Sep 18 **210/200** ×1 | 217.36 | 210 | **3.4%** | $2.25 | **~$2.42** | **~−$17** | Still tight. Whale **bearish**. 210P bid/ask 3.65–4.45 — noisy. Abort **$210 or mid ≥ $4.50**. Do not add. |
| **MARA** 100 sh @ $9.89 | 9.20 | — | — | — | — | **−$69** | Friday **was** the weekly close. **9.20 > $9.00** — stop holds. **Do not sell puts on top.** |
| Agentic MARA 100 @ $9.72 | 9.20 | — | — | — | — | ~−$52 | Same stop. Cash ~$110 — stand down. |

Pending 50% GTCs on CRWD/HOOD/MS were still resting Friday. CRWD 50% ($0.83) will not fill from $1.93. HOOD 50% ($0.66) still live.

---

## 4–7. Health Check + whale (`daily.py --all`, 81 names)

Top model GOs vs overlay:

| Rank | Name | Model | Whale / IV | Overlay |
|---|---|---|---|---|
| — | **AVGO** | STRONG GO put-credit | bullish / IV 51% | **KILL** — Fri −5.9%, no print, T+3 dump. Do not sell puts. |
| — | **AMC** | GO put-credit | IV 77% | **KILL** — $2.50 name, quality gate. |
| 1 | **XOM** | GO-on-confirmation **call debit** | bullish / cheap IV | **ARM MON** — energy leader, mid $2.03 ≤ $2.20 cap |
| 2 | **MPC** | GO on pullback call debit | bullish / cheap IV | **ARM** — held dip only; 350/360 debit ~$5.20 on $10, fills wide |
| 3 | **FN** | AVOID (lean-bear) | stale into Mon AMC | **ARM PRINT** — whale is prior-session; catalyst day ignores it |
| — | **AMZN / GOOGL** | GO call debit | bullish / cheap IV | Secondary. Tech lagged. Only if XLE still leads *and* Mag-7 holds — do not lead with them |
| — | **MARA** | GO put-credit | neutral / rich | **OVERRIDE** — long shares |
| — | **HPE** | GO on pullback put-credit | bullish / rich | **KILL structure** — Aug 21 c/w ~9%; Sep gated 9/2 |
| — | **U / XE** | AVOID | bearish | **Stand down** — see hunt |
| — | **STX / SNDK** | GO | mixed/lean-bull | **Stand down** — storage T+2 |
| — | **KEYS** | GO on pullback put-credit | neutral | **Event-gated** — earn Tue AMC. Debit after print only |
| — | **TLN** | GO-on-confirmation put-credit | lean-bull (flipped vs Fri −1) | Arm only if XLE leads and TLN holds Friday low. Not the #1 |
| — | **CRWD / MS** | AVOID / trap | bearish | Book management, not new sells |
| — | **ORCL / NNE** | value-trap | — | Stand down |
| — | **AMD** | GO put-credit | lean-bull | **KILL chase** — Fri +6.5%, Monday is T+1 |
| — | **DELL** | AVOID | bearish | Earn **9/3** — no Sep credits |
| — | **LLY / EXPE** | GO call debit | lean-bull | Diversifiers, extended or thin R:R — not Monday musts |

SelfIDB50: FFTY top-25 still **healthcare / fintech / biotech** as of Aug 11 (HNGE, TER, WT, OUST, KNSA…). Tape Friday was **energy**. Do not buy TER on an AMAT-dump hangover. Cache RS (Thu bars): U/HPE/DELL still 3-month leaders and **extended**; XOM only +0.4% 3-month / +9% 1-month / −3% from high — that is a *setup*, not a chase.

---

## 8. Event gate

**Credit-sell block:** FN **Mon 8/17 AMC**; HD **Tue 8/18 BMO**; KEYS **Tue 8/18 AMC**; then CRM/CRWD/NVDA/OKTA/VEEV **8/26 AMC**; IREN/MRVL/WDAY **8/27**. HPE **9/2**, DELL **9/3**. No new Sep credits on those.

**Macro:** Empire State Mon 8:30 ET. Housing starts / industrial production Tue. **FOMC minutes Wed 2:00 PM ET.** ADI/TJX/LOW/TGT/ROST Wed BMO. WMT/DE Thu BMO.

Investor-day search: **none** Mon–Tue on book / SMH / memory / NVDA / HPE / DELL. SNDK day was Thu 8/13. FN Rosenblatt Age of AI Summit **Tue 1:00 PM EDT** = conference, not a second long.

Robinhood calendar: MCP auth timed out. UNION used Nasdaq radar + StockTi / Fabrinet IR / HPE IR / Dell IR.

Catalyst cards: `ssr-analyst/Documents/catalyst_cards.md`.

---

## 9. News

- Fri close: SPX −0.17% to 7,785.76 after a record week. Energy +1.4%, tech −0.7%. Weak retail sales. Oil +1.4% on Middle East. Source: Invezz, Barchart, AInvest 8/14.
- AMAT beat-and-raise AMC 8/13, stock **−5.1%** Fri. Morgan Stanley still cautious vs WFE. Source: Applied IR; TipRanks 8/14.
- SNDK **+7.4%** Fri after Thu Investor Day + JPMorgan overweight. STX +5.7%, WDC +4.4%. Source: Sandisk IR 8/13; Barchart 8/14.
- XE Thu: rev/grant $54.6M (+154% YoY), DOE up to +$1B ARDP. Fri **−7.7%**. Source: X-energy IR 8/13.
- U: Q2 8/6, strategic rev +38%, Q3 guide $540–550M. Fri still grinding highs. Source: Unity IR 8/6.
- HPE earn **9/2** 4:30 PM ET. Source: HPE IR.
- DELL earn **9/3** 3:30 PM CDT. Source: Dell IR.

---

## 10–12. Ranked plan (direction × IV)

### Take (Monday — none at the open)

No new order in the first tick. Confirm XLE still leads, then XOM. First job is **CRWD / MS abort lines**.

### Arm

| # | Idea | Structure | Trigger | Why |
|---|---|---|---|---|
| 1 | **XOM** | Sep 18 **160/165** call debit, cap **≤ $2.20** (Fri mid $2.03 = 5.13−3.10). 1×. Max loss ~$203 | First 15–30 min Mon holds above Friday low **~$159.30** while XLE still green | Bull + cheap IV. Energy led all 11 GICS. Liquid (OI 12.8k / 10.9k). Next earn not in the Sep window |
| 2 | **FN** | 1× Sep 18 debit **after Mon AMC** | 15–30 min hold of post-print range (AH or Tue open) | The XE-style card. Whale lean-bear is **stale** into a print |
| 3 | **MPC** | Call debit on a **held dip**, not $355 | Dip-hold, XLE still leading | Whale bullish, earn 11/3. 350/360 ~$5.20 debit is too expensive to chase |
| 4 | **HD** | 1× Sep 18 debit **Tue only** | 15–30 min hold after **BMO 8/18** | Do not buy Monday |
| 5 | **KEYS** | 1× debit after **Tue AMC** | 15–30 min hold | Put-credit GO is event-gated |
| 6 | **ADI** | 1× debit **Wed** after BMO | 15–30 min hold | Next semicap print after AMAT dump |

### Stand-down

- **AVGO / AMC** model GOs (dump-chase puts / quality)
- **MARA / NNE / ORCL** puts (shares, trap, downtrend)
- **HPE / DELL / MRVL** Sep credits (9/2, 9/3, 8/27)
- **SNDK / STX / WDC / AMD** chase
- **AMAT / AVGO** dump-chase
- **XE / U**
- **NVDA 225/230** debit still ~$2.04 vs **$1.80** cap; earn 8/26
- **TLN** unless XLE leads *and* Friday low holds
- **HD / KEYS / FN** from the long side *before* the print

### $1k agentic sleeve

100 MARA, ~$110 cash. **Stand down.** Stop already survived the Friday weekly close ($9.20). Cannot size a defined-risk debit.

---

## Action tickets (wait for your go)

1. No orders this weekend.
2. Monday open: re-mark **CRWD** and **MS**. Abort same session if $210 tags or CRWD mid ≥ $3.30 / MS mid ≥ $4.50.
3. Leave HOOD 50% GTC (~$0.66).
4. MARA: weekly close held. No puts.
5. If XLE still leads and XOM holds ~$159.30 for 15–30 min → **XOM 160/165 debit ≤ $2.20**, 1×.
6. FN: nothing Monday cash. After AMC, 1× Sep debit only on a held range.

_Sources: `daily.py --all` Sat 10:12–10:23 PT (81 names); Yahoo Fri closes; Nasdaq option chain weekend marks; FFTY holdings as of 8/11; Fabrinet / HPE / Dell / X-energy / Unity / Sandisk IR; Invezz, Barchart, StockTi calendar._
