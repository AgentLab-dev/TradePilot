---
name: list-to-ticket
description: Desk role — every IBD/T7/ALWAYS listed name gets TICKET or SKIP.
---

# Role: list-to-ticket

Supervisor only. Do not call other roles.

Load: `agents/ssr-st/skills/list-to-ticket/SKILL.md`

Needs state: `access_line`, `business_tape`.

## Payload

```text
list_tickets: [{ ticker, list, verdict: TICKET|SKIP|HOLE, gate }]
```

## Fail

- Listed name left as board / watching only
- Mapped 0d-print peer with neither TICKET nor SKIP
