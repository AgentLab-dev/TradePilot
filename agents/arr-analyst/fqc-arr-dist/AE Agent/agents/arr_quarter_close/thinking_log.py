"""Live append-only Markdown trace of the Finance ARR Quarter Close (FQC-ARR) supervisor.

One file per supervisor run. Every section is appended-and-flushed so the
operator can ``tail -f`` it from another terminal while the run is
executing, inspect intermediate state, and decide whether to send a
``task: ...`` Slack message to course-correct.

Design rules:

* The log is **opt-in by default** and **fail-safe** - any IO error
  disables the writer for the rest of the run; the supervisor never
  raises because of a logging failure.
* The default path is ``<project_dir>/runs/thinking/<UTC_ts>_<slug>.md``
  so multiple parallel runs never collide.
* Every write ends with ``flush() + fsync()`` so ``tail -f`` sees the
  content immediately.
* Sections are pure Markdown; no HTML, no embedded code execution.

Sections emitted per run:

1. ``header()``                - run metadata, started timestamp, links.
2. ``supervisor_decision()``   - free-form reasoning between phases.
3. ``role_start()``            - "About to run X because Y".
4. ``role_end()``              - status, summary, pause reason, payload.
5. ``side_task()``             - operator ``task:`` messages dispatched.
6. ``orchestrator_step()``     - per-dbt-step status during Mode A.
7. ``footer()``                - overall status, counts, elapsed.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


STATUS_ICON = {
    "ok": ":white_check_mark:",
    "warn": ":warning:",
    "needs_input": ":pause_button:",
    "fail": ":x:",
    "skipped": ":fast_forward:",
}


@dataclass
class ThinkingLog:
    """Append-only Markdown trace of one supervisor run.

    The writer is best-effort: missing parent dir, permission errors, or
    IO failures flip ``enabled=False`` and no exception propagates.
    """

    path: Path
    enabled: bool = True
    _writes: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        if not self.enabled:
            return
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            log.warning(
                "thinking-log: cannot create parent dir %s (%s); disabling.",
                self.path.parent, exc,
            )
            self.enabled = False

    # ------------------------------------------------------------------ header
    def header(
        self,
        *,
        display_name: str,
        mode: str,
        ticket_key: Optional[str],
        as_was_date: Optional[str],
        auth_mode: str,
        role_count: int,
        slack_channel: str,
        project_dir: str,
        aliases: tuple[str, ...] = (),
    ) -> None:
        if not self.enabled:
            return
        now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        alias_line = (
            f"| Aliases | `{', '.join(aliases)}` |\n" if aliases else ""
        )
        body = (
            f"# {display_name} - thinking log\n\n"
            f"_Live, append-only trace of every supervisor decision, role "
            f"outcome, dbt step, and side-task in this run. Tail with_ "
            f"`tail -f {self.path}` _and intervene via Slack_ `task: ...` "
            f"_messages if you need to course-correct._\n\n"
            f"| Field | Value |\n|---|---|\n"
            f"| Started (UTC) | `{now}` |\n"
            f"| Mode | `{mode}` |\n"
            f"| Ticket | `{ticket_key or '-'}` |\n"
            f"| As-was-date | `{as_was_date or '-'}` |\n"
            f"| Auth mode | `{auth_mode}` |\n"
            f"| Role count | `{role_count}` |\n"
            f"| Slack channel | `{slack_channel or '(disabled)'}` |\n"
            f"| Project dir | `{project_dir}` |\n"
            f"{alias_line}"
            f"\n---\n\n"
        )
        self._append(body)

    # ---------------------------------------------------- role start / end
    def role_start(
        self,
        role: str,
        *,
        plan_only: bool = False,
        reason: str = "",
    ) -> None:
        if not self.enabled:
            return
        ts = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        head = f"## :arrow_forward: `{role}`"
        meta = " *(dry-run plan only)*" if plan_only else ""
        body = f"{head}{meta}\n\n_Started at `{ts}` UTC._\n\n"
        if reason:
            body += f"**Why running now:** {reason}\n\n"
        self._append(body)

    def role_end(
        self,
        role: str,
        *,
        status: str,
        summary: str,
        pause_reason: Optional[str] = None,
        payload: Optional[dict] = None,
        artifacts: Optional[dict] = None,
    ) -> None:
        if not self.enabled:
            return
        icon = STATUS_ICON.get(status, ":grey_question:")
        body = f"**Result:** {icon} `{status}` - {summary or '(no summary)'}\n\n"
        if pause_reason:
            body += f"**Pause reason:** {pause_reason}\n\n"
        if artifacts:
            body += "**Artifacts:**\n"
            for name, path in artifacts.items():
                body += f"- `{name}` -> `{path}`\n"
            body += "\n"
        body += _render_validation_matrices(payload)
        body += _render_debugger_session(payload)
        body += _render_quarter_close_session(payload)
        payload_preview = _payload_preview(payload)
        if payload_preview:
            body += (
                f"<details><summary>Payload preview</summary>\n\n"
                f"```json\n{payload_preview}\n```\n\n</details>\n\n"
            )
        body += "---\n\n"
        self._append(body)

    # --------------------------------------------------------- side tasks
    def side_task(
        self,
        *,
        requester: str,
        text: str,
        action: str,
        result: str,
    ) -> None:
        if not self.enabled:
            return
        body = (
            f"### :incoming_envelope: side-task picked up from Slack\n\n"
            f"- **From:** `{requester or 'unknown'}`\n"
            f"- **Task:** {text}\n"
            f"- **Dispatched as:** `{action}`\n"
            f"- **Result:** {result}\n\n"
        )
        self._append(body)

    # ----------------------------------------------- free-form reasoning
    def supervisor_decision(self, title: str, body_md: str) -> None:
        if not self.enabled:
            return
        self._append(f"### :brain: supervisor decision - {title}\n\n{body_md.rstrip()}\n\n")

    # --------------------------------------- per-dbt-step (Mode A inline)
    def orchestrator_step(
        self,
        *,
        step_name: str,
        status: str,
        duration_s: float,
        stderr_tail: str = "",
    ) -> None:
        if not self.enabled:
            return
        icon = STATUS_ICON.get(status, ":grey_question:")
        body = (
            f"- {icon} `close:{step_name}` -> `{status}` "
            f"({duration_s:.1f}s)"
        )
        if stderr_tail:
            body += f"\n  - stderr: `{stderr_tail[:200].replace(chr(10), ' | ')}`"
        body += "\n"
        self._append(body)

    # ---------------------------------------------------------- footer
    def footer(
        self,
        *,
        overall_status: str,
        role_count: int,
        pause_count: int,
        side_task_count: int,
        elapsed_s: float,
        queued_side_tasks: Optional[list[dict]] = None,
    ) -> None:
        if not self.enabled:
            return
        now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        icon = STATUS_ICON.get(overall_status, ":grey_question:")
        body = (
            f"\n---\n\n"
            f"## :checkered_flag: Finished\n\n"
            f"| Field | Value |\n|---|---|\n"
            f"| Finished (UTC) | `{now}` |\n"
            f"| Overall status | {icon} `{overall_status}` |\n"
            f"| Roles completed | `{role_count}` |\n"
            f"| Pause points | `{pause_count}` |\n"
            f"| Side-tasks dispatched | `{side_task_count}` |\n"
            f"| Elapsed | `{elapsed_s:.1f}s` |\n"
        )
        if queued_side_tasks:
            body += "\n**Queued side-tasks for human / Cursor follow-up:**\n\n"
            for t in queued_side_tasks[:20]:
                body += (
                    f"- `{t.get('requester') or 'unknown'}`: "
                    f"{t.get('text', '')[:200]}\n"
                )
        self._append(body)

    # ----------------------------------------------------- internal IO
    def _append(self, body: str) -> None:
        try:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(body)
                f.flush()
                try:
                    os.fsync(f.fileno())
                except OSError:
                    pass
            self._writes += 1
        except OSError as exc:
            log.warning(
                "thinking-log: append to %s failed (%s); disabling.",
                self.path, exc,
            )
            self.enabled = False


def _payload_preview(payload: Optional[dict], *, max_chars: int = 2500) -> Optional[str]:
    """JSON-dump a payload for the log, truncated for readability."""
    if not payload:
        return None
    try:
        s = json.dumps(payload, indent=2, default=str, sort_keys=True)
    except (TypeError, ValueError):
        return None
    if len(s) > max_chars:
        s = s[:max_chars] + "\n... (truncated)"
    return s


def _render_validation_matrices(payload: Optional[dict]) -> str:
    """Render any ``validation_matrix`` found in the payload as a Markdown table.

    Walks the well-known payload keys (``validation``, ``test_report``,
    ``ci_report``, ``cd_report``) for a ``validation_matrix`` dict and
    emits a fenced table. Returns ``""`` if none found - the role-end
    section then prints just its summary + payload preview as before.
    """
    if not payload:
        return ""

    headers = [
        "Check", "Grain", "Salesforce", "Prod baseline",
        "Dev/QA", "Expected", "Actual", "Business logic", "Verdict",
    ]
    sections: list[str] = []
    # (payload_key, matrix_key_inside_sub, label) - debugger puts its matrix
    # at debug.stage_matrix; the other roles use sub.validation_matrix.
    for key, matrix_key, label in (
        ("validation",     "validation_matrix", "code-data-validator"),
        ("test_report",    "validation_matrix", "test-runner"),
        ("ci_report",      "validation_matrix", "ci-monitor (finance_dev)"),
        ("cd_report",      "validation_matrix", "cd-monitor (finance_qa)"),
        ("debug",          "stage_matrix",      "debugger stage-by-stage"),
        ("quarter_close",  "recon_matrix",      "quarter-close-runner (ARR recon)"),
    ):
        sub = payload.get(key)
        if not isinstance(sub, dict):
            continue
        matrix = sub.get(matrix_key)
        if not isinstance(matrix, dict):
            continue
        checks = matrix.get("checks") or []
        if not checks:
            continue
        lines = [
            f"**Validation matrix - {label}**  "
            f"(target_db=`{matrix.get('target_db', '?')}`, "
            f"baseline_db=`{matrix.get('baseline_db', '?')}`, "
            f"source_db=`{matrix.get('source_db', '?')}`, "
            f"overall_verdict=`{matrix.get('overall_verdict', '?')}`)",
            "",
            "| " + " | ".join(headers) + " |",
            "|" + "|".join(["---"] * len(headers)) + "|",
        ]
        for c in checks:
            cells = [
                _md_cell(c.get("check_name", "")),
                _md_cell(c.get("grain", "")),
                _md_cell(c.get("source_salesforce", "")),
                _md_cell(c.get("baseline_prod", "")),
                _md_cell(c.get("target_dev_qa", "")),
                _md_cell(c.get("expected", "")),
                _md_cell(c.get("actual", "")),
                _md_cell(c.get("business_logic", "")),
                _verdict_badge(c.get("verdict", "")),
            ]
            lines.append("| " + " | ".join(cells) + " |")
        sections.append("\n".join(lines) + "\n\n")
    return "".join(sections)


def _render_quarter_close_session(payload: Optional[dict]) -> str:
    """Render the quarter-close-runner's dbt pipeline step list.

    The recon matrix is already covered by ``_render_validation_matrices``;
    this function adds the pipeline-phase table so the operator sees
    every dbt step that ran, its status, and its duration. Skipped
    (returns "") when ``payload['quarter_close']`` is missing.
    """
    if not payload:
        return ""
    qc = payload.get("quarter_close")
    if not isinstance(qc, dict):
        return ""

    out: list[str] = []
    out.append(
        f"**Quarter-close session** "
        f"as_was_date=`{qc.get('as_was_date', '?')}` "
        f"baseline=`{qc.get('baseline_as_was_date') or '-'}` "
        f"target=`{qc.get('target_db', '?')}` "
        f"baseline_db=`{qc.get('baseline_db', '?')}` "
        f"recon_verdict=`{qc.get('overall_verdict', '?')}`\n\n"
    )
    steps = qc.get("pipeline_steps") or []
    if steps:
        out.append(
            f"**Pipeline phase** "
            f"(executed=`{qc.get('pipeline_executed', False)}`, "
            f"status=`{qc.get('pipeline_overall_status', '?')}`, "
            f"duration={qc.get('pipeline_duration_s', 0.0):.1f}s)\n\n"
        )
        out.append("| Step | Status | Duration | Command |\n|---|---|---|---|\n")
        for s in steps:
            out.append(
                f"| {_md_cell(s.get('step', '?'))} | "
                f"`{s.get('status', '?')}` | "
                f"{s.get('duration_s', 0.0):.1f}s | "
                f"`{_md_cell(s.get('command', ''))[:80]}` |\n"
            )
        out.append("\n")
    elif qc.get("pipeline_executed") is False:
        out.append("_Pipeline phase skipped (recon-only mode)._\n\n")
    notes = qc.get("notes") or []
    if notes:
        out.append("**Notes**\n\n")
        for n in notes:
            out.append(f"- {n}\n")
        out.append("\n")
    return "".join(out)


def _render_debugger_session(payload: Optional[dict]) -> str:
    """Render the on-demand debugger's lineage + hypotheses + fix + harness.

    Skipped (returns "") when ``payload['debug']`` is missing - the
    matrix portion is already covered by ``_render_validation_matrices``;
    this function adds the distinct debugger-only sections so the
    operator sees the root-cause reasoning, not just the stage SQL.
    """
    if not payload:
        return ""
    debug = payload.get("debug")
    if not isinstance(debug, dict):
        return ""

    out: list[str] = []
    out.append(
        f"**Debugger session** ticket=`{debug.get('ticket_key', '?')}` "
        f"issue_type=`{debug.get('issue_type', '?')}` "
        f"trigger=`{debug.get('trigger', '?')}` "
        f"target=`{debug.get('target_model', '?')}`\n\n"
    )

    lineage = debug.get("lineage") or []
    if lineage:
        out.append("**Lineage walked**\n\n")
        out.append("| Depth | Layer | Model | File | Refs |\n|---|---|---|---|---|\n")
        for n in lineage[:25]:
            out.append(
                f"| {n.get('depth')} | {n.get('layer', '?')} | "
                f"`{n.get('name', '?')}` | `{n.get('file_path') or '-'}` | "
                f"{len(n.get('refs') or [])} |\n"
            )
        if len(lineage) > 25:
            out.append(f"| ... | ... | ... | ... | _and {len(lineage) - 25} more_ |\n")
        out.append("\n")

    hyps = debug.get("hypotheses") or []
    if hyps:
        out.append("**Ranked hypotheses**\n\n")
        out.append("| # | Confidence | Hypothesis | Suggested action |\n|---|---|---|---|\n")
        for i, h in enumerate(hyps, 1):
            out.append(
                f"| {i} | {h.get('confidence', '?')} | "
                f"{_md_cell(h.get('title', ''))} | "
                f"{_md_cell(h.get('suggested_action', ''))} |\n"
            )
        out.append("\n")

    fix = debug.get("proposed_fix")
    if isinstance(fix, dict):
        out.append("**Proposed fix**\n\n")
        out.append(
            f"- File: `{fix.get('file_path', '-')}`\n"
            f"- Confidence: `{fix.get('confidence', '?')}`\n"
            f"- Summary: {_md_cell(fix.get('summary', ''))}\n\n"
        )

    harness = debug.get("pytest_harness")
    if isinstance(harness, dict):
        out.append("**Regression test harness**\n\n")
        out.append(
            f"- dbt singular test: `{harness.get('dbt_test_sql_path', '-')}`\n"
            f"- pytest wrapper: `{harness.get('pytest_path', '-')}`\n"
            f"- selector: `{harness.get('selector', '-')}`\n"
            f"- written to disk: `{harness.get('written_to_disk', False)}`\n\n"
        )

    return "".join(out)


def _md_cell(s: str) -> str:
    if not s:
        return "-"
    # Escape pipes and collapse newlines to keep the table well-formed.
    return str(s).replace("|", "\\|").replace("\n", " ")[:120]


def _verdict_badge(v: str) -> str:
    return {
        "pass": ":white_check_mark: pass",
        "fail": ":x: fail",
        "warn": ":warning: warn",
        "needs_review": ":pause_button: needs_review",
        "pending": "_pending_",
    }.get(v, v or "-")


def default_thinking_log_path(
    project_dir: Path,
    *,
    ticket_key: Optional[str],
    as_was_date: Optional[str],
) -> Path:
    """Return the canonical default path for a thinking log.

    ``<project_dir>/runs/thinking/<UTC_ts>_<slug>.md``
    """
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    slug_parts = [p for p in (ticket_key, as_was_date) if p]
    slug = "_".join(slug_parts).replace("-", "").replace(":", "") or "run"
    return Path(project_dir) / "runs" / "thinking" / f"{ts}_{slug}.md"
