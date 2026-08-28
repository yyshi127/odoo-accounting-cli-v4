from __future__ import annotations

from functools import cache

import pytest

from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

BATCH_IDS = {
    "account.account.create",
    "account.account.update",
    "account.account.archive",
    "account.account.restore",
    "journal.create",
    "journal.update",
    "journal.archive",
    "journal.restore",
    "tax.create",
    "tax.update",
    "tax.archive",
    "tax.restore",
}
UNIT_REFERENCES = [
    "tests/unit/test_accounting_config_writes.py",
    "tests/unit/test_accounting_config_writes_runtime.py",
    "tests/unit/test_accounting_config_write_cli.py",
    "tests/unit/test_accounting_config_write_registry.py",
]
INTEGRATION_REFERENCE = "tests/integration/test_accounting_config_write_batch_live.py"
EXPECTED_ACL = {
    "account.account.create": {
        "res.company:read",
        "res.currency:read",
        "account.account:read",
        "account.account:create",
    },
    "account.account.update": {
        "res.company:read",
        "res.currency:read",
        "account.account:read",
        "account.account:write",
    },
    "account.account.archive": {
        "res.company:read",
        "account.account:read",
        "account.account:write",
    },
    "account.account.restore": {
        "res.company:read",
        "account.account:read",
        "account.account:write",
    },
    "journal.create": {
        "res.company:read",
        "res.currency:read",
        "account.account:read",
        "account.account:create",
        "account.journal:read",
        "account.journal:create",
    },
    "journal.update": {
        "res.company:read",
        "res.currency:read",
        "account.account:read",
        "account.journal:read",
        "account.journal:write",
    },
    "journal.archive": {
        "res.company:read",
        "account.journal:read",
        "account.journal:write",
    },
    "journal.restore": {
        "res.company:read",
        "account.journal:read",
        "account.journal:write",
    },
    "tax.create": {
        "res.company:read",
        "account.tax.group:read",
        "account.tax:read",
        "account.tax:create",
    },
    "tax.update": {
        "res.company:read",
        "account.tax.group:read",
        "account.tax:read",
        "account.tax:write",
    },
    "tax.archive": {"res.company:read", "account.tax:read", "account.tax:write"},
    "tax.restore": {"res.company:read", "account.tax:read", "account.tax:write"},
}
EXPECTED_PARAMETERS = {
    "account.account.create": {
        "code",
        "name",
        "account_type",
        "reconcile",
        "currency_id",
    },
    "account.account.update": {"account_id", "changes"},
    "account.account.archive": {"account_id"},
    "account.account.restore": {"account_id"},
    "journal.create": {
        "name",
        "code",
        "type",
        "sequence",
        "currency_id",
        "default_account_id",
    },
    "journal.update": {"journal_id", "changes"},
    "journal.archive": {"journal_id"},
    "journal.restore": {"journal_id"},
    "tax.create": {
        "name",
        "type_tax_use",
        "amount_type",
        "amount",
        "sequence",
        "tax_group_id",
        "invoice_label",
        "price_include_override",
        "include_base_amount",
        "is_base_affected",
    },
    "tax.update": {"tax_id", "changes"},
    "tax.archive": {"tax_id"},
    "tax.restore": {"tax_id"},
}
VALID_PARAMETERS = {
    "account.account.create": {
        "code": "6100.01",
        "name": "Consulting Expense",
        "account_type": "expense",
        "reconcile": False,
        "currency_id": None,
    },
    "account.account.update": {
        "account_id": 7,
        "changes": {"name": "Consulting Fees", "currency_id": None},
    },
    "account.account.archive": {"account_id": 7},
    "account.account.restore": {"account_id": 7},
    "journal.create": {
        "name": "Operations",
        "code": "OPS1",
        "type": "general",
        "sequence": 20,
        "currency_id": None,
        "default_account_id": 7,
    },
    "journal.update": {
        "journal_id": 8,
        "changes": {"name": "Operations 2", "code": "OPS2", "default_account_id": None},
    },
    "journal.archive": {"journal_id": 8},
    "journal.restore": {"journal_id": 8},
    "tax.create": {
        "name": "Sales Tax 10%",
        "type_tax_use": "sale",
        "amount_type": "percent",
        "amount": 10.0,
        "sequence": 1,
        "tax_group_id": None,
        "invoice_label": "Tax 10%",
        "price_include_override": None,
        "include_base_amount": False,
        "is_base_affected": True,
    },
    "tax.update": {
        "tax_id": 9,
        "changes": {
            "name": "Sales Tax 8%",
            "amount": 8,
            "invoice_label": None,
            "price_include_override": "tax_excluded",
        },
    },
    "tax.archive": {"tax_id": 9},
    "tax.restore": {"tax_id": 9},
}


@cache
def _registry():
    return load_registry()


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
    registry = _registry()
    registry.validate_instance(
        registry.describe(capability_id)["schemas"]["request"],
        _request(parameters),
    )


def _assert_invalid(capability_id: str, parameters: dict[str, object]) -> None:
    with pytest.raises(InstanceValidationError):
        _validate(capability_id, parameters)


def test_accounting_config_batch_descriptors_freeze_access_and_evidence() -> None:
    registry = _registry()
    assert BATCH_IDS <= set(registry.ids())
    for capability_id in BATCH_IDS:
        descriptor = registry.describe(capability_id)
        assert descriptor["access"] == "write"
        assert descriptor["handler_key"] == "core_write"
        assert descriptor["requirements"]["configuration"] == [
            "database_alias",
            "company_allowlist",
            "user_mapping",
        ]
        assert descriptor["requirements"]["company"] == "required"
        assert descriptor["requirements"]["groups"] == ["account.group_account_manager"]
        assert set(descriptor["requirements"]["acl"]) == EXPECTED_ACL[capability_id]
        assert descriptor["tests"]["unit"]["status"] == "implemented"
        assert descriptor["tests"]["unit"]["references"] == UNIT_REFERENCES
        assert descriptor["tests"]["integration"]["status"] == "implemented"
        assert descriptor["tests"]["integration"]["references"] == [
            INTEGRATION_REFERENCE
        ]
        for evidence_kind in ("golden", "e2e"):
            assert descriptor["tests"][evidence_kind]["status"] == "planned"
            assert descriptor["tests"][evidence_kind]["references"] == []

    for capability_id in ("account.account.create", "tax.create"):
        status = registry.describe(capability_id)["status"]
        assert status["value"] == "degraded"
        assert status["reason_code"] == "concurrent_idempotency_limit"
        assert "concurrent exactly-once" in status["reason"]
    for capability_id in BATCH_IDS - {"account.account.create", "tax.create"}:
        status = registry.describe(capability_id)["status"]
        assert status["value"] == "unconfigured"
        assert status["reason_code"] == "runtime_context_required"


def test_accounting_config_request_schemas_are_closed_and_accept_fixtures() -> None:
    registry = _registry()
    for capability_id, parameters in VALID_PARAMETERS.items():
        _validate(capability_id, parameters)
        schema = registry.load_schema(
            registry.describe(capability_id)["schemas"]["request"]
        )
        parameter_schema = schema["properties"]["parameters"]
        assert parameter_schema["additionalProperties"] is False
        assert set(parameter_schema["properties"]) == EXPECTED_PARAMETERS[capability_id]

    for capability_id in (
        "account.account.update",
        "journal.update",
        "tax.update",
    ):
        changes = registry.load_schema(
            f"schemas/v1/{capability_id}.request.schema.json"
        )["properties"]["parameters"]["properties"]["changes"]
        assert changes["additionalProperties"] is False
        assert changes["minProperties"] == 1


def test_accounting_config_requests_reject_unsafe_fields_and_bad_values() -> None:
    _assert_invalid(
        "account.account.create",
        {"code": " 6100", "name": "Expense", "account_type": "expense"},
    )
    _assert_invalid(
        "account.account.create",
        {"code": "6100-1", "name": "Expense", "account_type": "expense"},
    )
    _assert_invalid(
        "account.account.create",
        {"code": "6100", "name": " Expense", "account_type": "expense"},
    )
    _assert_invalid(
        "account.account.create",
        {"code": "6100", "name": "Expense", "account_type": "unknown"},
    )
    _assert_invalid("account.account.update", {"account_id": 7, "changes": {}})
    _assert_invalid(
        "account.account.update",
        {"account_id": 7, "changes": {"company_id": 2}},
    )
    _assert_invalid(
        "journal.create", {"name": "Operations", "code": "TOOLONG", "type": "general"}
    )
    _assert_invalid("journal.update", {"journal_id": 8, "changes": {"type": "bank"}})
    _assert_invalid(
        "tax.create",
        {"name": "Tax", "type_tax_use": "sale", "amount_type": "group", "amount": 10},
    )
    _assert_invalid(
        "tax.create",
        {
            "name": "Tax",
            "type_tax_use": "sale",
            "amount_type": "percent",
            "amount": True,
        },
    )
    _assert_invalid(
        "tax.create",
        {
            "name": "Tax",
            "type_tax_use": "sale",
            "amount_type": "percent",
            "amount": 1000001,
        },
    )
    _assert_invalid("tax.update", {"tax_id": 9, "changes": {}})
    for forbidden in ("company_id", "children_tax_ids", "invoice_repartition_line_ids"):
        _assert_invalid("tax.update", {"tax_id": 9, "changes": {forbidden: []}})


def test_accounting_config_write_responses_reuse_core_write_result() -> None:
    registry = _registry()
    for capability_id in BATCH_IDS:
        schema = registry.load_schema(
            registry.describe(capability_id)["schemas"]["response"]
        )
        assert schema["allOf"][1]["properties"]["data"] == {
            "oneOf": [
                {"type": "null"},
                {"$ref": "core-write-result.schema.json"},
            ]
        }
