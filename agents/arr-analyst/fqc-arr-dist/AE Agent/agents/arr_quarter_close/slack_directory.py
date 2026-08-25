"""Slack directory lookup for the fqc-arr supervisor + sub-agents.

Loads the JSON directory at ``agents/arr_quarter_close/data/slack_directory.json``
(written by ``data/_scrape_eda_channel.py``) and exposes a tiny lookup surface
so any sub-agent can resolve a friendly name / email to a Slack user id without
re-running the slk enumeration.

Coverage caveat: the directory only contains ACTIVE participants of the
#enterprise-data-and-analytics channel scraped via ``slk search`` (the full
channel roster cannot be enumerated on this enterprise workspace because
``conversations.members`` is blocked).

Usage:
    from agents.arr_quarter_close.slack_directory import SlackDirectory

    sd = SlackDirectory.load()
    uid = sd.resolve("jane.doe")          # -> "U07EAT736HG"
    uid = sd.resolve("[REDACTED_EMAIL]")
    uid = sd.resolve("U07EAT736HG")            # passthrough for already-ids

    # On the fly, when a sub-agent learns about a new id (e.g. parsed from
    # a webhook payload), persist it for next time:
    sd.add("U09XYZ123", name="alice.smith", email="[REDACTED_EMAIL]",
           channel="#enterprise-data-and-analytics")
    sd.save()
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

log = logging.getLogger(__name__)

DEFAULT_PATH = Path(__file__).resolve().parent / "data" / "slack_directory.json"

# Slack user-id format: U... (regular) or W... (legacy)
_ID_PREFIXES = ("U", "W")


@dataclass
class SlackUser:
    user_id: str
    name: str = ""
    email: Optional[str] = None
    channels: list[str] = field(default_factory=list)
    source: Optional[str] = None  # "mention" / "author" / "seed" / "manual"


@dataclass
class SlackDirectory:
    path: Path
    users: dict[str, SlackUser] = field(default_factory=dict)
    aliases: dict[str, str] = field(default_factory=dict)
    channels_meta: dict[str, dict] = field(default_factory=dict)
    version: int = 1
    updated_at: Optional[str] = None
    _dirty: bool = False

    # ------------------------------------------------------------------ load
    @classmethod
    def load(cls, path: Optional[Path | str] = None) -> "SlackDirectory":
        p = Path(path) if path else DEFAULT_PATH
        if not p.exists():
            log.warning("slack_directory not found at %s; returning empty directory.", p)
            return cls(path=p)
        try:
            doc = json.loads(p.read_text())
        except Exception as e:
            log.warning("slack_directory at %s is unreadable (%s); returning empty.", p, e)
            return cls(path=p)
        users = {
            uid: SlackUser(
                user_id=uid,
                name=u.get("name") or "",
                email=u.get("email"),
                channels=list(u.get("channels") or []),
                source=u.get("source"),
            )
            for uid, u in (doc.get("users") or {}).items()
        }
        return cls(
            path=p,
            users=users,
            aliases=dict(doc.get("aliases") or {}),
            channels_meta=dict(doc.get("channels") or {}),
            version=int(doc.get("version") or 1),
            updated_at=doc.get("updated_at"),
        )

    # --------------------------------------------------------------- resolve
    def resolve(self, query: str) -> Optional[str]:
        """Return a Slack user id for the given query, or None.

        Accepts:
            * raw ids (U... / W...) - returned as-is after format check
            * full names / handles (case-insensitive)
            * emails (case-insensitive)
            * single-word handle prefix (e.g. "jane" -> "jane.doe")
        """
        if not query:
            return None
        q = query.strip()
        if q.startswith(_ID_PREFIXES) and q[1:].isalnum() and q.isupper():
            return q if q in self.users or len(q) >= 9 else None
        ql = q.lower()
        if ql in self.aliases:
            return self.aliases[ql]
        # email-shaped lookup
        if "@" in ql:
            return self.aliases.get(ql)
        # bare first-name lookup ("jane" -> any handle starting with "jane.")
        for alias, uid in self.aliases.items():
            if alias.startswith(ql + "."):
                return uid
        return None

    def resolve_all(self, queries: Iterable[str]) -> dict[str, Optional[str]]:
        return {q: self.resolve(q) for q in queries}

    def user(self, uid: str) -> Optional[SlackUser]:
        return self.users.get(uid)

    # -------------------------------------------------------------- add/save
    def add(
        self,
        user_id: str,
        name: str = "",
        email: Optional[str] = None,
        channel: Optional[str] = None,
        source: str = "manual",
    ) -> SlackUser:
        if not user_id.startswith(_ID_PREFIXES):
            raise ValueError(f"user_id must start with U or W; got {user_id!r}")
        u = self.users.get(user_id)
        if not u:
            u = SlackUser(user_id=user_id, name=name, email=email, source=source)
            self.users[user_id] = u
        else:
            if name and not u.name:
                u.name = name
            if email and not u.email:
                u.email = email
        if channel and channel not in u.channels:
            u.channels.append(channel)
        # rebuild aliases for this user
        if u.name:
            self.aliases[u.name.lower()] = user_id
            first = u.name.split(".")[0].lower()
            if first:
                self.aliases.setdefault(first, user_id)
        if u.email:
            self.aliases[u.email.lower()] = user_id
        self._dirty = True
        return u

    def save(self) -> None:
        if not self._dirty:
            return
        doc = {
            "version": self.version,
            "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "channels": self.channels_meta,
            "users": {
                uid: {
                    "name": u.name,
                    "email": u.email,
                    "channels": sorted(u.channels),
                    "source": u.source,
                }
                for uid, u in sorted(self.users.items())
            },
            "aliases": dict(sorted(self.aliases.items())),
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(doc, indent=2, ensure_ascii=False))
        self._dirty = False

    # ------------------------------------------------------------- introspect
    def __len__(self) -> int:
        return len(self.users)

    def summary(self) -> str:
        return (
            f"SlackDirectory({len(self.users)} users, "
            f"{len(self.aliases)} aliases, "
            f"updated_at={self.updated_at}, path={self.path})"
        )


# Module-level cached singleton so multiple sub-agents share one read.
_singleton: Optional[SlackDirectory] = None


def get_directory(reload: bool = False) -> SlackDirectory:
    """Cached load. Pass ``reload=True`` to force a fresh read from disk."""
    global _singleton
    if reload or _singleton is None:
        _singleton = SlackDirectory.load()
    return _singleton


__all__ = ["SlackDirectory", "SlackUser", "get_directory", "DEFAULT_PATH"]
