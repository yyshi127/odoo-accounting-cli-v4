from __future__ import annotations

import io
import json

from odoo_accounting_cli_v4.cli import main


def _request(parameters: dict) -> dict:
    return {
        "schema_version": "v1",
        "request_id": "7bc39413-0d69-4092-9319-795d33f3167c",
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }


def _run(capability_id: str, request: dict, port: object) -> dict:
    stdout = io.StringIO()
    stderr = io.StringIO()
    exit_code = main(
        ["read", capability_id, "--request", "-"],
        stdin=io.StringIO(json.dumps(request)),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda selected, parsed: port,
    )
    assert exit_code == 0
    assert stderr.getvalue() == ""
    return json.loads(stdout.getvalue())


def test_cli_resolves_a_fiscal_position_with_the_fixed_handler() -> None:
    class Port:
        user_id = 42

        def resolve(self, **kwargs):
            assert kwargs == {
                "company_id": 7,
                "partner_id": 1,
                "delivery_partner_id": None,
                "account_id": None,
                "tax_ids": None,
            }
            return {
                "user_id": 42,
                "company_visible": True,
                "module_installed": True,
                "access_allowed": True,
                "data": {
                    "company_id": 7,
                    "partner_id": 1,
                    "delivery_partner_id": None,
                    "fiscal_position": None,
                    "account_mapping": None,
                    "tax_mapping": None,
                },
            }

    document = _run("fiscal_position.resolve", _request({"partner_id": 1}), Port())

    assert document["data"]["fiscal_position"] is None
    assert document["odoo"] == {
        "database": "v4-dev",
        "company_id": 7,
        "user_id": 42,
        "model": "account.fiscal.position",
        "record_ids": [],
    }


def test_cli_inspects_native_journal_hash_integrity() -> None:
    class Port:
        user_id = 42

        def inspect(self, *, company_id: int):
            assert company_id == 7
            return {
                "user_id": 42,
                "company_visible": True,
                "module_installed": True,
                "access_allowed": True,
                "data": {
                    "company_id": 7,
                    "printing_date": "08/25/2026",
                    "results": [],
                },
            }

    document = _run(
        "diagnostic.journal_integrity.inspect", _request({}), Port()
    )

    assert document["data"]["results"] == []
    assert document["odoo"] == {
        "database": "v4-dev",
        "company_id": 7,
        "user_id": 42,
        "model": "res.company",
        "record_ids": [7],
    }
