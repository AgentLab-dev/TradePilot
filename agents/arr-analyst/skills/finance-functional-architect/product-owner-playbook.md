# Product Owner Playbook

How to operate as the Finance Analytics Data Product Owner — managing
the backlog, prioritizing the roadmap, running standups, balancing
stakeholder + engineering tensions.

The "data product" mindset: treat each canonical dataset / dashboard /
metric as a product with users, an SLA, a versioning strategy, and a
lifecycle.

---

## §1. Your products (what you own)

| Product | What | Owner consumers |
|---|---|---|
| `FINANCE_LINE_ANALYTICS` | Canonical ARR / ACV / TCV at ALI grain | FP&A, Finance |
| `ARR_*_CATEGORIES` family | 7+ ARR aggregations | Product, Sales Ops, FP&A |
| `ARR_NDR_DASH_V2` | Dashboard publish | Product leadership, IR |
| `ARR_GROWTH_DECOMPOSITION_DASH` | Growth decomposition | CFO, exec team |
| `ARR_FORECAST_*` family | Forward-looking metrics | FP&A, sales planning |
| Various Sigma workbooks | BI consumption | Various |
| KPI catalog | Metadata about all the above | All consumers |

For each product:
- Named owner (you)
- Backlog (Jira)
- Roadmap (Atlassian Plans or Confluence)
- SLA (freshness, uptime)
- Versioning strategy
- Deprecation policy

---

## §2. The backlog structure

Backlog organized into epics → stories → tasks:

```
EPIC: Q2 FY26 — Cohort Retention Dashboards
   STORY: Vintage cohort retention dashboard
      TASK: KPI Spec authored
      TASK: Reconciliation queries built
      TASK: dbt model built
      TASK: Sigma dashboard built
      TASK: UAT
      TASK: Deploy
      TASK: Training
   STORY: Tenure cohort retention dashboard
      ...
```

Per Jira ticket: include KPI Spec link, acceptance criteria, definition of done.

---

## §3. The prioritization framework — RICE

RICE = Reach × Impact × Confidence / Effort

For each backlog item:

| Dimension | Range | How to score |
|---|---|---|
| **Reach** | # people benefiting per month | 1 person, 10 people, 100 people, 1000 people |
| **Impact** | 1-3 scale | Massive (3), High (2), Medium (1) |
| **Confidence** | 0-100% | How sure are you about reach + impact? |
| **Effort** | Person-weeks | T-shirt size → weeks |

Score: (Reach × Impact × Confidence) / Effort

Higher score = higher priority.

Example:
| Item | Reach | Impact | Conf | Effort | RICE |
|---|---|---|---|---|---|
| Cohort retention dashboard | 50 | 2 | 80% | 4 wk | 20 |
| Forecast accuracy dashboard | 30 | 3 | 70% | 6 wk | 10.5 |
| ARR FX decomposition | 10 | 2 | 90% | 2 wk | 9 |

RICE doesn't dictate priority — it informs the conversation.

---

## §4. The MoSCoW framework — for release planning

For each release / quarter:
- **Must have**: cannot ship without these
- **Should have**: high value, ship if possible
- **Could have**: nice to have, ship if time permits
- **Won't have**: explicitly deferred (still on backlog, just not this release)

Helps stakeholders accept what's NOT in the release. Manages expectations.

---

## §5. The OKR framework — for quarterly themes

Define OKRs per quarter aligned to business OKRs:

```
QUARTERLY OKR: Improve forecast accuracy across product portfolio
   KR1: Deliver product-level forecast variance dashboard by Q2 end
   KR2: Reduce forecast-actual variance from 8% → 5% via retraining
   KR3: Cover 100% of products (currently 60%) with forecast dashboards
```

Backlog items roll up to OKRs. Stakeholders see priorities through OKR lens.

---

## §6. The capacity planning conversation (with engineering)

Engineering has finite capacity. You + Engineering Manager:

| Conversation | What to discuss |
|---|---|
| Weekly | What's in this sprint? Any blockers? |
| Monthly | What's next sprint? Carry-over? Trade-offs? |
| Quarterly | Big-picture: how much of next quarter is committed? Slack for new urgent? |

Pattern: 70% committed work, 20% flexible / urgent, 10% tech debt / improvement.

---

## §7. The stakeholder communication cadence

| Cadence | Audience | Format |
|---|---|---|
| **Weekly** | Engineering team | Standup + Slack thread |
| **Bi-weekly** | Key stakeholders (FP&A, Sales Ops) | Roadmap sync (30 min) |
| **Monthly** | All consumers | Product update email + Slack |
| **Quarterly** | Exec stakeholders | Roadmap review (60 min) + memo |
| **Annually** | All-hands | State of finance analytics talk |

Consistent rhythm = stakeholders informed = fewer surprises.

---

## §8. The "shipping" SOP

When a new product (metric / dashboard) ships:

1. **Pre-launch**:
   - Sneak preview to key stakeholders (1 week before)
   - Documentation reviewed
   - Catalog entry drafted
2. **Launch day**:
   - Deploy to prod
   - Catalog published
   - Announcement: Slack + email to consumers
   - Office hours scheduled (drop-in for questions)
3. **Post-launch**:
   - Monitor usage (Sigma access logs, Atlan)
   - Solicit feedback (Slack thread)
   - Iterate on feedback (next sprint)

---

## §9. The "killing" SOP (deprecation)

When a product becomes obsolete:

1. **Identify candidates**: low usage, replaced by v2, no consumer requests
2. **Stakeholder consult**: confirm safe to deprecate
3. **Deprecation announcement**: 90-day window
4. **Catalog update**: mark deprecated, document migration path
5. **Sunset**: remove from prod, preserve in git
6. **Postmortem**: did this teach us anything about future builds?

---

## §10. The "data product as a product" mindset

Treat your data products as products:

| Software product | Data product analog |
|---|---|
| Feature request | New metric request |
| Bug | Metric discrepancy / wrong number |
| User story | KPI Spec |
| Sprint review | Stakeholder UAT |
| Acceptance criteria | Reconciliation criteria |
| Release notes | Catalog entry + change log |
| User documentation | KPI Spec + training material |
| Support | Office hours + Slack support |
| Analytics | Usage analytics (Sigma logs) |

This mindset elevates your work from "build a query" to "build a product".

---

## §11. The "I have 10 asks and 2 engineers" pattern

Inevitable. Approach:
1. **Stack rank all 10** (RICE + stakeholder importance)
2. **Capacity check**: 2 engineers × 6 weeks = 12 person-weeks
3. **Slice**: top items first; bottom items deferred
4. **Communicate**: every stakeholder gets a "yes / not now / no" with reason
5. **Track**: deferred items don't disappear — revisit quarterly

Don't say "yes" to everyone. Don't say "no" to everyone. Say "here's where you are in the queue and why".

---

## §12. The "stakeholder politics" reality

Different stakeholders pull in different directions:
- CFO wants forecast accuracy
- CRO wants pipeline visibility
- CMO wants attribution
- Each thinks their need is most important

Your job: triage with explicit framework (RICE / OKRs), not by who shouts loudest.

Document the framework. Apply consistently. Be transparent about tradeoffs.

When a senior exec pulls rank: escalate to the Chief Data Officer or your VP for re-prioritization decision (don't override RICE on your own).

---

## §13. The "MVP first, expand later" pattern

For large asks (e.g., full cohort retention suite):

1. **MVP**: minimum viable version (1 view, 1 dashboard, 1 use case)
2. **Stabilize**: ensure quality, fix bugs
3. **Expand**: add additional views, slices, use cases
4. **Mature**: optimize performance, add advanced features

MVP first lets you:
- Validate the design
- Gather feedback
- Demonstrate value early
- De-risk the rest

---

## §14. The "deprecation announcement" template

```
TO: All consumers of <product>
SUBJECT: <product> Deprecation Notice — Sunset Date <DATE>

Hi all,

We are deprecating <product> effective <SUNSET_DATE> (90 days from now).

REASON: <e.g., "Replaced by ARR_PRODUCT_CATEGORIES_v2, which adds X, Y, Z">

MIGRATION:
- Existing users should migrate to <new product>
- Migration guide: <link>
- Office hours: <date / time>

TIMELINE:
- Today: <DEPRECATION_DATE> — deprecation announced
- <30 days>: <30_DATE> — final migration support
- <60 days>: <60_DATE> — last-call reminder
- <90 days>: <SUNSET_DATE> — product retired

QUESTIONS: <Slack channel> or reply to this email.

Thanks,
<You>
```

---

## §15. The "monitor product health" dashboard

You maintain a meta-dashboard for finance analytics product health:

| Product | Last refresh | Uptime % | Active users (30d) | Open issues |
|---|---|---|---|---|
| FINANCE_LINE_ANALYTICS | 4 hrs ago | 99.8% | 12 (dbt + analysts) | 1 |
| ARR_PRODUCT_CATEGORIES | 4 hrs ago | 99.9% | 45 | 0 |
| ARR Sigma dashboard | live (view) | 99.5% | 120 | 2 |
| ... | ... | ... | ... | ... |

Source: Snowflake `ACCESS_HISTORY`, dbt Cloud, Atlan usage stats, Sigma logs.

Updates weekly. Reviewed at quarterly stakeholder meeting.

---

## §16. The "monthly product update email" template

```
TO: Finance analytics consumers
SUBJECT: Finance Analytics Product Update — <MONTH YYYY>

Hi all,

Highlights from last month:

SHIPPED:
- <Product A> — <one-line description + link>
- <Product B> — <...>

IN PROGRESS (next 30 days):
- <Product C> — <ETA>
- <Product D> — <ETA>

UPCOMING (next 90 days):
- <Product E>
- <Product F>

DEPRECATIONS:
- <Product X> (sunset <DATE>) — see migration guide

USAGE HIGHLIGHTS:
- <X> users on ARR Dashboard (up 12% MoM)
- Top query: total ARR by product (40% of all queries)

FEEDBACK / REQUESTS:
- Add your requests here: <link to backlog>

Office hours: <day/time>
Slack: <channel>

Thanks,
<You>
```

---

## §17. The "managing up" pattern

Your manager / VP needs to know:
- What's in flight
- What's done
- What's blocked
- What you need help with

Use a weekly 15-min 1:1 to communicate this. Be proactive about escalations.

---

## §18. Anti-patterns (PO smells)

- ❌ "I'll prioritize based on who asked most recently"
- ❌ Skipping the KPI Spec to save time
- ❌ Promising delivery without engineering commitment
- ❌ Not communicating deprecations to consumers
- ❌ No usage tracking → no idea if product is even used
- ❌ Quarterly themes that don't align with business OKRs
- ❌ Treating data products as one-time builds (no maintenance budget)
- ❌ Catalog out of date → consumers find broken products

---

## §19. Cross-references

- `kpi-specification-framework.md` — Spec template
- `requirements-to-models-workflow.md` — end-to-end intake
- `metric-governance-and-controls.md` — council ops
- `professional-writing` skill — for memos, status updates
