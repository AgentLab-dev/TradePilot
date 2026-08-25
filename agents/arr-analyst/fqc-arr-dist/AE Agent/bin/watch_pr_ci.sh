#!/usr/bin/env bash
# watch_pr_ci.sh - Poll `gh pr checks <PR>` and post heartbeat to Slack
#
# Standalone counterpart to agents/arr_quarter_close/subagents/ci_monitor.py
# for cases where the agent didn't open the PR itself (e.g. the PR was
# created manually from chat or the FQC-ARR run paused before pr-author).
#
# Usage:
#   bin/watch_pr_ci.sh <PR_NUMBER> <SLACK_CHANNEL_OR_USER_ID> \
#       [--poll-minutes 10] [--check-name ci/dbt_cloud] [--max-hours 4]
#
# Example:
#   bin/watch_pr_ci.sh 472 <YOUR_SLACK_USER_ID>
#   bin/watch_pr_ci.sh 472 C0123ABC --check-name dbtcloud-codevalidate
#
# Exits 0 on terminal pass, 1 on timeout, 2 on terminal fail/error/cancelled.

set -uo pipefail

PR_NUMBER="${1:-}"
CHANNEL="${2:-}"
shift 2 2>/dev/null || true

POLL_MIN=10
CHECK_NAME="ci/dbt_cloud"
MAX_HOURS=4

while [[ $# -gt 0 ]]; do
  case "$1" in
    --poll-minutes) POLL_MIN="$2"; shift 2 ;;
    --check-name)   CHECK_NAME="$2"; shift 2 ;;
    --max-hours)    MAX_HOURS="$2"; shift 2 ;;
    *) echo "[watch_pr_ci] unknown arg: $1" >&2; exit 64 ;;
  esac
done

if [[ -z "$PR_NUMBER" || -z "$CHANNEL" ]]; then
  echo "Usage: $0 <PR_NUMBER> <SLACK_CHANNEL> [--poll-minutes N] [--check-name X] [--max-hours H]" >&2
  exit 64
fi
command -v gh  >/dev/null || { echo "[watch_pr_ci] gh CLI not found"  >&2; exit 127; }
command -v slk >/dev/null || { echo "[watch_pr_ci] slk CLI not found" >&2; exit 127; }

REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo workday-inc/eda-dbt-em)"
PR_URL="https://github.com/${REPO}/pull/${PR_NUMBER}"

DEADLINE=$(( $(date +%s) + MAX_HOURS * 3600 ))
ITER=0
FINAL_STATE="timeout"

post() {
  local icon="$1" state="$2"
  local text=":${icon}: *PR #${PR_NUMBER} CI* check \`${CHECK_NAME}\` = \`${state}\` (poll #${ITER})
<${PR_URL}|PR #${PR_NUMBER}>"
  slk send "$CHANNEL" "$text" >/dev/null 2>&1 || \
    echo "[watch_pr_ci:slack-fallback] would post: ${text}"
  echo "[watch_pr_ci] $(date -u +%FT%TZ) poll=${ITER} state=${state}"
}

icon_for() {
  case "$1" in
    pass)     echo "white_check_mark" ;;
    fail|failure|error|cancelled) echo "x" ;;
    pending|"") echo "hourglass_flowing_sand" ;;
    *)        echo "grey_question" ;;
  esac
}

while [[ $(date +%s) -lt $DEADLINE ]]; do
  ITER=$((ITER + 1))
  RAW="$(gh pr checks "$PR_NUMBER" 2>/dev/null || true)"
  STATE="$(printf '%s\n' "$RAW" | awk -v p="$CHECK_NAME" 'index($0,p){print $2; exit}')"
  STATE="${STATE:-pending}"
  post "$(icon_for "$STATE")" "$STATE"
  case "$STATE" in
    pass|fail|failure|error|cancelled|skipping)
      FINAL_STATE="$STATE"; break ;;
  esac
  sleep "$((POLL_MIN * 60))"
done

if [[ "$FINAL_STATE" == "pass" ]]; then
  slk send "$CHANNEL" ":tada: *PR #${PR_NUMBER}* CI \`${CHECK_NAME}\` finished *PASS* after ${ITER} polls. <${PR_URL}|Open PR>" >/dev/null 2>&1
  exit 0
fi
if [[ "$FINAL_STATE" == "timeout" ]]; then
  slk send "$CHANNEL" ":alarm_clock: *PR #${PR_NUMBER}* CI watcher timed out after ${MAX_HOURS}h (${ITER} polls). <${PR_URL}|Open PR>" >/dev/null 2>&1
  exit 1
fi
slk send "$CHANNEL" ":rotating_light: *PR #${PR_NUMBER}* CI \`${CHECK_NAME}\` finished *${FINAL_STATE}* after ${ITER} polls. <${PR_URL}|Open PR>" >/dev/null 2>&1
exit 2
