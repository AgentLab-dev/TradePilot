---
name: pps-t1-em-recalibrate
description: >-
  Recaptures PPS-T1 expected-move (EM%) at last-90, not morning. TAKE only if
  ATM straddle/spot ≥15% on the expiry you buy. Weekly vs monthly are different
  gates. Do not use whale IV×√T as EM. Use on last-90, PPS-T1 TAKE/ARM, HPE
  print, guesstimate, or when EM% from whale_check disagrees with the chain.
---

# PPS-T1 EM% recapture

PPS-T1 TAKE is an **expiry-local** gate. Recapture in the **last 90 min of RTH**
(2:30–4:00 ET). Morning FULL CHECK EM% is a preview, not the fill number.

## Formula (this is EM)

```
EM% = (ATM call mid + ATM put mid) / spot
```

ATM = strike nearest live last. Use Robinhood `get_option_quotes` on that
expiry. Report both **weekly** (front, often Sep 4) and **monthly** (often
Sep 18) when the ticket is not the weekly.

**🟢 TAKE** only if EM% **≥15% on that expiry**. Beats / surprise / theme still
required (`pre-print-screen/t1.md`). EM% 12–14.9 stays **🟡 ARM**.

## Do not

| Wrong | Right |
|---|---|
| Whale `S×IV×√T` as EM | ATM straddle / spot |
| Morning EM as the fill | Recapture last-90 |
| Weekly EM for a monthly debit | Gate on the expiry you buy |
| User $60 thesis as TAKE | Thesis ≠ EM% |

Whale Watch still runs. Its IV×√T number is a **different formula**. If it
prints ±17% and the Sep 4 ATM straddle is ±11%, the PPS gate is **11%**.

## Weekly vs monthly

| Ticket | Gate |
|---|---|
| 0d weekly debit (e.g. Sep 4) | That weekly ATM straddle / spot |
| User-skipped weekly → monthly (HPE Sep 18 55/60) | **Monthly** ATM straddle / spot. Weekly is context only |
| Both <15% | **ARM**, not TAKE. Fill only on **go** |

HPE 9/1–9/2: Sep 4 ±11.5%, Sep 18 ±13.8–14.2%, whale ±17.8%. Gate = straddle.
**ARM.** Recapture Wed last-90. Do not promote on whale.

## Output (required)

```
expiry | ATM strike | call mid | put mid | straddle | spot | EM% | flag
weekly | … | | | | | xx.x% | ARM/TAKE/STAND
monthly | … | | | | | xx.x% | ARM/TAKE/STAND
whale IV×√T | … | (not the gate)
clock | last-90 recapture vs morning preview
```

No **go** in this skill. Personal 1×.
