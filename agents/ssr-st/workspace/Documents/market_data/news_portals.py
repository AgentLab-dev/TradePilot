#!/usr/bin/env python3
"""FULL CHECK / evening-wrap news floor: public RSS, optional Safari/Chrome tail.

Login to WSJ/MW is not this script. See agents/ssr-st/skills/news-portals/SKILL.md.

  python3 news_portals.py
  python3 news_portals.py --query "investor day"
  python3 news_portals.py --safari
  python3 news_portals.py --list-tabs
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "news_sweep.md"))
SAFARI = os.path.join(HERE, "safari_portal_tail.py")

FEEDS = [
    ("WSJ Markets", "https://feeds.a.dj.com/rss/RSSMarketsMain.xml"),
    ("WSJ US Business", "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml"),
    ("MarketWatch top", "https://feeds.marketwatch.com/marketwatch/topstories/"),
    ("MarketWatch pulse", "https://feeds.marketwatch.com/marketwatch/marketpulse/"),
    ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),
]

HDRS = [
    "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "-H", "Accept: application/rss+xml, application/xml, text/xml, */*",
]


def curl_xml(url: str, timeout: int = 25) -> str:
    try:
        p = subprocess.run(
            ["curl", "-sL", "-w", "\nHTTP_CODE:%{http_code}",
             "--max-time", str(timeout), *HDRS, url],
            capture_output=True, text=True, timeout=timeout + 5,
        )
        body = p.stdout or ""
        if "HTTP_CODE:" in body:
            body, code = body.rsplit("HTTP_CODE:", 1)
            code = code.strip()
            if code not in {"200", "301", "302"}:
                return ""
        return body
    except Exception:
        return ""


def _text(el: ET.Element | None) -> str:
    if el is None or el.text is None:
        return ""
    return html.unescape(el.text).strip()


def parse_items(xml_text: str, limit: int = 8) -> list[tuple[str, str, str]]:
    if not xml_text.strip():
        return []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    items: list[tuple[str, str, str]] = []
    for node in list(root.iter("item"))[:limit]:
        title = _text(node.find("title"))
        link = _text(node.find("link"))
        pub = _text(node.find("pubDate")) or _text(node.find("dc:date"))
        if not title:
            continue
        items.append((title, link, pub))
    if items:
        return items
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for node in list(root.iter("{http://www.w3.org/2005/Atom}entry"))[:limit]:
        title = _text(node.find("atom:title", ns)) or _text(
            node.find("{http://www.w3.org/2005/Atom}title")
        )
        link_el = node.find("{http://www.w3.org/2005/Atom}link")
        href = (link_el.get("href") if link_el is not None else "") or ""
        updated = _text(node.find("{http://www.w3.org/2005/Atom}updated"))
        if title:
            items.append((title, href, updated))
    return items


def run_safari(args: list[str]) -> str:
    cmd = [sys.executable, SAFARI, *args]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
        return (p.stdout or p.stderr or "").strip()
    except subprocess.TimeoutExpired:
        return (
            "Safari/Chrome tail timed out. Grant Automation permission "
            "(System Settings → Privacy & Security → Automation) and retry."
        )
    except Exception as e:
        return f"Safari/Chrome tail failed: {e}"


def matches_query(title: str, query: str) -> bool:
    if not query:
        return True
    t = title.lower()
    return all(tok.lower() in t for tok in query.split() if tok.lower() not in {"or", "and"})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", default="", help="Keep RSS items whose title contains these words")
    ap.add_argument("--safari", action="store_true", help="Also dump matching Safari/Chrome tabs")
    ap.add_argument("--list-tabs", action="store_true", help="List portal tabs only")
    args = ap.parse_args()

    if args.list_tabs:
        print(run_safari(["--list"]) or "(no matching tabs)")
        return 0

    now = dt.datetime.now().astimezone()
    lines = [
        f"# News sweep — {now.strftime('%a %Y-%m-%d %H:%M %Z')}",
        "",
        "_Public RSS floor. Paywall body needs Cursor browser or Safari tail. "
        "Skill: `news-portals`._",
        "",
    ]

    any_hit = False
    for name, url in FEEDS:
        raw = curl_xml(url)
        items = parse_items(raw)
        if args.query:
            items = [it for it in items if matches_query(it[0], args.query)]
        lines.append(f"## {name}")
        if not raw.strip():
            lines.append(f"_empty or blocked (`{url}`)_")
            lines.append("")
            continue
        if not items:
            lines.append("_no items (or none matched --query)_")
            lines.append("")
            continue
        any_hit = True
        for title, link, pub in items:
            extra = f" — {pub}" if pub else ""
            if link:
                lines.append(f"- [{title}]({link}){extra}")
            else:
                lines.append(f"- {title}{extra}")
        lines.append("")

    if args.safari:
        lines.append("## Safari / Chrome tail")
        lines.append("```")
        lines.append(run_safari([]) or "(no matching signed-in tabs)")
        lines.append("```")
        lines.append("")

    if args.query:
        lines.append(f"_Filter: `{args.query}`_")
        lines.append("")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")
    print(OUT)
    print(f"feeds_ok={any_hit} query={args.query!r}")
    return 0 if any_hit else 1


if __name__ == "__main__":
    raise SystemExit(main())
