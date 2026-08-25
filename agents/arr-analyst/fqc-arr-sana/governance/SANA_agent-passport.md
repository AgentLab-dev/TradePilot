# FQC-ARR — Agent Passport & governance checklist (Sana port)

Workday **Agent Passport** verifies an agent's safety, identity, and entitlements before it can act in the enterprise. This checklist gates deployment of any write-capable FQC-ARR role.

## Identity & auth

- [ ] Replace machine-local creds with Sana connector auth (OAuth2):
  - `~/.zshrc` `JIRA_API_TOKEN` → `fqc-jira` OAuth connector
  - `slk` Keychain session → `fqc-slack` OAuth connector
  - `gh` session → `fqc-github` OAuth connector
  - Snowflake SSO `externalbrowser` → `fqc-snowflake` OAuth connector (role `ROLE_ANALYTICS_ENGINEER`, wh `ANALYTICS_ENGINEER_WH`)
- [ ] Sana holds all tokens; the agent host holds none.
- [ ] **Permission mirroring** enabled — the agent acts as the invoking user, not a shared identity. Retires the single-identity `U03GK3V2FQU` model.

## Entitlements (least privilege per connector)

| Connector | Read scope | Write scope | Gated |
|---|---|---|---|
| fqc-snowflake | FINANCE_PROD/QA/DEV, BASE_PROD (SELECT) | none | n/a |
| fqc-jira | EDAEM issues | comment / attach / transition | ✅ all writes |
| fqc-dbt | run status, compile | build/test/run dev,qa / **run prod** | ✅ prod only |
| fqc-github | PR + checks | create_branch / push / create_pr | ✅ push + PR |
| fqc-slack | — | notify status channel | no (status only) |
| fqc-lessons | lessons collection | record/promote/archive/reflect | no (own collection) |

## Attestation gates (obtain before deploying each role)

- [ ] **Read-only roles** (jira-intake, requirements-analyzer, code-data-validator, test-runner, ci-monitor, cd-monitor) — attest read scopes; deploy first.
- [ ] **Gated-write roles** (clarifier, pr-author, qa-handoff, debugger) — attest each `destructiveHint` tool maps to a Tasks-inbox approval card before deploy.
- [ ] **Prod-capable** (quarter-close-runner) — attest prod `fqc-dbt.run` cannot execute without an explicit per-run approval; `full_auto` never pre-approves it.

## Hard rules (must remain enforceable post-port)

1. No prod writes unattended.
2. Jira only via token connector; never the Atlassian MCP.
3. Snowflake read-only from the agent.
4. Feature-branch-only PRs; never push `qa`/`prod`.
5. No silent edit of `dbt_project.yml::arr_refactor_as_was_date_list`.
6. No agent self-signature in user-facing output (Jira/Slack/PR/docstrings) — lead with the ticket/model identifier.

## Audit & observability

- [ ] Every gated approval (who/when/what) recorded in the Sana Tasks-inbox audit log.
- [ ] Every `fqc-snowflake.run_query` and `fqc-dbt` run logged with the resolved user identity.
- [ ] ValidationMatrix results attached to the qa-handoff Jira comment for traceability.
- [ ] Lessons writes traceable to the run that produced them.

## Open items to confirm with Workday

1. Final **Agent-Ready Tools** catalog for finance — which reads have a governed equivalent vs stay custom MCP.
2. Whether **Orchestrate Agent Actions** (Option B) or native **A2A** (Option C) is the supported DAG pattern at GA.
3. **Agent Passport** attestation vendors/requirements for write-capable agents.
4. Sana **model catalog** mapping for FQC-ARR `preferred_model` slugs.
5. dbt Cloud: Agent-Ready Tool vs custom `fqc-dbt` MCP calling the dbt Cloud API.
