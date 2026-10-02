from __future__ import annotations

from copy import deepcopy

import pytest
from test_core_writes import FakePort, _request, _success_response

from odoo_accounting_cli_v4.capabilities.core_writes import (
    CoreWriteError,
    _expected_idempotency_key,
    _valid_batch_result_shape,
    execute_core_write,
    validate_core_write_request,
)
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

REFUNDS = ("customer_credit_note.create", "vendor_refund.create")
PAYMENTS = ("receivable.payment.register", "payable.payment.register")
ORDERS = ("sale.order.invoice.create", "purchase.order.bill.create")
DOWN_PAYMENT = "sale.order.down_payment.create"
DATE = "2026-10-02"
PAYMENT = {"move_ids": [12, 11], "journal_id": 4, "payment_date": DATE}


@pytest.fixture(scope="module")
def registry():
    return load_registry()


def request(parameters):
    value = _request("customer_invoice.create")
    value["parameters"] = deepcopy(parameters)
    return value


def item(capability, source_id, record_id=901, **changes):
    payment = capability in PAYMENTS
    value = {
        "model": "account.payment" if payment else "account.move",
        "id": record_id,
        "name": "INV/2026/001",
        "state": "paid" if payment else "draft",
        "company_id": 7,
        "move_type": None if payment else (
            "out_refund" if capability == REFUNDS[0] else
            "in_refund" if capability == REFUNDS[1] else
            "in_invoice" if capability == ORDERS[1] else "out_invoice"
        ),
        "source_id": source_id,
        "line_ids": [record_id + 1000],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": payment,
    }
    return {**value, **changes}


def batch(*items):
    return {"items": list(items), "processed_count": len(items)}


def response(capability, data):
    value = _success_response(PAYMENTS[0])
    value["capability"] = capability
    value["data"] = data
    items = data["result"].get("items", [data["result"]])
    value["odoo"]["model"] = items[0]["model"]
    value["odoo"]["record_ids"] = [entry["id"] for entry in items]
    return value


@pytest.mark.parametrize("capability", REFUNDS)
def test_full_refund_batch_sorts_sources_and_keeps_caller_key(capability, registry):
    parameters = {"move_ids": [12, 11], "date": DATE, "reason": "Full refund"}
    value = request(parameters)
    registry.validate_instance(f"schemas/v1/{capability}.request.schema.json", value)
    normalized = validate_core_write_request(capability, value)[2]
    assert normalized == {**parameters, "move_ids": [11, 12]}
    assert _expected_idempotency_key(capability, normalized, 7) is None
    # Results are sorted by created ID, not by reversed source ID.
    result = batch(item(capability, 12), item(capability, 11, 902))
    data = execute_core_write(FakePort(capability, result=result), capability, value, "refund-round-1", capability)
    assert data["result"] == result and value == request(parameters)
    registry.validate_instance(f"schemas/v1/{capability}.response.schema.json", response(capability, data))


@pytest.mark.parametrize("capability", REFUNDS)
def test_legacy_single_refund_preserves_custom_lines(capability, registry):
    value = _request(capability)
    value["parameters"]["lines"] = _request("invoice.lines.replace")["parameters"]["lines"]
    original = deepcopy(value)
    registry.validate_instance(f"schemas/v1/{capability}.request.schema.json", value)
    normalized = validate_core_write_request(capability, value)[2]
    assert normalized == original["parameters"]
    port = FakePort(capability)
    data = execute_core_write(port, capability, value, "custom-refund-round-1", capability)
    assert "items" not in data["result"] and port.calls[0]["parameters"] == normalized
    assert value == original


@pytest.mark.parametrize("capability", PAYMENTS)
@pytest.mark.parametrize("sources", [{"move_id": 11}, {"move_ids": [12, 11]}])
@pytest.mark.parametrize("mode", ["full", "next", "overdue", "before_date"])
def test_payment_installment_modes_preserve_omission_and_allow_operation_keys(capability, sources, mode, registry):
    parameters = {**sources, "journal_id": 4, "payment_date": DATE, "installments_mode": mode}
    if mode == "before_date":
        parameters["installment_cutoff_date"] = "2026-11-30"
    value = request(parameters)
    registry.validate_instance(f"schemas/v1/{capability}.request.schema.json", value)
    normalized = validate_core_write_request(capability, value)[2]
    assert set(normalized) == set(parameters)
    assert _expected_idempotency_key(capability, normalized, 7) is None
    port = FakePort(capability, result=item(capability, 11))
    execute_core_write(port, capability, value, "installment-round-2", capability)
    assert port.calls[0]["parameters"] == normalized
    assert value == request(parameters)


@pytest.mark.parametrize("capability", PAYMENTS)
@pytest.mark.parametrize("extra", [
    {"amount": "25"},
    {"payment_difference_handling": "open"},
    {"amount": "25", "group_payment": True},
    {"amount": "25", "payment_difference_handling": "reconcile", "writeoff_account_id": 31, "writeoff_label": "Fee"},
])
def test_partial_grouped_batch_controls_use_operation_key(capability, extra, registry):
    value = request({**PAYMENT, **extra})
    registry.validate_instance(f"schemas/v1/{capability}.request.schema.json", value)
    normalized = validate_core_write_request(capability, value)[2]
    assert _expected_idempotency_key(capability, normalized, 7) is None
    result = item(capability, None, reconciled=False)
    execute_core_write(FakePort(capability, result=result), capability, value, "partial-batch-round", capability)


@pytest.mark.parametrize("capability", PAYMENTS)
@pytest.mark.parametrize("count", [1, 2])
def test_ungrouped_payment_always_returns_target_local_batch(capability, count, registry):
    value = request({**PAYMENT, "group_payment": False})
    result = batch(*(item(capability, 11 + index, 901 + index) for index in range(count)))
    data = execute_core_write(FakePort(capability, result=result), capability, value, "ungrouped-round-1", capability)
    registry.validate_instance(f"schemas/v1/{capability}.response.schema.json", response(capability, data))
    with pytest.raises(CoreWriteError, match="batch result"):
        execute_core_write(FakePort(capability, result=result["items"][0]), capability, value, "ungrouped-round-1", capability)


@pytest.mark.parametrize("capability", ORDERS)
@pytest.mark.parametrize("source_ids, source", [([11], 11), ([12, 11], None)])
@pytest.mark.parametrize("refund", [False, True])
def test_new_order_arrays_keep_batch_even_for_one_native_invoice(capability, source_ids, source, refund, registry):
    parameters = {"order_ids": source_ids}
    if capability == ORDERS[0]:
        parameters.update(consolidated_billing=True, deduct_down_payments=refund)
    value = request(parameters)
    registry.validate_instance(f"schemas/v1/{capability}.request.schema.json", value)
    normalized = validate_core_write_request(capability, value)[2]
    assert normalized == {**parameters, "order_ids": sorted(source_ids)}
    assert _expected_idempotency_key(capability, normalized, 7) is None
    native_item = item(capability, source)
    if refund:
        native_item["move_type"] = "out_refund" if capability == ORDERS[0] else "in_refund"
    result = batch(native_item)
    data = execute_core_write(FakePort(capability, result=result), capability, value, "invoice-round-2", capability)
    registry.validate_instance(f"schemas/v1/{capability}.response.schema.json", response(capability, data))
    with pytest.raises(CoreWriteError, match="batch result"):
        execute_core_write(FakePort(capability, result=native_item), capability, value, "invoice-round-2", capability)


@pytest.mark.parametrize("method,amount", [("percentage", "100"), ("percentage", "0.5"), ("fixed", "1000.25")])
def test_down_payment_closed_native_shape_and_caller_key(method, amount, registry):
    parameters = {"order_id": 11, "method": method, "amount": amount}
    value = request(parameters)
    registry.validate_instance(f"schemas/v1/{DOWN_PAYMENT}.request.schema.json", value)
    assert validate_core_write_request(DOWN_PAYMENT, value)[2] == parameters
    assert _expected_idempotency_key(DOWN_PAYMENT, parameters, 7) is None
    result = item(DOWN_PAYMENT, 11)
    data = execute_core_write(FakePort(DOWN_PAYMENT, result=result), DOWN_PAYMENT, value, "down-payment-round-1", DOWN_PAYMENT)
    registry.validate_instance(f"schemas/v1/{DOWN_PAYMENT}.response.schema.json", response(DOWN_PAYMENT, data))


@pytest.mark.parametrize("changes", [
    {"invoice_policy": "order"}, {"invoice_policy": "delivery"},
    {"purchase_method": "purchase"}, {"purchase_method": "receive"},
    {"invoice_policy": "delivery", "purchase_method": "receive", "sale_tax_ids": [42, 41]},
])
def test_product_policy_writes_are_optional_nonnull_and_keep_content_key(changes, registry):
    capability = "product.accounting_profile.update"
    value = request({"product_id": 11, "changes": changes})
    registry.validate_instance(f"schemas/v1/{capability}.request.schema.json", value)
    normalized = validate_core_write_request(capability, value)[2]
    assert set(normalized["changes"]) == set(changes)
    assert _expected_idempotency_key(capability, normalized, 7).startswith(f"{capability}:11:")
    assert value == request({"product_id": 11, "changes": changes})


INVALID = [
    *[(capability, {"move_ids": ids, "date": DATE, "reason": "Refund"}) for capability in REFUNDS for ids in ([11], [11, 11], [], list(range(1, 102)), [True, 12])],
    (REFUNDS[0], {"move_ids": [11, 12], "move_id": 11, "date": DATE, "reason": "Refund"}),
    (REFUNDS[0], {"move_ids": [11, 12], "lines": [], "date": DATE, "reason": "Refund"}),
    *[(capability, {**PAYMENT, **extra}) for capability in PAYMENTS for extra in (
        {"installments_mode": None}, {"installments_mode": []}, {"installments_mode": {}},
        {"installments_mode": "invalid"}, {"group_payment": None}, {"group_payment": 1},
        {"installments_mode": "before_date"}, {"installments_mode": "next", "installment_cutoff_date": DATE},
        {"installment_cutoff_date": DATE}, {"installments_mode": "before_date", "installment_cutoff_date": "2026-02-30"},
        {"group_payment": False, "amount": "10"}, {"amount": "10.0"},
        {"amount": "10", "payment_difference_handling": "reconcile"},
    )],
    *[(capability, {"order_ids": ids}) for capability in ORDERS for ids in ([], [11, 11], [True], list(range(1, 102)))],
    (ORDERS[0], {"order_id": 11, "consolidated_billing": True}),
    *[(ORDERS[0], {"order_ids": [11], "deduct_down_payments": value}) for value in (None, 1, [], {})],
    (ORDERS[1], {"order_ids": [11], "consolidated_billing": True}),
    *[(DOWN_PAYMENT, {"order_id": 11, "method": method, "amount": amount}) for method, amount in (
        ("percentage", "100.01"), ("percentage", "0"), ("fixed", "10.0"), ("fixed", 10),
        ("delivered", "10"), (None, "10"), ([], "10"), ({}, "10"),
    )],
    *[("product.accounting_profile.update", {"product_id": 11, "changes": {field: invalid}}) for field in ("invoice_policy", "purchase_method") for invalid in (None, True, [], {}, "invalid")],
    ("product.category.accounting_profile.update", {"category_id": 11, "changes": {"invoice_policy": "order"}}),
]


@pytest.mark.parametrize("capability,parameters", INVALID)
def test_invalid_new_requests_rejected_before_dispatch(capability, parameters, registry):
    value = request(parameters)
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(f"schemas/v1/{capability}.request.schema.json", value)
    port = FakePort(capability, result=None)
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(port, capability, value, "invalid-round-1", capability)
    assert caught.value.code == "invalid_request" and port.calls == []
    assert value == request(parameters)


@pytest.mark.parametrize("capability,parameters,result", [
    (REFUNDS[0], {"move_ids": [11, 12], "date": DATE, "reason": "Refund"}, batch(item(REFUNDS[0], 11))),
    (REFUNDS[0], {"move_ids": [11, 12], "date": DATE, "reason": "Refund"}, batch(item(REFUNDS[0], 11), item(REFUNDS[0], 13, 902))),
    (ORDERS[0], {"order_ids": [11]}, batch(item(ORDERS[0], None))),
    (ORDERS[0], {"order_ids": [11, 12]}, batch(item(ORDERS[0], 13))),
    (ORDERS[0], {"order_ids": [11]}, batch(item(ORDERS[0], 11, move_type="in_invoice"))),
    (ORDERS[1], {"order_ids": [11]}, batch(item(ORDERS[1], 11, company_id=8))),
    (PAYMENTS[0], {**PAYMENT, "group_payment": False}, batch(item(PAYMENTS[0], 13))),
    (PAYMENTS[0], {**PAYMENT, "group_payment": True}, batch(item(PAYMENTS[0], 11))),
    (ORDERS[0], {"order_ids": [11]}, {"items": [item(ORDERS[0], 11)], "processed_count": 2}),
    (ORDERS[0], {"order_ids": [11]}, batch(item(ORDERS[0], 11, 902), item(ORDERS[0], 11, 901))),
    (DOWN_PAYMENT, {"order_id": 11, "method": "fixed", "amount": "10"}, item(DOWN_PAYMENT, 11, move_type="out_refund")),
])
def test_new_result_validators_fail_closed(capability, parameters, result):
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(FakePort(capability, result=result), capability, request(parameters), "round-result-check", capability)
    assert caught.value.code == "failed_validation"


@pytest.mark.parametrize("capability", (*PAYMENTS, *ORDERS))
def test_legacy_omissions_preserve_parameters_keys_and_singular_results(capability):
    value = _request(capability)
    normalized = validate_core_write_request(capability, value)[2]
    assert normalized == value["parameters"]
    primary = normalized["move_id"] if capability in PAYMENTS else normalized["order_id"]
    key = f"{capability}:{primary}"
    assert _expected_idempotency_key(capability, normalized, 7) == key
    assert "items" not in execute_core_write(FakePort(capability), capability, value, key, capability)["result"]


def test_legacy_full_payment_batch_retains_content_key_and_verification_guard():
    capability = PAYMENTS[0]
    value = request(PAYMENT)
    normalized = validate_core_write_request(capability, value)[2]
    key = _expected_idempotency_key(capability, normalized, 7)
    assert key is not None and key.startswith(f"{capability}:7:")
    with pytest.raises(CoreWriteError):
        execute_core_write(FakePort(capability, result=item(capability, None, reconciled=False)), capability, value, key, capability)


@pytest.mark.parametrize("count", [1, 101, 1000, 1001])
def test_new_batch_bound_is_target_local_and_does_not_widen_lifecycle(count, registry):
    capability = ORDERS[0]
    result = batch(*(item(capability, 11, 901 + index) for index in range(count)))
    assert not _valid_batch_result_shape(result)
    value = request({"order_ids": [11]})
    if count <= 1000:
        data = execute_core_write(FakePort(capability, result=result), capability, value, "bound-round-1", capability)
        registry.validate_instance(f"schemas/v1/{capability}.response.schema.json", response(capability, data))
    else:
        with pytest.raises(CoreWriteError):
            execute_core_write(FakePort(capability, result=result), capability, value, "bound-round-1", capability)
        with pytest.raises(InstanceValidationError):
            registry.validate_instance(f"schemas/v1/{capability}.response.schema.json", response(capability, {"idempotent_replay": False, "result": result}))
    with pytest.raises(InstanceValidationError):
        registry.validate_instance("schemas/v1/core-write-batch-result.schema.json", {"idempotent_replay": False, "result": result})
