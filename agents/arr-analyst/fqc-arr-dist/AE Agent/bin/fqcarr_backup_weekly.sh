#!/usr/bin/env bash
# fqcarr_backup_weekly.sh -- weekly git push of the AE Agent home to the
# eda-dbt-em repo as a sidecar feature branch.
#
# What it does:
#   1. Adds (or refreshes) a separate git worktree at
#      $HOME/Backups/ae-agent-worktree pointing at branch
#      `feature/ae-agent-backup` of the `workday-inc/eda-dbt-em` repo.
#      If the branch does not yet exist on origin, it is created off
#      `origin/qa`.
#   2. Wipes `<worktree>/.ae-agent-backup/` and rsyncs the full contents of
#      $FQC_ARR_HOME into it (excluding transient files: .DS_Store,
#      __pycache__, launchd_*.out/.err, .lock).
#   3. Also captures the live ~/Library/LaunchAgents plists so the backup
#      is self-contained for disaster recovery.
#   4. git add + commit (no-op if nothing changed).
#   5. git push origin feature/ae-agent-backup.
#   6. Writes an audit report at $FQC_ARR_HOME/runs/backups/<ts>.{log,md}
#      and (optionally) DMs the operator on Slack with the result.
#
# Why a worktree (not the user's main checkout):
#   The user's eda-dbt-em working tree is usually on a feature branch with
#   uncommitted edits. We must not switch branches there. The git worktree
#   lives in $HOME/Backups/ae-agent-worktree and is fully isolated.
#
# Safety:
#   * Never `force-push`. Branch is append-only.
#   * Push goes to a feature branch -- never qa, never prod.
#   * No-op when the working tree shows zero diff (idempotent).
#   * Always exits 0 so launchd does not flag failures for benign no-ops.
#
# Manual run:
#   "$HOME/Library/Application Support/AE Agent/bin/fqcarr_backup_weekly.sh"

set -uo pipefail

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

AE_AGENT_HOME="${FQC_ARR_HOME:-$HOME/Library/Application Support/AE Agent}"

# DO NOT use the user's main eda-dbt-em checkout at $FQC_ARR_PROJECT_DIR --
# it lives under ~/Documents/ which is TCC-protected and unreachable from
# launchd. Instead we maintain a dedicated *bare* clone at $BACKUP_BARE_DIR
# that lives under ~/Backups/ (no TCC restriction). All git operations
# (fetch / worktree add / commit / push) happen against that bare clone
# from a worktree at $WORKTREE_DIR. The user's main checkout is never
# touched.
GIT_REMOTE_URL="${FQC_ARR_BACKUP_REMOTE_URL:-https://github.com/workday-inc/eda-dbt-em.git}"
BACKUP_BARE_DIR="$HOME/Backups/eda-dbt-em-backup.git"
WORKTREE_DIR="$HOME/Backups/ae-agent-worktree"
BRANCH="feature/ae-agent-backup"
BASE_BRANCH="qa"
SUBDIR=".ae-agent-backup"

LOG_DIR="$AE_AGENT_HOME/runs/backups"
mkdir -p "$LOG_DIR"
TS="$(date -u +'%Y%m%dT%H%M%SZ')"
LOCAL_LABEL="$(date +'%a %b %d %H:%M %Z')"
LOG_PATH="$LOG_DIR/${TS}.log"
REPORT_PATH="$LOG_DIR/${TS}.md"

# launchd doesn't inherit user PATH; source ~/.zshrc for git/curl/slk
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin${PATH:+:$PATH}"
if [[ -f "$HOME/.zshrc" ]]; then
  set +u
  source "$HOME/.zshrc" >/dev/null 2>&1 || true
  set -u
fi

# Prevent overlapping runs.
LOCK="$LOG_DIR/.lock"
exec 9>"$LOCK"
if command -v flock >/dev/null 2>&1; then
  flock -n 9 || { echo "[backup] another backup is already running; bailing." >&2; exit 0; }
fi

# rsync exclusions: transient files we don't need in git history.
RSYNC_EXCLUDES=(
  --exclude='.DS_Store'
  --exclude='__pycache__/'
  --exclude='*.pyc'
  --exclude='*.pyo'
  --exclude='runs/learning/.lock'
  --exclude='runs/learning/launchd_*.out'
  --exclude='runs/learning/launchd_*.err'
  --exclude='runs/backups/'        # don't include backup-job audit logs in the backup itself
  --exclude='runs/thinking/__pycache__/'
)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

# Status variables collected during the run; consumed by the report writer.
COMMIT_SHA=""
FILES_CHANGED="0"
SKIPPED="0"
PUSH_RC="?"
FAIL_REASON=""
LESSONS_COUNT="?"
TOTAL_BACKED_UP_BYTES="?"

run() {
  echo "=== AE Agent weekly backup ($LOCAL_LABEL / ${TS}) ==="
  echo "Agent home:     $AE_AGENT_HOME"
  echo "Bare clone:     $BACKUP_BARE_DIR"
  echo "Remote:         $GIT_REMOTE_URL"
  echo "Worktree:       $WORKTREE_DIR"
  echo "Branch:         $BRANCH  (base: $BASE_BRANCH)"
  echo "Subdir in repo: $SUBDIR"
  echo "git:            $(command -v git || echo 'git NOT FOUND')"
  echo "rsync:          $(command -v rsync || echo 'rsync NOT FOUND')"
  echo "----"

  # First-run init: create the bare clone if it doesn't yet exist. Use a
  # mirror clone so all branches are tracked (we only push our own branch
  # but want to fetch any branch from origin without re-cloning).
  if [[ ! -d "$BACKUP_BARE_DIR" ]]; then
    echo "[backup] first run -- creating bare mirror clone at $BACKUP_BARE_DIR"
    mkdir -p "$(dirname "$BACKUP_BARE_DIR")"
    if ! git clone --mirror --quiet "$GIT_REMOTE_URL" "$BACKUP_BARE_DIR" 2>&1; then
      FAIL_REASON="git clone --mirror failed (network / auth?)"
      echo "[backup] $FAIL_REASON"
      return 0
    fi
    # A mirror clone has fetch.mirror=true which makes push behaviour
    # surprising. Switch to a normal-clone fetch refspec so push only
    # affects $BRANCH.
    git --git-dir="$BACKUP_BARE_DIR" config remote.origin.mirror false
    git --git-dir="$BACKUP_BARE_DIR" config remote.origin.fetch "+refs/heads/*:refs/heads/*"
  fi

  # IMPORTANT: clean up any stale worktree BEFORE fetching. Otherwise
  # `git fetch origin` will refuse to update `refs/heads/$BRANCH` because
  # that ref is checked out in the stale worktree from a previous run.
  if git --git-dir="$BACKUP_BARE_DIR" worktree list 2>/dev/null | grep -q "$WORKTREE_DIR"; then
    echo "[backup] removing stale worktree at $WORKTREE_DIR"
    git --git-dir="$BACKUP_BARE_DIR" worktree remove --force "$WORKTREE_DIR" 2>&1 || true
  fi
  git --git-dir="$BACKUP_BARE_DIR" worktree prune 2>&1 || true
  rm -rf "$WORKTREE_DIR"

  echo "[backup] git fetch origin (bare clone)"
  if ! git --git-dir="$BACKUP_BARE_DIR" fetch origin --quiet 2>&1; then
    FAIL_REASON="git fetch failed (network / auth?)"
    echo "[backup] $FAIL_REASON"
    return 0
  fi

  local new_branch=0
  if git --git-dir="$BACKUP_BARE_DIR" rev-parse --quiet --verify "refs/heads/$BRANCH" >/dev/null 2>&1; then
    echo "[backup] $BRANCH already exists in bare clone (will fast-forward + add commit)"
  else
    new_branch=1
    echo "[backup] $BRANCH does NOT exist yet; will create from $BASE_BRANCH"
  fi

  echo "[backup] adding fresh worktree at $WORKTREE_DIR"
  if [[ $new_branch -eq 1 ]]; then
    if ! git --git-dir="$BACKUP_BARE_DIR" worktree add -b "$BRANCH" "$WORKTREE_DIR" "$BASE_BRANCH" 2>&1; then
      FAIL_REASON="git worktree add -b $BRANCH failed"
      echo "[backup] $FAIL_REASON"
      return 0
    fi
  else
    if ! git --git-dir="$BACKUP_BARE_DIR" worktree add "$WORKTREE_DIR" "$BRANCH" 2>&1; then
      FAIL_REASON="git worktree add $BRANCH failed"
      echo "[backup] $FAIL_REASON"
      return 0
    fi
  fi

  cd "$WORKTREE_DIR"

  # Wipe + repopulate the backup subdir.
  echo "[backup] refreshing $SUBDIR/ contents from $AE_AGENT_HOME"
  rm -rf "./$SUBDIR"
  mkdir -p "./$SUBDIR"
  rsync -a "${RSYNC_EXCLUDES[@]}" "$AE_AGENT_HOME/" "./$SUBDIR/" 2>&1 | head -20

  # Snapshot the live launchd plists too (they may have drifted from the
  # mirror copies in $AE_AGENT_HOME/launchd/ between weekly backups).
  if compgen -G "$HOME/Library/LaunchAgents/com.example.fqcarr.*.plist" >/dev/null; then
    echo "[backup] snapshotting live launchd plists -> $SUBDIR/launchd_live/"
    mkdir -p "./$SUBDIR/launchd_live"
    cp "$HOME/Library/LaunchAgents/com.example.fqcarr."*.plist "./$SUBDIR/launchd_live/" 2>&1 || true
  fi

  # Compute headline metrics before commit.
  LESSONS_COUNT="$(
    find "./$SUBDIR/agents/arr_quarter_close/data/lessons" -name '*.jsonl' \
        -not -name '_reflection_log.jsonl' 2>/dev/null \
      | xargs wc -l 2>/dev/null \
      | tail -1 | awk '{print $1}'
  )"
  LESSONS_COUNT="${LESSONS_COUNT:-0}"
  TOTAL_BACKED_UP_BYTES="$(du -sh "./$SUBDIR" | awk '{print $1}')"

  # Stage + commit (only what changed in our subdir).
  git add -A "./$SUBDIR/" 2>&1 || true

  if git diff --cached --quiet; then
    SKIPPED=1
    echo "[backup] no changes since last snapshot -> skipping commit + push"
  else
    FILES_CHANGED="$(git diff --cached --name-only | wc -l | tr -d ' ')"
    echo "[backup] staging $FILES_CHANGED changed paths"

    git -c user.email="ae-agent-bot@workday.local" \
        -c user.name="AE Agent (weekly backup)" \
        commit --quiet -m "ae-agent: weekly snapshot $(date -u +%Y-%m-%d)

Files changed: $FILES_CHANGED
Lessons in store: $LESSONS_COUNT
Backup size: $TOTAL_BACKED_UP_BYTES
Source: $AE_AGENT_HOME
Trigger: bin/fqcarr_backup_weekly.sh (launchd com.example.fqcarr.backup-weekly)
UTC: $TS" 2>&1 || {
        FAIL_REASON="git commit failed"
        echo "[backup] $FAIL_REASON"
        return 0
      }

    COMMIT_SHA="$(git rev-parse --short HEAD)"

    echo "[backup] pushing $BRANCH -> origin (no force)"
    if git push origin "$BRANCH" 2>&1; then
      PUSH_RC=0
      echo "[backup] push OK ($COMMIT_SHA)"
    else
      PUSH_RC=$?
      FAIL_REASON="git push failed (rc=$PUSH_RC)"
      echo "[backup] $FAIL_REASON"
    fi
  fi

  echo "----"
  echo "[backup] done."
}

# Everything below runs in ONE pipeline so the variables `run` assigns
# (COMMIT_SHA, FILES_CHANGED, SKIPPED, FAIL_REASON, ...) remain in scope
# for the audit-report and Slack-DM blocks. A simple `run | tee` followed
# by separate blocks would lose those assignments because each pipe creates
# a subshell.
{
  run

# ---------------------------------------------------------------------------
# Audit report
# ---------------------------------------------------------------------------

REMOTE_URL="$GIT_REMOTE_URL"
REMOTE_VIEW=""
if [[ "$REMOTE_URL" == https://* ]]; then
  REMOTE_VIEW="${REMOTE_URL%.git}/tree/$BRANCH"
fi

{
  echo "# AE Agent weekly backup -- $LOCAL_LABEL"
  echo
  echo "- UTC timestamp: \`$TS\`"
  echo "- Source: \`$AE_AGENT_HOME\`"
  echo "- Remote: \`$REMOTE_URL\`"
  echo "- Branch: \`$BRANCH\` (base: \`$BASE_BRANCH\`, subdir: \`$SUBDIR/\`)"
  if [[ -n "$REMOTE_VIEW" ]]; then
    echo "- Browse: $REMOTE_VIEW"
  fi
  echo "- Worktree: \`$WORKTREE_DIR\`"
  echo
  echo "## Outcome"
  echo
  echo "| metric | value |"
  echo "|---|---|"
  if [[ -n "${FAIL_REASON}" ]]; then
    echo "| status | FAILED -- $FAIL_REASON |"
  elif [[ "$SKIPPED" == "1" ]]; then
    echo "| status | SKIPPED (no changes since last snapshot) |"
  else
    echo "| status | OK |"
  fi
  echo "| files changed | \`$FILES_CHANGED\` |"
  echo "| lessons in store | \`$LESSONS_COUNT\` |"
  echo "| backup size | \`$TOTAL_BACKED_UP_BYTES\` |"
  if [[ -n "${COMMIT_SHA}" ]]; then
    echo "| commit | \`$COMMIT_SHA\` |"
  fi
  if [[ "${PUSH_RC}" != "?" ]]; then
    echo "| push rc | \`$PUSH_RC\` (0 = success) |"
  fi
  echo
  echo "## How to inspect on GitHub"
  echo
  if [[ -n "$REMOTE_VIEW" ]]; then
    echo "- Branch root: $REMOTE_VIEW"
    echo "- Backup subfolder: $REMOTE_VIEW/$SUBDIR"
    echo "- Commit history: ${REMOTE_VIEW/tree/commits}"
  else
    echo "- Open the repo and switch to branch \`$BRANCH\`, folder \`$SUBDIR/\`"
  fi
  echo
  echo "## How to restore on a fresh machine"
  echo
  echo '```bash'
  echo "# 1. Clone the eda-dbt-em repo (or any worktree)"
  echo "git clone $REMOTE_URL ~/Documents/Cursor/eda-dbt-em"
  echo "cd ~/Documents/Cursor/eda-dbt-em"
  echo "git checkout $BRANCH"
  echo
  echo "# 2. Copy the backup subdir into ~/Library/Application Support/"
  echo "mkdir -p \"\$HOME/Library/Application Support\""
  echo "cp -R $SUBDIR \"\$HOME/Library/Application Support/AE Agent\""
  echo
  echo "# 3. Re-create the symlink for convenience"
  echo "ln -s \"\$HOME/Library/Application Support/AE Agent\" \\"
  echo "      \"\$HOME/Documents/Cursor/AE Agent\""
  echo
  echo "# 4. Install launchd jobs from the backed-up plists"
  echo "cp \"\$HOME/Library/Application Support/AE Agent/launchd_live/\"*.plist \\"
  echo "   \"\$HOME/Library/LaunchAgents/\""
  echo "launchctl bootstrap gui/\$(id -u) ~/Library/LaunchAgents/com.example.fqcarr.learn-am.plist"
  echo "launchctl bootstrap gui/\$(id -u) ~/Library/LaunchAgents/com.example.fqcarr.learn-pm.plist"
  echo "launchctl bootstrap gui/\$(id -u) ~/Library/LaunchAgents/com.example.fqcarr.backup-weekly.plist"
  echo
  echo "# 5. Re-source ~/.zshrc env block (FQC_ARR_HOME, FQC_ARR_LESSONS_DIR, FQC_ARR_PROJECT_DIR)"
  echo '```'
} > "$REPORT_PATH"

# ---------------------------------------------------------------------------
# Slack DM (optional)
# ---------------------------------------------------------------------------

if [[ "${FQC_LEARN_NO_SLACK:-0}" == "1" ]]; then
  echo "[backup] FQC_LEARN_NO_SLACK=1 -> skipping Slack DM."
elif ! command -v slk >/dev/null 2>&1; then
  echo "[backup] slk not on PATH -> skipping Slack DM."
else
  SLACK_USER="${FQC_LEARN_SLACK_USER:-}"
  if [[ -n "${FAIL_REASON}" ]]; then
    MSG=":warning: *AE Agent weekly backup* ($LOCAL_LABEL) FAILED: $FAIL_REASON. Audit: \`runs/backups/${TS}.md\`"
    slk send "$SLACK_USER" "$MSG" >/dev/null 2>&1 || \
      echo "[backup] slk send failed"
  elif [[ "$SKIPPED" == "1" ]]; then
    echo "[backup] no changes -> skipping Slack DM (FQC_LEARN_ALWAYS_PING=1 to override)."
    if [[ "${FQC_LEARN_ALWAYS_PING:-0}" == "1" ]]; then
      MSG=":floppy_disk: *AE Agent weekly backup* ($LOCAL_LABEL) -- no changes since last snapshot ($LESSONS_COUNT lessons in store)."
      slk send "$SLACK_USER" "$MSG" >/dev/null 2>&1 || \
        echo "[backup] slk send failed"
    fi
  else
    MSG=":floppy_disk: *AE Agent weekly backup* ($LOCAL_LABEL) -- pushed \`$COMMIT_SHA\` to \`$BRANCH\` ($FILES_CHANGED files, $LESSONS_COUNT lessons, $TOTAL_BACKED_UP_BYTES). Audit: \`runs/backups/${TS}.md\`"
    if ! slk send "$SLACK_USER" "$MSG" >/dev/null 2>&1; then
      echo "[backup] slk send to $SLACK_USER failed"
    else
      echo "[backup] Slack DM sent to $SLACK_USER."
    fi
  fi
fi

  echo "[backup] audit: $REPORT_PATH"
} 2>&1 | tee -a "$LOG_PATH"

exit 0
