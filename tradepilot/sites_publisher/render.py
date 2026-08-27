"""Render FULL CHECK universe to Google-Sites-safe HTML (inline CSS, no JS)."""

from __future__ import annotations

import html
from typing import Any, Iterable

from tradepilot.sites_publisher.universe import snapshot

TONE_BG = {
    "arm": "#e8f1fb",
    "gated": "#fff4d6",
    "manage": "#fff4d6",
    "neutral": "#f4f4f2",
    "avoid": "#fdecea",
    "kill": "#fdecea",
}


def _e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _row(cells: Iterable[Any], tone: str | None = None) -> str:
    bg = TONE_BG.get(tone or "", "")
    style = f' style="background:{bg}"' if bg else ""
    tds = "".join(f"<td>{_e(c)}</td>" for c in cells)
    return f"<tr{style}>{tds}</tr>"


def _table(headers: list[str], rows: list[str]) -> str:
    head = "".join(f"<th>{_e(h)}</th>" for h in headers)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def _plain_table(headers: list[str], rows: list[list[Any]]) -> str:
    head = "".join(f"<th>{_e(h)}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{_e(c)}</td>" for c in row) + "</tr>" for row in rows
    )
    return f'<table border="1" cellpadding="4" cellspacing="0"><tr>{head}</tr>{body}</table>'


def render_docs_html(data: dict[str, Any] | None = None) -> str:
    """Sites Doc: one table, 9 columns x 9 rows. No CSS."""
    page = data or snapshot()
    return (
        "<html><body>"
        f"<h1>{_e(page['title'])}</h1>"
        f"<p>{_e(page['as_of'])}. Read-only until go.</p>"
        f"{_plain_table(page['doc_headers'], page['doc_rows'])}"
        "</body></html>"
    )


def render_html(data: dict[str, Any] | None = None) -> str:
    page = data or snapshot()
    stats = page["stats"]
    top_rows = [
        _row(
            [
                r["rank"],
                r["ticker"],
                r["why"],
                r["stkk"],
                r["stnow"],
                r["three_good"],
                r["whale"],
                r["iv_structure"],
                r["event"],
                r["after_gate"],
            ],
            r.get("tone"),
        )
        for r in page["top5"]
    ]
    model_rows = [_row(r, "gated") for r in page["model_top5"]]
    strat_rows = [_row(r) for r in page["strategies"]]
    name_rows = [
        _row(
            [
                n["ticker"],
                n["px"],
                n["industry"],
                n["stkk"],
                n["stnow"],
                n["three_good"],
                n["whale"],
                n["iv"],
                n["structure"],
                n["event"],
                n["model"],
                n["after_gate"],
            ],
            n.get("tone"),
        )
        for n in page["names"]
    ]
    industry_cards = "".join(
        f'<div class="card"><h3>{_e(title)}</h3><p>{_e(body)}</p></div>'
        for title, body in page["industries"]
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{_e(page["title"])}</title>
<style>
body {{ font: 14px/1.45 -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; color: #1a1a18; background: #fafaf8; margin: 0; }}
main {{ max-width: 1280px; margin: 0 auto; padding: 28px 20px 64px; }}
h1 {{ font-size: 24px; margin: 0 0 6px; }}
h2 {{ font-size: 18px; margin: 28px 0 8px; }}
h3 {{ font-size: 14px; margin: 0 0 6px; }}
p, .meta {{ color: #5c5c56; }}
.badge {{ display: inline-block; border: 1px solid #c9a227; color: #7a5b00; padding: 2px 8px; font-size: 12px; margin-left: 8px; vertical-align: middle; }}
.stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 16px 0 20px; }}
.stat {{ border: 1px solid #e6e6e1; background: #fff; padding: 12px; }}
.stat b {{ display: block; font-size: 20px; }}
.stat span {{ color: #6b6b64; font-size: 12px; }}
.callout {{ border: 1px solid #e0c36a; background: #fff8e5; padding: 12px 14px; margin: 12px 0 20px; }}
.grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }}
.card {{ border: 1px solid #e6e6e1; background: #fff; padding: 12px; }}
table {{ width: 100%; border-collapse: collapse; background: #fff; font-size: 12px; }}
th, td {{ border: 1px solid #e6e6e1; padding: 6px 8px; text-align: left; vertical-align: top; }}
th {{ background: #f4f4f2; font-weight: 600; }}
.legend {{ margin-top: 16px; font-size: 12px; color: #6b6b64; }}
@media (max-width: 900px) {{
  .stats, .grid {{ grid-template-columns: 1fr 1fr; }}
}}
</style>
</head>
<body>
<main>
  <h1>{_e(page["title"])} <span class="badge">Read-only until go</span></h1>
  <p class="meta">{_e(page["as_of"])}. {_e(page["source"])}</p>
  <div class="stats">
    <div class="stat"><b>{_e(stats["actionable"])}</b><span>Actionable #1 — Wed first-30 put debit</span></div>
    <div class="stat"><b>{_e(stats["gated_top"])}</b><span>After every gate (not raw GO)</span></div>
    <div class="stat"><b>{_e(stats["names"])}</b><span>Names in the scan</span></div>
    <div class="stat"><b>{_e(stats["structures"])}</b><span>Structures in the matrix</span></div>
  </div>
  <div class="callout"><strong>Model GO is not a take.</strong> {_e(page["callout"])}</div>
  <h2>Suggested top 5 (every flag applied)</h2>
  <p class="meta">Rank is action after event gate, book overlap, anti-chase, and PCE — not raw STNOW score.</p>
  {_table(["#", "Ticker", "Why it ranks", "STKK", "STNOW", "Three Good", "Whale", "IV / structure", "Event", "After gate"], top_rows)}
  <h2>Model top 5 (score only, before gates)</h2>
  {_table(["Rank", "Ticker", "Score", "Whale", "IV", "Routed structure", "Why it is not a take"], model_rows)}
  <h2>All 6 strategies</h2>
  {_table(["Quadrant", "Structure", "Names in this scan"], strat_rows)}
  <h2>Industries in the scan</h2>
  <div class="grid">{industry_cards}</div>
  <h2>All names, every flag</h2>
  {_table(["Ticker", "Spot", "Industry", "STKK", "STNOW", "3Good", "Whale", "IV", "Structure", "Event", "Model", "After every gate"], name_rows)}
  <p class="legend">{_e(page["legend"])}</p>
</main>
</body>
</html>
"""
