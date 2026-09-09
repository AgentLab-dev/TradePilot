"""Playwright login + capture for WSJ and IBD Stock Lists.

Uses the subscriber account on this laptop (env / keyring / portals.json).
Does not scrape behind the paywall without that session.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys

from tradepilot.portals.paths import (
    OUT_LISTS,
    OUT_NEWS,
    PROFILE_DIR,
    SECRETS,
    STATE_PATH,
)
from tradepilot.portals.secrets import (
    credential_flags,
    load_cfg,
    load_env,
    portal_email,
    portal_password,
    portal_signin,
)

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
DEFAULT_SIGNIN = {
    "wsj": "https://www.wsj.com/",
    "ibd": "https://myibd.investors.com/secure/signin.aspx",
}
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
SIGNED_OUT_JS = (
    "() => /\\bSign In\\b/.test((document.body.innerText || '').slice(0, 2500))"
)


def require_playwright():
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except ImportError:
        print(
            "Playwright not installed.\n"
            "  pip install playwright && python3 -m playwright install chromium\n"
            "Or skip the local bot and use the Cursor skill ibd-wsj-capture "
            "(signed-in browser — do not paste passwords in chat).",
            file=sys.stderr,
        )
        raise SystemExit(2)


def session_status() -> dict:
    """Whether a local session exists. Never includes cookies or passwords."""
    load_env()
    flags = credential_flags()
    cookie_hosts: list[str] = []
    if STATE_PATH.is_file():
        try:
            data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
            cookie_hosts = sorted(
                {
                    str(c.get("domain") or "").lstrip(".")
                    for c in data.get("cookies") or []
                    if c.get("domain")
                }
            )
        except (OSError, json.JSONDecodeError, TypeError):
            cookie_hosts = []
    profile_exists = PROFILE_DIR.is_dir() and any(PROFILE_DIR.iterdir())
    return {
        "storage_state": STATE_PATH.is_file(),
        "browser_profile": profile_exists,
        "cookie_hosts": cookie_hosts,
        "lists_out": str(OUT_LISTS),
        "news_out": str(OUT_NEWS),
        "secrets_dir": str(SECRETS),
        **flags,
    }


def _fill_first(page, selectors: tuple[str, ...], value: str) -> bool:
    if not value:
        return False
    for sel in selectors:
        loc = page.locator(sel)
        if loc.count():
            loc.first.fill(value)
            return True
    return False


def _click_first(page, selectors: tuple[str, ...]) -> bool:
    for sel in selectors:
        loc = page.locator(sel)
        if loc.count():
            loc.first.click()
            return True
    return False


def _wait_signed_in(page, wait_ms: int) -> bool:
    step = 2000
    elapsed = 0
    while elapsed < wait_ms:
        try:
            if not page.evaluate(SIGNED_OUT_JS):
                return True
        except Exception:
            pass
        page.wait_for_timeout(step)
        elapsed += step
    try:
        return not page.evaluate(SIGNED_OUT_JS)
    except Exception:
        return False


def _new_context(playwright, *, headed: bool):
    SECRETS.mkdir(parents=True, exist_ok=True)
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    return playwright.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE_DIR),
        headless=not headed,
        viewport={"width": 1280, "height": 800},
    )


def _save_storage(context) -> None:
    context.storage_state(path=str(STATE_PATH))


def login(*, wait_seconds: int | None = None) -> dict:
    """Headed Chromium. Fill email/password from local secrets if the form is simple; wait for 2FA."""
    require_playwright()
    from playwright.sync_api import sync_playwright

    load_env()
    cfg = load_cfg()
    wait_ms = int(
        (wait_seconds if wait_seconds is not None else int(os.environ.get("PORTAL_LOGIN_WAIT_SECONDS") or 120))
        * 1000
    )
    results: dict[str, str] = {}
    with sync_playwright() as p:
        context = _new_context(p, headed=True)
        page = context.pages[0] if context.pages else context.new_page()
        for name in ("wsj", "ibd"):
            url = portal_signin(cfg, name, DEFAULT_SIGNIN[name])
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(1500)
            try:
                already = not page.evaluate(SIGNED_OUT_JS)
            except Exception:
                already = False
            if already:
                print(f"{name.upper()} already signed in (profile).", flush=True)
                results[name] = "already_signed_in"
                continue
            email, pw = portal_email(cfg, name), portal_password(cfg, name)
            _fill_first(
                page,
                ('input[type="email"]', 'input[name="email"]', "#username", "#email", 'input[name="username"]'),
                email,
            )
            if pw and not page.locator('input[type="password"]').count():
                _click_first(
                    page,
                    (
                        'button[type="submit"]',
                        'input[type="submit"]',
                        'button:has-text("Continue")',
                        'button:has-text("Next")',
                    ),
                )
                page.wait_for_timeout(2000)
            _fill_first(page, ('input[type="password"]', "#password", "#pass", 'input[name="password"]'), pw)
            if pw:
                _click_first(
                    page,
                    (
                        'button[type="submit"]',
                        'input[type="submit"]',
                        'button:has-text("Sign in")',
                        'button:has-text("Sign In")',
                        'button:has-text("Log in")',
                    ),
                )
            print(
                f"Finish {name.upper()} Sign In / 2FA in the window "
                f"({wait_ms // 1000}s). Do not paste the password in chat.",
                flush=True,
            )
            ok = _wait_signed_in(page, wait_ms)
            results[name] = "signed_in" if ok else "timeout_finish_in_browser"
        _save_storage(context)
        context.close()
    print(f"Saved session (no password) → {STATE_PATH}")
    print(f"Browser profile → {PROFILE_DIR}")
    out = session_status()
    out["login"] = results
    return out


def _append_wsj_news(stamp: str, leads: list[str], signed_out: bool) -> None:
    lines = [f"## WSJ (local bot) — {stamp}", ""]
    if signed_out:
        lines.append("Signed out. Re-run `tradepilot portal-capture --login`.")
    for h in leads:
        lines.append(f"- {h}")
    lines.append("")
    blob = "\n".join(lines)
    if OUT_NEWS.is_file():
        text = OUT_NEWS.read_text(encoding="utf-8")
        updated, n = re.subn(
            r"## WSJ \(local bot\).*?(?=\n## |\Z)",
            blob,
            text,
            count=1,
            flags=re.S,
        )
        if not n:
            updated = text.rstrip() + "\n\n" + blob
        OUT_NEWS.write_text(updated if updated.endswith("\n") else updated + "\n", encoding="utf-8")
    else:
        OUT_NEWS.write_text(blob + "\n", encoding="utf-8")


def capture() -> dict:
    """Reuse the saved profile / cookies. Write IBD lists + WSJ leads. No password needed."""
    require_playwright()
    from playwright.sync_api import sync_playwright

    load_env()
    if not STATE_PATH.is_file() and not (PROFILE_DIR.is_dir() and any(PROFILE_DIR.iterdir())):
        print("No storage_state.json or browser-profile. Run --login first.", file=sys.stderr)
        raise SystemExit(1)
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    blocks = [
        f"# IBD + WSJ capture — {stamp}",
        "",
        "_Local bot (`tradepilot portal-capture`). Session cookies, not a chat password._",
        "",
    ]
    wsj_signed_out = False
    list_counts: dict[str, int] = {}
    with sync_playwright() as p:
        context = _new_context(p, headed=False)
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(WSJ, wait_until="domcontentloaded", timeout=60000)
        wsj = page.evaluate(WSJ_JS)
        wsj_signed_out = bool(wsj.get("signedOut"))
        blocks.append("## WSJ")
        if wsj_signed_out:
            blocks.append("Signed out. Re-run `--login`.")
        leads = list(wsj.get("leads") or [])
        for h in leads:
            blocks.append(f"- {h}")
        blocks.append("")
        for title, url in LISTS:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(1500)
            data = page.evaluate(EXTRACT_JS)
            n = int(data.get("n") or 0)
            list_counts[title] = n
            blocks.append(f"## {title} ({n})")
            if data.get("signedOut"):
                blocks.append("Signed out — tables may be truncated. Re-run `--login`.")
            if data.get("asof"):
                blocks.append(f"_{data['asof']}_")
            for row in data.get("tickers") or []:
                blocks.append(f"- {row}")
            blocks.append("")
        _save_storage(context)
        context.close()
    OUT_LISTS.write_text("\n".join(blocks).rstrip() + "\n", encoding="utf-8")
    _append_wsj_news(stamp, leads, wsj_signed_out)
    print(f"Wrote {OUT_LISTS}")
    print(f"Updated {OUT_NEWS}")
    return {
        "lists": str(OUT_LISTS),
        "news": str(OUT_NEWS),
        "wsj_signed_out": wsj_signed_out,
        "list_counts": list_counts,
        **session_status(),
    }
