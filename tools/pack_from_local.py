#!/usr/bin/env python3
"""Pack ssr-st + arr-analyst skills, commands, plans, and last-100-days chats into TradePilot."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import datetime
from pathlib import Path

ROOT = Path("/Users/koteswararao.venkata/Documents/Cursor/TradePilot")
HOME = Path.home()
CURSOR = HOME / "Documents" / "Cursor"
DOCS = CURSOR / "Documents"
CLAUDE_SKILLS = HOME / ".claude" / "skills"
CURSOR_SKILLS = HOME / ".cursor" / "skills"
CURSOR_RULES = HOME / ".cursor" / "rules"
GLOBAL_RULES = CURSOR / ".cursor" / "rules"
PROJECTS = HOME / ".cursor" / "projects"
CUTOFF = datetime.datetime(2026, 5, 17)  # last 100 days from 2026-08-25

SSR_SKILLS = [
    "trading-continuous-learning",
    "news-portals",
    "ibd-wsj-capture",
    "agentic-whale-short-term-trading",
    "evening-wrap-nextday-prep",
    "catalyst-overnight-plan",
    "three-good-put-credit",
    "stnow-360-check",
    "health-check",
    "tomorrow-market-predictor",
    "trade-entry-exit-pricing",
]

ARR_SKILLS = [
    "office-politics-navigation",
    "political-resilience-mentor",
    "mentor-mode",
    "humanize-writing",
    "emotional-writing",
    "fqc-arr-supervisor",
    "jira-intake",
    "requirements-analyzer",
    "code-data-validator",
    "clarifier",
    "implementer",
    "test-runner",
    "pr-author",
    "ci-monitor",
    "cd-monitor",
    "qa-handoff",
    "debugger",
    "quarter-close-runner",
    "finance-functional-analytics",
    "finance-functional-architect",
    "finance-bsa-data-analyst",
    "enterprise-metrics-finance-architect",
    "enterprise-data-architect",
    "salesforce-bsa-agreements-contracts",
    "salesforce-bsa-finance-analyst",
    "salesforce-bsa-close",
    "sigma-computing-analyst",
    "dbt-architect",
    "dbt-model-debugger",
    "dbt-platform-architect",
    "dbt-system-admin",
    "data-analytics-architect",
    "analytics-engineering-architect",
    "snowflake-architect",
    "snowflake-platform-admin",
    "mcp-connections",
    "professional-writing",
    "cross-check-before-answer",
    "autonomous-execution",
    "agentic-architecture-patterns",
    "agentic-architecture-validator",
    "twelve-factor-agents",
    "multi-agent-supervisor-pattern",
]

SHARED_SKILLS = ["professional-writing", "cross-check-before-answer"]

SKIP_DIR_NAMES = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".scratch",
}

REDACT_SUBS = [
    (re.compile(r"gho_[A-Za-z0-9_]+"), "gho_[REDACTED]"),
    (re.compile(r"ghp_[A-Za-z0-9_]+"), "ghp_[REDACTED]"),
    (re.compile(r"github_pat_[A-Za-z0-9_]+"), "github_pat_[REDACTED]"),
    (re.compile(r"sk-[A-Za-z0-9_-]+"), "sk-[REDACTED]"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9-]+"), "xox[REDACTED]"),
    (re.compile(r"(?i)(JIRA_API_TOKEN|JIRA_TOKEN|API_TOKEN|SNOWFLAKE_PASSWORD|RH_TOKEN)\s*[=:]\s*\S+"), r"\1=[REDACTED]"),
    (re.compile(r"\b789725611\b"), "••••5611"),
    (re.compile(r"\b407271451\b"), "••••1451"),
    (re.compile(r"[A-Za-z0-9._%+-]+@workday\.com"), "[REDACTED_EMAIL]"),
    (re.compile(r"[A-Za-z0-9._%+-]+@solutionlabs\.ai"), "[REDACTED_EMAIL]"),
]


def sanitize(text: str) -> str:
    if not text:
        return text
    for pat, repl in REDACT_SUBS:
        text = pat.sub(repl, text)
    return text


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIR_NAMES for part in path.parts)


def copy_tree(src: Path, dst: Path, text_sanitize: bool = True) -> int:
    if not src.exists():
        return 0
    n = 0
    dst.mkdir(parents=True, exist_ok=True)
    if src.is_file():
        copy_file(src, dst if dst.suffix else dst / src.name, text_sanitize)
        return 1
    for p in src.rglob("*"):
        if should_skip(p) or p.is_dir():
            continue
        rel = p.relative_to(src)
        out = dst / rel
        copy_file(p, out, text_sanitize)
        n += 1
    return n


def copy_file(src: Path, dst: Path, text_sanitize: bool) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".xlsx", ".pptx", ".zip"}:
        shutil.copy2(src, dst)
        return
    try:
        raw = src.read_bytes()
    except OSError:
        return
    # skip obviously-binary
    if b"\0" in raw[:2048]:
        shutil.copy2(src, dst)
        return
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        shutil.copy2(src, dst)
        return
    if text_sanitize:
        text = sanitize(text)
    dst.write_text(text, encoding="utf-8")


def copy_skill(name: str, dest_root: Path) -> None:
    for base in (CLAUDE_SKILLS, CURSOR_SKILLS):
        src = base / name
        if src.exists():
            copy_tree(src, dest_root / name)
            return


def extract_text_blocks(obj) -> list[str]:
    texts = []
    if obj is None:
        return texts
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, list):
        for item in obj:
            texts.extend(extract_text_blocks(item))
        return texts
    if isinstance(obj, dict):
        t = obj.get("type")
        if t in {"tool_use", "tool_result", "function_call", "function_result"}:
            return []
        if "text" in obj and isinstance(obj["text"], str):
            texts.append(obj["text"])
        for k in ("content", "message", "parts"):
            if k in obj:
                texts.extend(extract_text_blocks(obj[k]))
    return texts


def first_user_title(texts: list[str]) -> str:
    blob = " ".join(texts)
    m = re.search(r"<user_query>\s*(.*?)\s*</user_query>", blob, re.S)
    s = (m.group(1) if m else blob).strip()
    s = re.sub(r"<timestamp>.*?</timestamp>", "", s, flags=re.S).strip()
    s = re.sub(r"\s+", " ", s)
    return (s[:80] + "…") if len(s) > 80 else (s or "untitled")


def classify_project(proj: str) -> str:
    p = proj.lower()
    if "ssr-analyst" in p:
        return "ssr-st"
    if "eda-dbt-em" in p or "fqc" in p or "arr" in p:
        return "arr-analyst"
    return "other"


def extract_transcripts() -> dict:
    index = []
    out_root = ROOT / "discussions"
    if not PROJECTS.exists():
        return {"chats": 0, "files": []}
    jsonls = list(PROJECTS.rglob("*.jsonl"))
    chats = 0
    for path in jsonls:
        if "agent-transcripts" not in str(path):
            continue
        mtime = datetime.datetime.fromtimestamp(path.stat().st_mtime)
        if mtime < CUTOFF:
            continue
        proj = path.parts[path.parts.index("projects") + 1] if "projects" in path.parts else "unknown"
        agent = classify_project(proj)
        turns = []
        title = None
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                role = rec.get("role") or rec.get("type") or "unknown"
                msg = rec.get("message") if isinstance(rec.get("message"), dict) else rec
                blocks = extract_text_blocks(msg.get("content") if isinstance(msg, dict) else rec.get("content"))
                text = sanitize("\n".join(blocks).strip())
                if not text:
                    continue
                if role == "user" and title is None:
                    title = first_user_title([text])
                # keep discussion text; drop huge dumps
                if len(text) > 20000:
                    text = text[:20000] + "\n\n…[truncated at 20k chars]"
                turns.append((role, text))
        if not turns:
            continue
        chats += 1
        slug = path.parent.name
        day = mtime.strftime("%Y-%m-%d")
        digest = hashlib.sha1(str(path).encode()).hexdigest()[:8]
        fname = f"{day}_{slug}_{digest}.md"
        dest_dir = out_root / agent
        dest_dir.mkdir(parents=True, exist_ok=True)
        body = [
            f"# Chat — {title or 'untitled'}",
            "",
            f"- **Agent bucket:** `{agent}`",
            f"- **Cursor project:** `{proj}`",
            f"- **Transcript id:** `{path.parent.name}`",
            f"- **Last updated:** {mtime.isoformat(timespec='seconds')}",
            f"- **Turns kept:** {len(turns)} (user/assistant text only; tool payloads omitted)",
            "",
            "---",
            "",
        ]
        for i, (role, text) in enumerate(turns, 1):
            body.append(f"## {i}. {role}")
            body.append("")
            body.append(text)
            body.append("")
        (dest_dir / fname).write_text("\n".join(body), encoding="utf-8")
        index.append(
            {
                "date": day,
                "agent": agent,
                "title": title or "untitled",
                "file": str(Path("discussions") / agent / fname),
                "project": proj,
                "turns": len(turns),
                "mtime": mtime.isoformat(timespec="seconds"),
            }
        )
    index.sort(key=lambda r: r["mtime"], reverse=True)
    return {"chats": chats, "index": index}


def write_commands() -> None:
    d = ROOT / "agents" / "ssr-st" / "commands"
    d.mkdir(parents=True, exist_ok=True)
    files = {
        "FULLCHECK.md": """# Command: FULL CHECK (fullcheck)

Trigger: `FULL CHECK`, `fullcheck`, `full check`.

The 12-step battery. Read-only by default — surfaces tickets, waits for go.

1. Tape / macro (SPY QQQ SMH VXX 10Y)
2. Cross-sector GICS ETF gate
3. Book health (cushion, delta, GTC, abort)
4. Health Check 4-model composite
5. Event gate + T+0/T+1 catalyst cards (required)
6. STKK + STNOW + Three Good on finalists
7. Whale Watch (vol vs OI)
8. SelfIDB50 momentum discovery
9. WSJ / MarketWatch + investor-day search
10. Direction × IV routing
11. Backtest new structures
12. Ranked plan 🟢 / 🟡 / 🔴 + write catalyst_cards.md, next_day_prep.md, momentum_watchlist.md

Skill: `agents/ssr-st/skills/trading-continuous-learning/SKILL.md`
Loop: `agents/ssr-st/workspace/strategy_battery_loop.sh`
""",
        "HEALTHCHECK.md": """# Command: Health Check

Trigger: `Health Check` (optionally with tickers).

4-model composite: STKK + STNOW + Three Good + Whale → one VERDICT per name.

```
python3 agents/ssr-st/workspace/Documents/market_data/health_check.py TICKER [TICKER ...] [--to YYYY-MM-DD] [--live SYM=PX]
```

Skill: `agents/ssr-st/skills/health-check/SKILL.md`
Spec: `agents/ssr-st/workspace/Documents/health_check_algorithm.md`
""",
        "STNOW.md": """# Command: STNOW

Trigger: `STNOW` or `STNOW TICKER`.

360° pre-trade model. Step 0 is intake (account / entry / intent) — do not skip.

Skill: `agents/ssr-st/skills/stnow-360-check/SKILL.md`
Spec: `agents/ssr-st/workspace/Documents/stnow_algorithm.md`
""",
        "STKK.md": """# Command: STKK

Chart / technicals: regime (UP/DOWN/RANGE), RSI, R:R, support.

```
python3 agents/ssr-st/workspace/Documents/market_data/stkk_from_cache.py
```

Skills: `trade-entry-exit-pricing`
Specs: `trade_entry_exit_algorithms.md`
""",
        "THREE_GOOD.md": """# Command: Three Good

Trigger: `Three Good` / `THREE GOOD` only (do not auto-apply).

Bull put credit spread below 10-week weekly support. IV ≥ ~50%, event gate, credit ≥ 25–33% of width.

Skill: `agents/ssr-st/skills/three-good-put-credit/SKILL.md`
Spec: `agents/ssr-st/workspace/Documents/three_good_put_credit_strategy.md`
""",
        "SELFIDB50.md": """# Command: SelfIDB50

Momentum-discovery slice inside FULL CHECK. FFTY holdings + rs_screen.py + anti-chase.

See `agents/ssr-st/workspace/Documents/momentum_watchlist.md`
""",
        "EVENING_WRAP.md": """# Command: Evening wrap / next-day prep

After-hours close (~6 PM PT). No orders. Writes `next_day_prep.md` + `catalyst_cards.md`.

Skill: `agents/ssr-st/skills/evening-wrap-nextday-prep/SKILL.md`
Loop: `agents/ssr-st/workspace/evening_wrap_loop.sh`
""",
        "DAILY.md": """# Command: daily.py (session pipeline)

```
python3 Documents/market_data/daily.py
python3 Documents/market_data/daily.py --quick
python3 Documents/market_data/daily.py SYM …
```

Refresh + macro + MANGOS + earnings gate + Health Check.
""",
        "WHALE.md": """# Command: Whale Watch

Unusual options activity, volume vs OI, IV/skew.

```
python3 Documents/market_data/whale_check.py
```

Spec: `whale_check_algorithm.md`
""",
    }
    for name, body in files.items():
        (d / name).write_text(body, encoding="utf-8")

    arr = ROOT / "agents" / "arr-analyst" / "commands"
    arr.mkdir(parents=True, exist_ok=True)
    (arr / "FQC_ARR.md").write_text(
        """# Command: FQC-ARR / run ARR ticket

Drive an EDAEM Jira ticket through the 10-role DAG:

1. jira-intake
2. requirements-analyzer
3. code-data-validator
4. clarifier *(gate)*
5. implementer
6. test-runner
7. pr-author *(gate)*
8. ci-monitor
9. cd-monitor
10. qa-handoff *(gate)*

Supervisor skill: `agents/arr-analyst/skills/fqc-arr-supervisor/SKILL.md`
Workspace commands copied from eda-dbt-em `.cursor/commands/`.
""",
        encoding="utf-8",
    )


def write_context_md(meta: dict) -> None:
    idx = meta.get("index") or []
    ssr = [r for r in idx if r["agent"] == "ssr-st"]
    arr = [r for r in idx if r["agent"] == "arr-analyst"]
    other = [r for r in idx if r["agent"] == "other"]
    lines = [
        "# Last 100 days of context",
        "",
        f"_Packed {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} PT. Window: {CUTOFF.date()} → 2026-08-25 (100 days)._",
        "",
        "This file is the **index**. Full chat text (user + assistant, tools stripped, secrets redacted) lives under `discussions/`.",
        "",
        "## Agents in this repo",
        "",
        "| Agent | What it is | Home in this repo |",
        "|---|---|---|",
        "| **ssr-st** | SSR-analyst short-term / options discussion agent (FULLCHECK, Health Check, STNOW, STKK, Three Good, whale, evening wrap) | `agents/ssr-st/` |",
        "| **arr-analyst** | FQC-ARR / eda-dbt-em finance ARR quarter-close agent | `agents/arr-analyst/` |",
        "",
        "## Counts",
        "",
        f"- Chats extracted: **{meta.get('chats', 0)}**",
        f"- ssr-st chats: **{len(ssr)}**",
        f"- arr-analyst chats: **{len(arr)}**",
        f"- other chats: **{len(other)}**",
        "",
        "## Named operations (ssr-st)",
        "",
        "- `FULL CHECK` / fullcheck — 12-step battery (`agents/ssr-st/commands/FULLCHECK.md`)",
        "- `Health Check` — 4-model composite",
        "- `STNOW` — 360° pre-trade",
        "- `STKK` — chart / levels",
        "- `Three Good` — put credit spreads",
        "- `SelfIDB50` — momentum discovery",
        "- Evening wrap / next-day prep",
        "- Whale Watch",
        "- `daily.py` session pipeline",
        "- Loops: `strategy_battery_loop.sh`, `market_check_loop.sh`, `evening_wrap_loop.sh`",
        "",
        "## Named operations (arr-analyst)",
        "",
        "- FQC-ARR supervisor DAG (10 roles + debugger + quarter-close-runner)",
        "- `arr-quarter-close` workspace skill",
        "- Commands: inbox-action-items, fcq-arr-regression-test, product-hierarchy-recon-test",
        "",
        "## Chat index (newest first)",
        "",
        "| Date | Agent | Title | File | Turns |",
        "|---|---|---|---|---|",
    ]
    for r in idx:
        title = r["title"].replace("|", "/")
        lines.append(f"| {r['date']} | {r['agent']} | {title} | `{r['file']}` | {r['turns']} |")
    lines += [
        "",
        "## How this was built",
        "",
        "1. Copied live skills from `~/.claude/skills` and `~/.cursor/skills`.",
        "2. Copied `ssr-analyst` workspace (docs, scripts, loops, rules).",
        "3. Copied FQC-ARR Sana bundle, dist bundle, and eda-dbt-em `.cursor` agent files.",
        "4. Extracted Cursor `agent-transcripts` JSONL since 2026-05-17.",
        "5. Redacted tokens, Robinhood account ids, and work emails.",
        "",
        "Re-run: `python3 tools/pack_from_local.py`",
        "",
    ]
    (ROOT / "CONTEXT_LAST_100_DAYS.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    (ROOT / "agents" / "ssr-st" / "skills").mkdir(parents=True, exist_ok=True)
    (ROOT / "agents" / "arr-analyst" / "skills").mkdir(parents=True, exist_ok=True)

    for name in SSR_SKILLS:
        copy_skill(name, ROOT / "agents" / "ssr-st" / "skills")
    # workspace copies
    copy_tree(
        CURSOR / "ssr-analyst" / ".cursor" / "skills" / "catalyst-overnight-plan",
        ROOT / "agents" / "ssr-st" / "skills" / "catalyst-overnight-plan-workspace",
    )
    copy_tree(
        CURSOR / "ssr-analyst" / ".cursor" / "rules",
        ROOT / "agents" / "ssr-st" / "rules",
    )
    copy_tree(CURSOR / "ssr-analyst", ROOT / "agents" / "ssr-st" / "workspace")

    canvases = PROJECTS / "Users-koteswararao-venkata-Documents-Cursor-ssr-analyst" / "canvases"
    if canvases.exists():
        dest = ROOT / "agents" / "ssr-st" / "canvases"
        dest.mkdir(parents=True, exist_ok=True)
        for p in canvases.glob("*.tsx"):
            copy_file(p, dest / p.name, True)
        for p in canvases.glob("fullcheck*.md"):
            copy_file(p, dest / p.name, True)

    # fullcheck writeups
    fc = ROOT / "agents" / "ssr-st" / "plans"
    fc.mkdir(parents=True, exist_ok=True)
    if DOCS.exists():
        for p in DOCS.glob("fullcheck*.md"):
            copy_file(p, fc / p.name, True)
        copy_file(
            DOCS / "ssr_analyst_trading_agent_history.md",
            ROOT / "agents" / "ssr-st" / "plans" / "ssr_analyst_trading_agent_history.md",
            True,
        )

    # global trading-adjacent rules
    for src in (CURSOR_RULES, GLOBAL_RULES):
        if not src.exists():
            continue
        for p in src.glob("*.mdc"):
            if p.name.lower() in {
                "cross-check-before-answer.mdc",
                "professional-writing.mdc",
                "documents-output-folder.mdc",
            }:
                copy_file(p, ROOT / "shared" / "rules" / p.name, True)

    for name in ARR_SKILLS:
        copy_skill(name, ROOT / "agents" / "arr-analyst" / "skills")
    for name in SHARED_SKILLS:
        copy_skill(name, ROOT / "shared" / "skills")

    copy_tree(CURSOR / "fqc-arr-sana", ROOT / "agents" / "arr-analyst" / "fqc-arr-sana")
    copy_tree(CURSOR / "fqc-arr-dist", ROOT / "agents" / "arr-analyst" / "fqc-arr-dist")
    copy_tree(
        CURSOR / "eda-dbt-em" / ".cursor" / "skills",
        ROOT / "agents" / "arr-analyst" / "workspace-skills",
    )
    copy_tree(
        CURSOR / "eda-dbt-em" / ".cursor" / "commands",
        ROOT / "agents" / "arr-analyst" / "workspace-commands",
    )
    copy_tree(
        CURSOR / "eda-dbt-em" / ".cursor" / "rules",
        ROOT / "agents" / "arr-analyst" / "workspace-rules",
    )
    copy_tree(
        CURSOR / "eda-dbt-em" / ".cursor" / "automations",
        ROOT / "agents" / "arr-analyst" / "workspace-automations",
    )

    if DOCS.exists():
        plans = ROOT / "agents" / "arr-analyst" / "plans"
        plans.mkdir(parents=True, exist_ok=True)
        for p in DOCS.glob("fqc_arr*.md"):
            copy_file(p, plans / p.name, True)
        for name in (
            "eda_dbt_em_workspace_skills_index.md",
            "eda_agent_skills_v2_architecture_plan.md",
        ):
            src = DOCS / name
            if src.exists():
                copy_file(src, plans / name, True)

    write_commands()
    meta = extract_transcripts()
    write_context_md(meta)
    (ROOT / "discussions" / "INDEX.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "chats": meta.get("chats"), "ssr_skills": SSR_SKILLS, "arr_skills": ARR_SKILLS}, indent=2))


if __name__ == "__main__":
    main()
