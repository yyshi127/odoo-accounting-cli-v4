from __future__ import annotations

import base64
import copy
import io
import json
from functools import partial

import pytest
import test_balance_sheet as balance_tests
import test_financial_report_exports as export_tests
import test_trial_balance as trial_tests
import test_typed_financial_reports as typed_tests

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.bridge.financial_reports import (
    OdooFinancialReportExportPort,
    OdooFinancialReportPort,
)
from odoo_accounting_cli_v4.capabilities import financial_reports as reports
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

READ_CASES = {
    "report.trial_balance": (
        reports.read_trial_balance,
        reports.validate_trial_balance_request,
        trial_tests._request,
        trial_tests.FakePort,
    ),
    "report.balance_sheet": (
        reports.read_balance_sheet,
        reports.validate_balance_sheet_request,
        balance_tests._request,
        balance_tests.FakePort,
    ),
    "report.profit_and_loss": (
        reports.read_profit_and_loss,
        reports.validate_profit_and_loss_request,
        trial_tests._request,
        partial(
            balance_tests.FakePort,
            report={"key": "profit_and_loss", "name": "Profit and Loss"},
        ),
    ),
    "report.general_ledger": (
        partial(reports.read_typed_financial_report, "report.general_ledger"),
        partial(
            reports.validate_typed_financial_report_request, "report.general_ledger"
        ),
        partial(typed_tests._request, "report.general_ledger"),
        partial(typed_tests.FakePort, "report.general_ledger"),
    ),
}
CAPABILITIES = [*READ_CASES, *(f"{key}.export" for key in READ_CASES)]
INVALID_JOURNALS = [None, [], True, 3, "3", [True], [0], [-1], [3.5], ["3"], [3, 3]]


@pytest.fixture(scope="module")
def registry():
    return load_registry()


def _request(capability_id: str) -> dict:
    if capability_id.endswith(".export"):
        return export_tests._request(capability_id)
    return READ_CASES[capability_id][2]()


def _validate(capability_id: str, request: dict) -> tuple:
    if capability_id.endswith(".export"):
        return reports.validate_financial_report_export_request(capability_id, request)
    return READ_CASES[capability_id][1](request)


class RecordingClient:
    def __init__(self, capability_id: str) -> None:
        self.capability_id = capability_id
        self.calls: list[tuple[str, dict]] = []

    def invoke(self, action: str, payload: dict) -> dict:
        self.calls.append((action, copy.deepcopy(payload)))
        if self.capability_id.endswith(".export"):
            return export_tests._page(payload["format"])
        return READ_CASES[self.capability_id][3]().read_page(**payload)


def _port(capability_id: str, client: RecordingClient):
    if capability_id.endswith(".export"):
        return OdooFinancialReportExportPort(client)
    return OdooFinancialReportPort(client, capability_id)


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_journal_filter_preserves_validator_tuple_and_request(capability_id, registry):
    request = _request(capability_id)
    legacy = _validate(capability_id, request)
    request["parameters"]["journal_ids"] = [9, 3]
    original = copy.deepcopy(request)

    registry.validate_instance(
        f"schemas/v1/{capability_id}.request.schema.json", request
    )
    assert _validate(capability_id, request) == legacy
    assert request == original


@pytest.mark.parametrize("capability_id", CAPABILITIES)
@pytest.mark.parametrize("journal_ids", INVALID_JOURNALS)
def test_journal_filter_rejects_invalid_lists(capability_id, journal_ids, registry):
    request = _request(capability_id)
    request["parameters"]["journal_ids"] = journal_ids
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(
            f"schemas/v1/{capability_id}.request.schema.json", request
        )
    with pytest.raises(reports.FinancialReportError) as caught:
        _validate(capability_id, request)
    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_journal_filter_limit_and_closed_parameters(capability_id, registry):
    request = _request(capability_id)
    request["parameters"]["journal_ids"] = list(range(1, 1001))
    _validate(capability_id, request)
    registry.validate_instance(
        f"schemas/v1/{capability_id}.request.schema.json", request
    )
    for changes in ({"journal_ids": list(range(1, 1002))}, {"journal_id": 3}):
        invalid = copy.deepcopy(request)
        invalid["parameters"].update(changes)
        with pytest.raises(reports.FinancialReportError):
            _validate(capability_id, invalid)
        with pytest.raises(InstanceValidationError):
            registry.validate_instance(
                f"schemas/v1/{capability_id}.request.schema.json", invalid
            )


@pytest.mark.parametrize(
    ("capability_id", "export_format"),
    [(capability, None) for capability in READ_CASES]
    + [
        (f"{capability}.export", fmt)
        for capability in READ_CASES
        for fmt in ("pdf", "xlsx")
    ],
)
def test_cli_and_normal_ports_forward_sorted_journal_ids(
    capability_id, export_format, registry
):
    request = _request(capability_id)
    request["parameters"]["journal_ids"] = [9, 3]
    if export_format is not None:
        request["parameters"]["format"] = export_format
    client = RecordingClient(capability_id)
    stdout, stderr = io.StringIO(), io.StringIO()
    exit_code = cli.main(
        ["read", capability_id, "--request", "-"],
        stdin=io.StringIO(json.dumps(request)),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda _capability, _request: _port(capability_id, client),
    )
    assert exit_code == 0, stdout.getvalue()
    assert stderr.getvalue() == "" and len(stdout.getvalue().splitlines()) == 1
    response = json.loads(stdout.getvalue())
    assert response["success"] is True and response["status"] == "verified"
    assert response["odoo"]["user_id"] == 42
    assert client.calls[0][1]["journal_ids"] == [3, 9]
    assert client.calls[0][0] == (
        "account.report.fixed_export"
        if capability_id.endswith(".export")
        else f"account.{capability_id}.read_page"
    )
    registry.validate_instance(
        f"schemas/v1/{capability_id}.response.schema.json", response
    )


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_bridge_port_normalizes_and_validates_journal_ids(capability_id):
    client = RecordingClient(capability_id)
    port = _port(capability_id, client)
    validated = _validate(capability_id, _request(capability_id))
    context, date_from, date_to = validated[:3]
    parameters = {
        "company_id": context["company_id"],
        "date_from": date_from,
        "date_to": date_to,
    }
    if capability_id.endswith(".export"):
        parameters.update(capability_id=capability_id, format=validated[3])
        call = port.export
    else:
        parameters.update(after_line_id=None, limit=100)
        call = port.read_page
    journal_ids = [9, 3]
    call(**parameters, journal_ids=journal_ids)
    assert client.calls[0][1]["journal_ids"] == [3, 9]
    assert journal_ids == [9, 3]
    for invalid in ([], [True], [3.0], [0], [3, 3], list(range(1, 1002))):
        with pytest.raises(ValueError):
            call(**parameters, journal_ids=invalid)
        assert len(client.calls) == 1


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_python_validator_rejects_integral_float_ids(capability_id):
    # JSON Schema accepts mathematically integral numbers; the Python boundary
    # retains the existing strict record-ID type convention.
    request = _request(capability_id)
    request["parameters"]["journal_ids"] = [3.0]
    with pytest.raises(reports.FinancialReportError) as caught:
        _validate(capability_id, request)
    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize("capability_id", READ_CASES)
def test_cursor_binds_journal_set_and_keeps_unfiltered_legacy_payload(capability_id):
    read, _validator, factory, port_factory = READ_CASES[capability_id]
    request = factory(limit=1)
    unfiltered = read(port_factory(), request)
    old_cursor = unfiltered["next_cursor"]
    old_payload = json.loads(
        base64.urlsafe_b64decode(old_cursor + "=" * (-len(old_cursor) % 4))
    )
    assert set(old_payload) == {
        "after_line_id",
        "capability",
        "company_id",
        "database",
        "date_from",
        "date_to",
        "user_login",
        "version",
    }
    request["parameters"]["journal_ids"] = [9, 3]
    first = read(port_factory(), request)
    token = first["next_cursor"]
    request["parameters"].update(cursor=token, journal_ids=[3, 9])
    port = port_factory()
    read(port, request)
    assert port.calls[0]["journal_ids"] == [3, 9]
    assert port.calls[0]["after_line_id"] == first["lines"][-1]["id"]

    wrong_requests = []
    for journal_ids in ([3], [4, 9]):
        wrong = copy.deepcopy(request)
        wrong["parameters"]["journal_ids"] = journal_ids
        wrong_requests.append(wrong)
    unfiltered_request = factory(cursor=token)
    wrong_requests.append(unfiltered_request)
    wrong = copy.deepcopy(request)
    wrong["parameters"]["cursor"] = old_cursor
    wrong_requests.append(wrong)
    wrong = copy.deepcopy(request)
    wrong["parameters"][
        "as_of" if capability_id == "report.balance_sheet" else "date_to"
    ] = "2025-02-28"
    wrong_requests.append(wrong)
    for key, value in (
        ("company_id", 8),
        ("database", "v4-test"),
        ("user_login", "other-agent"),
    ):
        wrong = copy.deepcopy(request)
        wrong["context"][key] = value
        wrong_requests.append(wrong)
    for wrong in wrong_requests:
        port = port_factory()
        with pytest.raises(reports.FinancialReportError) as caught:
            read(port, wrong)
        assert caught.value.code == "invalid_cursor" and port.calls == []


@pytest.mark.parametrize("capability_id", READ_CASES)
@pytest.mark.parametrize("digest", [None, True, "0" * 64, {}])
def test_cursor_rejects_invalid_journal_filter_digest(capability_id, digest):
    read, _validator, factory, port_factory = READ_CASES[capability_id]
    request = factory(limit=1)
    request["parameters"]["journal_ids"] = [1, 9]
    token = read(port_factory(), request)["next_cursor"]
    payload = json.loads(base64.urlsafe_b64decode(token + "=" * (-len(token) % 4)))
    payload["journal_ids_sha256"] = digest
    request["parameters"]["cursor"] = (
        base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    )
    with pytest.raises(reports.FinancialReportError) as caught:
        read(port_factory(), request)
    assert caught.value.code == "invalid_cursor"


@pytest.mark.parametrize("capability_id", READ_CASES)
def test_thousand_journal_ids_fit_existing_cursor_limit_and_paginate(
    capability_id, registry
):
    read, _validator, factory, port_factory = READ_CASES[capability_id]
    request = factory(limit=1)
    journal_ids = list(range(100_000, 101_000))
    request["parameters"]["journal_ids"] = journal_ids
    first = read(port_factory(), request)
    assert first["has_more"] is True
    assert len(first["next_cursor"]) <= 4096
    request["parameters"].update(
        cursor=first["next_cursor"], journal_ids=journal_ids[::-1]
    )
    registry.validate_instance(
        f"schemas/v1/{capability_id}.request.schema.json", request
    )
    port = port_factory()
    second = read(port, request)
    assert second["lines"][0]["id"] != first["lines"][0]["id"]
    assert port.calls[0]["journal_ids"] == journal_ids


@pytest.mark.parametrize(
    "capability_id",
    ["report.partner_ledger", "report.cash_flow", "report.aged_receivable"],
)
@pytest.mark.parametrize("export", [False, True])
def test_other_reports_do_not_accept_journal_ids(capability_id, export, registry):
    if export:
        capability_id += ".export"
        request = export_tests._request(capability_id)
        validate = partial(
            reports.validate_financial_report_export_request, capability_id
        )
    elif capability_id == "report.cash_flow":
        request, validate = trial_tests._request(), reports.validate_cash_flow_request
    else:
        request = typed_tests._request(capability_id)
        validate = partial(
            reports.validate_typed_financial_report_request, capability_id
        )
    request["parameters"]["journal_ids"] = [3]
    with pytest.raises(reports.FinancialReportError):
        validate(request)
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(
            f"schemas/v1/{capability_id}.request.schema.json", request
        )


@pytest.mark.parametrize("export", [False, True])
def test_partner_ledger_ports_also_reject_unsupported_journal_filter(export):
    capability_id = (
        "report.partner_ledger.export" if export else "report.partner_ledger"
    )
    client = RecordingClient(capability_id)
    port = _port(capability_id, client)
    parameters = {
        "company_id": 7,
        "date_from": "2025-01-01",
        "date_to": "2025-01-31",
        "journal_ids": [3],
    }
    with pytest.raises(ValueError, match="unsupported"):
        if export:
            port.export(capability_id=capability_id, format="pdf", **parameters)
        else:
            port.read_page(after_line_id=None, limit=100, **parameters)
    assert client.calls == []
