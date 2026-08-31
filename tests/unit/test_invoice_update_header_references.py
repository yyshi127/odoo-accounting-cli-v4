from __future__ import annotations

from copy import deepcopy

import pytest
from test_document_lifecycle_writes import _key, _Port, _request

from odoo_accounting_cli_v4.capabilities.core_writes import (
    CoreWriteError,
    _expected_idempotency_key,
    execute_core_write,
    validate_core_write_request,
)
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

CAPABILITY = "invoice.update"
SCHEMA = "schemas/v1/invoice.update.request.schema.json"


@pytest.fixture(scope="module")
def registry():
    return load_registry()


@pytest.mark.parametrize(
    "changes",
    [
        {"reference": "PO-114"},
        {"journal_id": 1},
        {"currency_id": 6},
        {"journal_id": 4, "currency_id": 6},
        {
            "journal_id": 4,
            "currency_id": 6,
            "partner_id": 21,
            "date": "2026-08-31",
            "invoice_date": "2026-08-25",
            "payment_term_id": None,
            "reference": "Updated invoice",
            "payment_reference": None,
        },
        {"currency_id": 6, "invoice_date_due": None, "reference": None},
    ],
)
@pytest.mark.parametrize("replay", [False, True])
def test_header_references_pass_through_without_defaults(changes, replay, registry):
    request = _request(CAPABILITY, {"move_id": 101, "changes": changes})
    original = deepcopy(request)
    _, context, parameters = validate_core_write_request(CAPABILITY, request)
    assert parameters == original["parameters"]
    registry.validate_instance(SCHEMA, request)
    key = _key(CAPABILITY, parameters)
    assert (
        _expected_idempotency_key(CAPABILITY, parameters, context["company_id"]) == key
    )

    port = _Port(CAPABILITY, idempotent_replay=replay)
    data = execute_core_write(port, CAPABILITY, request, key, CAPABILITY)
    assert data["idempotent_replay"] is replay
    assert port.calls[0]["parameters"] == original["parameters"]
    assert request == original


@pytest.mark.parametrize("field", ["journal_id", "currency_id"])
@pytest.mark.parametrize("value", [None, True, False, 0, -1, "4", 1.5, [], {}])
def test_header_references_reject_invalid_ids_before_dispatch(field, value, registry):
    parameters = {"move_id": 101, "changes": {field: value}}
    request = _request(CAPABILITY, parameters)
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(SCHEMA, request)
    port = _Port(CAPABILITY)
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            port, CAPABILITY, request, _key(CAPABILITY, parameters), CAPABILITY
        )
    assert caught.value.code == "invalid_request" and caught.value.exit_code == 2
    assert port.calls == []


@pytest.mark.parametrize("field", ["journal_id", "currency_id"])
def test_header_reference_validator_retains_strict_python_integer_ids(field):
    # JSON Schema treats integral floats as integers; the public validator is stricter.
    request = _request(CAPABILITY, {"move_id": 101, "changes": {field: 4.0}})
    with pytest.raises(CoreWriteError, match="positive integer"):
        validate_core_write_request(CAPABILITY, request)


@pytest.mark.parametrize(
    "changes",
    [
        {"unknown": 1},
        {"partner_id": True},
        {"date": "2026-02-30"},
        {"reference": ""},
        {"invoice_date_due": None, "payment_term_id": None},
    ],
)
def test_header_references_keep_existing_change_guards(changes, registry):
    request = _request(
        CAPABILITY,
        {"move_id": 101, "changes": {"journal_id": 4, "currency_id": 6, **changes}},
    )
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(SCHEMA, request)
    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request(CAPABILITY, request)
    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize("field", ["journal_id", "currency_id"])
def test_header_reference_keys_bind_each_value_and_ignore_field_order(field):
    parameters = {
        "move_id": 101,
        "changes": {"journal_id": 4, "currency_id": 6, "reference": "发票参考"},
    }
    key = _key(CAPABILITY, parameters)
    reordered = {**parameters, "changes": dict(reversed(parameters["changes"].items()))}
    assert _key(CAPABILITY, reordered) == key
    execute_core_write(
        _Port(CAPABILITY), CAPABILITY, _request(CAPABILITY, reordered), key, CAPABILITY
    )

    changed = deepcopy(parameters)
    changed["changes"][field] += 1
    assert _key(CAPABILITY, changed) != key
    port = _Port(CAPABILITY)
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            port, CAPABILITY, _request(CAPABILITY, changed), key, CAPABILITY
        )
    assert caught.value.code == "invalid_idempotency_key"
    assert port.calls == []


@pytest.mark.parametrize("confirmation", [None, "journal_entry.update"])
def test_header_reference_update_keeps_explicit_confirmation(confirmation):
    parameters = {"move_id": 101, "changes": {"journal_id": 4, "currency_id": 6}}
    port = _Port(CAPABILITY)
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            port,
            CAPABILITY,
            _request(CAPABILITY, parameters),
            _key(CAPABILITY, parameters),
            confirmation,
        )
    assert caught.value.code == "confirmation_required"
    assert port.calls == []


def test_header_reference_registry_declares_read_dependencies(registry):
    descriptor = registry.describe(CAPABILITY)
    assert {"account.journal", "res.currency"} <= set(descriptor["source"]["models"])
    assert {
        "account/models/account_journal.py",
        "_references/base/models/res_currency.py",
    } <= set(descriptor["source"]["locations"])
    assert {"account.journal:read", "res.currency:read"} <= set(
        descriptor["requirements"]["acl"]
    )
