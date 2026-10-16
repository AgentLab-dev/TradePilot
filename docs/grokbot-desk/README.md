# Grok Bot TradePilot desk

Mirror of the live Grok Bot TradePilot desk skills and standing rules (Sep 2026).
Documentation only. The live desk still runs from Grok Bot skill files, agent
memory, and Google Sheet **TradePilot-26Q3**.

This tree does **not** replace `agents/ssr-st/commands/`. Classic pack commands
stay where they are.

## Start here

| Doc | Role |
|---|---|
| [`WHERE_LATEST_INFO_LIVES.md`](WHERE_LATEST_INFO_LIVES.md) | Live Sheet, GitHub pack, Grok Bot runtime, NEWS access, delivery |
| [`STANDING_RULES.md`](STANDING_RULES.md) | Event gate, AH vetoes, Soft-EM, hard NBT, Sheet, go, CREDITS |
| [`NEWS_DAY_PIPELINE.md`](NEWS_DAY_PIPELINE.md) | Capture order, apply map, access line, `desk_sources_YYYY-MM-DD.md` |

## Skills

| Skill | Role |
|---|---|
| [`skills/daily-desk-lessons/`](skills/daily-desk-lessons/SKILL.md) | 20-session scorecard, calibration, N≥8 gate rule, then lessons, new-feature, gate, Sheet, next-best |
| [`skills/daily-new-feature/`](skills/daily-new-feature/SKILL.md) | ≥1 row/day on Sheet tab `new-feature`; a new veto needs N≥8 and retires a rule |
| [`skills/desk-sources-capture/`](skills/desk-sources-capture/SKILL.md) | IBD → WSJ → MW → Whale → Reddit SOCIAL-ONLY; access line; never Reddit-alone TAKE |
| [`skills/evening-wrap/`](skills/evening-wrap/SKILL.md) | Post-close wrap; REGIME vs morning; score ledger picks; event-gate; print-readthrough; Sheet if book changed |
| [`skills/print-readthrough-t1/`](skills/print-readthrough-t1/SKILL.md) | After 0d AMC/BMO, if-then first-30 on unripped sleeve peers (ORCL→HPE miss) |
| [`skills/business-tape-interpret/`](skills/business-tape-interpret/SKILL.md) | After capture, APPLY block: regime, payer vs paid, Reddit nominated (never alone TAKE) |
| [`skills/event-gate-test/`](skills/event-gate-test/SKILL.md) | NEWS+4Q+10w; AH≤−5% veto; EM vs realized; lean and P%; new veto only with N≥8 and a retirement |
| [`skills/five-new-nbt/`](skills/five-new-nbt/SKILL.md) | 5 NEW all-four + EM>15%; regime; checklist; top 3 paper picks; print-readthrough; Sheet; wait for go |
| [`skills/desk-supervisor/`](skills/desk-supervisor/SKILL.md) | FULLCHECK / FLAGS / NBT DAG; roles never call each other; wait for go |
| [`skills/desk-tester/`](skills/desk-tester/SKILL.md) | Backtest + strategy score 1–10 before publish; recross once; second fail publishes score for review |
| [`skills/full-check/`](skills/full-check/SKILL.md) | 12-step FULL CHECK; regime first; checklist; paper-pick ledger; graph FULLCHECK |
| [`skills/imessage-desk-post/`](skills/imessage-desk-post/SKILL.md) | Short iMessage to most recent sender; GChat TradePilot fallback as `hr@solutionlabs.ai` |
| [`skills/miss-catch-sleeves/`](skills/miss-catch-sleeves/SKILL.md) | Sleeves A/B/C/D; checklist and paper log on candidates; no new sub-rule without N≥8 |
| [`skills/rank-next-best/`](skills/rank-next-best/SKILL.md) | Gate first; incomplete ranks below STAND; EV per dollar, regime haircut, calibration shrink |
| [`skills/reconnect-dow-jones-desk-portals/`](skills/reconnect-dow-jones-desk-portals/SKILL.md) | Box Chrome Dow Jones SSO (`hr@solutionlabs.ai`); never store passwords; then recapture |
| [`skills/sheet-latest-update/`](skills/sheet-latest-update/SKILL.md) | Tab `TradePilot-26Q3` full columns; flip Y→N; if the cell-write is blocked, `y_rows` + ledger + `SHEET STALE` |

## Delivery

Grok Bot chat + iMessage (recent sender) + Google Chat TradePilot fallback.
Tickets are read-only until the user says **go**.
