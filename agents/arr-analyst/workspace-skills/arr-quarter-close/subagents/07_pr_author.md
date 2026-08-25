# Sub-agent 7: pr-author

**Module**: `agents/arr_quarter_close/subagents/pr_author.py`
**Skill**: `split-to-prs` (PR shaping); `babysit` (post-merge follow-up)
**Inputs from repo**: `CODEOWNERS`, `pull_request_template.md`,
last 10 merged PRs (via `gh pr list ... --json`)

## Responsibility

1. Compose PR title / body / reviewers / labels deterministically.
2. Pause unless `auth_mode=full_auto`.
3. On approval: `git push -u origin <branch>` + `gh pr create`.

## Reviewer selection

Union of:

- CODEOWNERS handles (regex match on `@org/team` or `@user`).
- Top 5 most-frequent reviewers across the last 10 merged PRs.

Deduplicated, capped at 8.

## PR body

Generated from the standard template + test results + acceptance criteria
checkboxes. Title format: `EDAEM-XXXX: <ticket summary truncated to 80>`.

## Inputs

```json
{
  "ticket": <TicketSpec>,
  "implementation": <ImplementationResult>,
  "test_report": <TestReport>,
  "base_branch": "qa",
  "draft": false,
  "auth_mode": "smart_gates"
}
```

## Outputs (RoleResult)

```json
{
  "role": "pr-author",
  "status": "needs_input|ok|fail",
  "pause_reason": "Approve to push branch and open PR",
  "payload": {
    "pr": {
      "branch_name": "...",
      "pr_number": null,
      "pr_url": null,
      "reviewers": [...],
      "labels": ["arr", ...],
      "posted": false
    },
    "title": "EDAEM-3725: ...",
    "body": "## Summary\n..."
  }
}
```

## When delegated as a Cursor Task

```text
subagent_type: shell
description: "Open PR for EDAEM-XXXX"
prompt: |
  Read .cursor/skills/arr-quarter-close/subagents/07_pr_author.md.
  In auth_mode=smart_gates: print the PR draft and the gh command; do NOT
  push. In auth_mode=full_auto: push the branch and open the PR via gh.
  Return PRResult JSON.
```

## Hard rules

- Never push to `qa` or `prod` directly. Only push the feature branch.
- Never auto-merge. The PR goes through review + CI per repo policy.
- Always include the auto-detected reviewers; the user may add/remove in the
  PR UI.
