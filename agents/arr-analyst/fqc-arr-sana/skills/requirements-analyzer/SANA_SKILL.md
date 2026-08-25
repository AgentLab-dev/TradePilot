---
name: requirements-analyzer
description: Turn a parsed FQC-ARR TicketSpec into a KPI/requirements specification for an ARR analytics-engineering change — candidate dbt models, in-scope metrics, business rules, and open questions. Emits a host-LLM prompt for refinement. Use as role 2 of the FQC-ARR DAG after jira-intake. Read-only; produces a spec, not code.
license: Proprietary-Internal
compatibility: Host LLM runs the emitted refinement prompt. Grounds on fqc-lessons knowledge. Read-only.
metadata:
  role_order: "2"
  status_values: "ok | warn | needs_input"
allowed-tools: fqc-lessons.load_for fqc-lessons.search
---

# requirements-analyzer

Translate the ticket into a testable requirements/KPI spec that the validator and implementer can act on.

## Steps
1. Read `payload.ticket` (from jira-intake). Ground with `fqc-lessons.load_for("requirements-analyzer")`.
2. Produce a **heuristic skeleton**: candidate models (map AC nouns/metrics to `arr_*`/`finance_*` models), affected metrics (ARR/ACV/NRR/…), business rules touched, and explicit **open questions**.
3. Emit `payload.prompt` + `payload.preferred_model` so the host LLM can refine the skeleton (fill KPI formulas, edge cases, currency variant).

## Output — `payload.requirements` (RequirementsSpec)
`scope_summary, candidate_models[], kpis[]{name, grain, formula, variant}, business_rules[], questions[]`.
- `status = ok` if the spec is confident; `warn` if it is a heuristic skeleton needing LLM refinement; `needs_input` if AC is missing.

## Hard rules
- Read-only. Do not create branches or edit files (that is implementer).
- Pick exactly one currency variant per metric (`USD_CURRENT` / `USD_HIST` / `USD_ACTUAL`); never mix in one waterfall.
