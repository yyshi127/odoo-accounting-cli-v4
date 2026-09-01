from __future__ import annotations

import hashlib
import json
from copy import deepcopy

import pytest
import test_core_writes as fixtures

from odoo_accounting_cli_v4.capabilities.core_writes import (
    CoreWriteError,
    _expected_idempotency_key,
    execute_core_write,
    validate_core_write_request,
)
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

CAPABILITIES = ("receivable.payment.register", "payable.payment.register")


@pytest.fixture(scope="module")
def registry():
    return load_registry()


def _request(capability_id, parameters):
    request = fixtures._request(capability_id)
    request["parameters"] = deepcopy(parameters)
    return request


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_single_payment_registration_contract_remains_compatible(
    capability_id, registry
):
    request = fixtures._request(capability_id)
    _, context, parameters = validate_core_write_request(capability_id, request)
    assert parameters == request["parameters"]
    assert _expected_idempotency_key(
        capability_id, parameters, context["company_id"]
    ) == (f"{capability_id}:{parameters['move_id']}")
    registry.validate_instance(
        f"schemas/v1/{capability_id}.request.schema.json", request
    )


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_many_payment_registration_sorts_ids_and_uses_parameter_digest(
    capability_id, registry
):
    request = _request(
        capability_id,
        {"move_ids": [105, 101, 103], "journal_id": 7, "payment_date": "2026-09-01"},
    )
    _, context, parameters = validate_core_write_request(capability_id, request)
    assert parameters["move_ids"] == [101, 103, 105]
    canonical = json.dumps(
        parameters, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    digest = hashlib.sha256(canonical).hexdigest()[:32]
    assert _expected_idempotency_key(
        capability_id, parameters, context["company_id"]
    ) == (f"{capability_id}:7:{digest}")
    registry.validate_instance(
        f"schemas/v1/{capability_id}.request.schema.json", request
    )


@pytest.mark.parametrize("capability_id", CAPABILITIES)
@pytest.mark.parametrize(
    "parameters",
    [
        {"move_ids": [1], "journal_id": 7, "payment_date": "2026-09-01"},
        {"move_ids": [1, 1], "journal_id": 7, "payment_date": "2026-09-01"},
        {
            "move_ids": list(range(1, 102)),
            "journal_id": 7,
            "payment_date": "2026-09-01",
        },
        {
            "move_id": 1,
            "move_ids": [1, 2],
            "journal_id": 7,
            "payment_date": "2026-09-01",
        },
        {
            "move_ids": [1, 2],
            "journal_id": 7,
            "payment_date": "2026-09-01",
            "amount": "1",
        },
        {
            "move_ids": [1, 2],
            "journal_id": 7,
            "payment_date": "2026-09-01",
            "payment_difference_handling": "open",
        },
        {
            "move_ids": [1, 2],
            "journal_id": 7,
            "payment_date": "2026-09-01",
            "writeoff_account_id": 9,
        },
    ],
)
def test_many_payment_registration_rejects_invalid_shapes(
    capability_id, parameters, registry
):
    request = _request(capability_id, parameters)
    with pytest.raises(CoreWriteError):
        validate_core_write_request(capability_id, request)
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(
            f"schemas/v1/{capability_id}.request.schema.json", request
        )


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_many_payment_result_requires_grouped_reconciled_payment(capability_id):
    request = _request(
        capability_id,
        {"move_ids": [101, 102], "journal_id": 7, "payment_date": "2026-09-01"},
    )
    _, context, parameters = validate_core_write_request(capability_id, request)
    key = _expected_idempotency_key(capability_id, parameters, context["company_id"])
    result = fixtures._result(
        capability_id, source_id=None, reconciled=True, line_ids=[501, 502]
    )
    data = execute_core_write(
        fixtures.FakePort(capability_id, result=result),
        capability_id,
        request,
        key,
        capability_id,
    )
    assert data["result"]["source_id"] is None


@pytest.mark.parametrize(
    "change", [{"source_id": 101}, {"reconciled": False}, {"line_ids": []}]
)
def test_many_payment_result_rejects_single_or_incomplete_result(change):
    capability_id = "receivable.payment.register"
    request = _request(
        capability_id,
        {"move_ids": [101, 102], "journal_id": 7, "payment_date": "2026-09-01"},
    )
    _, context, parameters = validate_core_write_request(capability_id, request)
    key = _expected_idempotency_key(capability_id, parameters, context["company_id"])
    result = fixtures._result(
        capability_id, source_id=None, reconciled=True, line_ids=[501, 502]
    )
    result.update(change)
    with pytest.raises(CoreWriteError):
        execute_core_write(
            fixtures.FakePort(capability_id, result=result),
            capability_id,
            request,
            key,
            capability_id,
        )
