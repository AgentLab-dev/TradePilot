---
name: event-gate-test
description: >-
  Event gate test for TradePilot print picks: NEWS + last-four-quarters + 10-week
  structure, plus the live AH ≤ −5% first-30 veto (STAND / skip first-30; re-arm
  only on T+1 reclaim + go). Complements Soft-EM AH ≥ +5% arm. High IV is not
  permission to sell credit into an untested print. Use on FULL CHECK, Five-new
  NBT, evening wrap, daily-desk-lessons, or any earnings / investor-day name.
  Always output an EVENT-GATE TEST line.
---

# Event gate test

The #1 edge is not selling premium through an untested print. This skill is the test
you run **before** a name stays on the board as a take or first-30 arm.

Standing rules: [`../../STANDING_RULES.md`](../../STANDING_RULES.md).
Complement: Soft-EM AH ≥ +5% **arms** a defined-risk debit — it does not sell credit.
Overnight cards: pack `catalyst-overnight-plan` (structure still required; this skill
is the gate, not the card).

## When (mandatory)

- Every print name on FULL CHECK, Five-new NBT, evening wrap, or daily-desk-lessons
- Earnings BMO/AMC, investor / analyst / capital-markets day
- CPI / PPI / PCE / FOMC / Warsh in the window
- Leftover short premium into a print (close T−1 — not optional)
- User says event gate / "can we sell this into the number"

Do not wait to be asked. If you listed the event, you owe an `EVENT-GATE TEST` line.

## The test (NEWS + 4Q + 10w)

1. **NEWS** — Is there earnings, CPI/PPI/PCE/FOMC, or an investor / analyst /
   capital-markets day in the expiry / first-30 window? Cite source + date.
2. **4Q** — Last four quarters: did the print pay the long, or was it beat-and-dump?
   **Beat ≠ green.** A beat that gaps down is a dump until the tape proves otherwise.
3. **10w** — Is 10-week weekly support / structure still intact? A broken 10w is not
   a put-credit floor into the print.

Then apply the **live AH** overlays:

| AH vs prior close | Action |
|---|---|
| **AH ≤ −5%** | **STAND / skip first-30.** Veto the open ticket. Do not buy the dump because it "beat." Re-arm only on **T+1 reclaim + go**. |
| **AH ≥ +5%** | **Soft-EM arm** a defined-risk debit for first 15–30. Still wait for **go**. Not a credit. |
| AH between −5% and +5% | NEWS + 4Q + 10w decide STAND vs ARM. Still no credit into an untested print. |

**High IV ≠ credit into print.** Rich IV is why the gate exists (AVGO lesson). Credit
is allowed only after the print is tested (range holds) or the name is not an event.

## Verdicts

| Verdict | Meaning |
|---|---|
| `STAND` | Skip first-30. No new credit. Card may still show the structure you *would* have used. |
| `ARM` | Defined-risk debit (or explicit close of leftover short premium). Wait for **go** before 9:30 ET. |
| `RE-ARM T+1` | Prior first-30 was vetoed (AH ≤ −5% or missed go). Re-arm only if the name **reclaims** the post-print range **and** the user says **go**. |

## Required output line

Every tested name prints exactly one line:

```
EVENT-GATE TEST <TICKER>: NEWS=<event+when> | 4Q=<pay|dump|mixed> | 10w=<hold|broke> | AH=<pct or n/a> | VERDICT=STAND|ARM|RE-ARM T+1
```

Examples:

```
EVENT-GATE TEST INTU: NEWS=AMC FY+guide | 4Q=dump | 10w=broke | AH=-10% | VERDICT=STAND
EVENT-GATE TEST NVDA: NEWS=AMC beat | 4Q=pay | 10w=hold | AH=+4.4% | VERDICT=ARM
EVENT-GATE TEST WMT: NEWS=printed T-1 dump | 4Q=dump | 10w=broke | AH=RTH held dump | VERDICT=RE-ARM T+1
```

Fail the parent run if a named print has no `EVENT-GATE TEST` line.

## Hard rules

1. **No credit into an untested print.** High IV is not an exception.
2. **AH ≤ −5% vetoes first-30.** STAND / skip. Re-arm only T+1 reclaim + go.
3. **AH ≥ +5% is Soft-EM arm**, not an order and not a credit.
4. **Beat ≠ green.**
5. Leftover short premium into the print: **close T−1**.
6. This skill does not place. Wait for **go**.
7. CREDITS rates sleeve uses its own calendar. Do not import equity first-30 exceptions into CREDITS.
