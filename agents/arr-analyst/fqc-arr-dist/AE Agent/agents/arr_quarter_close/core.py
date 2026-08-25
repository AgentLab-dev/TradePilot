"""Portable ARR Quarter Close orchestration core.

This module has no Cursor / SANA / cloud dependency. It encodes the ARR close
runbook for the `eda_dbt_em` repo as a typed step manifest and a thin driver
that shells out to the local dbt CLI. Other runtimes (Cursor SDK, SANA, REST
service, CI) import `ARRCloseOrchestrator` and supply their own `runner`.

ARR close (post-IA Data Mesh layout)
------------------------------------
Build order (encoded in `build_default_manifest`):

  1. on-run-start UDFs are deployed by dbt automatically (declared in
     `dbt_project.yml`). No explicit step needed.
  2. Staging chain: `path:tmp_tbls_of_bt_arr_categories_optimized` writes the
     `stg_arr_categories_*` intermediates that feed every aggregate.
  3. `arr_line_categories` (heavy; respects `em_heavy_warehouse` if set).
  4. Rollups: `arr_sku_categories`, `arr_subproduct_categories`,
     `arr_product_categories` (parallel-safe in dbt's DAG).
  5. `arr_account_product_corp_report` corp rollup.
  6. `data_product/view` dashboard views (optional refresh).
  7. Validation:
       - `test_arr_waterfall_balance` (waterfall integrity at `as_was_date`)
       - `tag:ia_migration` (certified vs finance_prod recon, $1 tolerance)

Required var: `as_was_date` = the FY quarter-end snapshot date.
Known FY close snapshots ship in `dbt_project.yml::arr_refactor_as_was_date_list`.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shlex
import subprocess
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Iterable, Optional

log = logging.getLogger(__name__)

KNOWN_FY_CLOSE_DATES: tuple[str, ...] = (
    "2025-05-08",
    "2025-08-11",
    "2025-11-10",
    "2026-02-11",
)


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    WARN = "warn"
    FAIL = "fail"
    SKIPPED = "skipped"


@dataclass
class CloseStep:
    """One discrete dbt invocation in the close runbook."""

    name: str
    description: str
    command: str
    select: str
    exclude: Optional[str] = None
    is_validation: bool = False
    optional: bool = False
    extra_args: tuple[str, ...] = ()

    def render(self, vars_payload: dict) -> list[str]:
        argv: list[str] = ["dbt", self.command, "--select", self.select]
        if self.exclude:
            argv += ["--exclude", self.exclude]
        if vars_payload:
            argv += ["--vars", json.dumps(vars_payload, separators=(",", ":"))]
        argv += list(self.extra_args)
        return argv


@dataclass
class StepResult:
    step: CloseStep
    status: StepStatus
    started_at: float
    duration_s: float
    returncode: int
    stdout_tail: str
    stderr_tail: str

    def as_dict(self) -> dict:
        return {
            "step": self.step.name,
            "command": " ".join(shlex.quote(p) for p in self.step.render({})),
            "status": self.status.value,
            "started_at": datetime.fromtimestamp(self.started_at).isoformat(),
            "duration_s": round(self.duration_s, 2),
            "returncode": self.returncode,
            "stdout_tail": self.stdout_tail,
            "stderr_tail": self.stderr_tail,
        }


@dataclass
class CloseResult:
    as_was_date: str
    started_at: float
    finished_at: float
    overall_status: StepStatus
    steps: list[StepResult] = field(default_factory=list)

    @property
    def duration_s(self) -> float:
        return self.finished_at - self.started_at

    def as_dict(self) -> dict:
        return {
            "as_was_date": self.as_was_date,
            "overall_status": self.overall_status.value,
            "duration_s": round(self.duration_s, 2),
            "started_at": datetime.fromtimestamp(self.started_at).isoformat(),
            "finished_at": datetime.fromtimestamp(self.finished_at).isoformat(),
            "steps": [s.as_dict() for s in self.steps],
        }


@dataclass
class ARRCloseConfig:
    """Inputs that change per run."""

    as_was_date: str
    project_dir: Path
    profiles_dir: Optional[Path] = None
    target: Optional[str] = None
    heavy_warehouse: Optional[str] = None
    refresh_dashboards: bool = False
    run_validation: bool = True
    include_ia_migration_tests: bool = True
    dry_run: bool = False
    fail_fast: bool = True
    extra_vars: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_as_was_date(self.as_was_date)
        self.project_dir = Path(self.project_dir).resolve()
        if not (self.project_dir / "dbt_project.yml").exists():
            raise ValueError(
                f"project_dir does not look like a dbt project (no dbt_project.yml): {self.project_dir}"
            )
        if self.profiles_dir is not None:
            self.profiles_dir = Path(self.profiles_dir).resolve()

    def vars_payload(self) -> dict:
        payload: dict = {"as_was_date": _quote_date_literal(self.as_was_date)}
        if self.heavy_warehouse:
            payload["em_heavy_warehouse"] = self.heavy_warehouse
        payload.update(self.extra_vars)
        return payload

    def base_dbt_flags(self) -> list[str]:
        flags: list[str] = ["--project-dir", str(self.project_dir)]
        if self.profiles_dir:
            flags += ["--profiles-dir", str(self.profiles_dir)]
        if self.target:
            flags += ["--target", self.target]
        return flags


def build_default_manifest(cfg: ARRCloseConfig) -> list[CloseStep]:
    """Return the ordered ARR close step manifest for the IA layout."""
    steps: list[CloseStep] = [
        CloseStep(
            name="stage_arr_categories_chain",
            description=(
                "Build the stg_arr_categories_* staging chain that feeds every "
                "ARR aggregate (begin/end balances, fiscal attrs, incremental, "
                "FSE attrs, price/qty, related lines, sku_swap, up_for_renewal)."
            ),
            command="run",
            select="path:models/finance/int/stage/table/tmp_tbls_of_bt_arr_categories_optimized",
            exclude="*_scd2",
        ),
        CloseStep(
            name="arr_line_categories",
            description=(
                "Heavy ARR aggregate at line x fiscal_quarter x as_was_date grain. "
                "Materialized incremental delete+insert on as_was_date."
            ),
            command="run",
            select="+arr_line_categories",
            exclude="*_scd2",
        ),
        CloseStep(
            name="arr_rollups",
            description=(
                "Parallel-safe rollups derived from arr_line_categories: "
                "arr_sku_categories (L5), arr_subproduct_categories (L4), "
                "arr_product_categories (L3)."
            ),
            command="run",
            select="arr_sku_categories arr_subproduct_categories arr_product_categories",
            exclude="*_scd2",
        ),
        CloseStep(
            name="arr_account_product_corp_report",
            description=(
                "Corp reporting rollup over arr_product_categories with SSR / "
                "up-for-renewal logic."
            ),
            command="run",
            select="+arr_account_product_corp_report",
            exclude="*_scd2",
        ),
    ]

    if cfg.refresh_dashboards:
        steps.append(
            CloseStep(
                name="arr_dashboards",
                description=(
                    "Refresh data_product views consumed by Sigma / downstream "
                    "tools. No business logic; views only."
                ),
                command="run",
                select="path:models/finance/modeled/data_product/view",
                exclude="*_scd2",
                optional=True,
            )
        )

    if cfg.run_validation:
        steps.append(
            CloseStep(
                name="validate_arr_waterfall",
                description=(
                    "Singular test: Begin + incrementals = End Balance and QoQ "
                    "End -> Begin continuity within $0.01 per buying_center."
                ),
                command="test",
                select="test_arr_waterfall_balance",
                is_validation=True,
            )
        )
        if cfg.include_ia_migration_tests:
            steps.append(
                CloseStep(
                    name="validate_ia_migration_recon",
                    description=(
                        "Certified vs finance_prod IA migration recon across all "
                        "5 arr_* aggregates (row count + distinct keys + $1 sum)."
                    ),
                    command="test",
                    select="tag:ia_migration",
                    is_validation=True,
                )
            )

    return steps


SubprocessRunner = Callable[[list[str], Path], subprocess.CompletedProcess]


def default_runner(argv: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Default subprocess runner: stream-friendly, captures stdout/stderr."""
    log.info("exec: %s (cwd=%s)", " ".join(shlex.quote(p) for p in argv), cwd)
    return subprocess.run(
        argv,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env=os.environ.copy(),
        check=False,
    )


class ARRCloseOrchestrator:
    """Drive the ARR close manifest with a pluggable subprocess runner.

    Substituting `runner` is how non-CLI runtimes (dbt Cloud API, Cursor SDK
    with dbt MCP, SANA, mocks) hook in without rewriting the manifest.
    """

    def __init__(
        self,
        cfg: ARRCloseConfig,
        manifest: Optional[Iterable[CloseStep]] = None,
        runner: SubprocessRunner = default_runner,
    ) -> None:
        self.cfg = cfg
        self.steps: list[CloseStep] = list(manifest) if manifest is not None else build_default_manifest(cfg)
        self.runner = runner
        # Optional callback fired after each step completes (success/fail/skipped).
        # The supervisor wraps this to emit per-step Slack pings; default is no-op.
        self.on_step_complete: Callable[[StepResult], None] = lambda _r: None

    def run(self) -> CloseResult:
        started = time.time()
        results: list[StepResult] = []
        overall = StepStatus.SUCCESS

        for step in self.steps:
            argv = self._argv_for(step)
            if self.cfg.dry_run:
                sr = StepResult(
                    step=step,
                    status=StepStatus.SKIPPED,
                    started_at=time.time(),
                    duration_s=0.0,
                    returncode=0,
                    stdout_tail="(dry-run) " + " ".join(shlex.quote(p) for p in argv),
                    stderr_tail="",
                )
                results.append(sr)
                try:
                    self.on_step_complete(sr)
                except Exception:                        # noqa: BLE001
                    log.debug("on_step_complete hook raised; ignoring.")
                continue

            res = self._exec_step(step, argv)
            results.append(res)
            try:
                self.on_step_complete(res)
            except Exception:                            # noqa: BLE001
                log.debug("on_step_complete hook raised; ignoring.")

            if res.status == StepStatus.FAIL:
                overall = StepStatus.FAIL
                if self.cfg.fail_fast and not step.optional:
                    break
            elif res.status == StepStatus.WARN and overall == StepStatus.SUCCESS:
                overall = StepStatus.WARN

        if self.cfg.dry_run and overall == StepStatus.SUCCESS:
            overall = StepStatus.SKIPPED

        return CloseResult(
            as_was_date=self.cfg.as_was_date,
            started_at=started,
            finished_at=time.time(),
            overall_status=overall,
            steps=results,
        )

    def planned_commands(self) -> list[list[str]]:
        """Return the argv for every step without executing. Useful for review."""
        return [self._argv_for(s) for s in self.steps]

    def _argv_for(self, step: CloseStep) -> list[str]:
        argv: list[str] = ["dbt", step.command]
        argv += self.cfg.base_dbt_flags()
        argv += ["--select", step.select]
        if step.exclude:
            argv += ["--exclude", step.exclude]
        vars_payload = self.cfg.vars_payload()
        if vars_payload:
            argv += ["--vars", json.dumps(vars_payload, separators=(",", ":"))]
        argv += list(step.extra_args)
        return argv

    def _exec_step(self, step: CloseStep, argv: list[str]) -> StepResult:
        started = time.time()
        proc = self.runner(argv, self.cfg.project_dir)
        duration = time.time() - started
        status = _classify_returncode(proc.returncode, step)
        return StepResult(
            step=step,
            status=status,
            started_at=started,
            duration_s=duration,
            returncode=proc.returncode,
            stdout_tail=_tail(proc.stdout, 4000),
            stderr_tail=_tail(proc.stderr, 2000),
        )


_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _validate_as_was_date(value: str) -> None:
    if not isinstance(value, str) or not _DATE_RE.match(value):
        raise ValueError(
            f"as_was_date must be YYYY-MM-DD (got {value!r}). "
            f"Known FY close snapshots: {', '.join(KNOWN_FY_CLOSE_DATES)}"
        )
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"as_was_date {value!r} is not a real calendar date") from exc


def _quote_date_literal(value: str) -> str:
    """dbt vars need the literal wrapped in single quotes so Snowflake can cast it.

    Matches the README pattern: --vars '{"as_was_date": "'2025-05-08'"}'.
    """
    return f"'{value}'"


def _classify_returncode(rc: int, step: CloseStep) -> StepStatus:
    # dbt exit codes: 0 ok, 1 fail, 2 usage error. Tests with severity=warn
    # still return 0; the singular test severity is 'warn' anyway.
    if rc == 0:
        return StepStatus.SUCCESS
    if step.optional:
        return StepStatus.WARN
    return StepStatus.FAIL


def _tail(text: Optional[str], limit: int) -> str:
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return "..." + text[-limit:]
