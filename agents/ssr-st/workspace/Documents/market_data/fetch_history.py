#!/usr/bin/env python3
"""Fetch ~2y daily OHLCV for the watchlist and write it to ../market_history.md.

Why: avoid re-pulling on every STKK run (saves time + tokens + dodges rate limits).
Bulk data is written straight to disk as compact CSV blocks inside a Markdown file,
so it never has to pass through the model's context.

Source: Nasdaq historical API (free, scriptable, not rate-limited like Yahoo).
Run:  python3 fetch_history.py            # all tickers
      python3 fetch_history.py SYM1 SYM2  # only these (merges into existing md)
Output: /Users/koteswararao.venkata/Documents/Cursor/ssr-analyst/Documents/market_history.md
"""
import json, os, sys, time, subprocess, datetime as dt, re

HERE = os.path.dirname(os.path.abspath(__file__))
MD = os.path.normpath(os.path.join(HERE, "..", "market_history.md"))
# curl beats urllib here: system cert store avoids the sandbox SSL verify failure.
CURL_HDRS = [
    "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "-H", "Accept: application/json", "-H", "Accept-Language: en-US,en;q=0.9",
    "-H", "Origin: https://www.nasdaq.com", "-H", "Referer: https://www.nasdaq.com/",
]

UNIVERSE = {
    "benchmarks": ["SPY", "QQQ"],
    "ai_infra":   ["TLN", "CRWV", "IREN", "MARA"],
    "chip_chain": ["ASML", "INTC", "TSLA"],
    "semis":      ["MU", "SMH", "SOXX", "SOXL"],
    "core":       ["ORCL", "HOOD", "NNE", "NTAP", "XE", "OKLO"],
    "ntap_peers": ["ANET", "HPE", "PSTG", "DELL", "SMCI", "WDC", "STX", "IBM", "SNDK"],
    "other":      ["GDX", "DDOG", "AVGO", "SNOW"],
    "growth_screen": ["ZS", "VEEV", "MNDY"],
    "spx_swing": ["NOW", "AMZN", "META", "CRWD"],
    "mangos":     ["NVDA", "GOOGL", "MSFT"],  # AI-leadership basket (META/AMZN/SPCX already above)
    "watch_only": ["SPCX"],
}
ALL = [s for grp in UNIVERSE.values() for s in grp]
ETFS = {"SPY", "QQQ", "SMH", "SOXX", "SOXL", "GDX"}
ANALYST_MEAN = {
    "TLN": 473, "CRWV": 140, "NTAP": 172, "ORCL": 255, "HOOD": 100, "NNE": 40,
    "MARA": 16.3, "IREN": 96, "ASML": 1701, "INTC": 93, "MU": 739, "SPCX": 139,
    "AVGO": 490, "SNOW": 291, "ZS": 200, "VEEV": 235, "MNDY": 124.59,
    "NOW": 1150, "AMZN": 265, "META": 825, "CRWD": 520,
}

def _num(s):
    return float(str(s).replace("$", "").replace(",", "").strip())

def fetch(sym, years=2, fromdate=None):
    today = dt.date.today()
    frm = fromdate or today.replace(year=today.year - years).isoformat()
    classes = (["etf", "stocks"] if sym in ETFS else ["stocks", "etf"])
    for cls in classes:
        url = (f"https://api.nasdaq.com/api/quote/{sym}/historical?"
               f"assetclass={cls}&fromdate={frm}&todate={today.isoformat()}&limit=9999")
        for attempt in range(4):
            try:
                raw = subprocess.run(["curl", "-s", "--max-time", "30", *CURL_HDRS, url],
                                     capture_output=True, text=True, timeout=40).stdout
                d = json.loads(raw)
                rows = (d.get("data") or {}).get("tradesTable", {}).get("rows")
                if not rows:
                    break  # try next asset class
                out = []
                for r in rows:
                    mm, dd, yy = r["date"].split("/")
                    out.append((f"{yy}-{mm}-{dd}", _num(r["open"]), _num(r["high"]),
                                _num(r["low"]), _num(r["close"]),
                                int(_num(r["volume"]))))
                out.sort(key=lambda x: x[0])  # ascending by date
                return out
            except Exception:
                time.sleep(1.5 * (attempt + 1))
    return None

def parse_existing():
    if not os.path.exists(MD):
        return {}
    txt = open(MD).read()
    return {m.group(1): m.group(2).rstrip()
            for m in re.finditer(r"\n## ([A-Z0-9.]+)\n(.*?)(?=\n## |\Z)", txt, re.S)}

def parse_rows(section_text):
    """Pull the csv rows out of an existing section as tuples (ascending)."""
    m = re.search(r"```csv\n.*?\n(.*?)\n```", section_text, re.S)
    if not m:
        return []
    rows = []
    for line in m.group(1).splitlines():
        p = line.split(",")
        if len(p) >= 6:
            rows.append((p[0], float(p[1]), float(p[2]), float(p[3]), float(p[4]), int(p[5])))
    return rows

def section(sym, rows):
    last = rows[-1]
    head = (f"- bars: {len(rows)} | range: {rows[0][0]} → {last[0]} | "
            f"last close: {last[4]:.2f} | analyst mean: "
            f"{ANALYST_MEAN.get(sym, 'n/a')} | fetched: "
            f"{dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M')}Z")
    lines = "\n".join(f"{d},{o:.4f},{h:.4f},{l:.4f},{c:.4f},{v}"
                      for d, o, h, l, c, v in rows)
    return f"{head}\n\n```csv\ndate,open,high,low,close,volume\n{lines}\n```"

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    delta = "--delta" in sys.argv
    targets = args if args else ALL
    sections = parse_existing()
    ok, failed, nochange = [], [], []
    for sym in targets:
        if delta and sym in sections:
            old = parse_rows(sections[sym])
            last = old[-1][0] if old else None
            # pull a short recent window starting just before the last cached bar
            frm = (dt.date.fromisoformat(last) - dt.timedelta(days=7)).isoformat() if last else None
            new = fetch(sym, fromdate=frm)
            if not new:
                failed.append(sym); print(f"  {sym}: delta FAILED"); time.sleep(0.8); continue
            fresh = [r for r in new if (last is None or r[0] > last)]
            if not fresh:
                nochange.append(sym); print(f"  {sym}: up-to-date ({last})"); time.sleep(0.5); continue
            merged = old + fresh
            sections[sym] = section(sym, merged)
            ok.append(sym)
            print(f"  {sym}: +{len(fresh)} bar(s) → {merged[-1][0]} @ {merged[-1][4]:.2f}")
            time.sleep(0.8); continue
        rows = fetch(sym)
        if rows:
            sections[sym] = section(sym, rows)
            ok.append(sym)
            print(f"  {sym}: {len(rows)} bars → {rows[-1][0]} @ {rows[-1][4]:.2f}")
        else:
            failed.append(sym)
            print(f"  {sym}: FAILED / no history")
        time.sleep(0.8)
    order = [s for grp in UNIVERSE.values() for s in grp]
    order += [s for s in sections if s not in order]
    with open(MD, "w") as f:
        f.write("# Market History Cache (daily OHLCV)\n\n")
        f.write(f"_Last run: {dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M')}Z. "
                "Source: Nasdaq historical API (split-adjusted daily). "
                "Regenerate with `market_data/fetch_history.py`._\n\n")
        f.write("> STKK reads this file first; only re-pull a ticker if its last bar "
                "is older than the prior trading day, or it's missing here.\n\n")
        f.write("| Group | Tickers |\n|---|---|\n")
        for g, syms in UNIVERSE.items():
            f.write(f"| {g} | {', '.join(syms)} |\n")
        f.write("\n---\n")
        for s in order:
            if s in sections:
                f.write(f"\n## {s}\n{sections[s]}\n")
    sz = os.path.getsize(MD) / 1024
    print(f"\nupdated={len(ok)} up-to-date={len(nochange)} failed={len(failed)}  "
          f"→  {MD} ({sz:.0f} KB)")
    if failed:
        print("FAILED:", failed)

if __name__ == "__main__":
    main()
