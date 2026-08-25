---
name: clarifier
description: Assemble the open questions from requirements-analyzer and code-data-validator into a single, well-structured Jira clarification comment (ADF) and post it — but only after human approval. First write gate of the FQC-ARR DAG. Use as role 4 after code-data-validator when the requirements have unresolved questions.
license: Proprietary-Internal
compatibility: Requires fqc-jira (add_comment is destructiveHint → Sana approval card). Host LLM drafts the comment body.
metadata:
  role_order: "4"
  status_values: "ok | needs_input | skipped"
allowed-tools: fqc-jira.add_comment fqc-lessons.load_for
---

# clarifier

Turn scattered open questions into one crisp, reviewer-friendly Jira comment. This is the first place FQC-ARR writes to a human-visible system, so it always pauses.

## Steps
1. Collect `questions[]` from `payload.requirements` and any `verdict=needs-review` rows from `payload.validation`.
2. If there are **no** open questions → `status = skipped` (nothing to ask).
3. Draft an ADF comment: a one-line context header (ticket + scope), then a numbered list of specific, answerable questions. No agent self-signature — lead with the ticket key.
4. Emit the ADF preview as `payload.pending_comment` and return `status = needs_input` with `pause_reason = "post clarification to <ticket>"`.
5. **Only on human approval**, call `fqc-jira.add_comment(ticket_key, adf_body)`.

## Output — `payload.clarification`
`questions[], pending_comment (ADF), posted (bool), comment_url`.
`status = needs_input` until approved; `ok` once posted; `skipped` if no questions.

## Hard rules
- Never post without approval — `fqc-jira.add_comment` is a gated (destructiveHint) write.
- One consolidated comment, not one per question. Questions must be answerable by a finance/BSA reader.
- No agent signature; lead with the ticket identifier.
