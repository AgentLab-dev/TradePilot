"""Daily reflection sub-agent: turn yesterday's runs into tomorrow's lessons.

Runs at most once per UTC day (auto-triggered at the end of every supervisor
run, or on-demand via ``fqc-arr --reflect``).

What it does (deterministic, no LLM required to be present):

1. Scan ``runs/thinking/*.md`` for files modified in the last ``look_back_days``
   (default 1).
2. Extract structured signals from each role section:
   * ``fail`` / ``warn`` / ``needs_input`` outcomes -> potential ``failure`` /
     ``ambiguity`` lessons.
3. Compare against existing lessons in ``data/lessons/`` to dedupe (the
   recorder does this automatically via stable lesson IDs).
4. Record new lessons through ``LessonRecorder``.
5. Promote any lesson that crossed ``PROMOTE_AT_OCCURRENCE``.
6. Append a one-line entry to ``_reflection_log.jsonl`` so the daily
   cadence is auditable.

Why this is deterministic by default: the supervisor and LLM-driven leaf
sub-agents (requirements_analyzer, implementer) are expensive. The
reflection sub-agent should be cheap and crash-safe. When an LLM IS
available, an upstream caller can pass extra free-form lessons via
``record(role, lesson, ...)`` before invoking ``run()`` and they will be
folded into the same daily summary.

NOTE: No agent self-references in any lesson text. See
``.cursor/rules/no-agent-signatures.mdc``.
"""

from __future__ import annotations

import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from agents.arr_quarter_close.contracts import (
    ReflectionInput,
    ReflectionReport,
    RoleResult,
    RoleStatus,
)
from agents.arr_quarter_close.lessons import (
    GLOBAL_ROLE,
    KNOWN_CATEGORIES,
    LessonRecorder,
    get_recorder,
)


# ---------------------------------------------------------------------------
# Run-log scout (wide_scan only)
#
# Twice-daily scheduled passes (9am / 5pm via launchd) flip `wide_scan=True`
# so the reflection grabs lessons from sources beyond the thinking log:
#  - `runs/*.log` for Python Tracebacks + structured FAIL summaries
#    (captures crashes that happened OUTSIDE thinking-log tracking, e.g.
#    a supervisor that died before opening the log).
#
# Why not git log / Jira / PR review? Those needs creds at launchd time
# (sandboxed env) and are noisier. Kept for a later phase.
# ---------------------------------------------------------------------------

_TRACEBACK_RE = re.compile(
    r"Traceback \(most recent call last\):(?:\n.*?)+?\n([A-Z][a-zA-Z]*Error[^\n]*)",
    re.MULTILINE,
)
_FATAL_RE = re.compile(r"^\s*\[(?:error|fatal|fail)\][^\n]*", re.IGNORECASE | re.MULTILINE)


# ---------------------------------------------------------------------------
# Public API (plan / run)
# ---------------------------------------------------------------------------

def plan(req: ReflectionInput) -> dict:
    """Return the actions the daily-reflection pass would take."""
    sources = ["runs/thinking/*.md"]
    if req.wide_scan:
        sources.append("runs/*.log (Traceback + structured [error]/[fatal] lines)")
    return {
        "role": "daily-reflection",
        "look_back_days": req.look_back_days,
        "force": req.force,
        "wide_scan": req.wide_scan,
        "sources": sources,
        "approach": (
            f"Scan {'/'.join(sources)} for files modified in the last "
            f"{req.look_back_days}d. Extract FAIL/WARN/NEEDS_INPUT outcomes "
            "from each role section + (wide_scan) Python tracebacks from "
            "background run logs, bucket them as 'failure' / 'ambiguity', "
            "and write them through LessonRecorder. Dedupe is hash-based; "
            "lessons crossing occurrence_count >= 3 are promoted to _stable.jsonl."
        ),
        "writes": [
            "agents/arr_quarter_close/data/lessons/<role>.jsonl",
            "agents/arr_quarter_close/data/lessons/_global.jsonl (wide_scan crashes)",
            "agents/arr_quarter_close/data/lessons/_stable.jsonl (on promotion)",
            "agents/arr_quarter_close/data/lessons/_reflection_log.jsonl",
        ],
    }


def run(req: ReflectionInput) -> RoleResult:
    project_dir = Path(req.project_dir).resolve()
    recorder = get_recorder(project_dir)

    if recorder.reflected_today() and not req.force:
        return RoleResult(
            role="daily-reflection",
            status=RoleStatus.SKIPPED,
            summary="already reflected today (pass --reflect to force a fresh pass)",
            payload={"reflection": ReflectionReport(notes="already reflected today").as_dict()},
        )

    report = _reflect(
        project_dir,
        recorder,
        look_back_days=req.look_back_days,
        wide_scan=req.wide_scan,
    )
    recorder.log_reflection(
        lessons_added=report.lessons_added,
        lessons_promoted=report.lessons_promoted,
        lessons_archived=report.lessons_archived,
        notes=report.notes,
    )
    summary = (
        f"runs_scanned={report.runs_scanned} "
        f"lessons_added={report.lessons_added} "
        f"lessons_promoted={report.lessons_promoted}"
    )
    if report.notes:
        summary += f" - {report.notes[:120]}"
    return RoleResult(
        role="daily-reflection",
        status=RoleStatus.OK,
        summary=summary,
        payload={"reflection": report.as_dict()},
    )


# ---------------------------------------------------------------------------
# Core scan
# ---------------------------------------------------------------------------

# Match a single role section heading in the thinking log.
# Example: "## :arrow_forward: `debugger`"
_ROLE_HEADING_RE = re.compile(
    r"^##\s+(?::[\w_]+:\s+)?`(?P<role>[a-z][a-z0-9_\-]+)`",
    re.MULTILINE,
)
# Match the Result line we always emit. Example:
# "**Result:** :white_check_mark: `ok` - jira-intake summary"
# "**Result:** :pause_button: `needs_input` - need PR url"
# "**Result:** :no_entry_sign: `fail` - <crash summary>"
_RESULT_RE = re.compile(
    r"^\*\*Result:\*\*\s+(?::[\w_]+:\s+)?`(?P<status>ok|warn|fail|needs_input|skipped)`\s*-\s*(?P<summary>.+)$",
    re.MULTILINE,
)
# Match the optional pause-reason line.
_PAUSE_RE = re.compile(r"^\*\*Pause reason:\*\*\s+(?P<reason>.+)$", re.MULTILINE)


def _reflect(
    project_dir: Path,
    recorder: LessonRecorder,
    *,
    look_back_days: int,
    wide_scan: bool = False,
) -> ReflectionReport:
    log_dir = project_dir / "runs" / "thinking"
    runs_dir = project_dir / "runs"

    cutoff_epoch = time.time() - (look_back_days * 86400)

    log_files: list[Path] = []
    if log_dir.exists():
        for p in sorted(log_dir.glob("*.md")):
            try:
                if p.stat().st_mtime >= cutoff_epoch:
                    log_files.append(p)
            except OSError:
                continue

    run_logs: list[Path] = []
    if wide_scan and runs_dir.exists():
        for p in sorted(runs_dir.glob("*.log")):
            try:
                if p.stat().st_mtime >= cutoff_epoch:
                    run_logs.append(p)
            except OSError:
                continue

    if not log_files and not run_logs:
        scope = "thinking + run logs" if wide_scan else "thinking logs"
        return ReflectionReport(
            notes=f"no {scope} modified in the last {look_back_days}d "
                  "(agent has been quiet; no novel observations to record)",
        )

    lessons_added_before = _count_lessons(recorder)
    promoted_before = _count_promoted(recorder)

    runs_scanned = 0
    for log_path in log_files:
        runs_scanned += 1
        try:
            body = log_path.read_text(encoding="utf-8")
        except OSError:
            continue
        ticket_key = _ticket_from_log(log_path.name) or _ticket_from_body(body)
        _scan_log_for_lessons(body, recorder, source_ticket=ticket_key)

    run_logs_scanned = 0
    tracebacks_found = 0
    if wide_scan:
        for run_log in run_logs:
            run_logs_scanned += 1
            try:
                body = run_log.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            ticket_key = _ticket_from_log(run_log.name) or _ticket_from_body(body)
            tracebacks_found += _scan_run_log_for_crashes(
                body, recorder, source_ticket=ticket_key, log_name=run_log.name,
            )

    lessons_added_after = _count_lessons(recorder)
    promoted_after = _count_promoted(recorder)

    added = max(0, lessons_added_after - lessons_added_before)
    promoted = max(0, promoted_after - promoted_before)

    note_bits: list[str] = []
    if wide_scan:
        note_bits.append(
            f"wide_scan ON: scanned {len(log_files)} thinking logs + "
            f"{run_logs_scanned} run logs (tracebacks detected: {tracebacks_found})."
        )
    if added == 0:
        note_bits.append(
            "no novel observations today (all signals matched existing lessons). "
            "Agent is operating within its known playbook."
        )
    notes = " ".join(note_bits).strip()

    paths = [str(p) for p in log_files] + [str(p) for p in run_logs]
    return ReflectionReport(
        lessons_added=added,
        lessons_promoted=promoted,
        runs_scanned=runs_scanned + run_logs_scanned,
        log_paths_scanned=paths,
        notes=notes,
    )


def _scan_run_log_for_crashes(
    body: str,
    recorder: LessonRecorder,
    *,
    source_ticket: Optional[str],
    log_name: str,
) -> int:
    """Record one global lesson per distinct Traceback / fatal error in a run log.

    Returns the number of traceback matches found (regardless of whether the
    recorder deduped them - they still count as 'seen' for the audit log).
    """
    found = 0
    for m in _TRACEBACK_RE.finditer(body):
        found += 1
        err_line = m.group(1).strip()[:200]
        # The recorder dedupes via hash, so repeated crashes bump
        # occurrence_count -> auto-promote when >=3.
        recorder.record(
            role=GLOBAL_ROLE,
            lesson=(
                f"A prior background run hit `{err_line}`. "
                "Add a guard / fail-fast check upstream so the next runner "
                "gets a clear error message rather than a stack trace."
            ),
            category="failure",
            evidence=f"runs/{log_name} (Traceback)",
            tags=["runtime-error", "traceback", "scheduled-scout"],
            confidence="medium",
            source_ticket=source_ticket,
        )
    # Capture the first 3 fatal lines (de-duped by content) as 'failure' lessons.
    fatals: list[str] = []
    for m in _FATAL_RE.finditer(body):
        line = m.group(0).strip().strip("[]")
        if line and line not in fatals:
            fatals.append(line)
        if len(fatals) >= 3:
            break
    for line in fatals:
        recorder.record(
            role=GLOBAL_ROLE,
            lesson=(
                f"A prior run logged: \"{line[:180]}\". "
                "Trace this code path before the next scheduled run so the "
                "operator does not see the same error twice."
            ),
            category="failure",
            evidence=f"runs/{log_name} (structured fatal)",
            tags=["fatal-line", "scheduled-scout"],
            confidence="low",
            source_ticket=source_ticket,
        )
    return found


# ---------------------------------------------------------------------------
# Log parsing
# ---------------------------------------------------------------------------

def _scan_log_for_lessons(body: str, recorder: LessonRecorder, *, source_ticket: Optional[str]) -> None:
    """Walk the role sections in one thinking log and record one lesson per
    non-OK outcome. The recorder dedupes via stable hash so repeated runs
    bump occurrence_count instead of adding duplicates.
    """
    # Find all role headings + their positions, then slice between them.
    headings = list(_ROLE_HEADING_RE.finditer(body))
    if not headings:
        return
    for i, m in enumerate(headings):
        role = m.group("role")
        start = m.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(body)
        section = body[start:end]
        result = _RESULT_RE.search(section)
        if not result:
            continue
        status = result.group("status")
        summary = result.group("summary").strip()
        if status == "ok" or status == "skipped":
            continue
        pause = _PAUSE_RE.search(section)
        pause_text = pause.group("reason").strip() if pause else ""
        category, lesson = _outcome_to_lesson(role, status, summary, pause_text)
        if not lesson:
            continue
        recorder.record(
            role=role,
            lesson=lesson,
            category=category,
            evidence=f"{role} returned `{status}` in run for {source_ticket or '(unknown ticket)'}: {summary[:200]}",
            tags=_tags_for(role, status, source_ticket),
            confidence="medium",
            source_ticket=source_ticket,
        )


def _outcome_to_lesson(role: str, status: str, summary: str, pause_reason: str) -> tuple[str, str]:
    """Map one role outcome to a (category, lesson) pair.

    Lessons are framed as ACTIONABLE guidance for the next run, not as
    incident reports. Keep it to one sentence.
    """
    snippet = summary.strip().rstrip(".")
    pause_snippet = pause_reason.strip().rstrip(".") if pause_reason else ""

    if status == "fail":
        return "failure", (
            f"`{role}` has failed before with: \"{snippet}\". "
            "Before re-running, confirm upstream inputs and any required env/secrets "
            "(JIRA_*, DBT Cloud token, slack channel id) are populated."
        )
    if status == "warn":
        return "edge_case", (
            f"`{role}` flagged a WARN: \"{snippet}\". "
            "Treat the matching upstream condition as an edge case worth a guard or test."
        )
    if status == "needs_input":
        if pause_snippet:
            return "ambiguity", (
                f"`{role}` paused with: \"{pause_snippet}\". "
                "Resolve this kind of ambiguity earlier (clarifier or analyser) so the DAG keeps moving."
            )
        return "ambiguity", (
            f"`{role}` paused awaiting input: \"{snippet}\". "
            "Have the upstream role pre-fetch / pre-decide this so the supervisor does not stall."
        )
    return "best_practice", ""


def _tags_for(role: str, status: str, source_ticket: Optional[str]) -> list[str]:
    tags = [role, status]
    if source_ticket:
        tags.append(source_ticket.lower())
    return tags


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TICKET_RE = re.compile(r"EDAEM[-_]?(\d+)", re.IGNORECASE)


def _ticket_from_log(name: str) -> Optional[str]:
    m = _TICKET_RE.search(name)
    if not m:
        return None
    return f"EDAEM-{m.group(1)}"


def _ticket_from_body(body: str) -> Optional[str]:
    m = _TICKET_RE.search(body)
    if not m:
        return None
    return f"EDAEM-{m.group(1)}"


def _count_lessons(recorder: LessonRecorder) -> int:
    return sum(len(v) for v in recorder.all_lessons().values())


def _count_promoted(recorder: LessonRecorder) -> int:
    return len([
        l for l in recorder.all_lessons().get("_stable", [])
        if l.status == "promoted"
    ])
