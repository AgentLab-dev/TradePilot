# FULLCHECK — Thu Aug 20, 2026 ~11:22 ET

Read-only. Marks from Robinhood ~11:22 ET / 8:22 AM PT. First 15–30 of Thursday cash ended 10:00 ET.

## Lead

**HOOD Sep 18 85/80 ×3 closed at the open for +$198.** The 50% GTC ($0.65 vs $1.31 open) filled 9:30:03 ET.

**Live risk is MS.** Sep 18 210/200 mid ~$3.17 vs $2.25 open. Cushion 1.2%. Session low $211.38. Abort $210 tag or mid ≥ $4.50.

**DE and WMT overnight cards are kills.** DE beat $5.10 vs $4.72 and is +7.7%; first 30 held the high side ($587.15–$608.66, last $607.44) but there was no go before 9:30, and 11:22 is a chase. WMT beat $0.81 vs $0.74 then dumped −9.3% on 2.6% US comps and a Q3 guide miss; the armed *call* was the wrong side; the put debit (105/100 ~$2.23) would have been the ticket in the first 30, not now.

Tonight’s ticket is **BJ Fri BMO**. WMT is a ≥5% bellwether dump and BJ prints tomorrow — that is the same-session-peer rule, not a COST chase.

## Tape ~11:22 ET

| | |
|---|---|
| SPX / SPY | 7681 / $766.58 (−0.32%) |
| QQQ / IWM / RSP | −0.54% / −0.96% / −0.05% |
| SMH / SOXX | +0.41% / +0.58% |
| VIX / VXX / 10Y | 15.78 / +1.08% / ~4.68% |
| Oil / BTC | +2.26% / +4.0% |
| GICS #1 / laggard | XLE +1.25% / XLY −1.50% (WMT) |
| Regime | Risk-[REDACTED]: yields reverse Wednesday’s buyback bounce; WMT hits the consumer tape; energy/oil bid |

MANGOS: META −0.61% · NVDA flat · GOOGL −1.57% · AMZN −1.96% · MSFT −0.69%. SPCX −5.0%.

## Book — margin ••••5611 ~$60,825

| Position | Structure | Marks | Plan |
|---|---|---|---|
| **MS** | Sep 18 210/200 ×1 | Spot $212.45. Mid ~$3.17. Short δ −0.42. GTC $1.25 | **Manage.** Abort $210 or mid ≥ $4.50 |
| **HOOD** | Sep 18 85/80 ×3 | **Closed** 9:30:03 ET @ $0.65 debit | **+$198 realized.** Do not re-enter |
| **MARA** | 100 sh @ $9.89 | Spot $10.66 (+10.5%) | Hold. New invalidation **$9.80**. No puts |
| **CRWD** | flat | Spot $192.57 (−4.5%) | Earn 8/26 blocks new credit |
| Fractionals | NIO / MU / etc. | noise | Ignore |

Agentic ••••1451 ~$1,178: 100 MARA @ $9.72, cash ~$110. Stand down the sleeve. Options_value 0.

## Health Check (daily.py --quick)

GO raw, then gates:

- **MRVL** +6, IV 83%, GO on pullback put credit → **blocked** (earn 8/27; extended; T+1 of Wed bounce)
- **MARA** +5, IV 89%, put credit → **override** (shares already on)
- **HOOD** +4, IV 63%, put credit → **stand down** (just closed the winner; dumped $101→$94.55 from the open)
- **XOM** GO call debit (cheap IV) → **not a take** (first 30 gone, +1.85%, risk-[REDACTED])
- **AVGO** GO call debit → **stand down** (NVDA 8/26 + AVGO earn **9/2**)
- **MS** AVOID (flow against) — matches the live book: manage, do not add
- **CRWD** WAIT value-trap — earn 8/26

## Event gate

No new credit through **Wed 8/26 AMC** (CRM / CRWD / NVDA / OKTA / VEEV) and **Thu 8/27 AMC** (MRVL / IREN / WDAY). INTU / ZM / DKS print **Tue 8/25** — cards Monday night. Radar also: CRDO / DELL / PANW 9/1, AVGO / HPE / SNOW / NTAP / ZS 9/2–9/3.

No US investor/analyst/capital-markets day Fri–Mon on book or SMH/memory. MRVL Investor Day is **Tue Oct 6**.

## Ranked plan (read-only until you say go)

1. **MS** — manage. Abort $210 / mid ≥ $4.50.
2. **HOOD** — closed +$198. Do not replace.
3. **MARA** — hold shares / no puts. Invalidation $9.80.
4. **BJ** — **arm tonight** for Fri 8/21 BMO. 1× Sep 18 90/95 (or 90/85 if dump), cap $2.50. Recap 7:00 AM PT. Flatten Friday.
5. **No cash take Thursday.** DE / WMT / EL / MRVL / COST / XOM are chases or blocked.

## SelfIDB50 overlay

XLE still leads the 11 GICS. WMT took XLY/XLP with it. Do not promote MARA or MRVL off a one-day rip. Energy (XOM) is the Health Check diversifier and is **not** a 11:22 take.

Write-up also at repo `Documents/catalyst_cards.md` + `Documents/next_day_prep.md`.
