from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

import pytest

from odoo_accounting_cli_v4.capabilities.core_writes import (
    CORE_WRITE_CAPABILITY_IDS,
    CoreWriteError,
    _expected_idempotency_key,
    execute_core_write,
    validate_core_write_request,
)

CAPABILITY_IDS = (
    "sale.order.invoice.create",
    "stock.transfer.create",
    "stock.transfer.confirm",
    "stock.transfer.assign",
    "stock.transfer.quantities.set",
    "stock.transfer.validate",
    "stock.transfer.unreserve",
    "stock.transfer.cancel",
)
PARAMETERS: dict[str, dict[str, Any]] = {
    "sale.order.invoice.create": {"order_id": 101},
    "stock.transfer.create": {
        "picking_type_id": 2,
        "location_id": 8,
        "location_dest_id": 9,
        "partner_id": None,
        "scheduled_date": "2026-08-30 08:00:00",
        "origin": "CLI transfer",
        "moves": [
            {
                "product_id": 51,
                "name": "Stock item",
                "quantity": "3",
                "uom_id": 1,
            }
        ],
    },
    "stock.transfer.confirm": {"transfer_id": 401},
    "stock.transfer.assign": {"transfer_id": 401},
    "stock.transfer.quantities.set": {
        "transfer_id": 401,
        "lines": [
            {"move_id": 502, "quantity": "0"},
            {"move_id": 501, "quantity": "2.5"},
        ],
    },
    "stock.transfer.validate": {
        "transfer_id": 401,
        "backorder_policy": "create",
    },
    "stock.transfer.unreserve": {"transfer_id": 401},
    "stock.transfer.cancel": {"transfer_id": 401},
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


def _result(capability_id: str) -> dict[str, Any]:
    if capability_id == "sale.order.invoice.create":
        return {
            "model": "account.move",
            "id": 907,
            "name": "INV/2026/00907",
            "state": "draft",
            "company_id": 7,
            "move_type": "out_invoice",
            "source_id": 101,
            "line_ids": [507],
            "partial_reconcile_ids": [],
            "full_reconcile_id": None,
            "reconciled": False,
        }
    state = {
        "stock.transfer.create": "draft",
        "stock.transfer.confirm": "confirmed",
        "stock.transfer.assign": "assigned",
        "stock.transfer.quantities.set": "assigned",
        "stock.transfer.validate": "done",
        "stock.transfer.unreserve": "confirmed",
        "stock.transfer.cancel": "cancel",
    }[capability_id]
    return {
        "model": "stock.picking",
        "id": 908 if capability_id == "stock.transfer.create" else 401,
        "name": "WH/INT/00908",
        "state": state,
        "company_id": 7,
        "move_type": None,
        "source_id": 2,
        "line_ids": [501],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }


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


def _normalized_and_key(capability_id: str) -> tuple[dict[str, Any], str]:
    _, context, normalized = validate_core_write_request(
        capability_id, _request(PARAMETERS[capability_id])
    )
    expected = _expected_idempotency_key(
        capability_id, normalized, context["company_id"]
    )
    return normalized, expected or "caller-stock-transfer-create-key"


def test_all_eight_capabilities_are_in_the_fixed_core_write_set() -> None:
    assert set(CAPABILITY_IDS) <= CORE_WRITE_CAPABILITY_IDS


@pytest.mark.parametrize("capability_id", CAPABILITY_IDS)
def test_all_eight_closed_contracts_execute_through_the_shared_port(
    capability_id: str,
) -> None:
    normalized, key = _normalized_and_key(capability_id)
    port = Port(capability_id)

    data = execute_core_write(
        port,
        capability_id,
        _request(PARAMETERS[capability_id]),
        key,
        capability_id,
    )

    assert data == {"idempotent_replay": False, "result": _result(capability_id)}
    assert port.calls == [
        {
            "capability_id": capability_id,
            "company_id": 7,
            "idempotency_key": key,
            "confirmation": capability_id,
            "parameters": normalized,
        }
    ]


def test_quantity_lines_normalize_before_the_deterministic_key_is_derived() -> None:
    capability_id = "stock.transfer.quantities.set"
    normalized, key = _normalized_and_key(capability_id)
    assert [line["move_id"] for line in normalized["lines"]] == [501, 502]
    digest = hashlib.sha256(
        json.dumps(
            normalized["lines"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()[:32]
    assert key == f"{capability_id}:401:{digest}"


@pytest.mark.parametrize(
    ("capability_id", "expected"),
    (
        ("sale.order.invoice.create", "sale.order.invoice.create:101"),
        ("stock.transfer.confirm", "stock.transfer.confirm:401"),
        ("stock.transfer.assign", "stock.transfer.assign:401"),
        ("stock.transfer.validate", "stock.transfer.validate:401:create"),
        ("stock.transfer.unreserve", "stock.transfer.unreserve:401"),
        ("stock.transfer.cancel", "stock.transfer.cancel:401"),
    ),
)
def test_target_writes_have_stable_exact_keys(
    capability_id: str, expected: str
) -> None:
    assert _normalized_and_key(capability_id)[1] == expected


def test_stock_transfer_create_accepts_a_caller_safe_key() -> None:
    _, context, normalized = validate_core_write_request(
        "stock.transfer.create", _request(PARAMETERS["stock.transfer.create"])
    )
    assert (
        _expected_idempotency_key(
            "stock.transfer.create", normalized, context["company_id"]
        )
        is None
    )
    for key in ("first-stock-create-key", "second-stock-create-key"):
        execute_core_write(
            Port("stock.transfer.create"),
            "stock.transfer.create",
            _request(PARAMETERS["stock.transfer.create"]),
            key,
            "stock.transfer.create",
        )


@pytest.mark.parametrize(
    "capability_id",
    tuple(item for item in CAPABILITY_IDS if item != "stock.transfer.create"),
)
def test_target_writes_reject_a_non_deterministic_key(capability_id: str) -> None:
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            Port(capability_id),
            capability_id,
            _request(PARAMETERS[capability_id]),
            "safe-but-wrong-key",
            capability_id,
        )
    assert caught.value.code == "invalid_idempotency_key"


@pytest.mark.parametrize("capability_id", CAPABILITY_IDS)
def test_confirmation_is_the_exact_capability_id(capability_id: str) -> None:
    _, key = _normalized_and_key(capability_id)
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            Port(capability_id),
            capability_id,
            _request(PARAMETERS[capability_id]),
            key,
            "confirm",
        )
    assert caught.value.code == "confirmation_required"


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    (
        ("sale.order.invoice.create", {"order_id": 0}),
        (
            "stock.transfer.create",
            {**PARAMETERS["stock.transfer.create"], "scheduled_date": "2026-08-30"},
        ),
        (
            "stock.transfer.create",
            {**PARAMETERS["stock.transfer.create"], "moves": []},
        ),
        (
            "stock.transfer.create",
            {
                **PARAMETERS["stock.transfer.create"],
                "moves": [
                    {
                        "product_id": 51,
                        "name": "Stock item",
                        "quantity": "0",
                        "uom_id": 1,
                    }
                ],
            },
        ),
        ("stock.transfer.confirm", {"transfer_id": 0}),
        (
            "stock.transfer.quantities.set",
            {
                "transfer_id": 401,
                "lines": [
                    {"move_id": 501, "quantity": "1"},
                    {"move_id": 501, "quantity": "2"},
                ],
            },
        ),
        (
            "stock.transfer.quantities.set",
            {"transfer_id": 401, "lines": [{"move_id": 501, "quantity": "-1"}]},
        ),
        (
            "stock.transfer.validate",
            {"transfer_id": 401, "backorder_policy": "ask"},
        ),
        ("stock.transfer.cancel", {"transfer_id": 401, "sudo": True}),
    ),
)
def test_critical_invalid_contracts_fail_closed(
    capability_id: str, parameters: dict[str, Any]
) -> None:
    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request(capability_id, _request(parameters))
    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize("capability_id", CAPABILITY_IDS)
def test_results_are_bound_to_the_expected_business_model(capability_id: str) -> None:
    malformed = _result(capability_id)
    malformed["model"] = "res.partner"
    _, key = _normalized_and_key(capability_id)
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            Port(capability_id, malformed),
            capability_id,
            _request(PARAMETERS[capability_id]),
            key,
            capability_id,
        )
    assert caught.value.code == "failed_validation"


@pytest.mark.parametrize(
    ("capability_id", "field", "value"),
    (
        ("sale.order.invoice.create", "source_id", 999),
        ("stock.transfer.create", "source_id", 999),
        ("stock.transfer.confirm", "id", 999),
        ("stock.transfer.validate", "state", "assigned"),
        ("stock.transfer.cancel", "reconciled", True),
    ),
)
def test_result_identity_state_and_reconciliation_are_bound(
    capability_id: str, field: str, value: Any
) -> None:
    malformed = _result(capability_id)
    malformed[field] = value
    _, key = _normalized_and_key(capability_id)
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            Port(capability_id, malformed),
            capability_id,
            _request(PARAMETERS[capability_id]),
            key,
            capability_id,
        )
    assert caught.value.code == "failed_validation"
