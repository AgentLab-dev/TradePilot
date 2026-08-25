# Metric Governance & Controls

How to run the metric council, manage metric definition changes, handle
restated metrics, and govern the canonical metric portfolio over time.

This is your operating manual for the governance side of the job —
where you chair the metric council and adjudicate definition disputes.

---

## §1. The metric council — composition + cadence

| Role | Member | Purpose |
|---|---|---|
| **Chair** | You (Functional Architect) | Drives agenda, documents decisions |
| **Finance Controller** | Veto over SOX-tier changes |
| **VP FP&A** | Plan alignment |
| **Director Sales Ops** | Sales-side metric coordination |
| **Director CS Ops** | CS-side metric coordination |
| **Engineering Lead** (data) | Feasibility input |
| **Investor Relations Director** | Disclosure consistency |
| **Optional: VP Product Analytics** | Product analytics coordination |
| **Optional: Compliance Officer** | For Tier-1 changes |

Cadence: Monthly (60 min) + ad-hoc for material changes.

---

## §2. The council's authority

The council DECIDES:
- New metric approval (Tier 1/2)
- Metric definition changes (any tier)
- Restated metrics (Tier 1/2)
- Cross-domain metric reconciliation
- Metric deprecation (Tier 1/2)
- Canonical definition disputes

The council DOES NOT DECIDE:
- Implementation details (engineering owns)
- Build sequencing (you own as PO)
- Day-to-day ad-hoc analyses (analysts own)

---

## §3. The standard council meeting agenda

```
00:00-00:05  Welcome + review action items from prior meeting
00:05-00:20  Topic 1 (e.g., new metric proposal)
00:20-00:40  Topic 2 (e.g., restatement decision)
00:40-00:55  Topic 3 (e.g., definition dispute)
00:55-01:00  Wrap + action items + next meeting date
```

Pre-read sent 48 hours prior. Decisions captured same-day.

---

## §4. The decision log

Every council decision documented:

```
═══════════════════════════════════════════════════════════════════════════════
COUNCIL DECISION #2026-04-001
═══════════════════════════════════════════════════════════════════════════════

DATE:                2026-04-15
TOPIC:               Definition change — "Marketing-Sourced Pipeline"
PROPOSED BY:         CMO Office, via VP Marketing Ops
TIER IMPACTED:       3 (operational)

PROPOSED CHANGE:
   Current definition: Pipeline with lead_source = 'Marketing'
   Proposed definition: Pipeline with lead_source IN ('Marketing', 'Marketing-Event', 'Marketing-Webinar')
                       AND first_touch_attribution_source = 'Marketing'

RATIONALE:
   Current definition misses event + webinar sources, which Marketing 
   considers their channels. Multi-touch attribution should override.

IMPACT ASSESSMENT:
   - Marketing-Sourced Pipeline ARR likely increases ~12% under new definition
   - Sales would need re-attribution review
   - Downstream dashboard "Marketing Influence" affected (1 view)

DISCUSSION SUMMARY:
   - CMO Office: in favor; aligns with industry attribution standards
   - Sales Ops: concerned about double-counting with sales motion
   - FP&A: neutral; impacts marketing budget allocation reporting
   - Finance Controller: not Tier 1/2, no SOX concern

DECISION:                              APPROVED
   Effective:                          2026-05-01 (Q2 FY27 start)
   Affected products:                  Marketing-Sourced Pipeline, Marketing Dashboards
   Backward-compatibility approach:    Both versions live for 90 days (v1, v2)

ACTION ITEMS:
   - You: Update KPI Spec for "Marketing-Sourced Pipeline" (by 2026-04-22)
   - Engineering: Implement v2 (by 2026-04-30)
   - CMO Office: Update Sigma dashboards (by 2026-05-15)

ATTENDEES:
   [list of attendees]

SIGN-OFF:
   [Chair signature]
═══════════════════════════════════════════════════════════════════════════════
```

Logged in `Council_Decision_Log` (Confluence or similar).

---

## §5. The "definition change" workflow

When a stakeholder proposes changing a metric's definition:

### 5.1 Pre-council steps

1. **Receive proposal**: from stakeholder (often via Slack / email)
2. **Initial assessment** (you):
   - Is this purely operational (no investor / financial impact)? → Tier 3
   - Does it impact published numbers? → Tier 1/2 → must go to council
3. **Impact analysis** (you + engineering):
   - What models / dashboards affected?
   - What numbers shift, by how much?
   - What's the implementation effort?
4. **Stakeholder coordination**:
   - Notify affected parties
   - Get pre-meeting feedback
5. **Draft proposal**: with pre-read material

### 5.2 Council deliberation

At the meeting:
- Walk through the proposal
- Each member shares perspective
- Identify concerns / alternatives
- Vote (often by consensus, sometimes by majority for contested issues)

### 5.3 Post-decision

- Document in `Council_Decision_Log`
- Notify affected stakeholders
- Update KPI Spec (new version)
- Coordinate engineering rebuild
- Cutover communication
- Reconciliation + validation

---

## §6. The "metric restatement" workflow

When a published metric must be restated (correction):

### 6.1 Trigger

- Data quality bug discovered
- Source data correction (e.g., Salesforce data fix)
- Definition error realized

### 6.2 Pre-council

1. **Quantify the impact**:
   - Which `as_was_date`s affected?
   - Which dashboards / reports affected?
   - What's the magnitude (in $ + %)?
2. **Determine materiality**:
   - Material → council + Finance Controller approval
   - Non-material → standard fix workflow
3. **Stakeholder pre-notification**: heads-up to known consumers

### 6.3 Council decision

For material restatements:
- Walk through the impact
- Decide: restate vs disclose-going-forward only
- Determine investor-disclosure requirement
- Approve restatement window + plan

### 6.4 Execution

1. Engineering rebuilds affected snapshots (SOX-approved path; see `sox-and-audit-architecture.md`)
2. Restate logged in `RESTATEMENT_LOG`
3. Dashboards updated
4. Stakeholder communication: "previously published $X, now $Y"
5. If investor-disclosure-required: coordinate with IR for next earnings call

### 6.5 Post-mortem

- Root cause analysis
- Process / control change to prevent recurrence
- Document in `RESTATEMENT_POSTMORTEM_LOG`

---

## §7. The cross-domain definition reconciliation

Common: Sales and Finance define "renewal" differently.
- **Sales**: "Renewal" = a deal that was previously sold, re-sold (often loose)
- **Finance**: "Renewal" = SSR-resolved continuation of existing ARR

These ARE different things. Both are valid for their purpose.

Reconciliation approach:
1. **Both definitions documented explicitly** in respective glossaries
2. **Cross-reference** in the KPI Spec
3. **Mapping table** if applicable (e.g., Sales "Renewal" maps to which Finance categories?)
4. **Educate** users: "If you see different numbers, here's why"
5. **Tooling**: dashboards label clearly which definition is being shown

Don't force false convergence. Embrace explicit divergence.

---

## §8. The "metric is wrong" investigation flow

When someone claims a metric is wrong:

1. **Reproduce both numbers**:
   - The claimed wrong number
   - What the claimant thinks is right
2. **Identify the gap**:
   - Different filter? Different period? Different currency? Different definition?
3. **Determine the canonical answer**:
   - Reference KPI Spec
   - If spec says one thing and dashboard shows another → fix dashboard
   - If spec says one thing and stakeholder expected another → educate / re-spec
4. **Document the resolution**:
   - Update KPI Spec if definition was unclear
   - Fix bug if implementation was wrong
   - Communicate the canonical answer to all consumers
5. **Postmortem** if material: process change to prevent

---

## §9. The "definition deprecation" workflow

When a definition is changed materially (not just expanded), the old definition is deprecated:

1. **Announce deprecation**: 90-day window
2. **Both definitions live** during window (v1 + v2 in parallel)
3. **Migration support**: documentation, office hours
4. **Sunset**: v1 retired, v2 becomes canonical
5. **Catalog updated**: v1 marked deprecated, v2 marked canonical

---

## §10. The semi-annual portfolio audit

Every 6 months:

1. **List every published metric**
2. **For each**: pull KPI Spec, verify it's up to date
3. **For each**: pull current numbers, verify reconciliation passes
4. **For each**: verify consumer list current
5. **Identify gaps**: metrics in use without specs
6. **Identify redundancies**: multiple metrics measuring same thing
7. **Recommendations**: consolidations, deprecations, new specs

Output: Portfolio Health Report → CFO + leadership.

---

## §11. The "investor disclosure" alignment

Workday is public. Quarterly earnings include certain metrics.

For investor-facing metrics:
- Finance Controller + IR own external definition
- You ensure internal canonical matches external definition
- Any change to definition → coordinate with IR + Finance Controller
- Disclosure-impacting restatements → IR-coordinated process

Tight loop with IR: monthly sync, ad-hoc during earnings season.

---

## §12. The "regulator inquiry" pattern

Rare but possible: SEC or other regulators inquire about a metric.

If this happens:
1. **Notify Legal + Finance Controller + CFO immediately**
2. **Do NOT respond directly** — Legal + IR own response
3. **Gather supporting documentation**:
   - KPI Spec
   - Approval evidence
   - Reconciliation history
   - Audit log
4. **Provide to Legal**
5. **Maintain confidentiality**

Architectural implication: ensure documentation + audit trail is always inquiry-ready.

---

## §13. The "canonical glossary"

Maintain a single canonical glossary of finance terms:

| Term | Definition | Source |
|---|---|---|
| ARR | Annualized recurring revenue | KPI Spec FIN-001 |
| ACV | Annual contract value | KPI Spec FIN-002 |
| TCV | Total contract value | KPI Spec FIN-003 |
| NDR / NRR | Net dollar retention | KPI Spec FIN-010 |
| GRR | Gross retention rate | KPI Spec FIN-011 |
| Churn (customer) | Account fully terminated | KPI Spec FIN-020 |
| Churn (product) | Specific product dropped, account retained | KPI Spec FIN-021 |
| Renewal (SSR-resolved) | Continuation via Apttus SSR | KPI Spec FIN-030 |
| ... | ... | ... |

Stored in Confluence + Atlan. Linked from every KPI Spec.

When new term proposed → council reviews and adds.

---

## §14. The change-management calendar

Major metric changes:
- **Avoid Q4 close window** (Jan 15 – Feb 15)
- **Avoid earnings prep** (3 weeks before earnings)
- **Prefer**: early in a fiscal quarter (Feb, May, Aug, Nov)

Coordination calendar shared with stakeholders.

---

## §15. Anti-patterns (governance smells)

- ❌ Approving a change in private (without council) for Tier 1/2
- ❌ Not documenting the decision rationale (just "we decided X")
- ❌ Restating without SOX approval
- ❌ Letting two definitions of the same thing exist indefinitely
- ❌ No deprecation timeline → consumers stuck on old definition forever
- ❌ Failing to notify investors of material restatement
- ❌ Treating definition changes as engineering tickets (not council items)
- ❌ Glossary not maintained → terms drift

---

## §16. Cross-references

- `kpi-specification-framework.md` — Spec format
- `requirements-to-models-workflow.md` — intake workflow
- `product-owner-playbook.md` — backlog mechanics
- `enterprise-metrics-finance-architect/sox-and-audit-architecture.md` — SOX side
