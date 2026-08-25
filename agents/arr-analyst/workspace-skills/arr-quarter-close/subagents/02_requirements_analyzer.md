# Sub-agent 2: requirements-analyzer

**Module**: `agents/arr_quarter_close/subagents/requirements_analyzer.py`
**Skills**: `finance-functional-architect` (KPI spec framework),
`finance-bsa-data-analyst` (data-first translation)

## Responsibility

Translate a `TicketSpec` into a `RequirementsSpec` using the KPI spec
framework. Surface gaps as `questions` for the clarifier.

## How it works

The module produces a structural skeleton via regex + heuristics, then emits
an LLM prompt that the supervisor hands to a model (Cursor SDK or any other
LLM). The Python skeleton alone is usable but lower confidence.

## Inputs

```json
{ "ticket": <TicketSpec from sub-agent 1> }
```

## Outputs (RoleResult)

```json
{
  "role": "requirements-analyzer",
  "status": "needs_input|warn|ok",
  "pause_reason": "LLM refinement of RequirementsSpec",
  "payload": {
    "requirements": {
      "ticket_key": "EDAEM-3725",
      "scope_summary": "...",
      "in_scope_models": ["arr_line_categories", ...],
      "kpis": [{"name": "...", "formula": "...", "grain": "...", ...}],
      "questions": ["Currency variant not specified", ...],
      "confidence": "low|medium|high"
    },
    "prompt": "<LLM prompt to refine the skeleton>"
  }
}
```

## When delegated as a Cursor Task

```text
subagent_type: generalPurpose
description: "Requirements analysis EDAEM-XXXX"
prompt: |
  Read .cursor/skills/arr-quarter-close/subagents/02_requirements_analyzer.md.
  Read .cursor/skills/finance-functional-architect/SKILL.md.
  Run the heuristic skeleton via the module, then refine each KPI per the
  framework. Return strict JSON for RequirementsSpec - no surrounding prose.

  TicketSpec input: <paste>
```

## Quality bar

A KPI is "ready" only when every field is filled: Business Definition,
Formula, Grain, Periodicity, Currency Basis, Source of Truth, Validation
Rule. Anything else -> `open_questions` on the KPI.
