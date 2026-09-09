---
name: post-print-gap-capture
description: >-
  After results: if AH is ≥+7% or ≤−7%, do not chase AH. Capture path is 50%
  flatten if already filled; if not filled, STAND AH. Next RTH first-30 only if
  a new hold holds 15–30 min vs gap VWAP / RTH open. Use on missed print, "it's
  up 25%", SNOW / MDB / HPE after AMC, or anti-chase after a gap.
---

# Post-print gap capture

Anti-chase **+7% / −7%** stands. A 25% AH gap is already past that line.

Logged miss (2026-09-02): SNOW AH **+22.1%** vs RTH **$306.19** (high **+24.3%**).
User: **do not chase Thursday.** Path is the **next** analog name
(`next-25-print-screen`), not a market order into this spike.

## After the print (AH)

| State | Path |
|---|---|
| Already filled last-90 | **50% flatten** if AH ≥+7% or ≤−7% (or ≥0.8× EM). Do not sleep the weekly. |
| **Not** filled | **STAND AH.** No AH debit. No AH credit. |
| AH inside ±7% | Manage per the overnight card. Still no unarmed chase. |

Do **not** chase AH. First-30 next RTH is a **new** hold vs **new** AH/RTH spot,
not a market order into the spike.

## Next RTH first-30 (only if the user still wants this name)

Default after a ≥+7% AH rip the user did **not** fill: **STAND** that name and
screen the **next** 25% analog. If the user explicitly arms this name anyway:

1. Wait 15–30 min.
2. New hold must hold vs **gap VWAP / RTH open**.
3. Structure: 1× OTM 10-wide vs **new** spot, cap **$3–$4**.
4. Abort fade of that hold.
5. Run `option-chain-liquidity-gate`. Fail = no fill.

If the hold never prints, kill. Do not buy 90 minutes in.

## Apply analog here

Use `print-analog-vs-em` to **find the next name**, not to buy this gap.

## Do not

- Fill AH into ≥+7% or ≤−7%.
- Treat “we missed the print” as permission to chase.
- Rewrite PPS-T1 15% TAKE into an after-print TAKE.

No **go** in this skill.
