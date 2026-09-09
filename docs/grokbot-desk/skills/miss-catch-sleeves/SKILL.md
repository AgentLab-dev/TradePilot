---
name: miss-catch-sleeves
description: >-
  Classify TradePilot miss-catch names into sleeves A Soft-EM 10–15%, B hard T+1
  clock, C MANAGE breakout flatten, D known-catalyst. Use on FULL CHECK, Five-new
  NBT, evening wrap, or when Reddit / ApeWisdom / a peer rip flags a name that is
  not a hard NBT. Always event-gate before any credit into a print. Do not pad
  the hard five with EM ≤ 15%. Reddit never alone TAKE.
---

# Miss-catch sleeves

The hard five is NEW + all-four + EM > 15%. Everything else that still deserves a
clock or a veto sits in a **sleeve**. Sleeves catch misses. They do **not** fill
hard NBT slots.

Standing rules: [`../../STANDING_RULES.md`](../../STANDING_RULES.md).
Companions: [`../five-new-nbt/SKILL.md`](../five-new-nbt/SKILL.md),
[`../event-gate-test/SKILL.md`](../event-gate-test/SKILL.md),
[`../desk-sources-capture/SKILL.md`](../desk-sources-capture/SKILL.md).

## When

- Every FULL CHECK and Five-new NBT (after the hard five is set)
- Evening wrap when AH creates a Soft-EM or dump
- Reddit / ApeWisdom / Swaggy cluster (miss-catch D only)
- Bellwether ≥ 5% or mapped peer ≥ 7% with no hard-NBT slot

## Sleeves

### A — Soft-EM 10–15%

Names with **EM 10–15%** (not hard NBT) and a live AH move.

| AH vs prior close | Action |
|---|---|
| **AH ≥ +5%** | **Arm T+1 first-30** defined-risk debit. Soft-EM. Wait for **go**. |
| **AH ≤ −5%** | **STAND / skip first-30.** Beat ≠ green. Re-arm only T+1 reclaim + go. |

Do **not** promote a sleeve-A name into the hard five to "make five." EM ≤ 15%
stays sleeve A.

### B — Hard T+1 clock

A real T+1 event (earnings BMO/AMC, investor / analyst / capital-markets day)
with a **hard clock** (first 15–30) and a written structure, but the name fails
hard NBT (missing a model, EM ≤ 15%, or not NEW). Card required. Event gate
required. This is the XE / SNDK overnight-card sleeve — not "ignore the name."

### C — MANAGE breakout flatten

Open-book or already-extended names: breakout that must **flatten same session**
(50% of debit / first-30 fail / VWAP fade). No add. No new credit. Manage or
kill. Used when the miss would be holding a catalyst debit overnight (SNDK T+1
giveback).

### D — Known-catalyst

Social or peer-radar names with a **known** catalyst already on the calendar
(print, investor day, mapped sympathy). Source may be Reddit / ApeWisdom /
Swaggy / WSJ. **Never Reddit alone TAKE.** D is a nomination for
`event-gate-test` + all-four. If it fails, it stays D. If it passes hard NBT,
it **leaves** the sleeve and enters the five as NEW.

## Event gate before credit

**Always** run `event-gate-test` before any credit into a print, including sleeve
names. High IV ≠ permission. NEWS + 4Q + 10w + AH ≤ −5% veto. No credit into an
untested print.

## Do not pad the hard five

| Allowed in hard five | Not allowed |
|---|---|
| NEW + all-four + EM > 15% | EM ≤ 15% (that is sleeve A) |
| Whale ≥ 0 | Reddit-only heat |
| Event-gate ARM / clean | Event-gate STAND |

If you only have three hard names, publish **three**. Empty slots stay empty.
Padding with sleeve A/B/C/D is a miss.

## Output

```markdown
## Miss-catch sleeves
| Sleeve | Ticker | Why | Gate | Clock | Structure (if any) |
| A Soft-EM 10–15% | | AH +x% / −x% | ARM first-30 / STAND | T+1 9:30–10:00 ET | debit cap |
| B hard T+1 clock | | event | EVENT-GATE TEST | first-30 | card |
| C MANAGE flatten | | breakout / open book | no add | same session | flatten |
| D known-catalyst | | source | not TAKE | — | test later |
```

## Hard rules

1. **Don't pad hard five with EM ≤ 15%.**
2. **Always event-gate before credit into a print.**
3. **Reddit never alone TAKE.** D is social color + known catalyst, not a ticket.
4. Sleeve A AH ≥ +5% is an **arm**, not an order. AH ≤ −5% is **STAND**.
5. Sleeve C flattens. It does not rotate into a new credit the same session.
6. Wait for **go** on any sleeve that still has a structure.
