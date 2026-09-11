---
name: desk-supervisor
description: >-
  Trade Pilot desk supervisor for Grok Bot. Run graph FULLCHECK, FLAGS, or NBT.
  Pack skill: agents/ssr-st/skills/desk-supervisor/SKILL.md. Roles never call
  each other. Wait for go.
---

# Desk supervisor (desk)

Load the pack skill and `agents/ssr-st/orchestrate/desk.dag.yaml`.

- `FULL CHECK` → graph `FULLCHECK` (13 roles; `desk-tester` before publish)
- `FLAGS` / Health Check → graph `FLAGS` (`flags` → `desk-tester` → `desk-publish` table only)
- `NBT` → graph `NBT` (sources → tape → flags → gate → five → rank → tester → publish)

Do not treat Health Check as the 12-step battery. Halt on role `fail`, except
`desk-tester`: supervisor recrosses once, then tester runs again. Second fail
publishes the score to the desk for review (no go). Score 1–10; print best
strategies. Reddit nominates; never Reddit-alone TAKE. No orders until **go**.
Required sources include Yahoo `https://finance.yahoo.com/`.
