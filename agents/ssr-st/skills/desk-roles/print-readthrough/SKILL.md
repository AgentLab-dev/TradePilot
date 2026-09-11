---
name: print-readthrough
description: Desk role — 0d AMC/BMO mapped-peer if-then for next RTH first-30.
---

# Role: print-readthrough

Supervisor only. Do not call other roles.

Load: `agents/ssr-st/skills/print-readthrough-t1/SKILL.md`

Needs state: `business_tape`, `event_gates`.

On graph `NBT`, run this role only when a 0d AMC/BMO is live. Otherwise `skipped`.

## Payload

```text
readthrough: [{ printer, result_ah, peer, peer_pct, verdict, structure, clock }]
```

## Fail

- 0d AMC/BMO with no mapped-peer table (SKIP rows count; silence does not)
- Armed a peer already ≥ +7%
