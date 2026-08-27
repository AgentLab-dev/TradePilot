"""Publish FULL CHECK universe to local HTML, then Google Doc / Sites when authed."""

from __future__ import annotations

import argparse
from pathlib import Path

from tradepilot.sites_publisher.render import render_docs_html, render_html
from tradepilot.sites_publisher.universe import snapshot

DEFAULT_OUT = (
    Path(__file__).resolve().parents[2]
    / "agents"
    / "ssr-st"
    / "workspace"
    / "Documents"
    / "sites"
    / "fullcheck-universe-flags.html"
)


def write_html(out: Path, html: str) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


def publish(
    *,
    html_only: bool = False,
    login: bool = False,
    out: str | None = None,
    credentials: str | None = None,
    title: str | None = None,
) -> dict:
    page = snapshot()
    html = render_html(page)
    dest = Path(out).expanduser() if out else DEFAULT_OUT
    written = write_html(dest, html)
    result: dict = {"html": str(written), "title": title or page["title"]}
    print(f"Wrote Sites-ready HTML: {written}")

    if html_only and not login:
        print("HTML-only. Google upload skipped.")
        return result

    from tradepilot.sites_publisher.auth import (
        access_token,
        credentials_path,
        load_token,
        login as google_login,
    )
    from tradepilot.sites_publisher.google_api import (
        export_plain,
        load_last_doc_id,
        missing_tickers,
        publish_to_web,
        save_last_doc_id,
        upload_html_doc,
        upload_text_doc,
    )

    creds = credentials_path(credentials)
    if login or load_token() is None:
        if not creds.exists():
            result["needs_google"] = str(creds)
            print(
                "Google is not connected. Create an OAuth Desktop client in Google Cloud "
                "(enable Drive API + Sites API), save the JSON as:\n"
                f"  {creds}\n"
                "then run: tradepilot sites-publish --login"
            )
            return result
        google_login(str(creds))

    token = access_token(str(creds) if creds.exists() else None)
    doc_title = title or f"{page['title']} — {page['as_of']}"
    docs_html = render_docs_html(page)
    expected = [row[0] for row in page["doc_rows"]]
    doc = upload_html_doc(token, doc_title, docs_html, file_id=load_last_doc_id())
    file_id = doc["id"]
    plain = export_plain(token, file_id)
    missing = missing_tickers(plain, expected)
    if missing:
        print(
            f"HTML import dropped {len(missing)} tickers. Re-uploading as plain text."
        )
        doc = upload_text_doc(token, doc_title, docs_html, file_id=file_id)
        file_id = doc["id"]
        plain = export_plain(token, file_id)
        missing = missing_tickers(plain, expected)
        if missing:
            raise SystemExit(
                f"Google Doc is incomplete after import; missing {len(missing)} tickers "
                f"(first: {', '.join(missing[:8])}). Not printing the Doc body."
            )
    pub_url = publish_to_web(token, file_id)
    save_last_doc_id(file_id, doc.get("webViewLink"))
    result["doc"] = doc
    result["pub_url"] = pub_url
    result["tickers_verified"] = len(expected)
    print(f"Google Doc (edit): {doc.get('webViewLink')}")
    print(f"Published page (embed this in Sites): {pub_url}")
    print(f"Verified {len(expected)}/{len(expected)} tickers in the 9x9 table.")

    link = result.get("pub_url") or doc.get("webViewLink", "")
    print(
        "\nSites: Insert → Embed the /pub URL (not Insert → Docs).\n"
        f"Embed URL: {link}"
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Publish FULL CHECK universe to Google Sites")
    parser.add_argument("--html-only", action="store_true", help="Write local HTML and stop")
    parser.add_argument("--login", action="store_true", help="Run Google OAuth before upload")
    parser.add_argument("--out", help="Local HTML path")
    parser.add_argument("--credentials", help="OAuth client JSON path")
    parser.add_argument("--title", help="Google Doc / site title")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    publish(
        html_only=args.html_only,
        login=args.login,
        out=args.out,
        credentials=args.credentials,
        title=args.title,
    )
    return 0
