# SSR-Analyst Trading Agent — Complete History & Handoff

_Compiled: June 30, 2026. Covers the full build of the options/income trading agent from day 1 through the Robinhood-MCP setup. This is a readable history + a handoff doc for continuing the work in the `ssr-analyst` workspace._

- **Trading agent home:** `/Users/koteswararao.venkata/Documents/Cursor/ssr-analyst`
- **All trading files:** `ssr-analyst/Documents/` (watchlists, plans, logs, `market_data/` scripts)
- **Canonical deliverables folder:** `/Users/koteswararao.venkata/Documents/Cursor/Documents/`

---

## 1. What this agent is

A personal options/income trading assistant calibrated to a **~$50k account**, with the standing goal of **10–15 profitable closes per month at $300–500 each**, ideally **1–2 green closes per trading day**. It runs a multi-model decision stack, a multi-strategy options framework, a continuous-learning loop, and a one-command daily pipeline.

**Core principles that emerged:**
- Defined-risk spreads only; size to the $300–500 target with a hard ≤3% account loss cap (~$1,500).
- **Sell premium only into a confirmed hold; never into a slide or through a binary event.**
- Take profits fast (50–65% on credit spreads via GTC).
- A logged **stand-down** on a hostile tape counts as doing the job — never force a trade to hit a number.

---

## 2. The decision models (the "spine")

| Model | What it does | Data source |
|---|---|---|
| **STKK** | Chart/technical: regime (UP/DOWN/RANGE), RSI, R:R, support/level | local cache (`market_history.md`) |
| **STNOW** | 360° quant proxy: trend + analyst + flow + **value-trap gate** (news lens manual) | cache + whale |
| **Three Good** | Put-credit-spread eligibility (IV ≥ 50% & flow ≥ 0 & not breaking down) | whale IV |
| **Whale Check** | Institutional options flow + IV/skew → BULLISH/NEUTRAL/BEARISH, −2..+2 score | live Nasdaq chain |
| **Health Check** | The 4-model composite → one VERDICT per name | all of the above |
| **Tomorrow** | Next-session market direction (cross-asset risk tilt) | live cross-asset |

**IV-routing matrix (structure follows direction × IV):**
- Bullish + low IV → **call debit spread** (buy, theta small)
- Bullish + high IV → **put credit spread** (sell, IV crush + theta tailwind)
- Bearish + high IV → call credit spread
- Bearish + low IV → put debit spread
- Range + high IV → iron condor

---

## 3. System files & scripts (`ssr-analyst/Documents/`)

**Markdown "database":**
- `trading_watchlist.md` — primary watchlist & playbook (incl. 🥭 MANGOS daily cross-check)
- `options_watchlist.md` — live play cards, armed trades, open positions, backtests
- `monthly_income_plan.md` — the operating system (cadence, sizing, exits, strategy matrix), $50k-calibrated
- `agent_learning_log.md` — running memory: lessons + month tally + "tomorrow's first-check" (**read first every session**)
- `AGENT_LEARNING_README.md` — explains the continuous-learning system
- `backtest_multistrategy.md` — strategy expectancy results
- `earnings_radar.md` — upcoming earnings (sell-gate / directional flags)
- `market_history.md` — cached OHLCV
- `tomorrow_market_predictor.md`, `tomorrow_predictions_log.md` — next-session model
- algorithm docs: `health_check_algorithm.md`, `stnow_algorithm.md`, `whale_check_algorithm.md`, `three_good_put_credit_strategy.md`, `trade_entry_exit_algorithms.md`
- `account_profiles.md`, `ipo_watch.md`, `ntap_list.md`

**Python (`market_data/`):**
- `daily.py` — **the one command** (full pipeline; see §7)
- `health_check.py` — 4-model composite
- `whale_check.py` — Nasdaq options-flow + Black-Scholes IV engine
- `stkk_from_cache.py` — technicals from cache
- `fetch_history.py` — OHLCV fetch (with `--delta`)
- `fetch_earnings.py` — Nasdaq earnings calendar → radar
- `backtest_strategies.py` — 6-strategy + multi-strategy backtester

**Skill:** `~/.cursor/skills/trading-continuous-learning/SKILL.md` — governs the learning loop, session ritual, gates, cadence rule.

---

## 4. Timeline (day by day)

### Early — framework & first position
- Built the **monthly income plan** ($50k account; 10–15 trades/mo @ $300–500), capital model, cadence, sizing, exits, drawdown control, event calendar.
- Planned a **GOOGL call debit** (370/390, ~$712 debit, ~$1,288 max) as the directional template.
- Ran repeated Health Checks; built the watchlist (MARA, HOOD, ORCL, SNOW, MNDY, etc.).
- **NNE put credit opened (Jun 22):** Sell $23P / Buy $20P · Jul 17 · 5 contracts · **$0.80 credit (~$400)** · max loss ~$1,100. Sizing intentional for the $300–500 target; edge = ~80% win rate, not per-trade payoff.

### Multi-strategy expansion
- User pushed back on single-strategy focus → reworked the plan to a **multi-strategy** approach (call/put debit & credit, iron condor, calendar) routed by the direction × IV matrix.
- Built **`backtest_strategies.py`** (Black-Scholes priced, 2-yr weekly entries). Naive routing underperformed → added an **adaptive event gate + confirmation filter** (v2 router), which beat the put-credit-only baseline by avoiding bearish trades in a bull tape and binary events.

### Jun 24–25 — the MU miss & continuous learning
- **MU reported (6/24 AH), popped ~+15.7% on 6/25.** Agent failed to flag it proactively despite a user hint.
- Built **`fetch_earnings.py`** + `earnings_radar.md`; added the rule: **a user hint = run a full Health Check incl. earnings calendar.**
- Added the **`trading-continuous-learning` skill**, `agent_learning_log.md`, `AGENT_LEARNING_README.md` — permanent learning mode toward 1–2 green/day.
- **"Policy-put" thesis** logged (user view: administration props top-20 names pre-midterms).

### Jun 25 — MANGOS & the NNE correction
- **🥭 MANGOS** introduced (AI-leadership basket): **M**eta · **A**nthropic(proxy GOOGL/AMZN) · **N**vidia · **G**oogle · **O**penAI(proxy MSFT) · **S**paceX. Tradeable four: **META, NVDA, GOOGL, SPCX**. Added to the daily cross-check.
- **CORRECTION [MISS]:** NNE was wrongly called a "Bitcoin proxy." NNE = **NANO Nuclear Energy** (SMR microreactors). Fixed everywhere; reframed its driver as nuclear/AI-power theme + high-beta risk appetite (gauge via **QQQ**, not BTC). The real BTC proxy is **MARA** (miner).
- Ran a 3-month NNE dip-recovery base-rate analysis (sub-$21 → reclaim $23 median ~3 trading days; slow-bleed analog took 20 td).

### Jun 25 — the one command
- Built **`daily.py`** orchestrator: refresh → earnings gate → macro + Tomorrow tilt → MANGOS → Health Check composite → ranked candidate. Wired in as the canonical "what's today's plan" command.

### Jun 26 (Fri) — read-through radar
- **MISS logged:** MU's pop should have auto-triggered a NAND/storage sympathy scan — **SNDK ran +22% on 6/25** and was missed (and the Whale flag said AVOID *while it ripped*, because it uses prior-session volume).
- Built the **bellwether read-through** into `daily.py`: when a bellwether moves ≥7% in a session, auto-scan its peers and flag same-day momentum (exit same session; disregard the stale Whale flag). Map: MU→SNDK/WDC/STX/NTAP/semis · NVDA→AVGO/AMD/TSM/SMCI/CRWV · AVGO→semis · TSLA→RIVN/CHPT/LCID · ORCL/CRM→SaaS.
- Fixed a staleness bug so it reads the **most recent** session move only.
- **Friday outcome:** risk-[REDACTED] tape → **stood down**. No new position. The discipline paid: HPE (a candidate) broke down −6.4% — not chasing saved a loss. NNE closed **$19.87** (below the $20 abort) — decision point.

### Jun 29 (Mon) — armed trades meet a risk-[REDACTED] open
- Armed Fri night: **GOOGL** Jul31 340/350 call debit + **SNOW** Jul31 225/215 put credit, both as Monday confirmation triggers.
- Monday opened strong risk-[REDACTED]. **GOOGL gapped +4.8% past the short strike → SKIPPED** (chasing a gap = #1 don't). **SNOW held cleanly → adjusted up to 230/220** put credit (original credit had shrunk to $2.00).
- **NNE bounced +7%** off Friday's low (riding risk-[REDACTED] QQQ +2.5%), tagged ~$22.40 — the hold thesis working; GTC target left to ride.
- Specced a **MARA** put credit (Sell 12.5/Buy 11.5, IV 95%, 10.9% cushion) — real BTC proxy; abort if BTC < $57k.

### Jun 30 (Tue) — soft open, DELL pick, Robinhood
- BTC −2.6% → MARA red and **NOW flipped to value-trap** → both put on WAIT.
- Full scan → **DELL** flagged as the next green transaction: only name making fresh highs (+2.87%, $405→426 over 3 days) while crypto/semis wobbled → selling into strength. Plan: **Sell $390P / Buy $380P · Jul 17 · ~$2.75 credit · 2 ct · ~$550 max / ~$1,450 risk.**
- **Robinhood MCP:** found configured in `ssr-analyst/.cursor/mcp.json` (`https://agent.robinhood.com/mcp/trading`). Confirmed endpoint live (OAuth/PKCE; auth via `robinhood.com/oauth`). Scoped to `ssr-analyst` only. Pending: user completes the Login/OAuth click in the `ssr-analyst` workspace.

---

## 5. Key lessons (durable rules)

1. **Earnings/event gate is the #1 edge** — never sell premium through earnings/CPI/PCE/FOMC (born from the AVGO −$1,717 loss).
2. **A user hint about a ticker = run a full Health Check incl. the earnings calendar** (the MU miss).
3. **Bellwether read-through** — a sector bellwether's earnings gap auto-triggers a same-session sympathy scan of its peers; catch it *on* the catalyst day with a same-day exit; the Whale flag is stale on a fresh gap (MU→SNDK: +22% on 6/25 → −10.5% on 6/26).
4. **Don't chase a gap** — high IV after a pop → sell a put spread on a hold, don't buy calls (GOOGL 6/29 skip).
5. **One max loss erases ~3–6 wins** — size for the tail; stops/aborts are non-negotiable.
6. **Bullish core** (put-credit + call-debit); bearish only on confirmed breakdowns.
7. **Verify what a ticker actually IS** before assigning a driver/correlation (NNE ≠ BTC proxy).
8. **Stand-downs count** — measured over a rolling 5-day window, not a rigid daily quota.

---

## 6. Positions & armed trades (as of Jun 30, 2026)

| Item | Status |
|---|---|
| **NNE** $23/$20 put credit · Jul 17 · 5 ct | OPEN. Was underwater (low $19.87 on 6/26), **bounced +7% to ~$21.3** on 6/29–30. Hold thesis; GTC buy-to-close $0.16. Abort: NNE closes < $20 or risk-[REDACTED] deepens (QQQ breaks). |
| **GOOGL** 340/350 call debit | ❌ SKIPPED 6/29 — gapped +4.8% past short strike. |
| **SNOW** 230/220 put credit · Jul 31 (rolled from 225/215) | Armed; enter ≥$2.40 on a hold > $245. Composite cooled to NEUTRAL 6/30 — only on a confirmed hold. |
| **MARA** 12.5/11.5 put credit · Jul 31 · IV 95% | WAIT 6/30 — BTC −2.6%, don't sell into the crypto slide. Trigger: BTC firms > $58.5k + MARA reclaims ~$13.7. Abort: BTC < $57k. |
| **DELL** 390/380 put credit · Jul 17 · ~$2.75 · 2 ct | **Top "next green" pick 6/30** — uptrending, non-crypto, non-semi. Enter ≥$2.50 limit. |
| **NOW** put credit | OFF — flipped to value-trap 6/30. |

---

## 7. The one command

```bash
cd ~/Documents/Cursor/ssr-analyst/Documents/market_data && python3 daily.py
```
Runs: refresh cache (delta) → earnings gate → macro + cross-asset Tomorrow tilt → 🥭 MANGOS → **read-through radar** → Health Check composite (STKK+STNOW+ThreeGood+Whale) → ranked candidate(s). ~2 min focus / ~7 min `--all`.

Flags: `--quick` (skip refresh) · `--all` (full universe) · `daily.py SYM …` (specific names) · `--to YYYY-MM-DD` (whale expiry). Alias `daily` added to `~/.zshrc`.

---

## 8. Robinhood MCP — setup status & next step

- **Config (only place):** `ssr-analyst/.cursor/mcp.json` → `robinhood` → `https://agent.robinhood.com/mcp/trading`.
- **Endpoint:** live; OAuth + PKCE (login at `robinhood.com/oauth`, token at `api.robinhood.com/oauth2/token/`). The `/mcp/trading` URL is the **server endpoint, not a browser login link**.
- **Status:** registered in the `ssr-analyst` project (`mcps/project-0-ssr-analyst-robinhood/`) — **not yet authenticated.**
- **To finish:** open the **`ssr-analyst`** workspace → **Settings → Tools & MCP → robinhood → Login** → approve in browser. (Reload Window if the button doesn't appear.)
- **Safety:** the `/trading` endpoint can place **real orders**. Recommended: start **read-only** (positions, balances, fills) before enabling order placement; confirm each order.

---

## 9. Open items / next steps

1. **Authenticate Robinhood** in the `ssr-analyst` workspace (read-only first).
2. **DELL** — enter the Jul 17 390/380 put credit on the limit if it holds.
3. **NNE** — monitor vs $20 abort; let the GTC ride the bounce.
4. **SNOW / MARA** — enter only on confirmed holds (SNOW > $245; MARA needs BTC > $58.5k).
5. Keep logging lessons to `agent_learning_log.md`; re-run the backtest when a gate/rule changes.

---

_Workspace switching note: chats are scoped per workspace. To keep continuity, either add `ssr-analyst` to the current workspace (File → Add Folder to Workspace) or start a fresh chat in the `ssr-analyst` window and point it at this history file._
