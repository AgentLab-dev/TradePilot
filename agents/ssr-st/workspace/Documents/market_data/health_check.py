#!/usr/bin/env python3
"""Health Check — the full 4-model composite in one call.

Runs all four trading models on each ticker and prints 4 flags + a single
VERDICT per name:

  1. STKK        — chart/technical (regime, RSI, R:R, level)      [from cache]
  2. STNOW       — 360° quant proxy (trend + analyst + flow +     [cache + whale]
                   value-trap gate). News (N) lens = manual.
  3. Three Good  — put-credit-spread eligibility (IV >= 50% &      [whale IV]
                   whale flow >= 0 & not in active breakdown)
  4. Whale Check — institutional options flow + IV/skew           [live Nasdaq]

STKK + analyst come from the local cache (../market_history.md); Whale Check
hits the live Nasdaq option chain. STNOW here is a transparent quant proxy of
the full 7-lens model — it reproduces the value-trap gate but still wants a
live news/catalyst read before you act (flagged as "news: manual").

Usage:
  python3 health_check.py MARA HOOD ORCL SNOW MNDY
  python3 health_check.py AVGO --to 2026-09-30
  python3 health_check.py HOOD --live HOOD=109.4      # override cache price
"""
import os, sys, io, contextlib, datetime as dt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stkk_from_cache as stk
import whale_check as wc


# ---------- STKK (replicates stk.main per-symbol, returns a dict) ----------
def compute_stkk(sym, data, spy_ret, live):
    rows = data.get(sym)
    if not rows or len(rows) < 60:
        return None
    c = [r[4] for r in rows]
    px = live.get(sym, c[-1])
    s20, s50, s200 = stk.sma(c, 20), stk.sma(c, 50), stk.sma(c, 200)
    a, rs = stk.atr(rows), stk.rsi(c)
    ret = [c[i] / c[i - 1] - 1 for i in range(1, len(c))]
    n = min(len(ret), len(spy_ret), 252)
    beta = vol = None
    if n > 30:
        rr, sp = ret[-n:], spy_ret[-n:]
        mx, my = sum(sp) / n, sum(rr) / n
        cov = sum((sp[i] - mx) * (rr[i] - my) for i in range(n)) / n
        var = sum((sp[i] - mx) ** 2 for i in range(n)) / n
        beta = cov / var if var else None
        vol = (sum((x - my) ** 2 for x in rr) / n) ** 0.5 * (252 ** 0.5)
    if s200 and px > s50 > s200: regime = "UP"
    elif s200 and px < s50 < s200: regime = "DOWN"
    else: regime = "RANGE"
    low60 = min(r[3] for r in rows[-60:])
    high120 = max(r[2] for r in rows[-120:])
    entry = max(s20, low60) if regime == "UP" else min(px, max(low60, (s20 or px) * 0.99))
    k = 2.5 if ((vol and vol > 0.5) or (beta and beta > 2)) else 2.0
    stop = min(entry - k * a, low60)
    stop = min(stop, entry - max(1.0 * a, 0.03 * entry))
    tgt = high120
    rr_ratio = (tgt - entry) / (entry - stop) if (entry - stop) > 0 else None
    pabv = (px / entry - 1) * 100
    an = stk.ANALYST.get(sym)
    upside = ((an / px - 1) * 100) if an else None
    return dict(regime=regime, px=px, rsi=rs, beta=beta, vol=vol, entry=entry,
                stop=stop, tgt=tgt, rr=rr_ratio, pabv=pabv, an=an, upside=upside,
                s200=s200, last=rows[-1][0])


# ---------- flags ----------
def stkk_flag(d):
    if d["regime"] == "UP":
        return ("🟢", "UP trend, room") if (d["rr"] or 0) >= 1.5 else ("🟡", "UP, thin R:R")
    if d["regime"] == "DOWN":
        return ("🟡", "DOWN, oversold") if (d["rsi"] or 50) < 35 else ("🔴", "DOWN trend")
    if d["pabv"] > 15:
        return ("🟡", "RANGE, extended")
    return ("🟡", "RANGE")


def stnow_eval(d, w):
    """Transparent quant proxy of the 7-lens STNOW + Step-0.5 value-trap gate."""
    # trend lens
    t = {"UP": 2, "RANGE": 0, "DOWN": -2}[d["regime"]]
    if (d["rsi"] or 50) < 35: t += 1
    elif (d["rsi"] or 50) > 70: t -= 1
    # analyst lens (capped at +2 so deep-discount value traps don't inflate)
    up = d["upside"]
    if up is None: a = 0
    elif up > 25: a = 2
    elif up >= 10: a = 1
    elif up >= 0: a = 0
    else: a = -1
    # whale lens
    ws = (w or {}).get("score", 0)
    raw = t + a + ws
    # Step 0.5 — value-trap gate: deep discount + falling + below 200DMA, reason unconfirmed
    value_trap = (d["regime"] == "DOWN" and (up or 0) > 40
                  and d.get("s200") and d["px"] < d["s200"])
    return dict(t=t, a=a, w=ws, raw=raw, value_trap=value_trap)


def stnow_flag(sn):
    if sn["value_trap"]:
        return ("🔴", f"TRAP raw{sn['raw']:+d}")
    if sn["raw"] < 0:
        return ("🔴", f"raw{sn['raw']:+d}")
    if sn["raw"] >= 5:
        return ("🟢", f"STRONG raw{sn['raw']:+d}")
    if sn["raw"] >= 2:
        return ("🟢", f"GO raw{sn['raw']:+d}")
    return ("🟡", f"raw{sn['raw']:+d}")


def three_good_flag(d, w):
    iv = (w or {}).get("atm_iv")
    ws = (w or {}).get("score", 0)
    if iv is None:
        return ("⚪", "IV n/a")
    if iv < 0.50:
        return ("❌", f"IV {iv*100:.0f}% <50%")
    if ws < 0:
        return ("❌", "flow bearish")
    if d["regime"] == "DOWN":
        return ("⚠️", "IV ok, sell at support")
    return ("✅", f"IV {iv*100:.0f}%, flow ok")


def direction(d, w, sn):
    """Directional bias from chart regime + STNOW composite + whale flow.
    Returns 'bullish' | 'bearish' | 'range'."""
    ws = (w or {}).get("score", 0)
    raw = sn["raw"]
    regime = d["regime"]
    if regime == "DOWN" or raw < 0 or ws <= -2:
        return "bearish"
    if regime == "UP" or (raw >= 2 and ws >= 0):
        return "bullish"
    return "range"


def structure(d, w, sn):
    """FULL IV × direction routing matrix — consider ALL SIX structures, never
    default to put-credit. This is the "route through every strategy" rule.

    direction (STKK regime + STNOW + whale) × IV bucket (>=50% rich / <50% cheap):
        bullish + cheap IV  → call debit spread    (buy the move; theta small)
        bullish + rich IV   → put credit spread    (get paid; IV-crush + theta tailwind)
        bearish + rich IV   → call credit spread   (sell into weakness; defined risk)
        bearish + cheap IV  → put debit spread     (buy downside cheap)
        range   + rich IV   → iron condor          (sell both wings; IV-crush)
        range   + cheap IV  → calendar / stand-down (long theta only if pinned)
    """
    iv = (w or {}).get("atm_iv")
    if iv is None:
        return "shares / no-options (IV n/a)"
    rich = iv >= 0.50
    dirn = direction(d, w, sn)
    if dirn == "bullish":
        return "put credit spread (rich IV → sell)" if rich else "call debit spread (cheap IV → buy)"
    if dirn == "bearish":
        return ("call credit spread (rich IV → sell into weakness)" if rich
                else "put debit spread (cheap IV → buy downside)")
    return ("iron condor (rich IV → sell both wings)" if rich
            else "calendar / stand-down (cheap IV, pinned range)")


def verdict(d, w, sn):
    ws = (w or {}).get("score", 0)
    s = structure(d, w, sn)
    if sn["value_trap"]:
        return "🔴 WAIT — value-trap gate (needs live news to clear)"
    if ws < 0 or sn["raw"] < 0:
        return "🔴 AVOID/WAIT — flow or thesis against"
    if d["pabv"] > 15 or (d["rsi"] or 0) > 68:
        return f"🟢 GO on pullback — extended, don't chase ({s} on the dip)"
    if d["regime"] == "UP" and (d["rr"] or 9) < 0.5:
        return f"🟢 GO — {s} (limited chart upside)"
    if sn["raw"] >= 5 and ws >= 1:
        return f"🟢 STRONG GO ({s})"
    if sn["raw"] >= 2:
        return f"🟢 GO-on-confirmation ({s})"
    return "🟡 NEUTRAL — wait for chart trigger"


def main():
    spot = to = frm = None
    args, live, skip = [], {}, False
    argv = sys.argv[1:]
    for i, a in enumerate(argv):
        if skip:
            skip = False; continue
        if a == "--to": to = argv[i + 1]; skip = True
        elif a == "--from": frm = argv[i + 1]; skip = True
        elif a == "--live": skip = True; continue  # handled below
        elif "=" in a:
            k, v = a.split("="); live[k.upper()] = float(v)
        elif a.startswith("--"): continue
        else: args.append(a.upper())
    if not args:
        print("usage: python3 health_check.py TICKER [TICKER...] [--to YYYY-MM-DD] [--live SYM=PX]")
        return

    data = stk.load()
    spy = [r[4] for r in data.get("SPY", [])]
    spy_ret = [spy[i] / spy[i - 1] - 1 for i in range(1, len(spy))] if spy else []

    rows_out = []
    for sym in args:
        d = compute_stkk(sym, data, spy_ret, live)
        if not d:
            rows_out.append((sym, None, None, None)); continue
        with contextlib.redirect_stdout(io.StringIO()):   # silence whale_check's report
            w = wc.whale_check(sym, spot=live.get(sym), to=to)
        sn = stnow_eval(d, w)
        rows_out.append((sym, d, w, sn))

    W = 150
    print(f"\n{'='*W}")
    print("HEALTH CHECK — full 4-model composite")
    print(f"cache last bar: {next((d['last'] for _,d,_,_ in rows_out if d), '?')}"
          f"   |   whale = live Nasdaq chain   |   {dt.date.today()}")
    print('='*W)
    # 7 columns: Name | Price | STKK (chart) | STNOW (360°) | Three Good (put-sell) | Whale Check | VERDICT
    hdr = (f"{'Name':6}{'Price':>9}   {'STKK (chart)':20}{'STNOW (360°)':20}"
           f"{'Three Good (put-sell)':26}{'Whale Check':16}{'VERDICT'}")
    print(hdr); print('-'*W)
    for sym, d, w, sn in rows_out:
        if not d:
            print(f"{sym:6}  (insufficient cached history / no chain)"); continue
        sf, st = stkk_flag(d)
        nf, nt = stnow_flag(sn)
        tf, tt = three_good_flag(d, w)
        wflag = (w or {}).get("flag", "n/a")
        v = verdict(d, w, sn)
        print(f"{sym:6}{d['px']:>9.2f}   {sf+' '+st:20}{nf+' '+nt:20}"
              f"{tf+' '+tt:26}{wflag:16}{v}")
    print('-'*W)
    print("CONTEXT (numbers behind the flags):")
    for sym, d, w, sn in rows_out:
        if not d: continue
        em = (w or {}).get("em"); iv = (w or {}).get("atm_iv")
        extra = [f"STNOW T{sn['t']:+d}/A{sn['a']:+d}/W{sn['w']:+d}"]
        if d.get("upside") is not None: extra.append(f"{d['upside']:+.0f}% to mean ${d['an']}")
        if iv: extra.append(f"IV {iv*100:.0f}%")
        if em and d['px']: extra.append(f"EM ±{em/d['px']*100:.0f}%")
        extra.append(f"R:R {d['rr']:.2f}" if d.get('rr') is not None else "R:R n/a")
        extra.append(f"RSI {d['rsi']:.0f}, {d['regime']}")
        print(f"  {sym:6} {'; '.join(extra)}")
    print("\nNote: STNOW news/catalyst (N) lens is NOT automated — confirm live news before entry.")
    print("      Whale uses prior-session volume; OI is T+1. Re-run at the open for fresh marks.")


if __name__ == "__main__":
    main()
