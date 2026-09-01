from __future__ import annotations

import hashlib
from functools import cache
from pathlib import Path

import pytest

from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

READ_IDS = {"partner.search", "partner.get"}
WRITE_IDS = {
    "partner.create",
    "partner.update",
    "partner.archive",
    "partner.restore",
    "partner.accounting.update",
    "partner.bank_account.create",
    "partner.bank_account.update",
    "partner.bank_account.archive",
    "partner.bank_account.restore",
}
BATCH_IDS = READ_IDS | WRITE_IDS
UNIT_REFERENCES = [
    "tests/unit/test_partner_master_data.py",
    "tests/unit/test_partner_master_data_runtime.py",
    "tests/unit/test_partner_master_data_cli.py",
    "tests/unit/test_partner_master_data_registry.py",
]
INTEGRATION_REFERENCE = "tests/integration/test_partner_master_data_batch_live.py"
INTEGRATION_REASON = (
    "The shared guarded transactional smoke passed the full 11-capability chain in "
    "both isolated databases, verifying search/get visibility, private-marker "
    "stripping on get, first execution plus immediate replay for all nine writes, "
    "and rollback of partner/bank fixtures and the temporary partner-manager grant; "
    "the grant is test-only and does not establish default user permission."
)
EXPECTED_UNIT_REASONS = {
    "partner.search": (
        "Unit tests cover the exact search filters, normalized defaults, page and "
        "fail-closed result contracts, fixed company-scoped runtime normalization "
        "with private-marker stripping, declared ACL/group metadata, registry "
        "schemas, and CLI dispatch."
    ),
    "partner.get": (
        "Unit tests cover the exact identifier, item and fail-closed result "
        "contracts, fixed company-scoped runtime normalization with private-marker "
        "stripping, declared ACL/group metadata, registry schemas, and CLI dispatch."
    ),
    "partner.create": (
        "Unit tests cover the closed normalized create contract, optional-field "
        "normalization, reserved-marker rejection, deterministic full-parameter "
        "key, fixed company-scoped creation and visible-ref immediate replay, "
        "declared ACL/group metadata, fail-closed schemas/results, and CLI dispatch."
    ),
    "partner.update": (
        "Unit tests cover the closed partner mutation contracts, explicit-null "
        "handling where applicable, fixed company-scoped target/state rechecks and "
        "immediate replay, declared ACL/group metadata, fail-closed schemas/results, "
        "and CLI dispatch."
    ),
    "partner.archive": (
        "Unit tests cover the closed partner mutation contracts, explicit-null "
        "handling where applicable, fixed company-scoped target/state rechecks and "
        "immediate replay, declared ACL/group metadata, fail-closed schemas/results, "
        "and CLI dispatch."
    ),
    "partner.restore": (
        "Unit tests cover the closed partner mutation contracts, explicit-null "
        "handling where applicable, fixed company-scoped target/state rechecks and "
        "immediate replay, declared ACL/group metadata, fail-closed schemas/results, "
        "and CLI dispatch."
    ),
    "partner.accounting.update": (
        "Unit tests cover the closed accounting-property whitelist and explicit-null "
        "clears, child-partner rejection, fixed target-state recheck and immediate "
        "replay, declared accounting-user/partner-manager and ACL metadata, "
        "fail-closed schemas/results, and CLI dispatch."
    ),
    "partner.bank_account.create": (
        "Unit tests cover the closed bank-account contracts, owner/company isolation, "
        "reserved-marker rejection, fixed create/update/lifecycle state rechecks and "
        "immediate replay, declared ACL/group metadata, fail-closed schemas/results, "
        "and CLI dispatch."
    ),
    "partner.bank_account.update": (
        "Unit tests cover the closed bank-account contracts, owner/company isolation, "
        "reserved-marker rejection, fixed create/update/lifecycle state rechecks and "
        "immediate replay, declared ACL/group metadata, fail-closed schemas/results, "
        "and CLI dispatch."
    ),
    "partner.bank_account.archive": (
        "Unit tests cover the closed bank-account contracts, owner/company isolation, "
        "reserved-marker rejection, fixed create/update/lifecycle state rechecks and "
        "immediate replay, declared ACL/group metadata, fail-closed schemas/results, "
        "and CLI dispatch."
    ),
    "partner.bank_account.restore": (
        "Unit tests cover the closed bank-account contracts, owner/company isolation, "
        "reserved-marker rejection, fixed create/update/lifecycle state rechecks and "
        "immediate replay, declared ACL/group metadata, fail-closed schemas/results, "
        "and CLI dispatch."
    ),
}

EXPECTED_MODELS = {
    "partner.search": {
        "res.company",
        "res.partner",
        "res.country.state",
        "res.country",
    },
    "partner.get": {
        "res.company",
        "res.partner",
        "res.country.state",
        "res.country",
    },
    "partner.create": {
        "res.company",
        "res.partner",
        "res.country.state",
        "res.country",
    },
    "partner.update": {
        "res.company",
        "res.partner",
        "res.country.state",
        "res.country",
    },
    "partner.archive": {"res.company", "res.partner"},
    "partner.restore": {"res.company", "res.partner"},
    "partner.accounting.update": {
        "res.company",
        "res.partner",
        "account.account",
        "account.fiscal.position",
        "account.payment.term",
    },
    "partner.bank_account.create": {
        "res.company",
        "res.partner",
        "res.partner.bank",
        "res.bank",
        "res.currency",
    },
    "partner.bank_account.update": {
        "res.company",
        "res.partner",
        "res.partner.bank",
        "res.bank",
        "res.currency",
    },
    "partner.bank_account.archive": {
        "res.company",
        "res.partner",
        "res.partner.bank",
    },
    "partner.bank_account.restore": {
        "res.company",
        "res.partner",
        "res.partner.bank",
    },
}
EXPECTED_ACL = {
    "partner.search": {
        "res.company:read",
        "res.partner:read",
        "res.country.state:read",
        "res.country:read",
    },
    "partner.get": {
        "res.company:read",
        "res.partner:read",
        "res.country.state:read",
        "res.country:read",
    },
    "partner.create": {
        "res.company:read",
        "res.partner:read",
        "res.partner:create",
        "res.country.state:read",
        "res.country:read",
    },
    "partner.update": {
        "res.company:read",
        "res.partner:read",
        "res.partner:write",
        "res.country.state:read",
        "res.country:read",
    },
    "partner.archive": {
        "res.company:read",
        "res.partner:read",
        "res.partner:write",
    },
    "partner.restore": {
        "res.company:read",
        "res.partner:read",
        "res.partner:write",
    },
    "partner.accounting.update": {
        "res.company:read",
        "res.partner:read",
        "res.partner:write",
        "account.account:read",
        "account.fiscal.position:read",
        "account.payment.term:read",
    },
    "partner.bank_account.create": {
        "res.company:read",
        "res.partner:read",
        "res.partner.bank:read",
        "res.partner.bank:create",
        "res.bank:read",
        "res.currency:read",
    },
    "partner.bank_account.update": {
        "res.company:read",
        "res.partner:read",
        "res.partner.bank:read",
        "res.partner.bank:write",
        "res.bank:read",
        "res.currency:read",
    },
    "partner.bank_account.archive": {
        "res.company:read",
        "res.partner:read",
        "res.partner.bank:read",
        "res.partner.bank:write",
    },
    "partner.bank_account.restore": {
        "res.company:read",
        "res.partner:read",
        "res.partner.bank:read",
        "res.partner.bank:write",
    },
}
EXPECTED_PARAMETER_FIELDS = {
    "partner.search": {
        "query",
        "active",
        "company_type",
        "customer",
        "supplier",
        "limit",
        "cursor",
    },
    "partner.get": {"partner_id"},
    "partner.create": {
        "name",
        "company_type",
        "vat",
        "reference",
        "email",
        "phone",
        "mobile",
        "street",
        "street2",
        "city",
        "zip",
        "state_id",
        "country_id",
        "language",
    },
    "partner.update": {"partner_id", "changes"},
    "partner.archive": {"partner_id"},
    "partner.restore": {"partner_id"},
    "partner.accounting.update": {"partner_id", "changes"},
    "partner.bank_account.create": {
        "partner_id",
        "account_number",
        "account_holder_name",
        "bank_id",
        "currency_id",
    },
    "partner.bank_account.update": {"partner_bank_id", "changes"},
    "partner.bank_account.archive": {"partner_bank_id"},
    "partner.bank_account.restore": {"partner_bank_id"},
}
VALID_PARAMETERS = {
    "partner.search": {
        "query": "Acme",
        "active": True,
        "company_type": "company",
        "customer": True,
        "supplier": False,
        "limit": 25,
        "cursor": None,
    },
    "partner.get": {"partner_id": 7},
    "partner.create": {
        "name": "Acme Japan",
        "company_type": "company",
        "vat": "JP123",
        "reference": "CUST-7",
        "email": "accounting@example.test",
        "phone": "+81-3-1234-5678",
        "mobile": "+81-90-1234-5678",
        "street": "1 Marunouchi",
        "street2": "Suite 7",
        "city": "Tokyo",
        "zip": "100-0005",
        "state_id": 13,
        "country_id": 108,
        "language": "ja_JP",
    },
    "partner.update": {
        "partner_id": 7,
        "changes": {
            "name": "Acme Japan GK",
            "reference": None,
            "country_id": 108,
            "language": None,
        },
    },
    "partner.archive": {"partner_id": 7},
    "partner.restore": {"partner_id": 7},
    "partner.accounting.update": {
        "partner_id": 7,
        "changes": {
            "property_account_receivable_id": 110,
            "property_account_payable_id": None,
            "property_account_position_id": 4,
            "property_payment_term_id": 5,
            "property_supplier_payment_term_id": None,
        },
    },
    "partner.bank_account.create": {
        "partner_id": 7,
        "account_number": "JP00-TEST-123",
        "account_holder_name": "Acme Japan GK",
        "bank_id": 8,
        "currency_id": None,
    },
    "partner.bank_account.update": {
        "partner_bank_id": 19,
        "changes": {
            "account_number": "JP00-TEST-456",
            "account_holder_name": None,
            "bank_id": 8,
            "currency_id": 1,
        },
    },
    "partner.bank_account.archive": {"partner_bank_id": 19},
    "partner.bank_account.restore": {"partner_bank_id": 19},
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


def _validate_request(capability_id: str, parameters: dict[str, object]) -> None:
    registry = _registry()
    registry.validate_instance(
        registry.describe(capability_id)["schemas"]["request"],
        _request(parameters),
    )


def _assert_invalid(capability_id: str, parameters: dict[str, object]) -> None:
    with pytest.raises(InstanceValidationError):
        _validate_request(capability_id, parameters)


def _response(
    capability_id: str,
    *,
    success: bool,
    data: object,
    error: object,
) -> dict[str, object]:
    return {
        "schema_version": "v1",
        "request_id": "123e4567-e89b-42d3-a456-426614174000",
        "success": success,
        "capability": capability_id,
        "status": "verified" if success else "failed_validation",
        "data": data,
        "warnings": [],
        "error": error,
        "odoo": {
            "database": "odoo_cli_v4_dev",
            "company_id": 1,
            "user_id": 2,
            "model": "res.partner",
            "record_ids": [7],
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": None,
            "verification": None,
        },
    }


def _write_result() -> dict[str, object]:
    return {
        "idempotent_replay": False,
        "result": {
            "model": "res.partner",
            "id": 7,
            "name": "Acme Japan",
            "state": "active",
            "company_id": 1,
            "move_type": None,
            "source_id": None,
            "line_ids": [],
            "partial_reconcile_ids": [],
            "full_reconcile_id": None,
            "reconciled": False,
        },
    }


def _partner_item() -> dict[str, object]:
    return {
        "id": 7,
        "name": "Acme Japan",
        "display_name": "Acme Japan",
        "company_type": "company",
        "active": True,
        "vat": "JP123",
        "reference": "CUST-7",
        "email": "accounting@example.test",
        "phone": None,
        "mobile": None,
        "street": "1 Marunouchi",
        "street2": None,
        "city": "Tokyo",
        "zip": "100-0005",
        "state": {"id": 13, "name": "Tokyo"},
        "country": {"id": 108, "name": "Japan"},
        "language": "ja_JP",
        "company_id": 1,
        "parent": None,
        "customer_rank": 1,
        "supplier_rank": 0,
    }


def test_partner_batch_registry_counts_handlers_and_schema_inventory_are_exact() -> (
    None
):
    registry = _registry()
    ids = registry.ids()

    assert len(ids) == 357
    assert (
        sum(registry.describe(item)["handler_key"] is not None for item in ids) == 342
    )
    assert (
        sum(
            registry.describe(item)["handler_key"] is not None
            and registry.describe(item)["access"] == "read"
            for item in ids
        )
        == 210
    )
    assert (
        sum(
            registry.describe(item)["handler_key"] is not None
            and registry.describe(item)["access"] == "write"
            for item in ids
        )
        == 132
    )
    statuses = [registry.describe(item)["status"]["value"] for item in ids]
    assert statuses.count("disabled") == 15
    assert statuses.count("unconfigured") == 309
    assert statuses.count("degraded") == 33
    assert (
        hashlib.sha256("\n".join(ids).encode()).hexdigest()
        == "70afbb625e34ce065b06e4d058fd1ff9c41b17174f80e15109b246e0824ec8c3"
    )
    schema_root = Path(__file__).resolve().parents[2] / "schemas" / "v1"
    assert len(list(schema_root.glob("*.schema.json"))) == 689


def test_partner_batch_registry_models_acl_groups_and_evidence_are_exact() -> None:
    registry = _registry()

    assert set(EXPECTED_MODELS) == BATCH_IDS
    assert set(EXPECTED_ACL) == BATCH_IDS
    assert set(EXPECTED_UNIT_REASONS) == BATCH_IDS
    for capability_id in BATCH_IDS:
        descriptor = registry.describe(capability_id)
        assert descriptor["access"] == (
            "read" if capability_id in READ_IDS else "write"
        )
        assert descriptor["handler_key"] == {
            "partner.search": "partner_search",
            "partner.get": "partner_get",
        }.get(capability_id, "core_write")
        assert descriptor["source"]["modules"] == ["base", "account"]
        assert set(descriptor["source"]["models"]) == EXPECTED_MODELS[capability_id]
        assert set(descriptor["requirements"]["acl"]) == EXPECTED_ACL[capability_id]
        assert all(":unlink" not in item for item in descriptor["requirements"]["acl"])
        expected_groups = (
            ["account.group_account_readonly"]
            if capability_id in READ_IDS
            else (
                ["account.group_account_user", "base.group_partner_manager"]
                if capability_id == "partner.accounting.update"
                else ["base.group_partner_manager"]
            )
        )
        assert descriptor["requirements"]["groups"] == expected_groups
        assert descriptor["tests"]["unit"] == {
            "status": "implemented",
            "references": UNIT_REFERENCES,
            "reason": EXPECTED_UNIT_REASONS[capability_id],
        }
        assert descriptor["tests"]["integration"] == {
            "status": "implemented",
            "references": [INTEGRATION_REFERENCE],
            "reason": INTEGRATION_REASON,
        }
        for evidence_kind in ("golden", "e2e"):
            assert descriptor["tests"][evidence_kind]["status"] == "planned"
            assert descriptor["tests"][evidence_kind]["references"] == []

    create = registry.describe("partner.create")
    assert create["status"]["value"] == "degraded"
    assert (
        create["status"]["reason_code"]
        == "odoo_native_partner_ref_idempotency_field_unavailable"
    )
    assert "visible [ODACV4:<digest>] marker" in create["status"]["reason"]
    assert "no database uniqueness constraint" in create["status"]["reason"]
    assert "concurrent exactly-once" in create["status"]["reason"]
    assert (
        "full_normalized_parameters_digest32" in (create["strategies"]["idempotency"])
    )

    for capability_id in BATCH_IDS - {"partner.create"}:
        descriptor = registry.describe(capability_id)
        assert descriptor["status"]["value"] == "unconfigured"
        assert descriptor["status"]["reason_code"] == "runtime_context_required"
        assert "unimplemented" not in descriptor["status"]["reason"].lower()
        if capability_id in WRITE_IDS:
            idempotency = descriptor["strategies"]["idempotency"]
            assert "result_replay" not in idempotency
            assert "without_operation_store" in idempotency
            assert "intermediate_changes" in idempotency
            assert "Temporary live-test grants" in descriptor["status"]["reason"]


def test_partner_batch_request_schemas_freeze_exact_fields_and_accept_fixtures() -> (
    None
):
    registry = _registry()

    for capability_id, parameters in VALID_PARAMETERS.items():
        _validate_request(capability_id, parameters)
        schema = registry.load_schema(
            registry.describe(capability_id)["schemas"]["request"]
        )
        parameter_schema = schema["properties"]["parameters"]
        assert parameter_schema["additionalProperties"] is False
        assert (
            set(parameter_schema["properties"])
            == EXPECTED_PARAMETER_FIELDS[capability_id]
        )

    assert registry.load_schema("schemas/v1/partner.create.request.schema.json")[
        "properties"
    ]["parameters"]["required"] == ["name", "company_type"]
    for capability_id in (
        "partner.update",
        "partner.accounting.update",
        "partner.bank_account.update",
    ):
        changes = registry.load_schema(
            f"schemas/v1/{capability_id}.request.schema.json"
        )["properties"]["parameters"]["properties"]["changes"]
        assert changes["additionalProperties"] is False
        assert changes["minProperties"] == 1


def test_partner_requests_reject_unknown_unsafe_empty_and_bad_identifier_fields() -> (
    None
):
    for capability_id, id_field in {
        "partner.get": "partner_id",
        "partner.archive": "partner_id",
        "partner.restore": "partner_id",
        "partner.bank_account.archive": "partner_bank_id",
        "partner.bank_account.restore": "partner_bank_id",
    }.items():
        _assert_invalid(capability_id, {id_field: 0})
        _assert_invalid(capability_id, {id_field: 7, "force": True})

    _assert_invalid("partner.search", {"query": " Acme"})
    _assert_invalid("partner.search", {"query": "Acme "})
    _assert_invalid("partner.search", {"query": ""})
    _assert_invalid("partner.search", {"company_type": "organization"})
    _assert_invalid("partner.search", {"limit": 1001})

    _assert_invalid("partner.update", {"partner_id": 7, "changes": {}})
    _assert_invalid(
        "partner.accounting.update",
        {"partner_id": 7, "changes": {}},
    )
    _assert_invalid(
        "partner.bank_account.update",
        {"partner_bank_id": 19, "changes": {}},
    )
    for forbidden in (
        "values",
        "parent_id",
        "company_id",
        "user_id",
        "bank_ids",
        "trust",
        "allow_out_payment",
    ):
        _assert_invalid(
            "partner.update",
            {"partner_id": 7, "changes": {forbidden: True}},
        )
    _assert_invalid(
        "partner.accounting.update",
        {"partner_id": 7, "changes": {"property_account_receivable_id": 0}},
    )
    _assert_invalid(
        "partner.accounting.update",
        {"partner_id": 7, "changes": {"property_account_receivable_id": "110"}},
    )


def test_partner_and_bank_text_fields_enforce_trim_length_null_and_marker_rules() -> (
    None
):
    for field in (
        "vat",
        "reference",
        "email",
        "phone",
        "mobile",
        "street",
        "street2",
        "city",
        "zip",
    ):
        parameters = {"name": "Acme", "company_type": "company", field: None}
        _assert_invalid("partner.create", parameters)
        _assert_invalid(
            "partner.create",
            {"name": "Acme", "company_type": "company", field: " x"},
        )
        _assert_invalid(
            "partner.create",
            {"name": "Acme", "company_type": "company", field: "x "},
        )
        _validate_request(
            "partner.update",
            {"partner_id": 7, "changes": {field: None}},
        )

    for field in ("name", "reference"):
        create = {"name": "Acme", "company_type": "company"}
        create[field] = "Acme [ODACV4:reserved]"
        _assert_invalid("partner.create", create)
        _assert_invalid(
            "partner.update",
            {
                "partner_id": 7,
                "changes": {field: "Acme [ODACV4:reserved]"},
            },
        )
    _assert_invalid(
        "partner.update",
        {"partner_id": 7, "changes": {"name": None}},
    )
    _assert_invalid(
        "partner.update",
        {"partner_id": 7, "changes": {"company_type": None}},
    )
    _validate_request(
        "partner.create",
        {"name": "Acme", "company_type": "company", "language": None},
    )
    _assert_invalid(
        "partner.create",
        {"name": "Acme", "company_type": "company", "language": " en_US"},
    )

    for capability_id, parameters_key in {
        "partner.bank_account.create": "parameters",
        "partner.bank_account.update": "changes",
    }.items():
        base = (
            {"partner_id": 7, "account_number": "JP-1"}
            if capability_id.endswith(".create")
            else {"partner_bank_id": 19, "changes": {"account_number": "JP-1"}}
        )
        for field in ("account_number", "account_holder_name"):
            for value in (
                " padded",
                "padded ",
                "value [ODACV4:reserved]",
            ):
                candidate = {
                    key: (dict(item) if isinstance(item, dict) else item)
                    for key, item in base.items()
                }
                target = (
                    candidate
                    if parameters_key == "parameters"
                    else candidate["changes"]
                )
                assert isinstance(target, dict)
                target[field] = value
                _assert_invalid(capability_id, candidate)
        holder_null = {
            key: (dict(item) if isinstance(item, dict) else item)
            for key, item in base.items()
        }
        target = (
            holder_null if parameters_key == "parameters" else holder_null["changes"]
        )
        assert isinstance(target, dict)
        target["account_holder_name"] = None
        _validate_request(capability_id, holder_null)


def test_partner_read_response_item_page_and_fail_closed_contracts_are_exact() -> None:
    registry = _registry()
    search_schema = registry.load_schema(
        "schemas/v1/partner.search.response.schema.json"
    )
    item_schema = search_schema["$defs"]["item"]
    expected_item_fields = {
        "id",
        "name",
        "display_name",
        "company_type",
        "active",
        "vat",
        "reference",
        "email",
        "phone",
        "mobile",
        "street",
        "street2",
        "city",
        "zip",
        "state",
        "country",
        "language",
        "company_id",
        "parent",
        "customer_rank",
        "supplier_rank",
    }
    assert item_schema["additionalProperties"] is False
    assert set(item_schema["required"]) == expected_item_fields
    assert set(item_schema["properties"]) == expected_item_fields
    for field in ("state", "country", "parent"):
        assert item_schema["properties"][field]["oneOf"] == [
            {"type": "null"},
            {"$ref": "#/$defs/named"},
        ]
    assert item_schema["properties"]["company_id"] == {
        "type": ["integer", "null"],
        "minimum": 1,
    }
    for field in ("customer_rank", "supplier_rank"):
        assert item_schema["properties"][field] == {
            "type": "integer",
            "minimum": 0,
        }

    item = _partner_item()
    search_data = {"items": [item], "has_more": False, "next_cursor": None}
    registry.validate_instance(
        "schemas/v1/partner.search.response.schema.json",
        _response(
            "partner.search",
            success=True,
            data=search_data,
            error=None,
        ),
    )
    registry.validate_instance(
        "schemas/v1/partner.get.response.schema.json",
        _response("partner.get", success=True, data=item, error=None),
    )
    error = {
        "code": "not_found",
        "message": "Partner not found",
        "details": {},
        "retryable": False,
    }
    for capability_id in READ_IDS:
        schema_ref = f"schemas/v1/{capability_id}.response.schema.json"
        registry.validate_instance(
            schema_ref,
            _response(capability_id, success=False, data=None, error=error),
        )
        with pytest.raises(InstanceValidationError):
            registry.validate_instance(
                schema_ref,
                _response(capability_id, success=True, data=None, error=None),
            )
        with pytest.raises(InstanceValidationError):
            registry.validate_instance(
                schema_ref,
                _response(
                    capability_id,
                    success=False,
                    data=item,
                    error=error,
                ),
            )


def test_partner_write_responses_reuse_core_write_result_and_fail_closed() -> None:
    registry = _registry()
    error = {
        "code": "unauthorized",
        "message": "Permission denied",
        "details": {},
        "retryable": False,
    }

    for capability_id in WRITE_IDS:
        schema_ref = f"schemas/v1/{capability_id}.response.schema.json"
        response_schema = registry.load_schema(schema_ref)
        assert response_schema["allOf"][1]["properties"]["data"] == {
            "oneOf": [
                {"type": "null"},
                {"$ref": "core-write-result.schema.json"},
            ]
        }
        registry.validate_instance(
            schema_ref,
            _response(
                capability_id,
                success=True,
                data=_write_result(),
                error=None,
            ),
        )
        registry.validate_instance(
            schema_ref,
            _response(capability_id, success=False, data=None, error=error),
        )
        with pytest.raises(InstanceValidationError):
            registry.validate_instance(
                schema_ref,
                _response(capability_id, success=True, data=None, error=None),
            )
        with pytest.raises(InstanceValidationError):
            registry.validate_instance(
                schema_ref,
                _response(
                    capability_id,
                    success=False,
                    data=_write_result(),
                    error=error,
                ),
            )
