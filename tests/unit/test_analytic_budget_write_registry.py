from __future__ import annotations

import copy
from pathlib import Path

import pytest

from odoo_accounting_cli_v4.bridge.core_writes_runtime import (
    _ACCESS as CORE_WRITE_ACCESS,
)
from odoo_accounting_cli_v4.bridge.core_writes_runtime import (
    _GROUPS as CORE_WRITE_GROUPS,
)
from odoo_accounting_cli_v4.bridge.core_writes_runtime import (
    _MODELS as CORE_WRITE_MODELS,
)
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

BATCH_IDS = {
    "analytic.account.create",
    "analytic.account.update",
    "budget.cancel",
    "budget.confirm",
    "budget.create",
    "budget.lines.replace",
    "budget.mark_done",
    "budget.reset_to_draft",
    "budget.update_draft",
}
LIFECYCLE_IDS = {
    "budget.cancel",
    "budget.confirm",
    "budget.mark_done",
    "budget.reset_to_draft",
}
CREATE_IDS = {"analytic.account.create", "budget.create"}
UNIT_REFERENCES = [
    "tests/unit/test_analytic_budget_writes.py",
    "tests/unit/test_analytic_budget_writes_runtime.py",
    "tests/unit/test_analytic_budget_write_cli.py",
    "tests/unit/test_analytic_budget_write_registry.py",
]
INTEGRATION_REFERENCE = "tests/integration/test_analytic_budget_write_batch_live.py"
DEGRADED_REASON_CODES = {
    "analytic.account.create": (
        "odoo_native_analytic_account_idempotency_field_unavailable"
    ),
    "budget.create": "odoo_native_budget_idempotency_field_unavailable",
}


def _request(parameters: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": "v1",
        "request_id": "123e4567-e89b-42d3-a456-426614174000",
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": 1,
            "user_login": "accountant@example.test",
            "language": "en_US",
            "timezone": "UTC",
        },
        "parameters": parameters,
    }


def _validate(capability_id: str, parameters: dict[str, object]) -> None:
    registry = load_registry()
    registry.validate_instance(
        registry.describe(capability_id)["schemas"]["request"],
        _request(parameters),
    )


def _assert_invalid(capability_id: str, parameters: dict[str, object]) -> None:
    with pytest.raises(InstanceValidationError):
        _validate(capability_id, parameters)


def test_batch_registry_metadata_and_cumulative_counts_are_exact() -> None:
    registry = load_registry()

    assert len(registry.ids()) == 355
    assert (
        sum(
            registry.describe(capability_id)["handler_key"] is not None
            for capability_id in registry.ids()
        )
        == 340
    )
    assert (
        sum(
            registry.describe(capability_id)["handler_key"] is not None
            and registry.describe(capability_id)["access"] == "read"
            for capability_id in registry.ids()
        )
        == 210
    )
    assert (
        sum(
            registry.describe(capability_id)["handler_key"] is not None
            and registry.describe(capability_id)["access"] == "write"
            for capability_id in registry.ids()
        )
        == 130
    )
    assert (
        sum(
            registry.describe(capability_id)["status"]["value"] == "disabled"
            for capability_id in registry.ids()
        )
        == 15
    )
    assert (
        sum(
            registry.describe(capability_id)["status"]["value"] == "unconfigured"
            for capability_id in registry.ids()
        )
        == 307
    )
    assert (
        sum(
            registry.describe(capability_id)["status"]["value"] == "degraded"
            for capability_id in registry.ids()
        )
        == 33
    )

    for capability_id in BATCH_IDS:
        descriptor = registry.describe(capability_id)
        assert descriptor["access"] == "write"
        assert descriptor["handler_key"] == "core_write"
        if capability_id in CREATE_IDS:
            assert descriptor["status"]["value"] == "degraded"
            assert (
                descriptor["status"]["reason_code"]
                == DEGRADED_REASON_CODES[capability_id]
            )
            assert "visible deterministic name suffix" in descriptor["status"]["reason"]
            assert "concurrent exactly-once" in descriptor["status"]["reason"]
            assert "visible_odoo_" in descriptor["strategies"]["idempotency"]
        else:
            assert descriptor["status"]["value"] == "unconfigured"
            assert descriptor["status"]["reason_code"] == "runtime_context_required"
            assert "result_replay" not in descriptor["strategies"]["idempotency"]
            assert "current_" in descriptor["strategies"]["idempotency"]
        assert descriptor["requirements"]["groups"] == [
            CORE_WRITE_GROUPS[capability_id]
        ]
        assert set(descriptor["source"]["models"]) == CORE_WRITE_MODELS[capability_id]
        assert set(descriptor["requirements"]["acl"]) == {
            f"{model}:{operation}"
            for model, operation in CORE_WRITE_ACCESS[capability_id]
        }
        assert descriptor["schemas"] == {
            "request": f"schemas/v1/{capability_id}.request.schema.json",
            "response": f"schemas/v1/{capability_id}.response.schema.json",
        }
        assert descriptor["tests"]["unit"] == {
            "status": "implemented",
            "references": UNIT_REFERENCES,
            "reason": "Unit tests cover the closed public contract, fixed runtime execution, deterministic idempotency, visible marker behavior, registry schemas, and CLI dispatch.",
        }
        assert descriptor["tests"]["integration"]["status"] == "implemented"
        assert descriptor["tests"]["integration"]["references"] == [
            INTEGRATION_REFERENCE
        ]
        assert "immediate replay" in descriptor["tests"]["integration"]["reason"]


def test_batch_has_exactly_eighteen_closed_public_schema_files() -> None:
    registry = load_registry()
    schema_root = Path(__file__).resolve().parents[2] / "schemas" / "v1"

    assert len(list(schema_root.glob("*.schema.json"))) == 685
    for capability_id in BATCH_IDS:
        descriptor = registry.describe(capability_id)
        request_schema = registry.load_schema(descriptor["schemas"]["request"])
        response_schema = registry.load_schema(descriptor["schemas"]["response"])

        assert request_schema["additionalProperties"] is False
        assert (
            request_schema["properties"]["parameters"]["additionalProperties"] is False
        )
        assert response_schema["allOf"][1]["properties"]["data"] == {
            "oneOf": [
                {"type": "null"},
                {"$ref": "core-write-result.schema.json"},
            ]
        }


def test_analytic_account_request_schemas_freeze_exact_fields() -> None:
    _validate(
        "analytic.account.create",
        {"name": "Consulting", "plan_id": 3, "code": None, "partner_id": None},
    )
    _validate(
        "analytic.account.update",
        {
            "analytic_account_id": 7,
            "changes": {
                "name": "Consulting East",
                "code": "EAST",
                "partner_id": 9,
                "active": False,
            },
        },
    )

    _assert_invalid("analytic.account.create", {"name": "", "plan_id": 3})
    _assert_invalid("analytic.account.create", {"name": "x" * 201, "plan_id": 3})
    _assert_invalid("analytic.account.create", {"name": "Consulting", "plan_id": 0})
    for name in (
        " Consulting",
        "Consulting ",
        "Consulting [ODACV4:" + "a" * 64 + "]",
    ):
        _assert_invalid("analytic.account.create", {"name": name, "plan_id": 3})
    _assert_invalid(
        "analytic.account.create",
        {"name": "Consulting", "plan_id": 3, "code": " EAST "},
    )
    _assert_invalid(
        "analytic.account.create",
        {"name": "Consulting", "plan_id": 3, "unknown": True},
    )
    _assert_invalid(
        "analytic.account.update",
        {"analytic_account_id": 7, "changes": {}},
    )
    _assert_invalid(
        "analytic.account.update",
        {"analytic_account_id": 7, "changes": {"plan_id": 4}},
    )
    for changes in (
        {"name": " Consulting"},
        {"name": "Consulting "},
        {"name": "Consulting [ODACV4:" + "b" * 64 + "]"},
        {"code": " EAST "},
    ):
        _assert_invalid(
            "analytic.account.update",
            {"analytic_account_id": 7, "changes": changes},
        )


def test_budget_create_update_and_lines_schemas_freeze_exact_fields() -> None:
    _validate(
        "budget.create",
        {
            "name": "FY2027 operating budget",
            "date_from": "2027-01-01",
            "date_to": "2027-12-31",
            "budget_type": "both",
        },
    )
    _validate(
        "budget.update_draft",
        {"budget_id": 11, "changes": {"budget_type": "expense"}},
    )
    _validate(
        "budget.lines.replace",
        {
            "budget_id": 11,
            "lines": [
                {"budget_amount": "-1200.50", "analytic_account_ids": [2, 5]},
                {"budget_amount": "0", "analytic_account_ids": [8]},
            ],
        },
    )

    for value in ("Revenue", "income", ""):
        invalid = _request(
            {
                "name": "FY2027",
                "date_from": "2027-01-01",
                "date_to": "2027-12-31",
                "budget_type": value,
            }
        )
        registry = load_registry()
        with pytest.raises(InstanceValidationError):
            registry.validate_instance(
                registry.describe("budget.create")["schemas"]["request"], invalid
            )

    _assert_invalid("budget.update_draft", {"budget_id": 11, "changes": {}})
    for name in (
        " FY2027",
        "FY2027 ",
        "FY2027 [ODACV4:" + "c" * 64 + "]",
    ):
        _assert_invalid(
            "budget.create",
            {
                "name": name,
                "date_from": "2027-01-01",
                "date_to": "2027-12-31",
                "budget_type": "both",
            },
        )
        _assert_invalid(
            "budget.update_draft",
            {"budget_id": 11, "changes": {"name": name}},
        )
    _assert_invalid(
        "budget.lines.replace",
        {
            "budget_id": 11,
            "lines": [
                {"budget_amount": "+1", "analytic_account_ids": [2]},
            ],
        },
    )
    _assert_invalid(
        "budget.lines.replace",
        {
            "budget_id": 11,
            "lines": [
                {"budget_amount": "1", "analytic_account_ids": [2, 2]},
            ],
        },
    )

    schema = load_registry().load_schema(
        "schemas/v1/budget.lines.replace.request.schema.json"
    )
    analytic_ids = schema["properties"]["parameters"]["properties"]["lines"]["items"][
        "properties"
    ]["analytic_account_ids"]
    assert analytic_ids["minItems"] == 1
    assert analytic_ids["maxItems"] == 16
    assert analytic_ids["uniqueItems"] is True
    assert "strictly increasing" in analytic_ids["$comment"]


def test_budget_lifecycle_requests_only_accept_budget_id() -> None:
    for capability_id in LIFECYCLE_IDS:
        _validate(capability_id, {"budget_id": 17})
        _assert_invalid(capability_id, {"budget_id": 0})
        invalid = {"budget_id": 17, "force": True}
        _assert_invalid(capability_id, copy.deepcopy(invalid))
