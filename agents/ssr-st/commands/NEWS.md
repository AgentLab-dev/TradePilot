# Command: NEWS (IBD / WSJ / MW / Barron's)

Trigger: `NEWS`, `WSJ`, `MW`, `MarketWatch`, `Barron's`, login to WSJ, `IBD lists`.

Read-only. Load `news-portals` + `ibd-wsj-capture`. Never paste passwords.

1. MCP check (no WSJ-family content MCP; Whale Watch = Robinhood). Playwright (`project-0-TradePilot-playwright`) is valid. Built-in Browser Tab is **Settings → Browser & Network** (optional). Do **not** require Tools & MCP → Browser (On).
2. **SSO (confirmed 2026-09-09):** Log in **once at WSJ** (`https://www.wsj.com/`). Then open **IBD from the WSJ header**. That autologins IBD + MarketWatch + Barron's. Do **not** start at `https://www.investors.com/?ibdsilentlogin=true` unless the WSJ header IBD link is missing. Then open MW and Barron's from the same hat if needed. **Take Control** if Sign In; user says **done**.
   - https://www.wsj.com/
   - IBD from the WSJ header (fallback only: https://www.investors.com/?ibdsilentlogin=true)
   - https://www.marketwatch.com/?mod=WSJ_NavHat&mod=WSJ_NavHat
   - https://www.barrons.com/?mod=WSJ_NavHat&mod=WSJ_NavHat
   Then IBD Stock Lists (`ibd-wsj-capture`). **Do not ask for a paste.**
3. `python3 agents/ssr-st/workspace/Documents/market_data/news_portals.py` (RSS floor)
4. Required query: `"investor day" OR "analyst day" OR "capital markets day"`
5. Required: `{TICKER} earnings` on every 0d/1d name and every PPS-T7 2–7d category name.
6. On **FULL CHECK**, steps 8–9 treat the above as **fail conditions** (see `FULLCHECK.md`). RSS-only WSJ does not count. Zapier has no WSJ-family app.
