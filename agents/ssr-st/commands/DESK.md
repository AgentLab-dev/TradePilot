# Command: DESK

Trigger: `DESK`, `desk supervisor`, `run the desk DAG`.

Skill: `agents/ssr-st/skills/desk-supervisor/SKILL.md`  
DAG: `agents/ssr-st/orchestrate/desk.dag.yaml`

Pick a graph and dispatch roles in YAML order. Roles never call each other.

| User says | Graph |
|---|---|
| `FULL CHECK` / `DESK` | `FULLCHECK` |
| `FLAGS` / `Health Check` | `FLAGS` |
| `NBT` / Five-new | `NBT` |

Halt on `fail`. `desk-tester` is the exception: supervisor recrosses once, then the tester runs again. Second fail publishes the score to the desk for review (no go). `needs_input` only for **go**. No orders until **go**.
