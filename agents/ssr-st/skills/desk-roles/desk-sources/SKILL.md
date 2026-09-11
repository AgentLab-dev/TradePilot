---
name: desk-sources
description: Desk role — open IBD / WSJ / MW / Barron's / Yahoo / Reddit. Write access_line.
---

# Role: desk-sources

Supervisor only. Do not call other roles.

Load: `agents/ssr-st/skills/news-portals/SKILL.md` · `agents/ssr-st/skills/ibd-wsj-capture/SKILL.md`  
Desk: `docs/grokbot-desk/skills/desk-sources-capture/SKILL.md`

## Payload

```text
access_line: IBD|WSJ|MW|Barron's|Yahoo|Whale|Reddit|ApeWisdom OK/SKIP
artifacts: ibd_stock_lists.md · news_sweep.md · desk_sources_YYYY-MM-DD.md
```

Required Yahoo open: `https://finance.yahoo.com/` (public; no login). RSS is not a substitute.

## Fail

- Any of the five homepages not opened (WSJ, header IBD, MW, Barron's, Yahoo). RSS-only does not count
- Reddit required-sub scan skipped
- Asked the user to paste IBD tables

Status `ok` only with a complete access line.
