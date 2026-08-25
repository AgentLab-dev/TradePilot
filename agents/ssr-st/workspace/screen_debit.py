#!/usr/bin/env python3
"""Screen a universe for names that can support the 300-risk / 1000-return mandate.

Pulling real option chains for 40 names is expensive, and most will fail. So
this builds a SYNTHETIC spread per name -- Black-Scholes priced off the name's
own realized vol, marked up for the volatility risk premium -- searches the
strike grid for the structure that best fits the mandate, and runs the same
managed-path simulation as debit_sim.py.

The output is a shortlist, not a trade. Every survivor still needs its real
chain pulled, because a synthetic mid means nothing if the book is 6 contracts
wide (the NTAP/HON/EXPE lesson).

Vol handling: IV = realized_30d * VRP_MARKUP. Buying premium at realized vol
would flatter every result, since implied normally trades above realized.

Usage: python3 screen_debit.py <dump.json> ...
"""
import json
import math
import sys
from datetime import datetime

TP, SL = 1.00, 0.50
R = 0.042
WEEKS = 6
VRP_MARKUP = 1.15
BUDGET = 300.0       # dollars of risk per ticket
# $1,000 of gain on $300 of risk is a RATIO requirement, not a per-contract
# dollar one. Demanding $1,000 from a single contract silently deletes every
# stock under ~$60 from the universe -- MARA, NNE, SMCI, CELH, OKLO all
# vanished on the first run for that reason alone. Size to the budget instead.
MIN_RR = 1000.0 / 300.0
TS_FIELDS = ("begins_at", "timestamp", "date", "start_time")


def ncdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def call(s, k, t, iv):
    if t <= 1e-9:
        return max(0.0, s - k)
    d1 = (math.log(s / k) + (R + 0.5 * iv * iv) * t) / (iv * math.sqrt(t))
    return s * ncdf(d1) - k * math.exp(-R * t) * ncdf(d1 - iv * math.sqrt(t))


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


def realized_vol(closes, n=30):
    rets = [math.log(closes[i] / closes[i - 1]) for i in range(len(closes) - n, len(closes))]
    m = sum(rets) / len(rets)
    var = sum((r - m) ** 2 for r in rets) / (len(rets) - 1)
    return math.sqrt(var * 252)


def simulate(closes, spot, k1, k2, debit, iv, days, T0):
    width = k2 - k1
    out, tp, sl = [], 0, 0
    for i in range(len(closes) - days):
        scale = spot / closes[i]
        pnl = None
        for d in range(1, days + 1):
            t_left = max(T0 * (1 - d / days), 1e-9)
            s = closes[i + d] * scale
            val = call(s, k1, t_left, iv) - call(s, k2, t_left, iv)
            if val >= debit * (1 + TP):
                pnl, _ = debit * TP, tp
                tp += 1
                break
            if val <= debit * (1 - SL):
                pnl = -debit * SL
                sl += 1
                break
        if pnl is None:
            s = closes[i + days] * scale
            pnl = max(0.0, min(width, s - k1)) - debit
        out.append(pnl)
    n = len(out)
    return (sum(out) / n, sum(1 for p in out if p > 0) / n, n) if n else (0, 0, 0)


def main():
    series = load(sys.argv[1:])
    days, T0 = WEEKS * 5, WEEKS / 52.0
    rows = []

    for sym, bars in series.items():
        closes = [float(b["close_price"]) for b in bars]
        if len(closes) < 200:
            continue
        spot = closes[-1]
        iv = realized_vol(closes) * VRP_MARKUP
        step = max(round(spot * 0.02, 2), 0.5)

        best = None
        k1 = spot * 1.01
        while k1 <= spot * 1.30:
            for wmult in (2, 3, 4, 5, 6, 8, 10, 13, 16):
                k2 = k1 + step * wmult
                debit = call(spot, k1, T0, iv) - call(spot, k2, T0, iv)
                gain = (k2 - k1) - debit
                if debit <= 0 or debit * 100 > BUDGET or gain / debit < MIN_RR:
                    continue
                exp, win, n = simulate(closes, spot, k1, k2, debit, iv, days, T0)
                if n and (best is None or exp / debit > best[0]):
                    best = (exp / debit, exp, win, k1, k2, debit, gain, n)
            k1 += step

        if best:
            rows.append((sym, spot, iv, *best))

    rows.sort(key=lambda r: -r[3])
    print(f"{'SYM':6} {'spot':>9} {'IVest':>6} {'K1':>9} {'K2':>9} {'qty':>4} "
          f"{'risk$':>7} {'gain$':>7} {'R:R':>6} {'BE%':>6} {'win%':>6} {'exp%':>7} {'N':>5}")
    print("-" * 108)
    for sym, spot, iv, exp_pct, exp, win, k1, k2, debit, gain, n in rows:
        be = (k1 + debit) / spot - 1
        qty = max(1, int(BUDGET // (debit * 100)))
        print(f"{sym:6} {spot:9.2f} {iv:5.0%} {k1:9.2f} {k2:9.2f} {qty:4d} "
              f"{debit*100*qty:7.0f} {gain*100*qty:7.0f} {gain/debit:5.1f}x {be:+6.1%} "
              f"{win:6.0%} {exp_pct:+7.0%} {n:5d}")
    print()
    print(f"Synthetic strikes, ~2%-of-spot grid; IV = realized_30d x {VRP_MARKUP}.")
    print(f"qty sized to a ${BUDGET:.0f} budget; gain$ is total across contracts at max.")
    print("Survivors still need a real chain pull -- a synthetic mid is not a fill.")


if __name__ == "__main__":
    main()
