#!/usr/bin/env python3
"""Earnings radar — Nasdaq calendar ∩ cached universe + ALWAYS watch names.

Not sufficient alone (Nasdaq omitted XE on 2026-08-13). Agent must UNION
Robinhood get_earnings_calendar + investor/analyst-day search and write
catalyst_cards.md (skill: catalyst-overnight-plan).

Pulls the Nasdaq earnings calendar for the next N days, intersects it with the
tickers in market_history.md plus ALWAYS, and writes ../earnings_radar.md tagging:
  - sell-gate     : no credit spread may expire AFTER the report (the AVGO rule)
  - directional   : pre-earnings debit / long candidate (the MU lesson)

Also dumps an unfiltered 0–1d Nasdaq ticker list so off-universe names still surface.

Run:  python3 fetch_earnings.py            # next 14 calendar days
      python3 fetch_earnings.py --days 21
Source: Nasdaq calendar API (same host as fetch_history.py).
"""
import json, os, re, sys, subprocess, datetime as dt, time

HERE = os.path.dirname(os.path.abspath(__file__))
MD_HIST = os.path.normpath(os.path.join(HERE, "..", "market_history.md"))
MD_OUT = os.path.normpath(os.path.join(HERE, "..", "earnings_radar.md"))
CURL_HDRS = [
    "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "-H", "Accept: application/json", "-H", "Accept-Language: en-US,en;q=0.9",
    "-H", "Origin: https://www.nasdaq.com", "-H", "Referer: https://www.nasdaq.com/",
]

# Names that must appear on the radar even if they are missing from market_history.md.
# Still not sufficient: Nasdaq itself omitted XE on 8/13 — agent must UNION Robinhood.
ALWAYS = {
    "XE", "SNDK", "WDC", "STX", "SMCI", "CRWV", "NEM", "HOOD", "MS", "MARA",
    "CRWD", "HPE", "DELL", "PANW", "OKTA", "AMAT", "NVDA", "MU", "ORCL", "NNE",
    "OKLO", "AMD", "AVGO", "TSM", "MRVL", "WDAY",
}

def universe():
    if not os.path.exists(MD_HIST):
        return set()
    txt = open(MD_HIST).read()
    return {m.group(1) for m in re.finditer(r"\n## ([A-Z0-9.]+)\n", txt)}

def earnings_on(date_iso):
    url = f"https://api.nasdaq.com/api/calendar/earnings?date={date_iso}"
    for attempt in range(3):
        try:
            raw = subprocess.run(["curl", "-s", "--max-time", "30", *CURL_HDRS, url],
                                 capture_output=True, text=True, timeout=40).stdout
            d = json.loads(raw)
            rows = (d.get("data") or {}).get("rows") or []
            out = {}
            for r in rows:
                sym = (r.get("symbol") or "").upper().strip()
                if sym:
                    out[sym] = r.get("time", "")
            return out
        except Exception:
            time.sleep(1.2 * (attempt + 1))
    return {}

def main():
    days = 14
    if "--days" in sys.argv:
        try:
            days = int(sys.argv[sys.argv.index("--days") + 1])
        except Exception:
            pass
    uni = universe() | ALWAYS
    today = dt.date.today()
    hits = []  # (sym, date, days_away, time)
    near_all = []  # unfiltered 0–1d Nasdaq symbols (not universe-gated)
    for k in range(0, days + 1):
        d = today + dt.timedelta(days=k)
        if d.weekday() >= 5:  # skip weekends
            continue
        cal = earnings_on(d.isoformat())
        if k <= 1:
            for sym, t in sorted(cal.items()):
                near_all.append((sym, d.isoformat(), k, t))
        for sym in (uni & set(cal)) | (ALWAYS & set(cal)):
            hits.append((sym, d.isoformat(), (d - today).days, cal[sym]))
        time.sleep(0.5)
    # de-dupe hits
    seen = set()
    uniq = []
    for h in hits:
        if h[0] in seen:
            continue
        seen.add(h[0])
        uniq.append(h)
    hits = uniq
    hits.sort(key=lambda x: (x[2], x[0]))

    lines = [f"# Earnings Radar (next {days} days)\n",
             f"_Generated {dt.datetime.now():%Y-%m-%d %H:%M} local by "
             "`market_data/fetch_earnings.py`. Intersection of the Nasdaq earnings "
             "calendar with the cached universe **plus ALWAYS watch names**. "
             "**Not sufficient alone** — UNION Robinhood `get_earnings_calendar` "
             "and search investor/analyst days. Nasdaq omitted XE on 2026-08-13._\n",
             "> 🔴 **sell-gate**: do not let any credit spread expire after this date "
             "(the AVGO / MU rule). 🟢 **directional**: pre-earnings debit/long watch.\n",
             "| Ticker | Report date | Days away | Session | Flags |",
             "|---|---|---|---|---|"]
    if hits:
        for sym, d, away, t in hits:
            tt = {"time-pre-market": "BMO", "time-after-hours": "AMC"}.get(t, t or "?")
            lines.append(f"| **{sym}** | {d} | {away}d | {tt} | "
                         f"🔴 sell-gate · 🟢 directional |")
    else:
        lines.append("| _none in window_ | – | – | – | – |")
    lines.append(f"\n_{len(hits)} name(s) reporting in the next {days} days. "
                 "Regenerate daily: `python3 market_data/fetch_earnings.py`._")
    # Unfiltered 0–1d so off-universe names (XE-class) still surface
    lines.append("\n## Unfiltered Nasdaq 0–1d (not universe-gated)\n")
    lines.append("_If a name is here and not in the table above, it still needs a "
                 "catalyst card. Agent must also UNION Robinhood MCP — Nasdaq omitted "
                 "XE on 8/13._\n")
    if near_all:
        by_day = {}
        for sym, d, k, t in near_all:
            by_day.setdefault(f"{d} ({'0d' if k == 0 else '1d'})", []).append(sym)
        for label, syms in by_day.items():
            lines.append(f"- **{label}:** {', '.join(syms)}")
    else:
        lines.append("_none returned from Nasdaq for 0–1d._")
    open(MD_OUT, "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nwrote {MD_OUT}")

if __name__ == "__main__":
    main()
