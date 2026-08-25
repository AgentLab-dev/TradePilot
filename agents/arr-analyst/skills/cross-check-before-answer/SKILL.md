---
name: cross-check-before-answer
description: >-
  Mandatory pre-answer verification. Cross-check facts, dates, weekdays, numbers,
  names, acronyms, file paths, and claims against a source before sending any
  answer. Use on every user-facing response, especially calendars, metrics,
  quotes, SQL, Jira keys, and drafted emails.
---

# Cross-Check Before Answer

This skill is **mandatory**. Do not send a user-facing answer until the check below has been run.

## Rule

Always cross-check before you provide an answer.

## Checklist (run silently; do not dump it in the reply)

1. **Dates and weekdays** — Count from a known date. Do not assume “Aug 18 = Monday.” Verify: weekday + date + week-of label match.
2. **Numbers** — Recalculate or re-read the source. Do not blend two metrics into one.
3. **Names and acronyms** — ARR not AARRR; GRR not ZRR; exact person/system names.
4. **Claims vs evidence** — If it is not in the source doc, ticket, or prior confirmed fact, do not state it as fact.
5. **Lists and calendars** — First item, last item, and day names. One off-by-one error invalidates the whole list.
6. **Paths and IDs** — File paths, Jira keys, PR numbers, job IDs. Copy from source; do not reconstruct from memory.

## How to check

- Prefer a tool (`date`, file read, Jira/Snowflake query) over memory.
- If two sources conflict, state the conflict — do not pick the convenient one.
- If a fact cannot be verified, say so and give the next best confirmed fact.

## Failure pattern this exists to stop

Wrong: “Week of Aug 18 (Monday)” when today is Friday Aug 14 and Monday is Aug 17.

Right: Friday Aug 14 → Sat 15 → Sun 16 → **Mon Aug 17**. Then label weeks from that Monday.

## Output

Fix the answer. Do not lead with the checklist. If a check changed the answer, use the corrected facts only.
