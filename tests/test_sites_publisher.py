"""Tests for the Google Sites publisher bot."""

from pathlib import Path

from tradepilot.cli import build_parser, main
from tradepilot.sites_publisher.publish import publish
from tradepilot.sites_publisher.render import render_html
from tradepilot.sites_publisher.universe import NAMES, snapshot


def test_parser_exposes_sites_publish():
    parser = build_parser()
    subparsers = next(action for action in parser._actions if action.dest == "command")
    assert set(subparsers.choices) == {"version", "doctor", "sites-publish"}


def test_render_html_contains_universe():
    html = render_html()
    assert "FULL CHECK universe" in html
    assert "INTU" in html
    assert "BEARISH" in html
    assert "Read-only until go" in html
    assert "<script" not in html
    assert len(NAMES) == 24


def test_sites_publish_html_only(tmp_path: Path, capsys):
    out = tmp_path / "universe.html"
    result = publish(html_only=True, out=str(out))
    assert Path(result["html"]).exists()
    body = out.read_text()
    assert snapshot()["top5"][0]["ticker"] in body
    captured = capsys.readouterr()
    assert "Wrote Sites-ready HTML" in captured.out


def test_cli_sites_publish_html_only(tmp_path: Path):
    out = tmp_path / "cli.html"
    assert main(["sites-publish", "--html-only", "--out", str(out)]) == 0
    assert out.exists()
    assert "NVDA" in out.read_text()
