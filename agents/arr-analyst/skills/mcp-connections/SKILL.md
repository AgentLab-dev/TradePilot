---
name: mcp-connections
description: >
  MCP connection configurations for Snowflake, dbt, Salesforce, Jira, Slack, and Sigma.
  Use when any agent needs to query Snowflake, run dbt commands, query Salesforce,
  manage Jira issues, send Slack messages, or interact with Sigma dashboards.
globs:
  - "**/*"
---

# MCP Connections — Global Configuration Guide

This skill provides all MCP (Model Context Protocol) server configurations so any
Cursor agent in any workspace can discover and use them. No secrets are stored here —
all credentials are referenced via environment variables in `~/.zshrc`.

## Quick Setup for a New Workspace

1. Copy the template: `cp ~/.cursor/skills/mcp-connections/mcp-template.json <project>/.cursor/mcp.json`
2. Edit `DBT_PROJECT_DIR` in the copied file to point to the new project's root.
3. Ensure `~/.cursor/skills/mcp-connections/snowflake_mcp_server.py` exists (or copy it).
4. Restart Cursor to pick up the new MCP servers.
5. For Slack: call the `mcp_auth` tool on first use to complete OAuth.

Alternatively, run the automated setup script:

```bash
~/.cursor/skills/mcp-connections/setup.sh /path/to/your/project
```

---

## Available Connections

| # | Server | MCP Name | Transport | Primary Tool |
|---|--------|----------|-----------|-------------|
| 1 | Snowflake | `snowflake` | stdio (Python) | `snowflake_query` |
| 2 | dbt | `dbt` | stdio (uvx) | `build`, `run`, `test`, `compile`, `show`, `list`, `parse`, `docs`, `get_lineage_dev`, `get_node_details_dev`, `search_product_docs`, `get_product_doc_pages` |
| 3 | Salesforce | `salesforce` | stdio (sf-mcp-server) | `run_soql_query`, `get_username`, `resume_tool_operation` |
| 4 | Atlassian (Jira + Confluence) | `atlassian` | Remote URL (OAuth) | Search, create/update Jira issues, create/update Confluence pages |
| 5 | Slack | `slack` | Cursor plugin (OAuth) | `mcp_auth` (then native Slack tools) |
| 6 | Sigma | `sigma` | stdio (npx) | Sigma dashboard tools |
| — | GitHub | `gh` CLI | Shell (pre-authenticated) | `gh pr create`, `gh issue`, `gh api`, `gh repo` |

---

## 1. Snowflake

Custom Python MCP server using `snowflake-connector-python` with SSO (`externalbrowser`) auth.

### Server Configuration

```json
{
  "snowflake": {
    "command": "python3",
    "args": ["<SNOWFLAKE_MCP_SERVER_PATH>"],
    "env": {
      "SNOWFLAKE_ACCOUNT": "KTAZVPL-EVB32354",
      "SNOWFLAKE_USER": "KOTESWARARAO.VENKATA@WORKDAY.COM",
      "SNOWFLAKE_AUTHENTICATOR": "externalbrowser",
      "SNOWFLAKE_ROLE": "ROLE_ANALYTICS_ENGINEER",
      "SNOWFLAKE_WAREHOUSE": "ANALYTICS_ENGINEER_WH",
      "SNOWFLAKE_DATABASE": "CERTIFIED_DEV",
      "SNOWFLAKE_SCHEMA": "FINANCE"
    }
  }
}
```

Replace `<SNOWFLAKE_MCP_SERVER_PATH>` with the absolute path to `snowflake_mcp_server.py`.
The global copy lives at `~/.cursor/skills/mcp-connections/snowflake_mcp_server.py`.

### Tool: `snowflake_query`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sql` | string | Yes | The SQL query to execute |

**Example:**

```json
{ "sql": "SELECT COUNT(*) FROM CERTIFIED_DEV.FINANCE.BT_LINE_ARR_CATEGORIES" }
```

### When to Use

- Execute ad-hoc SQL against Snowflake (DDL, DML, DQL).
- Create views, tables, or stored procedures.
- Profile data, run validation queries, check row counts.
- Investigate production data issues.

---

## 2. dbt

Uses `dbt-mcp` via `uvx` to interact with the local dbt project.

### Server Configuration

```json
{
  "dbt": {
    "command": "<UVX_PATH>",
    "args": ["dbt-mcp"],
    "env": {
      "DBT_PROJECT_DIR": "<YOUR_DBT_PROJECT_DIR>",
      "DBT_PATH": "<YOUR_DBT_PATH>"
    }
  }
}
```

| Env Var | Default Value | Description |
|---------|---------------|-------------|
| `DBT_PROJECT_DIR` | Per-workspace | Absolute path to the dbt project root |
| `DBT_PATH` | `/Users/koteswararao.venkata/Library/Python/3.13/bin/dbt` | Absolute path to the `dbt` binary |

### Tools

#### `build` — Run models + tests + seeds + snapshots in DAG order

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `selector` | string | No | Node selector (e.g., `model_name`, `model_name+`, `+model_name+`) |
| `is_full_refresh` | boolean | No | Force full rebuild of incremental models |
| `vars` | string | No | Variables as string: `"key: value"` or `"{key1: val1, key2: val2}"` |

#### `run` — Execute compiled SQL models against the target database

Same parameters as `build`.

#### `test` — Run data tests and unit tests

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `selector` | string | No | Node selector |
| `vars` | string | No | Variables as string |

#### `compile` — Generate executable SQL without running it

No parameters.

#### `show` — Execute arbitrary SQL and return results

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sql_query` | string | Yes | SQL query to run (do NOT add LIMIT in the query) |
| `limit` | integer | No | Row limit (default: 5) |

#### `list` — List resources in the dbt project

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `selector` | string | No | Node selector |
| `resource_type` | array[string] | No | Filter by types: `model`, `test`, `source`, `seed`, `snapshot`, `exposure`, `metric`, etc. |

#### `parse` — Parse and validate the dbt project

No parameters.

#### `docs` — Generate the dbt documentation website

No parameters.

#### `get_lineage_dev` — Retrieve upstream/downstream lineage from local manifest

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `unique_id` | string | Yes | Fully-qualified ID (e.g., `model.eda_dbt_em.bt_line_arr_categories`) |
| `types` | array | No | Filter: `Model`, `Source`, `Seed`, `Snapshot`, `Exposure`, `Metric`, `Test` |
| `depth` | integer | No | Traversal depth (default: 5, 0 = infinite) |

#### `get_node_details_dev` — Get detailed metadata for a dbt node

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `node_id` | string | Yes | Node name or fully-qualified ID |

#### `search_product_docs` — Search dbt documentation at docs.getdbt.com

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Search query |

#### `get_product_doc_pages` — Fetch full dbt doc pages as Markdown

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `paths` | array[string] | Yes | List of doc URLs or relative paths (max 10) |

### When to Use

- Build, test, or run specific dbt models.
- Inspect lineage and node metadata.
- Compile SQL to validate Jinja logic.
- Preview query results with `show`.
- Search official dbt documentation.

---

## 3. Salesforce

Uses `sf-mcp-server` (Salesforce CLI MCP) to interact with a Salesforce org.

### Server Configuration

```json
{
  "salesforce": {
    "command": "/opt/homebrew/bin/sf-mcp-server",
    "args": [
      "--orgs=[REDACTED_EMAIL]",
      "--toolsets=data",
      "--no-telemetry"
    ],
    "env": {}
  }
}
```

### Tools

#### `run_soql_query` — Execute SOQL queries

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | SOQL query to run |
| `usernameOrAlias` | string | Yes | Org username (e.g., `[REDACTED_EMAIL]`) or alias |
| `directory` | string | Yes | Full path to working directory |
| `useToolingApi` | boolean | No | Use Tooling API instead of standard API |

**Example:**

```json
{
  "query": "SELECT Id, Name FROM Account LIMIT 5",
  "usernameOrAlias": "[REDACTED_EMAIL]",
  "directory": "/Users/koteswararao.venkata/Documents/Cursor/eda-dbt-em"
}
```

#### `get_username` — Resolve the org username or alias

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `directory` | string | Yes | Full path to working directory |
| `defaultTargetOrg` | boolean | No | Resolve default target org |
| `defaultDevHub` | boolean | No | Resolve default DevHub org |

#### `resume_tool_operation` — Resume a long-running Salesforce operation

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `jobId` | string | Yes | Job ID to resume |
| `usernameOrAlias` | string | Yes | Org username or alias |
| `directory` | string | Yes | Full path to working directory |
| `wait` | number | No | Minutes to wait (default: 30) |

### When to Use

- Query Salesforce data (Accounts, Opportunities, Agreements, etc.).
- Validate data at the source before dbt transforms.
- Look up specific records by ID for debugging.

---

## 4. GitHub (via `gh` CLI — no MCP server needed)

GitHub operations are handled directly through the `gh` CLI, which manages
authentication automatically via `gh auth login`. No MCP server or PAT is required.
Agents use the Shell tool to run `gh` commands.

### Common Commands

| Action | Command |
|--------|---------|
| Create PR | `gh pr create --title "..." --body "..."` |
| Assign reviewers | `gh pr edit <number> --add-reviewer user1,user2` |
| List PRs | `gh pr list` |
| Check PR status | `gh pr checks <number>` |
| Create issue | `gh issue create --title "..." --body "..."` |
| Search issues | `gh issue list --search "query"` |
| View PR comments | `gh api repos/owner/repo/pulls/123/comments` |
| View repo | `gh repo view owner/repo` |

### Setup (one-time)

```bash
gh auth login
```

Follow the browser-based OAuth flow. Once authenticated, `gh` works across all
terminal sessions and Cursor agents automatically.

### When to Use

- Create pull requests and assign reviewers.
- Search for existing issues or PRs.
- Check CI/CD status of a branch.
- View PR review comments.
- Any GitHub operation from within the IDE.

---

## 5. Atlassian (Jira + Confluence)

**PREFERRED APPROACH: API token via `~/.zshrc` env vars + `curl` (no MCP OAuth needed).**

The user explicitly prefers the API-token / email approach over the OAuth MCP flow.
Always use this method first; fall back to the MCP server only if the user asks.

### Environment Variables (already set in `~/.zshrc`)

| Variable | Purpose |
|---|---|
| `JIRA_BASE_URL` | `https://workdaybt.atlassian.net` |
| `JIRA_PROJECT` | `EDAEM` (default project key) |
| `JIRA_EMAIL` | `[REDACTED_EMAIL]` (basic-auth username) |
| `JIRA_TOKEN` / `JIRA_API_TOKEN` | API token (basic-auth password) |

### Standard Pattern

```bash
source ~/.zshrc 2>/dev/null

# Get an issue
curl -s -u "$JIRA_EMAIL:$JIRA_TOKEN" -H "Accept: application/json" \
  "$JIRA_BASE_URL/rest/api/3/issue/EDAEM-3349?fields=summary,status,assignee"

# JQL search (URL-encode the JQL)
JQL='project = EDAEM AND assignee = currentUser() AND statusCategory != Done'
ENC=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$JQL")
curl -s -u "$JIRA_EMAIL:$JIRA_TOKEN" -H "Accept: application/json" \
  "$JIRA_BASE_URL/rest/api/3/search?jql=$ENC&fields=summary,status,assignee&maxResults=50"

# List available transitions for an issue
curl -s -u "$JIRA_EMAIL:$JIRA_TOKEN" -H "Accept: application/json" \
  "$JIRA_BASE_URL/rest/api/3/issue/EDAEM-3349/transitions"

# Add a comment (ADF format)
curl -s -u "$JIRA_EMAIL:$JIRA_TOKEN" -X POST \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  "$JIRA_BASE_URL/rest/api/3/issue/EDAEM-3349/comment" \
  -d '{"body":{"type":"doc","version":1,"content":[{"type":"paragraph","content":[{"type":"text","text":"Comment text here"}]}]}}'

# Transition an issue (use id from /transitions endpoint)
curl -s -u "$JIRA_EMAIL:$JIRA_TOKEN" -X POST \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  "$JIRA_BASE_URL/rest/api/3/issue/EDAEM-3349/transitions" \
  -d '{"transition":{"id":"3"}}'

# User search by name/email (returns accountId)
curl -s -u "$JIRA_EMAIL:$JIRA_TOKEN" -H "Accept: application/json" \
  "$JIRA_BASE_URL/rest/api/3/user/search?query=ritam"
```

### Common JQL Snippets

```text
# Open tickets assigned to a user
project = EDAEM AND assignee = "<accountId>" AND statusCategory != Done

# Tickets closed in last completed sprint
project = EDAEM AND sprint in closedSprints() AND statusCategory = Done

# Tickets in current sprint
project = EDAEM AND sprint in openSprints()

# Multi-assignee search
project = EDAEM AND assignee in ("<id1>", "<id2>", "<id3>")
```

### Run Permissions

Always invoke shell with `required_permissions: ["all"]` — `~/.zshrc` source and
network calls require it.

### Fallback: Atlassian Remote MCP Server (OAuth)

Only use if the user explicitly asks. Server config:

```json
{
  "atlassian": {
    "url": "https://mcp.atlassian.com/v1/mcp"
  }
}
```

Authentication is via OAuth in the browser on first use.

### Capabilities

Once authenticated, the server provides:

- **Search** — Search across Jira issues, Confluence pages, and Compass
- **Jira: Create issue** — Create new Jira tickets with fields
- **Jira: Update issue** — Update existing issue fields, status, assignee
- **Jira: Get issue** — Retrieve issue details by key (e.g., `EDAEM-3349`)
- **Confluence: Create page** — Create new Confluence pages
- **Confluence: Update page** — Edit existing Confluence pages
- **Automate** — Trigger workflows through natural language

### Setup Instructions

1. Add the `"atlassian"` entry to your `.cursor/mcp.json` (see config above).
2. Restart Cursor.
3. On first use, a browser window opens for Atlassian OAuth consent.
4. Authorize access to your Jira/Confluence workspace.
5. Tools become available for the session.

### When to Use

- Look up Jira ticket details for context on requirements.
- Create or update tickets from within the IDE.
- Search for related issues.
- Add analysis comments to tickets.
- Create or update Confluence documentation pages.

---

## 6. Slack

Uses Cursor's built-in Slack plugin with OAuth authentication.

### Server Configuration

Slack is a Cursor built-in plugin and does not require an entry in `mcp.json`. It
appears automatically as `plugin-slack-slack` in MCP server lists.

### Authentication

On first use, call the `mcp_auth` tool to complete OAuth:

```json
{ "server": "plugin-slack-slack", "toolName": "mcp_auth", "arguments": {} }
```

This opens a browser window for Slack OAuth consent. After authentication, Slack
tools become available for the session.

### When to Use

- Send messages to Slack channels.
- Post analysis results or notifications.

---

## 7. Sigma

Uses the `@getguru/sigma-mcp` npm package for Sigma dashboard interaction.

### Server Configuration

```json
{
  "sigma": {
    "command": "npx",
    "args": ["-y", "@getguru/sigma-mcp"],
    "env": {}
  }
}
```

### When to Use

- Interact with Sigma dashboards and workbooks.
- Query or inspect Sigma visualizations.

---

## Environment Variables Summary

All credentials are stored as environment variables in `~/.zshrc`. Never hardcode
secrets in `mcp.json` or skill files.

| Variable | Server | Status |
|----------|--------|--------|
| `SNOWFLAKE_ACCOUNT` | Snowflake | Set in mcp.json (can override via env) |
| `SNOWFLAKE_USER` | Snowflake | Set in mcp.json (can override via env) |
| `SNOWFLAKE_AUTHENTICATOR` | Snowflake | Set in mcp.json (default: `externalbrowser`) |
| `SNOWFLAKE_ROLE` | Snowflake | Set in mcp.json (default: `ROLE_ANALYTICS_ENGINEER`) |
| `SNOWFLAKE_WAREHOUSE` | Snowflake | Set in mcp.json (default: `ANALYTICS_ENGINEER_WH`) |
| `SNOWFLAKE_DATABASE` | Snowflake | Set in mcp.json (default: `CERTIFIED_DEV`) |
| `SNOWFLAKE_SCHEMA` | Snowflake | Set in mcp.json (default: `FINANCE`) |
| `DBT_PROJECT_DIR` | dbt | Per-workspace (must be set per project) |
| `DBT_PATH` | dbt | Set (`/Users/koteswararao.venkata/Library/Python/3.13/bin/dbt`) |
| `DBT_CLOUD_HOST` | dbt Cloud | Set in `~/.zshrc` |
| `DBT_CLOUD_ACCOUNT_ID` | dbt Cloud | Set in `~/.zshrc` |
| `DBT_CLOUD_PROJECT_ID` | dbt Cloud | Set in `~/.zshrc` |
| `DBT_CLOUD_API_TOKEN` | dbt Cloud | Set in `~/.zshrc` |

GitHub uses `gh auth login` (OAuth) — no env vars needed.
Atlassian (Jira/Confluence) and Slack also use OAuth — no env vars needed.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Snowflake browser popup but no connection | SSO token expired | Close browser tab, retry — fresh SSO prompt will appear |
| dbt tools not found | `uvx` path wrong | Verify `which uvx` and update `mcp.json` |
| dbt build fails with "no nodes selected" | Wrong `DBT_PROJECT_DIR` | Ensure env var points to the correct project root |
| Salesforce "not authorized" | Org not authenticated | Run `sf org login web -a <alias>` in terminal |
| `gh` "not logged in" | Auth expired | Run `gh auth login` in terminal and follow the OAuth flow |
| Atlassian tools not available | OAuth not completed | Restart Cursor and trigger the Atlassian server — browser OAuth prompt will appear |
| Slack tools not available | Not authenticated | Call `mcp_auth` tool for `plugin-slack-slack` server |
| MCP server not appearing in Cursor | `mcp.json` not in `.cursor/` | Copy template to `<project>/.cursor/mcp.json` and restart Cursor |
