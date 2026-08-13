from __future__ import annotations

import copy
import hashlib
import json
import re

import pytest

from odoo_accounting_cli_v4.registry import (
    InstanceValidationError,
    RegistryError,
    _validate_descriptor,
    load_registry,
)


EXPECTED_CAPABILITY_COUNT = 102
EXPECTED_CAPABILITY_IDS_SHA256 = (
    "2d340b3b7dd406474775655c5efa0444d1e5afee96b0dcdc399e811521278773"
)
EXPECTED_FIRST_CAPABILITY_SHA256 = (
    "7b15597c6b11ea1a421b1a8ca56f25b653492951ee0efd3c9e1c70c06b448216"
)
IMPLEMENTED_READS = {
    "account.account.list": "account_account_list",
    "company.accounting_context.list": "company_accounting_context_list",
    "journal.list": "journal_list",
    "tax.list": "tax_list",
    "payment_term.list": "payment_term_list",
    "currency.list": "currency_list",
    "journal_entry.search": "journal_entry_search",
    "journal_entry.get": "journal_entry_get",
    "report.trial_balance": "report_trial_balance",
    "report.balance_sheet": "report_balance_sheet",
    "report.profit_and_loss": "report_profit_and_loss",
    "report.cash_flow": "report_cash_flow",
}


def test_registry_contains_the_frozen_full_matrix() -> None:
    registry = load_registry()

    assert len(registry.ids()) == EXPECTED_CAPABILITY_COUNT
    assert hashlib.sha256("\n".join(registry.ids()).encode()).hexdigest() == (
        EXPECTED_CAPABILITY_IDS_SHA256
    )
    assert re.fullmatch(r"[0-9a-f]{64}", registry.digest)

    domains = {registry.describe(item)["domain"] for item in registry.ids()}
    assert {
        "accounting_context",
        "accounting_master_data",
        "general_ledger",
        "invoices_and_bills",
        "receivables_payables",
        "payments",
        "bank_reconciliation",
        "multicurrency",
        "assets",
        "deferrals",
        "inventory_accounting",
        "purchase_accounting",
        "sales_accounting",
        "financial_reports",
        "localization_china",
        "localization_singapore",
        "diagnostics",
        "validation",
        "operations",
    } <= domains


def test_first_capability_is_byte_semantically_unchanged() -> None:
    registry = load_registry()

    descriptor = registry.describe("account.account.list")
    canonical = json.dumps(
        descriptor,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    assert hashlib.sha256(canonical).hexdigest() == EXPECTED_FIRST_CAPABILITY_SHA256
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
        "reason_code": "runtime_context_required",
        "reason": "Static registry metadata does not declare target-specific runtime availability; availability is evaluated for each configured database, company, and user.",
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
    assert descriptor["tests"]["integration"] == {
        "status": "implemented",
        "references": ["tests/integration/test_account_account_list_live.py"],
        "reason": "The live integration test verifies the real local Odoo bridge against both dedicated synthetic database aliases, including two-page cursor ordering and non-overlap.",
    }


def test_every_unimplemented_capability_is_honestly_disabled_without_a_handler() -> None:
    registry = load_registry()

    for capability_id in registry.ids():
        if capability_id in IMPLEMENTED_READS:
            continue
        descriptor = registry.describe(capability_id)
        assert descriptor["handler_key"] is None
        assert descriptor["status"] == {
            "value": "disabled",
            "reason_code": "implementation_pending",
            "reason": "The capability is frozen in the G3 matrix but has no implementation or allowlisted handler.",
        }
        assert {definition["status"] for definition in descriptor["tests"].values()} == {
            "planned"
        }
        assert all(
            definition["references"] == []
            for definition in descriptor["tests"].values()
        )


def test_implemented_reads_have_specialized_contracts_and_runtime_status() -> None:
    registry = load_registry()

    for capability_id, handler_key in IMPLEMENTED_READS.items():
        descriptor = registry.describe(capability_id)
        assert descriptor["handler_key"] == handler_key
        assert descriptor["schemas"] == {
            "request": f"schemas/v1/{capability_id}.request.schema.json",
            "response": f"schemas/v1/{capability_id}.response.schema.json",
        }
        assert descriptor["status"]["value"] == "unconfigured"
        assert descriptor["status"]["reason_code"] == "runtime_context_required"
        assert descriptor["tests"]["unit"]["status"] == "implemented"
        assert descriptor["tests"]["integration"]["status"] == "implemented"
        if capability_id in {"journal_entry.search", "journal_entry.get"}:
            expected_live_test = "tests/integration/test_journal_entries_live.py"
        elif capability_id == "report.trial_balance":
            expected_live_test = "tests/integration/test_trial_balance_live.py"
        elif capability_id == "report.balance_sheet":
            expected_live_test = "tests/integration/test_balance_sheet_live.py"
        elif capability_id == "report.profit_and_loss":
            expected_live_test = "tests/integration/test_profit_and_loss_live.py"
        elif capability_id == "report.cash_flow":
            expected_live_test = "tests/integration/test_cash_flow_live.py"
        elif capability_id == "company.accounting_context.list":
            expected_live_test = (
                "tests/integration/test_company_accounting_context_live.py"
            )
        else:
            expected_live_test = (
                "tests/integration/test_account_account_list_live.py"
                if capability_id == "account.account.list"
                else "tests/integration/test_master_data_lists_live.py"
            )
        assert descriptor["tests"]["integration"]["references"] == [
            expected_live_test
        ]


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
