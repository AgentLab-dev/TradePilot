---
name: ibd-wsj-capture
description: >-
  Daily auto-capture of IBD Stock Lists and WSJ headlines in the signed-in Cursor
  browser. Use on FULL CHECK step 8, evening wrap, SelfIDB50, IBD lists, WSJ
  capture, or when the user asks to scrape / auto-capture IBD or WSJ. Do not ask
  the user to paste list pages.
---

# IBD + WSJ auto-capture (daily)

Trade Pilot owns this. Not a second agent. **Do not ask the user to clipboard-paste IBD tables.** Navigate, extract, write files.

Login: `news-portals`. **SSO (confirmed 2026-09-09):** Log in **once at WSJ** (`https://www.wsj.com/`). Then open **IBD from the WSJ header**. That autologins IBD + MarketWatch + Barron's. Do **not** start at `https://www.investors.com/?ibdsilentlogin=true` unless the WSJ header IBD link is missing. Never store passwords. Never paste passwords. Take Control, then user says **done**.

## When (daily)

- Evening wrap (after RTH / into AH)
- FULL CHECK step 8 (before SelfIDB50 FFTY fallback) — **mandatory fail**, not best-effort
- User says IBD lists / WSJ capture / auto-capture

On FULL CHECK this repo has no `desk-sources-capture` folder. Load this skill plus `news-portals`.

### Fail the FULL CHECK if

- **IBD 50** was not opened, or the table is empty / as-of is not today, unless Sign In still blocks after Take Control / **done** (then FFTY + `rs_screen.py` is the only fallback).
- Any of these Stock List URLs was not opened: Sector Leaders, Big Cap 20, Spotlight, New Highs, RS at New High, IPO Leaders, Funds Buying.
- MarketTrend was not opened (signed-in when possible). MarketTrend **%** itself is optional if the page loaded.
- `ibd_stock_lists.md` is not dated today.
- The agent asked the user to paste list pages.

WSJ + MarketWatch + Barron's capture on this skill still feeds step 9; fail conditions for those pages live in `news-portals`.

## Login / open (exact URLs — WSJ first)

| Site | URL |
|---|---|
| WSJ (login first) | https://www.wsj.com/ |
| IBD | WSJ header **IBD** (fallback only: https://www.investors.com/?ibdsilentlogin=true) |
| MarketWatch | https://www.marketwatch.com/?mod=WSJ_NavHat&mod=WSJ_NavHat |
| Barron's | https://www.barrons.com/?mod=WSJ_NavHat&mod=WSJ_NavHat |

If **Sign In** is in the header: **Take Control**, user signs in, then **done**.

## Stock list URLs (research.investors.com, after IBD Sign In)

| List | URL |
|---|---|
| IBD 50 | https://research.investors.com/stock-lists/ibd-50/ |
| Sector Leaders | https://research.investors.com/stock-lists/sector-leaders |
| Stock Spotlight | https://research.investors.com/stock-lists/stock-spotlight/ |
| Big Cap 20 | https://research.investors.com/stock-lists/big-cap-20/ |
| New Highs | https://research.investors.com/stock-lists/new-highs/ |
| RS at New High | https://research.investors.com/stock-lists/relative-strength-at-new-high/ |
| IPO Leaders | https://research.investors.com/stock-lists/ipo-leaders/ |
| Funds Buying | https://research.investors.com/stock-lists/stocks-that-funds-are-buying/ |
| MarketTrend | https://research.investors.com/markettrend.aspx |

## Steps

1. `browser_tabs` list. Reuse an IBD/WSJ/MW/Barron's tab if open. Playwright MCP is valid; Cursor Browser Tab is optional.
2. Open https://www.wsj.com/ and sign in. Then open **IBD from the WSJ header** (autologin). Do **not** start at `https://www.investors.com/?ibdsilentlogin=true` unless the header IBD link is missing. **Signed in** = My Account / no Sign In. **Signed out** = Sign In / Subscribe in header. Ask Take Control / **done**. Then IBD 50 and the other Stock Lists.
3. For each list URL: `browser_navigate` then CDP `Runtime.evaluate` — pull `table tr` cells. Compact `TICKER|col|price`. Skip header rows. Record `Screen results as of …`.
4. Open MarketWatch and Barron's from the same Dow Jones hat if needed: https://www.marketwatch.com/?mod=WSJ_NavHat&mod=WSJ_NavHat · https://www.barrons.com/?mod=WSJ_NavHat&mod=WSJ_NavHat. Lead headlines + tape. No Sign In = session live.
5. Overwrite `agents/ssr-st/workspace/Documents/ibd_stock_lists.md` and append WSJ / MW / Barron's leads to `news_sweep.md`.
6. Merge into SelfIDB50: live IBD 50 **replaces** FFTY top-25 when the file is dated today. Still run `rs_screen.py`. Not a trade. Wait for **go**.
7. Unlock the tab.

Profile overlay "Skip and Continue to Investors.com" leaves the list page — **do not click Skip** until tables are extracted.

## Extract snippet

```javascript
(() => {
  const rows = [];
  for (const t of document.querySelectorAll('table')) {
    for (const tr of t.querySelectorAll('tr')) {
      const cells = Array.from(tr.querySelectorAll('th,td'))
        .map(c => c.innerText.replace(/\s+/g,' ').trim()).filter(Boolean);
      if (cells.length >= 2 && !/^Symbol/i.test(cells[0]))
        rows.push(cells[0].split(' ')[0] + '|' + cells[1] + '|' + cells[2]);
    }
  }
  const asof = (document.body.innerText.match(/Screen results as of [^\n]+/) || [])[0] || '';
  return JSON.stringify({ url: location.href, asof, n: rows.length, tickers: rows });
})()
```

## Outputs

- `ibd_stock_lists.md` — all lists + cross-list + as-of dates
- `news_sweep.md` — WSJ / MW / Barron's headlines (RSS floor still runs)

Safari/Chrome already-open tabs: `news_portals.py --safari` (hosts include investors.com + wsj.com + marketwatch.com + barrons.com).

## Local bot (optional, your laptop)

**Do not paste passwords in chat.** Copy `.env.example` → `.env` (`WSJ_USER` / `IBD_USER` / passwords) or `portals.example.json` → `portals.json` (emails) plus env/keyring passwords.

```bash
tradepilot portal-capture --login
tradepilot portal-capture --status
tradepilot portal-capture
```

Same scripts: `portal_login.py` and `ibd_wsj_capture.py` under `agents/ssr-st/workspace/Documents/market_data/`. Localhost trigger: `tradepilot portal-capture --serve` (127.0.0.1; no passwords in the HTTP body).

`--login` is headed Chromium (2FA). It saves `storage_state.json` and `browser-profile/` (gitignored). Later runs use cookies only. Needs Playwright. If 2FA/bot-check blocks the script, stay on this skill’s Cursor browser path. Usage: `agents/ssr-st/workspace/Documents/portal_login.md`.
