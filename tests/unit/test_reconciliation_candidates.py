from __future__ import annotations

import base64
import copy
from pathlib import Path

import pytest

from odoo_accounting_cli_v4.capabilities.reconciliation_candidates import (
    ReconciliationCandidatesError,
    list_reconciliation_candidates,
    validate_reconciliation_candidates_request,
)
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry


EMPTY_FILTERS = {
    "date_from": None,
    "date_to": None,
    "states": ["posted"],
    "account_id": None,
    "partner_id": None,
    "journal_id": None,
    "account_kinds": ["receivable", "payable", "other"],
    "query": None,
}


def _request(**parameters: object) -> dict:
    return {
        "schema_version": "v1",
        "request_id": "fe40da72-5faa-483b-9381-9e8de7f002fd",
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "zh_CN",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }


def _currency(record_id: int = 6, code: str = "CNY") -> dict:
    return {"id": record_id, "code": code}


def _row(
    record_id: int,
    line_date: str,
    *,
    state: str = "posted",
    account_type: str = "asset_current",
) -> dict:
    return {
        "id": record_id,
        "date": line_date,
        "invoice_date": "2025-01-20",
        "date_maturity": "2025-02-20",
        "state": state,
        "move": {
            "id": 1000 + record_id,
            "name": f"MISC/2025/{record_id:04d}",
            "move_type": "entry",
            "ref": f"REF-{record_id}",
        },
        "label": f"Candidate {record_id}",
        "account": {
            "id": 31,
            "code": "220200",
            "name": "Suspense",
            "account_type": account_type,
        },
        "partner": {"id": 16, "name": "Fixture Partner"},
        "journal": {"id": 9, "code": "BNK1", "name": "Bank", "type": "bank"},
        "company_id": 7,
        "company_currency": _currency(),
        "currency": _currency(),
        "balance": "50.00",
        "amount_currency": "50.00",
        "amount_residual": "25.00",
        "amount_residual_currency": "25.00",
        "matching_number": "P",
        # This is the rule that historically created the line, not a suggestion.
        "reconciliation_model": {"id": 4, "name": "Bank fees"},
    }


class FakePort:
    def __init__(
        self,
        *,
        rows: list[dict] | None = None,
        company_visible: bool = True,
        module_installed: bool = True,
        access_allowed: bool | None = None,
    ) -> None:
        self.user_id = 42
        self.rows = copy.deepcopy(rows or [])
        self.company_visible = company_visible
        self.module_installed = module_installed
        self.access_allowed = (
            company_visible and module_installed
            if access_allowed is None
            else access_allowed
        )
        self.calls: list[dict] = []

    def read_page(self, **kwargs) -> dict:
        self.calls.append(copy.deepcopy(kwargs))
        return {
            "user_id": self.user_id,
            "company_visible": self.company_visible,
            "module_installed": self.module_installed,
            "access_allowed": self.access_allowed,
            "rows": copy.deepcopy(self.rows[: kwargs["limit"]]),
        }


def test_defaults_mirror_the_posted_with_residual_action_and_fetch_one_extra() -> None:
    row = _row(20, "2025-01-25")
    port = FakePort(rows=[row])

    result = list_reconciliation_candidates(port, _request())

    assert result == {"items": [row], "has_more": False, "next_cursor": None}
    assert port.calls == [
        {
            "company_id": 7,
            "after": None,
            "limit": 101,
            "filters": EMPTY_FILTERS,
        }
    ]


def test_filters_are_canonical_and_cursor_uses_date_id_descending_seek() -> None:
    parameters = {
        "limit": 2,
        "date_from": "2025-01-01",
        "date_to": "2025-01-31",
        "states": ["posted", "draft"],
        "account_id": 31,
        "partner_id": 16,
        "journal_id": 9,
        "account_kinds": ["other", "receivable"],
        "query": "Manual Payment",
    }
    rows = [
        _row(22, "2025-01-25"),
        _row(21, "2025-01-25"),
        _row(20, "2025-01-24"),
    ]
    port = FakePort(rows=rows)

    first = list_reconciliation_candidates(port, _request(**parameters))

    assert [item["id"] for item in first["items"]] == [22, 21]
    assert first["has_more"] is True
    assert first["next_cursor"]
    expected_filters = {
        **EMPTY_FILTERS,
        "date_from": "2025-01-01",
        "date_to": "2025-01-31",
        "states": ["draft", "posted"],
        "account_id": 31,
        "partner_id": 16,
        "journal_id": 9,
        "account_kinds": ["receivable", "other"],
        "query": "Manual Payment",
    }
    assert port.calls[0]["filters"] == expected_filters

    replay_port = FakePort(rows=[rows[-1]])
    replay = dict(parameters, cursor=first["next_cursor"])
    second = list_reconciliation_candidates(replay_port, _request(**replay))
    assert second["items"] == [rows[-1]]
    assert replay_port.calls[0]["after"] == ["2025-01-25", 21]


def test_cursor_binds_capability_context_and_every_normalized_filter() -> None:
    parameters = {
        "limit": 1,
        "date_from": "2025-01-01",
        "date_to": "2025-01-31",
        "states": ["posted"],
        "account_id": 31,
        "partner_id": 16,
        "journal_id": 9,
        "account_kinds": ["other"],
        "query": "needle",
    }
    first = list_reconciliation_candidates(
        FakePort(rows=[_row(22, "2025-01-25"), _row(21, "2025-01-24")]),
        _request(**parameters),
    )
    cursor = first["next_cursor"]
    assert cursor

    changed_requests: list[dict] = []
    for key, value in {
        "date_from": "2025-01-02",
        "date_to": "2025-01-30",
        "states": ["draft"],
        "account_id": 32,
        "partner_id": 17,
        "journal_id": 10,
        "account_kinds": ["receivable"],
        "query": "other",
    }.items():
        changed_requests.append(_request(**{**parameters, key: value, "cursor": cursor}))
    for context_key, value in {
        "database": "other_db",
        "company_id": 8,
        "user_login": "other-user",
    }.items():
        request = _request(**{**parameters, "cursor": cursor})
        request["context"][context_key] = value
        changed_requests.append(request)

    for request in changed_requests:
        port = FakePort()
        with pytest.raises(ReconciliationCandidatesError) as caught:
            list_reconciliation_candidates(port, request)
        assert caught.value.code == "invalid_cursor"
        assert port.calls == []


def test_cursor_stays_bounded_for_long_valid_context_values() -> None:
    request = _request(limit=1)
    request["context"]["database"] = "d" * 3500
    request["context"]["user_login"] = "u" * 3500
    first = list_reconciliation_candidates(
        FakePort(rows=[_row(22, "2025-01-25"), _row(21, "2025-01-24")]),
        request,
    )

    assert first["next_cursor"] is not None
    assert len(first["next_cursor"]) <= 4096

    replay = copy.deepcopy(request)
    replay["parameters"]["cursor"] = first["next_cursor"]
    port = FakePort(rows=[_row(20, "2025-01-23")])
    list_reconciliation_candidates(port, replay)
    assert port.calls[0]["after"] == ["2025-01-25", 22]


@pytest.mark.parametrize(
    "mutate",
    [
        lambda raw: raw.replace('"version":1', '"version":1,"version":1'),
        lambda raw: raw.replace('"version":1', '"version":1.0'),
        lambda raw: raw.replace('"version":1', '"version":NaN'),
    ],
)
def test_cursor_rejects_duplicate_keys_floats_and_nonfinite_numbers(mutate) -> None:
    first = list_reconciliation_candidates(
        FakePort(rows=[_row(22, "2025-01-25"), _row(21, "2025-01-24")]),
        _request(limit=1),
    )
    raw = base64.urlsafe_b64decode(first["next_cursor"] + "==").decode()
    forged = base64.urlsafe_b64encode(mutate(raw).encode()).decode().rstrip("=")

    with pytest.raises(ReconciliationCandidatesError) as caught:
        list_reconciliation_candidates(FakePort(), _request(limit=1, cursor=forged))
    assert caught.value.code == "invalid_cursor"


@pytest.mark.parametrize(
    "parameters",
    [
        {"unexpected": True},
        {"limit": True},
        {"limit": 0},
        {"limit": 1001},
        {"cursor": ""},
        {"cursor": "x" * 4097},
        {"date_from": "2025/01/01"},
        {"date_from": "2025-02-01", "date_to": "2025-01-01"},
        {"states": []},
        {"states": ["cancel"]},
        {"states": ["posted", "posted"]},
        {"account_id": True},
        {"partner_id": 0},
        {"journal_id": 1.0},
        {"account_kinds": []},
        {"account_kinds": ["asset"]},
        {"account_kinds": ["other", "other"]},
        {"query": " untrimmed"},
        {"query": "trailing\n"},
        {"query": "x" * 201},
    ],
)
def test_invalid_requests_fail_before_the_port(parameters: dict) -> None:
    port = FakePort()
    with pytest.raises(ReconciliationCandidatesError) as caught:
        list_reconciliation_candidates(port, _request(**parameters))
    assert caught.value.code == "invalid_request"
    assert caught.value.exit_code == 2
    assert port.calls == []


def test_request_validator_exposes_the_closed_normalized_shape() -> None:
    request_id, context, filters, limit, cursor = (
        validate_reconciliation_candidates_request(_request())
    )

    assert request_id == _request()["request_id"]
    assert context["company_id"] == 7
    assert filters == EMPTY_FILTERS
    assert limit == 100
    assert cursor is None


def test_request_schema_and_python_agree_on_whitespace_boundaries() -> None:
    registry = load_registry()
    for query in ("needle\n", "\nneedle", "needle ", " needle"):
        request = _request(query=query)
        with pytest.raises(InstanceValidationError):
            registry.validate_instance(
                "schemas/v1/reconciliation.candidates.list.request.schema.json",
                request,
            )
        with pytest.raises(ReconciliationCandidatesError):
            validate_reconciliation_candidates_request(request)

    for field in ("database", "user_login", "language", "timezone"):
        request = _request()
        request["context"][field] = " \t\n"
        with pytest.raises(InstanceValidationError):
            registry.validate_instance(
                "schemas/v1/reconciliation.candidates.list.request.schema.json",
                request,
            )
        with pytest.raises(ReconciliationCandidatesError):
            validate_reconciliation_candidates_request(request)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda row: row.update(extra=True),
        lambda row: row.update(id=True),
        lambda row: row.update(company_id=8),
        lambda row: row.update(date="2025/01/25"),
        lambda row: row.update(invoice_date="2025/01/20"),
        lambda row: row.update(date_maturity="2025/02/20"),
        lambda row: row.update(state="cancel"),
        lambda row: row["move"].update(extra=True),
        lambda row: row["move"].update(id=False),
        lambda row: row["move"].update(name=""),
        lambda row: row["account"].update(code=""),
        lambda row: row["partner"].update(id=0),
        lambda row: row["journal"].update(type=""),
        lambda row: row["company_currency"].update(code="USDX"),
        lambda row: row.update(balance="01.00"),
        lambda row: row.update(amount_currency="NaN"),
        lambda row: row.update(amount_residual="0"),
        lambda row: row.update(amount_residual_currency="1e2"),
        lambda row: row["reconciliation_model"].update(name=""),
    ],
)
def test_invalid_or_impossible_rows_never_become_verified(mutation) -> None:
    row = _row(20, "2025-01-25")
    mutation(row)
    with pytest.raises(ReconciliationCandidatesError) as caught:
        list_reconciliation_candidates(FakePort(rows=[row]), _request())
    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8


@pytest.mark.parametrize("code", (" ", "BAD-CODE", "A/B", "A" * 65))
def test_account_code_matches_the_fixed_odoo_model_constraint(code: str) -> None:
    row = _row(20, "2025-01-25")
    row["account"]["code"] = code
    response = _success_response(
        {"items": [row], "has_more": False, "next_cursor": None}
    )

    with pytest.raises(InstanceValidationError):
        load_registry().validate_instance(
            "schemas/v1/reconciliation.candidates.list.response.schema.json",
            response,
        )
    with pytest.raises(ReconciliationCandidatesError) as caught:
        list_reconciliation_candidates(FakePort(rows=[row]), _request())
    assert caught.value.code == "failed_validation"


def test_default_with_residual_scope_excludes_foreign_only_residual_lines() -> None:
    row = _row(20, "2025-01-25")
    row.update(
        currency=_currency(2, "USD"),
        amount_currency="59.00",
        amount_residual="0",
        amount_residual_currency="1.00",
    )

    with pytest.raises(ReconciliationCandidatesError) as caught:
        list_reconciliation_candidates(FakePort(rows=[row]), _request())

    assert caught.value.code == "failed_validation"


def test_same_currency_requires_both_company_and_currency_amount_pairs_to_match() -> None:
    for field in ("amount_currency", "amount_residual_currency"):
        row = _row(20, "2025-01-25")
        row[field] = "49.00"
        with pytest.raises(ReconciliationCandidatesError) as caught:
            list_reconciliation_candidates(FakePort(rows=[row]), _request())
        assert caught.value.code == "failed_validation"


def test_foreign_currency_preserves_independent_canonical_amounts() -> None:
    row = _row(20, "2025-01-25")
    row.update(
        currency=_currency(2, "USD"),
        amount_currency="59.00",
        amount_residual_currency="29.50",
    )

    result = list_reconciliation_candidates(FakePort(rows=[row]), _request())

    assert result["items"] == [row]


def test_date_bounds_are_inclusive_and_negative_payable_amounts_are_valid() -> None:
    row = _row(20, "2025-01-25", account_type="liability_payable")
    row.update(
        balance="-113.00",
        amount_currency="-113.00",
        amount_residual="-113.00",
        amount_residual_currency="-113.00",
    )

    result = list_reconciliation_candidates(
        FakePort(rows=[row]),
        _request(
            date_from="2025-01-25",
            date_to="2025-01-25",
            account_kinds=["payable"],
        ),
    )

    assert result["items"] == [row]


def test_nullable_and_legal_odoo_text_values_are_preserved_without_fallbacks() -> None:
    row = _row(20, "2025-01-25", state="draft")
    row.update(
        invoice_date=None,
        date_maturity=None,
        label=" ",
        partner={"id": 16, "name": None},
        matching_number=None,
        reconciliation_model={"id": 4, "name": " "},
    )
    row["move"].update(name=None, ref=" ")
    row["account"].update(code="A.1", name=" ")
    row["journal"].update(code=" ", name=" ")
    row["currency"]["code"] = " "
    row["company_currency"]["code"] = " "

    result = list_reconciliation_candidates(
        FakePort(rows=[row]), _request(states=["draft"])
    )

    assert result["items"] == [row]


def test_optional_partner_and_char_fields_can_be_null() -> None:
    row = _row(20, "2025-01-25")
    row.update(
        invoice_date=None,
        date_maturity=None,
        label=None,
        partner=None,
        matching_number=None,
        reconciliation_model=None,
    )
    row["move"].update(name=None, ref=None)

    result = list_reconciliation_candidates(FakePort(rows=[row]), _request())

    assert result["items"] == [row]


def test_slash_move_name_is_preserved_and_historical_model_is_optional() -> None:
    row = _row(20, "2025-01-25")
    row["move"]["name"] = "/"
    row["reconciliation_model"] = None

    result = list_reconciliation_candidates(FakePort(rows=[row]), _request())

    assert result["items"] == [row]


def test_every_locally_verifiable_filter_is_enforced_but_query_is_not_replayed() -> None:
    row = _row(20, "2025-01-25", account_type="asset_receivable")
    valid = {
        "date_from": "2025-01-01",
        "date_to": "2025-01-31",
        "states": ["posted"],
        "account_id": 31,
        "partner_id": 16,
        "journal_id": 9,
        "account_kinds": ["receivable"],
        "query": "cafe",
    }
    row["label"] = "café"
    assert list_reconciliation_candidates(FakePort(rows=[row]), _request(**valid))[
        "items"
    ] == [row]

    for key, value in {
        "date_from": "2025-01-26",
        "date_to": "2025-01-24",
        "states": ["draft"],
        "account_id": 32,
        "partner_id": 17,
        "journal_id": 10,
        "account_kinds": ["payable"],
    }.items():
        parameters = dict(valid)
        parameters[key] = value
        with pytest.raises(ReconciliationCandidatesError) as caught:
            list_reconciliation_candidates(FakePort(rows=[row]), _request(**parameters))
        assert caught.value.code == "failed_validation"


def test_account_kind_classification_reserves_only_receivable_and_payable_types() -> None:
    cases = [
        ("asset_receivable", "receivable"),
        ("liability_payable", "payable"),
        ("asset_current", "other"),
        ("expense_other", "other"),
    ]
    for account_type, kind in cases:
        row = _row(20, "2025-01-25", account_type=account_type)
        result = list_reconciliation_candidates(
            FakePort(rows=[row]), _request(account_kinds=[kind])
        )
        assert result["items"] == [row]


@pytest.mark.parametrize(
    "rows",
    [
        [_row(20, "2025-01-25"), _row(21, "2025-01-26")],
        [_row(20, "2025-01-25"), _row(21, "2025-01-25")],
        [_row(20, "2025-01-25"), _row(20, "2025-01-24")],
    ],
)
def test_rows_must_be_unique_and_strictly_date_id_descending(rows: list[dict]) -> None:
    with pytest.raises(ReconciliationCandidatesError) as caught:
        list_reconciliation_candidates(FakePort(rows=rows), _request())
    assert caught.value.code == "failed_validation"


@pytest.mark.parametrize(
    ("port", "code"),
    [
        (FakePort(company_visible=False), "company_unavailable"),
        (FakePort(module_installed=False), "uninstalled"),
        (FakePort(access_allowed=False), "unauthorized"),
    ],
)
def test_runtime_availability_failures_are_typed(port: FakePort, code: str) -> None:
    with pytest.raises(ReconciliationCandidatesError) as caught:
        list_reconciliation_candidates(port, _request())
    assert caught.value.code == code


def test_malformed_or_contradictory_bridge_pages_are_failed_validation() -> None:
    with pytest.raises(ReconciliationCandidatesError) as caught:
        list_reconciliation_candidates(
            FakePort(company_visible=False, access_allowed=True), _request()
        )
    assert caught.value.code == "failed_validation"

    class Broken(FakePort):
        def read_page(self, **kwargs) -> dict:
            raise ValueError("bad page")

    with pytest.raises(ReconciliationCandidatesError) as caught:
        list_reconciliation_candidates(Broken(), _request())
    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8


def _success_response(data: dict) -> dict:
    return {
        "schema_version": "v1",
        "request_id": _request()["request_id"],
        "success": True,
        "capability": "reconciliation.candidates.list",
        "status": "verified",
        "data": data,
        "warnings": [],
        "error": None,
        "odoo": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_id": 42,
            "model": "account.move.line",
            "record_ids": [item["id"] for item in data["items"]],
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": None,
            "verification": {"result": "passed"},
        },
    }


def test_specialized_schemas_accept_success_and_error_documents() -> None:
    schema_dir = Path(__file__).parents[2] / "schemas" / "v1"
    capability = "reconciliation.candidates.list"
    assert (schema_dir / f"{capability}.request.schema.json").is_file()
    assert (schema_dir / f"{capability}.response.schema.json").is_file()
    registry = load_registry()
    registry.validate_instance(
        f"schemas/v1/{capability}.request.schema.json",
        _request(
            date_from=None,
            date_to=None,
            states=["posted"],
            account_id=None,
            partner_id=None,
            journal_id=None,
            account_kinds=["receivable", "payable", "other"],
            query=None,
            limit=100,
            cursor=None,
        ),
    )
    response = _success_response(
        {"items": [_row(20, "2025-01-25")], "has_more": False, "next_cursor": None}
    )
    registry.validate_instance(f"schemas/v1/{capability}.response.schema.json", response)
    response.update(
        success=False,
        status="failed_validation",
        data=None,
        error={
            "code": "failed_validation",
            "message": "The result failed validation.",
            "details": {},
            "retryable": False,
        },
    )
    registry.validate_instance(f"schemas/v1/{capability}.response.schema.json", response)


def test_schema_and_python_reject_decimal_with_trailing_newline() -> None:
    row = _row(20, "2025-01-25")
    row["amount_residual"] += "\n"
    response = _success_response(
        {"items": [row], "has_more": False, "next_cursor": None}
    )

    with pytest.raises(InstanceValidationError):
        load_registry().validate_instance(
            "schemas/v1/reconciliation.candidates.list.response.schema.json",
            response,
        )
    with pytest.raises(ReconciliationCandidatesError):
        list_reconciliation_candidates(FakePort(rows=[row]), _request())


@pytest.mark.parametrize(
    "mutation",
    [
        lambda row: row["move"].update(move_type="future_move"),
        lambda row: row["move"].update(move_type=" "),
        lambda row: row["account"].update(account_type="future_account"),
        lambda row: row["account"].update(account_type=" "),
        lambda row: row["journal"].update(type="future_journal"),
        lambda row: row["journal"].update(type=" "),
    ],
)
def test_schema_and_python_reject_unknown_or_blank_odoo_selections(mutation) -> None:
    row = _row(20, "2025-01-25")
    mutation(row)
    response = _success_response(
        {"items": [row], "has_more": False, "next_cursor": None}
    )

    with pytest.raises(InstanceValidationError):
        load_registry().validate_instance(
            "schemas/v1/reconciliation.candidates.list.response.schema.json",
            response,
        )
    with pytest.raises(ReconciliationCandidatesError) as caught:
        list_reconciliation_candidates(FakePort(rows=[row]), _request())
    assert caught.value.code == "failed_validation"


@pytest.mark.parametrize("zero", ["0", "-0", "0.00", "-0.00"])
def test_schema_and_python_reject_every_canonical_zero_company_residual(
    zero: str,
) -> None:
    row = _row(20, "2025-01-25")
    row["amount_residual"] = zero
    response = _success_response(
        {"items": [row], "has_more": False, "next_cursor": None}
    )

    with pytest.raises(InstanceValidationError):
        load_registry().validate_instance(
            "schemas/v1/reconciliation.candidates.list.response.schema.json",
            response,
        )
    with pytest.raises(ReconciliationCandidatesError) as caught:
        list_reconciliation_candidates(FakePort(rows=[row]), _request())
    assert caught.value.code == "failed_validation"
