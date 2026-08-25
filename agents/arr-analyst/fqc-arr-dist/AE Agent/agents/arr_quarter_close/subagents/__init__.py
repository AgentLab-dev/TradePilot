"""Sub-agent modules under the Finance ARR Quarter Close (FQC-ARR) supervisor.

Each module exposes:

* ``plan(input) -> dict``     - returns the actions the sub-agent would take,
                                without executing. Safe in --dry-run.
* ``run(input)  -> RoleResult``- executes whatever it can purely in Python
                                  (curl, gh CLI, pytest, subprocess). For
                                  roles that fundamentally need an LLM
                                  (requirements analysis, implementation),
                                  ``run`` returns a ``RoleResult`` with
                                  ``status='needs_input'`` and the LLM prompt
                                  in ``payload['prompt']``. The supervisor
                                  then either drives the LLM via Cursor SDK
                                  or surfaces the prompt to the user.

The naming convention ``01_jira_intake.py`` reflects the canonical execution
order. Modules also re-export from the unprefixed name to keep imports clean
(``from agents.arr_quarter_close.subagents import jira_intake``).
"""

from agents.arr_quarter_close.subagents import (  # noqa: F401
    cd_monitor,
    ci_monitor,
    clarifier,
    code_data_validator,
    daily_reflection,
    debugger,
    implementer,
    jira_intake,
    pr_author,
    qa_handoff,
    quarter_close_runner,
    requirements_analyzer,
    test_runner,
)

# Canonical DAG order. The debugger is intentionally NOT in this tuple - it
# is dispatched on-demand by the supervisor (auto on FAIL, Slack `task:
# debug`, or CLI `--debug-model`) and runs alongside the DAG rather than
# inside it.
ORDER = (
    jira_intake,
    requirements_analyzer,
    code_data_validator,
    clarifier,
    implementer,
    test_runner,
    pr_author,
    ci_monitor,
    cd_monitor,
    qa_handoff,
)

# Sub-agents that run outside the canonical DAG.
ON_DEMAND = (debugger, quarter_close_runner, daily_reflection)

__all__ = ["ORDER", "ON_DEMAND"]
