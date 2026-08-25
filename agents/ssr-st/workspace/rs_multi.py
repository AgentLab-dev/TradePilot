#!/usr/bin/env python3
"""Multi-window relative-strength table from Robinhood historicals dumps.

Exists because ranking on a single session is how the energy sector got cut
from the universe on Aug 8 (see agent_learning_log 2026-08-09). Sector tape
answers "is today risk-[REDACTED]"; leadership needs the 1-week / 1-month / 10-week
windows side by side.

Usage:  python3 rs_multi.py <dump.json> [<dump.json> ...]
        python3 rs_multi.py --sort 1mo <dump.json>

Prints, per symbol: last close, and returns over 1 day, 1 week, 1 month,
10 weeks — plus %-from-high over the loaded range and the true bar count, so
an interpolated-heavy series can't masquerade as a full lookback.
"""
import json
import sys
from datetime import datetime, timedelta

TS_FIELDS = ("begins_at", "timestamp", "date", "start_time")
WINDOWS = [("1d", 1), ("1w", 7), ("1mo", 30), ("10w", 70)]


def bar_time(b):
    for f in TS_FIELDS:
        v = b.get(f)
        if v:
            return datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    return None


def close_on_or_before(bars, cutoff):
    older = [b for b in bars if bar_time(b) <= cutoff]
    return older[-1] if older else bars[0]


def load(files):
    by_symbol = {}
    for f in files:
        with open(f) as fh:
            raw = json.load(fh)
        # MCP dumps arrive either as {"data": {"results": [...]}} or bare.
        results = raw.get("data", raw).get("results", [])
        for r in results:
            bucket = by_symbol.setdefault(r["symbol"], {})
            for b in r.get("bars", []):
                if b.get("interpolated"):
                    continue
                t = bar_time(b)
                if t:
                    bucket[t] = b
    return {s: [b[t] for t in sorted(b)] for s, b in by_symbol.items()}


def main():
    args = sys.argv[1:]
    sort_key = "1mo"
    if "--sort" in args:
        i = args.index("--sort")
        sort_key = args[i + 1]
        del args[i:i + 2]
    if not args:
        print("usage: python3 rs_multi.py [--sort 1d|1w|1mo|10w] <dump.json> ...")
        sys.exit(1)

    series = load(args)
    rows = []
    for sym, bars in series.items():
        if len(bars) < 3:
            continue
        last = bars[-1]
        t_end = bar_time(last)
        c = float(last["close_price"])
        rets = {}
        for name, days in WINDOWS:
            ref = close_on_or_before(bars, t_end - timedelta(days=days))
            rets[name] = (c / float(ref["close_price"]) - 1) * 100
        hi = max(float(b["high_price"]) for b in bars)

        # Price-vs-volume: was the last move backed by participation? An up day
        # on <0.7x average volume is drift, not accumulation.
        vols = [float(b.get("volume") or 0) for b in bars]
        avg_vol = sum(vols[-31:-1]) / max(1, len(vols[-31:-1]))
        rvol = vols[-1] / avg_vol if avg_vol else 0
        day_chg = rets["1d"]
        if day_chg > 0 and rvol >= 1.5:
            conf = "ACCUM"       # up on heavy volume
        elif day_chg < 0 and rvol >= 1.5:
            conf = "DISTRIB"     # down on heavy volume
        elif day_chg > 0 and rvol < 0.7:
            conf = "weak-up"     # rally nobody showed up for
        else:
            conf = "-"
        rows.append((sym, c, rets, (c / hi - 1) * 100, len(bars), rvol, conf))

    rows.sort(key=lambda r: -r[2].get(sort_key, 0))
    hdr = f"{'SYM':6} {'last':>10}" + "".join(f"{w:>9}" for w, _ in WINDOWS)
    print(hdr + f"{'fromHi':>9} {'rvol':>7} {'flag':>9} {'bars':>5}   (sort {sort_key})")
    print("-" * (len(hdr) + 34))
    for sym, c, rets, fh, n, rvol, conf in rows:
        line = f"{sym:6} {c:10.2f}" + "".join(f"{rets[w]:+9.1f}" for w, _ in WINDOWS)
        print(line + f"{fh:+9.1f} {rvol:7.2f} {conf:>9} {n:5d}")


if __name__ == "__main__":
    main()
