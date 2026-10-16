"""Desk process checks from the 2026-10-16 playbook update.

Pure functions. No network, no orders, no credentials. Callers supply live
quotes. This module classifies the regime, checks a pre-trade card, appends
the prediction ledger, scores outcomes, and decides whether a gate may change.

Units:
- returns, EM, and realized move are decimals (0.015 = 1.5%, 0.15 = 15%)
- ``p_pct`` is an integer percent on a 5-point step (55 means 55%)
- ``max_loss_pct_of_budget`` is a decimal (0.01 = 1% of the desk risk budget)
- VIX is the index level; ``vix_5d_change`` is points
- 10Y is a percent yield (4.20); ``ten_year_5d_bp`` is basis points
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field, replace
from pathlib import Path

HARD_FIVE_RULE = "em_gt_15_all_four"
MIN_CASES = 8
MIN_SESSIONS = 10
LOOSEN_WINDOW = 20
MIN_RR = 2.0
RICH_EM = 1.25
CHEAP_EM = 0.8
MISS_MOVE = 0.05

PREDICTION_COLUMNS = [
    "logged_pt",
    "run",
    "ticker",
    "kind",
    "direction",
    "structure",
    "entry",
    "stop",
    "target",
    "horizon_sessions",
    "p_pct",
    "regime",
    "gate_verdict",
    "thesis",
]
OUTCOME_COLUMNS = [
    "outcome",
    "underlying_return",
    "spy_return",
    "scored_pt",
]
LEDGER_COLUMNS = PREDICTION_COLUMNS + OUTCOME_COLUMNS

# Grok Bot box path named by the updated skills. This checkout stores the
# ledger under the trading documents folder; set TRADEPILOT_LEDGER to override.
GROK_BOX_LEDGER = Path("/workspace/tradepilot-ledger.csv")

_REAL_KINDS = {"real"}
_ARMED = {"take", "arm", "soft-arm"}
_STAND = {"stand", "stand-down"}


def default_ledger_path() -> Path:
    """Repo ledger path, or ``TRADEPILOT_LEDGER`` when set."""
    override = os.environ.get("TRADEPILOT_LEDGER")
    if override:
        return Path(override)
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "agents" / "ssr-st").is_dir():
            return (
                parent
                / "agents"
                / "ssr-st"
                / "workspace"
                / "Documents"
                / "tradepilot-ledger.csv"
            )
    return Path("agents/ssr-st/workspace/Documents/tradepilot-ledger.csv")


def vix_band(vix: float) -> str:
    """<15 calm, 15–20 normal, 20–25 elevated, >25 stress. 20 starts elevated."""
    if vix < 15:
        return "calm"
    if vix < 20:
        return "normal"
    if vix <= 25:
        return "elevated"
    return "stress"


def trend_vs_mas(spy: float, ma20: float, ma50: float) -> str:
    """up when price is above both averages, down when below both, else chop."""
    if spy > ma20 and spy > ma50:
        return "up"
    if spy < ma20 and spy < ma50:
        return "down"
    return "chop"


@dataclass(frozen=True)
class RegimeRead:
    trend: str
    vix: float | None
    vix_5d_change: float | None
    vix_band: str | None
    ten_year: float | None
    ten_year_5d_bp: float | None
    rsp_5d: float | None
    spy_5d: float | None
    breadth: float | None
    pct_above_50d: float | None
    leader_etf: str | None
    leader_5d: float | None
    laggard_etf: str | None
    laggard_5d: float | None
    verdict: str
    size_cap: float
    prefer_spreads: bool
    widen_stops: bool
    bearish_needs_catalyst: bool
    stale_fields: tuple[str, ...] = ()

    def block(self) -> str:
        return format_regime(self)


def _stale(name: str, stale_fields: set[str]) -> bool:
    return name in stale_fields


def read_regime(
    *,
    spy: float | None = None,
    ma20: float | None = None,
    ma50: float | None = None,
    vix: float | None = None,
    vix_5d_change: float | None = None,
    ten_year: float | None = None,
    ten_year_5d_bp: float | None = None,
    rsp_5d: float | None = None,
    spy_5d: float | None = None,
    pct_above_50d: float | None = None,
    leader_etf: str | None = None,
    leader_5d: float | None = None,
    laggard_etf: str | None = None,
    laggard_5d: float | None = None,
    stale_fields: list[str] | tuple[str, ...] | None = None,
) -> RegimeRead:
    """Classify RISK-ON / NEUTRAL / RISK-OFF from trend, VIX, and breadth.

    RISK-OFF when the trend is down, VIX is in stress (>25), or VIX is
    elevated and breadth is negative while trend is not up.
    RISK-ON when trend is up, VIX is under 20, and RSP has not lagged SPY.
    A stale trend or VIX cannot be labeled RISK-ON. Stress VIX is still
    RISK-OFF when the level itself was supplied.
    """
    stale = tuple(stale_fields or ())
    stale_set = set(stale)
    trend_missing = spy is None or ma20 is None or ma50 is None
    trend_stale = trend_missing or any(_stale(n, stale_set) for n in ("spy", "ma20", "ma50", "trend"))
    if trend_stale:
        trend = "stale"
    else:
        trend = trend_vs_mas(spy, ma20, ma50)  # type: ignore[arg-type]

    vix_stale = vix is None or _stale("vix", stale_set)
    band = None if vix is None else vix_band(vix)
    breadth = None
    if rsp_5d is not None and spy_5d is not None and not (
        _stale("rsp_5d", stale_set) or _stale("spy_5d", stale_set)
    ):
        breadth = rsp_5d - spy_5d

    if vix is not None and vix > 25:
        verdict = "RISK-OFF"
    elif trend_stale or vix_stale or breadth is None:
        verdict = "RISK-OFF" if trend == "down" else "NEUTRAL"
    elif trend == "down":
        verdict = "RISK-OFF"
    elif vix >= 20 and trend != "up" and breadth < 0:  # type: ignore[operator]
        verdict = "RISK-OFF"
    elif trend == "up" and vix < 20 and breadth >= 0:  # type: ignore[operator]
        verdict = "RISK-ON"
    else:
        verdict = "NEUTRAL"

    stress = vix is not None and vix > 25
    size_cap = 0.005 if verdict == "RISK-OFF" or stress else 0.01
    prefer = vix is not None and vix > 20
    return RegimeRead(
        trend=trend,
        vix=vix,
        vix_5d_change=vix_5d_change,
        vix_band=band,
        ten_year=ten_year,
        ten_year_5d_bp=ten_year_5d_bp,
        rsp_5d=rsp_5d,
        spy_5d=spy_5d,
        breadth=breadth,
        pct_above_50d=pct_above_50d,
        leader_etf=leader_etf,
        leader_5d=leader_5d,
        laggard_etf=laggard_etf,
        laggard_5d=laggard_5d,
        verdict=verdict,
        size_cap=size_cap,
        prefer_spreads=prefer,
        widen_stops=prefer,
        bearish_needs_catalyst=verdict == "RISK-ON",
        stale_fields=stale,
    )


def _pct(value: float | None, digits: int = 1) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:+.{digits}f}%"


def _num(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"


def format_regime(read: RegimeRead) -> str:
    vix_change = ""
    if read.vix_5d_change is not None:
        vix_change = f" ({read.vix_5d_change:+.1f} 5d)"
    band = f" {read.vix_band}" if read.vix_band else ""
    ten_change = ""
    if read.ten_year_5d_bp is not None:
        ten_change = f" ({read.ten_year_5d_bp:+.0f}bp 5d)"
    breadth = "n/a" if read.breadth is None else f"{read.breadth * 100:+.1f}pp"
    above = "n/a" if read.pct_above_50d is None else f"{read.pct_above_50d * 100:.0f}% above 50d"
    leader = read.leader_etf or "n/a"
    laggard = read.laggard_etf or "n/a"
    parts = [
        f"trend: SPY vs 20d/50d MA = {read.trend}",
        f"VIX {_num(read.vix)}{vix_change}{band}",
        f"10Y {_num(read.ten_year)}{ten_change}",
        f"breadth: RSP vs SPY 5d {breadth}, {above}",
        f"leaders: {leader} {_pct(read.leader_5d)} / laggard {laggard} {_pct(read.laggard_5d)}",
        f"verdict: {read.verdict}",
    ]
    text = "REGIME | " + " | ".join(parts)
    if read.stale_fields:
        text += " | STALE: " + ",".join(read.stale_fields)
    return text


@dataclass
class TradeCard:
    ticker: str
    direction: str
    thesis: str = ""
    catalyst: str | None = None
    entry: float | None = None
    stop: float | None = None
    target: float | None = None
    structure_max_gain: float | None = None
    structure_max_loss: float | None = None
    em: float | None = None
    realized_move: float | None = None
    max_loss_pct_of_budget: float | None = None
    p_pct: int | None = None
    regime: str | None = None
    vix: float | None = None
    open_event_tickets: int | None = None
    theme: str | None = None
    open_themes: list[str] = field(default_factory=list)
    structure: str = ""
    horizon_sessions: int | None = None
    gate_verdict: str = ""
    verdict: str = "paper"
    kind: str = "paper"
    run: str = ""
    logged_pt: str = ""


@dataclass(frozen=True)
class ChecklistResult:
    ok: bool
    incomplete: bool
    reasons: tuple[str, ...]
    underlying_rr: float | None
    structure_rr: float | None
    premium_bias: str
    expected_value: float | None
    size_cap: float


def _underlying_rr(card: TradeCard) -> float | None:
    if card.entry is None or card.stop is None or card.target is None:
        return None
    if card.direction == "bull" and card.target > card.entry > card.stop:
        risk = card.entry - card.stop
        return (card.target - card.entry) / risk
    if card.direction == "bear" and card.stop > card.entry > card.target:
        risk = card.stop - card.entry
        return (card.entry - card.target) / risk
    return None


def _structure_rr(card: TradeCard) -> float | None:
    gain = card.structure_max_gain
    loss = card.structure_max_loss
    if gain is None or loss is None or loss <= 0 or gain <= 0:
        return None
    return gain / loss


def _premium_bias(em: float | None, realized: float | None) -> str:
    if em is None or realized is None or realized <= 0:
        return "unknown"
    ratio = em / realized
    if ratio > RICH_EM:
        return "avoid long premium; prefer spreads"
    if ratio < CHEAP_EM:
        return "long premium is cheap"
    return "fair"


def _size_cap(regime: str | None, vix: float | None) -> float:
    if regime == "RISK-OFF" or (vix is not None and vix > 25):
        return 0.005
    return 0.01


def _expected_value(p_pct: int | None, gain: float | None, loss: float | None) -> float | None:
    if p_pct is None or gain is None or loss is None:
        return None
    p = p_pct / 100
    return p * gain - (1 - p) * loss


def check_card(card: TradeCard) -> ChecklistResult:
    """Pre-trade checklist. ``ok`` is false when any required line fails."""
    reasons: list[str] = []
    if not (card.thesis or "").strip():
        reasons.append("missing thesis")
    direction = (card.direction or "").lower()
    if direction not in {"bull", "bear", "neutral"}:
        reasons.append("direction must be bull, bear, or neutral")
    catalyst = card.catalyst
    if catalyst is None or str(catalyst).strip() == "":
        reasons.append("missing catalyst")
    elif str(catalyst).strip().lower() == "none":
        thesis = (card.thesis or "").lower()
        if "trend" not in thesis and "mean-reversion" not in thesis and "mean reversion" not in thesis:
            reasons.append("catalyst none requires a trend or mean-reversion thesis")
    if card.regime == "RISK-ON" and direction == "bear" and (
        catalyst is None or str(catalyst).strip().lower() in {"", "none"}
    ):
        reasons.append("RISK-ON bearish idea needs a named catalyst")

    urr = _underlying_rr(card)
    srr = _structure_rr(card)
    if card.entry is None or card.stop is None or card.target is None:
        reasons.append("missing entry, stop, or target")
    elif urr is None:
        reasons.append("levels do not match the direction")
    elif urr < MIN_RR:
        reasons.append(f"underlying risk-reward {urr:.2f} is below 2:1")
    if srr is None:
        reasons.append("missing structure max gain and max loss")
    elif srr < MIN_RR:
        reasons.append(f"structure risk-reward {srr:.2f} is below 2:1")

    bias = _premium_bias(card.em, card.realized_move)
    if card.em is None or card.realized_move is None:
        reasons.append("missing implied versus realized move")

    cap = _size_cap(card.regime, card.vix)
    if card.max_loss_pct_of_budget is None:
        reasons.append("missing position size")
    elif card.max_loss_pct_of_budget > cap + 1e-12:
        reasons.append(f"position size {card.max_loss_pct_of_budget:.4f} exceeds {cap:.4f}")
    if card.open_event_tickets is not None and card.open_event_tickets > 3:
        reasons.append("more than 3 open event tickets")
    if card.theme and card.theme in card.open_themes:
        reasons.append("two tickets in the same theme")

    if type(card.p_pct) is not int or card.p_pct % 5 != 0 or not 0 <= card.p_pct <= 100:
        reasons.append("P% must be an integer on a 5-point step")
        ev = None
    else:
        ev = _expected_value(card.p_pct, card.structure_max_gain, card.structure_max_loss)
        if ev is None or ev <= 0:
            reasons.append("expected value is not positive")

    incomplete = any(
        reason.startswith("missing") or reason.startswith("direction") or reason.startswith("P%")
        for reason in reasons
    )
    return ChecklistResult(
        ok=not reasons,
        incomplete=incomplete,
        reasons=tuple(reasons),
        underlying_rr=urr,
        structure_rr=srr,
        premium_bias=bias,
        expected_value=ev,
        size_cap=cap,
    )


def apply_shrink(p_pct: int, shrink: float) -> float:
    """Pull logged P toward the realized rate. ``shrink`` of 1 leaves P unchanged."""
    if shrink < 0:
        raise ValueError("shrink factor must be >= 0")
    p = (p_pct / 100) * shrink
    return min(0.95, max(0.05, p))


def ev_per_risk(card: TradeCard, *, regime: str | None = None, shrink: float = 1.0) -> float | None:
    """Expected value per dollar of structure loss, after shrink and regime."""
    if (
        type(card.p_pct) is not int
        or card.structure_max_gain is None
        or card.structure_max_loss is None
        or card.structure_max_loss <= 0
    ):
        return None
    p = apply_shrink(card.p_pct, shrink)
    gain = card.structure_max_gain
    loss = card.structure_max_loss
    ev = p * gain - (1 - p) * loss
    per = ev / loss
    label = regime if regime is not None else card.regime
    if label == "RISK-OFF" and card.direction == "bull":
        per *= 0.5
    return per


def rank_cards(
    cards: list[TradeCard],
    *,
    regime: str | None = None,
    shrink: float = 1.0,
) -> list[tuple[TradeCard, ChecklistResult]]:
    """Complete cards sort by EV. An incomplete card never ranks above a STAND."""
    scored = [(card, check_card(card)) for card in cards]

    def tier(item: tuple[TradeCard, ChecklistResult]) -> int:
        card, result = item
        if result.ok:
            return 0
        if card.verdict.lower() in _STAND:
            return 1
        return 2

    def sort_key(pair: tuple[int, tuple[TradeCard, ChecklistResult]]):
        index, item = pair
        card, result = item
        ev = ev_per_risk(card, regime=regime, shrink=shrink)
        # Complete cards: higher EV first. Others keep input order inside the tier.
        ev_key = -(ev if ev is not None else -1e9) if result.ok else 0.0
        return (tier(item), ev_key, index)

    ordered = [item for _, item in sorted(enumerate(scored), key=sort_key)]
    return ordered


def log_run(
    path: Path,
    cards: list[TradeCard],
    *,
    logged_pt: str,
    run: str,
    regime: str | None = None,
    shrink: float = 1.0,
) -> dict[str, int]:
    """Append armed cards as real and the top 3 checklist passes as paper.

    Prediction rows already in the file are left unchanged. A run with fewer
    than 3 paper picks returns that count so the caller can mark it incomplete.
    """
    armed = [
        replace(card, kind="real", logged_pt=logged_pt, run=run, regime=regime or card.regime)
        for card in cards
        if card.verdict.lower() in _ARMED and check_card(card).ok
    ]
    papers = [
        replace(card, kind="paper", logged_pt=logged_pt, run=run, regime=regime or card.regime)
        for card in select_paper_picks(cards, regime=regime, shrink=shrink)
    ]
    append_ledger(path, armed + papers)
    return {"real": len(armed), "paper": len(papers)}


def select_paper_picks(
    cards: list[TradeCard],
    *,
    regime: str | None = None,
    shrink: float = 1.0,
    n: int = 3,
) -> list[TradeCard]:
    """Top directional calls, including STAND names that pass the checklist."""
    ranked = rank_cards(cards, regime=regime, shrink=shrink)
    picks: list[TradeCard] = []
    for card, result in ranked:
        if not result.ok or card.direction not in {"bull", "bear"}:
            continue
        picks.append(card)
        if len(picks) == n:
            break
    return picks


def _cell(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def _row_from_card(card: TradeCard) -> dict[str, str]:
    return {
        "logged_pt": card.logged_pt,
        "run": card.run,
        "ticker": card.ticker,
        "kind": card.kind,
        "direction": card.direction,
        "structure": card.structure,
        "entry": _cell(card.entry),
        "stop": _cell(card.stop),
        "target": _cell(card.target),
        "horizon_sessions": _cell(card.horizon_sessions),
        "p_pct": _cell(card.p_pct),
        "regime": _cell(card.regime),
        "gate_verdict": card.gate_verdict,
        "thesis": card.thesis,
        "outcome": "",
        "underlying_return": "",
        "spy_return": "",
        "scored_pt": "",
    }


def _read_ledger(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for raw in reader:
            row = {column: (raw.get(column) or "") for column in LEDGER_COLUMNS}
            rows.append(row)
        return rows


def _write_ledger(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=LEDGER_COLUMNS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in LEDGER_COLUMNS})


def ensure_ledger(path: Path) -> None:
    if path.exists() and path.stat().st_size > 0:
        return
    _write_ledger(path, [])


def append_ledger(path: Path, cards: list[TradeCard]) -> int:
    """Append prediction rows. Existing rows are not rewritten."""
    existing: list[dict[str, str]] = []
    if path.exists() and path.stat().st_size > 0:
        existing = _read_ledger(path)
    before = [dict(row) for row in existing]
    existing.extend(_row_from_card(card) for card in cards)
    _write_ledger(path, existing)
    if before:
        written = _read_ledger(path)
        for prior, current in zip(before, written):
            for column in PREDICTION_COLUMNS:
                if prior.get(column, "") != current.get(column, ""):
                    raise RuntimeError(f"append changed prediction column {column}")
    return len(cards)


def score_ledger(path: Path, updates: list[dict[str, str]]) -> int:
    """Fill outcome columns on matching rows. Prediction columns stay put."""
    rows = _read_ledger(path)
    snapshot = [{column: row.get(column, "") for column in PREDICTION_COLUMNS} for row in rows]
    matched = 0
    for update in updates:
        key = (
            update.get("logged_pt", ""),
            update.get("run", ""),
            update.get("ticker", ""),
            update.get("kind", ""),
        )
        for row in rows:
            row_key = (row["logged_pt"], row["run"], row["ticker"], row["kind"])
            if row_key != key:
                continue
            for column in OUTCOME_COLUMNS:
                if column in update and update[column] is not None:
                    row[column] = str(update[column])
            matched += 1
    _write_ledger(path, rows)
    written = _read_ledger(path)
    for prior, current in zip(snapshot, written):
        for column in PREDICTION_COLUMNS:
            if prior[column] != current[column]:
                raise RuntimeError(f"score changed prediction column {column}")
    return matched


def directional_return(direction: str, underlying_return: float) -> float:
    if direction == "bull":
        return underlying_return
    if direction == "bear":
        return -underlying_return
    raise ValueError("direction must be bull or bear")


def classify_gated(direction: str, underlying_return: float, spy_return: float) -> str:
    """SAVE, MISSED-WINNER, or NEITHER for a name the gate did not trade.

    MISSED-WINNER: the called direction moved more than 5% and beat SPY.
    SAVE: the called direction fell, or lagged SPY.
    """
    moved = directional_return(direction, underlying_return)
    if moved > MISS_MOVE and moved > spy_return:
        return "MISSED-WINNER"
    if moved < 0 or moved < spy_return:
        return "SAVE"
    return "NEITHER"


def resolve_outcome(
    *,
    direction: str,
    entry: float,
    end_price: float,
    stop_touched: bool = False,
    target_touched: bool = False,
    horizon_ended: bool = False,
) -> tuple[str, float]:
    """Return the outcome label and the underlying return from entry to end_price."""
    if entry <= 0:
        raise ValueError("entry must be positive")
    underlying = end_price / entry - 1
    if target_touched and stop_touched:
        return "AMBIGUOUS", underlying
    if target_touched:
        return "HIT-TARGET", underlying
    if stop_touched:
        return "HIT-STOP", underlying
    if horizon_ended:
        sign = "+" if underlying >= 0 else "−"
        return f"EXPIRED {sign}{abs(underlying) * 100:.1f}%", underlying
    return "OPEN", underlying


def is_hit(outcome: str, direction: str, underlying_return: float) -> bool | None:
    """True/False for a resolved ticket. None when the row is still open or ambiguous."""
    if outcome == "HIT-TARGET":
        return True
    if outcome == "HIT-STOP":
        return False
    if outcome.startswith("EXPIRED"):
        return directional_return(direction, underlying_return) > 0
    return None


def brier_score(pairs: list[tuple[float, int]]) -> float | None:
    """Mean squared error of probabilities (0–1) against 0/1 outcomes."""
    if not pairs:
        return None
    return sum((p - y) ** 2 for p, y in pairs) / len(pairs)


def calibration_bucket(p_pct: int) -> str | None:
    """Buckets from the lessons scorecard. Gaps stay unbucketed."""
    if p_pct <= 40:
        return "≤40"
    if 45 <= p_pct <= 55:
        return "45–55"
    if 60 <= p_pct <= 70:
        return "60–70"
    if p_pct >= 75:
        return "≥75"
    return None


@dataclass(frozen=True)
class BucketStat:
    name: str
    n: int
    mean_p: float | None
    hit_rate: float | None


def calibration_table(pairs: list[tuple[int, int]]) -> list[BucketStat]:
    """``pairs`` are (p_pct, hit 0/1)."""
    order = ["≤40", "45–55", "60–70", "≥75"]
    grouped: dict[str, list[tuple[int, int]]] = {name: [] for name in order}
    for p_pct, hit in pairs:
        name = calibration_bucket(p_pct)
        if name is not None:
            grouped[name].append((p_pct, hit))
    stats = []
    for name in order:
        rows = grouped[name]
        if not rows:
            stats.append(BucketStat(name, 0, None, None))
            continue
        mean_p = sum(p for p, _ in rows) / len(rows) / 100
        hit_rate = sum(hit for _, hit in rows) / len(rows)
        stats.append(BucketStat(name, len(rows), mean_p, hit_rate))
    return stats


def shrink_factor(stats: list[BucketStat]) -> float:
    """Shrink logged P when a bucket with N≥8 is over-confident by more than 15pp.

    The factor is the smallest realized/predicted ratio among those buckets.
    Under-confident buckets do not raise P. No qualifying bucket leaves the
    factor at 1.
    """
    ratios: list[float] = []
    for stat in stats:
        if stat.n < MIN_CASES or stat.mean_p is None or stat.hit_rate is None:
            continue
        if stat.mean_p <= 0:
            continue
        if stat.mean_p - stat.hit_rate > 0.15:
            ratios.append(stat.hit_rate / stat.mean_p)
    if not ratios:
        return 1.0
    return min(ratios)


@dataclass(frozen=True)
class GateDecision:
    allowed: bool
    flag: str
    reason: str


def gate_stays(saves: int, misses: int) -> bool:
    """A gate stays when saves are at least twice the missed winners."""
    return saves >= 2 * misses


def loosen_flag(
    rule_id: str,
    *,
    saves: int,
    misses: int,
    sessions: int,
) -> str | None:
    """Flag LOOSEN? only after a 20-session window where misses exceed saves."""
    if sessions < LOOSEN_WINDOW or misses <= saves:
        return None
    if rule_id == HARD_FIVE_RULE:
        return "LOOSEN? user decision required; hard five stays until user OK"
    return "LOOSEN?"


def evaluate_gate_change(
    *,
    action: str,
    rule_id: str,
    cases: int,
    sessions: int,
    saves: int = 0,
    misses: int = 0,
    retires: str | None = None,
    user_ok: bool = False,
) -> GateDecision:
    """A gate change needs N≥8 cases over ≥10 sessions.

    Adding a rule retires one. The hard-five rule (EM>15% and all-four) is
    not loosened or retired unless the user says so. One anchor trade is not
    enough.
    """
    action = action.lower()
    hard = rule_id == HARD_FIVE_RULE
    if action == "keep":
        if gate_stays(saves, misses):
            return GateDecision(True, "STAY", "saves are at least twice misses")
        return GateDecision(True, "NO-CHANGE", "keep does not edit the gate")

    if action in {"loosen", "retire"} and hard and not user_ok:
        return GateDecision(
            False,
            "BLOCKED",
            "EM>15% all-four is user-mandated and stays without an explicit OK",
        )

    if cases < MIN_CASES or sessions < MIN_SESSIONS:
        return GateDecision(
            False,
            "BLOCKED",
            f"need at least {MIN_CASES} cases over {MIN_SESSIONS} sessions "
            f"(have {cases} cases, {sessions} sessions)",
        )

    if action == "add":
        if not retires or not str(retires).strip():
            return GateDecision(False, "BLOCKED", "adding a rule requires retiring one")
        if retires == rule_id:
            return GateDecision(False, "BLOCKED", "the new rule cannot retire itself")
        return GateDecision(True, "ADD", f"add {rule_id} and retire {retires}")

    if action == "retire":
        return GateDecision(True, "RETIRE", f"retire {rule_id}")

    if action == "loosen":
        if sessions < LOOSEN_WINDOW:
            return GateDecision(
                False,
                "BLOCKED",
                f"loosen is scored on {LOOSEN_WINDOW} sessions (have {sessions})",
            )
        if gate_stays(saves, misses):
            return GateDecision(False, "STAY", "saves are at least twice misses")
        if misses <= saves:
            return GateDecision(False, "BLOCKED", "misses do not exceed saves")
        return GateDecision(True, "LOOSEN", f"loosen {rule_id}")

    return GateDecision(False, "BLOCKED", f"unknown action {action}")


def _f(value: str) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def build_scorecard(rows: list[dict[str, str]]) -> dict:
    """Split real and paper results, then gate audit and calibration.

    Hit rate uses resolved tickets only (HIT-TARGET, HIT-STOP, EXPIRED).
    Gate counts use SAVE / MISSED-WINNER / NEITHER rows.
    """
    cohorts: dict[str, dict] = {}
    for kind in ("real", "paper"):
        group = [row for row in rows if row.get("kind") == kind]
        resolved = []
        for row in group:
            outcome = row.get("outcome") or ""
            underlying = _f(row.get("underlying_return", ""))
            if underlying is None:
                continue
            hit = is_hit(outcome, row.get("direction", ""), underlying)
            if hit is None:
                continue
            resolved.append((row, hit, underlying, _f(row.get("spy_return", ""))))
        n = len(resolved)
        hits = sum(1 for _, hit, _, _ in resolved if hit)
        avg_underlying = (
            sum(item[2] for item in resolved) / n if n else None
        )
        spy_vals = [item[3] for item in resolved if item[3] is not None]
        avg_spy = sum(spy_vals) / len(spy_vals) if spy_vals else None
        excess = None
        if avg_underlying is not None and avg_spy is not None:
            excess = avg_underlying - avg_spy
        cohorts[kind] = {
            "n": n,
            "hits": hits,
            "losses": n - hits,
            "hit_rate": (hits / n) if n else None,
            "avg_underlying_return": avg_underlying,
            "avg_spy_return": avg_spy,
            "excess_vs_spy": excess,
        }

    audit: dict[str, dict[str, int]] = {}
    for row in rows:
        outcome = row.get("outcome") or ""
        if outcome not in {"SAVE", "MISSED-WINNER", "NEITHER"}:
            continue
        gate = row.get("gate_verdict") or "unspecified"
        bucket = audit.setdefault(gate, {"SAVE": 0, "MISSED-WINNER": 0, "NEITHER": 0})
        bucket[outcome] += 1

    pairs: list[tuple[int, int]] = []
    brier_pairs: list[tuple[float, int]] = []
    for row in rows:
        underlying = _f(row.get("underlying_return", ""))
        if underlying is None or not row.get("p_pct"):
            continue
        hit = is_hit(row.get("outcome") or "", row.get("direction", ""), underlying)
        if hit is None:
            continue
        p_pct = int(float(row["p_pct"]))
        y = 1 if hit else 0
        pairs.append((p_pct, y))
        brier_pairs.append((p_pct / 100, y))

    stats = calibration_table(pairs)
    return {
        "real": cohorts["real"],
        "paper": cohorts["paper"],
        "gate_audit": audit,
        "calibration": stats,
        "brier": brier_score(brier_pairs),
        "shrink_factor": shrink_factor(stats),
        "saves": sum(item["SAVE"] for item in audit.values()),
        "missed_winners": sum(item["MISSED-WINNER"] for item in audit.values()),
    }


NON_HALTING_FIELDS = ("regime", "gate_fields", "checklist_levels", "paper_picks")

_FIELD_LABELS = {
    "regime": "regime",
    "gate_fields": "gate fields",
    "checklist_levels": "checklist levels",
    "paper_picks": "paper picks",
}

# Wrap and lessons record a sheet row on every run, including an unchanged book.
SHEET_ALWAYS_RUNS = frozenset({"evening-wrap", "daily-desk-lessons"})


def publish_desk_note(missing: list[str] | tuple[str, ...] = ()) -> dict[str, object]:
    """FULL CHECK and NBT still deliver when regime, gate, checklist, or picks are absent.

    ``halt`` is always false and ``status`` stays ``ok``, so the desk graph
    does not fail. The warning is empty when nothing is missing. Other standing
    fails (credit through a print, a missing EVENT-GATE TEST line, Reddit-alone
    TAKE) are outside this function.
    """
    unknown = [name for name in missing if name not in NON_HALTING_FIELDS]
    if unknown:
        raise ValueError(f"unknown desk field {unknown[0]}")
    ordered = [name for name in NON_HALTING_FIELDS if name in set(missing)]
    warning = ""
    if ordered:
        warning = "MISSING-FIELDS: " + ", ".join(_FIELD_LABELS[name] for name in ordered)
    return {"deliver": True, "halt": False, "status": "ok", "warning": warning}


def sheet_write_plan(*, run: str, book_changed: bool, cell_write_blocked: bool) -> dict[str, object]:
    """Wrap and lessons always write, even when the book is unchanged.

    A blocked cell-write does not skip the run: append the ledger and tag
    ``SHEET STALE``. ``execution_date`` stays the trade session; this plan
    does not set it. ``written_at`` in ``create_daily_top5.py`` is the write time.
    """
    if run not in SHEET_ALWAYS_RUNS:
        raise ValueError(f"sheet_write_plan is for wrap and lessons, not {run}")
    if cell_write_blocked:
        return {
            "write_sheet": False,
            "append_ledger": True,
            "tag": "SHEET STALE",
            "book_changed": book_changed,
        }
    return {
        "write_sheet": True,
        "append_ledger": True,
        "tag": "",
        "book_changed": book_changed,
    }


def format_scorecard_line(scorecard: dict) -> str:
    real = scorecard["real"]
    paper = scorecard["paper"]
    return (
        f"real {real['hits']}-{real['losses']} · "
        f"paper {paper['hits']}-{paper['losses']} · "
        f"saves {scorecard['saves']} · "
        f"missed winners {scorecard['missed_winners']}"
    )
