# Last 100 days of context

_Packed 2026-08-25 15:50 PT. Window: 2026-05-17 → 2026-08-25 (100 days)._

This file is the **index**. Full chat text (user + assistant, tools stripped, secrets redacted) lives under `discussions/`.

## Agents in this repo

| Agent | What it is | Home in this repo |
|---|---|---|
| **ssr-st** | SSR-analyst short-term / options discussion agent (FULLCHECK, Health Check, STNOW, STKK, Three Good, whale, evening wrap) | `agents/ssr-st/` |
| **arr-analyst** | FQC-ARR / eda-dbt-em finance ARR quarter-close agent | `agents/arr-analyst/` |

## Counts

- Chats extracted: **26**
- ssr-st chats: **4**
- arr-analyst chats: **19**
- other chats: **3**

## Named operations (ssr-st)

- `FULL CHECK` / fullcheck — 12-step battery (`agents/ssr-st/commands/FULLCHECK.md`)
- `Health Check` — 4-model composite
- `STNOW` — 360° pre-trade
- `STKK` — chart / levels
- `Three Good` — put credit spreads
- `SelfIDB50` — momentum discovery
- Evening wrap / next-day prep
- Whale Watch
- `daily.py` session pipeline
- Loops: `strategy_battery_loop.sh`, `market_check_loop.sh`, `evening_wrap_loop.sh`

## Named operations (arr-analyst)

- FQC-ARR supervisor DAG (10 roles + debugger + quarter-close-runner)
- `arr-quarter-close` workspace skill
- Commands: inbox-action-items, fcq-arr-regression-test, product-hierarchy-recon-test

## Chat index (newest first)

| Date | Agent | Title | File | Turns |
|---|---|---|---|---|
| 2026-08-25 | ssr-st | SSR-ST | `discussions/ssr-st/2026-08-25_0dc2e1e1-06c5-4296-a685-73d2b1e3912a_e7e3ccfb.md` | 1587 |
| 2026-08-25 | arr-analyst | Slack-Email-responses | `discussions/arr-analyst/2026-08-25_f7661e00-ebdd-4dea-941c-04df4aeac9ff_4f2a8bb8.md` | 47 |
| 2026-08-25 | arr-analyst | Agent Creation | `discussions/arr-analyst/2026-08-25_b83fe2d8-d6ac-4d71-8665-11ba202703f6_82fbf803.md` | 3243 |
| 2026-08-25 | arr-analyst | Refactoring - EM | `discussions/arr-analyst/2026-08-25_6401c5af-7473-4255-8b69-58efcea01b94_091f41da.md` | 4417 |
| 2026-08-24 | arr-analyst | add skills - office politics, managing the manager , and setting up proper tone … | `discussions/arr-analyst/2026-08-24_ce6c4f55-2150-4815-8d13-488b8a6a04c1_35a3d67f.md` | 1936 |
| 2026-08-19 | arr-analyst | GTM Next - Solution | `discussions/arr-analyst/2026-08-19_64446306-1a86-4cd1-a4d1-12ce9a24bc12_a724831e.md` | 658 |
| 2026-08-10 | arr-analyst | Workday Sana | `discussions/arr-analyst/2026-08-10_0f3b9f9a-6125-4e2d-b6a1-f941872a12cc_720e30e6.md` | 85 |
| 2026-08-04 | arr-analyst | SSR Agent | `discussions/arr-analyst/2026-08-04_8943f057-59bc-4a93-abf9-4ba4c0669633_2cb3e6d4.md` | 24 |
| 2026-07-31 | ssr-st | Flight tickets | `discussions/ssr-st/2026-07-31_63a4e52f-89d9-4a50-b0ad-deb2b025ffe1_2829078f.md` | 24 |
| 2026-07-29 | arr-analyst | Zuora Agent | `discussions/arr-analyst/2026-07-29_4576ab9a-14c7-4c07-8198-74e652b9e5ef_c307850e.md` | 95 |
| 2026-07-21 | arr-analyst | Explore the standalone Python application for the "FQC-ARR" (Finance ARR Quarter… | `discussions/arr-analyst/2026-07-21_subagents_75813fef.md` | 5 |
| 2026-07-16 | arr-analyst | You are auditing downstream impact in the **eda-dbt-gtm** repo (Workday ED&A sal… | `discussions/arr-analyst/2026-07-16_subagents_4d611aec.md` | 18 |
| 2026-07-16 | arr-analyst | You are auditing downstream impact in the **eda-dbt-cx** repo (Workday ED&A cust… | `discussions/arr-analyst/2026-07-16_subagents_bf92bf1a.md` | 17 |
| 2026-07-16 | arr-analyst | You are auditing downstream impact in the **eda-dbt-em** repo (Workday ED&A fina… | `discussions/arr-analyst/2026-07-16_subagents_a58bf263.md` | 15 |
| 2026-07-16 | arr-analyst | Goal: DEFINITIVELY determine whether the dbt model `models/redshift_history/base… | `discussions/arr-analyst/2026-07-16_subagents_05d872d0.md` | 14 |
| 2026-07-16 | arr-analyst | You are investigating dbt Cloud runs for the **eda-dbt-base** project (dbt Cloud… | `discussions/arr-analyst/2026-07-16_subagents_053143e5.md` | 7 |
| 2026-07-09 | ssr-st | hello | `discussions/ssr-st/2026-07-09_400f2d17-28e0-4bb4-a6ad-5ae9fb409532_c72ff46d.md` | 9 |
| 2026-07-05 | other | Advisor | `discussions/other/2026-07-05_6b37cc36-81fc-4802-be15-9adc6c974ea2_33fb2faf.md` | 126 |
| 2026-07-05 | other | Career Pilot AI | `discussions/other/2026-07-05_bbd888b2-f135-4a03-9073-8e52d0f212e4_235b6da1.md` | 19 |
| 2026-07-05 | arr-analyst | Advisor | `discussions/arr-analyst/2026-07-05_3241edd3-72c3-4c63-912d-b5f62a0e64e3_3e4a85c6.md` | 11 |
| 2026-07-01 | arr-analyst | ACV Reconciliation + QE | `discussions/arr-analyst/2026-07-01_d933bef1-de9f-42f2-8dc1-0ad514ee5939_172cfa04.md` | 2071 |
| 2026-06-30 | arr-analyst | SSR Analyst | `discussions/arr-analyst/2026-06-30_de5ec8c0-d4d7-4d06-858f-ad354c5ab19e_62f892aa.md` | 1422 |
| 2026-06-30 | ssr-st | Add mcp | `discussions/ssr-st/2026-06-30_3d2f3c91-6178-4023-bbbf-8a1907015cb8_d00726ea.md` | 14 |
| 2026-06-12 | other | Refactoring - EM | `discussions/other/2026-06-12_6401c5af-7473-4255-8b69-58efcea01b94_3b3d5ed5.md` | 3282 |
| 2026-06-12 | arr-analyst | Slack connection | `discussions/arr-analyst/2026-06-12_1a5e2f6a-b7b9-4495-853e-fda3ddde2217_3963e726.md` | 124 |
| 2026-06-11 | arr-analyst | ARR - Quarter Close | `discussions/arr-analyst/2026-06-11_9cc7a2bd-a4f1-402d-8491-c4a51739f8a6_991360d7.md` | 3229 |

## How this was built

1. Copied live skills from `~/.claude/skills` and `~/.cursor/skills`.
2. Copied `ssr-analyst` workspace (docs, scripts, loops, rules).
3. Copied FQC-ARR Sana bundle, dist bundle, and eda-dbt-em `.cursor` agent files.
4. Extracted Cursor `agent-transcripts` JSONL since 2026-05-17.
5. Redacted tokens, Robinhood account ids, and work emails.

Re-run: `python3 tools/pack_from_local.py`
