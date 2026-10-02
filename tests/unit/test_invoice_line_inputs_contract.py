from __future__ import annotations

import io
import json
from copy import deepcopy

import pytest
from test_core_writes import FakePort, _request, _success_response

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.capabilities.core_writes import (
    CoreWriteError,
    _expected_idempotency_key,
    execute_core_write,
    validate_core_write_request,
)
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

CREATES = ("customer_invoice.create", "vendor_bill.create")
REFUNDS = ("customer_credit_note.create", "vendor_refund.create")
WRITES = (*CREATES, "invoice.line.create", "invoice.line.update", "invoice.lines.replace", *REFUNDS)
LEGACY_KEYS = {
    "invoice.line.create": "invoice.line.create:115:0d68ec10654b677f8d606a428ac57e80",
    "invoice.line.update": "invoice.line.update:115:315:270412860549cb5497cd84dca91754e3",
    "invoice.lines.replace": "invoice.lines.replace:115:481c58cb70da00b71014dbdcb80d8c2a",
}


@pytest.fixture(scope="module")
def registry():
    return load_registry()


def line(value):
    parameters = value["parameters"]
    return parameters.get("line", parameters.get("changes", parameters.get("lines", [{}])[0]))


def request(capability, values):
    value = _request(capability)
    if capability in REFUNDS:
        value["parameters"]["lines"] = _request("invoice.lines.replace")["parameters"]["lines"]
    if "product_uom_id" in values:
        line(value)["product_id"] = 41
    line(value).update(deepcopy(values))
    return value


@pytest.mark.parametrize("capability", WRITES)
@pytest.mark.parametrize("values", [
    {"product_uom_id": 61},
    {"deductible_amount": "0"},
    {"deductible_amount": "100"},
    {"deductible_amount": "50.0"},
    {"deductible_amount": "50.001"},
    {"product_uom_id": 61, "deductible_amount": "50.001"},
])
def test_native_line_inputs_are_independent_and_keep_caller_text(capability, values, registry):
    value = request(capability, values)
    original = deepcopy(value)
    registry.validate_instance(f"schemas/v1/{capability}.request.schema.json", value)
    normalized = validate_core_write_request(capability, value)[2]
    assert normalized == original["parameters"] and value == original
    assert {key for key in line(value) if key in {"product_uom_id", "deductible_amount"}} == set(values)
    key = _expected_idempotency_key(capability, normalized, 7) or "invoice-line-inputs-round-1"
    port = FakePort(capability)
    data = execute_core_write(port, capability, value, key, capability)
    assert port.calls[0]["parameters"] == normalized and "items" not in data["result"]
    response = _success_response(capability)
    response["data"] = data
    response["audit"]["idempotency_key"] = key
    registry.validate_instance(f"schemas/v1/{capability}.response.schema.json", response)


@pytest.mark.parametrize("capability", WRITES)
@pytest.mark.parametrize("values", [
    {"product_uom_id": None}, {"product_uom_id": True}, {"product_uom_id": 0},
    {"product_uom_id": "61"}, {"product_uom_id": 1.5}, {"product_uom_id": {}},
    {"product_uom_id": []}, {"deductible_amount": None}, {"deductible_amount": True},
    {"deductible_amount": 50}, {"deductible_amount": 50.0}, {"deductible_amount": {}},
    {"deductible_amount": []}, {"deductible_amount": "-0"}, {"deductible_amount": "100.01"},
    {"deductible_amount": "1e2"}, {"deductible_amount": "+50"}, {"deductible_amount": "50\n"},
    {"unknown_line_input": 61},
])
def test_invalid_line_inputs_are_cleanly_rejected_by_sdk_and_schema(capability, values, registry):
    value = request(capability, values)
    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request(capability, value)
    assert caught.value.code == "invalid_request" and caught.value.exit_code == 2
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(f"schemas/v1/{capability}.request.schema.json", value)


@pytest.mark.parametrize("text", ["", " 50", "50 ", ".5", "50.", "00", "NaN", "Infinity", "-1", "101", "0." + "0" * 255])
def test_percentage_uses_the_existing_bounded_unsigned_decimal_contract(text, registry):
    value = request("vendor_bill.create", {"deductible_amount": text})
    with pytest.raises(CoreWriteError):
        validate_core_write_request("vendor_bill.create", value)
    with pytest.raises(InstanceValidationError):
        registry.validate_instance("schemas/v1/vendor_bill.create.request.schema.json", value)


@pytest.mark.parametrize("capability", WRITES)
def test_integral_float_unit_is_not_an_sdk_integer(capability):
    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request(capability, request(capability, {"product_uom_id": 61.0}))
    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize("capability", WRITES)
def test_explicit_unit_and_explicit_null_product_are_incompatible(capability, registry):
    value = request(capability, {"product_uom_id": 61, "product_id": None})
    with pytest.raises(CoreWriteError):
        validate_core_write_request(capability, value)
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(f"schemas/v1/{capability}.request.schema.json", value)


@pytest.mark.parametrize("capability", CREATES)
def test_create_unit_requires_an_explicit_product(capability, registry):
    value = request(capability, {"product_uom_id": 61})
    line(value).pop("product_id")
    with pytest.raises(CoreWriteError):
        validate_core_write_request(capability, value)
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(f"schemas/v1/{capability}.request.schema.json", value)


def test_partial_unit_only_patch_keeps_native_product_lookup_for_runtime(registry):
    value = _request("invoice.line.update")
    value["parameters"]["changes"] = {"product_uom_id": 61}
    assert validate_core_write_request("invoice.line.update", value)[2] == value["parameters"]
    registry.validate_instance("schemas/v1/invoice.line.update.request.schema.json", value)


@pytest.mark.parametrize("capability", WRITES)
def test_omission_keeps_legacy_normalization_keys_and_response_shape(capability, registry):
    value = _request(capability)
    original = deepcopy(value)
    normalized = validate_core_write_request(capability, value)[2]
    assert normalized == original["parameters"] and value == original
    assert _expected_idempotency_key(capability, normalized, 7) == LEGACY_KEYS.get(capability)
    registry.validate_instance(f"schemas/v1/{capability}.request.schema.json", value)
    registry.validate_instance(f"schemas/v1/{capability}.response.schema.json", _success_response(capability))


@pytest.mark.parametrize("capability", ("invoice.line.create", "invoice.line.update", "invoice.lines.replace"))
def test_existing_content_keys_bind_each_explicit_new_field(capability):
    baseline = validate_core_write_request(capability, request(capability, {}))[2]
    old_key = _expected_idempotency_key(capability, baseline, 7)
    for values in ({"product_uom_id": 61}, {"deductible_amount": "50"}, {"deductible_amount": "50.0"}):
        normalized = validate_core_write_request(capability, request(capability, values))[2]
        assert _expected_idempotency_key(capability, normalized, 7) != old_key


@pytest.mark.parametrize("capability", REFUNDS)
@pytest.mark.parametrize("custom_lines", [False, True])
def test_full_native_refund_batch_stays_unchanged_and_rejects_custom_lines(capability, custom_lines, registry):
    value = _request(capability)
    value["parameters"].pop("move_id")
    value["parameters"]["move_ids"] = [12, 11]
    if custom_lines:
        value["parameters"]["lines"] = request(capability, {"product_uom_id": 61, "deductible_amount": "50"})["parameters"]["lines"]
        with pytest.raises(CoreWriteError):
            validate_core_write_request(capability, value)
        with pytest.raises(InstanceValidationError):
            registry.validate_instance(f"schemas/v1/{capability}.request.schema.json", value)
    else:
        registry.validate_instance(f"schemas/v1/{capability}.request.schema.json", value)
        assert validate_core_write_request(capability, value)[2] == {**value["parameters"], "move_ids": [11, 12]}


@pytest.mark.parametrize("capability", WRITES)
def test_existing_fixed_cli_accepts_extended_line_contract(capability, registry, monkeypatch):
    value = request(capability, {"product_uom_id": 61, "deductible_amount": "100"})
    normalized = validate_core_write_request(capability, value)[2]
    key = _expected_idempotency_key(capability, normalized, 7) or "invoice-line-inputs-cli-1"
    port = FakePort(capability)
    monkeypatch.setattr(cli, "load_registry", lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    code = cli.main(["write", "run", capability, "--request", "-", "--idempotency-key", key, "--confirm", capability],
                    stdin=io.StringIO(json.dumps(value)), stdout=stdout, stderr=stderr, port_factory=lambda *_args: port)
    response = json.loads(stdout.getvalue())
    assert code == 0 and response["success"] and not stderr.getvalue(), response
    assert response["odoo"]["model"] == "account.move"
    assert response["odoo"]["record_ids"] == [response["data"]["result"]["id"]]
    assert port.calls[0]["parameters"] == normalized
