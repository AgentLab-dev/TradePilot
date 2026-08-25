# Agents

Two discussion agents live in this repo.

## ssr-st

Short-term trading / options income agent.

- Skills: `agents/ssr-st/skills/`
- Commands: `agents/ssr-st/commands/`
- Workspace (docs, python, loops): `agents/ssr-st/workspace/`
- Learning log: `agents/ssr-st/workspace/Documents/agent_learning_log.md`
- Primary skill: `trading-continuous-learning`

Standing rules: defined-risk only; no credit through prints; first 15–30 minutes for catalyst debits; never force a trade; wait for the user to say **go**.

## arr-analyst

Finance ARR quarter-close agent for `eda-dbt-em`.

- Skills: `agents/arr-analyst/skills/`
- Sana port: `agents/arr-analyst/fqc-arr-sana/`
- Python dist: `agents/arr-analyst/fqc-arr-dist/`
- Supervisor: `fqc-arr-supervisor`

Standing rules: Jira via API token not Atlassian MCP; Snowflake reads only; no prod dbt unattended; no agent self-signature on Jira/Slack/PRs.
