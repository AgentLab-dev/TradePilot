---
name: news-portals
description: >-
  Logs into and reads IBD, WSJ, MarketWatch, and Barron's (desk-sources set),
  plus Yahoo Finance and other FULL CHECK news portals. Use on FULL CHECK
  step 9, evening wrap news watch, WSJ, MW, IBD, Barron's, investor-day
  search, or when the user asks to login to a news site. Prefers MCP, then
  Cursor browser login, then Safari/Chrome already-signed-in tabs (headless
  tail), then public RSS. Whale Watch flow stays Robinhood MCP.
---

# News portals (IBD · WSJ · MW · Barron's)

FULL CHECK step 9 and evening wrap **news watch** must read headlines, not guess
behind a paywall. There is **no WSJ / MarketWatch / IBD / Barron's MCP**. Zapier
has no WSJ-family app. Use the ladder below. **Never store passwords in git.**
**Never paste passwords in chat.**

## Ladder (stop at the first that works)

| # | Method | When | What it gets |
|---|---|---|---|
| 0 | **MCP** | Always check first | **Playwright** (`project-0-TradePilot-playwright` in `.cursor/mcp.json`) is a valid news browser. **Whale Watch** = Robinhood MCP + `whale_check.py`. No WSJ/MW/IBD/Barron's content MCP. Zapier RSS is not a login. |
| 1 | **Cursor browser** | Optional built-in tab | `cursor-ide-browser` if present. Do **not** require Tools & MCP → Browser (On). |
| 2 | **Headless tail** | Safari or Chrome already signed in | Same pattern as Gmail: read the open tab. Do not open a new login. |
| 3 | **Public RSS** | Always as the floor | Headlines + links. Not full paywall text. Script: `news_portals.py`. |

## 0 — MCP check (do this every run)

1. Project `.cursor/mcp.json` has **Robinhood** + **Playwright**. Playwright is the Tools & MCP server and is valid for news login. There is no WSJ, MarketWatch, IBD, or Barron's content MCP. Zapier has no WSJ-family app. Do not invent one.
2. Built-in **Browser Tab** is **Settings → Browser & Network** (not Tools & MCP). `cursor-ide-browser` is optional. Do **not** fail the run because Tools & MCP → Browser is Off. If Playwright tools are missing: Enable the Playwright server in Tools & MCP, then Cmd+Shift+P → **Developer: Reload Window**, then a **new** chat.
3. **Whale Watch** is not a website login. Run `python3 whale_check.py` / Robinhood option volume vs OI. Unusual Whales has no MCP here.

If a WSJ MCP appears later, use it and skip 1–2.

## Where to Sign In (never paste passwords in chat)

**SSO (confirmed 2026-09-09):** Log in **once at WSJ** (`https://www.wsj.com/`). Then open **IBD from the WSJ header**. That autologins IBD + MarketWatch + Barron's. Do **not** start at `https://www.investors.com/?ibdsilentlogin=true` unless the WSJ header IBD link is missing.

| Site | Open this |
|---|---|
| WSJ (login first) | https://www.wsj.com/ |
| IBD (from WSJ header) | Header **IBD** → `myibd.investors.com/secure/signin.aspx?...&prompt=none` (lands on investors.com) |
| MarketWatch | Header **MarketWatch** (`?mod=WSJ_NavHat`) |
| Barron's | Header **Barron's** (`?mod=WSJ_NavHat`) |

Then:

1. Sign in on **WSJ only** (`.env` `WSJ_USER` / `WSJ_PASSWORD`, or Take Control / 2FA). Never paste the password in chat.
2. Click **IBD** in the WSJ / Dow Jones header. Wait for autologin.
3. Open MarketWatch and Barron's from the same header. Confirm no header **Sign In**.
4. If 2FA or captcha: Take Control on the **WSJ** tab, then **done**.

Optional laptop: copy `.env.example` → `.env` locally, then `tradepilot portal-capture --login`. Never paste secrets here.

After **done**, snapshot and continue. Do not ask for a password.

## 1 — Browser (Playwright MCP or optional Cursor Browser Tab)

Prefer Playwright (`project-0-TradePilot-playwright`). `cursor-ide-browser` is optional.

```
browser_tabs list
browser_navigate url=https://www.wsj.com/
# Sign in on WSJ only. Then click header IBD (autologin), then header MarketWatch and Barron's.
browser_lock lock
browser_snapshot
```

- **Signed in** if the snapshot has account/profile and **no** header "Sign In". Read the page.
- **Signed out** if **Sign In** is in the WSJ header. Sign in there once; do not fill four portals separately.
- After WSJ Sign In, open IBD from the WSJ header (that hop is the autologin). Then MarketWatch and Barron's from the same header (`?mod=WSJ_NavHat`). Do not skip Barron's.
- After IBD Sign In, Stock Lists / MarketTrend capture is `ibd-wsj-capture` (research.investors.com). Skip the profile overlay if it appears; stay on the list page (do not follow Skip to investors.com until tables are captured).
- Yahoo `https://finance.yahoo.com/` — usually no login.
- Unlock when finished.

Do **not** brute-force the Sign In form. WSJ-family sites use SSO + bot checks.

## 2 — Headless tail (Safari / Chrome already logged in)

Use when the user already has IBD/WSJ/MW/Barron's open and signed in (the Gmail Safari path).

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

**PPS news (OKTA 8/26):** homepage will be the mega-cap. PPS-T7 queries `{TICKER} earnings`
on WSJ/MW/IR for every **2–7d category** name each day. PPS-T1 does the same on **0d/1d**.
Do not wait until after AMC.

## Portals

See [portals.md](portals.md) for URLs. Login once at WSJ, then header-hop IBD (autologin), then MarketWatch and Barron's from the same hat. Yahoo / Reuters / CNBC are backup. Whale Watch = Robinhood, not unusualwhales.com.

## Secrets

`agents/ssr-st/secrets/portals.json` is gitignored. Prefer repo `.env` (`WSJ_USER` / `IBD_USER` / `WSJ_PASSWORD` / `IBD_PASSWORD`) or keyring (`tradepilot` / `wsj-password`). Login lives in the Cursor browser or `storage_state.json` + `browser-profile/` after `tradepilot portal-capture --login`. Never paste a password in chat. See `agents/ssr-st/workspace/Documents/portal_login.md`.

## FULL CHECK / evening wrap

Load this skill on step 9 / news watch. Run RSS. If a named article is paywalled, use ladder 1 or 2. Then the investor-day query. Do not skip news because Sign In is showing.

On FULL CHECK this is a **fail condition**, not a best-effort. There is no `desk-sources-capture` folder — this skill plus `ibd-wsj-capture` is that job.

### Fail the FULL CHECK if

- The four portals were not actually opened after the WSJ header SSO hop (WSJ → header IBD → header MarketWatch / Barron's). RSS-only does not count — WSJ public RSS is often months stale.
- `"investor day" OR "analyst day" OR "capital markets day"` was not run on book + SMH/memory/AI + READTHROUGH peers (SNDK 8/13).
- A **0d/1d** name has no `{TICKER} earnings` line on WSJ/MW/IR (OKTA 8/26 — homepage was NVDA).
- A **PPS-T7 ON** (2–7d category) name has no `{TICKER} earnings` line.
- Calendar UNION is missing a leg: Nasdaq `earnings_radar` ∪ Robinhood `get_earnings_calendar` ∪ fundamentals next-earnings ∪ investor-day search.
- News was skipped because Sign In was showing. Stop and ask Take Control; homepage snapshot is still required signed-out.

**Still optional:** MarketTrend % numbers, Zapier WSJ-family (no app), Unusual Whales, laptop `tradepilot portal-capture`, Reuters/CNBC backup once the four are open, Yahoo homepage if the Yahoo RSS floor already ran.
