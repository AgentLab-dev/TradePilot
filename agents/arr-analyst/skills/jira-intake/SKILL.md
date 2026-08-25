---
name: jira-intake
description: Pull an EDAEM Jira ticket, flatten its Atlassian Document Format (ADF) body to text, and extract acceptance criteria, labels, components, and comments into a structured TicketSpec. Use as the first role of the FQC-ARR DAG, or whenever you need the parsed contents of an ARR/analytics-engineering Jira ticket. Read-only — no writes.
license: Proprietary-Internal
compatibility: Requires the fqc-jira MCP server (token auth). Read-only.
metadata:
  role_order: "1"
  status_values: "ok | fail"
allowed-tools: fqc-jira.get_issue
---

# jira-intake

Fetch and normalize the ticket so downstream roles work from structured fields, not raw ADF.

## Steps
1. Call `fqc-jira.get_issue(ticket_key, fields=[summary,status,assignee,reporter,issuetype,labels,components,description,comment])`.
2. Flatten the ADF `description` to plain text (headings, lists, tables, code blocks → readable text).
3. Extract **acceptance criteria** (an "Acceptance Criteria"/"AC" section, a checklist, or bullet list). Keep them as an ordered list.
4. Summarize the latest N comments (author, created, flattened body).

## Output — `payload.ticket` (TicketSpec)
`ticket_key, summary, status, assignee, reporter, issue_type, labels[], components[], description_text, acceptance_criteria[], comments[], raw_url`.
`status = ok` when a ticket payload is produced; `fail` if the ticket can't be fetched (never fabricate fields).

## Hard rules
- Read-only. Never post or transition here (that is clarifier / qa-handoff).
- Never call the Atlassian MCP — only `fqc-jira` (token auth).
