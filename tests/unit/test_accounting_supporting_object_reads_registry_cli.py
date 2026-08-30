from __future__ import annotations

import io
import json
from functools import partial
from pathlib import Path

import pytest

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.capabilities.core_object_reads import (
    CORE_OBJECT_READ_CAPABILITY_IDS,
)
from odoo_accounting_cli_v4.cli import (
    _CAPABILITY_MODELS,
    _HANDLERS,
    _REQUEST_VALIDATORS,
)

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "capabilities" / "v1" / "registry.json"
UNIT_REFERENCE = "tests/unit/test_accounting_supporting_object_reads_registry_cli.py"
INTEGRATION_REFERENCE = (
    "tests/integration/test_accounting_supporting_object_reads_live.py"
)

CAPABILITIES = {
    "asset.group.search": {
        "handler": "asset_group_search",
        "model": "account.asset.group",
        "modules": ["account_asset", "account", "base"],
        "source_models": {"res.company", "account.asset.group", "account.asset"},
    },
    "asset.group.get": {
        "handler": "asset_group_get",
        "model": "account.asset.group",
        "modules": ["account_asset", "account", "base"],
        "source_models": {"res.company", "account.asset.group", "account.asset"},
    },
    "report.budget_definition.search": {
        "handler": "report_budget_definition_search",
        "model": "account.report.budget",
        "modules": ["account_reports", "account", "base"],
        "source_models": {
            "res.company",
            "account.report.budget",
            "account.report.budget.item",
        },
    },
    "report.budget_definition.get": {
        "handler": "report_budget_definition_get",
        "model": "account.report.budget",
        "modules": ["account_reports", "account", "base"],
        "source_models": {
            "res.company",
            "account.report.budget",
            "account.report.budget.item",
        },
    },
    "report.budget_item.search": {
        "handler": "report_budget_item_search",
        "model": "account.report.budget.item",
        "modules": ["account_reports", "account", "base"],
        "source_models": {
            "res.company",
            "account.report.budget",
            "account.report.budget.item",
            "account.account",
        },
    },
    "report.budget_item.get": {
        "handler": "report_budget_item_get",
        "model": "account.report.budget.item",
        "modules": ["account_reports", "account", "base"],
        "source_models": {
            "res.company",
            "account.report.budget",
            "account.report.budget.item",
            "account.account",
        },
    },
    "tax.unit.search": {
        "handler": "tax_unit_search",
        "model": "account.tax.unit",
        "modules": ["account_reports", "account", "base"],
        "source_models": {
            "res.company",
            "account.tax.unit",
            "res.country",
            "account.fiscal.position",
            "res.partner",
        },
    },
    "tax.unit.get": {
        "handler": "tax_unit_get",
        "model": "account.tax.unit",
        "modules": ["account_reports", "account", "base"],
        "source_models": {
            "res.company",
            "account.tax.unit",
            "res.country",
            "account.fiscal.position",
            "res.partner",
        },
    },
    "account.return.account_status.search": {
        "handler": "account_return_account_status_search",
        "model": "account.audit.account.status",
        "modules": ["account_reports", "account", "base"],
        "source_models": {
            "res.company",
            "account.return",
            "account.audit.account.status",
            "account.account",
        },
    },
    "account.return.account_status.get": {
        "handler": "account_return_account_status_get",
        "model": "account.audit.account.status",
        "modules": ["account_reports", "account", "base"],
        "source_models": {
            "res.company",
            "account.return",
            "account.audit.account.status",
            "account.account",
        },
    },
}


def _registry() -> dict[str, object]:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))["capabilities"]


def test_registry_freezes_ten_supporting_object_reads() -> None:
    registry = _registry()

    assert len(CAPABILITIES) == 10
    for capability_id, expected in CAPABILITIES.items():
        descriptor = registry[capability_id]
        assert descriptor["access"] == "read"
        assert descriptor["handler_key"] == expected["handler"]
        assert descriptor["source"]["modules"] == expected["modules"]
        assert set(descriptor["source"]["models"]) == expected["source_models"]
        assert descriptor["requirements"]["modules"] == expected["modules"]
        assert descriptor["requirements"]["groups"] == [
            "account.group_account_readonly"
        ]
        assert descriptor["status"]["value"] == "unconfigured"
        assert descriptor["status"]["reason_code"] == "runtime_context_required"
        assert descriptor["tests"]["unit"]["status"] == "implemented"
        assert descriptor["tests"]["unit"]["references"] == [UNIT_REFERENCE]
        assert descriptor["tests"]["integration"]["status"] == "implemented"
        assert descriptor["tests"]["integration"]["references"] == [
            INTEGRATION_REFERENCE
        ]

        source_tokens = " ".join(
            [
                *descriptor["source"]["modules"],
                *descriptor["source"]["models"],
                *descriptor["source"]["locations"],
            ]
        ).lower()
        for forbidden in ("stock", "inventory", "picking", "sale", "purchase"):
            assert forbidden not in source_tokens


def test_cli_routes_every_capability_through_core_object_reads() -> None:
    for capability_id, expected in CAPABILITIES.items():
        handler_key = expected["handler"]
        assert capability_id in CORE_OBJECT_READ_CAPABILITY_IDS
        assert _CAPABILITY_MODELS[capability_id] == expected["model"]

        handler = _HANDLERS[handler_key]
        validator = _REQUEST_VALIDATORS[handler_key]
        assert isinstance(handler, partial)
        assert handler.args == (capability_id,)
        assert isinstance(validator, partial)
        assert validator.args == (capability_id,)


@pytest.mark.parametrize(
    ("capability_id", "parameters", "item"),
    [
        (
            "report.budget_definition.search",
            {"limit": 10, "cursor": None},
            {
                "id": 201,
                "company_id": 7,
                "name": "Operating budget",
                "sequence": 10,
                "item_count": 2,
            },
        ),
        (
            "report.budget_definition.get",
            {"budget_definition_id": 201},
            {
                "id": 201,
                "company_id": 7,
                "name": "Operating budget",
                "sequence": 10,
                "item_count": 2,
            },
        ),
        (
            "report.budget_item.search",
            {"limit": 10, "cursor": None},
            {
                "id": 301,
                "company_id": 7,
                "budget_definition": {"id": 201, "name": "Operating budget"},
                "account": {"id": 31, "code": "6000", "name": "Expenses"},
                "amount": "1250.50",
                "date": "2026-06-30",
            },
        ),
        (
            "report.budget_item.get",
            {"budget_item_id": 301},
            {
                "id": 301,
                "company_id": 7,
                "budget_definition": {"id": 201, "name": "Operating budget"},
                "account": {"id": 31, "code": "6000", "name": "Expenses"},
                "amount": "1250.50",
                "date": "2026-06-30",
            },
        ),
    ],
)
def test_new_report_cli_reads_preserve_real_success_record_ids(
    capability_id: str,
    parameters: dict[str, object],
    item: dict[str, object],
) -> None:
    class Port:
        user_id = 42

        def read(self, **_: object) -> dict[str, object]:
            return {
                "user_id": self.user_id,
                "company_visible": True,
                "module_installed": True,
                "access_allowed": True,
                "cursor_found": True,
                "items": [item],
            }

    request = {
        "schema_version": "v1",
        "request_id": "7bc39413-0d69-4092-9319-795d33f3167c",
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "zh_CN",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }
    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = cli.main(
        ["read", capability_id, "--request", "-"],
        stdin=io.StringIO(json.dumps(request)),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda _capability_id, _request: Port(),
    )

    assert exit_code == 0
    assert stderr.getvalue() == ""
    assert json.loads(stdout.getvalue())["odoo"]["record_ids"] == [item["id"]]


def test_missing_supporting_get_preserves_verified_odoo_audit_context() -> None:
    class EmptyPort:
        user_id = 42

        def read(self, **_: object) -> dict[str, object]:
            return {
                "user_id": self.user_id,
                "company_visible": True,
                "module_installed": True,
                "access_allowed": True,
                "cursor_found": True,
                "items": [],
            }

    request = {
        "schema_version": "v1",
        "request_id": "7bc39413-0d69-4092-9319-795d33f3167c",
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "zh_CN",
            "timezone": "Asia/Shanghai",
        },
        "parameters": {"asset_group_id": 999},
    }
    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = cli.main(
        ["read", "asset.group.get", "--request", "-"],
        stdin=io.StringIO(json.dumps(request)),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda _capability_id, _request: EmptyPort(),
    )

    assert exit_code == 4
    assert stderr.getvalue() == ""
    document = json.loads(stdout.getvalue())
    assert document["error"]["code"] == "record_not_found"
    assert document["odoo"] == {
        "database": "v4-dev",
        "company_id": 7,
        "user_id": 42,
        "model": "account.asset.group",
        "record_ids": [],
    }
