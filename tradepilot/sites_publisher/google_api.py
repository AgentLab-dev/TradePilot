"""Drive upload + Sites list/create. New Google Sites cannot write page HTML via API."""

from __future__ import annotations

import json
import os
import uuid
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

DRIVE_UPLOAD = "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,webViewLink,mimeType"
DRIVE_PERM = "https://www.googleapis.com/drive/v3/files/{file_id}/permissions"
SITES_LIST = "https://sites.googleapis.com/v1/sites?pageSize=20"
SITES_CREATE = "https://sites.googleapis.com/v1/sites"


def _request(method: str, url: str, token: str, data: bytes | None = None, content_type: str | None = None) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {token}"}
    if content_type:
        headers["Content-Type"] = content_type
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=60) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except HTTPError as exc:
        body = exc.read().decode() if exc.fp else ""
        raise RuntimeError(f"Google API {exc.code} {url}: {body[:800]}") from exc


def upload_html_doc(token: str, title: str, html: str) -> dict[str, Any]:
    """Upload HTML and convert it to a Google Doc (embeddable in Sites)."""
    boundary = f"======{uuid.uuid4().hex}======"
    metadata = json.dumps(
        {"name": title, "mimeType": "application/vnd.google-apps.document"}
    )
    parts = (
        f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{metadata}\r\n"
        f"--{boundary}\r\nContent-Type: text/html; charset=UTF-8\r\n\r\n{html}\r\n"
        f"--{boundary}--\r\n"
    )
    created = _request(
        "POST",
        DRIVE_UPLOAD,
        token,
        data=parts.encode("utf-8"),
        content_type=f"multipart/related; boundary={boundary}",
    )
    _request(
        "POST",
        DRIVE_PERM.format(file_id=created["id"]),
        token,
        data=json.dumps({"role": "reader", "type": "anyone"}).encode(),
        content_type="application/json",
    )
    return created


def list_sites(token: str) -> list[dict[str, Any]]:
    payload = _request("GET", SITES_LIST, token)
    return list(payload.get("sites") or [])


def create_site_from_source(token: str, title: str, source_site: str) -> dict[str, Any]:
    """New Sites API only creates by copying an existing site."""
    name = source_site if source_site.startswith("sites/") else f"sites/{source_site}"
    return _request(
        "POST",
        SITES_CREATE,
        token,
        data=json.dumps({"title": title, "name": name}).encode(),
        content_type="application/json",
    )


def optional_source_site() -> str | None:
    return os.environ.get("GOOGLE_SITES_SOURCE")
