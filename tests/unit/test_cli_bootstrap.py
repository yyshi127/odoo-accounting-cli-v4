from __future__ import annotations

import json

from odoo_accounting_cli_v4.cli import main


def test_version_is_one_json_document(capsys) -> None:
    assert main(["version"]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == {
        "product": "odoo-accounting-cli-v4",
        "status": "bootstrap",
        "version": "0.0.0",
    }
