from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESK = ROOT / "docs" / "desk" / "index.html"
PUBLISHED = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQWnq16Jzrj91DqM1xlEukdqCpmI_3XnywQaQZ-l-tRN1-20pIsV38l3W7znjcOsSHuLJZyPzgFa7a-"
    "/pubhtml"
)


def test_desk_page_embeds_published_sheet_only():
    html = DESK.read_text(encoding="utf-8")
    assert "TradePilot Desk" in html
    assert "Live flags · latest book" in html
    assert PUBLISHED in html
    assert "gid=2024844456" in html
    assert "widget=true" in html
    assert "<iframe" in html
    assert "sandbox=" not in html
    assert "looker" not in html.lower()
    assert "login" not in html.lower()


def test_docs_root_points_at_desk():
    root = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    assert 'href="desk/"' in root
    assert (ROOT / "docs" / ".nojekyll").exists()
