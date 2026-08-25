"""Finance ARR Quarter Close (FQC-ARR) supervisor.

This class IS the **Manager agent** in OpenAI's "A Practical Guide to
Building Agents" (2025), the **Supervisor** in LangGraph multi-agent
docs, and the **Orchestrator** in Anthropic's "Building Effective Agents"
(Dec 2024). Three names for the same role — we adopt "Supervisor" as the
canonical name in this codebase.

The 10 modules under ``agents.arr_quarter_close.subagents`` (jira_intake,
requirements_analyzer, code_data_validator, clarifier, implementer,
test_runner, pr_author, ci_monitor, cd_monitor, qa_handoff) — plus the
on-demand ``debugger`` and ``quarter_close_runner`` — are the
**workers** (Anthropic) / **specialist agents** (OpenAI) that this
Supervisor delegates to. We use "sub-agent" as the canonical term for
them in this codebase. See
``~/.cursor/skills/multi-agent-supervisor-pattern/SKILL.md`` for the
three-way mapping and
``~/Documents/Cursor/Documents/fqc_arr_agentic_architecture_validation_report.md``
for the design validation.

Two execution modes:

* **Mode A - scheduled**: drives the existing ``ARRCloseOrchestrator`` for a
  known ``as_was_date``. No ticket. Used by the daily Automation and by
  the on-demand `arr-quarter-close` CLI.
* **Mode B - ticket-driven**: orchestrates the 10 sub-agents under
  ``agents.arr_quarter_close.subagents``.

The supervisor is pure-Python and runtime-agnostic. Each sub-agent runs as
a function call; sub-agents that fundamentally need an LLM (requirements
analyzer, implementer) return ``status='needs_input'`` with a prompt the
caller (Cursor SDK / SANA / user) can route to a model.

**Default LLM model.** The 3 LLM-driven leaf sub-agents and the Cursor SDK
runner all advertise a single ``preferred_model`` on their pause result.
The default is ``claude-opus-4-7-thinking-xhigh`` ("Opus 4.7 Extra High")
sourced from ``contracts.resolve_default_llm_model()``. Override
precedence: CLI ``--model`` > ``$FQC_ARR_DEFAULT_MODEL`` env var >
``contracts.DEFAULT_LLM_MODEL`` constant.

Pause-point handling:

The supervisor stops at a sub-agent whose status is ``needs_input`` or
``fail`` and returns a ``SupervisorRunReport`` with the role results so far
plus the pause reason. Resuming is a new ``run`` call with a populated
``state`` argument (see ``Supervisor.resume``).
"""

from __future__ import annotations

import logging
import re
import signal
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from agents.arr_quarter_close.contracts import (
    AuthMode,
    CDInput,
    CIInput,
    ClarificationInput,
    DebugInput,
    ImplementationInput,
    PRInput,
    QAHandoffInput,
    QuarterCloseInput,
    ReflectionInput,
    RequirementsInput,
    RoleResult,
    RoleStatus,
    SideTask,
    SupervisorRunReport,
    TestInput,
    TicketInput,
    ValidationInput,
)
from agents.arr_quarter_close.core import (
    ARRCloseConfig,
    ARRCloseOrchestrator,
    StepStatus,
)
from agents.arr_quarter_close.lessons import GLOBAL_ROLE, LessonRecorder, get_recorder
from agents.arr_quarter_close.notifier import SlackNotifier
from agents.arr_quarter_close.thinking_log import ThinkingLog, default_thinking_log_path
from agents.arr_quarter_close.subagents import (
    cd_monitor,
    ci_monitor,
    clarifier,
    code_data_validator,
    daily_reflection,
    debugger,
    implementer,
    jira_intake,
    pr_author,
    qa_handoff,
    quarter_close_runner,
    requirements_analyzer,
    test_runner,
)

log = logging.getLogger(__name__)

SUPERVISOR_DISPLAY_NAME = "Finance ARR Quarter Close (FQC-ARR)"
SUPERVISOR_SHORT_CODE = "FQC-ARR"
# All aliases users may type to refer to this supervisor. Recognized by the
# in-IDE data agent (.cursor/rules/arr-close-data-agent.mdc) and surfaced in
# rule / skill / README docs.
SUPERVISOR_ALIASES: tuple[str, ...] = (
    "FQC-ARR",
    "FQCARR",
    "FQC",
    "Finance ARR Quarter Close",
    "ARR Quarter Close",
    "ARR close",
)


@dataclass
class SupervisorInput:
    """Driving input for one supervisor run."""

    project_dir: Path
    ticket_key: Optional[str] = None
    as_was_date: Optional[str] = None
    auth_mode: AuthMode = AuthMode.SMART_GATES
    slack_channel: str = ""                       # required for ci/cd monitors
    slack_notify: bool = True                     # per-role thread pings
    pr_url_override: Optional[str] = None         # for resume scenarios
    pr_number_override: Optional[int] = None
    dbt_cloud_run_id_override: Optional[int] = None
    # Override the CI check name pattern the ci-monitor polls for. Defaults
    # to ci_monitor.CIInput's "ci/dbt_cloud". Useful when the GitHub check
    # context is renamed (e.g. "dbtcloud-codevalidate / DBT Code Validation").
    ci_check_name_override: Optional[str] = None
    dry_run: bool = False
    skip_roles: tuple[str, ...] = ()
    # Live thinking log (Markdown) - tail -f friendly. Default ON; None path
    # means use ``default_thinking_log_path(project_dir, ...)``.
    thinking_log_enabled: bool = True
    thinking_log_path: Optional[Path] = None
    # On-demand debugger sub-agent.
    debug_on_failure: bool = True       # auto-dispatch when any role FAILS
    debug_model: Optional[str] = None   # CLI: force-run debugger after the DAG
    debug_fallback_model: str = "arr_line_categories"   # used if upstream didn't pin one
    # Interactive clarifier: when clarifier returns NEEDS_INPUT, surface the
    # questions on stdin in the Cursor terminal and wait up to N seconds
    # for the operator to type answers. On timeout (or non-tty), fall back
    # to the existing "pause / post to Jira" path. Set to 0 to disable.
    clarifier_interactive_timeout_s: int = 600    # 10 minutes
    # Slack clarifier: when the interactive (stdin) path is unavailable or
    # times out, post the clarifier questions into the live Slack thread and
    # poll for an `ans:`-prefixed reply for up to N seconds before falling
    # back to the "pause / post to Jira" path. Reuses the same thread the
    # `task:` side-channel already polls. Set to 0 to disable. This is what
    # makes the agent resumable from Slack without a separate daemon: the
    # wait happens inside the live supervisor process.
    clarifier_slack_timeout_s: int = 1800         # 30 minutes
    # On-demand quarter-close-runner sub-agent (run dbt pipeline + ARR recon).
    # When set, the supervisor dispatches `quarter-close-runner` after the
    # canonical DAG so the QA-handoff comment carries the recon matrix.
    quarter_close: bool = False
    quarter_close_baseline_as_was_date: Optional[str] = None
    quarter_close_target_db: str = "certified_dev"
    quarter_close_baseline_db: str = "finance_prod"
    quarter_close_tolerance_pct: float = 1.0
    quarter_close_skip_pipeline: bool = False    # recon-only mode
    # Slack notify list - friendly names / emails resolved against
    # agents/arr_quarter_close/data/slack_directory.json into Slack user ids
    # at supervisor start. Sub-agents can read ``self.input.notify_user_ids``
    # to fan-out heartbeats or @-mentions to additional stakeholders.
    notify: tuple[str, ...] = ()             # CLI input (names / emails / ids)
    notify_user_ids: tuple[str, ...] = ()    # resolved at __post_init__-time
    notify_unresolved: tuple[str, ...] = ()  # entries we couldn't map
    # Continuous learning (lessons captured across runs).
    auto_reflect: bool = True                # auto-trigger daily-reflection once/day at end of run
    reflect_only: bool = False               # CLI: --reflect runs only the reflection sub-agent
    reflect_look_back_days: int = 1
    reflect_wide_scan: bool = False          # scheduled passes (9am/5pm) flip this on
    inject_lessons: bool = True              # include recorded lessons in role plans + LLM prompts
    max_lessons_per_role: int = 8

    def __post_init__(self) -> None:
        # Resolve --notify entries against the bundled Slack directory.
        # Lazy import: keeps slack_directory optional for environments that
        # haven't populated data/slack_directory.json yet.
        if self.notify and not self.notify_user_ids:
            try:
                from agents.arr_quarter_close.slack_directory import get_directory
                sd = get_directory()
                resolved: list[str] = []
                unresolved: list[str] = []
                for entry in self.notify:
                    uid = sd.resolve(entry)
                    if uid:
                        resolved.append(uid)
                    else:
                        unresolved.append(entry)
                # de-dup while preserving order
                seen: set[str] = set()
                self.notify_user_ids = tuple(
                    uid for uid in resolved if not (uid in seen or seen.add(uid))
                )
                self.notify_unresolved = tuple(unresolved)
            except Exception:
                # never let directory failure block the run
                self.notify_unresolved = tuple(self.notify)

    def resolve_mode(self) -> str:
        if self.ticket_key and self.as_was_date:
            return "both"
        if self.ticket_key:
            return "ticket"
        if self.as_was_date:
            return "scheduled"
        raise ValueError(
            "SupervisorInput needs at least one of ticket_key or as_was_date."
        )


@dataclass
class SupervisorState:
    """Carries intermediate role outputs between resume calls."""

    ticket_payload: Optional[dict] = None
    requirements_payload: Optional[dict] = None
    validation_payload: Optional[dict] = None
    implementation_payload: Optional[dict] = None
    test_report_payload: Optional[dict] = None
    pr_payload: Optional[dict] = None
    ci_payload: Optional[dict] = None
    cd_payload: Optional[dict] = None
    role_results: list[RoleResult] = field(default_factory=list)
    side_tasks: list[SideTask] = field(default_factory=list)
    last_side_channel_ts: Optional[str] = None    # cursor for poll_thread_messages


class Supervisor:
    # Recognized first-class side-channel commands. Anything not in this
    # set is queued as a free-form side task and surfaced in the final
    # report (so a human or the Cursor coding agent can pick it up later).
    SIDE_TASK_COMMANDS: tuple[str, ...] = (
        "skip", "pause", "cancel", "status", "debug", "quarter-close",
    )

    def __init__(self, input: SupervisorInput, state: Optional[SupervisorState] = None) -> None:
        self.input = input
        self.state = state or SupervisorState()
        self.project_dir = Path(input.project_dir).resolve()
        self.notifier: Optional[SlackNotifier] = self._build_notifier()
        self.thinking_log: ThinkingLog = self._build_thinking_log()
        # Continuous-learning store (lessons captured across runs).
        # Sub-agents access via ``self.recorder`` or ``get_recorder(project_dir)``.
        self.recorder: LessonRecorder = get_recorder(self.project_dir)
        self._pause_after_role: bool = False
        self._cancel_requested: bool = False

    def _build_thinking_log(self) -> ThinkingLog:
        if not self.input.thinking_log_enabled:
            return ThinkingLog(path=Path("/dev/null"), enabled=False)
        path = self.input.thinking_log_path or default_thinking_log_path(
            self.project_dir,
            ticket_key=self.input.ticket_key,
            as_was_date=self.input.as_was_date,
        )
        tlog = ThinkingLog(path=Path(path))
        if tlog.enabled:
            # Debug-level (not info) so SDK consumers don't get a duplicate
            # line in their logs. The CLI prints a visible click-to-open
            # banner via `_print_thinking_log_banner`; SDK callers can read
            # `sup.thinking_log.path` directly.
            log.debug("FQC-ARR thinking log: %s", tlog.path)
        return tlog

    def _build_notifier(self) -> Optional[SlackNotifier]:
        if self.input.dry_run:
            return None
        if not self.input.slack_notify:
            return None
        if not self.input.slack_channel:
            return None
        label = self.input.ticket_key or (
            f"snapshot {self.input.as_was_date}" if self.input.as_was_date else ""
        )
        return SlackNotifier(
            channel=self.input.slack_channel,
            label=label,
            display_name=SUPERVISOR_DISPLAY_NAME,
        )

    # ------------------------------------------------------------------ run
    def run(self) -> SupervisorRunReport:
        started = time.time()
        # Reflect-only fast path: skip the whole DAG and just run the
        # daily-reflection sub-agent. Useful for cron / manual reflect.
        if self.input.reflect_only:
            return self._run_reflect_only(started)
        mode = self.input.resolve_mode()
        log.info("%s mode=%s ticket=%s as_was_date=%s",
                 SUPERVISOR_DISPLAY_NAME, mode, self.input.ticket_key, self.input.as_was_date)

        role_count = 10 if mode in {"ticket", "both"} else 6
        self.thinking_log.header(
            display_name=SUPERVISOR_DISPLAY_NAME,
            mode=mode,
            ticket_key=self.input.ticket_key,
            as_was_date=self.input.as_was_date,
            auth_mode=self.input.auth_mode.value,
            role_count=role_count,
            slack_channel=self.input.slack_channel,
            project_dir=str(self.project_dir),
            aliases=SUPERVISOR_ALIASES,
        )
        if self.notifier:
            self.notifier.post_start_banner(
                mode=mode,
                auth_mode=self.input.auth_mode.value,
                role_count=role_count,
            )

        if mode in {"ticket", "both"}:
            report = self._run_ticket_mode(started)
            if report.overall_status in {RoleStatus.FAIL, RoleStatus.NEEDS_INPUT}:
                self._finish_notify(report)
                return report
            if mode == "both" and not self.input.quarter_close:
                # quarter-close-runner runs the same orchestrator manifest,
                # so skip the inline scheduled pass when both are requested.
                self._run_scheduled_mode_inline(report)
            # CLI-triggered debugger pass after a clean run.
            if self.input.debug_model:
                dbg = self._dispatch_debugger(
                    trigger="cli", failing_role=None,
                    target_model=self.input.debug_model,
                )
                if dbg is not None:
                    report.role_results.append(dbg)
                    report.overall_status = self._aggregate_status()
            # CLI-triggered quarter-close-runner pass after a clean run.
            if self.input.quarter_close:
                qc = self._dispatch_quarter_close(trigger="cli")
                if qc is not None:
                    report.role_results.append(qc)
                    report.overall_status = self._aggregate_status()
            report.elapsed_s = time.time() - started
            self._finish_notify(report)
            return report

        # mode == "scheduled". Two flavors:
        #
        #   a) --quarter-close NOT set  -> existing standalone orchestrator path
        #      (single role: scheduled-close, full ARR build + tests).
        #   b) --quarter-close set      -> quarter-close-runner takes over;
        #      it executes the same pipeline AND builds the recon matrix in
        #      one role result. Avoids running the dbt pipeline twice.
        if self.input.quarter_close:
            qc = self._dispatch_quarter_close(trigger="cli")
            results = [qc] if qc is not None else []
            report = SupervisorRunReport(
                ticket_key=None,
                mode=mode,
                overall_status=self._aggregate_status() if results else RoleStatus.WARN,
                role_results=results,
                pause_points=[],
                side_tasks=list(self.state.side_tasks),
                elapsed_s=time.time() - started,
            )
            self._finish_notify(report)
            return report

        result = self._run_scheduled_mode_standalone()
        result.elapsed_s = time.time() - started
        self._finish_notify(result)
        return result

    def _finish_notify(self, report: SupervisorRunReport) -> None:
        # Continuous-learning: trigger the daily-reflection sub-agent at most
        # once per UTC day. Runs BEFORE the thinking-log footer so it can
        # surface its own role-end entry in the same trace.
        if (
            self.input.auto_reflect
            and not self.input.dry_run
            and not self.input.reflect_only
            and not self.recorder.reflected_today()
        ):
            try:
                refl = self._dispatch_reflection(force=False)
                if refl is not None:
                    report.role_results.append(refl)
            except Exception:                                  # noqa: BLE001
                log.debug("auto-reflect failed; ignoring.", exc_info=True)

        # Thinking-log footer always runs (independent of Slack).
        queued = [
            {"requester": t.requester, "text": t.text}
            for t in report.side_tasks
            if t.action == "queued"
        ]
        self.thinking_log.footer(
            overall_status=report.overall_status.value,
            role_count=len(report.role_results),
            pause_count=len(report.pause_points),
            side_task_count=len(report.side_tasks),
            elapsed_s=report.elapsed_s,
            queued_side_tasks=queued,
        )
        if not self.notifier:
            return
        self.notifier.post_finish_banner(
            overall_status=report.overall_status.value,
            role_count=len(report.role_results),
            pause_count=len(report.pause_points),
            elapsed_s=report.elapsed_s,
        )
        if report.side_tasks:
            queued_tasks = [t for t in report.side_tasks if t.action == "queued"]
            if queued_tasks:
                lines = [f":memo: *{len(queued_tasks)} side-task(s) queued for follow-up*"]
                for t in queued_tasks[:10]:
                    lines.append(f"> `{t.requester or 'unknown'}`: {t.text[:160]}")
                if len(queued_tasks) > 10:
                    lines.append(f"> ... and {len(queued_tasks) - 10} more")
                try:
                    self.notifier.post("\n".join(lines))
                except Exception:                            # noqa: BLE001
                    log.debug("posting queued-tasks summary failed; ignoring.")

    # ---------------------------------------------------------- ticket DAG
    def _run_ticket_mode(self, started: float) -> SupervisorRunReport:
        roles = self._role_dag()
        for role_name, fn in roles:
            reason = self._role_reason(role_name)
            if role_name in self.input.skip_roles:
                self.thinking_log.role_start(
                    role_name, plan_only=False,
                    reason=f"skipped by --skip flag (would have run because: {reason})",
                )
                skip = RoleResult(role=role_name, status=RoleStatus.SKIPPED,
                                  summary=f"{role_name} skipped by --skip flag.")
                self.state.role_results.append(skip)
                self._notify_role(skip)
                self.thinking_log.role_end(
                    role_name, status="skipped", summary=skip.summary,
                )
                continue
            if self.input.dry_run:
                self.thinking_log.role_start(
                    role_name, plan_only=True, reason=reason,
                )
                try:
                    planned = fn(plan_only=True)
                except Exception as exc:                          # noqa: BLE001
                    crash = _crash_to_result(role_name, exc, phase="plan")
                    self.state.role_results.append(crash)
                    self._notify_role(crash)
                    self.thinking_log.role_end(
                        role_name, status=crash.status.value,
                        summary=crash.summary, pause_reason=crash.pause_reason,
                        payload=crash.payload or None,
                    )
                    self._maybe_debug_on_failure(crash)
                    return self._pause(crash, started)
                planned_summary = str(planned)[:200]
                self.state.role_results.append(
                    RoleResult(role=role_name, status=RoleStatus.SKIPPED,
                               summary=f"(dry-run) planned: {planned}",
                               payload={"plan": planned})
                )
                self.thinking_log.role_end(
                    role_name, status="skipped",
                    summary=f"(dry-run) planned: {planned_summary}",
                    payload={"plan": _safe_payload(planned)},
                )
                continue
            self.thinking_log.role_start(role_name, plan_only=False, reason=reason)
            try:
                result = fn(plan_only=False)
            except Exception as exc:                              # noqa: BLE001
                # Any uncaught exception inside a sub-agent becomes a
                # RoleResult(FAIL) so the supervisor still emits a pause
                # point, dispatches the debugger if enabled, writes the
                # thinking-log footer, and posts the Slack finish banner.
                # Crashing out of the DAG drops all of that audit trail.
                result = _crash_to_result(role_name, exc, phase="run")
            self.state.role_results.append(result)
            self._absorb(result)
            self._notify_role(result)
            self.thinking_log.role_end(
                role_name,
                status=result.status.value,
                summary=result.summary,
                pause_reason=result.pause_reason,
                payload=result.payload or None,
                artifacts=result.artifacts or None,
            )
            if result.status == RoleStatus.FAIL:
                # On-demand debugger sub-agent: auto-dispatch on FAIL so the
                # paused SupervisorRunReport already contains the lineage
                # walk + stage matrix + ranked hypotheses + Jira-ready ADF
                # comment. Caller can act on it without a second round-trip.
                self._maybe_debug_on_failure(result)
                return self._pause(result, started)
            if result.status == RoleStatus.NEEDS_INPUT:
                # Special case: clarifier asks for human answers. Try the
                # interactive path first (stdin in the Cursor terminal,
                # 10-minute default timeout). If the operator answers, we
                # absorb the Q&A into requirements + skip the Jira post.
                # On timeout / non-tty / empty answers, we fall through
                # to the normal pause -> approve-and-post flow.
                if result.role == "clarifier":
                    # 1) Terminal stdin (Cursor). 2) Slack `ans:` reply in the
                    # live thread. Either resolves the questions in-process and
                    # lets the DAG continue without a Jira round-trip.
                    resolved = self._try_interactive_clarifier(result)
                    if resolved is None:
                        resolved = self._try_slack_clarifier(result)
                    if resolved is not None:
                        # Replace the NEEDS_INPUT result with the resolved
                        # one so downstream roles see clarifier=OK.
                        self.state.role_results[-1] = resolved
                        self._notify_role(resolved)
                        self.thinking_log.role_end(
                            "clarifier", status=resolved.status.value,
                            summary=resolved.summary,
                            payload=resolved.payload or None,
                        )
                        continue
                return self._pause(result, started)

            # Slack side-channel: read any new `task:` messages posted in
            # the thread while the role was running, dispatch them, and
            # honor cancel/pause requests before continuing to the next role.
            self._drain_side_tasks()
            if self._cancel_requested:
                cancel = RoleResult(
                    role="supervisor", status=RoleStatus.WARN,
                    summary="cancel requested via Slack side-channel `task: cancel`.",
                )
                self.state.role_results.append(cancel)
                self._notify_role(cancel)
                self.thinking_log.supervisor_decision(
                    "cancel after current role",
                    "Operator sent `task: cancel` in the Slack thread. The "
                    "DAG is aborting cleanly with `overall_status=warn`.",
                )
                return self._pause(cancel, started)
            if self._pause_after_role:
                pause = RoleResult(
                    role="supervisor", status=RoleStatus.NEEDS_INPUT,
                    summary="pause requested via Slack side-channel `task: pause`.",
                    pause_reason="awaiting human authorization to continue",
                )
                self.state.role_results.append(pause)
                self._notify_role(pause)
                self.thinking_log.supervisor_decision(
                    "pause after current role",
                    "Operator sent `task: pause` in the Slack thread. The "
                    "DAG halts and returns `overall_status=needs_input`; "
                    "resume via `Supervisor(input, state=...).run()`.",
                )
                return self._pause(pause, started)

        overall = self._aggregate_status()
        return SupervisorRunReport(
            ticket_key=self.input.ticket_key,
            mode="ticket",
            overall_status=overall,
            role_results=list(self.state.role_results),
            side_tasks=list(self.state.side_tasks),
            elapsed_s=time.time() - started,
        )

    def _notify_role(self, result: RoleResult) -> None:
        if not self.notifier:
            return
        self.notifier.post_role_result(
            role=result.role,
            status=result.status.value,
            summary=result.summary,
            pause_reason=result.pause_reason,
        )

    def _role_dag(self) -> list[tuple[str, callable]]:
        return [
            ("jira-intake",            self._run_jira_intake),
            ("requirements-analyzer",  self._run_requirements_analyzer),
            ("code-data-validator",    self._run_code_data_validator),
            ("clarifier",              self._run_clarifier),
            ("implementer",            self._run_implementer),
            ("test-runner",            self._run_test_runner),
            ("pr-author",              self._run_pr_author),
            ("ci-monitor",             self._run_ci_monitor),
            ("cd-monitor",             self._run_cd_monitor),
            ("qa-handoff",             self._run_qa_handoff),
        ]

    # --------------------------------------------------------- scheduled
    def _run_scheduled_mode_standalone(self) -> SupervisorRunReport:
        if not self.input.as_was_date:
            raise ValueError("Scheduled mode requires as_was_date.")
        cfg = ARRCloseConfig(
            as_was_date=self.input.as_was_date,
            project_dir=self.project_dir,
            dry_run=self.input.dry_run,
        )
        orchestrator = ARRCloseOrchestrator(cfg)
        self._wrap_orchestrator_with_notifier(orchestrator)
        self.thinking_log.role_start(
            "scheduled-close",
            plan_only=self.input.dry_run,
            reason=f"Run dbt for as_was_date={self.input.as_was_date}.",
        )
        result = orchestrator.run()
        close_role = RoleResult(
            role="scheduled-close",
            status=_step_to_role_status(result.overall_status),
            summary=f"Scheduled close for {self.input.as_was_date}",
            payload={"close_result": result.as_dict()},
        )
        self._notify_role(close_role)
        self.thinking_log.role_end(
            "scheduled-close",
            status=close_role.status.value,
            summary=close_role.summary,
            payload={"close_result": result.as_dict()},
        )
        return SupervisorRunReport(
            ticket_key=self.input.ticket_key,
            mode="scheduled",
            overall_status=close_role.status,
            role_results=[close_role],
            elapsed_s=result.duration_s,
        )

    def _run_scheduled_mode_inline(self, report: SupervisorRunReport) -> None:
        impl = self.state.implementation_payload or {}
        if not (impl and impl.get("needs_snapshot_rebuild")):
            return
        if not self.input.as_was_date:
            skip = RoleResult(role="scheduled-close",
                              status=RoleStatus.SKIPPED,
                              summary="needs_snapshot_rebuild=True but no as_was_date supplied; skipping.")
            report.role_results.append(skip)
            self._notify_role(skip)
            self.thinking_log.role_end(
                "scheduled-close", status="skipped", summary=skip.summary,
            )
            return
        cfg = ARRCloseConfig(
            as_was_date=self.input.as_was_date,
            project_dir=self.project_dir,
            dry_run=self.input.dry_run,
        )
        orchestrator = ARRCloseOrchestrator(cfg)
        self._wrap_orchestrator_with_notifier(orchestrator)
        self.thinking_log.role_start(
            "scheduled-close",
            plan_only=self.input.dry_run,
            reason=(
                f"Implementer flagged `needs_snapshot_rebuild=True`; "
                f"re-running dbt for as_was_date={self.input.as_was_date}."
            ),
        )
        cr = orchestrator.run()
        close_role = RoleResult(
            role="scheduled-close",
            status=_step_to_role_status(cr.overall_status),
            summary=f"Inline close for {self.input.as_was_date} after implementer.",
            payload={"close_result": cr.as_dict()},
        )
        report.role_results.append(close_role)
        self._notify_role(close_role)
        self.thinking_log.role_end(
            "scheduled-close",
            status=close_role.status.value,
            summary=close_role.summary,
            payload={"close_result": cr.as_dict()},
        )

    def _wrap_orchestrator_with_notifier(self, orchestrator: ARRCloseOrchestrator) -> None:
        """Emit a Slack reply + thinking-log entry after every dbt step."""
        notifier = self.notifier
        tlog = self.thinking_log
        previous = getattr(orchestrator, "on_step_complete", None)

        def _wrapped(step_result) -> None:
            if previous is not None:
                try:
                    previous(step_result)
                except Exception:                    # noqa: BLE001
                    log.debug("prior on_step_complete raised; ignoring.")
            try:
                status = (
                    step_result.status.value
                    if hasattr(step_result.status, "value")
                    else str(step_result.status)
                )
                step_name = step_result.step.name
                duration = float(getattr(step_result, "duration_s", 0.0) or 0.0)
                stderr_tail = getattr(step_result, "stderr_tail", "") or ""
                if notifier is not None:
                    notifier.post_role_result(
                        role=f"close:{step_name}",
                        status=_close_to_role_status(status),
                        summary=f"dbt {step_name} -> {status} ({duration:.1f}s)",
                    )
                tlog.orchestrator_step(
                    step_name=step_name,
                    status=_close_to_role_status(status),
                    duration_s=duration,
                    stderr_tail=stderr_tail,
                )
            except Exception:                        # noqa: BLE001
                log.debug("per-step on_step_complete hook failed; ignoring.")

        orchestrator.on_step_complete = _wrapped

    # ---------------------------------------------------------- per-role
    def _run_jira_intake(self, plan_only: bool):
        req = TicketInput(ticket_key=self.input.ticket_key or "")
        if plan_only:
            return jira_intake.plan(req)
        return jira_intake.run(req)

    def _run_requirements_analyzer(self, plan_only: bool):
        ticket = self._ticket_or_stub("requirements-analyzer", plan_only)
        if isinstance(ticket, RoleResult):
            return ticket
        req = RequirementsInput(ticket=ticket)
        if plan_only:
            return requirements_analyzer.plan(req)
        return requirements_analyzer.run(req)

    def _run_code_data_validator(self, plan_only: bool):
        reqs = self._requirements_or_stub("code-data-validator", plan_only)
        if isinstance(reqs, RoleResult):
            return reqs
        req = ValidationInput(requirements=reqs, project_dir=str(self.project_dir))
        if plan_only:
            return code_data_validator.plan(req)
        return code_data_validator.run(req)

    def _run_clarifier(self, plan_only: bool):
        ticket = self._ticket_or_stub("clarifier", plan_only)
        if isinstance(ticket, RoleResult):
            return ticket
        reqs = self._requirements_or_stub("clarifier", plan_only)
        if isinstance(reqs, RoleResult):
            return reqs
        val = self._validation_or_stub("clarifier", plan_only)
        if isinstance(val, RoleResult):
            return val
        req = ClarificationInput(
            ticket=ticket, requirements=reqs, validation=val, auth_mode=self.input.auth_mode,
        )
        if plan_only:
            return clarifier.plan(req)

        # In full-auto, the clarifier would otherwise post straight to Jira
        # and continue with the questions UNANSWERED. Give the operator a
        # bounded chance to answer in the Slack thread with `ans:` first.
        # If they do, we absorb the Q&A and skip the Jira post. If not, we
        # fall through to the normal full-auto behavior (post + continue).
        if (
            self.input.auth_mode == AuthMode.FULL_AUTO
            and int(getattr(self.input, "clarifier_slack_timeout_s", 0) or 0) > 0
            and self.notifier is not None
            and self.notifier.thread_ts
        ):
            payload = clarifier.build_clarification(req)
            if payload is not None:
                pseudo = RoleResult(
                    role="clarifier",
                    status=RoleStatus.NEEDS_INPUT,
                    summary="(full-auto) offering Slack `ans:` before Jira post.",
                    payload={"clarification": payload.as_dict()},
                )
                resolved = self._try_slack_clarifier(pseudo)
                if resolved is not None:
                    return resolved

        return clarifier.run(req)

    def _run_implementer(self, plan_only: bool):
        reqs = self._requirements_or_stub("implementer", plan_only)
        if isinstance(reqs, RoleResult):
            return reqs
        val = self._validation_or_stub("implementer", plan_only)
        if isinstance(val, RoleResult):
            return val
        req = ImplementationInput(
            requirements=reqs, validation=val, project_dir=str(self.project_dir),
        )
        if plan_only:
            return implementer.plan(req)
        return implementer.run(req)

    def _run_test_runner(self, plan_only: bool):
        req = TestInput(project_dir=str(self.project_dir), as_was_date=self.input.as_was_date)
        if plan_only:
            return test_runner.plan(req)
        return test_runner.run(req)

    def _run_pr_author(self, plan_only: bool):
        ticket = self._ticket_or_stub("pr-author", plan_only)
        if isinstance(ticket, RoleResult):
            return ticket
        impl = self._implementation_or_stub("pr-author", plan_only)
        if isinstance(impl, RoleResult):
            return impl
        tr = self._test_report_or_stub("pr-author", plan_only)
        if isinstance(tr, RoleResult):
            return tr
        req = PRInput(
            ticket=ticket, implementation=impl, test_report=tr,
            auth_mode=self.input.auth_mode,
        )
        if plan_only:
            return pr_author.plan(req)
        return pr_author.run(req)

    def _run_ci_monitor(self, plan_only: bool):
        pr = self.state.pr_payload or {}
        pr_url = self.input.pr_url_override or pr.get("pr_url") or ""
        pr_number = self.input.pr_number_override or pr.get("pr_number") or 0
        if not pr_url and not plan_only:
            return RoleResult(role="ci-monitor", status=RoleStatus.NEEDS_INPUT,
                              summary="PR url not available yet (pr-author paused or skipped).",
                              pause_reason="Need PR url/number to start CI monitor.")
        ci_kwargs: dict = dict(
            pr_url=pr_url, pr_number=int(pr_number),
            slack_channel=self.input.slack_channel or "PINNED_CHANNEL",
        )
        if self.input.ci_check_name_override:
            ci_kwargs["check_name_pattern"] = self.input.ci_check_name_override
        req = CIInput(**ci_kwargs)
        if plan_only:
            return ci_monitor.plan(req)
        if not self.input.slack_channel:
            return RoleResult(role="ci-monitor", status=RoleStatus.NEEDS_INPUT,
                              summary="Slack channel not pinned; supervisor must collect once per ticket.",
                              pause_reason="Pick Slack channel (e.g. U... or C...)")
        return ci_monitor.run(req)

    def _run_cd_monitor(self, plan_only: bool):
        pr = self.state.pr_payload or {}
        req = CDInput(
            dbt_cloud_run_id=self.input.dbt_cloud_run_id_override,
            pr_url=pr.get("pr_url") or self.input.pr_url_override or "",
            slack_channel=self.input.slack_channel or "PINNED_CHANNEL",
        )
        if plan_only:
            return cd_monitor.plan(req)
        return cd_monitor.run(req)

    def _run_qa_handoff(self, plan_only: bool):
        ticket = self._ticket_or_stub("qa-handoff", plan_only)
        if isinstance(ticket, RoleResult):
            return ticket
        tr = self._test_report_or_stub("qa-handoff", plan_only)
        if isinstance(tr, RoleResult):
            return tr
        ci = self._ci_report_or_stub("qa-handoff", plan_only)
        if isinstance(ci, RoleResult):
            return ci
        cd = self._cd_report_or_stub("qa-handoff", plan_only)
        if isinstance(cd, RoleResult):
            return cd
        req = QAHandoffInput(
            ticket=ticket, test_report=tr, ci_report=ci, cd_report=cd,
            auth_mode=self.input.auth_mode,
        )
        if plan_only:
            return qa_handoff.plan(req)
        return qa_handoff.run(req)

    # ----------------------------------------------------- helpers / state
    def _absorb(self, result: RoleResult) -> None:
        p = result.payload or {}
        if "ticket" in p:
            self.state.ticket_payload = p["ticket"]
        if "requirements" in p:
            self.state.requirements_payload = p["requirements"]
        if "validation" in p:
            self.state.validation_payload = p["validation"]
        if "implementation" in p:
            self.state.implementation_payload = p["implementation"]
        if "test_report" in p:
            self.state.test_report_payload = p["test_report"]
        if "pr" in p:
            self.state.pr_payload = p["pr"]
        if "ci_report" in p:
            self.state.ci_payload = p["ci_report"]
        if "cd_report" in p:
            self.state.cd_payload = p["cd_report"]

    def _pause(self, result: RoleResult, started: float) -> SupervisorRunReport:
        return SupervisorRunReport(
            ticket_key=self.input.ticket_key,
            mode="ticket",
            overall_status=result.status,
            role_results=list(self.state.role_results),
            pause_points=[{
                "role": result.role,
                "reason": result.pause_reason or result.summary,
            }],
            side_tasks=list(self.state.side_tasks),
            elapsed_s=time.time() - started,
        )

    # ------------------------------------------------------- debugger hook
    def _dispatch_debugger(
        self,
        *,
        trigger: str,
        failing_role: Optional[str],
        target_model: Optional[str] = None,
    ) -> Optional[RoleResult]:
        """Run the on-demand debugger sub-agent.

        Called from three places:

        * ``_maybe_debug_on_failure`` after any role returns ``FAIL``.
        * ``_process_side_task`` when an operator posts ``task: debug``.
        * The CLI when ``--debug-model`` (or just ``--debug``) is passed.

        Returns the dispatched ``RoleResult`` so the caller can surface
        the debugger summary in the side-task ack / final report.
        Returns ``None`` when there is no ticket payload yet and we
        cannot synthesise a useful debugger input.
        """
        # In dry-run / when jira-intake was skipped, we still want the
        # debugger to render its plan against a synthetic ticket so the
        # operator can see what it would do.
        ticket = self._ticket_or_stub("debugger", plan_only=self.input.dry_run)
        if isinstance(ticket, RoleResult):
            # No ticket yet (e.g. jira-intake failed first); can't debug usefully.
            return None
        model = target_model or self._infer_debug_model()
        failing_payload: dict = {}
        if failing_role:
            for r in reversed(self.state.role_results):
                if r.role == failing_role and r.payload:
                    failing_payload = r.payload
                    break
        req = DebugInput(
            ticket=ticket,
            project_dir=str(self.project_dir),
            target_model=model,
            trigger=trigger,
            failing_role=failing_role,
            failing_payload=failing_payload,
            auth_mode=self.input.auth_mode,
        )
        reason = (
            f"Auto-dispatch on FAIL from `{failing_role}`; debugging `{model}`."
            if trigger == "auto_failure" else
            f"Operator-triggered ({trigger}); debugging `{model}`."
        )
        self.thinking_log.role_start("debugger", plan_only=False, reason=reason)
        if self.input.dry_run:
            planned = debugger.plan(req)
            result = RoleResult(
                role="debugger", status=RoleStatus.SKIPPED,
                summary=f"(dry-run) planned: {planned}", payload={"plan": planned},
            )
        else:
            result = debugger.run(req)
        self.state.role_results.append(result)
        self._absorb(result)
        self._notify_role(result)
        self.thinking_log.role_end(
            "debugger",
            status=result.status.value,
            summary=result.summary,
            pause_reason=result.pause_reason,
            payload=result.payload or None,
            artifacts=result.artifacts or None,
        )
        return result

    def _maybe_debug_on_failure(self, failed: RoleResult) -> None:
        if not self.input.debug_on_failure:
            return
        if failed.role == "debugger":          # avoid recursion
            return
        dispatched = self._dispatch_debugger(
            trigger="auto_failure",
            failing_role=failed.role,
        )
        if dispatched is None:
            self.thinking_log.supervisor_decision(
                "debugger auto-dispatch skipped",
                f"Role `{failed.role}` failed but no ticket payload is "
                "available yet (jira-intake hasn't produced one). The "
                "debugger needs a TicketSpec to shape its output, so it "
                "was not dispatched. Resume after jira-intake to enable "
                "auto-debugging.",
            )

    # --------------------------------------- daily-reflection hook
    def _dispatch_reflection(self, *, force: bool) -> Optional[RoleResult]:
        """Run the on-demand daily-reflection sub-agent.

        Returns the RoleResult so callers can append it to the run report.
        Never raises - reflection failures should not affect the parent run.
        """
        req = ReflectionInput(
            project_dir=str(self.project_dir),
            look_back_days=self.input.reflect_look_back_days,
            force=force,
            wide_scan=self.input.reflect_wide_scan,
            auth_mode=self.input.auth_mode,
        )
        self.thinking_log.role_start(
            "daily-reflection", plan_only=False,
            reason="Auto-trigger at end of run (once per UTC day) to capture lessons learned.",
        )
        try:
            result = daily_reflection.run(req)
        except Exception as exc:                            # noqa: BLE001
            result = _crash_to_result("daily-reflection", exc, phase="run")
        self.state.role_results.append(result)
        self._notify_role(result)
        self.thinking_log.role_end(
            "daily-reflection",
            status=result.status.value,
            summary=result.summary,
            pause_reason=result.pause_reason,
            payload=result.payload or None,
            artifacts=result.artifacts or None,
        )
        return result

    def _run_reflect_only(self, started: float) -> SupervisorRunReport:
        """Fast path for ``fqc-arr --reflect``: skip the DAG entirely."""
        self.thinking_log.header(
            display_name=SUPERVISOR_DISPLAY_NAME,
            mode="reflect",
            ticket_key=self.input.ticket_key,
            as_was_date=self.input.as_was_date,
            auth_mode=self.input.auth_mode.value,
            role_count=1,
            slack_channel=self.input.slack_channel,
            project_dir=str(self.project_dir),
            aliases=SUPERVISOR_ALIASES,
        )
        refl = self._dispatch_reflection(force=True)
        results = [refl] if refl is not None else []
        report = SupervisorRunReport(
            ticket_key=self.input.ticket_key,
            mode="reflect",
            overall_status=(refl.status if refl else RoleStatus.WARN),
            role_results=results,
            pause_points=[],
            side_tasks=list(self.state.side_tasks),
            elapsed_s=time.time() - started,
        )
        # Skip _finish_notify auto-reflect guard (we already reflected).
        queued = []
        self.thinking_log.footer(
            overall_status=report.overall_status.value,
            role_count=len(report.role_results),
            pause_count=0,
            side_task_count=0,
            elapsed_s=report.elapsed_s,
            queued_side_tasks=queued,
        )
        return report

    # --------------------------------------- quarter-close-runner hook
    def _dispatch_quarter_close(
        self,
        *,
        trigger: str,
        as_was_date_override: Optional[str] = None,
        baseline_as_was_date_override: Optional[str] = None,
        run_pipeline_override: Optional[bool] = None,
    ) -> Optional[RoleResult]:
        """Run the on-demand quarter-close-runner sub-agent.

        Called from three places:

        * The CLI when ``--quarter-close`` is passed (after the canonical DAG).
        * ``_process_side_task`` when an operator posts ``task: quarter-close [date]``.
        * Direct SDK calls (``sup._dispatch_quarter_close(trigger='sdk', ...)``).

        Returns the dispatched ``RoleResult`` so the caller can surface
        the recon summary in the side-task ack / final report. Returns
        ``None`` when there is no ``as_was_date`` to run against.
        """
        as_was = (
            as_was_date_override
            or self.input.as_was_date
            or _latest_known_close_date()
        )
        if not as_was:
            return None
        run_pipeline = (
            run_pipeline_override
            if run_pipeline_override is not None
            else not self.input.quarter_close_skip_pipeline
        )
        req = QuarterCloseInput(
            project_dir=str(self.project_dir),
            as_was_date=as_was,
            baseline_as_was_date=(
                baseline_as_was_date_override
                or self.input.quarter_close_baseline_as_was_date
                or _prior_known_close_date(as_was)
            ),
            target_db=self.input.quarter_close_target_db,
            baseline_db=self.input.quarter_close_baseline_db,
            run_pipeline=run_pipeline,
            tolerance_pct=self.input.quarter_close_tolerance_pct,
            auth_mode=self.input.auth_mode,
        )
        reason = (
            f"Operator-triggered ({trigger}); "
            f"as_was_date={as_was} run_pipeline={run_pipeline}."
        )
        self.thinking_log.role_start(
            "quarter-close-runner", plan_only=False, reason=reason,
        )
        try:
            if self.input.dry_run:
                planned = quarter_close_runner.plan(req)
                result = RoleResult(
                    role="quarter-close-runner",
                    status=RoleStatus.SKIPPED,
                    summary=f"(dry-run) planned: {planned}",
                    payload={"plan": planned},
                )
            else:
                result = quarter_close_runner.run(req)
        except Exception as exc:                                       # noqa: BLE001
            result = _crash_to_result("quarter-close-runner", exc, phase="run")
        self.state.role_results.append(result)
        self._notify_role(result)
        self.thinking_log.role_end(
            "quarter-close-runner",
            status=result.status.value,
            summary=result.summary,
            pause_reason=result.pause_reason,
            payload=result.payload or None,
            artifacts=result.artifacts or None,
        )
        return result

    # ----------------------------------------------- interactive clarifier
    def _try_interactive_clarifier(self, result: RoleResult) -> Optional[RoleResult]:
        """Surface clarifier questions on stdin; return a resolved OK result
        on answer, ``None`` on timeout / non-tty / all-blank.

        Behavior:

        * If ``clarifier_interactive_timeout_s == 0`` or stdin is not a
          tty (e.g. piped, CI), returns ``None`` immediately -> falls
          back to the normal pause-and-post-to-Jira path.
        * Prints a clearly-bordered banner with the numbered questions
          and a per-question prompt. Each ``input()`` call is wrapped
          in a single SIGALRM timer covering the whole exchange.
        * On any answer being non-empty: builds a ``RoleResult(OK)``
          carrying the Q&A on ``payload['clarification']['answers']``,
          logs a Slack notice (if enabled), and writes a thinking-log
          decision so the audit trail records the interactive resolve.
        * On timeout or empty answers: prints a "falling back to Jira"
          line, returns ``None``.
        """
        timeout_s = int(self.input.clarifier_interactive_timeout_s or 0)
        if timeout_s <= 0:
            return None
        if not sys.stdin.isatty():
            return None
        clar = (result.payload or {}).get("clarification") or {}
        # Re-derive the questions from the ADF (clarifier's existing format).
        questions = _extract_questions_from_clar_payload(clar)
        if not questions:
            return None

        # Banner
        bar = "=" * 78
        if timeout_s >= 60:
            timeout_label = f"{timeout_s // 60} min"
        else:
            timeout_label = f"{timeout_s} sec"
        print("")
        print(bar)
        print(f"  Clarifier wants to ask {len(questions)} question(s) before posting to Jira.")
        print(f"  Answer here in the terminal - each on its own line, blank to skip one.")
        print(f"  All-blank or {timeout_label} timeout -> falls back to a Jira comment.")
        print(bar)
        print("")
        sys.stdout.flush()

        # SIGALRM wraps the entire exchange. Available on macOS / Linux;
        # if signal.SIGALRM isn't available, we fall through without a
        # timer (the operator can ^C to abort).
        answers: list[str] = []
        sig_alarm = getattr(signal, "SIGALRM", None)
        sig_handler_prev = None
        if sig_alarm is not None:
            def _handler(signum, frame):                  # noqa: ARG001
                raise TimeoutError(
                    f"interactive clarifier timed out after {timeout_s}s")
            sig_handler_prev = signal.signal(sig_alarm, _handler)
            signal.alarm(timeout_s)
        try:
            for i, q in enumerate(questions, 1):
                print(f"  [{i}/{len(questions)}] {q}")
                try:
                    ans = input("    > ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\n  (aborted by operator; falling back to Jira post)")
                    return None
                answers.append(ans)
        except TimeoutError:
            print(f"\n  (no answer in {timeout_s}s; falling back to Jira post)")
            return None
        finally:
            if sig_alarm is not None:
                signal.alarm(0)
                if sig_handler_prev is not None:
                    signal.signal(sig_alarm, sig_handler_prev)

        if not any(a for a in answers):
            print("  (all answers blank; falling back to Jira post)\n")
            return None

        # Resolved interactively - build the OK result via the shared absorber.
        answered = sum(1 for a in answers if a)
        qa_pairs = [{"question": q, "answer": a} for q, a in zip(questions, answers)]
        new_result = self._absorb_clarifier_answers(
            clar,
            qa_pairs,
            via="interactively in Cursor terminal",
            summary=(
                f"Resolved interactively in Cursor terminal: "
                f"{answered}/{len(questions)} answered; skipping Jira post."
            ),
            extra_clar_flags={"resolved_interactively": True},
        )
        self.thinking_log.supervisor_decision(
            "clarifier resolved interactively",
            f"Operator answered {answered}/{len(questions)} clarifier "
            f"question(s) in the terminal within "
            f"{self.input.clarifier_interactive_timeout_s}s. Q&A absorbed "
            f"into requirements.scope_summary; Jira comment NOT posted. "
            f"Downstream roles continue with the enriched requirements.",
        )
        print(f"\n  OK - {answered}/{len(questions)} answered; continuing the DAG.\n")
        sys.stdout.flush()
        return new_result

    def _absorb_clarifier_answers(
        self,
        clar: dict,
        qa_pairs: list[dict],
        *,
        via: str,
        summary: str,
        extra_clar_flags: Optional[dict] = None,
    ) -> RoleResult:
        """Fold a set of clarifier Q&A pairs into requirements + build OK result.

        Shared by the interactive (terminal) and Slack (`ans:`) resolution
        paths so both enrich ``requirements.scope_summary`` identically, drop
        the now-answered questions from the open-questions list, and emit a
        ``clarifier=OK`` RoleResult that skips the Jira post.
        """
        rp = dict(self.state.requirements_payload or {})
        existing = rp.get("scope_summary", "") or ""
        qa_block = f"\n\nClarifying Q&A (resolved {via}):\n" + "\n".join(
            f"  Q: {p['question']}\n  A: {p.get('answer') or '(skipped)'}"
            for p in qa_pairs
        )
        rp["scope_summary"] = existing + qa_block
        # Drop the now-answered questions so downstream roles don't re-ask.
        if "questions" in rp:
            answered_set = {p["question"] for p in qa_pairs if p.get("answer")}
            rp["questions"] = [
                q for q in rp.get("questions") or [] if q not in answered_set
            ]
        self.state.requirements_payload = rp

        clar_payload = dict(clar)
        clar_payload["answers"] = qa_pairs
        clar_payload["posted"] = False
        if extra_clar_flags:
            clar_payload.update(extra_clar_flags)

        return RoleResult(
            role="clarifier",
            status=RoleStatus.OK,
            summary=summary,
            payload={"clarification": clar_payload},
        )

    def _try_slack_clarifier(self, result: RoleResult) -> Optional[RoleResult]:
        """Post clarifier questions to the live Slack thread and wait for an
        ``ans:`` reply; return a resolved OK result on answer, ``None`` on
        timeout / no-Slack / disabled.

        This is the no-daemon Slack resume path. The wait runs inside the
        live supervisor process, polling the same thread the ``task:``
        side-channel uses. Behavior:

        * Disabled when ``clarifier_slack_timeout_s <= 0`` or there is no
          active Slack thread (``--no-slack`` / no ``--slack-channel``).
        * Posts a numbered question block asking the operator to reply with
          ``ans: ...`` (single combined reply or one ``ans:`` line per
          question).
        * Polls ``poll_thread_messages`` every ~20s until the deadline.
          A ``task: cancel`` in the thread aborts the wait early and falls
          back to the Jira post.
        * On an ``ans:`` reply, maps answers to questions (numbered split,
          else positional, else combined) and absorbs via
          ``_absorb_clarifier_answers``.
        """
        timeout_s = int(getattr(self.input, "clarifier_slack_timeout_s", 0) or 0)
        if timeout_s <= 0:
            return None
        if not self.notifier or not self.notifier.thread_ts:
            return None
        clar = (result.payload or {}).get("clarification") or {}
        questions = _extract_questions_from_clar_payload(clar)
        if not questions:
            return None

        timeout_label = (
            f"{timeout_s // 60} min" if timeout_s >= 60 else f"{timeout_s} sec"
        )
        prompt = [
            f":question: *Clarifications needed* "
            f"({len(questions)} question(s)) before I post to Jira.",
            f"Reply in this thread starting with `ans:` within "
            f"*{timeout_label}* and I'll absorb it and continue the DAG.",
            "",
        ]
        for i, q in enumerate(questions, 1):
            prompt.append(f"{i}. {q}")
        prompt.append("")
        prompt.append(
            "_Example:_ `ans: 1) USD_HIST  2) 2026-05-11  3) account grain`"
        )
        prompt.append("_(or send `task: cancel` to skip and post to Jira)_")
        try:
            self.notifier.post("\n".join(prompt))
        except Exception:                                     # noqa: BLE001
            log.debug("posting Slack clarifier prompt failed; skipping wait.")
            return None

        poll_interval_s = 20
        deadline = time.time() + timeout_s
        cursor = self.state.last_side_channel_ts
        answer_bodies: list[str] = []
        cancelled = False
        while time.time() < deadline:
            try:
                msgs = self.notifier.poll_thread_messages(since_ts=cursor)
            except Exception as exc:                          # noqa: BLE001
                log.warning("Slack clarifier poll failed: %s", exc)
                break
            for m in msgs:
                ts = m.get("ts") or ""
                if ts and (cursor or "") < ts:
                    cursor = ts
                    # Advance the shared side-channel cursor so the post-role
                    # `task:` drain doesn't reprocess these same messages.
                    if (self.state.last_side_channel_ts or "") < ts:
                        self.state.last_side_channel_ts = ts
                text = (m.get("text") or "").strip()
                low = text.lower()
                if low.startswith("ans:"):
                    body = text.split(":", 1)[1].strip()
                    if body:
                        answer_bodies.append(body)
                elif low.startswith("task: cancel"):
                    cancelled = True
            if answer_bodies or cancelled:
                break
            time.sleep(poll_interval_s)

        if cancelled:
            try:
                self.notifier.post(
                    ":octagonal_sign: clarifier wait cancelled; "
                    "posting questions to Jira."
                )
            except Exception:                                 # noqa: BLE001
                pass
            return None

        if not answer_bodies:
            try:
                self.notifier.post(
                    f":hourglass: no `ans:` reply within {timeout_label}; "
                    "posting questions to Jira instead."
                )
            except Exception:                                 # noqa: BLE001
                pass
            return None

        qa_pairs = _map_answers_to_questions(questions, answer_bodies)
        answered = sum(1 for p in qa_pairs if p.get("answer"))
        new_result = self._absorb_clarifier_answers(
            clar,
            qa_pairs,
            via="via Slack `ans:` reply",
            summary=(
                f"Resolved via Slack `ans:` reply: "
                f"{answered}/{len(questions)} answered; skipping Jira post."
            ),
            extra_clar_flags={"resolved_via_slack": True},
        )
        try:
            self.notifier.post(
                f":white_check_mark: absorbed {answered}/{len(questions)} "
                "answer(s); continuing the DAG."
            )
        except Exception:                                     # noqa: BLE001
            pass
        self.thinking_log.supervisor_decision(
            "clarifier resolved via Slack",
            f"Operator answered {answered}/{len(questions)} clarifier "
            f"question(s) via a Slack `ans:` reply within {timeout_s}s. Q&A "
            f"absorbed into requirements.scope_summary; Jira comment NOT "
            f"posted. Downstream roles continue with the enriched "
            f"requirements.",
        )
        return new_result

    def _infer_debug_model(self) -> str:
        """Best-effort target model when the operator didn't pin one.

        Picks the first in-scope model from the requirements analyzer; falls
        back to the configured default if none is known yet.
        """
        rp = self.state.requirements_payload or {}
        for name in rp.get("in_scope_models", []) or []:
            if name:
                return name
        return self.input.debug_fallback_model

    # -------------------------------------------------- Slack side-channel
    def _drain_side_tasks(self) -> list[SideTask]:
        """Read new `task:` messages from the parent thread and dispatch them.

        Called after each sub-agent completes (ticket mode only). Honors the
        ``_pause_after_role`` and ``_cancel_requested`` flags by simply
        setting them; the calling loop short-circuits on the next iteration.
        Slack failures are swallowed - the supervisor must never block.
        """
        if not self.notifier or not self.notifier.thread_ts:
            return []
        try:
            msgs = self.notifier.poll_thread_messages(
                since_ts=self.state.last_side_channel_ts,
            )
        except Exception as exc:                              # noqa: BLE001
            log.warning("side-channel poll failed; continuing without it: %s", exc)
            return []
        new_tasks: list[SideTask] = []
        for m in msgs:
            ts = m.get("ts") or ""
            if not ts:
                continue
            # Advance the cursor regardless of whether we acted on it.
            if (self.state.last_side_channel_ts or "") < ts:
                self.state.last_side_channel_ts = ts
            text = (m.get("text") or "").strip()
            if not text.lower().startswith("task:"):
                continue
            body = text.split(":", 1)[1].strip()
            task = SideTask(ts=ts, requester=m.get("user", ""), text=body)
            action, result = self._process_side_task(body)
            task.action = action
            task.result = result
            new_tasks.append(task)
            self.state.side_tasks.append(task)
            try:
                self.notifier.post(
                    f":incoming_envelope: side-task `{action}`: {result}"
                )
            except Exception:                                 # noqa: BLE001
                log.debug("posting side-task ack failed; ignoring.")
            self.thinking_log.side_task(
                requester=task.requester, text=task.text,
                action=task.action, result=task.result,
            )
        return new_tasks

    def _process_side_task(self, body: str) -> tuple[str, str]:
        """Map a free-form `task:` body to (action, result_string).

        First-class commands run immediately; everything else is queued for
        later human / Cursor-agent action.
        """
        low = body.lower().strip()

        if low.startswith("skip "):
            target = body[5:].strip()
            valid_roles = {name for name, _ in self._role_dag()}
            if target in valid_roles:
                if target not in self.input.skip_roles:
                    self.input.skip_roles = self.input.skip_roles + (target,)
                return "skip", f"role `{target}` added to skip list."
            return "skip-rejected", (
                f"unknown role `{target}`. Valid: {sorted(valid_roles)}."
            )

        if low == "pause":
            self._pause_after_role = True
            return "pause", "supervisor will pause after the current role."

        if low == "cancel":
            self._cancel_requested = True
            return "cancel", "supervisor will cancel after the current role."

        if low == "status":
            tail = self.state.role_results[-5:]
            summary = (
                ", ".join(f"{r.role}={r.status.value}" for r in tail)
                or "(no roles completed yet)"
            )
            return "status", f"recent: {summary}"

        if low == "debug" or low.startswith("debug "):
            target = body[5:].strip() if low.startswith("debug ") else ""
            model = target or self._infer_debug_model()
            debug_result = self._dispatch_debugger(
                trigger="side_channel",
                failing_role=None,
                target_model=model,
            )
            if debug_result is None:
                return "debug-skipped", "debugger could not run (no ticket payload yet)."
            top = ""
            try:
                hyps = (debug_result.payload or {}).get("debug", {}).get("hypotheses") or []
                if hyps:
                    top = hyps[0].get("title", "")
            except Exception:                                  # noqa: BLE001
                top = ""
            return "debug", (
                f"ran debugger on `{model}` -> status={debug_result.status.value}"
                + (f"; top hypothesis: {top}" if top else "")
            )

        if low == "quarter-close" or low.startswith("quarter-close "):
            # Optional positional date: `task: quarter-close 2026-02-11`
            target = body[len("quarter-close"):].strip()
            qc = self._dispatch_quarter_close(
                trigger="side_channel",
                as_was_date_override=target or None,
            )
            if qc is None:
                return "quarter-close-skipped", (
                    "no as_was_date supplied and supervisor has no default; "
                    "post `task: quarter-close YYYY-MM-DD`."
                )
            try:
                qc_payload = (qc.payload or {}).get("quarter_close") or {}
                verdict = qc_payload.get("overall_verdict", "pending")
                pipe = qc_payload.get("pipeline_overall_status", "skipped")
            except Exception:                                   # noqa: BLE001
                verdict, pipe = "unknown", "unknown"
            return "quarter-close", (
                f"ran quarter-close-runner -> status={qc.status.value} "
                f"pipeline={pipe} recon={verdict}"
            )

        # Free-form task: queue + acknowledge for human / Cursor coding agent.
        snippet = body[:200] + ("..." if len(body) > 200 else "")
        return "queued", f"queued for human/Cursor agent: \"{snippet}\""

    def _role_reason(self, role: str) -> str:
        """One-liner shown in the thinking log when a role is about to run."""
        return _ROLE_REASONS.get(role, "")

    def _aggregate_status(self) -> RoleStatus:
        statuses = [r.status for r in self.state.role_results]
        if RoleStatus.FAIL in statuses:
            return RoleStatus.FAIL
        if RoleStatus.NEEDS_INPUT in statuses:
            return RoleStatus.NEEDS_INPUT
        if RoleStatus.WARN in statuses:
            return RoleStatus.WARN
        return RoleStatus.OK

    # ----------------------------------- typed accessors with stub fallback
    # In real runs, missing upstream payload returns RoleResult(FAIL) so the
    # supervisor halts. In dry-run (plan_only), we substitute a synthetic
    # stub so the downstream sub-agent's `plan(...)` can render meaningful
    # output for the user.
    def _ticket_or_stub(self, role: str, plan_only: bool):
        from agents.arr_quarter_close.contracts import TicketSpec
        if self.state.ticket_payload:
            return TicketSpec(**self.state.ticket_payload)
        if plan_only:
            return TicketSpec(
                ticket_key=self.input.ticket_key or "EDAEM-FAKE",
                summary="(stub for dry-run)",
                status="(unknown)",
                assignee=None,
                reporter=None,
            )
        return RoleResult(role=role, status=RoleStatus.FAIL,
                          summary="jira-intake produced no ticket payload.")

    def _requirements_or_stub(self, role: str, plan_only: bool):
        from agents.arr_quarter_close.contracts import KPISpec, RequirementsSpec
        if self.state.requirements_payload:
            rp = dict(self.state.requirements_payload)
            rp["kpis"] = [KPISpec(**k) for k in rp.get("kpis", []) or []]
            return RequirementsSpec(**rp)
        if plan_only:
            return RequirementsSpec(
                ticket_key=self.input.ticket_key or "EDAEM-FAKE",
                scope_summary="(stub for dry-run)",
                in_scope_models=[],
                questions=["(stub) no upstream requirements payload"],
                confidence="low",
            )
        return RoleResult(role=role, status=RoleStatus.FAIL,
                          summary="requirements-analyzer produced no payload.")

    def _validation_or_stub(self, role: str, plan_only: bool):
        from agents.arr_quarter_close.contracts import (
            CodeFindings, DataFindings, ValidationReport,
        )
        if self.state.validation_payload:
            vp = dict(self.state.validation_payload)
            vp["code"] = CodeFindings(**vp["code"])
            vp["data"] = DataFindings(**vp["data"])
            return ValidationReport(**vp)
        if plan_only:
            return ValidationReport(
                ticket_key=self.input.ticket_key or "EDAEM-FAKE",
                code=CodeFindings(),
                data=DataFindings(),
                risks=["(stub) no upstream validation payload"],
                proposed_changes=[],
            )
        return RoleResult(role=role, status=RoleStatus.FAIL,
                          summary="code-data-validator produced no payload.")

    def _implementation_or_stub(self, role: str, plan_only: bool):
        from agents.arr_quarter_close.contracts import FileEdit, ImplementationResult
        if self.state.implementation_payload:
            ip = dict(self.state.implementation_payload)
            ip["edits"] = [FileEdit(**e) for e in ip.get("edits", []) or []]
            return ImplementationResult(**ip)
        if plan_only:
            return ImplementationResult(
                ticket_key=self.input.ticket_key or "EDAEM-FAKE",
                branch_name="feature/edaem-fake-stub",
                edits=[],
            )
        return RoleResult(role=role, status=RoleStatus.FAIL,
                          summary="implementer produced no payload.")

    def _test_report_or_stub(self, role: str, plan_only: bool):
        from agents.arr_quarter_close.contracts import TestReport
        if self.state.test_report_payload:
            return TestReport(**self.state.test_report_payload)
        if plan_only:
            return TestReport(ticket_key=self.input.ticket_key or "EDAEM-FAKE")
        return RoleResult(role=role, status=RoleStatus.FAIL,
                          summary="test-runner produced no payload.")

    def _ci_report_or_stub(self, role: str, plan_only: bool):
        from agents.arr_quarter_close.contracts import CIReport
        if self.state.ci_payload:
            return CIReport(**self.state.ci_payload)
        if plan_only:
            return CIReport(
                ticket_key=self.input.ticket_key or "EDAEM-FAKE",
                pr_number=0, final_state="(dry-run stub)",
            )
        return RoleResult(role=role, status=RoleStatus.FAIL,
                          summary="ci-monitor produced no payload.")

    def _cd_report_or_stub(self, role: str, plan_only: bool):
        from agents.arr_quarter_close.contracts import CDReport
        if self.state.cd_payload:
            return CDReport(**self.state.cd_payload)
        if plan_only:
            return CDReport(
                ticket_key=self.input.ticket_key or "EDAEM-FAKE",
                final_state="(dry-run stub)",
            )
        return RoleResult(role=role, status=RoleStatus.FAIL,
                          summary="cd-monitor produced no payload.")


# Per-role one-liner explanations written into the thinking log when a role
# starts. Surfaces *why* the supervisor is invoking each sub-agent without
# the operator needing to read the architecture doc.
_ROLE_REASONS: dict[str, str] = {
    "jira-intake":            "Pull ticket payload (curl + ADF flatten) to seed every downstream sub-agent.",
    "requirements-analyzer":  "Translate the ticket into a KPI spec; emit open questions.",
    "code-data-validator":    "Scan repo + emit Snowflake validation SQL (waterfall / parity / baselines).",
    "clarifier":              "Surface any open questions to Jira before code changes (pause unless full_auto).",
    "implementer":            "Create feature branch + LLM edit prompt; signal snapshot rebuild if needed.",
    "test-runner":            "Run pytest + dbt test selectors; capture junit + dbt artifacts.",
    "pr-author":              "Compose PR (title/body/reviewers/labels), push branch, gh pr create (pause unless full_auto).",
    "ci-monitor":             "Poll CI every 10m + Slack heartbeat; on green, emit finance_dev validation SQL.",
    "cd-monitor":             "Watch merge + dbt Cloud deploy; on green, emit finance_qa validation SQL.",
    "qa-handoff":             "Post 'Ready for QA' Jira comment with results table + artifacts (pause unless full_auto).",
    "debugger":               "Walk lineage + build per-stage matrix + rank hypotheses + draft Jira ADF shaped by ticket type.",
    "quarter-close-runner":   "Run ARR dbt pipeline (orchestrator manifest) + build 7-check recon matrix (waterfall, totals, parity, currency, account continuity).",
}


def _latest_known_close_date() -> Optional[str]:
    """Return the most recent FY quarter-end snapshot date shipped with the
    repo. Used by the quarter-close-runner when the operator didn't pass
    one explicitly (e.g. via Slack `task: quarter-close`).
    """
    from agents.arr_quarter_close.core import KNOWN_FY_CLOSE_DATES
    if not KNOWN_FY_CLOSE_DATES:
        return None
    return sorted(KNOWN_FY_CLOSE_DATES)[-1]


def _prior_known_close_date(as_was: str) -> Optional[str]:
    """Given a snapshot date, return the prior FY close from the shipped list.

    Used to auto-populate the period-over-period baseline when the
    operator didn't pass ``--quarter-close-baseline-date``. Returns
    ``None`` if no earlier date exists (e.g. earliest snapshot).
    """
    from agents.arr_quarter_close.core import KNOWN_FY_CLOSE_DATES
    earlier = sorted(d for d in KNOWN_FY_CLOSE_DATES if d < as_was)
    return earlier[-1] if earlier else None


def _extract_questions_from_clar_payload(clar: dict) -> list[str]:
    """Pull the list of human-readable questions out of a clarifier payload.

    Prefers the markdown form (numbered lines) because it's what the
    operator already understands. Falls back to walking the ADF
    orderedList if the markdown is missing.
    """
    md = (clar or {}).get("question_block_markdown") or ""
    questions: list[str] = []
    for line in md.splitlines():
        s = line.strip()
        if not s or len(s) < 3:
            continue
        # Lines that look like "1. <text>" / "12) <text>"
        if s[0].isdigit():
            # strip leading "1." / "12) " etc.
            for prefix_end in range(1, 6):
                if prefix_end < len(s) and s[prefix_end] in {".", ")"}:
                    rest = s[prefix_end + 1:].strip()
                    if rest:
                        questions.append(rest)
                    break
    if questions:
        return questions
    # ADF fallback
    adf = (clar.get("adf_payload") or {}).get("body") or {}
    for node in adf.get("content", []) or []:
        if node.get("type") == "orderedList":
            for item in node.get("content", []) or []:
                inner_paras = item.get("content", []) or []
                for p in inner_paras:
                    text_runs = p.get("content", []) or []
                    text = "".join(r.get("text", "") for r in text_runs if r.get("type") == "text")
                    if text:
                        questions.append(text)
    return questions


def _split_numbered_answers(text: str, expected: int) -> list[str]:
    """Split a single free-text answer into segments by numbered markers.

    Recognizes markers like ``1)`` ``2.`` ``3:`` ``4-`` at line start or
    after whitespace. Returns ``[]`` when fewer than 2 markers are found
    (so callers fall back to positional / combined mapping). Only the
    segment text after each marker is returned, in order of appearance.
    """
    if not text:
        return []
    matches = list(re.finditer(r"(?:(?<=\s)|^)(\d{1,2})[\).:\-]\s+", text))
    if len(matches) < 2:
        return []
    segments: list[str] = []
    for idx, mobj in enumerate(matches):
        start = mobj.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        segments.append(text[start:end].strip())
    return segments


def _map_answers_to_questions(
    questions: list[str], answer_bodies: list[str]
) -> list[dict]:
    """Best-effort map of ``ans:`` reply bodies to clarifier questions.

    Strategy, in priority order:

    1. **Numbered split** - one combined reply like
       ``1) USD_HIST 2) 2026-05-11 3) account grain`` split on the markers.
    2. **Positional** - N separate ``ans:`` lines for N questions.
    3. **Combined fallback** - attach the whole reply to the first question
       and point the rest at it, so every question is marked answered (and
       therefore cleared from the open-questions list downstream).
    """
    combined = "\n".join(answer_bodies).strip()

    if len(answer_bodies) == 1:
        segments = _split_numbered_answers(combined, len(questions))
        if segments and len(segments) == len(questions):
            return [
                {"question": q, "answer": a.strip()}
                for q, a in zip(questions, segments)
            ]

    if len(answer_bodies) == len(questions):
        return [
            {"question": q, "answer": a.strip()}
            for q, a in zip(questions, answer_bodies)
        ]

    # Fallback: combined block on the first question, pointers on the rest.
    pairs = [{"question": questions[0], "answer": combined}]
    for q in questions[1:]:
        pairs.append(
            {"question": q, "answer": "(answered together in the combined reply above)"}
        )
    return pairs


def _crash_to_result(role_name: str, exc: BaseException, *, phase: str) -> RoleResult:
    """Convert an uncaught sub-agent exception into a RoleResult(FAIL).

    The supervisor's contract is that a sub-agent always returns a
    ``RoleResult``; a Python exception breaks that contract and would
    drop the entire DAG, the thinking-log footer, and the Slack finish
    banner. Wrapping the call site lets us treat the crash like any
    other FAIL (it gets a pause point, auto-debug, audit trail).

    The payload carries the exception type, message, and a short
    traceback tail so the operator can see the root cause without
    re-running. We also surface a specific, actionable hint when we
    recognize the error (e.g. ``rg`` missing).
    """
    import traceback

    tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
    tb_tail = "".join(tb)[-2000:]
    exc_type = type(exc).__name__
    msg = str(exc)
    hint = _hint_for_exception(exc, msg)
    summary = (
        f"{role_name} crashed during {phase} ({exc_type}): {msg[:160]}"
        + (f" - hint: {hint}" if hint else "")
    )
    return RoleResult(
        role=role_name,
        status=RoleStatus.FAIL,
        summary=summary,
        payload={
            "crash": {
                "phase": phase,
                "exc_type": exc_type,
                "message": msg,
                "hint": hint,
                "traceback_tail": tb_tail,
            }
        },
        pause_reason=hint or f"Sub-agent `{role_name}` raised {exc_type}; see traceback in payload.",
    )


def _hint_for_exception(exc: BaseException, msg: str) -> str:
    """Map common errors to an actionable one-liner."""
    if isinstance(exc, FileNotFoundError):
        lower = msg.lower()
        if "'rg'" in msg or "ripgrep" in lower or "rg:" in lower:
            return (
                "ripgrep is required for repo scans; install with "
                "`brew install ripgrep` (mac) or `apt install ripgrep` (linux)."
            )
        if "'gh'" in msg:
            return "GitHub CLI is required; install with `brew install gh` then `gh auth login`."
        if "'dbt'" in msg:
            return "dbt is not on PATH; activate the project venv or `pip install dbt-snowflake`."
        if "'slk'" in msg:
            return "slk CLI not found; Slack side-channel will be disabled (continue without `--slack-channel`)."
        return f"required external command not found ({msg})."
    if isinstance(exc, PermissionError):
        return "permission denied; check the file/socket permissions and re-run."
    return ""


def _safe_payload(obj) -> dict:
    """Best-effort dict coercion for the thinking-log payload preview."""
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "as_dict"):
        try:
            return obj.as_dict()
        except Exception:                            # noqa: BLE001
            return {"repr": repr(obj)[:500]}
    return {"repr": repr(obj)[:500]}


def _step_to_role_status(s: StepStatus) -> RoleStatus:
    return {
        StepStatus.SUCCESS: RoleStatus.OK,
        StepStatus.WARN:    RoleStatus.WARN,
        StepStatus.FAIL:    RoleStatus.FAIL,
        StepStatus.SKIPPED: RoleStatus.SKIPPED,
        StepStatus.PENDING: RoleStatus.NEEDS_INPUT,
        StepStatus.RUNNING: RoleStatus.NEEDS_INPUT,
    }[s]


def _close_to_role_status(status_str: str) -> str:
    return {
        "success": "ok",
        "warn":    "warn",
        "fail":    "fail",
        "skipped": "skipped",
        "pending": "needs_input",
        "running": "needs_input",
    }.get(status_str.lower(), status_str)
