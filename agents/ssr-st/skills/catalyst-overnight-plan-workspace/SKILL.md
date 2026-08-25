---
name: catalyst-overnight-plan
description: >-
  Forces a T+1 catalyst card (take / arm / stand-down WITH structure) for every
  known next-session event: earnings, investor day, analyst day, capital-markets
  day, and mapped sympathy peers. Use on FULLCHECK, evening wrap, next-day prep,
  "tomorrow's plan", or whenever earnings_radar / the calendar is read. Prevents
  treating the event gate as "ignore the name." Logged miss: 2026-08-13 XE
  earnings and SNDK investor day were known 8/12 and never armed.
---

# Catalyst Overnight Cards

The event gate answers **"do not sell premium through this print."** That is defense.
This skill answers **"what is the defined-risk ticket if the print rips or dumps?"**
That is the overnight plan. **A name on tomorrow's calendar with no card is a miss.**

Logged failure (2026-08-13): XE earn AM and SNDK investor day were both knowable on
8/12. Plans said "No XE anything" and "don't chase SNDK" *after* the open. Neither
was an armed first-30-min ticket the night before.

## When this skill is mandatory

- Every `FULL CHECK` / FULLCHECK (after step 5 Event gate, before ranking takes)
- Every evening wrap / "prepare for next day"
- Any time `earnings_radar.md` is regenerated or read
- Any user ask about tomorrow's plan, catalysts, or "what should we have traded"

**Do not wait to be asked.** If you listed an event, you owe a card.

## Calendar sources (UNION — Nasdaq radar alone is not enough)

`fetch_earnings.py` intersects Nasdaq's calendar with `market_history.md`. It **missed
XE on 8/13** even though XE was in the cache and Robinhood's calendar had it. Always UNION:

1. `ssr-analyst/Documents/earnings_radar.md` (Nasdaq ∩ universe)
2. Robinhood MCP `get_earnings_calendar` for **today + next 2 sessions**
3. `get_equity_fundamentals` → next earnings date for **book + watch + READTHROUGH peers**
4. Web search, every evening and every FULLCHECK:  
   `"investor day" OR "analyst day" OR "capital markets day"`  
   for SMH/memory/AI names, the book, and mapped peers (MU→SNDK/WDC/STX, NVDA→SMCI/CRWV, …)
5. Open book / `next_day_prep.md` / `options_watchlist.md` leftover shorts into a print

Investor days **never** appear on the earnings radar. That is why SNDK was invisible to code.

## What a card is (required fields)

Write one card per T+0 / T+1 event into `ssr-analyst/Documents/catalyst_cards.md`
(overwrite each evening / FULLCHECK). Also paste the table into `next_day_prep.md`
§ **"Tomorrow's catalyst cards"** and into FULLCHECK output.

| Field | Required |
|---|---|
| Ticker + event type + session (BMO / AMC / open / investor day) | yes |
| Verdict | **take** / **arm** / **stand-down** |
| Structure | strikes, expiry, debit/credit cap, size (1× default) |
| Trigger | first 15–30 min hold / reclaim / fail of a named level |
| Invalidation | price or time (e.g. fade VWAP → flatten) |
| Exit | **same session** unless explicitly a hold |
| Why not "no trade" | one sentence; "broken 3-month chart" is **not** sufficient on catalyst day |

**"No credit sell" is not a card.** It is only the event-gate line. The card is the
directional play *or* an explicit stand-down **with structure you would have used
if the trigger printed** — so the morning agent can execute without reinventing it.

## How to pick the structure (do not confuse with Rule 3)

| Situation | Structure |
|---|---|
| Known binary **tomorrow** (earnings BMO/AMC, investor day) | Arm a **defined-risk debit** (call if hold/rip, put if dump). Same-day exit. Tiny size (1×). |
| Bellwether already ripped **today** and a **new** peer event is **tomorrow** (MU rip + SNDK investor day) | Arm the **peer** for the open / first 30 min — this is still catalyst day for the peer, not T+1 chase. |
| Bellwether ripped **today**, peer has **no** new event tomorrow | Do **not** arm the peer overnight. That is the 6/26 SNDK giveback (chase next day). |
| Name already +7%+ **this morning** and you have **no** pre-armed card | Stand down. Anti-chase. Log the miss. Do not buy calls 90 minutes in. |
| Leftover **short premium** into the print | **Close before the print.** Not optional. |

Rule 3 ("don't chase a post-earnings gap / don't buy calls as a hold") still stands for
**overnight holds and credit sells**. It does **not** cancel a same-day debit that was
armed T−1 and confirmed in the first 15–30 minutes.

Anti-chase is an **entry-timing** rule, not a **planning** rule. You still write the
card the night before.

## FULLCHECK / evening-wrap checklist (fail the run if any box is empty)

- [ ] Every 0d / 1d earnings name (radar ∪ MCP ∪ fundamentals) has a card
- [ ] Web search for investor / analyst / capital-markets days on book + SMH/memory/AI + mapped peers
- [ ] Every mapped peer of a name that moved ≥5% today is either on a card or explicitly "no new event → do not chase T+1"
- [ ] Leftover short premium into a T+0/T+1 print has a **close** ticket
- [ ] `catalyst_cards.md` written; `next_day_prep.md` has the same table
- [ ] Morning FULLCHECK **leads** with those cards (confirm / fire / kill), not with "don't chase" after the rip

## Same-day exit (non-negotiable on these tickets)

Catalyst-day momentum dies on T+1 (SNDK 6/25 +22% → 6/26 −10.5%). Debit cards from this
skill flatten the same session unless the user explicitly converts to a hold.

## Examples (the 8/13 miss, written as the cards that should have existed)

**XE — earn Thu 8/13 BMO** (known Wed 8/12):
- Close leftover Aug 21 $12.50P **before** the print
- Arm: if XE holds first 15–30 min above the post-print opening range, 1× defined-risk
  call debit, flatten same day. If it dumps and holds below, skip or 1× put debit.
- Not allowed: "No XE anything" because the 3-month chart is broken. Catalyst day ≠ put-credit day.

**SNDK — Investor Day Thu 8/13** (MU already +5–6% Wed, SNDK already +8% Wed):
- Arm Wed night: if SNDK holds first 15–30 min on investor-day headlines, 1× call debit,
  flatten same day. WDC/STX as lagging sympathy only if they have not already ripped.
- Not allowed: discover +15% at 9:10 AM and write "don't chase." That is correct *entry*
  discipline and a failed *overnight plan*.
