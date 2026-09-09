---
name: print-analog-vs-em
description: >-
  When last-4 or last-7 realized post-print move is at least 1.5× current ATM
  EM, treat EM under 15% as ARM with a written ticket, not STAND-and-forget.
  Monster band in guesstimate cannot be under 20% if last print was ≥+20% and
  this print is still in the same category (AI/data). Does not override a user
  one-T1-name rule — it forces a second-name card. Use on last-90, guesstimate,
  PPS-T1 ARM, SNOW/HPE/MDB-style analog, or when EM looks cheap versus history.
---

# Print analog vs EM

PPS-T1 TAKE stays **EM% ≥15%** (`pps-t1-em-recalibrate`). This skill does **not**
delete that gate. Analog upgrades **ARM + a written ticket**, not automatic TAKE.

Logged miss (2026-09-02): SNOW last print **+36%**, 6-for-6, Sep 4 EM **±12.7%**.
Guesstimate put monster at **10%**. User kept **HPE-only** last-90. No second-name
card. AH then **+22.1%** (~1.7× EM). Do not chase that gap.

## Inputs

| Input | Source |
|---|---|
| Current EM% | ATM straddle / spot on the expiry you would buy |
| Last print realized | Next RTH close vs print-day RTH close (AH open if RTH not in yet) |
| Last-4 / last-7 | Same, average of |move| and count of higher closes |
| Category | AI/data/software still in the same bucket as the analog |

## Gate

When **last-4 or last-7 realized post-print move ≥ 1.5× current ATM EM**:

- EM **<15%** → **🟡 ARM with a written ticket**. Not STAND-and-forget.
- EM **≥15%** → still the PPS-T1 TAKE path if beat/theme fire. Analog does not
  skip liquidity or **go**.

Ticket required: structure, cap, clock = **last-90 T−0** **or** **Thu first-30**
(next RTH). Size 1×. Defined-risk OTM 10-wide.

## Guesstimate monster band

Monster band in `print-ah-guesstimate` **cannot be <20%** if:

1. Last print realized was **≥+20%**, and
2. This print is still in the same category (AI/data).

A 10% monster probability with a +36% analog is the SNOW miss.

## One T1 name

Does **not** override user “one T1 name.” It forces a **second-name card**
(structure, cap, clock) so “HPE only” cannot mean “SNOW has no ticket.”

Primary fill = the user’s one name. Second-name card = analog ARM. If the
primary skips, the second-name clock is still live.

## Do not

- Promote analog to **🟢 TAKE** when EM <15%.
- Treat cheap EM as “nothing to capture.”
- Chase a name already **≥+7% AH** (`post-print-gap-capture`).
- Drop the second-name card because the user named one fill.

## Output

```
name | last print % | last-4/7 | EM% | analog/EM | flag | clock | structure
```

Write the second-name card into `catalyst_cards.md`. No **go**.
