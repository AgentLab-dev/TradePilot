#!/usr/bin/env python3
"""Headed WSJ + IBD login. Saves gitignored cookies/profile. No passwords in git.

  python3 portal_login.py
  tradepilot portal-capture --login

Secrets: copy .env.example → .env, or portals.example.json → portals.json,
and/or `python3 -m keyring set tradepilot wsj-password`. Never paste a password in chat.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tradepilot.portals.session import login  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="WSJ + IBD headed login")
    ap.add_argument("--wait-seconds", type=int, default=120)
    args = ap.parse_args()
    login(wait_seconds=args.wait_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
