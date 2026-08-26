"""FULL CHECK universe snapshot (Tue 25 Aug 2026 ~5:15 PM PT)."""

from __future__ import annotations

from typing import Any

AS_OF = "Tue 25 Aug 2026 ~5:15 PM PT"
SOURCE = "Health Check composite + catalyst-overnight-plan. Prices: daily.py live marks ~5:11 PT. Whale/IV: live Nasdaq chain."

STATS = {
    "actionable": "INTU",
    "gated_top": "5",
    "names": "24",
    "structures": "6",
}

CALLOUT = (
    "NVDA, GOOGL, and AMZN are the highest composite scores. PCE Wednesday "
    "8:30 ET and NVDA/CRWD/CRM after the close block new credits and Mag-7 "
    "call debits. The only first-30 tickets tomorrow are INTU and ZM. Need "
    "go before 9:30 ET."
)

TOP5: list[dict[str, str]] = [
    {
        "rank": "1",
        "ticker": "INTU",
        "why": "Beat-and-dump -10% AH. Same shape as WMT 8/20. Card exists.",
        "stkk": "RANGE",
        "stnow": "raw-3",
        "three_good": "no",
        "whale": "BEARISH",
        "iv_structure": "put debit 320/310 cap $4.00",
        "event": "printed AMC",
        "after_gate": "ARM Wed 9:30-10:00. Recalibrate 7:00 AM PT",
        "tone": "arm",
    },
    {
        "rank": "2",
        "ticker": "ZM",
        "why": "Beat, soft Q3, AH -4.8%. Secondary to INTU.",
        "stkk": "UP, thin R:R",
        "stnow": "raw+0",
        "three_good": "no",
        "whale": "BEARISH",
        "iv_structure": "put debit cap $2.50",
        "event": "printed AMC",
        "after_gate": "ARM Wed first-30 if dump holds",
        "tone": "arm",
    },
    {
        "rank": "3",
        "ticker": "NVDA",
        "why": "Best model (+6, whale BULLISH, IV 41% cheap). Binary tomorrow.",
        "stkk": "UP, thin R:R",
        "stnow": "GO raw+4",
        "three_good": "IV 41% <50%",
        "whale": "BULLISH",
        "iv_structure": "call debit if rip; put if dump",
        "event": "Wed AMC $2.09",
        "after_gate": "ARM Thu first-30. No credit. Do not buy AH Wed",
        "tone": "gated",
    },
    {
        "rank": "4",
        "ticker": "CRM",
        "why": "INTU dumped >=5% and CRM still prints. MU to SNDK rule.",
        "stkk": "RANGE",
        "stnow": "raw+1",
        "three_good": "IV 50% ok",
        "whale": "lean-bull",
        "iv_structure": "10-wide debit cap $4.00",
        "event": "Wed AMC $3.09",
        "after_gate": "ARM Thu first-30. Not a NOW/DDOG/SNOW chase",
        "tone": "arm",
    },
    {
        "rank": "5",
        "ticker": "MS",
        "why": "Open book. Cushion 3.1% (was 1.2%). Model wants more; book says no.",
        "stkk": "RANGE",
        "stnow": "GO raw+2",
        "three_good": "IV 29% <50%",
        "whale": "BULLISH",
        "iv_structure": "live 210/200 PCS mid ~$2.32",
        "event": "PCE; earn Oct 14",
        "after_gate": "MANAGE. GTC $1.25. Abort $210 or mid >= $4.50",
        "tone": "manage",
    },
]

MODEL_TOP5: list[list[str]] = [
    ["1", "NVDA", "+6", "BULLISH", "41%", "call debit", "Earn Wed AMC"],
    ["2", "GOOGL", "+6", "BULLISH", "28%", "call debit", "PCE 8:30 ET"],
    ["3", "AMZN", "+5", "lean-bull", "29%", "call debit", "PCE 8:30 ET"],
    ["4", "HOOD", "GO pullback", "BULLISH", "72%", "put credit on dip", "PCE + NVDA week; PCS already closed"],
    ["5", "AVGO / MS / MRVL", "GO-on-conf", "bull / lean-bull", "50% / 29% / 82%", "credit or debit", "AVGO earn 9/2 · MS already on · MRVL earn Thu"],
]

STRATEGIES: list[list[str]] = [
    ["Bull + cheap IV", "Call debit", "NVDA, GOOGL, AMZN, MS, TSM"],
    ["Bull + rich IV", "Put credit on a hold", "HOOD, SMCI, MU, AVGO, MRVL, AMD, CRWV — all gated this week"],
    ["Bear + cheap IV", "Put debit", "INTU, ZM (catalyst). META if trap clears"],
    ["Bear + rich IV", "Call credit", "None. No confirmed breakdown ticket"],
    ["Range + rich IV", "Iron condor", "SMCI model only — do not take extended"],
    ["Range + cheap IV", "Calendar / stand-down", "CRM pre-print, GOOGL into PCE"],
]

INDUSTRIES: list[tuple[str, str]] = [
    ("AI compute / semis", "NVDA, AVGO, MRVL, SMCI, MU, AMD, TSM, CRWV. SMH +1.65% today. NVDA print is the gate."),
    ("Software / SaaS", "INTU dump, ZM dump, CRM/OKTA/VEEV/SNOW/ORCL/MSFT. INTU is the live software tell."),
    ("Internet / Mag-7", "GOOGL, AMZN, META. Model likes GOOGL/AMZN; PCE kills a Wednesday take. META is a value-trap."),
    ("Other", "Financials MS (manage) + HOOD (blocked). Crypto MARA (shares, no puts). Retail DKS (kill). Cyber CRWD/OKTA (Thu debit only)."),
]

NAMES: list[dict[str, str]] = [
    {"ticker": "INTU", "px": "357.46 RTH / 322 AH", "industry": "Software / SaaS", "stkk": "RANGE", "stnow": "raw-3", "three_good": "no (bearish dump)", "whale": "BEARISH", "iv": "rich into print", "structure": "put debit 320/310", "event": "printed AMC; FY27 9-10% guide", "model": "AVOID/WAIT", "after_gate": "ARM Wed first-30, cap $4.00", "tone": "arm"},
    {"ticker": "ZM", "px": "100.92 RTH / 96 AH", "industry": "Software / SaaS", "stkk": "UP, thin R:R", "stnow": "raw+0", "three_good": "no (bearish)", "whale": "BEARISH", "iv": "61%", "structure": "put debit 100/95 or 95/90", "event": "printed AMC; soft Q3", "model": "AVOID/WAIT", "after_gate": "ARM Wed first-30, cap $2.50", "tone": "arm"},
    {"ticker": "NVDA", "px": "213.05", "industry": "AI compute / semis", "stkk": "UP, thin R:R", "stnow": "GO raw+4", "three_good": "no (IV 41% <50%)", "whale": "BULLISH", "iv": "41%", "structure": "call debit (cheap IV)", "event": "Wed 8/26 AMC street $2.09", "model": "GO-on-confirmation +6", "after_gate": "ARM Thu first-30, cap $4.00. No credit", "tone": "gated"},
    {"ticker": "CRM", "px": "205.69", "industry": "Software / SaaS", "stkk": "RANGE", "stnow": "raw+1", "three_good": "yes (IV 50%)", "whale": "lean-bull", "iv": "50%", "structure": "10-wide debit after print", "event": "Wed 8/26 AMC; INTU dump read-through", "model": "NEUTRAL", "after_gate": "ARM Thu first-30, cap $4.00", "tone": "arm"},
    {"ticker": "MS", "px": "216.77", "industry": "Financials", "stkk": "RANGE", "stnow": "GO raw+2", "three_good": "no (IV 29% <50%)", "whale": "BULLISH", "iv": "29%", "structure": "call debit (model) / live PCS 210/200", "event": "next earn Oct 14; PCE tomorrow", "model": "GO-on-confirmation", "after_gate": "MANAGE. Abort $210 or mid >= $4.50. Do not add", "tone": "manage"},
    {"ticker": "CRWD", "px": "185.38", "industry": "Cyber", "stkk": "DOWN, oversold", "stnow": "TRAP raw+2", "three_good": "IV ok, sell at support", "whale": "lean-bull", "iv": "61%", "structure": "185/195 call debit if hold; put if dump", "event": "Wed 8/26 AMC street $0.24", "model": "WAIT value-trap", "after_gate": "ARM Thu debit only. No credit replace of -$340", "tone": "arm"},
    {"ticker": "GOOGL", "px": "346.96", "industry": "Internet / Mag-7", "stkk": "RANGE", "stnow": "GO raw+4", "three_good": "no (IV 28% <50%)", "whale": "BULLISH", "iv": "28%", "structure": "call debit", "event": "PCE Wed 8:30. No name print", "model": "GO-on-confirmation +6", "after_gate": "STAND DOWN into PCE", "tone": "gated"},
    {"ticker": "AMZN", "px": "261.06", "industry": "Internet / Mag-7", "stkk": "UP, thin R:R", "stnow": "GO raw+4", "three_good": "no (IV 29% <50%)", "whale": "lean-bull", "iv": "29%", "structure": "call debit", "event": "PCE Wed 8:30", "model": "GO-on-confirmation +5", "after_gate": "STAND DOWN into PCE", "tone": "gated"},
    {"ticker": "HOOD", "px": "112.09", "industry": "Financials", "stkk": "UP trend, room", "stnow": "GO raw+3", "three_good": "yes (IV 72%)", "whale": "BULLISH", "iv": "72%", "structure": "put credit on a dip", "event": "PCE + NVDA week. Next earn ~Nov 4", "model": "GO on pullback", "after_gate": "STAND DOWN. Do not replace closed PCS", "tone": "gated"},
    {"ticker": "AVGO", "px": "356.74", "industry": "AI compute / semis", "stkk": "RANGE", "stnow": "GO raw+3", "three_good": "yes (IV 50%)", "whale": "lean-bull", "iv": "50%", "structure": "put credit (rich) / call debit (daily.py)", "event": "earn Sep 2 — Sep 18 credit blocked", "model": "GO-on-confirmation", "after_gate": "STAND DOWN this week", "tone": "gated"},
    {"ticker": "MRVL", "px": "240.38", "industry": "AI compute / semis", "stkk": "UP trend, room", "stnow": "GO raw+3", "three_good": "yes (IV 82%)", "whale": "lean-bull", "iv": "82%", "structure": "put credit (blocked)", "event": "Thu 8/27 AMC. Investor Day Oct 6", "model": "GO-on-confirmation", "after_gate": "Card Wed night. Do not buy +4.8% bounce", "tone": "gated"},
    {"ticker": "SMCI", "px": "38.46", "industry": "AI compute / semis", "stkk": "RANGE, extended", "stnow": "GO raw+2", "three_good": "yes (IV 83%)", "whale": "BULLISH", "iv": "83%", "structure": "put credit on a dip", "event": "no print Wed; NVDA peer +9.4% today", "model": "GO on pullback", "after_gate": "DO NOT CHASE T+1", "tone": "kill"},
    {"ticker": "TSM", "px": "417.41", "industry": "AI compute / semis", "stkk": "RANGE", "stnow": "raw+1", "three_good": "no (IV 35% <50%)", "whale": "lean-bull", "iv": "35%", "structure": "call debit", "event": "NVDA peer, lagging +1.8%", "model": "NEUTRAL", "after_gate": "DO NOT CHASE T+1", "tone": "neutral"},
    {"ticker": "AMD", "px": "479.18", "industry": "AI compute / semis", "stkk": "RANGE", "stnow": "raw+0", "three_good": "yes (IV 58%)", "whale": "NEUTRAL", "iv": "58%", "structure": "put credit if GO", "event": "NVDA peer +4.9%; no print Wed", "model": "NEUTRAL", "after_gate": "DO NOT CHASE T+1", "tone": "neutral"},
    {"ticker": "MU", "px": "932.97", "industry": "AI compute / semis", "stkk": "RANGE", "stnow": "raw+1", "three_good": "yes (IV 66%)", "whale": "BULLISH", "iv": "66%", "structure": "put credit on confirmation", "event": "no 0d/1d print", "model": "NEUTRAL", "after_gate": "WAIT. PCE week", "tone": "neutral"},
    {"ticker": "META", "px": "570.05", "industry": "Internet / Mag-7", "stkk": "DOWN trend", "stnow": "TRAP raw+2", "three_good": "no (IV 36% <50%)", "whale": "BULLISH", "iv": "36%", "structure": "put debit if trap clears", "event": "value-trap gate", "model": "WAIT value-trap", "after_gate": "STAND DOWN", "tone": "avoid"},
    {"ticker": "MSFT", "px": "491.71", "industry": "Software / SaaS", "stkk": "RANGE", "stnow": "raw-2", "three_good": "no (IV 26% <50%)", "whale": "BEARISH", "iv": "26%", "structure": "none", "event": "flow against", "model": "AVOID/WAIT", "after_gate": "STAND DOWN", "tone": "avoid"},
    {"ticker": "ORCL", "px": "144.76", "industry": "Software / SaaS", "stkk": "RANGE", "stnow": "raw+0", "three_good": "no (flow bearish)", "whale": "BEARISH", "iv": "70%", "structure": "none", "event": "earn Sep 8; STKK downtrend = no put sell", "model": "AVOID/WAIT", "after_gate": "STAND DOWN", "tone": "avoid"},
    {"ticker": "SNOW", "px": "317.02", "industry": "Software / SaaS", "stkk": "UP, thin R:R", "stnow": "raw-1", "three_good": "no (flow bearish)", "whale": "BEARISH", "iv": "70%", "structure": "none", "event": "earn Sep 2. INTU peer with no Wed print", "model": "AVOID/WAIT", "after_gate": "DO NOT CHASE T+1", "tone": "avoid"},
    {"ticker": "OKTA", "px": "130.61", "industry": "Cyber", "stkk": "RANGE", "stnow": "raw-1", "three_good": "no (bearish)", "whale": "BEARISH", "iv": "n/a cache", "structure": "10-wide debit if named after print", "event": "Wed 8/26 AMC street $0.86", "model": "AVOID/WAIT", "after_gate": "ARM only if NVDA/CRWD/CRM already fired", "tone": "arm"},
    {"ticker": "VEEV", "px": "246.78", "industry": "Software / SaaS", "stkk": "RANGE", "stnow": "raw-4", "three_good": "no (flow bearish)", "whale": "BEARISH", "iv": "56%", "structure": "10-wide debit if named", "event": "Wed 8/26 AMC street $2.10", "model": "AVOID/WAIT", "after_gate": "ARM only if leads already fired", "tone": "arm"},
    {"ticker": "DKS", "px": "124.31", "industry": "Retail", "stkk": "RANGE", "stnow": "raw+1", "three_good": "n/a", "whale": "NEUTRAL", "iv": "n/a cache", "structure": "would have been 10-wide debit", "event": "BMO miss $3.53 vs $3.88", "model": "NEUTRAL", "after_gate": "KILL. First-30 gone", "tone": "kill"},
    {"ticker": "MARA", "px": "11.83", "industry": "Crypto", "stkk": "RANGE", "stnow": "raw+0", "three_good": "no (flow bearish)", "whale": "BEARISH", "iv": "98%", "structure": "shares + covered calls. No puts", "event": "next earn ~Nov 3", "model": "AVOID/WAIT", "after_gate": "HOLD SHARES. Personal Sep 4 11C ITM", "tone": "manage"},
    {"ticker": "CRWV", "px": "88.04", "industry": "AI compute / semis", "stkk": "DOWN trend", "stnow": "TRAP raw+0", "three_good": "yes (IV 77%)", "whale": "lean-bull", "iv": "77%", "structure": "put credit on dip if trap clears", "event": "NVDA peer; value-trap", "model": "WAIT value-trap", "after_gate": "DO NOT CHASE T+1", "tone": "avoid"},
]

LEGEND = (
    "ARM — catalyst debit, wait for first-30 + go. "
    "GATED — model GO, event/book kills it. "
    "MANAGE — live position. "
    "NEUTRAL — wait. "
    "AVOID / KILL / DO NOT CHASE. "
    "Whale is prior-session volume; stale on a live catalyst. "
    "Three Good requires IV at least 50%, whale score at least 0, and not an active downtrend. "
    "Cache STKK last bar 8/14; prices are daily.py live marks from 5:11 PT. Read-only until go."
)


def snapshot() -> dict[str, Any]:
    return {
        "title": "FULL CHECK universe",
        "as_of": AS_OF,
        "source": SOURCE,
        "stats": STATS,
        "callout": CALLOUT,
        "top5": TOP5,
        "model_top5": MODEL_TOP5,
        "strategies": STRATEGIES,
        "industries": INDUSTRIES,
        "names": NAMES,
        "legend": LEGEND,
    }
