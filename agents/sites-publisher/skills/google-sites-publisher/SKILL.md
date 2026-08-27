---
name: google-sites-publisher
description: Publishes Trade Pilot FULL CHECK as one 9-column x 9-row Google Doc table. Use when the user says Google Sites, sites-publish, or publish the universe.
---

# Google Sites Publisher

One table only. 9 columns, 9 rows (INTU through HOOD). No Zapier.

```bash
tradepilot sites-publish
```

Columns: Ticker, Why, STKK, STNOW, 3Good, Whale, IV / structure, Event, After gate.

Do not put the 24-name scan in the Doc. Skip Sites API list (it 404s and slows the run).

After upload: Sites editor → Insert → **Embed** the `/pub` URL (not Insert → Docs) → Publish.
