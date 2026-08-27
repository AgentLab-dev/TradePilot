"""Drive upload + Sites list/create. New Google Sites cannot write page HTML via API."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

DRIVE_UPLOAD = "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,webViewLink,mimeType"
DRIVE_UPDATE = (
    "https://www.googleapis.com/upload/drive/v3/files/{file_id}"
    "?uploadType=multipart&fields=id,name,webViewLink,mimeType"
)
DRIVE_PERM = "https://www.googleapis.com/drive/v3/files/{file_id}/permissions"
DRIVE_EXPORT = "https://www.googleapis.com/drive/v3/files/{file_id}/export?mimeType=text/plain"
DRIVE_REVISIONS = "https://www.googleapis.com/drive/v3/files/{file_id}/revisions?fields=revisions(id)"
DRIVE_REVISION = "https://www.googleapis.com/drive/v3/files/{file_id}/revisions/{revision_id}"
SITES_LIST = "https://sites.googleapis.com/v1/sites?pageSize=20"
SITES_CREATE = "https://sites.googleapis.com/v1/sites"


def last_doc_path() -> Path:
    env = os.environ.get("GOOGLE_SITES_LAST_DOC")
    if env:
        return Path(env).expanduser()
    return (
        Path(__file__).resolve().parents[2]
        / "agents"
        / "sites-publisher"
        / "secrets"
        / "last_doc.json"
    )


def load_last_doc_id() -> str | None:
    path = last_doc_path()
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text()).get("id")
    except json.JSONDecodeError:
        return None


def save_last_doc_id(file_id: str, web_view: str | None = None) -> None:
    path = last_doc_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"id": file_id, "webViewLink": web_view or ""}, indent=2))


def _request(
    method: str,
    url: str,
    token: str,
    data: bytes | None = None,
    content_type: str | None = None,
    json_response: bool = True,
) -> dict[str, Any] | str:
    headers = {"Authorization": f"Bearer {token}"}
    if content_type:
        headers["Content-Type"] = content_type
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8", "replace")
            if not json_response:
                return raw
            return json.loads(raw) if raw else {}
    except HTTPError as exc:
        body = exc.read().decode() if exc.fp else ""
        raise RuntimeError(f"Google API {exc.code} {url}: {body[:800]}") from exc


def _multipart(title: str, body: str, media_type: str) -> tuple[bytes, str]:
    boundary = f"======{uuid.uuid4().hex}======"
    metadata = json.dumps({"name": title, "mimeType": "application/vnd.google-apps.document"})
    parts = (
        f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{metadata}\r\n"
        f"--{boundary}\r\nContent-Type: {media_type}; charset=UTF-8\r\n\r\n{body}\r\n"
        f"--{boundary}--\r\n"
    )
    return parts.encode("utf-8"), f"multipart/related; boundary={boundary}"


def _share_anyone(token: str, file_id: str) -> None:
    try:
        _request(
            "POST",
            DRIVE_PERM.format(file_id=file_id),
            token,
            data=json.dumps({"role": "reader", "type": "anyone"}).encode(),
            content_type="application/json",
        )
    except RuntimeError as exc:
        if "already" not in str(exc).lower() and "403" not in str(exc):
            raise


def _put_doc(token: str, title: str, body: str, media_type: str, file_id: str | None) -> dict[str, Any]:
    payload, content_type = _multipart(title, body, media_type)
    if file_id:
        try:
            updated = _request(
                "PATCH",
                DRIVE_UPDATE.format(file_id=file_id),
                token,
                data=payload,
                content_type=content_type,
            )
            assert isinstance(updated, dict)
            _share_anyone(token, updated["id"])
            return updated
        except RuntimeError:
            pass
    created = _request("POST", DRIVE_UPLOAD, token, data=payload, content_type=content_type)
    assert isinstance(created, dict)
    _share_anyone(token, created["id"])
    return created


def upload_html_doc(token: str, title: str, html: str, file_id: str | None = None) -> dict[str, Any]:
    """Upload Docs-import HTML and convert it to a Google Doc (embeddable in Sites)."""
    return _put_doc(token, title, html, "text/html", file_id)


def upload_text_doc(token: str, title: str, html: str, file_id: str | None = None) -> dict[str, Any]:
    """Fallback: strip tags to plain text so Drive cannot drop tables."""
    import re

    text = re.sub(r"(?i)<br\s*/?>", "\n", html)
    text = re.sub(r"(?i)</p>", "\n", text)
    text = re.sub(r"(?i)</h[1-6]>", "\n", text)
    text = re.sub(r"(?i)</tr>", "\n", text)
    text = re.sub(r"(?i)</t[dh]>", " | ", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return _put_doc(token, title, text.strip(), "text/plain", file_id)


def export_plain(token: str, file_id: str) -> str:
    raw = _request("GET", DRIVE_EXPORT.format(file_id=file_id), token, json_response=False)
    return str(raw)


def missing_tickers(plain: str, tickers: list[str]) -> list[str]:
    return [t for t in tickers if t not in plain]


def publish_to_web(token: str, file_id: str) -> str:
    payload = _request("GET", DRIVE_REVISIONS.format(file_id=file_id), token)
    assert isinstance(payload, dict)
    revisions = payload.get("revisions") or []
    if not revisions:
        return f"https://docs.google.com/document/d/{file_id}/edit"
    rev_id = revisions[-1]["id"]
    try:
        _request(
            "PATCH",
            DRIVE_REVISION.format(file_id=file_id, revision_id=rev_id),
            token,
            data=json.dumps(
                {
                    "published": True,
                    "publishAuto": True,
                    "publishedOutsideDomain": True,
                }
            ).encode(),
            content_type="application/json",
        )
    except RuntimeError:
        pass
    return f"https://docs.google.com/document/d/{file_id}/pub"


def list_sites(token: str) -> list[dict[str, Any]]:
    payload = _request("GET", SITES_LIST, token)
    assert isinstance(payload, dict)
    return list(payload.get("sites") or [])


def create_site_from_source(token: str, title: str, source_site: str) -> dict[str, Any]:
    """New Sites API only creates by copying an existing site."""
    name = source_site if source_site.startswith("sites/") else f"sites/{source_site}"
    created = _request(
        "POST",
        SITES_CREATE,
        token,
        data=json.dumps({"title": title, "name": name}).encode(),
        content_type="application/json",
    )
    assert isinstance(created, dict)
    return created


def optional_source_site() -> str | None:
    return os.environ.get("GOOGLE_SITES_SOURCE")
