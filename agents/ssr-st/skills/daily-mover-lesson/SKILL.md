---
name: daily-mover-lesson
description: >-
  Twice-daily lesson (10:00 AM PT and 3:00 PM PT) plus one consolidated daily
  lesson. For known list names and their industries, record what went up or
  down, what exactly helped the move, and the next-pick strategy. Use at 10 AM,
  3 PM, evening wrap, "daily lesson", or when a listed name ripped with no go.
---

# Daily mover + lesson cadence

The lesson is **not** a dump of % gainers. It is: take the **known list**
(IBD 50 / Sector Leaders / Big Cap 20 / PPS-T7 ON / ALWAYS / today's five /
NEWS-named sleeve leaders), see **what went up or down**, name **what helped
the move** (print, industry tape, news, IR, analog, or "no catalyst / tape
only"), then write the **next-pick strategy** from that cause.

Public practice (unusual-volume / journal reviews): scan **at fixed clocks**,
do not rank on % alone, require a catalyst + liquidity, do not chase a stale
gap, write **one lesson per day**, change at most one process rule from the
consolidated note.

## Clocks (America/Los_Angeles)

| Clock | Job |
|---|---|
| **10:00 AM PT** | Morning snapshot. Open + first 90 min. Write section `## 10:00`. |
| **3:00 PM PT** | Mid/late RTH update (into last-90). Write section `## 15:00`. Promote any 0d PPS-T1 TICKET. |
| **Evening wrap** | Merge 10:00 + 15:00 + AH into **one** `## Consolidated` lesson. Append holes to `agent_learning_log.md`. |

Skip weekends / US market holidays. If the user says "daily lesson" off-clock, run the **nearest** snapshot and still keep one file per date.

## File (one per session date)

`agents/ssr-st/workspace/Documents/daily_lessons/YYYY-MM-DD.md`

Overwrite in place. Do not spawn a second file for 3 PM.

## Universe (known stocks + industries)

Quote the **list**, not the whole market:

- IBD 50 + Sector Leaders + Big Cap 20 (from `ibd_stock_lists.md`)
- PPS-T7 ON + ALWAYS / category map
- Today's five + book + leftover ban
- Sleeve ETFs: GDX · IGV · SMH · XOP · KRE (industry tape)
- Any NEWS / Reddit-named sleeve leader

Also log **≥+20% / ≤−20%** anywhere (penny spikes go in a footnote; they do
not become the next pick). Large-cap or list names **≥+10% / ≤−10%** always
get a row even if under 20%.

## What each mover row must answer

| Field | Meaning |
|---|---|
| Ticker + % vs prior official close | Up or down. Say RTH vs AH. |
| Industry / sleeve | GDX IGV SMH XOP KRE or GICS. Did the **sleeve** move with it? |
| **What helped the move** | One concrete cause: print beat/miss, AH gap, industry rotation, WSJ/MW headline, IR date, analog follow-through, or **tape-only / no catalyst**. |
| On the list? | IBD / T7 / five / NEWS / book. |
| TICKET / SKIP / HOLE | Per `list-to-ticket`. Board = hole if it then ripped. |
| Chase? | Already ≥+7% from the open → STAND. Do not reuse as next pick. |

Sources: Robinhood quotes + `get_equity_news`, WSJ/IBD/MW/Barron's (SSO),
Reddit SOCIAL-ONLY, `ibd_stock_lists.md`. % alone is not a lesson.

## Consolidated lesson (required fields)

1. **Tape one-liner** — SPY/QQQ/SMH/VXX + strongest/weakest sleeve.
2. **List movers** — up and down on **known** names, grouped by industry.
3. **What helped** — one paragraph: the cause that actually moved listed
   names today (print / industry / news). That sentence **is** the lesson.
4. **Process hole** — list≠ticket, analog ignored, board not scored, reclaim
   killed, or no **go** on a live card.
5. **Flags/gates** — PPS-T7/T1, analog, gap, mix, leftover, whale. Name the
   gate that blocked a go **or** failed to force a ticket.
6. **Next-pick strategy** — one TICKET that **shares the cause** (next analog
   in the same industry or next print with the same setup), with structure,
   cap, clock. Not the already-ripped name. Not a recycled leftover.
7. **Skill delta** — one line if a rule must change. Else "none".

## Fail the run if

- 10:00 or 15:00 was due (weekday RTH) and today's file has no that section.
- Evening wrap has no `## Consolidated`.
- A listed name moved ≥+10% / ≤−10% and has no "what helped" line.
- Next pick is the already-ripped name, or has no shared-cause sentence.
- A HOLE row is not copied into `agent_learning_log.md` the same day.
- A 0d AMC/BMO is live and the publish has no `print-readthrough-t1` mapped-peer table.

No orders. Wait for **go** on any TICKET.
