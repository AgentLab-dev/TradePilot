# News portal sessions (WSJ + IBD)

**Never paste passwords into chat. Never commit `portals.json` or `storage_state.json`.**

Trade Pilot is the bot. This folder is local secrets only.

## What to do (you)

1. Copy `portals.example.json` → `portals.json`.
2. Put your **emails** (and URLs if they change) in `portals.json`.
3. Put passwords in the environment, not in git:

```bash
export WSJ_PASSWORD='…'
export IBD_PASSWORD='…'
```

Optional last resort: a `"password"` key inside `portals.json`. That file is gitignored and still a risk if the laptop is copied. Env vars are better.

4. One headed login (2FA ok), then unattended capture:

```bash
tradepilot portal-capture --login
tradepilot portal-capture
```

Same as `python3 agents/ssr-st/workspace/Documents/market_data/ibd_wsj_capture.py`.

`--login` opens Chromium, can fill email/password from env if the form is simple, then waits so you can finish 2FA. It writes `storage_state.json` (cookies). Later runs reuse that file and **do not need the password**.

Needs: `pip install playwright && python3 -m playwright install chromium`

## What the agent does

- **Default:** Cursor browser (`ibd-wsj-capture` skill). You click Sign In if asked. No password in chat.
- **Local bot:** the script above, using saved cookies.
- **Safari already signed in:** `news_portals.py --safari`

WSJ and IBD often share Dow Jones SSO. One `--login` may cover both.

## Files (gitignored)

| File | What |
|---|---|
| `portals.json` | Emails + URLs |
| `storage_state.json` | Playwright cookies after `--login` |
| `browser-profile/` | unused reserved path |
