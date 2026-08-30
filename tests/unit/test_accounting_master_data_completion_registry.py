from __future__ import annotations

from odoo_accounting_cli_v4.bridge.core_writes_runtime import (
    _ACCESS as CORE_WRITE_ACCESS,
)
from odoo_accounting_cli_v4.bridge.core_writes_runtime import (
    _GROUPS as CORE_WRITE_GROUPS,
)
from odoo_accounting_cli_v4.bridge.core_writes_runtime import (
    _MODELS as CORE_WRITE_MODELS,
)
from odoo_accounting_cli_v4.capabilities.core_writes import (
    CORE_WRITE_CAPABILITY_IDS,
)
from odoo_accounting_cli_v4.cli import _CAPABILITY_MODELS
from odoo_accounting_cli_v4.registry import load_registry

BATCH = {
    "account.tag.create",
    "account.tag.update",
    "account.tag.archive",
    "account.tag.restore",
    "tax.group.create",
    "tax.group.update",
    "cash_rounding.create",
    "cash_rounding.update",
}
MODELS = {
    "account.tag.create": "account.account.tag",
    "account.tag.update": "account.account.tag",
    "account.tag.archive": "account.account.tag",
    "account.tag.restore": "account.account.tag",
    "tax.group.create": "account.tax.group",
    "tax.group.update": "account.tax.group",
    "cash_rounding.create": "account.cash.rounding",
    "cash_rounding.update": "account.cash.rounding",
}
UNIT_REFERENCES = {
    "tests/unit/test_core_writes.py",
    "tests/unit/test_accounting_master_data_completion_contracts.py",
    "tests/unit/test_core_writes_runtime.py",
    "tests/unit/test_accounting_master_data_completion_registry.py",
}


def test_batch_is_exactly_eight_non_inventory_accounting_writes() -> None:
    assert len(BATCH) == 8
    assert not any(
        capability_id.startswith(("stock.", "inventory.", "warehouse."))
        for capability_id in BATCH
    )


def test_registry_exposes_closed_schemas_and_fixed_core_write_routes() -> None:
    registry = load_registry()

    for capability_id in BATCH:
        descriptor = registry.describe(capability_id)
        assert descriptor["access"] == "write"
        assert descriptor["handler_key"] == "core_write"
        assert descriptor["schemas"] == {
            "request": f"schemas/v1/{capability_id}.request.schema.json",
            "response": f"schemas/v1/{capability_id}.response.schema.json",
        }
        assert registry.load_schema(descriptor["schemas"]["request"])[
            "additionalProperties"
        ] is False
        registry.load_schema(descriptor["schemas"]["response"])
        assert descriptor["tests"]["unit"]["status"] == "implemented"
        assert set(descriptor["tests"]["unit"]["references"]) == UNIT_REFERENCES
        assert descriptor["tests"]["integration"]["status"] == "implemented"
        assert descriptor["tests"]["integration"]["references"] == [
            "tests/integration/test_accounting_master_data_completion_live.py"
        ]
        assert descriptor["requirements"]["groups"] == [
            "account.group_account_manager"
        ]
        assert _CAPABILITY_MODELS[capability_id] == MODELS[capability_id]


def test_runtime_maps_are_closed_and_match_registry_access() -> None:
    registry = load_registry()

    assert BATCH <= CORE_WRITE_CAPABILITY_IDS
    for capability_id in BATCH:
        descriptor = registry.describe(capability_id)
        assert CORE_WRITE_GROUPS[capability_id] == "account.group_account_manager"
        assert set(descriptor["source"]["models"]) == CORE_WRITE_MODELS[capability_id]
        assert set(descriptor["requirements"]["acl"]) == {
            f"{model}:{operation}"
            for model, operation in CORE_WRITE_ACCESS[capability_id]
        }


def test_statuses_disclose_global_scope_and_create_concurrency() -> None:
    registry = load_registry()

    for capability_id in (
        "account.tag.create",
        "account.tag.update",
        "account.tag.archive",
        "account.tag.restore",
        "cash_rounding.create",
        "cash_rounding.update",
    ):
        assert registry.describe(capability_id)["status"]["reason_code"] == (
            "database_global_record_scope"
        )
    assert registry.describe("tax.group.create")["status"]["reason_code"] == (
        "concurrent_idempotency_limit"
    )
    assert registry.describe("tax.group.update")["status"]["reason_code"] == (
        "runtime_context_required"
    )
