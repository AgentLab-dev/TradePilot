---
name: twelve-factor-agents
description: >-
  12-factor checklist for production-grade agentic AI systems (Dex Horthy,
  HumanLayer, 2024). Covers natural-language-to-tool-calls, owning prompts
  and context windows, structured outputs, unified execution state,
  launch/pause/resume APIs, contacting humans with tool calls, owning
  control flow, error compaction, small focused agents, triggers from
  anywhere, and stateless-reducer design. Use when designing a new agent
  system, reviewing an agent design before sign-off, or scoring an existing
  agent against production-grade criteria.
---

# 12-Factor Agents

A checklist for agentic AI systems that need to be **production-grade**: predictable, debuggable, recoverable, and reviewable. Authored by Dex Horthy (HumanLayer) in 2024, inspired by the original 12-Factor App methodology.

The 12 factors define what separates a hobby agent (works on the demo, breaks in prod) from a system that finance / ops / security teams will sign off on.

## How to use this skill

When reviewing an agent design or implementation, work through the 12 factors below. Score each ✅ pass / ⚠️ partial / ❌ fail. A production-ready agent passes **≥ 10 of 12**. Factors 4, 7, 8, and 10 are non-negotiable for systems that write to production.

## The 12 factors

### 1. Natural-language → tool calls
The agent's job is to convert natural-language intent into structured tool calls. Tool calls are JSON, not prose.

**Pass criteria:** Every sub-agent returns a typed payload (dataclass / Pydantic / JSON schema), never free-form text consumed by the next step.

### 2. Own your prompts
Don't hide prompts inside framework abstractions. Write them in your repo, version them, test them.

**Pass criteria:** Every LLM call's prompt lives in code you can `grep` for. No "magic" prompts from a library.

### 3. Own your context window
You decide what goes in the context window — not a framework. Explicitly select / summarize / prune the history.

**Pass criteria:** Typed contracts between roles; no implicit "pass the whole conversation history" calls.

### 4. Tools = structured outputs
Tools should return structured data the agent can reason about, not free text. Errors are also structured.

**Pass criteria:** Every tool / sub-agent returns a typed result with a status field (`ok` / `warn` / `fail` / `needs_input`) and a structured payload.

### 5. Unify execution state and business state
The data the agent reasons about and the data your business cares about should be the same. Don't keep two copies that drift.

**Pass criteria:** One state object (e.g. `SupervisorState`) carries both intermediate agent state and the final business artifact (e.g. Jira ticket payload, PR URL).

### 6. Launch / pause / resume with simple APIs
The agent must be runnable, pausable, and resumable through a small, documented API. Long-running operations need explicit checkpoints.

**Pass criteria:** A single `run()` entrypoint that returns a status (`ok` / `needs_input` / `fail`); resume = call `run()` again with the externalized state.

### 7. Contact humans with tool calls
When the agent needs human input or approval, "contacting the human" should be a tool call like any other — same structured contract.

**Pass criteria:** Explicit pause points before every irreversible write (e.g. Jira comment, git push, dbt prod run). Pause = `RoleStatus.NEEDS_INPUT` with a structured `pause_reason`. Side-channel for mid-run intervention (e.g. Slack `task:` messages).

### 8. Own your control flow
Don't let the LLM decide what runs next. The control flow lives in code you can read, test, and reason about.

**Pass criteria:** The orchestrator's DAG / state machine is in Python (or equivalent), not in an LLM prompt. LLM is consulted at specific leaves, not at every routing decision.

### 9. Compact errors into context window
When something fails, summarize the failure into the next prompt — don't dump the raw stack trace. The agent should be able to recover or escalate based on a structured error.

**Pass criteria:** Exception → structured error result (exception type, message, traceback tail, actionable hint). On retry, the agent sees the summarized error, not the raw 200-line stack.

### 10. Small, focused agents
Each agent (and sub-agent) should have ONE clear responsibility. Resist the temptation to make a sub-agent "do one more thing."

**Pass criteria:** Each sub-agent fits in one module; its responsibility describable in one sentence; documented "what it does NOT do" boundary.

### 11. Trigger from anywhere
The same agent should be runnable from CLI, an HTTP endpoint, a scheduled job, an IDE, a Slack message — without forking the code.

**Pass criteria:** Core logic in a portable module (no IDE / framework imports). Adapters / runners wrap it for each trigger source.

### 12. Make your agent a stateless reducer
The agent is a pure function: `new_state = agent(prev_state, input)`. All state externalized. No hidden in-process mutation.

**Pass criteria:** Sub-agents are pure functions of their input. Supervisor state lives in a serializable dataclass. Restarting the process from saved state produces identical results.

## Scoring rubric

| Score | Meaning |
|---|---|
| **12 / 12** | Production-ready by design. Rare; usually the result of explicit 12-factor compliance from day one. |
| **10–11 / 12** | Production-ready with documented exceptions. The 1–2 misses must have a remediation plan. |
| **7–9 / 12** | Pre-production. Will work in demos but will be painful to debug, audit, or recover in incidents. |
| **< 7 / 12** | Not production-ready. Likely an ad-hoc design that hasn't been thought through. |

## Common misses and how to fix them

| Miss | Symptom | Fix |
|---|---|---|
| **Factor 3** (context window) | Token costs grow O(n²) with conversation length; agent forgets early steps | Typed contracts between sub-agents; explicit summarization at boundaries |
| **Factor 7** (humans as tool calls) | Agent posts to Jira / pushes to git without authorization | Explicit pause points with structured `pause_reason`; `auth_mode` flag |
| **Factor 8** (control flow) | "Why did it do that?" can't be answered without reading LLM trace | Move routing decisions into code; LLM at leaves only |
| **Factor 9** (error compaction) | Failed runs leave 5 MB of stack traces in logs; no recovery path | Wrap every tool call in a try/except that produces a structured error |
| **Factor 10** (small agents) | One sub-agent does 5 things; its prompt is 800 lines | Split into 5 sub-agents; each has one responsibility |
| **Factor 12** (stateless reducer) | Restart loses progress; can't replay; race conditions | Externalize all state to a serializable object; sub-agents pure functions |

## Companion skills

- `agentic-architecture-patterns` — pick the right topology BEFORE applying these factors
- `multi-agent-supervisor-pattern` — the topology this checklist works best with
- `owasp-llm-top-10` — security boundaries (factor 7 + 10 overlap with LLM06)
- `agentic-architecture-validator` — runs the full 8-dimension audit including this checklist

## Reference

- **12-Factor Agents** (Dex Horthy, HumanLayer, 2024): <https://github.com/humanlayer/12-factor-agents>
- **Original 12-Factor App** (Heroku, 2011) for the inspiration pattern: <https://12factor.net>
