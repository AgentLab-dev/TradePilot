---
name: flags
description: Desk role — FLAGS 4-model (STKK + STNOW + Three Good + Whale).
---

# Role: flags

Supervisor only. Do not call other roles.

This **is** graph `FLAGS`. STKK / STNOW / Three Good / Whale are tools here, not DAG roles.

Load: `agents/ssr-st/skills/health-check/SKILL.md`  
Command: `agents/ssr-st/commands/HEALTHCHECK.md`

```
python3 agents/ssr-st/workspace/Documents/market_data/health_check.py TICKER [...]
python3 agents/ssr-st/workspace/Documents/market_data/whale_check.py
```

`daily.py` whale n/a is a cache miss — run `whale_check.py`.

## Payload

```text
flags_table: [{ ticker, stkk, stnow, three_good, whale, verdict }]
```

## Fail

- Candidate / NBT / book row omits STKK · STNOW · 3Good · Whale
- 3Good used to veto a call debit
- STKK/STNOW ⚪ stale-cache treated as a pass
