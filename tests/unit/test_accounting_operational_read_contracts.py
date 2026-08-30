from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from referencing import Registry, Resource

from odoo_accounting_cli_v4.capabilities.core_object_reads import (
    CoreObjectReadError,
    read_core_object,
    validate_core_object_read_request,
)
from odoo_accounting_cli_v4.contracts import success_document

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas" / "v1"
REQUEST_ID = "7bc39413-0d69-4092-9319-795d33f3167c"
CAPABILITY_IDS = (
    "invoice.duplicate_candidates.list",
    "invoice.tax_breakdown.inspect",
    "recurring.journal_entry.search",
    "recurring.journal_entry.get",
    "account.transfer_model.search",
    "account.transfer_model.get",
    "partner.credit_exposure.inspect",
    "journal.sequence_irregularity.list",
    "account.lock_exception.search",
    "account.lock_exception.get",
    "report.external_value.search",
    "report.external_value.get",
)
PAGED_CAPABILITY_IDS = frozenset(
    {
        "invoice.duplicate_candidates.list",
        "recurring.journal_entry.search",
        "account.transfer_model.search",
        "journal.sequence_irregularity.list",
        "account.lock_exception.search",
        "report.external_value.search",
    }
)
PARAMETERS: dict[str, dict[str, Any]] = {
    "invoice.duplicate_candidates.list": {
        "invoice_id": 100,
        "limit": 10,
        "cursor": None,
    },
    "invoice.tax_breakdown.inspect": {"invoice_id": 102},
    "recurring.journal_entry.search": {
        "states": ["posted", "draft"],
        "auto_post_types": ["monthly", "at_date"],
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "limit": 10,
        "cursor": None,
    },
    "recurring.journal_entry.get": {"entry_id": 201},
    "account.transfer_model.search": {
        "query": "Accrual",
        "active": True,
        "limit": 10,
        "cursor": None,
    },
    "account.transfer_model.get": {"transfer_model_id": 301},
    "partner.credit_exposure.inspect": {"partner_id": 401},
    "journal.sequence_irregularity.list": {
        "journal_id": 12,
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "limit": 10,
        "cursor": None,
    },
    "account.lock_exception.search": {
        "states": ["expired", "active"],
        "user_id": 42,
        "lock_date_fields": ["tax_lock_date", "fiscalyear_lock_date"],
        "limit": 10,
        "cursor": None,
    },
    "account.lock_exception.get": {"lock_exception_id": 601},
    "report.external_value.search": {
        "report_id": 71,
        "expression_id": 73,
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "limit": 10,
        "cursor": None,
    },
    "report.external_value.get": {"external_value_id": 701},
}

RECURRING_ITEM = {
    "id": 201,
    "company_id": 7,
    "name": "MISC/2026/0001",
    "date": "2026-01-31",
    "state": "posted",
    "journal": {"id": 12, "code": "MISC", "name": "Miscellaneous"},
    "reference": None,
    "auto_post": "monthly",
    "auto_post_until": None,
    "auto_post_origin": None,
}
TRANSFER_ITEM = {
    "id": 301,
    "name": "Monthly accrual transfer",
    "active": True,
    "state": "in_progress",
    "company_id": 7,
    "journal": {"id": 12, "code": "MISC", "name": "Miscellaneous"},
    "date_start": "2026-01-01",
    "date_stop": None,
    "frequency": "month",
    "origin_accounts": [{"id": 31, "code": "6000", "name": "Expense"}],
    "destination_lines": [
        {
            "id": 302,
            "sequence": 10,
            "account": {"id": 32, "code": "1700", "name": "Prepayments"},
            "percentage": "100.0",
        }
    ],
    "move_ids_count": 2,
    "has_draft_moves": False,
    "total_percent": "100.0",
}
LOCK_ITEM = {
    "id": 601,
    "company_id": 7,
    "user": None,
    "reason": None,
    "end_datetime": "2026-08-31T12:30:00Z",
    "state": "active",
    "active": True,
    "lock_date_field": "fiscalyear_lock_date",
    "lock_date": None,
    "company_lock_date": None,
}
EXTERNAL_ITEM = {
    "id": 701,
    "company_id": 7,
    "name": "Manual adjustment",
    "date": "2026-06-30",
    "value": "125.50",
    "text_value": None,
    "report": {"id": 71, "name": "Balance Sheet"},
    "report_line": {"id": 72, "name": "Cash", "code": None},
    "expression": {"id": 73, "label": "balance"},
    "carryover_origin_line": None,
    "carryover_origin_expression_label": None,
}
ITEMS: dict[str, dict[str, Any]] = {
    "invoice.duplicate_candidates.list": {
        "id": 101,
        "company_id": 7,
        "name": "BILL/2026/0042",
        "move_type": "in_invoice",
        "state": "draft",
        "invoice_date": None,
        "reference": "SUP-42",
        "partner": None,
        "currency": {"id": 1, "code": "CNY"},
        "amount_total": "100.00",
    },
    "invoice.tax_breakdown.inspect": {
        "id": 102,
        "invoice": {
            "id": 102,
            "name": "INV/2026/0043",
            "move_type": "out_invoice",
            "state": "posted",
        },
        "company_id": 7,
        "currency": {"id": 1, "code": "CNY"},
        "amount_untaxed": "100.00",
        "amount_tax": "13.00",
        "amount_total": "113.00",
        "has_tax_groups": True,
        "subtotals": [
            {
                "name": "Untaxed Amount",
                "base_amount": "100.00",
                "tax_amount": "13.00",
                "tax_groups": [
                    {
                        "id": 21,
                        "name": "VAT 13%",
                        "base_amount": "100.00",
                        "tax_amount": "13.00",
                    }
                ],
            }
        ],
    },
    "recurring.journal_entry.search": RECURRING_ITEM,
    "recurring.journal_entry.get": RECURRING_ITEM,
    "account.transfer_model.search": TRANSFER_ITEM,
    "account.transfer_model.get": TRANSFER_ITEM,
    "partner.credit_exposure.inspect": {
        "id": 401,
        "partner": {"id": 401, "name": "ABC Customer"},
        "company_id": 7,
        "company_currency": {"id": 1, "code": "CNY"},
        "credit": "200.00",
        "debit": "25.00",
        "credit_to_invoice": "50.00",
        "credit_limit": "1000.00",
        "use_partner_credit_limit": True,
        "days_sales_outstanding": "12.5",
        "total_invoiced": "500.00",
    },
    "journal.sequence_irregularity.list": {
        "id": 501,
        "company_id": 7,
        "name": "MISC/2026/0042",
        "date": "2026-06-30",
        "state": "posted",
        "move_type": "entry",
        "journal": {"id": 12, "code": "MISC", "name": "Miscellaneous"},
        "sequence_prefix": "MISC/2026/",
        "sequence_number": 42,
        "made_sequence_gap": True,
    },
    "account.lock_exception.search": LOCK_ITEM,
    "account.lock_exception.get": LOCK_ITEM,
    "report.external_value.search": EXTERNAL_ITEM,
    "report.external_value.get": EXTERNAL_ITEM,
}


def _request(capability_id: str) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "zh_CN",
            "timezone": "Asia/Shanghai",
        },
        "parameters": deepcopy(PARAMETERS[capability_id]),
    }


def _load_schema(name: str) -> dict[str, Any]:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def _schema_validator(name: str) -> Draft202012Validator:
    resources: dict[str, Resource[Any]] = {}
    resource_names = [
        "request.schema.json",
        "response.schema.json",
        *[
            f"{capability_id}.{kind}.schema.json"
            for capability_id in CAPABILITY_IDS
            for kind in ("request", "response")
        ],
    ]
    for resource_name in resource_names:
        schema = _load_schema(resource_name)
        resource = Resource.from_contents(schema)
        resources[resource_name] = resource
        resources[schema["$id"]] = resource
    return Draft202012Validator(
        _load_schema(name),
        registry=Registry().with_resources(resources.items()),
        format_checker=FormatChecker(),
    )


class _Port:
    user_id = 42

    def __init__(self, item: dict[str, Any]) -> None:
        self.item = item

    def read(self, **_: Any) -> dict[str, Any]:
        return {
            "user_id": 42,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "cursor_found": True,
            "items": [deepcopy(self.item)],
        }


@pytest.mark.parametrize("capability_id", CAPABILITY_IDS)
def test_requests_are_closed_normalized_and_schema_valid(
    capability_id: str,
) -> None:
    request_name = f"{capability_id}.request.schema.json"
    response_name = f"{capability_id}.response.schema.json"
    Draft202012Validator.check_schema(_load_schema(request_name))
    Draft202012Validator.check_schema(_load_schema(response_name))
    _schema_validator(request_name).validate(_request(capability_id))

    _, _, normalized = validate_core_object_read_request(
        capability_id, _request(capability_id)
    )
    if capability_id in PAGED_CAPABILITY_IDS:
        assert normalized["limit"] == 10
        assert normalized["cursor"] is None
    else:
        assert normalized == PARAMETERS[capability_id]

    invalid = _request(capability_id)
    invalid["parameters"]["sudo"] = True
    with pytest.raises(CoreObjectReadError) as caught:
        validate_core_object_read_request(capability_id, invalid)
    assert caught.value.code == "invalid_request"
    with pytest.raises(ValidationError):
        _schema_validator(request_name).validate(invalid)


@pytest.mark.parametrize("capability_id", CAPABILITY_IDS)
def test_result_validators_and_response_schemas_share_the_closed_item(
    capability_id: str,
) -> None:
    item = deepcopy(ITEMS[capability_id])
    data = read_core_object(capability_id, _Port(item), _request(capability_id))
    expected = (
        {"items": [item], "has_more": False, "next_cursor": None}
        if capability_id in PAGED_CAPABILITY_IDS
        else item
    )
    assert data == expected

    response = success_document(
        capability_id,
        data,
        request_id=REQUEST_ID,
        database="v4-dev",
        company_id=7,
        user_id=42,
        model="accounting.read",
        record_ids=[item["id"]],
    )
    response_name = f"{capability_id}.response.schema.json"
    _schema_validator(response_name).validate(response)

    invalid = deepcopy(response)
    invalid_item = (
        invalid["data"]["items"][0]
        if capability_id in PAGED_CAPABILITY_IDS
        else invalid["data"]
    )
    invalid_item["sudo"] = True
    with pytest.raises(ValidationError):
        _schema_validator(response_name).validate(invalid)


def test_request_semantics_reject_reversed_dates_and_duplicate_enum_values() -> None:
    reversed_dates = _request("report.external_value.search")
    reversed_dates["parameters"].update(
        {"date_from": "2026-12-31", "date_to": "2026-01-01"}
    )
    with pytest.raises(CoreObjectReadError):
        validate_core_object_read_request(
            "report.external_value.search", reversed_dates
        )

    duplicate_states = _request("account.lock_exception.search")
    duplicate_states["parameters"]["states"] = ["active", "active"]
    with pytest.raises(CoreObjectReadError):
        validate_core_object_read_request(
            "account.lock_exception.search", duplicate_states
        )


def test_sequence_irregularity_rejects_a_false_gap_marker() -> None:
    capability_id = "journal.sequence_irregularity.list"
    item = deepcopy(ITEMS[capability_id])
    item["made_sequence_gap"] = False

    with pytest.raises(CoreObjectReadError) as caught:
        read_core_object(capability_id, _Port(item), _request(capability_id))
    assert caught.value.code == "failed_validation"

    response = success_document(
        capability_id,
        {"items": [item], "has_more": False, "next_cursor": None},
        request_id=REQUEST_ID,
        database="v4-dev",
        company_id=7,
        user_id=42,
        model="account.move",
        record_ids=[item["id"]],
    )
    with pytest.raises(ValidationError):
        _schema_validator(
            "journal.sequence_irregularity.list.response.schema.json"
        ).validate(response)
