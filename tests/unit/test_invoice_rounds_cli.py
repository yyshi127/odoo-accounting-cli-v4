"""Fixed public CLI paths for the invoice-round additions and extensions."""

from __future__ import annotations

import io
import json

import pytest
from test_invoice_rounds_write_contract import batch, item, request

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.bridge.core_writes import (
    OdooCoreWritePort,
    _valid_batch_result,
)
from odoo_accounting_cli_v4.capabilities import core_writes
from odoo_accounting_cli_v4.registry import load_registry

CASES = {
    "customer_credit_note.create": {"move_ids": [11, 12], "date": "2026-10-02", "reason": "Correction"},
    "vendor_refund.create": {"move_ids": [11, 12], "date": "2026-10-02", "reason": "Correction"},
    "receivable.payment.register": {"move_id": 11, "journal_id": 4, "payment_date": "2026-10-02", "group_payment": False, "installments_mode": "next"},
    "payable.payment.register": {"move_id": 11, "journal_id": 4, "payment_date": "2026-10-02", "group_payment": False, "installments_mode": "full"},
    "sale.order.invoice.create": {"order_ids": [11], "consolidated_billing": True, "deduct_down_payments": True},
    "purchase.order.bill.create": {"order_ids": [11]},
    "sale.order.down_payment.create": {"order_id": 11, "method": "percentage", "amount": "25"},
    "product.accounting_profile.update": {"product_id": 11, "changes": {"invoice_policy": "delivery", "purchase_method": "receive"}},
}


@pytest.fixture(scope="module")
def registry():
    return load_registry()


@pytest.mark.parametrize("capability", CASES)
def test_cli_validates_dispatches_new_fields_and_single_item_batches(capability, registry, monkeypatch):
    req = request(CASES[capability])
    normalized = core_writes.validate_core_write_request(capability, req)[2]
    key = core_writes._expected_idempotency_key(capability, normalized, 7) or "rounds:caller-key"
    result = item(capability, 11)
    if capability.startswith("product."):
        result.update(model="product.product", id=11, move_type=None, source_id=21, state="active", line_ids=[])
    elif "move_ids" in normalized:
        result = batch(result, item(capability, 12, 902))
    elif "order_ids" in normalized or normalized.get("group_payment") is False:
        result = batch(result)

    class Client:
        def invoke(self, action, payload):
            assert action == "accounting.core_write.execute"
            assert payload["parameters"] == normalized
            assert payload["confirmation"] == capability and payload["idempotency_key"] == key
            return {"user_id": 42, "company_visible": True, "module_installed": True, "access_allowed": True,
                    "idempotent_replay": False, "result": result}

    monkeypatch.setattr(cli, "load_registry", lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    code = cli.main(["write", "run", capability, "--request", "-", "--confirm", capability, "--idempotency-key", key],
                    stdin=io.StringIO(json.dumps(req)), stdout=stdout, stderr=stderr, port_factory=lambda *args: OdooCoreWritePort(Client()))
    document = json.loads(stdout.getvalue())
    assert code == 0 and not stderr.getvalue() and document["data"]["result"] == result, document
    expected_ids = [entry["id"] for entry in result["items"]] if "items" in result else [result["id"]]
    assert document["odoo"]["record_ids"] == expected_ids
    registry.validate_instance(f"schemas/v1/{capability}.response.schema.json", document)


def test_bridge_global_lifecycle_bounds_do_not_expand_with_local_rounds():
    result = batch(item("sale.order.invoice.create", 11))
    assert not _valid_batch_result(result)
    assert _valid_batch_result(result, minimum=1, maximum=1000)
    many = batch(*(item("sale.order.invoice.create", 11, 1000 + i) for i in range(101)))
    assert not _valid_batch_result(many)
    assert _valid_batch_result(many, minimum=1, maximum=1000)
