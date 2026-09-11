---
name: print-readthrough-t1
description: >-
  After a 0d BMO/AMC print, write an if-then first-30 ticket on 2–3 unripped
  sleeve peers for the next cash session. Fail evening wrap if the printer has
  no mapped-peer card. Closes ORCL Thu AMC → HPE/DELL Fri +10% with no go.
  Use on evening wrap, FULL CHECK after a print, next-day prep, or when a
  bellwether beats and peers have not yet moved ≥+7%.
---

# Print read-through T+1

The printer is not the only ticket. If a category name **beats and raises** (or
AH ≥ +5%) **after the cash close**, the **next RTH first 15–30** is the sympathy
session for peers that have **not** already ripped.

Logged miss (2026-09-10 18:30 PT wrap): ORCL beat/raise, AH +4.13%. Wrap wrote
ORCL MANAGE + RH Soft-ARM + ADBE STAND. **No HPE. No DELL.** Fri HPE +10.5% /
DELL +11.3% on that cause. The run happened. The **peer card** did not.

This is **not** “predict whatever goes up.” It is: **named printer → named peers
→ if-then go** before the open.

## Clock (do not mix these)

| Printer clock | Peer catalyst session | Example |
|---|---|---|
| **AMC** today | **Next RTH** first-30 | ORCL Thu AMC → HPE/DELL Fri 9:30 ET |
| **BMO** today, first-30 still open | **Same RTH** first-30 | KR Fri BMO → grocery peer same morning |
| **BMO** today, first-30 gone | Next RTH only if peer still **< +7%** | else STAND |
| Peer already **≥ +7%** same session as the printer | **STAND** | SNDK 6/26 giveback. Do not arm T+2. |

T+1 after an AMC print is **catalyst day for the peer**, not a chase.
T+2 after the peer already ripped is the giveback. Anti-chase still kills a
name that is already ≥ +7% when you write the card.

## When mandatory

- Every evening wrap after a 0d AMC/BMO
- Morning FULL CHECK if last night’s printer is still T+1
- User asks “what goes up tomorrow” / next-day prep / sympathy / read-through

Do not wait to be asked. If you named the print, you owe the peer table.

## Map (start here; add if NEWS names a better analog)

| Printer sleeve | Peers (pick 2–3, unripped first) |
|---|---|
| Software / cloud (ORCL, MSFT, AMZN) | HPE, DELL, NTAP, SMCI, ANET |
| Semis / AI (NVDA, AVGO, AMD) | AVGO, AMD, TSM, SMCI, MRVL |
| Memory (MU) | SNDK, WDC, STX, NTAP |
| Cyber (CRWD, PANW) | OKTA, ZS, FTNT, NET, S |
| Travel / software (TCOM, BKNG) | BKNG, EXPE, ABNB — not a smashed analog (NAVN) |
| Energy tanker (ECO) | Other IBD energy leaders — liquidity gate still binds |
| Hardware already ripped | STAND. Next dated card (HPE IR Sep 30), not a chase |

Prefer names on IBD / Big Cap / ALWAYS / PPS-T7. Skip leftover-ban names unless
they are the only liquid analog.

## Verdict

| Printer result | Unripped peer (< +7%) | Already ≥ +7% |
|---|---|---|
| Beat **and** raise, or AH ≥ +5% | **TICKET** first-30 debit, wait for **go** | **SKIP** chase |
| In-line / AH +0 to +5% | Soft-watch card (structure written, no auto go) | SKIP |
| Miss or AH ≤ −5% | **STAND** (or put debit only if analog + liquidity pass) | SKIP |

## What a card is

Same fields as `catalyst-overnight-plan`: ticker, verdict, structure (expiry,
strikes, cap, 1×), first-30 trigger, invalidation, same-session exit.

Required line on the wrap / iMessage `#1` **or** a second line the human can
execute at 9:30 ET:

```
If <PRINTER> beats → go <PEER> first 15–30. If miss → STAND.
```

“Manage the printer, no add” is **not** this card.

## Fail the wrap / FULL CHECK if

- A 0d AMC/BMO name has **no** mapped-peer table (even if every peer is SKIP).
- The table exists but every peer is blank / “watching.”
- A later ≥ +7% mover was on last night’s map and had neither TICKET nor SKIP.
- You armed a peer that was already ≥ +7% (chase).
- You skipped peers because “they have no print tomorrow” (the HPE hole).

## Output (required block)

```markdown
## Print read-through T+1
| Printer | Result / AH | Peer | Peer % vs prior | Verdict | Structure | Clock |
|---|---|---|---|---|---|---|
| ORCL | beat/raise AH +4.1% | HPE | −5.5% Thu | TICKET | Sep18 55/60 cap $1.50 | Fri first-30 |
```

Write the same rows into `catalyst_cards.md` and `next_day_prep.md`.
Every **daily publish** (FULL CHECK, Five-new NBT, evening wrap, 10 AM / 8 PM
lessons, iMessage, Sheet `new-feature`) must include this table when a 0d
AMC/BMO exists. Fail the publish if it is missing. Deliver on Grok Bot +
iMessage (`#1` can be the best unripped peer). Wait for **go**.
No orders from this skill.

## Lesson — ORCL vs HPE / DELL / NTAP (2026-09-10 → 09-11)

One print, two prices. Do not assume the printer leads the sleeve.

| Side | What they priced | Tape |
|---|---|---|
| **Printer (ORCL)** | Funding: capex **~$28.5B**, FCF **−$5.4B**, tiny FY raise, BYO-hardware RPO that hits **FY28+**. Sell-the-news + IV crush. | AH +4% to ~$159, Fri faded to **~$152**. Flattened 155/165 @ **$2.22** vs **$4.80**. |
| **Peers (HPE / DELL / NTAP)** | Bill of materials: **>$30B** AI contracts, RPO **$664B**, OCI **+121%**. They sell the boxes. No FCF debate on their ticket. | Fri HPE **+10%**, DELL **+11%**, NTAP **+6.6%**. SMH only **+1.8%**. |

**Rule:** after a 0d print, ask *who gets paid, and when?* Owner of the build (printer) ≠ seller of the iron (peer). Ticket the **unripped peer**. Do not add the crushed printer. Do not chase a peer already ≥ +7%.
