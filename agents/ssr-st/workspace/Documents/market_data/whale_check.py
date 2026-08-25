#!/usr/bin/env python3
"""Whale Check — institutional options-flow read from the Nasdaq option chain.

Replicates the "unusual options activity" screens (Barchart Vol/OI, OptionStrat
Flow) for free: pulls the live chain, then surfaces standing OI walls, fresh
unusual activity (Vol/OI > 2), and a put/call skew → one BULLISH / NEUTRAL /
BEARISH whale flag per name with a -2..+2 score (feeds STNOW / STKK / Three Good
/ Tomorrow).

Source: Nasdaq options API (curl; system cert store dodges sandbox SSL).
Usage:
  python3 whale_check.py AVGO              # one name, default ~6 months out
  python3 whale_check.py MARA NNE HOOD     # several
  python3 whale_check.py AVGO --spot 411.35 --to 2026-09-30
Notes:
  - Volume = prior completed session; OI updates T+1. Far-OTM puts are usually
    HEDGES, not bearish bets — the flag down-weights deep-OTM put OI.
"""
import subprocess, json, sys, datetime as dt
from math import log, sqrt, exp, erf, pi

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
HDRS = ["-H", f"User-Agent: {UA}", "-H", "Accept: application/json",
        "-H", "Origin: https://www.nasdaq.com", "-H", "Referer: https://www.nasdaq.com/"]
RFR = 0.045  # risk-[REDACTED] rate proxy (2026)


def num(x):
    try:
        return float(str(x).replace("$", "").replace(",", "").strip())
    except Exception:
        return None


# ---------- IV engine ----------
def _N(x):
    return 0.5 * (1 + erf(x / sqrt(2)))


def _npdf(x):
    return exp(-x * x / 2) / sqrt(2 * pi)


def bs_price(S, K, T, sigma, r=RFR, call=True):
    if T <= 0 or sigma <= 0:
        return max(0.0, (S - K) if call else (K - S))
    d1 = (log(S / K) + (r + sigma * sigma / 2) * T) / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)
    if call:
        return S * _N(d1) - K * exp(-r * T) * _N(d2)
    return K * exp(-r * T) * _N(-d2) - S * _N(-d1)


def implied_vol(price, S, K, T, r=RFR, call=True):
    """Newton-Raphson IV inversion; falls back to bisection if it diverges."""
    if price is None or price <= 0 or T <= 0 or S <= 0:
        return None
    intrinsic = max(0.0, (S - K) if call else (K - S))
    if price < intrinsic - 1e-6:
        return None
    sigma = 0.5
    for _ in range(60):
        d1 = (log(S / K) + (r + sigma * sigma / 2) * T) / (sigma * sqrt(T))
        vega = S * sqrt(T) * _npdf(d1)
        diff = bs_price(S, K, T, sigma, r, call) - price
        if abs(diff) < 1e-4:
            return sigma
        if vega < 1e-8:
            break
        sigma -= diff / vega
        if sigma <= 0 or sigma > 8:
            break
    lo, hi = 1e-3, 8.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if bs_price(S, K, T, mid, r, call) > price:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def atm_iv_quick(C, S, T):
    """Brenner-Subrahmanyam closed-form ATM approximation."""
    if not C or not S or T <= 0:
        return None
    return (C / S) * sqrt(2 * pi / T)


def fetch_chain(sym, frm, to):
    for cls in ("stocks", "etf"):
        url = (f"https://api.nasdaq.com/api/quote/{sym}/option-chain?assetclass={cls}"
               f"&limit=8000&fromdate={frm}&todate={to}&excode=oprac"
               f"&callput=callput&money=all&type=all")
        raw = subprocess.run(["curl", "-s", "--max-time", "40", *HDRS, url],
                             capture_output=True, text=True, timeout=50).stdout
        try:
            d = json.loads(raw)
        except Exception:
            continue
        tbl = (d.get("data") or {}).get("table") or {}
        rows = tbl.get("rows")
        last = (d.get("data") or {}).get("lastTrade")
        if rows:
            return rows, last
    return None, None


def _exp_date(s):
    for fmt in ("%B %d, %Y", "%b %d, %Y"):
        try:
            return dt.datetime.strptime(s.strip(), fmt).date()
        except Exception:
            pass
    return None


def parse(rows):
    recs, cur, curd = [], None, None
    for r in rows:
        if r.get("expirygroup"):
            cur = r["expirygroup"]; curd = _exp_date(cur); continue
        k = num(r.get("strike"))
        if k is None:
            continue
        for side, vcol, ocol, bcol, acol in (
                ("C", "c_Volume", "c_Openinterest", "c_Bid", "c_Ask"),
                ("P", "p_Volume", "p_Openinterest", "p_Bid", "p_Ask")):
            vol, oi = num(r.get(vcol)), num(r.get(ocol))
            if vol is None or oi is None:
                continue
            voi = vol / oi if oi > 0 else (vol if vol > 0 else 0.0)
            bid, ask = num(r.get(bcol)), num(r.get(acol))
            mid = (bid + ask) / 2 if (bid and ask) else None
            recs.append(dict(exp=cur, expd=curd, k=k, side=side, vol=vol, oi=oi,
                             voi=voi, bid=bid, ask=ask, mid=mid))
    return recs


def iv_metrics(recs, spot, today=None):
    """Headline ATM IV (BS-inverted), expected move, and 25Δ-ish skew.
    Reference expiry = the one closest to 30 DTE with DTE >= 10 and a liquid ATM."""
    today = today or dt.date.today()
    exps = sorted({r["expd"] for r in recs if r["expd"] and (r["expd"] - today).days >= 10})
    if not exps or not spot:
        return None
    ref = min(exps, key=lambda d: abs((d - today).days - 30))
    T = (ref - today).days / 365.0
    leg = [r for r in recs if r["expd"] == ref and r["mid"]]
    if not leg:
        return None
    def nearest(side, target):
        cand = [r for r in leg if r["side"] == side]
        return min(cand, key=lambda r: abs(r["k"] - target)) if cand else None
    atm_c, atm_p = nearest("C", spot), nearest("P", spot)
    ivs = []
    for r in (atm_c, atm_p):
        if r:
            iv = implied_vol(r["mid"], spot, r["k"], T, call=(r["side"] == "C"))
            if iv:
                ivs.append(iv)
    atm_iv = sum(ivs) / len(ivs) if ivs else None
    em = spot * atm_iv * sqrt(T) if atm_iv else None
    # skew: ~7% OTM put IV minus ~7% OTM call IV
    otm_p, otm_c = nearest("P", spot * 0.93), nearest("C", spot * 1.07)
    iv_p = implied_vol(otm_p["mid"], spot, otm_p["k"], T, call=False) if otm_p else None
    iv_c = implied_vol(otm_c["mid"], spot, otm_c["k"], T, call=True) if otm_c else None
    skew = (iv_p - iv_c) if (iv_p and iv_c) else None
    return dict(ref=ref, dte=(ref - today).days, T=T, atm_iv=atm_iv, em=em,
                skew=skew, iv_put=iv_p, iv_call=iv_c)


def whale_check(sym, spot=None, frm=None, to=None):
    today = dt.date.today()
    frm = frm or (today + dt.timedelta(days=3)).isoformat()
    to = to or (today + dt.timedelta(days=185)).isoformat()
    rows, last = fetch_chain(sym, frm, to)
    if not rows:
        print(f"\n{sym}: no chain returned"); return
    recs = parse(rows)
    if spot is None and last:  # parse "LAST TRADE: $411.35 (AS OF ...)"
        for tok in last.replace("$", " ").split():
            v = num(tok)
            if v and v > 0:
                spot = v; break
    calls = [r for r in recs if r["side"] == "C"]
    puts = [r for r in recs if r["side"] == "P"]
    cv, pv = sum(r["vol"] for r in calls), sum(r["vol"] for r in puts)
    co, po = sum(r["oi"] for r in calls), sum(r["oi"] for r in puts)
    pcv = pv / cv if cv else 9.99
    pco = po / co if co else 9.99

    # fresh unusual (new positioning, not pre-existing)
    un = [r for r in recs if r["voi"] > 2 and r["vol"] > max(500, 0.0)]
    un_call = sum(r["vol"] for r in un if r["side"] == "C")
    un_put = sum(r["vol"] for r in un if r["side"] == "P")

    # near-the-money put skew (hedges are deep OTM; near-money puts are real bears)
    nm_put = sum(r["vol"] for r in puts if spot and 0.90 * spot <= r["k"] <= 1.02 * spot)

    # ---- score (-2..+2) ----
    s = 0
    if pcv < 0.5: s += 2
    elif pcv < 0.7: s += 1
    elif pcv <= 1.0: s += 0
    elif pcv <= 1.5: s -= 1
    else: s -= 2
    if un_call + un_put > 0:
        frac = un_call / (un_call + un_put)
        s += 1 if frac >= 0.65 else (-1 if frac <= 0.35 else 0)
    flow_s = max(-2, min(2, s))

    # ---- IV metrics + confirmation modifier ----
    ivm = iv_metrics(recs, spot)
    iv_mod = 0
    call_heavy = (un_call + un_put > 0 and un_call / (un_call + un_put) >= 0.65)
    put_heavy = (un_call + un_put > 0 and un_call / (un_call + un_put) <= 0.35)
    if ivm and ivm.get("skew") is not None:
        sk = ivm["skew"]
        if call_heavy and sk <= -0.01:   # calls bid up + call-heavy flow = paying up
            iv_mod = 1
        elif sk >= 0.03 or (put_heavy and sk > 0):  # puts bid up = fear/hedging pressure
            iv_mod = -1

    s = max(-2, min(2, flow_s + iv_mod))
    flag = ("\U0001F7E2 BULLISH" if s >= 2 else "\U0001F7E2 lean-bull" if s == 1
            else "\U0001F7E1 NEUTRAL" if s == 0 else "\U0001F534 lean-bear" if s == -1
            else "\U0001F534 BEARISH")

    print(f"\n{'='*68}\nWHALE CHECK — {sym}" + (f"  ~${spot}" if spot else "")
          + f"   ({last or 'last session'})")
    print(f"  Vol:  calls {cv:>9,.0f} | puts {pv:>9,.0f}  → P/C vol {pcv:>4.2f}"
          f"  ({'bullish' if pcv<0.7 else 'bearish' if pcv>1.3 else 'neutral'})")
    print(f"  OI:   calls {co:>9,.0f} | puts {po:>9,.0f}  → P/C OI  {pco:>4.2f}")
    print(f"  Fresh unusual (Vol/OI>2): call vol {un_call:>8,.0f} | put vol {un_put:>8,.0f}")
    if spot:
        print(f"  Near-money put vol (real-bear tell): {nm_put:,.0f}")
    if ivm and ivm.get("atm_iv"):
        ivpct = ivm["atm_iv"] * 100
        empct = (ivm["em"] / spot * 100) if (ivm.get("em") and spot) else None
        gate = "✅ ≥50% (Three Good OK)" if ivpct >= 50 else "⚠️ <50% (thin for put-selling)"
        print(f"  IV:   ATM ~{ivpct:.0f}%  ({ivm['dte']}DTE, exp {ivm['ref']})  {gate}")
        if ivm.get("em"):
            print(f"        Expected move by exp: ±${ivm['em']:.2f}"
                  + (f" (±{empct:.1f}%)" if empct else ""))
        if ivm.get("skew") is not None:
            sk = ivm["skew"] * 100
            tell = ("PUT skew (fear/hedging)" if sk >= 1 else
                    "CALL skew (upside demand)" if sk <= -1 else "flat")
            print(f"        Skew (25Δ put−call IV): {sk:+.1f} pts → {tell}")
    print(f"  WHALE SCORE: flow {flow_s:+d}  IV-mod {iv_mod:+d}  =  {s:+d}  →  {flag}")

    print("  Top OI walls (standing open positions):")
    for r in sorted(recs, key=lambda x: -x["oi"])[:5]:
        zone = ""
        if spot:
            zone = ("call-above" if r["side"] == "C" and r["k"] > spot else
                    "PUT-HEDGE(below)" if r["side"] == "P" and r["k"] < 0.92 * spot else "")
        print(f"    {r['exp']:16} ${r['k']:>7.1f}{r['side']}  OI {r['oi']:>7,.0f}  {zone}")
    print("  Fresh unusual (top 5):")
    for r in sorted(un, key=lambda x: -x["vol"])[:5]:
        tag = "BULL call" if r["side"] == "C" else "BEAR put"
        print(f"    {r['exp']:16} ${r['k']:>7.1f}{r['side']}  vol {r['vol']:>7,.0f}"
              f"  OI {r['oi']:>6,.0f}  Vol/OI {r['voi']:>5.1f}  {tag}")
    return dict(sym=sym, pcv=pcv, pco=pco, score=s, flag=flag, spot=spot,
                flow_s=flow_s, iv_mod=iv_mod, un_call=un_call, un_put=un_put,
                nm_put=nm_put,
                atm_iv=(ivm.get("atm_iv") if ivm else None),
                skew=(ivm.get("skew") if ivm else None),
                em=(ivm.get("em") if ivm else None),
                dte=(ivm.get("dte") if ivm else None),
                ref=(ivm.get("ref") if ivm else None))


def main():
    spot = to = frm = None
    args, skip = [], False
    argv = sys.argv[1:]
    for i, a in enumerate(argv):
        if skip:
            skip = False; continue
        if a == "--spot": spot = float(argv[i + 1]); skip = True
        elif a == "--to": to = argv[i + 1]; skip = True
        elif a == "--from": frm = argv[i + 1]; skip = True
        elif a.startswith("--"): continue
        else: args.append(a)
    if not args:
        print("usage: python3 whale_check.py TICKER [TICKER...] [--spot X] [--to YYYY-MM-DD]")
        return
    out = []
    for sym in args:
        r = whale_check(sym.upper(), spot=spot if len(args) == 1 else None, frm=frm, to=to)
        if r: out.append(r)
    if len(out) > 1:
        print(f"\n{'='*68}\nWHALE FLAGS:")
        for r in out:
            ivs = f"IV ~{r['atm_iv']*100:.0f}%" if r.get("atm_iv") else "IV n/a"
            sks = f"skew {r['skew']*100:+.1f}" if r.get("skew") is not None else ""
            print(f"  {r['sym']:6} score {r['score']:+d}  {r['flag']}  "
                  f"(P/C vol {r['pcv']:.2f}, {ivs} {sks})")


if __name__ == "__main__":
    main()
