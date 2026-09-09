---
name: pre-print-screen
description: >-
  PPS (pre-print screen). Two separate strategies: PPS-T7 (week monitor on
  known-category names 2–7d from a print) and PPS-T1 (into-print OTM debit on
  0d/1d). Use on FULL CHECK, evening wrap, earnings radar, missed gap, OKTA-style
  print, or when writing catalyst cards. Output tables must show two flags:
  PPS-T7 and PPS-T1. Load t7.md and t1.md as separate approaches — do not merge
  them into one ticket.
---

# PPS — pre-print screen

Two strategies. Two flags. Do not collapse them.

| Code | Strategy | Window | Job |
|---|---|---|---|
| **PPS-T7** | Week monitor | 2–7d | Watch category names. News, peers, EM, beats. **No fill.** |
| **PPS-T1** | Into-print fill | 0d / last 90 min RTH | Cheap OTM debit **before 4:00 ET** if the T−1 score promotes. |

Logged miss (2026-08-26): OKTA was already ALWAYS / cyber / IBD. **PPS-T7** never
ran the week of 8/19. **PPS-T1** never promoted a 160/170 into AMC. The after-print
ATM card is neither flag.

Shared category union, scoring, and “how we pick the best”:
[approach.md](approach.md) · [t7.md](t7.md) · [t1.md](t1.md).
Load the file for the window you are in. A name can carry **both** flags at once
(T−7 ON while T−1 is still ⚪).

## Flags (required columns on every output table)

Use these exact tokens. 3Good stays put-credit-only. Whale does not veto PPS.

**PPS-T7**

| Flag | Meaning |
|---|---|
| 🟢 ON | Category name, print in 2–7d, daily watch live |
| 🟡 THIN | In window; EM/news/beats still incomplete |
| ⚪ | Not a T−7 name (0d/1d, >7d, or not in a category) |
| ⬛ DONE | Print already happened (was ON) |

**PPS-T1**

| Flag | Meaning |
|---|---|
| 🟢 TAKE | Fill 1× OTM last 90 min / T−1 close (wait for **go**) |
| 🟡 ARM | 0d/1d; score close; fill only if last-90 still clears |
| 🔴 STAND | EM gate without beat/theme (do not auto-buy) |
| ⚪ | Not a T−1 name |
| ⬛ MISS | Should have been TAKE; window closed |

Every FULL CHECK / wrap ticker row that already shows STKK · STNOW · 3Good · Whale
also shows **PPS-T7 · PPS-T1**. The PPS board is `print_monitor.md`.

## Fail the run if

- A category name with a print in 2–7d has PPS-T7 = ⚪
- A 0d/1d category name has no PPS-T1 flag
- The ranked table omits the two PPS columns

Personal 1×. Wait for **go**. Agentic cash does not take a $3–4 debit.
