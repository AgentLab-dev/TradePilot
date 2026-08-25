#!/bin/zsh
# Weekly lesson-store audit (READ-ONLY verifier).
# Runs the cross-check verifier against the latest qa + prod heads
# of eda-dbt-em. If any NEEDS_CORRECTION drift is detected, writes a
# digest + DMs the operator.

set -euo pipefail
exec 0</dev/null

AGENT_HOME="$HOME/Library/Application Support/AE Agent"
BARE="$HOME/Backups/eda-dbt-em-backup.git"
LOG_DIR="$AGENT_HOME/runs/audit"
mkdir -p "$LOG_DIR"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
LOG_PATH="$LOG_DIR/audit_run_${TS}.log"

{
  echo "=== AE Agent lesson audit (weekly) — $TS ==="
  echo "[step 1] refresh bare clone (TCC-safe)"
  if [ -d "$BARE" ]; then
    git --git-dir="$BARE" fetch origin --quiet || echo "WARN: fetch failed"
  else
    echo "WARN: bare clone missing at $BARE — skipping fetch"
  fi
  PROD_HEAD="$(git --git-dir=$BARE rev-parse prod 2>/dev/null || echo unknown)"
  QA_HEAD="$(git --git-dir=$BARE rev-parse qa 2>/dev/null || echo unknown)"
  echo "    prod=$PROD_HEAD"
  echo "    qa=  $QA_HEAD"

  echo ""
  echo "[step 2] sync worktree to qa head"
  WT="$HOME/Backups/eda-dbt-em-postia-mining"
  if [ -d "$WT/.git" ] || [ -f "$WT/.git" ]; then
    git -C "$WT" fetch origin --quiet || true
    git -C "$WT" reset --hard origin/qa --quiet || echo "WARN: reset failed"
  fi

  echo ""
  echo "[step 3] run verifier"
  cd "$AGENT_HOME"
  python3 agents/arr_quarter_close/data/lessons/_audit_verifier.py

  echo ""
  echo "[step 4] check for drift"
  LATEST="$(ls -1t $LOG_DIR/lesson_audit_*.json 2>/dev/null | head -1)"
  if [ -z "$LATEST" ]; then
    echo "WARN: no audit json produced"
    exit 0
  fi
  NC="$(python3 -c "import json; print(json.load(open('$LATEST'))['by_status'].get('NEEDS_CORRECTION',0))")"
  echo "    NEEDS_CORRECTION = $NC"

  if [ "$NC" -gt 0 ]; then
    echo ""
    echo "[step 5] DRIFT DETECTED — DM operator"
    python3 - <<PY
import json, subprocess
SLKCLI = "/opt/homebrew/lib/node_modules/slkcli/src/api.js"
ad = json.load(open("$LATEST"))
nc = [v for v in ad["verdicts"] if v["status"] == "NEEDS_CORRECTION"]
text = (
    "*Weekly lesson audit — drift detected*\n"
    f"prod head: \`{ad['prod_head'][:8]}\`\n"
    f"qa head:   \`{ad['qa_head'][:8]}\`\n"
    f"NEEDS_CORRECTION: {len(nc)} lessons\n\n"
    "Top issues:\n" + "\n".join(
        f"• [{v['tier']}] {v['role']}/{v['lesson_id']} — {v['snippet'][:100]}"
        for v in nc[:10]
    ) + "\n\nFull report: $LATEST\nApply: \`python3 _audit_apply.py\` after editing CORRECTIONS dict."
)
payload = {"channel": "D03GVBRLU9F", "text": text,
           "unfurl_links": False, "unfurl_media": False}
script = f"import('{SLKCLI}').then(({{ slackApi }}) => slackApi('chat.postMessage', {json.dumps(payload)}).then(r => console.log(JSON.stringify(r)))).catch(e => {{ console.error(e); process.exit(1) }})"
p = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=30)
print("DM:", p.stdout[:200])
PY
  else
    echo ""
    echo "[step 5] all lessons VERIFIED — no DM"
  fi

  echo ""
  echo "=== done @ $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
} 2>&1 | tee -a "$LOG_PATH"
