# Command: NEWS (IBD / WSJ / MW / Barron's / Yahoo / Reddit SOCIAL-ONLY)

Trigger: `NEWS`, `WSJ`, `MW`, `MarketWatch`, `Barron's`, `Yahoo`, login to WSJ, `IBD lists`, Reddit.

Read-only. Load `news-portals` + `ibd-wsj-capture`. Never paste passwords.
Load `business-tape-interpret` after capture and emit `## Business tape`. If a 0d AMC/BMO is live, also load `print-readthrough-t1` and emit the mapped-peer table on any daily publish.

1. MCP check (no WSJ-family content MCP; Whale Watch = Robinhood). Playwright (`project-0-TradePilot-playwright`) is valid. Built-in Browser Tab is **Settings → Browser & Network** (optional). Do **not** require Tools & MCP → Browser (On).
2. **SSO (confirmed 2026-09-09):** Log in **once at WSJ** (`https://www.wsj.com/`). Then open **IBD from the WSJ header**. That autologins IBD + MarketWatch + Barron's. Do **not** start at `https://www.investors.com/?ibdsilentlogin=true` unless the WSJ header IBD link is missing. Then open MW and Barron's from the same hat if needed. **Take Control** if Sign In; user says **done**.
   - https://www.wsj.com/
   - IBD from the WSJ header (fallback only: https://www.investors.com/?ibdsilentlogin=true)
   - https://www.marketwatch.com/?mod=WSJ_NavHat&mod=WSJ_NavHat
   - https://www.barrons.com/?mod=WSJ_NavHat&mod=WSJ_NavHat
   - https://finance.yahoo.com/
   Then IBD Stock Lists (`ibd-wsj-capture`). **Do not ask for a paste.** Yahoo is public; no SSO. RSS does not replace the homepage.
3. `python3 agents/ssr-st/workspace/Documents/market_data/news_portals.py` (RSS floor)
4. Required query: `"investor day" OR "analyst day" OR "capital markets day"`
5. Required: `{TICKER} earnings` on every 0d/1d name and every PPS-T7 2–7d category name.
6. **Reddit SOCIAL-ONLY (required, additional — does not replace the five).** Public browse is enough. Optional logged-in home (`/?feed=home`) via gitignored `.env` `REDDIT_USER` / `REDDIT_PASSWORD` clears the signup overlay. Never put the password in docs or chat. Open + scan every required sub (copied from Grok Bot `docs/grokbot-desk/NEWS_DAY_PIPELINE.md`):
   - https://www.reddit.com/r/algotrading/
   - https://www.reddit.com/r/Quant/
   - https://www.reddit.com/r/stocks/
   - https://www.reddit.com/r/investing/
   - https://www.reddit.com/r/StockMarket/
   - https://www.reddit.com/r/wallstreetbets/
   - https://www.reddit.com/r/options/
   - https://www.reddit.com/r/semiconductors/
   Optional (do not replace the required set): r/spacs, r/pennystocks, ApeWisdom, SwaggyStocks. Those pages are **required input** (`business-tape-interpret`: what social is pricing + Nominated). Tag SOCIAL-ONLY for ranking — miss-catch D; **never Reddit-alone TAKE**.
7. Write `## Business tape` (regime, payer vs paid, sleeve, veto, Reddit nominated). Fail NEWS if capture ran and the block is missing.
8. On **FULL CHECK**, steps 8–9 treat the above as **fail conditions** (see `FULLCHECK.md`). RSS-only WSJ does not count. Skipping the Reddit check fails NEWS / FULL CHECK. Zapier has no WSJ-family app.
