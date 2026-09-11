# Command: Health Check

Trigger: `Health Check` (optionally with tickers).

4-model composite: STKK + STNOW + Three Good + Whale → one VERDICT per name.

```
python3 agents/ssr-st/workspace/Documents/market_data/health_check.py TICKER [TICKER ...] [--to YYYY-MM-DD] [--live SYM=PX]
```

Skill: `agents/ssr-st/skills/health-check/SKILL.md`
If a 0d AMC/BMO is live and this run is a daily publish, also emit `print-readthrough-t1` (TICKET or SKIP per mapped peer).
Spec: `agents/ssr-st/workspace/Documents/health_check_algorithm.md`
