"""Sub-agent 10: qa-handoff.

Updates the Jira ticket for QA readiness:
- Posts a status comment with test results + CI/CD outcomes (as an ADF table).
- Attaches the pytest junit.xml and dbt target/ output if present.
- Optionally transitions the ticket to "Ready for QA".

Honors the supervisor auth mode: pauses before any Jira write unless
FULL_AUTO. Reuses the ADF table/heading/mention helpers from
``scripts/update_jira_desc.py``.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from agents.arr_quarter_close.contracts import (
    AuthMode,
    QAHandoffInput,
    QAHandoffResult,
    RoleResult,
    RoleStatus,
)

ROLE = "qa-handoff"


def plan(req: QAHandoffInput) -> dict:
    return {
        "role": ROLE,
        "qa_ticket_key": req.qa_ticket_key or req.ticket.ticket_key,
        "would_post": req.auth_mode == AuthMode.FULL_AUTO,
        "attachments": _attachment_paths(req),
        "auth_mode": req.auth_mode.value,
    }


def run(req: QAHandoffInput) -> RoleResult:
    qa_key = req.qa_ticket_key or req.ticket.ticket_key
    attachments = _attachment_paths(req)
    adf = _build_handoff_adf(req)

    result = QAHandoffResult(
        ticket_key=req.ticket.ticket_key,
        qa_ticket_key=qa_key,
        attached_artifacts=[str(p) for p in attachments],
    )

    if req.auth_mode != AuthMode.FULL_AUTO:
        return RoleResult(
            role=ROLE,
            status=RoleStatus.NEEDS_INPUT,
            summary=f"QA handoff for {qa_key} ready; awaiting approval before Jira writes.",
            payload={"qa_handoff": result.as_dict(), "adf_preview": adf},
            pause_reason="Approve to post QA-readiness comment + attach artifacts",
        )

    posted = _post_comment(qa_key, adf)
    result.comment_posted = bool(posted.get("id"))
    attached = []
    for p in attachments:
        ok = _attach_file(qa_key, p)
        if ok:
            attached.append(str(p))
    result.attached_artifacts = attached
    status = RoleStatus.OK if result.comment_posted else RoleStatus.FAIL
    return RoleResult(
        role=ROLE,
        status=status,
        summary=(
            f"Posted handoff comment + attached {len(attached)} files to {qa_key}"
            if result.comment_posted else f"Failed to post handoff to {qa_key}: {posted.get('error')}"
        ),
        payload={"qa_handoff": result.as_dict()},
    )


def _attachment_paths(req: QAHandoffInput) -> list[Path]:
    paths: list[Path] = []
    junit = req.test_report.junit_xml_path
    if junit:
        p = Path(junit)
        if p.exists():
            paths.append(p)
    dbt_target = req.test_report.dbt_target_path
    if dbt_target:
        run_results = Path(dbt_target) / "run_results.json"
        if run_results.exists():
            paths.append(run_results)
    return paths


def _build_handoff_adf(req: QAHandoffInput) -> dict:
    def text(s, strong=False):
        node = {"type": "text", "text": s}
        if strong:
            node["marks"] = [{"type": "strong"}]
        return node

    def para(*runs):
        return {"type": "paragraph", "content": list(runs)}

    def cell(s, header=False, strong=False):
        return {
            "type": "tableHeader" if header else "tableCell",
            "content": [{"type": "paragraph", "content": [text(s, strong)]}],
        }

    def row(cells):
        return {"type": "tableRow", "content": cells}

    def table(headers, rows):
        return {
            "type": "table",
            "attrs": {"isNumberColumnEnabled": False, "layout": "default"},
            "content": [row([cell(h, header=True) for h in headers])]
                       + [row([cell(c) for c in r]) for r in rows],
        }

    tr = req.test_report
    summary_rows = [
        ["pytest passed", str(tr.pytest_passed)],
        ["pytest failed", str(tr.pytest_failed)],
        ["pytest skipped", str(tr.pytest_skipped)],
        ["dbt tests run", str(len(tr.dbt_test_results))],
        ["CI final state", req.ci_report.final_state],
        ["finance_dev validated", str(req.ci_report.finance_dev_validation_passed)],
        ["CD final state", req.cd_report.final_state],
        ["finance_qa validated", str(req.cd_report.finance_qa_validation_passed)],
    ]

    # Gather every 7-column validation matrix attached upstream: test-runner,
    # ci-monitor, cd-monitor. Each becomes its own ADF table so reviewers
    # can scan a single Jira comment without leaving the ticket.
    matrix_sections: list[dict] = []
    for source_name, matrix in (
        ("test-runner",  tr.validation_matrix),
        ("ci-monitor (finance_dev)", req.ci_report.validation_matrix),
        ("cd-monitor (finance_qa)",  req.cd_report.validation_matrix),
    ):
        if not matrix or not matrix.checks:
            continue
        headers = ["Check", "Grain", "Salesforce", "Prod baseline",
                   "Dev/QA", "Expected", "Actual", "Business logic", "Verdict"]
        matrix_rows = [
            [
                c.check_name, c.grain, c.source_salesforce or "-",
                c.baseline_prod or "-", c.target_dev_qa or "-",
                c.expected or "-", c.actual or "-",
                c.business_logic, c.verdict,
            ]
            for c in matrix.checks
        ]
        matrix_sections.append({"type": "heading", "attrs": {"level": 3},
                                "content": [text(f"Validation matrix - {source_name}")]})
        matrix_sections.append(para(text(
            f"target_db={matrix.target_db}  baseline_db={matrix.baseline_db}  "
            f"source_db={matrix.source_db}  overall_verdict={matrix.overall_verdict}"
        )))
        matrix_sections.append(table(headers, matrix_rows))

    return {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                para(text("Ready for QA review.", True)),
                para(text(f"Ticket {req.ticket.ticket_key}: {req.ticket.summary}")),
                {"type": "heading", "attrs": {"level": 3},
                 "content": [text("Test + CI/CD summary")]},
                table(["Item", "Value"], summary_rows),
                *matrix_sections,
                para(text("Acceptance criteria (please verify):", True)),
                {"type": "bulletList",
                 "content": [{"type": "listItem",
                              "content": [{"type": "paragraph", "content": [text(ac)]}]}
                             for ac in req.ticket.acceptance_criteria]
                            or [{"type": "listItem",
                                 "content": [{"type": "paragraph",
                                              "content": [text("(no AC extracted - confirm with dev)")]}]}]},
            ],
        },
    }


def _post_comment(qa_key: str, adf: dict) -> dict:
    base = os.environ.get("JIRA_BASE_URL", "https://workdaybt.atlassian.net")
    email = os.environ.get("JIRA_EMAIL")
    token = os.environ.get("JIRA_API_TOKEN")
    if not email or not token:
        return {"error": "JIRA_EMAIL / JIRA_API_TOKEN not set"}
    url = f"{base}/rest/api/3/issue/{qa_key}/comment"
    proc = subprocess.run(
        ["curl", "-sS", "-u", f"{email}:{token}",
         "-X", "POST", "-H", "Content-Type: application/json",
         "--data", json.dumps(adf), url],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return {"error": f"curl exit {proc.returncode}: {proc.stderr[:200]}"}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"error": f"non-JSON response: {proc.stdout[:200]}"}


def _attach_file(qa_key: str, path: Path) -> bool:
    base = os.environ.get("JIRA_BASE_URL", "https://workdaybt.atlassian.net")
    email = os.environ.get("JIRA_EMAIL")
    token = os.environ.get("JIRA_API_TOKEN")
    if not (email and token and path.exists()):
        return False
    url = f"{base}/rest/api/3/issue/{qa_key}/attachments"
    proc = subprocess.run(
        ["curl", "-sS", "-u", f"{email}:{token}",
         "-H", "X-Atlassian-Token: no-check",
         "-X", "POST", "-F", f"file=@{path}",
         url],
        capture_output=True, text=True,
    )
    return proc.returncode == 0 and "errorMessages" not in proc.stdout
