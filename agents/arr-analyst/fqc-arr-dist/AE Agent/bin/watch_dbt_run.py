#!/usr/bin/env python3
"""watch_dbt_run.py - Watch any dbt Cloud run by id (CI, CD, refresh, ad-hoc)
and post rich progress to Slack. Same telemetry as watch_pr_ci.py but
PR-agnostic, so it works for post-merge CD jobs and ad-hoc backfills.

Usage:
    bin/watch_dbt_run.py <RUN_ID> <SLACK_CHANNEL> <LABEL>
        [--poll-minutes 5] [--max-hours 8]

Env:
    DBT_CLOUD_HOST  DBT_CLOUD_ACCOUNT_ID  DBT_CLOUD_API_TOKEN
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from watch_pr_ci import _dbt_run, _parse_progress, _short_step_name, DBT_STATUS, DBT_TERMINAL  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("run_id", type=int)
    p.add_argument("slack_channel")
    p.add_argument("label", help="Human label for the run (e.g. 'PR #472 CD (post-merge)')")
    p.add_argument("--poll-minutes", type=float, default=5.0)
    p.add_argument("--max-hours", type=float, default=6.0)
    args = p.parse_args()

    for var in ("DBT_CLOUD_HOST", "DBT_CLOUD_ACCOUNT_ID", "DBT_CLOUD_API_TOKEN"):
        if not os.environ.get(var):
            print(f"[watch_run] env var {var} missing", file=sys.stderr)
            return 64

    deadline = time.time() + args.max_hours * 3600
    iter_n = 0
    last_sig: Optional[tuple] = None
    last_post = 0.0

    while time.time() < deadline:
        iter_n += 1
        snap = _snapshot(args.run_id)
        sig = (snap["dbt_status"], snap["progress_done"], snap["current"], snap["step_index"])
        elapsed = time.time() - last_post
        if sig != last_sig or elapsed > 900:
            _post(args.slack_channel, args.label, snap, iter_n)
            last_sig = sig
            last_post = time.time()
        if snap["dbt_status"] in DBT_TERMINAL:
            _post_final(args.slack_channel, args.label, snap, iter_n)
            return 0 if snap["dbt_status"] == 10 else 2
        time.sleep(args.poll_minutes * 60)

    _post_timeout(args.slack_channel, args.label, args.max_hours, iter_n)
    return 1


def _snapshot(run_id: int) -> dict:
    snap = {
        "dbt_run_id": run_id, "dbt_run_url": None,
        "dbt_status": None, "dbt_status_name": "(unknown)",
        "step_index": None, "step_total": None, "step_name": None,
        "progress_done": 0, "progress_total": 0, "current": None,
        "errors": 0, "warnings": 0, "passed": 0, "skipped": 0,
        "elapsed": None, "branch": None, "sha": None,
    }
    try:
        run = _dbt_run(run_id)
    except Exception as e:
        snap["dbt_status_name"] = f"(fetch error: {e})"
        return snap
    host = os.environ["DBT_CLOUD_HOST"]
    aid = os.environ["DBT_CLOUD_ACCOUNT_ID"]
    snap["dbt_run_url"] = f"https://{host}/deploy/{aid}/projects/12/runs/{run_id}"
    snap["dbt_status"] = run.get("status")
    snap["dbt_status_name"] = DBT_STATUS.get(run.get("status"), str(run.get("status")))
    snap["elapsed"] = run.get("duration_humanized")
    snap["branch"] = run.get("git_branch")
    snap["sha"] = (run.get("git_sha") or "")[:8]
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


def _post(channel: str, label: str, snap: dict, iter_n: int) -> None:
    icon_map = {10: ":white_check_mark:", 20: ":x:", 30: ":no_entry_sign:"}
    icon = icon_map.get(snap["dbt_status"], ":hourglass_flowing_sand:")
    lines = [
        f"{icon} *{label}* (poll #{iter_n}) - dbt Cloud run "
        f"*<{snap['dbt_run_url']}|#{snap['dbt_run_id']}>* = `{snap['dbt_status_name']}` "
        f"(elapsed {snap['elapsed'] or '?'})"
    ]
    if snap["branch"] or snap["sha"]:
        lines.append(f"Branch `{snap['branch'] or '?'}` @ `{snap['sha'] or '?'}`")
    if snap["step_index"] and snap["step_total"]:
        lines.append(f"Step {snap['step_index']}/{snap['step_total']}: `{snap['step_name']}`")
    if snap["progress_total"]:
        lines.append(f"Progress: *{snap['progress_done']} of {snap['progress_total']}* "
                     f"({_pct(snap['progress_done'], snap['progress_total'])}%)")
    if snap["current"]:
        lines.append(f"Currently building: `{snap['current']}`")
    if any([snap["errors"], snap["warnings"], snap["passed"], snap["skipped"]]):
        lines.append(f":white_check_mark: {snap['passed']} pass  "
                     f":warning: {snap['warnings']} warn  "
                     f":x: {snap['errors']} err  "
                     f":fast_forward: {snap['skipped']} skip")
    _slk(channel, "\n".join(lines))


def _post_final(channel: str, label: str, snap: dict, iter_n: int) -> None:
    head_map = {10: ":tada: *{label}* completed", 20: ":rotating_light: *{label}* ERRORED",
                30: ":no_entry_sign: *{label}* CANCELLED"}
    head = head_map.get(snap["dbt_status"], ":grey_question: *{label}* in unexpected state").format(label=label)
    body = [f"{head} after {iter_n} polls",
            f"dbt Cloud run <{snap['dbt_run_url']}|#{snap['dbt_run_id']}> = `{snap['dbt_status_name']}` "
            f"(elapsed {snap['elapsed'] or '?'})"]
    if snap["progress_total"]:
        body.append(f"Final: {snap['progress_done']}/{snap['progress_total']} models  "
                    f":white_check_mark: {snap['passed']}  :warning: {snap['warnings']}  "
                    f":x: {snap['errors']}  :fast_forward: {snap['skipped']}")
    _slk(channel, "\n".join(body))


def _post_timeout(channel: str, label: str, max_hours: float, iter_n: int) -> None:
    _slk(channel, f":alarm_clock: *{label}* watcher timed out after {max_hours}h ({iter_n} polls).")


def _slk(channel: str, text: str) -> None:
    try:
        subprocess.run(["slk", "send", channel, text], capture_output=True, text=True, timeout=15)
    except Exception as e:
        print(f"[watch_run] slk send failed: {e}", file=sys.stderr)
    print(f"[watch_run] {datetime.now(timezone.utc).isoformat(timespec='seconds')} posted to {channel}: {text[:160]}")


def _pct(d: int, t: int) -> int:
    return int(round(100.0 * d / t)) if t else 0


if __name__ == "__main__":
    sys.exit(main())
