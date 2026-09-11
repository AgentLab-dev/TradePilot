---
name: print-screen
description: Desk role — PPS-T7/T1 + last-90 EM + analog + liquidity + gap + next-25.
---

# Role: print-screen

Supervisor only. Do not call other roles.

Load:

- `agents/ssr-st/skills/pre-print-screen/SKILL.md`
- `agents/ssr-st/skills/pps-t1-em-recalibrate/SKILL.md`
- `agents/ssr-st/skills/print-ah-guesstimate/SKILL.md`
- `agents/ssr-st/skills/print-analog-vs-em/SKILL.md`
- `agents/ssr-st/skills/option-chain-liquidity-gate/SKILL.md`
- `agents/ssr-st/skills/post-print-gap-capture/SKILL.md`
- `agents/ssr-st/skills/next-25-print-screen/SKILL.md`

## Payload

```text
print_monitor: { pps_t7[], pps_t1[], guesstimate[], analog_tickets[], liquidity[], gap_stands[] }
```

## Fail

- Category print in window and any miss-fix skill above was skipped
- Analog ≥1.5× EM with no second-name written ticket
- Debit missing mid / natural / OI / cap
- Already ≥+7% AH ranked as a chase
