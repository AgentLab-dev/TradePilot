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
| [`skills/daily-desk-lessons/`](skills/daily-desk-lessons/SKILL.md) | Harvest lessons, ≥1 new-feature row, gate print picks, print-readthrough T+1, Sheet, next-best, deliver |
| [`skills/daily-new-feature/`](skills/daily-new-feature/SKILL.md) | ≥1 row/day on Sheet tab `new-feature` (`date \| new-feature \| strategy \| lesson`) |
| [`skills/desk-sources-capture/`](skills/desk-sources-capture/SKILL.md) | IBD → WSJ → MW → Whale → Reddit SOCIAL-ONLY; access line; never Reddit-alone TAKE |
| [`skills/evening-wrap/`](skills/evening-wrap/SKILL.md) | Post-close wrap; event-gate T+1 prints; print-readthrough-t1 peer table; Sheet if book changed; deliver |
| [`skills/print-readthrough-t1/`](skills/print-readthrough-t1/SKILL.md) | After 0d AMC/BMO, if-then first-30 on unripped sleeve peers (ORCL→HPE miss) |
| [`skills/event-gate-test/`](skills/event-gate-test/SKILL.md) | NEWS+4Q+10w; AH≤−5% first-30 veto; Soft-EM complement; `EVENT-GATE TEST` line |
| [`skills/five-new-nbt/`](skills/five-new-nbt/SKILL.md) | 5 NEW all-four + EM>15%; print-readthrough T+1; sources; gate; miss-catch; Sheet; wait for go |
| [`skills/full-check/`](skills/full-check/SKILL.md) | 12-step FULL CHECK / Health Check battery; sources first; NBT + print-readthrough; Sheet; deliver |
| [`skills/imessage-desk-post/`](skills/imessage-desk-post/SKILL.md) | Short iMessage to most recent sender; GChat TradePilot fallback as `hr@solutionlabs.ai` |
| [`skills/miss-catch-sleeves/`](skills/miss-catch-sleeves/SKILL.md) | Sleeves A Soft-EM 10–15% / B T+1 clock / C MANAGE flatten / D known-catalyst |
| [`skills/rank-next-best/`](skills/rank-next-best/SKILL.md) | Rank take/arm/stand-down; gate first; EM; Three Good ≠ call-debit veto; one-name; go |
| [`skills/reconnect-dow-jones-desk-portals/`](skills/reconnect-dow-jones-desk-portals/SKILL.md) | Box Chrome Dow Jones SSO (`hr@solutionlabs.ai`); never store passwords; then recapture |
| [`skills/sheet-latest-update/`](skills/sheet-latest-update/SKILL.md) | Tab `TradePilot-26Q3` full columns; flip Y→N; sort Y on top; why comments; no skeletons |

## Delivery

Grok Bot chat + iMessage (recent sender) + Google Chat TradePilot fallback.
Tickets are read-only until the user says **go**.
