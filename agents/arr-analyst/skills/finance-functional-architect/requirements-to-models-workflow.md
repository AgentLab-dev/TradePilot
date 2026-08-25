# Requirements to Models Workflow

End-to-end from "I need a new metric" → production deploy.

This is your operating manual for managing the full lifecycle of a new
analytics build, from intake through retirement.

---

## §1. The 8 stages

```
INTAKE → DISCOVERY → KPI SPEC → FEASIBILITY → BACKLOG → BUILD → UAT → DEPLOY → MONITOR
```

Each stage has entry + exit criteria, owners, and artifacts.

---

## §2. Stage 1 — INTAKE

**Trigger**: Stakeholder request via Slack / email / meeting

**Entry criteria**: someone asks for a metric / dashboard / analysis

**Process**:
- 15-min intake call OR thread-based scoping
- Determine: is this an existing canonical, an ad-hoc, or a new build?

**Output artifact**: Intake form / Jira ticket

**Decision**:
- Existing canonical → route to `finance-functional-analytics` (SME answers)
- One-off analysis → route to `finance-bsa-data-analyst` (build in Sigma)
- New durable metric → proceed to STAGE 2

**Exit criteria**: Decision documented, owner assigned

**SLA**: 1 business day

---

## §3. Stage 2 — DISCOVERY

**Trigger**: Intake classified as "new durable metric"

**Entry criteria**: Approved Jira ticket; discovery interview scheduled

**Process**:
- 45-60 min discovery interview (see `kpi-specification-framework.md §4` for script)
- Follow-up clarifications via Slack / email
- Validate assumptions with related stakeholders

**Participants**:
- You (lead)
- Business owner
- Anyone else who'd consume this metric
- Optional: 1 engineer for early feasibility input

**Output artifact**: Discovery notes + draft KPI Spec outline

**Exit criteria**: All discovery questions answered; outline drafted

**SLA**: 1 week for discovery + outline

---

## §4. Stage 3 — KPI SPEC

**Trigger**: Discovery complete

**Entry criteria**: Discovery notes available

**Process**:
- Draft full KPI Spec (use template from `kpi-specification-framework.md`)
- Stakeholder review meeting (30-60 min)
- Iterate on the spec
- Collect written sign-offs

**Output artifact**: Approved KPI Spec (versioned, signed)

**Exit criteria**: Sign-off from business owner + SOX classifier (Finance Controller if Tier 1/2)

**SLA**: 1-2 weeks

---

## §5. Stage 4 — FEASIBILITY

**Trigger**: KPI Spec approved

**Entry criteria**: Spec signed off

**Process**:
- Engineering review with `enterprise-metrics-finance-architect`
- Identify upstream dependencies
- Estimate effort (T-shirt sizing or story points)
- Identify risks (data quality, performance, cross-domain coordination)
- Surface tradeoffs (full spec vs MVP)

**Output artifact**: Engineering effort estimate + risk register

**Decision**:
- Build as specified
- Build as MVP first, then full
- Defer (insufficient capacity)
- Reject (infeasible without major architectural change → escalate to council)

**Exit criteria**: Engineering commitment OR documented deferral

**SLA**: 1 week

---

## §6. Stage 5 — BACKLOG

**Trigger**: Engineering committed

**Entry criteria**: Effort estimate + risk register available

**Process**:
- Add to data engineering backlog (Jira)
- Prioritize against other items
- Sequence (which sprint, which engineer)

**Output artifact**: Sprint commitment

**Exit criteria**: Item in active sprint with assigned engineer

**SLA**: Up to 1 sprint (2 weeks)

---

## §7. Stage 6 — BUILD

**Trigger**: Sprint commitment

**Entry criteria**: Engineer kicked off

**Process** (engineering-led, you oversee):
- Engineer builds per spec
- dbt models implemented + tested
- You're available for clarification questions
- Mid-build checkpoint: review work in progress
- Pre-prod validation: reconciliation queries pass

**Output artifact**: Model + tests + documentation in PR

**Exit criteria**: PR merged to QA branch

**SLA**: Per spec — typically 1-4 sprints

---

## §8. Stage 7 — UAT (User Acceptance Testing)

**Trigger**: Built in QA

**Entry criteria**: QA build available; stakeholders available for review

**Process**:
- You + business owner review actual numbers
- Compare against acceptance criteria (from KPI Spec)
- Identify any discrepancies; route back to BUILD or DEPLOY
- Capture sign-off

**Output artifact**: UAT sign-off

**Exit criteria**: All acceptance criteria pass; stakeholder signs off

**SLA**: 1 week

---

## §9. Stage 8 — DEPLOY

**Trigger**: UAT passed

**Entry criteria**: UAT sign-off

**Process**:
- PR merged to prod branch
- Production build runs
- Dashboard published to Sigma
- Access granted to consumers
- Documentation published to catalog (Atlan / Confluence)

**Output artifact**: Deployed model + dashboard

**Exit criteria**: 
- Production reads work
- Dashboard renders for end users
- Catalog updated

**SLA**: 1 sprint

---

## §10. Stage 9 — MONITOR (ongoing)

**Trigger**: Deploy complete

**Entry criteria**: In production

**Process**:
- Monitor for issues:
  - Data freshness alerts
  - Reconciliation queries (quarterly)
  - Usage analytics
- Surface needs for changes
- Quarterly review

**Exit criteria**: Continuous (until deprecation)

---

## §11. The artifact trail (what gets created)

For every new metric:

| Stage | Artifact | Stored in |
|---|---|---|
| Intake | Intake form / Jira ticket | Jira |
| Discovery | Discovery notes | Confluence |
| KPI Spec | Signed KPI Spec | Catalog (Confluence + Atlan) |
| Feasibility | Effort estimate | Jira (as story points) |
| Backlog | Sprint commitment | Jira |
| Build | PR + commits | GitHub |
| Build | dbt models + tests | git repo |
| UAT | Sign-off document | Email / Jira |
| Deploy | Dashboard | Sigma |
| Deploy | Catalog entry | Atlan / Confluence |
| Monitor | Quarterly review | Confluence |

---

## §12. The roles + handoffs

| Stage | Lead | Supporting |
|---|---|---|
| Intake | You | Stakeholder |
| Discovery | You | Stakeholder, related parties |
| KPI Spec | You | Stakeholder, Controller (if SOX) |
| Feasibility | Engineering Lead | You |
| Backlog | Engineering Manager | You |
| Build | Engineer | You for questions |
| UAT | You | Stakeholder, Engineer |
| Deploy | Engineer | You for catalog |
| Monitor | You | Data engineering |

---

## §13. The "expedite" / "fast track" pattern

Sometimes (e.g., earnings prep) you need to fast-track:

```
INTAKE → KPI SPEC (compressed) → BUILD (parallel with spec) → UAT → DEPLOY
```

Timeline: 2-3 weeks instead of 6-8.

Tradeoffs:
- Higher rework risk (spec finalized in parallel with build)
- Less stakeholder cycle time
- More mid-build pivots

Use sparingly. Pre-coordinate with engineering capacity.

---

## §14. The "rejected" / "deferred" workflow

When you reject or defer:

1. **Document the reason** (in Jira)
2. **Notify stakeholder** with reason + alternatives
3. **Suggest workaround** (e.g., one-off Sigma analysis instead of new model)
4. **Capture re-evaluation criteria** (e.g., "revisit when product roadmap stabilizes")
5. **Schedule follow-up** (e.g., quarterly review)

Don't ghost the stakeholder. Reject explicitly.

---

## §15. The "stakeholder is unhappy" pattern

Sometimes the build doesn't meet expectations. Handle:

1. **Acknowledge**: "I hear that the dashboard doesn't show what you expected"
2. **Reproduce the gap**: walk through the spec vs the build
3. **Identify root cause**:
   - Spec was wrong → KPI spec amendment
   - Build was wrong → bug fix
   - Expectation mismatch → re-alignment meeting
4. **Plan fix**: timeline + responsibility
5. **Follow through**: don't drop until stakeholder confirms resolved

---

## §16. The "metric changed at source" pattern

When upstream changes (e.g., GTM team changes deal motion taxonomy):

1. **Notification from upstream** (or proactive monitoring)
2. **Impact assessment**: which downstream metrics affected?
3. **Coordinate with upstream owner**: timing, magnitude
4. **Plan downstream changes**: KPI Spec amendments, model updates
5. **Stakeholder communication**: notify consumers in advance
6. **Coordinated cutover**: same release window
7. **Validation**: reconciliation post-cutover

---

## §17. The "quarterly review" cadence

Every quarter:
- Review all in-flight projects
- Check stage of each
- Identify stuck items + unblock
- Refresh roadmap priorities
- Re-validate stakeholder priorities

Quarterly review meeting: 2-3 hours, attended by leadership + key stakeholders.

---

## §18. Anti-patterns

- ❌ Skip KPI Spec because "it's urgent" → leads to rework
- ❌ Build without UAT → stakeholder unhappy at deploy
- ❌ Skip catalog publishing → metric is "hidden" from broader org
- ❌ Skip stakeholder sign-off → no accountability
- ❌ Promise delivery without engineering commitment → broken promise

---

## §19. Cross-references

- `kpi-specification-framework.md` — KPI Spec template + capture
- `product-owner-playbook.md` — backlog + prioritization
- `metric-governance-and-controls.md` — council ops
- `enterprise-metrics-finance-architect` — build-side architecture
