from __future__ import annotations

from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge.period_context import (
    ACTION,
    OdooPeriodContextPort,
)
from odoo_accounting_cli_v4.capabilities.period_context import (
    PeriodContextReadError,
    read_period_context,
    validate_period_context_request,
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
    value = {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "cursor_found": True,
        "items": items,
    }
    value.update(overrides)
    return value


def _fiscal_year(
    record_id: int = 12,
    *,
    name: str = "2026",
    date_from: str = "2026-01-01",
    date_to: str = "2026-12-31",
    company_id: int = 7,
) -> dict[str, Any]:
    return {
        "id": record_id,
        "name": name,
        "company_id": company_id,
        "date_from": date_from,
        "date_to": date_to,
    }


class FakePort:
    def __init__(self, pages: list[dict[str, Any]]) -> None:
        self.pages = pages
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
        return self.pages.pop(0)


def test_lock_dates_and_native_fiscal_year_resolution_are_closed_single_reads() -> None:
    lock_result = {
        "company_id": 7,
        "configured": {
            "fiscalyear_lock_date": "2025-12-31",
            "tax_lock_date": None,
            "sale_lock_date": None,
            "purchase_lock_date": None,
            "hard_lock_date": "2026-01-31",
        },
        "effective": {
            "fiscalyear_lock_date": "2025-12-31",
            "tax_lock_date": None,
            "sale_lock_date": None,
            "purchase_lock_date": None,
            "hard_lock_date": "2026-01-31",
        },
    }
    lock_port = FakePort([_page([lock_result])])
    assert read_period_context(
        "company.lock_dates.inspect", lock_port, _request({})
    ) == lock_result
    assert lock_port.calls == [
        {
            "capability_id": "company.lock_dates.inspect",
            "company_id": 7,
            "parameters": {},
        }
    ]

    resolved = {
        "company_id": 7,
        "date": "2026-08-28",
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "fiscal_year": {"id": 12, "name": "2026"},
    }
    resolve_port = FakePort([_page([resolved])])
    assert read_period_context(
        "company.fiscal_year.resolve",
        resolve_port,
        _request({"date": "2026-08-28"}),
    ) == resolved
    assert resolve_port.calls[0]["parameters"] == {"date": "2026-08-28"}


def test_fiscal_year_search_uses_filter_bound_date_id_cursor() -> None:
    request = _request(
        {
            "contains_date": "2026-06-01",
            "date_from": "2026-01-01",
            "date_to": "2026-12-31",
            "limit": 1,
        }
    )
    first_port = FakePort(
        [
            _page(
                [
                    _fiscal_year(),
                    _fiscal_year(
                        11,
                        name="FY 2025/26",
                        date_from="2025-07-01",
                        date_to="2026-06-30",
                    ),
                ]
            )
        ]
    )
    first = read_period_context("fiscal_year.search", first_port, request)

    assert first["items"] == [_fiscal_year()]
    assert first["has_more"] is True
    assert isinstance(first["next_cursor"], str)
    assert first_port.calls[0]["parameters"] == {
        "contains_date": "2026-06-01",
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "after": None,
        "limit": 2,
    }

    second_request = _request(
        {
            "contains_date": "2026-06-01",
            "date_from": "2026-01-01",
            "date_to": "2026-12-31",
            "limit": 1,
            "cursor": first["next_cursor"],
        }
    )
    second_port = FakePort(
        [
            _page(
                [
                    _fiscal_year(
                        11,
                        name="FY 2025/26",
                        date_from="2025-07-01",
                        date_to="2026-06-30",
                    )
                ]
            )
        ]
    )
    second = read_period_context("fiscal_year.search", second_port, second_request)

    assert second["has_more"] is False
    assert second["next_cursor"] is None
    assert second_port.calls[0]["parameters"]["after"] == ["2026-01-01", 12]


def test_cursor_cannot_be_reused_with_changed_company_or_filters() -> None:
    first = read_period_context(
        "fiscal_year.search",
        FakePort([_page([_fiscal_year(), _fiscal_year(11)])]),
        _request({"limit": 1}),
    )
    changed = _request(
        {"contains_date": "2026-08-28", "limit": 1, "cursor": first["next_cursor"]}
    )
    port = FakePort([_page([])])

    with pytest.raises(PeriodContextReadError) as caught:
        read_period_context("fiscal_year.search", port, changed)

    assert caught.value.code == "invalid_cursor"
    assert port.calls == []


def test_search_rejects_cross_company_filter_misses_and_wrong_order() -> None:
    cases = [
        [_fiscal_year(company_id=8)],
        [_fiscal_year(date_from="2025-01-01", date_to="2025-12-31")],
        [
            _fiscal_year(11, date_from="2025-01-01", date_to="2025-12-31"),
            _fiscal_year(),
        ],
    ]
    for items in cases:
        with pytest.raises(PeriodContextReadError) as caught:
            read_period_context(
                "fiscal_year.search",
                FakePort([_page(items)]),
                _request({"contains_date": "2026-06-01"}),
            )
        assert caught.value.code == "failed_validation"


def test_get_is_company_scoped_and_reports_a_missing_record() -> None:
    assert read_period_context(
        "fiscal_year.get",
        FakePort([_page([_fiscal_year()])]),
        _request({"fiscal_year_id": 12}),
    ) == _fiscal_year()

    with pytest.raises(PeriodContextReadError) as caught:
        read_period_context(
            "fiscal_year.get",
            FakePort([_page([])]),
            _request({"fiscal_year_id": 999}),
        )
    assert caught.value.code == "record_not_found"


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    [
        ("company.lock_dates.inspect", {"company_id": 7}),
        ("company.fiscal_year.resolve", {}),
        ("company.fiscal_year.resolve", {"date": "2026-02-30"}),
        ("fiscal_year.get", {"fiscal_year_id": True}),
        ("fiscal_year.search", {"extra": True}),
        (
            "fiscal_year.search",
            {"date_from": "2026-12-31", "date_to": "2026-01-01"},
        ),
        ("fiscal_year.search", {"limit": True}),
    ],
)
def test_requests_reject_expanded_or_invalid_parameters(
    capability_id: str, parameters: dict[str, Any]
) -> None:
    with pytest.raises(PeriodContextReadError) as caught:
        validate_period_context_request(capability_id, _request(parameters))
    assert caught.value.code == "invalid_request"


class Client:
    def __init__(self, response: Any) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def invoke(self, action: str, payload: dict[str, Any]) -> Any:
        self.calls.append((action, payload))
        return self.response


def test_bridge_port_invokes_only_the_fixed_action_and_records_identity() -> None:
    client = Client(_page([_fiscal_year()]))
    port = OdooPeriodContextPort(client)

    result = port.read(
        capability_id="fiscal_year.get",
        company_id=7,
        parameters={"fiscal_year_id": 12},
    )

    assert result == _page([_fiscal_year()])
    assert port.user_id == 5
    assert client.calls == [
        (
            ACTION,
            {
                "capability_id": "fiscal_year.get",
                "company_id": 7,
                "parameters": {"fiscal_year_id": 12},
            },
        )
    ]


def test_bridge_port_rejects_unknown_capabilities_and_malformed_pages() -> None:
    client = Client(_page([]))
    port = OdooPeriodContextPort(client)
    with pytest.raises(ValueError, match="Unsupported"):
        port.read(capability_id="fiscal_year.unlink", company_id=7, parameters={})
    assert client.calls == []

    client.response = _page([], user_id=True)
    with pytest.raises(ValueError, match="invalid period-context page"):
        port.read(capability_id="fiscal_year.search", company_id=7, parameters={})
    with pytest.raises(ValueError, match="No verified"):
        _ = port.user_id
