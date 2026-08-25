#!/usr/bin/env bash
# 1x/day EVENING WRAP + next-day prep (session-scoped).
# Fires at 18:00 America/Los_Angeles on weekdays only (after after-hours closes ~5 PM PT).
# Emits a sentinel the agent watches via notify_on_output. Review/prep only — places NO orders.
set -u
DIR="/Users/koteswararao.venkata/Documents/Cursor/ssr-analyst"
SENTINEL="AGENT_LOOP_TICK_evening"
PROMPT='Run the EVENING WRAP + next-day prep (follow the evening-wrap-nextday-prep skill; NO orders, market closed). Sweep all seven: (1) final close + after-hours tape for the book + SPX/QQQ/VIX/10Y; (2) news watch — WSJ, MarketWatch, Yahoo Finance (+Reuters/CNBC) for the day and for GOOGL/book/watch names, cite source+date; (3) options whale watch — unusual activity, call/put skew, volume vs OI; (4) analyst rating changes (upgrades/downgrades/PT) on book + bellwethers; (5) next-day levels per held/watch name (support/resistance/recycle target/stop); (6) next-day catalyst calendar — earnings + macro (CPI/PCE/PPI/jobs/FOMC) + Fed speakers, feed the event gate; (7) regime read. OUTPUT: overwrite ssr-analyst/Documents/next_day_prep.md with the structured template, and update the learning log first-check pointer if the plan changed. End with a 4-line TL;DR to the user.'

while true; do
  now=$(date +%s)
  next=$(python3 "$DIR/next_slot.py" 18:0 2>/dev/null)
  if [ -z "$next" ]; then wait_s=3600; else wait_s=$(( next - now )); fi
  [ "$wait_s" -lt 1 ] && wait_s=3600
  sleep "$wait_s"
  echo "$SENTINEL {\"prompt\":\"$PROMPT\"}"
done
