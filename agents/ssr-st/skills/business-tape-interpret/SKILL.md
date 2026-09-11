---
name: business-tape-interpret
description: >-
  After WSJ / IBD / MW / Barron's / Reddit capture, write the APPLY block:
  regime, who pays vs who gets paid, sleeve, veto, and Reddit nominations.
  Closes the capture-without-apply hole (ORCL beat/raise, no FCF vs BOM read)
  and the Reddit-as-junk hole (subs are required input, never alone TAKE).
  Use on FULL CHECK step 9, NBT, evening wrap, daily lessons, NEWS.
---

# Business tape interpret

Capture is not understanding. Opening WSJ, IBD, MW, Barron's, and the eight
Reddit subs is **not** a pass unless this block is written.

Logged miss (2026-09-10 wrap): portals were open. Wrap wrote ORCL MANAGE on a
beat/raise. It did not apply the cash-flow story (capex / FCF / BYO hardware)
that WSJ/MW/the call already had. HPE/DELL ripped. **Apply** was the hole.

Logged hole (Reddit): SOCIAL-ONLY is a **ranking** rule, not a skip. Those
subs are required input. A cluster **nominates**. It does not 🟢 take alone.

## When mandatory

Every **daily publish** after desk sources: FULL CHECK, NBT, evening wrap,
10 AM / 8 PM lessons, NEWS when it is the day's capture. Fail the publish if
this block is missing.

Do not wait to be asked. If you opened the portals, you owe APPLY.

## Required pages (signed-in where the desk already logs in)

| Source | Open | Pull |
|---|---|---|
| **IBD** | MarketTrend + The Big Picture | Regime (rally / correction / distribution). `%` is required, not optional. Lists stay `ibd-wsj-capture`. |
| **WSJ** | Homepage + Markets + Heard on the Street | Who is paying vs who is getting paid. Rates, dollar, oil, named dumps. |
| **MW** | Homepage + Market Pulse + earnings | Tape, movers, calendar confirmation. |
| **Barron's** | Homepage (weekend: Up & Down) | Same layer as WSJ. Not a fourth universe. |
| **Yahoo** | https://finance.yahoo.com/ | Public movers, earnings calendar, named headlines. No login. Not a substitute for Heard / MarketTrend. |
| **0d print** | IR 8-K / call color | Income statement **and** cash flow / capex / guide / mix. Beat ≠ the trade. |
| **Reddit** | All eight required subs | What social is pricing + nominated tickers. Miss-catch D. **Never Reddit-alone TAKE.** |

RSS / homepage-only does not replace Heard, MarketTrend, or a 0d 8-K.

## Reddit (input, not a lone TAKE)

Scan is already required (`news-portals`). This skill **applies** that scan.

| Sub | Use as |
|---|---|
| r/semiconductors | Hardware / AI-server color |
| r/options | IV / unusual — check against whale |
| r/stocks · r/investing · r/StockMarket | Named earnings / macro — verify on WSJ/MW |
| r/algotrading · r/Quant | Systems / data, not a ticker take |
| r/wallstreetbets | Crowd / squeeze — noise unless gates also pass |

Rules:

1. Write **Nominated** tickers + one line of **what social is pricing**.
2. Each nominated name is miss-catch D until event-gate + all-four + EM pass.
3. If it passes hard NBT, it **leaves** D and may enter the five as NEW.
4. Fail if the Reddit scan ran and this block has no Reddit line (even `none`).
5. Fail if a 🟢 take cites Reddit as the only source.

## APPLY (required block)

```markdown
## Business tape
Regime: <IBD MarketTrend + WSJ Markets, one line>
Story: <what the market is pricing, not the headline>
Payer vs paid: <who spends now vs who gets paid now>
Sleeve: <GICS / ETF + 2–3 listed names>
Veto: <named dump / Fed / geo / none>
Reddit: <what social is pricing> | Nominated: <TICKER, TICKER, or none>
IS vs CFS (0d only): <income-statement vs cash-flow / guide / mix, or n/a>
```

A 0d AMC/BMO **must** have the IS vs CFS line. That line feeds
`print-readthrough-t1`. “Beat and a small raise” is not enough.

Write the same block into `news_sweep.md` (or `desk_sources_YYYY-MM-DD.md` on
the Grok Bot box) and into the day's FULL CHECK / wrap / lesson publish.

## Fail the publish if

- Capture ran (portals opened) and there is no `## Business tape` block.
- A 0d print has no IS vs CFS / payer-vs-paid line.
- Reddit was scanned and the Reddit / Nominated line is missing.
- A ranked 🟢 take is Reddit-only (no WSJ/MW/IBD cite and no model pass).
- MarketTrend was opened but regime is blank / “n/a” with no SKIP reason.

## Do not

- Add a second portal-login skill. Login stays `news-portals`.
- Treat Unusual Whales as required.
- Promote WSB heat into the five without gates.
- Replace `print-readthrough-t1` — that skill tickets peers; this skill
  explains **why** the peer is the payer or the paid.

No orders. Wait for **go**.
