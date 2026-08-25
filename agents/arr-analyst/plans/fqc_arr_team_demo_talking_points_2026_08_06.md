# FQC-ARR Team Demo — Talking Points (Aug 6, 2026)
**~30 min | Audience: wider team | Goal: show the agent as a team multiplier, not a personal showcase**

---

## MENTOR BRIEF — read before you walk in (2 min)

**Win condition:** People leave thinking *“this removes grind I hate, keeps judgment with me, and I can use it.”* Not *“Kote built something that replaces us.”*

**Delivery stance**
- Speak as **we / the team / the agent** — not “I built an autonomous AE.”
- Lead with **pain they feel** (close recon, RCA, PR overhead), then the agent.
- Pause after each section. Invite one question before the next.
- Pick **one live demo** only (A or B). Don’t chase all four options.
- If someone pushes “will this replace AEs?” — go straight to Q&A row #1 and the judgment line.

**Do not**
- Lead with architecture diagrams or lesson counts
- Say “two-person team” as if the rest of the pod didn’t matter — frame as *small delivery core + agent for cognitive load*
- Overclaim “ran the entire refactoring” — say *drove investigation, validation, docs, monitoring; humans owned judgment and SQL*
- Relitigate QCI / siloed working / P5 — this room is not that conversation

**Credit line if asked who built it**
> “I drove the build. The point of today is the pattern the team can reuse — not the authorship.”

---

## TIMING MAP

| Block | Time | Section |
|---|---|---|
| Open | 2 min | Pitch |
| 1 | 3 min | What it is / isn’t |
| 2 | 6 min | How it helped ARR refactoring |
| 3 | 5 min | Close without tribal knowledge |
| 4 | 4 min | Productivity multiplier |
| 5 | 4 min | How it evolved + architecture (light) |
| Live demo | 4 min | Pick ONE |
| Close + Q&A | 2+ min | Close, then open floor |

---

# TALKING POINTS (say these)

## OPEN — 2 min

**One breath pitch**
- Biggest finance ARR refactor in recent memory: monolithic query → **85+ modular models**
- Ran **in parallel with live close** — **4 quarter closes, zero miss**
- Small delivery core; the agent carried **investigation, validation, documentation, monitoring**
- Humans kept **judgment** — metric design, stakeholder calls, what ships
- Today: what it is, what it did, how you can use it

**Land line**
> “Too important to skip. Too repetitive to enjoy. That’s the work AI should take.”

*(pause — “Any questions on scope before I go deeper?”)*

---

## 1. WHAT THIS AGENT IS — 3 min

**Problem (their week, not your architecture)**
- Refresh ARR / ACV / NRR / GRR for a snapshot
- Tie out to Salesforce + production baselines
- Reconcile Sigma vs Snowflake vs certified
- RCA through a large DAG
- Write Jira, open PRs, watch CI/CD, hand to QA

**What it is**
- **FQC-ARR** = Finance ARR Quarter Close agent
- **Supervisor + specialist sub-agents** (ticket lifecycle + scheduled close)
- Works **intake → validate → test → PR → CI/CD → QA handoff**
- **Pauses where human judgment matters** (writes, unclear requirements, implementer boundary)

**What it is NOT**
- Not a chatbot
- Not a replacement for AE decisions
- Not a static script that rots
- Not an island tool — Jira, Snowflake, dbt, GitHub, Slack, Sigma

**One-liner (memorize)**
> “A senior AE workflow for the full ticket lifecycle — pausing only where human judgment actually matters.”

---

## 2. HOW IT HELPED THE ARR REFACTORING — 6 min

**Glance numbers (say slowly)**
- **5 months** (Nov 2025 – Apr 2026)
- **85+** files / models / macros / YAML
- **27** reusable Snowflake TVFs
- **8+** PRs, CI-validated
- **6** critical prod hotfixes during the work
- **4 closes** supported — **zero disruptions**
- Tie-out tolerance **&lt; $1** across aggregation levels

**Where the agent earned its keep**
1. **Parity at scale** — automated old vs new / prod vs dev tie-outs, not ad-hoc SQL each time
2. **RCA in minutes** — e.g. **$51.8M “backwards term”** traced to the exact CASE; proved **correct business behavior**, avoided a bad “fix”
3. **Hotfix cycle** — weeks → **&lt; 48 hours**; validate vs prod baselines before PR
4. **PR assurance** — NRR/GRR wiring, Copilot triage, PII scan, findings on PR + Jira
5. **CI/CD + comms** — Slack heartbeats, Jira write-backs under close pressure

**Bottom line**
> “We rewrote the critical finance pipeline in five months while supporting four closes. The agent handled investigation, validation, documentation, and monitoring. We handled the judgment calls.”

*(pause)*

---

## 3. CLOSE WITHOUT TRIBAL KNOWLEDGE — 5 min

**Context (careful wording)**
- Institutional knowledge used to live in people’s heads — why a CASE exists, SKU swap rules, SSR edge cases
- As people transitioned, that was a **business risk**, not a personality story

**How the agent filled the gap**
1. **Read the codebase** — lineage, macros, CTEs, joins → Salesforce → staging → int → aggregates → dashboards
2. **Captured lessons** — **353** verified; **28** promoted; examples: SSR mapping, sku_swap fiscal-quarter matching, MCP one-statement rule
3. **Same close workflow every time** — refresh → 7-check recon → baseline compare (Scheduled Mode)
4. **New bugs, same method** — e.g. **NVIDIA XTND** (EDAEM-3856): SKU Conversion → Contraction, not Product Churn; validated across **dev / qa / prod**; QA confirmed same day

**Impact line**
> “It didn’t just fill a knowledge gap — it created a knowledge asset. Edge cases, RCAs, and fixes get recorded, verified, and reused. Knowledge compounds every close.”

---

## 4. PRODUCTIVITY MULTIPLIER — 4 min

**Before → after (pick 4 to say out loud)**
- Quarter-close recon: **2–3 days → ~4 hours (~80%)**
- PR impact analysis: **30–60 min → ~5 min (~85%)**
- Sigma ↔ Snowflake variance: **2–4 hrs → 10–20 min (~90%)**
- Prod RCA: **hours/days → minutes (~95%)**
- Knowledge capture: **often skipped → automatic (353 lessons)**
- New AE ramp: **4–6 weeks → 1–2 weeks (~70%)**

**Why multiplier, not just a tool**
- Compounds (lessons grow)
- Doesn’t sleep (scheduled close + CI monitors)
- Documents in the team’s places (Jira / PR / Slack)
- Catches silent drift (e.g. small NRR variance live for months)
- Frees AEs for **judgment** — design, stakeholders, strategy

**Pattern line**
> “Agent takes repetitive cognitive load. Judgment stays with the AE. That’s the multiplier — not replacing the analyst, removing what blocked the work leadership actually needs.”

---

## 5. EVOLUTION + ARCHITECTURE (LIGHT) — 4 min

**Timeline in 5 beats**
1. **Nov 2025** — Cursor rules / skills for ARR close
2. **Jan 2026** — MCP live (Snowflake, dbt, SFDC, Sigma)
3. **Mar 2026** — Supervisor + sub-agents (full ticket lifecycle)
4. **May 2026** — Lesson store + daily reflection
5. **Aug 2026** — Full E2E + learning loop in production use

**Architecture — one sentence each**
- **Supervisor** = deterministic Python (state, dispatch, gates) — not an LLM free-for-all
- **~12 specialists** = intake → requirements → validate → clarify → implement → test → PR → CI → CD → QA
- **Only a few roles use LLM**; rest are deterministic
- **Smart gates** = pause before writes / unclear requirements
- **Memory** = lesson store + thinking logs

**Agent vs script (say 3 contrasts)**
- Adapts to the ticket vs fixed logic
- Learns (lessons) vs same every run
- Pauses for judgment vs all-or-nothing automation
- Posts in Jira/Slack/GitHub vs log file only

**Portability (if leadership / other domains in room)**
> “Same Supervisor + specialists + lessons pattern. New domain = new specialists + new lesson store. Safety model and learning loop stay.”

---

## LIVE DEMO — pick ONE — 4 min

**Option A (safest): thinking log**
- Show pause at clarifier / write gate
- Line: *“Watch where it stops — it won’t post to Jira without approval.”*

**Option B: ticket run (if CLI ready)**
- `fqc-arr --ticket EDAEM-3856 --mode ticket --no-slack --json`
- Point at roles complete + smart-gated pause

**Option C: lessons**
- “353 lessons, 28 promoted — verified against production.”

**Option D: Jira comment on EDAEM-3856**
- RCA structure: root cause, affected lines, expected behavior, validation table

**If demo fails:** skip to Closing. Don’t debug live for more than 60 seconds.

---

## CLOSE — 1 min

> “Started as Cursor rules for the ARR refactor. Evolved into an agent that supported four closes, helped ship hotfixes, cut RCA from days to minutes, and built 353 verified lessons that didn’t exist before.”
>
> “The refactoring is done. The agent isn’t. It compounds every run. That’s the multiplier.”

**Invite**
> “Happy to walk anyone through a ticket run after this — or take questions now.”

---

# Q&A — SHORT ANSWERS

| If they ask… | Say… |
|---|---|
| Does it edit prod code alone? | **No.** Implementer is a human boundary. Agent stages, tests, PRs, documents. SQL lands with human ownership. |
| Hallucinations? | Lessons verified vs prod commits; stale ones archive; debugger proposes, doesn’t write; writes are gated. |
| Authorization? | Default **smart_gates** — pause before writes. `full_auto` is opt-in. Same review bar as a junior PR. |
| Unclear requirements? | Clarifier asks (terminal → Slack → Jira). **Never guesses.** |
| Other teams? | Yes — domain-agnostic pattern. New domain agent ~**4–6 weeks**. |
| SOX / audit? | Read-mostly default; thinking logs; recorded Jira/Slack/PR; no prod write outside change control. |
| Cost? | ~**$30–50/mo** API; ROI framed as AE hours returned (~**150x** if they press). |
| What’s next? | SANA / Workday agent runtime, parallel close, self-healing pipelines, Marketing + Sales domains. |
| Will this replace AEs? | **No.** It removes grind so AEs do judgment, design, and stakeholder work. That’s the job getting better, not smaller. |
| Who owns it if you’re out? | Lessons + runbooks + gates are the durability play. Next step is pairing so more people can trigger and review runs. |

---

# EXECUTIVE / PRESENTATION VOCABULARY (use these)

Ten high-standard words. Use **one per section max** — they elevate you; stacking them sounds like a deck.

| Word | Say it like this (in your talk) | Avoid sounding like |
|---|---|---|
| **Mandate** | “The mandate of the agent is repetitive cognitive load — not AE judgment.” | “The agent does stuff.” |
| **Operating model** | “This is an operating model for close and ticket work, not a one-off demo.” | “Here’s a cool tool.” |
| **Governed** | “We moved ARR onto a governed platform with audit-ready validation.” | “We cleaned up the code.” |
| **Defensible** | “Finance gets a defensible number — tied to source and baselines.” | “The numbers look good.” |
| **Institutional knowledge** | “We turned tribal knowledge into institutional knowledge that compounds.” | “People used to know this.” |
| **Force multiplier** | “This is a force multiplier for the AE — same judgment, less grind.” | “It makes us faster.” |
| **Blast radius** | “We contain blast radius — validate before PR, dual-run before cutover.” | “We try not to break things.” |
| **Durable** | “The durable outcome isn’t the PR — it’s the lesson store and the standards.” | “We built something cool.” |
| **Accountability** | “Accountability stays with the AE — smart gates pause where humans must decide.” | “AI does it for us.” |
| **Adoption** | “Success is adoption by the team — not authorship of the agent.” | “I built this.” |

**Three executive phrases (optional openers / bridges)**
- “At the business level…”
- “The outcome that matters for Finance is…”
- “What this changes for the team is…”

**Self-presentation lines (high standard, not self-promoting)**
- “I’ll keep this at the outcome level, then show one live proof.”
- “I’ll separate judgment work from automation — that boundary is intentional.”
- “Happy to go deep on architecture offline; today I’ll stay on impact and how you use it.”

---

# CHEAT CARD (glance mid-talk)

| Prompt | Line |
|---|---|
| What is it? | Full ticket lifecycle AE agent; pauses for judgment |
| Proof | 85+ models · 4 closes · &lt;$1 tie-out · RCA minutes |
| Multiplier | 80% close recon · 95% RCA · 353 lessons |
| Trust | Smart gates · no solo prod SQL · audit logs |
| Close | Refactor done · agent compounds · judgment stays human |
| Vocab | mandate · operating model · governed · defensible · force multiplier |

---

# POST-DEMO MOVE (mentor)

Within 24 hours:
1. Drop a short Slack follow-up: link to demo doc + “office hours / pair on one ticket this week”
2. Offer **one** volunteer a guided run (don’t flood the channel)
3. If leadership asks for reuse — reply with “4–6 weeks for a domain agent” + ask which domain first

**Reputation protection:** keep follow-ups about *team access*, not *your invention*.
