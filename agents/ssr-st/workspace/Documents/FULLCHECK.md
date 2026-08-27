# FULLCHECK — Wed Aug 26, 2026 ~5:56 PM PT

Read-only. Combined from `catalyst_cards.md` · `next_day_prep.md` · `momentum_watchlist.md` · `news_sweep.md` · `agent_learning_log.md` **plus Whale Watch (step 7)**, which this run originally skipped. Marks: Robinhood RTH close + AH; Nasdaq chain via `whale_check.py --to 2026-09-18`. Wait for **go**. Personal **1×**. Agentic cash **$176** does not take these debits.

## Why whale was missing

FULL CHECK step **7 is Whale Watch** (vol vs OI → 🟢/🟡/🔴 flag). This session:

1. `daily.py` printed **whale n/a** on every name (cache / IV miss) and was treated as unusable — correct for tape, **wrong as a skip of the whale step**.
2. `whale_check.py` was **not run** on candidates + book + NBT.
3. `next_day_prep.md` §3 had four strike vol/OI prints from Robinhood quotes, **not** the −2…+2 flag.

That is a process miss. Flags below are **Wed RTH chain**. Volume is the completed session. **Disregard at 9:30 on a live catalyst** (NVDA / CRWD / CRM / VEEV printed AMC). Recalibrate **7:00 AM PT**.

## Lead

**INTU / ZM first-30 is a kill.** Cards existed. No go before 9:30 ET. Same miss as DE / WMT / DKS.

**Thursday #1 is NVDA.** Beat **$2.22 vs $2.09**. RTH **$209.66** → AH **$218.85 (+4.4%)**. 1× Sep 18 **220/230 call debit**, cap **$4.00**. Need **go before 9:30 ET**.

**Live risk is MS.** Sep 18 210/200 ×1. Open **$2.25**. RTH mid **~$2.67**. Cushion **1.9%**. Abort **$210 or mid ≥ $4.50**. GTC **$1.25**. Do not add.

**NBT (not Thursday):** **WPM** + **ANET** for **Tue Sep 1 → Fri Sep 11**. GLW dead. MRVL is Friday’s print, not a 2-week hold.

---

## Ranked plan — Thu Aug 27

Flags on every row: **STKK** (chart) · **STNOW** (360°) · **3Good** (put-credit eligibility; does not veto a call debit) · **Whale** (vol vs OI). Live-catalyst whale/STNOW: **stale at 9:30**.

| Rank | Stock | STKK | STNOW | 3Good | Whale | Strategy | Entry | Exit | Why |
|---|---|---|---|---|---|---|---|---|---|
| 1 🟢 | **NVDA** $209.66 | 🟡 UP, thin R:R | 🟢 GO **+3** | ❌ IV 44% | 🟢 +1 lean-bull (stale 9:30) | Sep 18 **220/230 call debit** ×1 | Pay **≤ $4.00**. First 15–30 holds AH **~$219 / VWAP** | 50% of debit same day. Fade VWAP → flatten. Clock **10:00 ET** | Beat **$2.22 vs $2.09**. AH **+4.4%**. Cheap IV → debit not credit |
| 2 🟡 | **CRWD** $189.18 | 🔴 DOWN | 🔴 TRAP **+1** | ⚠️ IV 66% at support | 🟢 +2 BULLISH (stale 9:30) | Sep 18 **205/215 call debit** ×1 | Pay **≤ $4.50**. Only if NVDA skipped. Hold AH **~$206** | 50% of debit. Clock **10:00 ET** | Beat **$0.31 vs $0.24**. AH **+9.2%**. TRAP is the *credit* gate — debit only if first-30 holds. No new credit |
| 3 🟡 | **CRM** $205.62 | 🟡 RANGE | 🔴 raw **−2** | ❌ flow bearish | 🔴 −2 BEARISH (stale after +12.4% AH) | Sep 18 **230/240 call debit** ×1 | Pay **≤ $4.00**. Hold AH **~$231** | 50% of debit. Clock **10:00 ET** | INTU peer **with a print**. RTH flow put-heavy **into** the print — not a 9:30 veto; skip if debit > cap |
| 4 🟡 | **VEEV** $244.91 | 🟡 RANGE, ext | 🔴 raw **−4** | ❌ flow bearish | 🔴 −2 BEARISH (stale after +8.4% AH) | Sep 18 **260/270 call debit** ×1 | Pay **≤ $4.00**. Only if 1–3 skipped | 50% of debit. Clock **10:00 ET** | Beat **$2.35 vs $2.10**. Backup. Flags do **not** confirm a call |
| 5 🟡 | **MS** $214.08 | 🟡 RANGE | 🟢 GO **+2** | ❌ IV 29% | 🟢 +2 BULLISH | **Manage** Sep 18 **210/200 PCS** ×1 | Already in at **$2.25**. Do **not** add | GTC **$1.25**. Abort **$210** or mid **≥ $4.50** | Cushion **1.9%**. Flow with the book; IV too cheap to sell more puts |

Not in the five: **OKTA** (+20.6% AH). **MRVL** STKK 🟢 UP / STNOW 🟢 GO +2 / 3Good ✅ / Whale 🟡 0 — print **Thu AMC** → Fri card (3Good blocked). **HOOD** STKK 🟢 UP / STNOW 🟡 +0 / 3Good ❌ / Whale 🔴 −1 — do not replace the closed PCS.

---

## NBT — Tue Sep 1 → Fri Sep 11

Old window (8/17–8/28): **GLW dead** (RTH **$152.78**, $170 reclaim never held). **MRVL** = Fri first-30, not a 2-week hold.

| # | Name | STKK | STNOW | 3Good | Whale | Industry | Structure | Entry | Exit |
|---|---|---|---|---|---|---|---|---|---|
| NBT-1 | **WPM** $156.02 | 🟡 RANGE, ext (RSI 75) | 🟡 raw **+0** | ❌ IV ~50% | 🟢 +1 lean-bull | Gold streamer (IBD 50 ∩ Sector Leaders ∩ Big Cap) | Sep 18 **155/165 call debit** ×1 | Pay **≤ $4.50**. After Warsh holds **$156**. Do **not** buy Thu/Fri | Abort close **<$150**. Next earn ~Nov 5 |
| NBT-2 | **ANET** $202.25 | 🟡 UP, thin R:R | 🟢 GO **+3** | ✅ IV 50% | 🟢 +2 BULLISH | AI networking (Sector Leader **#1**) | Sep 18 **200/210 call debit** ×1 | Pay **≤ $5.00**. Arm **Thu Sep 3** after AVGO/HPE. Hold **$202 / $200** | Abort close **<$195**. No ANET puts |

**Do not open NBT Thu or Fri.** Full NBT write-up: `NBT.md`. GLW **dead** (STKK 🟡 RANGE; whale n/a). MRVL leftover is Fri print, not this pair.

Killed substitutes: TVTX/ETON/KNSA (biotech lotto), HNGE (IPO), IBKR (slipped **97.84**; spot **$97.02**), COHR, NTRA, AU (same metal bet as WPM), CIEN (prints **Sep 3 AM**).

---

## 1. Tape / macro

| | |
|---|---|
| SPY | **766.08** RTH / AH **769.41** |
| QQQ | **711.37** / AH **716.43** |
| SMH | **555.77** / AH **566.10** |
| VXX / VIX | **18.54** / **15.21** |
| IWM / TLT | **298.93** / **83.30** |
| IBD close | S&P **7675.70** −0.02% · DJIA **53463.88** −0.21% · Nasdaq **26130.20** −0.08% |
| 10Y / gold | **4.651%** / **4669** |
| Exposure | IBD **40–60%** |
| GICS Wed vs Tue | **XLI +1.09%** lead · XLK +0.61% · XLE +0.60%. Lag **XLV −1.00%** · XLY −0.67% |
| Regime | Flat RTH, risk-on AH on NVDA. Jul PCE **3.7%** y/y vs 3.6% est; core **3.3%**. **Warsh Fri 8/28 ~10:00 ET** — no new credits Friday |
| MANGOS | NVDA RTH **$209.66** → AH **~$218.82**. Do not chase SMCI/AMD/AVGO as T+1 |

`daily.py` finished ~11 min later with **macro n/a**, **IV n/a**, stale prices (ANET **$190.94** vs Wed **$202.25**). **Do not trade off it.** Ranked GOs AVGO/NVDA/GOOGL shares-only do **not** override this file.

---

## 2. Book health

**Personal ••••5611 (margin — this agent does not trade it):**

| Position | STKK | STNOW | 3Good | Whale | Structure | Marks | Plan |
|---|---|---|---|---|---|---|---|
| **MS** $214.08 | 🟡 RANGE | 🟢 GO **+2** | ❌ IV 29% | 🟢 +2 BULLISH | Sep 18 **210/200** PCS ×1 | Open **$2.25**. RTH mid **~$2.67**. Cushion **1.9%** | **Manage.** Abort **$210 or mid ≥ $4.50**. GTC **$1.25**. Do not add |
| **MARA** $11.22 | 🟡 RANGE | 🟢 GO **+3** | ✅ IV 85% | 🟢 +1 lean-bull | 100 @ $9.89 + short Sep 4 **$11C** | Mark $0.73 | Hold shares. **No puts** (3Good ✅ is ignored — shares already on) |
| **HOOD** $108.54 | 🟢 UP, room | 🟡 raw **+0** | ❌ flow bearish | 🔴 −1 lean-bear | Sep 18 85/80 ×3 **closed** | +$198 on 8/20 | Do not replace |

**Agentic ••••1451 (cash — the tradable sleeve):** cash **$176.31**, total **~$1,241**. MARA 100 @ $9.72 + short Sep 18 **$12C**. Catalyst debits are **personal 1×**.

No leftover short premium into NVDA / CRWD / CRM / OKTA / VEEV / MRVL.

---

## 3. 4-model flags — STKK · STNOW · Three Good · Whale (Wed RTH)

Regular columns on every name. Whale = Nasdaq chain `--to 2026-09-18`. STKK = cache + live RTH. STNOW / 3Good from those. **Printed names: whale/STNOW stale at 9:30.** 3Good is put-credit only.

| Name | Px | STKK | STNOW | 3Good | Whale | P/C vol | ATM IV | Use |
|---|---|---|---|---|---|---|---|---|
| **NVDA** | $209.66 | 🟡 UP, thin R:R | 🟢 GO **+3** | ❌ IV 44% | 🟢 +1 lean-bull | 0.53 | ~44% | Call debit. Stale at 9:30 |
| **CRWD** | $189.18 | 🔴 DOWN | 🔴 TRAP **+1** | ⚠️ IV 66% at support | 🟢 +2 BULLISH | 0.58 | ~66% | Debit only; no credit replace. Stale at 9:30 |
| **CRM** | $205.62 | 🟡 RANGE | 🔴 raw **−2** | ❌ flow bearish | 🔴 −2 BEARISH | 1.37 | ~52% | Rank 3. Stale after +12.4% AH |
| **VEEV** | $244.91 | 🟡 RANGE, ext | 🔴 raw **−4** | ❌ flow bearish | 🔴 −2 BEARISH | 1.29 | ~56% | Rank 4 only |
| **MS** | $214.08 | 🟡 RANGE | 🟢 GO **+2** | ❌ IV 29% | 🟢 +2 BULLISH | 0.39 | ~29% | Manage. Do not add |
| **MARA** | $11.22 | 🟡 RANGE | 🟢 GO **+3** | ✅ IV 85% | 🟢 +1 lean-bull | 0.54 | ~85% | Shares on. No puts |
| **WPM** | $156.02 | 🟡 RANGE, ext | 🟡 raw **+0** | ❌ IV ~50% | 🟢 +1 lean-bull | 0.55 | ~50% | NBT-1 after Warsh |
| **ANET** | $202.25 | 🟡 UP, thin R:R | 🟢 GO **+3** | ✅ IV 50% | 🟢 +2 BULLISH | 0.41 | ~50% | NBT-2 Thu Sep 3. No puts |
| **MRVL** | $245.11 | 🟢 UP, room | 🟢 GO **+2** | ✅ IV 82% | 🟡 0 NEUTRAL | 0.75 | ~82% | Fri card. 3Good blocked by print |
| **HOOD** | $108.54 | 🟢 UP, room | 🟡 raw **+0** | ❌ flow bearish | 🔴 −1 lean-bear | 1.05 | ~63% | Do not replace closed PCS |
| **GLW** | $152.78 | 🟡 RANGE | 🟡 raw **+0** | ⚪ IV n/a | ⚪ n/a | — | — | NBT dead |

Ticket-strike RH quotes (RTH 16:00 ET, stale vs AH): NVDA Sep 18 **220C** vol **20,453** / OI **51,407** · **225C** vol **20,230** / OI **52,084**. MS **210P** vol **32** / OI **5,010**. MARA **12C** vol **821** / OI **27,338**.

---

## 4. Event gate + catalyst cards

**No new credit** through Thu AMC (MRVL / WDAY / ADSK) and **Warsh Fri ~10:00 ET**. No new US investor/analyst/capital-markets days this week. SNDK ID **8/13 done**. **MRVL ID Tue Oct 6.** **INTU ID Thu Sep 17.**

| Ticker | Event | Session | Verdict | Structure | Trigger | Invalidation | Exit |
|---|---|---|---|---|---|---|---|
| **INTU** | Earnings | Tue 8/25 AMC | **kill** | Beat-and-dump. Wed first-30 gone. RTH **$345.88**. No go before 9:30 | — | Clock gone | Skip |
| **ZM** | Earnings | Tue 8/25 AMC | **kill** | Dump held. RTH **$93.83** | — | Clock gone | Skip |
| **PCE** | Macro | Wed 8/26 8:30 ET | **done** | Jul **3.7%** y/y (est 3.6%), core **3.3%** | — | — | Warsh still Fri |
| **NVDA** | Earnings | Wed 8/26 AMC | **arm** (#1 Thu) | EPS **$2.22 vs $2.09**. AH **$218.85 (+4.4%)**. 1× Sep 18 **220/230 call debit**. Cap **$4.00**. Recalibrate 7:00 AM PT | First 15–30 holds AH ~$219 / VWAP | Fade VWAP. Debit > $4.00 | Same session Thu. Do not buy AH |
| **CRWD** | Earnings | Wed 8/26 AMC | **arm** (2) | EPS **$0.31 vs $0.24**. AH **+9.2%**. Cap **$4.50**. No new credit | Hold AH range | Fade VWAP | Prefer NVDA if both fire |
| **CRM** | Earnings | Wed 8/26 AMC | **arm** (3) | RH **$5.90 vs $3.09** definition mismatch. AH **+12.4%**. Cap **$4.00** | Hold AH ~$231 | Fade VWAP | INTU peer **with** a print |
| **OKTA** | Earnings | Wed 8/26 AMC | **stand-down** | AH **+20.6%**. Debit will not clear $4.00 | Dump-and-hold only | +21% rip = skip | Skip unless asked |
| **VEEV** | Earnings | Wed 8/26 AMC | **stand-down** unless 1–3 skipped | AH **+8.4%**. Cap **$4.00** | Hold first-30 | Fade | Rank 4 |
| **SNPS** | Earnings | Wed 8/26 AMC | **stand-down** | AH **−0.4%**. Off-book | — | — | Skip unless asked |
| **MRVL** | Earnings | **Thu 8/27 AMC** | **arm later** (Fri) | Street **$0.87**. AH **$252.53 (+3.0%)** NVDA sympathy. Cap **$4.00**. No credit through 8/27 | First 15–30 **Fri** | Do not buy Thu RTH | Recalibrate Thu night |
| **WDAY / ADSK / AFRM / IREN** | Earnings | Thu 8/27 AMC | **stand-down** | Off-book | — | — | Skip unless asked |
| **DG / DLTR / BBY / ULTA** | Earnings | Thu 8/27 BMO | **stand-down** | Off-book retail | — | — | Skip unless asked |
| **SMCI / AMD / AVGO** | NVDA peer | Wed AH | **do not chase T+1** | No new event Thursday except MRVL’s own print | — | 6/26 SNDK path | Do not arm |
| **Jackson Hole** | Macro | Fri 8/28 ~10:00 ET | **stand-down credits** | Warsh | Wait for the speech | Do not sell premium | Manage MS only |
| **MS** | Open book | Now → Sep 18 | **manage** | 210/200 ×1. Mid ~$2.67. Abort $210 / mid ≥ $4.50 | Tag abort | Do not add | Leave GTC $1.25 |
| **MARA** | Shares + CC | Now | **hold / no puts** | Personal 100 + Sep 4 $11C. Agentic 100 + Sep 18 $12C | Crypto beta | No puts | Overlay is not a new credit-sell |

---

## 5. News (WSJ / IBD)

- **WSJ** (signed-in capture): **Nvidia Reports Blowout Quarter, Says Demand for AI Chips Is Getting Even Hotter.** CIA Moscow trip · US–Canada trade · Fed’s Cook. Tape: DJIA **53463.88** −0.21% · S&P **7675.70** −0.02% · Nasdaq **26130.20** −0.08% · 10Y **4.651%** · VIX **15.21**.
- **IBD MarketTrend** (Scott Lehtonen, 6:05 PM ET): sticky PCE into Warsh Fri; stay 40–60% invested; cut losers.
- RSS floor **empty** this run. Live homepage + IBD lists are the tape.
- Investor days: **none this week.** SNDK 8/13 done. INTU **Thu Sep 17**. MRVL **Tue Oct 6**.

**IBD lists (8/26 capture):** IBD 50 #1–3 TVTX ETON KNSA. Cross-list 50 ∩ Sector Leaders ∩ Big Cap: **ANET · AU · IBKR · WPM**. Sector Leader #1 **ANET**. IBKR slipped entry **97.84** (spot **$97.02**).

Oversold-bounce offense: **none.** SMH was flat RTH then **+1.9% AH** on NVDA — not a washout reclaim.

---

## 6. Health Check composite (`daily.py` — stale, do not route off this)

Whale column was **n/a**. Ranked GOs: AVGO / NVDA / GOOGL **shares / IV n/a**. AVGO as #1 GO is **wrong** for Thursday (prints **Sep 2**; NVDA peer T+1). SMCI **+9.4%** radar is **Tuesday’s** move. Use the Whale table in §3 and the ranked plan above.

---

## 7. Learning (today)

### INTU/ZM first-30 missed again; NVDA/CRWD/CRM armed for Thu
Cards existed. No **go** before 9:30. Kill at 5:45 PM is correct *entry*. Need **go before 9:30 Thu** or this repeats.

### NBT rotation: GLW dead; WPM + ANET for Sep 1–11
GLW $170 reclaim never held. MRVL leftover is Fri first-30. New pair: different industries, arm after Warsh, no ANET puts.

### Whale Watch skipped on FULL CHECK (this file)
Step 7 was not run. `daily.py` whale n/a was treated as a skip instead of a fallback to `whale_check.py`. **Fix:** every FULL CHECK writes a whale flag table for candidates + book + NBT before ranking. Adopted here.

Full log: `agent_learning_log.md`.

---

## 8. Pre-staged plan for 7:00 AM PT / 8 AM battery

1. Recalibrate NVDA 220/230 debit. Lead confirm-fire-kill **9:30–10:00 ET**. Need **go before 9:30**.
2. If NVDA debit > $4.00, CRWD then CRM. Skip OKTA unless it dumps. VEEV only if 1–3 skipped.
3. MS: abort still live. Do not add. Cushion **1.9%**.
4. No HOOD / SMCI / MRVL put credit. No Agentic debit.
5. After Thu close: rewrite MRVL for **Fri** first-30. Stand down new credits into Warsh.
6. NBT: WPM 155/165 after Warsh; ANET 200/210 **Thu Sep 3** after AVGO/HPE. GLW stays dead.

Sources (still canonical for overwrite next run): `catalyst_cards.md` · `next_day_prep.md` · `momentum_watchlist.md` · `news_sweep.md` · `agent_learning_log.md`.
