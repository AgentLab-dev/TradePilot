# Sites Publisher

Trade Pilot bot that publishes the FULL CHECK universe flags page to Google Sites.

Zapier is not used. New Google Sites has no page-HTML write API, so the bot publishes a Google Doc from the same HTML and you embed that Doc on the site, then click Publish.

```bash
tradepilot sites-publish --html-only
tradepilot sites-publish --login
tradepilot sites-publish
```

OAuth Desktop client JSON goes in `secrets/credentials.json` (not committed).
