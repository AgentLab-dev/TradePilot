# News portal sessions (WSJ + IBD)

**Never paste passwords into chat. Never commit `portals.json`, `storage_state.json`, `.env`, or `browser-profile/`.**

Trade Pilot is the bot. This folder is local secrets only.

## What to do (you)

1. Copy repo `.env.example` → `.env` and fill `WSJ_USER` / `IBD_USER` / `WSJ_PASSWORD` / `IBD_PASSWORD`, **or** copy `portals.example.json` → `portals.json` (emails only) and put passwords in the environment:

```bash
export WSJ_PASSWORD='…'
export IBD_PASSWORD='…'
```

Optional: macOS keyring instead of a password file:

```bash
python3 -m keyring set tradepilot wsj-password
python3 -m keyring set tradepilot ibd-password
```

Optional last resort: a `"password"` key inside `portals.json`. That file is gitignored and still a risk if the laptop is copied. Env / keyring are better.

2. One headed login (2FA ok), then unattended capture:

```bash
tradepilot portal-capture --login
tradepilot portal-capture --status
tradepilot portal-capture
```

Same as `python3 agents/ssr-st/workspace/Documents/market_data/portal_login.py` then `ibd_wsj_capture.py`.

`--login` opens Chromium, can fill email/password from env/keyring if the form is simple, then waits so you can finish 2FA. It writes `storage_state.json` (cookies) and `browser-profile/`. Later runs reuse those and **do not need the password**.

Needs: `pip install playwright && python3 -m playwright install chromium` (or `pip install -e ".[portals]"`).

Localhost trigger (127.0.0.1 only; no passwords in the HTTP body): `tradepilot portal-capture --serve`

Usage: `agents/ssr-st/workspace/Documents/portal_login.md`

## What the agent does

- **Default:** Cursor browser (`ibd-wsj-capture` skill). You click Sign In if asked. No password in chat.
- **Local bot:** the commands above, using saved cookies.
- **Safari already signed in:** `news_portals.py --safari`

WSJ and IBD often share Dow Jones SSO. One `--login` may cover both.

## Files (gitignored)

| File | What |
|---|---|
| `portals.json` | Emails + URLs |
| `storage_state.json` | Playwright cookies after `--login` |
| `browser-profile/` | Persistent Chromium profile after `--login` |
| `.env` | `WSJ_USER` / `IBD_USER` / passwords (repo root or this folder) |
| `looker.ini` | Looker Core API3 keys (copy from `looker.ini.example`) |

Looker Core is not Looker Studio. See `agents/ssr-st/workspace/Documents/looker_core_api.md`.
