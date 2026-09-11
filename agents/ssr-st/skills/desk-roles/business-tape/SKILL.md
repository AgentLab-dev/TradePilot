---
name: business-tape
description: Desk role — APPLY capture into regime, payer vs paid, Reddit nominated.
---

# Role: business-tape

Supervisor only. Do not call other roles.

Load: `agents/ssr-st/skills/business-tape-interpret/SKILL.md`

Needs state: `access_line`.

## Payload

```text
business_tape: { regime, story, payer_vs_paid, sleeve, veto, reddit, nominated, is_vs_cfs }
```

## Fail

- Capture ran and `## Business tape` is missing
- 0d print with no IS vs CFS / payer-vs-paid
- Reddit scanned and Nominated line missing
- A 🟢 take that is Reddit-only

Never Reddit-alone TAKE.
