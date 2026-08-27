# Google OAuth for Sites Publisher

Live login file (gitignored): `credentials.json`
Template (safe to commit): `credentials.example.json`

`tradepilot sites-publish --login` writes `token.json` beside them. Never commit `credentials.json` or `token.json`.

## Login access the bot expects

| Field | Value |
|---|---|
| Client type | OAuth **Desktop app** |
| Redirect URI | `http://localhost:8753/` (Google Desktop clients ship as `http://localhost`) |
| Scopes | `https://www.googleapis.com/auth/drive.file` (Sites API uses Drive; `auth/sites` is invalid) |
| APIs to enable | Google Drive API, Google Sites API |
| Auth URI | `https://accounts.google.com/o/oauth2/v2/auth` |
| Token URI | `https://oauth2.googleapis.com/token` |

## What you upload

1. Open [Google Cloud credentials](https://console.cloud.google.com/apis/credentials).
2. Create OAuth client ID → application type **Desktop app**.
3. Desktop clients from Google already include `http://localhost`. The bot listens on `http://localhost:8753/`.
4. Download the JSON.
5. Overwrite this folder’s `credentials.json` with that download (keep the filename `credentials.json`).

Do not paste `client_id` / `client_secret` into chat. Replace the `REPLACE_ME` fields by uploading the Google file.
