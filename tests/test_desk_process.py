"""Regime, checklist, ledger, calibration, and the 8-case gate rule."""

from pathlib import Path

import pytest

from tradepilot.desk_process import (
    HARD_FIVE_RULE,
    NON_HALTING_FIELDS,
    LEDGER_COLUMNS,
    PREDICTION_COLUMNS,
    TradeCard,
    append_ledger,
    apply_shrink,
    brier_score,
    build_scorecard,
    calibration_bucket,
    calibration_table,
    check_card,
    classify_gated,
    default_ledger_path,
    evaluate_gate_change,
    format_scorecard_line,
    gate_stays,
    is_hit,
    log_run,
    loosen_flag,
    publish_desk_note,
    sheet_write_plan,
    rank_cards,
    read_regime,
    resolve_outcome,
    score_ledger,
    select_paper_picks,
    shrink_factor,
    trend_vs_mas,
    vix_band,
)


def _card(**overrides) -> TradeCard:
    base = dict(
        ticker="AAA",
        direction="bull",
        thesis="Bullish into the print",
        catalyst="earnings 2026-10-21",
        entry=100.0,
        stop=90.0,
        target=120.0,
        structure_max_gain=200.0,
        structure_max_loss=100.0,
        em=0.10,
        realized_move=0.10,
        max_loss_pct_of_budget=0.01,
        p_pct=55,
        regime="RISK-ON",
        vix=16.0,
        open_event_tickets=1,
        theme="semis",
        structure="call debit",
        horizon_sessions=5,
        gate_verdict="clean",
        verdict="arm",
        kind="real",
    )
    base.update(overrides)
    return TradeCard(**base)


def test_trend_and_vix_bands():
    assert trend_vs_mas(110, 100, 105) == "up"
    assert trend_vs_mas(90, 100, 95) == "down"
    assert trend_vs_mas(102, 100, 105) == "chop"
    assert vix_band(14.9) == "calm"
    assert vix_band(15) == "normal"
    assert vix_band(19.9) == "normal"
    assert vix_band(20) == "elevated"
    assert vix_band(25) == "elevated"
    assert vix_band(25.1) == "stress"


def test_risk_on_up_calm_breadth():
    read = read_regime(
        spy=110, ma20=100, ma50=105, vix=14.8, vix_5d_change=0.4,
        ten_year=4.12, ten_year_5d_bp=3, rsp_5d=0.012, spy_5d=0.008,
        pct_above_50d=0.62, leader_etf="XLF", leader_5d=0.012,
        laggard_etf="XLK", laggard_5d=-0.008,
    )
    assert read.verdict == "RISK-ON"
    assert read.trend == "up"
    assert read.vix_band == "calm"
    assert read.size_cap == 0.01
    assert read.prefer_spreads is False
    assert read.bearish_needs_catalyst is True
    block = read.block()
    assert block.startswith("REGIME | trend: SPY vs 20d/50d MA = up")
    assert "verdict: RISK-ON" in block
    assert "XLF" in block
    assert "10Y 4.12" in block


def test_risk_off_on_downtrend_or_stress_vix():
    down = read_regime(
        spy=90, ma20=100, ma50=95, vix=16, rsp_5d=0.01, spy_5d=0.0,
    )
    assert down.verdict == "RISK-OFF"
    assert down.size_cap == 0.005
    stress = read_regime(
        spy=110, ma20=100, ma50=105, vix=26, rsp_5d=0.02, spy_5d=0.01,
    )
    assert stress.verdict == "RISK-OFF"
    assert stress.size_cap == 0.005
    assert stress.prefer_spreads is True
    assert stress.widen_stops is True


def test_risk_off_when_elevated_chop_and_weak_breadth():
    read = read_regime(
        spy=100, ma20=101, ma50=99, vix=22, rsp_5d=-0.01, spy_5d=0.01,
    )
    assert read.trend == "chop"
    assert read.verdict == "RISK-OFF"
    assert read.prefer_spreads is True


def test_neutral_when_uptrend_but_vix_elevated():
    read = read_regime(
        spy=110, ma20=100, ma50=105, vix=21, rsp_5d=0.02, spy_5d=0.01,
    )
    assert read.verdict == "NEUTRAL"
    assert read.size_cap == 0.01


def test_stale_trend_cannot_be_risk_on_but_stress_vix_still_risk_off():
    stale = read_regime(
        spy=110, ma20=100, ma50=105, vix=14, rsp_5d=0.02, spy_5d=0.01,
        stale_fields=["ma20"],
    )
    assert stale.trend == "stale"
    assert stale.verdict == "NEUTRAL"
    assert "STALE: ma20" in stale.block()
    stress = read_regime(vix=28, stale_fields=["spy", "ma20", "ma50"])
    assert stress.verdict == "RISK-OFF"


def test_complete_bull_card_passes():
    result = check_card(_card())
    assert result.ok
    assert result.incomplete is False
    assert result.underlying_rr == pytest.approx(2.0)
    assert result.structure_rr == pytest.approx(2.0)
    assert result.premium_bias == "fair"
    assert result.expected_value > 0


def test_risk_reward_below_two_fails():
    result = check_card(_card(target=108))
    assert not result.ok
    assert any("underlying risk-reward" in reason for reason in result.reasons)


def test_bear_card_uses_downside_reward():
    result = check_card(_card(
        direction="bear",
        thesis="Bearish into the print",
        entry=100,
        stop=110,
        target=80,
        regime="NEUTRAL",
    ))
    assert result.ok
    assert result.underlying_rr == pytest.approx(2.0)


def test_implied_versus_realized_sets_premium_bias():
    rich = check_card(_card(em=0.20, realized_move=0.10))
    cheap = check_card(_card(em=0.07, realized_move=0.10))
    assert rich.ok
    assert rich.premium_bias == "avoid long premium; prefer spreads"
    assert cheap.premium_bias == "long premium is cheap"


def test_missing_thesis_is_incomplete():
    result = check_card(_card(thesis=""))
    assert result.incomplete
    assert not result.ok


def test_probability_must_be_five_point_step():
    assert not check_card(_card(p_pct=53)).ok
    assert not check_card(_card(p_pct=True)).ok  # type: ignore[arg-type]


def test_negative_expected_value_fails():
    result = check_card(_card(p_pct=20, structure_max_gain=100, structure_max_loss=50))
    assert not result.ok
    assert any("expected value" in reason for reason in result.reasons)


def test_size_cap_and_concentration():
    assert check_card(_card(max_loss_pct_of_budget=0.01, regime="RISK-ON")).ok
    risk_off = check_card(_card(max_loss_pct_of_budget=0.006, regime="RISK-OFF", vix=18))
    assert not risk_off.ok
    assert check_card(_card(max_loss_pct_of_budget=0.005, regime="RISK-OFF")).ok
    assert not check_card(_card(open_event_tickets=4)).ok
    assert not check_card(_card(theme="semis", open_themes=["semis"])).ok


def test_risk_on_bear_needs_named_catalyst_and_none_needs_trend_language():
    blocked = check_card(_card(
        direction="bear", entry=100, stop=110, target=80,
        catalyst="none", thesis="Bearish into the print", regime="RISK-ON",
    ))
    assert any("named catalyst" in reason for reason in blocked.reasons)
    trend = check_card(_card(
        catalyst="none",
        thesis="Bullish trend continuation",
        regime="NEUTRAL",
    ))
    assert trend.ok


def test_incomplete_card_ranks_below_stand():
    stand = _card(ticker="STAND", verdict="stand", p_pct=40)
    incomplete = _card(ticker="GAP", verdict="take", thesis="")
    ranked = [card.ticker for card, _ in rank_cards([incomplete, stand])]
    assert ranked == ["STAND", "GAP"]


def test_risk_off_halves_bullish_ev_and_shrink_can_rerank():
    bull = _card(ticker="BULL", direction="bull", p_pct=60, verdict="arm")
    bear = _card(
        ticker="BEAR", direction="bear", thesis="Bearish into the print",
        entry=100, stop=110, target=80, p_pct=55, verdict="arm", regime="NEUTRAL",
    )
    on = [card.ticker for card, _ in rank_cards([bull, bear], regime="RISK-ON")]
    off = [card.ticker for card, _ in rank_cards([bull, bear], regime="RISK-OFF")]
    assert on[0] == "BULL"
    assert off[0] == "BEAR"
    shrunk = apply_shrink(60, 0.5)
    assert shrunk == pytest.approx(0.30)
    # A common shrink scales every card, so equal-payoff rank stays with the higher P.
    reranked = [card.ticker for card, _ in rank_cards([bull, bear], regime="RISK-ON", shrink=0.5)]
    assert reranked[0] == "BULL"


def test_paper_picks_include_stands_and_stop_at_three():
    cards = [
        _card(ticker=f"N{i}", verdict="stand", p_pct=40 + i * 5)
        for i in range(4)
    ]
    # p 40, 45, 50, 55. Higher P has higher EV. 40% may fail EV.
    picks = select_paper_picks(cards, regime="RISK-ON")
    assert len(picks) == 3
    assert picks[0].ticker == "N3"
    assert all(card.verdict == "stand" for card in picks)


def test_ledger_appends_without_editing_past_rows(tmp_path: Path):
    path = tmp_path / "tradepilot-ledger.csv"
    path.write_text("logged_pt,run,ticker,kind,direction,structure,entry,stop,target,horizon_sessions,p_pct,regime,gate_verdict,thesis\n", encoding="utf-8")
    first = _card(ticker="AAA", logged_pt="2026-10-16T09:00", run="FULLCHECK", thesis="Bullish, with a comma")
    second = _card(ticker="BBB", logged_pt="2026-10-16T09:00", run="FULLCHECK", kind="paper", verdict="stand")
    assert append_ledger(path, [first]) == 1
    assert append_ledger(path, [second]) == 1
    text = path.read_text(encoding="utf-8")
    assert text.splitlines()[0] == ",".join(LEDGER_COLUMNS)
    assert "Bullish, with a comma" in text
    updated = score_ledger(path, [{
        "logged_pt": "2026-10-16T09:00",
        "run": "FULLCHECK",
        "ticker": "AAA",
        "kind": "real",
        "outcome": "HIT-TARGET",
        "underlying_return": "0.04",
        "spy_return": "0.01",
        "scored_pt": "2026-10-23",
    }])
    assert updated == 1
    rows = list(__import__("csv").DictReader(path.open(encoding="utf-8")))
    assert rows[0]["thesis"] == "Bullish, with a comma"
    assert rows[0]["outcome"] == "HIT-TARGET"
    assert rows[1]["outcome"] == ""
    assert rows[0]["ticker"] == "AAA"
    for column in PREDICTION_COLUMNS:
        assert column in rows[0]


def test_log_run_writes_real_and_paper_even_when_the_arm_is_a_stand(tmp_path: Path):
    path = tmp_path / "ledger.csv"
    armed = _card(ticker="ARM", verdict="arm", p_pct=70)
    stands = [
        _card(ticker="S1", verdict="stand", p_pct=55),
        _card(ticker="S2", verdict="stand", p_pct=50),
    ]
    counts = log_run(path, [armed, *stands], logged_pt="2026-10-16T09:00", run="NBT", regime="NEUTRAL")
    assert counts["real"] == 1
    assert counts["paper"] == 3
    empty = log_run(
        tmp_path / "empty.csv",
        [_card(ticker="NO", thesis="")],
        logged_pt="2026-10-16T09:00",
        run="FULLCHECK",
    )
    assert empty == {"real": 0, "paper": 0}


def test_gated_save_and_missed_winner():
    assert classify_gated("bull", 0.08, 0.01) == "MISSED-WINNER"
    assert classify_gated("bull", -0.06, 0.01) == "SAVE"
    assert classify_gated("bull", 0.06, 0.07) == "SAVE"
    assert classify_gated("bull", 0.03, 0.01) == "NEITHER"
    assert classify_gated("bear", -0.08, 0.01) == "MISSED-WINNER"
    assert classify_gated("bear", 0.04, 0.01) == "SAVE"


def test_resolve_outcome_and_hit_flag():
    label, underlying = resolve_outcome(
        direction="bull", entry=100, end_price=110, target_touched=True,
    )
    assert label == "HIT-TARGET"
    assert underlying == pytest.approx(0.10)
    assert is_hit(label, "bull", underlying) is True
    stopped, _ = resolve_outcome(
        direction="bull", entry=100, end_price=89, stop_touched=True,
    )
    assert stopped == "HIT-STOP"
    expired, ret = resolve_outcome(
        direction="bull", entry=100, end_price=97, horizon_ended=True,
    )
    assert expired.startswith("EXPIRED −")
    assert is_hit(expired, "bull", ret) is False
    both, _ = resolve_outcome(
        direction="bull", entry=100, end_price=100, stop_touched=True, target_touched=True,
    )
    assert both == "AMBIGUOUS"
    assert is_hit(both, "bull", 0.0) is None


def test_brier_buckets_and_shrink_need_eight_cases():
    assert brier_score([(0.7, 1), (0.7, 0)]) == pytest.approx((0.09 + 0.49) / 2)
    assert calibration_bucket(40) == "≤40"
    assert calibration_bucket(41) is None
    assert calibration_bucket(55) == "45–55"
    assert calibration_bucket(71) is None
    assert calibration_bucket(75) == "≥75"
    short = calibration_table([(70, 0)] * 6 + [(70, 1)])
    assert shrink_factor(short) == 1.0
    over = calibration_table([(70, 0)] * 8 + [(70, 1)] * 2)
    factor = shrink_factor(over)
    assert factor == pytest.approx(0.2 / 0.7)
    assert factor < 1


def test_gate_change_needs_eight_cases_and_retires_one_rule():
    thin = evaluate_gate_change(
        action="add", rule_id="holiday-warm", cases=7, sessions=12, retires="reheat",
    )
    assert thin.allowed is False
    assert "8" in thin.reason
    no_retire = evaluate_gate_change(
        action="add", rule_id="holiday-warm", cases=8, sessions=10,
    )
    assert no_retire.allowed is False
    added = evaluate_gate_change(
        action="add", rule_id="holiday-warm", cases=8, sessions=10, retires="reheat",
    )
    assert added.allowed is True
    assert added.flag == "ADD"
    self_retire = evaluate_gate_change(
        action="add", rule_id="holiday-warm", cases=8, sessions=10, retires="holiday-warm",
    )
    assert self_retire.allowed is False


def test_hard_five_is_not_loosened_without_user_ok():
    blocked = evaluate_gate_change(
        action="loosen",
        rule_id=HARD_FIVE_RULE,
        cases=12,
        sessions=20,
        saves=2,
        misses=10,
        user_ok=False,
    )
    assert blocked.allowed is False
    assert "user-mandated" in blocked.reason
    retired = evaluate_gate_change(
        action="retire", rule_id=HARD_FIVE_RULE, cases=12, sessions=20, user_ok=False,
    )
    assert retired.allowed is False
    allowed = evaluate_gate_change(
        action="loosen",
        rule_id=HARD_FIVE_RULE,
        cases=12,
        sessions=20,
        saves=2,
        misses=10,
        user_ok=True,
    )
    assert allowed.allowed is True
    assert loosen_flag(HARD_FIVE_RULE, saves=2, misses=10, sessions=20).startswith("LOOSEN?")
    assert loosen_flag(HARD_FIVE_RULE, saves=2, misses=10, sessions=19) is None
    assert "user decision" in loosen_flag(HARD_FIVE_RULE, saves=2, misses=10, sessions=20)


def test_gate_stays_when_saves_are_double_misses_and_other_loosen_rules():
    assert gate_stays(8, 4) is True
    assert gate_stays(7, 4) is False
    stay = evaluate_gate_change(
        action="loosen", rule_id="ah-veto", cases=12, sessions=20, saves=8, misses=4,
    )
    assert stay.allowed is False
    assert stay.flag == "STAY"
    opened = evaluate_gate_change(
        action="loosen", rule_id="ah-veto", cases=12, sessions=20, saves=3, misses=9,
    )
    assert opened.allowed is True
    early = evaluate_gate_change(
        action="loosen", rule_id="ah-veto", cases=12, sessions=10, saves=3, misses=9,
    )
    assert early.allowed is False
    kept = evaluate_gate_change(
        action="keep", rule_id="ah-veto", cases=0, sessions=0, saves=8, misses=2,
    )
    assert kept.allowed is True
    assert kept.flag == "STAY"


def test_scorecard_keeps_real_and_paper_separate():
    rows = [
        {
            "kind": "real", "direction": "bull", "p_pct": "70", "outcome": "HIT-TARGET",
            "underlying_return": "0.04", "spy_return": "0.01", "gate_verdict": "clean",
        },
        {
            "kind": "real", "direction": "bull", "p_pct": "60", "outcome": "HIT-STOP",
            "underlying_return": "-0.05", "spy_return": "0.01", "gate_verdict": "clean",
        },
        {
            "kind": "paper", "direction": "bull", "p_pct": "55", "outcome": "EXPIRED +2.0%",
            "underlying_return": "0.02", "spy_return": "0.01", "gate_verdict": "clean",
        },
        {
            "kind": "paper", "direction": "bull", "p_pct": "40", "outcome": "SAVE",
            "underlying_return": "-0.08", "spy_return": "0.01", "gate_verdict": "EM>15%",
        },
        {
            "kind": "paper", "direction": "bull", "p_pct": "65", "outcome": "MISSED-WINNER",
            "underlying_return": "0.09", "spy_return": "0.01", "gate_verdict": "EM>15%",
        },
    ]
    card = build_scorecard(rows)
    assert card["real"]["n"] == 2
    assert card["real"]["hits"] == 1
    assert card["real"]["hit_rate"] == pytest.approx(0.5)
    assert card["real"]["avg_underlying_return"] == pytest.approx(-0.005)
    assert card["real"]["excess_vs_spy"] == pytest.approx(-0.015)
    assert card["paper"]["n"] == 1
    assert card["paper"]["hits"] == 1
    assert card["gate_audit"]["EM>15%"] == {"SAVE": 1, "MISSED-WINNER": 1, "NEITHER": 0}
    line = format_scorecard_line(card)
    assert line == "real 1-1 · paper 1-0 · saves 1 · missed winners 1"
    assert card["saves"] == 1
    assert card["real"]["n"] != card["paper"]["n"]


def test_missing_fields_still_deliver_and_do_not_halt():
    assert NON_HALTING_FIELDS == ("regime", "gate_fields", "checklist_levels", "paper_picks")
    clear = publish_desk_note([])
    assert clear == {"deliver": True, "halt": False, "status": "ok", "warning": ""}
    noted = publish_desk_note(["paper_picks", "regime", "checklist_levels", "gate_fields"])
    assert noted["deliver"] is True
    assert noted["halt"] is False
    assert noted["status"] == "ok"
    assert noted["warning"] == "MISSING-FIELDS: regime, gate fields, checklist levels, paper picks"
    with pytest.raises(ValueError):
        publish_desk_note(["business_tape"])


def test_wrap_and_lessons_write_sheet_when_the_book_is_unchanged():
    for run in ("evening-wrap", "daily-desk-lessons"):
        unchanged = sheet_write_plan(run=run, book_changed=False, cell_write_blocked=False)
        assert unchanged["write_sheet"] is True
        assert unchanged["append_ledger"] is True
        assert unchanged["tag"] == ""
        blocked = sheet_write_plan(run=run, book_changed=False, cell_write_blocked=True)
        assert blocked["write_sheet"] is False
        assert blocked["append_ledger"] is True
        assert blocked["tag"] == "SHEET STALE"
    with pytest.raises(ValueError):
        sheet_write_plan(run="full-check", book_changed=True, cell_write_blocked=False)


def test_default_ledger_path_stays_in_the_documents_folder(monkeypatch):
    monkeypatch.delenv("TRADEPILOT_LEDGER", raising=False)
    path = default_ledger_path()
    assert path.as_posix().endswith("agents/ssr-st/workspace/Documents/tradepilot-ledger.csv")
    header = path.read_text(encoding="utf-8").splitlines()[0]
    assert header.split(",") == LEDGER_COLUMNS
