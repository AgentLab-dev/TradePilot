#!/usr/bin/env python3
"""ONE command — run the whole pipeline and surface today's possible trade.

Chains everything:
  1. refresh cache (fetch_history --delta) for the focus list
  2. earnings gate (fetch_earnings) → earnings_radar.md
  3. macro + cross-asset "Tomorrow" risk tilt (live)
  4. MANGOS AI-leadership cross-check (live)
  5. Health Check composite = STKK + STNOW + Three Good + Whale (per name)
  6. rank the GO verdicts → today's candidate(s), routed by the IV matrix

Usage:
  python3 daily.py                 # default focus list (MANGOS + book + key watch)
  python3 daily.py NNE DELL MU     # specific names
  python3 daily.py --all           # entire cached universe
  python3 daily.py --quick         # skip the cache refresh + earnings pull (faster)
  python3 daily.py --to 2026-09-30 # whale expiry target
"""
import os, sys, io, json, contextlib, subprocess, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import stkk_from_cache as stk
import whale_check as wc
import health_check as hc

MANGOS = ["META", "NVDA", "GOOGL", "SPCX"]          # public AI leaders
PROXY  = ["AMZN", "MSFT"]                            # Anthropic / OpenAI proxies
BOOK   = ["NNE", "HPE", "DELL", "ANET", "CRM"]       # open + armed
WATCH  = ["MARA", "HOOD", "ORCL", "SNOW", "SMCI", "MU", "XE", "SNDK", "WDC", "STX"]
FOCUS  = list(dict.fromkeys(MANGOS + BOOK + WATCH))
H = ["-H", "User-Agent: Mozilla/5.0", "-H", "Accept: application/json"]

# Bellwether → sympathy peers (the MU→SNDK lesson). When a bellwether shows a
# catalyst-size move in the last 1–2 sessions, scan its peers for a SAME-DAY play.
READTHROUGH = {
    "MU":   ["SNDK", "WDC", "STX", "NTAP", "SMH", "SOXX"],   # memory/storage
    "NVDA": ["AVGO", "AMD", "TSM", "SMCI", "CRWV", "MRVL"],  # AI compute
    "AVGO": ["NVDA", "AMD", "MRVL", "SMH"],                  # semis
    "TSLA": ["RIVN", "CHPT", "LCID"],                        # EV / charging
    "ORCL": ["SNOW", "DDOG", "MDB", "NOW"],                  # data/cloud
    "CRM":  ["NOW", "DDOG", "SNOW", "MDB"],                  # enterprise SaaS
}
GAP = 0.05       # bellwether |move| >= 5% (was 7%; MU +5.8% missed SNDK +15% on 8/13)
PEER_GAP = 0.07  # mapped peer ripping this hard fires the radar even if the bellwether is quiet


def q(sym):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=1d&interval=1d"
    try:
        raw = subprocess.run(["curl", "-s", "--max-time", "20", *H, url],
                             capture_output=True, text=True, timeout=25).stdout
        m = json.loads(raw)["chart"]["result"][0]["meta"]
        p = m.get("regularMarketPrice"); pc = m.get("chartPreviousClose") or m.get("previousClose")
        return p, ((p / pc - 1) * 100 if p and pc else 0.0)
    except Exception:
        return None, None


def line(sym, label=None):
    p, c = q(sym)
    if p is None:
        return f"  {(label or sym):10} n/a"
    arrow = "🟢" if c > 0.15 else "🔴" if c < -0.15 else "⚪"
    return f"  {(label or sym):10} {p:>10.2f}  {c:+5.2f}% {arrow}"


def sess_move(sym, data):
    """Most-recent session move (signed). Catch the catalyst ON the day, not 1–2
    sessions stale — so use today's live move (live px vs prior close) first;
    fall back to the last cached close-to-close only if live is unavailable."""
    p, pct = q(sym)
    if p is not None and pct is not None:
        return p, pct / 100.0                # today's session move (live vs prev close)
    c = [r[4] for r in data.get(sym, [])]
    if len(c) >= 2:
        return c[-1], c[-1] / c[-2] - 1      # fallback: last completed session
    return p, None


def read_through(data):
    """Detect bellwether OR peer-rip catalysts; return (alert_lines, extra_targets).

    Fire if the bellwether session move is >= GAP (5%) OR any mapped peer is
    already >= PEER_GAP (7%). The 8/13 miss: MU +5.8% < old 7% gate while SNDK
    was +15% on investor day — radar printed "no bellwether catalyst."
    """
    alerts, extra = [], []
    for bw, peers in READTHROUGH.items():
        bp, bm = sess_move(bw, data)
        peer_rows = []
        peer_fire = False
        for pk in peers:
            pp, pm = sess_move(pk, data)
            peer_rows.append((pk, pp, pm))
            if pm is not None and abs(pm) >= PEER_GAP:
                peer_fire = True
        bw_fire = bm is not None and abs(bm) >= GAP
        if not bw_fire and not peer_fire:
            continue
        if bw_fire:
            dirn = "🟢 UP" if bm > 0 else "🔴 DOWN"
            why = f"{bw} {dirn} {bm*100:+.1f}%"
            ref = bm
        else:
            hot = [f"{pk} {pm*100:+.1f}%" for pk, _, pm in peer_rows
                   if pm is not None and abs(pm) >= PEER_GAP]
            bw_s = f"{bm*100:+.1f}%" if bm is not None else "n/a"
            why = f"peer rip ({', '.join(hot)}) — bellwether {bw} only {bw_s}"
            ref = next((pm for _, _, pm in peer_rows
                        if pm is not None and abs(pm) >= PEER_GAP), 0.0)
        alerts.append(f"  ⚡ {why}  → scan peers (same-day momentum, exit same session):")
        extra.append(bw)
        for pk, pp, pm in peer_rows:
            if pp is None:
                alerts.append(f"       {pk:6} n/a"); continue
            same_dir = pm is not None and ref and (pm * ref > 0)
            tag = ("🔥 moving WITH" if (same_dir and abs(pm) >= 0.03)
                   else "… lagging (catch-up?)" if same_dir
                   else "↔ diverging")
            alerts.append(f"       {pk:6} {pp:>9.2f}  {pm*100:+5.1f}%  {tag}")
            extra.append(pk)
    return alerts, extra


def main():
    argv = sys.argv[1:]
    quick = "--quick" in argv
    to = argv[argv.index("--to") + 1] if "--to" in argv else None
    names = [a.upper() for a in argv if not a.startswith("--") and a != to]
    if "--all" in argv:
        names = [s for s in stk.load().keys() if s not in {"SPY", "QQQ", "SPCX"}]
    targets = names or FOCUS

    print(f"\n{'#'*70}\n#  DAILY PLAN — {dt.datetime.now():%a %Y-%m-%d %H:%M} local\n{'#'*70}")

    # 1+2. refresh + earnings gate
    if not quick:
        print("\n[1/8] refreshing cache (delta) + [2/8] earnings gate ...")
        subprocess.run(["python3", os.path.join(HERE, "fetch_history.py"), *targets, "--delta"],
                       capture_output=True, text=True)
        subprocess.run(["python3", os.path.join(HERE, "fetch_earnings.py")],
                       capture_output=True, text=True)

    # 3. macro + cross-asset Tomorrow tilt
    print("\n[3/8] MACRO + cross-asset risk tilt (Tomorrow block-3)")
    for s, lbl in [("^GSPC","SPX"),("^VIX","VIX"),("QQQ","QQQ"),("RSP","S&P-EW"),
                   ("^TNX","10Y"),("BTC-USD","BTC"),("CL=F","Oil"),("GLD","Gold"),("UUP","Dollar")]:
        print(line(s, lbl))
    vix_p, vix_c = q("^VIX"); qqq_p, qqq_c = q("QQQ")
    tilt = "🟢 RISK-ON" if (qqq_c or 0) > 0.2 and (vix_c or 0) < 0 else \
           "🔴 RISK-OFF" if (qqq_c or 0) < -0.2 or (vix_c or 0) > 3 else "⚪ MIXED"
    print(f"  → tilt: {tilt}")

    # 4. MANGOS
    print("\n[4/8] 🥭 MANGOS AI-leadership cross-check")
    for s in MANGOS: print(line(s))
    print("  proxies (Anthropic/OpenAI):")
    for s in PROXY: print(line(s))

    # 5. earnings gate readout + T+0/T+1 catalyst-ticket flag
    print("\n[5/8] EARNINGS GATE (next 1–2 wks → no credit sell through these)")
    rad = os.path.normpath(os.path.join(HERE, "..", "earnings_radar.md"))
    hits = []
    if os.path.exists(rad):
        hits = [l for l in open(rad).read().splitlines() if l.startswith("| **")]
        print("  " + ("\n  ".join(hits) if hits else "none in window ✅"))
    print("  NOTE: Nasdaq ∩ universe misses names (XE 8/13). UNION Robinhood "
          "get_earnings_calendar + investor-day search before ranking takes.")

    print("\n[5b/8] T+0 / T+1 CATALYST TICKETS (each needs a card — 'no credit sell' is not a plan)")
    near = [l for l in hits if "| 0d |" in l or "| 1d |" in l]
    if near:
        print("  Nasdaq radar 0d/1d:")
        print("  " + "\n  ".join(near))
    else:
        print("  none on Nasdaq radar 0d/1d — still run MCP calendar + investor-day search")
    cards = os.path.normpath(os.path.join(HERE, "..", "catalyst_cards.md"))
    if os.path.exists(cards):
        body = open(cards).read().strip()
        print("  --- catalyst_cards.md ---")
        for ln in body.splitlines()[:40]:
            print("  " + ln)
    else:
        print("  ⚠ catalyst_cards.md MISSING — write it before ranking takes "
              "(skill: catalyst-overnight-plan)")

    data = stk.load()

    # 6. bellwether read-through radar (the MU→SNDK lesson)
    print("\n[6/8] READ-THROUGH RADAR (bellwether ≥5% OR mapped peer ≥7%)")
    alerts, extra = read_through(data)
    if alerts:
        print("\n".join(alerts))
        print("  NOTE: catalyst-day momentum only — Whale flag is stale on a fresh gap; exit same session.")
        print("  If a mapped peer has a scheduled event TOMORROW (investor day / earn), arm T−1 — "
              "do not wait to 'not chase' after the open.")
        new = [s for s in extra if s not in targets]
        if new:
            targets = targets + list(dict.fromkeys(new))
            print(f"  → added to Health Check scan: {', '.join(dict.fromkeys(new))}")
    else:
        print("  no bellwether ≥5% and no mapped peer ≥7% this session")

    # 7. Health Check composite + ranking
    print(f"\n[7/8] HEALTH CHECK composite (STKK+STNOW+ThreeGood+Whale) — {len(targets)} names")
    live = {}
    for s in targets:
        p, _ = q(s)
        if p: live[s] = p
    spy = [r[4] for r in data.get("SPY", [])]
    spy_ret = [spy[i]/spy[i-1]-1 for i in range(1, len(spy))] if spy else []
    ranked = []
    print(f"  {'Name':6}{'Px':>9}  {'STKK':18}{'STNOW':16}{'Whale':14}{'VERDICT'}")
    print("  " + "-"*94)
    for sym in targets:
        d = hc.compute_stkk(sym, data, spy_ret, live)
        if not d:
            print(f"  {sym:6}  (insufficient history / no chain)"); continue
        with contextlib.redirect_stdout(io.StringIO()):
            w = wc.whale_check(sym, spot=live.get(sym), to=to)
        sn = hc.stnow_eval(d, w)
        v = hc.verdict(d, w, sn)
        sf, st = hc.stkk_flag(d); nf, nt = hc.stnow_flag(sn)
        wflag = (w or {}).get("flag", "n/a")
        print(f"  {sym:6}{d['px']:>9.2f}  {sf+' '+st:18}{nf+' '+nt:16}{wflag:14}{v}")
        score = sn["raw"] + (w or {}).get("score", 0)
        is_go = "GO" in v and "WAIT" not in v and "AVOID" not in v
        ranked.append((is_go, score, sym, v, hc.structure(d, w, sn), (w or {}).get("atm_iv")))

    # candidate
    gos = sorted([r for r in ranked if r[0]], key=lambda x: -x[1])
    print("\n" + "="*70)
    print("🎯 TODAY'S CANDIDATE(S) — ranked GO verdicts (route by IV matrix)")
    print("="*70)
    if not gos:
        print("  none clean today → STAND DOWN (log the reason). Protect the streak.")
    else:
        for is_go, score, sym, v, struct, iv in gos[:3]:
            ivs = f"IV {iv*100:.0f}%" if iv else "IV n/a"
            print(f"  • {sym:5} score {score:+d} | {ivs:8} | {struct:34} | {v}")
    print("\n  Reminders: confirm a held level (no chasing) · check earnings gate above ·"
          " size to $300–500 / ≤3% loss · take 50% profit fast.")
    print("  Catalyst cards: every 0d/1d event needs take/arm/stand-down WITH structure "
          "(skill catalyst-overnight-plan). 'No credit sell' is not a plan.")


if __name__ == "__main__":
    main()
