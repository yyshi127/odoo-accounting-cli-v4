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

ORDER_WRITE_IDS = (
    "sale.order.create",
    "sale.order.update_draft",
    "sale.order.lines.replace",
    "sale.order.confirm",
    "sale.order.cancel",
    "sale.order.reset_to_draft",
    "purchase.order.create",
    "purchase.order.update_draft",
    "purchase.order.lines.replace",
    "purchase.order.confirm",
    "purchase.order.cancel",
    "purchase.order.reset_to_draft",
)

SALE_LINE = {
    "product_id": 51,
    "name": "Consulting service",
    "quantity": "3",
    "uom_id": 1,
    "price_unit": "10.5",
    "discount": "0",
    "tax_ids": [8, 9],
}
PURCHASE_LINE = {
    **SALE_LINE,
    "product_id": 52,
    "name": "Purchased service",
    "quantity": "5",
    "price_unit": "8",
    "date_planned": "2026-08-30 02:03:04",
}
PARAMETERS: dict[str, dict[str, Any]] = {
    "sale.order.create": {
        "partner_id": 31,
        "pricelist_id": 41,
        "date_order": "2026-08-28 01:02:03",
        "client_order_ref": "CLIENT-31",
        "validity_date": "2026-09-30",
        "commitment_date": "2026-09-01 08:00:00",
        "payment_term_id": None,
        "lines": [SALE_LINE],
    },
    "sale.order.update_draft": {
        "order_id": 101,
        "changes": {
            "client_order_ref": "CLIENT-UPDATED",
            "validity_date": None,
            "commitment_date": "2026-09-02 08:00:00",
            "payment_term_id": 12,
        },
    },
    "sale.order.lines.replace": {"order_id": 101, "lines": [SALE_LINE]},
    "sale.order.confirm": {"order_id": 101},
    "sale.order.cancel": {"order_id": 101},
    "sale.order.reset_to_draft": {"order_id": 101},
    "purchase.order.create": {
        "partner_id": 32,
        "currency_id": 6,
        "picking_type_id": 2,
        "date_order": "2026-08-28 01:02:03",
        "partner_ref": "VENDOR-32",
        "payment_term_id": 13,
        "incoterm_id": None,
        "lines": [PURCHASE_LINE],
    },
    "purchase.order.update_draft": {
        "order_id": 201,
        "changes": {
            "partner_ref": "VENDOR-UPDATED",
            "date_order": "2026-08-29 01:02:03",
            "payment_term_id": None,
            "incoterm_id": 3,
        },
    },
    "purchase.order.lines.replace": {"order_id": 201, "lines": [PURCHASE_LINE]},
    "purchase.order.confirm": {"order_id": 201},
    "purchase.order.cancel": {"order_id": 201},
    "purchase.order.reset_to_draft": {"order_id": 201},
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
    if capability_id.endswith(".create"):
        return "order-create-safe-key-001"
    if capability_id.endswith((".update_draft", ".lines.replace")):
        target = (
            parameters["changes"]
            if capability_id.endswith(".update_draft")
            else parameters["lines"]
        )
        canonical = json.dumps(
            target,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"{capability_id}:{parameters['order_id']}:{digest}"
    return f"{capability_id}:{parameters['order_id']}"


def _state(capability_id: str) -> str:
    if capability_id == "sale.order.confirm":
        return "sale"
    if capability_id == "purchase.order.confirm":
        return "purchase"
    if capability_id.endswith(".cancel"):
        return "cancel"
    return "draft"


def _result(capability_id: str, *, state: str | None = None) -> dict[str, Any]:
    parameters = PARAMETERS[capability_id]
    sale = capability_id.startswith("sale.order.")
    record_id = 901 if capability_id.endswith(".create") else parameters["order_id"]
    line_count = len(parameters.get("lines", [None]))
    return {
        "model": "sale.order" if sale else "purchase.order",
        "id": record_id,
        "name": "S00901" if sale else "P00901",
        "state": _state(capability_id) if state is None else state,
        "company_id": 7,
        "move_type": None,
        "source_id": 31 if sale else 32,
        "line_ids": list(range(501, 501 + line_count)),
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }


class Port:
    user_id = 42

    def __init__(self, capability_id: str, *, state: str | None = None) -> None:
        self.capability_id = capability_id
        self.state = state
        self.calls: list[dict[str, Any]] = []

    def execute(self, **payload: Any) -> dict[str, Any]:
        self.calls.append(deepcopy(payload))
        return {
            "user_id": self.user_id,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "idempotent_replay": False,
            "result": _result(self.capability_id, state=self.state),
        }


def test_order_write_capability_set_is_registered() -> None:
    assert set(ORDER_WRITE_IDS) <= CORE_WRITE_CAPABILITY_IDS


@pytest.mark.parametrize("capability_id", ORDER_WRITE_IDS)
def test_exact_contract_executes_through_the_shared_core_write_port(
    capability_id: str,
) -> None:
    parameters = PARAMETERS[capability_id]
    _, context, normalized = validate_core_write_request(
        capability_id, _request(parameters)
    )
    port = Port(capability_id)

    data = execute_core_write(
        port,
        capability_id,
        _request(parameters),
        _key(capability_id, normalized),
        capability_id,
    )

    assert context["company_id"] == 7
    assert normalized == parameters
    assert data == {"idempotent_replay": False, "result": _result(capability_id)}
    assert port.calls == [
        {
            "capability_id": capability_id,
            "company_id": 7,
            "idempotency_key": _key(capability_id, parameters),
            "confirmation": capability_id,
            "parameters": parameters,
        }
    ]


@pytest.mark.parametrize(
    "capability_id",
    (
        "sale.order.update_draft",
        "sale.order.lines.replace",
        "sale.order.confirm",
        "purchase.order.update_draft",
        "purchase.order.lines.replace",
        "purchase.order.cancel",
    ),
)
def test_deterministic_order_keys_are_required(capability_id: str) -> None:
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            Port(capability_id),
            capability_id,
            _request(PARAMETERS[capability_id]),
            "safe-but-wrong-key",
            capability_id,
        )
    assert caught.value.code == "invalid_idempotency_key"


@pytest.mark.parametrize("capability_id", ORDER_WRITE_IDS)
def test_confirmation_must_exactly_equal_the_capability(capability_id: str) -> None:
    parameters = PARAMETERS[capability_id]
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            Port(capability_id),
            capability_id,
            _request(parameters),
            _key(capability_id, parameters),
            "confirm",
        )
    assert caught.value.code == "confirmation_required"


def test_create_accepts_a_free_safe_idempotency_key() -> None:
    first = deepcopy(PARAMETERS["sale.order.create"])
    second = deepcopy(first)
    second["client_order_ref"] = "A different business request"

    for parameters in (first, second):
        execute_core_write(
            Port("sale.order.create"),
            "sale.order.create",
            _request(parameters),
            "caller-owned-safe-key-42",
            "sale.order.create",
        )


@pytest.mark.parametrize("state", ("purchase", "to approve"))
def test_purchase_confirm_accepts_both_native_terminal_states(state: str) -> None:
    capability_id = "purchase.order.confirm"
    parameters = PARAMETERS[capability_id]
    data = execute_core_write(
        Port(capability_id, state=state),
        capability_id,
        _request(parameters),
        _key(capability_id, parameters),
        capability_id,
    )
    assert data["result"]["state"] == state


@pytest.mark.parametrize(
    ("capability_id", "path", "invalid"),
    (
        ("sale.order.create", ("partner_id",), 0),
        ("sale.order.create", ("date_order",), "2026-08-28T01:02:03Z"),
        ("sale.order.create", ("validity_date",), "2026-02-30"),
        ("sale.order.create", ("commitment_date",), "2026-08-28"),
        ("sale.order.create", ("client_order_ref",), " padded "),
        ("sale.order.create", ("lines", 0, "quantity"), "0"),
        ("sale.order.create", ("lines", 0, "price_unit"), "-1"),
        ("sale.order.create", ("lines", 0, "price_unit"), "10.50"),
        ("sale.order.create", ("lines", 0, "discount"), "100.01"),
        ("sale.order.create", ("lines", 0, "tax_ids"), [9, 8]),
        ("purchase.order.create", ("currency_id",), None),
        ("purchase.order.create", ("lines", 0, "date_planned"), "2026-08-30"),
        ("purchase.order.update_draft", ("changes", "date_order"), "bad"),
    ),
)
def test_field_decimal_date_and_datetime_validation_is_closed(
    capability_id: str, path: tuple[Any, ...], invalid: Any
) -> None:
    parameters = deepcopy(PARAMETERS[capability_id])
    target: Any = parameters
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = invalid

    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request(capability_id, _request(parameters))
    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    (
        ("sale.order.create", {**PARAMETERS["sale.order.create"], "extra": 1}),
        ("sale.order.lines.replace", {"order_id": 101, "lines": []}),
        ("sale.order.update_draft", {"order_id": 101, "changes": {}}),
        ("purchase.order.confirm", {"order_id": 201, "state": "purchase"}),
    ),
)
def test_parameter_objects_are_exact(
    capability_id: str, parameters: dict[str, Any]
) -> None:
    with pytest.raises(CoreWriteError):
        validate_core_write_request(capability_id, _request(parameters))


def test_envelope_and_result_shapes_fail_closed() -> None:
    request = _request(PARAMETERS["sale.order.confirm"])
    request["extra"] = True
    with pytest.raises(CoreWriteError):
        validate_core_write_request("sale.order.confirm", request)

    capability_id = "sale.order.lines.replace"
    parameters = PARAMETERS[capability_id]
    port = Port(capability_id)
    malformed = _result(capability_id)
    malformed["line_ids"] = []
    port.execute = lambda **_payload: {
        "user_id": 42,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "idempotent_replay": False,
        "result": malformed,
    }
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            port,
            capability_id,
            _request(parameters),
            _key(capability_id, parameters),
            capability_id,
        )
    assert caught.value.code == "failed_validation"
