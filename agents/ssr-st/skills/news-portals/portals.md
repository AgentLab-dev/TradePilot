# Portal URLs and feeds

Login lives in the browser. These URLs are for the agent, not for storing credentials.

## Homepages — WSJ header SSO (do not fill four passwords)

**SSO (confirmed 2026-09-09):** Log in **once at WSJ** (`https://www.wsj.com/`). Then open **IBD from the WSJ header**. That autologins IBD + MarketWatch + Barron's. Do **not** start at `https://www.investors.com/?ibdsilentlogin=true` unless the WSJ header IBD link is missing. Then open MW and Barron's from the same Dow Jones hat if needed (`?mod=WSJ_NavHat`).

| Portal | Home | Notes |
|---|---|---|
| WSJ | https://www.wsj.com/ | Login first. Header **Sign In** if logged out. |
| IBD | WSJ header **IBD** | Autologin hop. Lands on investors.com. Table proof: research.investors.com IBD 50. |
| MarketWatch | Header **MarketWatch** (`?mod=WSJ_NavHat`) | Already in after the IBD header hop. |
| Barron's | Header **Barron's** (`?mod=WSJ_NavHat`) | Already in after the IBD header hop. |
| Yahoo Finance | https://finance.yahoo.com/ | Public headlines; login optional |
| CNBC | https://www.cnbc.com/ | Backup |
| Reuters | https://www.reuters.com/business/ | Backup |
| Investopedia calendar | https://www.investopedia.com/ | Macro calendar backup |
| IBD MarketTrend | https://research.investors.com/markettrend.aspx | After IBD Sign In. Capture lists via `ibd-wsj-capture`. |

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
| IBD 50 | After IBD Sign In: auto-capture via `ibd-wsj-capture` (Stock Lists URLs). SelfIDB50 (`FFTY` + `rs_screen.py`) is fallback only. |

## First-time login (user)

1. Agent opens **WSJ** and signs in (`.env` or Take Control / 2FA). Never paste a password in chat.
2. Agent clicks **IBD** in the WSJ header (autologin). Then **MarketWatch** and **Barron's** from the same hat.
3. If 2FA/captcha: user Take Control on the **WSJ** tab, then says **done**.
4. Agent snapshots all four. Session should stick for later tabs, including IBD Stock Lists.
