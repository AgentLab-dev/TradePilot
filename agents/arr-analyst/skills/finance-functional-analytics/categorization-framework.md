# Categorization Framework — Deal Motion + ARR Waterfall

The complete taxonomy for classifying every contract event in a subscription
business. This is the conceptual core of finance analytics — if you get
categorization wrong, every downstream metric is wrong.

Two parallel taxonomies that MUST stay aligned:
1. **Booking-side (deal motion)** — how Sales describes the transaction
2. **ARR-side (waterfall category)** — how Finance accounts for the impact

This doc maps between them, gives the canonical decision tree, and works
through every edge case.

---

## §1. The two taxonomies (and why they exist)

### 1.1 Booking-side (Sales / GTM taxonomy)

Sales reps and CRO use these terms day-to-day. They describe **the deal motion**:

| Term | What sales means | Example |
|---|---|---|
| **New New** | First contract with a brand-new account | Pure new logo, never sold before |
| **Net New** | New product family for existing customer | They had HCM, now buying Spend Management |
| **Add-on** | Any expansion booking (loose term) | More seats, more products, higher tier |
| **Cross-sell** | New product family (sub-type of Add-on) | Same as Net New, sales terminology |
| **Upsell** | Higher tier of existing product | Standard → Enterprise SKU |
| **Renewal** | Same product, renewal term | Contract renewed (flat / up / down) |
| **SSR** | Supersede & Replace (Apttus-specific) | Old agreement closed, new one starts (renewal mechanism) |
| **Migration** | SKU swap | HCM v1 → HCM v2 (platform upgrade) |
| **True-up** | Mid-term seat addition | They had 100 seats, added 50 mid-term |
| **True-down** | Mid-term seat reduction | Rare; usually contractual |
| **Pilot conversion** | Pilot → full subscription | 3-month pilot becomes 3-year contract |
| **Downsell** | Smaller contract on renewal | Renewing but with fewer seats |
| **Churn** | Customer didn't renew, terminated | Full customer loss |

### 1.2 ARR-side (Finance waterfall taxonomy)

Finance + FP&A use these to account for the **ARR impact**:

| Category | Direction | Definition |
|---|---|---|
| **BEGIN_ARR** | Reference | Starting ARR at beginning of period |
| **NEW_LOGO** | + | ARR from brand-new customer accounts |
| **EXPANSION** | + | ARR added to existing customers (sub: cross-sell, upsell, volume up, price up) |
| **CONTRACTION** | - | ARR removed from existing customers (sub: downsell, volume down, price down) |
| **CHURN** | - | ARR from customers that fully terminated |
| **SKU_CHANGE** | ± | Net ARR change from SKU swaps (typically near-zero net) |
| **VOLUME** | ± | Sub-effect of EXPANSION/CONTRACTION isolating seat/usage change |
| **PRICE** | ± | Sub-effect isolating list-price change |
| **MIX** | ± | Currency / region rebalance effect |
| **END_ARR** | Reference | Ending ARR at end of period |

The walk: `END_ARR = BEGIN_ARR + NEW_LOGO + EXPANSION - CONTRACTION - CHURN + SKU_CHANGE`

(VOLUME + PRICE + MIX sub-totals roll up into EXPANSION / CONTRACTION at the parent level.)

---

## §2. The mapping (Sales motion → ARR category)

For every closed-won deal, sales motion maps to ARR category:

| Sales motion | ARR category | Sub-category | Comment |
|---|---|---|---|
| New New (Pure new logo) | NEW_LOGO | n/a | Account had zero prior ARR |
| Net New (new product, existing customer) | EXPANSION | Cross-sell | Different product family from prior holdings |
| Add-on / Cross-sell (different product family) | EXPANSION | Cross-sell | Same as Net New |
| Add-on / Upsell (higher tier) | EXPANSION | Upsell | Same product, premium tier |
| Renewal — Flat (same ARR) | (no waterfall contribution) | Flat Renewal | Continuity; doesn't move waterfall |
| Renewal — Up (more ARR) | EXPANSION | Renewal Expansion | Sub-attribution: Volume / Price |
| Renewal — Down (less ARR) | CONTRACTION | Renewal Contraction | Sub-attribution: Volume / Price |
| SSR — Flat | (no contribution) | Flat Renewal | SSR-resolved as continuity |
| SSR — Up | EXPANSION | Renewal Expansion | SSR-resolved as expansion |
| SSR — Down | CONTRACTION | Renewal Contraction | SSR-resolved as contraction |
| Migration (SKU swap, equal value) | SKU_CHANGE | Migration | Net-zero category |
| Migration (SKU swap, more value) | SKU_CHANGE + EXPANSION (delta) | Migration + Expansion | Split: SKU portion + price delta |
| True-up (mid-term seat add) | EXPANSION | Volume | Annualized delta from amendment date |
| True-down (mid-term seat reduction) | CONTRACTION | Volume | Rare |
| Pilot conversion | NEW_LOGO (if pilot was excluded from ARR) or EXPANSION (if pilot was in ARR) | n/a | Depends on pilot inclusion policy |
| Downsell (renewal with fewer seats) | CONTRACTION | Volume | Sub-attribution |
| Customer churn (no renewal, no SSR) | CHURN | Customer churn | Full loss |
| Product churn (specific product dropped, customer retained) | CHURN | Product churn | Partial loss |

**Key insight**: Sales motions are descriptive (how the deal felt); ARR categories are accounting (how it impacts the recurring revenue base). The mapping is well-defined but requires SSR resolution + grain awareness.

---

## §3. The master decision tree

For a single Agreement Line Item (ALI), comparing **current as_was_date** to **prior as_was_date**:

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│ START: ALI snapshot delta (current_arr vs prior_arr, current_sku vs prior_sku)   │
└────────────────────────────────────┬──────────────────────────────────────────────┘
                                     ▼
                  ┌──────────────────┴──────────────────┐
                  │ prior_arr IS NULL (line didn't exist) │
                  └──────────────────┬──────────────────┘
                                     │
                Yes ◀────────────────┴────────────────▶ No
                  │                                       │
                  ▼                                       ▼
   ┌─────────────────────────────┐          ┌─────────────────────────────┐
   │ NEW LINE — what kind?       │          │ EXISTING LINE — what happened?│
   │                             │          │                             │
   │ Is account brand new?       │          │ Is current_arr = 0?         │
   │ (no prior agreement at all) │          │ (line went to zero)         │
   │                             │          │                             │
   │ Yes → NEW_LOGO              │          │ Yes ▼               No ▼    │
   │                             │          │                             │
   │ No  → check via SSR:        │          │ ┌────────────┐ ┌──────────┐ │
   │                             │          │ │ Is there   │ │ ARR delta│ │
   │ Is this line the "new" side │          │ │ an SSR     │ │ vs SKU   │ │
   │ of an SSR link?             │          │ │ link to    │ │ change   │ │
   │                             │          │ │ another    │ │ tree...  │ │
   │ Yes → categorize via SSR:   │          │ │ line?      │ └──────────┘ │
   │   - SSR Flat → (no contrib) │          │ │            │              │
   │   - SSR Up → EXPANSION      │          │ │ Yes →      │              │
   │     (sub: Renewal Exp)     │          │ │  Handled    │              │
   │   - SSR Down → CONTRACTION  │          │ │  by SSR     │              │
   │     (sub: Renewal Contr)   │          │ │  logic      │              │
   │                             │          │ │            │              │
   │ No → EXPANSION              │          │ │ No  →      │              │
   │   (sub: Cross-sell —        │          │ │   CHURN    │              │
   │   new product family)       │          │ │ (further   │              │
   └─────────────────────────────┘          │ │ attribute  │              │
                                            │ │ as Cust    │              │
                                            │ │ vs Product │              │
                                            │ │ churn —    │              │
                                            │ │ see churn  │              │
                                            │ │ -anatomy)  │              │
                                            │ └────────────┘              │
                                            └─────────────────────────────┘

                                            EXISTING LINE — ARR delta + SKU
                                            ┌─────────────────────────────────┐
                                            │ Did SKU change?                  │
                                            │                                  │
                                            │ Yes ▼              No ▼          │
                                            │                                  │
                                            │ SKU_CHANGE         Did ARR move? │
                                            │ (+ split into      │             │
                                            │  EXPANSION /       │             │
                                            │  CONTRACTION       │             │
                                            │  for delta)        │             │
                                            │                                  │
                                            │                    ARR went up:  │
                                            │                    → EXPANSION   │
                                            │                    (sub: Volume / │
                                            │                     Price / Mix) │
                                            │                                  │
                                            │                    ARR went down:│
                                            │                    → CONTRACTION │
                                            │                    (sub: Volume / │
                                            │                     Price / Mix) │
                                            │                                  │
                                            │                    Flat:         │
                                            │                    → (no contrib)│
                                            └─────────────────────────────────┘
```

This is encoded in `get_arr_line_base_fn` UDTF + macros in `eda-dbt-em`.

---

## §4. The SSR-aware reclassification (the critical step)

Without SSR resolution, you get this wrong every time:

**Without SSR** (naive interpretation):
```
Old AGR_001 (line 1, $100k ARR) → status = Terminated  → looks like CHURN: -$100k
New AGR_002 (line 1, $110k ARR) → status = Activated   → looks like NEW_LOGO: +$110k

Net waterfall impact: -$100k CHURN + +$110k NEW_LOGO = +$10k
```

This is WRONG. Customer is still here. Sales did a renewal with expansion.

**With SSR** (canonical):
```
Old AGR_001 ↔ New AGR_002 linked via SSR_AGREEMENT_RELATIONSHIP

Old AGR_001 (line 1, $100k → 0) → SSR-resolved: not churn
New AGR_002 (line 1, 0 → $110k) → SSR-resolved: not new logo

Net waterfall impact:
- $100k → $110k = +$10k EXPANSION (sub: Renewal Expansion, Price/Volume sub-attribution)
```

This is RIGHT. The customer renewed and expanded by $10k.

**The SSR resolution table** (`FINANCE_PROD.MANAGED.SSR_AGREEMENT_RELATIONSHIP`):
| old_agreement_id | new_agreement_id | ssr_category | delta_arr_usd |
|---|---|---|---|
| AGR_001 | AGR_002 | RENEWAL_EXPANSION | +10000 |
| AGR_003 | AGR_004 | FLAT_RENEWAL | 0 |
| AGR_005 | AGR_006 | RENEWAL_CONTRACTION | -5000 |
| AGR_007 | AGR_008 | MIGRATION | 0 (SKU swap, same value) |

When categorizing a line that has SSR linkage, ALWAYS consult this table.

---

## §5. The 4 deal motions (canonical sales taxonomy)

Sales orgs canonicalize motion using these 4 (sometimes 5) buckets:

### 5.1 New New (Pure New Logo)

**Definition**: First contract with a brand-new account. No prior agreement history.

**SQL test**:
```sql
-- New New: account_id has no prior agreement before this one
WHERE NOT EXISTS (
    SELECT 1 FROM WD_AGREEMENT_SCD2 prior
    WHERE prior.account_id = current.account_id
      AND prior.term_start_date < current.term_start_date
)
```

**ARR category**: NEW_LOGO
**Common confusion**: "We acquired a customer from a competitor — is this New New?"
- **Answer**: Yes, if the parent account in Workday is new. If we acquired the company (Adaptive / Scout etc.), then the customer base inherits the acquisition date as ARR baseline (see `enterprise-data-architect/subscription-business-model.md §12`).

### 5.2 Net New (Existing customer, new product family)

**Definition**: Existing account, but buying a product family they didn't previously own.

**SQL test**:
```sql
-- Net New: account has prior agreement, but no prior holding in this product L3
WHERE EXISTS (
    SELECT 1 FROM WD_AGREEMENT_SCD2 prior
    WHERE prior.account_id = current.account_id
      AND prior.term_start_date < current.term_start_date
)
AND NOT EXISTS (
    SELECT 1 FROM WD_AGREEMENT_LINE_SCD2 prior_line
    JOIN WD_AGREEMENT_SCD2 prior_agr ON prior_line.agreement_id = prior_agr.agreement_id
    WHERE prior_agr.account_id = current.account_id
      AND prior_line.product_code_l3 = current.product_code_l3
      AND prior_agr.term_start_date < current.term_start_date
)
```

**ARR category**: EXPANSION → Cross-sell
**Used for**: Cross-sell attribution dashboards, product-roadmap "land and expand" metrics.

### 5.3 Add-on (also Cross-sell / Upsell — used interchangeably by sales)

**Definition**: Any expansion booking — more seats, new product, higher tier — for an existing customer.

This is a **loose sales term** that covers multiple ARR sub-categories:
- More seats on existing product → EXPANSION (Volume)
- Higher tier of same product → EXPANSION (Price / Upgrade)
- New product family → EXPANSION (Cross-sell / Net New)

For dashboards: typically "Add-on bookings ACV" = SUM of all bookings that aren't NEW_LOGO and aren't RENEWAL.

### 5.4 Renewal

**Definition**: Same customer, renewing an existing contract.

Three sub-types:
- **Flat renewal** — same ARR → no waterfall contribution
- **Renewal expansion** — more ARR → EXPANSION (sub: Renewal Expansion)
- **Renewal contraction** — less ARR → CONTRACTION (sub: Renewal Contraction)

Detection: SSR-aware (via `SSR_AGREEMENT_RELATIONSHIP`)
- If SSR link exists AND old agreement was Terminated AND new agreement is Activated → it's a renewal
- Compare old_arr vs new_arr to determine flat / up / down

**Important**: Some customers do an **early renewal** (renew 3 months before contract end). The SSR link captures this; the old agreement is superseded mid-term.

### 5.5 Migration (sometimes a 5th explicit motion)

**Definition**: Same customer, switching from one SKU to another (typically platform upgrade).

Examples:
- HCM v1 → HCM v2 (Workday platform upgrade)
- Workday Spend → Workday Adaptive (re-baseline to acquired product)
- HCM Standard → HCM Enterprise (tier change — sometimes treated as Upsell instead)

**ARR category**: SKU_CHANGE (typically near-zero net; split into EXPANSION/CONTRACTION for the delta)
**Detection**: SSR link AND `prior_sku != current_sku` AND `arr_within_tolerance` (e.g., ±5%)

---

## §6. The full sub-categorization tree

Every ARR category has formal sub-categories used in reporting:

```
NEW_LOGO
├── Direct Sales (sales-led)
├── Partner-influenced (partner co-sell)
├── Partner-sourced (partner originated)
├── Marketing-sourced (marketing originated)
├── Self-serve (online signup; rare at Workday)
└── Acquisition baseline (inherited from acquired company)

EXPANSION
├── Cross-sell (Net New — new product family)
├── Upsell (higher tier of existing product)
├── Renewal Expansion (renewing with more ARR)
├── Volume Expansion (more seats / usage on same product)
├── Price Expansion (list price increase)
└── True-up (mid-term seat add)

CONTRACTION
├── Downsell (renewing with fewer seats)
├── Renewal Contraction (renewing at lower ARR)
├── Volume Contraction (fewer seats / usage)
├── Price Contraction (discount applied)
└── True-down (mid-term seat reduction; rare)

CHURN
├── Customer Churn (entire customer gone)
│   ├── Voluntary (customer chose to leave)
│   ├── Involuntary (M&A, business shutdown)
│   └── Acquired-into-Workday (acquired-competitor customer didn't renew)
└── Product Churn (specific product dropped; customer retained on others)

SKU_CHANGE
├── Migration (platform upgrade, e.g., v1 → v2)
├── Re-baseline (acquired product mapped to Workday SKU)
└── Tier change (sometimes; often categorized as Upsell instead)
```

Each sub-category may be a separate column in `ARR_*_CATEGORIES` views or a separate dashboard slice.

---

## §7. The "what motion is this opp?" worked examples

### Example 1 — Pure New Logo

```
Opportunity: Globex Corp - Workday HCM
Account: Globex (no prior agreements in Workday)
Proposal: Apttus_Proposal__c (primary), HCM Enterprise, 500 seats, $500k TCV, 3-yr
Agreement: AGR_2001, status = Activated
Term start: 2026-02-01, Term end: 2029-01-31

Categorization:
  - Account is new (no prior agreements) → NEW_LOGO
  - Sub: Direct Sales (no partner / marketing involvement specified)

ARR impact at 2026-02-06 snapshot:
  - arr_usd_current = $166.7k (annualized: $500k / 3yr)
  - acv_usd_current = $166.7k (assuming flat ramp)
  - tcv_usd_current = $500k

Waterfall contribution:
  + NEW_LOGO ARR = +$166.7k
```

### Example 2 — Net New (Cross-sell)

```
Opportunity: Acme Co - Workday Adaptive (existing HCM customer)
Account: Acme (has prior HCM agreement AGR_1001, active, $200k ARR)
Proposal: Apttus_Proposal__c, Adaptive Planning, 100 seats, $50k TCV, 2-yr
Agreement: AGR_2002, status = Activated

Categorization:
  - Account exists (prior HCM agreement) → NOT NEW_LOGO
  - Account has NO prior Adaptive holdings → NET NEW (sub-type)
  - Maps to ARR category: EXPANSION (Cross-sell)

ARR impact:
  + EXPANSION ARR = +$25k (annualized: $50k / 2yr)
    Sub: Cross-sell (Net New)
```

### Example 3 — Renewal Expansion (with SSR)

```
Old: AGR_1001 (Acme HCM, $200k ARR, term ends 2026-04-30)
New: AGR_2003 (Acme HCM, $230k ARR, term starts 2026-05-01)
SSR link: SSR_AGREEMENT_RELATIONSHIP shows AGR_1001 → AGR_2003 (RENEWAL_EXPANSION)

Categorization:
  - Old line: prior_arr = $200k, current_arr = 0 at 2026-05-06 snapshot
    → Without SSR: would look like CHURN
    → With SSR: recognized as part of renewal
  - New line: prior_arr = NULL, current_arr = $230k
    → Without SSR: would look like NEW_LOGO
    → With SSR: recognized as renewal expansion
  
Net categorization:
  + EXPANSION ARR = +$30k ($230k - $200k)
    Sub: Renewal Expansion
  + Sub-attribution: Volume? Price? Cross-sell? — drill into seat/price deltas
```

### Example 4 — Migration (SKU Change)

```
Old: AGR_1002 (Acme HCM v1, $100k ARR)
New: AGR_2004 (Acme HCM v2, $100k ARR)
SSR link: MIGRATION category

Categorization:
  - Old line + new line both at $100k → no ARR delta
  - SKU changed (v1 → v2)
  - Category: SKU_CHANGE (net zero)

Waterfall contribution:
  + SKU_CHANGE ARR = 0 (or split as $100k SKU_OUT, +$100k SKU_IN)
```

### Example 5 — Migration with Expansion (SKU Change + Price)

```
Old: AGR_1003 (Acme HCM v1, $100k ARR)
New: AGR_2005 (Acme HCM v2, $130k ARR)
SSR link: MIGRATION_WITH_EXPANSION

Categorization:
  - Old line: SKU_CHANGE_OUT, $100k
  - New line: SKU_CHANGE_IN, $100k (matched portion)
                + EXPANSION (sub: Price), $30k (delta portion)

Waterfall contribution:
  + SKU_CHANGE = 0 (matched portion offsets)
  + EXPANSION = +$30k
    Sub: Renewal Expansion (Price)
```

### Example 6 — Customer Churn

```
Old: AGR_1004 (Globex HCM, $150k ARR, term ends 2026-04-30, status = Terminated)
New: NONE (no SSR, no replacement agreement)
Other Globex agreements: NONE (this was their only product)

Categorization:
  - Old line: prior_arr = $150k, current_arr = 0
  - No SSR link → CHURN
  - All Globex agreements gone → CUSTOMER CHURN (sub-type)

Waterfall contribution:
  - CHURN ARR = -$150k
    Sub: Customer Churn (Voluntary or Involuntary — see churn-anatomy.md)
```

### Example 7 — Product Churn

```
Old: AGR_1005 (Acme Adaptive, $50k ARR, term ends 2026-04-30, status = Terminated)
New: NONE
Other Acme agreements: AGR_1001 (HCM, active, $200k ARR) — customer retained on other products

Categorization:
  - Old line: prior_arr = $50k, current_arr = 0
  - No SSR link → CHURN
  - Account still has other active agreements → PRODUCT CHURN (sub-type, not customer churn)

Waterfall contribution:
  - CHURN ARR = -$50k
    Sub: Product Churn (Adaptive dropped, customer retained on HCM)
```

### Example 8 — True-up (Mid-term Volume Expansion)

```
Original: AGR_1001 line 1 (HCM, 500 seats, $100k ARR, signed 2025-02-01)
Amendment: AGR_1001 line 2 (HCM, 100 additional seats, +$20k ARR, signed 2025-08-15)
   APTTUS__AGREEMENTLINEITEM__C row with SKU_ADDED_VIA_AMENDMENT__C = TRUE

Categorization at 2025-08-06 → 2025-11-06 snapshot delta:
  - Line 1 (original): prior_arr = $100k, current_arr = $100k → no contribution
  - Line 2 (amendment): prior_arr = 0, current_arr = $20k → NEW LINE
    - Account is existing → NOT NEW_LOGO
    - No SSR link → EXPANSION
    - Same product as line 1 → Sub: Volume Expansion (True-up)

Waterfall contribution:
  + EXPANSION ARR = +$20k
    Sub: True-up (Volume)
```

---

## §8. The Volume / Price / Mix decomposition

For EXPANSION and CONTRACTION, finance often wants further sub-attribution:

```
Total EXPANSION/CONTRACTION
  ├── Volume effect — change attributable to seat/usage change
  ├── Price effect — change attributable to list-price change
  └── Mix effect — change attributable to currency/region rebalance
```

Math (for a single line, period-over-period):
```
prior_arr = prior_quantity × prior_price_per_unit
current_arr = current_quantity × current_price_per_unit

total_delta = current_arr - prior_arr

volume_effect = (current_quantity - prior_quantity) × prior_price_per_unit
price_effect  = (current_price_per_unit - prior_price_per_unit) × current_quantity
mix_effect    = (other adjustments — FX, region rebalance)

verify: volume_effect + price_effect + mix_effect ≈ total_delta
```

For currency mix (most common at Workday):
```
USD_HIST: arr_usd_hist (locked at prior FX)
USD_CURRENT: arr_usd_current (revalued at current FX)
fx_mix_effect = arr_usd_current - arr_usd_hist  -- the pure FX impact
```

---

## §9. The Customer Churn vs Product Churn attribution

Critical distinction. Use this logic on every CHURN classification:

```
Line classified as CHURN (prior_arr > 0, current_arr = 0, no SSR link)
   │
   ▼
Check: does this account have ANY OTHER active agreements (or active lines) as of current as_was_date?
   │
   ├── No → CUSTOMER CHURN (entire customer gone)
   │
   └── Yes → PRODUCT CHURN (this product dropped, customer retained on others)
```

SQL implementation:
```sql
-- For each line classified as CHURN, determine cust vs product churn
SELECT
    line.agreement_line_item_id,
    line.account_id,
    line.product_code_l3,
    line.arr_category,  -- 'CHURN'
    CASE
        WHEN EXISTS (
            SELECT 1 FROM FINANCE_LINE_ANALYTICS active
            WHERE active.account_id = line.account_id
              AND active.as_was_date = line.as_was_date
              AND active.arr_usd_current > 0
              AND active.is_arr_eligible = TRUE
        )
        THEN 'PRODUCT_CHURN'
        ELSE 'CUSTOMER_CHURN'
    END AS churn_sub_category
FROM FINANCE_LINE_ANALYTICS line
WHERE line.as_was_date = '2026-04-30'
  AND line.arr_category = 'CHURN';
```

Reported as separate KPIs:
- **Customer Churn ARR** — fully-lost customer count + ARR
- **Product Churn ARR** — retained-customer-but-lost-product count + ARR

These have different operational implications:
- Customer churn → CS save plays failed; possible relationship issue
- Product churn → product-fit issue; possible product roadmap signal

---

## §10. The "edge case" catalog

### 10.1 Customer comes back after churn

A customer churned in Q2 → signs new agreement in Q4 of same fiscal year.

**Categorization**:
- The Q2 line is CHURN (categorized at Q2 close — immutable)
- The Q4 new line is NEW_LOGO (treat as new customer; no SSR link to old)
- Account ARR went $X → 0 → $Y over the year

Some companies have a "back from churn" / "winback" sub-category. Workday currently doesn't distinguish.

### 10.2 Multi-line churn

Customer has 3 product lines; all 3 terminate same period.
- Each line individually: classified as CHURN
- For attribution: all 3 lines aggregate to CUSTOMER_CHURN (no other active lines for account)

### 10.3 Backdated activation

Agreement signed Q4 with effective date Q2 (backdated). 

**Categorization**:
- ARR attribution depends on the `as_was_date` snapshot policy
- Standard policy: ARR enters the waterfall at the earliest as_was_date where `is_activated = TRUE AND term_start_date <= as_was_date`
- May result in retroactive booking in a closed quarter → requires SOX approval before restating

### 10.4 Cancelled agreement re-activated

Agreement cancelled in Q2 → re-activated in Q3 (rare, but happens for accidental cancellations).

**Categorization**:
- Q2: CHURN (line goes to 0)
- Q3: NEW_LOGO (line comes back, no SSR)
- Net: same ARR as before, but waterfall shows churn + new logo

If finance wants a "correction" treatment (un-do the churn): file a Jira; requires reload of Q2 snapshot (SOX-controlled).

### 10.5 Partial mid-term termination

Agreement has 3 lines. One line gets terminated mid-term (rare but happens for "abandoned" product use).

**Categorization**:
- The terminated line: CHURN (or CONTRACTION if reduced rather than fully terminated)
- Sub: PRODUCT_CHURN (customer retained on other lines)

### 10.6 SSR with line restructuring

Old agreement: 3 lines totaling $300k
New agreement: 1 consolidated line totaling $320k

**Categorization** (with SSR):
- 3 old lines → 0 (linked via SSR to new agreement)
- 1 new line → $320k (linked via SSR to old agreement)
- Net: +$20k EXPANSION (Renewal Expansion)

The 1-line vs 3-line restructuring is handled via SSR-resolution; doesn't show as 3 churns + 1 new logo.

### 10.7 Currency change at renewal

Old: $200k USD (account was in USD)
New: €180k EUR (account re-billed in EUR at renewal)

**Categorization**:
- USD_HIST: lock both to original FX → compare in USD equivalent
- USD_CURRENT: revalue both at current FX → may show "fake" expansion/contraction due to FX move
- Use MIX effect for currency-induced delta

### 10.8 Pilot conversion

3-month pilot at $25k → Converts to 3-year full subscription at $300k

**Categorization** depends on pilot inclusion policy:
- **Policy A**: pilots excluded from ARR (`is_arr_eligible = FALSE`)
  - Pilot ARR = 0 throughout
  - Conversion → NEW_LOGO at $100k annualized
- **Policy B**: pilots included
  - Pilot ARR = $100k (annualized from 3-mo $25k)
  - Conversion: same product, same account → SSR-resolved as EXPANSION? Depends.

Workday's policy: pilots excluded by default (Policy A). Customer-facing reporting uses post-conversion as new logo.

### 10.9 Acquired customer rolling to Workday SKU

Acquired company (e.g., VNDLY) had customers on legacy SKU. Workday re-baselines them onto Workday product hierarchy.

**Categorization**:
- Inherited ARR baseline at acquisition date (not retroactive)
- SKU mapping via `REF_ACQUISITION_MAPPING` Google Sheet
- Any change post-acquisition flows as normal (NEW_LOGO if new logo, EXPANSION if expansion, etc.)

---

## §11. Reconciliation patterns

### The "ARR walk balances" reconciliation

```sql
-- Verify: BEGIN_ARR + Δs = END_ARR
WITH walk AS (
    SELECT
        SUM(CASE WHEN arr_category = 'BEGIN_ARR' THEN arr_usd_hist ELSE 0 END) AS begin_arr,
        SUM(CASE WHEN arr_category = 'NEW_LOGO'   THEN arr_usd_hist ELSE 0 END) AS new_logo,
        SUM(CASE WHEN arr_category = 'EXPANSION'  THEN arr_usd_hist ELSE 0 END) AS expansion,
        SUM(CASE WHEN arr_category = 'CONTRACTION' THEN arr_usd_hist ELSE 0 END) AS contraction,
        SUM(CASE WHEN arr_category = 'CHURN'      THEN arr_usd_hist ELSE 0 END) AS churn,
        SUM(CASE WHEN arr_category = 'SKU_CHANGE' THEN arr_usd_hist ELSE 0 END) AS sku_change,
        SUM(CASE WHEN arr_category = 'END_ARR'    THEN arr_usd_hist ELSE 0 END) AS end_arr
    FROM FINANCE_PROD.AGGREGATIONS.ARR_PRODUCT_CATEGORIES
    WHERE fiscal_quarter = 'FY26Q1'
)
SELECT
    begin_arr,
    new_logo,
    expansion,
    contraction,
    churn,
    sku_change,
    end_arr,
    (begin_arr + new_logo + expansion + contraction + churn + sku_change) AS computed_end,
    end_arr - (begin_arr + new_logo + expansion + contraction + churn + sku_change) AS variance
FROM walk;

-- Variance should be < $1 (rounding only). Anything more = bug.
```

### The "deal motion vs ARR category alignment" reconciliation

```sql
-- For Q4 closed-won opps, verify deal motion maps to expected ARR category
SELECT
    o.deal_motion_classification,
    fla.arr_category,
    COUNT(*) AS num_lines,
    SUM(fla.arr_usd_current) AS total_arr
FROM SALES_PROD.MANAGED.WD_OPPORTUNITY_SCD2 o
JOIN FINANCE_PROD.MANAGED.FINANCE_LINE_ANALYTICS fla 
    ON o.opportunity_id = fla.opportunity_id
WHERE o.fiscal_quarter_won = 'FY26Q1'
  AND fla.as_was_date = '2025-05-06'
  AND fla.is_arr_eligible = TRUE
GROUP BY 1, 2
ORDER BY 1, 2;

-- Expected mapping:
-- "New New" → NEW_LOGO
-- "Net New" / "Cross-sell" → EXPANSION (Cross-sell)
-- "Upsell" → EXPANSION (Upsell)
-- "Renewal Up" → EXPANSION (Renewal Expansion)
-- "Renewal Flat" → (no ARR category — flat doesn't contribute to walk)
-- etc.
-- 
-- Any unexpected combinations = data quality issue
```

---

## §12. The "I don't know what category this is" escalation

If you encounter a deal that doesn't cleanly fit any category:

1. **Stage 1**: Check if it's a known edge case (§10 above)
2. **Stage 2**: Check the `categorization_audit_flags` column in `FINANCE_LINE_ANALYTICS` — finance team annotates ambiguous cases
3. **Stage 3**: If still unclear, escalate to:
   - **enterprise-metrics-finance-architect** if it's a model logic question
   - **finance-functional-architect** if it's a "what should this category be?" question (business definition)
   - **Finance Ops** if it requires a manual classification override

DO NOT make a judgment call solo. Finance categorization is governed.

---

## §13. Cross-references

- `retention-deep-dive.md` — how categories aggregate into retention metrics
- `churn-anatomy.md` — Customer vs Product churn deep dive
- `metric-recipes.md` — SQL patterns for every metric
- `enterprise-data-architect/finance-metrics-canonical.md` — canonical metric definitions
- `enterprise-data-architect/subscription-business-model.md` — SSR business context
- `salesforce-bsa-finance-analyst` skill — Apttus deal motion fields
- `enterprise-metrics-finance-architect` skill — how to architect new categorization logic
- `finance-functional-architect` skill — how to spec a new category
