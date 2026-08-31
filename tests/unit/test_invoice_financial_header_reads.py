from __future__ import annotations

import json

import pytest
import test_invoice_runtime as runtime_fixtures
import test_invoices as invoice_fixtures

from odoo_accounting_cli_v4.bridge import runtime
from odoo_accounting_cli_v4.capabilities.invoices import InvoiceError
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

FIELDS = ("partner_bank_id", "fiscal_position_id")
SCHEMA = "schemas/v1/invoice.get.response.schema.json"


@pytest.fixture(scope="module")
def registry():
    return load_registry()


@pytest.mark.parametrize(
    "bank_id,position_id", [(None, None), (12, 14), (12, None), (None, 14)]
)
def test_get_accepts_nullable_financial_reference_ids(bank_id, position_id, registry):
    invoice = invoice_fixtures._invoice()
    invoice.update(partner_bank_id=bank_id, fiscal_position_id=position_id)

    result = invoice_fixtures.get_invoice(
        invoice_fixtures.FakePort(invoice=invoice), invoice_fixtures._get_request()
    )

    assert result == invoice
    registry.validate_instance(
        SCHEMA, invoice_fixtures._success_response("invoice.get", result)
    )


@pytest.mark.parametrize("field", FIELDS)
@pytest.mark.parametrize(
    "value", [True, False, 0, -1, "12", 1.5, [], {"id": 12, "name": "secret"}]
)
def test_get_rejects_non_id_financial_references(field, value, registry):
    invoice = invoice_fixtures._invoice()
    invoice[field] = value

    with pytest.raises(InvoiceError) as caught:
        invoice_fixtures.get_invoice(
            invoice_fixtures.FakePort(invoice=invoice), invoice_fixtures._get_request()
        )
    assert caught.value.code == "failed_validation"
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(
            SCHEMA, invoice_fixtures._success_response("invoice.get", invoice)
        )


@pytest.mark.parametrize("field", FIELDS)
def test_get_requires_financial_reference_fields(field, registry):
    invoice = invoice_fixtures._invoice()
    invoice.pop(field)

    with pytest.raises(InvoiceError) as caught:
        invoice_fixtures.get_invoice(
            invoice_fixtures.FakePort(invoice=invoice), invoice_fixtures._get_request()
        )
    assert caught.value.code == "failed_validation"
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(
            SCHEMA, invoice_fixtures._success_response("invoice.get", invoice)
        )


@pytest.mark.parametrize("field", FIELDS)
def test_get_keeps_strict_python_integer_ids(field):
    invoice = invoice_fixtures._invoice()
    invoice[field] = 12.0

    with pytest.raises(InvoiceError) as caught:
        invoice_fixtures.get_invoice(
            invoice_fixtures.FakePort(invoice=invoice), invoice_fixtures._get_request()
        )
    assert caught.value.code == "failed_validation"


@pytest.mark.parametrize(
    "bank,position,expected",
    [
        (False, None, (None, None)),
        (12, 14, (12, 14)),
        ([12, "private account number"], (14, "private fiscal name"), (12, 14)),
    ],
)
def test_runtime_get_only_exposes_ids_without_new_related_reads(
    bank, position, expected
):
    env = runtime_fixtures._Environment("get")
    raw = env.models["account.move"].responses[0][0]
    for field in ("journal_id", "company_id", "currency_id", "partner_id"):
        raw[field] = raw[field][0]
    raw.update(partner_bank_id=bank, fiscal_position_id=position)

    result = runtime._dispatch(
        env,
        runtime_fixtures.GET_ACTION,
        runtime_fixtures._payload(runtime_fixtures.GET_ACTION),
        7,
    )

    assert tuple(result["invoice"][field] for field in FIELDS) == expected
    assert "private account number" not in json.dumps(result)
    assert "private fiscal name" not in json.dumps(result)
    assert ("read_options", "account.move", {"load": None}) in env.calls
    assert not any(
        call[0] == "model"
        and call[1] in {"res.partner.bank", "account.fiscal.position"}
        for call in env.calls
    )


@pytest.mark.parametrize("field", FIELDS)
@pytest.mark.parametrize(
    "value", [True, 0, -1, "12", 1.5, [], {"id": 12}, [0, "private"]]
)
def test_runtime_get_rejects_malformed_financial_references(field, value):
    env = runtime_fixtures._Environment("get")
    env.models["account.move"].responses[0][0][field] = value

    with pytest.raises(runtime.RuntimeFailure) as caught:
        runtime._dispatch(
            env,
            runtime_fixtures.GET_ACTION,
            runtime_fixtures._payload(runtime_fixtures.GET_ACTION),
            7,
        )
    assert caught.value.code == "odoo_runtime_error"


@pytest.mark.parametrize("field", [*FIELDS, "unexpected"])
def test_runtime_get_retains_exact_header_shape(field):
    env = runtime_fixtures._Environment("get")
    raw = env.models["account.move"].responses[0][0]
    if field == "unexpected":
        raw[field] = True
    else:
        raw.pop(field)

    with pytest.raises(runtime.RuntimeFailure) as caught:
        runtime._dispatch(
            env,
            runtime_fixtures.GET_ACTION,
            runtime_fixtures._payload(runtime_fixtures.GET_ACTION),
            7,
        )
    assert caught.value.code == "odoo_runtime_error"


def test_search_response_contract_stays_unchanged(registry):
    schema = registry.load_schema("schemas/v1/invoice.search.response.schema.json")
    assert not set(FIELDS) & set(schema["$defs"]["item"]["properties"])
    assert not set(FIELDS) & set(runtime._INVOICE_HEADER_FIELDS)
    row = invoice_fixtures._header()
    result = invoice_fixtures.search_invoices(
        invoice_fixtures.FakePort(rows=[row]), invoice_fixtures._search_request()
    )
    assert result["items"] == [row]
