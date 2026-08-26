"""Installed-app OAuth for Google Drive + Sites. Token stays local, never committed."""

from __future__ import annotations

import json
import os
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

SCOPES = (
    "https://www.googleapis.com/auth/drive.file "
    "https://www.googleapis.com/auth/sites"
)
TOKEN_URI = "https://oauth2.googleapis.com/token"
AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
REDIRECT_PORT = 8753
REDIRECT_URI = f"http://127.0.0.1:{REDIRECT_PORT}/"


def default_secrets_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "agents" / "sites-publisher" / "secrets"


def credentials_path(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit).expanduser()
    env = os.environ.get("GOOGLE_SITES_CREDENTIALS")
    if env:
        return Path(env).expanduser()
    return default_secrets_dir() / "credentials.json"


def token_path() -> Path:
    env = os.environ.get("GOOGLE_SITES_TOKEN")
    if env:
        return Path(env).expanduser()
    return default_secrets_dir() / "token.json"


def load_client(path: Path) -> dict:
    raw = json.loads(path.read_text())
    return raw.get("installed") or raw.get("web") or raw


def load_token(path: Path | None = None) -> dict | None:
    target = path or token_path()
    if not target.exists():
        return None
    return json.loads(target.read_text())


def save_token(token: dict, path: Path | None = None) -> Path:
    target = path or token_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(token, indent=2))
    return target


def _post_form(url: str, data: dict) -> dict:
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def refresh_access_token(token: dict, client: dict) -> dict:
    payload = _post_form(
        TOKEN_URI,
        {
            "client_id": client["client_id"],
            "client_secret": client.get("client_secret", ""),
            "refresh_token": token["refresh_token"],
            "grant_type": "refresh_token",
        },
    )
    token["access_token"] = payload["access_token"]
    if "expires_in" in payload:
        token["obtained_at"] = int(time.time())
        token["expires_in"] = int(payload["expires_in"])
    if payload.get("refresh_token"):
        token["refresh_token"] = payload["refresh_token"]
    return token


def token_expired(token: dict, skew: int = 60) -> bool:
    obtained = int(token.get("obtained_at") or 0)
    expires_in = int(token.get("expires_in") or 0)
    if not obtained or not expires_in:
        return False
    return time.time() >= obtained + expires_in - skew


def login(client_file: str | None = None) -> dict:
    client = load_client(credentials_path(client_file))
    code_holder: dict[str, str] = {}
    done = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            if params.get("code"):
                code_holder["code"] = params["code"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"<html><body><p>Trade Pilot Sites Publisher connected. You can close this tab.</p></body></html>")
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing code")
            done.set()

        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            return

    server = HTTPServer(("127.0.0.1", REDIRECT_PORT), Handler)
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    params = {
        "client_id": client["client_id"],
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES.strip(),
        "access_type": "offline",
        "prompt": "consent",
    }
    url = AUTH_URI + "?" + urllib.parse.urlencode(params)
    print(f"Open this Google consent URL if the browser does not:\n{url}\n")
    webbrowser.open(url)
    if not done.wait(timeout=180):
        raise SystemExit("Google login timed out after 180s. Re-run tradepilot sites-publish --login")
    payload = _post_form(
        TOKEN_URI,
        {
            "client_id": client["client_id"],
            "client_secret": client.get("client_secret", ""),
            "code": code_holder["code"],
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
        },
    )
    payload["obtained_at"] = int(time.time())
    save_token(payload)
    print(f"Saved token to {token_path()}")
    return payload


def access_token(client_file: str | None = None) -> str:
    client_file_path = credentials_path(client_file)
    token = load_token()
    if token is None:
        raise SystemExit(
            "No Google token. Place an OAuth Desktop client JSON at "
            f"{credentials_path()} then run: tradepilot sites-publish --login"
        )
    if token_expired(token) or not token.get("access_token"):
        if not client_file_path.exists():
            raise SystemExit(f"Token expired and credentials missing at {client_file_path}")
        client = load_client(client_file_path)
        token = refresh_access_token(token, client)
        save_token(token)
    return str(token["access_token"])
