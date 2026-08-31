from __future__ import annotations

import base64
import copy
import json
from pathlib import Path

import pytest

from odoo_accounting_cli_v4.capabilities.invoices import (
    InvoiceError,
    get_invoice,
    inspect_invoice_payment_status,
    search_invoices,
    validate_invoice_get_request,
    validate_invoice_payment_status_request,
    validate_invoice_search_request,
)
from odoo_accounting_cli_v4.registry import load_registry

REQUEST_ID = "7bc39413-0d69-4092-9319-795d33f3167c"


class FakePort:
    def __init__(
        self,
        *,
        rows: list[dict] | None = None,
        invoice: dict | None = None,
        payment_status: dict | None = None,
        company_visible: bool = True,
        module_installed: bool = True,
        access_allowed: bool | None = None,
    ) -> None:
        self.user_id = 42
        self.rows = [] if rows is None else rows
        self.invoice = invoice
        self.payment_status = payment_status
        self.company_visible = company_visible
        self.module_installed = module_installed
        self.access_allowed = (
            company_visible and module_installed
            if access_allowed is None
            else access_allowed
        )
        self.search_calls: list[dict] = []
        self.get_calls: list[dict] = []
        self.status_calls: list[dict] = []

    def _page(self, **payload) -> dict:
        if not self.access_allowed:
            payload = {
                key: ([] if key == "rows" else None) for key in payload
            }
        return {
            "user_id": self.user_id,
            "company_visible": self.company_visible,
            "module_installed": self.module_installed,
            "access_allowed": self.access_allowed,
            **payload,
        }

    def search_page(self, **kwargs) -> dict:
        self.search_calls.append(kwargs)
        return self._page(rows=copy.deepcopy(self.rows))

    def get_invoice(self, **kwargs) -> dict:
        self.get_calls.append(kwargs)
        return self._page(invoice=copy.deepcopy(self.invoice))

    def inspect_payment_status(self, **kwargs) -> dict:
        self.status_calls.append(kwargs)
        return self._page(payment_status=copy.deepcopy(self.payment_status))


def _context() -> dict:
    return {
        "database": "odoo_cli_v4_dev",
        "company_id": 7,
        "user_login": "accountant@example.com",
        "language": "en_US",
        "timezone": "UTC",
    }


def _request(parameters: dict) -> dict:
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "context": _context(),
        "parameters": parameters,
    }


def _search_request(**parameters) -> dict:
    return _request(parameters)


def _get_request(invoice_id=30) -> dict:
    return _request({"invoice_id": invoice_id})


def _status_request(invoice_id=30) -> dict:
    return _request({"invoice_id": invoice_id})


def _journal() -> dict:
    return {"id": 8, "code": "INV", "name": "Customer Invoices"}


def _currency(code: str = "USD", record_id: int = 2) -> dict:
    return {"id": record_id, "code": code}


def _partner() -> dict:
    return {"id": 9, "name": "Fixture Customer"}


def _header(record_id: int = 30, move_date: str = "2025-02-01") -> dict:
    return {
        "id": record_id,
        "name": "INV/2025/0030",
        "move_type": "out_invoice",
        "state": "posted",
        "date": move_date,
        "invoice_date": "2025-01-20",
        "invoice_date_due": "2025-02-20",
        "ref": None,
        "payment_reference": None,
        "invoice_origin": "SO001",
        "journal": _journal(),
        "company_id": 7,
        "currency": _currency(),
        "partner": _partner(),
        "amount_untaxed": "100.00",
        "amount_tax": "13.00",
        "amount_total": "113.00",
        "amount_residual": "63.00",
        "payment_state": "partial",
    }


def _tax() -> dict:
    return {
        "id": 4,
        "name": "Tax 13%",
        "type_tax_use": "sale",
        "amount_type": "percent",
        "amount": "13.00",
        "price_include": False,
    }


def _line() -> dict:
    return {
        "id": 301,
        "sequence": 10,
        "display_type": "product",
        "name": "Fixture service",
        "product": {"id": 11, "name": "Consulting"},
        "account": {"id": 101, "code": "6000", "name": "Sales"},
        "quantity": "1.00",
        "price_unit": "100.00",
        "discount": "0.00",
        "price_subtotal": "100.00",
        "price_total": "113.00",
        "deferred_start_date": None,
        "deferred_end_date": None,
        "taxes": [_tax()],
        "analytic_distribution": {},
    }


def _invoice() -> dict:
    return {**_header(), "lines": [_line()]}


def _status() -> dict:
    return {
        "id": 30,
        "name": "INV/2025/0030",
        "move_type": "out_invoice",
        "state": "posted",
        "payment_state": "partial",
        "company_id": 7,
        "currency": _currency(),
        "company_currency": _currency("SGD", 37),
        "amount_total": "113.00",
        "amount_residual": "63.00",
        "receivable_payable_lines": [
            {
                "id": 302,
                "account": {
                    "id": 102,
                    "code": "1100",
                    "name": "Accounts Receivable",
                    "account_type": "asset_receivable",
                },
                "date_maturity": "2025-02-20",
                "balance": "152.55",
                "amount_currency": "113.00",
                "amount_residual": "85.05",
                "amount_residual_currency": "63.00",
                "currency": _currency(),
                "reconciled": False,
                "matching_number": "P",
            }
        ],
        "reconciliations": [
            {
                "id": 501,
                "date": "2025-01-25",
                "amount": "50.00",
                "company_amount": "67.50",
                "currency": _currency(),
                "company_currency": _currency("SGD", 37),
                "invoice_line_id": 302,
                "counterpart_line_id": 402,
                "counterpart_move": {
                    "id": 40,
                    "name": "BNK1/2025/0040",
                    "move_type": "entry",
                    "state": "posted",
                    "date": "2025-01-25",
                },
                "payment_id": 5,
                "exchange_move_id": None,
            }
        ],
        "payments": [
            {
                "id": 5,
                "name": "BNK1/2025/0040",
                "state": "paid",
                "date": "2025-01-25",
                "payment_type": "inbound",
                "partner_type": "customer",
                "amount": "50.00",
                "currency": _currency(),
                "journal": {"id": 10, "code": "BNK1", "name": "Bank"},
                "payment_method": {
                    "id": 3,
                    "code": "manual",
                    "name": "Manual Payment",
                },
                "move_id": 40,
                "is_reconciled": True,
                "is_matched": True,
            }
        ],
        "outstanding_items": [
            {
                "line_id": 602,
                "move_id": 60,
                "payment_id": 6,
                "date": "2025-01-27",
                "label": "BNK1/2025/0060",
                "amount": "20.00",
                "currency": _currency(),
            }
        ],
    }


def test_search_normalizes_filters_and_uses_descending_keyset_cursor() -> None:
    rows = [_header(30, "2025-02-01"), _header(29, "2025-02-01"), _header(10, "2025-01-31")]
    request = _search_request(
        limit=2,
        date_from="2025-01-01",
        date_to=None,
        document_types=["in_refund", "out_invoice"],
        states=["cancel", "draft", "posted"],
        payment_states=["paid", "not_paid", "partial"],
        journal_id=None,
        partner_id=9,
        query="inv/2025",
    )
    port = FakePort(rows=rows)

    result = search_invoices(port, request)

    assert result == {
        "items": rows[:2],
        "has_more": True,
        "next_cursor": result["next_cursor"],
    }
    assert isinstance(result["next_cursor"], str)
    assert port.search_calls == [
        {
            "company_id": 7,
            "after": None,
            "limit": 3,
            "filters": {
                "date_from": "2025-01-01",
                "date_to": None,
                "document_types": ["out_invoice", "in_refund"],
                "states": ["draft", "posted", "cancel"],
                "payment_states": ["not_paid", "paid", "partial"],
                "journal_id": None,
                "partner_id": 9,
                "query": "inv/2025",
            },
        }
    ]

    second_request = copy.deepcopy(request)
    second_request["parameters"].update(limit=100, cursor=result["next_cursor"])
    second_port = FakePort(rows=rows[2:])
    assert search_invoices(second_port, second_request) == {
        "items": rows[2:],
        "has_more": False,
        "next_cursor": None,
    }
    assert second_port.search_calls[0]["after"] == ["2025-02-01", 29]


def test_search_defaults_and_maximum_limit_are_closed() -> None:
    port = FakePort()
    assert search_invoices(port, _search_request()) == {
        "items": [],
        "has_more": False,
        "next_cursor": None,
    }
    assert port.search_calls[0] == {
        "company_id": 7,
        "after": None,
        "limit": 101,
        "filters": {
            "date_from": None,
            "date_to": None,
            "document_types": [],
            "states": [],
            "payment_states": [],
            "journal_id": None,
            "partner_id": None,
            "query": None,
        },
    }
    search_invoices(FakePort(), _search_request(limit=1000))
    with pytest.raises(InvoiceError) as caught:
        search_invoices(FakePort(), _search_request(limit=1001))
    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize(
    "parameters",
    [
        {"unexpected": True},
        {"date_from": "2025-02-30"},
        {"date_from": "2025-02-01", "date_to": "2025-01-31"},
        {"document_types": []},
        {"document_types": ["entry"]},
        {"document_types": ["out_invoice", "out_invoice"]},
        {"states": None},
        {"states": ["invalid"]},
        {"payment_states": []},
        {"payment_states": ["invalid"]},
        {"query": " untrimmed"},
        {"query": "x" * 201},
        {"journal_id": True},
        {"partner_id": 0},
    ],
)
def test_invalid_search_parameters_fail_before_the_port(parameters: dict) -> None:
    port = FakePort()
    with pytest.raises(InvoiceError) as caught:
        search_invoices(port, _search_request(**parameters))
    assert caught.value.code == "invalid_request"
    assert caught.value.exit_code == 2
    assert port.search_calls == []


def _forge_cursor(cursor: str, mutate) -> str:
    padding = "=" * (-len(cursor) % 4)
    payload = json.loads(base64.urlsafe_b64decode(cursor + padding))
    mutate(payload)
    return base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode()
    ).decode().rstrip("=")


def test_cursor_is_bound_and_rejects_boolean_aliases() -> None:
    rows = [_header(30, "2025-02-01"), _header(29, "2025-01-31")]
    first = search_invoices(
        FakePort(rows=rows),
        _search_request(limit=1, states=["posted"], journal_id=8),
    )
    cursor = first["next_cursor"]
    assert cursor

    requests = []
    for section, key, value in [
        ("context", "database", "other-db"),
        ("context", "company_id", 8),
        ("context", "user_login", "other-user"),
        ("parameters", "states", ["draft"]),
    ]:
        request = _search_request(limit=1, states=["posted"], journal_id=8, cursor=cursor)
        request[section][key] = value
        requests.append(request)
    requests.append(
        _search_request(
            limit=1,
            states=["posted"],
            journal_id=8,
            cursor=_forge_cursor(
                cursor,
                lambda value: (
                    value.update(company_id=True),
                    value["filters"].update(journal_id=True),
                ),
            ),
        )
    )
    for request in requests:
        port = FakePort()
        with pytest.raises(InvoiceError) as caught:
            search_invoices(port, request)
        assert caught.value.code == "invalid_cursor"
        assert port.search_calls == []


@pytest.mark.parametrize(
    "raw_mutation",
    [
        lambda raw: raw.replace('"query":null', '"query":NaN'),
        lambda raw: raw.replace('"query":null', '"query":1e400'),
        lambda raw: raw.replace('"version":1', '"version":1,"version":1'),
        lambda raw: raw.replace('"query":null', '"query":null,"query":null'),
    ],
)
def test_cursor_rejects_nonfinite_and_duplicate_json(raw_mutation) -> None:
    rows = [_header(30, "2025-02-01"), _header(29, "2025-01-31")]
    first = search_invoices(FakePort(rows=rows), _search_request(limit=1))
    padding = "=" * (-len(first["next_cursor"]) % 4)
    raw = base64.urlsafe_b64decode(first["next_cursor"] + padding).decode()
    forged = base64.urlsafe_b64encode(raw_mutation(raw).encode()).decode().rstrip("=")

    with pytest.raises(InvoiceError) as caught:
        search_invoices(FakePort(), _search_request(limit=1, cursor=forged))
    assert caught.value.code == "invalid_cursor"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda row: row.update(extra=True),
        lambda row: row.update(company_id=8),
        lambda row: row.update(move_type="entry"),
        lambda row: row.update(amount_total=113.0),
        lambda row: row.update(amount_total="NaN"),
        lambda row: row.update(amount_total="114.00"),
        lambda row: row.update(payment_state=None),
        lambda row: row.update(invoice_date="2025-02-30"),
    ],
)
def test_invalid_search_rows_never_become_verified(mutation) -> None:
    row = _header()
    mutation(row)
    with pytest.raises(InvoiceError) as caught:
        search_invoices(FakePort(rows=[row]), _search_request())
    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8


@pytest.mark.parametrize(
    ("parameters", "mutation"),
    [
        ({"date_from": "2025-02-02"}, lambda row: None),
        ({"date_to": "2025-01-31"}, lambda row: None),
        ({"document_types": ["in_invoice"]}, lambda row: None),
        ({"states": ["draft"]}, lambda row: None),
        ({"payment_states": ["paid"]}, lambda row: None),
        ({"journal_id": 99}, lambda row: None),
        ({"partner_id": 99}, lambda row: None),
        ({"query": "not-present"}, lambda row: None),
    ],
)
def test_search_rows_must_match_every_structured_filter(
    parameters: dict, mutation
) -> None:
    row = _header()
    mutation(row)
    with pytest.raises(InvoiceError) as caught:
        search_invoices(FakePort(rows=[row]), _search_request(**parameters))
    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8


@pytest.mark.parametrize(
    ("query", "field", "value"),
    [
        ("inv/2025", "name", "INV/2025/0030"),
        ("customer ref", "ref", "Customer REF 42"),
        ("pay%0030", "payment_reference", "PAYMENT/2025/0030"),
        ("so_01", "invoice_origin", "SOX01"),
        ("literal\\", "ref", "prefix literal%"),
    ],
)
def test_search_query_is_reverified_with_odoo_ilike_semantics(
    query: str, field: str, value: str
) -> None:
    row = _header()
    row[field] = value

    assert search_invoices(
        FakePort(rows=[row]), _search_request(query=query)
    )["items"] == [row]


def test_search_requires_date_then_id_descending_and_allows_nullable_fields() -> None:
    unordered = [_header(29), _header(30)]
    with pytest.raises(InvoiceError):
        search_invoices(FakePort(rows=unordered), _search_request())

    row = _header()
    row.update(
        name=None,
        invoice_date=None,
        invoice_date_due=None,
        ref=None,
        payment_reference=None,
        invoice_origin=None,
        partner=None,
        state="draft",
        payment_state="not_paid",
    )
    assert search_invoices(FakePort(rows=[row]), _search_request())["items"] == [row]


def test_get_verifies_exact_invoice_and_line_shapes() -> None:
    invoice = _invoice()
    port = FakePort(invoice=invoice)
    assert get_invoice(port, _get_request()) == invoice
    assert port.get_calls == [{"company_id": 7, "invoice_id": 30}]


@pytest.mark.parametrize(
    ("start_date", "end_date"),
    [
        (None, None),
        (None, "2026-12-31"),
        ("2026-09-01", None),
        ("2026-09-01", "2026-12-31"),
        ("2026-12-31", "2026-09-01"),
    ],
)
def test_get_preserves_native_deferred_dates_without_write_pair_constraints(
    start_date: str | None, end_date: str | None
) -> None:
    invoice = _invoice()
    invoice["lines"][0].update(
        deferred_start_date=start_date, deferred_end_date=end_date
    )

    assert get_invoice(FakePort(invoice=invoice), _get_request()) == invoice
    load_registry().validate_instance(
        "schemas/v1/invoice.get.response.schema.json",
        _success_response("invoice.get", invoice),
    )


@pytest.mark.parametrize("field", ("deferred_start_date", "deferred_end_date"))
@pytest.mark.parametrize(
    "value", ("2026-02-30", "20260901", "2026-09-01T00:00:00", 0, True, False)
)
def test_get_rejects_non_iso_deferred_dates(field: str, value: object) -> None:
    invoice = _invoice()
    invoice["lines"][0][field] = value

    with pytest.raises(InvoiceError) as caught:
        get_invoice(FakePort(invoice=invoice), _get_request())
    assert caught.value.code == "failed_validation"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda invoice: invoice.update(extra=True),
        lambda invoice: invoice["lines"][0].update(extra=True),
        lambda invoice: invoice["lines"][0].update(quantity=1.0),
        lambda invoice: invoice["lines"][0].update(account=None),
        lambda invoice: invoice["lines"][0].update(display_type="line_section"),
        lambda invoice: invoice["lines"][0].update(display_type="tax"),
        lambda invoice: invoice["lines"][0].update(display_type=None),
        lambda invoice: invoice["lines"][0].pop("deferred_start_date"),
        lambda invoice: invoice["lines"][0].pop("deferred_end_date"),
        lambda invoice: invoice["lines"][0]["taxes"][0].update(extra=True),
        lambda invoice: invoice["lines"][0]["taxes"][0].update(amount=float("inf")),
        lambda invoice: invoice.update(lines=[_line(), _line()]),
    ],
)
def test_invalid_invoice_lines_never_become_verified(mutation) -> None:
    invoice = _invoice()
    mutation(invoice)
    with pytest.raises(InvoiceError) as caught:
        get_invoice(FakePort(invoice=invoice), _get_request())
    assert caught.value.code == "failed_validation"


def test_get_accepts_nullable_odoo_fields_and_section_without_account() -> None:
    invoice = _invoice()
    line = invoice["lines"][0]
    line.update(
        display_type="line_section",
        name=None,
        product=None,
        account=None,
        quantity="0.00",
        price_unit="0.00",
        discount="0.00",
        price_subtotal="0.00",
        price_total="0.00",
        taxes=[],
    )
    invoice.update(
        name=None,
        invoice_date=None,
        invoice_date_due=None,
        invoice_origin=None,
        partner=None,
        amount_untaxed="0.00",
        amount_tax="0.00",
        amount_total="0.00",
        amount_residual="0.00",
    )
    assert get_invoice(FakePort(invoice=invoice), _get_request()) == invoice


@pytest.mark.parametrize("operation", ("search", "get", "status"))
def test_malformed_bridge_pages_are_typed_failed_validation(operation: str) -> None:
    class MalformedPort(FakePort):
        def search_page(self, **kwargs):
            raise ValueError("malformed bridge search page")

        def get_invoice(self, **kwargs):
            raise ValueError("malformed bridge invoice page")

        def inspect_payment_status(self, **kwargs):
            raise ValueError("malformed bridge status page")

    with pytest.raises(InvoiceError) as caught:
        if operation == "search":
            search_invoices(MalformedPort(), _search_request())
        elif operation == "get":
            get_invoice(MalformedPort(), _get_request())
        else:
            inspect_invoice_payment_status(MalformedPort(), _status_request())
    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8


def test_payment_status_verifies_accounting_reconciliations_and_payments() -> None:
    status = _status()
    port = FakePort(payment_status=status)
    assert inspect_invoice_payment_status(port, _status_request()) == status
    assert port.status_calls == [{"company_id": 7, "invoice_id": 30}]


@pytest.mark.parametrize(
    "mutation",
    [
        lambda status: status.update(extra=True),
        lambda status: status.update(company_id=8),
        lambda status: status["receivable_payable_lines"][0].update(extra=True),
        lambda status: status["receivable_payable_lines"][0]["account"].update(account_type="income"),
        lambda status: status["reconciliations"][0].update(company_amount=67.5),
        lambda status: status["reconciliations"][0].update(invoice_line_id=999),
        lambda status: status["reconciliations"][0]["counterpart_move"].update(extra=True),
        lambda status: status["reconciliations"][0].update(payment_id=999),
        lambda status: status["reconciliations"][0].update(currency=_currency("EUR", 3)),
        lambda status: status["reconciliations"][0].update(
            company_currency=_currency("CNY", 2)
        ),
        lambda status: status["payments"][0].update(move_id=999),
        lambda status: status["payments"][0].update(amount="Infinity"),
        lambda status: status["payments"][0]["payment_method"].update(extra=True),
        lambda status: status["outstanding_items"][0].update(extra=True),
        lambda status: status["outstanding_items"][0].update(amount="0"),
        lambda status: status["outstanding_items"][0].update(
            currency=_currency("EUR", 3)
        ),
    ],
)
def test_invalid_payment_status_never_becomes_verified(mutation) -> None:
    status = _status()
    mutation(status)
    with pytest.raises(InvoiceError) as caught:
        inspect_invoice_payment_status(FakePort(payment_status=status), _status_request())
    assert caught.value.code == "failed_validation"


def test_payment_status_enforces_stable_orders_and_unique_records() -> None:
    status = _status()
    second_reconciliation = copy.deepcopy(status["reconciliations"][0])
    second_reconciliation.update(id=502, date="2025-01-24")
    status["reconciliations"].append(second_reconciliation)
    with pytest.raises(InvoiceError):
        inspect_invoice_payment_status(FakePort(payment_status=status), _status_request())

    status = _status()
    duplicate_outstanding = copy.deepcopy(status["outstanding_items"][0])
    status["outstanding_items"].append(duplicate_outstanding)
    with pytest.raises(InvoiceError):
        inspect_invoice_payment_status(FakePort(payment_status=status), _status_request())

    status = _status()
    duplicate_payment = copy.deepcopy(status["payments"][0])
    status["payments"].append(duplicate_payment)
    with pytest.raises(InvoiceError):
        inspect_invoice_payment_status(FakePort(payment_status=status), _status_request())


def test_payment_status_accepts_empty_outstanding_items() -> None:
    status = _status()
    status["outstanding_items"] = []
    assert inspect_invoice_payment_status(
        FakePort(payment_status=status), _status_request()
    ) == status


def test_payment_status_accepts_nullable_optional_ids_and_fields() -> None:
    status = _status()
    line = status["receivable_payable_lines"][0]
    line.update(date_maturity=None, matching_number=None)
    reconciliation = status["reconciliations"][0]
    reconciliation.update(payment_id=None, exchange_move_id=None)
    payment = status["payments"][0]
    payment.update(name=None, move_id=None)
    assert inspect_invoice_payment_status(
        FakePort(payment_status=status), _status_request()
    ) == status


@pytest.mark.parametrize("operation", ["get", "status"])
def test_missing_invoice_is_explicit(operation: str) -> None:
    with pytest.raises(InvoiceError) as caught:
        if operation == "get":
            get_invoice(FakePort(invoice=None), _get_request())
        else:
            inspect_invoice_payment_status(FakePort(payment_status=None), _status_request())
    assert caught.value.code == "record_not_found"
    assert caught.value.exit_code == 4


def test_single_record_requests_are_closed_positive_non_boolean_ids() -> None:
    assert validate_invoice_get_request(_get_request())[2] == 30
    assert validate_invoice_payment_status_request(_status_request())[2] == 30
    for validator, request_factory in [
        (validate_invoice_get_request, _get_request),
        (validate_invoice_payment_status_request, _status_request),
    ]:
        for value in (0, -1, True, "30"):
            with pytest.raises(InvoiceError):
                validator(request_factory(value))
        request = request_factory()
        request["parameters"]["unexpected"] = True
        with pytest.raises(InvoiceError):
            validator(request)


@pytest.mark.parametrize(
    ("port", "code"),
    [
        (FakePort(company_visible=False), "company_unavailable"),
        (FakePort(module_installed=False), "uninstalled"),
        (FakePort(access_allowed=False), "unauthorized"),
    ],
)
@pytest.mark.parametrize("operation", ["search", "get", "status"])
def test_runtime_availability_failures_are_explicit(
    port: FakePort, code: str, operation: str
) -> None:
    with pytest.raises(InvoiceError) as caught:
        if operation == "search":
            search_invoices(port, _search_request())
        elif operation == "get":
            get_invoice(port, _get_request())
        else:
            inspect_invoice_payment_status(port, _status_request())
    assert caught.value.code == code


def test_contradictory_or_wrong_user_page_is_rejected() -> None:
    with pytest.raises(InvoiceError) as caught:
        search_invoices(
            FakePort(company_visible=False, access_allowed=True), _search_request()
        )
    assert caught.value.code == "failed_validation"

    class WrongUserPort(FakePort):
        def search_page(self, **kwargs) -> dict:
            page = super().search_page(**kwargs)
            page["user_id"] = self.user_id + 1
            return page

    with pytest.raises(InvoiceError) as caught:
        search_invoices(WrongUserPort(), _search_request())
    assert caught.value.code == "failed_validation"


def _success_response(capability_id: str, data: dict) -> dict:
    record_ids = (
        [item["id"] for item in data["items"]]
        if capability_id == "invoice.search"
        else [data["id"]]
    )
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "success": True,
        "capability": capability_id,
        "status": "verified",
        "data": data,
        "warnings": [],
        "error": None,
        "odoo": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_id": 42,
            "model": "account.move",
            "record_ids": record_ids,
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": None,
            "verification": {"result": "passed"},
        },
    }


@pytest.mark.parametrize(
    ("capability_id", "request_document", "data"),
    [
        (
            "invoice.search",
            _search_request(states=["posted"], date_from=None),
            {"items": [_header()], "has_more": False, "next_cursor": None},
        ),
        ("invoice.get", _get_request(), _invoice()),
        ("invoice.payment_status.inspect", _status_request(), _status()),
    ],
)
def test_specialized_schemas_accept_success_and_error_documents(
    capability_id: str, request_document: dict, data: dict
) -> None:
    schema_dir = Path(__file__).parents[2] / "schemas" / "v1"
    assert (schema_dir / f"{capability_id}.request.schema.json").is_file()
    assert (schema_dir / f"{capability_id}.response.schema.json").is_file()
    registry = load_registry()
    registry.validate_instance(
        f"schemas/v1/{capability_id}.request.schema.json", request_document
    )
    registry.validate_instance(
        f"schemas/v1/{capability_id}.response.schema.json",
        _success_response(capability_id, data),
    )
    error = _success_response(capability_id, data)
    error.update(
        success=False,
        status="failed_validation",
        data=None,
        error={
            "code": "failed_validation",
            "message": "The result failed validation.",
            "details": {},
            "retryable": False,
        },
    )
    registry.validate_instance(
        f"schemas/v1/{capability_id}.response.schema.json", error
    )


def test_search_validator_exposes_canonical_filters() -> None:
    _, _, filters, limit, cursor = validate_invoice_search_request(
        _search_request(
            document_types=["in_refund", "out_refund"],
            states=["cancel", "draft"],
            payment_states=["partial", "in_payment"],
        )
    )
    assert filters == {
        "date_from": None,
        "date_to": None,
        "document_types": ["out_refund", "in_refund"],
        "states": ["draft", "cancel"],
        "payment_states": ["in_payment", "partial"],
        "journal_id": None,
        "partner_id": None,
        "query": None,
    }
    assert limit == 100
    assert cursor is None
