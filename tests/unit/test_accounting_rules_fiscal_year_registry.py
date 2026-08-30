from __future__ import annotations

from odoo_accounting_cli_v4.bridge.core_object_reads_runtime import (
    _REQUIRED_MODELS as READ_MODELS,
)
from odoo_accounting_cli_v4.bridge.core_writes_runtime import (
    _ACCESS as WRITE_ACCESS,
)
from odoo_accounting_cli_v4.bridge.core_writes_runtime import (
    _GROUPS as WRITE_GROUPS,
)
from odoo_accounting_cli_v4.bridge.core_writes_runtime import (
    _MODELS as WRITE_MODELS,
)
from odoo_accounting_cli_v4.capabilities.core_object_reads import (
    CORE_OBJECT_READ_CAPABILITY_IDS,
)
from odoo_accounting_cli_v4.capabilities.core_writes import CORE_WRITE_CAPABILITY_IDS
from odoo_accounting_cli_v4.cli import (
    _CAPABILITY_MODELS,
    _HANDLERS,
    _REQUEST_VALIDATORS,
)
from odoo_accounting_cli_v4.registry import load_registry

WRITE_IDS = (
    "fiscal_year.create",
    "fiscal_year.update",
    "analytic.applicability.create",
    "analytic.applicability.update",
    "analytic.distribution_model.create",
    "analytic.distribution_model.update",
)
READ_HANDLERS = {
    "fiscal_position.account_mapping.list": "fiscal_position_account_mapping_list",
    "fiscal_position.tax_mapping.list": "fiscal_position_tax_mapping_list",
}


def test_six_writes_match_runtime_models_acls_groups_and_cli() -> None:
    registry = load_registry()

    for capability_id in WRITE_IDS:
        descriptor = registry.describe(capability_id)
        assert capability_id in CORE_WRITE_CAPABILITY_IDS
        assert descriptor["access"] == "write"
        assert descriptor["handler_key"] == "core_write"
        assert set(descriptor["source"]["models"]) == WRITE_MODELS[capability_id]
        assert set(descriptor["requirements"]["acl"]) == {
            f"{model}:{mode}" for model, mode in WRITE_ACCESS[capability_id]
        }
        assert descriptor["requirements"]["groups"] == [
            WRITE_GROUPS[capability_id]
        ]
        assert _CAPABILITY_MODELS[capability_id] in WRITE_MODELS[capability_id]
        assert descriptor["status"]["value"] == (
            "degraded" if capability_id.endswith(".create") else "unconfigured"
        )
        assert "stock" not in descriptor["source"]["modules"]
        assert all(
            not model.startswith("stock.")
            for model in descriptor["source"]["models"]
        )
        for kind in ("request", "response"):
            schema = registry.load_schema(descriptor["schemas"][kind])
            assert schema["$id"].endswith(f"{capability_id}.{kind}.schema.json")


def test_two_mapping_reads_match_runtime_acl_schema_and_cli() -> None:
    registry = load_registry()

    for capability_id, handler_key in READ_HANDLERS.items():
        descriptor = registry.describe(capability_id)
        assert capability_id in CORE_OBJECT_READ_CAPABILITY_IDS
        assert descriptor["access"] == "read"
        assert descriptor["handler_key"] == handler_key
        assert tuple(descriptor["source"]["models"]) == READ_MODELS[capability_id]
        assert descriptor["requirements"]["acl"] == [
            f"{model}:read" for model in READ_MODELS[capability_id]
        ]
        assert descriptor["requirements"]["groups"] == [
            "account.group_account_readonly"
        ]
        assert handler_key in _HANDLERS
        assert handler_key in _REQUEST_VALIDATORS
        assert _CAPABILITY_MODELS[capability_id] in READ_MODELS[capability_id]
        assert descriptor["status"]["value"] == "unconfigured"
        for kind in ("request", "response"):
            schema = registry.load_schema(descriptor["schemas"][kind])
            assert schema["$id"].endswith(f"{capability_id}.{kind}.schema.json")
            assert schema["additionalProperties"] is False


def test_tax_mapping_response_preserves_empty_mapping_removal_semantics() -> None:
    schema = load_registry().load_schema(
        "schemas/v1/fiscal_position.tax_mapping.list.response.schema.json"
    )

    data = schema["$defs"]["data"]
    assert "removes_all_taxes" in data["required"]
    assert data["properties"]["removes_all_taxes"] == {"type": "boolean"}
