#!/usr/bin/env python3
"""Managed-path simulation for PUT CREDIT spreads.

A touch-rate is a blunt proxy: it assumes any tag of the short strike costs a
fixed multiple of the credit. Real management closes at a profit target long
before most touches happen, and a touch with five weeks left is not the same
loss as a touch with five days left. So this reprices both put legs every day
with Black-Scholes and applies the actual rules:

    take profit  at +TP% of the credit collected
    stop         when the spread's value reaches SL x the credit
    otherwise    hold to expiry and settle at intrinsic

Companion to debit_sim.py, same caveat: IV is held constant along each path.
For credit spreads that cuts against us in the honest direction -- a real
selloff expands vol and would make the stop fire harder than modeled.

Usage: python3 credit_sim.py <historicals_dump.json> ...
"""
import json
import math
import sys
from datetime import datetime

TP = 0.50   # buy back at 50% of max profit -- the standing income-book rule
SL = 2.00   # abort when the spread costs 2x the credit to close
R = 0.042
WEEKS = 6

# sym, spot, short K, long K, credit, IV, label
TRADES = [
    ("PLTR", 178.33, 160, 150, 1.996, 0.520, "160/150p @ 2.00"),
    ("PLTR", 178.33, 155, 145, 1.497, 0.526, "155/145p @ 1.50"),
    ("PLTR", 178.33, 150, 140, 1.099, 0.536, "150/140p @ 1.10"),
    ("NEM",  115.72, 110, 100, 2.671, 0.443, "110/100p @ 2.67"),
    ("NEM",  115.72, 105,  95, 1.643, 0.438, "105/95p  @ 1.64"),
    ("NEM",  115.72, 100,  90, 0.877, 0.433, "100/90p  @ 0.88"),
    ("MPC",  312.31, 280, 270, 1.481, 0.403, "280/270p @ 1.48 (illiquid)"),
    ("VLO",  311.56, 290, 280, 2.132, 0.413, "290/280p @ 2.13"),
    ("VLO",  311.56, 280, 270, 1.388, 0.424, "280/270p @ 1.39"),
    ("VLO",  311.56, 270, 260, 1.194, 0.435, "270/260p @ 1.19"),
]

TS_FIELDS = ("begins_at", "timestamp", "date", "start_time")


def ncdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def put(s, k, t, iv):
    if t <= 1e-9:
        return max(0.0, k - s)
    d1 = (math.log(s / k) + (R + 0.5 * iv * iv) * t) / (iv * math.sqrt(t))
    d2 = d1 - iv * math.sqrt(t)
    return k * math.exp(-R * t) * ncdf(-d2) - s * ncdf(-d1)


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
    days, T0 = WEEKS * 5, WEEKS / 52.0
    print(f"{'SYM':5} {'STRUCTURE':26} {'cred$':>6} {'risk$':>6} {'RoR':>6} "
          f"{'buffer':>7} {'win%':>6} {'TP%':>5} {'stop%':>6} {'exp$':>7} {'exp%':>6} {'N':>5}")
    print("-" * 104)

    for sym, spot, ks, kl, credit, iv, label in TRADES:
        bars = series.get(sym)
        if not bars:
            continue
        closes = [float(b["close_price"]) for b in bars]
        width = ks - kl
        risk = (width - credit) * 100

        out, tp, sl = [], 0, 0
        for i in range(len(closes) - days):
            scale = spot / closes[i]
            pnl = None
            for d in range(1, days + 1):
                t_left = max(T0 * (1 - d / days), 1e-9)
                s = closes[i + d] * scale
                val = put(s, ks, t_left, iv) - put(s, kl, t_left, iv)
                if val <= credit * (1 - TP):
                    pnl = credit * TP
                    tp += 1
                    break
                if val >= credit * SL:
                    pnl = -credit * (SL - 1)
                    sl += 1
                    break
            if pnl is None:
                s = closes[i + days] * scale
                settle = max(0.0, min(width, ks - s))
                pnl = credit - settle
            out.append(pnl)

        n = len(out)
        wins = sum(1 for p in out if p > 0)
        exp = sum(out) / n
        print(f"{sym:5} {label:26} {credit*100:6.0f} {risk:6.0f} "
              f"{credit*100/risk:5.0%} {ks/spot-1:+7.1%} {100*wins/n:5.0f}% "
              f"{100*tp/n:4.0f}% {100*sl/n:5.0f}% {exp*100:+7.0f} "
              f"{100*exp*100/risk:+5.0f}% {n:5d}")

    print()
    print(f"Rules: close at +{TP:.0%} of credit, abort when the spread costs {SL:.0f}x the credit.")
    print("exp% is expectancy against capital at risk. IV constant -- a real selloff would")
    print("expand vol and make the stop fire harder than this shows.")


if __name__ == "__main__":
    main()
