"""Publish FULL CHECK universe to local HTML, then Google Doc / Sites when authed."""

from __future__ import annotations

import argparse
from pathlib import Path

from tradepilot.sites_publisher.render import render_html
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
        create_site_from_source,
        list_sites,
        optional_source_site,
        upload_html_doc,
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
    doc = upload_html_doc(token, doc_title, html)
    result["doc"] = doc
    print(f"Google Doc (embed this in Sites): {doc.get('webViewLink')}")

    try:
        sites = list_sites(token)
    except RuntimeError as exc:
        print(f"Sites list skipped: {exc}")
        sites = []
    result["sites"] = sites
    if sites:
        print("Existing Google Sites:")
        for site in sites:
            print(f"  - {site.get('title')}  {site.get('siteUrl') or site.get('name')}")
    else:
        print("No Google Sites visible on this account yet.")

    source = optional_source_site()
    if source:
        try:
            created = create_site_from_source(token, doc_title, source)
            result["created_site"] = created
            print(f"Copied site: {created.get('siteUrl') or created.get('name')}")
        except RuntimeError as exc:
            print(f"Site copy failed: {exc}")

    link = doc.get("webViewLink", "")
    print(
        "\nTo finish on Google Sites:\n"
        "  1. Open https://sites.google.com and create or open a site.\n"
        "  2. Insert > Docs (or Embed URL) and paste the Google Doc link above.\n"
        f"  3. Publish the site.\n"
        f"Doc: {link}"
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
