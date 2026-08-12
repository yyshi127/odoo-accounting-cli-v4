#!/usr/bin/env python3
"""Development-tree launcher for the Odoo-side V4 bridge."""

from __future__ import annotations

import sys
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "src"))

from odoo_accounting_cli_v4.bridge.runtime import main  # noqa: E402


raise SystemExit(main())
