# FQC-ARR — Demo Cheat Sheet (present-now)

Full presenter script: `fqc_arr_30min_demo_talking_points.md`. This is the quick card to walk in cold.

## One-liner (open with this)
> "FQC-ARR — Finance ARR Quarter Close — is an autonomous Analytics Engineer that takes a Jira ticket from intake → validation → testing → PR → CI/CD → QA hand-off, pausing only where human judgment matters."

## What it is (30 sec)
- The repetitive, high-stakes ARR close work — build/validate ARR/ACV/NRR/GRR, reconcile dashboards, write it up in Jira — run the way a senior AE would.
- Built as a **deterministic Python Supervisor + 12 specialist sub-agents**. The Supervisor runs **no LLM** — it holds state, dispatches, enforces gates. Only 3 leaf sub-agents use a model.

## Architecture in one breath
- **Entry points:** CLI / Cursor / scheduled — same logic, different runner.
- **Supervisor:** Mode A = scheduled snapshot close; Mode B = 10-role ticket DAG; on-demand debugger / quarter-close-runner / daily-reflection.
- **External systems via MCP/CLI** (Jira, Snowflake, dbt, GitHub, Slack, Sigma) — auditable, sub-second.
- **Memory:** live thinking log (`tail -f`) + a verified lesson store that auto-promotes recurring lessons.

## Flow A — new ticket (the core demo, 10 roles)
jira-intake → requirements-analyzer → code-data-validator → clarifier → **implementer (HUMAN writes the SQL)** → test-runner → pr-author → ci-monitor → cd-monitor → qa-handoff.
- **Punchline:** everything but the red box runs without you. You write the SQL; the agent does intake, validation, testing, PR, monitoring, and the Jira write-up.

## Flow B — debugging (root-cause in minutes)
Lineage walk → validation matrix → AC analysis → ranked root-cause → **proposes fix (never writes it)** → regression test → Jira comment shaped by ticket type.
- **Proof story:** the **$22K NRR variance** two dashboards disagreed on — one filtered lifetime at *product* grain, the other at *account* grain. Agent traced it in minutes, proposed the one-line fix + regression test.

## Trust anchors (leadership will ask)
- **No autonomous prod edits** — implementer is a deliberate human boundary.
- **Authorization dial:** `smart_gates` (default, pauses before every write) vs opt-in `full_auto`.
- **Clarifier never guesses** — asks terminal → Slack `ans:` → Jira, in that order.
- **Lessons verified against prod commits**, stale ones auto-archived — no silent drift.

## Impact soundbites
- RCA: hours/days → **minutes**. Hotfix: 1–2 weeks → **<48h**.
- Traced the **$51.8M "backwards term"** issue through 400+ models to the exact CASE in `stg_em_int_renewal_flags.sql` — and proved it was *correct* business behavior, avoiding an unnecessary fix.
- Daily automated parity tie-outs; auto-generated recon/Excel; end-to-end PR assurance (Copilot triage, PII scan, Jira write-back).

## 30-second elevator (if cut short)
> "A deterministic Supervisor dispatches 12 specialist sub-agents to run an ARR ticket end-to-end — pausing only where judgment matters, like writing the SQL. It root-causes metric bugs in minutes, asks in Slack instead of guessing, documents everything to Jira, and gets smarter every run through a verified lesson store."
