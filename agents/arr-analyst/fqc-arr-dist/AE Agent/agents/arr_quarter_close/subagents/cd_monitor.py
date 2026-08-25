"""Sub-agent 9: cd-monitor.

Polls the dbt Cloud run that CD spawns (or, if no run id is known yet, waits
for one to appear via the dbt MCP / API) and posts heartbeats to Slack. On
success, emits the finance_qa validation queries the supervisor should run
via the Snowflake MCP.

Heavy lifting reuses the prior-quarter pattern in
``.cursor/cloud-agent/monitor_dbt_run.py`` (dbt Cloud API + Snowflake +
Slack DM). Import the helpers from there if you want full execution; this
module shells out where possible to keep dependencies optional.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

from agents.arr_quarter_close.contracts import (
    CDInput,
    CDReport,
    RoleResult,
    RoleStatus,
)
from agents.arr_quarter_close.subagents._validation_matrix import build_matrix

ROLE = "cd-monitor"


def plan(req: CDInput) -> dict:
    return {
        "role": ROLE,
        "dbt_cloud_run_id": req.dbt_cloud_run_id,
        "pr_url": req.pr_url,
        "poll_minutes": req.poll_minutes,
        "max_hours": req.max_hours,
        "slack_channel": req.slack_channel,
        "validation_db": req.validation_db,
        "validation_sql_paths": req.validation_sql_paths,
        "uses": ".cursor/cloud-agent/monitor_dbt_run.py for full dbt Cloud + Snowflake + Slack flow",
        "validation_matrix_plan": {
            "matrix_name": "cd-monitor post-CD validation",
            "target_db": req.validation_db,
            "baseline_db": "finance_prod",
            "source_db": "base_prod.salesforce",
            "checks": [
                "arr_total_at_latest_snapshot",
                "line_vs_sku_rollup_parity",
                "waterfall_balance",
                "row_count_parity_vs_baseline",
            ],
            "when": "built on terminal state == success; SQL run via Snowflake MCP",
        },
    }


def run(req: CDInput) -> RoleResult:
    if not req.dbt_cloud_run_id:
        return RoleResult(
            role=ROLE,
            status=RoleStatus.NEEDS_INPUT,
            summary="No dbt Cloud run id supplied; supervisor must obtain one from the merge event.",
            pause_reason="dbt Cloud run id required before polling",
        )

    monitor_script = Path(".cursor/cloud-agent/monitor_dbt_run.py").resolve()
    if monitor_script.exists() and _has_env_for_monitor():
        return _delegate_to_monitor_script(req, monitor_script)

    deadline = time.time() + req.max_hours * 3600
    iters = 0
    final_state = "timeout"
    while time.time() < deadline:
        iters += 1
        status = _curl_dbt_run_status(req.dbt_cloud_run_id)
        _post_slack_heartbeat(req.slack_channel, req.dbt_cloud_run_id, status, iters)
        if status in {"success", "error", "cancelled"}:
            final_state = "success" if status == "success" else "error"
            break
        time.sleep(req.poll_minutes * 60)

    report = CDReport(
        ticket_key="",
        run_id=req.dbt_cloud_run_id,
        final_state=final_state,
    )
    if final_state == "success":
        # 7-column validation matrix against finance_qa vs finance_prod
        # baseline vs Salesforce source. Same shape as ci-monitor for
        # apples-to-apples comparison in the qa-handoff Jira table.
        report.validation_matrix = build_matrix(
            matrix_name="cd-monitor post-CD validation",
            target_db=req.validation_db,
            baseline_db="finance_prod",
        )
        if req.validation_sql_paths:
            report.validation_notes = [
                f"Run via Snowflake MCP against {req.validation_db}: {p}"
                for p in req.validation_sql_paths
            ]
    status = (
        RoleStatus.OK if final_state == "success" else
        RoleStatus.WARN if final_state == "timeout" else
        RoleStatus.FAIL
    )
    return RoleResult(
        role=ROLE,
        status=status,
        summary=f"CD run {req.dbt_cloud_run_id} -> {final_state} after {iters} polls",
        payload={"cd_report": report.as_dict()},
    )


def _has_env_for_monitor() -> bool:
    needed = ["DBT_CLOUD_API_TOKEN", "DBT_CLOUD_ACCOUNT_ID", "DBT_CLOUD_BASE_URL"]
    return all(os.environ.get(k) for k in needed)


def _delegate_to_monitor_script(req: CDInput, script: Path) -> RoleResult:
    argv = [
        "python", str(script),
        "--run-id", str(req.dbt_cloud_run_id),
        "--poll-interval-min", str(req.poll_minutes),
        "--max-hours", str(req.max_hours),
        "--label", f"CD run {req.dbt_cloud_run_id}",
    ]
    if req.validation_sql_paths:
        argv += ["--validation-sql", req.validation_sql_paths[0]]
    proc = subprocess.run(argv, capture_output=True, text=True)
    state = "success" if proc.returncode == 0 else ("timeout" if proc.returncode == 2 else "error")
    report = CDReport(
        ticket_key="",
        run_id=req.dbt_cloud_run_id,
        final_state=state,
    )
    if state == "success":
        report.validation_matrix = build_matrix(
            matrix_name="cd-monitor post-CD validation (delegated)",
            target_db=req.validation_db,
            baseline_db="finance_prod",
        )
    status = (
        RoleStatus.OK if state == "success" else
        RoleStatus.WARN if state == "timeout" else
        RoleStatus.FAIL
    )
    return RoleResult(
        role=ROLE,
        status=status,
        summary=f"Delegated to monitor_dbt_run.py: state={state}",
        payload={"cd_report": report.as_dict(), "stdout_tail": proc.stdout[-1000:]},
    )


def _curl_dbt_run_status(run_id: int) -> str:
    base = os.environ.get("DBT_CLOUD_BASE_URL", "").rstrip("/")
    account = os.environ.get("DBT_CLOUD_ACCOUNT_ID")
    token = os.environ.get("DBT_CLOUD_API_TOKEN")
    if not (base and account and token):
        return "unknown"
    url = f"{base}/api/v2/accounts/{account}/runs/{run_id}/"
    proc = subprocess.run(
        ["curl", "-sS", "-H", f"Authorization: Token {token}", "-H", "Accept: application/json", url],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return "unknown"
    try:
        import json
        body = json.loads(proc.stdout).get("data", {})
        if body.get("is_success"):
            return "success"
        if body.get("is_error"):
            return "error"
        if body.get("is_cancelled"):
            return "cancelled"
        if body.get("in_progress"):
            return "in_progress"
        return body.get("status_humanized", "unknown").lower()
    except Exception:
        return "unknown"


def _post_slack_heartbeat(channel: str, run_id: int, state: str, iter_n: int) -> None:
    icon = {
        "success": ":white_check_mark:",
        "error": ":x:", "cancelled": ":x:",
        "in_progress": ":hourglass_flowing_sand:",
    }.get(state, ":grey_question:")
    text = f"{icon} *CD dbt Cloud run {run_id}* -> `{state}` (poll #{iter_n})"
    if shutil.which("slk") is not None:
        subprocess.run(["slk", "send", channel, text], capture_output=True, text=True)
    else:
        print(f"[cd-monitor:slack-fallback] would post to {channel}: {text}")
