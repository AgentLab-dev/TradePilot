---
name: google-sites-publisher
description: Publishes Trade Pilot FULL CHECK universe flags to Google Sites (local HTML, then Google Doc embed). Use when the user says Google Sites, sites-publish, publish the universe, or asks the Sites Publisher bot to go live.
---

# Google Sites Publisher

Trade Pilot bot. No Zapier. Converts the FULL CHECK universe into Sites-safe HTML and publishes it.

## When to run

User says **Google Sites**, **sites-publish**, **publish the universe**, or **Sites Publisher**.

## Command

```bash
tradepilot sites-publish --html-only
tradepilot sites-publish --login
tradepilot sites-publish
```

Default local file: `agents/ssr-st/workspace/Documents/sites/fullcheck-universe-flags.html`

## Connect Google (once)

1. Google Cloud project → enable **Google Drive API** and **Google Sites API**.
2. Create OAuth client type **Desktop app**. Download JSON.
3. Save it as `agents/sites-publisher/secrets/credentials.json` (gitignored).
4. `tradepilot sites-publish --login` then finish consent in the browser.

Token lands at `agents/sites-publisher/secrets/token.json` (gitignored).

## What actually publishes

New Google Sites **cannot write page HTML via API**. The bot:

1. Always writes local Sites-safe HTML (inline CSS, no JS).
2. If authed, uploads that HTML as a **Google Doc** with anyone-with-link reader and prints `webViewLink`.
3. Lists existing Sites on the account.
4. If `GOOGLE_SITES_SOURCE` is set (a site id you already own), copies that site as a new shell.

Finish in Sites: Insert → Docs (or Embed URL) → paste the Doc link → **Publish**.

## Do not

- Do not use Zapier.
- Do not commit `credentials.json` or `token.json`.
- Do not treat model GO as a take on the published page; the HTML already applies the event gate.
