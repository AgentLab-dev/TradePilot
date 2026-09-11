# Command: NBT / Five-new

Trigger: `NBT`, `Five-new`, `five new`, `next-best`.

Supervisor: `agents/ssr-st/skills/desk-supervisor/SKILL.md` — graph `NBT`.
DAG: `agents/ssr-st/orchestrate/desk.dag.yaml`.
Skills: `docs/grokbot-desk/skills/five-new-nbt/SKILL.md` · `agents/ssr-st/skills/print-readthrough-t1/SKILL.md` · `agents/ssr-st/skills/business-tape-interpret/SKILL.md` · `agents/ssr-st/skills/desk-tester/SKILL.md`

Hard five = NEW + all-four + EM > 15%. Do not pad.

**Daily publish required:** emit `## Business tape` after capture (regime, payer vs paid, Reddit nominated). If any 0d AMC/BMO is live, also emit `## Print read-through T+1`. Fail NBT if either required block is missing. Reddit nominates; never Reddit-alone TAKE. `desk-tester` scores 1–10 before publish; fail recrosses the supervisor once. Rewrite `NBT.md`. Wait for **go**.
