"""Cursor SDK wrapper that runs the ARR Quarter Close via a Cursor agent.

Use this when you want the close to be driven by Cursor (interactive in-IDE,
cloud agent, or scheduled Cursor Automation) so the streaming output, MCP
tool calls (Snowflake, dbt MCP), and PR/comment authoring all happen inside
a single Cursor run.

Two modes:

* ``run_close_via_prompt`` (default) - delegates the entire runbook to a
  Cursor agent with the close skill + rule already loaded. The agent picks
  its dbt invocations from the skill/runbook.
* ``run_close_via_core`` - keeps deterministic control in ``core`` and uses
  Cursor only to wrap, narrate, and post-process the result.

Both honor ``CURSOR_API_KEY`` from the environment; both require the
``cursor-sdk`` package (``pip install cursor-sdk``).
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from agents.arr_quarter_close.contracts import resolve_default_llm_model
from agents.arr_quarter_close.core import (
    ARRCloseConfig,
    ARRCloseOrchestrator,
    CloseResult,
)

log = logging.getLogger(__name__)


@dataclass
class CursorRunOptions:
    api_key: Optional[str] = None
    # Default model for the Cursor SDK agent that drives the Mode A close.
    # Pulls from ``resolve_default_llm_model()`` (which honors the
    # ``$FQC_ARR_DEFAULT_MODEL`` env override) so a single
    # ``DEFAULT_LLM_MODEL`` constant in ``contracts.py`` is the source of
    # truth across the CLI runner, the SDK runner, and every LLM-driven
    # sub-agent. Override at the call site if needed.
    model: str = field(default_factory=resolve_default_llm_model)
    project_dir: Path = Path(".")

    def resolved_api_key(self) -> str:
        key = self.api_key or os.environ.get("CURSOR_API_KEY")
        if not key:
            raise RuntimeError(
                "CURSOR_API_KEY is not set. Export it or pass api_key=. "
                "Mint a key at https://cursor.com/dashboard/integrations."
            )
        return key


_AGENT_PROMPT_TEMPLATE = """\
You are running the ARR Quarter Close for the eda-dbt-em repo.

Inputs:
  as_was_date     : {as_was_date}
  target          : {target}
  heavy_warehouse : {heavy_warehouse}
  refresh_dashboards: {refresh_dashboards}
  run_validation  : {run_validation}
  include_ia_migration_tests: {include_ia_migration_tests}

Mandatory steps - follow `.cursor/skills/arr-quarter-close/runbook.md` exactly,
and respect the guardrails in `.cursor/rules/arr-quarter-close.mdc`:

  1. Stage:    path:models/finance/int/stage/table/tmp_tbls_of_bt_arr_categories_optimized
  2. Line:     +arr_line_categories  (heavy; use em_heavy_warehouse if provided)
  3. Rollups:  arr_sku_categories arr_subproduct_categories arr_product_categories
  4. Corp:     +arr_account_product_corp_report
  5. Optional: path:models/finance/modeled/data_product/view  (only if refresh_dashboards)
  6. Validate: dbt test test_arr_waterfall_balance
  7. Validate: dbt test tag:ia_migration  (only if include_ia_migration_tests)

Always:
  - Always pass --exclude '*_scd2' on run steps.
  - Always pass --vars '{{"as_was_date":"\\'{as_was_date}\\'"}}'.
  - Prefer the dbt MCP over raw shell when available.
  - Report status per step; stop on first hard failure unless explicitly told otherwise.

When finished, emit a JSON object on the final line with this shape:
  {{ "as_was_date": "...", "overall_status": "success|warn|fail", "steps": [...] }}
"""


def _format_prompt(cfg: ARRCloseConfig) -> str:
    return _AGENT_PROMPT_TEMPLATE.format(
        as_was_date=cfg.as_was_date,
        target=cfg.target or "(default)",
        heavy_warehouse=cfg.heavy_warehouse or "(unset)",
        refresh_dashboards=str(cfg.refresh_dashboards).lower(),
        run_validation=str(cfg.run_validation).lower(),
        include_ia_migration_tests=str(cfg.include_ia_migration_tests).lower(),
    )


def run_close_via_prompt(cfg: ARRCloseConfig, opts: CursorRunOptions) -> dict:
    """Delegate the entire close to a Cursor agent with skill/rule loaded.

    Returns the parsed final JSON the agent emitted, or a wrapper dict with
    the raw final text if parsing fails.
    """
    try:
        from cursor_sdk import Agent, AgentOptions, LocalAgentOptions
    except ImportError as exc:
        raise RuntimeError(
            "cursor-sdk is not installed. `pip install cursor-sdk` to enable "
            "the Cursor runner, or fall back to agents.arr_quarter_close.cli."
        ) from exc

    prompt = _format_prompt(cfg)
    log.info("Launching Cursor agent for ARR close as_was_date=%s", cfg.as_was_date)

    result = Agent.prompt(
        prompt,
        AgentOptions(
            api_key=opts.resolved_api_key(),
            model=opts.model,
            local=LocalAgentOptions(cwd=str(opts.project_dir.resolve())),
        ),
    )
    final_text = (result.result or "").strip()
    parsed = _try_extract_json(final_text)
    return {
        "agent_status": result.status,
        "agent_text_tail": final_text[-2000:],
        "parsed": parsed,
    }


def run_close_via_core(cfg: ARRCloseConfig, opts: CursorRunOptions) -> CloseResult:
    """Run deterministically via core but emit a Cursor agent narration after.

    Used when you want the strict step manifest of `core` but still want a
    Cursor agent to summarize and (e.g.) post the result to Slack/Jira via MCP.
    """
    result = ARRCloseOrchestrator(cfg).run()
    try:
        from cursor_sdk import Agent, AgentOptions, LocalAgentOptions
    except ImportError:
        log.warning("cursor-sdk not installed; skipping narration step.")
        return result

    summary_prompt = (
        "Summarize this ARR Quarter Close run for the finance team. "
        "Lead with the bottom line (status + duration), then per-step "
        "highlights, then any follow-ups. Use the result JSON:\n\n"
        + json.dumps(result.as_dict(), indent=2)
    )
    Agent.prompt(
        summary_prompt,
        AgentOptions(
            api_key=opts.resolved_api_key(),
            model=opts.model,
            local=LocalAgentOptions(cwd=str(opts.project_dir.resolve())),
        ),
    )
    return result


def _try_extract_json(text: str) -> Optional[dict]:
    """Best-effort: find the last balanced { ... } in `text` and json.loads it."""
    if not text:
        return None
    last_close = text.rfind("}")
    if last_close == -1:
        return None
    depth = 0
    for i in range(last_close, -1, -1):
        ch = text[i]
        if ch == "}":
            depth += 1
        elif ch == "{":
            depth -= 1
            if depth == 0:
                candidate = text[i : last_close + 1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    return None
    return None
