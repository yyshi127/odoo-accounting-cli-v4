from __future__ import annotations

import hashlib
import io
import json
from copy import deepcopy
from typing import Any

import pytest

from odoo_accounting_cli_v4.cli import main

_REQUEST_ID = "529c95af-0b85-4c9a-a9d9-1b5982822987"
_SALE_LINE = {
    "product_id": 51,
    "name": "Sale line",
    "quantity": "3",
    "uom_id": 1,
    "price_unit": "10.5",
    "discount": "0",
    "tax_ids": [],
}
_PURCHASE_LINE = {
    **_SALE_LINE,
    "product_id": 52,
    "name": "Purchase line",
    "quantity": "5",
    "price_unit": "8",
    "date_planned": "2026-08-30 02:03:04",
}
_CASES: dict[str, dict[str, Any]] = {
    "sale.order.create": {
        "partner_id": 31,
        "pricelist_id": 41,
        "date_order": "2026-08-28 01:02:03",
        "client_order_ref": "CLIENT-31",
        "validity_date": "2026-09-30",
        "commitment_date": None,
        "payment_term_id": None,
        "lines": [_SALE_LINE],
    },
    "sale.order.update_draft": {
        "order_id": 101,
        "changes": {"client_order_ref": "CLIENT-UPDATED"},
    },
    "sale.order.lines.replace": {"order_id": 101, "lines": [_SALE_LINE]},
    "sale.order.confirm": {"order_id": 101},
    "sale.order.cancel": {"order_id": 101},
    "sale.order.reset_to_draft": {"order_id": 101},
    "purchase.order.create": {
        "partner_id": 32,
        "currency_id": 6,
        "picking_type_id": 2,
        "date_order": "2026-08-28 01:02:03",
        "partner_ref": "VENDOR-32",
        "payment_term_id": None,
        "incoterm_id": None,
        "lines": [_PURCHASE_LINE],
    },
    "purchase.order.update_draft": {
        "order_id": 201,
        "changes": {"partner_ref": "VENDOR-UPDATED"},
    },
    "purchase.order.lines.replace": {"order_id": 201, "lines": [_PURCHASE_LINE]},
    "purchase.order.confirm": {"order_id": 201},
    "purchase.order.cancel": {"order_id": 201},
    "purchase.order.reset_to_draft": {"order_id": 201},
}


def _request(parameters: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": _REQUEST_ID,
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
        return f"caller-order-create-{capability_id.split('.')[0]}"
    target = parameters.get("changes", parameters.get("lines"))
    if target is None:
        return f"{capability_id}:{parameters['order_id']}"
    canonical = json.dumps(
        target,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()[:32]
    return f"{capability_id}:{parameters['order_id']}:{digest}"


class Port:
    user_id = 42

    def __init__(self, capability_id: str) -> None:
        self.capability_id = capability_id
        self.calls: list[dict[str, Any]] = []

    def execute(self, **payload: Any) -> dict[str, Any]:
        self.calls.append(deepcopy(payload))
        parameters = payload["parameters"]
        sale = self.capability_id.startswith("sale.order.")
        record_id = (
            901 if self.capability_id.endswith(".create") else parameters["order_id"]
        )
        state = (
            "sale"
            if self.capability_id == "sale.order.confirm"
            else "purchase"
            if self.capability_id == "purchase.order.confirm"
            else "cancel"
            if self.capability_id.endswith(".cancel")
            else "draft"
        )
        line_count = len(parameters.get("lines", [None]))
        return {
            "user_id": self.user_id,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "idempotent_replay": False,
            "result": {
                "model": "sale.order" if sale else "purchase.order",
                "id": record_id,
                "name": "S00901" if sale else "P00901",
                "state": state,
                "company_id": payload["company_id"],
                "move_type": None,
                "source_id": 31 if sale else 32,
                "line_ids": list(range(501, 501 + line_count)),
                "partial_reconcile_ids": [],
                "full_reconcile_id": None,
                "reconciled": False,
            },
        }


@pytest.mark.parametrize("capability_id", tuple(_CASES))
def test_order_write_uses_the_existing_generic_core_write_cli_path(
    capability_id: str,
) -> None:
    parameters = _CASES[capability_id]
    idempotency_key = _key(capability_id, parameters)
    port = Port(capability_id)
    stdout = io.StringIO()
    stderr = io.StringIO()

    code = main(
        [
            "write",
            "run",
            capability_id,
            "--request",
            "-",
            "--idempotency-key",
            idempotency_key,
            "--confirm",
            capability_id,
        ],
        stdin=io.StringIO(json.dumps(_request(parameters))),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda selected, _document: (
            port if selected == capability_id else None
        ),
    )

    document = json.loads(stdout.getvalue())
    expected_id = 901 if capability_id.endswith(".create") else parameters["order_id"]
    assert code == 0
    assert stderr.getvalue() == ""
    assert port.calls == [
        {
            "capability_id": capability_id,
            "company_id": 7,
            "idempotency_key": idempotency_key,
            "confirmation": capability_id,
            "parameters": parameters,
        }
    ]
    assert document["success"] is True
    assert document["capability"] == capability_id
    assert document["status"] == "verified"
    assert document["odoo"] == {
        "database": "v4-dev",
        "company_id": 7,
        "user_id": 42,
        "model": "sale.order"
        if capability_id.startswith("sale.order.")
        else "purchase.order",
        "record_ids": [expected_id],
    }
