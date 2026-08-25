#!/usr/bin/env bash
# Headless Miro REST helper — mirrors the Jira API-token pattern.
# Auth: reads MIRO_TOKEN from the environment (set it in ~/.zshrc).
#   export MIRO_TOKEN="<your Miro app access token>"
#
# Usage:
#   miro_api.sh boards                         # list boards
#   miro_api.sh board <board_id>               # get one board
#   miro_api.sh items <board_id>               # list items on a board
#   miro_api.sh sticky <board_id> "text"       # create a sticky note
#   miro_api.sh raw GET /v2/boards             # arbitrary call (METHOD PATH [JSON_BODY])
#
# All calls hit https://api.miro.com and emit JSON.

set -euo pipefail

BASE="https://api.miro.com"

if [[ -z "${MIRO_TOKEN:-}" ]]; then
  # try to pull it from ~/.zshrc without a full shell init
  MIRO_TOKEN="$(grep -E '^[[:space:]]*export[[:space:]]+MIRO_TOKEN=' "$HOME/.zshrc" 2>/dev/null \
    | tail -1 | sed -E 's/.*MIRO_TOKEN=//; s/^["'\'']//; s/["'\'']$//')"
fi

if [[ -z "${MIRO_TOKEN:-}" ]]; then
  echo "ERROR: MIRO_TOKEN is not set. Add to ~/.zshrc:  export MIRO_TOKEN=\"<token>\"" >&2
  exit 1
fi

auth=(-H "Authorization: Bearer ${MIRO_TOKEN}" -H "Accept: application/json")

cmd="${1:-boards}"; shift || true

case "$cmd" in
  boards)
    curl -s "${auth[@]}" "$BASE/v2/boards?limit=50" ;;
  board)
    curl -s "${auth[@]}" "$BASE/v2/boards/$1" ;;
  items)
    curl -s "${auth[@]}" "$BASE/v2/boards/$1/items?limit=50" ;;
  sticky)
    bid="$1"; text="$2"
    curl -s "${auth[@]}" -H "Content-Type: application/json" -X POST \
      "$BASE/v2/boards/$bid/sticky_notes" \
      -d "{\"data\":{\"content\":\"${text}\"}}" ;;
  raw)
    method="$1"; path="$2"; body="${3:-}"
    if [[ -n "$body" ]]; then
      curl -s "${auth[@]}" -H "Content-Type: application/json" -X "$method" "$BASE$path" -d "$body"
    else
      curl -s "${auth[@]}" -X "$method" "$BASE$path"
    fi ;;
  *)
    echo "Unknown command: $cmd" >&2
    echo "Try: boards | board <id> | items <id> | sticky <id> \"text\" | raw <METHOD> <PATH> [BODY]" >&2
    exit 2 ;;
esac
