"""Backward-compatible optional native template policy projection."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from test_product_accounting_profile import FakePort, _data, _request

from odoo_accounting_cli_v4.capabilities.product_accounting_profile import (
    ProductAccountingProfileError,
    get_product_accounting_profile,
)


@pytest.mark.parametrize("policies", [
    {}, {"invoice_policy": None}, {"purchase_method": None},
    {"invoice_policy": "order"}, {"invoice_policy": "delivery"},
    {"purchase_method": "purchase"}, {"purchase_method": "receive"},
    {"invoice_policy": "delivery", "purchase_method": "receive"},
    {"invoice_policy": None, "purchase_method": None},
])
def test_optional_policies_are_independent_and_preserve_old_shape(policies):
    data = {**_data(), **policies}
    port = FakePort(data=data)
    assert get_product_accounting_profile(port, _request()) == data
    assert port.calls == [{"company_id": 7, "product_id": 31}]
    path = Path(__file__).parents[2] / "schemas/v1/product.accounting_profile.get.response.schema.json"
    schema = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator({"$defs": schema["$defs"], "$ref": "#/$defs/data"}).validate(data)
    for name in policies:
        assert "template-shared" in schema["$defs"]["data"]["properties"][name]["description"]


@pytest.mark.parametrize("field", ["invoice_policy", "purchase_method"])
@pytest.mark.parametrize("value", [True, 1, "", "other", [], {}])
def test_invalid_native_policy_is_closed_validation_not_python_type_error(field, value):
    with pytest.raises(ProductAccountingProfileError) as caught:
        get_product_accounting_profile(FakePort(data={**_data(), field: value}), _request())
    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8
