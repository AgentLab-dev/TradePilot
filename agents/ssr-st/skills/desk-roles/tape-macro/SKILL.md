---
name: tape-macro
description: Desk role — SPY/QQQ/SMH/VXX/10Y + MANGOS + GICS/sleeves.
---

# Role: tape-macro

Supervisor only. Do not call other roles.

Load: `agents/ssr-st/skills/trading-continuous-learning/SKILL.md` (steps 1–2)

## Payload

```text
tape_macro: { spy, qqq, smh, vxx, ten_year, mangos, gics, sleeves: [GDX, IGV, SMH, XOP, KRE], regime: "REGIME | trend … | VIX … | 10Y … | breadth … | leaders … | verdict" }
```

`regime` is the step-0 block: trend vs 20d/50d, VIX band, 10Y, RSP vs SPY, leader/laggard, verdict RISK-ON / NEUTRAL / RISK-OFF. Use `tradepilot.desk_process.read_regime` on the quotes this role already pulled. Do not place orders.

## Fail

- MANGOS omitted or n/a with no live-quote fallback
- Only the 11 GICS ETFs ranked (need GDX · IGV · SMH · XOP · KRE)
- FULLCHECK publish with no `regime` verdict
