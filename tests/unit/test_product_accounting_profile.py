from __future__ import annotations

import copy
from pathlib import Path

import pytest

from odoo_accounting_cli_v4.capabilities.product_accounting_profile import (
    ProductAccountingProfileError,
    get_product_accounting_profile,
    validate_product_accounting_profile_request,
)
from odoo_accounting_cli_v4.registry import load_registry


def _request(product_id: int = 31) -> dict:
    return {
        "schema_version": "v1",
        "request_id": "a31769b9-c6ab-4975-9690-e96f1556bd34",
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "zh_CN",
            "timezone": "Asia/Shanghai",
        },
        "parameters": {"product_id": product_id},
    }


def _account(account_id: int, code: str, name: str) -> dict:
    return {"id": account_id, "code": code, "name": name}


def _account_slot(account: dict | None) -> dict:
    return {"available": True, "reason_code": None, "account": account}


def _selection_slot(value: str) -> dict:
    return {"available": True, "reason_code": None, "value": value}


def _unavailable_account(reason_code: str) -> dict:
    return {"available": False, "reason_code": reason_code, "account": None}


def _unavailable_selection(reason_code: str) -> dict:
    return {"available": False, "reason_code": reason_code, "value": None}


def _data() -> dict:
    return {
        "company_id": 7,
        "product": {
            "id": 31,
            "name": "Office Chair / Blue",
            "default_code": "CHAIR-BLUE",
            "active": True,
            "company_id": None,
            "template_id": 21,
        },
        "template": {
            "id": 21,
            "name": "Office Chair",
            "company_id": None,
            "category_id": 11,
        },
        "category": {
            "id": 11,
            "name": "Office Furniture",
            "complete_name": "All / Office Furniture",
        },
        "modules": {"account": True, "stock_account": True},
        "accounts": {
            "income": _account_slot(_account(401, "600100", "Sales")),
            "expense": _account_slot(_account(501, "640100", "Cost of Sales")),
            "stock_valuation": _account_slot(
                _account(101, "140500", "Stock Valuation")
            ),
            "stock_input": _account_slot(_account(201, "220200", "Stock Input")),
            "stock_output": _account_slot(
                _account(202, "140600", "Stock Output")
            ),
        },
        "valuation": _selection_slot("real_time"),
        "cost_method": _selection_slot("average"),
    }


class FakePort:
    def __init__(
        self,
        *,
        data: dict | None = None,
        company_visible: bool = True,
        module_installed: bool = True,
        access_allowed: bool | None = None,
    ) -> None:
        self.user_id = 42
        self.data = copy.deepcopy(data)
        self.company_visible = company_visible
        self.module_installed = module_installed
        self.access_allowed = (
            company_visible and module_installed
            if access_allowed is None
            else access_allowed
        )
        self.calls: list[dict] = []

    def get_profile(self, **kwargs) -> dict:
        self.calls.append(copy.deepcopy(kwargs))
        return {
            "user_id": self.user_id,
            "company_visible": self.company_visible,
            "module_installed": self.module_installed,
            "access_allowed": self.access_allowed,
            "data": copy.deepcopy(self.data),
        }


def test_get_returns_the_final_company_scoped_accounting_profile() -> None:
    data = _data()
    port = FakePort(data=data)

    result = get_product_accounting_profile(port, _request())

    assert result == data
    assert port.calls == [{"company_id": 7, "product_id": 31}]


def test_optional_accounting_modules_are_explicitly_unavailable() -> None:
    data = _data()
    data["modules"]["stock_account"] = False
    for key in ("stock_valuation", "stock_input", "stock_output"):
        data["accounts"][key] = _unavailable_account("module_uninstalled")
    data["valuation"] = _unavailable_selection("module_uninstalled")
    data["cost_method"] = _unavailable_selection("module_uninstalled")

    result = get_product_accounting_profile(FakePort(data=data), _request())

    assert result == data
    assert result["accounts"]["income"]["available"] is True
    assert result["accounts"]["stock_input"] == {
        "available": False,
        "reason_code": "module_uninstalled",
        "account": None,
    }


def test_installed_module_can_report_an_unavailable_final_field() -> None:
    data = _data()
    data["accounts"]["stock_input"] = _unavailable_account("field_unavailable")

    assert get_product_accounting_profile(FakePort(data=data), _request()) == data


def test_account_slot_json_key_order_is_not_semantic() -> None:
    data = _data()
    data["accounts"] = dict(reversed(list(data["accounts"].items())))

    assert get_product_accounting_profile(FakePort(data=data), _request()) == data


@pytest.mark.parametrize("product_id", [0, -1, True, "31"])
def test_request_requires_one_positive_non_boolean_product_id(product_id) -> None:
    port = FakePort(data=_data())
    with pytest.raises(ProductAccountingProfileError) as caught:
        get_product_accounting_profile(port, _request(product_id))
    assert caught.value.code == "invalid_request"
    assert caught.value.exit_code == 2
    assert port.calls == []


def test_request_envelope_is_closed() -> None:
    request = _request()
    request["parameters"]["unexpected"] = True
    with pytest.raises(ProductAccountingProfileError):
        validate_product_accounting_profile_request(request)
    request = _request()
    request["context"]["unexpected"] = True
    with pytest.raises(ProductAccountingProfileError):
        validate_product_accounting_profile_request(request)


@pytest.mark.parametrize(
    ("port", "code"),
    [
        (FakePort(company_visible=False), "company_unavailable"),
        (FakePort(module_installed=False), "uninstalled"),
        (FakePort(access_allowed=False), "unauthorized"),
        (FakePort(data=None), "record_not_found"),
    ],
)
def test_runtime_availability_and_missing_product_are_explicit(
    port: FakePort, code: str
) -> None:
    with pytest.raises(ProductAccountingProfileError) as caught:
        get_product_accounting_profile(port, _request())
    assert caught.value.code == code


@pytest.mark.parametrize(
    "mutate",
    [
        lambda data: data.update(extra=True),
        lambda data: data.update(company_id=8),
        lambda data: data["product"].update(id=32),
        lambda data: data["product"].update(template_id=22),
        lambda data: data["product"].update(company_id=8),
        lambda data: data["template"].update(category_id=12),
        lambda data: data["template"].update(company_id=8),
        lambda data: data["modules"].update(account=False, stock_account=True),
        lambda data: data["accounts"]["income"].update(available=False),
        lambda data: data["accounts"]["income"].update(reason_code="field_unavailable"),
        lambda data: data["accounts"]["stock_input"].update(
            available=False, reason_code="module_uninstalled"
        ),
        lambda data: data["accounts"]["expense"]["account"].update(id=True),
        lambda data: data["valuation"].update(value="manual"),
        lambda data: data["valuation"].update(value={}),
        lambda data: data["cost_method"].update(value="lifo"),
    ],
)
def test_inconsistent_or_out_of_scope_profiles_fail_closed(mutate) -> None:
    data = _data()
    mutate(data)

    with pytest.raises(ProductAccountingProfileError) as caught:
        get_product_accounting_profile(FakePort(data=data), _request())

    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8


def test_wrong_bridge_user_fails_closed() -> None:
    class WrongUserPort(FakePort):
        def get_profile(self, **kwargs) -> dict:
            page = super().get_profile(**kwargs)
            page["user_id"] = self.user_id + 1
            return page

    with pytest.raises(ProductAccountingProfileError) as caught:
        get_product_accounting_profile(WrongUserPort(data=_data()), _request())
    assert caught.value.code == "failed_validation"


def test_specialized_schemas_accept_success_and_error_documents() -> None:
    schema_dir = Path(__file__).parents[2] / "schemas" / "v1"
    request_schema = "schemas/v1/product.accounting_profile.get.request.schema.json"
    response_schema = "schemas/v1/product.accounting_profile.get.response.schema.json"
    assert (schema_dir / Path(request_schema).name).is_file()
    assert (schema_dir / Path(response_schema).name).is_file()
    response = {
        "schema_version": "v1",
        "request_id": _request()["request_id"],
        "success": True,
        "capability": "product.accounting_profile.get",
        "status": "verified",
        "data": _data(),
        "warnings": [],
        "error": None,
        "odoo": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_id": 42,
            "model": "product.product",
            "record_ids": [31],
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": None,
            "verification": {"result": "passed"},
        },
    }
    registry = load_registry()
    registry.validate_instance(request_schema, _request())
    registry.validate_instance(response_schema, response)
    response.update(
        success=False,
        status="failed_validation",
        data=None,
        error={
            "code": "failed_validation",
            "message": "The result failed validation.",
            "details": {},
            "retryable": False,
        },
    )
    registry.validate_instance(response_schema, response)
