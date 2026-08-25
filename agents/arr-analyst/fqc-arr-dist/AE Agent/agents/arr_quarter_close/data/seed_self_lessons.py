"""Self-knowledge seeder: teach the agent its own design.

Walks the ARR Quarter Close agent codebase (README, supervisor, sub-agents)
and distills the architecturally-important patterns into role-targeted
lessons. The result lands in ``data/lessons/`` so every future run prepends
these invariants into its plan / LLM prompt.

Run once after a refactor or when on-boarding the lessons store:

    python -m agents.arr_quarter_close.data.seed_self_lessons

Idempotent - duplicates bump ``occurrence_count`` instead of inserting.
"""

from __future__ import annotations

from pathlib import Path

from agents.arr_quarter_close.lessons import GLOBAL_ROLE, get_recorder


SELF_LESSONS: list[dict] = [
    # ---- Architecture-wide (apply to every role) -------------------------
    {
        "role": GLOBAL_ROLE,
        "category": "best_practice",
        "lesson": (
            "Architecture follows the multi-agent Supervisor / Manager pattern "
            "(OpenAI 'Practical Guide to Building Agents' 2025; LangGraph; "
            "Anthropic 'Building Effective Agents' Dec 2024). The Supervisor "
            "holds state and dispatches; sub-agents are stateless workers. "
            "Never let a sub-agent talk to another sub-agent directly - go "
            "through the supervisor."
        ),
        "evidence": "agents/arr_quarter_close/README.md - 'Manager / Supervisor / Orchestrator' design note.",
        "tags": ["architecture", "supervisor-pattern", "multi-agent"],
        "confidence": "high",
    },
    {
        "role": GLOBAL_ROLE,
        "category": "best_practice",
        "lesson": (
            "Public identity is FQC-ARR (Finance ARR Quarter Close). All "
            "aliases - FQC, FQCARR, FQC-ARR, 'Finance ARR Quarter Close', "
            "'ARR Quarter Close', 'ARR close' - resolve to the same supervisor. "
            "Never rename the folder, module, class, or rule filenames - it would "
            "break every import / rule glob / data-agent reference."
        ),
        "evidence": "supervisor.py: SUPERVISOR_DISPLAY_NAME / SUPERVISOR_SHORT_CODE / SUPERVISOR_ALIASES.",
        "tags": ["naming", "identity"],
        "confidence": "high",
    },
    {
        "role": GLOBAL_ROLE,
        "category": "best_practice",
        "lesson": (
            "Every sub-agent returns a typed RoleResult (role, status in "
            "{ok, needs_input, warn, fail, skipped}, summary, payload, "
            "artifacts, pause_reason, preferred_model). The supervisor ONLY "
            "reads typed fields - never parse free-form text out of summary. "
            "Add new fields to the contract, don't smuggle them through summary."
        ),
        "evidence": "agents/arr_quarter_close/contracts.py - 'Design rules' header.",
        "tags": ["contracts", "typed-io"],
        "confidence": "high",
    },
    {
        "role": GLOBAL_ROLE,
        "category": "best_practice",
        "lesson": (
            "All public dataclasses must be JSON-serializable via asdict() - "
            "no Path / datetime / Enum in the public field set. Convert to "
            "string at the boundary. This keeps SDK / SANA / pytest mock "
            "callers portable."
        ),
        "evidence": "contracts.py:1-19 dataclass design rules.",
        "tags": ["contracts", "serialization"],
        "confidence": "high",
    },
    {
        "role": GLOBAL_ROLE,
        "category": "tooling",
        "lesson": (
            "Snowflake / Salesforce / dbt / Sigma queries always go through "
            "MCP via CallMcpTool - never write Python scripts that authenticate "
            "directly (externalbrowser SSO hangs the agent for minutes). "
            "Jira and Confluence are the explicit exception: use curl + API "
            "token from $JIRA_EMAIL / $JIRA_API_TOKEN. Google Drive has no MCP - "
            "use Snowflake's BASE_PROD.GOOGLE_SHEETS.* if Fivetran-synced, else "
            "CSV export URL, manual download, or cursor-ide-browser MCP."
        ),
        "evidence": "Workspace rule prefer-mcp-for-data-platforms.mdc.",
        "tags": ["mcp", "snowflake", "jira", "tooling"],
        "confidence": "high",
    },
    {
        "role": GLOBAL_ROLE,
        "category": "tooling",
        "lesson": (
            "Use ref()/source() exclusively in dbt models - never hardcode "
            "table names. Use `{{ tcv_to_arr() }}` / `{{ tcv_to_acv() }}` "
            "macros (TCV is raw from Agreement Line; ARR annualizes over "
            "contract term; ACV normalizes to first-year). Corrected TCV is "
            "always COALESCE(corrected_tcv, raw_tcv) via "
            "stg_em_lkp_wd_fin_tcv_correction."
        ),
        "evidence": "Workspace rules salesforce-bsa-finance-analyst.mdc + finance-functional-analytics.mdc.",
        "tags": ["dbt", "macros", "arr", "tcv"],
        "confidence": "high",
    },
    {
        "role": GLOBAL_ROLE,
        "category": "best_practice",
        "lesson": (
            "Default LLM model = claude-opus-4-7-thinking-xhigh. Override "
            "precedence: --model > $FQC_ARR_DEFAULT_MODEL > "
            "contracts.DEFAULT_LLM_MODEL. The supervisor itself runs NO LLM. "
            "Only requirements_analyzer / clarifier / implementer (+ debugger "
            "fix prompt) are LLM-driven; they emit `preferred_model` on the "
            "RoleResult so the caller (Cursor SDK, SANA, Cursor chat) routes "
            "to the right model."
        ),
        "evidence": "README.md '## Default LLM model' + contracts.resolve_default_llm_model.",
        "tags": ["llm", "model-selection"],
        "confidence": "high",
    },
    {
        "role": GLOBAL_ROLE,
        "category": "best_practice",
        "lesson": (
            "Three auth modes: FULL_AUTO (no pauses, only when explicitly "
            "authorized), SMART_GATES (default - pauses before Jira/PR/Slack/QA "
            "writes), GATED_MINIMAL, GATED_FULL. CLI `--auto` is the shortcut "
            "for FULL_AUTO. NEVER push to GitHub or open a PR in any mode "
            "except FULL_AUTO without an explicit approval pause - the pr-author "
            "enforces this hard rule."
        ),
        "evidence": "contracts.AuthMode + pr_author.py docstring.",
        "tags": ["authorization", "safety"],
        "confidence": "high",
    },

    # ---- Supervisor ------------------------------------------------------
    {
        "role": "supervisor",
        "category": "best_practice",
        "lesson": (
            "Two-mode dispatcher: Mode A (scheduled - delegates to "
            "ARRCloseOrchestrator core) and Mode B (ticket-driven 10-role DAG). "
            "Mode-resolution rule: ticket only -> Mode B; as_was_date only -> "
            "Mode A; both -> Mode B then a snapshot rebuild. --quarter-close "
            "always routes through Mode B so the on-demand quarter-close-runner "
            "gets dispatched (with its thinking-log entry + recon matrix)."
        ),
        "evidence": "supervisor.py: SupervisorInput.resolve_mode() + run() routing.",
        "tags": ["dag", "mode", "routing"],
        "confidence": "high",
    },
    {
        "role": "supervisor",
        "category": "best_practice",
        "lesson": (
            "Canonical DAG order: jira-intake -> requirements-analyzer -> "
            "code-data-validator -> clarifier -> implementer -> test-runner -> "
            "pr-author -> ci-monitor -> cd-monitor -> qa-handoff. Debugger and "
            "quarter-close-runner are on-demand (NOT in the canonical tuple) - "
            "dispatched via auto-on-FAIL, Slack `task:` side-channel, or CLI "
            "(--debug-model / --quarter-close)."
        ),
        "evidence": "subagents/__init__.py: ORDER and ON_DEMAND tuples.",
        "tags": ["dag", "ordering"],
        "confidence": "high",
    },
    {
        "role": "supervisor",
        "category": "best_practice",
        "lesson": (
            "Recognized side-channel commands (Slack `task:` prefix): "
            "skip, pause, cancel, status, debug, quarter-close. Anything "
            "else is queued as a free-form side task and surfaced in the "
            "final report so a human or the Cursor coding agent can pick it "
            "up later. Polling cursor is `last_side_channel_ts` on "
            "SupervisorState - resume-safe."
        ),
        "evidence": "supervisor.Supervisor.SIDE_TASK_COMMANDS.",
        "tags": ["side-channel", "slack"],
        "confidence": "high",
    },
    {
        "role": "supervisor",
        "category": "best_practice",
        "lesson": (
            "Debug-on-failure is ON by default - whenever any role returns "
            "FAIL, the debugger auto-dispatches BEFORE the supervisor pauses, "
            "so the operator sees a debug bundle alongside the pause point. "
            "Disable with --no-debug-on-failure. The debugger needs a "
            "TicketSpec from jira-intake - never auto-skip jira-intake when "
            "--debug-model is set."
        ),
        "evidence": "supervisor.Supervisor._maybe_debug_on_failure + _dispatch_debugger.",
        "tags": ["debugger", "auto-dispatch"],
        "confidence": "high",
    },
    {
        "role": "supervisor",
        "category": "best_practice",
        "lesson": (
            "Clarifier interactive timeout defaults to 600s. When clarifier "
            "returns NEEDS_INPUT, the supervisor surfaces the questions on "
            "stdin and waits; on timeout (or non-tty), falls back to "
            "pause-and-post to Jira. Set --clarifier-interactive-timeout 0 "
            "(or --no-clarifier-interactive) for unattended runs to skip "
            "straight to Jira."
        ),
        "evidence": "supervisor.SupervisorInput.clarifier_interactive_timeout_s.",
        "tags": ["clarifier", "ux"],
        "confidence": "medium",
    },

    # ---- jira-intake -----------------------------------------------------
    {
        "role": "jira-intake",
        "category": "best_practice",
        "lesson": (
            "Reads Jira via curl + API token (NOT the Atlassian MCP - it's "
            "broken in this env). Required env: JIRA_BASE_URL, JIRA_EMAIL, "
            "JIRA_API_TOKEN (per jira-api-access.mdc). Flattens ADF "
            "description to plain text and harvests labels / components / "
            "comments. Tries to extract bullet-style acceptance criteria; if "
            "none are found, signal NEEDS_INPUT instead of guessing."
        ),
        "evidence": "subagents/jira_intake.py docstring + body.",
        "tags": ["jira", "adf", "curl"],
        "confidence": "high",
    },

    # ---- requirements-analyzer ------------------------------------------
    {
        "role": "requirements-analyzer",
        "category": "best_practice",
        "lesson": (
            "Apply the KPI Spec framework from the finance-functional-architect "
            "skill: Business Definition, Formula, Grain, Periodicity, Currency "
            "Basis (USD_CURRENT/USD_HIST/USD_ACTUAL), Filters, Source of Truth, "
            "Validation Rule. Return STRICT JSON matching the RequirementsSpec "
            "dataclass (scope_summary, in_scope_models[], out_of_scope[], "
            "kpis[], questions[], confidence). If a field is unknown, leave "
            "it blank and ADD a question to questions[] - do NOT fabricate."
        ),
        "evidence": "subagents/requirements_analyzer.py + finance-functional-architect.mdc.",
        "tags": ["kpi-spec", "requirements"],
        "confidence": "high",
    },

    # ---- code-data-validator --------------------------------------------
    {
        "role": "code-data-validator",
        "category": "best_practice",
        "lesson": (
            "NEVER opens a Snowflake connection itself - emits SQL templates "
            "tagged with target DB (default finance_prod). The supervisor or "
            "the operator runs them via the Snowflake MCP. Code-side: walks "
            "the repo with grep/rg to map requirements -> dbt models / macros "
            "/ tests that would be touched (no edits). Output shape: "
            "ValidationReport(code_findings, data_findings)."
        ),
        "evidence": "subagents/code_data_validator.py docstring.",
        "tags": ["snowflake", "mcp", "validation"],
        "confidence": "high",
    },

    # ---- clarifier ------------------------------------------------------
    {
        "role": "clarifier",
        "category": "best_practice",
        "lesson": (
            "Emits BOTH a Markdown preview (for interactive stdin display) "
            "AND a Jira ADF payload (for pause-and-post). Posts to Jira only "
            "when auth_mode permits unattended writes (FULL_AUTO). One open "
            "question per ClarificationRequest entry; keep questions atomic "
            "so answers can be machine-parsed."
        ),
        "evidence": "subagents/clarifier.py docstring + flow.",
        "tags": ["clarifier", "adf"],
        "confidence": "medium",
    },

    # ---- implementer ----------------------------------------------------
    {
        "role": "implementer",
        "category": "best_practice",
        "lesson": (
            "Prepares branch metadata (name, base=qa by default, prefix=feature/) "
            "deterministically; the LLM only does the SQL edits. Branch naming: "
            "`feature/<ticket-key-lower>-<slug>`. Always check out from the "
            "qa branch (not main) for finance ARR work. Pair every .sql change "
            "with the matching .yml test (unique / not_null / accepted_values "
            "/ dbt_expectations) or a singular test under tests/ in the SAME "
            "PR - never split the test into a follow-up."
        ),
        "evidence": "subagents/implementer.py docstring + branch helpers.",
        "tags": ["git", "branch", "testing"],
        "confidence": "high",
    },

    # ---- test-runner ----------------------------------------------------
    {
        "role": "test-runner",
        "category": "best_practice",
        "lesson": (
            "Runs BOTH pytest (singular tests + Python harnesses under "
            "tests/pytest/) AND `dbt test` with the configured selectors. "
            "Aggregates into a TestReport with a ValidationMatrix the "
            "qa-handoff sub-agent attaches to Jira. dbt singular tests "
            "live under tests/ and must FAIL on the broken state (regression "
            "framing) - assert the bug-condition returns rows, then fix the "
            "model so the test passes."
        ),
        "evidence": "subagents/test_runner.py docstring + output shape.",
        "tags": ["testing", "dbt", "pytest"],
        "confidence": "high",
    },

    # ---- pr-author ------------------------------------------------------
    {
        "role": "pr-author",
        "category": "best_practice",
        "lesson": (
            "Hard rule: do NOT push or open the PR in any auth mode except "
            "FULL_AUTO without an explicit approval pause. Compute the PR "
            "shape (title, body, reviewers from CODEOWNERS + recent-PR "
            "pattern, labels) deterministically and return it in payload so "
            "the operator can review BEFORE approving. Base branch: qa (not "
            "main) for finance ARR work. PR title format: `<ticket-key>: "
            "<one-line summary>` - no agent self-attribution anywhere."
        ),
        "evidence": "subagents/pr_author.py docstring + auth-mode gating.",
        "tags": ["pr", "gh-cli", "safety"],
        "confidence": "high",
    },

    # ---- ci-monitor -----------------------------------------------------
    {
        "role": "ci-monitor",
        "category": "best_practice",
        "lesson": (
            "Polls `gh pr checks <PR>` every N minutes (default 10). Default "
            "target check name = `ci/dbt_cloud`; override with --check-name "
            "when the context was renamed (e.g. `dbtcloud-codevalidate / DBT "
            "Code Validation`). Stops at terminal state (success/failure). On "
            "success, emits the finance_dev SQL validation queries the "
            "supervisor runs via the Snowflake MCP. Posts X-of-N progress "
            "from the dbt log step (regex `(\\d+) of (\\d+) (START|OK|ERROR)`)."
        ),
        "evidence": "subagents/ci_monitor.py docstring + bin/watch_pr_ci.py.",
        "tags": ["ci", "gh", "dbt-cloud", "polling"],
        "confidence": "high",
    },

    # ---- cd-monitor -----------------------------------------------------
    {
        "role": "cd-monitor",
        "category": "best_practice",
        "lesson": (
            "Polls the dbt Cloud run that CD spawns. If no run id is known "
            "yet, waits for one to appear via the dbt MCP / API. Reuses the "
            "prior-quarter pattern in .cursor/cloud-agent/monitor_dbt_run.py "
            "(dbt Cloud API + Snowflake + Slack DM). Required env: "
            "DBT_CLOUD_HOST, DBT_CLOUD_ACCOUNT_ID, DBT_CLOUD_API_TOKEN. Use "
            "curl as the fallback when Python's requests hits SSL issues on "
            "the privatelink host."
        ),
        "evidence": "subagents/cd_monitor.py docstring + bin/watch_dbt_run.py.",
        "tags": ["cd", "dbt-cloud", "polling"],
        "confidence": "high",
    },

    # ---- qa-handoff ----------------------------------------------------
    {
        "role": "qa-handoff",
        "category": "best_practice",
        "lesson": (
            "Posts a Jira status comment as an ADF table with: PR url + merge "
            "sha, CD run id + deployed-to-QA confirmation, the 7-col "
            "ValidationMatrix (or recon table when --quarter-close was set), "
            "and @-mentions of every uid in notify_user_ids resolved against "
            "slack_directory.json. Optionally transitions the ticket to "
            "'Ready for QA'. Pauses before posting in any auth mode != FULL_AUTO. "
            "Attaches pytest junit.xml + dbt target/ output when available."
        ),
        "evidence": "subagents/qa_handoff.py docstring + ADF helpers.",
        "tags": ["qa", "jira", "adf", "handoff"],
        "confidence": "high",
    },

    # ---- debugger -------------------------------------------------------
    {
        "role": "debugger",
        "category": "best_practice",
        "lesson": (
            "BFS-walks upstream lineage of target_model via ripgrep on `ref()` "
            "calls (no `dbt list` needed; works without a compiled project). "
            "Depth cap = 5. Produces: LineageNode[], ValidationMatrix (one "
            "row per lineage node, 7-col shape), ACAnalysis[] (one row per "
            "acceptance criterion), ranked RootCauseHypothesis[], ProposedFix "
            "(file + LLM prompt - NEVER writes the change itself), and a "
            "PytestHarnessSpec under tests/pytest/ (both .gitignored)."
        ),
        "evidence": "subagents/debugger.py docstring (lines 1-29) + MAX_LINEAGE_DEPTH.",
        "tags": ["lineage", "rca", "matrix"],
        "confidence": "high",
    },
    {
        "role": "debugger",
        "category": "best_practice",
        "lesson": (
            "Jira ADF comment shape is ticket-type-aware: Bug -> 'Root cause "
            "+ reproducible fix' + Repro steps + Regression test. "
            "Story/Task/Sub-task/Epic -> 'Debug findings' + Suggested "
            "investigation focus. Always pause before posting unless auth_mode "
            "= FULL_AUTO."
        ),
        "evidence": "subagents/debugger.py: jira_update_adf shaping by issue_type.",
        "tags": ["jira", "adf", "ticket-type"],
        "confidence": "high",
    },

    # ---- quarter-close-runner ------------------------------------------
    {
        "role": "quarter-close-runner",
        "category": "best_practice",
        "lesson": (
            "Two-phase: (1) Pipeline phase (optional) delegates to "
            "ARRCloseOrchestrator for the standard ARR build sequence: "
            "tmp_tbls -> arr_line_categories -> sku/subproduct/product rollups -> "
            "arr_account_product_corp_report -> dbt test. (2) Recon phase "
            "(always) builds 7 ARR-specific tie-out checks: waterfall_balance, "
            "total_arr, row-parity for arr_line/sku/account_product_corp, "
            "currency_variant_tie_out, active_account_continuity. Tolerance: "
            "<1% = pass, <5% = warn, else fail."
        ),
        "evidence": "subagents/quarter_close_runner.py docstring + 7-check enum.",
        "tags": ["quarter-close", "recon", "arr"],
        "confidence": "high",
    },
    {
        "role": "quarter-close-runner",
        "category": "best_practice",
        "lesson": (
            "Known FY close snapshot dates live in core.KNOWN_FY_CLOSE_DATES "
            "(mirrors dbt_project.yml::arr_refactor_as_was_date_list): "
            "2025-05-08, 2025-08-11, 2025-11-10, 2026-02-11. The CLI WARNS "
            "(does not block) when --as-was-date is not in the list, so "
            "ad-hoc close-adjacent dates still work for one-off recons."
        ),
        "evidence": "core.py: KNOWN_FY_CLOSE_DATES tuple.",
        "tags": ["snapshot-date", "calendar"],
        "confidence": "high",
    },

    # ---- daily-reflection -----------------------------------------------
    {
        "role": "daily-reflection",
        "category": "best_practice",
        "lesson": (
            "Runs at most once per UTC day (guarded by reflected_today()). "
            "Scans runs/thinking/*.md for the last look_back_days (default 1) "
            "and bucket-extracts FAIL -> failure, WARN -> edge_case, "
            "NEEDS_INPUT -> ambiguity lessons. Dedupes via stable hash of "
            "(role, lesson) so re-runs bump occurrence_count. Cross threshold "
            ">= 3 -> auto-promote to _stable.jsonl. Force with --reflect."
        ),
        "evidence": "subagents/daily_reflection.py + lessons.PROMOTE_AT_OCCURRENCE.",
        "tags": ["reflection", "cadence", "promotion"],
        "confidence": "high",
    },

    # ---- Portability seam (cross-cutting) -------------------------------
    {
        "role": GLOBAL_ROLE,
        "category": "best_practice",
        "lesson": (
            "ARRCloseOrchestrator accepts a `runner` callable "
            "(argv, cwd) -> CompletedProcess. Substituting the runner is the "
            "entire portability story: Local CLI uses default_runner "
            "(subprocess), Cursor SDK wraps a dbt MCP call, dbt Cloud / SANA "
            "wraps POST /jobs/.../run/, tests pass a lambda returning canned "
            "CompletedProcess. Never bypass this seam."
        ),
        "evidence": "README.md '## Why the seam' + core.ARRCloseOrchestrator.",
        "tags": ["portability", "seam", "runtime"],
        "confidence": "high",
    },
]


def seed(project_dir: Path = Path(".")) -> int:
    recorder = get_recorder(project_dir)
    n = 0
    for item in SELF_LESSONS:
        if recorder.record(**item) is not None:
            n += 1
    print(f"Seeded {n} self-knowledge lessons "
          "(re-running bumps occurrence_count for existing entries).")
    return n


if __name__ == "__main__":
    import sys
    sys.exit(0 if seed(Path(".")) >= 0 else 1)
