"""Live payment reads against accounting fixture v1 only.

Fixture v1 contains exactly one inbound, customer, in-process payment per
company.  These tests prove company isolation, all available filters, detail
provenance, and decimal/currency invariants.  They intentionally do not claim
live cursor traversal, outbound/supplier behavior, other payment states,
detached method lines, cross-currency payments, or multi-document
reconciliation; those remain contract/unit coverage until a richer versioned
fixture exists.
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
_EXPECTED_PAYMENT_IDS = {
    "v4-dev": {1: 5, 2: 6},
    "v4-e2e": {1: 1, 2: 2},
}
_MONEY = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_COMMON_KEYS = {
    "id",
    "name",
    "date",
    "state",
    "payment_type",
    "partner_type",
    "amount",
    "amount_signed",
    "amount_company_currency_signed",
    "currency",
    "company_currency",
    "company_id",
    "partner",
    "journal",
    "memo",
    "payment_reference",
    "payment_method_line",
    "payment_method",
    "move_id",
    "is_reconciled",
    "is_matched",
}


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
            f"odacv4:{alias}:{company_id}:{capability_id}:payment-live:{case}",
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
        input=json.dumps(request, sort_keys=True, separators=(",", ":")),
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


def _assert_metadata(
    document: dict,
    *,
    alias: str,
    company_id: int,
    success: bool,
    record_ids: list[int],
) -> None:
    assert document["success"] is success
    assert document["status"] == ("verified" if success else "unavailable")
    assert document["odoo"]["database"] == alias
    assert document["odoo"]["company_id"] == company_id
    assert document["odoo"]["model"] == "account.payment"
    assert document["odoo"]["record_ids"] == record_ids
    if success:
        assert document["error"] is None
        assert document["warnings"] == []
        assert document["odoo"]["user_id"] == 5


def _money(value: str, expected: str | None = None) -> Decimal:
    assert isinstance(value, str) and _MONEY.fullmatch(value)
    result = Decimal(value)
    assert result.is_finite()
    if expected is not None:
        assert result == Decimal(expected)
    return result


def _assert_common(payment: dict, *, alias: str, company_id: int) -> None:
    assert set(payment) == _COMMON_KEYS
    assert payment["id"] == _EXPECTED_PAYMENT_IDS[alias][company_id]
    assert payment["date"] == "2025-01-25"
    assert payment["state"] == "in_process"
    assert payment["payment_type"] == "inbound"
    assert payment["partner_type"] == "customer"
    assert payment["company_id"] == company_id
    assert payment["currency"]["code"] == _CURRENCY[company_id]
    assert payment["company_currency"] == payment["currency"]
    assert payment["partner"] is not None
    assert payment["partner"]["name"]
    assert payment["journal"]["code"] == "BNK1"
    assert payment["journal"]["name"] == "Bank"
    assert payment["memo"] == "INV/2025/00001"
    assert payment["payment_reference"] is None
    assert payment["payment_method_line"]["id"] > 0
    assert payment["payment_method_line"]["name"]
    assert payment["payment_method_line"]["journal_id"] == payment["journal"]["id"]
    assert payment["payment_method"] == {
        "id": 1,
        "code": "manual",
        "name": "Manual Payment",
        "payment_type": "inbound",
    }
    assert isinstance(payment["move_id"], int) and payment["move_id"] > 0
    assert payment["is_reconciled"] is True
    assert payment["is_matched"] is False
    amount = _money(payment["amount"], "50")
    assert amount >= 0
    assert _money(payment["amount_signed"]) == amount
    assert _money(payment["amount_company_currency_signed"]) == amount


def _assert_document(document: dict, *, company_id: int) -> None:
    assert set(document) == {
        "id", "name", "move_type", "state", "payment_state", "company_id"
    }
    assert isinstance(document["id"], int) and document["id"] > 0
    assert document["name"]
    assert document["move_type"] == "out_invoice"
    assert document["company_id"] == company_id
    assert document["state"] == "posted"
    assert document["payment_state"] == "partial"


@pytest.mark.integration
@pytest.mark.parametrize("alias", _ALIASES)
@pytest.mark.parametrize("company_id", _COMPANIES)
def test_payment_search_get_and_company_isolation_use_real_read_only_bridge(
    alias: str,
    company_id: int,
) -> None:
    if not os.environ.get(_CONFIG_ENV):
        pytest.skip(f"{_CONFIG_ENV} is not configured")

    basic = _invoke(
        alias,
        company_id,
        "payment.search",
        {"limit": 1, "cursor": None},
        case="terminal-limit-one",
    )
    payment = basic["data"]["items"][0]
    _assert_metadata(
        basic,
        alias=alias,
        company_id=company_id,
        success=True,
        record_ids=[payment["id"]],
    )
    assert basic["data"]["has_more"] is False
    assert basic["data"]["next_cursor"] is None
    _assert_common(payment, alias=alias, company_id=company_id)

    filtered = _invoke(
        alias,
        company_id,
        "payment.search",
        {
            "limit": 1,
            "cursor": None,
            "date_from": payment["date"],
            "date_to": payment["date"],
            "states": [payment["state"]],
            "payment_types": [payment["payment_type"]],
            "partner_types": [payment["partner_type"]],
            "journal_id": payment["journal"]["id"],
            "partner_id": payment["partner"]["id"],
            "currency_id": payment["currency"]["id"],
            "query": payment["memo"],
        },
        case="all-filters",
    )
    assert filtered["data"] == basic["data"]

    detail = _invoke(
        alias,
        company_id,
        "payment.get",
        {"payment_id": payment["id"]},
        case="get",
    )
    _assert_metadata(
        detail,
        alias=alias,
        company_id=company_id,
        success=True,
        record_ids=[payment["id"]],
    )
    assert set(detail["data"]) == _COMMON_KEYS | {
        "journal_entry",
        "invoice_ids",
        "reconciled_invoices",
        "reconciled_bills",
    }
    for key in _COMMON_KEYS:
        assert detail["data"][key] == payment[key]
    entry = detail["data"]["journal_entry"]
    assert entry == {
        "id": payment["move_id"],
        "name": payment["name"],
        "state": "posted",
        "date": payment["date"],
    }
    assert len(detail["data"]["invoice_ids"]) == 1
    assert len(detail["data"]["reconciled_invoices"]) == 1
    assert detail["data"]["reconciled_bills"] == []
    _assert_document(detail["data"]["invoice_ids"][0], company_id=company_id)
    _assert_document(
        detail["data"]["reconciled_invoices"][0], company_id=company_id
    )
    assert detail["data"]["invoice_ids"] == detail["data"]["reconciled_invoices"]

    other_company = 1 if company_id == 2 else 2
    cross_id = _EXPECTED_PAYMENT_IDS[alias][other_company]
    cross = _invoke(
        alias,
        company_id,
        "payment.get",
        {"payment_id": cross_id},
        case="cross-company",
        expected_exit=4,
    )
    absent = _invoke(
        alias,
        company_id,
        "payment.get",
        {"payment_id": 2_147_483_647},
        case="absent",
        expected_exit=4,
    )
    for document in (cross, absent):
        _assert_metadata(
            document,
            alias=alias,
            company_id=company_id,
            success=False,
            record_ids=[],
        )
        assert document["data"] is None
        assert document["error"]["code"] == "record_not_found"
        assert document["error"]["retryable"] is False
    assert cross["error"] == absent["error"]
