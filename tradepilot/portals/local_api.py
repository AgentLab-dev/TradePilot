"""Localhost-only HTTP trigger for WSJ/IBD login + capture.

Does not accept passwords in the request body. Secrets stay in env / keyring /
portals.json on this machine.
"""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from tradepilot.portals.session import capture, login, session_status

LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
DEFAULT_PORT = 8765


def dispatch(method: str, path: str) -> tuple[int, dict]:
    route = (path.split("?", 1)[0] or "/").rstrip("/") or "/"
    method = method.upper()
    if method == "GET" and route == "/health":
        return 200, {"ok": True, "service": "tradepilot-portals"}
    if method == "GET" and route == "/status":
        return 200, session_status()
    if method == "POST" and route == "/login":
        result = login()
        return 200, {"ok": True, **result}
    if method == "POST" and route == "/capture":
        result = capture()
        return 200, {"ok": True, **result}
    return 404, {
        "ok": False,
        "error": "not found",
        "routes": ["GET /health", "GET /status", "POST /login", "POST /capture"],
    }


class PortalHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("portal-api %s\n" % (fmt % args))

    def _read_body(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        if length:
            self.rfile.read(length)

    def _send(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        code, payload = dispatch("GET", self.path)
        self._send(code, payload)

    def do_POST(self) -> None:  # noqa: N802
        self._read_body()
        code, payload = dispatch("POST", self.path)
        self._send(code, payload)


def serve(*, host: str = "127.0.0.1", port: int = DEFAULT_PORT) -> None:
    if host not in LOCAL_HOSTS:
        raise SystemExit("portal API binds localhost only (127.0.0.1 / localhost / ::1)")
    httpd = ThreadingHTTPServer((host, port), PortalHandler)
    print(
        f"Portal API http://{host}:{port}\n"
        "  GET  /health   GET /status\n"
        "  POST /login    POST /capture\n"
        "Passwords are not accepted over HTTP. Use .env / keyring / portals.json."
    )
    httpd.serve_forever()
