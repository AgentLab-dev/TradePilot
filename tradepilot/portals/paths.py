"""Gitignored secret paths and FULL CHECK write targets."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SECRETS = REPO_ROOT / "agents" / "ssr-st" / "secrets"
DOCS = REPO_ROOT / "agents" / "ssr-st" / "workspace" / "Documents"
CFG_PATH = SECRETS / "portals.json"
STATE_PATH = SECRETS / "storage_state.json"
PROFILE_DIR = SECRETS / "browser-profile"
ENV_FILES = (REPO_ROOT / ".env", SECRETS / ".env")
OUT_LISTS = DOCS / "ibd_stock_lists.md"
OUT_NEWS = DOCS / "news_sweep.md"
