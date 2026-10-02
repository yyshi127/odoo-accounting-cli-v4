"""Optional native invoice line input projections preserve legacy read shapes."""
from __future__ import annotations

import pytest
import test_invoice_runtime as native
import test_invoices as sdk

from odoo_accounting_cli_v4.bridge import runtime
from odoo_accounting_cli_v4.capabilities import invoices
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry


@pytest.fixture(scope="module")
def registry():
    return load_registry()


@pytest.mark.parametrize("extra", [{}, {"product_uom_id": 7}, {"product_uom_id": None},
                                  {"deductible_amount": "0"}, {"deductible_amount": "50.001"},
                                  {"product_uom_id": 7, "deductible_amount": "100.00"}])
def test_sdk_accepts_independent_optional_line_inputs(extra, registry):
    row = sdk._invoice()
    row["lines"][0].update(extra)
    assert invoices._validate_invoice(row, company_id=7, invoice_id=row["id"]) == row
    registry.validate_instance("schemas/v1/invoice.get.response.schema.json", sdk._success_response("invoice.get", row))


@pytest.mark.parametrize("extra", [{"product_uom_id": True}, {"product_uom_id": 0},
                                  {"product_uom_id": "7"}, {"deductible_amount": True},
                                  {"deductible_amount": 50}, {"deductible_amount": None},
                                  {"deductible_amount": "-0"}, {"deductible_amount": "100.01"},
                                  {"deductible_amount": "1e1"}, {"deductible_amount": "NaN"},
                                  {"deductible_amount": "+1"}, {"deductible_amount": "50\n"},
                                  {"deductible_percent": "50"}])
def test_sdk_rejects_malformed_or_unknown_line_inputs(extra, registry):
    row = sdk._invoice()
    row["lines"][0].update(extra)
    with pytest.raises(invoices.InvoiceError):
        invoices._validate_invoice(row, company_id=7, invoice_id=row["id"])
    with pytest.raises(InstanceValidationError):
        registry.validate_instance("schemas/v1/invoice.get.response.schema.json", sdk._success_response("invoice.get", row))


@pytest.mark.parametrize("extra,expected", [({}, {}), ({"product_uom_id": [7, "Pack"]}, {"product_uom_id": 7}),
                                          ({"product_uom_id": False}, {"product_uom_id": None}),
                                          ({"deductible_amount": 50.001}, {"deductible_amount": "50.001"}),
                                          ({"product_uom_id": 7, "deductible_amount": 100.0},
                                           {"product_uom_id": 7, "deductible_amount": "100"})])
def test_runtime_reads_only_available_native_fields_without_extra_model_gate(extra, expected):
    env = native._Environment("get")
    model = env.models["account.move.line"]
    model._fields.update(extra)
    model.responses[0][0].update(extra)
    result = runtime._dispatch(env, native.GET_ACTION, native._payload(native.GET_ACTION), 7)
    line = result["invoice"]["lines"][0]
    assert {key: line[key] for key in expected} == expected
    assert set(line) & {"product_uom_id", "deductible_amount"} == set(expected)
    requested = native._search_calls(env, "account.move.line")[0][3]
    assert set(requested) == set(native.INVOICE_LINE_FIELDS) | set(extra)
    assert not any(len(call) > 1 and call[1] == "uom.uom" for call in env.calls)


@pytest.mark.parametrize("value", [-1, 101])
def test_runtime_rejects_out_of_range_native_percentage(value):
    env = native._Environment("get")
    model = env.models["account.move.line"]
    model._fields.add("deductible_amount")
    model.responses[0][0]["deductible_amount"] = value
    with pytest.raises(runtime.RuntimeFailure):
        runtime._dispatch(env, native.GET_ACTION, native._payload(native.GET_ACTION), 7)
