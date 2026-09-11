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
ranked_plan: [{ verdict, ticker, structure, cap, clock, gate, why }]
```

## Fail

- Ranked row omits STKK · STNOW · 3Good · Whale
- `#1` is Reddit-only
- Credit through a print / CPI / PCE / FOMC
