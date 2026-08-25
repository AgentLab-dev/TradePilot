#!/usr/bin/env python3
"""Full path simulation of a call debit spread under the management rule.

debit_test.py answers "did the underlying get there." That is not the same
question as "did the trade make money," because a debit spread can be exited
at +100% long before the underlying reaches breakeven, and can be stopped out
at -50% on a path that later recovers. The 2026-08-09 lesson (endpoint
backtest != live P&L) applies to long premium exactly as it did to credit.

So: walk every historical window day by day, reprice both legs with
Black-Scholes at each step, and apply the actual rules --
    take profit  at >= +TP% of debit
    stop         at <= -SL% of debit
    otherwise    hold to expiry and settle at intrinsic
Report expectancy per contract, win rate, and the split between managed exits
and expiry settlements.

IV is held constant across the path. That is a real simplification: it
understates gains on a vol expansion and overstates them on a crush. It is
stated here rather than buried, and it is why the OKTA pre-earnings vol ramp
is described as an unmodeled tailwind rather than counted in the number.

Usage: python3 debit_sim.py <historicals_dump.json> ...
"""
import json
import math
import sys
from datetime import datetime

TP = 1.00   # exit at +100% of debit
SL = 0.50   # stop at -50% of debit

# sym, spot, weeks, long K, short K, debit, IV, label
# Every debit below is built from the REAL chain: buy at high_fill_rate_buy,
# sell at high_fill_rate_sell. Mid-price fills are a fiction that inflates
# every one of these numbers.
# A short strike of 99999 makes the short leg worthless, which turns the
# structure into a plain LONG CALL. Needed because the cash/Level-2 account
# cannot hold a vertical -- the broker prices the short leg as naked and
# demands 100 shares of collateral (Aug 10 dry run, alertType
# OPTION_NOT_ENOUGH_SHARES_FOR_COLLATERAL, cash.infinite=true).
TRADES = [
    # Spreads at Aug 10 live prices -- what we WOULD trade with Level 3 margin
    ("HOOD",  93.31, 6, 105, 120,  2.406, 0.635, "SPREAD 105/120c @ 2.41"),
    ("NEM",  115.72, 6, 125, 140,  2.544, 0.452, "SPREAD 125/140c @ 2.54"),
    ("NEM",  115.72, 6, 120, 135,  3.424, 0.439, "SPREAD 120/135c @ 3.42"),
    # Long calls -- what the cash account CAN actually hold
    ("HOOD",  93.31, 6, 110, 99999, 2.713, 0.640, "LONGCALL 110c @ 2.71"),
    ("HOOD",  93.31, 6, 120, 99999, 1.412, 0.657, "LONGCALL 120c @ 1.41"),
    ("NEM",  115.72, 6, 130, 99999, 2.534, 0.461, "LONGCALL 130c @ 2.53"),
    ("NEM",  115.72, 6, 135, 99999, 1.720, 0.471, "LONGCALL 135c @ 1.72"),
    ("NEM",  115.72, 6, 125, 99999, 3.650, 0.452, "LONGCALL 125c @ 3.65"),
]

R = 0.042
TS_FIELDS = ("begins_at", "timestamp", "date", "start_time")


def ncdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def call(s, k, t, iv):
    if t <= 1e-9:
        return max(0.0, s - k)
    d1 = (math.log(s / k) + (R + 0.5 * iv * iv) * t) / (iv * math.sqrt(t))
    d2 = d1 - iv * math.sqrt(t)
    return s * ncdf(d1) - k * math.exp(-R * t) * ncdf(d2)


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
    print(f"{'SYM':5} {'STRUCTURE':24} {'risk':>6} {'maxGain':>8} {'R:R':>6} "
          f"{'win%':>6} {'TP%':>5} {'stop%':>6} {'exp$':>8} {'exp%':>7} {'N':>5}")
    print("-" * 104)

    for sym, spot, weeks, k1, k2, debit, iv, label in TRADES:
        bars = series.get(sym)
        if not bars:
            continue
        closes = [float(b["close_price"]) for b in bars]
        days = weeks * 5
        T0 = weeks / 52.0
        width = k2 - k1
        maxgain = width - debit

        results = []
        tp_hits = sl_hits = 0
        for i in range(len(closes) - days):
            s0 = closes[i]
            scale = spot / s0           # replay the shape, anchored at today's spot
            pnl = None
            for d in range(1, days + 1):
                t_left = max(T0 * (1 - d / days), 1e-9)
                s = closes[i + d] * scale
                val = call(s, k1, t_left, iv) - call(s, k2, t_left, iv)
                if val >= debit * (1 + TP):
                    pnl = debit * TP
                    tp_hits += 1
                    break
                if val <= debit * (1 - SL):
                    pnl = -debit * SL
                    sl_hits += 1
                    break
            if pnl is None:
                s = closes[i + days] * scale
                pnl = max(0.0, min(width, s - k1)) - debit
            results.append(pnl)

        n = len(results)
        if not n:
            continue
        wins = sum(1 for p in results if p > 0)
        exp = sum(results) / n
        print(f"{sym:5} {label:24} {debit*100:6.0f} {maxgain*100:8.0f} "
              f"{maxgain/debit:5.1f}x {100*wins/n:5.0f}% {100*tp_hits/n:4.0f}% "
              f"{100*sl_hits/n:5.0f}% {exp*100:+8.0f} {100*exp/debit:+6.0f}% {n:5d}")

    print()
    print(f"Rules simulated: take profit +{TP:.0%} of debit, stop -{SL:.0%} of debit, else hold to expiry.")
    print("risk/maxGain/exp$ are per contract in dollars. exp% is expectancy as a share of capital risked.")
    print("IV held constant across each path - vol expansion and crush are both unmodeled.")


if __name__ == "__main__":
    main()
