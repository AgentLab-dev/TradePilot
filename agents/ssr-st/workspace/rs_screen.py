#!/usr/bin/env python3
"""Relative-strength / momentum screen — self-serve discovery fallback.

Purpose: reproduce IBD-style RS ranking from raw Robinhood data so the agent
never depends on a manual IBD paste. Validated Jul 9 2026: this screen ranks
ALAB #1 (+212% 3mo) with zero IBD input — closing the discovery gap.

Usage (two steps, because price data comes from the MCP, not this script):
  1. Agent pulls get_equity_historicals for UNIVERSE (start ~6 months back,
     interval=week is cheapest; interval=day also works). Each MCP call
     writes a JSON dump file.
  2. Run:  python3 rs_screen.py <dump1.json> <dump2.json> ...
     -> prints the ranked table (3mo return, 1mo momentum, %-from-high).

Ranking logic (all windows are DATE-based, so any bar interval works):
  - 3-month return (close ~90d ago -> last close)       = primary RS
  - %-from-high (last close vs high of last 90d)        = anti-chase lens
      (near 0 = extended/at highs; deeply negative = pulled back = setup)
  - 1-month momentum (close ~30d ago -> last close)     = freshness

Cross-check the top of this list against FFTY holdings
(stockanalysis.com/etf/ffty/holdings) — the public IBD-50 proxy.
"""
import json, sys
from datetime import datetime, timedelta

# Cross-sector universe. Edit as leadership rotates.
# Refreshed Aug 8 2026: FFTY rotated out of AI-hardware into
# healthcare/biotech + fintech/financials — those names added here.
UNIVERSE = [
    # book + live option candidates
    "NVDA", "ORCL", "MS", "CEG", "HPE", "UNH", "HON", "AVGO", "DELL", "AMD",
    # FFTY (IBD-50 proxy) top holdings — Aug 6 2026 snapshot
    "SEZL", "ENVA", "LQDA", "CARE", "SN", "INDV", "DAVE", "KNSA", "ECO", "TGTX",
    "GKOS", "KRYS", "OSCR", "EXPE", "EXEL", "NBIX", "LLY", "DDOG", "RSI", "NET",
    # liquid top-gainers cross-check + prior non-tech survivors
    "SNDK", "AEHR", "MXL", "AGL", "HWM", "AGX", "FIX", "TRGP", "NEM", "COIN",
]

TS_FIELDS = ("begins_at", "timestamp", "date", "start_time")


def bar_time(b):
    for f in TS_FIELDS:
        v = b.get(f)
        if v:
            return datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    return None


def close_on_or_before(bars, cutoff):
    """Last bar at or before cutoff; falls back to the oldest bar."""
    older = [b for b in bars if bar_time(b) and bar_time(b) <= cutoff]
    return older[-1] if older else bars[0]


def load_rows(files):
    """Merge bars per symbol across every dump.

    Weekly history + a daily tail can be passed together: the weekly series
    lags by up to a week, so pass a short daily dump alongside it to bring the
    last close current. Bars are merged, de-duplicated by timestamp (finer
    interval wins) and re-sorted.
    """
    by_symbol = {}
    for f in files:
        d = json.load(open(f))
        for r in d["data"]["results"]:
            bucket = by_symbol.setdefault(r["symbol"], {})
            for b in r.get("bars", []):
                if b.get("interpolated"):
                    continue
                t = bar_time(b)
                if t:
                    bucket[t] = b

    rows = []
    for sym, bucket in by_symbol.items():
        bars = [bucket[t] for t in sorted(bucket)]
        if len(bars) >= 5:
            last = bars[-1]
            t_end = bar_time(last)
            c = float(last["close_price"])

            b3 = close_on_or_before(bars, t_end - timedelta(days=90))
            b1 = close_on_or_before(bars, t_end - timedelta(days=30))
            ret3 = (c / float(b3["close_price"]) - 1) * 100
            ret1 = (c / float(b1["close_price"]) - 1) * 100

            window = [b for b in bars if bar_time(b) >= t_end - timedelta(days=90)]
            hi = max(float(b["high_price"]) for b in window)
            from_hi = (c / hi - 1) * 100

            # Robinhood returns heavily interpolated series for some symbols
            # (XOM came back 21-of-26 bars interpolated). Those get dropped by the
            # interpolated filter, close_on_or_before silently falls back to the
            # oldest bar, and the "3-month" return is really a 3-week return.
            # Carry the true lookback so a short window is visible, not implied.
            span3 = (t_end - bar_time(b3)).days
            rows.append((sym, ret3, ret1, from_hi, c, span3))
    rows.sort(key=lambda x: -x[1])
    return rows


def main():
    if len(sys.argv) < 2:
        print("usage: python3 rs_screen.py <historicals_dump.json> ...")
        print("universe (%d names):" % len(UNIVERSE), " ".join(UNIVERSE))
        sys.exit(1)
    rows = load_rows(sys.argv[1:])
    print("SYMBOL   3moRET%   1moRET%   %fromHigh      last  lookback")
    for s, r3, r1, fh, c, span3 in rows:
        flag = "  <-- SHORT, ignore RS" if span3 < 60 else ""
        print(f"{s:6} {r3:8.1f} {r1:8.1f} {fh:9.1f}   {c:9.2f}    {span3:4d}d{flag}")


if __name__ == "__main__":
    main()
