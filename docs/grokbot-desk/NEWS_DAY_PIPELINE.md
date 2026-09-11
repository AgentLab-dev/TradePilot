# News-day pipeline

Standing capture order for every FULL CHECK and Five-new NBT. Do not skip a source silently — mark `OK` or `SKIP` on the access line.

## Capture order (required)

1. **IBD** — research.investors.com SSO (Stock Lists / IBD 50 / leaders). Do not ask the user to paste.
2. **WSJ** — homepage + headlines (login if Sign In).
3. **MarketWatch** — tape / headline / catalyst read.
4. **WhaleWatch** — `whale_check.py` on candidates + book names.
5. **Reddit SOCIAL-ONLY** — `r/algotrading`, `r/Quant`, `r/stocks`, `r/investing`, `r/StockMarket`, `r/wallstreetbets`, `r/options`, `r/semiconductors`; optional `r/spacs`, `r/pennystocks`; plus ApeWisdom / Swaggy.
6. **Optional** — Benzinga / Barron's / FedWatch when the tape or calendar needs it.

## How each source is applied

| Source | Apply to |
|---|---|
| IBD | NBT universe |
| WSJ / MarketWatch | Tape + vetoes |
| Whale | Gate: Whale ≥ 0 |
| Reddit | Miss-catch D only (social color, not a ticket source) |

Optional Benzinga / Barron's / FedWatch feed the same tape/veto layer as WSJ/MW when used.

## Access line (required on every run)

```
IBD|WSJ|MW|Whale|Reddit|ApeWisdom OK/SKIP
```

Example: `IBD OK | WSJ OK | MW OK | Whale OK | Reddit SKIP | ApeWisdom OK`

A skipped source must say why (SSO, outage, no MCP, blocked). Do not invent a fill from RSS when the live portal failed unless the access line says `SKIP`.

## Output then apply

1. Write `/workspace/desk_sources_YYYY-MM-DD.md` (or overwrite today's file).
2. Run **FULL CHECK** + **Five new NBT** against that capture.
3. After any 0d AMC/BMO, emit `print-readthrough-t1` on that publish. Fail if the mapped-peer table is missing.
4. Pack playbook remains `agents/ssr-st/commands/NEWS.md` + `IBDWSJCAPTURE.md` + `NBT.md` + `PRINT_READTHROUGH.md`.

## Delivery

Grok Bot chat + Google Chat TradePilot + iMessage (recent sender).
