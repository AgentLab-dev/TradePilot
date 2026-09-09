---
name: five-new-nbt
description: >-
  Build the Five-new NBT book: five NEW names that pass all-four models
  (STKK + STNOW + Three Good + Whale) and EM > 15%. Run desk-sources-capture
  first, event-gate every event name, apply Reddit only as miss-catch D, write
  Sheet latest with full columns, and wait for go. Use on FULL CHECK, 7am
  automation, NBT rotation, or when the user asks for next-best trades / five new.
---

# Five new NBT

Hard next-best-trade list. **Five NEW names.** Not a recycle of the open book. Not
a Reddit list. Not a "maybe later" watchlist.

Standing rules: [`../../STANDING_RULES.md`](../../STANDING_RULES.md).
Pipeline: [`../../NEWS_DAY_PIPELINE.md`](../../NEWS_DAY_PIPELINE.md).
Must load first: [`../desk-sources-capture/SKILL.md`](../desk-sources-capture/SKILL.md),
[`../event-gate-test/SKILL.md`](../event-gate-test/SKILL.md).

## When

- 7:00 AM PT FULL CHECK automation (after desk sources)
- User says Five new / NBT / next-best / "rotate the pair"
- After a hard NBT name dies (reclaim never held, print veto, clock gone)

## Qualification (all required for a hard NBT name)

A name is a **hard NBT** only if **all** of these hold:

1. **NEW** — not already the open book / last NBT pair unless it was explicitly killed
2. **All-four** — STKK + STNOW + Three Good + Whale shown as regular columns
3. **Whale ≥ 0** (from `whale_check.py`; `daily.py` n/a is not a pass)
4. **EM > 15%**
5. **Desk sources applied** — IBD feeds universe; WSJ/MW feed tape/vetoes
6. **Event names pass `event-gate-test`** — no credit into an untested print;
   AH ≤ −5% is STAND, not an NBT take

Missing any of the four models is **not** a hard NBT. Three Good is put-credit
eligibility only — it does **not** veto a call debit, but the column must still print.

Soft / secondary names (EM ≤ 15% or a missing model) can appear below the hard five
as 🟡 arm / 🔴 stand-down. They do not fill a hard slot.

## Miss-catch D

Reddit / ApeWisdom / Swaggy are **Miss-catch D only**. A social cluster can nominate
a name for the all-four + EM > 15% test. **Never Reddit alone TAKE.** If a social
name fails all-four or EM, log it as miss-catch D and move on.

## Steps

1. Run `desk-sources-capture`. Refuse to rank without today's
   `/workspace/desk_sources_YYYY-MM-DD.md` and access line.
2. Build the universe from **IBD** lists (50 / Sector Leaders / Big Cap / Spotlight).
3. Veto from **WSJ / MW** tape (regime, named dumps, macro prints).
4. Run all-four + EM on survivors. Keep Whale ≥ 0 and EM > 15%.
5. `EVENT-GATE TEST` every event name. STAND / skip first-30 if AH ≤ −5%.
6. Pick **five NEW** hard names. Different industries when the book is already stacked.
7. Write Sheet latest — **full columns mandatory** (`is_latest=Y`, flags, EM,
   structure, clocks, comments) on tab `TradePilot-26Q3`.
8. Deliver and **wait for go**.

## Output

```markdown
# Five new NBT — <weekday, date>

Access: IBD|WSJ|MW|Whale|Reddit|ApeWisdom OK/SKIP

## Hard five (NEW · all-four · EM>15%)
| # | Ticker | STKK | STNOW | 3Good | Whale | EM | Structure | Clock | Gate |
|---|---|---|---|---|---|---|---|---|---|

## EVENT-GATE TEST
- EVENT-GATE TEST <TICKER>: …

## Miss-catch D (Reddit / ApeWisdom — not TAKE)
## Sheet latest (full columns written)
## Wait for go
```

## Sheet

- Id: `1RkdF93AK7BWRf0SktGVrHehG0XU_nz21WCzSrAP68vQ`
- Main tab `TradePilot-26Q3` — latest NBT / book row, **full columns**
- Tab `new-feature` — if the rotation itself is today's feature, also write that row

Partial Sheet updates are a miss.

## Hard rules

1. **Five NEW.** All-four + EM > 15% or it is not hard NBT.
2. **Desk sources first.** No sources file → no list.
3. **Event gate on event names.** Beat ≠ green. No credit into untested print.
4. **Miss-catch D ≠ TAKE.**
5. **Sheet full columns mandatory.**
6. **Wait for go.** Read-only tickets.
7. Do not open NBT into a known macro print (Warsh / CPI / FOMC) as credit.
8. CREDITS rates sleeve is not an NBT slot.
9. Do not delete `agents/ssr-st/commands/*`.
