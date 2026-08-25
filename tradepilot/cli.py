"""TradePilot command-line interface."""

from __future__ import annotations

import argparse
import sys

from tradepilot import __version__


def cmd_version(_args: argparse.Namespace) -> None:
    print(__version__)


def cmd_doctor(_args: argparse.Namespace) -> None:
    major, minor = sys.version_info[:2]
    print("TradePilot environment check")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  Version: {__version__}")
    if major == 3 and minor >= 11:
        print("  Status: OK")
    else:
        print("  Status: Python 3.11+ is required")
        raise SystemExit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tradepilot",
        description="Autonomous AI agent for market monitoring, trade planning, and risk reporting.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command")

    version_parser = subparsers.add_parser("version", help="Print the installed version")
    version_parser.set_defaults(func=cmd_version)

    doctor_parser = subparsers.add_parser("doctor", help="Verify the local environment")
    doctor_parser.set_defaults(func=cmd_doctor)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
