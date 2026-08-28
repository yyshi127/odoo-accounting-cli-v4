from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

import pytest

from odoo_accounting_cli_v4.capabilities.core_writes import (
    CORE_WRITE_CAPABILITY_IDS,
    CoreWriteError,
    execute_core_write,
    validate_core_write_request,
)

CAPABILITY_IDS = (
    "purchase.order.bill.create",
    "purchase_bill.match",
    "purchase_bill.lines.unmatch",
    "payment_term.create",
    "payment_term.update",
    "payment_term.lines.replace",
    "payment_term.archive",
    "payment_term.restore",
    "period.accrual.generate",
)
PARAMETERS: dict[str, dict[str, Any]] = {
    "purchase.order.bill.create": {"order_id": 101},
    "purchase_bill.match": {
        "bill_id": 201,
        "pairs": [
            {"bill_line_id": 12, "purchase_line_id": 22},
            {"bill_line_id": 11, "purchase_line_id": 21},
        ],
    },
    "purchase_bill.lines.unmatch": {"bill_id": 201, "bill_line_ids": [12, 11]},
    "payment_term.create": {
        "name": "30 Days",
        "company_id": 7,
        "sequence": 10,
        "note": None,
        "display_on_invoice": True,
        "early_discount": True,
        "discount_percentage": "2",
        "discount_days": 10,
        "early_pay_discount_computation": "included",
        "lines": [
            {
                "value": "percent",
                "value_amount": "100",
                "delay_type": "days_after",
                "nb_days": 30,
            }
        ],
    },
    "payment_term.update": {
        "payment_term_id": 301,
        "sequence": 20,
        "note": "Updated",
    },
    "payment_term.lines.replace": {
        "payment_term_id": 301,
        "lines": [
            {
                "value": "percent",
                "value_amount": "50",
                "delay_type": "days_after",
                "nb_days": 15,
            },
            {
                "value": "percent",
                "value_amount": "50",
                "delay_type": "days_end_of_month_on_the",
                "nb_days": 30,
                "days_next_month": 10,
            },
        ],
    },
    "payment_term.archive": {"payment_term_id": 301},
    "payment_term.restore": {"payment_term_id": 301},
    "period.accrual.generate": {
        "source_model": "purchase.order",
        "order_ids": [102, 101],
        "date": "2026-08-28",
        "reversal_date": "2026-08-29",
        "journal_id": 8,
        "accrual_account_id": 9,
    },
}


def _request(parameters: dict[str, Any]) -> dict[str, Any]:
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
        "parameters": deepcopy(parameters),
    }


def _key(capability_id: str, parameters: dict[str, Any]) -> str:
    if capability_id == "purchase.order.bill.create":
        return f"{capability_id}:{parameters['order_id']}"
    if capability_id in {"payment_term.create", "period.accrual.generate"}:
        return "caller-safe-create-key-001"
    if capability_id in {"payment_term.archive", "payment_term.restore"}:
        return f"{capability_id}:{parameters['payment_term_id']}"
    if capability_id in {"payment_term.update", "payment_term.lines.replace"}:
        target = (
            parameters["lines"]
            if capability_id == "payment_term.lines.replace"
            else {
                key: value
                for key, value in parameters.items()
                if key != "payment_term_id"
            }
        )
        record_id = parameters["payment_term_id"]
    else:
        target = parameters.get("pairs", parameters.get("bill_line_ids"))
        record_id = parameters["bill_id"]
    digest = hashlib.sha256(
        json.dumps(
            target, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()[:32]
    return f"{capability_id}:{record_id}:{digest}"


def _result(capability_id: str) -> dict[str, Any]:
    if capability_id.startswith("payment_term."):
        parameters = PARAMETERS[capability_id]
        return {
            "model": "account.payment.term",
            "id": 902
            if capability_id == "payment_term.create"
            else parameters["payment_term_id"],
            "name": "30 Days",
            "state": "archived"
            if capability_id == "payment_term.archive"
            else "active",
            "company_id": 7,
            "move_type": None,
            "source_id": None,
            "line_ids": [
                601 + index for index, _ in enumerate(parameters.get("lines", []))
            ],
            "partial_reconcile_ids": [],
            "full_reconcile_id": None,
            "reconciled": False,
        }
    if capability_id == "period.accrual.generate":
        return {
            "model": "account.move",
            "id": 903,
            "name": "Accrued Expense entry as of 08/28/2026",
            "state": "posted",
            "company_id": 7,
            "move_type": "entry",
            "source_id": 904,
            "line_ids": [701, 702],
            "partial_reconcile_ids": [],
            "full_reconcile_id": None,
            "reconciled": False,
        }
    result = {
        "model": "account.move",
        "id": 901
        if capability_id == "purchase.order.bill.create"
        else PARAMETERS[capability_id]["bill_id"],
        "name": None,
        "state": "draft",
        "company_id": 7,
        "move_type": "in_invoice",
        "source_id": 101 if capability_id == "purchase.order.bill.create" else None,
        "line_ids": [501]
        if capability_id == "purchase.order.bill.create"
        else [11, 12],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }
    return result


class Port:
    user_id = 42

    def __init__(
        self, capability_id: str, result: dict[str, Any] | None = None
    ) -> None:
        self.capability_id = capability_id
        self.result = result or _result(capability_id)
        self.calls: list[dict[str, Any]] = []

    def execute(self, **payload: Any) -> dict[str, Any]:
        self.calls.append(deepcopy(payload))
        return {
            "user_id": self.user_id,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "idempotent_replay": False,
            "result": deepcopy(self.result),
        }


def test_capability_set_is_registered() -> None:
    assert set(CAPABILITY_IDS) <= CORE_WRITE_CAPABILITY_IDS


@pytest.mark.parametrize("capability_id", CAPABILITY_IDS)
def test_fixed_contract_executes_through_shared_port(capability_id: str) -> None:
    _, _, normalized = validate_core_write_request(
        capability_id, _request(PARAMETERS[capability_id])
    )
    port = Port(capability_id)
    data = execute_core_write(
        port,
        capability_id,
        _request(PARAMETERS[capability_id]),
        _key(capability_id, normalized),
        capability_id,
    )
    assert data == {"idempotent_replay": False, "result": _result(capability_id)}
    assert port.calls[0]["parameters"] == normalized


def test_match_and_unmatch_normalize_unordered_ids() -> None:
    _, _, matched = validate_core_write_request(
        "purchase_bill.match", _request(PARAMETERS["purchase_bill.match"])
    )
    _, _, unmatched = validate_core_write_request(
        "purchase_bill.lines.unmatch",
        _request(PARAMETERS["purchase_bill.lines.unmatch"]),
    )
    assert [pair["bill_line_id"] for pair in matched["pairs"]] == [11, 12]
    assert unmatched["bill_line_ids"] == [11, 12]
    _, _, accrual = validate_core_write_request(
        "period.accrual.generate", _request(PARAMETERS["period.accrual.generate"])
    )
    assert accrual["order_ids"] == [101, 102]


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    (
        ("purchase.order.bill.create", {"order_id": 0}),
        ("purchase_bill.match", {"bill_id": 1, "pairs": []}),
        (
            "purchase_bill.match",
            {
                "bill_id": 1,
                "pairs": [
                    {"bill_line_id": 2, "purchase_line_id": 3},
                    {"bill_line_id": 2, "purchase_line_id": 4},
                ],
            },
        ),
        ("purchase_bill.lines.unmatch", {"bill_id": 1, "bill_line_ids": [2, 2]}),
        (
            "payment_term.create",
            {
                **PARAMETERS["payment_term.create"],
                "lines": [
                    {
                        "value": "percent",
                        "value_amount": "90",
                        "delay_type": "days_after",
                        "nb_days": 30,
                    }
                ],
            },
        ),
        ("payment_term.update", {"payment_term_id": 1, "lines": []}),
        ("payment_term.lines.replace", {"payment_term_id": 1, "lines": []}),
        (
            "period.accrual.generate",
            {
                **PARAMETERS["period.accrual.generate"],
                "reversal_date": "2026-08-28",
            },
        ),
        (
            "period.accrual.generate",
            {
                **PARAMETERS["period.accrual.generate"],
                "amount": "10",
            },
        ),
    ),
)
def test_invalid_closed_contracts_fail(
    capability_id: str, parameters: dict[str, Any]
) -> None:
    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request(capability_id, _request(parameters))
    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize(
    "capability_id",
    (
        "purchase.order.bill.create",
        "purchase_bill.match",
        "purchase_bill.lines.unmatch",
        "payment_term.update",
        "payment_term.lines.replace",
        "payment_term.archive",
        "payment_term.restore",
    ),
)
def test_non_create_capabilities_require_deterministic_keys(
    capability_id: str,
) -> None:
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            Port(capability_id),
            capability_id,
            _request(PARAMETERS[capability_id]),
            "safe-but-wrong-key",
            capability_id,
        )
    assert caught.value.code == "invalid_idempotency_key"


@pytest.mark.parametrize(
    "capability_id",
    (
        "payment_term.create",
        "period.accrual.generate",
    ),
)
def test_create_capabilities_accept_caller_safe_keys(capability_id: str) -> None:
    results = [
        execute_core_write(
            Port(capability_id),
            capability_id,
            _request(PARAMETERS[capability_id]),
            key,
            capability_id,
        )
        for key in ("first-safe-create-key", "other-safe-create-key")
    ]
    assert results[0] == results[1]


@pytest.mark.parametrize("capability_id", CAPABILITY_IDS)
def test_result_requires_draft_vendor_bill_without_reconciliation(
    capability_id: str,
) -> None:
    result = _result(capability_id)
    result["partial_reconcile_ids"] = [8]
    normalized = validate_core_write_request(
        capability_id, _request(PARAMETERS[capability_id])
    )[2]
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            Port(capability_id, result),
            capability_id,
            _request(PARAMETERS[capability_id]),
            _key(capability_id, normalized),
            capability_id,
        )
    assert caught.value.code == "failed_validation"
