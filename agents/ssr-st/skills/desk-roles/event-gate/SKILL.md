---
name: event-gate
description: Desk role — NEWS + 4Q + 10w + AH veto. EVENT-GATE TEST line per name.
---

# Role: event-gate

Supervisor only. Do not call other roles.

Load: `docs/grokbot-desk/skills/event-gate-test/SKILL.md`

Needs state: `flags_table`, `access_line`.

## Payload

```text
event_gates: [{ ticker, news, q4, ten_w, ah, verdict: STAND|ARM|RE-ARM T+1 }]
```

## Fail

- Named T+0/T+1 or elevated-IV name has no `EVENT-GATE TEST` line
- Credit routed through an untested print
- AH ≤ −5% and first-30 still armed
