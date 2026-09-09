# Command: FULL CHECK (fullcheck)

Trigger: `FULL CHECK`, `fullcheck`, `full check`.

The 12-step battery. Read-only by default — surfaces tickets, waits for go.

1. Tape / macro (SPY QQQ SMH VXX 10Y) + **MANGOS** pulse (META·NVDA·GOOGL·SPCX + proxies AMZN/MSFT). Fail if MANGOS is omitted or left n/a with no live-quote fallback.
2. Cross-sector GICS ETF gate + industry sleeves (GDX · IGV · SMH · XOP · KRE). Fail if only the 11 GICS ETFs are ranked (gold/miners vs XLB, 9/3).
3. Book health (cushion, delta, GTC, abort). Fail if any open position lacks a GTC status and abort line (abort fired → same-session BTC, not "watch").
4. Health Check 4-model composite. Fail if any candidate / NBT / book row omits STKK · STNOW · 3Good · Whale (3Good does not veto a debit).
5. Event gate + catalyst cards + **PPS-T7** and **PPS-T1** (`pre-print-screen` / `print_monitor.md`). Then the miss-fix skills (skipping any of these is a failed FULL CHECK when a category print is in window or already out):
   - `pps-t1-em-recalibrate` — morning EM is preview; TAKE only on last-90 ATM straddle/spot ≥15%
   - `print-ah-guesstimate` — numbered AH bands on every 0d AMC (monster band cannot be <20% if last print ≥+20%)
   - `print-analog-vs-em` — analog ≥1.5× EM → ARM + **written second-name ticket** (SNOW 9/2)
   - `option-chain-liquidity-gate` — every debit: mid, natural, OI, cap
   - `post-print-gap-capture` — AH ≥+7% or ≤−7% and not filled → **STAND AH**, no T+1 chase
   - `next-25-print-screen` — screen the **next** analog; never rank the already-ripped name as a fill
6. STKK + STNOW + Three Good on finalists. Fail if a finalist skips this pass because Health Check already ran, or if 3Good vetoes a call debit.
7. Whale Watch (vol vs OI). Fail if `daily.py` whale n/a is treated as skip — run `whale_check.py` on candidates + book + NBT (8/26).
8. SelfIDB50 + **IBD lists auto-capture** (`ibd-wsj-capture` — do not ask for a paste). This is `news-portals` + `ibd-wsj-capture`, not a separate desk-sources-capture skill. Skipping live capture is a failed FULL CHECK:
   - **SSO (confirmed 2026-09-09):** Log in **once at WSJ** (`https://www.wsj.com/`). Then open **IBD from the WSJ header**. That autologins IBD + MarketWatch + Barron's. Do **not** start at `https://www.investors.com/?ibdsilentlogin=true` unless the WSJ header IBD link is missing. Playwright MCP is valid; Cursor Browser Tab is optional. If Sign In is showing, Take Control; user says **done**. Never paste passwords.
   - Open **IBD 50** in the Cursor browser. Fail if IBD 50 is not live today (as-of not today / empty tables) unless Sign In still blocks after Take Control / **done** — then FFTY + `rs_screen.py` is the only fallback.
   - Capture the rest of the Stock Lists: Sector Leaders, Big Cap 20, Spotlight, New Highs, RS at New High, IPO Leaders, Funds Buying. Fail if a listed URL was not opened.
   - Open MarketTrend (signed-in when possible). MarketTrend **%** itself is optional if the page loaded.
   - Overwrite `ibd_stock_lists.md` dated today. Fail if the agent asked the user to paste.
9. Desk sources — IBD / WSJ / MarketWatch / Barron's (`news-portals` + `ibd-wsj-capture`). Skipping any of these is a failed FULL CHECK. **SSO (confirmed 2026-09-09):** Log in **once at WSJ** (`https://www.wsj.com/`). Then open **IBD from the WSJ header**. That autologins IBD + MarketWatch + Barron's. Do **not** start at `https://www.investors.com/?ibdsilentlogin=true` unless the WSJ header IBD link is missing. Then open MW and Barron's from the same Dow Jones hat if needed. Open these (exact URLs, WSJ first):
   - https://www.wsj.com/
   - IBD from the WSJ header (fallback only: https://www.investors.com/?ibdsilentlogin=true)
   - https://www.marketwatch.com/?mod=WSJ_NavHat&mod=WSJ_NavHat
   - https://www.barrons.com/?mod=WSJ_NavHat&mod=WSJ_NavHat
   - Fail if any of the four was not opened (Playwright MCP, optional Cursor Browser Tab, or Safari/Chrome tail). RSS-only does not count (WSJ RSS is months stale).
   - Run `news_portals.py` RSS floor every run.
   - Required query: `"investor day" OR "analyst day" OR "capital markets day"` on book + SMH/memory/AI + READTHROUGH peers (SNDK 8/13). Fail if this query was not run.
   - Required: `{TICKER} earnings` on every **0d/1d** name (OKTA 8/26 — homepage was NVDA). Fail if a 0d/1d name has no `{TICKER} earnings` line.
   - PPS-T7: `{TICKER} earnings` on every **2–7d category** name. Fail if a PPS-T7 ON name has no ticker-earnings line.
   - Calendar UNION (with step 5): Nasdaq `earnings_radar` ∪ Robinhood `get_earnings_calendar` ∪ fundamentals next-earnings ∪ investor-day search. Fail if any of those four legs is missing.
   - Do not skip news because Sign In is showing — stop and ask Take Control. Signed-in when possible; homepage snapshot still required signed-out. Zapier has no WSJ-family app — it is not a substitute. After Sign In the user says **done**.
10. Direction × IV routing. Fail if a credit (put or call) is routed through a print / CPI / PCE / FOMC window.
11. Backtest new structures
12. Ranked plan 🟢 / 🟡 / 🔴 + write catalyst_cards.md, next_day_prep.md, momentum_watchlist.md. Fail if any ranked row omits STKK · STNOW · 3Good · Whale. Fail if the five recycle last session's unused names without a live unique-sleeve win (rewrite `NBT.md`; leftover five 9/2).
    Then upsert `daily_top5` and reload **both** Google Sheet and BigQuery `Daily_Top` (every batch writes both; `is_latest=Y` on the new date only):
    `python3 agents/ssr-st/workspace/Documents/market_data/create_daily_top5.py --from-csv <dated.csv> --csv --bq`
    Sheet = one tab **TradePilot-26Q3** (doc title the same); `date` + `execution_date` columns; `is_latest` Y/N. Never a new dated tab. `is_latest=Y` on that session_date, `N` on every older session. Never append without flipping the prior Y rows. Do not filter Looker on `latest_flag=Y`. Fail if Sheet or BQ is skipped, or prior `is_latest=Y` rows are not flipped to N.

Skill: `agents/ssr-st/skills/trading-continuous-learning/SKILL.md`
News: `agents/ssr-st/skills/news-portals/SKILL.md`
IBD/WSJ capture: `agents/ssr-st/skills/ibd-wsj-capture/SKILL.md`
EM recapture: `agents/ssr-st/skills/pps-t1-em-recalibrate/SKILL.md`
Liquidity: `agents/ssr-st/skills/option-chain-liquidity-gate/SKILL.md`
AH guesstimate: `agents/ssr-st/skills/print-ah-guesstimate/SKILL.md`
Analog vs EM: `agents/ssr-st/skills/print-analog-vs-em/SKILL.md`
Post-print gap: `agents/ssr-st/skills/post-print-gap-capture/SKILL.md`
Next 25% print: `agents/ssr-st/skills/next-25-print-screen/SKILL.md`
Loop: `agents/ssr-st/workspace/strategy_battery_loop.sh`
