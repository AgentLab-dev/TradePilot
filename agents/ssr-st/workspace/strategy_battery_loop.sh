#!/usr/bin/env bash
# 3x/day full-battery strategy loop (session-scoped).
# Fires at 08:00, 11:00, 13:00 America/Los_Angeles on weekdays only.
# Emits a sentinel the agent watches via notify_on_output.
set -u
DIR="/Users/koteswararao.venkata/Documents/Cursor/ssr-analyst"
SENTINEL="AGENT_LOOP_TICK_strategy"
PROMPT='Run the FULL strategy battery and produce a 5-transaction plan. Steps: (1) CROSS-SECTOR GATE FIRST (mandatory, no tech-first bias) — pull the live sector-rotation map across ALL 11 GICS sectors via ETFs (XLK XLF XLE XLV XLRE XLI XLU XLP XLY XLB XLC) plus tape/subsector reads (SPY QQQ IWM, SMH KRE XOP, GLD TLT VXX); rank sectors by live % vs prior close and identify the leaders/laggards; (2) pull macro (SPX/QQQ/VIX/10Y) + MANGOS (META NVDA GOOGL AMZN MSFT) as ONE input among sectors, not the whole scan; (3) hunt candidates starting from the STRONGEST sectors first, then pull those leaders (only look at semis/tech if tech won the sector rank) — semiconductor scan (NVDA AMD AVGO SMCI MRVL TSM MU ARM INTC ON) is a sub-step, not the headline; (3b) MOMENTUM DISCOVERY (MANDATORY, closes the ALAB-blindspot) — read Documents/momentum_watchlist.md, then screen the WHOLE-MARKET momentum factor (top YTD/3-month gainers + relative-strength leaders + fresh 52-wk highs BEYOND MANGOS and the semis-10, e.g. ALAB NBIS SNDK WDC STX PENG LITE CIEN AMD ARM Bloom), apply the anti-chase parabolic gate, check whether any ARMED pullback alert (ALAB/NBIS) has TRIGGERED, and update the watchlist file (retire faded names, add new leaders). IF NO FRESH IBD PASTE IS AVAILABLE, run the SELF-SERVE FALLBACK (do NOT wait for the user): (a) fetch FFTY holdings from stockanalysis.com/etf/ffty/holdings as the IBD-50 proxy (ALAB was #1 there — this catches leaders on its own); (b) run the RS SCREEN — pull the ~50-name cross-sector universe via get_equity_historicals (start 3 months back, interval day) and rank by 3-month return + %-below-high (anti-chase) + 1-month momentum, reuse rs_screen.py to compute; (c) web-search top YTD/3-month gainers as a cross-check; then apply the same gates; (4) run the per-name battery on the top cross-sector candidates — event gate (earnings/CPI/PCE/FOMC via get_earnings_calendar) FIRST, then STKK (trend/historicals), STNOW (fundamentals), Whale Check (option volume vs OI on busy strikes); (5) pull WSJ + MarketWatch headlines for the rotation/regime read; (6) route each survivor through the direction x IV matrix (bull+lowIV=call debit, bull+highIV=put credit, bear+highIV=call credit, bear+lowIV=put debit, range+highIV=iron condor). OUTPUT: a ranked 5-transaction plan spanning the leading sectors (NOT all tech), each with structure, strikes/shares, sizing, entry trigger, stop/target. Label each take / wait-for-trigger / stand-down, and note options book vs the $1k agentic sleeve.'

while true; do
  now=$(date +%s)
  next=$(python3 "$DIR/next_slot.py" 8:0 11:0 13:0 2>/dev/null)
  if [ -z "$next" ]; then wait_s=1800; else wait_s=$(( next - now )); fi
  [ "$wait_s" -lt 1 ] && wait_s=1800
  sleep "$wait_s"
  echo "$SENTINEL {\"prompt\":\"$PROMPT\"}"
done
