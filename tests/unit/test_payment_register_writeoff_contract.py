from __future__ import annotations

from copy import deepcopy

import pytest
from test_core_writes import FakePort, _request

from odoo_accounting_cli_v4.capabilities.core_writes import (
    CoreWriteError,
    _expected_idempotency_key,
    execute_core_write,
    validate_core_write_request,
)
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

CAPABILITIES = ("receivable.payment.register", "payable.payment.register")
RECONCILE = {
    "amount": "99",
    "payment_difference_handling": "reconcile",
    "writeoff_account_id": 31,
}


@pytest.fixture(scope="module")
def registry():
    return load_registry()


@pytest.mark.parametrize("capability_id", CAPABILITIES)
@pytest.mark.parametrize(
    "extra",
    [
        pytest.param({}, id="legacy-full"),
        pytest.param({"amount": "99"}, id="legacy-partial"),
        pytest.param({"payment_difference_handling": "open"}, id="explicit-open-full"),
        pytest.param(
            {"amount": "99", "payment_difference_handling": "open"},
            id="explicit-open-partial",
        ),
        pytest.param(RECONCILE, id="reconcile-minimal"),
        pytest.param(
            {**RECONCILE, "writeoff_label": "收付款尾差"}, id="reconcile-label"
        ),
        pytest.param({**RECONCILE, "writeoff_label": "x" * 200}, id="label-boundary"),
        pytest.param(
            {**RECONCILE, "writeoff_label": "bank fee\nadjustment"},
            id="internal-whitespace",
        ),
    ],
)
def test_payment_registration_accepts_parameters_without_inserting_defaults(
    capability_id, extra, registry
):
    request = _request(capability_id)
    request["parameters"].update(extra)
    original = deepcopy(request)
    registry.validate_instance(
        f"schemas/v1/{capability_id}.request.schema.json", request
    )
    _, context, parameters = validate_core_write_request(capability_id, request)
    assert parameters == original["parameters"] and request == original
    expected_key = (
        None if "amount" in extra else f"{capability_id}:{parameters['move_id']}"
    )
    assert (
        _expected_idempotency_key(capability_id, parameters, context["company_id"])
        == expected_key
    )

    port = FakePort(capability_id)
    key = expected_key or "payment-writeoff:operation-1"
    result = execute_core_write(port, capability_id, request, key, capability_id)
    assert port.calls[0]["parameters"] == original["parameters"]
    assert port.calls[0]["idempotency_key"] == key
    assert result["result"]["source_id"] == parameters["move_id"]
    assert request == original


@pytest.mark.parametrize("capability_id", CAPABILITIES)
@pytest.mark.parametrize(
    "extra",
    [
        {"writeoff_account_id": 31},
        {"writeoff_label": "Fee"},
        {"amount": "99", "writeoff_account_id": 31},
        {"payment_difference_handling": "open", "writeoff_account_id": 31},
        {"payment_difference_handling": "open", "writeoff_label": "Fee"},
        {
            "amount": "99",
            "payment_difference_handling": "open",
            "writeoff_label": "Fee",
        },
        {"payment_difference_handling": "reconcile", "writeoff_account_id": 31},
        {"amount": "99", "payment_difference_handling": "reconcile"},
        {**RECONCILE, "unexpected": True},
        *(
            {**RECONCILE, "payment_difference_handling": value}
            for value in (None, True, 1, [], {}, "RECONCILE")
        ),
        *(
            {**RECONCILE, "writeoff_account_id": value}
            for value in (None, True, 0, -1, "31", 31.5)
        ),
        *(
            {**RECONCILE, "writeoff_label": value}
            for value in (
                None,
                True,
                "",
                " ",
                " Fee",
                "Fee ",
                "Fee\n",
                "\tFee",
                "\u00a0Fee",
                "x" * 201,
            )
        ),
        *(
            {**RECONCILE, "amount": value}
            for value in (None, True, 99, "0", "-1", "99.0", "099", "9.9e1")
        ),
    ],
)
def test_payment_registration_rejects_invalid_writeoff_combinations(
    capability_id, extra, registry
):
    request = _request(capability_id)
    request["parameters"].update(extra)
    original = deepcopy(request)
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(
            f"schemas/v1/{capability_id}.request.schema.json", request
        )
    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request(capability_id, request)
    assert caught.value.code == "invalid_request" and caught.value.exit_code == 2
    assert request == original


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_writeoff_account_id_retains_strict_python_integer_validation(capability_id):
    # JSON Schema treats 31.0 as an integer; the existing Python ID convention
    # still rejects floats before any write is dispatched.
    request = _request(capability_id)
    request["parameters"].update(RECONCILE, writeoff_account_id=31.0)
    port = FakePort(capability_id)
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(port, capability_id, request, "writeoff-1", capability_id)
    assert caught.value.code == "invalid_request" and port.calls == []
