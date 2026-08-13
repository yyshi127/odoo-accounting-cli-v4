from __future__ import annotations

import io
import json

import pytest

import odoo_accounting_cli_v4.cli as cli
from odoo_accounting_cli_v4.bridge.reconciliation_candidates import (
    OdooReconciliationCandidatesPort,
)
from odoo_accounting_cli_v4.registry import load_registry


CAPABILITY_ID = "reconciliation.candidates.list"


def _request(parameters: dict) -> dict:
    return {
        "schema_version": "v1",
        "request_id": "fe40da72-5faa-483b-9381-9e8de7f002fd",
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "zh_CN",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }


def _candidate() -> dict:
    currency = {"id": 6, "code": "CNY"}
    return {
        "id": 20,
        "date": "2025-01-25",
        "invoice_date": "2025-01-20",
        "date_maturity": "2025-02-20",
        "state": "posted",
        "move": {
            "id": 1020,
            "name": "MISC/2025/0020",
            "move_type": "entry",
            "ref": "REF-20",
        },
        "label": "Candidate 20",
        "account": {
            "id": 31,
            "code": "220200",
            "name": "Suspense",
            "account_type": "asset_current",
        },
        "partner": {"id": 16, "name": "Fixture Partner"},
        "journal": {"id": 9, "code": "BNK1", "name": "Bank", "type": "bank"},
        "company_id": 7,
        "company_currency": dict(currency),
        "currency": dict(currency),
        "balance": "50.00",
        "amount_currency": "50.00",
        "amount_residual": "25.00",
        "amount_residual_currency": "25.00",
        "matching_number": "P",
        "reconciliation_model": {"id": 4, "name": "Bank fees"},
    }


def test_cli_dispatches_the_fixed_reconciliation_candidate_read() -> None:
    candidate = _candidate()

    class Port:
        user_id = 42

        def read_page(self, **kwargs):
            assert kwargs == {
                "company_id": 7,
                "after": None,
                "limit": 2,
                "filters": {
                    "date_from": None,
                    "date_to": None,
                    "states": ["posted"],
                    "account_id": None,
                    "partner_id": None,
                    "journal_id": None,
                    "account_kinds": ["receivable", "payable", "other"],
                    "query": None,
                },
            }
            return {
                "user_id": 42,
                "company_visible": True,
                "module_installed": True,
                "access_allowed": True,
                "rows": [candidate],
            }

    def port_factory(selected: str, request: dict) -> Port:
        assert selected == CAPABILITY_ID
        assert request == _request({"limit": 1})
        return Port()

    stdout = io.StringIO()
    stderr = io.StringIO()
    result = cli.main(
        ["read", CAPABILITY_ID, "--request", "-"],
        stdin=io.StringIO(json.dumps(_request({"limit": 1}))),
        stdout=stdout,
        stderr=stderr,
        port_factory=port_factory,
    )

    document = json.loads(stdout.getvalue())
    assert result == 0
    assert stderr.getvalue() == ""
    assert document["success"] is True
    assert document["data"] == {
        "items": [candidate],
        "has_more": False,
        "next_cursor": None,
    }
    assert document["odoo"] == {
        "database": "odoo_cli_v4_dev",
        "company_id": 7,
        "user_id": 42,
        "model": "account.move.line",
        "record_ids": [20],
    }
    load_registry().validate_instance(
        "schemas/v1/reconciliation.candidates.list.response.schema.json", document
    )


def test_uninstalled_result_preserves_verified_odoo_context() -> None:
    class Port:
        user_id = 42

        def read_page(self, **kwargs):
            return {
                "user_id": 42,
                "company_visible": True,
                "module_installed": False,
                "access_allowed": False,
                "rows": [],
            }

    stdout = io.StringIO()
    stderr = io.StringIO()
    result = cli.main(
        ["read", CAPABILITY_ID, "--request", "-"],
        stdin=io.StringIO(json.dumps(_request({}))),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda selected, request: Port(),
    )

    document = json.loads(stdout.getvalue())
    assert result == 4
    assert stderr.getvalue() == ""
    assert document["error"]["code"] == "uninstalled"
    assert document["odoo"] == {
        "database": "odoo_cli_v4_dev",
        "company_id": 7,
        "user_id": 42,
        "model": "account.move.line",
        "record_ids": [],
    }
    load_registry().validate_instance(
        "schemas/v1/reconciliation.candidates.list.response.schema.json", document
    )


def test_invalid_reconciliation_cursor_does_not_read_unverified_port_user_id() -> None:
    class Client:
        def invoke(self, action, payload):
            raise AssertionError("invalid cursor must fail before bridge invocation")

    stdout = io.StringIO()
    stderr = io.StringIO()
    result = cli.main(
        ["read", CAPABILITY_ID, "--request", "-"],
        stdin=io.StringIO(
            json.dumps(_request({"limit": 1, "cursor": "not-a-valid-cursor"}))
        ),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda selected, request: OdooReconciliationCandidatesPort(
            Client()
        ),
    )

    document = json.loads(stdout.getvalue())
    assert result == 2
    assert stderr.getvalue() == ""
    assert document["error"]["code"] == "invalid_cursor"
    assert document["odoo"] == {
        "database": None,
        "company_id": None,
        "user_id": None,
        "model": None,
        "record_ids": [],
    }
    load_registry().validate_instance(
        "schemas/v1/reconciliation.candidates.list.response.schema.json", document
    )


def test_configured_factory_selects_reconciliation_candidates_port(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = object()
    client = object()

    class RuntimeConfig:
        def resolve(self, database: str, company_id: int, user_login: str) -> object:
            assert (database, company_id, user_login) == (
                "odoo_cli_v4_dev",
                7,
                "v4-agent",
            )
            return target

    monkeypatch.setattr(cli, "load_runtime_config", lambda path: RuntimeConfig())
    monkeypatch.setattr(
        cli,
        "OdooBridgeClient",
        lambda selected_target, **kwargs: (
            client
            if selected_target is target
            and kwargs == {"language": "zh_CN", "timezone": "Asia/Shanghai"}
            else None
        ),
    )

    port = cli._configured_port_factory(CAPABILITY_ID, _request({}))

    assert isinstance(port, OdooReconciliationCandidatesPort)
    assert port._client is client
