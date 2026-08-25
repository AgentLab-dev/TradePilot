# Analysis Deliverables

Templates for the deliverables you produce: executive memos, validation
reports, walk-the-numbers decks, ad-hoc analysis spreadsheets.

Each template comes with a structure, a sample, and "when to use".

---

## §1. The one-page executive memo (the workhorse)

**Use when**: stakeholder asks an analytical question and the answer requires more than a Slack reply but less than a deck.

```
═══════════════════════════════════════════════════════════════════════════════
TO:        <Stakeholder name + role>
FROM:      <You>
RE:        <Topic — concise, action-oriented>
DATE:      <YYYY-MM-DD>
═══════════════════════════════════════════════════════════════════════════════

BOTTOM LINE
   <1-2 sentence summary of THE answer>
   <Example: "Q1 FY26 NDR declined from 112% to 108%, driven primarily by 
   Healthcare segment slowdown (-1.8pp) and one large customer downgrade (-1pp).">

KEY FINDINGS
   1. <Finding 1 with number + context>
   2. <Finding 2 with number + context>
   3. <Finding 3 with number + context>

ROOT CAUSE
   <The "why" — what caused the change>

RECOMMENDATION (if applicable)
   <What to do about it — actionable, specific>

CAVEATS
   <Any limitations of the analysis>

DETAIL
   See attached spreadsheet: <link>
   Or reproduce: <link to SQL>

QUESTIONS? Reach out via Slack <@channel>
═══════════════════════════════════════════════════════════════════════════════
```

Length: 1 page. Single-screen email or 1-page PDF.

---

## §2. The validation report

**Use when**: documenting validation cycle results (e.g., after quarter close).

```
═══════════════════════════════════════════════════════════════════════════════
FINANCE METRICS VALIDATION REPORT — <PERIOD>
═══════════════════════════════════════════════════════════════════════════════

EXECUTIVE SUMMARY
   Validation cycle ran <date>.
   Total validations: <N>
   Passed: <N>
   Warnings: <N>
   Failures: <N>

   Overall status: ✓ PASS / ⚠ WARN / ✗ FAIL

   <One sentence: "All metrics are ready for executive reporting" OR 
                  "Hold on Q-close — investigation underway">

───────────────────────────────────────────────────────────────────────────────
VALIDATION DETAIL
───────────────────────────────────────────────────────────────────────────────

V1. ARR WALK BALANCES
   Status: ✓ PASS
   Result: Variance < $1 across all quarters
   SQL: <link>

V2. NDR IN EXPECTED RANGE
   Status: ✓ PASS
   Result: 108% (range: 95-115%)
   SQL: <link>

V3. GRR IN EXPECTED RANGE
   Status: ✓ PASS
   Result: 96.5% (range: 95-100%)
   SQL: <link>

V4. SALES BOOKINGS RECONCILIATION
   Status: ⚠ WARN
   Result: Sales bookings $312M; Finance NEW_LOGO + EXPANSION $305M (variance 2.2%)
   Action: Investigate timing of activation for $7M of deals
   SQL: <link>

V5. CURRENCY VARIANT VALIDATION
   Status: ✓ PASS
   Result: USD_CURRENT vs USD_HIST variance 1.8% (within ±5%)
   SQL: <link>

V6. SSR COVERAGE
   Status: ✓ PASS
   Result: 98% of churn lines SSR-resolved or true churn
   SQL: <link>

V7. SNAPSHOT FRESHNESS
   Status: ✓ PASS
   Result: Latest snapshot: 2026-05-06 (2 days ago)
   SQL: <link>

V8. CATEGORY COVERAGE
   Status: ✓ PASS
   Result: 0 uncategorized lines

V9. METRIC REASONABLENESS
   Status: ✓ PASS
   Result: Total ARR $7.5B, account count 12,400, avg/line $32k — all in range

V10. SIGMA DASHBOARD MATCH
    Status: ⚠ WARN
    Result: Top 5 dashboards match within $1; ARR by Industry dashboard 
            shows $5M lower (under investigation)
    Action: Sigma cache may be stale; refresh in progress

───────────────────────────────────────────────────────────────────────────────
ACTIONS REQUIRED
───────────────────────────────────────────────────────────────────────────────

1. Investigate V4 variance: $7M timing difference — Sara to check
2. Refresh Sigma ARR by Industry dashboard cache — Pat to action
3. Schedule re-validation tomorrow once both addressed

───────────────────────────────────────────────────────────────────────────────
APPENDICES
───────────────────────────────────────────────────────────────────────────────

A. Full SQL for each validation: <link to scripts>
B. Historical validation results: <link>
C. Reconciliation workbook: <link to Excel>

═══════════════════════════════════════════════════════════════════════════════
```

Sent to: Finance leadership, FP&A, Data Engineering, Functional Architect.

---

## §3. The "walk the numbers" deck

**Use when**: walking finance team through quarter-end numbers in a 30-min meeting.

```
SLIDE 1: AGENDA
   - Total ARR walk (Q1 FY26)
   - Category breakdown
   - Notable drivers
   - Q&A

SLIDE 2: TOTAL ARR WALK
   BEGIN_ARR (FY25 close):   $X.X B
   + NEW_LOGO                +$X M
   + EXPANSION               +$X M
   - CHURN                   -$X M
   - CONTRACTION             -$X M
   ± SKU_CHANGE              ±$X M
   ─────────────────────────────────
   END_ARR (Q1 FY26):         $X.X B
   
   Y/Y growth: X% | Q/Q growth: X%

SLIDE 3: KEY CATEGORY DRIVERS
   NEW_LOGO: $X M (vs $Y prior; ↑ X%)
      - Top new logos: <list top 3>
   
   EXPANSION: $X M (vs $Y prior; ↑/↓ X%)
      - Top expansion: <list top 3>
   
   CHURN: $X M (vs $Y prior; ↑/↓ X%)
      - Material churns: <list top 3 with reasons>

SLIDE 4: BY PRODUCT
   HCM: $X B (X% of total) — NDR Y%
   Adaptive: $X B (X% of total) — NDR Y%
   Spend: $X B (X% of total) — NDR Y%
   <other products>

SLIDE 5: BY SEGMENT
   Enterprise: $X B (X%) — NDR Y%
   Mid-Market: $X B (X%) — NDR Y%

SLIDE 6: FX IMPACT
   USD_CURRENT total: $X.X B
   USD_HIST total: $X.X B
   FX impact: ±$X M (X%)

SLIDE 7: NOTABLE CALLOUTS
   1. <Insight 1>
   2. <Insight 2>
   3. <Insight 3>

SLIDE 8: Q&A
```

Length: 8-12 slides, 30-min walk-through.

---

## §4. The ad-hoc analysis spreadsheet

**Use when**: stakeholder wants the data in Excel for their own slicing.

Structure:
- **Sheet 1: SUMMARY** — top-line numbers, key takeaways
- **Sheet 2: DATA** — the raw analysis data (sortable, filterable)
- **Sheet 3: METHODOLOGY** — how the data was sourced, definitions, filters
- **Sheet 4: SOURCE_SQL** — the SQL used

Pattern:
```
Sheet 1: SUMMARY
========
A1: Analysis: <Topic>
A2: Date: <YYYY-MM-DD>
A3: Owner: <You>

A5: Key Findings
A6: 1. <Finding>
A7: 2. <Finding>
A8: 3. <Finding>

A10: Total accounts in analysis: <N>
A11: Total ARR in analysis: <$N>
A12: Currency variant: <USD_CURRENT>
A13: as_was_date: <YYYY-MM-DD>
```

Always include the SQL — auditability matters.

---

## §5. The "variance investigation" memo

**Use when**: explaining why two numbers differ.

```
TO:        <Recipient>
FROM:      <You>
RE:        Variance Investigation: <Metric A> vs <Metric B>
DATE:      <YYYY-MM-DD>

QUESTION ASKED
   "<The specific question, e.g., 'Why does Sigma show $312M ARR but the
   board deck shows $315M?'>"

INVESTIGATION SUMMARY
   - Reproduced both numbers from canonical source
   - Decomposed the difference
   - Identified <N> contributing factors

RESULTS

   Number A: $312M (Sigma "Total ARR" dashboard)
     Source: FINANCE_PROD.DATA_PRODUCTS.ARR_TOTAL_DASH
     Filter: as_was_date = '2026-05-06', is_arr_eligible = TRUE, USD_CURRENT
     SQL: <link>

   Number B: $315M (Board deck Q1 FY26)
     Source: Manual snapshot from FY26Q1-close.xlsx
     Filter: as_was_date = '2026-04-30', is_arr_eligible = TRUE, USD_HIST
     Captured: 2026-05-03

   Difference: $3M

ATTRIBUTION
   1. FX revaluation: $2.5M
      Sigma uses USD_CURRENT (current FX rates).
      Board deck used USD_HIST (FX locked at quarter close).
      Between 4/30 and 5/06, USD weakened slightly → USD_CURRENT lower.

   2. Pilot inclusion: $0.5M
      Sigma applies is_arr_eligible = TRUE filter (excludes pilots).
      Board deck excluded pilots AND certain internal accounts that 
      Sigma doesn't filter.

CONCLUSION
   Both numbers are correct for their intended purpose:
   - Sigma: live operational view (FX revalued)
   - Board deck: point-in-time snapshot (FX locked)

RECOMMENDATION
   Add explanatory note to Sigma dashboard:
   "Total ARR shown in USD_CURRENT; differs from quarter-close USD_HIST 
   number by FX revaluation. See <link> for reconciliation."

QUESTIONS? Reply or Slack.
```

---

## §6. The "deep-dive" analysis (multi-day investigation)

**Use when**: large-scope analysis requested (e.g., "explain why Healthcare ARR is declining").

Structure:
1. **Question framing** (1 page)
2. **Hypothesis + data plan** (1 page)
3. **Findings** (3-5 pages)
4. **Root cause** (1 page)
5. **Recommendation** (1 page)
6. **Methodology + data sources** (appendix)

Length: 8-15 pages. Distributed as PDF.

---

## §7. The "you asked, here's the answer" Slack reply

**Use when**: 5-minute answer to a Slack question.

```
@username — Here's what I found:

HCM ARR right now: $1.2B USD_CURRENT
  - Source: FINANCE_LINE_ANALYTICS as of 2026-05-06
  - 1,243 active accounts
  - +12% Y/Y, +3% Q/Q

Reproduce: <link to query>

Let me know if you want it sliced further.
```

Crisp. Cite source. Offer next step.

---

## §8. The "I'm sending this to a non-data person" pattern

When sending to finance leaders who aren't SQL-fluent:

- **Don't** include SQL in the body — link to it instead
- **Don't** use jargon like "primary key", "incremental", "SCD2"
- **Do** use business terms: "active customers", "active contracts"
- **Do** include visuals (charts, tables) over text
- **Do** lead with the number, not the methodology

Translation guide:
- "ARR at line grain" → "annualized recurring revenue per contract line"
- "is_arr_eligible = TRUE" → "excludes pilots and one-time fees"
- "USD_HIST" → "historical FX (matches what's in our financial statements)"
- "as_was_date" → "snapshot date"
- "SCD2 lookup" → "as-of-that-date account details"

---

## §9. The reproducibility footer (standard template)

Every analysis includes a reproducibility footer:

```
───────────────────────────────────────────────────────────────────────────────
REPRODUCIBILITY
───────────────────────────────────────────────────────────────────────────────

Data source:        FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS
Snapshot:           2026-05-06
Currency:           USD_HIST
Filters:            is_arr_eligible = TRUE
Generated:          2026-05-08 14:30 UTC
SQL:                <link>
Analyst:            <You>
───────────────────────────────────────────────────────────────────────────────
```

So anyone can re-run and re-verify.

---

## §10. The "I delivered something wrong" recovery

When you discover post-delivery that your analysis had a bug:

1. **Confirm the bug** before notifying
2. **Quantify the impact**: how wrong was it?
3. **Notify the stakeholder immediately**:
   ```
   Hi <name> — I need to flag a correction to my <date> analysis on <topic>.
   
   I discovered <bug description>.
   
   Impact: <revised number> vs original <wrong number>.
   
   Updated analysis attached. I apologize for the confusion.
   ```
4. **Send corrected deliverable**
5. **Document for future**: what process change prevents recurrence?

Never hide or downplay. Acknowledge, correct, learn.

---

## §11. Cross-references

- `profiling-validation-playbook.md` — analysis underpinnings
- `stakeholder-communication.md` — communication style
- `professional-writing` skill — broader writing guidance
- `finance-functional-analytics/metric-recipes.md` — query templates
