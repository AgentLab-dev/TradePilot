"""ARR Quarter Close agent package.

Layout:
    core.py            - portable, framework-agnostic orchestration
    cursor_runner.py   - Cursor SDK wrapper (in-IDE / cloud agent runtime)
    cli.py             - command-line entrypoint
    sana_adapter.py    - placeholder for Workday SANA integration

The portable surface is `core`. Everything else wraps `core` for a specific runtime.
"""

from agents.arr_quarter_close.core import (
    ARRCloseConfig,
    ARRCloseOrchestrator,
    CloseResult,
    CloseStep,
    StepResult,
    StepStatus,
    build_default_manifest,
)
from agents.arr_quarter_close.contracts import (
    ACAnalysis,
    AuthMode,
    DebugInput,
    DebugReport,
    LineageNode,
    ProposedFix,
    PytestHarnessSpec,
    QuarterCloseInput,
    QuarterCloseReport,
    RoleResult,
    RoleStatus,
    RootCauseHypothesis,
    SupervisorRunReport,
)
from agents.arr_quarter_close.supervisor import (
    SUPERVISOR_ALIASES,
    SUPERVISOR_DISPLAY_NAME,
    SUPERVISOR_SHORT_CODE,
    Supervisor,
    SupervisorInput,
    SupervisorState,
)

__all__ = [
    "ARRCloseConfig",
    "ARRCloseOrchestrator",
    "CloseResult",
    "CloseStep",
    "StepResult",
    "StepStatus",
    "build_default_manifest",
    "AuthMode",
    "RoleResult",
    "RoleStatus",
    "SupervisorRunReport",
    "Supervisor",
    "SupervisorInput",
    "SupervisorState",
    "SUPERVISOR_DISPLAY_NAME",
    "SUPERVISOR_SHORT_CODE",
    "SUPERVISOR_ALIASES",
    "ACAnalysis",
    "DebugInput",
    "DebugReport",
    "LineageNode",
    "ProposedFix",
    "PytestHarnessSpec",
    "RootCauseHypothesis",
    "QuarterCloseInput",
    "QuarterCloseReport",
]
