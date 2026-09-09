"""Local portal capture bot — URLs and secrets path (no network, no passwords)."""
from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

from tradepilot.cli import build_parser
from tradepilot.portals.local_api import dispatch, serve
from tradepilot.portals.paths import CFG_PATH, PROFILE_DIR, SECRETS, STATE_PATH
from tradepilot.portals.secrets import load_env_file, portal_email, portal_password
from tradepilot.portals.session import LISTS, session_status


ROOT = Path(__file__).resolve().parents[1]


def test_parser_exposes_portal_capture():
    parser = build_parser()
    subparsers = next(action for action in parser._actions if action.dest == "command")
    assert "portal-capture" in subparsers.choices
    portal = subparsers.choices["portal-capture"]
    dests = {a.dest for a in portal._actions}
    assert {"login", "status", "serve", "port", "wait_seconds"} <= dests


def test_capture_script_lists_and_secrets_dir():
    import importlib.util

    path = (
        ROOT
        / "agents"
        / "ssr-st"
        / "workspace"
        / "Documents"
        / "market_data"
        / "ibd_wsj_capture.py"
    )
    spec = importlib.util.spec_from_file_location("ibd_wsj_capture", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert len(mod.LISTS) == 8
    assert any("ibd-50" in u for _, u in mod.LISTS)
    assert mod.SECRETS == ROOT / "agents" / "ssr-st" / "secrets"
    assert mod.CFG_PATH.name == "portals.json"
    assert mod.STATE_PATH.name == "storage_state.json"
    assert mod.PROFILE_DIR.name == "browser-profile"
    example = json.loads(
        (ROOT / "agents" / "ssr-st" / "secrets" / "portals.example.json").read_text()
    )
    assert "password" not in example.get("wsj", {})
    assert "password" not in example.get("ibd", {})
    assert "YOUR_WSJ_EMAIL" in example["wsj"]["email"]


def test_env_example_is_placeholders_only():
    text = (ROOT / ".env.example").read_text()
    assert "WSJ_USER=" in text
    assert "IBD_USER=" in text
    assert "WSJ_PASSWORD=" in text
    assert "IBD_PASSWORD=" in text
    for line in text.splitlines():
        if line.startswith("#") or "=" not in line:
            continue
        _, _, value = line.partition("=")
        assert value == "", f"placeholder must be empty: {line}"


def test_package_paths_and_lists():
    assert len(LISTS) == 8
    assert SECRETS == ROOT / "agents" / "ssr-st" / "secrets"
    assert CFG_PATH == SECRETS / "portals.json"
    assert STATE_PATH == SECRETS / "storage_state.json"
    assert PROFILE_DIR == SECRETS / "browser-profile"


def test_load_env_file_does_not_override(monkeypatch, tmp_path):
    envf = tmp_path / ".env"
    envf.write_text("WSJ_USER=fromfile@example.com\nWSJ_PASSWORD=fromfile\n")
    monkeypatch.setenv("WSJ_USER", "already@example.com")
    monkeypatch.delenv("WSJ_PASSWORD", raising=False)
    load_env_file(envf)
    assert os.environ["WSJ_USER"] == "already@example.com"
    assert os.environ["WSJ_PASSWORD"] == "fromfile"


def test_portal_email_prefers_wsj_user(monkeypatch):
    monkeypatch.setenv("WSJ_USER", "user@example.com")
    assert portal_email({}, "wsj") == "user@example.com"


def test_portal_password_prefers_env_over_json(monkeypatch):
    monkeypatch.setenv("IBD_PASSWORD", "from-env")
    assert portal_password({"ibd": {"password": "from-json"}}, "ibd") == "from-env"


def test_session_status_has_no_secrets(monkeypatch):
    monkeypatch.setenv("WSJ_PASSWORD", "should-not-appear")
    monkeypatch.setenv("IBD_PASSWORD", "should-not-appear")
    status = session_status()
    blob = json.dumps(status)
    assert "should-not-appear" not in blob
    assert "wsj_password_set" in status
    assert isinstance(status["wsj_password_set"], bool)


def test_dispatch_health_and_unknown():
    code, payload = dispatch("GET", "/health")
    assert code == 200
    assert payload["ok"] is True
    code, payload = dispatch("GET", "/nope")
    assert code == 404
    assert "POST /login" in payload["routes"]


@patch("tradepilot.portals.local_api.login", return_value={"login": {"wsj": "signed_in"}})
def test_dispatch_login_ignores_http_body(mock_login):
    code, payload = dispatch("POST", "/login")
    assert code == 200
    mock_login.assert_called_once_with()
    assert payload["ok"] is True


def test_serve_localhost_only():
    try:
        serve(host="0.0.0.0", port=9)
    except SystemExit as exc:
        assert "localhost" in str(exc)
    else:
        raise AssertionError("serve must refuse non-localhost binds")


def test_portal_login_script_exists():
    path = (
        ROOT
        / "agents"
        / "ssr-st"
        / "workspace"
        / "Documents"
        / "market_data"
        / "portal_login.py"
    )
    assert path.is_file()
    text = path.read_text()
    assert "Never paste" in text or "no password" in text.lower() or "No passwords" in text
