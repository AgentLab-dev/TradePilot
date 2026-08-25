---
name: agentic-architecture-validator
description: >-
  Run an 8-dimension validation audit on any agentic AI system (supervisor +
  sub-agents). Combines Anthropic's "Building Effective Agents", 12-Factor
  Agents, LangGraph multi-agent patterns, OWASP LLM Top 10, and NIST AI RMF
  into a single reviewable rubric with pass/partial/fail scoring per
  dimension. Use when reviewing a new agent design, certifying an existing
  agent as production-ready, preparing a sign-off document, or asking
  "is this agent architecture good?". Produces a structured validation
  report ready to attach to a Jira ticket or share with reviewers.
---

# Agentic Architecture Validator

A single rubric that lets you answer the question **"Is this agent architecture sound?"** with evidence, not vibes.

The rubric is the union of:

- Anthropic's "Building Effective Agents" (Dec 2024) — pattern fitness
- 12-Factor Agents (Dex Horthy, 2024) — production-grade properties
- LangGraph / OpenAI Supervisor pattern — topology fitness
- OWASP Top 10 for LLM Apps (2025) — security boundaries
- NIST AI RMF 1.0 — governance

Use this skill any time someone asks "is this design good?" or "should we sign off on this?"

## The 8 dimensions

| # | Dimension | What it tests | Source |
|---|---|---|---|
| 1 | **Pattern fitness** | Can you name the pattern? Is it the right pattern for the problem? | `agentic-architecture-patterns` |
| 2 | **Functional correctness** | Typed contracts, structured outputs, no free-text passing | 12-Factor #1, #4 |
| 3 | **Boundary integrity** | Sub-agents have single responsibilities; supervisor doesn't leak | 12-Factor #10; `multi-agent-supervisor-pattern` |
| 4 | **Authorization safety** | Pause points before every write; explicit auth modes | 12-Factor #7; OWASP LLM06 |
| 5 | **Observability & auditability** | Live thinking log, structured reports, every decision recorded | 12-Factor #8; NIST AI RMF MEASURE |
| 6 | **Resumability & fault tolerance** | Pause / resume API; crash → structured error; tool fallbacks | 12-Factor #6, #9, #12 |
| 7 | **Controllability mid-run** | Side-channel intervention; trigger from anywhere | 12-Factor #7, #11 |
| 8 | **Domain correctness** | Sub-agents match domain semantics (e.g. finance recon checks tie to the canonical waterfall) | Domain skills (e.g. `finance-functional-analytics`) |

## How to run an audit

### Phase 1: Discovery (5 min)

Gather these inputs:

- **Architecture doc** (Markdown, Mermaid, or whiteboard photo)
- **Code location** (path to the supervisor + sub-agents)
- **Sample run output** (dry-run JSON or pretty-print)
- **Doc trail** (rules + skills + READMEs)

If any is missing, the audit cannot proceed — flag it and stop.

### Phase 2: Score each dimension

For each of the 8 dimensions, produce:

- **Score:** ✅ pass / ⚠️ partial / ❌ fail
- **Evidence:** specific file paths, line numbers, or output excerpts
- **Gaps:** what's missing if not ✅
- **Remediation:** concrete next steps if ⚠️ or ❌

### Phase 3: Cross-check security

Run the full **OWASP LLM Top 10** checklist via the `owasp-llm-top-10` skill. Any ❌ on LLM05, LLM06, or LLM10 blocks sign-off.

### Phase 4: Produce the report

Use the **Validation Report Template** below.

## Validation Report Template

```markdown
# Agentic Architecture Validation Report — <Agent Name>

**Date:** YYYY-MM-DD
**Reviewer:** <name>
**Scope:** <agent or sub-agent set under review>
**Verdict:** ✅ Production-ready / ⚠️ UAT-ready / ❌ Design-stage only

## Executive summary

<3-5 sentence verdict. Lead with the bottom line.>

## Dimension scores

| # | Dimension | Score | Evidence | Gaps |
|---|---|---|---|---|
| 1 | Pattern fitness | ✅ / ⚠️ / ❌ | <file or quote> | <if any> |
| 2 | Functional correctness | ✅ / ⚠️ / ❌ | | |
| 3 | Boundary integrity | ✅ / ⚠️ / ❌ | | |
| 4 | Authorization safety | ✅ / ⚠️ / ❌ | | |
| 5 | Observability | ✅ / ⚠️ / ❌ | | |
| 6 | Resumability | ✅ / ⚠️ / ❌ | | |
| 7 | Controllability | ✅ / ⚠️ / ❌ | | |
| 8 | Domain correctness | ✅ / ⚠️ / ❌ | | |

## 12-Factor Agents compliance

<Score X / 12. Table of factor → pass/partial/fail → evidence.>

## OWASP LLM Top 10 exposure

<For each of 10 risks: mitigated / partial / exposed + evidence.>

## Pattern match

<Anthropic pattern named: e.g. "Orchestrator-Workers". Justification.>

## Sign-off blockers

<List concrete items that must be remediated before sign-off.>

## Recommended next steps

1. <Concrete action item>
2. <Concrete action item>
```

## Scoring guidance

| Overall verdict | Criteria |
|---|---|
| **✅ Production-ready** | All 8 dimensions ✅; 12-Factor ≥10/12; OWASP no ❌ on LLM05/06/10 |
| **⚠️ UAT-ready** | All 8 dimensions ✅ or ⚠️; LLM06 mitigated; needs operational validation (real run, peer review, sign-off) |
| **❌ Design-stage only** | Any dimension ❌; or 12-Factor < 7/12; or OWASP ❌ on LLM05/06/10 |

## Common findings (and how to remediate)

| Finding | Symptom | Remediation |
|---|---|---|
| Pattern not named | Architecture doc describes "the system orchestrates agents" without naming the pattern | Map to one of: Prompt Chaining / Routing / Parallelization / Orchestrator-Workers / Evaluator-Optimizer / Supervisor (see `agentic-architecture-patterns`) |
| Free-text passing | Sub-agent A returns a paragraph; sub-agent B parses it with regex | Add typed dataclass contracts at every boundary |
| Supervisor doing one more thing | supervisor.py > 1500 LOC; mixed responsibilities | Move responsibility to a new sub-agent |
| No pause points | Agent writes to prod / Jira / git without authorization | Add `RoleStatus.NEEDS_INPUT` at every irreversible write; smart-gate by default |
| Missing thinking log | "Why did it do that?" requires reading 5 log files | Add an append-only thinking-log file written at every role start/end + decision |
| Crash brings down DAG | One missing CLI tool kills the whole supervisor | Wrap every sub-agent call in try/except; convert to structured `RoleResult(FAIL)`; provide fallback (e.g. `rg` → `grep` → `Path.rglob`) |
| LLM06 (excessive agency) | Sub-agent can write code AND merge PR AND deploy | Split into separate sub-agents; pause point between each; per-sub-agent authorization |
| LLM10 (unbounded consumption) | CI monitor polls indefinitely | Add `max_hours` / `max_polls` / `tolerance_pct` caps |

## Worked example — FQC-ARR (reference)

The Finance ARR Quarter Close supervisor is the reference implementation. See `~/Documents/Cursor/Documents/fqc_arr_agentic_architecture_validation_report.md` for the full audit with evidence.

Headline result: ✅ on 7 of 8 dimensions; 12/12 on 12-Factor; OWASP no ❌ on LLM05/06/10. Verdict: UAT-ready (operational validation pending; logical validation complete).

## Companion skills (required reading)

This skill calls into the other four. Read them when you need depth:

- `agentic-architecture-patterns` — for dimension 1 (pattern fitness)
- `twelve-factor-agents` — for dimensions 2, 3, 4, 5, 6, 7
- `multi-agent-supervisor-pattern` — for dimension 3 (boundary integrity)
- `owasp-llm-top-10` — for dimension 4 (authorization safety) + security cross-check

## Output: where to write the report

Per `~/.cursor/rules/documents-output-folder.mdc`, validation reports go to:

```
~/Documents/Cursor/Documents/<agent_name>_agentic_architecture_validation_report.md
```

Name convention: `<agent_slug>_agentic_architecture_validation_report.md` (snake_case, no spaces).

## References

- `agentic-architecture-patterns` — Anthropic patterns
- `twelve-factor-agents` — production checklist
- `multi-agent-supervisor-pattern` — topology
- `owasp-llm-top-10` — security
- NIST AI RMF 1.0: <https://www.nist.gov/itl/ai-risk-[REDACTED]>
