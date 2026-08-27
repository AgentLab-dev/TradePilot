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


def cmd_sites_publish(args: argparse.Namespace) -> None:
    from tradepilot.sites_publisher.publish import publish

    publish(
        html_only=args.html_only,
        login=args.login,
        out=args.out,
        credentials=args.credentials,
        title=args.title,
    )


def cmd_portal_capture(args: argparse.Namespace) -> None:
    import runpy
    from pathlib import Path

    script = (
        Path(__file__).resolve().parents[1]
        / "agents"
        / "ssr-st"
        / "workspace"
        / "Documents"
        / "market_data"
        / "ibd_wsj_capture.py"
    )
    sys.argv = [str(script)] + (["--login"] if args.login else [])
    runpy.run_path(str(script), run_name="__main__")


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

    sites = subparsers.add_parser(
        "sites-publish",
        help="Publish FULL CHECK universe flags to Google Sites",
    )
    sites.add_argument("--html-only", action="store_true", help="Write local HTML and stop")
    sites.add_argument("--login", action="store_true", help="Run Google OAuth before upload")
    sites.add_argument("--out", help="Local HTML path")
    sites.add_argument("--credentials", help="OAuth Desktop client JSON")
    sites.add_argument("--title", help="Google Doc / site title")
    sites.set_defaults(func=cmd_sites_publish)

    portal = subparsers.add_parser(
        "portal-capture",
        help="Capture IBD Stock Lists + WSJ (local Playwright session)",
    )
    portal.add_argument("--login", action="store_true", help="Headed login; save cookies")
    portal.set_defaults(func=cmd_portal_capture)

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
