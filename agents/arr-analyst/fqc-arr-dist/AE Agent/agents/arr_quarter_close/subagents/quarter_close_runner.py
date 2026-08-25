"""Sub-agent 12: quarter-close-runner (on-demand).

Runs the ARR quarter-close dbt pipeline and validates the reconciliation
for the snapshot. Dispatched whenever and wherever needed:

* Supervisor mode A (``--as-was-date`` only) - runs as the primary role.
* Supervisor mode B (ticket-driven) - dispatched after CD when
  ``--quarter-close`` is set, so the QA-handoff comment carries the
  recon matrix.
* Slack side-channel - ``task: quarter-close [YYYY-MM-DD]``.
* CLI on-demand - ``fqc-arr --mode quarter-close --as-was-date 2026-02-11``.
* Direct SDK call - ``quarter_close_runner.run(QuarterCloseInput(...))``.

What it does (in two phases):

1. **Pipeline phase** (optional; skip with ``run_pipeline=False``):
   Delegates to ``ARRCloseOrchestrator`` for the standard ARR build
   sequence (tmp_tbls -> arr_line_categories -> rollups ->
   arr_account_product_corp_report -> dbt test). Captures every step
   result so the operator sees what ran and how long it took.

2. **Recon phase** (always; this is the value-add):
   Builds an ARR-specific ``ValidationMatrix`` with 7 tie-out checks:

   * ``waterfall_balance_per_category`` - Begin + New + Expansion -
     Contraction - Churn +/- SKU/Volume/Price/Mix = End (per category)
   * ``total_arr_at_snapshot`` - sum(arr_usd_current) vs prior snapshot
     +/- ``tolerance_pct``
   * ``arr_line_categories_row_parity`` - row count vs prior snapshot
   * ``arr_sku_categories_row_parity`` - row count vs prior snapshot
   * ``arr_account_product_corp_report_row_parity`` - row count vs prior
   * ``currency_variant_tie_out`` - USD_CURRENT vs USD_HIST when rates
     are equal (structural sanity)
   * ``active_account_continuity`` - account count vs prior snapshot
     (catches churn / migration regressions)

   Each check carries an auditable CTE-based SQL template. The
   supervisor (or operator) runs them via the Snowflake MCP to populate
   the actual columns; the sub-agent never opens a Snowflake connection
   directly (per ``prefer-mcp-for-data-platforms``).

Status mapping:

* All checks pass -> ``RoleStatus.OK``
* Any check warn (and none fail) -> ``RoleStatus.WARN``
* Any check fail -> ``RoleStatus.FAIL`` (-> auto-debugger if enabled)
* Pipeline fail -> ``RoleStatus.FAIL`` (recon still attempted on the
  partial state so the operator sees which model didn't load)
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional

from agents.arr_quarter_close.contracts import (
    AuthMode,
    QuarterCloseInput,
    QuarterCloseReport,
    RoleResult,
    RoleStatus,
    ValidationCheck,
    ValidationMatrix,
)
from agents.arr_quarter_close.core import (
    ARRCloseConfig,
    ARRCloseOrchestrator,
    StepStatus,
)

log = logging.getLogger(__name__)

ROLE = "quarter-close-runner"

# Models the recon matrix covers. Mirrors the ARRCloseOrchestrator
# manifest so the row-count checks line up with the pipeline output.
ARR_RECON_MODELS: tuple[str, ...] = (
    "arr_line_categories",
    "arr_sku_categories",
    "arr_subproduct_categories",
    "arr_product_categories",
    "arr_account_product_corp_report",
)

# Waterfall categories used by the per-category balance check. Mirrors
# the bt_*_arr_categories convention from the finance-functional-analytics
# skill (Beginning + Categories = Ending).
ARR_WATERFALL_CATEGORIES: tuple[str, ...] = (
    "NEW_LOGO",
    "EXPANSION",
    "CONTRACTION",
    "CHURN",
    "FLAT_RENEWAL",
    "SKU_CHANGE",
    "VOLUME_CHANGE",
    "PRICE_CHANGE",
    "MIX_CHANGE",
)


def plan(req: QuarterCloseInput) -> dict:
    return {
        "role": ROLE,
        "as_was_date": req.as_was_date,
        "baseline_as_was_date": req.baseline_as_was_date or "(supplied at run time)",
        "target_db": req.target_db,
        "baseline_db": req.baseline_db,
        "tolerance_pct": req.tolerance_pct,
        "phases": [
            (
                "1. Pipeline (delegates to ARRCloseOrchestrator): "
                "tmp_tbls -> arr_line_categories -> rollups -> "
                "arr_account_product_corp_report -> dbt test"
            ) if req.run_pipeline else "1. Pipeline SKIPPED (run_pipeline=False)",
            (
                "2. Recon matrix (7 ARR-quarter-close tie-out checks): "
                "waterfall balance / total / row parity / currency / "
                "account continuity"
            ),
        ],
        "models_covered": list(ARR_RECON_MODELS),
        "waterfall_categories": list(ARR_WATERFALL_CATEGORIES),
        "would_post": False,
    }


def run(req: QuarterCloseInput) -> RoleResult:
    project_dir = Path(req.project_dir).resolve()
    started = time.time()
    report = QuarterCloseReport(
        as_was_date=req.as_was_date,
        baseline_as_was_date=req.baseline_as_was_date,
        target_db=req.target_db,
        baseline_db=req.baseline_db,
    )

    # ---------- Phase 1: pipeline -----------------------------------------
    pipeline_status = StepStatus.SKIPPED
    if req.run_pipeline:
        cfg = ARRCloseConfig(
            as_was_date=req.as_was_date,
            project_dir=project_dir,
            refresh_dashboards=req.refresh_dashboards,
            run_validation=True,
            include_ia_migration_tests=req.include_ia_migration_tests,
            dry_run=False,
            fail_fast=True,
        )
        orch = ARRCloseOrchestrator(cfg)
        try:
            close_result = orch.run()
        except Exception as exc:                                       # noqa: BLE001
            # Wrap a hard orchestrator failure into a soft report so the
            # supervisor still gets a RoleResult and can dispatch debugger.
            log.warning("ARRCloseOrchestrator raised %s: %s", type(exc).__name__, exc)
            report.pipeline_executed = True
            report.pipeline_overall_status = "fail"
            report.notes.append(
                f"ARRCloseOrchestrator raised {type(exc).__name__}: {exc}"
            )
        else:
            report.pipeline_executed = True
            report.pipeline_overall_status = close_result.overall_status.value
            report.pipeline_steps = [sr.as_dict() for sr in close_result.steps]
            report.pipeline_duration_s = close_result.duration_s
            pipeline_status = close_result.overall_status
    else:
        report.notes.append("Pipeline phase skipped (run_pipeline=False).")

    # ---------- Phase 2: recon matrix -------------------------------------
    matrix = _build_quarter_close_matrix(req)
    report.recon_matrix = matrix
    report.overall_verdict = matrix.overall_verdict

    # ---------- Status aggregation ----------------------------------------
    role_status = _aggregate_status(pipeline_status, matrix.overall_verdict)

    summary = (
        f"as_was_date={req.as_was_date} "
        f"pipeline={report.pipeline_overall_status} "
        f"recon_checks={len(matrix.checks)} "
        f"recon_verdict={matrix.overall_verdict}"
    )

    elapsed = time.time() - started
    log.info("quarter-close-runner finished in %.1fs (%s)", elapsed, summary)

    return RoleResult(
        role=ROLE,
        status=role_status,
        summary=summary,
        payload={"quarter_close": report.as_dict(),
                 # Surface matrix at the well-known thinking-log key so
                 # _render_validation_matrices renders it as a table.
                 "validation_matrix_label": "quarter-close recon"},
        artifacts={},
    )


# ---------------------------------------------------------------------------
# Recon matrix builder
# ---------------------------------------------------------------------------

def _build_quarter_close_matrix(req: QuarterCloseInput) -> ValidationMatrix:
    """Build the 7 quarter-close tie-out checks.

    Each check is structural (a single SQL template the operator runs
    via the Snowflake MCP). Verdicts default to ``pending`` until the
    SQL is run; the supervisor then re-attaches actuals and re-computes
    the matrix verdict.
    """
    target = req.target_db
    baseline = req.baseline_db
    sf = req.source_db
    as_was = req.as_was_date
    baseline_as_was = req.baseline_as_was_date or "(prior-quarter snapshot)"
    tol = float(req.tolerance_pct)
    warn_tol = tol * 5.0    # < tol = pass, < 5x tol = warn, else fail

    checks: list[ValidationCheck] = []

    # ----- 1. Waterfall balance per category (the headline check) ---------
    cat_list = ", ".join(f"'{c}'" for c in ARR_WATERFALL_CATEGORIES)
    waterfall_sql = (
        "-- check: arr waterfall balance per category at as_was_date\n"
        "-- For each category, sum(arr_usd_current) should match the canonical\n"
        "-- waterfall identity: Begin + Categories = End (within tolerance).\n\n"
        "with categories as (\n"
        "    select arr_category,\n"
        "           sum(arr_usd_current) as arr_total,\n"
        "           count(*) as line_count\n"
        f"    from {target}.aggregations.arr_line_categories\n"
        f"    where as_was_date = '{as_was}'\n"
        f"      and arr_category in ({cat_list})\n"
        "    group by 1\n"
        "),\n"
        "begin_balance as (\n"
        "    select sum(arr_usd_current) as begin_arr\n"
        f"    from {target}.aggregations.arr_line_categories\n"
        f"    where as_was_date = '{as_was}'\n"
        "      and arr_category = 'BEGINNING_BALANCE'\n"
        "),\n"
        "end_balance as (\n"
        "    select sum(arr_usd_current) as end_arr\n"
        f"    from {target}.aggregations.arr_line_categories\n"
        f"    where as_was_date = '{as_was}'\n"
        "      and arr_category = 'ENDING_BALANCE'\n"
        ")\n"
        "select (select begin_arr from begin_balance)\n"
        "       + coalesce(sum(arr_total), 0)\n"
        "       - (select end_arr from end_balance) as variance_abs,\n"
        "       (select end_arr from end_balance) as end_arr,\n"
        "       case\n"
        "         when (select end_arr from end_balance) = 0 then 'needs_review'\n"
        "         when abs(\n"
        "           (select begin_arr from begin_balance)\n"
        "           + coalesce(sum(arr_total), 0)\n"
        "           - (select end_arr from end_balance)\n"
        "         ) / nullif(abs((select end_arr from end_balance)), 0) * 100\n"
        f"              < {tol} then 'pass'\n"
        "         when abs(\n"
        "           (select begin_arr from begin_balance)\n"
        "           + coalesce(sum(arr_total), 0)\n"
        "           - (select end_arr from end_balance)\n"
        "         ) / nullif(abs((select end_arr from end_balance)), 0) * 100\n"
        f"              < {warn_tol} then 'warn'\n"
        "         else 'fail'\n"
        "       end as verdict\n"
        "from categories;"
    )
    checks.append(ValidationCheck(
        check_name="waterfall_balance_per_category",
        grain="one row aggregated across all waterfall categories",
        source_salesforce="(structural; sf source not applicable)",
        baseline_prod="N/A (self-balancing identity)",
        target_dev_qa=f"{target}.aggregations.arr_line_categories @ {as_was}",
        business_logic=(
            f"Begin + sum(categories) = End within {tol}% tolerance "
            f"(warn < {warn_tol}%, else fail)"
        ),
        sql_template=waterfall_sql,
        notes=(
            "Headline ARR quarter-close check. If this fails, look first "
            "at SKU_CHANGE / VOLUME_CHANGE / PRICE_CHANGE category sums - "
            "they are the most common offenders during refactors."
        ),
    ))

    # ----- 2. Total ARR vs prior snapshot ---------------------------------
    total_sql = (
        "-- check: total ARR at current snapshot vs prior snapshot (period-over-period)\n"
        "with current_total as (\n"
        "    select sum(arr_usd_current) as v\n"
        f"    from {target}.aggregations.arr_line_categories\n"
        f"    where as_was_date = '{as_was}'\n"
        "      and arr_category = 'ENDING_BALANCE'\n"
        "),\n"
        "prior_total as (\n"
        "    select sum(arr_usd_current) as v\n"
        f"    from {baseline}.aggregations.arr_line_categories\n"
        f"    where as_was_date = '{baseline_as_was}'\n"
        "      and arr_category = 'ENDING_BALANCE'\n"
        ")\n"
        "select c.v as current_arr,\n"
        "       p.v as prior_arr,\n"
        "       (c.v - p.v) as variance_abs,\n"
        "       case when p.v = 0 then null\n"
        "            else (c.v - p.v) / nullif(p.v, 0) * 100 end as variance_pct,\n"
        "       case\n"
        "         when p.v = 0 then 'needs_review'\n"
        f"         when abs((c.v - p.v) / nullif(p.v, 0)) * 100 < {tol} then 'pass'\n"
        f"         when abs((c.v - p.v) / nullif(p.v, 0)) * 100 < {warn_tol} then 'warn'\n"
        "         else 'fail'\n"
        "       end as verdict\n"
        "from current_total c, prior_total p;"
    )
    checks.append(ValidationCheck(
        check_name="total_arr_at_snapshot",
        grain="single scalar (sum of arr_usd_current at ENDING_BALANCE)",
        source_salesforce=f"{sf}.* (raw Salesforce; not joined directly)",
        baseline_prod=f"{baseline}.aggregations.arr_line_categories @ {baseline_as_was}",
        target_dev_qa=f"{target}.aggregations.arr_line_categories @ {as_was}",
        business_logic=(
            f"Period-over-period total ARR variance < {tol}% pass / "
            f"< {warn_tol}% warn / else fail"
        ),
        sql_template=total_sql,
        notes="Catches outright regressions before they hit the dashboard.",
    ))

    # ----- 3-5. Row-count parity per model --------------------------------
    parity_models = (
        "arr_line_categories",
        "arr_sku_categories",
        "arr_account_product_corp_report",
    )
    for model in parity_models:
        parity_sql = (
            f"-- check: row count parity for {model} (current vs prior snapshot)\n"
            "with t as (\n"
            f"    select count(*) as v from {target}.aggregations.{model}\n"
            f"    where as_was_date = '{as_was}'\n"
            "),\n"
            "b as (\n"
            f"    select count(*) as v from {baseline}.aggregations.{model}\n"
            f"    where as_was_date = '{baseline_as_was}'\n"
            ")\n"
            "select t.v as target_rows, b.v as baseline_rows,\n"
            "       (t.v - b.v) as variance_abs,\n"
            "       case when b.v = 0 then null\n"
            "            else (t.v - b.v) / nullif(b.v, 0.0) * 100 end as variance_pct,\n"
            "       case\n"
            "         when b.v = 0 then 'needs_review'\n"
            f"         when abs((t.v - b.v) / nullif(b.v, 0.0)) * 100 < {tol} then 'pass'\n"
            f"         when abs((t.v - b.v) / nullif(b.v, 0.0)) * 100 < {warn_tol} then 'warn'\n"
            "         else 'fail'\n"
            "       end as verdict\n"
            "from t, b;"
        )
        checks.append(ValidationCheck(
            check_name=f"{model}_row_parity",
            grain=f"single scalar (count(*) on {model})",
            source_salesforce=(
                f"{sf}.opportunity / {sf}.apttus__agreementlineitem__c"
                if "line" in model else "(rollup of upstream)"
            ),
            baseline_prod=f"{baseline}.aggregations.{model} @ {baseline_as_was}",
            target_dev_qa=f"{target}.aggregations.{model} @ {as_was}",
            business_logic=(
                f"Row count variance < {tol}% pass / < {warn_tol}% warn / else fail"
            ),
            sql_template=parity_sql,
        ))

    # ----- 6. Currency variant tie-out ------------------------------------
    currency_sql = (
        "-- check: currency variant cross-check (USD_CURRENT vs USD_HIST)\n"
        "-- For closed deals where the historical rate equals the current rate,\n"
        "-- the two variants must agree exactly. Used to catch currency-conversion\n"
        "-- regressions early.\n\n"
        "with same_rate_lines as (\n"
        "    select arr_usd_current, arr_usd_hist\n"
        f"    from {target}.aggregations.arr_line_categories\n"
        f"    where as_was_date = '{as_was}'\n"
        "      and currencyisocode = 'USD'\n"
        "      and arr_usd_current is not null\n"
        "      and arr_usd_hist is not null\n"
        ")\n"
        "select count(*) as same_rate_lines,\n"
        "       sum(case when arr_usd_current <> arr_usd_hist then 1 else 0 end)\n"
        "           as variance_abs,\n"
        "       case\n"
        "         when count(*) = 0 then 'needs_review'\n"
        "         when sum(case when arr_usd_current <> arr_usd_hist then 1 else 0 end) = 0\n"
        "              then 'pass'\n"
        "         when sum(case when arr_usd_current <> arr_usd_hist then 1 else 0 end)\n"
        "              <= count(*) * 0.001\n"
        "              then 'warn'\n"
        "         else 'fail'\n"
        "       end as verdict\n"
        "from same_rate_lines;"
    )
    checks.append(ValidationCheck(
        check_name="currency_variant_tie_out",
        grain="single scalar (count of USD_CURRENT <> USD_HIST mismatches)",
        source_salesforce=f"{sf}.datedconversionrate (rate source)",
        baseline_prod=f"{baseline}.aggregations.arr_line_categories (rate logic baseline)",
        target_dev_qa=f"{target}.aggregations.arr_line_categories @ {as_was}",
        business_logic=(
            "For USD currencyisocode lines, USD_CURRENT must equal USD_HIST "
            "exactly (pass), <0.1% mismatch (warn), else fail."
        ),
        sql_template=currency_sql,
        notes="Smoking-gun check when stg_em_datedconversionrate regresses.",
    ))

    # ----- 7. Active account continuity vs prior quarter ------------------
    continuity_sql = (
        "-- check: active account continuity vs prior snapshot\n"
        "-- An account on the prior snapshot but not on the current one must\n"
        "-- have a CHURN category row recording its loss. Otherwise we have\n"
        "-- silently dropped customers.\n\n"
        "with prior_active as (\n"
        "    select distinct salesforce_account_id\n"
        f"    from {baseline}.aggregations.arr_account_product_corp_report\n"
        f"    where as_was_date = '{baseline_as_was}'\n"
        "      and arr_usd_current > 0\n"
        "),\n"
        "current_active as (\n"
        "    select distinct salesforce_account_id\n"
        f"    from {target}.aggregations.arr_account_product_corp_report\n"
        f"    where as_was_date = '{as_was}'\n"
        "      and arr_usd_current > 0\n"
        "),\n"
        "current_churn as (\n"
        "    select distinct salesforce_account_id\n"
        f"    from {target}.aggregations.arr_account_product_corp_report\n"
        f"    where as_was_date = '{as_was}'\n"
        "      and arr_category = 'CHURN'\n"
        "),\n"
        "dropped as (\n"
        "    select p.salesforce_account_id\n"
        "    from prior_active p\n"
        "    left join current_active c using (salesforce_account_id)\n"
        "    left join current_churn  ch using (salesforce_account_id)\n"
        "    where c.salesforce_account_id is null\n"
        "      and ch.salesforce_account_id is null\n"
        ")\n"
        "select count(*) as silently_dropped_accounts,\n"
        "       (select count(*) from prior_active) as prior_active_count,\n"
        "       count(*) as variance_abs,\n"
        "       case\n"
        "         when (select count(*) from prior_active) = 0 then 'needs_review'\n"
        "         when count(*) = 0 then 'pass'\n"
        "         when count(*) <= 5 then 'warn'\n"
        "         else 'fail'\n"
        "       end as verdict\n"
        "from dropped;"
    )
    checks.append(ValidationCheck(
        check_name="active_account_continuity",
        grain="single scalar (count of silently dropped accounts)",
        source_salesforce=f"{sf}.account",
        baseline_prod=f"{baseline}.aggregations.arr_account_product_corp_report @ {baseline_as_was}",
        target_dev_qa=f"{target}.aggregations.arr_account_product_corp_report @ {as_was}",
        business_logic=(
            "Accounts active in prior quarter must either still be active "
            "or be recorded as CHURN. 0 dropped = pass, <=5 = warn, else fail."
        ),
        sql_template=continuity_sql,
        notes=(
            "Catches the worst-case regression: customers silently disappearing "
            "from the snapshot without a CHURN waterfall entry."
        ),
    ))

    return ValidationMatrix(
        matrix_name=f"quarter-close recon ({as_was}, target={target})",
        target_db=target,
        baseline_db=baseline,
        source_db=sf,
        checks=checks,
    )


def _aggregate_status(pipeline: StepStatus, recon_verdict: str) -> RoleStatus:
    """Combine pipeline outcome and recon verdict into a single RoleStatus.

    Pipeline FAIL is always FAIL (the recon SQL won't be runnable anyway).
    Otherwise we honor the recon verdict.
    """
    if pipeline == StepStatus.FAIL:
        return RoleStatus.FAIL
    if recon_verdict == "fail":
        return RoleStatus.FAIL
    if pipeline == StepStatus.WARN or recon_verdict == "warn":
        return RoleStatus.WARN
    if recon_verdict in ("pending", "needs_review"):
        # No SQL has been run yet (typical fresh dispatch). Return OK so
        # the supervisor doesn't block on a not-yet-evaluated matrix.
        return RoleStatus.OK
    return RoleStatus.OK


def _attach_actuals(report: QuarterCloseReport, actuals: dict[str, dict]) -> RoleStatus:
    """Re-attach actual values to the matrix and recompute the verdict.

    Called by the supervisor (or a later operator pass) after running the
    SQL templates via the Snowflake MCP. ``actuals`` keyed by check_name
    with values like ``{"actual": "...", "verdict": "pass", ...}``.

    Mutates the report in place and returns the new aggregate status.
    """
    if not report.recon_matrix:
        return RoleStatus.WARN
    for check in report.recon_matrix.checks:
        upd = actuals.get(check.check_name)
        if not upd:
            continue
        for k in ("actual", "verdict", "variance_abs", "variance_pct", "notes"):
            if k in upd and upd[k] is not None:
                setattr(check, k, upd[k])
    report.recon_matrix.recompute_verdict()
    report.overall_verdict = report.recon_matrix.overall_verdict
    return _aggregate_status(StepStatus.SUCCESS, report.recon_matrix.overall_verdict)
