---
name: daily-desk-lessons
description: >-
  Harvest the day's TradePilot desk lessons, write at least one Daily new-feature
  row, event-gate every print pick, update Sheet latest with the full column set,
  and surface next-best picks. Use on the 10am / 8pm lesson automations, after a
  FULL CHECK or Five-new NBT, after a miss or win, or when the user asks for
  lessons, new-feature, or "what did we learn." Read-only until go. Deliver Grok
  Bot chat + iMessage (recent sender) + Google Chat TradePilot fallback.
---

# Daily desk lessons

Close the learning loop every session. A silent day is a miss. Harvest the lesson,
write the Sheet, event-gate any print pick still on the board, then surface next-best
picks. Do **not** place. Wait for **go**.

Standing rules: [`../../STANDING_RULES.md`](../../STANDING_RULES.md).
Source map: [`../../WHERE_LATEST_INFO_LIVES.md`](../../WHERE_LATEST_INFO_LIVES.md).
Companion skill: [`../daily-new-feature/SKILL.md`](../daily-new-feature/SKILL.md),
[`../print-readthrough-t1/SKILL.md`](../print-readthrough-t1/SKILL.md),
[`../business-tape-interpret/SKILL.md`](../business-tape-interpret/SKILL.md).

## When

- 10:00 AM and 8:00 PM PT lesson automations
- After FULL CHECK, Five-new NBT, or evening wrap if a rule moved
- After any miss, win, first-30 veto, or Sheet write
- User says lessons / new-feature / "what did we learn"

Skip weekends/holidays unless a print or Sheet change happened.

## Scorecard + calibration (first)

Using the prediction ledger and real closes. Do not invent fills. Helper: `tradepilot.desk_process.build_scorecard`.

1. Rolling 20-session table, real tickets and paper picks **separately**: N, hit rate, average underlying return, the same-window SPY return, and the excess. Option return only where the exit fill is known.
2. Gate audit: STAND / veto names as `SAVE` vs `MISSED-WINNER` (> +5% and beat SPY in the called direction), split by the gate that blocked the trade (EM>15%, all-four, AH veto, and any other logged gate).
3. Calibration: buckets ≤40, 45–55, 60–70, ≥75. Hit rate per bucket and the Brier score. If a bucket is off by more than 15 percentage points with N ≥ 8, publish the shrink factor for rank-next-best. Gaps between those buckets stay unbucketed.
4. Regime split: results by the REGIME verdict at entry.

Write `agents/ssr-st/workspace/Documents/scorecard_YYYY-MM-DD.md` and put the one-line scorecard in the desk note (`real W-L · paper W-L · saves · missed winners`).

## Feedback into gates (evidence rule)

- A gate change needs N ≥ 8 relevant cases over at least 10 sessions. One anchor trade is a note, not a rule. `evaluate_gate_change`.
- A gate whose missed-winner count exceeds its save count over 20 sessions is flagged `LOOSEN?` and goes to the user. Do not loosen EM>15% + all-four without the user's OK.
- A gate whose blocked names lagged (saves ≥ 2× misses) stays.
- **Rule budget:** every new veto or sub-rule added to event-gate or miss-catch retires or merges one existing rule. Anchors stay in the dated lesson, not as a new skill veto.

## Sweep (scorecard first, then the six)

0. Scorecard, calibration, and the `REGIME` block.
1. **Harvest lessons** — Read today's `desk_sources_YYYY-MM-DD.md`, catalyst cards, Sheet
   latest (`is_latest=Y`), and the agent learning log. Pull every miss, win, veto, and
   process break. Newest first. One lesson = one durable rule or confirmed non-change.
2. **Daily new feature (≥1 row)** — Load `daily-new-feature`. Write **at least one** row
   to Sheet tab `new-feature` with `date | new-feature | strategy | lesson`. No silent
   days. If the only honest feature is "stood down," write that.
3. **Event gate on print picks** — Load `event-gate-test`. Every name still armed into a
   print (T+0 / T+1 earnings, investor / analyst / capital-markets day, CPI/PPI/PCE/FOMC)
   gets a NEWS + 4Q + 10w line **and** the live AH ≤ −5% first-30 veto. No credit into an
   untested print. Beat ≠ green.
4. **Sheet latest update (full columns)** — If the book, flags, EM, structure, clocks, or
   comments changed, write the **full** latest row on tab `TradePilot-26Q3`
   (`is_latest=Y`, flags, EM, structure, clocks, comments). Partial rows are a miss.
5. **Next-best picks** — Surface the current NBT / first-30 / stand-down list from
   Five-new NBT + overnight cards. Hard NBT still requires all-four + EM > 15%. Label
   🟢 take / 🟡 arm / 🔴 stand-down. Each armed card and each paper pick carries the
   pre-trade checklist (thesis, catalyst, levels, R:R ≥ 2:1, size, P%). Append them
   to the ledger. Not an order. Tie each lesson to a scorecard count, not to one anecdote.
5a. **Business tape** — Load `business-tape-interpret`. Fail the lesson if capture ran and `## Business tape` is missing. Reddit nominates; never Reddit-alone TAKE.
5b. **Print read-through T+1** — Load `print-readthrough-t1`. If any 0d AMC/BMO is live,
    emit the mapped-peer table. Fail the lesson publish if it is missing (ORCL 9/10 →
    no HPE/DELL).
6. **Deliver** — Grok Bot chat + iMessage (recent sender) + Google Chat TradePilot
   fallback. Same body on all three when possible.

## Output (required block)

```markdown
# Daily desk lessons — <weekday, date>  (<time> PT)

## Scorecard (20 sessions)
real W-L · paper W-L · hit rate · excess vs SPY
Gate audit: <gate> SAVE n / MISSED-WINNER n
Calibration: bucket hit rates · Brier · shrink factor
REGIME | …

## Lessons harvested
- YYYY-MM-DD — <title>  [MISS | WIN | RULE]
  - What happened / rule / status

## New-feature row
- date | new-feature | strategy | lesson

## Event-gate on print picks
- EVENT-GATE TEST <TICKER>: NEWS=… | 4Q=… | 10w=… | AH=… | VERDICT=STAND|ARM|RE-ARM T+1

## Sheet latest
- full-columns written | skipped (no book change)

## Next-best picks
- 🟢 / 🟡 / 🔴 + structure + clock + wait for go

## Business tape (required after capture)
Regime: … | Story: … | Payer vs paid: … | Reddit: … | Nominated: …

## Print read-through T+1 (required if any 0d AMC/BMO)
| Printer | Result / AH | Peer | Peer % | Verdict | Structure | Clock |

Access: IBD|WSJ|MW|Whale|Reddit|ApeWisdom OK/SKIP (if a capture ran this session)
```

## Hard rules

1. **≥1 new-feature row per trading day.** Standing `daily-new-feature`.
2. **Event gate before any print pick stays on the board.** High IV ≠ credit into print.
3. **Sheet latest = full columns or do not write.** See standing rules.
4. **Wait for go.** Lessons and picks are read-only.
5. **Defined-risk only.** CREDITS rates sleeve stays separate from equity NBT.
6. **Never force a trade to make a lesson look complete.** A logged stand-down counts.
7. **Print read-through on every daily publish** after a 0d AMC/BMO. Fail if the mapped-peer table is missing.
8. **Business tape on every daily publish** after capture. Fail if missing. Reddit nominates; never Reddit-alone TAKE.
9. **Scorecard before anecdotes.** Fail the lesson if the 20-session line is missing. Do not add a veto from a single anchor, and do not loosen EM>15% + all-four without the user.

## Sheet

- Id: `1RkdF93AK7BWRf0SktGVrHehG0XU_nz21WCzSrAP68vQ`
- Main tab `TradePilot-26Q3` — latest book
- Tab `new-feature` — daily features
