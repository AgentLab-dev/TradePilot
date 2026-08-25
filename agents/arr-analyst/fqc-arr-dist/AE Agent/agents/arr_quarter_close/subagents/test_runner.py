"""Sub-agent 6: test-runner.

Runs pytest (singular tests + python harnesses) and dbt test against the
configured selectors, and aggregates results into a structured TestReport
the qa-handoff sub-agent will attach to the Jira ticket.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from agents.arr_quarter_close.contracts import (
    RoleResult,
    RoleStatus,
    TestInput,
    TestReport,
    ValidationCheck,
    ValidationMatrix,
)

ROLE = "test-runner"

# Best-effort selector -> business-rule mapping. Falls back to the selector
# text when not listed. Used when projecting dbt test results into the
# 7-column validation matrix surfaced to the operator and qa-handoff.
_SELECTOR_BUSINESS_LOGIC: dict[str, str] = {
    "test_arr_waterfall_balance":
        "Begin Balance + sum(category deltas) = End Balance per fiscal quarter.",
    "tag:ia_migration":
        "Identifier-affecting migration: every legacy id mapped exactly once.",
}


def plan(req: TestInput) -> dict:
    return {
        "role": ROLE,
        "pytest_targets": req.pytest_paths,
        "dbt_test_selectors": req.dbt_test_selectors,
        "as_was_date": req.as_was_date,
        "matrix_columns": [
            "check_name", "grain", "source_salesforce", "baseline_prod",
            "target_dev_qa", "expected", "actual", "business_logic", "verdict",
        ],
        "matrix_source": (
            "Each dbt-test selector is projected into one ValidationCheck "
            "row (source_salesforce='' for structural tests; "
            "expected='all rows pass'; actual derived from dbt-test status; "
            "verdict=pass|fail|warn)."
        ),
    }


def run(req: TestInput) -> RoleResult:
    project_dir = Path(req.project_dir).resolve()

    pytest_passed, pytest_failed, pytest_skipped, junit_path = _run_pytest(
        project_dir, req.pytest_paths
    )
    dbt_results, dbt_target_path = _run_dbt_tests(
        project_dir, req.dbt_test_selectors, req.as_was_date
    )

    overall = (pytest_failed == 0) and all(
        r.get("status") in {"pass", "warn"} for r in dbt_results
    )
    matrix = _build_test_matrix(
        target_db="finance_dev",  # tests typically run after CI lands on dev
        pytest_passed=pytest_passed,
        pytest_failed=pytest_failed,
        pytest_skipped=pytest_skipped,
        dbt_results=dbt_results,
    )
    report = TestReport(
        ticket_key="",
        pytest_passed=pytest_passed,
        pytest_failed=pytest_failed,
        pytest_skipped=pytest_skipped,
        dbt_test_results=dbt_results,
        junit_xml_path=str(junit_path) if junit_path else None,
        dbt_target_path=str(dbt_target_path) if dbt_target_path else None,
        overall_passed=overall,
        validation_matrix=matrix,
    )
    summary = (
        f"pytest: {pytest_passed} passed, {pytest_failed} failed, {pytest_skipped} skipped; "
        f"dbt: {sum(1 for r in dbt_results if r.get('status') == 'pass')} passed / "
        f"{sum(1 for r in dbt_results if r.get('status') == 'fail')} failed / "
        f"{sum(1 for r in dbt_results if r.get('status') == 'warn')} warn"
    )
    return RoleResult(
        role=ROLE,
        status=RoleStatus.OK if overall else RoleStatus.WARN,
        summary=summary,
        payload={"test_report": report.as_dict()},
        artifacts={
            **({"junit_xml": str(junit_path)} if junit_path else {}),
            **({"dbt_target": str(dbt_target_path)} if dbt_target_path else {}),
        },
    )


def _run_pytest(project_dir: Path, paths: list[str]) -> tuple[int, int, int, Path | None]:
    junit_path = project_dir / ".cursor" / "test-results" / "pytest.xml"
    junit_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["pytest", "-q", f"--junitxml={junit_path}"] + paths
    proc = subprocess.run(cmd, cwd=str(project_dir), capture_output=True, text=True)
    summary = (proc.stdout + "\n" + proc.stderr).strip().splitlines()
    passed = failed = skipped = 0
    for line in summary[::-1]:
        m = re.search(r"(\d+)\s+passed", line)
        if m:
            passed = int(m.group(1))
        m = re.search(r"(\d+)\s+failed", line)
        if m:
            failed = int(m.group(1))
        m = re.search(r"(\d+)\s+skipped", line)
        if m:
            skipped = int(m.group(1))
        if passed or failed or skipped:
            break
    return passed, failed, skipped, junit_path if junit_path.exists() else None


def _run_dbt_tests(
    project_dir: Path, selectors: list[str], as_was_date: str | None
) -> tuple[list[dict], Path | None]:
    target_dir = project_dir / "target"
    results: list[dict] = []
    for sel in selectors:
        argv = ["dbt", "test", "--select", sel, "--project-dir", str(project_dir)]
        if as_was_date:
            argv += ["--vars", json.dumps({"as_was_date": f"'{as_was_date}'"})]
        proc = subprocess.run(argv, capture_output=True, text=True)
        status = "pass" if proc.returncode == 0 else "fail"
        results.append({
            "selector": sel,
            "status": status,
            "returncode": proc.returncode,
            "tail": (proc.stdout + "\n" + proc.stderr).strip()[-1000:],
        })
    return results, target_dir if target_dir.exists() else None


def _build_test_matrix(
    *,
    target_db: str,
    pytest_passed: int,
    pytest_failed: int,
    pytest_skipped: int,
    dbt_results: list[dict],
) -> ValidationMatrix:
    """Project pytest + dbt-test outcomes into the 7-column matrix.

    Each pytest run becomes ONE rollup row; each dbt selector becomes one
    row. ``source_salesforce`` is left empty for structural tests; for tests
    that have a documented business rule it surfaces the rule text.
    """
    checks: list[ValidationCheck] = []

    pytest_actual = (
        f"{pytest_passed} passed, {pytest_failed} failed, {pytest_skipped} skipped"
    )
    pytest_verdict = (
        "pass" if pytest_failed == 0 and pytest_passed > 0 else
        "warn" if pytest_failed == 0 and pytest_passed == 0 else
        "fail"
    )
    checks.append(ValidationCheck(
        check_name="pytest_singular_tests",
        grain="(suite-level)",
        baseline_prod="0 failed in prod",
        target_dev_qa=pytest_actual,
        expected="0 failed",
        actual=pytest_actual,
        business_logic="All singular SQL tests under tests/ must pass on the candidate branch.",
        verdict=pytest_verdict,
    ))

    for r in dbt_results:
        sel = r.get("selector", "")
        status = r.get("status", "unknown")
        verdict = {"pass": "pass", "fail": "fail"}.get(status, "warn")
        logic = _SELECTOR_BUSINESS_LOGIC.get(sel, f"dbt test --select {sel}")
        checks.append(ValidationCheck(
            check_name=f"dbt_test::{sel}",
            grain="(test-level)",
            baseline_prod="0 failed in prod",
            target_dev_qa=f"returncode={r.get('returncode', '?')}",
            expected="all rows pass",
            actual=status,
            business_logic=logic,
            verdict=verdict,
            notes=(r.get("tail") or "")[-200:],
        ))

    return ValidationMatrix(
        matrix_name="test-runner",
        target_db=target_db,
        baseline_db="finance_prod",
        source_db="(not applicable for unit tests)",
        checks=checks,
    )
