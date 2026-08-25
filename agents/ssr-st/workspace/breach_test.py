#!/usr/bin/env python3
"""Breach backtest for defined-risk option structures.

Answers the only question that matters for a credit spread: over the recent
past, how often would the underlying have moved through the short strike
before expiry?

Usage:
  python3 breach_test.py <historicals_dump.json> ...

Reads the CANDIDATES table below. For each candidate it walks every
overlapping N-week window in the loaded history and reports:
  - breach%  : share of windows where the move exceeded the cushion
  - worst    : worst move over any window (the tail that actually hurts)
  - last10   : worst move over windows starting in the last 10 weeks

Direction 'down' = short put (we lose if price falls through the strike).
Direction 'up'   = long call debit (we need price above breakeven).
"""
import json, sys
from datetime import datetime

# The Mon Aug 10 six. name, spot, level (strike or breakeven), direction,
# weeks to expiry, label. Spots are the Fri Aug 7 close.
CANDIDATES = [
    ("MPC",  298.20,  270.0, "down", 6, "Sep18 $270/$260 put credit"),
    ("MS",   216.25,  200.0, "down", 6, "Sep18 $200/$195 put credit"),
    ("HPE",   53.22,   48.0, "down", 2, "Aug21 $48/$45 put credit"),
    ("DELL", 453.775, 410.0, "down", 2, "Aug21 $410/$400 put credit"),
    ("LLY", 1185.335, 1221.4, "up",  6, "Sep18 $1200/$1250 call debit"),
    ("NVDA", 223.90,  205.0, "down", 2, "Aug21 $205/$195 put credit"),
    # benchmark / rejected — kept so the comparison stays visible
    ("VLO",  298.31,  270.0, "down", 6, "Sep18 $270/$260 put credit (alt to MPC)"),
    ("ORCL", 146.935, 135.0, "down", 2, "Aug21 $135/$130 — DISQUALIFIED"),
    ("CEG",  269.98,  240.0, "down", 6, "Sep18 $240/$230 — DISQUALIFIED"),
    ("CCJ",   97.39,   87.0, "down", 6, "Sep18 ~$87 — nuclear, FAILS"),
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
        d = json.load(open(f))
        for r in d["data"]["results"]:
            bucket = by_symbol.setdefault(r["symbol"], {})
            for b in r.get("bars", []):
                if b.get("interpolated"):
                    continue
                t = bar_time(b)
                if t:
                    bucket[t] = b
    return {s: [b[t] for t in sorted(b)] for s, b in by_symbol.items()}


# name, spot, weeks, kind, short/long strike, credit-or-debit, label.
# Premium = the realistic fill (Robinhood high/low fill-rate prices), NOT the
# mark — the mark overstates what a marketable limit actually gets on a spread.
PNL = [
    ("MPC",  298.20,  6, "put_credit",  270, 260, 1.90, "Sep18 $270/$260 @ $1.90"),
    ("MS",   216.25,  6, "put_credit",  200, 195, 0.87, "Sep18 $200/$195 @ $0.87"),
    ("HPE",   53.22,  2, "put_credit",   48,  45, 0.445, "Aug21 $48/$45 @ $0.445"),
    ("DELL", 453.775, 2, "put_credit",  410, 400, 1.88, "Aug21 $410/$400 @ $1.88"),
    ("LLY", 1185.335, 6, "call_debit", 1200, 1250, 21.38, "Sep18 1200/1250 @ 21.38 LIMIT"),
    ("LLY", 1185.335, 6, "call_debit", 1200, 1250, 25.85, "Sep18 1200/1250 @ 25.85 ASK"),
    ("LLY", 1185.335, 6, "call_debit", 1200, 1250, 19.00, "Sep18 1200/1250 @ 19.00 MARK"),
    ("NVDA", 223.90,  2, "put_credit",  205, 195, 0.485, "Aug21 $205/$195 @ $0.485"),
    ("VLO",  298.31,  6, "put_credit",  270, 260, 1.34, "Sep18 $270/$260 @ $1.34"),
]


def expectancy(series):
    """Hold-to-expiry P&L distribution over every overlapping window.

    No abort/close-stop applied, so the loss tail here is worse than live —
    the book's abort rule truncates it. Treat as a conservative floor.
    """
    print()
    print(f"{'SYMBOL':6} {'STRUCTURE':30} {'N':>4} {'win%':>6} {'avgW$':>8} "
          f"{'avgL$':>8} {'exp$':>8} {'$/$1k':>8}")
    for sym, spot, weeks, kind, k1, k2, prem, label in PNL:
        bars = series.get(sym)
        if not bars:
            continue
        closes = [float(b["close_price"]) for b in bars]
        pnls = []
        for i in range(len(closes) - weeks):
            st = spot * (closes[i + weeks] / closes[i])
            if kind == "put_credit":
                width = k1 - k2
                intrinsic = max(0.0, min(k1 - st, width))
                pnl = (prem - intrinsic) * 100
                risk = (width - prem) * 100
            else:
                intrinsic = max(0.0, min(st, k2) - k1)
                pnl = (intrinsic - prem) * 100
                risk = prem * 100
            pnls.append(pnl)
        if not pnls:
            continue
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]
        exp = sum(pnls) / len(pnls)
        aw = sum(wins) / len(wins) if wins else 0
        al = sum(losses) / len(losses) if losses else 0
        print(f"{sym:6} {label:30} {len(pnls):4d} {100*len(wins)/len(pnls):6.0f} "
              f"{aw:8.0f} {al:8.0f} {exp:8.0f} {1000*exp/risk:8.0f}")


def main():
    series = load(sys.argv[1:])
    print(f"{'SYMBOL':6} {'STRUCTURE':32} {'cush%':>7} {'N':>4} {'endpt%':>8} "
          f"{'TOUCH%':>8} {'worst%':>8} {'last10 worst%':>14}  verdict")
    for sym, spot, level, direction, weeks, label in CANDIDATES:
        bars = series.get(sym)
        if not bars:
            print(f"{sym:6} {label:32}   no data")
            continue
        closes = [float(b["close_price"]) for b in bars]
        cushion = (level / spot - 1) * 100

        moves = []
        for i in range(len(closes) - weeks):
            moves.append((closes[i + weeks] / closes[i] - 1) * 100)
        if not moves:
            continue

        # Both structures are hurt by the underlying FALLING, so the adverse
        # tail is min(moves) either way. Reporting max(moves) for 'up' was a
        # bug: it printed the best case under a column headed "worst".
        worst = min(moves)
        last10 = min(moves[-10:])
        if direction == "down":
            breaches = [m for m in moves if m <= cushion]
        else:
            breaches = [m for m in moves if m < cushion]

        # Endpoint-only breach is not what a live book experiences. The abort
        # rule fires the moment the underlying trades through the short strike,
        # so what matters is whether price EVER touched the level inside the
        # window — not where it happened to close on expiry day. MPC fell 15.2%
        # in 3 weeks in April and recovered by week 6: endpoint says -2.8%, the
        # abort rule says stopped out.
        # Only meaningful for credit spreads, where there is a short strike an
        # abort rule can be triggered through. A debit spread has no such level.
        if direction == "down":
            touches = 0
            for i in range(len(closes) - weeks):
                path = closes[i:i + weeks + 1]
                excursion = (min(path) / closes[i] - 1) * 100
                if excursion <= cushion:
                    touches += 1
            touch_rate = 100 * touches / len(moves)
        else:
            touch_rate = float("nan")

        rate = 100 * len(breaches) / len(moves)
        if direction == "down":
            ok = rate <= 10 and worst > cushion * 1.5
        else:
            ok = rate <= 60
        verdict = "PASS" if ok else ("MARGINAL" if rate <= 20 else "FAIL")
        if touch_rate > max(rate, 10):
            verdict += f" !PATH({touch_rate:.0f}%)"
        print(f"{sym:6} {label:32} {cushion:7.1f} {len(moves):4d} {rate:8.0f} "
              f"{touch_rate:8.0f} {worst:8.1f} {last10:14.1f}  {verdict}")
    expectancy(series)


if __name__ == "__main__":
    main()
