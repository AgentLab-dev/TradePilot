#!/usr/bin/env python3
"""Local IBD + WSJ capture bot. Passwords never go to git or stdout.

  python3 ibd_wsj_capture.py --login   # headed Chromium, save cookies
  python3 ibd_wsj_capture.py           # reuse profile / storage_state.json
  python3 ibd_wsj_capture.py --status

Same as `tradepilot portal-capture`. Emails: portals.json or WSJ_USER / IBD_USER.
Passwords: env WSJ_PASSWORD / IBD_PASSWORD or keyring (optional; --login can be manual 2FA).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tradepilot.portals.paths import CFG_PATH, PROFILE_DIR, SECRETS, STATE_PATH  # noqa: E402
from tradepilot.portals.session import LISTS, capture, login, session_status  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="IBD + WSJ local capture bot")
    ap.add_argument("--login", action="store_true", help="Headed login; save storage_state.json")
    ap.add_argument("--status", action="store_true", help="Show whether a saved session exists")
    ap.add_argument("--wait-seconds", type=int, default=120)
    args = ap.parse_args()
    if args.status:
        print(json.dumps(session_status(), indent=2))
        return 0
    if args.login:
        login(wait_seconds=args.wait_seconds)
    else:
        capture()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
