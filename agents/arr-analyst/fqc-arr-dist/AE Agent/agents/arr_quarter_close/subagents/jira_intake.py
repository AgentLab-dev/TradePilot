"""Sub-agent 1: jira-intake.

Reads a Jira ticket, flattens its ADF description to plain text, harvests
its labels / components / comments, and tries to extract bullet-style
acceptance criteria.

Honors the workspace rule ``jira-api-access.mdc``: uses ``$JIRA_BASE_URL`` +
``$JIRA_EMAIL`` + ``$JIRA_API_TOKEN`` from the environment, via ``curl``.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
from typing import Iterable

from agents.arr_quarter_close.contracts import (
    RoleResult,
    RoleStatus,
    TicketInput,
    TicketSpec,
)

ROLE = "jira-intake"


def plan(req: TicketInput) -> dict:
    base = req.base_url or os.environ.get("JIRA_BASE_URL", "https://workdaybt.atlassian.net")
    return {
        "role": ROLE,
        "ticket_key": req.ticket_key,
        "endpoint": f"{base}/rest/api/3/issue/{req.ticket_key}",
        "fields": "summary,status,assignee,reporter,labels,components,description,issuetype"
                  + (",comment" if req.include_comments else ""),
        "auth_env_vars": ["JIRA_EMAIL", "JIRA_API_TOKEN"],
    }


def run(req: TicketInput) -> RoleResult:
    email = os.environ.get("JIRA_EMAIL")
    token = os.environ.get("JIRA_API_TOKEN")
    if not email or not token:
        return RoleResult(
            role=ROLE,
            status=RoleStatus.FAIL,
            summary="JIRA_EMAIL and/or JIRA_API_TOKEN not set; see jira-api-access rule.",
        )

    base = req.base_url or os.environ.get("JIRA_BASE_URL", "https://workdaybt.atlassian.net")
    fields = "summary,status,assignee,reporter,labels,components,description,issuetype"
    if req.include_comments:
        fields += ",comment"
    if req.include_changelog:
        url = f"{base}/rest/api/3/issue/{req.ticket_key}?expand=changelog&fields={fields}"
    else:
        url = f"{base}/rest/api/3/issue/{req.ticket_key}?fields={fields}"

    argv = ["curl", "-sS", "-u", f"{email}:{token}", "-H", "Accept: application/json", url]
    proc = subprocess.run(argv, capture_output=True, text=True)
    if proc.returncode != 0:
        return RoleResult(
            role=ROLE,
            status=RoleStatus.FAIL,
            summary=f"curl exited {proc.returncode}: {proc.stderr[:200]}",
        )

    try:
        body = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return RoleResult(
            role=ROLE,
            status=RoleStatus.FAIL,
            summary=f"non-JSON response from Jira: {exc}",
        )

    if "fields" not in body:
        return RoleResult(
            role=ROLE,
            status=RoleStatus.FAIL,
            summary=f"Jira API error: {body.get('errorMessages') or body}",
        )

    f = body["fields"]
    description_text = _flatten_adf(f.get("description")) if f.get("description") else ""
    issue_type = ((f.get("issuetype") or {}).get("name") or "Story").strip() or "Story"
    spec = TicketSpec(
        ticket_key=body.get("key", req.ticket_key),
        summary=f.get("summary", ""),
        status=(f.get("status") or {}).get("name", ""),
        assignee=((f.get("assignee") or {}).get("displayName") if f.get("assignee") else None),
        reporter=((f.get("reporter") or {}).get("displayName") if f.get("reporter") else None),
        issue_type=issue_type,
        labels=list(f.get("labels", []) or []),
        components=[(c.get("name") or "") for c in (f.get("components") or [])],
        description_text=description_text,
        acceptance_criteria=_extract_acceptance_criteria(description_text),
        comments=_normalize_comments((f.get("comment") or {}).get("comments", [])) if req.include_comments else [],
        raw_url=f"{base}/browse/{body.get('key', req.ticket_key)}",
    )
    summary_line = (
        f"{spec.ticket_key} ({spec.issue_type}) "
        f"\"{spec.summary[:60]}\" status={spec.status}"
    )
    return RoleResult(
        role=ROLE,
        status=RoleStatus.OK,
        summary=summary_line,
        payload={"ticket": spec.as_dict()},
    )


_AC_HEADERS = re.compile(
    r"(acceptance\s+criteria|definition\s+of\s+done|success\s+criteria)\s*:?",
    re.IGNORECASE,
)
_BULLET_RE = re.compile(r"^\s*(?:[-*+\u2022]|\d+[.)])\s+(.+)$")


def _extract_acceptance_criteria(text: str) -> list[str]:
    if not text:
        return []
    lines = text.splitlines()
    items: list[str] = []
    in_ac = False
    for line in lines:
        if _AC_HEADERS.search(line):
            in_ac = True
            continue
        if in_ac:
            stripped = line.strip()
            if not stripped:
                if items:
                    break
                continue
            m = _BULLET_RE.match(line)
            if m:
                items.append(m.group(1).strip())
            elif stripped and not items:
                items.append(stripped)
            elif not m and items:
                break
    return items


def _flatten_adf(node: dict | list | str | None) -> str:
    """Best-effort ADF -> plain text. Preserves paragraph and bullet breaks."""
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return "\n".join(_flatten_adf(n) for n in node)
    t = node.get("type", "")
    content = node.get("content", [])
    if t == "text":
        return node.get("text", "")
    if t in {"paragraph", "heading"}:
        inner = "".join(_flatten_adf(c) for c in content)
        return inner + "\n"
    if t == "bulletList":
        return "\n".join("- " + _flatten_adf(c).strip() for c in content) + "\n"
    if t == "orderedList":
        return "\n".join(f"{i+1}. " + _flatten_adf(c).strip() for i, c in enumerate(content)) + "\n"
    if t == "listItem":
        return "".join(_flatten_adf(c) for c in content)
    if t == "hardBreak":
        return "\n"
    if t == "mention":
        return (node.get("attrs") or {}).get("text", "")
    return "".join(_flatten_adf(c) for c in content) if content else ""


def _normalize_comments(comments: Iterable[dict]) -> list[dict]:
    out: list[dict] = []
    for c in comments:
        out.append({
            "author": (c.get("author") or {}).get("displayName"),
            "created": c.get("created"),
            "body": _flatten_adf(c.get("body")),
        })
    return out
