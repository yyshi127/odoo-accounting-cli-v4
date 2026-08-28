from __future__ import annotations

import copy
import io
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError
from referencing import Registry, Resource

from odoo_accounting_cli_v4.bridge.localization_configuration import (
    ACTION,
    OdooLocalizationConfigurationPort,
)
from odoo_accounting_cli_v4.capabilities.localization_configuration import (
    LocalizationConfigurationReadError,
    read_localization_configuration,
    validate_localization_configuration_request,
)
from odoo_accounting_cli_v4.cli import main

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas" / "v1"
REQUEST_ID = "12345678-1234-4234-8234-123456789abc"
CAPABILITIES = (
    "localization.china.configuration.inspect",
    "localization.singapore.configuration.inspect",
)


def _request(parameters: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": 1,
            "user_login": "odacv4_g5_accountant",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": {} if parameters is None else parameters,
    }


def _tax(record_id: int, name: str, rate: str, tax_type: str) -> dict[str, Any]:
    return {
        "id": record_id,
        "name": name,
        "rate": rate,
        "type_tax_use": tax_type,
    }


def _china() -> dict[str, Any]:
    return {
        "company_id": 1,
        "fiscal_country_code": "CN",
        "chart_template": "cn_oscg",
        "modules": {"l10n_cn": True, "l10n_cn_oscg": True},
        "account_count": 110,
        "default_sale_tax": _tax(5, "13% INC", "13", "sale"),
        "default_purchase_tax": _tax(11, "13%", "13", "purchase"),
        "fapiao_field_ready": True,
        "voucher_report_ready": True,
        "configured": True,
        "missing": [],
    }


def _singapore() -> dict[str, Any]:
    return {
        "company_id": 1,
        "fiscal_country_code": "SG",
        "chart_template": "sg",
        "currency_code": "SGD",
        "default_sale_tax": _tax(15, "9% SR", "9", "sale"),
        "default_purchase_tax": _tax(33, "9% TX", "9", "purchase"),
        "tax_report": {"id": 22, "name": "Tax Report"},
        "uen_configured": False,
        "vat_configured": False,
        "paynow_configured": False,
        "configured": False,
        "missing": ["uen", "vat", "paynow"],
    }


def _page(item: dict[str, Any], **overrides: Any) -> dict[str, Any]:
    value = {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "cursor_found": True,
        "items": [item],
    }
    value.update(overrides)
    return value


class Port:
    user_id = 5

    def __init__(self, page: dict[str, Any]) -> None:
        self.page = page
        self.calls: list[dict[str, Any]] = []

    def read(
        self,
        *,
        capability_id: str,
        company_id: int,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "capability_id": capability_id,
                "company_id": company_id,
                "parameters": parameters,
            }
        )
        return self.page


@pytest.mark.parametrize(
    ("capability_id", "data"),
    [
        ("localization.china.configuration.inspect", _china()),
        ("localization.singapore.configuration.inspect", _singapore()),
    ],
)
def test_cli_routes_localization_readiness_and_reports_the_company(
    capability_id: str, data: dict[str, Any]
) -> None:
    port = Port(_page(data))
    stdout = io.StringIO()
    stderr = io.StringIO()

    code = main(
        ["read", capability_id, "--request", "-"],
        stdin=io.StringIO(json.dumps(_request())),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda selected, _document: (
            port if selected == capability_id else None
        ),
    )

    document = json.loads(stdout.getvalue())
    assert code == 0
    assert stderr.getvalue() == ""
    assert document["capability"] == capability_id
    assert document["data"] == data
    assert document["odoo"] == {
        "database": "odoo_cli_v4_dev",
        "company_id": 1,
        "user_id": 5,
        "model": "res.company",
        "record_ids": [1],
    }


@pytest.mark.parametrize(
    ("capability_id", "data"),
    [
        ("localization.china.configuration.inspect", _china()),
        ("localization.singapore.configuration.inspect", _singapore()),
    ],
)
def test_parameterless_read_validates_fixed_company_readiness(
    capability_id: str, data: dict[str, Any]
) -> None:
    port = Port(_page(data))

    assert read_localization_configuration(capability_id, port, _request()) == data
    assert port.calls == [
        {"capability_id": capability_id, "company_id": 1, "parameters": {}}
    ]


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_request_rejects_any_parameters_or_expanded_envelopes(
    capability_id: str,
) -> None:
    with pytest.raises(LocalizationConfigurationReadError) as caught:
        validate_localization_configuration_request(
            capability_id, _request({"company_id": 1})
        )
    assert caught.value.code == "invalid_request"

    request = _request()
    request["extra"] = True
    with pytest.raises(LocalizationConfigurationReadError) as caught:
        validate_localization_configuration_request(capability_id, request)
    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize(
    ("capability_id", "data"),
    [
        ("localization.china.configuration.inspect", _china()),
        ("localization.singapore.configuration.inspect", _singapore()),
    ],
)
def test_result_rejects_inconsistent_configured_or_missing_flags(
    capability_id: str, data: dict[str, Any]
) -> None:
    inconsistent = copy.deepcopy(data)
    inconsistent["configured"] = not data["configured"]
    with pytest.raises(LocalizationConfigurationReadError) as caught:
        read_localization_configuration(
            capability_id, Port(_page(inconsistent)), _request()
        )
    assert caught.value.code == "failed_validation"

    inconsistent = copy.deepcopy(data)
    inconsistent["missing"] = ["fiscal_country"]
    with pytest.raises(LocalizationConfigurationReadError) as caught:
        read_localization_configuration(
            capability_id, Port(_page(inconsistent)), _request()
        )
    assert caught.value.code == "failed_validation"


class Client:
    def __init__(self, response: Any) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def invoke(self, action: str, payload: dict[str, Any]) -> Any:
        self.calls.append((action, payload))
        return self.response


def test_bridge_uses_one_fixed_action_and_closed_capability_ids() -> None:
    client = Client(_page(_china()))
    port = OdooLocalizationConfigurationPort(client)

    assert port.read(
        capability_id="localization.china.configuration.inspect",
        company_id=1,
        parameters={},
    ) == _page(_china())
    assert port.user_id == 5
    assert client.calls == [
        (
            ACTION,
            {
                "capability_id": "localization.china.configuration.inspect",
                "company_id": 1,
                "parameters": {},
            },
        )
    ]

    with pytest.raises(ValueError, match="Unsupported"):
        port.read(
            capability_id="localization.configuration.call",
            company_id=1,
            parameters={},
        )
    assert len(client.calls) == 1


def _load_schema(name: str) -> dict[str, Any]:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def _validator(name: str) -> Draft202012Validator:
    resources: dict[str, Resource[Any]] = {}
    for common in ("request.schema.json", "response.schema.json"):
        schema = _load_schema(common)
        resource = Resource.from_contents(schema)
        resources[common] = resource
        resources[schema["$id"]] = resource
    return Draft202012Validator(
        _load_schema(name),
        registry=Registry().with_resources(resources.items()),
        format_checker=FormatChecker(),
    )


def _response(capability_id: str, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "success": True,
        "capability": capability_id,
        "status": "verified",
        "data": data,
        "warnings": [],
        "error": None,
        "odoo": {
            "database": "odoo_cli_v4_dev",
            "company_id": 1,
            "user_id": 5,
            "model": "res.company",
            "record_ids": [1],
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": None,
            "verification": None,
        },
    }


@pytest.mark.parametrize(
    ("capability_id", "data"),
    [
        ("localization.china.configuration.inspect", _china()),
        ("localization.singapore.configuration.inspect", _singapore()),
    ],
)
def test_four_schemas_are_closed_and_accept_only_the_frozen_shapes(
    capability_id: str, data: dict[str, Any]
) -> None:
    request_name = f"{capability_id}.request.schema.json"
    response_name = f"{capability_id}.response.schema.json"
    for name in (request_name, response_name):
        schema = _load_schema(name)
        Draft202012Validator.check_schema(schema)
        assert schema["additionalProperties"] is False

    _validator(request_name).validate(_request())
    _validator(response_name).validate(_response(capability_id, data))

    with pytest.raises(ValidationError):
        _validator(request_name).validate(_request({"extra": True}))
    expanded = _response(capability_id, data)
    expanded["data"] = {**data, "extra": True}
    with pytest.raises(ValidationError):
        _validator(response_name).validate(expanded)
