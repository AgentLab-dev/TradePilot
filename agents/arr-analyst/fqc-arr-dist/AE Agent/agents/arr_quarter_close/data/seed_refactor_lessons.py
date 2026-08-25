"""IA Refactor (refactoring-discussion) lessons seeder.

Distills the cross-session refactoring-discussion thread (eda-dbt-em IA
Refactor / data-mesh migration era, including the 'Refactoring Code Fixes',
'Refactored QA / UAT Testing', and 'Refactoring Discussion for EM' chats)
into role-targeted lessons. These are high-signal, hard-won learnings that
the agent must apply on every refactor / RCA / cross-environment validation
task.

Run once after on-boarding the lessons store, or any time the refactor
playbook changes:

    python -m agents.arr_quarter_close.data.seed_refactor_lessons

Idempotent - duplicates bump ``occurrence_count`` instead of inserting.
"""

from __future__ import annotations

from pathlib import Path

from agents.arr_quarter_close.lessons import GLOBAL_ROLE, get_recorder


REFACTOR_LESSONS: list[dict] = [
    # ---- Global: refactor playbook --------------------------------------
    {
        "role": GLOBAL_ROLE,
        "category": "best_practice",
        "lesson": (
            "Three-source cross-validation is the gold standard for any "
            "ARR-touching refactor: PVQ (Prior-version Q baseline at "
            "`$HOME/Documents/Cursor/New_PvQ`) vs "
            "CERTIFIED_PROD.FINANCE.* vs CERTIFIED_QA.FINANCE.*. Validate at "
            "the finest grain (account_id, agreement_id, fiscal_quarter_name, "
            "arr_category, product_code_l3, as_was_date). Fixed test "
            "agreement_ids that have surfaced refactor bugs before: "
            "a1X4X000007UyvvUAC, a1X80000001uPYwEAM, a1XVT00000CSn6w2AD."
        ),
        "evidence": (
            "Refactored QA / UAT Testing thread: 5+ RCA rounds against PVQ "
            "for ssr_off_cycle, up_for_renewal, sku_change_list mismatches."
        ),
        "tags": ["refactor", "pvq", "validation", "snowflake"],
        "confidence": "high",
    },
    {
        "role": GLOBAL_ROLE,
        "category": "best_practice",
        "lesson": (
            "PVQ vs QA divergence is NOT automatically a refactor bug. "
            "Three buckets: (1) Intentional design change (e.g. "
            "`is_ssr.last_fq_for_agreement` replacing `term_end_in_quarter` - "
            "PVQ design decision, NOT a regression). (2) Sourcing change "
            "with same logical intent (e.g. `finance_line_data` via "
            "`finance_line_analytics` join instead of `bt_sku_analytics` - "
            "may yield different values when joins behave differently). "
            "(3) True refactor regression (must be fixed). Classify "
            "category BEFORE proposing a fix."
        ),
        "evidence": (
            "Refactored QA / UAT Testing - `is_ssr` change was bucket (1); "
            "`up_for_renewal_fn` dual term_end fan-out was bucket (3)."
        ),
        "tags": ["refactor", "pvq", "classification"],
        "confidence": "high",
    },
    {
        "role": GLOBAL_ROLE,
        "category": "tooling",
        "lesson": (
            "Refactor RCA reports follow a stable filename convention: "
            "`$HOME/Documents/Cursor/Documents/"
            "Refactor_QA/pvq_qa_rca_report_<YYYY-MM-DD>.html`. Always cite "
            "the report path + issue number when posting an RCA back to Jira "
            "(e.g. 'issue-1 for as_was_date 2026-04-12'); never restate the "
            "analysis from memory."
        ),
        "evidence": "User-supplied report path used as canonical RCA reference.",
        "tags": ["refactor", "rca", "documentation"],
        "confidence": "high",
    },
    {
        "role": GLOBAL_ROLE,
        "category": "edge_case",
        "lesson": (
            "`finance_line_analytics` history depth differs sharply by DB: "
            "CERTIFIED_DEV holds only the last ~7 as_was_dates, while "
            "CERTIFIED_PROD holds the full 70+ day history. Any function or "
            "model that `ref()`s finance_line_analytics will pull a SHORT "
            "window when deployed in dev, producing apparent gaps vs prod. "
            "Always run historical recon queries against CERTIFIED_QA or "
            "CERTIFIED_PROD - never CERTIFIED_DEV."
        ),
        "evidence": (
            "Refactored QA / UAT Testing - root-cause table showed dev had "
            "7 distinct as_was_dates, prod had 71."
        ),
        "tags": ["snowflake", "history", "dev-vs-prod"],
        "confidence": "high",
    },
    {
        "role": GLOBAL_ROLE,
        "category": "best_practice",
        "lesson": (
            "Multi-repo awareness: ARR work spans THREE repos that move in "
            "lockstep during IA Refactor: eda-dbt-base (sources, SCD2) -> "
            "eda-dbt-gtm (staging wrappers) -> eda-dbt-em (finance models). "
            "Plus eda-dbt-semantic-layer is a SEPARATE repo for downstream "
            "metric definitions. A refactor PR in eda-dbt-em may need a "
            "parallel PR in semantic-layer (or the metric definitions break). "
            "Always grep across all four repos before declaring scope done."
        ),
        "evidence": "Refactoring Code Fixes thread: PR review of eda-dbt-semantic-layer #51 alongside eda-dbt-em #339.",
        "tags": ["multi-repo", "scope", "semantic-layer"],
        "confidence": "high",
    },

    # ---- Supervisor: cross-ticket coordination --------------------------
    {
        "role": "supervisor",
        "category": "best_practice",
        "lesson": (
            "EDADEV cross-ticket dependency pattern: when a refactor needs "
            "GTM-side SCD2 column enablement (or any upstream platform "
            "change), file an EDADEV ticket and link it as a blocker on the "
            "EDAEM ticket. Template: clone EDADEV-2861 / EDAEM-3411. The "
            "supervisor should refuse to mark the EDAEM ticket Ready-for-QA "
            "until the EDADEV dependency is Resolved."
        ),
        "evidence": "Refactored QA / UAT Testing - separate ref() for stg_em_agreement_line_item_scd2 blocked on EDADEV-2861.",
        "tags": ["edadev", "dependency", "blocker"],
        "confidence": "high",
    },

    # ---- ci-monitor: CI selector limitations ----------------------------
    {
        "role": "ci-monitor",
        "category": "failure",
        "lesson": (
            "CI uses `dbt build --select state:modified+ --defer` for slim "
            "CI - this catches DOWNSTREAM dependencies of changed nodes but "
            "NOT end-to-end-chain rebuilds. For refactor PRs that change "
            "shared staging (tmp_tbls_*, stg_arr_categories_*) the CI run "
            "looks clean but the downstream ARR tables remain stale until "
            "the next scheduled run. Flag refactor PRs that touch staging "
            "with the `needs-full-pipeline` label so cd-monitor triggers "
            "the adhoc_pipeline_runner_config path post-merge."
        ),
        "evidence": "Refactoring Code Fixes - PR #326/#327 passed CI but didn't trigger E2E.",
        "tags": ["ci", "state-modified", "refactor"],
        "confidence": "high",
    },
    {
        "role": "ci-monitor",
        "category": "tooling",
        "lesson": (
            "For QA-environment full pipeline runs (when state:modified+ "
            "isn't enough), the canonical anchor is "
            "`models/stage/table/adhoc_pipeline_runner_config.sql`. Bumping "
            "its `as_was_date` constant + merging the PR triggers a full "
            "end-to-end rebuild of stage tables, finance_line_analytics, "
            "arr_line/sku/subproduct/product (excluding SCD2 wrappers). "
            "Treat this file as a deployment-time switch, NOT a routine code "
            "change."
        ),
        "evidence": "Refactoring Code Fixes - adhoc_pipeline_runner_config built specifically for this purpose.",
        "tags": ["adhoc-runner", "qa", "full-pipeline"],
        "confidence": "high",
    },

    # ---- code-data-validator: dev-vs-prod + PVQ validation --------------
    {
        "role": "code-data-validator",
        "category": "best_practice",
        "lesson": (
            "Standard PVQ recon SQL template (parameterize account_id + "
            "agreement_id): `SELECT AS_WAS_DATE, ARR_CATEGORY, ACCOUNT_ID, "
            "AGREEMENT_ID, OPPORTUNITY_ID, FISCAL_QUARTER_NAME, TERM_END, "
            "PRODUCT_CODE_L1, PRODUCT_CODE_L2, PRODUCT_CODE_L3, "
            "SSR_UP_FOR_RENEWAL_ARR, SSR_OFF_CYCLE_ARR, TOTAL_OFF_CYCLE "
            "FROM <db>.FINANCE.bt_product_arr_categories WHERE ...`. Run "
            "against CERTIFIED_PROD (prod), CERTIFIED_QA (refactored), and "
            "CERTIFIED_QA bt_product_arr_categories_pvq (PVQ-mirrored)."
        ),
        "evidence": "Refactored QA / UAT Testing - canonical 13-column recon query reused across sessions.",
        "tags": ["recon", "snowflake", "pvq"],
        "confidence": "high",
    },
    {
        "role": "code-data-validator",
        "category": "best_practice",
        "lesson": (
            "When refactoring `up_for_renewal_fn` / `get_price_quantity_fn` "
            "/ any other Snowflake UDF or table function, validate against "
            "`certified_qa.stage.<fn>('YYYY-MM-DD'::date)` directly - not "
            "just the downstream materialized table. Function output can "
            "differ from the table even on the same date when the table is "
            "stale or fan-out happens in the intermediate join."
        ),
        "evidence": "Refactored QA / UAT Testing - up_for_renewal_fn dual term_end fan-out only visible at function grain.",
        "tags": ["function", "validation", "refactor"],
        "confidence": "high",
    },

    # ---- implementer: refactor anti-patterns ---------------------------
    {
        "role": "implementer",
        "category": "failure",
        "lesson": (
            "Converting a staging table from `table` to `incremental` "
            "materialization introduces TWO recurring failure modes: "
            "(1) `Database Error: ambiguous column name 'AS_WAS_DATE'` when "
            "the macro that filters on as_was_date now sees the column from "
            "both the existing target and the new batch. Fix: qualify the "
            "filter with the source alias. "
            "(2) Schema drift: `columns are specified in the schema but are "
            "not in the relation` after the first incremental run. Fix: run "
            "`--full-refresh` once on the first deploy."
        ),
        "evidence": "Refactoring Code Fixes - PR #339 (price_quantity ambiguous) and PR #336 (fse_attributes drift).",
        "tags": ["incremental", "as-was-date", "schema-drift"],
        "confidence": "high",
    },
    {
        "role": "implementer",
        "category": "best_practice",
        "lesson": (
            "Dual-`term_end` fan-out anti-pattern: when a subquery does "
            "`SELECT DISTINCT account_id, agreement_id, agreement_end_date, "
            "term_end FROM finance_line_analytics`, agreements with multiple "
            "term_end values (only 2 of 268,033 agreements at last count: "
            "a1X80000001uPYwEAM and a1X80000001ifFQEAY) get duplicated rows, "
            "inflating downstream joins. Fix: replace with "
            "`SELECT account_id, agreement_id, MAX(agreement_end_date), "
            "MAX(term_end) ... GROUP BY account_id, agreement_id`. Applied "
            "in 5 subqueries of `up_for_renewal_fn.sql`."
        ),
        "evidence": "Refactored QA / UAT Testing - documented as the single primary fix for up_for_renewal_fn.",
        "tags": ["fan-out", "agreement", "up-for-renewal"],
        "confidence": "high",
    },
    {
        "role": "implementer",
        "category": "best_practice",
        "lesson": (
            "Account categorization rule (HCM/FIN/Platform): an account that "
            "owns ANY HCM or FIN product is categorized as HCM-Only, "
            "FIN-Only, or Platform. Standalone HCM or standalone FIN values "
            "must NEVER appear in the product-array categorization output. "
            "When applying CASE-statement fixes, validate via Snowflake dev "
            "with: `SELECT account_category, COUNT(*) FROM "
            "bt_account_product_corp_report WHERE 'HCM' = ANY(product_array) "
            "GROUP BY 1` - 'HCM' alone in the result should be 0 rows."
        ),
        "evidence": "Refactored QA / UAT Testing - explicit fix for udf_product_mix_* categorization.",
        "tags": ["account-categorization", "hcm", "fin", "platform"],
        "confidence": "high",
    },
    {
        "role": "implementer",
        "category": "best_practice",
        "lesson": (
            "`get_price_quantity_fn.sql` separately ref()s "
            "`stg_em_agreement_line_item_scd2` for `expansion_quantity` "
            "because the GTM-side `wd_agreement_line_item_scd2` does NOT "
            "expose that column today. This is NOT a refactor bug - both QA "
            "and PVQ do the same thing. Keep the separate ref() until the "
            "EDADEV ticket enabling the column on the GTM SCD2 is resolved. "
            "Document the dependency in any PR that touches this file."
        ),
        "evidence": "Refactored QA / UAT Testing - documented in EDAEM-3411 + EDADEV-2861.",
        "tags": ["scd2", "gtm", "expansion-quantity"],
        "confidence": "high",
    },

    # ---- requirements-analyzer: SSR business rules ----------------------
    {
        "role": "requirements-analyzer",
        "category": "best_practice",
        "lesson": (
            "SSR off-cycle invariant (every non-zero `ssr_off_cycle_arr` "
            "row must satisfy): `(is_superseded AND is_early_termination) "
            "OR (is_superseding AND NOT has_related_bb_product AND NOT "
            "term_end_in_quarter AND arr_category IN ('Net New','Add On',"
            "'Expansion','Contraction'))`. Cite this as the validation rule "
            "for any spec that touches SSR / agreement renewal. Business "
            "meaning: superseding agreement where the old agreements it "
            "replaced had `term_end_in_quarter=TRUE` but `agreement_end_date` "
            "NOT in that quarter - the replacement happened BEFORE the old "
            "agreements' natural expiry, so it's an off-cycle SSR rather "
            "than a clean renewal."
        ),
        "evidence": "Refactored QA / UAT Testing - canonical SSR off-cycle rule, posted multiple times.",
        "tags": ["ssr", "off-cycle", "business-rule"],
        "confidence": "high",
    },
    {
        "role": "requirements-analyzer",
        "category": "best_practice",
        "lesson": (
            "`is_renewing_agreement` MUST include `term_start_in_quarter` in "
            "its predicate. Omitting it (a frequent refactor regression) "
            "shifts ARR from `up_for_renewal` to `off_cycle` for all "
            "superseding agreements after the start quarter. Flag any spec "
            "or PR that touches renewal logic without explicitly mentioning "
            "`term_start_in_quarter` for clarifier follow-up."
        ),
        "evidence": "Refactored QA / UAT Testing - identified as 'Medium' magnitude expected output difference.",
        "tags": ["renewal", "term-start", "off-cycle"],
        "confidence": "high",
    },

    # ---- debugger: known refactor RCA patterns -------------------------
    {
        "role": "debugger",
        "category": "best_practice",
        "lesson": (
            "PBU-Manual records pattern (a known RCA shortcut): when "
            "PVQ-vs-QA mismatch rows are 100% concentrated in "
            "`agree_data_migrations = 'NonMigrated-PBU-Manual'` with PVQ "
            "stage_name='9- Closed/Won' and QA stage_name=NULL, the root "
            "cause is the UNION trick in `stg_em_opp_source_temp.sql` (the "
            "`LEFT JOIN ... LIMIT 0` against COMMON_SOURCE structurally "
            "drops Account attributes for PBU rows). QA's surrogate-key "
            "join architecture is actually CORRECT here - PVQ/Prod is "
            "structurally deficient. Fix: hardcode the PBU stage_name "
            "fallback in QA; leave PARENT_ACCOUNT_NAME alone (QA is right)."
        ),
        "evidence": "Refactored QA / UAT Testing - 24,140 mismatches, 100% PBU-Manual, full RCA documented.",
        "tags": ["pbu", "stage-name", "parent-account", "union-trick"],
        "confidence": "high",
    },
    {
        "role": "debugger",
        "category": "best_practice",
        "lesson": (
            "Before declaring a refactor regression, ALWAYS check if QA is "
            "actually IMPROVING coverage vs Prod. QA's surrogate-key joins "
            "achieved 99.97% fidelity to Salesforce for "
            "`parent_account_name` on PBU records where Prod/PVQ return "
            "NULL for all 5,261 PBU accounts. A 'mismatch' isn't always a "
            "bug - sometimes the refactor fixes a long-standing prod "
            "deficiency. Include a 'QA improvements over Prod' subsection "
            "in the RCA so the requester sees the upside."
        ),
        "evidence": "Refactored QA / UAT Testing - parent_account_name analysis conclusion.",
        "tags": ["qa-improvement", "salesforce", "fidelity"],
        "confidence": "high",
    },
    {
        "role": "debugger",
        "category": "best_practice",
        "lesson": (
            "Sourcing-change recon: when a refactor changes the source of "
            "a derived column (e.g. `term_start`/`term_end` moves from "
            "`bt_sku_analytics` join in PVQ to `finance_line_data` via "
            "`finance_line_analytics` join in QA), values may differ even "
            "though logic is equivalent. Validate at agreement grain via "
            "Snowflake before opening a regression ticket: run both join "
            "expressions inline as CTEs and diff the (term_start, term_end) "
            "pairs."
        ),
        "evidence": "Refactored QA / UAT Testing - $141K ARR shifted between ssr_off_cycle and off_cycle for a1X4X000007UyvvUAC.",
        "tags": ["sourcing", "join-diff", "agreement-grain"],
        "confidence": "high",
    },

    # ---- pr-author: refactor-era PR hygiene -----------------------------
    {
        "role": "pr-author",
        "category": "user_preference",
        "lesson": (
            "Refactor-era PR title format: `<EDAEM-XXXX>: <verb> "
            "<short scope>` (e.g. `EDAEM-3458: Fix up_for_renewal dual "
            "term_end fan-out`). PR body MUST start with the Jira link, "
            "scope summary, and any cross-linked Jiras (EDADEV-* for GTM "
            "dependencies, semantic-layer PR# for downstream metric "
            "changes). Never open a refactor PR without at least one "
            "linked Jira."
        ),
        "evidence": "Refactored QA / UAT Testing - user explicitly required Jira# in PR name AND link in description.",
        "tags": ["pr-format", "jira", "cross-link"],
        "confidence": "high",
    },

    # ---- qa-handoff: refactor-specific recon attachments ----------------
    {
        "role": "qa-handoff",
        "category": "best_practice",
        "lesson": (
            "For refactor / PVQ-recon tickets, the QA-handoff comment MUST "
            "attach the side-by-side PVQ-vs-QA-vs-Prod recon table at the "
            "test-fixture agreement grain (a1X4X000007UyvvUAC and any other "
            "agreement_ids from the requirements spec). The acceptable "
            "tolerance is ZERO row-count drift for `ssr_off_cycle_arr`, "
            "`ssr_up_for_renewal_arr`, and any other named-bucket ARR "
            "category; cosmetic differences (sub-penny rounding, array "
            "ordering) can be called out as 'no action needed'."
        ),
        "evidence": "Refactored QA / UAT Testing - recurring pattern of 3-way recon table requirements.",
        "tags": ["recon-table", "pvq", "tolerance"],
        "confidence": "high",
    },

    # ---- code-data-validator: schema-drift detector ---------------------
    {
        "role": "code-data-validator",
        "category": "best_practice",
        "lesson": (
            "Schema-drift early-warning: after any refactor that consolidates "
            "or renames staging columns, run "
            "`SELECT column_name FROM information_schema.columns WHERE "
            "table_schema='stage' AND table_name=<refactored_table>` against "
            "BOTH the dev DB (where the refactor lives) and the prod DB "
            "(pre-deploy state). Any column present in dev's .yml but missing "
            "from prod's relation = an `--full-refresh` will be required on "
            "first deploy."
        ),
        "evidence": "Refactoring Code Fixes - stg_arr_categories_fse_attributes drift on PR #336.",
        "tags": ["schema-drift", "incremental", "information-schema"],
        "confidence": "medium",
    },
]


def seed(project_dir: Path = Path(".")) -> int:
    recorder = get_recorder(project_dir)
    n = 0
    for item in REFACTOR_LESSONS:
        if recorder.record(**item) is not None:
            n += 1
    print(f"Seeded {n} refactor-discussion lessons "
          "(re-running bumps occurrence_count for existing entries).")
    return n


if __name__ == "__main__":
    import sys
    sys.exit(0 if seed(Path(".")) >= 0 else 1)
