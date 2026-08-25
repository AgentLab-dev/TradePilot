---
name: professional-writing
description: Professional writing across business, technical, and executive communication — emails, Slack messages, documentation, proposals, status reports, executive summaries, PRDs, RFP responses, Confluence pages, Jira tickets, SOPs, runbooks, blog posts, and LinkedIn content. Use when drafting emails, writing documentation, creating proposals, preparing status updates, writing executive summaries, authoring technical docs, composing Slack messages, or any professional written communication.
---

# Professional Writing Skills

Role: Professional writer and communications specialist — produces clear, concise, audience-appropriate written content across business, technical, and executive contexts.

## Writing Principles

### The 4 C's (apply to everything)

1. **Clear** — One idea per sentence. No ambiguity.
2. **Concise** — Cut every word that doesn't earn its place.
3. **Concrete** — Specific facts, numbers, and examples over vague statements.
4. **Courteous** — Respectful tone matched to audience and context.

### Voice & Tone Guide

| Context | Tone | Example |
|---------|------|---------|
| Executive communication | Direct, confident, data-driven | "Q3 NDR improved 2.1pp to 109.3%, driven by reduced churn in Enterprise." |
| Technical documentation | Precise, neutral, instructional | "The model joins `stg_em_agreement_scd2` on `agreement_id` to resolve the SSR chain." |
| Team/Slack messages | Conversational, action-oriented | "Heads up — the ARR model fix is merged. Can you validate the Q3 numbers?" |
| Client/stakeholder | Professional, solution-oriented | "We've identified the root cause and have a fix ready for deployment this sprint." |
| Proposals/RFPs | Persuasive, evidence-based | "Our approach reduces pipeline processing time by 40% while maintaining full auditability." |

---

## Email Writing

### Structure

```
Subject: [Action Required/FYI/Decision Needed]: [Specific Topic]

[1-2 sentence context — why this email exists]

[Body — organized by priority, not chronology]

[Clear ask or next step]

[Sign-off]
```

### Email Templates

#### Status Update

```
Subject: [FYI] Weekly Status — [Project/Team] — [Date]

Hi [Name/Team],

Summary:
- [Key accomplishment 1]
- [Key accomplishment 2]

In Progress:
- [Item] — [Expected completion]
- [Item] — [Blocker if any]

Needs Attention:
- [Item] — [What's needed and from whom]

Next week:
- [Priority 1]
- [Priority 2]

Let me know if questions.

Best,
[Name]
```

#### Decision Request

```
Subject: [Decision Needed by DATE]: [Topic]

Hi [Name],

Context: [1-2 sentences on why this decision is needed now]

Options:
1. [Option A] — [Pros] / [Cons] / [Impact]
2. [Option B] — [Pros] / [Cons] / [Impact]
3. [Option C] — [Pros] / [Cons] / [Impact]

Recommendation: Option [X] because [reason].

Timeline: Need decision by [date] to meet [deadline/dependency].

Happy to discuss live if helpful.

Best,
[Name]
```

#### Escalation

```
Subject: [Urgent] [Issue] — Impact on [What's Affected]

Hi [Name],

Issue: [One sentence description]
Impact: [Who/what is affected and severity]
Root Cause: [Known or under investigation]
Current Status: [What's been done so far]
Ask: [What you need — decision, resources, approval]
Timeline: [When resolution is needed]

I'll send updates every [frequency] until resolved.

[Name]
```

#### Thank You / Recognition

```
Subject: Kudos — [Person/Team] on [Achievement]

Hi [Name/Team],

Wanted to call out [Person]'s excellent work on [specific achievement].

[1-2 sentences on what they did and why it mattered]

[Impact: saved time, unblocked team, improved metrics, etc.]

Great work — thank you!

[Name]
```

---

## Slack / Chat Messages

### Principles

- **Lead with context** — Don't start with "Hey" and wait. Put the full message in one block.
- **Thread heavy topics** — Keep channels scannable.
- **Use formatting** — Bold for emphasis, bullets for lists, code blocks for technical references.
- **State the ask clearly** — "Can you review by EOD?" not "thoughts?"

### Templates

#### Asking for Help

```
*[Topic] — need help with [specific thing]*

Context: [1-2 sentences]
What I've tried: [What you already did]
What I need: [Specific ask]
Urgency: [By when]

cc @[person] if you have context on this
```

#### Sharing an Update

```
:white_check_mark: *[Feature/Fix] — Done*

- What: [Brief description]
- PR: [link]
- Impact: [What changes for users/team]
- Testing: [How it was validated]

No action needed — FYI only.
```

#### Flagging a Problem

```
:warning: *[System/Process] issue — [severity]*

What's happening: [Description]
Impact: [Who's affected]
Workaround: [If any]
ETA for fix: [If known]

Will update in this thread.
```

---

## Technical Documentation

### Structure for Technical Docs

```markdown
# [Title]

## Overview
[1 paragraph — what this is, who it's for, why it matters]

## Prerequisites
- [Tool/access/knowledge needed]

## Architecture / How It Works
[Diagram or description of the system/flow]

## Step-by-Step Guide
### Step 1: [Action]
[Instructions with code examples]

### Step 2: [Action]
[Instructions]

## Configuration
| Parameter | Default | Description |
|-----------|---------|-------------|

## Troubleshooting
| Problem | Cause | Solution |
|---------|-------|----------|

## FAQ
**Q: [Common question]**
A: [Answer]

## References
- [Link to related doc]
```

### dbt Model Documentation

```markdown
# [Model Name]

## Purpose
[What this model does in 1-2 sentences]

## Grain
One row per [grain description].

## Source Models
- `ref('model_1')` — [What it provides]
- `ref('model_2')` — [What it provides]

## Key Columns
| Column | Type | Description |
|--------|------|-------------|
| `pk_column` | VARCHAR | Primary key |

## Business Logic
- [Rule 1 — what transformation and why]
- [Rule 2]

## Dependencies
- Upstream: [models this reads from]
- Downstream: [models/dashboards that read this]

## Change Log
| Date | Change | Author |
|------|--------|--------|
```

---

## Executive Communication

### Executive Summary

```markdown
# Executive Summary: [Topic]

**Bottom Line:** [The single most important takeaway in one sentence]

## Key Metrics
| Metric | Current | Prior Period | Delta |
|--------|---------|-------------|-------|
| [KPI] | [Value] | [Value] | [+/-] |

## What Happened
[2-3 bullet points — facts only, no opinions]

## What It Means
[2-3 bullet points — interpretation and implications]

## Recommended Action
[1-2 specific actions with owners and timelines]

## Risks
- [Risk] — Mitigation: [approach]
```

### Steering Committee / Leadership Update

```markdown
# [Project] — Leadership Update ([Date])

## Status: [Green/Yellow/Red]

**One-liner:** [Project status in one sentence]

## Progress Since Last Update
- [Milestone achieved]
- [Milestone achieved]

## Upcoming Milestones
| Milestone | Target Date | Status | Owner |
|-----------|-------------|--------|-------|
| [Item] | [Date] | On Track / At Risk | [Name] |

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| [Risk] | High/Med/Low | High/Med/Low | [Action] |

## Asks / Decisions Needed
1. [Specific ask with context]
```

---

## Proposals & RFP Responses

### Proposal Structure

```markdown
# [Proposal Title]

## Executive Summary
[The problem, your solution, expected outcome — in 3-4 sentences]

## Problem Statement
[What pain exists today — use the client's own words/data]

## Proposed Solution
### Approach
[High-level description]

### Scope
| In Scope | Out of Scope |
|----------|-------------|
| [Item] | [Item] |

### Timeline
| Phase | Duration | Deliverables |
|-------|----------|-------------|
| Phase 1 | [Weeks] | [What's delivered] |

## Expected Outcomes
- [Measurable outcome 1]
- [Measurable outcome 2]

## Investment
| Component | Effort | Cost |
|-----------|--------|------|
| [Item] | [Hours/days] | [Amount] |

## Why Us
[2-3 differentiators with evidence]

## Next Steps
[Specific proposed next action]
```

---

## SOPs & Runbooks

### SOP Template

```markdown
# SOP: [Process Name]

**Owner:** [Team/Person]
**Last Updated:** [Date]
**Review Cadence:** [Quarterly/Annually]

## Purpose
[Why this SOP exists — what problem it prevents]

## Scope
[Who this applies to and when]

## Prerequisites
- [Access/tools/permissions needed]

## Procedure

### Step 1: [Action]
- [Detailed instruction]
- Expected result: [What you should see]

### Step 2: [Action]
- [Detailed instruction]
- If [condition]: [Do this instead]

## Verification
- [ ] [Check that confirms process completed correctly]

## Escalation
If [condition], escalate to [person/team] via [channel].

## Revision History
| Date | Change | Author |
|------|--------|--------|
```

---

## Jira / Ticket Writing

### Bug Report

```
**Title:** [Component] — [What's broken] when [Trigger]

**Description:**
**Expected:** [What should happen]
**Actual:** [What happens instead]
**Steps to Reproduce:**
1. [Step]
2. [Step]
3. [Observe error]

**Impact:** [Who's affected, severity]
**Environment:** [Prod/QA/Dev, browser, etc.]
**Screenshots/Logs:** [Attach]
**Workaround:** [If any]
```

### User Story

```
**Title:** As a [role], I want [capability] so that [benefit]

**Acceptance Criteria:**
- [ ] Given [context], when [action], then [expected result]
- [ ] Given [context], when [action], then [expected result]

**Technical Notes:**
- [Implementation guidance]
- [Dependencies]

**Out of Scope:**
- [What this does NOT include]
```

---

## Blog Posts & LinkedIn Content

### Blog Post Structure

```markdown
# [Compelling Title — promise a benefit]

**Hook:** [Opening sentence that creates curiosity or states a bold claim]

## The Problem
[Relatable description of the pain point — 2-3 sentences]

## The Insight
[Your unique perspective or discovery]

## The Approach
[Step-by-step or framework explanation]
[Include code snippets, screenshots, or data if technical]

## Results
[Concrete outcomes with numbers if possible]

## Takeaway
[One-sentence lesson the reader walks away with]

---
*[Bio line / CTA]*
```

### LinkedIn Post Formula

```
[Hook — bold statement or question] (1 line)

[Context — why this matters] (2-3 lines)

[The insight / lesson / framework] (3-5 bullet points)

[Takeaway — one sentence]

[CTA — question to drive engagement]

#[Relevant] #[Hashtags]
```

---

## Editing Checklist

Before delivering any written content:

- [ ] **Lead with the point** — Can the reader get the main message from the first sentence?
- [ ] **Cut filler words** — Remove "just", "actually", "basically", "in order to", "it should be noted that"
- [ ] **Active voice** — "The team fixed the bug" not "The bug was fixed by the team"
- [ ] **Specific over vague** — "Reduced build time by 40%" not "Significantly improved performance"
- [ ] **One idea per paragraph** — Break up dense blocks
- [ ] **Consistent formatting** — Headers, bullets, tables used consistently
- [ ] **Audience-appropriate** — Technical depth matches the reader
- [ ] **Action-oriented close** — Every piece ends with a clear next step or takeaway
- [ ] **Spell-checked** — Names, product names, acronyms correct
- [ ] **Length appropriate** — Emails < 5 sentences for asks; docs as long as needed but no longer

## Constraints

- Match the writer's voice when editing existing content — don't impose a different style.
- Preserve technical accuracy — never simplify to the point of being wrong.
- Ask for audience and purpose if not clear — the same content reads differently for executives vs engineers.
- Default to shorter over longer — the reader's time is the scarcest resource.
- Never use jargon without context when writing for mixed audiences.
