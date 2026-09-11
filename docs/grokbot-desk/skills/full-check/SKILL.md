---
name: full-check
description: >-
  FULL CHECK / Health Check 12-step battery for the Grok Bot TradePilot desk.
  Desk sources first (IBD → WSJ → MW → Whale → Reddit SOCIAL-ONLY), event-gate
  every T+0/T+1 or elevated-IV name, then Five-new NBT + miss-catch, Sheet latest
  full columns, delivery Grok Bot + Google Chat + iMessage. Use on the 7am
  automation, FULL CHECK / fullcheck, or Health Check as the battery. Read-only
  until go. CREDITS is the rates sleeve. Reddit never alone TAKE.
---

# FULL CHECK

The everything-command. Same engine as the 7:00 AM PT automation. **Desk sources
first.** Rank last. Surface tickets. Do **not** place. Wait for **go**.

Standing rules: [`../../STANDING_RULES.md`](../../STANDING_RULES.md).
Pipeline: [`../../NEWS_DAY_PIPELINE.md`](../../NEWS_DAY_PIPELINE.md).
Source map: [`../../WHERE_LATEST_INFO_LIVES.md`](../../WHERE_LATEST_INFO_LIVES.md).
Must load: [`../desk-sources-capture/SKILL.md`](../desk-sources-capture/SKILL.md),
[`../event-gate-test/SKILL.md`](../event-gate-test/SKILL.md),
[`../five-new-nbt/SKILL.md`](../five-new-nbt/SKILL.md),
[`../miss-catch-sleeves/SKILL.md`](../miss-catch-sleeves/SKILL.md),
[`../rank-next-best/SKILL.md`](../rank-next-best/SKILL.md),
[`../sheet-latest-update/SKILL.md`](../sheet-latest-update/SKILL.md),
[`../imessage-desk-post/SKILL.md`](../imessage-desk-post/SKILL.md),
[`../print-readthrough-t1/SKILL.md`](../print-readthrough-t1/SKILL.md),
[`../business-tape-interpret/SKILL.md`](../business-tape-interpret/SKILL.md),
[`../desk-supervisor/SKILL.md`](../desk-supervisor/SKILL.md),
[`../desk-tester/SKILL.md`](../desk-tester/SKILL.md).
Pack command (unchanged): `agents/ssr-st/commands/FULLCHECK.md`.
Machine order: graph `FULLCHECK` in `agents/ssr-st/orchestrate/desk.dag.yaml`. Health Check standalone is graph `FLAGS`, not this battery.

## When

- 7:00 AM PT FULL CHECK automation
- User says FULL CHECK / fullcheck / full check / Health Check (as the battery)
- After reconnect-dow-jones-desk-portals restores IBD/WSJ/MW

Health Check standalone (4-model only) stays the pack skill. On this desk, **Health
Check inside FULL CHECK** means the 12-step battery, not a mute 4-flag dump.

## 12-step battery (in order)

1. **Desk sources first** — Load `desk-sources-capture`. Standing order:
   IBD lists → WSJ → MarketWatch → Barron's → Yahoo `https://finance.yahoo.com/` → `whale_check.py` → Reddit SOCIAL-ONLY
   (plus ApeWisdom/Swaggy). Write `/workspace/desk_sources_YYYY-MM-DD.md`.
   Print the access line. **Do not rank without it.** If WSJ/MW/IBD are signed
   out, load `reconnect-dow-jones-desk-portals`, then recapture.
2. **Tape / macro** — SPY · QQQ · SMH · VXX · 10Y. Regime read.
3. **Cross-sector GICS gate** — all 11, no tech-first bias.
4. **Book health** — cushion %, short-leg delta, GTC, abort. CREDITS rates sleeve
   reported separately — do not mix into equity NBT slots.
5. **Health Check 4-model** — STKK + STNOW + Three Good + Whale on book + candidates.
   `daily.py` whale n/a is a cache miss: run `whale_check.py`.
6. **Event gate test** — Load `event-gate-test` on **every T+0 / T+1 print and every
   elevated-IV name**. NEWS + 4Q + 10w + live AH ≤ −5% first-30 veto. High IV ≠
   credit into an untested print. Fail the run if a named event has no
   `EVENT-GATE TEST` line **and** no catalyst card (structure + first-30 + same-day
   exit). "No credit sell" is not a card.
7. **STKK + STNOW + Three Good** on finalists. Three Good = put-credit eligibility
   only — it does **not** veto a call debit.
8. **Whale Watch** — vol vs OI. Gate Whale ≥ 0 for hard NBT. Live-catalyst flow is
   stale at the open — read tape.
9. **Five new NBT + miss-catch** — Load `five-new-nbt` and `miss-catch-sleeves`.
   Hard five = NEW + all-four + EM > 15%. Do not pad with EM ≤ 15%. Reddit /
   ApeWisdom = **miss-catch D only**. **Never Reddit alone TAKE.**
   Load `print-readthrough-t1`. Fail the publish if a 0d AMC/BMO has no mapped-peer
   table (ORCL 9/10 → no HPE/DELL).
   Load `business-tape-interpret`. Fail if capture ran and `## Business tape` is
   missing. Reddit nominates; never Reddit-alone TAKE.
10. **Direction × IV route + rank** — Load `rank-next-best`. Event gate first, then
    Sheet plan, EM gates, STNOW green + whale ≥ 0, one-name rule, clocks.
11. **Sheet latest update** — Load `sheet-latest-update`. Tab `TradePilot-26Q3`
    only. **Full columns mandatory.** Flip prior `Y` → `N`. No skeleton rows.
12. **Output + deliver** — Ranked 🟢 take / 🟡 arm / 🔴 stand-down with structure
    and cap. Deliver Grok Bot chat + iMessage (recent sender) + Google Chat
    TradePilot fallback (`imessage-desk-post`). **Wait for go.**

Required extra query inside desk sources / news: `"investor day" OR "analyst day" OR "capital markets day"`
on book + SMH/memory/AI + READTHROUGH peers.

## Output (required block)

```markdown
# FULL CHECK — <weekday, date>  (<time> PT)

Access: IBD|WSJ|MW|Whale|Reddit|ApeWisdom OK/SKIP

## Tape / book
## EVENT-GATE TEST (every T+0/T+1 and elevated-IV name)
## Four-model table (STKK · STNOW · 3Good · Whale)
## Five new NBT (hard five — NEW · all-four · EM>15%)
## Business tape (required after capture)
## Print read-through T+1 (required if any 0d AMC/BMO)
## Miss-catch sleeves (A/B/C/D — not hard-five padding)
## Ranked plan
- 🟢 take / 🟡 arm / 🔴 stand-down + structure + cap + clock
## Sheet latest (full columns written)
## Wait for go
```

## Hard rules

1. **Desk sources first.** No access line → no rank.
2. **Event gate on every T+0/T+1 or elevated-IV name.** Beat ≠ green. AH ≤ −5%
   STAND / skip first-30; re-arm only T+1 reclaim + go.
3. **Reddit never alone TAKE.** Reddit is required **input** (nominated + what social is pricing). Fail if the scan ran and the Reddit line is missing.
4. **Sheet latest = full columns or do not write.**
5. **Wait for go.** Read-only tickets. No orders in the delivery.
6. **CREDITS = rates sleeve.** Separate from equity NBT. Do not bleed rules.
7. **Never force a trade.** A logged stand-down counts.
8. Do not delete `agents/ssr-st/commands/FULLCHECK.md` or the rest of that folder.
9. **Print read-through table on every daily publish** after a 0d AMC/BMO. Fail if missing.
10. **Business tape on every daily publish** after capture. Fail if missing.

## Delivery

Grok Bot chat + Google Chat TradePilot + iMessage (recent sender). If iMessage
fails, Google Chat is the fallback (`imessage-desk-post`). Same facts on all three.
Short iMessage copy; full table in Grok Bot / GChat.
