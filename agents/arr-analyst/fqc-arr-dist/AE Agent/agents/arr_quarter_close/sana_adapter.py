"""Workday SANA adapter (stub).

STATUS: blocked on the SANA integration spec.

This module exists as the single, clearly marked seam where the portable
`core` orchestrator will be wired to Workday's SANA agent flow. The portable
core is intentionally framework-agnostic, so wiring SANA later will not
require any changes to `core.py`, `cli.py`, or `cursor_runner.py`.

When you receive the SANA contract:

  1. Replace `SANAHandlerInput` / `SANAHandlerOutput` with the real schemas
     SANA expects (or import them from the SANA SDK).
  2. Implement `handle_request` against that contract. The body should:
       a. Translate the SANA input into an ``ARRCloseConfig``.
       b. Build an ``ARRCloseOrchestrator`` (optionally with a SANA-specific
          ``runner`` that calls dbt Cloud / SANA-managed dbt instead of the
          local CLI).
       c. Convert the returned ``CloseResult`` into a SANA-shaped response.
  3. Add whatever entrypoint SANA expects (Flask/FastAPI handler, AWS
     Lambda ``lambda_handler``, gRPC method, AgentFlow ``Tool``, etc.).
     Keep this file as the only place that knows about SANA.

Do NOT add SANA imports to `core.py`. The portability seam stops here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agents.arr_quarter_close.core import (
    ARRCloseConfig,
    ARRCloseOrchestrator,
    CloseResult,
)


@dataclass
class SANAHandlerInput:
    """Placeholder. Replace with the real SANA request schema."""

    as_was_date: str
    project_dir: str = "."
    target: str | None = None
    heavy_warehouse: str | None = None
    refresh_dashboards: bool = False
    run_validation: bool = True
    include_ia_migration_tests: bool = True
    extra_vars: dict[str, Any] = field(default_factory=dict)


@dataclass
class SANAHandlerOutput:
    """Placeholder. Replace with the real SANA response schema."""

    status: str
    payload: dict[str, Any]


def handle_request(req: SANAHandlerInput) -> SANAHandlerOutput:
    """SANA -> ARR close orchestrator -> SANA, framework-agnostic for now.

    When the real SANA contract arrives, change only the input/output types
    and the entrypoint shape. The body below already works as a reference
    implementation.
    """
    cfg = ARRCloseConfig(
        as_was_date=req.as_was_date,
        project_dir=Path(req.project_dir),
        target=req.target,
        heavy_warehouse=req.heavy_warehouse,
        refresh_dashboards=req.refresh_dashboards,
        run_validation=req.run_validation,
        include_ia_migration_tests=req.include_ia_migration_tests,
        extra_vars=req.extra_vars,
    )
    result: CloseResult = ARRCloseOrchestrator(cfg).run()
    return SANAHandlerOutput(
        status=result.overall_status.value,
        payload=result.as_dict(),
    )
