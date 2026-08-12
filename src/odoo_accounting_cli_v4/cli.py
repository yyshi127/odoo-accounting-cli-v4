"""Bootstrap command surface for the independent V4 package."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from odoo_accounting_cli_v4 import __version__


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="odoo-accounting-cli-v4")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("version", help="Show bootstrap package metadata as JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "version":
        print(
            json.dumps(
                {
                    "product": "odoo-accounting-cli-v4",
                    "version": __version__,
                    "status": "bootstrap",
                },
                separators=(",", ":"),
                sort_keys=True,
            )
        )
        return 0
    raise AssertionError(f"unhandled command: {args.command}")
