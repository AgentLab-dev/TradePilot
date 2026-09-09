---
name: daily-new-feature
description: >-
  Write at least one Daily new-feature row every trading day to Google Sheet
  TradePilot-26Q3 tab new-feature. Columns are date | new-feature | strategy |
  lesson. Use on the 10am / 8pm lesson automations, daily-desk-lessons, FULL
  CHECK, evening wrap, or when the user asks for new-feature / "what changed."
  No silent days. Not a ticket. Wait for go if the feature implies an order.
---

# Daily new feature

Every trading day the desk records **≥1** feature on the Sheet. This is the public
memory of what changed in process, tape, or book — not a blog, not optional.

Standing rules: [`../../STANDING_RULES.md`](../../STANDING_RULES.md).
Source map: [`../../WHERE_LATEST_INFO_LIVES.md`](../../WHERE_LATEST_INFO_LIVES.md).
Called by: [`../daily-desk-lessons/SKILL.md`](../daily-desk-lessons/SKILL.md).

## When

- Once per weekday (10:00 AM and/or 8:00 PM PT lesson pass)
- After a rule change, miss, first-30 veto, Soft-EM arm, or NBT rotation
- User says new-feature / "log today's feature"

If today's date already has a row, **append another** only when a second real feature
landed. Do not duplicate the morning row at 8 PM unless the lesson changed.

## Sheet

- Spreadsheet id: `1RkdF93AK7BWRf0SktGVrHehG0XU_nz21WCzSrAP68vQ`
- URL: https://docs.google.com/spreadsheets/d/1RkdF93AK7BWRf0SktGVrHehG0XU_nz21WCzSrAP68vQ/edit
- Tab: `new-feature`
- Columns (mandatory, in this order):

| Column | What goes in |
|---|---|
| `date` | Session date `YYYY-MM-DD` (America/Los_Angeles) |
| `new-feature` | The one durable change or observation (one line) |
| `strategy` | Which sleeve / structure it affects (equity NBT, first-30 debit, CREDITS, stand-down, Sheet process) |
| `lesson` | The rule in one sentence (what we will do differently, or what we confirmed) |

A row missing any of the four columns is a miss. Do not write a blank lesson.

## What counts as a feature

Good rows:

- AH ≤ −5% veto fired on TICKER — first-30 skipped; re-arm only T+1 reclaim + go
- Soft-EM AH ≥ +5% armed TICKER first-30 debit; wait for go
- Hard NBT replaced GLW with WPM/ANET (all-four + EM > 15%)
- Whale step cannot skip when `daily.py` prints n/a — run `whale_check.py`
- Stood down into untested print / Warsh / CPI

Not a feature:

- "Markets were mixed"
- A ticker mention with no rule
- A copy of the ranked plan without a lesson

If the only honest feature is a stand-down, write the stand-down.

## Steps

1. Read today's capture, cards, and latest Sheet row.
2. Pick **one** durable feature (process > P&L color).
3. Write the four columns to tab `new-feature`.
4. Confirm the row is visible on the tab (do not claim a write you did not verify).
5. Point to the row from daily-desk-lessons output.

## Hard rules

1. **≥1 row per trading day.** No silent days.
2. **Four columns or do not write.**
3. This tab is **not** the latest-book tab. Book writes still need the full
   `TradePilot-26Q3` column set (`is_latest=Y`, flags, EM, structure, clocks, comments).
4. **Not an order.** If the feature implies a ticket, surface it and wait for **go**.
5. CREDITS features stay labeled CREDITS. Do not bleed them into equity NBT.

## Delivery

Grok Bot chat + iMessage (recent sender) + Google Chat TradePilot fallback when this
skill runs standalone. When nested under daily-desk-lessons, one delivery covers both.
