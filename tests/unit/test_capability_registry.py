from __future__ import annotations

import copy
import re

import pytest

from odoo_accounting_cli_v4.registry import (
    InstanceValidationError,
    RegistryError,
    _validate_descriptor,
    load_registry,
)


def test_registry_contains_a_complete_first_capability() -> None:
    registry = load_registry()

    assert registry.ids() == ("account.account.list",)
    assert re.fullmatch(r"[0-9a-f]{64}", registry.digest)

    descriptor = registry.describe("account.account.list")
    assert descriptor["domain"] == "chart_of_accounts"
    assert descriptor["access"] == "read"
    assert descriptor["source"]["modules"] == ["account", "base"]
    assert descriptor["source"]["models"] == ["account.account", "res.company"]
    assert descriptor["requirements"]["company"] == "required"
    assert descriptor["requirements"]["groups"] == ["base.group_user"]
    assert descriptor["requirements"]["acl"] == [
        "res.company:read",
        "account.account:read",
    ]
    assert descriptor["status"] == {
        "value": "unconfigured",
        "reason_code": "bridge_configuration_missing",
        "reason": "The implementation exists, but no real Odoo bridge configuration is active.",
    }
    assert descriptor["handler_key"] == "account_account_list"
    assert "会计科目" in descriptor["routing"]["aliases"]["zh_CN"]
    assert "科目余额" in descriptor["routing"]["not_for"]["zh_CN"]
    assert set(descriptor["strategies"]) == {
        "preview",
        "execute",
        "verify",
        "idempotency",
        "reverse",
    }
    assert set(descriptor["tests"]) == {"unit", "integration", "golden", "e2e"}


def test_registry_schema_references_resolve_to_public_files() -> None:
    registry = load_registry()
    descriptor = registry.describe("account.account.list")

    request_schema = registry.load_schema(descriptor["schemas"]["request"])
    response_schema = registry.load_schema(descriptor["schemas"]["response"])

    assert request_schema["$id"].endswith("account.account.list.request.schema.json")
    assert response_schema["$id"].endswith("account.account.list.response.schema.json")
    assert request_schema["additionalProperties"] is False
    assert response_schema["additionalProperties"] is False


def test_runtime_registry_validation_rejects_schema_invalid_status_metadata() -> None:
    descriptor = copy.deepcopy(load_registry().describe("account.account.list"))
    descriptor["status"]["reason_code"] = 7

    with pytest.raises(RegistryError):
        _validate_descriptor("account.account.list", descriptor)


def test_runtime_schema_enforces_request_and_response_semantics() -> None:
    registry = load_registry()
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
        "parameters": {"limit": 100, "cursor": ""},
    }
    invalid_response = {
        "schema_version": "v1",
        "request_id": request["request_id"],
        "success": True,
        "capability": "account.account.list",
        "status": "verified",
        "data": None,
        "warnings": [],
        "error": {
            "code": "impossible",
            "message": "success and error cannot coexist",
            "details": {},
            "retryable": False,
        },
        "odoo": {
            "database": "v4-dev",
            "company_id": 7,
            "user_id": 42,
            "model": "account.account",
            "record_ids": [],
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": None,
            "verification": None,
        },
    }

    with pytest.raises(InstanceValidationError):
        registry.validate_instance(
            "schemas/v1/account.account.list.request.schema.json", request
        )
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(
            "schemas/v1/account.account.list.response.schema.json",
            invalid_response,
        )
