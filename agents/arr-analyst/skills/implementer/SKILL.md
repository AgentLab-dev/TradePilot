---
name: implementer
description: Make the actual code change for an FQC-ARR ticket — create a feature branch, edit the affected dbt models/macros/YAML, and add or update tests, guided by a host-LLM prompt grounded in the requirements and validation matrix. Use as role 5 of the FQC-ARR DAG after clarifier. Edits files on a feature branch only; never pushes (that is pr-author).
license: Proprietary-Internal
compatibility: Host LLM performs the edits from the emitted prompt. Deterministic scaffolding (branch name, file plan) comes from the tool. Requires fqc-github (branch create) + local repo.
metadata:
  role_order: "5"
  status_values: "ok | warn | needs_input | fail"
allowed-tools: fqc-github.create_branch fqc-lessons.load_for fqc-lessons.search
---

# implementer

Produce the code change on an isolated feature branch. The deterministic parts (branch name, file plan, test stubs) are scaffolded; the substantive SQL/Jinja edits are done by the host LLM from the emitted prompt.

## Steps
1. Ground with `fqc-lessons.load_for("implementer")` + `fqc-lessons.search(<affected models>)`.
2. Create a feature branch `feature/<ticket_key>-<slug>` via `fqc-github.create_branch` (from the default branch; never `qa`/`prod`).
3. Build a **file plan** from `payload.requirements` + `payload.validation`: which models/macros/YAML change, which tests to add.
4. Emit `payload.prompt` + `payload.preferred_model` (heavy reasoning model) instructing the host LLM to apply the edits and add/adjust dbt tests per the validation matrix.
5. Record the edited files + diff summary as `payload.implementation`.

## Output — `payload.implementation`
`branch, file_plan[], edited_files[], added_tests[], diff_summary, notes`.
`status = ok` when edits are complete and coherent; `warn` if partial; `needs_input` if a design choice needs a human; `fail` if the branch/edits can't be produced.

## Hard rules
- Feature branch only — never edit on `qa`/`prod`, never push here (pr-author pushes).
- Never silently edit `dbt_project.yml::arr_refactor_as_was_date_list`; if it must change, surface it explicitly as a `needs_input`.
- Every behavioral change ships with a matching test (waterfall / parity / tie-out).
- Pick one currency variant per metric; keep grain consistent with the requirements spec.
