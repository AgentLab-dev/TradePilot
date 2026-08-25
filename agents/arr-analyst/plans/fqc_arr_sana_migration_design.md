# FQC-ARR → Workday Sana — Migration Design & Build Plan

**Agent:** Finance ARR Quarter Close (FQC-ARR) — the autonomous Analytics Engineer for `eda-dbt-em`.
**Target:** Run the FQC-ARR supervisor + 10-role DAG + on-demand workers on **Workday Sana / Workday Build**.
**Strategy:** **Hybrid port** — keep the proven Python DAG core; expose sub-agents as **AgentSkills (`SKILL.md`)** and tools as **custom MCP servers**; let Sana own orchestration, human-in-the-loop approvals, the Tasks inbox, knowledge, and governance.
**Data access:** **Agent-Ready Tools** for anything Workday-governed; **custom MCP servers** for Snowflake / dbt / Sigma.
**Goal of this document:** architecture + build plan + a scaffolding bundle you can execute against once early access lands. Scaffolding lives at `~/Documents/Cursor/fqc-arr-sana/`.

> Status caveat: Workday Developer Agent, Agent-Ready Tools, and Agent Passport are **early access** (GA projected H2 2026). Treat the manifests/cards here as templates to reconcile against the final GA schemas — the *shapes* (AgentSkills, MCP tool annotations, A2A agent cards) are stable open standards and unlikely to move much.

---

## 1. Current-state recap (what we are porting)

The live agent is a **stdlib-only Python app** at `~/Library/Application Support/AE Agent/` (package `agents/arr_quarter_close/`). Key properties that make it Sana-friendly:

- **Supervisor owns the DAG.** `supervisor.py::_role_dag()` = 10 ordered roles; on-demand `debugger`, `quarter-close-runner`, `daily-reflection` run outside the DAG.
- **Sub-agents are pure + structured.** Each exposes `plan(input)->dict` and `run(input)->RoleResult`. They **never call an LLM** and **never open a Snowflake connection** — they emit a `prompt` + `preferred_model` and/or a `sql_template`, and the *caller* executes it. This is exactly the MCP + host-LLM split Sana uses.
- **Every result is typed.** `RoleResult{role, status, summary, payload, artifacts, pause_reason, preferred_model}`; `RoleStatus ∈ {ok, needs_input, warn, fail, skipped}`; `ValidationMatrix` of `ValidationCheck` rows.
- **Side effects are already isolated per tool:** Jira (curl+token), dbt Cloud (curl), GitHub (`gh`), Slack (`slk`/`node`), dbt (local CLI/orchestrator), Snowflake (MCP only).
- **Auth model:** effectively binary today — `full_auto` (writes) vs everything-else (`smart_gates`: pause before writes). Four canonical pause points: clarifier→Jira, pr-author→push/PR, ci-monitor→pick Slack channel, qa-handoff→Jira.
- **Learning loop:** JSONL lessons store (`data/lessons/*.jsonl`, `_stable.jsonl`), twice-daily `--learn`, weekly backup + lesson audit via launchd.
- **There is already a `sana_adapter.py` seam** — but it only wraps the scheduled `ARRCloseOrchestrator`, not the ticket DAG. We extend that seam to the whole supervisor.

---

## 2. Target architecture on Sana (hybrid)

```
                         ┌──────────────────────────────────────────────┐
                         │                 Workday Sana                  │
                         │  (front door · Tasks inbox · HITL approvals · │
                         │   governance · knowledge · connectors)        │
                         └───────────────┬──────────────────────────────┘
                                         │ invokes (A2A / AgentSkills)
                         ┌───────────────▼──────────────────────────────┐
                         │        fqc-arr-supervisor  (Sana Agent)        │
                         │  AgentSkill: skills/fqc-arr-supervisor         │
                         │  runtime: Python core (supervisor.py) behind   │
                         │  an MCP "orchestrator" tool OR Orchestrate flow │
                         └───────────────┬──────────────────────────────┘
        A2A / skill dispatch, one per role (supervisor owns the DAG)
   ┌──────────┬──────────┬──────────┬───────────┬──────────┬───────────┐
   ▼          ▼          ▼          ▼           ▼          ▼           ▼
 jira-    require-   code-data-  clarifier   implementer  test-     pr-author
 intake   ments      validator   (HITL)      (HITL/LLM)   runner    (HITL)
   │          │          │          │           │            │          │
   ▼          ▼          ▼          ▼           ▼            ▼          ▼
 ci-monitor  cd-monitor  qa-handoff(HITL)   [debugger]  [quarter-close-runner]
   │          │          │
   └──────────┴──────────┴──── tool calls over MCP ─────────────────────┐
                                                                        ▼
   ┌───────────────────────── Tool layer (MCP) ───────────────────────────┐
   │ Agent-Ready Tools (Workday-governed)     Custom MCP servers            │
   │  • workday finance data / org / policy    • fqc-snowflake (read-only)  │
   │  • (identity, audit, entitlements)        • fqc-dbt (build/test/CD)    │
   │                                           • fqc-jira (read + write*)   │
   │                                           • fqc-github (read + write*) │
   │                                           • fqc-slack (notify)         │
   │                                           • fqc-lessons (knowledge R/W)│
   └────────────────────────────────────────────────────────────────────┘
   (* write tools carry destructiveHint=true → Sana human-in-the-loop gate)
```

### 2.1 Three ways the supervisor can run on Sana (pick per role maturity)

| Option | How the DAG runs | Use when |
|---|---|---|
| **A. Core-as-MCP (recommended first)** | Python `supervisor.py` stays intact behind one MCP tool `run_role(role, state)`; Sana agent calls it role-by-role, rendering each `RoleResult` in the Tasks inbox and gating writes. | Fastest, maximal reuse, lowest risk. Ship here first. |
| **B. Orchestrate flow** | Re-express `_role_dag()` as a Workday **Orchestrate** synchronous orchestration; each step = an **Agent Action** (MCP tool). | When you want the DAG itself governed/observable inside Workday. |
| **C. Native multi-agent (A2A)** | Each role is its own Sana Agent with an **A2A agent card**; supervisor delegates via A2A. | End-state, when roles need independent scaling / reuse across other agents. |

The scaffolding supports all three: `SKILL.md` (A + C), MCP manifests (all), agent cards (C), Orchestrate spec (B).

---

## 3. Concept → Sana mapping (the core of the port)

| FQC-ARR concept | Sana / Workday primitive | Scaffolding artifact |
|---|---|---|
| Supervisor + `_role_dag()` | Supervisor **Sana Agent** (Option A/C) or **Orchestrate** flow (Option B) | `skills/fqc-arr-supervisor/SKILL.md`, `orchestrate/dag.orchestration.yaml`, `agent-cards/fqc-arr-supervisor.agent-card.json` |
| Each role (`jira-intake`…`qa-handoff`) | **AgentSkill** (`SKILL.md`) invoked by the supervisor; optionally its own Agent (A2A) | `skills/<role>/SKILL.md`, `agent-cards/<role>.agent-card.json` |
| `debugger`, `quarter-close-runner` | On-demand AgentSkills (not in the linear flow) | `skills/debugger/`, `skills/quarter-close-runner/` |
| Tool calls (Jira/Snowflake/dbt/gh/Slack) | **Custom MCP servers** (+ Agent-Ready Tools for Workday data) | `mcp/fqc-*.mcp.json` |
| `RoleStatus.needs_input` pause points | Sana **human-in-the-loop approval** + **Tasks inbox** card | `orchestrate/hitl-gates.md`, `destructiveHint` on write tools |
| `auth_mode` (full_auto / smart_gates) | Sana per-connector/per-tool **governance** + approval policy | `governance/agent-passport.md` |
| `ValidationMatrix` / `ValidationCheck` | Structured tool output (JSON schema) rendered in Tasks inbox | tool `outputSchema` in `mcp/fqc-snowflake.mcp.json` |
| Slack heartbeats + thinking log | Tasks inbox activity feed + `fqc-slack` MCP notify tool | `mcp/fqc-slack.mcp.json` |
| Lessons JSONL store + `--learn` | Sana **knowledge source** + `fqc-lessons` MCP (read/record/promote) | `mcp/fqc-lessons.mcp.json` |
| `slack_directory.json` (`--notify`) | Sana directory / connector identity resolution | mapped in `fqc-slack` MCP |
| Snowflake "SQL template, never connect" rule | MCP tool `readOnlyHint=true` (no HITL) returning rows | `mcp/fqc-snowflake.mcp.json` |
| Jira-only-via-curl, feature-branch-only, no-prod-unattended | MCP tool annotations + Sana approval policy + Agent Passport | `governance/agent-passport.md` |

---

## 4. Human-in-the-loop: pause points → Sana approvals

Sana's model: a tool with `readOnlyHint=true` runs silently; a tool with `destructiveHint=true` triggers an approval card in the **Tasks inbox**. That maps 1:1 onto the FQC-ARR gates:

| # | FQC-ARR pause point | Triggering MCP write tool | Sana behavior |
|---|---|---|---|
| 1 | clarifier → post Jira comment | `fqc-jira.add_comment` (`destructiveHint`) | Approval card shows ADF preview; approve → post |
| 2 | pr-author → push + open PR | `fqc-github.push_branch`, `fqc-github.create_pr` | Approval card shows title/body/reviewers |
| 3 | ci-monitor → pin Slack channel | supervisor config (one-time) | Set channel in agent config; no per-run gate |
| 4 | qa-handoff → post QA-readiness + attach | `fqc-jira.add_comment`, `fqc-jira.add_attachment` | Approval card shows ADF preview |
| — | debugger → post Bug/Debug comment | `fqc-jira.add_comment` | Approval card (ticket-type-shaped body) |
| — | quarter-close / any prod write | `fqc-dbt.run --target prod` | **Always** requires approval; never auto |

`full_auto` maps to a Sana policy that pre-approves specific read-heavy or low-risk tools; **prod dbt runs and prod Jira transitions are never auto-approved** (hard rule preserved).

---

## 5. Tool layer: MCP servers + Agent-Ready Tools

Six custom MCP servers wrap the existing side-effect code. Annotation discipline (drives Sana HITL):

| MCP server | Representative tools | `readOnlyHint` | `destructiveHint` |
|---|---|---|---|
| `fqc-snowflake` | `run_query` (SELECT only) | ✅ true | false |
| `fqc-dbt` | `dbt_build`, `dbt_test`, `dbt_run` (dev/qa) | false | false (qa) / **true (prod)** |
| `fqc-jira` | `get_issue`, `search` / `add_comment`, `transition`, `add_attachment` | reads true / writes false | writes **true** |
| `fqc-github` | `get_pr`, `pr_checks` / `push_branch`, `create_pr` | reads true / writes false | writes **true** |
| `fqc-slack` | `notify`, `post_thread` | n/a | false |
| `fqc-lessons` | `load_for`, `search` / `record`, `promote`, `archive` | reads true / writes false | writes false |

**Agent-Ready Tools** (Workday-governed) cover anything that should be read through Workday's governance/audit rather than a raw connector — e.g. finance org/policy/entitlement context. Snowflake/dbt/Sigma have no Workday-governed equivalent, so they stay as custom MCP. Governance for those is enforced by (a) `readOnlyHint` on reads, (b) approval on prod writes, (c) Agent Passport attestation.

**Reuse note:** each MCP tool is a thin shim over existing functions — e.g. `fqc-jira` wraps the same curl+token calls in `jira_intake.py`/`clarifier.py`; `fqc-snowflake.run_query` executes the `sql_template` the sub-agents already emit; `fqc-dbt` wraps `ARRCloseOrchestrator`/`test_runner`. No business logic is rewritten.

---

## 6. Knowledge & learning loop

- **Lessons store → Sana knowledge source.** Index `data/lessons/*.jsonl` + `_stable.jsonl` as a Sana knowledge collection so every role's prompt is grounded with citations (mirrors `format_lessons_for_prompt`). Writes (`record`/`promote`/`archive`) go through `fqc-lessons` MCP so the store stays the single source of truth.
- **`--learn` / weekly audit.** Keep the launchd jobs *or* move them to Sana scheduled triggers calling `fqc-lessons.reflect`. Recommendation: keep launchd for now (zero-risk), add a Sana trigger later.
- **Thinking log.** Replaced by the Tasks inbox activity trail; optionally keep the Markdown `runs/thinking/` as a debug artifact via `fqc-lessons.write_trace`.

---

## 7. LLM strategy

FQC-ARR sub-agents emit a `prompt` + `preferred_model` and pause. On Sana:

- The **Sana Agent itself is the LLM host** — it consumes the emitted prompt and runs it on the workspace model (Sana supports OpenAI/Claude selection + "extended range of LLMs" on enterprise).
- Keep `preferred_model` as a **hint** in the tool output; map FQC-ARR model slugs (`claude-opus-4-7-thinking-xhigh`, etc.) to the closest Sana-available model, with a documented fallback table.
- `requirements-analyzer` and `implementer` (the two heaviest prompt authors) stay as skills whose *body* tells the Sana agent exactly how to think; the deterministic scaffolding (branch creation, file plan) stays in the Python tool.

---

## 8. Governance, identity, safety

- **Identity:** replace machine-local creds (`~/.zshrc` Jira token, `slk` Keychain, `gh` session) with Sana connector auth (SSO/OAuth). Each MCP server declares an OAuth2 `securityScheme`; Sana holds the tokens, not the agent host.
- **Permission mirroring:** Sana mirrors the invoking user's permissions — a huge upgrade over the single-identity `U03GK3V2FQU` model. Finance users only see what they're entitled to.
- **Agent Passport:** obtain attestation before deploying any write-capable role (jira/github/dbt-prod). See `governance/agent-passport.md`.
- **Hard rules preserved verbatim** (encoded in skill bodies + tool annotations): no prod writes unattended; Jira only via token (never Atlassian MCP); Snowflake read-only from agent; feature-branch-only PRs; no silent edits to `arr_refactor_as_was_date_list`; no agent self-signatures in user-facing output.

---

## 9. Build plan / rollout sequence

| Phase | Deliverable | Exit criteria |
|---|---|---|
| **0. Foundations** | Stand up `fqc-snowflake` (read-only) + `fqc-jira` (read-only) MCP servers; register in Sana; index lessons as knowledge. | Sana can read a ticket + run a SELECT with citations. |
| **1. Read-only POC** | Ship `jira-intake → requirements-analyzer → code-data-validator` as AgentSkills under a supervisor skill (Option A). | On a real EDAEM ticket, Sana produces the requirements skeleton + a `pending` ValidationMatrix. No writes. |
| **2. First gated write** | Add `clarifier` + `fqc-jira.add_comment` (destructiveHint) → prove the Tasks-inbox approval card. | Approving in Sana posts the exact ADF comment the Python clarifier would. |
| **3. Implement→test→PR** | `implementer` (LLM in Sana) + `test-runner` + `pr-author` + `fqc-dbt`/`fqc-github`. | A feature branch + PR opens after approval; dbt tests run in dev. |
| **4. CI/CD/QA** | `ci-monitor` + `cd-monitor` + `qa-handoff`; Slack notify via `fqc-slack`. | Full DAG runs on a ticket end-to-end with 3 approval gates. |
| **5. On-demand + governance** | `debugger`, `quarter-close-runner`; Agent Passport; prod-write policy. | Debugger dispatch on FAIL; prod dbt run blocked without approval. |
| **6. Native A2A (optional)** | Split heavy roles into standalone A2A agents. | Roles reusable by other Sana agents. |

---

## 10. What's in the scaffolding bundle (`~/Documents/Cursor/fqc-arr-sana/`)

```
fqc-arr-sana/
├── README.md                       # deploy + rollout runbook
├── skills/<role>/SKILL.md          # 13 AgentSkills (supervisor + 10 roles + debugger + quarter-close-runner)
├── mcp/fqc-*.mcp.json              # 6 custom MCP server manifests + README (tool defs + annotations)
├── agent-cards/*.agent-card.json   # A2A cards: supervisor + read-only + write/HITL examples + _TEMPLATE + generator
├── orchestrate/dag.orchestration.yaml   # Option B: DAG-as-orchestration
├── orchestrate/hitl-gates.md       # pause-point → approval mapping
└── governance/agent-passport.md    # attestation + governance checklist
```

Each artifact is grounded in a real published standard: **AgentSkills** (`SKILL.md` frontmatter: `name`, `description`, optional `license`/`compatibility`/`metadata`/`allowed-tools`), **A2A Agent Card v1.0** (`name`, `description`, `version`, `supportedInterfaces[]`, `capabilities`, `securitySchemes`, `skills[]`), and **MCP tool annotations** (`readOnlyHint`, `destructiveHint`).

---

## 11. Open items to confirm with Workday (before Phase 3+)

1. Final **Agent-Ready Tools** catalog for finance — which of our reads have a governed equivalent vs. stay custom MCP.
2. Whether Sana **Orchestrate Agent Actions** (Option B) or native **A2A** (Option C) is the supported DAG pattern for a 10-step flow at GA.
3. **Agent Passport** requirements/vendors for write-capable agents.
4. Sana **model catalog** mapping for our `preferred_model` slugs.
5. dbt Cloud: does Workday expect dbt runs via an Agent-Ready Tool, or does `fqc-dbt` stay a custom MCP calling dbt Cloud's API?
