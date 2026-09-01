from __future__ import annotations

from copy import deepcopy

import pytest

from odoo_accounting_cli_v4.capabilities.core_writes import (
    CoreWriteError,
    _expected_idempotency_key,
    execute_core_write,
    validate_core_write_request,
)
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

REQUEST_ID = "df462ab8-bb53-4914-87f7-48da17187c04"


def _request(capability_id, parameters):
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "zh_CN",
            "timezone": "Asia/Shanghai",
        },
        "parameters": deepcopy(parameters),
    }


class Port:
    user_id = 42

    def __init__(self, result):
        self.result = result

    def execute(self, **_kwargs):
        return {
            "user_id": 42,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "idempotent_replay": False,
            "result": self.result,
        }


def _result(**changes):
    result = {
        "model": "account.move",
        "id": 201,
        "name": "Draft 201",
        "state": "draft",
        "company_id": 7,
        "move_type": "out_invoice",
        "source_id": 101,
        "line_ids": [301, 302],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }
    result.update(changes)
    return result


@pytest.fixture(scope="module")
def registry():
    return load_registry()


@pytest.mark.parametrize(
    "capability_id,parameters,expected_key",
    [
        ("invoice.duplicate", {"move_id": 101}, None),
        (
            "invoice.type.switch",
            {"move_id": 101, "target_move_type": "out_refund"},
            "invoice.type.switch:101:out_refund",
        ),
    ],
)
def test_invoice_copy_type_requests_and_keys(
    capability_id, parameters, expected_key, registry
):
    request = _request(capability_id, parameters)
    _, context, normalized = validate_core_write_request(capability_id, request)
    assert normalized == parameters
    assert (
        _expected_idempotency_key(capability_id, normalized, context["company_id"])
        == expected_key
    )
    registry.validate_instance(
        f"schemas/v1/{capability_id}.request.schema.json", request
    )


@pytest.mark.parametrize(
    "target", ["out_invoice", "out_refund", "in_invoice", "in_refund"]
)
def test_invoice_type_switch_accepts_only_fixed_types(target):
    request = _request(
        "invoice.type.switch", {"move_id": 101, "target_move_type": target}
    )
    assert (
        validate_core_write_request("invoice.type.switch", request)[2][
            "target_move_type"
        ]
        == target
    )


@pytest.mark.parametrize("target", [None, "entry", "out_receipt", 1, True])
def test_invoice_type_switch_rejects_other_types(target, registry):
    request = _request(
        "invoice.type.switch", {"move_id": 101, "target_move_type": target}
    )
    with pytest.raises(CoreWriteError):
        validate_core_write_request("invoice.type.switch", request)
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(
            "schemas/v1/invoice.type.switch.request.schema.json", request
        )


@pytest.mark.parametrize(
    "capability_id,parameters,result",
    [
        ("invoice.duplicate", {"move_id": 101}, _result()),
        (
            "invoice.type.switch",
            {"move_id": 101, "target_move_type": "out_refund"},
            _result(id=101, source_id=101, move_type="out_refund"),
        ),
    ],
)
def test_invoice_copy_type_results(capability_id, parameters, result):
    request = _request(capability_id, parameters)
    _, context, normalized = validate_core_write_request(capability_id, request)
    key = _expected_idempotency_key(capability_id, normalized, context["company_id"])
    key = key or "duplicate-operation-0001"
    data = execute_core_write(Port(result), capability_id, request, key, capability_id)
    assert data["result"] == result


@pytest.mark.parametrize(
    "capability_id,parameters,change",
    [
        ("invoice.duplicate", {"move_id": 101}, {"id": 101}),
        ("invoice.duplicate", {"move_id": 101}, {"source_id": 102}),
        ("invoice.duplicate", {"move_id": 101}, {"state": "posted"}),
        (
            "invoice.type.switch",
            {"move_id": 101, "target_move_type": "out_refund"},
            {"id": 102},
        ),
        (
            "invoice.type.switch",
            {"move_id": 101, "target_move_type": "out_refund"},
            {"move_type": "out_invoice"},
        ),
        (
            "invoice.type.switch",
            {"move_id": 101, "target_move_type": "out_refund"},
            {"source_id": None},
        ),
    ],
)
def test_invoice_copy_type_rejects_mismatched_results(
    capability_id, parameters, change
):
    result = _result(
        **(
            {"id": 101, "source_id": 101, "move_type": parameters["target_move_type"]}
            if capability_id == "invoice.type.switch"
            else {}
        )
    )
    result.update(change)
    request = _request(capability_id, parameters)
    _, context, normalized = validate_core_write_request(capability_id, request)
    key = _expected_idempotency_key(capability_id, normalized, context["company_id"])
    key = key or "duplicate-operation-0001"
    with pytest.raises(CoreWriteError):
        execute_core_write(Port(result), capability_id, request, key, capability_id)
