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

Login: `news-portals`. Never store passwords.

## When (daily)

- Evening wrap (after RTH / into AH)
- FULL CHECK step 8 (before SelfIDB50 FFTY fallback)
- User says IBD lists / WSJ capture / auto-capture

## URLs (research.investors.com, session cookies)

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
| WSJ | https://www.wsj.com/ |
| WSJ Markets | https://www.wsj.com/market-data |

## Steps

1. `browser_tabs` list. Reuse the IBD/WSJ tab if open.
2. Open MarketTrend or IBD 50. **Signed in** = My Account / Dashboard, table rows present, no Sign In. **Signed out** = Sign In in header or Register now. Then SSO `https://myibd.investors.com/secure/signin.aspx?eurl=…` (WSJ session often carries). Only then ask Take Control / **done**.
3. For each list URL: `browser_navigate` then CDP `Runtime.evaluate` — pull `table tr` cells. Compact `TICKER|col|price`. Skip header rows. Record `Screen results as of …`.
4. WSJ homepage: lead headlines + tape (DJIA / S&P / Nasdaq / 10Y / VIX). No Sign In = session live.
5. Overwrite `agents/ssr-st/workspace/Documents/ibd_stock_lists.md` and append WSJ leads to `news_sweep.md` or the same file's WSJ section.
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
- `news_sweep.md` — WSJ/MW headlines (RSS floor still runs)

Safari/Chrome already-open tabs: `news_portals.py --safari` (hosts include investors.com + wsj.com).

## Local bot (optional, your laptop)

**Do not paste passwords in chat.** Copy `agents/ssr-st/secrets/portals.example.json` → `portals.json`. Emails in the file. Passwords in env `WSJ_PASSWORD` / `IBD_PASSWORD`.

```bash
tradepilot portal-capture --login
tradepilot portal-capture
```

Same script: `python3 agents/ssr-st/workspace/Documents/market_data/ibd_wsj_capture.py`.

`--login` is headed Chromium (2FA). It saves `storage_state.json` (gitignored). Later runs use cookies only. Needs Playwright. If 2FA/bot-check blocks the script, stay on this skill’s Cursor browser path.
