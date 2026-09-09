---
name: print-ah-guesstimate
description: >-
  Numbered after-hours % bands versus implied move, last-4 surprise, same-night
  cluster, and analog prints. Output base / bull / dump with probabilities that
  sum to 100. Hitting Street is not +10%. Use on guesstimate, "what happens
  after print", HPE / AVGO / SNOW AMC, or any T−0 AMC card.
---

# Print AH guesstimate

Guess the **AH vs RTH close** move, not a PT. Write a numbered table. Do not
write a hedge essay. Hitting consensus EPS is **not** a +10% gap.

## Inputs (live)

| Input | Tool |
|---|---|
| Spot, RTH last | Robinhood `get_equity_quotes` |
| Est + last-4 actual vs est | `get_earnings_results` |
| EM% on the expiry you care about | ATM straddle / spot (`pps-t1-em-recalibrate`) — not whale IV×√T |
| Cluster same AMC | radar + quotes (HPE + **AVGO** + SNOW 9/2) |
| Analog | same-name last rip/fade (HPE **6/2** $64.25 then $45–$49 in 10d) and peer same week (DELL beat → AH fade toward +5%) |
| Theme vs base | WSJ / MW / IBD (`news-portals`). BofA $2B AI-server is **base**, not a rip |

HPE is **Hewlett Packard Enterprise**, not HPQ. NAVN is **Navan**, not NVDA.

## Honesty

- Street beat / in-line EPS **without** a raise or a new mix tell ≈ **fade /
  in-line** band, not 1× EM.
- Last-4 surprise ~20–25% already sits in the price if EM% is only ~12%.
- Cluster can cap the rip (AVGO same night) or the dump (DELL sympathy).
- Analog fade (DELL +10% AH → closer to +5% into RTH; HPE 6/2 spike-then-give)
  pulls probability **out** of the far bull band.

## Output template (required)

Probabilities **sum to 100**. Bands vs **RTH close**, not vs pre.

```
| Band | AH vs RTH close | Spot ~ | When this happens | P |
| dump | ≤ −0.5× EM | | miss / guide cut / cluster dump | xx% |
| fade / in-line | ~0 to +0.5× EM | | hit Street, no raise | xx% |
| +1× EM | ~ +EM% | | beat + raise / mix tell | xx% |
| far bull (name a $ level) | >1.2× EM | | monster + cluster bid | xx% |
```

Then **one** base-case line (the actual guesstimate). Then what that band does
to the live debit (e.g. Sep 18 55/60). Then PPS flag: last-90 still **ARM** if
EM <15%. **No go.**

Write `agents/ssr-st/workspace/Documents/<ticker>_guesstimate_YYYY-MM-DD.md`.
