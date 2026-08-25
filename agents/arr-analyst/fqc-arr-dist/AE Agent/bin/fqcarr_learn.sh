#!/usr/bin/env bash
# fqcarr_learn.sh -- twice-daily continuous-learning pass for the FQC-ARR agent.
#
# Layout (Jun-2026 relocation):
#   Agent home:  $AE_AGENT_HOME   (parent of this script's dir)
#   Lessons:     $AE_AGENT_HOME/agents/arr_quarter_close/data/lessons/
#   Audit logs:  $AE_AGENT_HOME/runs/learning/<UTC_ts>.{log,md}
#
# Triggered by two launchd jobs:
#   ~/Library/LaunchAgents/com.example.fqcarr.learn-am.plist  (09:00 local)
#   ~/Library/LaunchAgents/com.example.fqcarr.learn-pm.plist  (17:00 local)
#
# What it does:
#   1. Runs `fqc-arr --learn` (= --reflect --reflect-look-back-days 7
#      --reflect-wide-scan). Scans every learning source we currently
#      capture (thinking logs + run logs). Dedupes via hashed lesson ids;
#      promotes lessons crossing occurrence_count >= 3 to _stable.jsonl.
#   2. Captures full stdout/stderr to runs/learning/<ts>.log
#   3. Writes a clean Markdown audit report to runs/learning/<ts>.md
#   4. (optional) Posts a 1-line summary as a Slack DM to the operator.
#      Set FQC_LEARN_NO_SLACK=1 to silence; FQC_LEARN_SLACK_USER overrides
#      the recipient (default: <YOUR_SLACK_USER_ID> = <you>).
#   5. Always exits 0 so launchd does not log "exit status: 2" for benign
#      no-op runs ("no novel observations today"). The audit log and the
#      ledger's _reflection_log.jsonl carry the actual outcome.
#
# Manual run:
#   "$HOME/Documents/Cursor/AE Agent/bin/fqcarr_learn.sh"
#
# Test mode (no Slack ping):
#   FQC_LEARN_NO_SLACK=1 "$HOME/Documents/Cursor/AE Agent/bin/fqcarr_learn.sh"

set -uo pipefail

# Resolve agent home from script location (works under launchd where CWD is /).
SCRIPT_DIR="$(cd "$(dirname "$(readlink "$0" 2>/dev/null || echo "$0")")" 2>/dev/null && pwd)" || \
  SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AE_AGENT_HOME="$(cd "$SCRIPT_DIR/.." && pwd)"
export AE_AGENT_HOME
cd "$AE_AGENT_HOME"

# launchd does NOT inherit the user's interactive shell PATH. Build a sane
# minimal one that has python3, git, slk, gh, curl. Also source ~/.zshrc
# inside an interactive subshell so JIRA_* / SLACK_* env vars are visible.
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin${PATH:+:$PATH}"
if [[ -f "$HOME/.zshrc" ]]; then
  # shellcheck disable=SC1091
  set +u
  source "$HOME/.zshrc" >/dev/null 2>&1 || true
  set -u
fi

# Pin the lessons store to the agent home (durable across dbt-repo re-clones).
if [[ -z "${FQC_ARR_LESSONS_DIR:-}" ]]; then
  export FQC_ARR_LESSONS_DIR="$AE_AGENT_HOME/agents/arr_quarter_close/data/lessons"
fi

LEARN_DIR="$AE_AGENT_HOME/runs/learning"
mkdir -p "$LEARN_DIR"

TS="$(date -u +'%Y%m%dT%H%M%SZ')"
LOCAL_LABEL="$(date +'%a %b %d %H:%M %Z')"
LOG_PATH="$LEARN_DIR/${TS}.log"
REPORT_PATH="$LEARN_DIR/${TS}.md"

# Prevent overlapping runs (e.g. operator triggers manually while a launchd
# job is still finishing). flock acquires an exclusive lock on the lock file.
LOCK="$LEARN_DIR/.lock"
exec 9>"$LOCK"
if command -v flock >/dev/null 2>&1; then
  flock -n 9 || { echo "[learn] another pass is already running; bailing." >&2; exit 0; }
fi

# ---------------------------------------------------------------------------
# Run the learn pass
# ---------------------------------------------------------------------------

START_TS="$(date -u +'%s')"

{
  echo "=== fqc-arr --learn ($LOCAL_LABEL / ${TS}) ==="
  echo "Agent home:    $AE_AGENT_HOME"
  echo "Lessons dir:   $FQC_ARR_LESSONS_DIR"
  echo "dbt project:   ${FQC_ARR_PROJECT_DIR:-(auto-resolved by bin/fqc-arr)}"
  echo "Python:        $(command -v python3 || echo 'python3 NOT FOUND')"
  echo "slk:           $(command -v slk     || echo 'slk NOT FOUND (Slack DM will be skipped)')"
  echo "----"
  "$AE_AGENT_HOME/bin/fqc-arr" --learn 2>&1
  LEARN_RC=$?
  echo "----"
  echo "fqc-arr exit code: $LEARN_RC"
  echo "elapsed: $(( $(date -u +'%s') - START_TS ))s"
} | tee "$LOG_PATH"

# ---------------------------------------------------------------------------
# Distill the run into a clean Markdown audit + 1-line Slack summary
# ---------------------------------------------------------------------------

# Pull the latest entry from _reflection_log.jsonl
read -r REFLECTION_LINE <<<"$(
  python3 - "$FQC_ARR_LESSONS_DIR" <<'PY' 2>/dev/null || echo ''
import sys, json
from pathlib import Path
p = Path(sys.argv[1]) / "_reflection_log.jsonl"
if not p.exists():
    sys.exit(0)
last = ""
with p.open() as f:
    for ln in f:
        ln = ln.strip()
        if ln:
            last = ln
if not last:
    sys.exit(0)
try:
    obj = json.loads(last)
except Exception:
    sys.exit(0)
print(f"{obj.get('ts','?')}\t{obj.get('lessons_added',0)}\t{obj.get('lessons_promoted',0)}\t{obj.get('notes','').replace(chr(10),' ')[:240]}")
PY
)"

IFS=$'\t' read -r LAST_TS ADDED PROMOTED NOTES <<<"${REFLECTION_LINE:-}"
ADDED="${ADDED:-?}"
PROMOTED="${PROMOTED:-?}"
NOTES="${NOTES:-(no reflection entry written)}"

# Total lesson count
TOTAL_LESSONS="$(
  python3 - "$FQC_ARR_LESSONS_DIR" <<'PY' 2>/dev/null || echo '?'
import sys, glob, os
d = sys.argv[1]
total = 0
for fp in glob.glob(os.path.join(d, "*.jsonl")):
    if fp.endswith("_reflection_log.jsonl"):
        continue
    with open(fp) as f:
        total += sum(1 for ln in f if ln.strip())
print(total)
PY
)"

# Recent thinking-log file (audit pointer back to the deepest signal)
LATEST_THINKING="$(ls -1t "$AE_AGENT_HOME/runs/thinking/"*.md 2>/dev/null | head -1 || echo '')"

# Build the Markdown audit report.
{
  echo "# FQC-ARR learning pass -- $LOCAL_LABEL"
  echo
  echo "- UTC timestamp: \`$TS\`"
  echo "- Agent home: \`$AE_AGENT_HOME\`"
  echo "- Lessons store: \`$FQC_ARR_LESSONS_DIR\`"
  echo "- Trigger: \`bin/fqcarr_learn.sh\` (manual or launchd \`com.example.fqcarr.learn-*\`)"
  echo
  echo "## Outcome"
  echo
  echo "| metric | value |"
  echo "|---|---|"
  echo "| lessons added this pass | \`$ADDED\` |"
  echo "| lessons promoted to \`_stable\` | \`$PROMOTED\` |"
  echo "| total lessons in store | \`$TOTAL_LESSONS\` |"
  echo "| recorder note | $NOTES |"
  echo
  echo "## Audit pointers"
  echo
  echo "- Full run log: \`runs/learning/${TS}.log\`"
  echo "- Recorder ledger: \`agents/arr_quarter_close/data/lessons/_reflection_log.jsonl\`"
  echo "- Promoted-lessons snapshot: \`agents/arr_quarter_close/data/lessons/_stable.jsonl\`"
  if [[ -n "$LATEST_THINKING" ]]; then
    echo "- Latest thinking log (this run): \`${LATEST_THINKING#$AE_AGENT_HOME/}\`"
  fi
  echo
  echo "## How to inspect"
  echo
  echo '```bash'
  echo "# show all current lessons"
  echo "fqc-arr --show-lessons"
  echo
  echo "# show lessons for one role"
  echo "fqc-arr --show-lessons debugger"
  echo
  echo "# tail the recorder ledger"
  echo "tail -n 10 \"\$FQC_ARR_LESSONS_DIR/_reflection_log.jsonl\""
  echo '```'
} > "$REPORT_PATH"

# ---------------------------------------------------------------------------
# Slack DM (optional; silenced when no novel observations to avoid noise)
# ---------------------------------------------------------------------------

if [[ "${FQC_LEARN_NO_SLACK:-0}" == "1" ]]; then
  echo "[learn] FQC_LEARN_NO_SLACK=1 -> skipping Slack DM."
elif ! command -v slk >/dev/null 2>&1; then
  echo "[learn] slk not on PATH -> skipping Slack DM."
else
  SLACK_USER="${FQC_LEARN_SLACK_USER:-}"
  if [[ "$ADDED" == "0" && "$PROMOTED" == "0" ]]; then
    echo "[learn] no new/promoted lessons -> skipping Slack DM (FQC_LEARN_ALWAYS_PING=1 to override)."
    if [[ "${FQC_LEARN_ALWAYS_PING:-0}" == "1" ]]; then
      MSG=":books: *FQC-ARR learn pass* ($LOCAL_LABEL) -- no new lessons today (total=$TOTAL_LESSONS). Audit: \`runs/learning/${TS}.md\`"
      slk send "$SLACK_USER" "$MSG" >/dev/null 2>&1 || \
        echo "[learn] slk send returned non-zero; continuing."
    fi
  else
    MSG=":books: *FQC-ARR learn pass* ($LOCAL_LABEL) -- *+$ADDED* new lesson(s), *+$PROMOTED* promoted (total=$TOTAL_LESSONS). Audit: \`runs/learning/${TS}.md\`. Inspect: \`fqc-arr --show-lessons\`."
    if ! slk send "$SLACK_USER" "$MSG" >/dev/null 2>&1; then
      echo "[learn] slk send to $SLACK_USER failed; full report still at $REPORT_PATH"
    else
      echo "[learn] Slack DM sent to $SLACK_USER."
    fi
  fi
fi

echo "[learn] done. audit: $REPORT_PATH"
exit 0
