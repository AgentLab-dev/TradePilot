# FQC-ARR human-in-the-loop gates → Sana approvals

Sana's model: a tool with `readOnlyHint=true` runs silently; a tool with `destructiveHint=true` triggers an approval card in the **Tasks inbox**. That maps 1:1 onto the FQC-ARR pause points. Nothing writes to a human-visible system without an approval.

## Gate map

| # | Pause point | Role | Triggering MCP write tool | Approval card shows | On reject |
|---|---|---|---|---|---|
| 1 | Post Jira clarification | clarifier | `fqc-jira.add_comment` (destructiveHint) | ADF preview of the consolidated questions | stop; no comment posted |
| 2 | Push branch + open PR | pr-author | `fqc-github.push_branch`, `fqc-github.create_pr` | PR title, body, base, reviewers, diff summary | stop; branch stays local |
| 3 | Pin Slack channel | supervisor (config) | — (one-time config) | channel picker | uses no channel; heartbeats off |
| 4 | Post QA-readiness + attach report | qa-handoff | `fqc-jira.add_comment`, `fqc-jira.add_attachment` | ADF preview + attachment name | stop; ticket not handed off |
| — | Post Bug/Debug note | debugger | `fqc-jira.add_comment` | ticket-type-shaped ADF preview | stop; note not posted |
| — | Any **prod** dbt run | quarter-close-runner / any | `fqc-dbt.run --target prod` | model selector + target=prod banner | stop; **never auto** |

## auth_mode semantics

- `smart_gates` (default): every `destructiveHint` tool raises an approval card. Reads run silently.
- `full_auto`: Sana policy pre-approves a **whitelist** of low-risk writes (e.g. `fqc-slack.notify`, `fqc-lessons.record`). **Prod dbt runs and prod Jira transitions are never pre-approved** — the hard rule is preserved regardless of auth_mode.

## Non-gated writes (deliberately)

- `fqc-github.create_branch` — creating a feature branch is low-risk and reversible; the *push* + *PR* are the gates.
- `fqc-slack.notify` / `post_thread` — status text, not a governed data write.
- `fqc-lessons.record` / `promote` / `archive` — writes only to the agent's own knowledge collection.

## Preserved hard rules (encoded in skill bodies + tool annotations)

1. No prod writes unattended — prod `fqc-dbt.run` is always gated.
2. Jira only via `fqc-jira` (token auth); never the Atlassian MCP.
3. Snowflake is read-only from the agent (`fqc-snowflake.run_query`, readOnlyHint).
4. PRs only to feature branches; never push to `qa`/`prod`.
5. Never silently edit `dbt_project.yml::arr_refactor_as_was_date_list` — surface as `needs_input`.
6. No agent self-signature in any Jira/Slack/PR/user-facing output — identifier-first.
