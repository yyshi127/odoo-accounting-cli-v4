from __future__ import annotations

import copy
import io
import json
from functools import partial
from typing import Any

import pytest

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.capabilities.core_object_reads import (
    read_core_object,
    validate_core_object_read_request,
)
from odoo_accounting_cli_v4.contracts import success_document
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

REQUEST_ID = "7bc39413-0d69-4092-9319-795d33f3167c"

CAPABILITIES = {
    "account.group.list": ("account_group_list", "account.group"),
    "journal.configuration.inspect": (
        "journal_configuration_inspect",
        "account.journal",
    ),
    "tax.repartition_line.list": (
        "tax_repartition_line_list",
        "account.tax.repartition.line",
    ),
    "tax.repartition_line.get": (
        "tax_repartition_line_get",
        "account.tax.repartition.line",
    ),
    "reconciliation.model.line.list": (
        "reconciliation_model_line_list",
        "account.reconcile.model.line",
    ),
    "reconciliation.model.line.get": (
        "reconciliation_model_line_get",
        "account.reconcile.model.line",
    ),
    "bank.list": ("bank_list", "res.bank"),
    "bank.get": ("bank_get", "res.bank"),
    "report.catalog.list": ("report_catalog_list", "account.report"),
    "report.catalog.get": ("report_catalog_get", "account.report"),
}

LIST_CAPABILITIES = {
    "account.group.list",
    "tax.repartition_line.list",
    "reconciliation.model.line.list",
    "bank.list",
    "report.catalog.list",
}

PARAMETERS = {
    "account.group.list": {
        "query": "Assets",
        "parent_id": None,
        "limit": 1,
        "cursor": None,
    },
    "journal.configuration.inspect": {"journal_id": 31},
    "tax.repartition_line.list": {
        "tax_id": 21,
        "document_types": ["invoice", "refund"],
        "repartition_types": ["base", "tax"],
        "account_id": 41,
        "use_in_tax_closing": False,
        "limit": 1,
        "cursor": None,
    },
    "tax.repartition_line.get": {"tax_repartition_line_id": 31},
    "reconciliation.model.line.list": {
        "reconciliation_model_id": 21,
        "account_id": 41,
        "partner_id": 51,
        "amount_types": ["fixed", "percentage"],
        "limit": 1,
        "cursor": None,
    },
    "reconciliation.model.line.get": {"reconciliation_model_line_id": 31},
    "bank.list": {
        "query": "Fixture",
        "country_id": 45,
        "active": True,
        "limit": 1,
        "cursor": None,
    },
    "bank.get": {"bank_id": 31},
    "report.catalog.list": {
        "country_id": 45,
        "root_report_id": None,
        "availability_conditions": ["always", "country"],
        "active": True,
        "limit": 1,
        "cursor": None,
    },
    "report.catalog.get": {"report_id": 31},
}

SOURCE_AND_ACL = {
    "account.group.list": (
        ["account", "base"],
        ["res.company", "account.group"],
        ["account"],
        ["res.company:read", "account.group:read"],
    ),
    "journal.configuration.inspect": (
        ["account", "base"],
        [
            "res.company",
            "account.journal",
            "res.currency",
            "account.account",
            "res.partner.bank",
            "account.payment.method.line",
        ],
        ["account"],
        [
            "res.company:read",
            "account.journal:read",
            "res.currency:read",
            "account.account:read",
            "res.partner.bank:read",
            "account.payment.method.line:read",
        ],
    ),
    "tax.repartition_line.list": (
        ["account", "base"],
        [
            "res.company",
            "account.tax",
            "account.tax.repartition.line",
            "account.account",
            "account.account.tag",
        ],
        ["account"],
        [
            "res.company:read",
            "account.tax:read",
            "account.tax.repartition.line:read",
            "account.account:read",
            "account.account.tag:read",
        ],
    ),
    "reconciliation.model.line.list": (
        ["account", "account_accountant", "analytic", "base"],
        [
            "res.company",
            "account.reconcile.model",
            "account.reconcile.model.line",
            "account.account",
            "res.partner",
            "account.tax",
            "account.analytic.account",
        ],
        ["account", "account_accountant", "analytic"],
        [
            "res.company:read",
            "account.reconcile.model:read",
            "account.reconcile.model.line:read",
            "account.account:read",
            "res.partner:read",
            "account.tax:read",
            "account.analytic.account:read",
        ],
    ),
    "bank.list": (
        ["account", "base"],
        ["res.company", "res.bank", "res.country", "res.country.state"],
        ["account", "base"],
        [
            "res.company:read",
            "res.bank:read",
            "res.country:read",
            "res.country.state:read",
        ],
    ),
    "report.catalog.list": (
        ["account_reports", "base"],
        ["res.company", "account.report", "account.report.column", "res.country"],
        ["account_reports"],
        [
            "res.company:read",
            "account.report:read",
            "account.report.column:read",
            "res.country:read",
        ],
    ),
}


def _request(capability_id: str) -> dict[str, Any]:
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
        "parameters": copy.deepcopy(PARAMETERS[capability_id]),
    }


def _named(record_id: int, name: str) -> dict[str, Any]:
    return {"id": record_id, "name": name}


def _coded(record_id: int, code: str, name: str) -> dict[str, Any]:
    return {"id": record_id, "code": code, "name": name}


def _item(capability_id: str) -> dict[str, Any]:
    if capability_id == "account.group.list":
        return {
            "id": 31,
            "name": "Current Assets",
            "code_prefix_start": "10",
            "code_prefix_end": "19",
            "parent": _named(21, "Assets"),
            "company_id": 7,
        }
    if capability_id == "journal.configuration.inspect":
        return {
            "id": 31,
            "code": "BNK1",
            "name": "Bank",
            "type": "bank",
            "active": True,
            "company_id": 7,
            "currency": {"id": 6, "code": "CNY"},
            "default_account": _coded(41, "100201", "Bank"),
            "suspense_account": None,
            "profit_account": None,
            "loss_account": None,
            "bank_account": _named(51, "Fixture Bank Account"),
            "inbound_payment_methods": [_named(61, "Manual")],
            "outbound_payment_methods": [_named(71, "Manual")],
            "invoice_reference_type": "invoice",
            "invoice_reference_model": "odoo",
            "restrict_mode_hash_table": False,
        }
    if capability_id.startswith("tax.repartition_line."):
        return {
            "id": 31,
            "sequence": 10,
            "company_id": 7,
            "tax": _named(21, "VAT 13%"),
            "document_type": "invoice",
            "repartition_type": "tax",
            "factor_percent": "100",
            "factor": "1",
            "account": _coded(41, "222101", "Output VAT"),
            "tags": [_named(51, "VAT")],
            "use_in_tax_closing": False,
        }
    if capability_id.startswith("reconciliation.model.line."):
        return {
            "id": 31,
            "sequence": 10,
            "company_id": 7,
            "reconciliation_model": _named(21, "Bank Fees"),
            "account": _coded(41, "660300", "Bank Fees"),
            "partner": _named(51, "Fixture Partner"),
            "label": "Bank fee",
            "amount_type": "fixed",
            "amount": "10",
            "amount_string": "10.00",
            "taxes": [_named(61, "VAT 6%")],
            "analytic_distribution": [
                {
                    "analytic_accounts": [_named(71, "Operations")],
                    "percentage": "100",
                }
            ],
        }
    if capability_id.startswith("bank."):
        return {
            "id": 31,
            "name": "Fixture Bank",
            "bic": "FIXTCNBJ",
            "active": True,
            "street": "1 Finance Street",
            "street2": None,
            "zip": "100000",
            "city": "Beijing",
            "email": "bank@example.test",
            "phone": "+86-10-00000000",
            "state": _named(44, "Beijing"),
            "country": _named(45, "China"),
        }
    return {
        "id": 31,
        "name": "Balance Sheet",
        "active": True,
        "root_report": None,
        "country": _named(45, "China"),
        "availability_condition": "country",
        "variants": [_named(41, "Balance Sheet Variant")],
        "sections": [_named(51, "Assets")],
        "columns": [
            {
                "id": 61,
                "name": "Balance",
                "expression_label": "balance",
                "figure_type": "monetary",
                "sortable": True,
                "blank_if_zero": False,
            }
        ],
        "filters": {
            "multi_company": "selector",
            "date_range": True,
            "show_draft": True,
            "unreconciled": False,
            "unfold_all": True,
            "journals": True,
            "analytic": True,
            "partner": False,
        },
    }


def _data(capability_id: str) -> dict[str, Any]:
    item = _item(capability_id)
    if capability_id in LIST_CAPABILITIES:
        return {"items": [item], "has_more": False, "next_cursor": None}
    return item


def _source_key(capability_id: str) -> str:
    if capability_id.startswith("tax.repartition_line."):
        return "tax.repartition_line.list"
    if capability_id.startswith("reconciliation.model.line."):
        return "reconciliation.model.line.list"
    if capability_id.startswith("bank."):
        return "bank.list"
    if capability_id.startswith("report.catalog."):
        return "report.catalog.list"
    return capability_id


def _assert_partial(value: object, function: object, capability_id: str) -> None:
    assert isinstance(value, partial)
    assert value.func is function
    assert value.args == (capability_id,)


@pytest.fixture(scope="module")
def registry() -> Any:
    return load_registry()


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_registry_metadata_and_cli_wiring_are_exact(
    capability_id: str, registry: Any
) -> None:
    descriptor = registry.describe(capability_id)
    handler_key, model = CAPABILITIES[capability_id]
    source_modules, source_models, required_modules, acl = SOURCE_AND_ACL[
        _source_key(capability_id)
    ]

    assert descriptor["access"] == "read"
    assert descriptor["handler_key"] == handler_key
    assert descriptor["source"]["modules"] == source_modules
    assert descriptor["source"]["models"] == source_models
    assert descriptor["requirements"]["modules"] == required_modules
    assert descriptor["requirements"]["groups"] == ["account.group_account_readonly"]
    assert descriptor["requirements"]["acl"] == acl
    assert descriptor["status"]["value"] == "unconfigured"
    assert descriptor["status"]["reason_code"] == "runtime_context_required"
    _assert_partial(cli._HANDLERS[handler_key], read_core_object, capability_id)
    _assert_partial(
        cli._REQUEST_VALIDATORS[handler_key],
        validate_core_object_read_request,
        capability_id,
    )
    assert cli._CAPABILITY_MODELS[capability_id] == model


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_request_and_response_schemas_are_closed(
    capability_id: str, registry: Any
) -> None:
    descriptor = registry.describe(capability_id)
    request_schema = registry.load_schema(descriptor["schemas"]["request"])
    response_schema = registry.load_schema(descriptor["schemas"]["response"])
    request = _request(capability_id)
    response = success_document(
        capability_id,
        _data(capability_id),
        request_id=REQUEST_ID,
        database="odoo_cli_v4_dev",
        company_id=7,
        user_id=42,
        model=CAPABILITIES[capability_id][1],
        record_ids=[31],
    )

    assert request_schema["additionalProperties"] is False
    assert request_schema["$defs"]["parameters"]["additionalProperties"] is False
    assert response_schema["additionalProperties"] is False
    registry.validate_instance(descriptor["schemas"]["request"], request)
    registry.validate_instance(descriptor["schemas"]["response"], response)

    invalid_request = copy.deepcopy(request)
    invalid_request["parameters"]["unexpected"] = True
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(descriptor["schemas"]["request"], invalid_request)

    invalid_response = copy.deepcopy(response)
    item = (
        invalid_response["data"]["items"][0]
        if capability_id in LIST_CAPABILITIES
        else invalid_response["data"]
    )
    item["unexpected"] = True
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(descriptor["schemas"]["response"], invalid_response)


class _SuccessPort:
    user_id = 42

    def __init__(self, capability_id: str) -> None:
        self.capability_id = capability_id

    def read(
        self,
        *,
        capability_id: str,
        company_id: int,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        assert capability_id == self.capability_id
        assert company_id == 7
        assert isinstance(parameters, dict)
        return {
            "user_id": self.user_id,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "cursor_found": True,
            "items": [_item(capability_id)],
        }


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_cli_emits_exact_model_and_record_ids(
    capability_id: str,
    monkeypatch: pytest.MonkeyPatch,
    registry: Any,
) -> None:
    request = _request(capability_id)
    stdout = io.StringIO()
    stderr = io.StringIO()
    monkeypatch.setattr(cli, "load_registry", lambda: registry)

    exit_code = cli.main(
        ["read", capability_id, "--request", "-"],
        stdin=io.StringIO(json.dumps(request)),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda selected, _request: _SuccessPort(selected),
    )

    document = json.loads(stdout.getvalue())
    assert exit_code == 0
    assert stderr.getvalue() == ""
    assert document["data"] == _data(capability_id)
    assert document["odoo"] == {
        "database": "odoo_cli_v4_dev",
        "company_id": 7,
        "user_id": 42,
        "model": CAPABILITIES[capability_id][1],
        "record_ids": [31],
    }
