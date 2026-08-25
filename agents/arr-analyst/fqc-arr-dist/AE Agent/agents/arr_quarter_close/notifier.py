"""Slack notifier for the Finance ARR Quarter Close (FQC-ARR) supervisor.

One thread per supervisor run:

* ``start(...)``  -> posts the parent message in the channel.
* ``post(...)``   -> posts a threaded reply under that parent.
* ``finish(...)`` -> posts a final summary reply.

Transport:

* ``slk send`` (slkcli) for the initial channel/DM message (it transparently
  resolves user ids to DM channels and creates the conversation if needed).
* ``slackApi`` (Node shim from slkcli) over ``node -e`` for threaded
  replies and to resolve the DM channel id when posting in a user-id thread.

If neither ``slk`` nor ``node`` is on PATH (or the slkcli npm package is
missing), the notifier degrades to logging and does not raise. Slack
failures must never block the supervisor.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)

SLKCLI_API_PATH = "/opt/homebrew/lib/node_modules/slkcli/src/api.js"

# Hard caps so a misconfigured channel or Slack outage can never block the
# supervisor for more than these durations.
SEND_TIMEOUT_S = 15.0
READ_TIMEOUT_S = 10.0
API_TIMEOUT_S = 15.0

# UI icons per RoleStatus value
STATUS_ICON = {
    "ok": ":white_check_mark:",
    "warn": ":warning:",
    "needs_input": ":pause_button:",
    "fail": ":x:",
    "skipped": ":fast_forward:",
}


@dataclass
class SlackNotifier:
    """Lazy, thread-aware Slack notifier scoped to one supervisor run."""

    channel: str
    enabled: bool = True
    label: str = ""                              # e.g. "EDAEM-3725"
    display_name: str = ""   # internal label only; do NOT embed in user-facing output (no signatures)
    thread_ts: Optional[str] = None              # set by start()
    resolved_channel_id: Optional[str] = None    # DM channel for U... ids
    _has_slk: bool = field(default=False, init=False)
    _has_node: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self._has_slk = shutil.which("slk") is not None
        self._has_node = shutil.which("node") is not None
        if not self._has_slk:
            log.warning("slk CLI not on PATH; Slack notifications will be logged only.")

    # ------------------------------------------------------------------ start
    def start(self, text: str) -> Optional[str]:
        """Post the parent message; record thread_ts for replies."""
        if not self.enabled:
            return None
        if not self._has_slk:
            log.info("[slack:disabled] would post to %s: %s", self.channel, text)
            return None
        try:
            self.resolved_channel_id = self._resolve_channel_id()
        except Exception as exc:                  # noqa: BLE001
            log.warning("Slack channel resolution failed for %s: %s", self.channel, exc)
            self.enabled = False
            return None

        # Send via slk so it works for both channel ids and user ids.
        try:
            proc = subprocess.run(
                ["slk", "send", self.channel, text],
                capture_output=True, text=True, timeout=SEND_TIMEOUT_S,
            )
        except subprocess.TimeoutExpired:
            log.warning("slk send to %s timed out after %.0fs; disabling notifier.",
                        self.channel, SEND_TIMEOUT_S)
            self.enabled = False
            return None
        if proc.returncode != 0:
            log.warning("slk send failed (%s): %s", proc.returncode, proc.stderr.strip())
            self.enabled = False
            return None

        # slk send doesn't reliably print the ts; read it back.
        ts = self._read_latest_ts()
        if not ts:
            log.warning("Could not read back parent ts for %s; further replies will be flat.",
                        self.channel)
        self.thread_ts = ts
        return ts

    # -------------------------------------------------------------------- post
    def post(self, text: str) -> None:
        """Post a threaded reply (falls back to a flat post if no thread_ts)."""
        if not self.enabled:
            return
        if not self._has_slk:
            log.info("[slack:disabled] reply to %s/%s: %s",
                     self.channel, self.thread_ts, text)
            return
        if not self.thread_ts or not self.resolved_channel_id or not self._has_node:
            # Best-effort flat send if we lost the thread.
            try:
                subprocess.run(["slk", "send", self.channel, text],
                               capture_output=True, text=True, timeout=SEND_TIMEOUT_S)
            except subprocess.TimeoutExpired:
                log.warning("slk send (flat) to %s timed out; disabling.", self.channel)
                self.enabled = False
            return
        self._slack_api("chat.postMessage", {
            "channel": self.resolved_channel_id,
            "thread_ts": self.thread_ts,
            "text": text,
            "unfurl_links": False,
        })

    # ------------------------------------------------------------------ finish
    def finish(self, text: str) -> None:
        self.post(text)

    # ---------------------------------------------- side-channel intake (poll)
    def poll_thread_messages(self, since_ts: Optional[str] = None) -> list[dict]:
        """Return new thread replies (newer than ``since_ts``) as dicts.

        Each item: ``{"ts": str, "user": str, "text": str}``. The parent
        message itself is excluded, and bot-authored messages (likely our
        own acks) are filtered when Slack reports ``bot_id`` on them.

        Returns ``[]`` if the notifier is disabled, has no thread, lacks
        ``node``, or the API call fails. Slack failures must never block
        the supervisor.
        """
        if not self.enabled or not self.thread_ts or not self.resolved_channel_id:
            return []
        if not self._has_node:
            return []
        resp = self._slack_api("conversations.replies", {
            "channel": self.resolved_channel_id,
            "ts": self.thread_ts,
            "oldest": since_ts or self.thread_ts,
            "inclusive": False,
            "limit": 100,
        })
        if not resp or not resp.get("ok"):
            return []
        out: list[dict] = []
        for msg in resp.get("messages", []) or []:
            ts = msg.get("ts")
            if not ts or ts == self.thread_ts:
                continue
            if since_ts and ts <= since_ts:
                continue
            if msg.get("bot_id"):                     # skip our own bot replies
                continue
            out.append({
                "ts": ts,
                "user": msg.get("user", ""),
                "text": msg.get("text", "") or "",
            })
        return out

    # -------------------------------------------- convenience role formatters
    def post_role_result(self, role: str, status: str, summary: str,
                         pause_reason: Optional[str] = None) -> None:
        icon = STATUS_ICON.get(status, ":grey_question:")
        lines = [f"{icon} *{role}* - `{status}`"]
        if summary:
            lines.append(f"> {summary[:300]}")
        if pause_reason:
            lines.append(f":pushpin: PAUSE: {pause_reason}")
        self.post("\n".join(lines))

    def post_start_banner(self, mode: str, auth_mode: str, role_count: int) -> Optional[str]:
        head = ":rocket: *Started*"
        if self.label:
            head += f" - `{self.label}`"
        body = f"mode=`{mode}`  auth=`{auth_mode}`  roles=`{role_count}`"
        return self.start(f"{head}\n{body}\nThread :arrow_down: for per-role status.")

    def post_finish_banner(self, overall_status: str, role_count: int,
                           pause_count: int, elapsed_s: float) -> None:
        icon = STATUS_ICON.get(overall_status, ":grey_question:")
        label = f" `{self.label}`" if self.label else ""
        text = (f"{icon} *Finished*{label} - overall=`{overall_status}` "
                f"({role_count} roles, {pause_count} pause(s), {elapsed_s:.1f}s)")
        self.finish(text)

    # ----------------------------------------------------------- internals
    def _resolve_channel_id(self) -> str:
        """Return the channel id usable by chat.postMessage (opens DM for U...)."""
        ch = self.channel.strip()
        if ch.startswith("U"):
            if not self._has_node:
                raise RuntimeError("node required to open DM for user id")
            resp = self._slack_api("conversations.open", {"users": ch})
            cid = ((resp or {}).get("channel") or {}).get("id")
            if not cid:
                raise RuntimeError(f"conversations.open returned no channel id: {resp}")
            return cid
        if ch.startswith(("C", "D", "G")):
            return ch
        # Name like 'arr-analytics' - let chat.postMessage resolve it.
        return ch

    def _read_latest_ts(self, attempts: int = 4, delay_s: float = 0.4) -> Optional[str]:
        """Re-read the last message in the channel/DM to get its ts."""
        for _ in range(attempts):
            try:
                proc = subprocess.run(
                    ["slk", "read", self.channel, "1", "--ts"],
                    capture_output=True, text=True, timeout=READ_TIMEOUT_S,
                )
            except subprocess.TimeoutExpired:
                log.warning("slk read of %s timed out; abandoning thread ts.", self.channel)
                return None
            if proc.returncode == 0:
                ts = _parse_first_ts(proc.stdout)
                if ts:
                    return ts
            time.sleep(delay_s)
        return None

    def _slack_api(self, method: str, payload: dict) -> Optional[dict]:
        if not self._has_node:
            log.info("[slack:no-node] would call %s(%s)", method, payload)
            return None
        snippet = (
            f"import('{SLKCLI_API_PATH}').then(({{ slackApi }}) =>"
            f" slackApi('{method}', {json.dumps(payload)})"
            f"  .then(r => process.stdout.write(JSON.stringify(r)))"
            f"  .catch(e => {{ process.stderr.write(String(e)); process.exit(1); }}));"
        )
        try:
            proc = subprocess.run(
                ["node", "-e", snippet], capture_output=True, text=True, timeout=API_TIMEOUT_S,
            )
        except subprocess.TimeoutExpired:
            log.warning("slackApi(%s) timed out after %.0fs", method, API_TIMEOUT_S)
            return None
        if proc.returncode != 0:
            log.warning("slackApi(%s) failed: %s", method, proc.stderr.strip()[:200])
            return None
        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError:
            return None


# slk read --ts prints "<ts>  <author>: <text>". Be liberal in what we accept.
def _parse_first_ts(stdout: str) -> Optional[str]:
    import re
    m = re.search(r"\b(\d{10}\.\d{3,6})\b", stdout)
    return m.group(1) if m else None
