"""Sub-agent 8: ci-monitor.

Polls ``gh pr checks <PR>`` every N minutes (default 10) and posts a heart-
beat to Slack using the same shape as the prior-quarter
``monitor_pr458_slack.sh`` script. Stops when the target check name reaches
a terminal state, then optionally runs SQL validation queries against
``finance_dev`` via the Snowflake MCP (caller responsibility - we emit the
queries; the supervisor or the user runs them).
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from pathlib import Path

from agents.arr_quarter_close.contracts import (
    CIInput,
    CIReport,
    RoleResult,
    RoleStatus,
)
from agents.arr_quarter_close.subagents._validation_matrix import build_matrix

ROLE = "ci-monitor"

TERMINAL_STATES = {"pass", "fail", "failure", "error", "cancelled", "skipping"}


def plan(req: CIInput) -> dict:
    return {
        "role": ROLE,
        "pr": req.pr_url,
        "poll_minutes": req.poll_minutes,
        "max_hours": req.max_hours,
        "check_name_pattern": req.check_name_pattern,
        "slack_channel": req.slack_channel,
        "post_ci_validation_db": req.validation_db,
        "post_ci_validation_sql_paths": req.validation_sql_paths,
        "validation_matrix_plan": {
            "matrix_name": "ci-monitor post-CI validation",
            "target_db": req.validation_db,
            "baseline_db": "finance_prod",
            "source_db": "base_prod.salesforce",
            "checks": [
                "arr_total_at_latest_snapshot",
                "line_vs_sku_rollup_parity",
                "waterfall_balance",
                "row_count_parity_vs_baseline",
            ],
            "when": "built on terminal state == pass; SQL run via Snowflake MCP",
        },
    }


def run(req: CIInput) -> RoleResult:
    if shutil.which("gh") is None:
        return RoleResult(
            role=ROLE,
            status=RoleStatus.FAIL,
            summary="gh CLI not found on PATH; install GitHub CLI.",
        )

    deadline = time.time() + req.max_hours * 3600
    iters = 0
    final_state = "timeout"
    last_url: str | None = None

    while time.time() < deadline:
        iters += 1
        state, url = _check_state(req.pr_number, req.check_name_pattern)
        last_url = url or last_url
        _post_slack_heartbeat(req.slack_channel, req.pr_url, req.pr_number, state, iters)
        if state in TERMINAL_STATES:
            final_state = "pass" if state == "pass" else "fail"
            break
        time.sleep(req.poll_minutes * 60)

    report = CIReport(
        ticket_key="",
        pr_number=req.pr_number,
        final_state=final_state,
        polls_sent=iters,
        last_status_url=last_url,
    )

    if final_state == "pass":
        # 7-column validation matrix against finance_dev vs finance_prod
        # baseline vs Salesforce source. Supervisor runs the SQL via the
        # Snowflake MCP and populates the value columns.
        report.validation_matrix = build_matrix(
            matrix_name="ci-monitor post-CI validation",
            target_db=req.validation_db,
            baseline_db="finance_prod",
        )
        if req.validation_sql_paths:
            report.validation_notes = _emit_validation_queries(
                req.validation_db, req.validation_sql_paths
            )
        report.finance_dev_validation_passed = None  # supervisor / user runs

    status = (
        RoleStatus.OK if final_state == "pass" else
        RoleStatus.WARN if final_state == "timeout" else
        RoleStatus.FAIL
    )
    return RoleResult(
        role=ROLE,
        status=status,
        summary=f"CI {final_state} after {iters} polls; last check url: {last_url}",
        payload={"ci_report": report.as_dict()},
    )


def _check_state(pr_number: int, pattern: str) -> tuple[str, str | None]:
    proc = subprocess.run(
        ["gh", "pr", "checks", str(pr_number)],
        capture_output=True, text=True,
    )
    if proc.returncode not in (0, 1):  # 1 means failing checks - still readable output
        return "unknown", None
    for line in proc.stdout.splitlines():
        if pattern in line:
            cols = line.split()
            state = cols[1] if len(cols) > 1 else ""
            url = next((c for c in cols if c.startswith("http")), None)
            return state, url
    return "pending", None


def _post_slack_heartbeat(channel: str, pr_url: str, pr_number: int, state: str, iter_n: int) -> None:
    icon = {
        "pass": ":white_check_mark:",
        "fail": ":x:", "failure": ":x:", "error": ":x:", "cancelled": ":x:",
        "pending": ":hourglass_flowing_sand:",
        "": ":hourglass_flowing_sand:",
    }.get(state, ":grey_question:")
    text = (
        f"{icon} *PR #{pr_number} CI* check `ci/dbt_cloud` = `{state or 'not-spawned'}` "
        f"(poll #{iter_n})\n<{pr_url}|PR #{pr_number}>"
    )
    if shutil.which("slk") is not None:
        subprocess.run(["slk", "send", channel, text], capture_output=True, text=True)
    else:
        # No slk; Slack MCP must handle this from the supervisor.
        print(f"[ci-monitor:slack-fallback] would post to {channel}: {text}")


def _emit_validation_queries(db: str, sql_paths: list[str]) -> list[str]:
    notes: list[str] = []
    for p in sql_paths:
        path = Path(p)
        if path.exists():
            notes.append(f"Run via Snowflake MCP against {db}: {path}")
        else:
            notes.append(f"Missing validation SQL: {p}")
    return notes


def _label_from_pr_url(url: str) -> str:
    m = re.search(r"/pull/(\d+)", url)
    return f"PR #{m.group(1)}" if m else url
