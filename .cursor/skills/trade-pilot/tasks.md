# Trade Pilot tasks

Copy the matching checklist into the turn and tick it. Do not start a domain task on the other domain's checklist.

## Session start

```
- [ ] Identity: Trade Pilot (this repo). Not a second agent named ssr-st or arr-analyst.
- [ ] Route the first user turn to trading or ARR. If unclear, ask.
- [ ] Trading: wait for go. ARR: no self-signature; Snowflake reads only.
```

## Trading — first check of the day

```
- [ ] Read agents/ssr-st/workspace/Documents/agent_learning_log.md
- [ ] Read agents/ssr-st/workspace/Documents/catalyst_cards.md (confirm / fire / kill)
- [ ] Run python3 agents/ssr-st/workspace/Documents/market_data/daily.py (paths may still say ssr-analyst)
- [ ] Manage open book (stops, GTC, abort)
- [ ] Surface ≥1 vetted idea (strikes, size, stop) OR an explicit stand-down
- [ ] Wait for go before any order
```

## Trading — FULL CHECK

```
- [ ] Run the 12 steps in agents/ssr-st/commands/FULLCHECK.md
- [ ] Fail the run if any 0d/1d event has no catalyst card
- [ ] End with take / arm / stand-down, split options book vs Agentic sleeve
- [ ] Overwrite catalyst_cards.md, next_day_prep.md, momentum_watchlist.md
- [ ] Wait for go
```

## Trading — evening wrap

```
- [ ] After close. No orders.
- [ ] Catalyst cards + next_day_prep.md
```

## Sites — publish universe

```
- [ ] tradepilot sites-publish --html-only
- [ ] If secrets/credentials.json exists: tradepilot sites-publish (--login if no token)
- [ ] Return HTML path + Google Doc link + any listed Sites
- [ ] Publishing is not go
```

## ARR — FQC-ARR ticket

```
- [ ] jira-intake
- [ ] requirements-analyzer
- [ ] code-data-validator
- [ ] clarifier (gate)
- [ ] implementer
- [ ] test-runner
- [ ] pr-author (gate)
- [ ] ci-monitor
- [ ] cd-monitor
- [ ] qa-handoff (gate)
- [ ] No agent signature on Jira / Slack / PR
- [ ] No unattended prod dbt
```

Packed automation drafts (finalize in the Agents Window, not from this skill): `agents/arr-analyst/workspace-automations/`.
