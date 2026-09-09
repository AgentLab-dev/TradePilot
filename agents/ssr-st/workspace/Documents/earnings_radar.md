# Earnings Radar (next 14 days)

_Generated 2026-09-09 11:27 local by `market_data/fetch_earnings.py`. Intersection of the Nasdaq earnings calendar with the cached universe **plus ALWAYS watch names**. **Not sufficient alone** — UNION Robinhood `get_earnings_calendar` and search investor/analyst days. Nasdaq omitted XE on 2026-08-13._

> 🔴 **sell-gate**: do not let any credit spread expire after this date (the AVGO / MU rule). 🟢 **directional**: pre-earnings debit/long watch. 🟡 **PPS-T7**: category name 2–7d out — week monitor, no fill (`pre-print-screen` / `print_monitor.md`). PPS-T1 is the 0d fill.

| Ticker | Report date | Days away | Session | Flags |
|---|---|---|---|---|
| **ORCL** | 2026-09-10 | 1d | AMC | 🔴 sell-gate · 🟢 directional |

_1 name(s) reporting in the next 14 days (universe-gated). Regenerate daily: `python3 market_data/fetch_earnings.py`._

## Robinhood UNION (2026-09-09 ~11:28 PT — source of truth)

Nasdaq universe table is **ORCL-only**. FULL CHECK used RH `get_earnings_calendar` + `get_earnings_results`. Do not treat the one-row table as “no other prints.”

| Ticker | Report date | Days away | Session | Flags |
|---|---|---|---|---|
| NAVN | 2026-09-09 | 0 | AMC | 🟢 PPS-T1 · EM 17.7% · ARM last-90 |
| AVAV | 2026-09-09 | 0 | AMC | 🟢 PPS-T1 · EM 14.0% · ARM last-90 |
| SAIL | 2026-09-09 | 0 | BMO | printed $0.09 vs $0.08 · STAND |
| COO / AEO | 2026-09-09 | 0 | AMC | cards only |
| CHWY / ASO / SIG | 2026-09-09 | 0 | BMO | printed / off-book STAND |
| ORCL | 2026-09-10 | 1 | AMC | 🟢 book 155/165 · no add · sell-gate Sep 18 |
| ADBE | 2026-09-10 | 1 | AMC | 🟢 second-name · recapture last-90 |
| TCOM | 2026-09-15 | 6 | AMC | 🟡 PPS-T7 · week monitor, no fill |

**Investor / analyst days (not prints):** NVDA Goldman Communacopia **Thu Sep 10 8:50 AM PT**. NAVN Goldman **Thu 8:10 AM PT** — do not chase. ORCL Investor Day **Oct 28** Las Vegas. **HPE Networking Investor Day Wed Sep 30** Sunnyvale 8:30 AM PT (announced Sep 3 — missed until this FULL CHECK).

## Unfiltered Nasdaq 0–1d (not universe-gated)

_If a name is here and not in the table above, it still needs a catalyst card. Agent must also UNION Robinhood MCP — Nasdaq omitted XE on 8/13._

- **2026-09-09 (0d):** AACG, AEO, ALZN, ANAB, ANIX, ASO, ATCH, AVAV, CAL, CGNT, CHWY, CLGN, CNM, COE, COO, CULP, GAUZ, GLOO, GURE, HTT, JILL, JMKE, KEQU, KFY, LAKE, LKSP, LMNR, LSAK, NAVN, NBP, NNOX, OCC, ODD, PTN, RYDE, SA, SAIL, SIG, SJ, SKIL, WLTH
- **2026-09-10 (1d):** ADBE, AENT, ALAR, BTTC, CMMB, CMND, CPRT, CSBR, DAVA, DBI, DSGX, EONR, FEIM, FIZZ, FLWS, HSCS, HUBG, IBEX, IMPP, IPST, ITP, LOVE, LPTH, M, MCFT, ORCL, REBN, REF, RH, SHOE, SMXT, SNYR, TEN, UROY, VFS, VNCE, YB, YRD, ZUMZ
