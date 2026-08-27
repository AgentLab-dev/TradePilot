# Command: NEWS (WSJ / MW / IBD)

Trigger: `NEWS`, `WSJ`, `MW`, `MarketWatch`, login to WSJ, `IBD lists`.

Read-only. Load `news-portals` + `ibd-wsj-capture`.

1. MCP check (no WSJ/MW MCP today; Whale Watch = Robinhood)
2. Cursor browser: WSJ homepage + IBD Stock Lists (`ibd-wsj-capture`). **Do not ask for a paste.**
3. `python3 agents/ssr-st/workspace/Documents/market_data/news_portals.py` (RSS floor)
4. Required query: `"investor day" OR "analyst day" OR "capital markets day"`
