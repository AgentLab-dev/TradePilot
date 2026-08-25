"""Continuous learning ledger for the supervisor + all sub-agents.

Each sub-agent (and the supervisor itself) accumulates *lessons* across runs:
small, actionable takeaways that should change behaviour next time. Lessons
are stored as JSONL under ``agents/arr_quarter_close/data/lessons/<role>.jsonl``
(one file per role + ``_global.jsonl`` for cross-role lessons + ``_stable.jsonl``
for lessons that have re-occurred enough times to be promoted to permanent
guardrails).

Why JSONL:
* Append-only -> no read/write races between concurrent sub-agents.
* Easy to ``tail -f`` / ``rg`` / diff in PRs.
* Survives partial writes (worst case: lose the trailing line).

Design rules:
* Sub-agents NEVER write the file directly - they go through ``LessonRecorder``
  so dedupe, timestamping, and id hashing stay consistent.
* Sub-agents NEVER read it directly either - they call ``recorder.load_for(role)``
  which returns at most ``max_lessons`` rows sorted by relevance
  (stable -> high-occurrence -> recent).
* No agent self-references inside the ``lesson`` text - see
  ``.cursor/rules/no-agent-signatures.mdc``.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional


# ---------------------------------------------------------------------------
# Storage location
# ---------------------------------------------------------------------------

DEFAULT_LESSONS_DIR_ENV = "FQC_ARR_LESSONS_DIR"


def default_lessons_dir(project_dir: Path) -> Path:
    """Resolve the lessons directory; env override wins."""
    override = os.environ.get(DEFAULT_LESSONS_DIR_ENV, "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return (Path(project_dir) / "agents" / "arr_quarter_close" / "data" / "lessons").resolve()


GLOBAL_ROLE = "_global"
STABLE_ROLE = "_stable"
REFLECTION_LOG = "_reflection_log"
PROMOTE_AT_OCCURRENCE = 3
ARCHIVE_AFTER_DAYS = 90

# Categories sub-agents may record. Free-form strings are accepted but the
# daily-reflection sub-agent uses these for its own bucketing.
KNOWN_CATEGORIES: tuple[str, ...] = (
    "failure",          # something the agent did wrong (next time: don't)
    "ambiguity",        # input was unclear; clarifier or analyser should ask
    "optimization",    # a faster / cleaner / cheaper path was found
    "correction",       # the user fixed something the agent emitted
    "validation_gap",  # a check that should have caught a real bug
    "user_preference", # a personal preference (e.g. "no signatures")
    "edge_case",        # a rare data shape worth remembering
    "tooling",          # MCP/CLI gotcha (e.g. "slk search hangs after N queries")
    "best_practice",   # codify a pattern that worked well
)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Lesson:
    """One actionable takeaway.

    The ``id`` is a stable hash of ``role + lesson`` so dedupe across runs
    works without name-spacing. ``occurrence_count`` is bumped on dedupe.
    """

    id: str
    role: str
    category: str
    lesson: str
    evidence: str = ""
    tags: list[str] = field(default_factory=list)
    confidence: str = "medium"          # low | medium | high
    occurrence_count: int = 1
    status: str = "active"              # active | promoted | deprecated
    source_ticket: Optional[str] = None
    source_run_ts: str = ""
    first_seen: str = ""
    last_seen: str = ""

    def as_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Lesson":
        # Tolerate extra fields from future versions.
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

    @staticmethod
    def make_id(role: str, lesson: str) -> str:
        h = hashlib.sha1(f"{role.strip().lower()}::{lesson.strip().lower()}".encode("utf-8"))
        return h.hexdigest()[:12]


# ---------------------------------------------------------------------------
# Recorder
# ---------------------------------------------------------------------------

class LessonRecorder:
    """Thread-safe append + dedupe for the lessons JSONL store.

    One instance per supervisor run. Sub-agents call ``record(role, ...)``
    during their run; ``load_for(role)`` returns the curated set to inject
    back into the next plan/prompt.
    """

    def __init__(self, lessons_dir: Path) -> None:
        self.dir = Path(lessons_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        # in-process cache of (role -> {id -> Lesson}) so dedupe across one
        # supervisor run doesn't hit disk N times.
        self._cache: dict[str, dict[str, Lesson]] = {}

    # ---------------------------------------------------------------- write
    def record(
        self,
        role: str,
        lesson: str,
        *,
        category: str = "best_practice",
        evidence: str = "",
        tags: Optional[Iterable[str]] = None,
        confidence: str = "medium",
        source_ticket: Optional[str] = None,
    ) -> Optional[Lesson]:
        """Append a new lesson (or bump the occurrence_count if seen before).

        Returns the Lesson written, or None if the lesson string is empty.
        """
        text = (lesson or "").strip()
        if not text:
            return None
        role = (role or GLOBAL_ROLE).strip()
        lid = Lesson.make_id(role, text)
        now = _now_iso()
        existing = self._load_index(role).get(lid)
        if existing:
            existing.occurrence_count += 1
            existing.last_seen = now
            # bump confidence one tier on each repeat, max=high
            existing.confidence = _bump_confidence(existing.confidence)
            # auto-promote on the threshold
            if (
                existing.occurrence_count >= PROMOTE_AT_OCCURRENCE
                and existing.status == "active"
            ):
                existing.status = "promoted"
                self._append(STABLE_ROLE, existing)
            self._rewrite(role)
            return existing
        lesson_obj = Lesson(
            id=lid,
            role=role,
            category=(category if category in KNOWN_CATEGORIES else "best_practice"),
            lesson=text,
            evidence=evidence.strip(),
            tags=sorted({t.strip() for t in (tags or []) if t and t.strip()}),
            confidence=confidence if confidence in {"low", "medium", "high"} else "medium",
            occurrence_count=1,
            status="active",
            source_ticket=source_ticket,
            source_run_ts=now,
            first_seen=now,
            last_seen=now,
        )
        with self._lock:
            self._cache.setdefault(role, {})[lid] = lesson_obj
        self._append(role, lesson_obj)
        return lesson_obj

    def log_reflection(
        self,
        *,
        lessons_added: int,
        lessons_promoted: int,
        lessons_archived: int,
        notes: str = "",
    ) -> None:
        """Append a one-line summary of a daily-reflection pass."""
        entry = {
            "ts": _now_iso(),
            "lessons_added": lessons_added,
            "lessons_promoted": lessons_promoted,
            "lessons_archived": lessons_archived,
            "notes": notes,
        }
        path = self._path(REFLECTION_LOG)
        with self._lock:
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # ----------------------------------------------------------------- read
    def load_for(
        self,
        role: str,
        *,
        max_lessons: int = 10,
        include_global: bool = True,
        include_stable: bool = True,
        min_confidence: str = "low",
    ) -> list[Lesson]:
        """Return up to ``max_lessons`` lessons relevant to ``role``.

        Ordering:
          1. Stable (promoted) lessons matching role or global.
          2. Role-specific active lessons by occurrence_count desc, then last_seen desc.
          3. Global active lessons by occurrence_count desc, then last_seen desc.
        """
        conf_rank = {"low": 0, "medium": 1, "high": 2}
        min_rank = conf_rank.get(min_confidence, 0)

        pool: list[Lesson] = []
        if include_stable:
            for l in self._load_role(STABLE_ROLE).values():
                if l.role == role or l.role == GLOBAL_ROLE:
                    pool.append(l)
        for l in self._load_role(role).values():
            if l.status != "deprecated":
                pool.append(l)
        if include_global:
            for l in self._load_role(GLOBAL_ROLE).values():
                if l.status != "deprecated":
                    pool.append(l)

        # de-dup by id (stable lessons may also live in role file)
        seen: dict[str, Lesson] = {}
        for l in pool:
            if conf_rank.get(l.confidence, 1) < min_rank:
                continue
            cur = seen.get(l.id)
            if not cur or l.occurrence_count > cur.occurrence_count:
                seen[l.id] = l

        def sort_key(l: Lesson) -> tuple:
            status_rank = 0 if l.status == "promoted" else 1
            return (status_rank, -l.occurrence_count, -_iso_epoch(l.last_seen))

        return sorted(seen.values(), key=sort_key)[:max_lessons]

    def all_lessons(self) -> dict[str, list[Lesson]]:
        """Return every lesson grouped by role. Useful for --show-lessons."""
        out: dict[str, list[Lesson]] = {}
        for path in sorted(self.dir.glob("*.jsonl")):
            role = path.stem
            if role == REFLECTION_LOG:
                continue
            out[role] = list(self._load_role(role).values())
        return out

    def reflection_log(self, *, last_n: int = 30) -> list[dict]:
        path = self._path(REFLECTION_LOG)
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as f:
            rows = [json.loads(ln) for ln in f if ln.strip()]
        return rows[-last_n:]

    def reflected_today(self) -> bool:
        rows = self.reflection_log(last_n=10)
        if not rows:
            return False
        today = datetime.now(timezone.utc).date().isoformat()
        return any(r.get("ts", "")[:10] == today for r in rows)

    # --------------------------------------------------------------- helpers
    def _path(self, role: str) -> Path:
        safe = role.replace("/", "_")
        return self.dir / f"{safe}.jsonl"

    def _load_index(self, role: str) -> dict[str, Lesson]:
        with self._lock:
            cached = self._cache.get(role)
        if cached is not None:
            return cached
        loaded = self._load_role(role)
        with self._lock:
            self._cache[role] = loaded
        return loaded

    def _load_role(self, role: str) -> dict[str, Lesson]:
        path = self._path(role)
        if not path.exists():
            return {}
        out: dict[str, Lesson] = {}
        with path.open("r", encoding="utf-8") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    out[json.loads(raw)["id"]] = Lesson.from_dict(json.loads(raw))
                except (json.JSONDecodeError, KeyError, TypeError):
                    # bad line; skip but don't poison the whole file
                    continue
        return out

    def _append(self, role: str, lesson: Lesson) -> None:
        path = self._path(role)
        with self._lock:
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(lesson.as_dict(), ensure_ascii=False) + "\n")

    def _rewrite(self, role: str) -> None:
        """Rewrite a role file from its cached index (used after dedupe bumps).

        Writes to a per-process-unique temp file, then atomically ``os.replace``s
        it over the target. The unique suffix is what prevents the recurring
        cross-process crash: ``self._lock`` only serialises threads within one
        process, but the launchd daily-reflection job and an interactive run are
        *separate processes*. With a deterministic ``<role>.jsonl.tmp`` name they
        raced on the same temp file — one process's ``replace`` consumed the temp
        the other was about to replace, surfacing as
        ``FileNotFoundError: <role>.jsonl.tmp -> <role>.jsonl``.
        """
        path = self._path(role)
        with self._lock:
            idx = self._cache.get(role, {})
            fd, tmp_name = tempfile.mkstemp(
                prefix=f"{path.name}.", suffix=f".tmp.{os.getpid()}", dir=str(self.dir)
            )
            tmp = Path(tmp_name)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    for l in idx.values():
                        f.write(json.dumps(l.as_dict(), ensure_ascii=False) + "\n")
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp, path)
            except BaseException:
                # Never leave a partial temp file behind if the write/replace fails.
                try:
                    tmp.unlink()
                except FileNotFoundError:
                    pass
                raise


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def format_lessons_for_prompt(lessons: list[Lesson], heading: str = "Lessons learned") -> str:
    """Render the lessons as a Markdown bullet list suitable for an LLM prompt.

    Returns an empty string when ``lessons`` is empty so the caller can
    cleanly omit the section without producing a stray heading.
    """
    if not lessons:
        return ""
    out = [f"## {heading} (apply these)"]
    for l in lessons:
        tag = f" [{', '.join(l.tags)}]" if l.tags else ""
        prefix = "(promoted) " if l.status == "promoted" else ""
        out.append(f"- {prefix}**{l.category}**: {l.lesson}{tag}")
    return "\n".join(out) + "\n"


def render_lessons_table(lessons_by_role: dict[str, list[Lesson]]) -> str:
    """Render a plain-text table for the CLI --show-lessons output."""
    if not lessons_by_role:
        return "(no lessons captured yet)"
    lines = []
    for role, lessons in sorted(lessons_by_role.items()):
        if not lessons:
            continue
        lines.append(f"\n=== {role} ({len(lessons)}) ===")
        for l in sorted(lessons, key=lambda x: (-x.occurrence_count, x.last_seen), reverse=False):
            tag = f"  [{', '.join(l.tags)}]" if l.tags else ""
            ticket = f" <{l.source_ticket}>" if l.source_ticket else ""
            lines.append(
                f"  - [{l.status} x{l.occurrence_count} {l.confidence}] {l.category}: "
                f"{l.lesson}{ticket}{tag}"
            )
    return "\n".join(lines).strip() or "(no lessons captured yet)"


# Module-level cached singleton (one per process).
_RECORDER: Optional[LessonRecorder] = None
_RECORDER_DIR: Optional[Path] = None


def get_recorder(project_dir: Path) -> LessonRecorder:
    """Return a process-wide singleton recorder for the given project dir."""
    global _RECORDER, _RECORDER_DIR
    target_dir = default_lessons_dir(project_dir)
    if _RECORDER is None or _RECORDER_DIR != target_dir:
        _RECORDER = LessonRecorder(target_dir)
        _RECORDER_DIR = target_dir
    return _RECORDER


def get_cached_recorder() -> Optional[LessonRecorder]:
    """Return the singleton recorder if the supervisor has initialised it.

    Sub-agents call this to inject lessons into their prompts without having
    to thread ``project_dir`` through every contract. Returns ``None`` when
    the supervisor hasn't called ``get_recorder(project_dir)`` yet (which
    means the sub-agent is running standalone in a test); callers should
    treat ``None`` as "no lessons available" and proceed unchanged.
    """
    return _RECORDER


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _bump_confidence(cur: str) -> str:
    order = ("low", "medium", "high")
    try:
        i = order.index(cur)
    except ValueError:
        return "medium"
    return order[min(i + 1, len(order) - 1)]


def _iso_epoch(ts: str) -> float:
    """Parse an ISO-8601 timestamp to a unix epoch float. Missing/bad -> 0.0."""
    if not ts:
        return 0.0
    try:
        return datetime.fromisoformat(ts).timestamp()
    except (ValueError, TypeError):
        return 0.0
