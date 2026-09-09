# Trade Pilot tasks

Copy the matching checklist into the turn and tick it. Do not start a domain task on the other domain's checklist.

## Session start

```
- [ ] Identity: Trade Pilot (this repo). Not a second agent named ssr-st or arr-analyst.
- [ ] Route the first user turn to trading or ARR. If unclear, ask.
- [ ] Trading: wait for go. ARR: no self-signature; Snowflake reads only.
```

## Trading — first check of the day

```
- [ ] Read agents/ssr-st/workspace/Documents/agent_learning_log.md
- [ ] Read agents/ssr-st/workspace/Documents/catalyst_cards.md (confirm / fire / kill)
- [ ] Run python3 agents/ssr-st/workspace/Documents/market_data/daily.py (paths may still say ssr-analyst)
- [ ] Manage open book (stops, GTC, abort)
- [ ] Surface ≥1 vetted idea (strikes, size, stop) OR an explicit stand-down
- [ ] Wait for go before any order
```

## Trading — FULL CHECK

```
- [ ] Run the 12 steps in agents/ssr-st/commands/FULLCHECK.md
- [ ] Step 8: `ibd-wsj-capture` live IBD lists (no paste); SelfIDB50 FFTY only if Sign In still blocks after Take Control
- [ ] Step 9 news: load `news-portals` + `ibd-wsj-capture`. **SSO (confirmed 2026-09-09):** Log in **once at WSJ** (`https://www.wsj.com/`). Then open **IBD from the WSJ header**. That autologins IBD + MarketWatch + Barron's. Do **not** start at `https://www.investors.com/?ibdsilentlogin=true` unless the WSJ header IBD link is missing. Playwright MCP is valid; RSS is the floor, not a substitute
- [ ] Fail if IBD 50 is not live today (as-of not today / empty tables) unless Sign In blocked after Take Control; fail if Sector Leaders / Big Cap 20 / Spotlight / New Highs / RS / IPO / Funds URLs were not opened; fail if the agent asked for a paste
- [ ] Fail if WSJ, header IBD, MarketWatch, or Barron's was not actually opened
- [ ] Fail if the investor-day / analyst-day / capital-markets-day query was not run on book + SMH/memory/AI + READTHROUGH peers
- [ ] Fail if a 0d/1d name has no `{TICKER} earnings` line (OKTA 8/26), or a PPS-T7 ON name has no ticker-earnings line
- [ ] Fail if calendar UNION is missing a leg: Nasdaq `earnings_radar` ∪ Robinhood `get_earnings_calendar` ∪ fundamentals ∪ investor-day
- [ ] Fail the run if PPS-T7 / PPS-T1 flags are missing from the ranked table, or a 2–7d category print is missing from `print_monitor.md`
- [ ] Fail if a printed name already ≥+7% AH is ranked as a chase (`post-print-gap-capture`)
- [ ] Fail if analog ≥1.5× EM has no second-name written ticket (`print-analog-vs-em` + `next-25-print-screen`)
- [ ] Fail if a debit in the five has no liquidity line (mid / natural / OI / cap)
- [ ] Fail if MANGOS pulse is omitted or left n/a with no live-quote fallback
- [ ] Fail if only the 11 GICS ETFs are ranked (need industry sleeves: GDX/IGV/SMH)
- [ ] Fail if any open position lacks a GTC status and abort line
- [ ] Fail if any ranked / NBT / book row omits STKK · STNOW · 3Good · Whale
- [ ] Fail if `daily.py` whale n/a skips Whale Watch — run `whale_check.py` (8/26)
- [ ] Fail if a credit is routed through a print / CPI / PCE / FOMC window
- [ ] Fail if the five recycle last session's unused names (NBT rewrite 9/2)
- [ ] Fail if Sheet or BQ is skipped or prior `is_latest=Y` rows are not flipped to N
- [ ] Load miss-fix skills on step 5: `pps-t1-em-recalibrate` · `print-ah-guesstimate` · `print-analog-vs-em` · `option-chain-liquidity-gate` · `post-print-gap-capture` · `next-25-print-screen`
- [ ] End with take / arm / stand-down, split options book vs Agentic sleeve
- [ ] Overwrite catalyst_cards.md, next_day_prep.md, momentum_watchlist.md
- [ ] Upsert daily_top5; write Google Sheet AND BigQuery (`is_latest=Y` on the new date only; `N` on older rows)
- [ ] Wait for go
```

## Trading — evening wrap

```
- [ ] After close. No orders.
- [ ] Catalyst cards + next_day_prep.md
```

## Sites — publish universe

```
- [ ] tradepilot sites-publish --html-only
- [ ] If secrets/credentials.json exists: tradepilot sites-publish (--login if no token)
- [ ] Return HTML path + Google Doc link + any listed Sites
- [ ] Publishing is not go
```

## ARR — FQC-ARR ticket

```
- [ ] jira-intake
- [ ] requirements-analyzer
- [ ] code-data-validator
- [ ] clarifier (gate)
- [ ] implementer
- [ ] test-runner
- [ ] pr-author (gate)
- [ ] ci-monitor
- [ ] cd-monitor
- [ ] qa-handoff (gate)
- [ ] No agent signature on Jira / Slack / PR
- [ ] No unattended prod dbt
```

Packed automation drafts (finalize in the Agents Window, not from this skill): `agents/arr-analyst/workspace-automations/`.
