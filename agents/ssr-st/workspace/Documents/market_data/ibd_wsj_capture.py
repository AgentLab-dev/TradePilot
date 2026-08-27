#!/usr/bin/env python3
"""Local IBD + WSJ capture bot. Passwords never go to git or stdout.

  python3 ibd_wsj_capture.py --login   # headed Chromium, save cookies
  python3 ibd_wsj_capture.py           # reuse storage_state.json, write lists

Emails/URLs: agents/ssr-st/secrets/portals.json (copy from portals.example.json).
Passwords: env WSJ_PASSWORD / IBD_PASSWORD (optional; --login can be manual 2FA).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOCS = HERE.parent
SECRETS = HERE.resolve().parents[2] / "secrets"
CFG_PATH = SECRETS / "portals.json"
STATE_PATH = SECRETS / "storage_state.json"
OUT_LISTS = DOCS / "ibd_stock_lists.md"
OUT_NEWS = DOCS / "news_sweep.md"

LISTS = [
    ("IBD 50", "https://research.investors.com/stock-lists/ibd-50/"),
    ("Sector Leaders", "https://research.investors.com/stock-lists/sector-leaders"),
    ("Stock Spotlight", "https://research.investors.com/stock-lists/stock-spotlight/"),
    ("Big Cap 20", "https://research.investors.com/stock-lists/big-cap-20/"),
    ("New Highs", "https://research.investors.com/stock-lists/new-highs/"),
    ("RS at New High", "https://research.investors.com/stock-lists/relative-strength-at-new-high/"),
    ("IPO Leaders", "https://research.investors.com/stock-lists/ipo-leaders/"),
    ("Funds Buying", "https://research.investors.com/stock-lists/stocks-that-funds-are-buying/"),
]
WSJ = "https://www.wsj.com/"
EXTRACT_JS = """() => {
  const rows = [];
  for (const t of document.querySelectorAll('table')) {
    for (const tr of t.querySelectorAll('tr')) {
      const cells = Array.from(tr.querySelectorAll('th,td'))
        .map(c => c.innerText.replace(/\\s+/g,' ').trim()).filter(Boolean);
      if (cells.length >= 2 && !/^Symbol/i.test(cells[0]) && !/^# of Funds/i.test(cells[0]))
        rows.push(cells[0].split(' ')[0] + '|' + cells[1] + '|' + cells[2]);
    }
  }
  const asof = (document.body.innerText.match(/Screen results as of [^\\n]+/) || [])[0] || '';
  const signedOut = /\\bSign In\\b/.test((document.body.innerText || '').slice(0, 2500));
  return { url: location.href, title: document.title, asof, signedOut, n: rows.length, tickers: rows };
}"""
WSJ_JS = """() => {
  const signedOut = /\\bSign In\\b/.test((document.body.innerText || '').slice(0, 2000));
  const leads = Array.from(document.querySelectorAll('h2, h3, [data-testid="headline"] a, h2 a, h3 a'))
    .map(el => (el.innerText || '').replace(/\\s+/g,' ').trim())
    .filter(t => t.length > 24 && t.length < 180)
    .slice(0, 12);
  return { url: location.href, title: document.title, signedOut, leads };
}"""


def load_cfg() -> dict:
    if not CFG_PATH.exists():
        return {}
    return json.loads(CFG_PATH.read_text())


def portal_email(cfg: dict, name: str) -> str:
    block = cfg.get(name) if isinstance(cfg.get(name), dict) else {}
    return str(block.get("email") or cfg.get(f"{name}_email") or "")


def portal_password(cfg: dict, name: str) -> str:
    env = os.environ.get(f"{name.upper()}_PASSWORD", "")
    if env:
        return env
    block = cfg.get(name) if isinstance(cfg.get(name), dict) else {}
    return str(block.get("password") or "")


def portal_signin(cfg: dict, name: str, default: str) -> str:
    block = cfg.get(name) if isinstance(cfg.get(name), dict) else {}
    return str(block.get("signin") or block.get("url") or default)


def require_playwright():
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except ImportError:
        print(
            "Playwright not installed. "
            "pip install playwright && python3 -m playwright install chromium\n"
            "Or skip the local bot and use the Cursor skill ibd-wsj-capture "
            "(signed-in browser — do not paste passwords in chat).",
            file=sys.stderr,
        )
        raise SystemExit(2)


def login() -> None:
    require_playwright()
    from playwright.sync_api import sync_playwright

    cfg = load_cfg()
    SECRETS.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        for name, default in (
            ("wsj", "https://www.wsj.com/"),
            ("ibd", "https://myibd.investors.com/secure/signin.aspx"),
        ):
            page.goto(portal_signin(cfg, name, default), wait_until="domcontentloaded", timeout=60000)
            email, pw = portal_email(cfg, name), portal_password(cfg, name)
            if email:
                for sel in ('input[type="email"]', 'input[name="email"]', "#username", "#email"):
                    loc = page.locator(sel)
                    if loc.count():
                        loc.first.fill(email)
                        break
            if pw:
                for sel in ('input[type="password"]', "#password", "#pass"):
                    loc = page.locator(sel)
                    if loc.count():
                        loc.first.fill(pw)
                        break
            print(f"Finish {name.upper()} Sign In / 2FA in the window (120s)…", flush=True)
            page.wait_for_timeout(120_000)
        context.storage_state(path=str(STATE_PATH))
        browser.close()
    print(f"Saved session (no password) → {STATE_PATH}")


def capture() -> None:
    require_playwright()
    from playwright.sync_api import sync_playwright

    if not STATE_PATH.exists():
        print("No storage_state.json. Run --login first.", file=sys.stderr)
        raise SystemExit(1)
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    blocks = [f"# IBD + WSJ capture — {stamp}", "", "_Local bot (`ibd_wsj_capture.py`). Session cookies, not a chat password._", ""]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=str(STATE_PATH))
        page = context.new_page()
        page.goto(WSJ, wait_until="domcontentloaded", timeout=60000)
        wsj = page.evaluate(WSJ_JS)
        blocks.append("## WSJ")
        if wsj.get("signedOut"):
            blocks.append("Signed out. Re-run `--login`.")
        for h in wsj.get("leads") or []:
            blocks.append(f"- {h}")
        blocks.append("")
        for title, url in LISTS:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(1500)
            data = page.evaluate(EXTRACT_JS)
            blocks.append(f"## {title} ({data.get('n', 0)})")
            if data.get("signedOut"):
                blocks.append("Signed out — tables may be truncated. Re-run `--login`.")
            if data.get("asof"):
                blocks.append(f"_{data['asof']}_")
            for row in data.get("tickers") or []:
                blocks.append(f"- {row}")
            blocks.append("")
        browser.close()
    OUT_LISTS.write_text("\n".join(blocks).rstrip() + "\n")
    print(f"Wrote {OUT_LISTS}")


def main() -> int:
    ap = argparse.ArgumentParser(description="IBD + WSJ local capture bot")
    ap.add_argument("--login", action="store_true", help="Headed login; save storage_state.json")
    args = ap.parse_args()
    if args.login:
        login()
    else:
        capture()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
