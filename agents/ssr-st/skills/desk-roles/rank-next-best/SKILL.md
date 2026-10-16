---
name: rank-next-best
description: Desk role — 🟢 take / 🟡 arm / 🔴 stand-down. Wait for go.
---

# Role: rank-next-best

Supervisor only. Do not call other roles.

Load: `docs/grokbot-desk/skills/rank-next-best/SKILL.md`

Needs state: `flags_table`, `event_gates`, `nbt_five`, `readthrough`, `book`.

If a ticket is live, status may be `needs_input` (wait for **go**). Do not place.

## Payload

```text
ranked_plan: [{ verdict, ticker, structure, cap, clock, gate, entry, stop, target, rr, size, p_pct, why }]
```

Incomplete cards rank below STAND. Complete cards rank by expected value per dollar risked, with the RISK-OFF bullish haircut and the lessons shrink factor. Event gate still kills a take first. Do not place orders.

## Fail

- Ranked row omits STKK · STNOW · 3Good · Whale
- `#1` is Reddit-only
- Credit through a print / CPI / PCE / FOMC

## Missing checklist levels

A TAKE / ARM missing entry, stop, target, R:R, size, or P% still delivers. Status stays `ok`. Print `MISSING-FIELDS: checklist levels`. Do not halt the graph. An incomplete card still ranks below STAND.
