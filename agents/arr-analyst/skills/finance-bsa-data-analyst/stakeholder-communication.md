# Stakeholder Communication — Finance Speak ↔ Data Speak

Finance stakeholders don't speak SQL. Engineering doesn't speak GAAP. You
are the translator. This doc covers the patterns for translating between
worlds.

---

## §1. The audience-tone map

| Audience | Tone | Format |
|---|---|---|
| **CFO** | Bottom-line first; minimal jargon; numbers + recommendation | 1-page memo or 5-line Slack |
| **VP FP&A** | Technical-but-business; comfortable with definitional nuance | Memo with appendix, deck for monthly |
| **Controller** | Precise; audit-ready; reference SOX impact if any | Documented memo + reconciliation |
| **CRO** | Action-oriented; sales-relevant framing | Bullet points; action items emphasized |
| **CMO** | Marketing-attribution-relevant; visual | Dashboard demo + memo |
| **CS leadership** | Customer-impact-focused | Account-level details + narrative |
| **IR Director** | Disclosure-aware; consistent with public statements | Reconciled, audit-friendly |
| **Data engineering peer** | Technical; assume context | Slack thread; SQL inline |
| **Sales Ops** | Operational; deal-motion-aware | Process-flow + numbers |

Calibrate per recipient.

---

## §2. The translation glossary

| Data speak | Finance speak | Notes |
|---|---|---|
| Grain | "Per what — per customer, per contract, per month?" | Define when first used |
| Primary key | "Unique identifier" | Or just "ID" |
| as_was_date | "Snapshot date" / "as of date" | Whichever finance uses |
| SCD2 | "Historical record" / "Versioned" | Don't say "Slowly Changing Dimension Type 2" |
| Materialization | "How the data is stored" | Often not needed |
| Ephemeral | "Calculated on-the-fly" | When relevant |
| Categorization UDTF | "The categorization logic" | UDTF is internal jargon |
| ARR walk balances | "The math adds up" | More relatable |
| Cluster key | "Indexed on..." | Approximation |
| Incremental merge | "Updated daily" | When time-relevant |
| dbt project | "Our data pipeline" | Project name when needed |
| Snowflake credits | "Cloud computing cost" | Or "data warehouse usage" |
| USD_CURRENT | "Today's FX rates" | |
| USD_HIST | "Historical FX rates (period-locked)" | |
| USD_ACTUAL | "Local currency" | |
| is_arr_eligible | "Recurring revenue eligible (excludes pilots / one-time)" | |
| SSR | "Renewal mechanism through Apttus" | Less acronym-heavy |

---

## §3. The "explain a complex thing" pattern

When explaining a complex technical concept to a finance partner:

1. **Start with WHY**: why does this matter for their work?
2. **Use ANALOGY**: connect to something they know
3. **Show the BUSINESS impact**: what changes in their reporting?
4. **Then the HOW**: only if they want detail

Example — explaining "as-was date":
```
WHY: When we report ARR, we have to pick a snapshot date — the data 
changes daily as contracts come in, so we need to "freeze" the view at 
a specific date.

ANALOGY: Like taking a photo of your bank statement on the last day 
of the month — that's the official month-end number, regardless of 
what happens the next day.

IMPACT: Reports use Q-close snapshots (e.g., 2026-05-06 for Q1 FY26 
close). Live dashboards may show different numbers from the previous 
Friday — that's intentional.

HOW (if asked): We snapshot weekly on Friday close. Our official Q-end 
snapshot is the first Friday after the fiscal quarter end.
```

---

## §4. The "be confident, but honest about uncertainty" balance

When delivering analysis:
- Be **confident** about numbers you've validated
- Be **honest** about what's uncertain ("This is a directional estimate" or "I'm 90% confident in this number")
- **Never** fake confidence

Phrases:
- ✓ "Total ARR is $7.5B"
- ✓ "Likely $X based on current trends — final number Q-close"
- ✓ "Approximately $X — I'm reconciling with one more source"
- ✗ "Probably about $X" (vague + unprofessional)

---

## §5. The "saying no" pattern

When you can't deliver what's asked:

| Reason | How to say it |
|---|---|
| Out of capacity | "I can do this, but not until <date>. Or I can defer X to make room." |
| Wrong canonical | "This question is better answered with <other dashboard>. Let me point you there." |
| Not feasible | "The data we'd need doesn't exist in our systems. We'd need to build it first." |
| Should be productized | "This is a great question that 3 other teams have asked. Let me escalate to the Functional Architect to formalize this metric." |
| Outside scope | "This is more of a <other domain> question. Let me connect you with <other analyst>." |

Always offer a path forward. Never just "no".

---

## §6. The "asking for clarification" pattern

When the ask is ambiguous, don't guess. Ask:

```
Hi <name>, before I run this:

I want to make sure I get the right answer. A few clarifications:

1. By "Healthcare ARR", do you mean:
   (a) Accounts where industry = 'Healthcare' (per our SCD2 dimension)
   (b) Specific list of accounts you have in mind
   (c) Healthcare-specific products only

2. As of when — latest snapshot (currently 2026-05-06) or Q1 close (2026-04-30)?

3. Currency: live FX (USD_CURRENT) or quarter-end (USD_HIST)?

Once I have these, I'll have an answer in <X hours>.

Thanks!
```

Front-loaded clarification saves rework.

---

## §7. The "walk through the numbers" meeting structure

When walking finance through a quarter-close validation (30-60 min):

```
0:00 - 0:05  Welcome + agenda
0:05 - 0:15  Total ARR walk (begin → end)
0:15 - 0:25  Category breakdown (where ARR moved)
0:25 - 0:35  Notable drivers (top contributors)
0:35 - 0:45  Caveats + open items
0:45 - 0:60  Q&A
```

Live shared screen with SQL/Sigma — not a deck. Live execution is convincing.

---

## §8. The "I have bad news" pattern

When numbers are worse than expected (e.g., NDR declined):

1. **Lead with the number** — don't soften
2. **Show the math** — make it indisputable
3. **Attribute** — where did the decline come from?
4. **Context** — is this temporary or structural?
5. **Recommendation** — what's the path forward?
6. **Acknowledge emotion** — "I know this is concerning..."

Don't bury, don't dramatize. Be clinical + actionable.

---

## §9. The "managing expectations" pattern

When you commit to a delivery:
- Quote a date conservatively (under-promise, over-deliver)
- Communicate ETA changes early — never miss without warning
- If you hit a blocker, share immediately

Example:
```
Hi <name>, quick update on the analysis I committed to deliver Friday:

I hit an unexpected complication — the data I need from System X 
isn't refreshing as expected. I'm working with the data engineering 
team on a fix.

Realistic new ETA: Monday EOD.

If you need a directional answer Friday, I can provide that with a 
caveat. Otherwise, Monday for the polished version. Your call.
```

Honest + clear + options. Respects their time.

---

## §10. The "follow up properly" pattern

After delivering an analysis:

1. **Confirm receipt** — make sure they got it
2. **Offer to walk through** — 15 min discussion
3. **Check in later** — "did this answer your question?"
4. **Capture lessons** — if they had follow-up questions, did you miss something?

Don't disappear after sending. Closing the loop builds trust.

---

## §11. The "tone for difficult situations" patterns

### When stakeholder is wrong
```
"Great question. Let me dig in.
[after investigation]
"I see what you're thinking — the number in <their source> reflects 
<X>, while the canonical answer is <Y>. The difference is because 
<root cause>. Both are technically correct for their purpose; the 
canonical we should use for <decision> is <Y> because <reason>."
```

Never make them feel stupid. Anchor on data + context.

### When you're under pressure
```
"I want to make sure I give you the right answer, not just a fast one.
Realistic timeline: <X hours>. Want me to send a directional answer 
in 30 min while I refine?"
```

Don't let pressure drive sloppy work.

### When asked to interpret beyond the data
```
"The data shows <X>. The interpretation depends on <factors I can't 
quantify>. My read is <Y>, but you and <stakeholder> have better 
context for the final interpretation."
```

Share data; let business own interpretation.

### When you've made a mistake
```
"I made an error in <prior analysis>. The corrected number is <X>, 
not <Y>. I apologize for the confusion. Here's what I'm doing to 
prevent recurrence: <process change>."
```

Acknowledge clearly. Don't make excuses.

---

## §12. The "build relationships, not just transactions" mindset

Stakeholders work with you for years. Invest in:
- Learning their domain (read what they read; sit in their meetings)
- Anticipating their needs (proactive suggestions)
- Trust-building (honesty over speed)
- Mutual respect (their work matters)

Transactional analysts get more transactions. Relational analysts get strategic work.

---

## §13. The Slack hygiene

| Practice | Why |
|---|---|
| Use threads for follow-ups | Keeps channel scannable |
| @-mention sparingly | Respects attention |
| Use code blocks for SQL | Readable |
| Link to long content (Confluence / Docs) | Don't paste war + peace |
| Use status emojis (✓ ⚠ ✗) | Quick scanning |
| Acknowledge receipt | "Got it, looking now" |

---

## §14. The "documenting recurring asks" pattern

When you find yourself answering the same question repeatedly:

1. **Document it** — Confluence FAQ or canonical SQL snippet
2. **Share the link** when asked again
3. **Escalate** to Functional Architect if it should be productized
4. **Train colleagues** — sometimes the asker is a team that should self-serve

Pattern: every 3rd time = productize candidate.

---

## §15. Cross-references

- `analysis-deliverables.md` — deliverable templates
- `profiling-validation-playbook.md` — analytical patterns
- `professional-writing` skill — broader writing
- `finance-functional-analytics` skill — when to escalate definitional questions
- `finance-functional-architect` skill — when to escalate metric productization
