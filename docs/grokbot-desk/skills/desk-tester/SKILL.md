---
name: desk-tester
description: >-
  Desk tester for Grok Bot. Backtest + strategy test + score 1–10 before
  desk-publish. Pack skill: agents/ssr-st/skills/desk-tester/SKILL.md.
---

# Desk tester (desk)

Load the pack skill. Run after rank (or after flags on FLAGS), before publish.

Score 1–10. Print the top-3 backtest strategies. Fail on score 1–5 or a hard
gate. Supervisor recrosses once, then this role runs again. Second fail
publishes the score to the desk for user review (no go).
