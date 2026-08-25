---
name: bay-area-pdx-flights
description: >-
  Find and compare nonstop Bay Area ↔ Portland (PDX) one-way fares across OAK,
  SFO, and SJC. Use when the user asks about flight tickets, PDX travel,
  Oakland/SFO/SJC to Portland, return PDX to Bay Area, or wants a side-by-side
  airline fare comparison for this corridor.
---

# Bay Area ↔ PDX Flight Finder (ssr-analyst only)

Project-scoped skill. Do **not** copy to `~/.cursor/skills/` or other repos.

## Defaults for this agent

| Preference | Default |
|---|---|
| Preferred Bay Area airport | **OAK** (then SFO, then SJC) |
| Trip type | One-way unless user says round-trip |
| Stops | **Nonstop only** — ignore connections unless user asks |
| Fare class note | Prefer Main/Choice over Saver/Basic if delta ≤ ~$15 |

## Search workflow

1. Confirm dates (and year). If user says “Wednesday” without a date, resolve against today.
2. Search both directions as needed: Bay Area → PDX and PDX → Bay Area.
3. Always compare **OAK + SFO** (add SJC if useful). Airlines:
   - **OAK ↔ PDX**: Alaska, Southwest
   - **SFO ↔ PDX**: Alaska, United (no Southwest nonstop)
   - **SJC ↔ PDX**: Alaska, Southwest
4. Prefer live airline pages over aggregator teasers:
   - Alaska: `alaskaair.com`
   - Southwest: `southwest.com` (not on most OTAs)
   - Cross-check: Google Flights / Kayak for calendar view only
5. Ask user to paste airline result pages when live inventory is needed. Aggregator “from $59” often maps to other dates.
6. Deliver a side-by-side table: airport, airline, flight #, depart/arrive, duration, cheapest fare, bag/change notes.
7. End with one clear book recommendation + direct booking links.

## Fare interpretation rules (learned)

- Calendar strip lowest fare ≠ every flight that day — use the flight list price.
- **Saver (Alaska) / Basic (Southwest)**: cheapest, no seat pick, restrictive changes. Upsell to Main/Choice if ≤ ~$15 more.
- Southwest free bags: only on higher bundles (Choice Extra / status / RR card) — **not** on Basic. Do not assume free bags on the cheap fare.
- Peak summer midweek Bay Area → PDX can sit ~$250–$350; reverse/shoulder dates often much lower ($59–$130). Always re-price; do not reuse prior-session outbound fares for the return.
- Skip connections when nonstops exist unless connection is clearly cheaper *and* user accepts the time cost.

## Output template

```markdown
## [Direction] nonstops — [dates]

| Airport | Airline | Flight | Depart → Arrive | Fare | Notes |
|---|---|---|---|---|---|
| ... | ... | ... | ... | $.. | ... |

### Recommendation
- **Book:** [airport + airline + flight + fare]
- **Why:** [1 sentence]
- **Links:** [airline URLs]
```

## Booking links (quick)

- Alaska OAK–PDX: https://www.alaskaair.com/en/flights-from-oakland-to-portland
- Alaska PDX–OAK: https://www.alaskaair.com/en/flights-from-portland-to-oakland
- Alaska SFO–PDX: https://www.alaskaair.com/en/flights-from-san-francisco-to-portland
- Alaska PDX–SFO: https://www.alaskaair.com/en/flights-from-portland-to-san-francisco
- Southwest OAK–PDX: https://www.southwest.com/en/flights/flights-from-oakland-to-portland-or
- Southwest PDX–OAK: https://www.southwest.com/en/flights/flights-from-portland-or-to-oakland

## Honesty constraints

- State when prices are estimates vs pasted live inventory.
- Never invent flight numbers or exact fares. If uncertain, say so and ask for a paste of the airline results page.
