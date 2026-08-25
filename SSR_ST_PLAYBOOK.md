# SSR-ST playbook

Operating manual for TradePilot **except** `agents/arr-analyst/`. Compiled 25 Aug 2026 on branch `TP-08-25-2026` from commands, skills, workspace docs, plans, shared rules, discussions, and the TradePilot CLI.

This file is the index. Canonical details stay in the linked paths. Packed snapshot — live quotes, Robinhood MCP, and loops still assume the original `ssr-analyst` machine unless paths are retargeted.

**Out of scope:** `agents/arr-analyst/` (FQC-ARR / eda-dbt-em).

---

## 1. What this agent is

Personal **short-term / options-income** agent (`ssr-st`, also called SSR-ST / ssr-analyst).

| Book | Size (packed) | Instruments | Who can place |
|---|---|---|---|
| Income / margin | ~$50k–$60k | Defined-risk spreads (options L3) | Human, unless `agentic_allowed` is on |
| Agentic sleeve | ~$1k cash | Shares + long options only (L2). No multi-leg | Agent, after **go** |
| Equity sleeve (SSR-EQ) | Same personal account | Shares, rotation away from stacked tech | Separate rules from options |

**North star:** 1–2 green closes per trading day via a rolling 6–8 position book and 50% GTC takes. Measure over a **rolling 5-day window**. Never force a trade to hit the number. A logged **stand-down** counts as doing the job.

**Hard wait:** FULL CHECK and tickets are **read-only until the user says `go`**.

Repo CLI (this checkout): `tradepilot` 0.1.0 — `version` / `doctor` only. It does not run the trading battery.

---

## 2. Commands

Triggers the user types. Paths under `agents/ssr-st/commands/`.

| Command | Triggers | What it does | Spec / skill | Script |
|---|---|---|---|---|
| **FULL CHECK** | `FULL CHECK`, `fullcheck`, `full check` | 12-step battery. Ranked take / arm / stand-down. Writes catalyst cards + next-day prep + momentum watchlist | `skills/trading-continuous-learning/SKILL.md` | Loop: `workspace/strategy_battery_loop.sh` |
| **Health Check** | `Health Check` [tickers] | 4-model composite → one VERDICT per name. Off unless typed | `skills/health-check/SKILL.md`, `workspace/Documents/health_check_algorithm.md` | `workspace/Documents/market_data/health_check.py` |
| **STNOW** | `STNOW` [ticker] | 360° thesis. **Step 0 intake is mandatory** (account / entry / intent / size) | `skills/stnow-360-check/SKILL.md`, `stnow_algorithm.md` | — |
| **STKK / TASP** | `STKK` or `TASP` | Chart: regime, RSI, R:R ≥ 2, entry/stop/target | `skills/trade-entry-exit-pricing/SKILL.md`, `trade_entry_exit_algorithms.md` | `stkk_from_cache.py` |
| **Three Good** | `Three Good` / `THREE GOOD` | Bull put credit below 10-week weekly support | `skills/three-good-put-credit/SKILL.md`, `three_good_put_credit_strategy.md` | — |
| **SelfIDB50** | `SelfIDB50` | Momentum discovery (FFTY + `rs_screen.py` + anti-chase) | `workspace/Documents/momentum_watchlist.md` | `workspace/rs_screen.py` |
| **Whale Watch** | `Whale Watch` | Vol vs OI, IV/skew. Stale on a **live** catalyst — ignore and read tape | `whale_check_algorithm.md` | `whale_check.py` (command file path is wrong; use `workspace/Documents/market_data/`) |
| **Evening wrap** | evening wrap / next-day prep | After close, **no orders**. Cards + `next_day_prep.md` | `skills/evening-wrap-nextday-prep/SKILL.md` | `workspace/evening_wrap_loop.sh` |
| **daily.py** | `daily.py` / `--quick` / `SYM …` | Session pipeline: refresh, macro, MANGOS, earnings, Health Check | `commands/DAILY.md` | `workspace/Documents/market_data/daily.py` |
| **Tomorrow** | `Tomorrow` | Next-session UP/FLAT/DOWN from 7 blocks. Off unless typed | `skills/tomorrow-market-predictor/SKILL.md` | Log: `tomorrow_predictions_log.md` |

### FULL CHECK — 12 steps (in order)

1. Tape / macro — SPY, QQQ, SMH, VXX, 10Y  
2. Cross-sector GICS ETF gate — all 11, no tech-first bias  
3. Book health — cushion, short-leg delta, GTC, abort  
4. Health Check composite  
5. Event gate **and** T+0/T+1 catalyst cards (required; “no credit” is not a card)  
6. STKK + STNOW + Three Good on finalists  
7. Whale Watch  
8. SelfIDB50  
9. WSJ / MarketWatch + required investor/analyst/capital-markets-day search  
10. Direction × IV routing  
11. Backtest new structures (`backtest_strategies.py --md`) — promote only if RoR improves  
12. Ranked plan + overwrite `catalyst_cards.md`, `next_day_prep.md`, `momentum_watchlist.md`

**Invocation conflict:** Health Check, STNOW, Three Good, STKK, and Tomorrow are `disable-model-invocation` / “only when typed.” FULL CHECK still requires those models as sub-steps. Prefer: FULL CHECK may run them; standalone triggers stay for one-off runs.

---

## 3. Strategy

Primary skill: `agents/ssr-st/skills/trading-continuous-learning/SKILL.md`.  
Operating system: `agents/ssr-st/workspace/Documents/monthly_income_plan.md` (last updated 23 Jun 2026; $50k-calibrated).

### Decision spine

```
Tape + GICS → book health → Health Check (STKK + STNOW-proxy + Three Good + Whale)
  → event gate + catalyst cards → finalist STNOW/STKK → whale → SelfIDB50
  → news → direction × IV → backtest → ranked plan → wait for go
```

Health Check STNOW is **T + A + W** (trend, analyst, whale), not the 6-lens STNOW skill (P / A / N / H / M). Do not mix the scores.

### Direction × IV matrix

| | Low IV (≲40–50%) — buy premium | High IV (≳50%) — sell premium |
|---|---|---|
| **Bullish** | Call debit spread | Put credit (Three Good) |
| **Bearish** | Put debit spread | Call credit / bear call |
| **Range** | Calendar / diagonal | Iron condor |

Backtest (packed): call debit **+15.6% RoR**; put credit **+3.5%** (live better via vol-risk premium); gated multi-strategy **+5.87% RoR** while standing down **27%** of the time. Iron condor and bearish legs lost in that bull sample — insurance, not the core.

### Selection filter (all must pass)

- Ranked scan (GO or a clear fade level)  
- Structure matches the matrix  
- Cushion ≥ 8–10% (credit) or R:R ≥ 2:1 (debit)  
- Credit / width ≥ 25% (HOOD lesson: 84% win rate still lost money)  
- Liquid chain  
- **No earnings / CPI / PCE / FOMC in the window**  
- Sector / theme cap 1–2; do not stack eight bullish credits into a topping tape  

### Sizing and exits (income book)

- Win target **$300–500** per close; max loss **≤ 3% (~$1,500)**  
- Max **6–8** names; collateral **≤ 25–30%**  
- Monthly circuit breaker **−6%** → stop opening  
- Profit: GTC BTC at **50%** (whippy) to **60–80%** (clean)  
- Stop: **close** below short strike (credit) or spread **−50%** (debit); judge the close, not the wick  
- Time: close/roll before expiry week  

### Three books — do not bleed rules

1. **Options income** — spreads, event gate, Three Good / matrix.  
2. **Agentic $1k** — `skills/agentic-whale-short-term-trading/SKILL.md`. No blind dip-limits. Recycle ~+1.2–1.8% under resistance. 1–2 names. Sell only after buy fills.  
3. **SSR-EQ shares** — `equity_strategy.md`. Five-factor scorer; rotation leaders scan; underweight stacked tech vs the options book.

STNOW Step 0: **ask which account** (`account_profiles.md`). SPCX lesson: $1k rules must not apply to a personal IPO allocation.

### MANGOS

Daily AI-leadership pulse: **M**eta, Anthropic proxy (GOOGL/AMZN), **N**vidia, **G**oogle, **O**penAI proxy (MSFT), **S**paceX (SPCX). Lead “today’s plan” with this, then the book, then the idea.

### Bellwether read-through

If a mapped bellwether is **≥5%** **or** a mapped peer is **≥7%**, same-session defined-risk debit + same-day exit. Do **not** chase T+1 (SNDK 6/26). Maps: MU→SNDK/WDC/STX/NTAP; NVDA→AVGO/AMD/TSM/SMCI/CRWV; AVGO→NVDA/AMD/MRVL; TSLA→RIVN/CHPT.

---

## 4. Plans

Handoff history: `agents/ssr-st/plans/ssr_analyst_trading_agent_history.md` (compiled 30 Jun 2026).

FULLCHECK write-ups (Aug 2026):

| File | Session |
|---|---|
| `plans/fullcheck_2026-08-12.md` | 12 Aug |
| `plans/fullcheck_2026-08-12_chips_wday.md` | chips / WDAY overlay |
| `plans/fullcheck_2026-08-13.md` | 13 Aug (XE / SNDK miss window) |
| `plans/fullcheck_2026-08-14.md` | 14 Aug |
| `plans/fullcheck_2026-08-15.md` | 15 Aug |
| `plans/fullcheck_2026-08-17.md` | 17 Aug |
| `plans/fullcheck_2026-08-18.md` | 18 Aug |
| `plans/fullcheck_glw_mrvl_hd_2026-08-18.md` | GLW / MRVL / HD |
| `plans/fullcheck_2026-08-19.md` | 19 Aug |
| `plans/fullcheck_2026-08-20.md` | **Latest packed** — HOOD closed +$198; MS manage; DE/WMT killed; arm BJ |
| `plans/fullcheck_crosscheck_aug11_earnings_sentiment.md` | earnings/sentiment cross-check |

Companion canvases: `agents/ssr-st/canvases/fullcheck-*.canvas.tsx` (and a few named screens).

Live rolling plans (overwrite each FULLCHECK / evening wrap):

- `workspace/Documents/catalyst_cards.md`  
- `workspace/Documents/next_day_prep.md`  
- `workspace/Documents/options_watchlist.md`  
- `workspace/Documents/momentum_watchlist.md`  
- `workspace/Documents/trading_watchlist.md`  

---

## 5. Rules

### 5.1 ssr-st standing rules (always enforce)

From `AGENTS.md`, learning README, and continuous-learning skill:

1. Defined-risk only.  
2. **Never sell premium through earnings / CPI / PCE / FOMC.**  
3. User hint on a ticker = full Health Check **including earnings calendar**.  
4. Catalyst card required for every T+0/T+1 event. “No XE anything” is the event gate, not the plan (`rules/catalyst-overnight-cards.mdc`).  
5. First 15–30 minutes for armed catalyst **debits**; unarmed chase after +7% = stand down.  
6. Close leftover short premium **T−1** before a print.  
7. Do not chase a post-print gap as a hold or with a credit sell.  
8. One max loss ≈ 3–6 wins — size for the tail.  
9. Bullish core (put credit + call debit); bearish only on confirmed breakdown.  
10. Verify what the ticker **is** (NNE ≠ BTC; MARA is the miner).  
11. Wait for **go**. Never force the daily number.  
12. Calendar = Nasdaq radar **UNION** Robinhood calendar **UNION** fundamentals **UNION** investor-day web search.

Workspace copy: `agents/ssr-st/rules/catalyst-overnight-cards.mdc` and `workspace/.cursor/rules/catalyst-overnight-cards.mdc`. Both still write `ssr-analyst/Documents/catalyst_cards.md` — retarget to `agents/ssr-st/workspace/Documents/`.

### 5.2 Shared rules (`shared/rules/`)

Workday ARR playbook (Jira curl, Snowflake/dbt MCP, inbox → Slack at 8/11/2/3 PT) was **removed** from `shared/`. `agents/arr-analyst/` was left unchanged.

| File | For ssr-st |
|---|---|
| `cross-check-before-answer.mdc` | **Keep** — dates, weekdays, numbers, tickers |
| `professional-writing.mdc` | Optional — ticket style is take / arm / stand-down |
| `documents-output-folder.mdc` | **Retarget or drop** — hardcoded other-machine Documents path; FULLCHECK files stay in workspace |

Matching skills: `shared/skills/cross-check-before-answer/`, `shared/skills/professional-writing/`.

### 5.3 Off-strategy skill in the ssr-st workspace

`workspace/.cursor/skills/bay-area-pdx-flights/` — OAK/SFO/SJC ↔ PDX. From discussion “Flight tickets.” Not part of FULL CHECK.

---

## 6. Tasks

### Session start (first “check” of the day)

```
- [ ] Read agent_learning_log.md (lessons, open items, tomorrow’s first-check)
- [ ] Read catalyst_cards.md — confirm / fire / kill overnight cards
- [ ] Run: python3 agents/ssr-st/workspace/Documents/market_data/daily.py
      (fallback: --quick, or SYM …; if scripts fail, Health Check + earnings_radar.md)
- [ ] Manage open book (stops, GTC, abort)
- [ ] Surface ≥1 vetted idea (strikes, size, stop) OR an explicit stand-down
- [ ] Wait for go before any order
```

### FULL CHECK (on demand or loop)

Run the 12 steps. Fail the run if any 0d/1d event has no card. End with 🟢 take / 🟡 arm / 🔴 stand-down, split options book vs $1k sleeve.

### Evening wrap (~6 PM PT, after AH)

No orders. Eight sweeps: close+AH, news (+ investor-day query), whale, analyst ratings, next-day levels, catalyst calendar+cards, regime, oversold-bounce **offense** arm. Write `next_day_prep.md`. Loop prompt is still 7 steps — skill is 8.

### Weekly cadence (income plan)

| Day | Task |
|---|---|
| Mon | Full-universe Health Check + Tomorrow/macro → week shortlist |
| Tue–Thu | Open 3–4 spreads **only** on confirmed holds |
| Daily | Manage book; GTC; close-below-strike |
| Fri | Log P&L; no new high-risk into the weekend |
| Month-end | KPI; resize |

### Scheduled loops (packed; DIR still old machine)

| Loop | PT slots | Job |
|---|---|---|
| `strategy_battery_loop.sh` | 08:00, 11:00, 13:00 | FULL battery (prompt still says 5-transaction plan — lag vs 12-step) |
| `market_check_loop.sh` | 08:30, 12:30, 15:00 | Agentic portfolio + recycle |
| `evening_wrap_loop.sh` | ~18:00 | Evening wrap |

### Lesson capture (required)

Append to `workspace/Documents/agent_learning_log.md`, newest first:

```markdown
### YYYY-MM-DD — <title>  [MISS | WIN | RULE | BACKTEST]
- **What happened:**
- **Root cause:**
- **Rule / fix:**
- **Status:** pending build | adopted | validated
```

Triggers: missed move, user hint not fully checked, any gate/size/matrix change.

### Packed snapshot tasks (from FULLCHECK 20 Aug 2026 — **re-pull live before acting**)

These are historical tickets from `catalyst_cards.md` / `next_day_prep.md`, not live orders.

- MS Sep 18 210/200 — manage; abort $210 or mid ≥ $4.50  
- HOOD 85/80 ×3 — closed +$198; do not replace that session  
- MARA shares — hold; no new puts; invalidation was $9.80 that day  
- BJ Fri BMO — was armed as WMT sympathy debit  
- No new credit through 8/26–8/27 mega prints (CRM, CRWD, NVDA, MRVL, …) at that time  

---

## 7. Skills (`agents/ssr-st/skills/`)

| Skill | Role |
|---|---|
| `trading-continuous-learning` | Session OS, FULL CHECK spec, cadence, lessons |
| `health-check` | 4-model composite |
| `stnow-360-check` | 6-lens thesis + value-trap + IPO branch |
| `trade-entry-exit-pricing` | STKK / TASP levels |
| `three-good-put-credit` | Put credit algorithm |
| `agentic-whale-short-term-trading` | $1k sleeve |
| `evening-wrap-nextday-prep` | EOD |
| `catalyst-overnight-plan` | T+1 cards |
| `catalyst-overnight-plan-workspace` | Duplicate of catalyst-overnight-plan |
| `tomorrow-market-predictor` | Next-session lean |

---

## 8. Workspace files and scripts

All under `agents/ssr-st/workspace/` unless noted.

**Markdown OS**

| File | Role |
|---|---|
| `Documents/agent_learning_log.md` | Lessons + tally + first-check |
| `Documents/AGENT_LEARNING_README.md` | How learning works |
| `Documents/monthly_income_plan.md` | Cadence, matrix, sizing |
| `Documents/account_profiles.md` | $1k vs personal |
| `Documents/options_watchlist.md` | Play cards / armed / open |
| `Documents/trading_watchlist.md` | Names + MANGOS |
| `Documents/equity_strategy.md` | SSR-EQ shares |
| `Documents/catalyst_cards.md` | Overnight tickets |
| `Documents/next_day_prep.md` | Morning warm-start |
| `Documents/momentum_watchlist.md` | SelfIDB50 layer |
| `Documents/earnings_radar.md` | Sell-gate vs directional |
| `Documents/backtest_multistrategy.md` | Expectancy |
| `Documents/market_history.md` | OHLCV cache |
| Algorithm specs | `health_check_algorithm.md`, `stnow_algorithm.md`, `whale_check_algorithm.md`, `three_good_put_credit_strategy.md`, `trade_entry_exit_algorithms.md`, `tomorrow_market_predictor.md` |

**Python (`Documents/market_data/` and workspace root)**

| Script | Role |
|---|---|
| `daily.py` | One-command session |
| `health_check.py` | Composite |
| `whale_check.py` | Nasdaq chain + IV |
| `stkk_from_cache.py` | Technicals from cache |
| `fetch_history.py` | OHLCV (output path still old machine) |
| `fetch_earnings.py` | Radar |
| `backtest_strategies.py` | Multi-strategy |
| `rs_screen.py` / `rs_multi.py` | Relative strength |
| `credit_sim.py` / `debit_sim.py` / `debit_test.py` / `breach_test.py` / `screen_debit.py` | Sims / tests |
| `next_slot.py` | Loop scheduling |

MCP: `workspace/.cursor/mcp.json` — Robinhood `https://agent.robinhood.com/mcp/trading`.

---

## 9. Discussions (except arr-analyst)

Index: `discussions/INDEX.json`, `CONTEXT_LAST_100_DAYS.md`. Tools stripped; secrets redacted (`SANITIZATION.md`).

**ssr-st (4 chats)**

| Date | Title | Turns | Why it matters |
|---|---|---|---|
| 30 Jun | Add mcp | 14 | Robinhood URL already in mcp.json; gap was OAuth |
| 9 Jul | hello | 9 | Isolate trading workspace from Snowflake/dbt/SF/Sigma |
| 31 Jul | Flight tickets | 24 | PDX skill; not trading |
| 25 Aug | SSR-ST | 1,587 | Live OS: two accounts, Health Check, DELL, wait-for-go, FULLCHECK named |

**other (3 chats)** — Advisor, Career Pilot AI, Refactoring-EM. Not the trading battery.

---

## 10. Repo glue (non-arr)

| Path | Role |
|---|---|
| `README.md` | CLI setup + packed agent index |
| `AGENTS.md` | Two-agent map (use ssr-st half only) |
| `tradepilot/` | CLI package |
| `tools/pack_from_local.py` | Re-pack from original machine (hardcoded paths) |
| `SANITIZATION.md` | What the packer redacts |

---

## 11. Path and pack warnings

- Skills, loops, and `fetch_history.py` still point at `/Users/koteswararao.venkata/Documents/Cursor/ssr-analyst`. This checkout lives at `agents/ssr-st/workspace/`.  
- WHALE.md / DAILY.md use `Documents/market_data/...` relative to the old workspace.  
- `strategy_battery_loop.sh` prompt lags the 12-step + catalyst-card spec.  
- Do not treat packed JSON caches or 20 Aug cards as live. Re-run scripts and MCP on a machine that has Robinhood + cache.

---

## 12. Quick start (this repo)

```bash
# CLI only
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
tradepilot doctor

# Trading battery (after retargeting paths / on original machine)
python3 agents/ssr-st/workspace/Documents/market_data/daily.py
# or: FULL CHECK in chat, wait for go
```
