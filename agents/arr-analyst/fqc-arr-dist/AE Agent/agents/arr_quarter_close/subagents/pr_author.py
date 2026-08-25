"""Sub-agent 7: pr-author.

Pushes the branch and opens a PR via ``gh``, picks reviewers from CODEOWNERS
plus the recent-PR pattern, and applies the standard PR template.

Hard rule from the supervisor: do NOT push or open the PR in any auth mode
except FULL_AUTO without an explicit approval pause. The PR shape (title,
body, reviewers, labels) is computed deterministically here and returned in
``payload`` so the user can review before approving.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections import Counter
from pathlib import Path

from agents.arr_quarter_close.contracts import (
    AuthMode,
    PRInput,
    PRResult,
    RoleResult,
    RoleStatus,
)

ROLE = "pr-author"


def plan(req: PRInput) -> dict:
    return {
        "role": ROLE,
        "branch": req.implementation.branch_name,
        "base": req.base_branch,
        "title": _pr_title(req),
        "body_preview": _pr_body(req)[:500],
        "reviewers": _pick_reviewers(Path(".").resolve()),
        "labels": _pick_labels(req),
        "draft": req.draft,
        "auth_mode": req.auth_mode.value,
        "would_push": req.auth_mode == AuthMode.FULL_AUTO,
    }


def run(req: PRInput) -> RoleResult:
    project_dir = Path(".").resolve()
    branch = req.implementation.branch_name
    title = _pr_title(req)
    body = _pr_body(req)
    reviewers = _pick_reviewers(project_dir)
    labels = _pick_labels(req)

    result = PRResult(
        ticket_key=req.ticket.ticket_key,
        branch_name=branch,
        reviewers=reviewers,
        labels=labels,
    )

    if req.auth_mode != AuthMode.FULL_AUTO:
        return RoleResult(
            role=ROLE,
            status=RoleStatus.NEEDS_INPUT,
            summary="PR draft ready; awaiting approval before push + gh pr create.",
            payload={"pr": result.as_dict(), "title": title, "body": body},
            pause_reason="Approve to push branch and open PR",
        )

    push = subprocess.run(
        ["git", "push", "-u", "origin", branch],
        cwd=str(project_dir), capture_output=True, text=True,
    )
    if push.returncode != 0:
        return RoleResult(
            role=ROLE,
            status=RoleStatus.FAIL,
            summary=f"git push failed: {push.stderr.strip()[:200]}",
            payload={"pr": result.as_dict()},
        )

    argv = [
        "gh", "pr", "create",
        "--base", req.base_branch,
        "--head", branch,
        "--title", title,
        "--body", body,
    ]
    if req.draft:
        argv.append("--draft")
    for r in reviewers:
        argv += ["--reviewer", r]
    for l in labels:
        argv += ["--label", l]

    proc = subprocess.run(argv, cwd=str(project_dir), capture_output=True, text=True)
    if proc.returncode != 0:
        return RoleResult(
            role=ROLE,
            status=RoleStatus.FAIL,
            summary=f"gh pr create failed: {proc.stderr.strip()[:200]}",
            payload={"pr": result.as_dict()},
        )
    url = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
    pr_number = _pr_number_from_url(url)
    result.pr_url = url
    result.pr_number = pr_number
    result.posted = True
    return RoleResult(
        role=ROLE,
        status=RoleStatus.OK,
        summary=f"Opened PR #{pr_number}: {url}",
        payload={"pr": result.as_dict()},
    )


def _pr_title(req: PRInput) -> str:
    return f"{req.ticket.ticket_key}: {req.ticket.summary[:80]}"


def _pr_body(req: PRInput) -> str:
    tr = req.test_report
    edits = "\n".join(f"- `{e.path}` - {e.summary}" for e in req.implementation.edits) or "- (no edits captured)"
    return f"""\
## Summary
{req.ticket.summary}

Jira: {req.ticket.raw_url or req.ticket.ticket_key}

## Changes
{edits}

## Test results (pre-CI)
- pytest: {tr.pytest_passed} passed, {tr.pytest_failed} failed, {tr.pytest_skipped} skipped
- dbt: {sum(1 for r in tr.dbt_test_results if r.get('status') == 'pass')} passed / {sum(1 for r in tr.dbt_test_results if r.get('status') == 'fail')} failed

## Acceptance criteria
{chr(10).join('- [ ] ' + ac for ac in req.ticket.acceptance_criteria) or '- (not extracted - confirm before merge)'}

## Reviewer checklist
- [ ] CTEs are named to clearly indicate the type of data they contain.
- [ ] Every SQL change paired with its .yml.
- [ ] Grain preserved; PK has unique + not_null tests.
- [ ] No hardcoded close dates; uses dbt_project.yml var.
"""


_CODEOWNER_RE = re.compile(r"@([\w./-]+/?[\w-]+)")


def _pick_reviewers(project_dir: Path) -> list[str]:
    """Pull team owners from CODEOWNERS plus most-frequent recent-PR reviewers."""
    owners: list[str] = []
    codeowners = project_dir / "CODEOWNERS"
    if codeowners.exists():
        for line in codeowners.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            owners.extend(_CODEOWNER_RE.findall(line))

    recent = _recent_pr_reviewers(project_dir)
    deduped: list[str] = []
    seen = set()
    for r in owners + recent:
        if r not in seen:
            deduped.append(r)
            seen.add(r)
    return deduped[:8]


def _recent_pr_reviewers(project_dir: Path) -> list[str]:
    proc = subprocess.run(
        ["gh", "pr", "list", "--state", "merged", "--limit", "10",
         "--json", "reviewRequests,reviews"],
        cwd=str(project_dir), capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return []
    try:
        data = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        return []
    counts: Counter[str] = Counter()
    for pr in data:
        for rr in pr.get("reviewRequests", []) or []:
            login = rr.get("login") or (rr.get("name") and rr["name"])
            if login:
                counts[login] += 1
        for rv in pr.get("reviews", []) or []:
            login = (rv.get("author") or {}).get("login")
            if login:
                counts[login] += 1
    return [login for login, _ in counts.most_common(5)]


def _pick_labels(req: PRInput) -> list[str]:
    labels = ["arr"]
    if any("test_" in e.path for e in req.implementation.edits):
        labels.append("data-quality")
    if any("scd2" in e.path for e in req.implementation.edits):
        labels.append("scd2")
    return labels


def _pr_number_from_url(url: str) -> int | None:
    m = re.search(r"/pull/(\d+)", url)
    return int(m.group(1)) if m else None
