---
name: rank-next-best
description: >-
  Rank TradePilot tickets after sources and models are in: event gate first (no
  credit through a print), then Sheet plan, EM gates, Three Good as put-credit
  eligibility only (does not veto a call debit), prefer STNOW green + whale ≥ 0,
  one-name rule, clocks. Output take / arm / stand-down with structure and cap.
  Use on FULL CHECK step 10–12, Five-new NBT, or "what's the ticket." Wait for go.
---

# Rank next best

Turn the battery into a ranked plan. This skill does **not** recapture news and
does **not** invent models. It ranks what FULL CHECK / NBT already measured.

Standing rules: [`../../STANDING_RULES.md`](../../STANDING_RULES.md).
Upstream: [`../event-gate-test/SKILL.md`](../event-gate-test/SKILL.md),
[`../five-new-nbt/SKILL.md`](../five-new-nbt/SKILL.md),
[`../print-readthrough-t1/SKILL.md`](../print-readthrough-t1/SKILL.md),
[`../miss-catch-sleeves/SKILL.md`](../miss-catch-sleeves/SKILL.md),
[`../sheet-latest-update/SKILL.md`](../sheet-latest-update/SKILL.md).

## When

- FULL CHECK after event gate + four-model + NBT
- Five-new NBT when choosing order among the hard five
- User says rank / next best / "what's the ticket" / "what do I take"

Refuse to rank if today's desk-sources access line is missing.

## Rank order (apply in this sequence)

1. **Event gate first** — `EVENT-GATE TEST` STAND or AH ≤ −5% veto **kills** a take.
   No credit through a print. High IV ≠ exception. Leftover short premium into a
   print ranks as a **close** ticket, not a new credit.
2. **Sheet plan** — Honor the live `TradePilot-26Q3` latest row (`is_latest=Y`):
   existing clocks, structures, and comments. Do not silently replace a live clock
   with a new name unless the old clock is dead (killed, flattened, or go missed).
3. **EM gates** — Hard take / hard NBT needs **EM > 15%**. EM 10–15% is miss-catch
   sleeve A (Soft-EM), not a padded hard slot. EM < 10% is stand-down unless it is
   a MANAGE flatten (sleeve C).
4. **Three Good** — Put-credit **eligibility only**. A failed Three Good does
   **not** veto a call debit. A passed Three Good does **not** force a put credit
   into a print or a Soft-EM rip.
5. **Prefer STNOW green + whale ≥ 0** — Among survivors, rank STNOW green (or
   GO-on-confirmation) with Whale ≥ 0 above mixed/red. Whale < 0 is not a hard
   take unless the user already said go on a MANAGE flatten.
6. **One-name rule** — Delivery `#1` is a single name. Do not ask the user to
   pick among five equals. The other four stay 🟡 arm / 🔴 stand-down with clocks.
   After a 0d AMC/BMO beat/raise or AH ≥ +5%, `#1` may be the unripped peer
   from `print-readthrough-t1`. Fail the rank if that table is required and missing.
7. **Clocks** — First-30 is 9:30–10:00 ET. No go before 9:30 = miss (DE/WMT/INTU).
   Same-session flatten on catalyst debits. Do not rank a first-30 ticket after
   the clock is dead.

## Output (every ranked row)

Each row is **take / arm / stand-down** and must include:

| Field | Required |
|---|---|
| Verdict | 🟢 take / 🟡 arm / 🔴 stand-down |
| Ticker | yes |
| Structure | debit/credit, strikes, expiry, **cap** |
| Clock | first-30 / T+1 / MANAGE / none |
| Gate | `EVENT-GATE TEST` verdict or `clean` |
| Why | one line (Sheet plan / EM / STNOW+whale / clock) |

**"No credit sell" is not a row.** If you stand down, still show the structure you
would have used if the trigger printed.

```markdown
## Ranked plan
1. 🟢 take  <TICKER>  <structure>  cap <$>  clock <…>  gate <…>
2. 🟡 arm   …
3. 🔴 stand-down …
WAIT FOR GO
```

## Hard rules

1. **Event gate first.** No credit through a print.
2. **Sheet plan wins ties** against a new idea with the same EM.
3. **Three Good does not veto a call debit.**
4. **Prefer STNOW green + whale ≥ 0.**
5. **One-name rule** on the take.
6. **Wait for go.** This skill never places.
7. CREDITS rates sleeve ranks in its own block, never as equity `#1`.
8. Reddit / miss-catch D cannot become `#1` without all-four + EM > 15%.
