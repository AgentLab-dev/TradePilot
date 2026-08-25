"""Sub-agent 3: code-data-validator.

Maps the requirements onto repo files and proposes data-side validation
queries against the configured Snowflake DB (default ``finance_prod``).

* Code side: walks the repo (file + grep) to find which dbt models / macros /
  tests would be touched. No edits.
* Data side: emits SQL templates (waterfall snapshot, line-level recon,
  metric baselines) targeted at the configured DB. The supervisor or the
  user runs them via the Snowflake MCP (per the prefer-mcp-for-data-platforms
  rule); this module never opens a Snowflake connection itself.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from agents.arr_quarter_close.contracts import (
    CodeFindings,
    DataFindings,
    RoleResult,
    RoleStatus,
    ValidationInput,
    ValidationReport,
)
from agents.arr_quarter_close.subagents._validation_matrix import build_matrix

ROLE = "code-data-validator"

ARR_MODELS = (
    "arr_line_categories",
    "arr_sku_categories",
    "arr_subproduct_categories",
    "arr_product_categories",
    "arr_account_product_corp_report",
)


def plan(req: ValidationInput) -> dict:
    return {
        "role": ROLE,
        "ticket_key": req.requirements.ticket_key,
        "code_scope": (
            "Search models/, macros/, tests/ for any model/macro the "
            "requirements-analyzer flagged as in_scope. Add full upstream "
            "dependency walk for any arr_* model."
        ),
        "data_scope": {
            "target_db": req.snowflake_target_db,
            "baseline_db": req.baseline_db,
            "source_db": req.source_db,
            "matrix_checks": [
                "arr_total_at_latest_snapshot   (sf -> prod -> dev/qa, ±1% tolerance)",
                "line_vs_sku_rollup_parity      (structural, per FQ)",
                "waterfall_balance              (Begin + categories = End, per FQ)",
                "row_count_parity_vs_baseline   (count(*) vs prod, ±1%)",
            ],
        },
        "tooling": ["ripgrep for code", "Snowflake MCP for data"],
    }


def run(req: ValidationInput) -> RoleResult:
    project_dir = Path(req.project_dir).resolve()
    in_scope = list(req.requirements.in_scope_models) or list(ARR_MODELS)

    code = _scan_code(project_dir, in_scope)
    data = _propose_data_validations(req.snowflake_target_db, in_scope)
    proposed = _propose_changes(req.requirements)

    # 7-column comparison matrix: SF source -> prod baseline -> dev target,
    # with expected/actual/business-logic/verdict per row. SQL templates are
    # auditable; values populate when the supervisor runs them via the
    # Snowflake MCP.
    matrix = build_matrix(
        matrix_name="code-data-validator pre-flight",
        target_db=req.snowflake_target_db,
        baseline_db=req.baseline_db,
        source_db=req.source_db,
        in_scope_models=in_scope,
    )

    report = ValidationReport(
        ticket_key=req.requirements.ticket_key,
        code=code,
        data=data,
        risks=_risk_signals(req.requirements, code),
        proposed_changes=proposed,
        validation_matrix=matrix,
    )

    status = RoleStatus.OK if code.affected_models else RoleStatus.WARN
    summary = (
        f"affected_models={len(code.affected_models)} "
        f"affected_macros={len(code.affected_macros)} "
        f"matrix_checks={len(matrix.checks)} (sf->prod->{req.snowflake_target_db}) "
        f"risks={len(report.risks)}"
    )
    return RoleResult(
        role=ROLE,
        status=status,
        summary=summary,
        payload={"validation": report.as_dict()},
    )


def _scan_code(project_dir: Path, in_scope: list[str]) -> CodeFindings:
    affected_models: list[str] = []
    affected_macros: list[str] = []
    for name in in_scope:
        for hit in _rg(project_dir, name, ["models", "tests"]):
            affected_models.append(hit)
        for hit in _rg(project_dir, name, ["macros"]):
            affected_macros.append(hit)
    grain_notes = (
        "ARR models follow grain: one row per (as_was_date, account, agreement, "
        "opportunity, product_code_lN, fiscal_quarter_name, arr_category). "
        "Any new column or join must preserve this grain - add a uniqueness test."
    )
    layering = (
        "Edits to arr_*_categories belong in models/finance/modeled/aggregate/table/. "
        "Edits to upstream stg_arr_categories_* belong under "
        "tmp_tbls_of_bt_arr_categories_optimized/. data_product/view should not "
        "gain new business logic."
    )
    return CodeFindings(
        affected_models=sorted(set(affected_models)),
        affected_macros=sorted(set(affected_macros)),
        grain_check_notes=grain_notes,
        layering_notes=layering,
    )


def _rg(project_dir: Path, needle: str, paths: list[str]) -> list[str]:
    cmd = ["rg", "-l", "--no-messages", needle, *paths]
    try:
        proc = subprocess.run(
            cmd, cwd=str(project_dir), capture_output=True, text=True, check=False,
        )
    except FileNotFoundError:
        # ripgrep not installed; fall back to plain `grep -rl` which ships
        # with every macOS / Linux box. Slower for large repos but functionally
        # equivalent for this caller (we only want filenames).
        cmd = ["grep", "-rl", "--include=*.sql", "--include=*.yml", needle, *paths]
        try:
            proc = subprocess.run(
                cmd, cwd=str(project_dir), capture_output=True, text=True, check=False,
            )
        except FileNotFoundError:
            return []
    if proc.returncode not in (0, 1):
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def _propose_data_validations(db: str, in_scope: list[str]) -> DataFindings:
    queries: list[str] = []
    arr_models = [m for m in in_scope if m.startswith("arr_")]
    if not arr_models:
        arr_models = list(ARR_MODELS)

    queries.append(
        f"-- waterfall snapshot vs last close\n"
        f"select fiscal_quarter_name, buying_center,\n"
        f"       sum(case when arr_category = 'Begin Balance' then split_arr_usd_current end) as begin_arr,\n"
        f"       sum(case when arr_category = 'End Balance'   then split_arr_usd_current end) as end_arr\n"
        f"from {db}.aggregations.arr_product_categories\n"
        f"where as_was_date = (select max(as_was_date) from {db}.aggregations.arr_product_categories)\n"
        f"group by 1, 2 order by 1, 2;"
    )
    queries.append(
        f"-- line vs sku rollup parity\n"
        f"select 'line' as src, sum(split_sku_line_arr_usd_current) as arr\n"
        f"from {db}.aggregations.arr_line_categories\n"
        f"where as_was_date = (select max(as_was_date) from {db}.aggregations.arr_line_categories)\n"
        f"union all\n"
        f"select 'sku',  sum(split_arr_usd_current)\n"
        f"from {db}.aggregations.arr_sku_categories\n"
        f"where as_was_date = (select max(as_was_date) from {db}.aggregations.arr_sku_categories);"
    )
    baselines = {
        "max_as_was_date": f"select max(as_was_date) from {db}.aggregations.arr_product_categories;",
        "row_count_product_categories": (
            f"select count(*) from {db}.aggregations.arr_product_categories "
            f"where as_was_date = (select max(as_was_date) from {db}.aggregations.arr_product_categories);"
        ),
    }
    return DataFindings(
        queries_run=queries,
        metric_baselines=baselines,
        anomalies=[],
    )


def _risk_signals(requirements, code: CodeFindings) -> list[str]:
    risks: list[str] = []
    if requirements.confidence == "low":
        risks.append("Requirements confidence is LOW - clarifier should run before implementer.")
    if not code.affected_models:
        risks.append(
            "No matching dbt models found for the requirements' in_scope_models hint. "
            "Either the in_scope list is wrong or the ticket implies new models."
        )
    if requirements.questions:
        risks.append(f"{len(requirements.questions)} open requirement questions outstanding.")
    return risks


def _propose_changes(requirements) -> list[str]:
    proposals: list[str] = []
    if not requirements.in_scope_models:
        proposals.append("Identify the affected dbt models before implementation (no scope hint yet).")
        return proposals
    for m in requirements.in_scope_models:
        proposals.append(f"Touch {m} per the KPI spec; pair every SQL change with the .yml.")
    proposals.append("Add or extend a singular test under tests/ for the new behavior.")
    return proposals
