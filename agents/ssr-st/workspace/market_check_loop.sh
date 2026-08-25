#!/usr/bin/env bash
# 3x/day agent-account PORTFOLIO check (session-scoped).
# Morning / post-lunch / afternoon: 08:30, 12:30, 15:00 America/Los_Angeles, weekdays only.
# Emits a sentinel the agent watches via notify_on_output.
set -u
DIR="/Users/koteswararao.venkata/Documents/Cursor/ssr-analyst"
SENTINEL="AGENT_LOOP_TICK_mktcheck"
PROMPT='Agent-account portfolio check (account ••••1451). Pull ALL active equity + option positions (get_equity_positions / get_option_positions) and their live quotes, plus QQQ for the tape. For each open position report price, unrealized P&L, and any resting order status. Manage the GOOGL recycle: if the $372 sell filled, re-evaluate and place a fresh rebuy off live VWAP/support; if resting, re-check the target vs the tape. Halt a name only if it closes below its stop. Give a concise per-position update + running recycle-cycle tally.'

while true; do
  now=$(date +%s)
  next=$(python3 "$DIR/next_slot.py" 8:30 12:30 15:0 2>/dev/null)
  if [ -z "$next" ]; then wait_s=1800; else wait_s=$(( next - now )); fi
  [ "$wait_s" -lt 1 ] && wait_s=1800
  sleep "$wait_s"
  echo "$SENTINEL {\"prompt\":\"$PROMPT\"}"
done
