#!/usr/bin/env python3
"""Backtest for LONG-premium structures (call debit spreads).

The credit-spread question was "how often does price break the short strike."
For a debit spread the question inverts: how often does the underlying rise
FAR ENOUGH, FAST ENOUGH, to clear breakeven — and how often does it get far
enough to hand back the managed target (+100-150% of debit) that the 2026-07-07
backtest says is where call-debit expectancy actually lives.

Also answers the "80% probability" question three ways, because an 80% chance
of a GAIN is not a thing that exists (base rate ~52-55%):
  hold80   = the level a 0.20-delta short put implies, i.e. ~80% chance price
             stays above it. Derived from IV, not from a quoted put.
  win2w    = share of overlapping 2-week windows that closed green.
  reachBE  = share of N-week windows that closed above the spread's breakeven.

Every rate is printed next to the SAMPLE'S OWN TREND, because a clean number
on a +275% run is a statement about the tape, not about the trade
(see agent_learning_log 2026-08-09).

Usage: python3 debit_test.py <historicals_dump.json> ...
"""
import json
import math
import sys
from datetime import datetime

# sym, spot, weeks, long strike, short strike, debit, IV, label
TRADES = [
    ("NEM",  112.98, 6, 120, 135,  2.952, 0.445, "Sep18 120/135 @ 2.95"),
    ("OKTA", 148.32, 2, 155, 170,  2.920, 0.586, "Aug21 155/170 @ 2.92"),
    ("PLTR", 172.01, 6, 195, 210,  2.288, 0.526, "Sep18 195/210 @ 2.29"),
    ("NOW",  124.88, 6, 135, 150,  3.396, 0.579, "Sep18 135/150 @ 3.40"),
    ("MPC",  298.20, 6, 330, 350,  3.029, 0.378, "Sep18 330/350 @ 3.03"),
    ("MSFT", 499.99, 6, 560, 590,  2.166, 0.286, "Sep18 560/590 @ 2.17"),
]

TS_FIELDS = ("begins_at", "timestamp", "date", "start_time")


def bar_time(b):
    for f in TS_FIELDS:
        v = b.get(f)
        if v:
            return datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    return None


def load(files):
    by_symbol = {}
    for f in files:
        with open(f) as fh:
            raw = json.load(fh)
        for r in raw.get("data", raw).get("results", []):
            bucket = by_symbol.setdefault(r["symbol"], {})
            for b in r.get("bars", []):
                if b.get("interpolated"):
                    continue
                t = bar_time(b)
                if t:
                    bucket[t] = b
    return {s: [b[t] for t in sorted(b)] for s, b in by_symbol.items()}


def main():
    series = load(sys.argv[1:])
    print(f"{'SYM':5} {'STRUCTURE':22} {'BE%':>6} {'reachBE':>8} {'touch':>7} "
          f"{'2wkWin':>7} {'hold80':>8} {'sample':>8} {'worst':>7} {'N':>4}")
    print("-" * 96)

    for sym, spot, weeks, k1, k2, debit, iv, label in TRADES:
        bars = series.get(sym)
        if not bars:
            print(f"{sym:5} {label:22}   no data")
            continue
        closes = [float(b["close_price"]) for b in bars]
        highs = [float(b["high_price"]) for b in bars]

        be = k1 + debit
        be_pct = (be / spot - 1) * 100

        # Daily bars -> trading days per window.
        days = weeks * 5

        reach = touch = 0
        moves = []
        for i in range(len(closes) - days):
            end_move = (closes[i + days] / closes[i] - 1) * 100
            moves.append(end_move)
            if end_move >= be_pct:
                reach += 1
            # Path: did it EVER trade through breakeven inside the window?
            peak = (max(highs[i:i + days + 1]) / closes[i] - 1) * 100
            if peak >= be_pct:
                touch += 1
        n = len(moves)
        if not n:
            continue

        # Overlapping 2-week (10 trading day) win rate — the honest read on
        # "positive growth in two weeks".
        wins2 = sum(1 for i in range(len(closes) - 10)
                    if closes[i + 10] > closes[i])
        tot2 = len(closes) - 10
        win2w = 100 * wins2 / tot2 if tot2 else 0

        # Level with ~80% chance of holding, from a lognormal at this IV.
        # z=0.8416 is the 20th percentile; sigma scales with sqrt(time).
        t = weeks / 52
        sigma = iv * math.sqrt(t)
        hold80 = spot * math.exp(-0.8416 * sigma - 0.5 * sigma * sigma)

        sample_trend = (closes[-1] / closes[0] - 1) * 100
        print(f"{sym:5} {label:22} {be_pct:+6.1f} {100*reach/n:7.0f}% "
              f"{100*touch/n:6.0f}% {win2w:6.0f}% {hold80:8.2f} "
              f"{sample_trend:+7.1f}% {min(moves):+6.1f}% {n:4d}")

    print()
    print("reachBE = closed above breakeven at expiry · touch = traded through it at any point")
    print("2wkWin  = overlapping 2-week windows that closed green (base rate, ~52-55% is normal)")
    print("hold80  = price with ~80% chance of holding, implied by IV over the trade's life")
    print("sample  = the underlying's total move across the loaded history — read every")
    print("          rate above against it; a high hit rate on a big uptrend is not edge")


if __name__ == "__main__":
    main()
