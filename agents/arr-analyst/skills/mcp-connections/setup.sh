#!/usr/bin/env bash
# setup.sh — Configure MCP connections for a Cursor workspace
#
# Usage:
#   ~/.cursor/skills/mcp-connections/setup.sh /path/to/your/project
#
# What it does:
#   1. Copies mcp-template.json → <project>/.cursor/mcp.json
#   2. Replaces placeholder paths with actual values
#   3. Validates that required env vars and binaries exist
#   4. Reports any missing prerequisites

set -euo pipefail

SKILL_DIR="$HOME/.cursor/skills/mcp-connections"
TEMPLATE="$SKILL_DIR/mcp-template.json"
SNOWFLAKE_SCRIPT="$SKILL_DIR/snowflake_mcp_server.py"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
warn() { echo -e "  ${YELLOW}⚠${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; }

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <project-directory>"
    echo ""
    echo "Example:"
    echo "  $0 ~/Documents/Cursor/eda-dbt-em"
    exit 1
fi

PROJECT_DIR="$(cd "$1" && pwd)"
TARGET_DIR="$PROJECT_DIR/.cursor"
TARGET_FILE="$TARGET_DIR/mcp.json"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  MCP Connections Setup for Cursor Workspace  ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "Project: $PROJECT_DIR"
echo ""

# --- Step 1: Copy template ---
echo "Step 1: Copying mcp.json template"

if [[ ! -f "$TEMPLATE" ]]; then
    fail "Template not found at $TEMPLATE"
    exit 1
fi

mkdir -p "$TARGET_DIR"

if [[ -f "$TARGET_FILE" ]]; then
    warn "Existing mcp.json found — backing up to mcp.json.bak"
    cp "$TARGET_FILE" "$TARGET_FILE.bak"
fi

cp "$TEMPLATE" "$TARGET_FILE"
ok "Copied template to $TARGET_FILE"

# --- Step 2: Replace placeholders ---
echo ""
echo "Step 2: Configuring project-specific paths"

UVX_PATH="$HOME/.local/bin/uvx"
DBT_PATH="$HOME/Library/Python/3.13/bin/dbt"

if [[ "$(uname)" == "Darwin" ]]; then
    sed -i '' "s|__REPLACE_WITH_PROJECT_DIR__|$PROJECT_DIR|g" "$TARGET_FILE"
    sed -i '' "s|\${HOME}|$HOME|g" "$TARGET_FILE"
else
    sed -i "s|__REPLACE_WITH_PROJECT_DIR__|$PROJECT_DIR|g" "$TARGET_FILE"
    sed -i "s|\${HOME}|$HOME|g" "$TARGET_FILE"
fi

ok "Set DBT_PROJECT_DIR to $PROJECT_DIR"
ok "Resolved \$HOME paths"

# --- Step 3: Validate prerequisites ---
echo ""
echo "Step 3: Validating prerequisites"

ISSUES=0

# Python 3
if command -v python3 &>/dev/null; then
    ok "python3 found at $(which python3)"
else
    fail "python3 not found in PATH"
    ((ISSUES++))
fi

# Snowflake MCP server
if [[ -f "$SNOWFLAKE_SCRIPT" ]]; then
    ok "snowflake_mcp_server.py found"
else
    fail "snowflake_mcp_server.py not found at $SNOWFLAKE_SCRIPT"
    ((ISSUES++))
fi

# snowflake-connector-python
if python3 -c "import snowflake.connector" 2>/dev/null; then
    ok "snowflake-connector-python installed"
else
    warn "snowflake-connector-python not installed (run: pip3 install snowflake-connector-python)"
    ((ISSUES++))
fi

# MCP SDK
if python3 -c "import mcp" 2>/dev/null; then
    ok "mcp Python SDK installed"
else
    warn "mcp Python SDK not installed (run: pip3 install mcp)"
    ((ISSUES++))
fi

# uvx (for dbt-mcp)
if [[ -f "$UVX_PATH" ]] || command -v uvx &>/dev/null; then
    ok "uvx found"
else
    warn "uvx not found (install uv: curl -LsSf https://astral.sh/uv/install.sh | sh)"
    ((ISSUES++))
fi

# dbt
if [[ -f "$DBT_PATH" ]] || command -v dbt &>/dev/null; then
    ok "dbt found"
else
    warn "dbt not found at $DBT_PATH"
    ((ISSUES++))
fi

# sf-mcp-server (Salesforce)
if command -v sf-mcp-server &>/dev/null || [[ -f "/opt/homebrew/bin/sf-mcp-server" ]]; then
    ok "sf-mcp-server found"
else
    warn "sf-mcp-server not found (install: npm install -g sf-mcp-server)"
    ((ISSUES++))
fi

# npx (for Sigma)
if command -v npx &>/dev/null; then
    ok "npx found"
else
    warn "npx not found (install Node.js)"
    ((ISSUES++))
fi

# dbt Cloud env vars
echo ""
echo "Step 4: Checking environment variables"

check_env() {
    local var_name="$1"
    local server="$2"
    if [[ -n "${!var_name:-}" ]]; then
        ok "$var_name is set ($server)"
    else
        warn "$var_name is not set ($server) — check ~/.zshrc"
        ((ISSUES++))
    fi
}

check_env "DBT_CLOUD_HOST" "dbt Cloud"
check_env "DBT_CLOUD_API_TOKEN" "dbt Cloud"
check_env "DBT_CLOUD_ACCOUNT_ID" "dbt Cloud"
check_env "DBT_CLOUD_PROJECT_ID" "dbt Cloud"

# GitHub uses gh CLI with OAuth — check if gh is authenticated
if command -v gh &>/dev/null; then
    if gh auth status &>/dev/null 2>&1; then
        ok "gh CLI authenticated"
    else
        warn "gh CLI installed but not authenticated (run: gh auth login)"
        ((ISSUES++))
    fi
else
    warn "gh CLI not found (install: brew install gh)"
    ((ISSUES++))
fi

# --- Summary ---
echo ""
echo "════════════════════════════════════════════════"
if [[ $ISSUES -eq 0 ]]; then
    echo -e "${GREEN}Setup complete — no issues found.${NC}"
else
    echo -e "${YELLOW}Setup complete with $ISSUES warning(s).${NC}"
    echo "Fix the warnings above, then restart Cursor."
fi
echo ""
echo "Next steps:"
echo "  1. Restart Cursor to load the new MCP servers."
echo "  2. For Slack: call mcp_auth on first use."
echo "  3. For Atlassian: browser OAuth prompt on first use."
echo ""
