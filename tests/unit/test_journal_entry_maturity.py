from __future__ import annotations

from copy import deepcopy

import pytest
from test_core_writes import FakePort, _key, _request
from test_document_lifecycle_writes import _key as _content_key

from odoo_accounting_cli_v4.capabilities.core_writes import (
    CoreWriteError,
    _expected_idempotency_key,
    execute_core_write,
    validate_core_write_request,
)
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

CAPABILITIES = ("journal_entry.create", "journal_entry.lines.replace")


@pytest.fixture(scope="module")
def registry():
    return load_registry()


@pytest.mark.parametrize("capability_id", CAPABILITIES)
@pytest.mark.parametrize(
    "changes",
    [
        {},
        {"date_maturity": None},
        {"date_maturity": "2026-08-24"},
        {"date_maturity": "2024-02-29"},
        {"date_maturity": "2026-09-30"},
    ],
)
def test_maturity_passes_through_without_defaults_or_date_order_rules(
    capability_id, changes, registry
):
    request = _request(capability_id)
    request["parameters"]["lines"][0].update(changes)
    original = deepcopy(request)
    _, context, parameters = validate_core_write_request(capability_id, request)
    assert parameters == original["parameters"]
    assert "date_maturity" not in parameters["lines"][1]
    registry.validate_instance(
        f"schemas/v1/{capability_id}.request.schema.json", request
    )
    key = (
        _content_key(capability_id, parameters)
        if capability_id.endswith(".lines.replace")
        else _key(capability_id)
    )
    expected = _expected_idempotency_key(
        capability_id, parameters, context["company_id"]
    )
    assert expected is None if capability_id.endswith(".create") else expected == key
    port = FakePort(capability_id)
    execute_core_write(port, capability_id, request, key, capability_id)
    assert port.calls[0]["parameters"] == original["parameters"]
    assert request == original


@pytest.mark.parametrize("capability_id", CAPABILITIES)
@pytest.mark.parametrize(
    "value",
    [
        True,
        False,
        1,
        "",
        "2026-8-1",
        "2026-02-30",
        "2026-08-31T00:00:00",
        "2026-08-31\n",
        " 2026-08-31",
        [],
        {},
    ],
)
def test_maturity_rejects_noncanonical_dates_and_non_date_types(
    capability_id, value, registry
):
    request = _request(capability_id)
    request["parameters"]["lines"][0]["date_maturity"] = value
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(
            f"schemas/v1/{capability_id}.request.schema.json", request
        )
    port = FakePort(capability_id)
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            port, capability_id, request, _key(capability_id), capability_id
        )
    assert caught.value.code == "invalid_request" and caught.value.exit_code == 2
    assert port.calls == []


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_maturity_coexists_with_currency_and_analytic_distribution(
    capability_id, registry
):
    request = _request(capability_id)
    request["parameters"]["lines"][0].update(
        date_maturity="2026-09-30",
        currency_id=6,
        amount_currency="100.00",
        analytic_distribution={"21": "100"},
    )
    request["parameters"]["lines"][1].update(
        date_maturity=None,
        currency_id=None,
        amount_currency=None,
        analytic_distribution=None,
    )
    _, _, parameters = validate_core_write_request(capability_id, request)
    assert parameters == request["parameters"]
    registry.validate_instance(
        f"schemas/v1/{capability_id}.request.schema.json", request
    )


@pytest.mark.parametrize("capability_id", CAPABILITIES)
@pytest.mark.parametrize(
    "changes",
    [
        {"debit": "-1"},
        {"debit": "99"},
        {"credit": "1"},
        {"currency_id": 6},
        {"currency_id": 6, "amount_currency": "-100"},
        {"analytic_distribution": {"21": True}},
        {"unknown": 1},
    ],
)
def test_maturity_keeps_existing_line_guards(capability_id, changes):
    request = _request(capability_id)
    request["parameters"]["lines"][0].update(date_maturity="2026-09-30", **changes)
    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request(capability_id, request)
    assert caught.value.code == "invalid_request"


def test_replacement_keys_distinguish_omitted_null_and_each_explicit_maturity():
    capability_id = "journal_entry.lines.replace"
    original = _request(capability_id)
    old_key = _key(capability_id)
    keys = set()
    for changes in (
        {},
        {"date_maturity": None},
        {"date_maturity": "2026-09-30"},
        {"date_maturity": "2026-10-01"},
    ):
        request = deepcopy(original)
        request["parameters"]["lines"][0].update(changes)
        _, context, parameters = validate_core_write_request(capability_id, request)
        key = _content_key(capability_id, parameters)
        assert (
            _expected_idempotency_key(capability_id, parameters, context["company_id"])
            == key
        )
        keys.add(key)
        if not changes:
            assert key == old_key
            continue
        port = FakePort(capability_id)
        with pytest.raises(CoreWriteError) as caught:
            execute_core_write(port, capability_id, request, old_key, capability_id)
        assert caught.value.code == "invalid_idempotency_key"
        assert port.calls == []
    assert len(keys) == 4
