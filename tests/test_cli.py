import pytest

from tradepilot.cli import build_parser, main


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "0.1.0" in captured.out


def test_doctor_succeeds_on_supported_python(capsys):
    assert main(["doctor"]) == 0
    captured = capsys.readouterr()
    assert "Status: OK" in captured.out


def test_parser_exposes_version_and_doctor_commands():
    parser = build_parser()
    subparsers = next(
        action for action in parser._actions if action.dest == "command"
    )
    assert set(subparsers.choices) == {"version", "doctor"}
