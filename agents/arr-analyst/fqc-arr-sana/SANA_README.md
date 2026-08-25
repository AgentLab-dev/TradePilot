# FQC-ARR → Workday Sana — scaffolding bundle

Port of the **Finance ARR Quarter Close (FQC-ARR)** agent (supervisor + 10-role DAG + on-demand debugger/quarter-close-runner) onto **Workday Sana / Workday Build**.

**Strategy:** hybrid port — keep the proven Python DAG core; expose sub-agents as **AgentSkills** (`SANA_SKILL.md`) and tools as **custom MCP servers**; let Sana own orchestration, human-in-the-loop approvals, the Tasks inbox, knowledge, and governance.

> All files here are `SANA_`-prefixed drafts in a **self-contained bundle**. They do **not** touch the live agent's skill files in `.cursor/skills/` or `~/Library/Application Support/AE Agent/`. Full design rationale: `~/Documents/Cursor/Documents/fqc_arr_sana_migration_design.md`.

## Bundle contents

```
fqc-arr-sana/
├── SANA_README.md                          # this file
├── skills/<role>/SANA_SKILL.md             # 13 AgentSkills (supervisor + 10 roles + debugger + quarter-close-runner)
├── mcp/SANA_fqc-*.mcp.json                 # 6 custom MCP server manifests (+ SANA_README.md)
├── agent-cards/SANA_*.agent-card.json      # 13 A2A cards + _TEMPLATE + generator (SANA_generate_cards.py)
├── orchestrate/SANA_dag.orchestration.yaml # Option B: DAG-as-orchestration
├── orchestrate/SANA_hitl-gates.md          # pause-point → approval mapping
└── governance/SANA_agent-passport.md       # attestation + governance checklist
```

## Three ways the supervisor can run on Sana

| Option | How the DAG runs | Use when | Artifacts |
|---|---|---|---|
| **A. Core-as-MCP** (ship first) | Python `supervisor.py` stays behind one MCP tool; Sana calls it role-by-role, renders each `RoleResult`, gates writes. | Fastest, max reuse, lowest risk. | `SANA_SKILL.md` + all MCP manifests |
| **B. Orchestrate flow** | `_role_dag()` re-expressed as a Workday Orchestrate synchronous flow; each step = an Agent Action. | When you want the DAG itself governed/observable in Workday. | `orchestrate/SANA_dag.orchestration.yaml` |
| **C. Native A2A** | Each role is its own Sana Agent with an A2A card; supervisor delegates via A2A. | End-state; roles reusable across other agents. | `agent-cards/SANA_*.agent-card.json` |

## Rollout sequence

| Phase | Deliverable | Exit criteria |
|---|---|---|
| 0. Foundations | Stand up `fqc-snowflake` (read-only) + `fqc-jira` (read-only); register in Sana; index lessons as knowledge. | Sana reads a ticket + runs a SELECT with citations. |
| 1. Read-only POC | `jira-intake → requirements-analyzer → code-data-validator` under the supervisor (Option A). | Real EDAEM ticket → requirements skeleton + `pending` ValidationMatrix. No writes. |
| 2. First gated write | Add `clarifier` + `fqc-jira.add_comment` (destructiveHint). | Approving in Sana posts the exact ADF the Python clarifier would. |
| 3. Implement→test→PR | `implementer` (LLM) + `test-runner` + `pr-author` + `fqc-dbt`/`fqc-github`. | Feature branch + PR after approval; dev tests run. |
| 4. CI/CD/QA | `ci-monitor` + `cd-monitor` + `qa-handoff` + `fqc-slack`. | Full DAG end-to-end with 3 approval gates. |
| 5. On-demand + governance | `debugger`, `quarter-close-runner`; Agent Passport; prod policy. | Debugger on FAIL; prod dbt run blocked without approval. |
| 6. Native A2A (optional) | Split heavy roles into standalone A2A agents. | Roles reusable by other Sana agents. |

## Standards this bundle follows

- **AgentSkills** — `SKILL.md` frontmatter (`name`, `description`, optional `license`/`compatibility`/`metadata`/`allowed-tools`) + markdown body.
- **A2A Agent Card v1.0** — `protocolVersion`, `name`, `description`, `version`, `supportedInterfaces[]`, `capabilities`, `securitySchemes`, `skills[]` (+ `x-fqc-arr` extension block).
- **MCP tool annotations** — `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`.

## Status caveat

Workday Developer Agent, Agent-Ready Tools, and Agent Passport are **early access** (GA projected H2 2026). Treat manifests/cards here as templates to reconcile against final GA schemas — the *shapes* (AgentSkills, MCP annotations, A2A cards) are stable open standards. Open items to confirm with Workday are listed in `governance/SANA_agent-passport.md`.
