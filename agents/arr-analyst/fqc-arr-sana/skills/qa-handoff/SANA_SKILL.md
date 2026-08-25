---
name: qa-handoff
description: Close out an FQC-ARR ticket by posting a QA-readiness summary to Jira — the validation matrix results across dev/qa, the PR link, test evidence, and what QA should verify — with the run report attached, after human approval. Third write gate of the DAG. Use as role 10 (final) after cd-monitor passes.
license: Proprietary-Internal
compatibility: Requires fqc-jira (add_comment + add_attachment are destructiveHint → Sana approval card). Host LLM drafts the ADF summary.
metadata:
  role_order: "10"
  status_values: "ok | needs_input | fail"
allowed-tools: fqc-jira.add_comment fqc-jira.add_attachment fqc-lessons.load_for
---

# qa-handoff

Give QA everything they need to validate, in one Jira comment, and attach the run report. Final write gate.

## Steps
1. Assemble the end-to-end evidence: `payload.validation` (dev), `payload.ci_report`, `payload.cd_report` (qa verdicts), `payload.pr` (link).
2. Draft an ADF QA-readiness comment: what changed, dev+qa tie-out results, the PR link, and a concrete "QA should verify …" checklist. Identifier-first; no agent signature.
3. Emit `payload.pending_handoff` (ADF + attachment plan) → `status = needs_input`, `pause_reason = "post QA-readiness to <ticket>"`.
4. **Only on approval**: `fqc-jira.add_comment(...)` then `fqc-jira.add_attachment(run_report)`.

## Output — `payload.handoff`
`pending_handoff{comment,attachment}, posted (bool), comment_url`.
`status = needs_input` until approved; `ok` once posted; `fail` on post error.

## Hard rules
- Never post/attach without approval — both `fqc-jira` writes are gated (destructiveHint).
- Do not transition the ticket to Done unattended; QA owns final acceptance.
- No agent signature; lead with the ticket key and the tie-out result.
