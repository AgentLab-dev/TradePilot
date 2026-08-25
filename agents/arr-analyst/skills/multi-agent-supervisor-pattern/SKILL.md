---
name: multi-agent-supervisor-pattern
description: >-
  Design multi-agent systems using the Supervisor (Manager) topology
  popularized by LangGraph, OpenAI's Practical Guide to Building Agents,
  and Anthropic's Orchestrator-Workers pattern. Covers when to pick
  supervisor vs network vs hierarchical, how to structure sub-agent
  contracts, how to manage state across roles, pause/resume semantics,
  side-channel intervention, and concrete examples (FQC-ARR finance close).
  Use when designing a multi-agent system, choosing a topology, deciding
  whether sub-agents should communicate peer-to-peer or through a single
  orchestrator, or implementing pause points for human-in-the-loop control.
---

# Multi-Agent Supervisor Pattern

The supervisor topology is the dominant production pattern for multi-agent systems in 2024-2025. LangGraph calls it **Supervisor**, OpenAI calls it **Manager**, Anthropic calls it **Orchestrator-Workers**. They are the same shape.

## The shape

```
                    ┌───────────────────┐
                    │    SUPERVISOR     │
                    │   (control flow)  │
                    └─────────┬─────────┘
                              │ dispatches one role at a time
              ┌───────────────┼───────────────┐
              │               │               │
        ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
        │  sub-     │   │  sub-     │   │  sub-     │
        │  agent A  │   │  agent B  │   │  agent C  │
        └───────────┘   └───────────┘   └───────────┘
```

Key properties:

1. **Sub-agents never call each other.** All communication goes through the supervisor.
2. **The supervisor owns state.** Each sub-agent is a pure function of its input.
3. **The control flow is in code.** Not in an LLM prompt.
4. **Sub-agents return structured results.** The supervisor inspects status + payload and decides what's next.

## When to use this pattern

| Use Supervisor when... | Use Network instead when... |
|---|---|
| Predictability and auditability matter | Speed and adaptability matter more |
| You need pause points for human approval | The task is open-ended and exploratory |
| The DAG is mostly known in advance | Steps cannot be enumerated up front |
| Failures need clear root cause | Cascading failures are acceptable |
| Regulated domain (finance, healthcare, SOX) | Research or prototyping |
| New sub-agents added regularly | Sub-agent set is stable and small |

**Default to Supervisor for any production system.** Network and Hierarchical are advanced topologies that should be justified.

## Sub-agent contract (the most important design decision)

Every sub-agent has the same shape. This consistency is what makes the supervisor extensible.

```python
@dataclass
class RoleInput:
    """Sub-agent specific input. Typed dataclass — never free text."""
    ...

@dataclass
class RoleResult:
    role: str                           # "jira-intake", "implementer", etc.
    status: RoleStatus                  # ok / warn / fail / needs_input / skipped
    summary: str                        # one-line human summary
    payload: dict                       # typed structured output
    pause_reason: Optional[str] = None  # required when status=needs_input
    artifacts: dict = field(default_factory=dict)  # file paths, URLs

def plan(req: RoleInput) -> dict:
    """Dry-run: return what would happen. No side effects."""

def run(req: RoleInput) -> RoleResult:
    """Execute. May produce side effects (file writes, network calls)."""
```

**Why both `plan()` and `run()`:** Dry-runs are mandatory for any agent system you want to debug. Without `plan()`, the operator can't see what the agent will do before letting it do it.

## State management

State lives in a single dataclass the supervisor owns. Sub-agents read from it and produce results that get merged in. Restarting from saved state must produce identical results.

```python
@dataclass
class SupervisorState:
    role_results: list[RoleResult] = field(default_factory=list)
    # Typed intermediate payloads as separate fields, not a free-form dict
    ticket_payload: Optional[dict] = None
    requirements_payload: Optional[dict] = None
    # ... one field per sub-agent's structured output
    side_tasks: list[SideTask] = field(default_factory=list)
```

Hard rule: **the supervisor never holds in-memory state outside this object.** Otherwise resume / replay / audit breaks.

## Pause points (human-in-the-loop)

Every irreversible write must be a pause point. The supervisor returns `status=needs_input` with a structured `pause_reason`; the caller (human or upstream system) decides whether to resume.

**FQC-ARR has 4 pause points:**

| Sub-agent | Pause reason | Why |
|---|---|---|
| `clarifier` | "Approve to post clarifier comment to Jira" | Jira write |
| `pr-author` | "Approve to push branch and open PR" | git push + GitHub write |
| `qa-handoff` | "Approve to post QA-ready Jira comment with artifacts" | Final ticket write |
| `debugger` | "Approve to post Bug-shaped debug comment to EDAEM-..." | Jira write |

Pause points are also where authorization modes apply:

| Mode | Behavior |
|---|---|
| `gated_minimal` | Pauses at every write |
| `smart_gates` | Pauses at writes that change Jira / repo / production (default) |
| `gated_full` | Pauses at every sub-agent boundary |
| `full_auto` | No pauses (requires explicit operator authorization) |

## Side-channel intervention

While the supervisor is running, operators need a way to course-correct without killing the run. Slack `task:` messages are the canonical pattern.

```
operator → Slack thread: task: skip ci-monitor
                         task: pause
                         task: debug arr_line_categories
                         task: status

supervisor polls Slack thread between roles → executes recognized commands
                                            → queues free-form tasks for human/Cursor agent
                                            → posts ack to thread
```

Hard rule: side-channel polling never blocks the DAG. Polling failures (Slack timeout, missing tools) log a warning and continue.

## Adding a new sub-agent

The supervisor pattern's main virtue: adding a new sub-agent is a localized change.

```python
# 1. Define the contract
@dataclass class MyInput: ...
@dataclass class MyResult: ...

# 2. Implement the sub-agent
def plan(req): return {...}
def run(req): return RoleResult(...)

# 3. Wire into the supervisor
#    - import the module in subagents/__init__.py
#    - add to ORDER (DAG) or ON_DEMAND tuple
#    - add a dispatch helper in supervisor.py (~30 LOC)
#    - add CLI flags if needed
#    - update _ROLE_REASONS

# 4. Update docs
#    - rule (.cursor/rules/...)
#    - skill (.cursor/skills/...)
#    - README
```

Total surface area: ~600 LOC across 8 files for a non-trivial sub-agent (FQC-ARR's quarter-close-runner is the reference implementation).

## Reference implementation: FQC-ARR

The Finance ARR Quarter Close supervisor (`agents/arr_quarter_close/` in eda-dbt-em) is a production-grade reference. It runs 10 DAG sub-agents + 2 on-demand sub-agents:

```
ticket mode DAG:
  jira-intake → requirements-analyzer → code-data-validator
             → clarifier (PAUSE) → implementer → test-runner
             → pr-author (PAUSE) → ci-monitor → cd-monitor
             → qa-handoff (PAUSE)

on-demand (outside the DAG):
  debugger              — auto-dispatched on FAIL, or via task: debug
  quarter-close-runner  — dispatched via --quarter-close or task: quarter-close
```

See `.cursor/skills/arr-quarter-close/supervisor.md` for the full reference.

## Anti-patterns

| Anti-pattern | Symptom | Fix |
|---|---|---|
| **Supervisor doing "one more thing"** | Supervisor.py grows past ~1500 LOC; mixed responsibilities | Move the new thing into a sub-agent. The supervisor only orchestrates. |
| **Sub-agents talking to each other** | Sub-agent A imports sub-agent B and calls it | Add a new role in the DAG; route B through the supervisor. |
| **Implicit state mutation** | Resume produces different results from initial run | Audit `SupervisorState`; move any in-process state into the dataclass. |
| **LLM-driven routing in the supervisor** | "Why did it skip step 5?" requires reading an LLM trace | Move the routing logic into code; LLM consulted at leaves only. |
| **No pause points** | Agent posts to prod and you only find out from Slack | Add `RoleStatus.NEEDS_INPUT` at every write; smart-gate by default. |
| **Side-channel polling blocks the DAG** | A Slack outage hangs the agent for 30 seconds per role | Always wrap polling in try/except with a short timeout. |

## Companion skills

- `agentic-architecture-patterns` — pick Supervisor vs Network vs Hierarchical first
- `twelve-factor-agents` — 12 production-grade properties any Supervisor agent should satisfy
- `owasp-llm-top-10` — security boundaries (LLM06 maps directly to pause points)
- `agentic-architecture-validator` — full 8-dimension audit

## References

- **LangGraph Multi-Agent Systems**: <https://langchain-ai.github.io/langgraph/concepts/multi_agent/>
- **OpenAI Practical Guide to Building Agents** (Manager Pattern): <https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf>
- **Anthropic Orchestrator-Workers**: <https://www.anthropic.com/research/building-effective-agents>
- **FQC-ARR reference** (this workspace): `agents/arr_quarter_close/` + `.cursor/skills/arr-quarter-close/`
