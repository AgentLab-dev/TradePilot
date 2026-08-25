#!/usr/bin/env python3
"""Run STKK levels from the local cache (../market_history.md) — no network.

Reads the cached daily OHLCV CSV blocks, computes regime / SMA20-50-200 / RSI14 /
ATR14 / annualized vol / beta-vs-SPY / entry / stop / target / R:R, and prints a
table ranked by R:R. Beta uses SPY from the same cache.

Usage:
  python3 stkk_from_cache.py                  # core actionable set
  python3 stkk_from_cache.py HOOD NNE NTAP    # specific tickers
  python3 stkk_from_cache.py --all            # every cached ticker
  python3 stkk_from_cache.py --live HOOD=93.2 NNE=23.6   # override price w/ live quote

Pass live prices (from get_equity_quotes) via --live SYM=PRICE to recompute %abv
against the current print; otherwise the cached last close is used as price.
"""
import os, sys, re, math

MD = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "..", "market_history.md"))
CORE = ["HOOD", "NNE", "ORCL", "NTAP", "CRWV", "TLN", "MARA", "IREN"]
ANALYST = {"TLN": 473, "CRWV": 140, "NTAP": 172, "ORCL": 255, "HOOD": 100, "NNE": 40,
           "MARA": 16.3, "IREN": 96, "ASML": 1701, "INTC": 93, "MU": 739,
           "AVGO": 490, "SNOW": 291, "DDOG": 232, "ZS": 200, "VEEV": 235, "MNDY": 124.59,
           "NOW": 1150, "AMZN": 265, "META": 825, "CRWD": 520, "ANET": 188, "ECG": 169.6,
           "TGTX": 55, "GOOGL": 420}

def load():
    txt = open(MD).read()
    data = {}
    for m in re.finditer(r"\n## ([A-Z0-9.]+)\n.*?```csv\n(.*?)\n```", txt, re.S):
        sym = m.group(1)
        rows = []
        for line in m.group(2).splitlines()[1:]:  # skip header
            p = line.split(",")
            if len(p) < 6:
                continue
            rows.append((p[0], float(p[1]), float(p[2]), float(p[3]), float(p[4]), int(p[5])))
        data[sym] = rows
    return data

def sma(c, n): return sum(c[-n:]) / n if len(c) >= n else None
def rsi(c, n=14):
    if len(c) < n + 1: return None
    g = l = 0.0
    for i in range(-n, 0):
        d = c[i] - c[i - 1]
        g += d if d > 0 else 0
        l += -d if d < 0 else 0
    if l == 0: return 100.0
    rs = (g / n) / (l / n)
    return 100 - 100 / (1 + rs)
def atr(rows, n=14):
    if len(rows) < n + 1: return None
    trs = []
    for i in range(-n, 0):
        h, lo, pc = rows[i][2], rows[i][3], rows[i - 1][4]
        trs.append(max(h - lo, abs(h - pc), abs(lo - pc)))
    return sum(trs) / n

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    live = {}
    for a in sys.argv[1:]:
        if "=" in a:
            k, v = a.split("=", 1)
            if v.strip():
                live[k.upper().lstrip("-")] = float(v)
    data = load()
    spy = [r[4] for r in data.get("SPY", [])]
    spy_ret = [spy[i] / spy[i - 1] - 1 for i in range(1, len(spy))] if spy else []

    if "--all" in sys.argv:
        syms = [s for s in data if s != "SPY"]
    else:
        syms = [a.upper() for a in args if "=" not in a] or CORE

    out = []
    for s in syms:
        rows = data.get(s)
        if not rows or len(rows) < 60:
            out.append((s, None)); continue
        c = [r[4] for r in rows]
        px = live.get(s, c[-1])
        s20, s50, s200 = sma(c, 20), sma(c, 50), sma(c, 200)
        a, rs = atr(rows), rsi(c)
        ret = [c[i] / c[i - 1] - 1 for i in range(1, len(c))]
        n = min(len(ret), len(spy_ret), 252)
        beta = vol = None
        if n > 30:
            rr, sp = ret[-n:], spy_ret[-n:]
            mx, my = sum(sp) / n, sum(rr) / n
            cov = sum((sp[i] - mx) * (rr[i] - my) for i in range(n)) / n
            var = sum((sp[i] - mx) ** 2 for i in range(n)) / n
            beta = cov / var if var else None
            vol = (sum((x - my) ** 2 for x in rr) / n) ** 0.5 * math.sqrt(252)
        if s200 and px > s50 > s200: regime = "UP"
        elif s200 and px < s50 < s200: regime = "DOWN"
        else: regime = "RANGE"
        low60 = min(r[3] for r in rows[-60:])
        high120 = max(r[2] for r in rows[-120:])
        entry = max(s20, low60) if regime == "UP" else min(px, max(low60, (s20 or px) * 0.99))
        k = 2.5 if ((vol and vol > 0.5) or (beta and beta > 2)) else 2.0
        stop = min(entry - k * a, low60)
        stop = min(stop, entry - max(1.0 * a, 0.03 * entry))  # guard: >=1ATR/3% below
        tgt = high120
        rr_ratio = (tgt - entry) / (entry - stop) if (entry - stop) > 0 else None
        pabv = (px / entry - 1) * 100
        out.append((s, dict(regime=regime, px=px, rsi=rs, beta=beta, vol=vol, entry=entry,
                            stop=stop, tgt=tgt, rr=rr_ratio, pabv=pabv, an=ANALYST.get(s),
                            live=s in live, last=rows[-1][0])))
    out.sort(key=lambda o: -(o[1]["rr"] if o[1] and o[1]["rr"] is not None else -999))
    print(f"STKK from cache ({MD.split('/')[-1]}) — '*' = live price, else cached close\n")
    print(f"{'Tk':5}{'Reg':6}{'Price':>9}{'Entry':>9}{'Stop':>9}{'Target':>9}"
          f"{'R:R':>7}{'%abv':>7}{'RSI':>5}{'Beta':>6}{'Vol':>6}  Analyst")
    for s, d in out:
        if not d:
            print(f"{s:5} (insufficient cached history)"); continue
        star = "*" if d["live"] else " "
        print(f"{s:5}{d['regime']:6}{d['px']:>8.2f}{star}{d['entry']:>9.2f}{d['stop']:>9.2f}"
              f"{d['tgt']:>9.2f}{(d['rr'] or 0):>7.2f}{d['pabv']:>7.1f}{(d['rsi'] or 0):>5.0f}"
              f"{(d['beta'] or 0):>6.2f}{(d['vol'] or 0) * 100:>5.0f}%  "
              f"mean ${d['an']}" if d['an'] else
              f"{s:5}{d['regime']:6}{d['px']:>8.2f}{star}{d['entry']:>9.2f}{d['stop']:>9.2f}"
              f"{d['tgt']:>9.2f}{(d['rr'] or 0):>7.2f}{d['pabv']:>7.1f}{(d['rsi'] or 0):>5.0f}"
              f"{(d['beta'] or 0):>6.2f}{(d['vol'] or 0) * 100:>5.0f}%")
    print(f"\ncache last bar: {out[0][1]['last'] if out and out[0][1] else '?'} "
          "(re-pull if older than prior trading day)")

if __name__ == "__main__":
    main()
