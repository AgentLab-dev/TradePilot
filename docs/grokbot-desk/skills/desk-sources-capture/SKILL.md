---
name: Desk sources capture
description: >-
  use this when any assistant captures IBD, WSJ, MarketWatch, WhaleWatch, and
  Reddit trend sources — shared Dow Jones box Chrome session; skip blocked
  portals and continue
---
# Desk sources capture

Standing news + flow capture for TradePilot and **any assistant** that needs the same portals. Use on FULL CHECK, evening wrap, NBT, or whenever IBD / WSJ / MarketWatch / Whale / Reddit trends are required. Read-only until **go** for trading. Box Chrome (shared across agents) is often already signed in to IBD, MarketWatch, and WSJ via Dow Jones SSO — reuse that session.

If WSJ/MW/IBD show signed-out or HTTP 401: run **Reconnect Dow Jones desk portals** once. If still failing, **skip that portal and continue**. Note skips.

Usually **no MCP** for IBD/MW/WSJ — use the signed-in browser. Prefer TradePilot pack scripts when present (`ibd-wsj-capture`, `whale_check.py`).

## Always capture (in order)

### 1) IBD lists
Open research.investors.com. Pull: IBD 50, Sector Leaders, Big Cap 20, New Highs / RS at New High, MarketTrend one-liner. Write tickers + as-of into desk_sources_YYYY-MM-DD.md.

### 2) WSJ
- `https://www.wsj.com/` and `https://www.wsj.com/market-data`
- Headlines, tape, geopolitics / Fed / sectors

### 3) MarketWatch
- `https://www.marketwatch.com/`
- Earnings calendar, movers, economy

### 4) WhaleWatch
- Run `whale_check.py` on book / finalists when available

### 5) Reddit / social (SOCIAL-ONLY)
Browser hot: r/algotrading, r/Quant, r/stocks, r/investing, r/StockMarket, r/wallstreetbets, r/options, r/semiconductors; optional r/spacs, r/pennystocks. Aggregators: ApeWisdom, SwaggyStocks. Tag **SOCIAL-ONLY** — never alone a TAKE. Skip if blocked.

### 6) Optional
Benzinga earnings, Barron's, FedWatch when CREDITS/rates matter.

## Apply
- IBD → SelfIDB50 / NBT universe
- WSJ + MW → tape, catalysts, vetoes
- Whale → whale ≥0
- Reddit → Miss-catch D / buzz screen only

## Access line
`IBD: OK|SKIP · WSJ: OK|SKIP · MW: OK|SKIP · Whale: OK|SKIP · Reddit: OK|SKIP · ApeWisdom: OK|SKIP`

## Shared use
Any of this user's agents may run this skill; Chrome SSO is machine-shared. After reconnect, other agents inherit the same portal session.
