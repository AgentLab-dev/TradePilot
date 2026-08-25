"""Command-line entrypoint for the ARR Quarter Close orchestrator + supervisor.

Two modes:

* **scheduled** (default when ``--as-was-date`` is given alone) - runs the
  existing ``ARRCloseOrchestrator``. This is the original behavior; no
  ticket required.
* **ticket** (when ``--ticket`` is given) - runs the Finance ARR Quarter
  Close (FQC-ARR) supervisor with the 10 sub-agent DAG. Add ``--as-was-date``
  to also rebuild a snapshot after the implementer.

Examples
--------
Plan only (no execution):

    python -m agents.arr_quarter_close.cli \\
        --as-was-date 2026-02-11 \\
        --project-dir . \\
        --dry-run

Run a full close (validation included by default):

    python -m agents.arr_quarter_close.cli \\
        --as-was-date 2026-02-11 \\
        --project-dir . \\
        --target qa

Drive a ticket end-to-end (smart-gated, dry-run plan):

    python -m agents.arr_quarter_close.cli \\
        --ticket EDAEM-3725 \\
        --project-dir . \\
        --mode ticket \\
        --dry-run

Drive a ticket end-to-end, autonomous (no pauses):

    python -m agents.arr_quarter_close.cli \\
        --ticket EDAEM-3725 \\
        --project-dir . \\
        --mode ticket \\
        --auto \\
        --slack-channel <YOUR_SLACK_USER_ID>
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from agents.arr_quarter_close.contracts import (
    DEFAULT_LLM_MODEL,
    DEFAULT_LLM_MODEL_ENV,
    AuthMode,
    RoleStatus,
    resolve_default_llm_model,
)
from agents.arr_quarter_close.core import (
    KNOWN_FY_CLOSE_DATES,
    ARRCloseConfig,
    ARRCloseOrchestrator,
    StepStatus,
)
from agents.arr_quarter_close.supervisor import Supervisor, SupervisorInput


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="arr-quarter-close",
        description="Run the eda-dbt-em ARR quarter close - scheduled or ticket-driven.",
    )
    p.add_argument("--as-was-date", required=False, help="YYYY-MM-DD snapshot date.")
    p.add_argument(
        "--ticket",
        default=None,
        help="Jira ticket key (e.g. EDAEM-3725) to drive in ticket mode.",
    )
    p.add_argument(
        "--mode",
        choices=("auto", "scheduled", "ticket"),
        default="auto",
        help="auto: pick from inputs; scheduled: orchestrator only; ticket: supervisor.",
    )
    p.add_argument(
        "--auth-mode",
        choices=("full_auto", "smart_gates", "gated_minimal", "gated_full"),
        default="smart_gates",
        help="Authorization for sub-agent writes. Default: smart_gates.",
    )
    p.add_argument(
        "--auto",
        action="store_true",
        help="Shortcut: --auth-mode full_auto.",
    )
    p.add_argument(
        "--model",
        default=None,
        help=(
            "LLM model the LLM-driven sub-agents (requirements-analyzer, "
            "clarifier, implementer) and the Cursor SDK runner should "
            "advertise as `preferred_model` on their pause result. "
            f"Default: {DEFAULT_LLM_MODEL} (override precedence: --model > "
            f"${DEFAULT_LLM_MODEL_ENV} env var > DEFAULT_LLM_MODEL constant). "
            "Allowed slugs include claude-opus-4-7-thinking-xhigh, "
            "claude-opus-4-8-thinking-high, claude-4.6-opus-high-thinking, "
            "gpt-5.5-medium, gpt-5.3-codex, gemini-3.1-pro."
        ),
    )
    p.add_argument(
        "--slack-channel",
        default="",
        help="Slack channel id (C... / G... / D...) or user id (U...). Enables per-role thread pings + CI/CD heartbeats.",
    )
    p.add_argument(
        "--no-slack",
        dest="slack_notify",
        action="store_false",
        default=True,
        help="Disable per-role Slack notifications (CI/CD monitors may still post their own heartbeats).",
    )
    p.add_argument(
        "--skip",
        action="append",
        default=[],
        help="Sub-agent role to skip (repeatable). e.g. --skip ci-monitor.",
    )
    # --- Attach ci-monitor / cd-monitor to an existing PR -----------------
    # When the PR was opened outside the agent (manual `gh pr create`, or
    # the upstream DAG paused before pr-author), the ci/cd monitors have
    # no PR url/number to poll. These overrides plumb directly into the
    # supervisor so you can run e.g.:
    #
    #   fqc-arr --ticket EDAEM-3723 --pr-number 472 \
    #           --slack-channel <YOUR_SLACK_USER_ID> \
    #           --skip jira-intake --skip requirements-analyzer \
    #           --skip clarifier --skip code-data-validator \
    #           --skip implementer --skip test-runner --skip pr-author
    p.add_argument(
        "--pr-number",
        dest="pr_number_override",
        type=int,
        default=None,
        help=(
            "Attach ci-monitor / cd-monitor to an existing PR number. "
            "Bypasses the pr-author sub-agent's payload. Pair with --skip "
            "for every role upstream of ci-monitor."
        ),
    )
    p.add_argument(
        "--pr-url",
        dest="pr_url_override",
        default=None,
        help=(
            "Full PR url, paired with --pr-number. If omitted but "
            "--pr-number is set, the watcher derives the url from the "
            "active git remote."
        ),
    )
    p.add_argument(
        "--check-name",
        dest="ci_check_name_override",
        default=None,
        help=(
            "GitHub check name pattern the ci-monitor polls for "
            "(substring match). Default: ci/dbt_cloud. Override when the "
            "context was renamed, e.g. --check-name 'dbtcloud-codevalidate'."
        ),
    )
    p.add_argument(
        "--dbt-cloud-run-id",
        dest="dbt_cloud_run_id_override",
        type=int,
        default=None,
        help=(
            "Attach cd-monitor to a specific dbt Cloud run id (skip the "
            "auto-discovery via PR webhook payload)."
        ),
    )
    p.add_argument(
        "--notify",
        action="append",
        default=[],
        help=(
            "Additional Slack stakeholder to notify (repeatable). Accepts "
            "Slack user id (U.../W...), full handle (jane.doe), email "
            "([REDACTED_EMAIL]), or first-name prefix (jane). "
            "Resolved at startup against "
            "agents/arr_quarter_close/data/slack_directory.json. "
            "Sub-agents can fan-out heartbeats / @-mentions to these uids."
        ),
    )
    p.add_argument(
        "--thinking-log",
        default=None,
        help=(
            "Path for the live Markdown thinking log. "
            "Default: <project_dir>/runs/thinking/<UTC_ts>_<slug>.md. "
            "Tail with `tail -f <path>` during a run to watch progress."
        ),
    )
    p.add_argument(
        "--no-thinking-log",
        dest="thinking_log_enabled",
        action="store_false",
        default=True,
        help="Disable the live thinking-log Markdown file.",
    )
    p.add_argument(
        "--debug-model",
        default=None,
        help=(
            "After the DAG, run the on-demand debugger sub-agent against this "
            "model (e.g. `arr_line_categories`). Walks lineage, builds the "
            "per-stage 7-col matrix, ranks hypotheses, drafts a Jira ADF "
            "comment shaped by ticket type. Pauses before posting unless --auto."
        ),
    )
    p.add_argument(
        "--debug",
        dest="debug_default_model",
        action="store_true",
        help=(
            "Shortcut: --debug-model <first in_scope_model or arr_line_categories>."
        ),
    )
    p.add_argument(
        "--no-debug-on-failure",
        dest="debug_on_failure",
        action="store_false",
        default=True,
        help=(
            "Disable auto-dispatch of the debugger sub-agent when any role "
            "returns FAIL (default: on; emits a debug bundle alongside the "
            "pause point)."
        ),
    )
    p.add_argument(
        "--clarifier-interactive-timeout",
        dest="clarifier_interactive_timeout_s",
        type=int,
        default=600,
        help=(
            "Seconds to wait for the operator to answer clarifier questions "
            "interactively in the terminal before falling back to a Jira "
            "comment. Default: 600 (10 min). Set to 0 to skip the "
            "interactive ask and go straight to the pause-and-post flow."
        ),
    )
    p.add_argument(
        "--no-clarifier-interactive",
        dest="clarifier_interactive_timeout_s",
        action="store_const",
        const=0,
        help="Shortcut: --clarifier-interactive-timeout 0.",
    )
    p.add_argument(
        "--clarifier-slack-timeout",
        dest="clarifier_slack_timeout_s",
        type=int,
        default=1800,
        help=(
            "Seconds to wait for an `ans:`-prefixed reply in the live Slack "
            "thread before falling back to a Jira comment. Used when the "
            "interactive terminal path is unavailable or times out (e.g. "
            "under --auto / --no-clarifier-interactive). Reuses the same "
            "thread as the `task:` side-channel - no daemon. Default: 1800 "
            "(30 min). Set to 0 to disable the Slack wait. Requires "
            "--slack-channel."
        ),
    )
    p.add_argument(
        "--no-clarifier-slack",
        dest="clarifier_slack_timeout_s",
        action="store_const",
        const=0,
        help="Shortcut: --clarifier-slack-timeout 0.",
    )
    # --- Quarter-close-runner (sub-agent 12, on-demand) -----------------
    p.add_argument(
        "--quarter-close",
        action="store_true",
        help=(
            "After the DAG (or as the primary action in scheduled mode), "
            "run the quarter-close-runner sub-agent: executes the ARR "
            "dbt pipeline and builds the 7-check recon matrix "
            "(waterfall / totals / parity / currency / continuity)."
        ),
    )
    p.add_argument(
        "--quarter-close-skip-pipeline",
        action="store_true",
        help=(
            "Recon-only mode for the quarter-close-runner: skip the "
            "ARRCloseOrchestrator dbt pipeline phase and only build the "
            "tie-out matrix. Use when the snapshot is already loaded."
        ),
    )
    p.add_argument(
        "--quarter-close-baseline-date",
        dest="quarter_close_baseline_as_was_date",
        default=None,
        help=(
            "Prior-quarter snapshot date (YYYY-MM-DD) the recon ties out "
            "against. Defaults to the prior FY close in KNOWN_FY_CLOSE_DATES."
        ),
    )
    p.add_argument(
        "--quarter-close-target-db",
        default="certified_dev",
        help="Snowflake database the dbt pipeline writes to. Default: certified_dev.",
    )
    p.add_argument(
        "--quarter-close-baseline-db",
        default="finance_prod",
        help="Snowflake database the recon ties out against. Default: finance_prod.",
    )
    p.add_argument(
        "--quarter-close-tolerance-pct",
        type=float,
        default=1.0,
        help=(
            "Variance threshold for recon checks: < tol = pass, < 5*tol = "
            "warn, else fail. Default: 1.0%%."
        ),
    )
    # --- Continuous learning -----------------------------------------------
    p.add_argument(
        "--reflect",
        action="store_true",
        help=(
            "Skip the DAG and only run the daily-reflection sub-agent: scans "
            "recent thinking logs, extracts lessons, dedupes, promotes "
            "lessons that have re-occurred >=3 times. Forces a fresh pass "
            "even if reflection already ran today."
        ),
    )
    p.add_argument(
        "--reflect-look-back-days",
        type=int,
        default=1,
        help="How many days of thinking logs the reflection pass scans. Default: 1.",
    )
    p.add_argument(
        "--reflect-wide-scan",
        action="store_true",
        help=(
            "Also scan runs/*.log for Python tracebacks + structured "
            "[error]/[fatal] lines (in addition to runs/thinking/*.md). "
            "Auto-enabled by --learn. Useful for the twice-daily scheduled "
            "passes that need to catch crashes outside thinking-log tracking."
        ),
    )
    p.add_argument(
        "--learn",
        action="store_true",
        help=(
            "Scheduled-pass shortcut: --reflect --reflect-look-back-days 7 "
            "--reflect-wide-scan. Reads every learning source we have, dedupes, "
            "promotes lessons crossing occurrence_count >= 3, writes an audit "
            "report. Triggered twice daily by the launchd jobs installed under "
            "~/Library/LaunchAgents/com.example.fqcarr.learn-{am,pm}.plist."
        ),
    )
    p.add_argument(
        "--no-auto-reflect",
        dest="auto_reflect",
        action="store_false",
        default=True,
        help=(
            "Disable the end-of-run auto-reflection. Default: ON - the "
            "supervisor runs daily-reflection once per UTC day at the end "
            "of the run so lessons keep accumulating."
        ),
    )
    p.add_argument(
        "--show-lessons",
        nargs="?",
        const="ALL",
        default=None,
        help=(
            "Print accumulated lessons and exit. Optional role filter "
            "(e.g. --show-lessons debugger). 'ALL' (default when flag is "
            "passed without value) dumps every role's lessons in a table."
        ),
    )
    p.add_argument(
        "--no-inject-lessons",
        dest="inject_lessons",
        action="store_false",
        default=True,
        help=(
            "Disable injection of recorded lessons into the LLM-driven sub-agent "
            "prompts. Default: ON - lessons are included so the agent learns "
            "from prior runs."
        ),
    )
    p.add_argument(
        "--max-lessons-per-role",
        type=int,
        default=8,
        help="Cap how many lessons the supervisor injects per role. Default: 8.",
    )
    p.add_argument(
        "--project-dir",
        default=".",
        help="dbt project directory (default: cwd).",
    )
    p.add_argument("--profiles-dir", default=None)
    p.add_argument("--target", default=None, help="dbt target (e.g. dev, qa, prod).")
    p.add_argument(
        "--heavy-warehouse",
        default=None,
        help="Override em_heavy_warehouse for the heavy ARR models.",
    )
    p.add_argument(
        "--refresh-dashboards",
        action="store_true",
        help="Also refresh data_product/view dashboards.",
    )
    p.add_argument(
        "--no-validation",
        dest="run_validation",
        action="store_false",
        help="Skip the validation step. Default: run validation.",
    )
    p.add_argument(
        "--no-ia-migration-tests",
        dest="include_ia_migration_tests",
        action="store_false",
        help="Skip the tag:ia_migration recon step.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned dbt commands without executing them.",
    )
    p.add_argument(
        "--no-fail-fast",
        dest="fail_fast",
        action="store_false",
        help="Continue running on first failure (default: stop on first hard fail).",
    )
    p.add_argument(
        "--json",
        dest="emit_json",
        action="store_true",
        help="Emit a single JSON object summarizing the run.",
    )
    p.add_argument("-v", "--verbose", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # Promote --model to the env var the sub-agents resolve against, so a
    # single CLI flag flows through to every LLM-driven leaf without
    # threading a parameter through 13 sub-agent contracts.
    if args.model:
        import os
        os.environ[DEFAULT_LLM_MODEL_ENV] = args.model
    logging.getLogger(__name__).info(
        "fqc-arr preferred LLM model = %s", resolve_default_llm_model()
    )

    # --show-lessons exits before any DAG / supervisor work.
    if args.show_lessons is not None:
        return _show_lessons(args)

    # --learn = scheduled-pass shortcut for --reflect with the widest possible
    # scope (7-day lookback + run-log traceback scout). The twice-daily
    # launchd jobs use this entrypoint.
    if args.learn:
        args.reflect = True
        args.reflect_wide_scan = True
        # Only widen the lookback if the operator didn't override it explicitly.
        if args.reflect_look_back_days == 1:
            args.reflect_look_back_days = 7

    # --reflect runs the daily-reflection sub-agent in isolation.
    if args.reflect:
        return _run_reflect_only(args)

    mode = _resolve_mode(args)
    # --quarter-close always routes through the supervisor so the
    # on-demand quarter-close-runner sub-agent gets dispatched (with
    # its thinking-log entry, Slack ping, and recon matrix). Otherwise
    # the standalone orchestrator path skips the dispatch hook.
    if mode == "scheduled" and not args.quarter_close:
        return _run_scheduled(args)
    if mode == "ticket":
        return _run_supervisor(args, include_scheduled=False)
    # both, OR (scheduled + --quarter-close)
    return _run_supervisor(args, include_scheduled=True)


def _resolve_mode(args) -> str:
    if args.mode == "scheduled":
        if not args.as_was_date:
            print("[error] --mode scheduled requires --as-was-date", file=sys.stderr)
            sys.exit(2)
        return "scheduled"
    if args.mode == "ticket":
        if not args.ticket:
            print("[error] --mode ticket requires --ticket", file=sys.stderr)
            sys.exit(2)
        return "both" if args.as_was_date else "ticket"
    # auto
    if args.ticket and args.as_was_date:
        return "both"
    if args.ticket:
        return "ticket"
    if args.as_was_date:
        return "scheduled"
    print("[error] supply --as-was-date and/or --ticket", file=sys.stderr)
    sys.exit(2)


def _run_scheduled(args) -> int:
    if args.as_was_date not in KNOWN_FY_CLOSE_DATES:
        print(
            f"[warn] {args.as_was_date} is not in the canonical FY close list "
            f"({', '.join(KNOWN_FY_CLOSE_DATES)}). Continuing anyway.",
            file=sys.stderr,
        )

    cfg = ARRCloseConfig(
        as_was_date=args.as_was_date,
        project_dir=Path(args.project_dir),
        profiles_dir=Path(args.profiles_dir) if args.profiles_dir else None,
        target=args.target,
        heavy_warehouse=args.heavy_warehouse,
        refresh_dashboards=args.refresh_dashboards,
        run_validation=args.run_validation,
        include_ia_migration_tests=args.include_ia_migration_tests,
        dry_run=args.dry_run,
        fail_fast=args.fail_fast,
    )

    result = ARRCloseOrchestrator(cfg).run()

    if args.emit_json:
        print(json.dumps(result.as_dict(), indent=2))
    else:
        _pretty_print(result)

    if result.overall_status == StepStatus.FAIL:
        return 2
    if result.overall_status == StepStatus.WARN:
        return 1
    return 0


def _run_supervisor(args, include_scheduled: bool) -> int:
    auth_mode = AuthMode.FULL_AUTO if args.auto else AuthMode(args.auth_mode)
    debug_model = args.debug_model
    if not debug_model and args.debug_default_model:
        debug_model = "arr_line_categories"   # supervisor will override from in_scope_models
    sup_input = SupervisorInput(
        project_dir=Path(args.project_dir),
        ticket_key=args.ticket,
        as_was_date=args.as_was_date if include_scheduled else None,
        auth_mode=auth_mode,
        slack_channel=args.slack_channel,
        slack_notify=args.slack_notify,
        pr_url_override=args.pr_url_override,
        pr_number_override=args.pr_number_override,
        dbt_cloud_run_id_override=args.dbt_cloud_run_id_override,
        ci_check_name_override=args.ci_check_name_override,
        dry_run=args.dry_run,
        skip_roles=tuple(args.skip),
        notify=tuple(args.notify),
        thinking_log_enabled=args.thinking_log_enabled,
        thinking_log_path=Path(args.thinking_log) if args.thinking_log else None,
        debug_on_failure=args.debug_on_failure,
        debug_model=debug_model,
        clarifier_interactive_timeout_s=args.clarifier_interactive_timeout_s,
        clarifier_slack_timeout_s=args.clarifier_slack_timeout_s,
        quarter_close=args.quarter_close,
        quarter_close_baseline_as_was_date=args.quarter_close_baseline_as_was_date,
        quarter_close_target_db=args.quarter_close_target_db,
        quarter_close_baseline_db=args.quarter_close_baseline_db,
        quarter_close_tolerance_pct=args.quarter_close_tolerance_pct,
        quarter_close_skip_pipeline=args.quarter_close_skip_pipeline,
        auto_reflect=args.auto_reflect,
        reflect_look_back_days=args.reflect_look_back_days,
        reflect_wide_scan=args.reflect_wide_scan,
        inject_lessons=args.inject_lessons,
        max_lessons_per_role=args.max_lessons_per_role,
    )
    sup = Supervisor(sup_input)
    if sup.thinking_log.enabled and not args.emit_json:
        _print_thinking_log_banner(
            sup.thinking_log.path, when="open before the run starts"
        )
    report = sup.run()

    if args.emit_json:
        print(json.dumps(report.as_dict(), indent=2, default=str))
    else:
        _pretty_print_supervisor(report)
        if sup.thinking_log.enabled:
            _print_thinking_log_banner(
                sup.thinking_log.path, when="full transcript of this run"
            )

    if report.overall_status == RoleStatus.FAIL:
        return 2
    if report.overall_status in {RoleStatus.WARN, RoleStatus.NEEDS_INPUT}:
        return 1
    return 0


def _print_thinking_log_banner(path: Path, *, when: str) -> None:
    """Print a visible banner pointing at the live thinking-log file.

    Goes to stdout (after the pretty-print) so caller order is preserved
    and the line wrapping isn't interleaved with stderr log noise. Both
    the absolute path and a ``file://`` URL are emitted on their own
    lines so terminals can auto-detect them as clickable links:

    * Cursor IDE terminal: Cmd+Click the absolute path opens it in
      the editor (the operator's "side screen").
    * iTerm2 / VS Code terminal: Cmd+Click on the ``file://`` URL
      opens it in the default Markdown viewer.

    A ``tail -f`` hint is included so the operator can stream the log
    live without leaving the terminal. The caller is responsible for
    gating this on ``not args.emit_json`` so JSON consumers aren't
    disturbed.
    """
    abs_path = Path(path).resolve()
    bar = "=" * 78
    print("")
    print(bar)
    print(f"  FQC-ARR thinking log ({when}):")
    print(f"    {abs_path}")
    print(f"    file://{abs_path}")
    print( "  Cmd+Click the path to open it in Cursor (or any terminal),")
    print( "  or tail the live transcript:")
    print(f"    tail -f \"{abs_path}\"")
    print(bar)
    print("")
    sys.stdout.flush()


def _pretty_print_supervisor(report) -> None:
    from agents.arr_quarter_close.supervisor import SUPERVISOR_DISPLAY_NAME
    print(f"\n{SUPERVISOR_DISPLAY_NAME} - mode={report.mode} ticket={report.ticket_key}")
    print(f"Status: {report.overall_status.value.upper()}  "
          f"(elapsed {report.elapsed_s:.1f}s, {len(report.role_results)} roles)")
    print("-" * 78)
    for r in report.role_results:
        rstatus = r.status.value if hasattr(r.status, "value") else r.status
        print(f"  [{rstatus:>12}]  {r.role:24s}  {r.summary[:80]}")
    if report.pause_points:
        print("\nPAUSE:")
        for p in report.pause_points:
            print(f"  - {p['role']}: {p['reason']}")
    print()


def _show_lessons(args) -> int:
    from agents.arr_quarter_close.lessons import (
        get_recorder,
        render_lessons_table,
    )
    recorder = get_recorder(Path(args.project_dir))
    everything = recorder.all_lessons()
    if args.show_lessons and args.show_lessons != "ALL":
        role = args.show_lessons.strip()
        filtered = {k: v for k, v in everything.items() if k == role}
        if not filtered:
            print(f"(no lessons captured yet for role `{role}`)")
            return 0
        print(render_lessons_table(filtered))
    else:
        print(render_lessons_table(everything))
    refl = recorder.reflection_log(last_n=5)
    if refl:
        print("\n--- recent reflection passes ---")
        for r in refl:
            print(
                f"  {r['ts']}: +{r.get('lessons_added',0)} added, "
                f"+{r.get('lessons_promoted',0)} promoted"
                + (f" - {r.get('notes')}" if r.get("notes") else "")
            )
    return 0


def _run_reflect_only(args) -> int:
    auth_mode = AuthMode.FULL_AUTO if args.auto else AuthMode(args.auth_mode)
    sup_input = SupervisorInput(
        project_dir=Path(args.project_dir),
        ticket_key=args.ticket,                       # both optional in reflect mode
        as_was_date=args.as_was_date,
        auth_mode=auth_mode,
        slack_channel=args.slack_channel,
        slack_notify=False,                            # reflection is internal
        dry_run=False,
        thinking_log_enabled=args.thinking_log_enabled,
        thinking_log_path=Path(args.thinking_log) if args.thinking_log else None,
        reflect_only=True,
        reflect_look_back_days=args.reflect_look_back_days,
        reflect_wide_scan=args.reflect_wide_scan,
        auto_reflect=False,
        inject_lessons=False,                          # reflect-only doesn't use prompts
    )
    sup = Supervisor(sup_input)
    if sup.thinking_log.enabled and not args.emit_json:
        _print_thinking_log_banner(
            sup.thinking_log.path, when="reflection pass transcript"
        )
    report = sup.run()
    if args.emit_json:
        print(json.dumps(report.as_dict(), indent=2, default=str))
    else:
        _pretty_print_supervisor(report)
    return 0 if report.overall_status in {RoleStatus.OK, RoleStatus.SKIPPED} else 1


def _pretty_print(result) -> None:
    print(f"\nARR Quarter Close - as_was_date={result.as_was_date}")
    print(f"Status: {result.overall_status.value.upper()}  "
          f"(duration {result.duration_s:.1f}s, {len(result.steps)} steps)")
    print("-" * 78)
    for s in result.steps:
        print(f"  [{s.status.value:>7}]  {s.step.name:38s}  {s.duration_s:6.1f}s")
        if s.status in {StepStatus.FAIL, StepStatus.WARN} and s.stderr_tail:
            print("            stderr:", s.stderr_tail[:400].replace("\n", " | "))
    print()


if __name__ == "__main__":
    sys.exit(main())
