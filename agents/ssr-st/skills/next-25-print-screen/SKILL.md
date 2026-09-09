---
name: next-25-print-screen
description: >-
  Screens the next category print that looks like a SNOW-style ≥20–25% post-print
  analog: last realized move ≥+20% or last-7 avg ≥1.5× current EM, cheap EM vs
  that analog, beat streak or IBD 50, defined-risk 1× OTM 10-wide. One primary
  fill plus a mandatory second-name written ticket. Never chase a name already
  ≥+7% AH. Use after a missed monster print, "next similar stock", SNOW +25%,
  or when ranking remaining T7/T1 names for a 25% capture.
---

# Next 25% print screen

Find the **next** name that can still do a SNOW-class gap. Do not buy the gap
that already printed.

Template (2026-09-02): SNOW 6-for-6, last print **+36%**, EM **±12.7%**, monster
band written at 10%, HPE-only last-90, AH **+22.1%**. Next screen ≠ chase SNOW.

## Who (all required)

| Filter | Need |
|---|---|
| Clock | Category print inside **2–10 sessions** (PPS-T7 / T1) |
| Analog | Last-4 **or** last print realized **≥+20%**, **or** last-7 avg **≥ 1.5×** current ATM EM |
| Cheap EM | Current ATM EM **<** that realized move |
| Quality | Beat streak **5-for-5 / 6-for-6** **or** IBD 50 / SelfIDB50 |
| Anti-chase | Never chase a name already **≥+7% AH** |

Same-category bonus (AI/data) is a rank tilt, not a hard fail. Travel/cyber can
pass analog without being Snowflake.

## Structure

- Defined-risk **1× OTM 10-wide**, cap **$3–$4** (tighter if the card says so).
- Clock: **last-90 T−0** if EM% **≥15%** (`pps-t1-em-recalibrate` TAKE), **or**
  **ARM ticket** if analog **≥1.5× EM** even when EM **<15%** (`print-analog-vs-em`).
- Liquidity: `option-chain-liquidity-gate`. Thin OI / natural over cap = reject.
- One **primary** fill + **mandatory second-name written ticket** (the SNOW miss).

Analog upgrades ARM + ticket. It does **not** auto-TAKE when EM <15%.

## After a miss tonight

1. Mark the printed name **STAND** if AH ≥+7% (`post-print-gap-capture`).
2. Run this screen on remaining prints **Thu → next 10 sessions**.
3. Rank 2–4 names: analog %, EM%, print date, TAKE/ARM, structure, clock.
4. Write `agents/ssr-st/workspace/Documents/next_25_print_YYYY-MM-DD.md`.
5. Put primary + second-name on `catalyst_cards.md`.

## Fail the run if

- A passing analog name has no written ticket.
- The printed ≥+7% AH name is still listed as a fill.
- Ranked table has no second-name row.

No **go**.
