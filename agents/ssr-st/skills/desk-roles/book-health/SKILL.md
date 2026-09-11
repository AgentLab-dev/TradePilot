---
name: book-health
description: Desk role — cushion, GTC, abort. CREDITS stays separate.
---

# Role: book-health

Supervisor only. Do not call other roles.

Robinhood MCP read-only. No orders.

## Payload

```text
book: { positions[], gtc, abort, credits_separate }
```

## Fail

- Open position missing GTC status and abort line
- Abort fired and the role says "watch" instead of same-session BTC
