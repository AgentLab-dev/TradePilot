# Command: DAILY LESSON

Trigger: `DAILY LESSON`, `daily lesson`, `10am lesson`, `3pm lesson`.

Skill: `agents/ssr-st/skills/daily-mover-lesson/SKILL.md`
Read-through: `agents/ssr-st/skills/print-readthrough-t1/SKILL.md` (required on the publish if a 0d AMC/BMO is live)

- If before ~12:00 PT and no `## 10:00` yet → run the 10:00 snapshot.
- If after ~12:00 PT and no `## 15:00` yet → run the 15:00 snapshot.
- Evening wrap always writes `## Consolidated`.

Write `agents/ssr-st/workspace/Documents/daily_lessons/YYYY-MM-DD.md`. For **known list names and their industries**, record what went up or down, **what exactly helped the move**, and the next-pick strategy that shares that cause. Also log ≥20% / ≤−20% anywhere (penny spikes are a footnote). Append HOLE rows to `agent_learning_log.md`. No orders. Wait for **go**.
