---
name: five-new-nbt
description: Desk role — five NEW hard names (all-four + EM > 15%) + miss-catch D.
---

# Role: five-new-nbt

Supervisor only. Do not call other roles.

Load: `docs/grokbot-desk/skills/five-new-nbt/SKILL.md` · `docs/grokbot-desk/skills/miss-catch-sleeves/SKILL.md`

Needs state: `access_line`, `business_tape`, `flags_table`, `event_gates`.

## Payload

```text
nbt_five: [{ ticker, stkk, stnow, three_good, whale, em, structure, clock, gate }]
miss_catch: { A[], B[], C[], D[] }
regime: REGIME block
paper_picks: [{ ticker, direction, entry, stop, target, horizon_sessions, p_pct, thesis }]
```

Hard five stays EM > 15% + all-four. Log `paper_picks` (top 3, including STAND names) on every run. Append them with `tradepilot.desk_process.log_run`. Do not place orders.

## Fail

- Hard slot filled with EM ≤ 15%
- Hard slot missing a model
- Reddit-alone TAKE
- Mix: all five are prints + book manage (FULLCHECK graph)
- Recycled leftover five with no live unique-sleeve win
- No REGIME verdict
- No paper picks and no explicit shortfall when every card failed the checklist
