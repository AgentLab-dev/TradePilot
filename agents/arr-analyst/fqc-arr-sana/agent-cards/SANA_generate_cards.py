#!/usr/bin/env python3
"""Generate the remaining FQC-ARR A2A agent cards from the role registry.

Three cards are hand-authored as canonical examples (supervisor, jira-intake=read-only,
clarifier=gated-write). This script emits the other 9 role cards from the same shape so
every card stays consistent. stdlib only; run:  python3 SANA_generate_cards.py
"""
import json
import pathlib

HERE = pathlib.Path(__file__).parent

# role -> (order, description, write_capable, requires_approval, gated_tools, mcp_deps, output_key, tags, example)
ROLES = {
    "requirements-analyzer": (2, "Read-only role agent. Turns a TicketSpec into a KPI/requirements spec (candidate models, metrics, business rules, open questions) and emits a host-LLM refinement prompt.", False, False, [], ["fqc-lessons"], "payload.requirements", ["requirements", "kpi", "read-only"], "build the requirements spec for EDAEM-3772"),
    "code-data-validator": (3, "Read-only role agent. Scans the eda-dbt-em repo for affected models/macros and builds a ValidationMatrix of Snowflake tie-out checks, emitting auditable SELECT-only SQL templates.", False, False, [], ["fqc-snowflake", "fqc-lessons"], "payload.validation", ["validation", "snowflake", "read-only"], "build the validation matrix for EDAEM-3772"),
    "implementer": (5, "Write-capable (feature branch only) role agent. Creates a feature branch and applies the dbt model/macro/test edits from a host-LLM prompt. Never pushes; never touches qa/prod.", True, False, ["fqc-github.create_branch"], ["fqc-github", "fqc-lessons"], "payload.implementation", ["implement", "dbt", "feature-branch"], "implement the change for EDAEM-3772"),
    "test-runner": (6, "Non-destructive role agent. Builds + tests the feature branch on finance_dev and re-runs the ValidationMatrix SQL to fill actual values and verdicts.", False, False, [], ["fqc-dbt", "fqc-snowflake", "fqc-lessons"], "payload.test_report", ["dbt", "test", "dev"], "run dev tests for EDAEM-3772"),
    "pr-author": (7, "Write-capable (gated) role agent. Drafts a substance-first PR title/body and, after approval, pushes the branch and opens the PR into the default branch.", True, True, ["fqc-github.push_branch", "fqc-github.create_pr"], ["fqc-github", "fqc-lessons"], "payload.pr", ["github", "pr", "gated", "hitl"], "open the PR for EDAEM-3772"),
    "ci-monitor": (8, "Read-only role agent. Polls PR CI checks until they conclude and re-runs the ValidationMatrix vs finance_dev to confirm the CI build ties out.", False, False, [], ["fqc-github", "fqc-snowflake", "fqc-slack", "fqc-lessons"], "payload.ci_report", ["ci", "github", "read-only"], "watch CI for the EDAEM-3772 PR"),
    "cd-monitor": (9, "Read-only role agent. Watches the CD deploy to finance_qa and re-runs the ValidationMatrix vs finance_qa to confirm the deployed models tie out.", False, False, [], ["fqc-dbt", "fqc-snowflake", "fqc-slack", "fqc-lessons"], "payload.cd_report", ["cd", "deploy", "qa", "read-only"], "watch the qa deploy for EDAEM-3772"),
    "qa-handoff": (10, "Write-capable (gated) role agent. Posts a QA-readiness summary (dev+qa tie-out, PR link, checklist) to Jira and attaches the run report, after approval. Final write gate.", True, True, ["fqc-jira.add_comment", "fqc-jira.add_attachment"], ["fqc-jira", "fqc-lessons"], "payload.handoff", ["jira", "qa", "gated", "hitl"], "hand EDAEM-3772 to QA"),
    "debugger": (0, "Read-only investigation role agent (on-demand). Root-causes a failing dbt model or ValidationMatrix check via lineage + read-only Snowflake probes and proposes a fix + regression test. Any Jira note is gated.", True, True, ["fqc-jira.add_comment"], ["fqc-snowflake", "fqc-dbt", "fqc-jira", "fqc-lessons"], "payload.debug", ["debug", "root-cause", "on-demand"], "task: debug arr_line_categories"),
    "quarter-close-runner": (0, "On-demand role agent. Runs the scheduled/snapshot ARR close (stage stg_arr_categories chain, build rollups, refresh corp report, validate waterfall + IA recon). Prod runs always require approval.", True, True, ["fqc-dbt.run"], ["fqc-dbt", "fqc-snowflake", "fqc-lessons"], "payload.close_report", ["quarter-close", "dbt", "on-demand", "gated"], "task: quarter-close 2026-01-31"),
}


def card(name, spec):
    order, desc, write_capable, requires_approval, gated, deps, out_key, tags, example = spec
    skill_id = name.replace("-", "_")
    return {
        "protocolVersion": "1.0",
        "name": name,
        "description": desc,
        "version": "2.0-sana",
        "provider": {"organization": "analytics-engineering", "url": "internal://eda-dbt-em"},
        "supportedInterfaces": [{"transport": "A2A", "url": f"a2a://fqc-arr/{name}"}],
        "defaultInputModes": ["application/json"],
        "defaultOutputModes": ["application/json"],
        "capabilities": {"streaming": False, "pushNotifications": bool(requires_approval)},
        "securitySchemes": {"sana-oauth2": {"type": "oauth2", "description": "Sana connector auth."}},
        "security": [{"sana-oauth2": []}],
        "skills": [{
            "id": skill_id,
            "name": name.replace("-", " ").title(),
            "description": desc,
            "tags": tags,
            "examples": [example],
            "inputModes": ["application/json"],
            "outputModes": ["application/json"],
        }],
        "x-fqc-arr": {
            "role_order": order,
            "write_capable": write_capable,
            "requires_approval": requires_approval,
            "gated_tools": gated,
            "mcp_dependencies": deps,
            "output_key": out_key,
        },
    }


def main():
    written = []
    for name, spec in ROLES.items():
        path = HERE / f"SANA_{name}.agent-card.json"
        path.write_text(json.dumps(card(name, spec), indent=2) + "\n")
        written.append(path.name)
    print(f"wrote {len(written)} cards:")
    for w in sorted(written):
        print(f"  {w}")


if __name__ == "__main__":
    main()
