"""Local portal capture bot — URLs and secrets path (no network, no passwords)."""
import json
from pathlib import Path

from tradepilot.cli import build_parser


def test_parser_exposes_portal_capture():
    parser = build_parser()
    subparsers = next(action for action in parser._actions if action.dest == "command")
    assert "portal-capture" in subparsers.choices


def test_capture_script_lists_and_secrets_dir():
    import importlib.util

    root = Path(__file__).resolve().parents[1]
    path = (
        root
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
    assert mod.SECRETS == root / "agents" / "ssr-st" / "secrets"
    assert mod.CFG_PATH.name == "portals.json"
    example = json.loads(
        (root / "agents" / "ssr-st" / "secrets" / "portals.example.json").read_text()
    )
    assert "password" not in example.get("wsj", {})
    assert "password" not in example.get("ibd", {})
    assert "YOUR_WSJ_EMAIL" in example["wsj"]["email"]
