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

CAPABILITY = "invoice.lines.remove"


@pytest.fixture(scope="module")
def registry():
    return load_registry()


def request(**parameters):
    value = _request("invoice.line.delete")
    value["parameters"] = {"move_id": 115, "line_ids": [316, 315], **parameters}
    return value


def key_for(value):
    return _expected_idempotency_key(CAPABILITY, validate_core_write_request(CAPABILITY, value)[2], 7)


@pytest.mark.parametrize("move_type", ["out_invoice", "out_refund", "in_invoice", "in_refund"])
@pytest.mark.parametrize("remaining", [[], [317, 318]])
def test_remove_uses_one_fixed_call_and_accepts_empty_or_surviving_native_graph(move_type, remaining, registry):
    value = request()
    normalized = validate_core_write_request(CAPABILITY, value)[2]
    assert normalized == {"move_id": 115, "line_ids": [315, 316]}
    registry.validate_instance(f"schemas/v1/{CAPABILITY}.request.schema.json", value)
    result = _result("invoice.line.update", move_type=move_type, source_id=None, line_ids=remaining)
    port = FakePort(CAPABILITY, result=result)
    key = key_for(value)
    data = execute_core_write(port, CAPABILITY, value, key, CAPABILITY)
    assert len(port.calls) == 1 and port.calls[0]["parameters"] == normalized
    assert not data["idempotent_replay"] and data["result"] == result
    response = _success_response("invoice.line.update")
    response.update({"capability": CAPABILITY, "data": data})
    response["audit"]["idempotency_key"] = key
    registry.validate_instance(f"schemas/v1/{CAPABILITY}.response.schema.json", response)


def test_remove_normalizes_id_order_without_mutating_input_and_binds_complete_target():
    value = request()
    original = deepcopy(value)
    normalized = validate_core_write_request(CAPABILITY, value)[2]
    digest = hashlib.sha256(json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()[:32]
    assert key_for(value) == f"{CAPABILITY}:115:{digest}" == key_for(request(line_ids=[315, 316]))
    assert value == original
    assert key_for(request(move_id=116)) != key_for(value)
    assert key_for(request(line_ids=[315])) != key_for(value)


@pytest.mark.parametrize("count", [1, 200])
def test_remove_accepts_exact_request_limits(count, registry):
    value = request(line_ids=list(range(count, 0, -1)))
    assert validate_core_write_request(CAPABILITY, value)[2]["line_ids"] == list(range(1, count + 1))
    registry.validate_instance(f"schemas/v1/{CAPABILITY}.request.schema.json", value)


@pytest.mark.parametrize("parameters", [None, [], {}, {"move_id": 115}, {"line_ids": [315]}, {"move_id": 115, "line_ids": [315], "expected_line_ids": []}, {"move_id": True, "line_ids": [315]}, {"move_id": None, "line_ids": [315]}, {"move_id": 0, "line_ids": [315]}, {"move_id": "115", "line_ids": [315]}, {"move_id": 1.5, "line_ids": [315]}])
def test_remove_rejects_invalid_or_unfrozen_parameter_shapes(parameters, registry):
    value = request()
    value["parameters"] = parameters
    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request(CAPABILITY, value)
    assert caught.value.code == "invalid_request" and caught.value.exit_code == 2
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(f"schemas/v1/{CAPABILITY}.request.schema.json", value)


@pytest.mark.parametrize("identifiers", [None, {}, "315", [], [315, 315], [True], [False], [0], [-1], ["315"], [1.5], [{}], [[]], list(range(1, 202))])
def test_remove_rejects_invalid_identifier_arrays(identifiers, registry):
    value = request(line_ids=identifiers)
    with pytest.raises(CoreWriteError):
        validate_core_write_request(CAPABILITY, value)
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(f"schemas/v1/{CAPABILITY}.request.schema.json", value)


@pytest.mark.parametrize("parameters", [{"move_id": 115.0}, {"line_ids": [315.0]}])
def test_sdk_ids_are_strict_even_for_integral_floats(parameters):
    with pytest.raises(CoreWriteError):
        validate_core_write_request(CAPABILITY, request(**parameters))


def test_remove_rejects_arbitrary_key_before_port_call():
    port = FakePort(CAPABILITY, result=_result("invoice.line.update", source_id=None, line_ids=[]))
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(port, CAPABILITY, request(), "caller-selected-key", CAPABILITY)
    assert caught.value.code == "invalid_idempotency_key" and not port.calls


@pytest.mark.parametrize("change", [{"model": "res.partner"}, {"id": 116}, {"company_id": 8}, {"state": "posted"}, {"move_type": "entry"}, {"source_id": 315}, {"line_ids": [315, 317]}, {"line_ids": [316]}, {"line_ids": [317, 317]}, {"partial_reconcile_ids": [100]}, {"full_reconcile_id": 100}])
def test_remove_result_is_bound_to_parent_and_requires_every_selected_id_absent(change):
    result = _result("invoice.line.update", source_id=None, line_ids=[])
    result.update(change)
    value = request()
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(FakePort(CAPABILITY, result=result), CAPABILITY, value, key_for(value), CAPABILITY)
    assert caught.value.code == "failed_validation"


def test_remove_cannot_claim_replay_for_already_absent_lines():
    value = request()
    port = FakePort(CAPABILITY, result=_result("invoice.line.update", source_id=None, line_ids=[]), idempotent_replay=True)
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(port, CAPABILITY, value, key_for(value), CAPABILITY)
    assert caught.value.code == "failed_validation"


def test_legacy_single_delete_request_and_key_remain_unchanged():
    value = _request("invoice.line.delete")
    assert validate_core_write_request("invoice.line.delete", value)[2] == value["parameters"]
    assert _expected_idempotency_key("invoice.line.delete", value["parameters"], 7) == "invoice.line.delete:115:315"
