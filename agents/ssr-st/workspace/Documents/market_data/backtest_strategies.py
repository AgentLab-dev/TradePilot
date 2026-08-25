#!/usr/bin/env python3
"""Multi-strategy options backtester on cached daily OHLCV.

No historical options chains exist, so each spread is priced with Black-Scholes
using trailing realized vol as sigma (same approach as the original "Three Good"
put-credit backtest). We then walk the real underlying path to expiry, applying an
optional close-below/above-short-strike stop, and book defined-risk P&L.

Six structures (the strategy-selection matrix in monthly_income_plan.md):
  put_credit   bullish / high-IV   sell put  -C% , buy put  -(C+W)%
  call_debit   bullish / low-IV    buy call ATM, sell call +W%
  call_credit  bearish / high-IV   sell call +C%, buy call +(C+W)%
  put_debit    bearish / low-IV    buy put  ATM, sell put  -W%
  iron_condor  neutral / high-IV   put_credit + call_credit (both sides)
  calendar     neutral / low-IV    sell ATM near, buy ATM far (theta harvest)

Two reports:
  A) each strategy run on every name (apples-to-apples expectancy)
  B) MATRIX-ROUTED: classify regime(dir) x IV each week, trade the matching
     structure; compared against a PUT-CREDIT-ONLY baseline.

All P&L is scale-free: return-on-risk (RoR) = pnl / max_loss, so names of
different price levels aggregate cleanly. Expectancy is also shown as
$ per $1,000 risked per trade.

Run:  python3 backtest_strategies.py            # all cached names
      python3 backtest_strategies.py NNE DELL   # subset
      python3 backtest_strategies.py --md        # also write backtest_multistrategy.md
"""
import os, re, sys, math, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
MD_HIST = os.path.normpath(os.path.join(HERE, "..", "market_history.md"))
MD_OUT = os.path.normpath(os.path.join(HERE, "..", "backtest_multistrategy.md"))

# ---- knobs -------------------------------------------------------------------
DTE_TD = 21          # trading days to expiry (~30 calendar days)
STEP_TD = 5          # new entry every 5 trading days (weekly)
CUSHION = 0.08       # short strike distance for credit spreads (8% OTM)
WIDTH = 0.05         # spread width as % of spot (5%)
RFR = 0.04           # risk-[REDACTED] rate
VOL_WIN = 20         # trailing window for realized vol
REGIME_WIN = 50      # SMA window for direction
USE_CLOSE_STOP = True
EXCLUDE = {"SPCX"}   # too little history / IPO
# --- v2: event gate + confirmation filter -----------------------------------
EVENT_FLOOR = 0.07   # min overnight gap to flag as an event (earnings/guidance)
EVENT_MULT = 3.5     # ...or this many trailing-std of overnight gaps, whichever larger
EVENT_STD_WIN = 60   # trailing window for the adaptive gap threshold
CONF_DIST = 0.03     # price must be >3% beyond SMA50 to CONFIRM a trend (vs 2% raw)

# ---- Black-Scholes -----------------------------------------------------------
def _norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def bs(kind, S, K, T, sigma, r=RFR):
    """European option price. kind in {'c','p'}. T in years."""
    if T <= 0 or sigma <= 0:
        return max(0.0, (S - K) if kind == "c" else (K - S))
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    if kind == "c":
        return S * _norm_cdf(d1) - K * math.exp(-r * T) * _norm_cdf(d2)
    return K * math.exp(-r * T) * _norm_cdf(-d2) - S * _norm_cdf(-d1)

def vert(kind, side, S, Klo, Khi, T, sigma):
    """Value of a vertical spread (per share). side='credit' or 'debit'.
    For a put spread Klo<Khi: short Khi-ish; we just net the two legs by kind."""
    return None  # not used; we price legs explicitly below

# ---- data --------------------------------------------------------------------
def load_history():
    txt = open(MD_HIST).read()
    out = {}
    for m in re.finditer(r"\n## ([A-Z0-9.]+)\n(.*?)(?=\n## |\Z)", txt, re.S):
        sym = m.group(1)
        cm = re.search(r"```csv\n.*?\n(.*?)\n```", m.group(2), re.S)
        if not cm:
            continue
        bars = []
        for line in cm.group(1).splitlines():
            p = line.split(",")
            if len(p) >= 6:
                bars.append((p[0], float(p[1]), float(p[2]), float(p[3]),
                             float(p[4]), int(p[5])))
        if len(bars) > REGIME_WIN + DTE_TD + 5:
            out[sym] = bars
    return out

def realized_vol(closes, i, win=VOL_WIN):
    seg = closes[max(0, i - win):i + 1]
    if len(seg) < 3:
        return 0.4
    rets = [math.log(seg[k] / seg[k - 1]) for k in range(1, len(seg))]
    mu = sum(rets) / len(rets)
    var = sum((x - mu) ** 2 for x in rets) / (len(rets) - 1)
    return math.sqrt(var) * math.sqrt(252)

def regime(closes, i):
    """('up'|'down'|'range') — raw 2% SMA band, used by the un-gated router."""
    if i < REGIME_WIN:
        return "range"
    sma = sum(closes[i - REGIME_WIN + 1:i + 1]) / REGIME_WIN
    sma_prev = sum(closes[i - REGIME_WIN:i]) / REGIME_WIN
    px = closes[i]
    slope_up = sma > sma_prev
    if px > sma * 1.02 and slope_up:
        return "up"
    if px < sma * 0.98 and not slope_up:
        return "down"
    return "range"

def confirmed(closes, i):
    """Stricter regime for the v2 router: price must be decisively (>3%) beyond a
    sloping SMA50 AND on the same side of SMA20 (short-term agrees). Otherwise
    'range' -> the router stands down rather than forcing a trade."""
    if i < REGIME_WIN:
        return "range"
    sma50 = sum(closes[i - 49:i + 1]) / 50
    sma50_prev = sum(closes[i - 50:i]) / 50
    sma20 = sum(closes[i - 19:i + 1]) / 20
    px = closes[i]
    if px > sma50 * (1 + CONF_DIST) and sma50 > sma50_prev and px > sma20:
        return "up"
    if px < sma50 * (1 - CONF_DIST) and sma50 < sma50_prev and px < sma20:
        return "down"
    return "range"

def detect_events(bars):
    """Flag bar indices with an abnormal OVERNIGHT GAP (earnings/guidance proxy).
    Threshold is per-name adaptive: max(EVENT_FLOOR, EVENT_MULT * trailing-std of
    gaps). In live trading earnings dates are known in advance, so using these
    (historical) dates as 'known' is a faithful sim of the AVGO event-gate rule."""
    ev = set()
    gaps = []
    for i in range(1, len(bars)):
        prev_c = bars[i - 1][4]
        op = bars[i][1]
        g = (op / prev_c - 1) if prev_c > 0 else 0.0
        gaps.append(g)
        win = gaps[max(0, len(gaps) - EVENT_STD_WIN):]
        if len(win) >= 10:
            mu = sum(win) / len(win)
            sd = (sum((x - mu) ** 2 for x in win) / (len(win) - 1)) ** 0.5
            thr = max(EVENT_FLOOR, EVENT_MULT * sd)
        else:
            thr = EVENT_FLOOR
        if abs(g) >= thr:
            ev.add(i)
    return ev

# ---- strategy simulators -----------------------------------------------------
# Each returns (pnl_per_share, max_loss_per_share) or None if unpriceable.
# Path = list of closes for the holding window (index 0 = entry day close).
def sim_credit(path, S, T_years, sigma, put=True):
    """Bull put credit (put=True) or bear call credit (put=False)."""
    if put:
        Ks = S * (1 - CUSHION)          # short
        Kl = S * (1 - CUSHION - WIDTH)  # long (protection)
        c_short = bs("p", S, Ks, T_years, sigma)
        c_long = bs("p", S, Kl, T_years, sigma)
    else:
        Ks = S * (1 + CUSHION)
        Kl = S * (1 + CUSHION + WIDTH)
        c_short = bs("c", S, Ks, T_years, sigma)
        c_long = bs("c", S, Kl, T_years, sigma)
    credit = c_short - c_long
    width = abs(Ks - Kl)
    if credit <= 0 or credit >= width:
        return None
    max_loss = width - credit
    n = len(path) - 1
    # close-stop: underlying closes beyond short strike -> exit at BS mark
    if USE_CLOSE_STOP:
        for d in range(1, n + 1):
            breached = path[d] < Ks if put else path[d] > Ks
            if breached:
                Tr = max(0.0, (n - d) / 252.0)
                sig = sigma
                if put:
                    v = bs("p", path[d], Ks, Tr, sig) - bs("p", path[d], Kl, Tr, sig)
                else:
                    v = bs("c", path[d], Ks, Tr, sig) - bs("c", path[d], Kl, Tr, sig)
                pnl = credit - v
                return (max(pnl, -max_loss), max_loss)
    ST = path[-1]
    if put:
        intrinsic = max(0.0, Ks - ST) - max(0.0, Kl - ST)
    else:
        intrinsic = max(0.0, ST - Ks) - max(0.0, ST - Kl)
    pnl = credit - intrinsic
    return (max(pnl, -max_loss), max_loss)

def sim_debit(path, S, T_years, sigma, call=True):
    """Bull call debit (call=True) or bear put debit (call=False)."""
    if call:
        Kl = S                      # long ATM
        Ks = S * (1 + WIDTH)        # short OTM
        d_long = bs("c", S, Kl, T_years, sigma)
        d_short = bs("c", S, Ks, T_years, sigma)
    else:
        Kl = S
        Ks = S * (1 - WIDTH)
        d_long = bs("p", S, Kl, T_years, sigma)
        d_short = bs("p", S, Ks, T_years, sigma)
    debit = d_long - d_short
    width = abs(Ks - Kl)
    if debit <= 0 or debit >= width:
        return None
    max_loss = debit
    n = len(path) - 1
    # debit stop: spread value <= 50% of debit -> exit
    if USE_CLOSE_STOP:
        for d in range(1, n + 1):
            Tr = max(0.0, (n - d) / 252.0)
            if call:
                v = bs("c", path[d], Kl, Tr, sigma) - bs("c", path[d], Ks, Tr, sigma)
            else:
                v = bs("p", path[d], Kl, Tr, sigma) - bs("p", path[d], Ks, Tr, sigma)
            if v <= 0.5 * debit:
                return (v - debit, max_loss)
    ST = path[-1]
    if call:
        intrinsic = max(0.0, ST - Kl) - max(0.0, ST - Ks)
    else:
        intrinsic = max(0.0, Kl - ST) - max(0.0, Ks - ST)
    pnl = intrinsic - debit
    return (max(pnl, -max_loss), max_loss)

def sim_condor(path, S, T_years, sigma):
    p = sim_credit(path, S, T_years, sigma, put=True)
    c = sim_credit(path, S, T_years, sigma, put=False)
    if not p or not c:
        return None
    pnl = p[0] + c[0]
    max_loss = max(p[1], c[1])   # only one side can lose
    return (pnl, max_loss)

def sim_calendar(path, S, T_years, sigma):
    """Sell ATM near (DTE), buy ATM far (2*DTE). Close when near expires."""
    K = S
    Tn, Tf = T_years, 2 * T_years
    short0 = bs("c", S, K, Tn, sigma)
    long0 = bs("c", S, K, Tf, sigma)
    debit = long0 - short0
    if debit <= 0:
        return None
    max_loss = debit            # calendars can't lose more than the debit paid
    ST = path[-1]
    short_exp = max(0.0, ST - K)            # near option intrinsic at expiry
    long_val = bs("c", ST, K, Tf - Tn, sigma)
    pnl = (long_val - short_exp) - debit
    return (max(pnl, -max_loss), max_loss)

STRATS = {
    "put_credit":  lambda path, S, T, sig: sim_credit(path, S, T, sig, put=True),
    "call_debit":  lambda path, S, T, sig: sim_debit(path, S, T, sig, call=True),
    "call_credit": lambda path, S, T, sig: sim_credit(path, S, T, sig, put=False),
    "put_debit":   lambda path, S, T, sig: sim_debit(path, S, T, sig, call=False),
    "iron_condor": lambda path, S, T, sig: sim_condor(path, S, T, sig),
    "calendar":    lambda path, S, T, sig: sim_calendar(path, S, T, sig),
}

# ---- backtest engine ---------------------------------------------------------
def stats(trades):
    """trades = list of (ror, pnl_per_share, max_loss_per_share)."""
    if not trades:
        return None
    n = len(trades)
    wins = [t for t in trades if t[0] > 0]
    losses = [t for t in trades if t[0] <= 0]
    wr = len(wins) / n
    avg_w = sum(t[0] for t in wins) / len(wins) if wins else 0.0
    avg_l = sum(t[0] for t in losses) / len(losses) if losses else 0.0
    exp = sum(t[0] for t in trades) / n                 # expectancy in RoR
    dollar_per_1k = exp * 1000.0                         # $ per $1k risked / trade
    return dict(n=n, wr=wr, avg_w=avg_w, avg_l=avg_l, exp=exp, dpk=dollar_per_1k)

CREDIT_STRATS = {"put_credit", "call_credit", "iron_condor"}

def run(symbols):
    hist = load_history()
    names = [s for s in (symbols or hist.keys()) if s in hist and s not in EXCLUDE]
    per_strat = {k: [] for k in STRATS}
    routed_raw = []      # v1: naive SMA router, no gate
    routed_v2 = []       # v2: confirmation + event gate, can stand down
    pc_only = []         # put-credit-only baseline
    pc_gated = []        # put-credit-only + event gate (isolates the gate's value)
    skips = 0            # entries the v2 router stood down on
    iv_dist = {}
    for sym in names:
        closes = [b[4] for b in hist[sym]]
        vols = [realized_vol(closes, i) for i in range(VOL_WIN, len(closes))]
        iv_dist[sym] = sorted(vols)

    for sym in names:
        bars = hist[sym]
        closes = [b[4] for b in bars]
        events = detect_events(bars)
        med_vol = iv_dist[sym][len(iv_dist[sym]) // 2] if iv_dist[sym] else 0.5
        i = REGIME_WIN
        while i + DTE_TD < len(bars):
            S = closes[i]
            sigma = realized_vol(closes, i)
            T = DTE_TD / 252.0
            path = closes[i:i + DTE_TD + 1]
            high_iv = sigma >= med_vol
            event_in_window = any(i < j <= i + DTE_TD for j in events)

            # ---- per-strategy (every strat, every entry, ungated) ----
            for k, fn in STRATS.items():
                r = fn(path, S, T, sigma)
                if r:
                    per_strat[k].append((r[0] / r[1], r[0], r[1]))

            # ---- v1 naive router (raw regime, no gate) ----
            d1 = regime(closes, i)
            s1 = ("put_credit" if high_iv else "call_debit") if d1 == "up" else \
                 ("call_credit" if high_iv else "put_debit") if d1 == "down" else \
                 ("iron_condor" if high_iv else "calendar")
            r = STRATS[s1](path, S, T, sigma)
            if r:
                routed_raw.append((r[0] / r[1], r[0], r[1], s1))

            # ---- v2 router: confirmation + event gate (stands down otherwise) ----
            d2 = confirmed(closes, i)
            if d2 == "up":
                s2 = "put_credit" if high_iv else "call_debit"
            elif d2 == "down":
                s2 = "call_credit" if high_iv else "put_debit"
            else:  # unconfirmed/range
                s2 = "iron_condor" if high_iv else None  # skip range+lowIV (flat)
            # event gate: never SELL premium through an event (debit buys are ok)
            if s2 in CREDIT_STRATS and event_in_window:
                s2 = None
            if s2 is None:
                skips += 1
            else:
                r = STRATS[s2](path, S, T, sigma)
                if r:
                    routed_v2.append((r[0] / r[1], r[0], r[1], s2))

            # ---- baselines ----
            r = STRATS["put_credit"](path, S, T, sigma)
            if r:
                pc_only.append((r[0] / r[1], r[0], r[1]))
                if not event_in_window:
                    pc_gated.append((r[0] / r[1], r[0], r[1]))

            i += STEP_TD

    return dict(names=names, per_strat=per_strat, routed_raw=routed_raw,
                routed_v2=routed_v2, pc_only=pc_only, pc_gated=pc_gated, skips=skips)

def fmt(s):
    if not s:
        return "   n/a"
    return (f"{s['n']:>5} | win {s['wr']*100:5.1f}% | "
            f"avgW {s['avg_w']*100:+6.1f}% | avgL {s['avg_l']*100:+6.1f}% | "
            f"exp {s['exp']*100:+5.2f}% RoR | ${s['dpk']:+7.2f}/$1k")

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    write_md = "--md" in sys.argv
    R = run(args)
    names, per_strat = R["names"], R["per_strat"]
    routed_raw, routed_v2 = R["routed_raw"], R["routed_v2"]
    pc_only, pc_gated, skips = R["pc_only"], R["pc_gated"], R["skips"]
    label = {
        "put_credit": "Put credit (bull/highIV)",
        "call_debit": "Call debit (bull/lowIV)",
        "call_credit": "Call credit (bear/highIV)",
        "put_debit": "Put debit (bear/lowIV)",
        "iron_condor": "Iron condor (range/highIV)",
        "calendar": "Calendar (range/lowIV)",
    }
    from collections import Counter
    lines = []
    lines.append(f"Universe: {len(names)} names | {DTE_TD}td DTE | weekly entries | "
                 f"close-stop={'on' if USE_CLOSE_STOP else 'off'} | "
                 f"cushion {CUSHION*100:.0f}% width {WIDTH*100:.0f}%")
    lines.append("")
    lines.append("A) PER-STRATEGY (each structure on every name, every week)")
    lines.append("-" * 92)
    for k in STRATS:
        lines.append(f"  {label[k]:<28} {fmt(stats(per_strat[k]))}")
    lines.append("")
    lines.append("B) ROUTERS vs BASELINES")
    lines.append("-" * 92)
    lines.append(f"  {'v1 naive router (no gate)':<32} {fmt(stats([t[:3] for t in routed_raw]))}")
    lines.append(f"  {'v2 router (confirm+event gate)':<32} {fmt(stats([t[:3] for t in routed_v2]))}")
    lines.append(f"  {'put-credit-only':<32} {fmt(stats(pc_only))}")
    lines.append(f"  {'put-credit-only + event gate':<32} {fmt(stats(pc_gated))}")
    lines.append(f"  v2 stood down on {skips} entries (no confirmed edge / event in window)")
    lines.append("")
    c1 = Counter(t[3] for t in routed_raw)
    c2 = Counter(t[3] for t in routed_v2)
    lines.append("  v1 picks: " + ", ".join(f"{k}={v}" for k, v in c1.most_common()))
    lines.append("  v2 picks: " + ", ".join(f"{k}={v}" for k, v in c2.most_common()))
    out = "\n".join(lines)
    print(out)

    if write_md:
        def row(name, s):
            if not s:
                return f"| {name} | – | – | – | – | – | – |"
            return (f"| {name} | {s['n']} | {s['wr']*100:.1f}% | {s['avg_w']*100:+.1f}% | "
                    f"{s['avg_l']*100:+.1f}% | {s['exp']*100:+.2f}% | ${s['dpk']:+.0f} |")
        md = []
        md.append("# Multi-Strategy Backtest")
        md.append(f"\n_Generated {dt.datetime.utcnow():%Y-%m-%d %H:%M}Z by "
                  "`market_data/backtest_strategies.py` on the cached 2-year daily "
                  "OHLCV ({} names). Spreads priced with Black-Scholes using trailing "
                  "{}-day realized vol as sigma (no historical option chains exist). "
                  "Weekly entries, {}-trading-day expiry, close-stop "
                  "{}. v2 router adds a confirmation filter (price decisively beyond a "
                  "sloping SMA50 + SMA20 agreement) and an event gate (no premium "
                  "selling through a detected earnings/guidance gap)._\n".format(
                      len(names), VOL_WIN, DTE_TD, "ON" if USE_CLOSE_STOP else "OFF"))
        md.append("> **Read RoR-expectancy, not win rate.** A high win rate with a big "
                  "avg loss still bleeds (the HOOD lesson). `exp` = avg return-on-risk "
                  "per trade; `$/ $1k` = dollars per $1,000 risked per trade.\n")
        md.append("## A) Per-strategy (every structure, every name, every week)\n")
        md.append("| Strategy | N | Win% | Avg win | Avg loss | Exp (RoR) | $/ $1k |")
        md.append("|---|---|---|---|---|---|---|")
        for k in STRATS:
            md.append(row(label[k], stats(per_strat[k])))
        md.append("\n## B) Routers vs baselines\n")
        md.append("| Approach | N | Win% | Avg win | Avg loss | Exp (RoR) | $/ $1k |")
        md.append("|---|---|---|---|---|---|---|")
        md.append(row("v1 naive router (no gate)", stats([t[:3] for t in routed_raw])))
        md.append(row("**v2 router (confirm + event gate)**", stats([t[:3] for t in routed_v2])))
        md.append(row("put-credit-only", stats(pc_only)))
        md.append(row("put-credit-only + event gate", stats(pc_gated)))
        md.append(f"\n_v2 stood down on **{skips}** entries (no confirmed edge or an "
                  "event in the window). v1 picks: "
                  + ", ".join(f"{k}={v}" for k, v in c1.most_common())
                  + ". v2 picks: "
                  + ", ".join(f"{k}={v}" for k, v in c2.most_common()) + "._")
        md.append("\n## Method & caveats\n")
        md.append("- **Pricing:** Black-Scholes, realized vol as IV proxy. Real IV is "
                  "usually richer than realized for sellers (vol-risk-[REDACTED]), so live "
                  "credit-spread edge is typically **better** than shown here; debit "
                  "spreads slightly worse. Treat as *relative* ranking, not absolute $.")
        md.append("- **Strikes:** % -based (cushion {:.0f}%, width {:.0f}%) so names "
                  "aggregate; live trades use real strikes/liquidity.".format(CUSHION*100, WIDTH*100))
        md.append("- **Stops:** credit = close beyond short strike; debit = spread −50%. "
                  "Held to expiry otherwise.")
        md.append("- **No earnings gate** in the sim (live book always applies it) — so "
                  "real tail losses are smaller than backtest.")
        md.append("- **Calendar** is a single-vol approximation (same sigma both expiries); "
                  "real calendars depend on term-structure, so treat that row as indicative.")
        open(MD_OUT, "w").write("\n".join(md) + "\n")
        print(f"\nwrote {MD_OUT}")

if __name__ == "__main__":
    main()
