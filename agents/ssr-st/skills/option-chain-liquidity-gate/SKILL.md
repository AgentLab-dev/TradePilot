---
name: option-chain-liquidity-gate
description: >-
  Rejects thin OI or a wide natural before a defined-risk debit. Cap $3–$4
  (tighter if the card says so). Report bid/ask/mid/natural/OI on both legs.
  ITM 10-wide that blows the cap is a stock-substitute reject. Use on PPS-T1
  structure, last-90 fill, HPE 55/60, MDB-style chain, HOOD 100/110, or when
  the user asks liquidity / natural / OI.
---

# Option-chain liquidity gate

A ticket that clears EM% still fails if the book cannot fill 1× inside the cap.
Run this on **every** debit before last-90 **go**.

## Report (both legs, every time)

| Field | How |
|---|---|
| Bid / ask / mark | Robinhood `get_option_quotes` |
| Mid debit | long mark − short mark |
| Open natural | long ask − short bid |
| Close natural | long bid − short ask |
| OI + volume | both legs |
| Cap | **$3.00–$4.00** unless the card is tighter (HPE 55/60 **$1.50**) |

Do not quote mid without natural. Do not call a name liquid without OI.

## Reject

| Fail | Lesson |
|---|---|
| Thin OI (single-digit / low tens on a leg) **or** natural that cannot work inside the cap | **MDB 500/510** — morning TAKE on a skinny far OTM; recapture moved the ticket to **490/500**. Do not fill the thin print |
| Open natural **> cap** | You cannot buy it at the cap. Reject or wait |
| Spread **> ~15%** of mid on either leg with OI too thin to cross | AGX 420C OI **5**, 17% wide → STAND on liquidity, not EM |
| **ITM 10-wide that blows the cap** | **HOOD 100/110** — that is a **stock-substitute**, not an OTM debit. Reject. Keep the OTM 10-wide that fits $3–$4 |

HPE 51/61 and 53/63 (OI ~62–155) were the same reject: near-ATM stock-sub /
thin short strike. Keep **55/60** (OI 15k / 13k) if mid and natural stay under
the **$1.50** card cap.

## Pass

- Both legs OI enough to fill 1× (hundreds+; walls in the thousands are the
  PPS call-wall bonus, not a requirement).
- Mid **and** open natural ≤ cap.
- Long strike is **OTM** (~0.7–1.0× EM), not ITM.

## Output

```
spread | long bid-ask (OI) | short bid-ask (OI) | mid | open natural | cap | PASS/REJECT
```

Work the mid. Do not fill at a panic natural. No **go** here.
