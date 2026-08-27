---
name: news-portals
description: >-
  Logs into and reads WSJ, MarketWatch, IBD MarketTrend, Yahoo Finance, and
  other FULL CHECK news portals. Use on FULL CHECK step 9, evening wrap news
  watch, WSJ, MW, IBD, investor-day search, or when the user asks to login to a
  news site. Prefers MCP, then Cursor browser login, then Safari/Chrome
  already-signed-in tabs (headless tail), then public RSS. Whale Watch flow
  stays Robinhood MCP.
---

# News portals (WSJ · MW · Yahoo · others)

FULL CHECK step 9 and evening wrap **news watch** must read headlines, not guess
behind a paywall. There is **no WSJ or MarketWatch MCP**. Zapier has no WSJ/MW
app. Use the ladder below. **Never store passwords in git.**

## Ladder (stop at the first that works)

| # | Method | When | What it gets |
|---|---|---|---|
| 0 | **MCP** | Always check first | **None today** for WSJ/MW. **Whale Watch** = Robinhood MCP + `whale_check.py`. Zapier RSS exists but is not a login. |
| 1 | **Cursor browser** | First login / 2FA / paywall article | Session in the Cursor-owned tab. User completes **Sign In** if asked. |
| 2 | **Headless tail** | Safari or Chrome already signed in | Same pattern as Gmail: read the open tab. Do not open a new login. |
| 3 | **Public RSS** | Always as the floor | Headlines + links. Not full paywall text. Script: `news_portals.py`. |

## 0 — MCP check (do this every run)

1. Project MCP is Robinhood only (`.cursor/mcp.json`). No WSJ server.
2. Zapier `discover_zapier_actions` for "Wall Street Journal" and "MarketWatch" returns **no app**. Do not invent one.
3. **Whale Watch** is not a website login. Run `python3 whale_check.py` / Robinhood option volume vs OI. Unusual Whales has no MCP here.

If a WSJ MCP appears later, use it and skip 1–2.

## 1 — Cursor browser (best first login)

Namespace: `cursor-ide-browser`.

```
browser_tabs list
browser_navigate url=https://www.wsj.com/   (newTab true; position side if the user must type)
browser_lock lock
browser_snapshot
```

- **Signed in** if the snapshot has account/profile and **no** "Sign In". Read Markets + the article.
- **Signed out** if **Sign In** / **Subscribe** is in the header (verified 2026-08-26 on `https://www.wsj.com/`). Stop. Tell the user to click **Take Control**, sign in (2FA ok), then say **done**. Do not type a password from chat.
- Then MarketWatch `https://www.marketwatch.com/` in the same browser (WSJ/MW often share Dow Jones SSO).
- IBD MarketTrend `https://research.investors.com/markettrend.aspx`. Sign In is `https://myibd.investors.com/secure/signin.aspx`. After WSJ is signed in, myibd often SSO-lands already authenticated (Dow Jones). Newsletter `ibdsilentlogin=true` alone does **not** carry a session. Skip the profile overlay if it appears; stay on MarketTrend (do not follow Skip to investors.com until you have captured exposure + Big Picture).
- Yahoo `https://finance.yahoo.com/` — usually no login.
- Unlock when finished.

Do **not** brute-force the Sign In form. WSJ uses SSO + bot checks.

## 2 — Headless tail (Safari / Chrome already logged in)

Use when the user already has WSJ/MW open and signed in (the Gmail Safari path).

```
python3 agents/ssr-st/workspace/Documents/market_data/news_portals.py --safari
python3 agents/ssr-st/workspace/Documents/market_data/news_portals.py --list-tabs
```

`--safari` times out in ~8s so a macOS Automation prompt cannot hang FULL CHECK. If it times out: **System Settings → Privacy & Security → Automation** — allow the calling app (Cursor / Terminal) to control Safari and/or Chrome. Then retry.

Do not dump full HTML. Take headlines, dek, and article URL.

## 3 — Public RSS (always run)

```
python3 agents/ssr-st/workspace/Documents/market_data/news_portals.py
python3 agents/ssr-st/workspace/Documents/market_data/news_portals.py --query "investor day"
```

Writes `agents/ssr-st/workspace/Documents/news_sweep.md`. Cite title + source + date. RSS is the floor when login fails.

**WSJ public RSS is often months stale.** MarketWatch topstories and the WSJ **homepage** (even signed out) are current. Use the Cursor browser homepage for today's lead; Sign In only when you need the article body.

Required FULL CHECK / wrap query still runs after the sweep:

`"investor day" OR "analyst day" OR "capital markets day"` on book + SMH/memory/AI + READTHROUGH peers.

## Portals

See [portals.md](portals.md) for URLs. Defaults: WSJ, MarketWatch, Yahoo Finance, Reuters/CNBC backup. Whale Watch = Robinhood, not unusualwhales.com.

## Secrets

`agents/ssr-st/secrets/portals.json` is gitignored. Do not put passwords there if you can use env vars (`WSJ_PASSWORD` / `IBD_PASSWORD`). Login lives in the browser session or `storage_state.json` after `ibd_wsj_capture.py --login`. Never paste a password in chat.

## FULL CHECK / evening wrap

Load this skill on step 9 / news watch. Run RSS. If a named article is paywalled, use ladder 1 or 2. Then the investor-day query. Do not skip news because Sign In is showing.
