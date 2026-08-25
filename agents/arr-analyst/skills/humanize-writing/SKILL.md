---
name: humanize-writing
description: Rewrite AI-generated or AI-flavored text so it reads like a human wrote it — cut hedging, remove AI tells (em-dashes, "delve", "robust", "leverage", throat-clearing openings), vary sentence rhythm, use contractions, prefer specific over generic, land on a point. Use when the user asks to humanize, de-AI, sound natural, sound less robotic, polish prose, or make writing feel less templated. Apply by default to LinkedIn posts, emails, Slack replies, executive summaries, retro notes, and any external-facing prose.
---

# Humanize Writing

Strip AI tells from prose so it reads like a person wrote it — confident, specific, varied, and grounded.

## When to Apply

Apply automatically when generating or editing:
- LinkedIn posts and articles
- Slack replies, DMs, email drafts
- Executive summaries, retro notes, meeting recaps
- Blog drafts, internal memos
- Any prose meant to be read by a human (not code, not technical reference)

Apply on explicit request when the user says: *humanize*, *de-AI*, *make it sound less robotic*, *make it sound natural*, *less templated*, *polish the prose*, *humanise* (any spelling).

## The Eleven Rules

### 1. Cut throat-clearing openings
Drop "Great question!", "Certainly!", "I'd be happy to", "I'll do my best to", "Let me", and any sentence whose only job is to acknowledge before starting.

**Before**: *"Great question! Let me walk you through this."*
**After**: *"Here's how it works."*

### 2. Kill the AI vocabulary list
Strike or replace these words on sight unless they are technically required:
- *delve*, *navigate*, *leverage*, *robust*, *seamless*, *comprehensive*, *intricate*, *crucial*, *vital*, *paramount*, *pivotal*, *meticulous*, *foster*, *embark*, *unleash*, *unlock*, *empower*, *transformative*, *holistic*, *cutting-edge*, *state-of-the-art*, *in today's fast-paced world*, *in the realm of*

**Before**: *"This robust solution leverages cutting-edge technology to seamlessly empower teams."*
**After**: *"This setup gives the team the data they need without the usual integration work."*

### 3. Em-dash control
AI overuses em-dashes (`—`). One per paragraph maximum. Replace excess with periods, commas, or parentheses. Em-dashes work best when they introduce a punchline or an aside, not as default sentence connectors.

### 4. Vary sentence length
Mix short, medium, and long. AI defaults to uniform medium-length sentences, which feels mechanical. A short sentence after two long ones lands. So does the reverse.

**Before**: *"The pipeline processes data efficiently and delivers reliable outputs that meet business requirements."*
**After**: *"The pipeline runs. It hits the SLA. The numbers tie."*

### 5. Use contractions
*we're, it's, can't, won't, don't, there's, that's, I'll, we'll, you're.*
The exception: regulatory, legal, or formal-policy text where contractions read as too casual.

### 6. Prefer specific over generic
Numbers, names, dates, file paths, and concrete artifacts over abstractions.

**Before**: *"a significant amount of data"* → **After**: *"5.7 million rows"*
**Before**: *"recently"* → **After**: *"on May 12"*
**Before**: *"a downstream consumer"* → **After**: *"`bv_acv_quoteline_new_hierarchy`"*

### 7. Drop hedging templates
*"It's worth noting that..."*, *"It's important to mention..."*, *"One could argue..."*, *"In many cases..."*, *"Generally speaking..."* — all signal lack of confidence. Cut them. State the thing directly.

### 8. Strong verbs
Replace passive constructions and weak verbs with active, specific ones.
- *was deployed* → *shipped*
- *was caused by* → *came from*
- *should be considered* → *consider*
- *is responsible for* → *handles*
- *plays a role in* → *drives*

### 9. No bulleted lists when prose works
AI defaults to bullets. Use bullets when items are genuinely parallel and three or more. For two items, use a sentence. For sequential reasoning, use prose.

### 10. Land on a point — don't trail off
Cut closing phrases that exist only to wrap up: *"Let me know if you have any questions"*, *"I hope this helps"*, *"Feel free to reach out"*, *"In conclusion"*. End on the actual last substantive sentence.

### 11. One opinion per paragraph
Humans state things. AI hedges every claim with three caveats. State the claim, give one piece of evidence, move on.

## Quick Audit Pass

Before sending any prose, scan for:

1. Any word from the AI vocabulary list (rule 2) → replace
2. More than one em-dash per paragraph → replace excess
3. Three consecutive sentences of similar length → break the rhythm
4. Zero contractions across multiple paragraphs → add some
5. Generic nouns ("solution", "approach", "framework", "process") without a specific anchor → make concrete
6. Hedging openers ("It's worth noting", "One could argue") → cut
7. Passive voice in more than ~20% of sentences → flip to active
8. Bulleted list of two items → convert to sentence
9. Closing phrase like "Let me know if..." → delete

## Length Calibration

| Format | Target |
|---|---|
| Slack reply | 1-3 sentences. Period. |
| Email | 4-8 sentences. One ask. |
| Retro / meeting note | Headers + tight paragraphs. Tables for comparisons. |
| LinkedIn post (feed) | 8-15 short lines. Line breaks every 1-2 sentences. |
| LinkedIn article | Sections with clear breaks. Mix of paragraphs and lists. |
| Executive summary | Bottom-line first sentence. ≤5 sentences total. |

## Voice Calibration by Audience

- **Executive**: Direct. Numbers first. Cut every word that doesn't earn its place. No hedging.
- **Peer / engineer**: Specific. Technical when warranted. Confident. Some dry humor OK.
- **External / LinkedIn**: First-person, story-led, lessons concrete. Show the work, don't claim the outcome.
- **Manager 1:1 / coaching reply**: Brief. Receive the message. Don't over-thank. Forward-looking close.
- **Slack DM to senior leader**: Five sentences max. State the ask. Offer to provide more on request.

## Two Demonstration Edits

### Demo 1 — AI version vs Humanized
**AI version**:
> *"It's worth noting that the recent deployment introduced several robust improvements that significantly enhanced the pipeline's overall performance. By leveraging the new caching layer, the team was able to navigate the complexities of the legacy code and ultimately deliver a comprehensive solution. Let me know if you'd like more details!"*

**Humanized**:
> *"The May 12 deploy added a caching layer in front of the legacy CTE. Query times dropped from 90s to under 8s. Happy to share the trace if useful."*

### Demo 2 — Coaching reply
**AI version**:
> *"Thank you so much for taking the time to share this wonderful feedback! I really appreciate the kind words and the coaching that has been provided. I will absolutely continue to embrace the collaborative and mentoring approach, and I'm excited to see what doors this opens. Please feel free to share any additional feedback at any time!"*

**Humanized**:
> *"Thank you, Allison — that means a lot to hear. I appreciate you taking the time to share it, and the coaching that got me here. I'll keep at it."*

## When NOT to Apply

- Code, SQL, configuration files, schemas — leave technical syntax alone
- Legal, compliance, or regulatory text — formality is intentional
- Formal published documentation where corporate voice is required
- Direct quotes from third parties — preserve verbatim

## Self-Check Phrase

When unsure if a passage reads as human, ask: *"Would a busy senior person who is good at writing actually phrase it this way in a Slack message at 4pm on a Thursday?"* If no, edit.
