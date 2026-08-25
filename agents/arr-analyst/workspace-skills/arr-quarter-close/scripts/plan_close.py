"""Print the planned ARR close dbt commands without executing them.

This is a thin wrapper around the orchestrator's `--dry-run`, kept here
because the skill references it. Use from the repo root:

    python .cursor/skills/arr-quarter-close/scripts/plan_close.py 2026-02-11

Add an optional --target to mimic a real run's flags.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.arr_quarter_close.core import (  # noqa: E402
    ARRCloseConfig,
    ARRCloseOrchestrator,
)


def main() -> int:
    p = argparse.ArgumentParser(description="Plan-only view of the ARR close.")
    p.add_argument("as_was_date")
    p.add_argument("--target", default=None)
    p.add_argument("--heavy-warehouse", default=None)
    p.add_argument("--refresh-dashboards", action="store_true")
    p.add_argument("--no-ia-migration-tests", dest="ia_tests", action="store_false")
    args = p.parse_args()

    cfg = ARRCloseConfig(
        as_was_date=args.as_was_date,
        project_dir=REPO_ROOT,
        target=args.target,
        heavy_warehouse=args.heavy_warehouse,
        refresh_dashboards=args.refresh_dashboards,
        include_ia_migration_tests=args.ia_tests,
        dry_run=True,
    )
    for argv in ARRCloseOrchestrator(cfg).planned_commands():
        print(" ".join(shlex.quote(a) for a in argv))
    return 0


if __name__ == "__main__":
    sys.exit(main())
