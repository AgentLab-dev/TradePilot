# FULLCHECK — Thursday 13 Aug 2026 · ~9:10 AM PT

Account **••••5611** (margin L3) · value **$61,002** · cash **$61,426** · options mark **−$1,383** · BP **$223k** / unlev **$55.6k**.
Read-only. No new orders placed.

## Bottom line

Chips still lead (SMH **+1.6%**, QQQ **+1.0%**). Everything AI is extended. **No new credit sells today** — Applied Materials prints after the close, and yesterday’s Oracle ticket fails both the trend gate and the $1.50 credit floor.

**First action: buy back the Marathon Aug 21 $10.50 call @ ≤ $0.12** (mark $0.11 vs $0.24 sold). That is the green close. Keep the 100 shares. Weekly close stop still **<$9**.

**Watch Newmont.** Gold −1.2%, NEM −3.4% to **$113.78**. Short $110 has **3.3% cushion**. Abort same session if $110 tags or mid ≥ **$4.50**.

## Tape / macro

| | Px | Day |
|---|---:|---:|
| SPX | 7784 | +0.46% |
| QQQ | 731 | +1.05% |
| SMH | 594 | +1.64% |
| DIA | 536 | −0.16% |
| VIX | 14.69 | +1.0% (still low) |
| 10Y | 4.64 | −0.88% |
| Gold | GLD $400 | −1.20% |
| Oil | $82.59 | −0.82% |

Tilt: **mixed** — Nasdaq/chips risk-[REDACTED], gold/oil/Dow risk-[REDACTED], VIX ticking up from a 14-handle.

### GICS (no tech-first)

Leaders: XLRE +1.09% · XLK +1.04% · XLC +1.02% · XLP +0.82%.
Laggards: XLI −0.40% · XLB −0.32% · XLF −0.16% · XLE −0.11%.

### MANGOS

META +1.2% · NVDA +0.4% · GOOGL +0.5% · **SPCX −3.3%** (diverges) · AMZN −0.5% · MSFT +0.5%.

## Book

| Position | Spot | Cushion | Open → mid | uPnL | Call |
|---|---:|---:|---:|---:|---|
| CRWD Aug 21 **210/200** ×2 | $222.69 | 5.7% | $1.65 → $1.36 | **+$58** | Hold. 50% = $0.83. Expires before 8/26 print. Δ −0.21. |
| NEM Sep 18 **110/100** ×2 | $113.78 | **3.3%** | $2.26 → $2.86 | **−$120** | **Watch.** Abort $110 tagged or mid ≥ $4.50 (2×). Δ −0.36. |
| HOOD Sep 18 **85/80** ×3 | $97.79 | 15% | $1.31 → $0.93 | **+$114** | Hold. 50% = $0.66. Abort mid ≥ $2.60. |
| MS Sep 18 **210/200** ×1 | $218.99 | 4.1% | $2.25 → $2.32 | −$7 | Hold. 50% = $1.13. IV thin ~29%. |
| MARA **100 sh** | $9.31 | vs $9.89 | — | −$58 | Weekly close stop **<$9**. |
| MARA Aug 21 **$10.50C** ×1 | OTM | — | $0.24 → $0.11 | **+$13** | **Take.** BTC ≤ $0.12. |

CRWD / NEM / HOOD / MS shorts show pending buy + longs pending sell — 50% GTC closes still resting.

Do **not** sell puts on MARA on top of shares + the call.

## Event gate

| When | Name | Note |
|---|---|---|
| **Today AMC** | **AMAT** | Est $3.39. Whale lean-bear. No credit sell. |
| Today AM | **XE** | Miss: −$0.21 vs −$0.09. Stock +5%. Whale bearish. Skip. |
| Today | **SNDK investor day** | SNDK **+15%**, WDC **+8.4%**, STX **+4.3%**. Window to play same-day is closed. Do not chase (MU→SNDK lesson). |
| 8/26 AMC | NVDA · CRWD · CRM · OKTA | CRWD Aug 21 dies first — keep. No new CRWD. |
| 8/27 AMC | MRVL · WDAY · S | Software lag. Stand down. |
| 9/1–9/3 | PANW · HPE · AVGO · SNOW · DELL · ZS | Sep put-credit blocked. |

## Health Check (daily.py) — with overrides

Ranked GO: MARA +7 · MPC +6 · HPE +5.

| Name | Model | Override |
|---|---|---|
| MARA | STRONG GO put credit, IV 79% | **No.** Already long stock + short $10.50C. |
| MPC | GO call debit, IV 40% | **Arm.** Only clean non-tech GO. Next earn 11/3. Do not fire at $351. |
| HPE / SMCI / DELL | GO on pullback, rich IV | Still extended (HPE $61 / SMCI $40.6 / DELL $497). Sep blocked. |
| NVDA | GO-on-confirmation call debit, IV ~32% | **Arm** Aug 21 225/230 ≤ **$1.80**. Mark **$2.06** — wait. |
| ORCL | Whale +2, STKK **downtrend trap** | **Stand down.** Aug 28 145/140 credit now **$1.38** (below $1.50). Same fade pattern as UNH. |
| LLY | GO call debit, IV ~34% | Fill quality was 16–20% wide last week. Arm, don’t chase $1,216. |
| AMAT / XE / CRWD add / WDAY | AVOID | Event or book concentration. |

## SelfIDB50

FFTY top-25 (as of Aug 6) is still **healthcare / fintech**: SEZL, ENVA, LQDA, CARE, SN. Only DDOG and NET in the top 25 as tech. The live tape is chips and memory. Do not force FFTY names onto a chip day, and do not chase chips that already moved 8–15%.

## Route

- Bull + high IV, extended → **wait for pullback** (HPE/SMCI/DELL). Sep still blocked.
- Bull + low IV → **call debit** (NVDA, MPC, LLY) only on a hold, not a rip.
- ORCL whale bull + STKK down → **do not sell puts into a downtrend**.
- SNDK/WDC same-day momentum → **too late**; next-day chase is where the 6/26 loss lived.

No new structure promoted to “fire now,” so the multi-strategy backtest was not re-run. Call-debit still has the higher expectancy sleeve (~4× put credit in the v2 matrix).

## Action tickets (wait for go)

1. **BTC MARA Aug 21 $10.50C ×1 @ ≤ $0.12** — lock ~$12–13, keep shares.
2. **NEM abort line** — if $110 trades or 110/100 mid ≥ $4.50, BTC the 2× same session.
3. Nothing else until AMAT prints and NEM either holds $114 or is closed.

Write-up path confirmed. Canvas: `fullcheck-2026-08-13`.
