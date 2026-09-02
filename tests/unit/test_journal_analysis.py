from __future__ import annotations

from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge.journal_analysis import (
    ACTION,
    OdooJournalAnalysisPort,
)
from odoo_accounting_cli_v4.capabilities.journal_analysis import (
    JournalAnalysisReadError,
    read_journal_analysis,
    validate_journal_analysis_request,
)

REQUEST_ID = "12345678-1234-4234-8234-123456789abc"


def _request(parameters: dict[str, Any], *, company_id: int = 7) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "context": {
            "database": "v4-dev",
            "company_id": company_id,
            "user_login": "accountant@example.com",
            "language": "en_US",
            "timezone": "UTC",
        },
        "parameters": parameters,
    }


def _page(items: list[dict[str, Any]], **overrides: Any) -> dict[str, Any]:
    page = {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "cursor_found": True,
        "items": items,
    }
    page.update(overrides)
    return page


def _resolution(**overrides: Any) -> dict[str, Any]:
    value = {
        "company_id": 7,
        "journal": {"id": 9, "code": "INV", "name": "Customer Invoices"},
        "requested_date": "2026-08-28",
        "has_tax": True,
        "accounting_date": "2026-08-31",
        "adjusted": True,
    }
    value.update(overrides)
    return value


def _summary(**overrides: Any) -> dict[str, Any]:
    value = {
        "company_id": 7,
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "basis": "posted_entries",
        "group_by": "account",
        "company_currency": {"id": 6, "code": "CNY"},
        "groups": [
            {
                "group": {"id": 101, "code": "1001", "name": "Cash"},
                "row_count": 2,
                "debit": "10.5",
                "credit": "2",
                "balance": "8.5",
            },
            {
                "group": {"id": 102, "code": "1002", "name": "Bank"},
                "row_count": 1,
                "debit": "0",
                "credit": "3",
                "balance": "-3",
            },
        ],
        "totals": {
            "row_count": 3,
            "debit": "10.5",
            "credit": "5",
            "balance": "5.5",
        },
    }
    value.update(overrides)
    return value


def _analytic_summary(**overrides: Any) -> dict[str, Any]:
    value = {
        "company_id": 7,
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "basis": "analytic_lines",
        "group_by": "analytic_account",
        "plan": {"id": 11, "name": "Projects"},
        "company_currency": {"id": 6, "code": "CNY"},
        "groups": [
            {
                "analytic_account": {"id": 21, "name": "Project A", "code": "A"},
                "row_count": 2,
                "amount": "10.5",
                "unit_amount": "3",
            },
            {
                "analytic_account": {"id": 22, "name": "Project B", "code": None},
                "row_count": 1,
                "amount": "-2",
                "unit_amount": "0.5",
            },
        ],
        "totals": {"row_count": 3, "amount": "8.5", "unit_amount": "3.5"},
    }
    value.update(overrides)
    return value


class FakePort:
    def __init__(self, page: dict[str, Any]) -> None:
        self.page = page
        self.calls: list[dict[str, Any]] = []

    @property
    def user_id(self) -> int:
        return 5

    def read(
        self,
        *,
        capability_id: str,
        company_id: int,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "capability_id": capability_id,
                "company_id": company_id,
                "parameters": parameters,
            }
        )
        return self.page


class Client:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((action, payload))
        return self.response


def test_accounting_date_resolution_is_a_closed_single_read() -> None:
    parameters = {"journal_id": 9, "date": "2026-08-28", "has_tax": True}
    result = _resolution()
    port = FakePort(_page([result]))

    assert (
        read_journal_analysis(
            port, "journal.accounting_date.resolve", _request(parameters)
        )
        == result
    )
    assert port.calls == [
        {
            "capability_id": "journal.accounting_date.resolve",
            "company_id": 7,
            "parameters": parameters,
        }
    ]

def test_summary_accepts_only_ordered_groups_and_exact_totals() -> None:
    parameters = {
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "group_by": "account",
    }
    result = _summary()
    assert (
        read_journal_analysis(
            FakePort(_page([result])),
            "journal_item.analysis.summary",
            _request(parameters),
        )
        == result
    )

    invalid = [
        _summary(groups=list(reversed(result["groups"]))),
        _summary(totals={**result["totals"], "balance": "6"}),
        _summary(totals={**result["totals"], "debit": "NaN"}),
        _summary(basis="all_entries"),
    ]
    for value in invalid:
        with pytest.raises(JournalAnalysisReadError) as caught:
            read_journal_analysis(
                FakePort(_page([value])),
                "journal_item.analysis.summary",
                _request(parameters),
            )
        assert caught.value.code == "failed_validation"


def test_analytic_summary_normalizes_optional_filter_and_fails_closed() -> None:
    parameters = {
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "plan_id": 11,
    }
    result = _analytic_summary()
    port = FakePort(_page([result]))

    assert read_journal_analysis(
        port, "analytic.line.summary", _request(parameters)
    ) == result
    assert port.calls == [
        {
            "capability_id": "analytic.line.summary",
            "company_id": 7,
            "parameters": {**parameters, "analytic_account_id": None},
        }
    ]

    explicit_null_port = FakePort(_page([result]))
    assert read_journal_analysis(
        explicit_null_port,
        "analytic.line.summary",
        _request({**parameters, "analytic_account_id": None}),
    ) == result
    assert explicit_null_port.calls[0]["parameters"] == {
        **parameters,
        "analytic_account_id": None,
    }

    invalid = [
        _analytic_summary(groups=list(reversed(result["groups"]))),
        _analytic_summary(totals={**result["totals"], "amount": "9"}),
        _analytic_summary(plan={"id": 12, "name": "Other"}),
        _analytic_summary(basis="posted_entries"),
    ]
    for value in invalid:
        with pytest.raises(JournalAnalysisReadError) as caught:
            read_journal_analysis(
                FakePort(_page([value])),
                "analytic.line.summary",
                _request(parameters),
            )
        assert caught.value.code == "failed_validation"


def test_analytic_summary_account_filter_allows_only_the_requested_group() -> None:
    parameters = {
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "plan_id": 11,
        "analytic_account_id": 21,
    }
    group = _analytic_summary()["groups"][0]
    result = _analytic_summary(
        groups=[group],
        totals={
            "row_count": group["row_count"],
            "amount": group["amount"],
            "unit_amount": group["unit_amount"],
        },
    )
    assert (
        read_journal_analysis(
            FakePort(_page([result])),
            "analytic.line.summary",
            _request(parameters),
        )
        == result
    )

    with pytest.raises(JournalAnalysisReadError) as caught:
        read_journal_analysis(
            FakePort(_page([_analytic_summary()])),
            "analytic.line.summary",
            _request(parameters),
        )
    assert caught.value.code == "failed_validation"


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    [
        (
            "journal.accounting_date.resolve",
            {"journal_id": 9, "date": "2026-08-28", "has_tax": 1},
        ),
        (
            "journal.accounting_date.resolve",
            {"journal_id": 9, "date": "2026-08-28", "has_tax": False, "x": 1},
        ),
        (
            "journal_item.analysis.summary",
            {
                "date_from": "2026-12-31",
                "date_to": "2026-01-01",
                "group_by": "account",
            },
        ),
        (
            "journal_item.analysis.summary",
            {
                "date_from": "2026-01-01",
                "date_to": "2026-12-31",
                "group_by": "partner",
            },
        ),
        (
            "analytic.line.summary",
            {
                "date_from": "2026-01-01",
                "date_to": "2026-12-31",
                "plan_id": 11,
                "limit": 10,
            },
        ),
        (
            "analytic.line.summary",
            {
                "date_from": "2026-12-31",
                "date_to": "2026-01-01",
                "plan_id": 11,
            },
        ),
    ],
)
def test_requests_reject_extra_or_generic_query_controls(
    capability_id: str, parameters: dict[str, Any]
) -> None:
    with pytest.raises(JournalAnalysisReadError) as caught:
        validate_journal_analysis_request(capability_id, _request(parameters))
    assert caught.value.code == "invalid_request"


def test_resolution_reports_missing_and_rejects_contract_drift() -> None:
    request = _request({"journal_id": 9, "date": "2026-08-28", "has_tax": True})
    with pytest.raises(JournalAnalysisReadError) as missing:
        read_journal_analysis(
            FakePort(_page([])), "journal.accounting_date.resolve", request
        )
    assert missing.value.code == "record_not_found"

    for result in (
        _resolution(company_id=8),
        _resolution(adjusted=False),
        _resolution(journal={"id": 10, "code": "BNK", "name": "Bank"}),
    ):
        with pytest.raises(JournalAnalysisReadError) as drift:
            read_journal_analysis(
                FakePort(_page([result])),
                "journal.accounting_date.resolve",
                request,
            )
        assert drift.value.code == "failed_validation"


def test_availability_failures_are_distinct() -> None:
    request = _request({"journal_id": 9, "date": "2026-08-28", "has_tax": False})
    cases = [
        ({"company_visible": False, "access_allowed": False}, "company_unavailable"),
        ({"module_installed": False, "access_allowed": False}, "uninstalled"),
        ({"access_allowed": False}, "unauthorized"),
    ]
    for overrides, code in cases:
        with pytest.raises(JournalAnalysisReadError) as caught:
            read_journal_analysis(
                FakePort(_page([], **overrides)),
                "journal.accounting_date.resolve",
                request,
            )
        assert caught.value.code == code


def test_bridge_port_uses_only_the_fixed_action_and_minimal_payload() -> None:
    page = _page([_resolution()])
    client = Client(page)
    port = OdooJournalAnalysisPort(client)
    parameters = {"journal_id": 9, "date": "2026-08-28", "has_tax": True}

    assert (
        port.read(
            capability_id="journal.accounting_date.resolve",
            company_id=7,
            parameters=parameters,
        )
        == page
    )
    assert port.user_id == 5
    assert client.calls == [
        (
            ACTION,
            {
                "capability_id": "journal.accounting_date.resolve",
                "company_id": 7,
                "parameters": parameters,
            },
        )
    ]


def test_bridge_port_rejects_unknown_capability_and_malformed_page() -> None:
    with pytest.raises(ValueError):
        OdooJournalAnalysisPort(Client(_page([]))).read(
            capability_id="journal_item.analysis.group_by",
            company_id=7,
            parameters={},
        )
    with pytest.raises(ValueError):
        OdooJournalAnalysisPort(Client({"user_id": 5})).read(
            capability_id="journal_item.analysis.summary",
            company_id=7,
            parameters={
                "date_from": "2026-01-01",
                "date_to": "2026-12-31",
                "group_by": "account",
            },
        )
