"""Live invoice reads against accounting fixture v1 only.

This covers the two fixture documents, one partial customer payment, limit-one
cursor traversal, and record non-disclosure in both dedicated databases and
companies.  It does not claim live coverage for credit notes, draft/cancelled
documents, full or multiple payments, exchange differences, write-offs,
products, discounts, section/note lines, or per-record ACL hiding.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import uuid
from decimal import Decimal
from pathlib import Path

import pytest

from odoo_accounting_cli_v4.registry import load_registry


_CONFIG_ENV = "ODOO_ACCOUNTING_CLI_V4_CONFIG"
_ALIASES = ("v4-dev", "v4-e2e")
_COMPANIES = (1, 2)
_CODE = {1: "CN", 2: "SG"}
_CURRENCY = {1: "CNY", 2: "SGD"}
_INVOICE = {
    1: {"untaxed": "100", "tax": "13", "total": "113", "residual": "63"},
    2: {"untaxed": "100", "tax": "9", "total": "109", "residual": "59"},
}
_BILL = {
    1: {"untaxed": "100", "tax": "13", "total": "113", "residual": "113"},
    2: {"untaxed": "103.67", "tax": "9.33", "total": "113", "residual": "113"},
}
_MONEY = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")


def _invoke(
    alias: str,
    company_id: int,
    capability_id: str,
    parameters: dict,
    *,
    case: str,
    expected_exit: int = 0,
) -> dict:
    project_root = Path(__file__).resolve().parents[2]
    request_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"odacv4:{alias}:{company_id}:{capability_id}:invoice-live:{case}",
        )
    )
    request = {
        "schema_version": "v1",
        "request_id": request_id,
        "context": {
            "database": alias,
            "company_id": company_id,
            "user_login": os.environ.get(
                "ODACV4_LIVE_USER_LOGIN", "odacv4_g5_accountant"
            ),
            "language": os.environ.get("ODACV4_LIVE_LANGUAGE", "en_US"),
            "timezone": os.environ.get(
                "ODACV4_LIVE_TIMEZONE", "Asia/Shanghai"
            ),
        },
        "parameters": parameters,
    }
    registry = load_registry()
    registry.validate_instance(
        f"schemas/v1/{capability_id}.request.schema.json", request
    )

    environment = os.environ.copy()
    environment[_CONFIG_ENV] = os.environ[_CONFIG_ENV]
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = os.pathsep.join(
        part
        for part in (str(project_root / "src"), environment.get("PYTHONPATH"))
        if part
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "odoo_accounting_cli_v4",
            "read",
            capability_id,
            "--request",
            "-",
        ],
        cwd=project_root,
        env=environment,
        input=json.dumps(request),
        text=True,
        capture_output=True,
        check=False,
        timeout=240,
    )

    assert completed.returncode == expected_exit, completed.stdout
    assert completed.stderr == ""
    assert len(completed.stdout.splitlines()) == 1
    document = json.loads(completed.stdout)
    assert document["schema_version"] == "v1"
    assert document["capability"] == capability_id
    assert document["request_id"] == request_id
    registry.validate_instance(
        f"schemas/v1/{capability_id}.response.schema.json", document
    )
    return document


def _assert_success_metadata(
    document: dict,
    *,
    alias: str,
    company_id: int,
    record_ids: list[int],
) -> None:
    assert document["success"] is True
    assert document["status"] == "verified"
    assert document["error"] is None
    assert document["warnings"] == []
    assert document["odoo"]["database"] == alias
    assert document["odoo"]["company_id"] == company_id
    assert isinstance(document["odoo"]["user_id"], int)
    assert document["odoo"]["user_id"] > 0
    assert document["odoo"]["model"] == "account.move"
    assert document["odoo"]["record_ids"] == record_ids


def _assert_money(value: str, expected: str | None = None) -> None:
    assert isinstance(value, str) and _MONEY.fullmatch(value)
    if expected is not None:
        assert Decimal(value) == Decimal(expected)


def _assert_header(
    item: dict,
    *,
    company_id: int,
    move_type: str,
    expected: dict[str, str],
) -> None:
    code = _CODE[company_id]
    is_invoice = move_type == "out_invoice"
    assert item["move_type"] == move_type
    assert item["state"] == "posted"
    assert item["date"] == ("2025-01-20" if is_invoice else "2025-01-21")
    assert item["invoice_date"] == item["date"]
    assert item["invoice_date_due"] == (
        "2025-02-20" if is_invoice else "2025-02-21"
    )
    assert item["ref"] == (
        f"ODACV4-FX1-{code}-INVOICE-TAX-EXCLUDED"
        if is_invoice
        else f"ODACV4-FX1-{code}-BILL-TAX-INCLUDED"
    )
    assert item["company_id"] == company_id
    assert item["currency"]["code"] == _CURRENCY[company_id]
    assert item["partner"] is not None
    assert item["journal"]["code"]
    assert item["name"]
    for field in ("amount_untaxed", "amount_tax", "amount_total", "amount_residual"):
        key = field.removeprefix("amount_")
        _assert_money(item[field], expected[key])
    assert item["payment_state"] == ("partial" if is_invoice else "not_paid")


def _assert_not_found(document: dict, *, alias: str, company_id: int) -> None:
    assert document["success"] is False
    assert document["status"] == "unavailable"
    assert document["data"] is None
    assert document["error"]["code"] == "record_not_found"
    assert document["error"]["retryable"] is False
    assert document["odoo"]["database"] == alias
    assert document["odoo"]["company_id"] == company_id
    assert document["odoo"]["record_ids"] == []


@pytest.mark.integration
@pytest.mark.parametrize("alias", _ALIASES)
@pytest.mark.parametrize("company_id", _COMPANIES)
def test_invoice_search_get_and_payment_status_use_the_real_read_only_bridge(
    alias: str, company_id: int
) -> None:
    if not os.environ.get(_CONFIG_ENV):
        pytest.skip(f"{_CONFIG_ENV} is not configured")

    first = _invoke(
        alias,
        company_id,
        "invoice.search",
        {"limit": 1, "cursor": None},
        case="page-1",
    )
    first_items = first["data"]["items"]
    assert len(first_items) == 1
    bill = first_items[0]
    _assert_success_metadata(
        first, alias=alias, company_id=company_id, record_ids=[bill["id"]]
    )
    assert first["data"]["has_more"] is True
    assert isinstance(first["data"]["next_cursor"], str)
    assert first["data"]["next_cursor"]
    _assert_header(
        bill,
        company_id=company_id,
        move_type="in_invoice",
        expected=_BILL[company_id],
    )

    second = _invoke(
        alias,
        company_id,
        "invoice.search",
        {"limit": 1, "cursor": first["data"]["next_cursor"]},
        case="page-2",
    )
    second_items = second["data"]["items"]
    assert len(second_items) == 1
    invoice = second_items[0]
    _assert_success_metadata(
        second, alias=alias, company_id=company_id, record_ids=[invoice["id"]]
    )
    assert second["data"]["has_more"] is False
    assert second["data"]["next_cursor"] is None
    _assert_header(
        invoice,
        company_id=company_id,
        move_type="out_invoice",
        expected=_INVOICE[company_id],
    )
    assert [(bill["date"], bill["id"]), (invoice["date"], invoice["id"])] == sorted(
        [(bill["date"], bill["id"]), (invoice["date"], invoice["id"])],
        reverse=True,
    )

    fetched_invoice = _invoke(
        alias,
        company_id,
        "invoice.get",
        {"invoice_id": invoice["id"]},
        case="get-invoice",
    )
    _assert_success_metadata(
        fetched_invoice,
        alias=alias,
        company_id=company_id,
        record_ids=[invoice["id"]],
    )
    invoice_data = fetched_invoice["data"]
    for key, value in invoice.items():
        assert invoice_data[key] == value
    assert len(invoice_data["lines"]) == 1
    invoice_line = invoice_data["lines"][0]
    assert invoice_line["display_type"] == "product"
    assert invoice_line["name"] == "ODACV4 FX1 tax-exclusive service"
    assert invoice_line["product"] is None
    assert invoice_line["account"] is not None
    _assert_money(invoice_line["quantity"], "1")
    _assert_money(invoice_line["price_unit"], "100")
    _assert_money(invoice_line["discount"], "0")
    _assert_money(invoice_line["price_subtotal"], "100")
    _assert_money(invoice_line["price_total"], _INVOICE[company_id]["total"])
    assert len(invoice_line["taxes"]) == 1
    invoice_tax = invoice_line["taxes"][0]
    _assert_money(invoice_tax["amount"], _INVOICE[company_id]["tax"])
    assert invoice_tax["price_include"] is False

    fetched_bill = _invoke(
        alias,
        company_id,
        "invoice.get",
        {"invoice_id": bill["id"]},
        case="get-bill",
    )
    _assert_success_metadata(
        fetched_bill,
        alias=alias,
        company_id=company_id,
        record_ids=[bill["id"]],
    )
    bill_data = fetched_bill["data"]
    for key, value in bill.items():
        assert bill_data[key] == value
    assert len(bill_data["lines"]) == 1
    bill_line = bill_data["lines"][0]
    assert bill_line["display_type"] == "product"
    assert bill_line["name"] == "ODACV4 FX1 tax-inclusive supplies"
    assert bill_line["product"] is None
    assert bill_line["account"] is not None
    _assert_money(bill_line["quantity"], "1")
    _assert_money(bill_line["price_unit"], "113")
    _assert_money(bill_line["price_subtotal"], _BILL[company_id]["untaxed"])
    _assert_money(bill_line["price_total"], "113")
    assert len(bill_line["taxes"]) == 1
    bill_tax = bill_line["taxes"][0]
    _assert_money(bill_tax["amount"], _INVOICE[company_id]["tax"])
    assert bill_tax["price_include"] is True

    invoice_status_document = _invoke(
        alias,
        company_id,
        "invoice.payment_status.inspect",
        {"invoice_id": invoice["id"]},
        case="invoice-status",
    )
    _assert_success_metadata(
        invoice_status_document,
        alias=alias,
        company_id=company_id,
        record_ids=[invoice["id"]],
    )
    invoice_status = invoice_status_document["data"]
    assert invoice_status["payment_state"] == "partial"
    assert invoice_status["currency"]["code"] == _CURRENCY[company_id]
    assert invoice_status["company_currency"] == invoice_status["currency"]
    _assert_money(invoice_status["amount_total"], _INVOICE[company_id]["total"])
    _assert_money(invoice_status["amount_residual"], _INVOICE[company_id]["residual"])
    assert len(invoice_status["receivable_payable_lines"]) == 1
    term_line = invoice_status["receivable_payable_lines"][0]
    assert term_line["account"]["account_type"] == "asset_receivable"
    _assert_money(term_line["balance"], _INVOICE[company_id]["total"])
    _assert_money(term_line["amount_currency"], _INVOICE[company_id]["total"])
    _assert_money(term_line["amount_residual"], _INVOICE[company_id]["residual"])
    _assert_money(
        term_line["amount_residual_currency"], _INVOICE[company_id]["residual"]
    )
    assert term_line["reconciled"] is False
    assert len(invoice_status["reconciliations"]) == 1
    reconciliation = invoice_status["reconciliations"][0]
    assert reconciliation["date"] == "2025-01-25"
    _assert_money(reconciliation["amount"], "50")
    _assert_money(reconciliation["company_amount"], "50")
    assert reconciliation["currency"] == invoice_status["currency"]
    assert reconciliation["company_currency"] == invoice_status["company_currency"]
    assert reconciliation["counterpart_move"]["move_type"] == "entry"
    assert reconciliation["counterpart_move"]["state"] == "posted"
    assert reconciliation["exchange_move_id"] is None
    assert len(invoice_status["payments"]) == 1
    payment = invoice_status["payments"][0]
    assert payment["id"] == reconciliation["payment_id"]
    assert payment["state"] == "in_process"
    assert payment["date"] == "2025-01-25"
    assert payment["payment_type"] == "inbound"
    assert payment["partner_type"] == "customer"
    _assert_money(payment["amount"], "50")
    assert payment["currency"] == invoice_status["currency"]
    assert payment["payment_method"]["code"] == "manual"
    assert payment["is_reconciled"] is True
    assert payment["is_matched"] is False

    bill_status_document = _invoke(
        alias,
        company_id,
        "invoice.payment_status.inspect",
        {"invoice_id": bill["id"]},
        case="bill-status",
    )
    _assert_success_metadata(
        bill_status_document,
        alias=alias,
        company_id=company_id,
        record_ids=[bill["id"]],
    )
    bill_status = bill_status_document["data"]
    assert bill_status["payment_state"] == "not_paid"
    _assert_money(bill_status["amount_total"], "113")
    _assert_money(bill_status["amount_residual"], "113")
    assert len(bill_status["receivable_payable_lines"]) == 1
    assert (
        bill_status["receivable_payable_lines"][0]["account"]["account_type"]
        == "liability_payable"
    )
    assert bill_status["reconciliations"] == []
    assert bill_status["payments"] == []

    other_company = 1 if company_id == 2 else 2
    other_ref = f"ODACV4-FX1-{_CODE[other_company]}-INVOICE-TAX-EXCLUDED"
    other_search = _invoke(
        alias,
        other_company,
        "invoice.search",
        {"limit": 10, "cursor": None, "query": other_ref},
        case=f"discover-cross-for-{company_id}",
    )
    assert len(other_search["data"]["items"]) == 1
    cross_company_id = other_search["data"]["items"][0]["id"]

    for capability_id in ("invoice.get", "invoice.payment_status.inspect"):
        cross_company = _invoke(
            alias,
            company_id,
            capability_id,
            {"invoice_id": cross_company_id},
            case=f"{capability_id}-cross-company",
            expected_exit=4,
        )
        absent = _invoke(
            alias,
            company_id,
            capability_id,
            {"invoice_id": 2_147_483_647},
            case=f"{capability_id}-absent",
            expected_exit=4,
        )
        _assert_not_found(cross_company, alias=alias, company_id=company_id)
        _assert_not_found(absent, alias=alias, company_id=company_id)
        assert cross_company["error"] == absent["error"]
