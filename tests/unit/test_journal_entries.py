from __future__ import annotations

import copy
import base64
import json
from pathlib import Path

import pytest

from odoo_accounting_cli_v4.capabilities.journal_entries import (
    JournalEntryError,
    get_journal_entry,
    search_journal_entries,
    validate_journal_entry_get_request,
    validate_journal_entry_search_request,
)
from odoo_accounting_cli_v4.registry import load_registry


class FakePort:
    def __init__(
        self,
        *,
        rows: list[dict] | None = None,
        entry: dict | None = None,
        company_visible: bool = True,
        module_installed: bool = True,
        access_allowed: bool | None = None,
    ) -> None:
        self.user_id = 42
        self.rows = copy.deepcopy(rows or [])
        self.entry = copy.deepcopy(entry)
        self.company_visible = company_visible
        self.module_installed = module_installed
        self.access_allowed = (
            company_visible and module_installed
            if access_allowed is None
            else access_allowed
        )
        self.search_calls: list[dict] = []
        self.get_calls: list[dict] = []

    def search_page(self, **kwargs) -> dict:
        self.search_calls.append(copy.deepcopy(kwargs))
        return self._page(rows=self.rows[: kwargs["limit"]])

    def get_entry(self, **kwargs) -> dict:
        self.get_calls.append(copy.deepcopy(kwargs))
        return self._page(entry=self.entry)

    def _page(self, **payload) -> dict:
        return {
            "user_id": self.user_id,
            "company_visible": self.company_visible,
            "module_installed": self.module_installed,
            "access_allowed": self.access_allowed,
            **payload,
        }


def _context(**overrides) -> dict:
    value = {
        "database": "odoo_cli_v4_dev",
        "company_id": 7,
        "user_login": "v4-agent",
        "language": "zh_CN",
        "timezone": "Asia/Shanghai",
    }
    value.update(overrides)
    return value


def _search_request(**parameters) -> dict:
    return {
        "schema_version": "v1",
        "request_id": "7bc39413-0d69-4092-9319-795d33f3167c",
        "context": _context(),
        "parameters": parameters,
    }


def _get_request(entry_id: int = 30) -> dict:
    return {
        "schema_version": "v1",
        "request_id": "7bc39413-0d69-4092-9319-795d33f3167c",
        "context": _context(),
        "parameters": {"entry_id": entry_id},
    }


def _journal() -> dict:
    return {"id": 4, "code": "MISC", "name": "Miscellaneous Operations"}


def _currency() -> dict:
    return {"id": 6, "code": "CNY"}


def _search_row(record_id: int, date: str) -> dict:
    return {
        "id": record_id,
        "name": f"MISC/2025/{record_id:04d}",
        "date": date,
        "state": "posted",
        "ref": f"fixture-{record_id}",
        "journal": _journal(),
        "company_id": 7,
        "currency": _currency(),
        "partner": None,
        "debit": "123.45",
        "credit": "123.45",
        "balance": "0.00",
    }


def _entry() -> dict:
    return {
        "id": 30,
        "name": "MISC/2025/0030",
        "date": "2025-02-01",
        "state": "posted",
        "ref": None,
        "journal": _journal(),
        "company_id": 7,
        "currency": _currency(),
        "partner": {"id": 9, "name": "Example Partner"},
        "lines": [
            {
                "id": 301,
                "sequence": 10,
                "display_type": "product",
                "name": "Debit line",
                "account": {"id": 101, "code": "1000", "name": "Cash"},
                "partner": {"id": 9, "name": "Example Partner"},
                "debit": "123.45",
                "credit": "0.00",
                "balance": "123.45",
                "company_currency": _currency(),
                "amount_currency": "123.45",
                "currency": _currency(),
                "date_maturity": "2025-02-28",
                "reconciled": False,
                "matching_number": None,
                "analytic_distribution": {},
            },
            {
                "id": 302,
                "sequence": 10,
                "display_type": "product",
                "name": "Credit line",
                "account": {
                    "id": 202,
                    "code": "2000",
                    "name": "Clearing",
                },
                "partner": None,
                "debit": "0.00",
                "credit": "123.45",
                "balance": "-123.45",
                "company_currency": _currency(),
                "amount_currency": "-123.45",
                "currency": _currency(),
                "date_maturity": None,
                "reconciled": True,
                "matching_number": "P",
                "analytic_distribution": {},
            },
        ],
        "totals": {"debit": "123.45", "credit": "123.45", "balance": "0.00"},
    }


def test_search_normalizes_filters_and_uses_descending_keyset_cursor() -> None:
    rows = [
        _search_row(30, "2025-02-01"),
        _search_row(29, "2025-02-01"),
        _search_row(10, "2025-01-31"),
    ]
    request = _search_request(
        limit=2,
        date_from="2025-01-01",
        date_to=None,
        states=["cancel", "draft", "posted"],
        journal_id=None,
        partner_id=9,
        query="fixture",
    )
    port = FakePort(rows=rows)

    result = search_journal_entries(port, request)

    assert result == {
        "items": rows[:2],
        "has_more": True,
        "next_cursor": result["next_cursor"],
    }
    assert isinstance(result["next_cursor"], str)
    assert port.search_calls == [
        {
            "company_id": 7,
            "after": None,
            "limit": 3,
            "filters": {
                "date_from": "2025-01-01",
                "date_to": None,
                "states": ["draft", "posted", "cancel"],
                "journal_id": None,
                "partner_id": 9,
                "query": "fixture",
            },
        }
    ]

    second_port = FakePort(rows=rows[2:])
    second_request = copy.deepcopy(request)
    second_request["parameters"]["cursor"] = result["next_cursor"]
    second_request["parameters"]["limit"] = 100
    second = search_journal_entries(second_port, second_request)
    assert second == {"items": rows[2:], "has_more": False, "next_cursor": None}
    assert second_port.search_calls[0]["after"] == ["2025-02-01", 29]


def test_search_defaults_and_maximum_limit_are_closed() -> None:
    port = FakePort()
    assert search_journal_entries(port, _search_request()) == {
        "items": [],
        "has_more": False,
        "next_cursor": None,
    }
    assert port.search_calls == [
        {
            "company_id": 7,
            "after": None,
            "limit": 101,
            "filters": {
                "date_from": None,
                "date_to": None,
                "states": [],
                "journal_id": None,
                "partner_id": None,
                "query": None,
            },
        }
    ]
    maximum_port = FakePort()
    search_journal_entries(maximum_port, _search_request(limit=1000))
    assert maximum_port.search_calls[0]["limit"] == 1001
    with pytest.raises(JournalEntryError) as caught:
        search_journal_entries(FakePort(), _search_request(limit=1001))
    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize(
    "request_id",
    [
        "7bc39413-0d69-0092-9319-795d33f3167c",
        "7bc39413-0d69-4092-7319-795d33f3167c",
    ],
)
def test_request_uuid_matches_the_schema_version_and_variant(request_id: str) -> None:
    request = _search_request()
    request["request_id"] = request_id

    with pytest.raises(JournalEntryError) as caught:
        validate_journal_entry_search_request(request)

    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize(
    "parameters",
    [
        {"unexpected": True},
        {"date_from": "2025-02-30"},
        {"date_from": "2025-02-01", "date_to": "2025-01-31"},
        {"states": None},
        {"states": []},
        {"states": [{}]},
        {"states": [[]]},
        {"states": ["posted", "posted"]},
        {"states": ["invalid"]},
        {"query": " untrimmed"},
        {"query": "x" * 201},
        {"journal_id": True},
        {"partner_id": 0},
    ],
)
def test_invalid_search_parameters_fail_before_the_port(parameters: dict) -> None:
    port = FakePort()
    with pytest.raises(JournalEntryError) as caught:
        search_journal_entries(port, _search_request(**parameters))
    assert caught.value.code == "invalid_request"
    assert caught.value.exit_code == 2
    assert port.search_calls == []


def test_cursor_is_bound_to_database_company_user_and_normalized_filters() -> None:
    rows = [_search_row(30, "2025-02-01"), _search_row(29, "2025-01-31")]
    first = search_journal_entries(
        FakePort(rows=rows), _search_request(limit=1, states=["posted", "draft"])
    )
    assert first["next_cursor"]

    mutations = [
        ("context", "database", "other-db"),
        ("context", "company_id", 8),
        ("context", "user_login", "other-user"),
        ("parameters", "states", ["posted"]),
    ]
    for section, key, value in mutations:
        request = _search_request(
            limit=1,
            cursor=first["next_cursor"],
            states=["draft", "posted"],
        )
        request[section][key] = value
        port = FakePort()
        with pytest.raises(JournalEntryError) as caught:
            search_journal_entries(port, request)
        assert caught.value.code == "invalid_cursor"
        assert port.search_calls == []


def test_cursor_binding_rejects_json_boolean_integer_aliases() -> None:
    rows = [_search_row(30, "2025-02-01"), _search_row(29, "2025-01-31")]
    first = search_journal_entries(
        FakePort(rows=rows), _search_request(limit=1, journal_id=1)
    )
    raw = base64.urlsafe_b64decode(first["next_cursor"] + "==")
    payload = json.loads(raw)
    payload["company_id"] = True
    payload["filters"]["journal_id"] = True
    forged = (
        base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode())
        .decode()
        .rstrip("=")
    )

    port = FakePort()
    with pytest.raises(JournalEntryError) as caught:
        search_journal_entries(
            port, _search_request(limit=1, journal_id=1, cursor=forged)
        )

    assert caught.value.code == "invalid_cursor"
    assert port.search_calls == []


def test_cursor_rejects_overflowing_json_numbers_as_invalid_cursor() -> None:
    rows = [_search_row(30, "2025-02-01"), _search_row(29, "2025-01-31")]
    first = search_journal_entries(FakePort(rows=rows), _search_request(limit=1))
    raw = base64.urlsafe_b64decode(first["next_cursor"] + "==").decode("utf-8")
    forged_raw = raw.replace('"query":null', '"query":1e400')
    forged = base64.urlsafe_b64encode(forged_raw.encode("utf-8")).decode("ascii").rstrip("=")
    port = FakePort()

    with pytest.raises(JournalEntryError) as caught:
        search_journal_entries(port, _search_request(limit=1, cursor=forged))

    assert caught.value.code == "invalid_cursor"
    assert caught.value.exit_code == 2
    assert port.search_calls == []


@pytest.mark.parametrize(
    "mutation",
    [
        lambda row: row.update(extra=True),
        lambda row: row.update(company_id=8),
        lambda row: row.update(debit=123.45),
        lambda row: row.update(balance="1.00"),
        lambda row: row.update(currency={"id": 6, "code": "CNY", "name": "Yuan"}),
    ],
)
def test_invalid_search_rows_never_become_verified(mutation) -> None:
    row = _search_row(30, "2025-02-01")
    mutation(row)
    with pytest.raises(JournalEntryError) as caught:
        search_journal_entries(FakePort(rows=[row]), _search_request())
    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8


def test_search_requires_date_descending_then_id_descending() -> None:
    unordered = [_search_row(29, "2025-02-01"), _search_row(30, "2025-02-01")]
    with pytest.raises(JournalEntryError) as caught:
        search_journal_entries(FakePort(rows=unordered), _search_request())
    assert caught.value.code == "failed_validation"


def test_search_accepts_draft_name_null_and_signed_storno_totals() -> None:
    row = _search_row(30, "2025-02-01")
    row.update(
        name=None,
        state="draft",
        debit="-123.45",
        credit="0.00",
        balance="-123.45",
    )

    result = search_journal_entries(FakePort(rows=[row]), _search_request())

    assert result["items"] == [row]


def test_get_reads_one_company_scoped_entry_and_verifies_line_totals() -> None:
    entry = _entry()
    port = FakePort(entry=entry)

    result = get_journal_entry(port, _get_request())

    assert result == entry
    assert port.get_calls == [{"company_id": 7, "entry_id": 30}]
    assert result["currency"] == result["lines"][0]["company_currency"]


@pytest.mark.parametrize(
    "mutation",
    [
        lambda entry: entry.update(extra=True),
        lambda entry: entry.update(company_id=8),
        lambda entry: entry["lines"][0].update(extra=True),
        lambda entry: entry["lines"][0].update(debit=123.45),
        lambda entry: entry["lines"][0].update(balance="0.00"),
        lambda entry: entry["lines"][0].update(
            company_currency={"id": 37, "code": "SGD"}
        ),
        lambda entry: entry["lines"][0].update(account=None),
        lambda entry: entry["lines"][0].update(display_type="line_section"),
        lambda entry: entry["lines"][0].update(display_type={}),
        lambda entry: entry["lines"][0].update(display_type=[]),
        lambda entry: entry["totals"].update(debit="999.00"),
        lambda entry: entry.update(lines=list(reversed(entry["lines"]))),
    ],
)
def test_invalid_entry_or_lines_never_become_verified(mutation) -> None:
    entry = _entry()
    mutation(entry)
    with pytest.raises(JournalEntryError) as caught:
        get_journal_entry(FakePort(entry=entry), _get_request())
    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8


def test_get_accepts_nullable_model_fields_and_non_accountable_section() -> None:
    entry = _entry()
    entry["name"] = None
    entry["lines"][0]["name"] = None
    section = copy.deepcopy(entry["lines"][-1])
    section.update(
        id=303,
        sequence=20,
        display_type="line_section",
        name=None,
        account=None,
        debit="0.00",
        credit="0.00",
        balance="0.00",
        amount_currency="0.00",
    )
    entry["lines"].append(section)

    result = get_journal_entry(FakePort(entry=entry), _get_request())

    assert result["name"] is None
    assert result["lines"][-1]["account"] is None


def test_missing_entry_is_explicit() -> None:
    with pytest.raises(JournalEntryError) as caught:
        get_journal_entry(FakePort(entry=None), _get_request())
    assert caught.value.code == "record_not_found"
    assert caught.value.exit_code == 4


def test_get_request_is_closed_and_requires_a_positive_non_boolean_id() -> None:
    assert validate_journal_entry_get_request(_get_request())[2] == 30
    for value in (0, -1, True, "30"):
        with pytest.raises(JournalEntryError):
            validate_journal_entry_get_request(_get_request(value))
    request = _get_request()
    request["parameters"]["unexpected"] = True
    with pytest.raises(JournalEntryError):
        validate_journal_entry_get_request(request)


@pytest.mark.parametrize(
    ("port", "code"),
    [
        (FakePort(company_visible=False), "company_unavailable"),
        (FakePort(module_installed=False), "uninstalled"),
        (FakePort(access_allowed=False), "unauthorized"),
    ],
)
@pytest.mark.parametrize("operation", ["search", "get"])
def test_runtime_availability_failures_are_explicit(
    port: FakePort, code: str, operation: str
) -> None:
    with pytest.raises(JournalEntryError) as caught:
        if operation == "search":
            search_journal_entries(port, _search_request())
        else:
            get_journal_entry(port, _get_request())
    assert caught.value.code == code


def test_contradictory_or_wrong_user_page_is_rejected() -> None:
    contradictory = FakePort(company_visible=False, access_allowed=True)
    with pytest.raises(JournalEntryError) as caught:
        search_journal_entries(contradictory, _search_request())
    assert caught.value.code == "failed_validation"

    class WrongUserPort(FakePort):
        def search_page(self, **kwargs) -> dict:
            page = super().search_page(**kwargs)
            page["user_id"] = self.user_id + 1
            return page

    with pytest.raises(JournalEntryError) as caught:
        search_journal_entries(WrongUserPort(), _search_request())
    assert caught.value.code == "failed_validation"


def _success_response(capability_id: str, data: dict) -> dict:
    record_ids = (
        [item["id"] for item in data["items"]]
        if capability_id.endswith("search")
        else [data["id"]]
    )
    return {
        "schema_version": "v1",
        "request_id": _get_request()["request_id"],
        "success": True,
        "capability": capability_id,
        "status": "verified",
        "data": data,
        "warnings": [],
        "error": None,
        "odoo": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_id": 42,
            "model": "account.move",
            "record_ids": record_ids,
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": None,
            "verification": {"result": "passed"},
        },
    }


@pytest.mark.parametrize(
    ("capability_id", "request_document", "data"),
    [
        (
            "journal_entry.search",
            _search_request(states=["posted"], date_from=None),
            {
                "items": [_search_row(30, "2025-02-01")],
                "has_more": False,
                "next_cursor": None,
            },
        ),
        ("journal_entry.get", _get_request(), _entry()),
    ],
)
def test_specialized_schemas_accept_success_and_error_documents(
    capability_id: str, request_document: dict, data: dict
) -> None:
    schema_dir = Path(__file__).parents[2] / "schemas" / "v1"
    assert (schema_dir / f"{capability_id}.request.schema.json").is_file()
    assert (schema_dir / f"{capability_id}.response.schema.json").is_file()
    registry = load_registry()
    registry.validate_instance(
        f"schemas/v1/{capability_id}.request.schema.json", request_document
    )
    registry.validate_instance(
        f"schemas/v1/{capability_id}.response.schema.json",
        _success_response(capability_id, data),
    )
    error = _success_response(capability_id, data)
    error.update(
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
    registry.validate_instance(
        f"schemas/v1/{capability_id}.response.schema.json", error
    )


def test_search_validator_exposes_canonical_filters() -> None:
    _, _, filters, limit, cursor = validate_journal_entry_search_request(
        _search_request(states=["cancel", "draft"])
    )
    assert filters["states"] == ["draft", "cancel"]
    assert limit == 100
    assert cursor is None
