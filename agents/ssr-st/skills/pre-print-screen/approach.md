# PPS — how we find the best names

Two strategies. One funnel. Existing skills only — do not invent a second
universe or a new news login.

```
calendar (2–14d)
    → category gate (ALWAYS ∪ history ∪ book ∪ IBD ∪ maps)
        → PPS-T7 ON (watch every name that passes)
            → daily evidence stack (IBD, WSJ, MW, whale EM, beats)
                → PPS score 0–12
                    → T−7 leads = top 3
                        → on 0d: PPS-T1 promote / stand
                            → at most one 🟢 TAKE (1×)
```

**T−7 answers:** who do we watch this week?  
**T−1 answers:** which one (if any) do we buy before 4:00 ET?

Mega-cap is not the rank. Whale 🔴 does not veto. Homepage news is not the
ticker query.

## Step 1 — calendar ∩ category (gate, not a score)

| Input | Skill / tool |
|---|---|
| Who prints in 2–7d | `fetch_earnings.py` → `earnings_radar.md` ∪ Robinhood `get_earnings_calendar` |
| Already ours? | ALWAYS + `fetch_history.py` groups + open book + industry maps |
| IBD overlap | `ibd-wsj-capture` → `ibd_stock_lists.md` (50, Sector Leaders, Big Cap, Funds, Spotlight, New Highs) |

Pass both → **PPS-T7 🟢 ON** (or 🟡 THIN if EM/news missing).  
Fail category → both flags ⚪ (still a catalyst card if 0d/1d — XE rule).

This step does **not** pick a winner. OKTA would have passed on ~8/19.

## Step 2 — daily evidence stack (T−7, no fill)

Run every FULL CHECK / wrap on every 🟢 ON / 🟡 THIN row. Extra depth on the
current top 3.

| # | Evidence | Skill / tool | What “good” looks like |
|---|---|---|---|
| 1 | ATM **expected move %** | `whale_check.py SYM --to <monthly>` (Whale Watch) | ≥15% is a monster-print candidate; ≥18% is OKTA-class |
| 2 | Beat streak + surprise | Robinhood `get_earnings_results` | ≥4 consecutive beats; last-4 avg surprise ≥15% |
| 3 | IBD quality | `ibd-wsj-capture` | 50 or Sector Leaders > Funds/Big Cap > Spotlight |
| 4 | Ticker news (not homepage) | `news-portals` + browser: `{TICKER} earnings` on **WSJ, MarketWatch, IR, CNBC** | Theme (AI, identity, cyber, custom silicon) or beat-and-raise preview |
| 5 | Same-week cluster | radar + maps | CRWD+OKTA same AMC; PANW after that cyber tape |
| 6 | OTM **call OI wall** | whale_check walls | Wall at ~0.7–1.0× EM OTM (OKTA 160C ≈ 19% OTM vs 18.6% EM) |
| 7 | Peer tape | Robinhood quotes | Own print still required — no T+1 chase on names with no event |

4-model (STKK / STNOW / 3Good / Whale flag) is **context**, not the PPS rank.
OKTA was RANGE / bearish / missing STKK and still the 20% name.

## Step 3 — PPS score (same sheet all week)

| Signal | Points |
|---|---|
| EM% <12 | 0 (still watch if category) |
| EM% 12–14.9 | +2 |
| EM% 15–17.9 | +3 |
| EM% ≥18 | +4 |
| Consecutive beats ≥4 | +2 |
| Last-4 avg surprise ≥15% | +2 |
| IBD 50 or Sector Leaders | +2 |
| IBD Funds or Big Cap only | +1 (do not stack with +2) |
| Ticker WSJ/MW/IR theme | +1 |
| Same-week cluster print | +1 |
| Call wall ~0.7–1.0× EM | +1 |

Max 12. Recompute daily. **Leads = top 3** by score (ties: higher EM%, then
surprise). Leads get the extra news pass. Everyone ON stays on the board.

## Step 4 — PPS-T1 (separate strategy, print day)

Only 0d / last 90 min. Use the T−7 score if it exists.

**🟢 TAKE** if EM% ≥15% **and** (beats ≥4 **or** last-4 surprise ≥15% **or**
theme+cluster).  
**🔴 STAND** if EM% ≥15% but surprises are small (MRVL).  
**🟡 ARM** if score is close and last-90 still has to clear the $4 cap.

If two names are TAKE, pick the **higher PPS score**. Size is 1× → **one name**.
Wait for **go**.

Structure: OTM 10-wide, long strike ≈ spot + 0.7–1.0× EM, cap $3–$4.

## Worked contrast (why this ranking exists)

| | OKTA 8/26 (should have been TAKE) | MRVL 8/27 (STAND) |
|---|---|---|
| Category | ALWAYS + IBD Funds + cyber | ALWAYS + NVDA map |
| EM% | **±18.6%** | ±20.7% (clears EM, not the rest) |
| Beats / surprise | 6-for-6, last-4 **~41%** | 6-for-6, last-4 **~2–13%** |
| News / cluster | identity/AI + CRWD same night | NVDA already printed into the name |
| Call wall | 160C OI 1,712 ≈ EM | 250C ATM wall |
| Whale flag | 🔴 −1 (ignored) | 🟡 0 |
| Result | T−7 lead → T−1 TAKE | T−1 STAND |

## What we do not do

- Rank by market cap (NVDA first).
- Buy ATM seven days early (8/9 two-week reject).
- Let whale 🔴 or missing STKK bury a print.
- Query only the WSJ homepage.
- Fill more than one PPS-T1 lottery.
- Chase a peer with **no** print tomorrow (6/26 SNDK).
