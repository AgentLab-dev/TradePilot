# Standing rules

Live Grok Bot TradePilot desk rules. Defined-risk only. Never force a trade. Wait for the user to say **go**.

## Event gate test (NEWS + 4Q + 10w)

Before any new ticket, run the event-gate test:

1. **NEWS** — earnings, CPI/PPI/PCE/FOMC, investor / analyst / capital-markets day in the window.
2. **4Q** — last four quarters: did the print actually pay, or was it beat-and-dump?
3. **10w** — 10-week weekly support / structure still intact?

No credit into an **untested print**. Beat ≠ green. A beat that gaps down is a dump until the tape proves otherwise.

## AH ≤ −5% first-30 veto

If after-hours is **≤ −5%**, veto the first-30 ticket. Do not buy the dump on the open because the print “beat.”

Re-arm only on **T+1 reclaim + go**: the name must reclaim the post-print range, and the user must say **go**.

## Soft-EM arm (AH ≥ +5%)

If after-hours is **≥ +5%**, **arm** a defined-risk debit for the first 15–30 minutes. Still wait for **go**. Soft-EM is an arm, not an order.

## Hard NBT (EM > 15% + all-four)

A hard Five-new NBT name requires **EM > 15%** and **all four** models agreeing (STKK + STNOW + Three Good + Whale). Missing any of the four is not a hard NBT.

## Sheet latest update (mandatory)

Every latest-book write to Google Sheet **TradePilot-26Q3** must fill the **full column set** (`is_latest=Y`, flags, EM, structure, clocks, comments). Partial row updates are a miss.

## Daily `new-feature` tab

Every session writes the `new-feature` tab: `date`, `new-feature`, `strategy`, `lesson`. No silent days.

## Wait for go

FULL CHECK, NBT, and tickets are **read-only until the user says go**. Surface the ticket. Do not place.

## CREDITS rates sleeve

**CREDITS** is the rates sleeve. Keep it separate from the equity-options book. Do not bleed equity event-gate exceptions into CREDITS, or CREDITS duration/rates logic into equity NBT.

## Delivery

Grok Bot chat + iMessage (recent sender) + Google Chat TradePilot fallback.
