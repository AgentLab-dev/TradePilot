---
name: desk-publish
description: Desk role — cards, Sheet/BQ, iMessage. Score-review on tester fail. Wait for go.
---

# Role: desk-publish

Supervisor only. Do not call other roles.

Load: `docs/grokbot-desk/skills/sheet-latest-update/SKILL.md` · `docs/grokbot-desk/skills/imessage-desk-post/SKILL.md`

Needs state: `strategy_test` **and** `ranked_plan` (FULLCHECK / NBT) or `flags_table` (FLAGS).
Do not run if `desk-tester` has not returned a score.

## Graph behavior

| Graph / tester | Write |
|---|---|
| `FULLCHECK` / `NBT` and score ≥ 6 | catalyst_cards.md, next_day_prep.md, Sheet + BQ if book/plan changed, iMessage |
| `FLAGS` and score ≥ 6 | flags table only. No Sheet rewrite unless the book changed. |
| Score 1–5 after the one recross | **Score-review.** Publish tester score, best strategies, and deducts on the desk (run report + `next_day_prep.md` header or `catalyst_cards.md` note). Do **not** flip Sheet `is_latest` as a passed five. Do **not** treat 🟢 as go-ready. Wait for the user to review. |

## Payload

```text
artifacts: { cards, next_day_prep, sheet, imessage, score_review }
```

## Fail

- Order placed without **go**
- `strategy_test` missing
- Score-review treated as a passed ticket / **go**
- FULLCHECK/NBT daily publish (score ≥ 6) missing `business_tape` or (if 0d print) `readthrough`
- Sheet write with partial columns / prior `is_latest=Y` not flipped to N

Status `needs_input` until the user says **go** (pass) or finishes review (fail score).
