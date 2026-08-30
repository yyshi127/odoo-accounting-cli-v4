from __future__ import annotations

from functools import partial

from odoo_accounting_cli_v4.bridge.core_writes_runtime import (
    _ACCESS as CORE_WRITE_ACCESS,
)
from odoo_accounting_cli_v4.bridge.core_writes_runtime import (
    _GROUPS as CORE_WRITE_GROUPS,
)
from odoo_accounting_cli_v4.bridge.core_writes_runtime import (
    _MODELS as CORE_WRITE_MODELS,
)
from odoo_accounting_cli_v4.capabilities.core_object_reads import (
    CORE_OBJECT_READ_CAPABILITY_IDS,
)
from odoo_accounting_cli_v4.capabilities.core_writes import (
    CORE_WRITE_CAPABILITY_IDS,
)
from odoo_accounting_cli_v4.cli import (
    _CAPABILITY_MODELS,
    _HANDLERS,
    _REQUEST_VALIDATORS,
)
from odoo_accounting_cli_v4.registry import load_registry

READ = "account.group.get"
WRITES = {
    "currency.rate.record",
    "account.group.create",
    "account.group.update",
    "tax.repartition_lines.replace",
    "reconciliation.model.create",
    "reconciliation.model.update",
    "reconciliation.model.lines.replace",
    "reconciliation.model.archive",
    "reconciliation.model.restore",
}
BATCH = {READ, *WRITES}
MODELS = {
    "currency.rate.record": "res.currency.rate",
    "account.group.get": "account.group",
    "account.group.create": "account.group",
    "account.group.update": "account.group",
    "tax.repartition_lines.replace": "account.tax",
    "reconciliation.model.create": "account.reconcile.model",
    "reconciliation.model.update": "account.reconcile.model",
    "reconciliation.model.lines.replace": "account.reconcile.model",
    "reconciliation.model.archive": "account.reconcile.model",
    "reconciliation.model.restore": "account.reconcile.model",
}


def test_batch_is_exactly_ten_accounting_capabilities() -> None:
    assert len(BATCH) == 10
    assert not any(
        capability_id.startswith(("stock.", "inventory.", "warehouse."))
        for capability_id in BATCH
    )


def test_registry_exposes_real_handlers_and_closed_schemas() -> None:
    registry = load_registry()

    for capability_id in BATCH:
        descriptor = registry.describe(capability_id)
        assert descriptor["schemas"] == {
            "request": f"schemas/v1/{capability_id}.request.schema.json",
            "response": f"schemas/v1/{capability_id}.response.schema.json",
        }
        assert registry.load_schema(descriptor["schemas"]["request"])[
            "additionalProperties"
        ] is False
        registry.load_schema(descriptor["schemas"]["response"])
        assert descriptor["tests"]["unit"]["status"] == "implemented"
        assert descriptor["tests"]["integration"]["status"] == "implemented"
        assert descriptor["tests"]["integration"]["references"] == [
            "tests/integration/test_accounting_configuration_expansion_live.py"
        ]
        assert _CAPABILITY_MODELS[capability_id] == MODELS[capability_id]

    read_descriptor = registry.describe(READ)
    assert read_descriptor["access"] == "read"
    assert read_descriptor["handler_key"] == "account_group_get"
    assert read_descriptor["status"]["value"] == "unconfigured"

    for capability_id in WRITES:
        descriptor = registry.describe(capability_id)
        assert descriptor["access"] == "write"
        assert descriptor["handler_key"] == "core_write"
        assert descriptor["requirements"]["groups"] == [
            "account.group_account_manager"
        ]
        assert set(descriptor["source"]["models"]) == CORE_WRITE_MODELS[
            capability_id
        ]
        assert set(descriptor["requirements"]["acl"]) == {
            f"{model}:{operation}"
            for model, operation in CORE_WRITE_ACCESS[capability_id]
        }
        assert CORE_WRITE_GROUPS[capability_id] == "account.group_account_manager"


def test_creation_statuses_disclose_concurrency_limit() -> None:
    registry = load_registry()

    for capability_id in ("account.group.create", "reconciliation.model.create"):
        assert registry.describe(capability_id)["status"]["reason_code"] == (
            "concurrent_idempotency_limit"
        )
    for capability_id in WRITES - {
        "account.group.create",
        "reconciliation.model.create",
    }:
        assert registry.describe(capability_id)["status"]["reason_code"] == (
            "runtime_context_required"
        )


def test_cli_routes_get_and_all_writes_through_fixed_ports() -> None:
    assert READ in CORE_OBJECT_READ_CAPABILITY_IDS
    assert WRITES <= CORE_WRITE_CAPABILITY_IDS

    handler = _HANDLERS["account_group_get"]
    validator = _REQUEST_VALIDATORS["account_group_get"]
    assert isinstance(handler, partial) and handler.args == (READ,)
    assert isinstance(validator, partial) and validator.args == (READ,)
