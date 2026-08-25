# Domain — Marketing

Owner: GTM Analytics Engineering team (shared with Sales).
Project: `eda-dbt-gtm` (writes to `MARKETING_PROD` + `MARKETING_INT_PROD`).
Primary sources: Marketo, Bizible, Salesforce (Lead/Campaign/Contact).

---

## §1. What this domain owns

| Area | Examples |
|---|---|
| Lead & MQL | Lead lifecycle, MQL scoring, lead source rationalization |
| Campaign | Campaign performance, email open/click, event registrations |
| Attribution | Bizible multi-touch, first-touch, last-touch, contact-role attribution |
| ABM | Account-based marketing, target account scoring, ABM penetration |
| Pipeline influence | Marketing-sourced pipeline, marketing-influenced pipeline, ROI |
| Web analytics | Form fills, page views, content engagement |
| Brand / awareness | Reach, impressions, share of voice (sometimes external feeds) |

What this domain does NOT own:
- ❌ Pipeline / opportunity reporting — that's `domain-sales-gtm.md`
- ❌ Customer success / health — that's `eda-dbt-cx`
- ❌ Product usage analytics (engagement post-purchase) — that's `eda-dbt-cx`
- ❌ Revenue recognition — that's Finance

---

## §2. Source systems

| System | Connector | Refresh | Primary tables |
|---|---|---|---|
| **Marketo** | Fivetran | 1 hr | `LEAD`, `ACTIVITY_EMAIL_SEND`, `ACTIVITY_EMAIL_OPEN`, `ACTIVITY_EMAIL_CLICK`, `ACTIVITY_FILL_OUT_FORM`, `CAMPAIGN`, `PROGRAM`, `PROGRAM_MEMBER` |
| **Bizible** | Fivetran | 1 hr | `TOUCHPOINT` (attribution), `STAGE_CONVERSION` |
| **Salesforce** | (shared with sales) | 1 hr CDC | `LEAD`, `CAMPAIGN`, `CAMPAIGNMEMBER`, `CONTACT`, `MQL__C` |
| **Drift / 6Sense** | Fivetran | 4 hr | Chat conversations, intent data |
| **Eloqua** (legacy) | Fivetran | Daily | Used by legacy programs; migrating to Marketo |
| **Google Sheets** | Fivetran | 15 min | `REF_CAMPAIGN_BUDGET`, `REF_PROGRAM_HIERARCHY` |
| **Adobe Analytics** | Custom (S3 drop) | Daily | Web analytics (page views, sessions) |

---

## §3. The Marketo → Salesforce → Opportunity flow

```
[Anonymous web visitor]
        │
        │  Forms / content download / event registration
        ▼
[Marketo Lead created]                  ← captures source = "Web", campaign attribution
        │
        │  Lead nurtured via campaigns; scored by Marketo
        ▼
[Marketo Lead MQL]                       ← MQL threshold hit (lead score > 80, etc.)
        │
        │  Marketo syncs to SFDC (every 5 min via API)
        ▼
[SFDC Lead created or matched]
        │
        │  SDR qualifies → "Accepted" → Lead becomes Contact + opp created
        ▼
[SFDC Opportunity created]               ← `lead_source` field captures FIRST-touch
        │
        │  Bizible captures every touch along the way (multi-touch)
        ▼
[Closed Won / Lost]
        │
        │  Attribution: Bizible re-runs nightly to redistribute attribution
        ▼
[Reported in attribution dashboards]
```

---

## §4. Attribution models — the 4 industry-standard

Bizible (and most marketing analytics tools) provides 4 attribution models:

| Model | Logic | Use case |
|---|---|---|
| **First-touch** | All credit to first touchpoint | "What's bringing new leads in?" |
| **Lead conversion** | All credit to touch at lead→contact conversion | "What's converting leads?" |
| **Opportunity creation** | All credit to touch at opp creation | "What's creating pipeline?" |
| **W-shaped (multi-touch)** | 30% first / 30% lead conversion / 30% opp creation / 10% all others | Balanced view |
| **U-shaped** | 40% first / 40% lead conversion / 20% middle | Older variant |
| **Linear** | Equal credit across all touches | Pure multi-touch |
| **Time-decay** | More credit to recent touches | "What closed the deal?" |

Bizible touchpoints land in `BASE_PROD.BIZIBLE.TOUCHPOINT` with one row per (opp, touch, attribution_model, credit_percentage).

---

## §5. Marketing-sourced vs Marketing-influenced

Two **very different** definitions:

### Marketing-sourced pipeline
"The opp would not exist without marketing." Strictest definition.

Logic: `lead_source IN (marketing-attributable list)` AND `bizible_first_touch_channel = 'Marketing'`.

Lead source list (Marketing-Attributable):
- `Web`
- `Content Download`
- `Advertisement`
- `Event` (marketing event)
- `Webinar`
- `Email`
- `Outbound Email` (marketing email, not SDR)

NOT in Marketing-Attributable:
- `Sales Prospecting`
- `Cold Call`
- `Outbound` (SDR-driven)
- `Referral` / `Customer Referral`
- `Partner Referral`

### Marketing-influenced pipeline
"Marketing touched this deal at any point." Looser.

Logic: `EXISTS (bizible touchpoint where opp_id = X AND touch_type IS NOT NULL)`.

Typically 60-80% of all pipeline is marketing-influenced; only 20-30% is marketing-sourced.

Canonical views:
- `MARKETING_PROD.AGGREGATIONS.MARKETING_SOURCED_PIPELINE`
- `MARKETING_PROD.AGGREGATIONS.MARKETING_INFLUENCED_PIPELINE`

Anti-pattern: reporting marketing-influenced as marketing-sourced — inflates Marketing's claim. Marketing leadership cares about both, but they're separate KPIs.

---

## §6. Lead source rationalization

`Lead.LeadSource` in SFDC is messy — sales reps fill in different values. Rationalization view standardizes:

```
Raw lead_source             → Rationalized category
"Web - Form Fill"          → "Web"
"website"                  → "Web"
"WEB-Content"              → "Web"
"Trade Show - Dreamforce"  → "Event"
"Inbound Phone Call"       → "Inbound"
...
```

Canonical: `MARKETING_PROD.MANAGED.LEAD_SOURCE_RATIONALIZATION` (joined to bare Lead/Opp via `RATIONALIZED_LEAD_SOURCE__C` lookup).

Maintenance: rationalization rules in a Google Sheet (controlled by Marketing Operations); review quarterly.

---

## §7. The MQL — Marketing Qualified Lead

Definition: a lead that has reached a marketing-defined score threshold indicating "ready for sales."

Sources of truth:
1. **Marketo lead score** — composite of activities (email opens, content downloads, form fills, web visits)
2. **Custom `MQL__c` SFDC object** — captures MQL events with timestamp + reason

Canonical view: `MARKETING_PROD.AGGREGATIONS.MQL_BY_QUARTER`
- Grain: one row per MQL event per quarter
- Includes lead source, campaign, account, conversion-to-opportunity flag

MQL → SAL (Sales Accepted Lead) → SQL (Sales Qualified Lead) → Opp:

```
MQL (Marketo threshold)  →  SAL (SDR accepts)  →  SQL (AE confirms)  →  Opportunity created
       ↑                         ↑                       ↑                          ↑
   Marketing owns             Sales owns             Sales owns                 Sales owns
```

MQL → Opp conversion rate is a KPI: `MQL_TO_OPP_CONVERSION_RATE` in `AGGREGATIONS`.

---

## §8. Campaign performance

Campaigns are the unit of marketing program execution. Hierarchy:

```
Program (Marketo)                         ← Top level (e.g., "FY26 Q3 Demand Gen")
  └── Campaign (SFDC)                     ← Tactic (e.g., "FY26 Q3 Webinar - HCM")
        └── CampaignMember (SFDC)         ← Individual lead/contact participation
```

Canonical campaign-perf view: `MARKETING_PROD.AGGREGATIONS.CAMPAIGN_PERFORMANCE`
- Grain: one row per campaign per quarter
- Metrics: members, MQLs generated, opps generated, pipeline$, closed-won$, ROI

ROI formula:
```
Campaign ROI = (Closed-Won attributed_revenue - Campaign cost) / Campaign cost
```

Costs come from `REF_CAMPAIGN_BUDGET` Google Sheet (Marketing Ops-controlled).

---

## §9. ABM — Account-Based Marketing

ABM targets specific high-value accounts rather than mass lead generation.

ABM target list:
- `Account.TOP_TARGET_FOR_MARKETING_ABM__C = TRUE`  — ABM target flag
- `Account.MARKETING_CLASSIFICATIONS__C` — tier (Tier 1 / Tier 2 / Tier 3)

ABM penetration view: `MARKETING_PROD.AGGREGATIONS.ABM_PENETRATION`
- For each target account: # of contacts engaged, # of touchpoints, opp pipeline value
- KPI: % of ABM target accounts with engaged contacts in last 90 days

ABM-specific intent signals:
- 6Sense intent score (per account, per topic)
- Drift chat engagement
- Bombora intent surge

---

## §10. The contact-role attribution problem

SFDC opportunities can have multiple contacts with `OpportunityContactRole` (decision-maker, influencer, evaluator). Attribution can be:

- **Single contact**: credit primary contact only (often misleading)
- **All contacts**: credit each contact role equally
- **Buying committee**: credit pattern based on role weights

Bizible default: attribute to whichever contact's touchpoint is in the touch (multi-touch handles it).

Edge case: opp closed without any associated contact (bad data) → attribution falls back to account-level. View: `MARKETING_PROD.MANAGED.ATTRIBUTION_FALLBACK_ANALYSIS`.

---

## §11. Lead lifecycle metrics

| Metric | Definition |
|---|---|
| **Lead velocity** | Avg days from Lead created → MQL |
| **MQL→SAL rate** | % of MQLs accepted by sales within X days |
| **SAL→SQL rate** | % of SALs that convert to qualified opps |
| **SQL→Opp rate** | % of SQLs that become opportunities |
| **Lead-to-opp velocity** | Avg days from Lead → Opportunity |
| **Lead-to-win velocity** | Avg days from Lead → Closed-Won |

Funnel view: `MARKETING_PROD.AGGREGATIONS.LEAD_FUNNEL_CONVERSION`.

---

## §12. Channel performance

Channels = high-level marketing tactics. Standard channel taxonomy:

| Channel | Examples |
|---|---|
| **Paid Search** | Google Ads, Bing Ads |
| **Organic Search** | SEO traffic |
| **Paid Social** | LinkedIn, Facebook, Twitter ads |
| **Organic Social** | LinkedIn posts, Twitter |
| **Email** | Outbound campaigns, newsletter |
| **Webinar** | Live + on-demand webinars |
| **Event** | Trade shows, conferences |
| **Content Syndication** | Third-party content distribution |
| **Direct Mail** | Physical mail campaigns |
| **Partner** | Partner-driven campaigns |
| **Display / Programmatic** | Banner ads, retargeting |
| **Referral** | Customer referral programs |

Channel performance view: `MARKETING_PROD.AGGREGATIONS.CHANNEL_PERFORMANCE_BY_QUARTER`.

Cost-per-X by channel:
- Cost per Lead (CPL)
- Cost per MQL (CPMQL)
- Cost per Opportunity (CPO)
- Cost per Closed-Won Customer

---

## §13. Web analytics integration

Adobe Analytics provides web behavioral data:
- Page views per session
- Form completion paths
- Conversion funnels (web visit → form fill → MQL)
- Search keyword performance

Lands in `BASE_PROD.ADOBE_ANALYTICS.*` via S3 daily drop. Marketing analytics joins on `marketo_id` or `email_hash` to tie web behavior to known leads.

Anti-pattern: joining web analytics directly to opportunities — anonymity gap means most web sessions don't tie to a known person.

---

## §14. CDP (Customer Data Platform)

CDP unifies marketing identities across:
- Cookies (anonymous)
- Marketo (known leads/contacts)
- SFDC (accounts/contacts)
- Gainsight (customers)

CDP provides:
- Resolved person ID (cross-system)
- Account engagement score
- Intent topics (inferred from behavior)

Lives in `BASE_PROD.CDP.*`. Marketing analytics uses CDP for:
- Account engagement scoring
- Identity resolution across channels
- Audience segmentation for campaigns

---

## §15. Hightouch (reverse ETL)

Hightouch syncs Snowflake data BACK to:
- **Marketo**: enriched lead attributes (LTV potential, account tier, account ARR)
- **SFDC**: enriched account scores (CDP score, intent, customer health)
- **Drift**: ABM target account flag for chat routing

Pattern: Sigma/dbt produces a "person enrichment table" → Hightouch syncs to Marketo every hour.

---

## §16. Marketing KPI dashboard structure

Standard executive marketing dashboard:

| Section | Metrics |
|---|---|
| **Top of funnel** | MQLs by source, MQL velocity, $ in pipeline created |
| **Mid funnel** | SQL conversion, opps created, pipeline coverage |
| **Bottom funnel** | Marketing-sourced bookings, marketing-influenced bookings, ROI |
| **Channel mix** | Performance by channel, cost-per-MQL, cost-per-opp |
| **ABM performance** | ABM target account engagement, ABM pipeline $ |
| **Campaign top performers** | Top 10 campaigns by pipeline created |

Canonical dashboard model: `MARKETING_PROD.DATA_PRODUCTS.DASH_MARKETING_PERFORMANCE_QUARTERLY`.

---

## §17. Cross-domain dependencies

| Depends on | Why |
|---|---|
| `eda-dbt-base` | Raw Marketo, Bizible, SFDC wrappers |
| `eda-dbt-common` | Fiscal calendar, currency, Reltio MDM |
| (sales models from same `eda-dbt-gtm` project) | Account, Opportunity, OpportunityHistory for attribution |

Consumed by:
| Downstream | Use case |
|---|---|
| `eda-dbt-em` | Marketing-sourced pipeline for finance reporting |
| `eda-dbt-cx` | Pre-purchase touch history for customer health context |
| `eda-dbt-semantic-layer` | Marketing-sourced ARR semantic metric |

---

## §18. Common gotchas

- **Lead source updated post-creation** — `LeadSource` can be changed after lead creation; for true first-touch, use Bizible (it's snapshot-aware)
- **Marketo activity timestamp drift** — Marketo can backdate activities up to 24 hours; for time-windowed reports, use SFDC sync timestamp not Marketo activity timestamp
- **Bizible touchpoint duplicates** — same email can be tracked twice (once via Marketo, once via Bizible direct); de-dup on `(person_id, touch_timestamp, channel)`
- **Hidden inflation in MQL count** — every form fill creates a Marketo activity; spam fills inflate MQL count; filter out spam emails
- **Campaign members can be added in bulk** — bulk lists added to campaigns AFTER the program ran inflate "campaign reach"; check `CampaignMember.CreatedDate` vs `Campaign.StartDate`
- **Anonymous web visits** — most web traffic is anonymous; can only attribute when person fills a form or has been previously cookied
- **Cookie expiry** — Bizible's first-touch attribution depends on cookie persistence; cleared cookies → "first touch" recorded as later event

---

## §19. Cross-references

- `salesforce-bsa-marketing-expert` skill — Marketing-side SFDC objects
- `domain-sales-gtm.md` — Opportunity / pipeline downstream
- `subscription-business-model.md` — Quote-to-cash flow context
- `enterprise-data-products-catalog.md` — Published marketing data products
- `finance-metrics-canonical.md` — How marketing-sourced bookings tie to ACV
