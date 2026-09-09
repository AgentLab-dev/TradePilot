"""Load WSJ / IBD emails and passwords from env, .env, keyring, or portals.json.

Never print secret values. Never require a password in chat.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from tradepilot.portals.paths import CFG_PATH, ENV_FILES

KEYRING_SERVICE = "tradepilot"


def load_env_file(path: Path) -> None:
    """Set keys from a dotenv file only when they are not already in the environment."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key.startswith("export "):
            key = key[7:].strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value


def load_env() -> None:
    for path in ENV_FILES:
        load_env_file(path)


def load_cfg() -> dict:
    if not CFG_PATH.is_file():
        return {}
    data = json.loads(CFG_PATH.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _block(cfg: dict, name: str) -> dict:
    block = cfg.get(name)
    return block if isinstance(block, dict) else {}


def _keyring_password(name: str) -> str:
    try:
        import keyring
    except ImportError:
        return ""
    for username in (f"{name}-password", f"{name.upper()}_PASSWORD"):
        try:
            value = keyring.get_password(KEYRING_SERVICE, username)
        except Exception:
            value = None
        if value:
            return str(value)
    return ""


def portal_email(cfg: dict, name: str) -> str:
    env = (
        os.environ.get(f"{name.upper()}_USER", "")
        or os.environ.get(f"{name.upper()}_EMAIL", "")
    )
    if env:
        return env
    block = _block(cfg, name)
    return str(block.get("email") or cfg.get(f"{name}_email") or "")


def portal_password(cfg: dict, name: str) -> str:
    env = os.environ.get(f"{name.upper()}_PASSWORD", "")
    if env:
        return env
    keyed = _keyring_password(name)
    if keyed:
        return keyed
    block = _block(cfg, name)
    return str(block.get("password") or "")


def portal_signin(cfg: dict, name: str, default: str) -> str:
    block = _block(cfg, name)
    return str(block.get("signin") or block.get("url") or default)


def credential_flags(cfg: dict | None = None) -> dict[str, bool]:
    """Booleans only — never the secret values."""
    cfg = load_cfg() if cfg is None else cfg
    return {
        "wsj_user_set": bool(portal_email(cfg, "wsj")),
        "ibd_user_set": bool(portal_email(cfg, "ibd")),
        "wsj_password_set": bool(portal_password(cfg, "wsj")),
        "ibd_password_set": bool(portal_password(cfg, "ibd")),
    }
