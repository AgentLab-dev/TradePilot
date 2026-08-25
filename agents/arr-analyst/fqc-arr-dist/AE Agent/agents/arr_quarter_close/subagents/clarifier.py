"""Sub-agent 4: clarifier.

Generates a clarification block (Markdown preview + Jira ADF payload) for
the open questions surfaced by the requirements-analyzer and the
code-data-validator. Posts to the Jira ticket only when the supervisor's
auth mode permits unattended Jira writes.
"""

from __future__ import annotations

import json
import os
import subprocess

from agents.arr_quarter_close.contracts import (
    AuthMode,
    ClarificationInput,
    ClarificationRequest,
    RoleResult,
    RoleStatus,
    resolve_default_llm_model,
)

ROLE = "clarifier"


def plan(req: ClarificationInput) -> dict:
    return {
        "role": ROLE,
        "ticket_key": req.ticket.ticket_key,
        "questions_count": len(_collect_questions(req)),
        "auth_mode": req.auth_mode.value,
        "would_post": req.auth_mode == AuthMode.FULL_AUTO,
    }


def build_clarification(req: ClarificationInput) -> ClarificationRequest | None:
    """Build the clarification payload (markdown + ADF) without posting.

    Returns ``None`` when there are no open questions. Exposed so the
    supervisor can offer a Slack ``ans:`` resolution path *before* any Jira
    write in full-auto mode (and reuse the exact same question rendering).
    """
    questions = _collect_questions(req)
    if not questions:
        return None
    markdown = _render_markdown(
        req.ticket.ticket_key, questions, req.requirements.confidence
    )
    adf = _build_adf_payload(
        req.ticket.ticket_key, questions, req.requirements.confidence
    )
    return ClarificationRequest(
        ticket_key=req.ticket.ticket_key,
        question_block_markdown=markdown,
        adf_payload=adf,
    )


def run(req: ClarificationInput) -> RoleResult:
    payload = build_clarification(req)
    if payload is None:
        return RoleResult(
            role=ROLE,
            status=RoleStatus.OK,
            summary="No open questions; clarifier skipped.",
        )

    questions = _collect_questions(req)
    adf = payload.adf_payload

    # Smart-gates / gated_full / gated_minimal -> stop before posting
    if req.auth_mode != AuthMode.FULL_AUTO:
        model = resolve_default_llm_model()
        return RoleResult(
            role=ROLE,
            status=RoleStatus.NEEDS_INPUT,
            summary=f"{len(questions)} clarifying questions ready to post; awaiting approval.",
            payload={
                "clarification": payload.as_dict(),
                "preferred_model": model,
            },
            pause_reason="Approve to post clarifier comment to Jira",
            preferred_model=model,
        )

    posted = _post_comment(req.ticket.ticket_key, adf)
    payload.posted = bool(posted.get("id"))
    payload.comment_id = posted.get("id")
    status = RoleStatus.OK if payload.posted else RoleStatus.FAIL
    return RoleResult(
        role=ROLE,
        status=status,
        summary=("Posted clarifier comment id=" + str(payload.comment_id)) if payload.posted
                else f"Failed to post clarifier comment: {posted.get('error')}",
        payload={"clarification": payload.as_dict()},
    )


def _collect_questions(req: ClarificationInput) -> list[str]:
    out: list[str] = list(req.requirements.questions)
    for kpi in req.requirements.kpis:
        out.extend(kpi.open_questions)
    for risk in req.validation.risks:
        if risk.endswith("?") or "confirm" in risk.lower() or "clarify" in risk.lower():
            out.append(risk)
    seen = set()
    deduped: list[str] = []
    for q in out:
        if q not in seen:
            deduped.append(q)
            seen.add(q)
    return deduped


def _render_markdown(ticket_key: str, questions: list[str], confidence: str) -> str:
    lines = [
        f"**Clarifications needed for {ticket_key}**  (current confidence: {confidence})",
        "",
        "Please respond inline in the next comment - I will pick up the answers and proceed.",
        "",
    ]
    for i, q in enumerate(questions, 1):
        lines.append(f"{i}. {q}")
    return "\n".join(lines)


def _build_adf_payload(ticket_key: str, questions: list[str], confidence: str) -> dict:
    def text(s, strong=False):
        node = {"type": "text", "text": s}
        if strong:
            node["marks"] = [{"type": "strong"}]
        return node

    def para(*runs):
        return {"type": "paragraph", "content": list(runs)}

    list_items = [
        {
            "type": "listItem",
            "content": [{"type": "paragraph", "content": [text(q)]}],
        }
        for q in questions
    ]
    body = {
        "type": "doc",
        "version": 1,
        "content": [
            para(text(f"Clarifications needed for {ticket_key} ", True),
                 text(f"(current confidence: {confidence})")),
            para(text("Please respond inline - I'll pick up the answers and proceed.")),
            {"type": "orderedList", "content": list_items},
        ],
    }
    return {"body": body}


def _post_comment(ticket_key: str, adf: dict) -> dict:
    base = os.environ.get("JIRA_BASE_URL", "https://workdaybt.atlassian.net")
    email = os.environ.get("JIRA_EMAIL")
    token = os.environ.get("JIRA_API_TOKEN")
    if not email or not token:
        return {"error": "JIRA_EMAIL / JIRA_API_TOKEN not set"}
    url = f"{base}/rest/api/3/issue/{ticket_key}/comment"
    proc = subprocess.run(
        [
            "curl", "-sS", "-u", f"{email}:{token}",
            "-X", "POST", "-H", "Content-Type: application/json",
            "--data", json.dumps(adf),
            url,
        ],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return {"error": f"curl exit {proc.returncode}: {proc.stderr[:200]}"}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"error": f"non-JSON response: {proc.stdout[:200]}"}
