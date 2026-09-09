---
name: sheet-latest-update
description: >-
  Mandatory Google Sheet latest-book write after every FULL CHECK, NBT, evening
  wrap, or lessons run that has picks. Tab TradePilot-26Q3 only. Fill ALL
  columns, flip prior is_latest Y→N, sort Y on top, require a why in comments,
  no skeleton rows. Use whenever the live desk book or NBT changes. Spreadsheet
  1RkdF93AK7BWRf0SktGVrHehG0XU_nz21WCzSrAP68vQ.
---

# Sheet latest update

The Sheet is the live source of truth for picks and flags. A FULL CHECK / NBT /
wrap / lessons run that produced picks **must** write here. Partial rows are a miss.

Standing rules: [`../../STANDING_RULES.md`](../../STANDING_RULES.md).
Source map: [`../../WHERE_LATEST_INFO_LIVES.md`](../../WHERE_LATEST_INFO_LIVES.md).
`new-feature` tab is a **different** skill: [`../daily-new-feature/SKILL.md`](../daily-new-feature/SKILL.md).

## When (mandatory)

After every run that has picks:

- FULL CHECK / Health Check battery
- Five-new NBT
- Evening wrap **if the book changed** (new clock, kill, flatten, or NBT rotation)
- Daily desk lessons **if picks moved**

Skip only when the parent skill says the book did not change (evening wrap / lessons
with zero pick movement). "Forgot" is not a skip.

## Where

- Spreadsheet id: `1RkdF93AK7BWRf0SktGVrHehG0XU_nz21WCzSrAP68vQ`
- URL: https://docs.google.com/spreadsheets/d/1RkdF93AK7BWRf0SktGVrHehG0XU_nz21WCzSrAP68vQ/edit
- **Tab `TradePilot-26Q3` only** for this skill
- Published view (read-only): https://docs.google.com/spreadsheets/d/e/2PACX-1vQWnq16Jzrj91DqM1xlEukdqCpmI_3XnywQaQZ-l-tRN1-20pIsV38l3W7znjcOsSHuLJZyPzgFa7a-/pubhtml?gid=2024844456&single=true

Do not write latest-book rows onto `new-feature`. Do not create a new tab.

## Fill ALL columns (mandatory)

Every new latest row must fill **all** of these columns:

| Column | What |
|---|---|
| `date` | Session date `YYYY-MM-DD` |
| `execution_date` | When the ticket is meant to fire (session or T+1 date) |
| `ticker` | Symbol |
| `rank` | 1…n among current latest |
| `latest_flag` | Latest marker used by the Sheet views |
| `is_latest` | `Y` on the new current rows |
| `last` | Prior close / last official |
| `spot` | Live / AH spot used for the card |
| `stkk` | STKK flag |
| `stnow` | STNOW flag / raw |
| `three_good` | Three Good flag (put-credit eligibility only) |
| `whale` | Whale flag (≥ 0 for hard NBT) |
| `pps_t7` | PPS / plan metric T+7 |
| `pps_t1` | PPS / plan metric T+1 |
| `ibd` | IBD list membership (50 / SL / BC20 / none) |
| `gics` | GICS / industry |
| `ssr_eq` | Equity-sleeve flag if any |
| `dirxiv` | Direction × IV route |
| `bell` | Bellwether / read-through map |
| `sleeves` | Hard / A / B / C / D / CREDITS |
| `structure` | Strikes, expiry, debit/credit, **cap** |
| `clock` | first-30 / T+1 / MANAGE / none |
| `plan` | take / arm / stand-down |
| `snapshot_date` | When the four-model + EM snapshot was taken |
| `sort_date` | Sort key (latest `Y` rows sort on top) |
| `comments` | **Why** this row exists (required — see below) |
| `latest` | Companion latest marker if the tab uses it |

A blank required column is a **skeleton row**. Delete it and rewrite. Do not leave
`structure` or `comments` empty "to fill later."

## Flip prior Y → N

1. Find existing rows with `is_latest=Y` for names you are replacing or for the
   whole latest snapshot you are rotating.
2. Set those `is_latest` (and `latest_flag` / `latest` as the tab uses them) to **`N`**.
3. Insert / update the new rows with `is_latest=Y`.
4. **Sort `Y` on top.** `N` rows stay as history below.

Do not delete history. Do not leave two competing `Y` rows for the same ticker
unless the Sheet plan intentionally shows two live sleeves (call out why in
`comments`).

## Why `comments` is required

`comments` is the **why**, not a ticker repeat. It must answer at least one of:

- Why this name is `#1` / armed / stood down
- Which gate fired (`EVENT-GATE TEST STAND`, Soft-EM AH ≥ +5%, Whale < 0)
- Why a prior `Y` was flipped to `N` (clock dead, first-30 missed, EM failed)

A row with structure and no why is a miss.

## No skeleton rows

Forbidden:

- Ticker + blank models
- `is_latest=Y` with empty `structure` / `clock` / `plan`
- "TBD" / "later" / "see chat"
- Writing only `date` + `ticker`

If you cannot fill the row, do not write it. Fix the battery first.

## Hard rules

1. **Mandatory** after FULL CHECK / NBT / wrap / lessons **with picks**.
2. **Tab `TradePilot-26Q3` only.**
3. **ALL columns** in the table above.
4. **Flip prior Y → N. Sort Y on top.**
5. **`comments` = why.** Required.
6. **No skeleton rows.**
7. CREDITS rows stay `sleeves=CREDITS` and do not overwrite equity NBT `Y` rows
   unless the equity clock is actually dead.
8. This write is not an order. Wait for **go**.
