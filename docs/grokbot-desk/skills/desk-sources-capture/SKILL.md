---
name: desk-sources-capture
description: >-
  Capture the TradePilot news-day stack in standing order: IBD lists, WSJ,
  MarketWatch, whale_check.py, then Reddit SOCIAL-ONLY (plus ApeWisdom/Swaggy).
  Skip blocked sources, print the access line, write desk_sources_YYYY-MM-DD.md.
  Use on every FULL CHECK and Five-new NBT, evening wrap news watch, or when the
  user asks for desk sources / NEWS. Never take a ticket from Reddit alone.
---

# Desk sources capture

Every FULL CHECK and Five-new NBT starts here. Capture first, apply second. Do not
skip a source silently — mark `OK` or `SKIP` on the access line.

Pipeline: [`../../NEWS_DAY_PIPELINE.md`](../../NEWS_DAY_PIPELINE.md).
Source map: [`../../WHERE_LATEST_INFO_LIVES.md`](../../WHERE_LATEST_INFO_LIVES.md).
Pack playbook (unchanged): `agents/ssr-st/commands/NEWS.md` + `IBDWSJCAPTURE.md`.

## When

- Every FULL CHECK (before ranking)
- Every Five-new NBT
- Evening wrap news watch
- User says desk sources / NEWS / IBD lists / WSJ / MW

Do **not** ask the user to paste tables or passwords.

## Capture order (required)

1. **IBD lists** — research.investors.com SSO. IBD 50, Sector Leaders, Big Cap 20,
   Spotlight, New Highs, RS, IPO Leaders, Funds Buying, MarketTrend. Apply to **NBT
   universe**. Live IBD 50 replaces FFTY when dated today.
2. **WSJ** — homepage + Markets tape. Login if Sign In. Apply to **tape + vetoes**.
3. **MarketWatch** — tape / headline / catalyst read. Apply to **tape + vetoes**.
4. **WhaleWatch** — `whale_check.py` on candidates + book + NBT. `daily.py` whale n/a
   is a cache miss, **not** a skip. Gate: **Whale ≥ 0**. Live-catalyst flow is stale
   at the open — disregard and read tape.
5. **Reddit SOCIAL-ONLY** — miss-catch D only, never a TAKE source:
   - Required: `r/algotrading`, `r/Quant`, `r/stocks`, `r/investing`,
     `r/StockMarket`, `r/wallstreetbets`, `r/options`, `r/semiconductors`
   - Optional: `r/spacs`, `r/pennystocks`
   - Plus **ApeWisdom** / **Swaggy**
6. **Optional** — Benzinga / Barron's / FedWatch when the tape or calendar needs it
   (same tape/veto layer as WSJ/MW).

Required extra query after WSJ/MW: `"investor day" OR "analyst day" OR "capital markets day"`
on book + SMH/memory/AI + READTHROUGH peers.

## Apply map

| Source | Apply to |
|---|---|
| IBD | NBT universe |
| WSJ / MarketWatch | Tape + vetoes |
| Whale | Gate: Whale ≥ 0 |
| Reddit / ApeWisdom / Swaggy | Miss-catch D only |

**Never Reddit alone TAKE.** Social color can flag a miss-catch D name for a later
all-four + EM > 15% test. It cannot become a 🟢 take by itself.

## Access line (required)

```
IBD|WSJ|MW|Whale|Reddit|ApeWisdom OK/SKIP
```

Example: `IBD OK | WSJ OK | MW OK | Whale OK | Reddit SKIP (blocked) | ApeWisdom OK`

A skipped source must say why (SSO, outage, no MCP, blocked, 2FA). Do not invent a
fill from stale RSS when the live portal failed unless the access line says `SKIP`.

## Output

Write / overwrite `/workspace/desk_sources_YYYY-MM-DD.md`:

```markdown
# Desk sources — YYYY-MM-DD

Access: IBD|WSJ|MW|Whale|Reddit|ApeWisdom OK/SKIP

## IBD (NBT universe)
## WSJ (tape / vetoes)
## MarketWatch (tape / vetoes)
## Whale (flag ≥ 0)
## Reddit SOCIAL-ONLY (miss-catch D)
## ApeWisdom / Swaggy
## Optional (Benzinga / Barron's / FedWatch)
## Investor / analyst / capital-markets day hits
```

Then hand the file to FULL CHECK and Five-new NBT. Do not rank before it exists.

## Hard rules

1. Standing order. Do not start at Reddit or Whale.
2. Skip blocked. Do not loop a paywall. Mark `SKIP` and continue.
3. Never store portal passwords. Never ask for a paste.
4. **Never Reddit alone TAKE.**
5. Whale n/a ≠ skip. Run `whale_check.py`.
6. Pack commands under `agents/ssr-st/commands/` stay the repo playbook. Do not delete them.
