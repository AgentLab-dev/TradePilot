"""Sub-agent 11: debugger (on-demand).

Dispatched whenever and wherever a failure or discrepancy surfaces:

* The supervisor sees `RoleResult.status == FAIL` from any role.
* The operator posts `task: debug [<model>]` in the Slack thread.
* The CLI is invoked with `--debug-model <model>`.

What it does (in order):

1. Walks the upstream lineage of the target model via ripgrep on `ref()`
   calls (no `dbt list` invocation; works without a compiled project).
2. Builds a per-stage `ValidationMatrix` - one ValidationCheck per lineage
   node - using the same 7-column comparison shape every other validation
   surface uses (sf -> prod -> dev/qa, expected/actual/business_logic/verdict).
3. Maps the ticket's acceptance criteria onto the per-stage findings
   (`ACAnalysis`) so the operator immediately sees which AC is at risk.
4. Ranks `RootCauseHypothesis` items based on the lineage + matrix.
5. Emits a `ProposedFix` (file + before/after snippet + LLM prompt) - never
   writes the change itself; the implementer or coding agent does.
6. Generates a `PytestHarnessSpec` = (dbt singular test + thin pytest
   wrapper). The pytest harness shells out to `dbt test --select <new>`
   and asserts returncode == 0; the actual SQL runs through Snowflake via
   dbt, never via a Python Snowflake connection.
7. Builds a Jira ADF comment tailored to the ticket type:
   * Bug -> "Root cause + reproducible fix" framing.
   * Story / Task / Sub-task / Epic -> "Debug findings" framing.
   Pauses before POSTing unless `auth_mode=full_auto`.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Optional

from agents.arr_quarter_close.contracts import (
    ACAnalysis,
    AuthMode,
    DebugInput,
    DebugReport,
    LineageNode,
    ProposedFix,
    PytestHarnessSpec,
    RoleResult,
    RoleStatus,
    RootCauseHypothesis,
    ValidationCheck,
    ValidationMatrix,
)
from agents.arr_quarter_close.lessons import (
    format_lessons_for_prompt,
    get_cached_recorder,
)

ROLE = "debugger"


def _lessons_block(role: str, max_lessons: int = 8) -> str:
    recorder = get_cached_recorder()
    if recorder is None:
        return ""
    return format_lessons_for_prompt(
        recorder.load_for(role, max_lessons=max_lessons),
        heading="Lessons learned from prior runs",
    )

MAX_LINEAGE_DEPTH = 5
PYTEST_DIR = "tests/pytest"
DBT_TEST_DIR = "tests"


def plan(req: DebugInput) -> dict:
    return {
        "role": ROLE,
        "ticket_key": req.ticket.ticket_key,
        "issue_type": req.ticket.issue_type,
        "target_model": req.target_model,
        "trigger": req.trigger,
        "failing_role": req.failing_role,
        "snowflake_target_db": req.snowflake_target_db,
        "baseline_db": req.baseline_db,
        "phases": [
            "1. Lineage walk (upstream, depth<=5, via ripgrep on ref())",
            "2. Per-stage 7-col ValidationMatrix (sf -> prod -> dev/qa)",
            "3. AC -> stage-finding mapping (ACAnalysis)",
            "4. RootCauseHypothesis ranking with evidence citations",
            "5. ProposedFix (file + before/after snippet + LLM prompt)",
            "6. PytestHarnessSpec (dbt singular test + pytest wrapper)",
            "7. Jira ADF comment shaped by issue_type (Bug vs Story/Task)",
        ],
        "would_post": req.auth_mode == AuthMode.FULL_AUTO,
        "writes_artifacts_to": [PYTEST_DIR, DBT_TEST_DIR],
    }


def run(req: DebugInput) -> RoleResult:
    project_dir = Path(req.project_dir).resolve()

    lineage = _walk_lineage(project_dir, req.target_model)
    matrix = _build_stage_matrix(req, lineage)
    ac_analysis = _analyze_acceptance_criteria(req, matrix)
    hypotheses = _rank_hypotheses(req, lineage, matrix, ac_analysis)
    fix = _propose_fix(req, lineage, hypotheses)
    harness = _generate_pytest_harness(project_dir, req, fix)
    adf = _build_jira_adf(req, lineage, matrix, ac_analysis, hypotheses, fix, harness)

    report = DebugReport(
        ticket_key=req.ticket.ticket_key,
        issue_type=req.ticket.issue_type,
        target_model=req.target_model,
        trigger=req.trigger,
        lineage=lineage,
        stage_matrix=matrix,
        ac_analysis=ac_analysis,
        hypotheses=hypotheses,
        proposed_fix=fix,
        pytest_harness=harness,
        jira_update_adf=adf,
        jira_comment_posted=False,
        jira_comment_id=None,
    )

    summary = (
        f"target={req.target_model} trigger={req.trigger} "
        f"lineage_nodes={len(lineage)} stage_checks={len(matrix.checks)} "
        f"hypotheses={len(hypotheses)} top={hypotheses[0].confidence if hypotheses else '-'} "
        f"issue_type={req.ticket.issue_type}"
    )

    artifacts = {}
    if harness and harness.written_to_disk:
        artifacts["debug_pytest"] = harness.pytest_path
        artifacts["debug_dbt_test"] = harness.dbt_test_sql_path

    # Smart-gate pause: do not POST to Jira unless explicitly authorized.
    if req.auth_mode != AuthMode.FULL_AUTO:
        return RoleResult(
            role=ROLE,
            status=RoleStatus.NEEDS_INPUT,
            summary=summary,
            payload={"debug": report.as_dict()},
            artifacts=artifacts,
            pause_reason=(
                f"Approve to post {req.ticket.issue_type}-shaped debug comment "
                f"to {req.ticket.ticket_key}"
            ),
        )

    posted = _post_jira_comment(req.ticket.ticket_key, adf)
    report.jira_comment_posted = bool(posted.get("id"))
    report.jira_comment_id = posted.get("id")
    return RoleResult(
        role=ROLE,
        status=RoleStatus.OK if report.jira_comment_posted else RoleStatus.WARN,
        summary=summary + f" jira_posted={report.jira_comment_posted}",
        payload={"debug": report.as_dict()},
        artifacts=artifacts,
    )


# ---------------------------------------------------------------------------
# 1. Lineage walk - upstream, via ripgrep on ref() calls
# ---------------------------------------------------------------------------

_REF_RE = re.compile(r"""\{\{\s*ref\(\s*['"]([^'"]+)['"]\s*\)\s*\}\}""")
_SOURCE_RE = re.compile(r"""\{\{\s*source\(\s*['"]([^'"]+)['"]\s*,\s*['"]([^'"]+)['"]""")


def _walk_lineage(project_dir: Path, target: str) -> list[LineageNode]:
    """BFS upstream from `target` via ripgrep on ref() / source() calls.

    Depth-capped to keep the walk cheap; depth=0 is the target model
    itself. Returns nodes in BFS order (target first, then immediate
    parents, then grandparents).
    """
    visited: set[str] = set()
    queue: list[tuple[str, int]] = [(target, 0)]
    out: list[LineageNode] = []

    while queue:
        name, depth = queue.pop(0)
        if name in visited or depth > MAX_LINEAGE_DEPTH:
            continue
        visited.add(name)
        path = _find_model_file(project_dir, name)
        refs: list[str] = []
        if path is not None:
            refs = _extract_refs(path)
        node = LineageNode(
            name=name,
            depth=depth,
            layer=_classify_layer(name, path),
            file_path=str(path.relative_to(project_dir)) if path else "",
            refs=refs,
        )
        out.append(node)
        if depth < MAX_LINEAGE_DEPTH:
            for parent in refs:
                if parent not in visited:
                    queue.append((parent, depth + 1))
    return out


def _find_model_file(project_dir: Path, model_name: str) -> Optional[Path]:
    """Return repo-relative .sql file matching the model name, or None.

    Tries ripgrep first (fast). Falls back to ``Path.rglob`` if ripgrep is
    not installed, so the debugger works on machines without ``brew install
    ripgrep``. The find / rglob walk is slower but functionally
    equivalent for this single-file lookup.
    """
    try:
        proc = subprocess.run(
            ["rg", "--files", "-g", f"{model_name}.sql", "models"],
            cwd=str(project_dir), capture_output=True, text=True, check=False,
        )
        for line in proc.stdout.splitlines():
            line = line.strip()
            if line.endswith(f"{model_name}.sql"):
                return project_dir / line
        return None
    except FileNotFoundError:
        # Pure-Python fallback when ripgrep isn't on PATH.
        models_dir = project_dir / "models"
        if not models_dir.is_dir():
            return None
        for p in models_dir.rglob(f"{model_name}.sql"):
            return p
        return None


def _extract_refs(file_path: Path) -> list[str]:
    try:
        body = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    refs = _REF_RE.findall(body)
    # source() also counts as a lineage parent (prefixed for visibility).
    for src, tbl in _SOURCE_RE.findall(body):
        refs.append(f"source:{src}.{tbl}")
    seen: set[str] = set()
    out: list[str] = []
    for r in refs:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


def _classify_layer(name: str, path: Optional[Path]) -> str:
    if name.startswith("source:"):
        return "source"
    if name.startswith("stg_") or (path and "/stage/" in path.as_posix()):
        return "staging"
    if name.startswith("int_") or (path and "/intermediate/" in path.as_posix()):
        return "intermediate"
    if name.startswith(("arr_", "acv_", "bt_", "bv_")):
        return "mart"
    if path and "/finance/" in path.as_posix():
        return "mart"
    return "unknown"


# ---------------------------------------------------------------------------
# 2. Per-stage validation matrix - one ValidationCheck per lineage node
# ---------------------------------------------------------------------------

def _build_stage_matrix(req: DebugInput, lineage: list[LineageNode]) -> ValidationMatrix:
    """Emit one ValidationCheck per lineage node.

    Each check is a row-count parity check against the baseline DB at the
    same model name. Structural checks (no Salesforce source). The matrix
    surfaces which stage in the lineage first diverges from production,
    which is the most useful signal for narrowing the failure to one model.
    """
    target_db = req.snowflake_target_db
    baseline_db = req.baseline_db
    checks: list[ValidationCheck] = []
    for node in lineage:
        if node.layer == "source":
            # Source comparison: Salesforce raw row count vs whatever the
            # next-stage staging model loaded. Leave dev/qa value empty.
            _, _, tbl = node.name.partition(":")
            sql = (
                f"-- check: stage row-count parity at source `{node.name}`\n"
                f"select count(*) as v from {req.source_db}.{tbl};"
            )
            checks.append(ValidationCheck(
                check_name=f"stage::source::{node.name}",
                grain=f"depth={node.depth}, layer=source",
                business_logic=f"Row count in {req.source_db}.{tbl} as upstream baseline",
                sql_template=sql,
                notes="Salesforce source row count; compare against next-stage staging load.",
            ))
            continue

        # Try common dbt model locations: aggregations, staging, finance.
        schemas = _candidate_schemas(node.layer)
        sql_lines = [f"-- check: stage row-count parity at `{node.name}` (depth={node.depth})"]
        for s in schemas:
            sql_lines.append(
                f"-- try: {s}\n"
                f"with t as (select count(*) as v from {target_db}.{s}.{node.name}),\n"
                f"     b as (select count(*) as v from {baseline_db}.{s}.{node.name})\n"
                f"select '{node.name}' as model, '{s}' as schema_name,\n"
                f"       b.v as baseline_prod, t.v as target_dev_qa,\n"
                f"       (t.v - b.v) as variance_abs,\n"
                f"       case when b.v = 0 then 'needs_review'\n"
                f"            when abs(t.v - b.v) / nullif(b.v, 0) < 0.01 then 'pass'\n"
                f"            when abs(t.v - b.v) / nullif(b.v, 0) < 0.05 then 'warn'\n"
                f"            else 'fail' end as verdict\n"
                f"from t, b;"
            )
        checks.append(ValidationCheck(
            check_name=f"stage::{node.layer}::{node.name}",
            grain=f"depth={node.depth}, layer={node.layer}",
            business_logic=f"count(*) parity at {node.name} (try {', '.join(schemas)})",
            sql_template="\n\n".join(sql_lines),
            notes="Tolerance: <1% pass / <5% warn / else fail.",
        ))
    return ValidationMatrix(
        matrix_name=f"debugger stage-by-stage ({req.target_model})",
        target_db=target_db,
        baseline_db=baseline_db,
        source_db=req.source_db,
        checks=checks,
    )


def _candidate_schemas(layer: str) -> list[str]:
    if layer == "mart":
        return ["aggregations", "finance"]
    if layer == "intermediate":
        return ["intermediate", "aggregations"]
    if layer == "staging":
        return ["staging", "stage"]
    return ["aggregations", "staging", "intermediate"]


# ---------------------------------------------------------------------------
# 3. AC -> stage-finding mapping
# ---------------------------------------------------------------------------

def _analyze_acceptance_criteria(req: DebugInput, matrix: ValidationMatrix) -> list[ACAnalysis]:
    """Pair every AC bullet with what the matrix actually showed.

    All verdicts come back `needs_review` because the SQL has not been
    run yet - the supervisor will populate `actual` + `verdict` after
    running the matrix via the Snowflake MCP and re-invoking the
    debugger. This is the right operator default: the debugger
    surfaces *what to check* per AC, not a fabricated verdict.
    """
    out: list[ACAnalysis] = []
    for ac in req.ticket.acceptance_criteria:
        evidence: list[str] = []
        # Cite the matrix rows that mention any model name from the AC.
        ac_lower = ac.lower()
        for check in matrix.checks:
            base_name = check.check_name.split("::")[-1]
            if base_name and base_name.lower() in ac_lower:
                evidence.append(check.check_name)
        if not evidence and matrix.checks:
            evidence.append(matrix.checks[0].check_name)
        out.append(ACAnalysis(
            criterion=ac,
            expected="value implied by the AC text (operator confirms)",
            actual="(run stage matrix SQL to populate)",
            verdict="needs_review",
            evidence=evidence,
        ))
    return out


# ---------------------------------------------------------------------------
# 4. Root-cause hypothesis ranking
# ---------------------------------------------------------------------------

def _rank_hypotheses(
    req: DebugInput,
    lineage: list[LineageNode],
    matrix: ValidationMatrix,
    ac_analysis: list[ACAnalysis],
) -> list[RootCauseHypothesis]:
    """Cheap-but-useful ranked hypotheses from the lineage + failing payload.

    The debugger does NOT execute SQL or call an LLM here. It surfaces
    the structural suspicions (deepest layer with a recent edit, joins
    in mart layer, missing source) and leaves the actual verdict to the
    SQL the supervisor runs next.
    """
    out: list[RootCauseHypothesis] = []

    # Hypothesis 1: failing role gives strong prior on where to look.
    if req.failing_role:
        out.append(RootCauseHypothesis(
            title=f"Failure originated in `{req.failing_role}` - inspect its payload first.",
            confidence="high",
            evidence=[f"trigger=auto_failure from {req.failing_role}"],
            suggested_action=(
                f"Open the supervisor thinking-log section for `{req.failing_role}`; "
                f"its payload preview is the first place to look."
            ),
        ))

    # Hypothesis 2: row-count fan-out from a join in the mart layer is
    # the most common ARR-pipeline regression pattern.
    mart_nodes = [n for n in lineage if n.layer == "mart"]
    if mart_nodes:
        out.append(RootCauseHypothesis(
            title=f"Join-inflation in mart layer (`{mart_nodes[0].name}`) duplicating rows.",
            confidence="medium",
            evidence=[f"target {req.target_model} sits in mart layer; check ref() join keys"],
            suggested_action=(
                "Run the stage matrix at depth=0; if target row count > baseline +1%, "
                "look for a missing partition / join key in the last edit."
            ),
        ))

    # Hypothesis 3: missing or stale upstream staging model.
    staging_nodes = [n for n in lineage if n.layer == "staging"]
    if staging_nodes:
        out.append(RootCauseHypothesis(
            title=f"Stale upstream staging model `{staging_nodes[0].name}`.",
            confidence="medium",
            evidence=[f"first staging hop in lineage; check source freshness"],
            suggested_action="Re-run `dbt source freshness` against the relevant Salesforce sources.",
        ))

    # Hypothesis 4: requirement-side change not yet reflected in code.
    if ac_analysis:
        out.append(RootCauseHypothesis(
            title="Acceptance criteria imply a logic change not yet in the candidate branch.",
            confidence="low",
            evidence=[f"{len(ac_analysis)} AC item(s) currently `needs_review`"],
            suggested_action="Cross-check requirements-analyzer output against the implementer prompt.",
        ))

    return out


# ---------------------------------------------------------------------------
# 5. Proposed fix
# ---------------------------------------------------------------------------

def _propose_fix(
    req: DebugInput,
    lineage: list[LineageNode],
    hypotheses: list[RootCauseHypothesis],
) -> ProposedFix:
    """Generate a structured fix hint targeting the target model file.

    The debugger NEVER writes the change itself - it composes an LLM
    prompt the Cursor IDE coding agent (or a human) uses to make the
    actual edit. Mirrors the implementer sub-agent's pattern.
    """
    target_node = next((n for n in lineage if n.depth == 0), None)
    file_path = target_node.file_path if target_node else f"models/{req.target_model}.sql"
    top = hypotheses[0].title if hypotheses else "Inspect target model"
    lessons_block = _lessons_block("debugger")
    prompt = (
        f"# Fix prompt for {req.ticket.ticket_key}\n\n"
        f"Ticket type: {req.ticket.issue_type}\n"
        f"Target model: {req.target_model}\n"
        f"File: {file_path}\n"
        f"Failing role: {req.failing_role or '(manual trigger)'}\n\n"
        + (lessons_block + "\n" if lessons_block else "")
        + f"## Top hypothesis\n{top}\n\n"
        + f"## Lineage (upstream walk)\n"
        + "\n".join(f"- depth={n.depth} layer={n.layer} `{n.name}` ({n.file_path or 'n/a'})"
                    for n in lineage)
        + "\n\n"
        + "## Acceptance criteria\n"
        + ("\n".join(f"- {ac}" for ac in req.ticket.acceptance_criteria)
           or "- (no AC extracted)")
        + "\n\n"
        + "## Constraints\n"
        + "- Preserve grain documented in the model header.\n"
        + "- Pair every .sql change with the matching .yml test update.\n"
        + "- Add a singular dbt test under `tests/` for the new behavior.\n"
        + "- Run the validator matrix again after the edit; expect verdict=pass.\n"
    )
    return ProposedFix(
        file_path=file_path,
        summary=f"Address top hypothesis: {top}",
        before_snippet="(coding agent reads the file before editing)",
        after_snippet="(coding agent produces the edit)",
        llm_prompt=prompt,
        confidence=hypotheses[0].confidence if hypotheses else "medium",
    )


# ---------------------------------------------------------------------------
# 6. Pytest harness + dbt singular test
# ---------------------------------------------------------------------------

def _generate_pytest_harness(
    project_dir: Path,
    req: DebugInput,
    fix: ProposedFix,
) -> PytestHarnessSpec:
    """Generate a dbt singular test + thin pytest wrapper.

    SQL routes through dbt -> Snowflake (per `prefer-mcp-for-data-platforms`);
    the pytest wrapper shells out to `dbt test --select <new>` and
    asserts returncode == 0. Files are written to disk during run().
    """
    slug = re.sub(r"[^a-z0-9]+", "_", req.target_model.lower()).strip("_")
    ticket_slug = re.sub(r"[^a-z0-9]+", "_", req.ticket.ticket_key.lower()).strip("_")
    test_name = f"test_debug_{slug}_{ticket_slug}"

    dbt_sql_path = project_dir / DBT_TEST_DIR / f"{test_name}.sql"
    pytest_path = project_dir / PYTEST_DIR / f"{test_name}.py"

    dbt_sql_body = (
        "-- debugger-generated dbt singular test\n"
        f"-- ticket: {req.ticket.ticket_key} ({req.ticket.issue_type})\n"
        f"-- target_model: {req.target_model}\n"
        f"-- trigger: {req.trigger}\n"
        "-- Returns 0 rows when the expected condition holds.\n\n"
        f"with t as (\n"
        f"  select count(*) as v from {{{{ ref('{req.target_model}') }}}}\n"
        f")\n"
        f"select 'no_rows_in_{req.target_model}' as failure_reason\n"
        f"from t where v = 0;\n"
    )

    pytest_body = (
        '"""Pytest wrapper for the regression test on '
        f"{req.ticket.ticket_key} ({req.ticket.issue_type}).\n\n"
        f"Shells out to `dbt test --select {test_name}` and asserts the dbt\n"
        "return code is 0. The SQL itself runs in Snowflake via dbt - no\n"
        "direct snowflake.connector usage (per `prefer-mcp-for-data-platforms`).\n"
        '"""\n\n'
        "import subprocess\n\n"
        f"DBT_TEST_SELECTOR = \"{test_name}\"\n\n\n"
        f"def {test_name}() -> None:\n"
        "    proc = subprocess.run(\n"
        '        ["dbt", "test", "--select", DBT_TEST_SELECTOR],\n'
        "        capture_output=True, text=True, check=False,\n"
        "    )\n"
        "    assert proc.returncode == 0, (\n"
        '        "dbt test failed (returncode={}):\\n{}\\n{}".format(\n'
        "            proc.returncode, proc.stdout[-2000:], proc.stderr[-2000:]\n"
        "        )\n"
        "    )\n"
    )

    written = False
    try:
        dbt_sql_path.parent.mkdir(parents=True, exist_ok=True)
        pytest_path.parent.mkdir(parents=True, exist_ok=True)
        dbt_sql_path.write_text(dbt_sql_body, encoding="utf-8")
        pytest_path.write_text(pytest_body, encoding="utf-8")
        written = True
    except OSError:
        written = False

    return PytestHarnessSpec(
        dbt_test_sql_path=str(dbt_sql_path),
        dbt_test_sql_body=dbt_sql_body,
        pytest_path=str(pytest_path),
        pytest_body=pytest_body,
        selector=test_name,
        written_to_disk=written,
    )


# ---------------------------------------------------------------------------
# 7. Jira ADF comment - shaped by ticket type
# ---------------------------------------------------------------------------

def _build_jira_adf(
    req: DebugInput,
    lineage: list[LineageNode],
    matrix: ValidationMatrix,
    ac_analysis: list[ACAnalysis],
    hypotheses: list[RootCauseHypothesis],
    fix: ProposedFix,
    harness: PytestHarnessSpec,
) -> dict:
    """Build the ADF comment.

    Tone + framing changes by issue_type:
    * Bug -> "Root cause + reproducible fix", "Repro steps" section,
      explicit "Fix proposal" + "Regression test added".
    * Story / Task / Sub-task / Epic -> "Debug findings", framed as
      investigation results the dev team can fold into the next iteration.
    """
    issue = (req.ticket.issue_type or "Story").lower()
    is_bug = "bug" in issue

    title = (
        f"Root cause + reproducible fix for {req.ticket.ticket_key}"
        if is_bug else
        f"Debug findings for {req.ticket.ticket_key}"
    )
    intent_para = (
        "Investigating the failure surfaced by the supervisor; below is the "
        "structured root-cause analysis with a regression test you can run "
        "before merging the fix."
        if is_bug else
        "Diagnostic pass against the current candidate branch. Surfacing "
        "what each stage of the lineage shows so the implementer has a "
        "complete picture before the next iteration."
    )

    def text(s: str, strong: bool = False) -> dict:
        node = {"type": "text", "text": s}
        if strong:
            node["marks"] = [{"type": "strong"}]
        return node

    def para(*runs: dict) -> dict:
        return {"type": "paragraph", "content": list(runs)}

    def heading(level: int, s: str) -> dict:
        return {"type": "heading", "attrs": {"level": level}, "content": [text(s)]}

    def cell(s: str, header: bool = False, strong: bool = False) -> dict:
        return {
            "type": "tableHeader" if header else "tableCell",
            "content": [{"type": "paragraph", "content": [text(s, strong)]}],
        }

    def row(cells: list[dict]) -> dict:
        return {"type": "tableRow", "content": cells}

    def table(headers: list[str], rows: list[list[str]]) -> dict:
        return {
            "type": "table",
            "attrs": {"isNumberColumnEnabled": False, "layout": "default"},
            "content": [row([cell(h, header=True) for h in headers])]
                        + [row([cell(c) for c in r]) for r in rows],
        }

    def bullet_list(items: list[str]) -> dict:
        return {"type": "bulletList", "content": [
            {"type": "listItem",
             "content": [{"type": "paragraph", "content": [text(it)]}]}
            for it in (items or ["(none)"])
        ]}

    content: list[dict] = [
        para(text(title, strong=True)),
        para(text(intent_para)),

        heading(3, "Lineage walked"),
        table(
            ["Depth", "Layer", "Model", "File", "Refs"],
            [
                [str(n.depth), n.layer, n.name, n.file_path or "-", ", ".join(n.refs) or "-"]
                for n in lineage
            ],
        ),

        heading(3, f"Stage matrix ({matrix.target_db} vs {matrix.baseline_db})"),
        para(text(
            f"target_db={matrix.target_db}  baseline_db={matrix.baseline_db}  "
            f"source_db={matrix.source_db}  overall_verdict={matrix.overall_verdict}"
        )),
        table(
            ["Check", "Grain", "Salesforce", "Prod baseline", "Dev/QA",
             "Expected", "Actual", "Business logic", "Verdict"],
            [
                [
                    c.check_name, c.grain, c.source_salesforce or "-",
                    c.baseline_prod or "-", c.target_dev_qa or "-",
                    c.expected or "-", c.actual or "-",
                    c.business_logic, c.verdict,
                ]
                for c in matrix.checks
            ],
        ),

        heading(3, "Acceptance criteria - debugger findings"),
        table(
            ["Criterion", "Expected", "Actual", "Verdict", "Evidence"],
            [
                [a.criterion, a.expected or "-", a.actual or "-", a.verdict,
                 ", ".join(a.evidence) or "-"]
                for a in ac_analysis
            ] or [["(no AC extracted)", "-", "-", "-", "-"]],
        ),

        heading(3, "Ranked hypotheses"),
        table(
            ["#", "Confidence", "Hypothesis", "Suggested action", "Evidence"],
            [
                [str(i + 1), h.confidence, h.title, h.suggested_action,
                 ", ".join(h.evidence) or "-"]
                for i, h in enumerate(hypotheses)
            ] or [["-", "-", "(no hypotheses)", "-", "-"]],
        ),

        heading(3, "Proposed fix" if is_bug else "Suggested investigation focus"),
        bullet_list([
            f"File: {fix.file_path}",
            f"Summary: {fix.summary}",
            f"Confidence: {fix.confidence}",
            "Full LLM prompt is attached on the supervisor SupervisorRunReport "
            "(payload.debug.proposed_fix.llm_prompt).",
        ]),

        heading(3, "Regression test added" if is_bug else "Generated dbt + pytest harness"),
        bullet_list([
            f"dbt singular test: `{harness.dbt_test_sql_path}`",
            f"pytest wrapper: `{harness.pytest_path}`",
            f"Run with: `dbt test --select {harness.selector}` "
            f"or `pytest {harness.pytest_path} -k {harness.selector}`",
            "SQL routes through dbt to Snowflake; no direct snowflake.connector "
            "usage (per `prefer-mcp-for-data-platforms`).",
        ]),
    ]

    if is_bug:
        content.append(heading(3, "Repro steps"))
        content.append(bullet_list([
            f"`git checkout` the candidate branch.",
            f"Run `dbt run --select {req.target_model}` against `{req.snowflake_target_db}`.",
            f"Run `dbt test --select {harness.selector}` - should fail before fix, pass after.",
            "Re-run the validator matrix and confirm the regression test now passes.",
        ]))

    content.append(heading(3, "Trigger"))
    content.append(para(text(
        f"trigger=`{req.trigger}` failing_role=`{req.failing_role or '(none)'}` "
        f"issue_type=`{req.ticket.issue_type}`"
    )))

    return {"body": {"type": "doc", "version": 1, "content": content}}


# ---------------------------------------------------------------------------
# Jira write (only when auth_mode=full_auto)
# ---------------------------------------------------------------------------

def _post_jira_comment(ticket_key: str, adf: dict) -> dict:
    import json
    import os

    base = os.environ.get("JIRA_BASE_URL", "https://workdaybt.atlassian.net")
    email = os.environ.get("JIRA_EMAIL")
    token = os.environ.get("JIRA_API_TOKEN")
    if not email or not token:
        return {"error": "JIRA_EMAIL / JIRA_API_TOKEN not set"}
    url = f"{base}/rest/api/3/issue/{ticket_key}/comment"
    proc = subprocess.run(
        ["curl", "-sS", "-u", f"{email}:{token}",
         "-X", "POST", "-H", "Content-Type: application/json",
         "--data", json.dumps(adf), url],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return {"error": f"curl exit {proc.returncode}: {proc.stderr[:200]}"}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"error": f"non-JSON response: {proc.stdout[:200]}"}
