# Portal URLs and feeds

Login lives in the browser. These URLs are for the agent, not for storing credentials.

## Homepages (Cursor browser / Safari tail)

| Portal | Home | Notes |
|---|---|---|
| WSJ | https://www.wsj.com/ | Paywall. Sign In in header when logged out. Markets: https://www.wsj.com/market-data |
| MarketWatch | https://www.marketwatch.com/ | Often same Dow Jones SSO as WSJ |
| Yahoo Finance | https://finance.yahoo.com/ | Public headlines; login optional |
| CNBC | https://www.cnbc.com/ | Backup |
| Reuters | https://www.reuters.com/business/ | Backup |
| Investopedia calendar | https://www.investopedia.com/ | Macro calendar backup |
| IBD MarketTrend | https://research.investors.com/markettrend.aspx | Paid. Sign In top-right. Newsletter `ibdsilentlogin=true` does **not** carry into the Cursor browser. Big Picture + IBD-50 lists after login. |

## Public RSS (news_portals.py)

| Source | Feed |
|---|---|
| WSJ Markets | https://feeds.a.dj.com/rss/RSSMarketsMain.xml |
| WSJ US Business | https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml |
| MarketWatch top | https://feeds.marketwatch.com/marketwatch/topstories/ |
| MarketWatch pulse | https://feeds.marketwatch.com/marketwatch/marketpulse/ |
| Yahoo Finance news | https://finance.yahoo.com/news/rssindex |

A 403/empty feed is a skip, not a crash. Note it in `news_sweep.md`.

WSJ `RSSMarketsMain` / `WSJcomUSBusiness` can lag by months. Do not treat those dates as the tape. Prefer the live homepage snapshot.

## Not a news portal

| Name | How to access |
|---|---|
| Whale Watch | Robinhood MCP + `market_data/whale_check.py`. No website login. |
| Unusual Whales | No MCP in this repo. Do not scrape it unless the user names it and is signed in via ladder 1–2. |
| IBD 50 | After IBD Sign In: MarketTrend + Stock Lists. Until then SelfIDB50 (`FFTY` + `rs_screen.py`). |

## First-time WSJ login (user)

1. Agent opens https://www.wsj.com/ in the Cursor browser (side).
2. User clicks **Take Control** → **Sign In** (password manager / 2FA).
3. User says **done**.
4. Agent snapshots Markets. Session should stick for later tabs in that browser.

## First-time IBD login (user)

1. Agent opens https://research.investors.com/markettrend.aspx (or the myibd Sign In URL).
2. User clicks **Take Control** → signs in at myibd.investors.com (password manager / 2FA).
3. User says **done**.
4. Agent reloads MarketTrend. Signed in if **Sign In** is gone and The Big Picture is not truncated with **Register now!**.
