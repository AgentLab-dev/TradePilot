---
name: agentic-architecture-patterns
description: >-
  Pick the right agentic-AI pattern (workflow vs agent; orchestrator-workers,
  routing, parallelization, prompt chaining, evaluator-optimizer) for a new
  AI system. Codifies Anthropic's "Building Effective Agents" (Dec 2024)
  and OpenAI's "Practical Guide to Building Agents" (2025) so design choices
  are explicit and reviewable. Use when designing any new AI agent system,
  reviewing an existing agentic design, deciding whether to use a workflow
  or a true agent, or justifying a topology choice to a reviewer.
---

# Agentic Architecture Patterns

## The first decision: workflow vs agent

Anthropic's seminal Dec 2024 paper makes this distinction the foundation:

| Type | What it is | When to use |
|---|---|---|
| **Workflow** | LLMs + tools orchestrated through **predefined code paths** | Predictability + consistency matter (regulated domains, finance, healthcare, scheduled batch jobs). The path is known in advance. |
| **Agent** | LLM **dynamically directs its own processes** + tool use, maintaining control over how it accomplishes tasks | Flexibility + model-driven decision-making at scale (open-ended research, novel problems where steps cannot be enumerated up front). |

**Default to workflows.** Anthropic's explicit recommendation: *"When building applications with LLMs, we recommend finding the simplest solution possible, and only increasing complexity when needed."*

## The 5 workflow patterns (Anthropic)

Use these as building blocks. Most production systems combine 2-3.

### 1. Prompt Chaining
Decompose a task into a sequence of LLM calls where each step's output feeds the next.

**When to use:** Task cleanly decomposes into fixed sub-tasks (e.g. "outline → draft → polish").
**Trade-off:** Higher latency for higher accuracy on each subtask.

### 2. Routing
Classify input then dispatch to specialized follow-up tasks.

**When to use:** Distinct categories of input benefit from different handling (e.g. customer support: refund vs technical vs sales → different chains/models).
**Trade-off:** Misclassification cascades; needs a clear "default" route.

### 3. Parallelization
Run sub-tasks concurrently and aggregate results.

Two flavors:
- **Sectioning** — break task into independent subtasks, run in parallel (e.g. content moderation: check toxicity + check accuracy + check tone in parallel).
- **Voting** — same task multiple times, take consensus (e.g. code review with 3 LLM passes, flag if majority agree).

**When to use:** Subtasks are independent; speed matters; you can tolerate eventual consistency.

### 4. Orchestrator-Workers
A central LLM dynamically breaks down tasks, delegates them to worker LLMs, and synthesizes their results.

**Difference from parallelization:** Sub-tasks are NOT pre-defined — orchestrator decides at runtime.
**When to use:** Complex tasks where subtasks can't be predicted in advance (e.g. coding agents that explore unfamiliar codebases).

### 5. Evaluator-Optimizer
One LLM generates a response; another evaluates and provides feedback; loop until the evaluator approves.

**When to use:** Clear evaluation criteria exist AND iterative refinement provides measurable value (e.g. literary translation, complex search synthesis).
**Trade-off:** Latency cost is high; only worth it when output quality matters more than speed.

## The two agent topologies (LangGraph + OpenAI)

When you DO need a true agent (not just a workflow), there are essentially two topologies:

### Supervisor (Manager) pattern
A single supervisor agent routes work to specialized sub-agents. Sub-agents only ever communicate with the supervisor, never with each other.

**Properties:**
- Explicit control flow (supervisor decides what runs next)
- Easy to audit, observe, pause/resume
- Easy to add new sub-agents (supervisor is the only thing that changes)
- Failure surface is small (supervisor catches everything)

**Use when:** Predictability + auditability matter (regulated domains, customer-facing systems, finance pipelines).

### Network (Decentralized) pattern
Peers hand off to each other directly.

**Properties:**
- More flexible (sub-agents can route based on local context)
- Harder to audit (control flow is emergent)
- Failure surface is wider (cascading hand-offs)
- New sub-agents require updates to every peer that might call them

**Use when:** Speed + adaptability matter more than auditability (research agents, exploratory tools).

### Hybrid: Hierarchical
Supervisor of supervisors. Each sub-supervisor manages its own worker pool.

**Use when:** The problem decomposes into clearly bounded domains and each domain is itself complex.

## Decision tree

```
Is the task path known in advance?
├── YES → Workflow
│   ├── Sequential dependent steps?  → Prompt Chaining
│   ├── Distinct input categories?   → Routing
│   ├── Independent sub-tasks?       → Parallelization (sectioning or voting)
│   ├── Unknown sub-tasks at design? → Orchestrator-Workers
│   └── Quality bar requires loop?   → Evaluator-Optimizer
│
└── NO → True agent
    ├── Single domain?     → Supervisor (Manager)
    ├── Multi-domain?      → Hierarchical
    └── Truly emergent?    → Network (use with extreme caution)
```

## Hybrid systems (the realistic case)

Most production systems are workflows with agentic leaves. Anthropic explicitly endorses this:

> *"Workflow at the top with agentic sub-tasks where flexibility is genuinely needed."*

A typical pattern: **Supervisor workflow + LLM-driven sub-agents at specific roles where judgment is required** (e.g. clarifier, code writer, evaluator). The supervisor is deterministic; the leaves are agentic.

This is the FQC-ARR pattern (see `.cursor/skills/arr-quarter-close/supervisor.md` for a concrete instance).

## Design principles (apply to any pattern)

1. **Simplicity first.** Start with the simplest pattern that could work. Add complexity only when you've measured a problem the simpler design can't solve.
2. **Transparency over magic.** The control flow should be readable in code, not inferred from logs.
3. **Well-designed Agent-Computer Interface (ACI).** Tools (and sub-agent contracts) should be as carefully designed as any human-facing API: clear inputs, structured outputs, explicit errors.
4. **Token-cost awareness.** Every LLM call costs money and latency. Workflows beat agents on cost; routing beats running everything.
5. **Human-in-the-loop at every write boundary.** Especially for irreversible operations (Jira posts, git pushes, prod deploys). See `twelve-factor-agents` skill, factor 7.
6. **Bounded autonomy.** Set explicit limits: max iterations, max tool calls, max cost. Unbounded agents are dangerous.

## What to do when reviewing an agentic design

1. **Name the pattern.** If you can't name it, it's likely an ad-hoc design with unclear properties. Force the author to map it to one of the 5 workflow patterns or 2 agent topologies above.
2. **Justify the choice.** Why this pattern over the alternatives? What's the trade-off accepted?
3. **Check the hybrid line.** Is the deterministic supervisor / agentic-leaf boundary explicit? Or has agentic behavior leaked into the supervisor (a smell)?
4. **Map to 12-Factor Agents.** Use the `twelve-factor-agents` skill as the checklist. A good design passes 10+ of 12.
5. **Map to OWASP LLM Top 10.** Use the `owasp-llm-top-10` skill. Especially LLM06 (excessive agency) and LLM10 (unbounded consumption).

## References

- **Anthropic — Building Effective Agents** (Schluntz & Zhang, Dec 19 2024): <https://www.anthropic.com/research/building-effective-agents>
- **OpenAI — A Practical Guide to Building Agents** (2025): <https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf>
- **LangGraph Multi-Agent docs**: <https://langchain-ai.github.io/langgraph/concepts/multi_agent/>
- **12-Factor Agents** (Dex Horthy, 2024): <https://github.com/humanlayer/12-factor-agents>

## Companion skills

- `twelve-factor-agents` — production-grade properties an agent system needs
- `multi-agent-supervisor-pattern` — deep dive on the Supervisor topology
- `owasp-llm-top-10` — security boundaries for any agentic system
- `agentic-architecture-validator` — 8-dimension rubric that uses all of the above
