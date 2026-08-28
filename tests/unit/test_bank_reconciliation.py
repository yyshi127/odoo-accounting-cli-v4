from __future__ import annotations

import base64
import copy
import io
import json

import pytest

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.bridge.financial_reports import OdooFinancialReportPort
from odoo_accounting_cli_v4.capabilities.financial_reports import (
    BANK_RECONCILIATION_REPORT_CAPABILITY_ID,
    FinancialReportError,
    read_bank_reconciliation,
    read_typed_financial_report,
    validate_bank_reconciliation_request,
    validate_typed_financial_report_request,
)
from odoo_accounting_cli_v4.registry import load_registry

_COLUMNS = [
    {
        "index": 0,
        "label": "Date",
        "expression_label": "date",
        "figure_type": "date",
    },
    {
        "index": 1,
        "label": "Balance",
        "expression_label": "balance",
        "figure_type": "monetary",
    },
]
_LINES = [
    {
        "id": "bank:1",
        "parent_id": None,
        "name": "Opening balance",
        "level": 1,
        "unfoldable": False,
        "values": ["2025-01-01", "100.00"],
    },
    {
        "id": "bank:2",
        "parent_id": None,
        "name": "Closing balance",
        "level": 1,
        "unfoldable": False,
        "values": ["2025-01-31", "125.00"],
    },
]


def _request(
    *,
    journal_id: object = 9,
    as_of: str = "2025-01-31",
    limit: int = 100,
    cursor: str | None = None,
) -> dict:
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
        "parameters": {
            "journal_id": journal_id,
            "as_of": as_of,
            "limit": limit,
            "cursor": cursor,
        },
    }


def _page(
    *,
    report_key: str = "bank_reconciliation",
    lines: list[dict] | None = None,
    cursor_found: bool = True,
) -> dict:
    return {
        "user_id": 42,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "cursor_found": cursor_found,
        "report": {"key": report_key, "name": "Bank Reconciliation"},
        "date": {"from": "2025-01-01", "to": "2025-01-31"},
        "currency": {"id": 6, "code": "CNY", "decimal_places": 2},
        "basis": "posted_entries",
        "columns": copy.deepcopy(_COLUMNS),
        "lines": copy.deepcopy(_LINES if lines is None else lines),
    }


class FakePort:
    user_id = 42

    def __init__(self, lines: list[dict] | None = None) -> None:
        self.lines = copy.deepcopy(_LINES if lines is None else lines)
        self.calls: list[dict] = []

    def read_page(self, **kwargs) -> dict:
        self.calls.append(copy.deepcopy(kwargs))
        after = kwargs["after_line_id"]
        cursor_found = True
        start = 0
        if after is not None:
            ids = [line["id"] for line in self.lines]
            if after not in ids:
                cursor_found = False
            else:
                start = ids.index(after) + 1
        return _page(
            lines=self.lines[start : start + kwargs["limit"]],
            cursor_found=cursor_found,
        )


def test_bank_reconciliation_validates_and_reads_one_typed_page() -> None:
    request = _request()
    context, date_from, date_to, journal_id, limit, cursor = (
        validate_bank_reconciliation_request(request)
    )
    assert (date_from, date_to, journal_id, limit, cursor) == (
        None,
        "2025-01-31",
        9,
        100,
        None,
    )
    assert context == request["context"]
    assert validate_typed_financial_report_request(
        BANK_RECONCILIATION_REPORT_CAPABILITY_ID, request
    ) == (context, None, "2025-01-31", 100, None)

    port = FakePort()
    result = read_bank_reconciliation(port, request)

    assert result["report"]["key"] == "bank_reconciliation"
    assert result["columns"] == _COLUMNS
    assert result["lines"] == _LINES
    assert result["has_more"] is False
    assert result["next_cursor"] is None
    assert port.calls == [
        {
            "company_id": 7,
            "date_from": None,
            "date_to": "2025-01-31",
            "after_line_id": None,
            "limit": 101,
            "journal_id": 9,
        }
    ]


def test_generic_typed_reader_routes_bank_reconciliation_to_the_explicit_reader() -> (
    None
):
    result = read_typed_financial_report(
        BANK_RECONCILIATION_REPORT_CAPABILITY_ID, FakePort(), _request()
    )
    assert result["report"]["key"] == "bank_reconciliation"


@pytest.mark.parametrize("journal_id", [None, True, 0, -1, "9"])
def test_journal_id_is_required_and_must_be_a_positive_integer(
    journal_id: object,
) -> None:
    request = _request(journal_id=journal_id)
    with pytest.raises(FinancialReportError) as caught:
        validate_bank_reconciliation_request(request)
    assert caught.value.code == "invalid_request"
    assert caught.value.exit_code == 2


def test_bank_reconciliation_request_is_closed() -> None:
    request = _request()
    del request["parameters"]["journal_id"]
    with pytest.raises(FinancialReportError):
        validate_bank_reconciliation_request(request)

    request = _request()
    request["parameters"]["unexpected"] = True
    with pytest.raises(FinancialReportError):
        validate_bank_reconciliation_request(request)


def test_bank_reconciliation_cursor_is_bound_to_journal_id() -> None:
    first = read_bank_reconciliation(FakePort(), _request(limit=1))
    assert first["has_more"] is True
    assert first["next_cursor"]

    payload = json.loads(
        base64.urlsafe_b64decode(first["next_cursor"] + "==").decode("utf-8")
    )
    assert payload["journal_id"] == 9

    changed_port = FakePort()
    with pytest.raises(FinancialReportError) as caught:
        read_bank_reconciliation(
            changed_port,
            _request(journal_id=10, limit=1, cursor=first["next_cursor"]),
        )
    assert caught.value.code == "invalid_cursor"
    assert changed_port.calls == []

    continued_port = FakePort()
    continued = read_bank_reconciliation(
        continued_port, _request(limit=10, cursor=first["next_cursor"])
    )
    assert [line["id"] for line in continued["lines"]] == ["bank:2"]
    assert continued_port.calls[0]["journal_id"] == 9
    assert continued_port.calls[0]["after_line_id"] == "bank:1"


def test_existing_typed_report_cursor_shape_does_not_gain_journal_id() -> None:
    class GeneralLedgerPort(FakePort):
        def read_page(self, **kwargs) -> dict:
            assert "journal_id" not in kwargs
            page = super().read_page(**kwargs)
            page["report"] = {"key": "general_ledger", "name": "General Ledger"}
            return page

    request = _request(limit=1)
    request["parameters"] = {
        "date_from": "2025-01-01",
        "date_to": "2025-01-31",
        "limit": 1,
        "cursor": None,
    }
    result = read_typed_financial_report(
        "report.general_ledger", GeneralLedgerPort(), request
    )
    payload = json.loads(
        base64.urlsafe_b64decode(result["next_cursor"] + "==").decode("utf-8")
    )
    assert set(payload) == {
        "after_line_id",
        "capability",
        "company_id",
        "database",
        "date_from",
        "date_to",
        "user_login",
        "version",
    }


def test_bank_reconciliation_bridge_uses_fixed_action_and_payload() -> None:
    class Client:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict]] = []

        def invoke(self, action: str, payload: dict) -> dict:
            self.calls.append((action, copy.deepcopy(payload)))
            return _page()

    client = Client()
    port = OdooFinancialReportPort(client, BANK_RECONCILIATION_REPORT_CAPABILITY_ID)
    page = port.read_page(
        company_id=7,
        date_from=None,
        date_to="2025-01-31",
        after_line_id=None,
        limit=101,
        journal_id=9,
    )

    assert page["report"]["key"] == "bank_reconciliation"
    assert port.user_id == 42
    assert client.calls == [
        (
            "account.report.bank_reconciliation.read_page",
            {
                "company_id": 7,
                "date_from": None,
                "date_to": "2025-01-31",
                "after_line_id": None,
                "limit": 101,
                "journal_id": 9,
            },
        )
    ]


def test_bank_bridge_rejects_missing_journal_before_invocation() -> None:
    class Client:
        def invoke(self, action: str, payload: dict) -> dict:
            raise AssertionError("invalid bridge request must not be invoked")

    port = OdooFinancialReportPort(Client(), BANK_RECONCILIATION_REPORT_CAPABILITY_ID)
    with pytest.raises(ValueError, match="journal_id"):
        port.read_page(
            company_id=7,
            date_from=None,
            date_to="2025-01-31",
            after_line_id=None,
            limit=101,
        )


def test_registry_descriptor_routes_to_fixed_cli_handler_validator_and_port(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    descriptor = load_registry().describe(BANK_RECONCILIATION_REPORT_CAPABILITY_ID)
    handler_key = descriptor["handler_key"]

    assert handler_key == "report_bank_reconciliation"
    assert cli._HANDLERS[handler_key] is read_bank_reconciliation
    assert cli._REQUEST_VALIDATORS[handler_key] is validate_bank_reconciliation_request
    assert cli._CAPABILITY_MODELS[BANK_RECONCILIATION_REPORT_CAPABILITY_ID] == (
        "account.report"
    )

    target = object()
    client = object()

    class RuntimeConfig:
        def resolve(self, database: str, company_id: int, user_login: str) -> object:
            assert (database, company_id, user_login) == (
                "v4-dev",
                7,
                "v4-agent",
            )
            return target

    def bridge_factory(selected_target: object, **kwargs: str) -> object:
        assert selected_target is target
        assert kwargs == {"language": "en_US", "timezone": "Asia/Shanghai"}
        return client

    monkeypatch.setattr(cli, "load_runtime_config", lambda _path: RuntimeConfig())
    monkeypatch.setattr(cli, "OdooBridgeClient", bridge_factory)

    port = cli._configured_port_factory(
        BANK_RECONCILIATION_REPORT_CAPABILITY_ID, _request()
    )

    assert type(port) is OdooFinancialReportPort
    assert port._client is client
    assert port._action == "account.report.bank_reconciliation.read_page"


def test_cli_success_uses_descriptor_schema_and_report_odoo_metadata() -> None:
    request = _request()
    port = FakePort()
    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = cli.main(
        [
            "read",
            BANK_RECONCILIATION_REPORT_CAPABILITY_ID,
            "--request",
            "-",
        ],
        stdin=io.StringIO(json.dumps(request)),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda capability_id, selected_request: (
            port
            if capability_id == BANK_RECONCILIATION_REPORT_CAPABILITY_ID
            and selected_request == request
            else None
        ),
    )

    document = json.loads(stdout.getvalue())
    descriptor = load_registry().describe(BANK_RECONCILIATION_REPORT_CAPABILITY_ID)
    assert exit_code == 0
    assert stderr.getvalue() == ""
    assert document["success"] is True
    assert document["capability"] == BANK_RECONCILIATION_REPORT_CAPABILITY_ID
    assert document["data"]["report"]["key"] == "bank_reconciliation"
    assert document["odoo"] == {
        "database": "v4-dev",
        "company_id": 7,
        "user_id": 42,
        "model": "account.report",
        "record_ids": [],
    }
    load_registry().validate_instance(descriptor["schemas"]["response"], document)
