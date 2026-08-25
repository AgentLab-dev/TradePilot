"""Typed in/out contracts for every sub-agent under the Finance ARR Quarter Close (FQC-ARR) supervisor.

Every sub-agent module under ``agents.arr_quarter_close.subagents`` consumes
one of these inputs and returns one of these outputs. The supervisor parses
the outputs to decide what to do next - it never reads sub-agent free-form
text. This keeps the topology composable across runtimes (Cursor SDK, SANA,
plain Python, pytest mocks).

Design rules:

* Every dataclass is JSON-serializable via ``asdict`` (no Path / datetime in
  the public field set - convert to str at the boundary).
* Every output carries a ``status`` ('ok' / 'needs_input' / 'warn' / 'fail').
* Every output carries an ``artifacts`` mapping for files the supervisor
  should hand to later sub-agents (e.g. test reports -> qa handoff).
* Inputs carry the supervisor's authorization mode so each sub-agent knows
  whether it may write (Jira post, gh push, Slack post) or must stop at a
  pause point.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Default LLM model for the supervisor + LLM-driven sub-agents.
#
# The supervisor itself runs no LLM; this is the model the *callers* of the
# LLM-driven leaf sub-agents (``requirements_analyzer``, ``clarifier``,
# ``implementer``) and the Cursor SDK runner (``cursor_runner.py``) should
# default to. Sub-agents emit ``preferred_model`` on their ``RoleResult`` so
# the caller (Cursor chat, Cursor SDK, SANA) routes the emitted prompt to
# the right model.
#
# Override precedence (highest first):
#   1. Explicit field on the call site (e.g. ``SupervisorInput.llm_model`` /
#      ``CursorRunOptions.model`` / CLI ``--model``).
#   2. Environment variable ``FQC_ARR_DEFAULT_MODEL``.
#   3. This constant.
#
# Allowed slugs (subset that has thinking + Workday allowlist):
#   * ``claude-opus-4-7-thinking-xhigh``  (default - "Opus 4.7 Extra High")
#   * ``claude-opus-4-8-thinking-high``   ("Opus 4.8 High")
#   * ``claude-4.6-opus-high-thinking``   (prior generation)
#   * ``gpt-5.5-medium`` / ``gpt-5.3-codex``
#   * ``gemini-3.1-pro``
# ---------------------------------------------------------------------------

DEFAULT_LLM_MODEL: str = "claude-opus-4-7-thinking-xhigh"
DEFAULT_LLM_MODEL_ENV: str = "FQC_ARR_DEFAULT_MODEL"


def resolve_default_llm_model() -> str:
    """Return the model the LLM-driven sub-agents should advertise.

    Checks ``$FQC_ARR_DEFAULT_MODEL`` first; falls back to the
    ``DEFAULT_LLM_MODEL`` constant.
    """
    override = os.environ.get(DEFAULT_LLM_MODEL_ENV, "").strip()
    return override or DEFAULT_LLM_MODEL


class AuthMode(str, Enum):
    """How aggressive the supervisor may be about side-effecting actions."""

    FULL_AUTO = "full_auto"
    SMART_GATES = "smart_gates"   # default - pause before Jira/PR/Slack/QA writes
    GATED_MINIMAL = "gated_minimal"
    GATED_FULL = "gated_full"


class RoleStatus(str, Enum):
    OK = "ok"
    NEEDS_INPUT = "needs_input"   # supervisor must surface a question / pause
    WARN = "warn"
    FAIL = "fail"
    SKIPPED = "skipped"


@dataclass
class RoleResult:
    """Base shape for every sub-agent output."""

    role: str
    status: RoleStatus
    summary: str
    payload: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)   # name -> path
    pause_reason: Optional[str] = None
    # Model the caller should route any emitted ``prompt`` to. Set by
    # LLM-driven sub-agents (requirements_analyzer, clarifier, implementer)
    # via ``resolve_default_llm_model()``. ``None`` for sub-agents that do
    # not emit an LLM prompt.
    preferred_model: Optional[str] = None

    def as_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d


# ---------------------------------------------------------------------------
# 1. jira-intake
# ---------------------------------------------------------------------------

@dataclass
class TicketInput:
    ticket_key: str                          # e.g. EDAEM-3725
    base_url: Optional[str] = None           # falls back to JIRA_BASE_URL
    include_comments: bool = True
    include_changelog: bool = False


@dataclass
class TicketSpec:
    ticket_key: str
    summary: str
    status: str
    assignee: Optional[str]
    reporter: Optional[str]
    issue_type: str = "Story"                # Bug / Story / Task / Sub-task / Epic
    labels: list[str] = field(default_factory=list)
    components: list[str] = field(default_factory=list)
    description_text: str = ""               # ADF flattened to plain text
    acceptance_criteria: list[str] = field(default_factory=list)
    comments: list[dict] = field(default_factory=list)
    raw_url: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# 2. requirements-analyzer
# ---------------------------------------------------------------------------

@dataclass
class RequirementsInput:
    ticket: TicketSpec


@dataclass
class KPISpec:
    name: str
    business_definition: str
    formula: str
    grain: str
    periodicity: str
    currency_basis: str
    source_of_truth: str
    validation_rule: str
    open_questions: list[str] = field(default_factory=list)


@dataclass
class RequirementsSpec:
    ticket_key: str
    scope_summary: str
    in_scope_models: list[str] = field(default_factory=list)
    out_of_scope: list[str] = field(default_factory=list)
    kpis: list[KPISpec] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)  # surface to clarifier
    confidence: str = "medium"                          # high / medium / low

    def as_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# 3. code-data-validator
# ---------------------------------------------------------------------------

@dataclass
class ValidationInput:
    requirements: RequirementsSpec
    project_dir: str
    snowflake_target_db: str = "finance_dev"
    baseline_db: str = "finance_prod"
    source_db: str = "base_prod.salesforce"


@dataclass
class CodeFindings:
    affected_models: list[str] = field(default_factory=list)
    affected_macros: list[str] = field(default_factory=list)
    grain_check_notes: str = ""
    layering_notes: str = ""


@dataclass
class DataFindings:
    queries_run: list[str] = field(default_factory=list)
    metric_baselines: dict[str, str] = field(default_factory=dict)
    anomalies: list[str] = field(default_factory=list)


# --- shared 7-column comparison matrix ---------------------------------------

@dataclass
class ValidationCheck:
    """One row of the canonical FQC-ARR validation matrix.

    Columns map 1:1 to the operator's mental model:

      check_name           - human-friendly label ("ARR @ latest snapshot")
      grain                - e.g. "as_was_date, fiscal_quarter_name"
      source_salesforce    - raw Salesforce value (base_prod.salesforce.*)
      baseline_prod        - current production value (finance_prod) - pre-change
      target_dev_qa        - new value in finance_dev or finance_qa - post-change
      expected             - what business logic / AC says the value should be
      actual               - measured value (usually equals target_dev_qa)
      business_logic       - one-line formula or rule being tested
      verdict              - pass / fail / warn / needs_review / pending

    Any value cell may stay empty (``""``) when not applicable (e.g. a
    structural test has no Salesforce source). The ``sql_template`` field
    records the auditable SQL that produced the row.
    """

    check_name: str
    grain: str = ""
    source_salesforce: str = ""
    baseline_prod: str = ""
    target_dev_qa: str = ""
    expected: str = ""
    actual: str = ""
    business_logic: str = ""
    verdict: str = "pending"           # pass / fail / warn / needs_review / pending
    variance_abs: Optional[float] = None
    variance_pct: Optional[float] = None
    notes: str = ""
    sql_template: str = ""             # CTE-based SQL that yields the row


@dataclass
class ValidationMatrix:
    """Collection of ValidationCheck rows + a rollup verdict.

    Travels with every validation-producing sub-agent
    (code-data-validator, test-runner, ci-monitor, cd-monitor) and is
    rendered as an ADF table by qa-handoff and as a Markdown table by
    the thinking log.

    ``overall_verdict`` is auto-derived from ``checks`` at construction
    time (via ``__post_init__``) so it round-trips through ``asdict()``
    and survives JSON serialization in ``RoleResult.payload``. Call
    ``recompute_verdict()`` if checks are mutated after construction.
    """

    matrix_name: str                   # e.g. "code-data-validator pre-flight"
    target_db: str                     # finance_dev / finance_qa / finance_prod
    baseline_db: str = "finance_prod"
    source_db: str = "base_prod.salesforce"
    checks: list[ValidationCheck] = field(default_factory=list)
    overall_verdict: str = "pending"   # derived; do not set by hand

    def __post_init__(self) -> None:
        self.recompute_verdict()

    def recompute_verdict(self) -> str:
        verdicts = [c.verdict for c in self.checks]
        if not verdicts:
            self.overall_verdict = "pending"
        elif "fail" in verdicts:
            self.overall_verdict = "fail"
        elif "needs_review" in verdicts:
            self.overall_verdict = "needs_review"
        elif "warn" in verdicts:
            self.overall_verdict = "warn"
        elif all(v == "pass" for v in verdicts):
            self.overall_verdict = "pass"
        else:
            self.overall_verdict = "pending"
        return self.overall_verdict

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class ValidationReport:
    ticket_key: str
    code: CodeFindings
    data: DataFindings
    risks: list[str] = field(default_factory=list)
    proposed_changes: list[str] = field(default_factory=list)
    validation_matrix: Optional[ValidationMatrix] = None

    def as_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# 4. clarifier
# ---------------------------------------------------------------------------

@dataclass
class ClarificationInput:
    ticket: TicketSpec
    requirements: RequirementsSpec
    validation: ValidationReport
    auth_mode: AuthMode = AuthMode.SMART_GATES


@dataclass
class ClarificationRequest:
    ticket_key: str
    question_block_markdown: str             # human-readable preview
    adf_payload: dict                        # ready for Jira POST
    posted: bool = False
    comment_id: Optional[str] = None

    def as_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# 5. implementer
# ---------------------------------------------------------------------------

@dataclass
class ImplementationInput:
    requirements: RequirementsSpec
    validation: ValidationReport
    project_dir: str
    branch_prefix: str = "feature"


@dataclass
class FileEdit:
    path: str
    summary: str                              # one-line "what changed"


@dataclass
class ImplementationResult:
    ticket_key: str
    branch_name: str
    edits: list[FileEdit] = field(default_factory=list)
    needs_snapshot_rebuild: bool = False     # signal supervisor to re-enter Mode A

    def as_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# 6. test-runner
# ---------------------------------------------------------------------------

@dataclass
class TestInput:
    project_dir: str
    pytest_paths: list[str] = field(default_factory=lambda: ["tests"])
    dbt_test_selectors: list[str] = field(
        default_factory=lambda: [
            "test_arr_waterfall_balance",
            "tag:ia_migration",
        ]
    )
    as_was_date: Optional[str] = None


@dataclass
class TestReport:
    ticket_key: str
    pytest_passed: int = 0
    pytest_failed: int = 0
    pytest_skipped: int = 0
    dbt_test_results: list[dict] = field(default_factory=list)
    junit_xml_path: Optional[str] = None
    dbt_target_path: Optional[str] = None
    overall_passed: bool = False
    validation_matrix: Optional[ValidationMatrix] = None

    def as_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# 7. pr-author
# ---------------------------------------------------------------------------

@dataclass
class PRInput:
    ticket: TicketSpec
    implementation: ImplementationResult
    test_report: TestReport
    base_branch: str = "qa"                  # eda-dbt-em flow: feature -> qa -> prod
    draft: bool = False
    auth_mode: AuthMode = AuthMode.SMART_GATES


@dataclass
class PRResult:
    ticket_key: str
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    branch_name: str = ""
    reviewers: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)
    posted: bool = False

    def as_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# 8. ci-monitor
# ---------------------------------------------------------------------------

@dataclass
class CIInput:
    pr_url: str
    pr_number: int
    slack_channel: str                        # e.g. "<YOUR_SLACK_USER_ID>" or "C0123"
    poll_minutes: int = 10
    max_hours: float = 4.0
    check_name_pattern: str = "ci/dbt_cloud"
    validation_db: str = "finance_dev"
    validation_sql_paths: list[str] = field(default_factory=list)


@dataclass
class CIReport:
    ticket_key: str
    pr_number: int
    final_state: str                          # pass / fail / timeout
    polls_sent: int = 0
    last_status_url: Optional[str] = None
    finance_dev_validation_passed: Optional[bool] = None
    validation_notes: list[str] = field(default_factory=list)
    validation_matrix: Optional[ValidationMatrix] = None

    def as_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# 9. cd-monitor
# ---------------------------------------------------------------------------

@dataclass
class CDInput:
    dbt_cloud_run_id: Optional[int]           # if known; otherwise wait for trigger
    pr_url: str
    slack_channel: str
    poll_minutes: int = 10
    max_hours: float = 4.0
    validation_db: str = "finance_qa"
    validation_sql_paths: list[str] = field(default_factory=list)


@dataclass
class CDReport:
    ticket_key: str
    final_state: str                          # success / error / timeout
    run_id: Optional[int] = None
    finance_qa_validation_passed: Optional[bool] = None
    validation_notes: list[str] = field(default_factory=list)
    validation_matrix: Optional[ValidationMatrix] = None

    def as_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# 10. qa-handoff
# ---------------------------------------------------------------------------

@dataclass
class QAHandoffInput:
    ticket: TicketSpec
    test_report: TestReport
    ci_report: CIReport
    cd_report: CDReport
    qa_ticket_key: Optional[str] = None       # may be the same ticket
    auth_mode: AuthMode = AuthMode.SMART_GATES


@dataclass
class QAHandoffResult:
    ticket_key: str
    qa_ticket_key: str
    description_updated: bool = False
    comment_posted: bool = False
    transitions_applied: list[str] = field(default_factory=list)
    attached_artifacts: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# 11. debugger (on-demand sub-agent dispatched on failure / by side-channel)
# ---------------------------------------------------------------------------

@dataclass
class DebugInput:
    """Input contract for the on-demand debugger sub-agent.

    Dispatched in three ways:

    1. Auto on FAIL - supervisor sees ``RoleResult.status == FAIL`` from
       any role and dispatches the debugger before pausing.
    2. Side-channel - operator posts ``task: debug [model]`` in the Slack
       thread; supervisor maps it through ``_process_side_task``.
    3. CLI - ``--debug-model <model>`` runs the debugger standalone.

    Carries the failing role's payload (when triggered by failure) so the
    debugger can lift its lineage / matrix without re-deriving them.
    """

    ticket: TicketSpec
    project_dir: str
    target_model: str                          # e.g. "arr_line_categories"
    trigger: str = "manual"                    # "auto_failure" / "side_channel" / "manual" / "cli"
    failing_role: Optional[str] = None         # name of the role that failed (if any)
    failing_payload: dict = field(default_factory=dict)
    snowflake_target_db: str = "finance_dev"
    baseline_db: str = "finance_prod"
    source_db: str = "base_prod.salesforce"
    auth_mode: AuthMode = AuthMode.SMART_GATES


@dataclass
class LineageNode:
    """One node in the upstream lineage of the target model.

    ``depth`` = 0 for the target model itself; depth=1 is its immediate
    parents; etc. ``layer`` is the dbt layer the node belongs to (staging /
    intermediate / mart / source) and is the right level to insert a stage
    validation check.
    """

    name: str
    depth: int
    layer: str = "unknown"                     # staging / intermediate / mart / source / unknown
    file_path: str = ""                        # repo-relative path if found
    refs: list[str] = field(default_factory=list)  # immediate parents


@dataclass
class RootCauseHypothesis:
    """A single hypothesis for what caused the failure / discrepancy.

    The debugger emits a ranked list (top hypothesis first). Confidence
    is a string bucket (high/medium/low) - we deliberately avoid fake
    probabilities. The ``evidence`` list cites the lineage nodes /
    matrix rows / repo files that support the hypothesis.
    """

    title: str
    confidence: str = "medium"                 # high / medium / low
    evidence: list[str] = field(default_factory=list)
    suggested_action: str = ""


@dataclass
class ProposedFix:
    """A concrete fix recommendation the implementer or coding agent can apply.

    ``file_path`` + ``before_snippet`` + ``after_snippet`` form an
    additive, reviewable hint; the debugger NEVER writes the change
    itself. ``llm_prompt`` is the prompt the IDE coding agent receives
    if the operator delegates the edit.
    """

    file_path: str
    summary: str
    before_snippet: str = ""
    after_snippet: str = ""
    llm_prompt: str = ""
    confidence: str = "medium"


@dataclass
class PytestHarnessSpec:
    """The pytest harness + dbt singular test the debugger generates to validate the fix.

    Two artifacts:

    * ``dbt_test_sql_path`` - dbt singular test that asserts the expected
      condition against Snowflake (via dbt - never opens a connection).
    * ``pytest_path`` - thin Python wrapper that shells out to
      ``dbt test --select <singular>`` and asserts returncode == 0.

    Both are written to disk during ``run()`` so the operator can run
    them locally with ``pytest tests/pytest/<file>.py -k <node>``.
    """

    dbt_test_sql_path: str
    dbt_test_sql_body: str
    pytest_path: str
    pytest_body: str
    selector: str                              # the dbt --select for the new test
    written_to_disk: bool = False


@dataclass
class ACAnalysis:
    """One acceptance-criterion mapped to actual debugger findings.

    ``actual`` and ``verdict`` are populated when the debugger has enough
    evidence (matrix rows, test results) to judge; otherwise stay empty /
    "needs_review" and surface as a question for the operator.
    """

    criterion: str
    expected: str = ""
    actual: str = ""
    verdict: str = "needs_review"              # met / not_met / needs_review
    evidence: list[str] = field(default_factory=list)


@dataclass
class DebugReport:
    """Top-level output of the debugger sub-agent."""

    ticket_key: str
    issue_type: str                            # echoed from TicketSpec for routing
    target_model: str
    trigger: str
    lineage: list[LineageNode] = field(default_factory=list)
    stage_matrix: Optional[ValidationMatrix] = None
    ac_analysis: list[ACAnalysis] = field(default_factory=list)
    hypotheses: list[RootCauseHypothesis] = field(default_factory=list)
    proposed_fix: Optional[ProposedFix] = None
    pytest_harness: Optional[PytestHarnessSpec] = None
    jira_update_adf: Optional[dict] = None     # ADF doc tailored to issue_type
    jira_comment_posted: bool = False
    jira_comment_id: Optional[str] = None

    def as_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# 12. quarter-close-runner (on-demand: dbt pipeline + ARR recon validation)
# ---------------------------------------------------------------------------

@dataclass
class QuarterCloseInput:
    """Input contract for the quarter-close-runner sub-agent.

    Drives two things in one call:

    1. **Pipeline execution** - delegates to ``ARRCloseOrchestrator`` for
       the standard ARR run order (tmp_tbls -> arr_line_categories ->
       rollups -> arr_account_product_corp_report -> tests). Skip with
       ``run_pipeline=False`` if you only want the recon against an
       already-loaded snapshot.
    2. **Recon validation** - executes a richer set of ARR-quarter-close
       tie-out checks beyond the default ``test_arr_waterfall_balance``:
       waterfall category balance, period-over-period totals, row count
       parity vs prior snapshot, currency-variant cross-check, account
       continuity vs prior quarter.

    The result is a ``QuarterCloseReport`` carrying the ``CloseResult``
    plus a ``ValidationMatrix`` of recon checks (same 7-col shape used
    elsewhere). ``tolerance_pct`` is the variance threshold below which
    a check passes (default 1%); between 1% and 5% -> warn; above ->
    fail.
    """

    project_dir: str
    as_was_date: str                              # current snapshot (e.g. 2026-02-11)
    baseline_as_was_date: Optional[str] = None    # prior snapshot for period-over-period
    target_db: str = "certified_dev"              # where the dbt run writes
    baseline_db: str = "finance_prod"             # what we tie out against
    source_db: str = "base_prod.salesforce"
    run_pipeline: bool = True
    refresh_dashboards: bool = False
    include_ia_migration_tests: bool = True
    tolerance_pct: float = 1.0                    # < tol = pass, < 5x tol = warn
    auth_mode: AuthMode = AuthMode.SMART_GATES


@dataclass
class QuarterCloseReport:
    """Top-level output of the quarter-close-runner sub-agent."""

    as_was_date: str
    baseline_as_was_date: Optional[str]
    target_db: str
    baseline_db: str
    pipeline_executed: bool = False
    pipeline_overall_status: str = "skipped"      # success / warn / fail / skipped
    pipeline_steps: list[dict] = field(default_factory=list)
    pipeline_duration_s: float = 0.0
    recon_matrix: Optional[ValidationMatrix] = None
    overall_verdict: str = "pending"
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# 13. daily-reflection (on-demand: scan today's runs, extract new lessons)
# ---------------------------------------------------------------------------

@dataclass
class ReflectionInput:
    """Input for the daily-reflection sub-agent.

    Reads today's thinking logs + any role payloads accumulated in this
    run, asks the operator (or LLM) to extract structured lessons, and
    writes them through ``LessonRecorder``. Runs at most once per UTC
    day under the auto-trigger path; ``--reflect`` forces a fresh pass.
    """

    project_dir: str
    look_back_days: int = 1                  # default: today's runs only
    force: bool = False                      # ignore "already reflected today"
    wide_scan: bool = False                  # also scan runs/*.log for novel Traceback patterns
    auth_mode: AuthMode = AuthMode.SMART_GATES


@dataclass
class ReflectionReport:
    """Top-level output of the daily-reflection sub-agent."""

    lessons_added: int = 0
    lessons_promoted: int = 0
    lessons_archived: int = 0
    runs_scanned: int = 0
    log_paths_scanned: list[str] = field(default_factory=list)
    notes: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Side-channel intake (Slack `task:` messages picked up between roles)
# ---------------------------------------------------------------------------

@dataclass
class SideTask:
    """One Slack thread message that started with the ``task:`` prefix.

    The supervisor records the request, the action it dispatched to (one of
    the first-class commands or ``queued`` for free-form), and the short
    result string posted back to the Slack thread for auditability.
    """

    ts: str                                   # Slack message ts (sort key)
    requester: str                            # Slack user id, may be ""
    text: str                                 # everything after "task:"
    action: str = "queued"                    # skip / pause / cancel / status / queued
    result: str = ""                          # human summary echoed back to thread


# ---------------------------------------------------------------------------
# Supervisor envelope
# ---------------------------------------------------------------------------

@dataclass
class SupervisorRunReport:
    ticket_key: Optional[str]
    mode: str                                 # "scheduled" / "ticket" / "both"
    overall_status: RoleStatus
    role_results: list[RoleResult] = field(default_factory=list)
    pause_points: list[dict] = field(default_factory=list)
    side_tasks: list[SideTask] = field(default_factory=list)
    elapsed_s: float = 0.0

    def as_dict(self) -> dict:
        d = asdict(self)
        d["overall_status"] = self.overall_status.value
        d["role_results"] = [r.as_dict() if hasattr(r, "as_dict") else r for r in self.role_results]
        return d
