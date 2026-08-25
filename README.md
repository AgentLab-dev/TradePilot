# TradePilot

An autonomous AI agent that monitors markets, plans trades, and reports risk.

## Requirements

- Python 3.11+

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Verify

Run the environment check:

```bash
tradepilot doctor
```

Expected output includes `Status: OK`.

Run the test suite:

```bash
pytest
```

Run the CLI help:

```bash
tradepilot --help
```

Packaged operating system for two Cursor discussion agents:

| Agent | Role |
|---|---|
| **ssr-st** | Short-term / options / income trading agent (`ssr-analyst`) |
| **arr-analyst** | Finance ARR quarter-close agent (FQC-ARR / `eda-dbt-em`) |

Source GitHub repo: [AgentLab-dev/TradePilot](https://github.com/AgentLab-dev/TradePilot)

This dump was packed **25 Aug 2026** from the live Cursor + Claude skill trees, the `ssr-analyst` workspace, FQC-ARR bundles, and **the last 100 days** of Cursor agent transcripts (17 May 2026 → 25 Aug 2026).

## Start here

1. [`CONTEXT_LAST_100_DAYS.md`](CONTEXT_LAST_100_DAYS.md) — index of every extracted chat + named operations
2. [`agents/ssr-st/commands/FULLCHECK.md`](agents/ssr-st/commands/FULLCHECK.md) — the 12-step trading battery
3. [`agents/arr-analyst/commands/FQC_ARR.md`](agents/arr-analyst/commands/FQC_ARR.md) — the 10-role ARR DAG
4. [`discussions/`](discussions/) — full chat text (tools stripped, secrets redacted)

## Layout

```
TradePilot/
├── CONTEXT_LAST_100_DAYS.md
├── tradepilot/          CLI agent package
├── agents/
│   ├── ssr-st/          skills, commands, rules, plans, canvases, workspace
│   └── arr-analyst/     FQC skills, Sana bundle, dist, eda-dbt-em .cursor files
├── discussions/         last-100-days chats (ssr-st / arr-analyst / other)
├── shared/              rules + shared skills
└── tools/pack_from_local.py
```

## ssr-st named commands

| Trigger | What |
|---|---|
| `FULL CHECK` | 12-step battery (tape, GICS, book, Health Check, event gate + catalyst cards, STKK/STNOW/Three Good, whale, SelfIDB50, news, IV matrix, backtest, ranked plan) |
| `Health Check` | STKK + STNOW + Three Good + Whale → one verdict |
| `STNOW` | 360° pre-trade (intake first) |
| `STKK` | Chart / regime / levels |
| `Three Good` | Put credit spread below 10-week support |
| `SelfIDB50` | Momentum discovery |
| Evening wrap | After-close prep → `next_day_prep.md` |
| Whale Watch | Volume vs OI / IV |
| `daily.py` | Session pipeline |

Read-only by default: surface tickets, wait for **go** before orders.

## arr-analyst named commands

FQC-ARR supervisor DAG: jira-intake → requirements-analyzer → code-data-validator → clarifier → implementer → test-runner → pr-author → ci-monitor → cd-monitor → qa-handoff. Plus debugger and quarter-close-runner.

Workspace commands from `eda-dbt-em`: inbox-action-items, fcq-arr-regression-test, product-hierarchy-recon-test.

## Secrets

Public repo. Tokens, Robinhood account ids, and work emails were redacted on pack. See `SANITIZATION.md`. Do not paste live credentials back into this tree.

## Re-pack from the original machine

```bash
python3 tools/pack_from_local.py
```
