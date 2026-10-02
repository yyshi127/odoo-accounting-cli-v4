from __future__ import annotations

import hashlib
import json
from copy import deepcopy

import pytest
from test_core_writes import FakePort, _request, _result, _success_response

from odoo_accounting_cli_v4.capabilities.core_writes import (
    CoreWriteError,
    _expected_idempotency_key,
    execute_core_write,
    validate_core_write_request,
)
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

CAPABILITIES = ("invoice.lines.update", "invoice.lines.add")


@pytest.fixture(scope="module")
def registry():
    return load_registry()


def request(capability):
    value = _request("invoice.line.update")
    value["parameters"] = {"move_id": 115, "lines": [{"line_id": 315, "changes": {"quantity": "2.00"}}]} if capability.endswith("update") else {"move_id": 115, "expected_line_ids": [315], "lines": _request("invoice.lines.replace")["parameters"]["lines"]}
    return value


@pytest.mark.parametrize("capability", CAPABILITIES)
def test_bulk_contract_calls_one_fixed_port_and_reuses_move_response(capability, registry):
    value = request(capability)
    normalized = validate_core_write_request(capability, value)[2]
    registry.validate_instance(f"schemas/v1/{capability}.request.schema.json", value)
    result = _result("invoice.line.update", source_id=None, line_ids=[315, 316, 317, 318])
    port = FakePort(capability, result=result)
    key = _expected_idempotency_key(capability, normalized, 7)
    data = execute_core_write(port, capability, value, key, capability)
    assert len(port.calls) == 1 and port.calls[0]["parameters"] == normalized
    assert data["result"] == result and "items" not in data["result"]
    response = _success_response("invoice.line.update")
    response["capability"] = capability
    response["data"] = data
    response["audit"]["idempotency_key"] = key
    registry.validate_instance(f"schemas/v1/{capability}.response.schema.json", response)


def test_update_sorts_distinct_ids_and_preserves_sparse_caller_text():
    value = request("invoice.lines.update")
    value["parameters"]["lines"] = [{"line_id": 316, "changes": {"product_uom_id": 61}}, {"line_id": 315, "changes": {"deductible_amount": "50.001", "tax_ids": [8, 9]}}]
    original = deepcopy(value)
    normalized = validate_core_write_request("invoice.lines.update", value)[2]
    assert normalized["lines"] == list(reversed(original["parameters"]["lines"]))
    assert value == original and "product_id" not in normalized["lines"][1]["changes"]
    reordered = deepcopy(value)
    reordered["parameters"]["lines"].reverse()
    assert _expected_idempotency_key("invoice.lines.update", normalized, 7) == _expected_idempotency_key("invoice.lines.update", validate_core_write_request("invoice.lines.update", reordered)[2], 7)


def test_add_retains_order_duplicate_rows_and_empty_expected_membership(registry):
    value = request("invoice.lines.add")
    value["parameters"]["expected_line_ids"] = []
    value["parameters"]["lines"] *= 2
    normalized = validate_core_write_request("invoice.lines.add", value)[2]
    assert normalized == value["parameters"] and len(normalized["lines"]) == 2
    registry.validate_instance("schemas/v1/invoice.lines.add.request.schema.json", value)


@pytest.mark.parametrize("capability", CAPABILITIES)
def test_content_key_binds_the_complete_normalized_target(capability):
    normalized = validate_core_write_request(capability, request(capability))[2]
    digest = hashlib.sha256(json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()[:32]
    old_key = _expected_idempotency_key(capability, normalized, 7)
    assert old_key == f"{capability}:115:{digest}"
    changed = deepcopy(normalized)
    if capability.endswith("add"):
        changed["expected_line_ids"].append(316)
    else:
        changed["lines"][0]["changes"]["quantity"] = "2.0"
    assert _expected_idempotency_key(capability, changed, 7) != old_key


@pytest.mark.parametrize("capability", CAPABILITIES)
def test_bulk_content_key_is_required_before_calling_the_port(capability):
    port = FakePort(capability, result=_result("invoice.line.update", source_id=None))
    with pytest.raises(CoreWriteError):
        execute_core_write(port, capability, request(capability), "arbitrary-caller-key", capability)
    assert not port.calls


@pytest.mark.parametrize("capability", CAPABILITIES)
def test_bulk_replay_uses_the_same_parent_move_result(capability):
    value = request(capability)
    key = _expected_idempotency_key(capability, validate_core_write_request(capability, value)[2], 7)
    result = _result("invoice.line.update", source_id=None)
    data = execute_core_write(FakePort(capability, result=result, idempotent_replay=True), capability, value, key, capability)
    assert data["idempotent_replay"] and data["result"] == result


@pytest.mark.parametrize("capability", CAPABILITIES)
@pytest.mark.parametrize("field,value", [("move_id", None), ("move_id", True), ("move_id", 0), ("move_id", "115"), ("move_id", 1.5), ("lines", None), ("lines", {}), ("lines", []), ("unknown", 1)])
def test_invalid_bulk_top_level_is_rejected_by_sdk_and_schema(capability, field, value, registry):
    current = request(capability)
    current["parameters"][field] = value
    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request(capability, current)
    assert caught.value.code == "invalid_request" and caught.value.exit_code == 2
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(f"schemas/v1/{capability}.request.schema.json", current)


@pytest.mark.parametrize("capability", CAPABILITIES)
@pytest.mark.parametrize("size", [1, 200, 201])
def test_bulk_row_boundaries(capability, size, registry):
    current = request(capability)
    row = current["parameters"]["lines"][0]
    current["parameters"]["lines"] = [{**deepcopy(row), **({"line_id": 315 + index} if capability.endswith("update") else {})} for index in range(size)]
    if size <= 200:
        assert len(validate_core_write_request(capability, current)[2]["lines"]) == size
        registry.validate_instance(f"schemas/v1/{capability}.request.schema.json", current)
    else:
        with pytest.raises(CoreWriteError):
            validate_core_write_request(capability, current)
        with pytest.raises(InstanceValidationError):
            registry.validate_instance(f"schemas/v1/{capability}.request.schema.json", current)


@pytest.mark.parametrize("row", [None, [], {}, {"line_id": True, "changes": {"quantity": "1"}}, {"line_id": 315, "changes": {}}, {"line_id": 315, "changes": {"unknown": "1"}}, {"line_id": 315, "changes": {"quantity": True}}, {"line_id": 315, "changes": {"product_uom_id": 61, "product_id": None}}, {"line_id": 315, "changes": {"deductible_amount": "100.01"}}, {"line_id": 315, "changes": {"deferred_start_date": None}}])
def test_update_reuses_strict_single_line_partial_validation(row, registry):
    current = request("invoice.lines.update")
    current["parameters"]["lines"] = [row]
    with pytest.raises(CoreWriteError):
        validate_core_write_request("invoice.lines.update", current)
    with pytest.raises(InstanceValidationError):
        registry.validate_instance("schemas/v1/invoice.lines.update.request.schema.json", current)


def test_update_duplicate_ids_are_rejected_even_with_different_changes():
    current = request("invoice.lines.update")
    current["parameters"]["lines"].append({"line_id": 315, "changes": {"price_unit": "3"}})
    with pytest.raises(CoreWriteError):
        validate_core_write_request("invoice.lines.update", current)


@pytest.mark.parametrize("ids", [None, {}, [True], [0], ["315"], [315, 315]])
def test_add_expected_membership_is_strict_and_unique(ids, registry):
    current = request("invoice.lines.add")
    current["parameters"]["expected_line_ids"] = ids
    with pytest.raises(CoreWriteError):
        validate_core_write_request("invoice.lines.add", current)
    with pytest.raises(InstanceValidationError):
        registry.validate_instance("schemas/v1/invoice.lines.add.request.schema.json", current)


def test_add_expected_membership_must_already_be_sorted():
    current = request("invoice.lines.add")
    current["parameters"]["expected_line_ids"] = [316, 315]
    with pytest.raises(CoreWriteError):
        validate_core_write_request("invoice.lines.add", current)


@pytest.mark.parametrize("changes", [{"unknown": 1}, {"product_uom_id": None}, {"product_uom_id": 61, "product_id": None}, {"deductible_amount": 50}, {"deductible_amount": "100.01"}, {"tax_ids": [9, 8]}])
def test_add_reuses_strict_full_business_line_validation(changes, registry):
    current = request("invoice.lines.add")
    current["parameters"]["lines"][0].update(changes)
    with pytest.raises(CoreWriteError):
        validate_core_write_request("invoice.lines.add", current)
    if "tax_ids" not in changes:  # JSON Schema cannot express increasing ID order.
        with pytest.raises(InstanceValidationError):
            registry.validate_instance("schemas/v1/invoice.lines.add.request.schema.json", current)


@pytest.mark.parametrize("capability", CAPABILITIES)
@pytest.mark.parametrize("change", [{"id": 116}, {"state": "posted"}, {"move_type": "entry"}, {"source_id": 315}, {"line_ids": [316]}])
def test_bulk_result_is_bound_to_the_draft_invoice_and_selected_ids(capability, change):
    current = request(capability)
    key = _expected_idempotency_key(capability, validate_core_write_request(capability, current)[2], 7)
    port = FakePort(capability, result=_result("invoice.line.update", source_id=None, **change)) if "source_id" not in change else FakePort(capability, result=_result("invoice.line.update", **change))
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(port, capability, current, key, capability)
    assert caught.value.code == "failed_validation"
