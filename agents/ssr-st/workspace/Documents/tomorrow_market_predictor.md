# Tomorrow — Next-Session Market Direction Predictor

_Predicts the next trading session's direction (SPY/QQQ/Dow) by fusing 7 signal blocks into a probabilistic UP / FLAT / DOWN call with an expected range, key levels, swing factors, and a logged track record._
_Trigger: type **`Tomorrow`**. Skill: `~/.cursor/skills/tomorrow-market-predictor/`. Log: `tomorrow_predictions_log.md`._
_Last updated: June 12, 2026._

> ⚠️ **Educational / personal use — not financial advice.** Next-day moves are ~55–60% predictable at best. The edge is **process + calibration**, not certainty.

---

## The 8 signal blocks (each scored −2 … +2; + = risk-[REDACTED]/up)

| # | Block | What it reads | Source |
|---|---|---|---|
| 1 | **Today (tape & breadth)** | close vs open, % move, adv/dec breadth, sector leaders, volume, MA posture, reversals | RH quotes + WebSearch |
| 2 | **After-hours / futures** | ES/NQ overnight drift, AH earnings/guidance, AH news shocks | SPY/QQQ AH print + WebSearch |
| 3 | **Cross-asset** | oil, 10Y yield, VIX, dollar, BTC, gold — the risk tell that *leads* equities | RH ETF proxies (USO/IEF/VIXY/UUP/GLD/IBIT) |
| 4 | **News & government** | WSJ/MW/wire headlines; tariffs/USTR, war/geopolitics, Fed speak, regulation, exec actions | WebSearch |
| 5 | **Calendar (tomorrow)** | scheduled data (CPI/PPI/jobs/retail), Fed events, big earnings → **event-veto flag** | WebSearch |
| 6 | **Global / overnight** | Asia (Nikkei/HSI) + Europe (DAX/FTSE) direction, overnight gap | WebSearch |
| 7 | **Positioning / seasonality** | pre-FOMC drift, OpEx/triple-witching, day-of-week, month/quarter-end, holidays, sentiment extremes | known calendar |
| 8 | **Whale flow (index)** | SPY/QQQ put/call vol, OI walls (support/resistance magnets), 0DTE/weekly unusual skew | `Whale Check` (`market_data/whale_check.py SPY QQQ`) |

## Composite → next-day lean (sum −16 … +16)

| Score | Lean | Prob (Up / Flat / Down) |
|---|---|---|
| ≥ +6 | 🟢 UP (strong) | 60 / 25 / 15 |
| +2 … +5 | 🟢 UP (lean) | 50 / 30 / 20 |
| −1 … +1 | ⚪ FLAT / coin-flip | 38 / 34 / 28 |
| −5 … −2 | 🔴 DOWN (lean) | 20 / 30 / 50 |
| ≤ −6 | 🔴 DOWN (strong) | 15 / 25 / 60 |

### 🚦 Event veto
A binary event tomorrow (CPI/PPI/jobs/FOMC/major Fed speech/scheduled tariff/war decision) → **cap confidence at LOW, widen the range ×1.5, predict the reaction map (if hot→X / if cool→Y), not a single direction.**

### Magnitude (expected range)
**VIX-implied 1σ daily move = VIX ÷ 15.9 (%).** e.g. VIX 18 → ±1.13%. Range = close × (1 ± 1σ); ×1.5 on event days. Fallback: SPY ATR(14)%.

---

## Output format

```
Tomorrow — predicting {date}   (run {now})

1 Today ............ {±N}  SPY/QQQ/Dow closes; breadth; leaders; volume
2 AH/Futures ....... {±N}  ES/NQ drift; AH movers
3 Cross-asset ...... {±N}  oil, 10Y, VIX, DXY, BTC → risk on/off
4 News/Govt ........ {±N}  freshest WSJ/MW + admin/geopolitical
5 Calendar ......... {±N}  tomorrow's data/Fed/earnings | EVENT-VETO Y/N
6 Global/overnight . {±N}  Asia/Europe
7 Positioning ...... {±N}  pre-Fed/OpEx/day-of-week/month-end/holiday
8 Whale flow ....... {±N}  SPY/QQQ P/C vol; OI walls (magnets); 0DTE skew
──────────────────────────
BIAS {sum}/16 → LEAN {UP/FLAT/DOWN}  prob {U/F/D}
Expected SPY range {lo}–{hi} (±{x}% 1σ)
Key levels: SPY {sup}/{res} · QQQ {sup}/{res}
Swing factors: {1–3}
Confidence: {h/m/l}
Watchlist/positioning read: {1–2 lines}
```

---

## The plan to predict (calibration loop — this is the whole edge)

1. **Each evening** (post-close/AH): run the 7 blocks → produce the call.
2. **LOG IT** to `tomorrow_predictions_log.md` (date, lean, prob, range, levels, swing factors, score).
3. **Next close:** record the ACTUAL SPY move.
4. **Score:** direction-correct? in-range? → update rolling hit-rate.
5. **Weekly review:** down-weight blocks that mislead, up-weight blocks that nail it.
6. **Report the rolling hit-rate with every call** — confidence is earned. Target: beat the ~53% naive "up tomorrow" base rate.

## Worked example — predicting Monday June 15, 2026 (run Fri 6/12 PM)

```
1 Today ........... +1  Dow +0.70%/51,202, S&P +0.50%/7,431, Nasdaq +0.31%/25,889 (2nd up day);
                        Dow-led (VZ/GS/JPM), but MW flagged S&P internals weakening; Nasdaq lagged.
2 AH/Futures ...... 0   Quiet AH; SPCX afterglow but no broad futures catalyst.
3 Cross-asset ..... +1  Oil DOWN to ~$84 (Iran-deal hopes), risk-[REDACTED]; VIX subdued. Mild risk-[REDACTED].
4 News/Govt ....... +1  US–Iran peace odds >80% (oil↓); SpaceX IPO euphoria; AI-IPO pipeline buzz.
5 Calendar ........ -1  Mon: no US data. BUT FOMC Wed 6/17 (Warsh's 1st, hike-risk) → pre-Fed caution.
6 Global/overnight  0   Mixed Asia/Europe; nothing decisive over the weekend (headline risk only).
7 Positioning ..... -1  Pre-FOMC drift caps upside; 2-day rally prone to digestion; OpEx week.
──────────────────────────
BIAS +1/14 → LEAN ⚪ FLAT-to-slightly-UP   prob ~45 / 35 / 20
Expected SPY range ~7,390–7,475 (±~0.6%)
Key levels: SPY sup 7,394 (prev close)/7,363 (Fri low); res 7,456 (Fri high)/7,500 round
Swing factors: (1) Iran deal confirmed + oil soft = risk-[REDACTED]; (2) oil back >$90 or deal stumbles = risk-[REDACTED];
              (3) any hawkish Fed leak pre-meeting = high-beta sells.
Confidence: MEDIUM-LOW (weekend headline risk + pre-Fed positioning)
Watchlist read: calm-green Monday nudges HOOD toward $95 (helps the call debit spread), but the real
              test is Wed's FOMC — manage existing, don't add new longs into the Fed.
```

## Cross-reference
- Levels: `STKK` / `trade_entry_exit_algorithms.md` · Single-name: `stnow_algorithm.md`
- Macro gate + watchlist: `trading_watchlist.md` · Accounts: `account_profiles.md`
