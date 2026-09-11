---
name: evening-wrap
description: >-
  Post-close TradePilot evening wrap. Sweep close + AH, run desk-sources-capture,
  event-gate every T+1 print, write catalyst cards / next-day prep, and update
  Sheet latest only if the book changed (full columns). No orders. Deliver Grok
  Bot chat + iMessage (recent sender) + Google Chat TradePilot fallback. Use at
  ~6 PM PT, on "evening wrap", EOD, or "prepare for next day."
---

# Evening wrap

Post-close counterpart to the 7 AM FULL CHECK. Close today's loop and stage tomorrow.
The market is closed: **no orders**. Analysis + cards + Sheet only.

Standing rules: [`../../STANDING_RULES.md`](../../STANDING_RULES.md).
Pipeline: [`../../NEWS_DAY_PIPELINE.md`](../../NEWS_DAY_PIPELINE.md).
Companions: [`../desk-sources-capture/SKILL.md`](../desk-sources-capture/SKILL.md),
[`../event-gate-test/SKILL.md`](../event-gate-test/SKILL.md).
Pack skill (classic): `agents/ssr-st/skills/evening-wrap-nextday-prep/SKILL.md`.

## When

Once per weekday after US after-hours, default **6:00 PM PT**. Skip weekends/holidays
unless an AMC print just landed. User triggers: evening wrap / EOD / prepare for next day.

## Sweep (in order)

1. **Close + AH tape** — book + SPY/QQQ/SMH/VXX/10Y + notable AH movers. State % vs prior close.
2. **Desk sources capture** — IBD → WSJ → MW → `whale_check.py` → Reddit SOCIAL-ONLY.
   Write `desk_sources_YYYY-MM-DD.md`. Print the access line.
3. **Event gate on T+1 prints** — Load `event-gate-test` for every T+1 earnings,
   investor / analyst / capital-markets day, and mapped peer. NEWS + 4Q + 10w.
   AH ≤ −5% → STAND / skip first-30; re-arm only T+1 reclaim + go.
   AH ≥ +5% → Soft-EM **arm** (still wait for go). High IV ≠ credit into print.
   Output an `EVENT-GATE TEST` line per name.
4. **Catalyst cards** — One take / arm / stand-down card **with structure, first-30
   trigger, same-day exit** per T+1 event. "No credit sell" is not a card. Fail the
   wrap if a named T+1 event has no card.
   **Print read-through** — Load `print-readthrough-t1`. Every 0d AMC/BMO gets a
   mapped-peer if-then table for next RTH first-30. Fail the wrap if the table is
   missing (ORCL 9/10 18:30 write had no HPE/DELL). Best unripped peer may be iMessage `#1`.
5. **Sheet latest** — Write tab `TradePilot-26Q3` **only if the book changed**. If you
   write, fill the **full** column set (`is_latest=Y`, flags, EM, structure, clocks,
   comments). Also write `new-feature` if a lesson landed (`daily-new-feature`).
6. **Next-day prep** — Regime, book status, tomorrow's #1 focus, levels, offense + defense.
7. **Deliver** — Grok Bot chat + iMessage (recent sender) + Google Chat TradePilot fallback.

## Output

```markdown
# Evening wrap — <weekday, date>  (<time> PT)

## TL;DR
- Regime / book / tomorrow's #1

## Close + AH
## Desk sources
Access: IBD|WSJ|MW|Whale|Reddit|ApeWisdom OK/SKIP

## EVENT-GATE TEST (every T+1 print)
- EVENT-GATE TEST <TICKER>: NEWS=… | 4Q=… | 10w=… | AH=… | VERDICT=…

## Catalyst cards (structure + first-30 + same-day exit)
## Print read-through T+1 (required after any 0d AMC/BMO)
## Sheet latest (written | skipped — no book change)
## Next-day prep
```

Also overwrite pack files when this checkout is the runtime: `catalyst_cards.md`,
`next_day_prep.md`. On the Grok Bot box, keep `/workspace/desk_sources_YYYY-MM-DD.md`.

## Hard rules

1. **No orders.** Wait for **go** tomorrow, before 9:30 ET on first-30 cards.
2. **Event gate every T+1 print.** Beat ≠ green. No credit into an untested print.
3. **Sheet only if the book changed**, and then **full columns**.
4. **Offense and defense.** What breaks the book, and what Soft-EM / washout is armed.
5. CREDITS rates sleeve stays separate.
6. Do not delete `agents/ssr-st/commands/EVENING_WRAP.md`.
7. **Print read-through table required** after any 0d AMC/BMO. Fail the wrap if it is missing.
