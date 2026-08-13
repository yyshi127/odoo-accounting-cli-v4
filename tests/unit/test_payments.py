from __future__ import annotations

import base64
import copy
from decimal import Decimal
from pathlib import Path

import pytest

from odoo_accounting_cli_v4.capabilities.payments import (
    PaymentError,
    get_payment,
    search_payments,
    validate_payment_get_request,
    validate_payment_search_request,
)
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry


EMPTY_FILTERS = {
    "date_from": None,
    "date_to": None,
    "states": [],
    "payment_types": [],
    "partner_types": [],
    "journal_id": None,
    "partner_id": None,
    "currency_id": None,
    "query": None,
}


def _request(**parameters: object) -> dict:
    return {
        "schema_version": "v1",
        "request_id": "7bc39413-0d69-4092-9319-795d33f3167c",
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "zh_CN",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }


def _currency(record_id: int = 6, code: str = "CNY") -> dict:
    return {"id": record_id, "code": code}


def _row(
    record_id: int,
    payment_date: str,
    *,
    payment_type: str = "inbound",
    amount: str = "50.00",
) -> dict:
    signed = amount if payment_type == "inbound" else f"-{amount}"
    partner_type = "customer" if payment_type == "inbound" else "supplier"
    return {
        "id": record_id,
        "name": f"BNK/2025/{record_id:04d}",
        "date": payment_date,
        "state": "paid",
        "payment_type": payment_type,
        "partner_type": partner_type,
        "amount": amount,
        "amount_signed": signed,
        "amount_company_currency_signed": signed,
        "currency": _currency(),
        "company_currency": _currency(),
        "company_id": 7,
        "partner": {"id": 16, "name": "Fixture Partner"},
        "journal": {"id": 9, "code": "BNK1", "name": "Bank"},
        "memo": f"Fixture memo {record_id}",
        "payment_reference": f"PAYREF-{record_id}",
        "payment_method_line": {"id": 11, "name": "Manual", "journal_id": 9},
        "payment_method": {
            "id": 2,
            "code": "manual",
            "name": "Manual",
            "payment_type": payment_type,
        },
        "move_id": 1000 + record_id,
        "is_reconciled": True,
        "is_matched": False,
    }


def _document(
    record_id: int, move_type: str = "out_invoice", company_id: int = 7
) -> dict:
    return {
        "id": record_id,
        "name": f"INV/2025/{record_id:04d}",
        "move_type": move_type,
        "state": "posted",
        "payment_state": "partial",
        "company_id": company_id,
    }


def _detail(record_id: int = 20) -> dict:
    row = _row(record_id, "2025-01-25")
    row.update(
        journal_entry={
            "id": 1000 + record_id,
            "name": f"BNK/2025/{record_id:04d}",
            "state": "posted",
            "date": "2025-01-25",
        },
        invoice_ids=[_document(200)],
        reconciled_invoices=[_document(200)],
        reconciled_bills=[_document(300, "in_invoice")],
    )
    return row


class FakePort:
    def __init__(
        self,
        *,
        rows: list[dict] | None = None,
        payment: dict | None = None,
        company_visible: bool = True,
        module_installed: bool = True,
        access_allowed: bool | None = None,
    ) -> None:
        self.user_id = 42
        self.rows = copy.deepcopy(rows or [])
        self.payment = copy.deepcopy(payment)
        self.company_visible = company_visible
        self.module_installed = module_installed
        self.access_allowed = (
            company_visible and module_installed
            if access_allowed is None
            else access_allowed
        )
        self.search_calls: list[dict] = []
        self.get_calls: list[dict] = []

    def search_page(self, **kwargs) -> dict:
        self.search_calls.append(copy.deepcopy(kwargs))
        return self._page(rows=copy.deepcopy(self.rows[: kwargs["limit"]]))

    def get_payment(self, **kwargs) -> dict:
        self.get_calls.append(copy.deepcopy(kwargs))
        return self._page(payment=copy.deepcopy(self.payment))

    def _page(self, **payload) -> dict:
        return {
            "user_id": self.user_id,
            "company_visible": self.company_visible,
            "module_installed": self.module_installed,
            "access_allowed": self.access_allowed,
            **payload,
        }


def test_search_defaults_and_fetches_one_extra_row() -> None:
    row = _row(20, "2025-01-25")
    port = FakePort(rows=[row])

    result = search_payments(port, _request())

    assert result == {"items": [row], "has_more": False, "next_cursor": None}
    assert port.search_calls == [
        {
            "company_id": 7,
            "after": None,
            "limit": 101,
            "filters": EMPTY_FILTERS,
        }
    ]


def test_search_normalizes_filters_and_uses_descending_keyset_cursor() -> None:
    parameters = {
        "limit": 2,
        "date_from": "2025-01-01",
        "date_to": "2025-01-31",
        "states": ["paid", "draft"],
        "payment_types": ["outbound", "inbound"],
        "partner_types": ["supplier", "customer"],
        "journal_id": 9,
        "partner_id": 16,
        "currency_id": 6,
        "query": "Fixture",
    }
    rows = [
        _row(22, "2025-01-25"),
        _row(21, "2025-01-25"),
        _row(20, "2025-01-24"),
    ]
    port = FakePort(rows=rows)

    first = search_payments(port, _request(**parameters))

    assert [item["id"] for item in first["items"]] == [22, 21]
    assert first["has_more"] is True
    assert first["next_cursor"]
    expected_filters = {
        **EMPTY_FILTERS,
        "date_from": "2025-01-01",
        "date_to": "2025-01-31",
        "states": ["draft", "paid"],
        "payment_types": ["inbound", "outbound"],
        "partner_types": ["customer", "supplier"],
        "journal_id": 9,
        "partner_id": 16,
        "currency_id": 6,
        "query": "Fixture",
    }
    assert port.search_calls[0]["filters"] == expected_filters

    second_port = FakePort(rows=[rows[-1]])
    replay = dict(parameters, cursor=first["next_cursor"])
    second = search_payments(second_port, _request(**replay))
    assert second["items"] == [rows[-1]]
    assert second_port.search_calls[0]["after"] == ["2025-01-25", 21]


def test_cursor_binds_context_capability_and_every_filter() -> None:
    first = search_payments(
        FakePort(rows=[_row(22, "2025-01-25"), _row(21, "2025-01-24")]),
        _request(limit=1, states=["paid"], currency_id=6),
    )
    cursor = first["next_cursor"]
    assert cursor

    requests = [
        _request(limit=1, cursor=cursor, states=["draft"], currency_id=6),
        _request(limit=1, cursor=cursor, states=["paid"], currency_id=7),
        _request(limit=1, cursor=cursor, states=["paid"], currency_id=6),
    ]
    requests[-1]["context"]["company_id"] = 8
    for request in requests:
        port = FakePort()
        with pytest.raises(PaymentError) as caught:
            search_payments(port, request)
        assert caught.value.code == "invalid_cursor"
        assert port.search_calls == []


def test_cursor_is_bounded_for_long_valid_context_values() -> None:
    request = _request(limit=1)
    request["context"]["database"] = "d" * 3500
    request["context"]["user_login"] = "u" * 3500
    first = search_payments(
        FakePort(rows=[_row(22, "2025-01-25"), _row(21, "2025-01-24")]),
        request,
    )

    assert first["next_cursor"] is not None
    assert len(first["next_cursor"]) <= 4096

    replay = copy.deepcopy(request)
    replay["parameters"]["cursor"] = first["next_cursor"]
    port = FakePort(rows=[_row(20, "2025-01-23")])
    search_payments(port, replay)
    assert port.search_calls[0]["after"] == ["2025-01-25", 22]


@pytest.mark.parametrize(
    "mutate",
    [
        lambda raw: raw.replace('"version":1', '"version":1,"version":1'),
        lambda raw: raw.replace('"version":1', '"version":1.0'),
        lambda raw: raw.replace('"version":1', '"version":NaN'),
    ],
)
def test_cursor_rejects_duplicate_keys_floats_and_nonfinite_numbers(mutate) -> None:
    first = search_payments(
        FakePort(rows=[_row(22, "2025-01-25"), _row(21, "2025-01-24")]),
        _request(limit=1),
    )
    raw = base64.urlsafe_b64decode(first["next_cursor"] + "==").decode()
    forged = base64.urlsafe_b64encode(mutate(raw).encode()).decode().rstrip("=")

    with pytest.raises(PaymentError) as caught:
        search_payments(FakePort(), _request(limit=1, cursor=forged))
    assert caught.value.code == "invalid_cursor"


@pytest.mark.parametrize(
    "parameters",
    [
        {"unexpected": True},
        {"limit": True},
        {"limit": 1001},
        {"cursor": ""},
        {"date_from": "2025/01/01"},
        {"date_from": "2025-02-01", "date_to": "2025-01-01"},
        {"states": []},
        {"states": ["posted"]},
        {"states": ["paid", "paid"]},
        {"payment_types": ["receipt"]},
        {"partner_types": ["vendor"]},
        {"journal_id": True},
        {"partner_id": 0},
        {"currency_id": 1.0},
        {"query": " untrimmed"},
        {"query": "x" * 201},
    ],
)
def test_invalid_search_requests_fail_before_the_port(parameters: dict) -> None:
    port = FakePort()
    with pytest.raises(PaymentError) as caught:
        search_payments(port, _request(**parameters))
    assert caught.value.code == "invalid_request"
    assert caught.value.exit_code == 2
    assert port.search_calls == []


def test_request_validators_expose_the_closed_shapes() -> None:
    request_id, context, filters, limit, cursor = validate_payment_search_request(
        _request()
    )
    assert request_id == _request()["request_id"]
    assert context["company_id"] == 7
    assert filters == EMPTY_FILTERS
    assert limit == 100
    assert cursor is None
    assert validate_payment_get_request(_request(payment_id=20))[2] == 20


def test_request_schema_and_python_agree_on_query_whitespace_boundaries() -> None:
    registry = load_registry()
    for query in ("needle\n", "\nneedle", "needle ", " needle"):
        request = _request(query=query)
        with pytest.raises(InstanceValidationError):
            registry.validate_instance(
                "schemas/v1/payment.search.request.schema.json", request
            )
        with pytest.raises(PaymentError):
            validate_payment_search_request(request)

    for capability, validator, parameters in (
        ("payment.search", validate_payment_search_request, {}),
        ("payment.get", validate_payment_get_request, {"payment_id": 20}),
    ):
        for field in ("database", "user_login", "language", "timezone"):
            request = _request(**parameters)
            request["context"][field] = " \t\n"
            with pytest.raises(InstanceValidationError):
                registry.validate_instance(
                    f"schemas/v1/{capability}.request.schema.json", request
                )
            with pytest.raises(PaymentError):
                validator(request)

    for parameters in ({}, {"payment_id": True}, {"payment_id": 0}, {"payment_id": 1, "x": 2}):
        with pytest.raises(PaymentError):
            validate_payment_get_request(_request(**parameters))


@pytest.mark.parametrize(
    "mutation",
    [
        lambda row: row.update(extra=True),
        lambda row: row.update(id=True),
        lambda row: row.update(company_id=8),
        lambda row: row.update(date="2025/01/25"),
        lambda row: row.update(state="posted"),
        lambda row: row.update(payment_type="receipt"),
        lambda row: row.update(amount="-1"),
        lambda row: row.update(amount_signed="-50"),
        lambda row: row.update(amount_company_currency_signed="NaN"),
        lambda row: row["payment_method"].update(payment_type="outbound"),
        lambda row: row["payment_method_line"].update(journal_id=10),
        lambda row: row.update(is_reconciled=1),
        lambda row: row["journal"].update(code="TOOLONG"),
        lambda row: row["currency"].update(code="USDX"),
    ],
)
def test_invalid_or_impossible_search_rows_never_become_verified(mutation) -> None:
    row = _row(20, "2025-01-25")
    mutation(row)
    with pytest.raises(PaymentError) as caught:
        search_payments(FakePort(rows=[row]), _request())
    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8


def test_nullable_fields_and_zero_amount_force_balance_are_supported() -> None:
    row = _row(20, "2025-01-25", amount="0")
    row.update(
        name=None,
        partner=None,
        memo=None,
        payment_reference=None,
        move_id=None,
        amount_signed="0",
        amount_company_currency_signed="0.01",
        company_currency=_currency(37, "SGD"),
    )
    row["payment_method_line"].update(name=None, journal_id=None)

    assert search_payments(FakePort(rows=[row]), _request())["items"] == [row]

def test_legal_odoo_text_values_are_preserved_without_display_fallbacks() -> None:
    row = _row(20, "2025-01-25")
    row.update(name=" ", memo=" ", payment_reference=" ")
    row["partner"]["name"] = None
    row["journal"].update(code=" ", name=" ")
    row["currency"]["code"] = "   "
    row["company_currency"]["code"] = "   "
    row["payment_method_line"]["name"] = " "
    row["payment_method"].update(code=" ", name=" ")

    result = search_payments(FakePort(rows=[row]), _request())

    assert result["items"] == [row]


@pytest.mark.parametrize(
    ("payment_type", "company_signed"),
    (("inbound", "-360.50"), ("outbound", "360.50")),
)
def test_company_amount_is_not_derived_from_payment_amount_or_direction(
    payment_type: str, company_signed: str
) -> None:
    row = _row(20, "2025-01-25", amount="50")
    row.update(
        payment_type=payment_type,
        partner_type="customer" if payment_type == "inbound" else "supplier",
        amount_signed="50" if payment_type == "inbound" else "-50",
        amount_company_currency_signed=company_signed,
    )
    row["payment_method"]["payment_type"] = payment_type
    assert search_payments(FakePort(rows=[row]), _request())["items"] == [row]


@pytest.mark.parametrize(
    ("is_reconciled", "is_matched"), [(False, False), (False, True), (True, False), (True, True)]
)
def test_reconciled_and_bank_matched_are_independent_states(
    is_reconciled: bool, is_matched: bool
) -> None:
    row = _row(20, "2025-01-25")
    row.update(is_reconciled=is_reconciled, is_matched=is_matched)

    assert search_payments(FakePort(rows=[row]), _request())["items"] == [row]


def test_rows_must_match_every_locally_verifiable_normalized_filter() -> None:
    row = _row(20, "2025-01-25")
    valid = {
        "date_from": "2025-01-01",
        "date_to": "2025-01-31",
        "states": ["paid"],
        "payment_types": ["inbound"],
        "partner_types": ["customer"],
        "journal_id": 9,
        "partner_id": 16,
        "currency_id": 6,
        "query": "memo _0",
    }
    assert search_payments(FakePort(rows=[row]), _request(**valid))["items"]

    for key, value in {
        "date_from": "2025-01-26",
        "date_to": "2025-01-24",
        "states": ["draft"],
        "payment_types": ["outbound"],
        "partner_types": ["supplier"],
        "journal_id": 10,
        "partner_id": 17,
        "currency_id": 2,
    }.items():
        parameters = dict(valid)
        parameters[key] = value
        with pytest.raises(PaymentError) as caught:
            search_payments(FakePort(rows=[row]), _request(**parameters))
        assert caught.value.code == "failed_validation"


def test_query_result_is_not_rejected_by_a_python_approximation_of_odoo_ilike() -> None:
    row = _row(20, "2025-01-25")
    row["memo"] = "café"

    result = search_payments(FakePort(rows=[row]), _request(query="cafe"))

    assert result["items"] == [row]


@pytest.mark.parametrize(
    "rows",
    [
        [_row(20, "2025-01-25"), _row(21, "2025-01-26")],
        [_row(20, "2025-01-25"), _row(21, "2025-01-25")],
        [_row(20, "2025-01-25"), _row(20, "2025-01-24")],
    ],
)
def test_search_requires_unique_date_id_descending_rows(rows: list[dict]) -> None:
    with pytest.raises(PaymentError) as caught:
        search_payments(FakePort(rows=rows), _request())
    assert caught.value.code == "failed_validation"


def test_get_verifies_exact_payment_and_three_link_provenances() -> None:
    payment = _detail()
    port = FakePort(payment=payment)

    assert get_payment(port, _request(payment_id=20)) == payment
    assert port.get_calls == [{"company_id": 7, "payment_id": 20}]


@pytest.mark.parametrize(
    "mutation",
    [
        lambda row: row.update(id=21),
        lambda row: row["journal_entry"].update(id=999),
        lambda row: row.update(journal_entry=None),
        lambda row: row["invoice_ids"].append(copy.deepcopy(row["invoice_ids"][0])),
        lambda row: row.update(invoice_ids=[_document(201), _document(200)]),
        lambda row: row.update(reconciled_invoices=[_document(200, "in_invoice")]),
        lambda row: row.update(reconciled_bills=[_document(300, "out_invoice")]),
        lambda row: row["reconciled_bills"][0].update(payment_state="settled"),
        lambda row: row["invoice_ids"][0].update(company_id=True),
    ],
)
def test_get_rejects_wrong_identity_order_shape_or_document_provenance(mutation) -> None:
    payment = _detail()
    mutation(payment)
    with pytest.raises(PaymentError) as caught:
        get_payment(FakePort(payment=payment), _request(payment_id=20))
    assert caught.value.code == "failed_validation"


def test_get_accepts_draft_without_a_move_and_nullable_names() -> None:
    payment = _detail()
    payment.update(
        name=None,
        state="draft",
        move_id=None,
        journal_entry=None,
        invoice_ids=[],
        reconciled_invoices=[],
        reconciled_bills=[],
    )
    payment["partner"] = None
    payment["memo"] = None
    payment["payment_reference"] = None

    assert get_payment(FakePort(payment=payment), _request(payment_id=20)) == payment


@pytest.mark.parametrize("move_type", ["out_receipt", "in_receipt"])
def test_linked_receipts_are_accounting_documents(move_type: str) -> None:
    payment = _detail()
    payment["invoice_ids"] = [_document(200, move_type)]

    assert get_payment(FakePort(payment=payment), _request(payment_id=20))[
        "invoice_ids"
    ] == payment["invoice_ids"]


def test_reconciled_receipts_retain_sale_and_purchase_provenance() -> None:
    payment = _detail()
    payment["reconciled_invoices"] = [_document(200, "out_receipt")]
    payment["reconciled_bills"] = [_document(300, "in_receipt")]

    result = get_payment(FakePort(payment=payment), _request(payment_id=20))

    assert result["reconciled_invoices"][0]["move_type"] == "out_receipt"
    assert result["reconciled_bills"][0]["move_type"] == "in_receipt"


def test_linked_documents_preserve_their_own_company_provenance() -> None:
    payment = _detail()
    payment["invoice_ids"] = [_document(200, company_id=8)]
    payment["reconciled_invoices"] = [_document(200, company_id=8)]

    result = get_payment(FakePort(payment=payment), _request(payment_id=20))

    assert result["invoice_ids"][0]["company_id"] == 8
    assert result["reconciled_invoices"][0]["company_id"] == 8


def test_direct_only_links_are_not_promoted_to_reconciliation() -> None:
    payment = _detail()
    payment["reconciled_invoices"] = []
    payment["reconciled_bills"] = []

    result = get_payment(FakePort(payment=payment), _request(payment_id=20))

    assert result["invoice_ids"]
    assert result["reconciled_invoices"] == []
    assert result["reconciled_bills"] == []


def test_missing_payment_is_explicit() -> None:
    with pytest.raises(PaymentError) as caught:
        get_payment(FakePort(payment=None), _request(payment_id=20))
    assert caught.value.code == "record_not_found"
    assert caught.value.exit_code == 4


@pytest.mark.parametrize(
    ("port", "code"),
    [
        (FakePort(company_visible=False), "company_unavailable"),
        (FakePort(module_installed=False), "uninstalled"),
        (FakePort(access_allowed=False), "unauthorized"),
    ],
)
def test_runtime_availability_failures_are_typed(port: FakePort, code: str) -> None:
    with pytest.raises(PaymentError) as caught:
        search_payments(port, _request())
    assert caught.value.code == code


def test_malformed_or_contradictory_pages_are_failed_validation() -> None:
    with pytest.raises(PaymentError) as caught:
        search_payments(
            FakePort(company_visible=False, access_allowed=True), _request()
        )
    assert caught.value.code == "failed_validation"

    class Broken(FakePort):
        def search_page(self, **kwargs) -> dict:
            raise ValueError("bad page")

    with pytest.raises(PaymentError) as caught:
        search_payments(Broken(), _request())
    assert caught.value.code == "failed_validation"


def _success_response(capability: str, data: dict) -> dict:
    ids = [item["id"] for item in data.get("items", [])] if isinstance(data, dict) else []
    return {
        "schema_version": "v1",
        "request_id": _request()["request_id"],
        "success": True,
        "capability": capability,
        "status": "verified",
        "data": data,
        "warnings": [],
        "error": None,
        "odoo": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_id": 42,
            "model": "account.payment",
            "record_ids": ids or [data["id"]],
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": None,
            "verification": {"result": "passed"},
        },
    }


@pytest.mark.parametrize(
    ("capability", "request_document", "data"),
    [
        (
            "payment.search",
            _request(
                limit=100,
                cursor=None,
                date_from=None,
                date_to=None,
                states=["paid"],
                payment_types=["inbound"],
                partner_types=["customer"],
                journal_id=None,
                partner_id=None,
                currency_id=None,
                query=None,
            ),
            {"items": [_row(20, "2025-01-25")], "has_more": False, "next_cursor": None},
        ),
        ("payment.get", _request(payment_id=20), _detail()),
    ],
)
def test_specialized_schemas_accept_success_and_error_documents(
    capability: str, request_document: dict, data: dict
) -> None:
    schema_dir = Path(__file__).parents[2] / "schemas" / "v1"
    assert (schema_dir / f"{capability}.request.schema.json").is_file()
    assert (schema_dir / f"{capability}.response.schema.json").is_file()
    registry = load_registry()
    registry.validate_instance(
        f"schemas/v1/{capability}.request.schema.json", request_document
    )
    response = _success_response(capability, data)
    registry.validate_instance(f"schemas/v1/{capability}.response.schema.json", response)
    response.update(
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
    registry.validate_instance(f"schemas/v1/{capability}.response.schema.json", response)


def test_schema_and_python_reject_decimal_with_trailing_newline() -> None:
    row = _row(20, "2025-01-25")
    row["amount"] += "\n"
    response = _success_response(
        "payment.search",
        {"items": [row], "has_more": False, "next_cursor": None},
    )
    with pytest.raises(InstanceValidationError):
        load_registry().validate_instance(
            "schemas/v1/payment.search.response.schema.json", response
        )
    with pytest.raises(PaymentError):
        search_payments(FakePort(rows=[row]), _request())


def test_schema_accepts_legal_odoo_text_and_nullable_partner_name() -> None:
    row = _row(20, "2025-01-25", amount="0")
    row.update(
        state="draft",
        name=" ",
        move_id=None,
        partner={"id": 16, "name": None},
        memo=" ",
        payment_reference=" ",
        amount_signed="0",
        amount_company_currency_signed="0",
    )
    row["journal"].update(code=" ", name=" ")
    row["currency"]["code"] = "   "
    row["company_currency"]["code"] = "   "
    response = _success_response(
        "payment.search",
        {"items": [row], "has_more": False, "next_cursor": None},
    )

    load_registry().validate_instance(
        "schemas/v1/payment.search.response.schema.json", response
    )


def test_money_examples_lock_direction_without_binary_floats() -> None:
    inbound = _row(20, "2025-01-25", amount="0.10")
    outbound = _row(19, "2025-01-24", payment_type="outbound", amount="0.10")
    result = search_payments(FakePort(rows=[inbound, outbound]), _request())
    assert Decimal(result["items"][0]["amount_signed"]) == Decimal("0.10")
    assert Decimal(result["items"][1]["amount_signed"]) == Decimal("-0.10")
