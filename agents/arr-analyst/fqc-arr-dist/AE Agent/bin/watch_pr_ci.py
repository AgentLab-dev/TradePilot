#!/usr/bin/env python3
"""watch_pr_ci.py - Poll a PR's GitHub `ci/dbt_cloud` status, drill into the
linked dbt Cloud run, and post rich Slack progress (e.g. "144 of 185 models
complete - currently building aggregations.arr_sku_categories").

Replaces the bash watcher when richer telemetry is needed.

Usage:
    bin/watch_pr_ci.py <PR_NUMBER> <SLACK_CHANNEL>
        [--poll-minutes 5] [--max-hours 8]
        [--check-name ci/dbt_cloud]
        [--repo workday-inc/eda-dbt-em]

Reads from env:
    DBT_CLOUD_HOST            cloud.workday.privatelink.getdbt.com
    DBT_CLOUD_ACCOUNT_ID      1
    DBT_CLOUD_API_TOKEN       (required)

Posts to Slack via the `slk` CLI (must be on PATH).
Exits 0 on terminal pass, 1 on timeout, 2 on terminal fail/error/cancelled.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Optional

PROGRESS_RE = re.compile(
    r"(\d+)\s+of\s+(\d+)\s+(START|OK|ERROR|PASS|FAIL|SKIP|WARN)\b"
    r"[^\n]*?(\S+?)\s*(?:\.{3,}|\[)"
)
TERMINAL_GITHUB_STATES = {"success", "failure", "error", "cancelled"}
# dbt Cloud JobRunStatus enum
DBT_STATUS = {1: "Queued", 2: "Starting", 3: "Running", 10: "Success", 20: "Error", 30: "Cancelled"}
DBT_TERMINAL = {10, 20, 30}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("pr_number", type=int)
    p.add_argument("slack_channel")
    p.add_argument("--poll-minutes", type=float, default=5.0)
    p.add_argument("--max-hours", type=float, default=8.0)
    p.add_argument("--check-name", default="ci/dbt_cloud")
    p.add_argument("--repo", default="workday-inc/eda-dbt-em")
    args = p.parse_args()

    for var in ("DBT_CLOUD_HOST", "DBT_CLOUD_ACCOUNT_ID", "DBT_CLOUD_API_TOKEN"):
        if not os.environ.get(var):
            print(f"[watch] env var {var} missing", file=sys.stderr)
            return 64

    pr_url = f"https://github.com/{args.repo}/pull/{args.pr_number}"
    deadline = time.time() + args.max_hours * 3600
    iter_n = 0
    last_signature: Optional[tuple] = None
    last_post_ts = 0.0

    while time.time() < deadline:
        iter_n += 1
        snap = _build_snapshot(args.repo, args.pr_number, args.check_name)
        sig = (snap["gh_state"], snap["dbt_status"], snap["progress_done"], snap["current"])
        # Throttle: post if state changed OR 15 min since last post
        elapsed = time.time() - last_post_ts
        if sig != last_signature or elapsed > 900:
            _post_slack(args.slack_channel, args.pr_number, pr_url, snap, iter_n)
            last_signature = sig
            last_post_ts = time.time()
        if snap["gh_state"] in TERMINAL_GITHUB_STATES:
            _post_final(args.slack_channel, args.pr_number, pr_url, snap, iter_n)
            return 0 if snap["gh_state"] == "success" else 2
        time.sleep(args.poll_minutes * 60)

    _post_timeout(args.slack_channel, args.pr_number, pr_url, args.max_hours, iter_n)
    return 1


def _build_snapshot(repo: str, pr_number: int, check_name: str) -> dict:
    snap = {
        "gh_state": "pending", "gh_url": None, "dbt_run_id": None,
        "dbt_status": None, "dbt_status_name": "(not started)",
        "dbt_run_url": None, "step_index": None, "step_total": None,
        "step_name": None, "progress_done": 0, "progress_total": 0,
        "current": None, "errors": 0, "warnings": 0, "passed": 0, "skipped": 0,
        "elapsed": None,
    }
    sha = _gh_pr_head_sha(repo, pr_number)
    statuses = _gh_statuses(repo, sha)
    target = None
    for s in statuses:
        if s.get("context") == check_name:
            snap["gh_state"] = s.get("state") or "pending"
            target = s.get("target_url")
            snap["gh_url"] = target
            break
    if not target:
        return snap
    # Extract dbt cloud run id from a URL like
    # https://cloud.../#/accounts/1/projects/12/runs/150998/
    m = re.search(r"/runs/(\d+)", target)
    if not m:
        return snap
    snap["dbt_run_id"] = int(m.group(1))
    snap["dbt_run_url"] = target
    try:
        run = _dbt_run(snap["dbt_run_id"])
    except Exception as e:
        snap["dbt_status_name"] = f"(fetch error: {e})"
        return snap
    snap["dbt_status"] = run.get("status")
    snap["dbt_status_name"] = DBT_STATUS.get(run.get("status"), str(run.get("status")))
    snap["elapsed"] = run.get("duration_humanized")
    steps = run.get("run_steps") or []
    if steps:
        running = [s for s in steps if s.get("status") == 3]
        last_step = running[-1] if running else steps[-1]
        snap["step_index"] = last_step.get("index")
        snap["step_total"] = len(steps)
        snap["step_name"] = _short_step_name(last_step.get("name") or "")
        logs = last_step.get("logs") or ""
        if logs:
            done, total, current, counts = _parse_progress(logs)
            snap["progress_done"] = done
            snap["progress_total"] = total
            snap["current"] = current
            snap["errors"] = counts["errors"]
            snap["warnings"] = counts["warnings"]
            snap["passed"] = counts["passed"]
            snap["skipped"] = counts["skipped"]
    return snap


def _parse_progress(logs: str) -> tuple[int, int, Optional[str], dict]:
    """Scan dbt build log lines; return (last_done, total, currently_running, counts)."""
    counts = {"errors": 0, "warnings": 0, "passed": 0, "skipped": 0}
    started, completed = {}, set()
    current = None
    total = 0
    for m in PROGRESS_RE.finditer(logs):
        idx, tot, verb, obj = m.group(1), int(m.group(2)), m.group(3), m.group(4)
        total = tot
        obj = obj.strip(".")
        if not obj or not re.search(r"[A-Za-z]", obj):
            continue
        if verb == "START":
            started[idx] = obj
        elif verb in ("OK", "PASS"):
            completed.add(idx); counts["passed"] += 1
        elif verb == "WARN":
            completed.add(idx); counts["warnings"] += 1
        elif verb in ("ERROR", "FAIL"):
            completed.add(idx); counts["errors"] += 1
        elif verb == "SKIP":
            completed.add(idx); counts["skipped"] += 1
    in_flight = [obj for idx, obj in started.items() if idx not in completed]
    current = in_flight[-1] if in_flight else (next(iter(started.values()), None) if started else None)
    return (len(completed), total, current, counts)


def _short_step_name(name: str) -> str:
    """Trim verbose step names like 'Invoke dbt with `dbt build --select state:modified+1 --exclude ...`'."""
    m = re.search(r"`(dbt\s+\w+[^`]*)`", name)
    if m:
        cmd = m.group(1)
        # truncate selector tail
        return (cmd[:60] + "...") if len(cmd) > 60 else cmd
    return name[:60]


def _post_slack(channel: str, pr_n: int, pr_url: str, snap: dict, iter_n: int) -> None:
    icon = {"success": ":white_check_mark:", "failure": ":x:", "error": ":x:",
            "cancelled": ":x:", "pending": ":hourglass_flowing_sand:"}.get(snap["gh_state"], ":grey_question:")
    lines = [f"{icon} *PR #{pr_n} CI* (poll #{iter_n}) - GitHub `{snap['gh_state']}`"]
    if snap["dbt_run_id"]:
        lines.append(f"dbt Cloud run *<{snap['dbt_run_url']}|#{snap['dbt_run_id']}>* "
                     f"= `{snap['dbt_status_name']}` (elapsed {snap['elapsed'] or '?'})")
        if snap["step_index"] and snap["step_total"]:
            lines.append(f"Step {snap['step_index']}/{snap['step_total']}: `{snap['step_name']}`")
        if snap["progress_total"]:
            lines.append(f"Progress: *{snap['progress_done']} of {snap['progress_total']}* "
                         f"({_pct(snap['progress_done'], snap['progress_total'])}%)")
        if snap["current"]:
            lines.append(f"Currently building: `{snap['current']}`")
        c = snap
        if any([c["errors"], c["warnings"], c["passed"], c["skipped"]]):
            lines.append(f":white_check_mark: {c['passed']} pass  "
                         f":warning: {c['warnings']} warn  "
                         f":x: {c['errors']} err  "
                         f":fast_forward: {c['skipped']} skip")
    lines.append(f"<{pr_url}|Open PR>")
    _slk(channel, "\n".join(lines))


def _post_final(channel: str, pr_n: int, pr_url: str, snap: dict, iter_n: int) -> None:
    if snap["gh_state"] == "success":
        head = f":tada: *PR #{pr_n}* CI passed after {iter_n} polls"
    else:
        head = f":rotating_light: *PR #{pr_n}* CI {snap['gh_state'].upper()} after {iter_n} polls"
    body = [head]
    if snap["dbt_run_id"]:
        body.append(f"dbt Cloud run <{snap['dbt_run_url']}|#{snap['dbt_run_id']}> "
                    f"= `{snap['dbt_status_name']}` (elapsed {snap['elapsed'] or '?'})")
        if snap["progress_total"]:
            c = snap
            body.append(f"Final: {c['progress_done']}/{c['progress_total']} models  "
                        f":white_check_mark: {c['passed']}  :warning: {c['warnings']}  "
                        f":x: {c['errors']}  :fast_forward: {c['skipped']}")
    body.append(f"<{pr_url}|Open PR>")
    _slk(channel, "\n".join(body))


def _post_timeout(channel: str, pr_n: int, pr_url: str, max_hours: float, iter_n: int) -> None:
    _slk(channel, f":alarm_clock: *PR #{pr_n}* watcher timed out after {max_hours}h ({iter_n} polls). <{pr_url}|Open PR>")


def _slk(channel: str, text: str) -> None:
    try:
        subprocess.run(["slk", "send", channel, text], capture_output=True, text=True, timeout=15)
    except Exception as e:
        print(f"[watch] slk send failed: {e}", file=sys.stderr)
    print(f"[watch] {datetime.now(timezone.utc).isoformat(timespec='seconds')} posted to {channel}: {text[:120]}")


def _pct(done: int, total: int) -> int:
    return int(round(100.0 * done / total)) if total else 0


def _gh_pr_head_sha(repo: str, pr: int) -> str:
    out = subprocess.run(
        ["gh", "pr", "view", str(pr), "--repo", repo, "--json", "headRefOid", "-q", ".headRefOid"],
        capture_output=True, text=True, timeout=20)
    return out.stdout.strip()


def _gh_statuses(repo: str, sha: str) -> list[dict]:
    out = subprocess.run(
        ["gh", "api", f"repos/{repo}/commits/{sha}/statuses"],
        capture_output=True, text=True, timeout=20)
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError:
        return []


def _dbt_run(run_id: int) -> dict:
    # Use curl (macOS keychain) rather than urllib - the dbt Cloud
    # PrivateLink host (cloud.workday.privatelink.getdbt.com) uses an
    # internal CA that Python's stdlib SSL doesn't trust by default.
    host = os.environ["DBT_CLOUD_HOST"]
    aid = os.environ["DBT_CLOUD_ACCOUNT_ID"]
    token = os.environ["DBT_CLOUD_API_TOKEN"]
    url = (f"https://{host}/api/v2/accounts/{aid}/runs/{run_id}/"
           "?include_related=%5B%22run_steps%22%2C%22debug_logs%22%5D")
    proc = subprocess.run(
        ["curl", "-sS", "--max-time", "25",
         "-H", f"Authorization: Token {token}", url],
        capture_output=True, text=True, timeout=30)
    if proc.returncode != 0:
        raise RuntimeError(f"curl failed rc={proc.returncode}: {proc.stderr.strip()[:200]}")
    try:
        d = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"json parse failed: {e}; first 200 chars: {proc.stdout[:200]}")
    return d.get("data") or {}


if __name__ == "__main__":
    sys.exit(main())
