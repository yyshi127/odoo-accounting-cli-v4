from __future__ import annotations

import copy
import io
import json
from pathlib import Path
from typing import Any

import pytest

from odoo_accounting_cli_v4.capabilities.assets import (
    AssetReadError,
    read_assets,
    validate_asset_request,
)
from odoo_accounting_cli_v4.cli import main
from odoo_accounting_cli_v4.registry import load_registry


def _request(capability_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": "a31769b9-c6ab-4975-9690-e96f1556bd34",
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }


def _summary(asset_id: int = 31, *, state: str = "open") -> dict[str, Any]:
    return {
        "id": asset_id,
        "name": f"Asset {asset_id}",
        "state": state,
        "company_id": 7,
        "currency": {"id": 6, "code": "CNY"},
        "acquisition_date": "2025-01-01",
        "original_value": "120",
        "book_value": "60",
    }


def _account(account_id: int, code: str) -> dict[str, Any]:
    return {"id": account_id, "code": code, "name": f"Account {code}"}


def _detail(asset_id: int = 31) -> dict[str, Any]:
    return {
        "id": asset_id,
        "name": f"Asset {asset_id}",
        "state": "open",
        "active": True,
        "company_id": 7,
        "currency": {"id": 6, "code": "CNY"},
        "accounts": {
            "asset": _account(78, "1601"),
            "depreciation": _account(80, "160301"),
            "expense": _account(146, "6602"),
        },
        "journal": {"id": 11, "code": "MISC", "name": "Miscellaneous"},
        "values": {
            "original": "120",
            "salvage": "0",
            "depreciable": "120",
            "book": "60",
            "residual": "60",
        },
        "method": {
            "type": "linear",
            "number": 2,
            "period": "12",
            "progress_factor": "0.3",
            "prorata_computation_type": "none",
        },
        "dates": {
            "acquisition": "2025-01-01",
            "prorata": "2025-01-01",
            "disposal": None,
        },
    }


def _schedule(asset_id: int = 31) -> dict[str, Any]:
    return {
        "asset": _summary(asset_id),
        "moves": [
            {
                "id": 91,
                "name": "MISC/2025/0001",
                "date": "2025-12-31",
                "state": "posted",
                "auto_post": "no",
                "journal": {
                    "id": 11,
                    "code": "MISC",
                    "name": "Miscellaneous",
                },
                "depreciation_value": "60",
                "cumulative_depreciation": "60",
                "remaining_value": "60",
                "line_ids": [101, 102],
            }
        ],
    }


class FakePort:
    def __init__(self, pages: list[dict[str, Any]]) -> None:
        self.user_id = 5
        self.pages = copy.deepcopy(pages)
        self.calls: list[dict[str, Any]] = []

    def read(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(copy.deepcopy(kwargs))
        return self.pages.pop(0)


def _page(items: list[dict[str, Any]], **overrides: Any) -> dict[str, Any]:
    value = {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "cursor_found": True,
        "items": items,
    }
    value.update(overrides)
    return value


def test_search_normalizes_filters_and_uses_bound_id_cursor() -> None:
    first_port = FakePort([_page([_summary(32), _summary(31)])])
    request = _request("asset.search", {"states": ["open"], "limit": 1})

    first = read_assets("asset.search", first_port, request)

    assert first["items"] == [_summary(32)]
    assert first["has_more"] is True
    assert isinstance(first["next_cursor"], str)
    assert first_port.calls == [
        {
            "capability_id": "asset.search",
            "company_id": 7,
            "parameters": {
                "query": None,
                "states": ["open"],
                "after": None,
                "limit": 2,
            },
        }
    ]

    second_port = FakePort([_page([_summary(31)])])
    second_request = _request(
        "asset.search",
        {"states": ["open"], "limit": 1, "cursor": first["next_cursor"]},
    )
    second = read_assets("asset.search", second_port, second_request)

    assert second == {"items": [_summary(31)], "has_more": False, "next_cursor": None}
    assert second_port.calls[0]["parameters"]["after"] == 32


def test_empty_asset_search_is_a_verified_result() -> None:
    assert read_assets(
        "asset.search", FakePort([_page([])]), _request("asset.search", {})
    ) == {"items": [], "has_more": False, "next_cursor": None}


def test_cursor_is_bound_to_company_user_and_filters() -> None:
    first = read_assets(
        "asset.search",
        FakePort([_page([_summary(32), _summary(31)])]),
        _request("asset.search", {"states": ["open"], "limit": 1}),
    )
    changed = _request(
        "asset.search",
        {"states": ["draft"], "limit": 1, "cursor": first["next_cursor"]},
    )
    port = FakePort([_page([])])

    with pytest.raises(AssetReadError) as caught:
        read_assets("asset.search", port, changed)

    assert caught.value.code == "invalid_cursor"
    assert port.calls == []


@pytest.mark.parametrize(
    "parameters",
    [
        {"extra": True},
        {"query": " padded "},
        {"states": []},
        {"states": ["open", "open"]},
        {"states": ["model"]},
        {"states": [{}]},
        {"limit": True},
    ],
)
def test_search_request_is_closed(parameters: dict[str, Any]) -> None:
    with pytest.raises(AssetReadError) as caught:
        validate_asset_request("asset.search", _request("asset.search", parameters))
    assert caught.value.code == "invalid_request"


def test_get_returns_company_scoped_detail_and_allows_incomplete_draft_slots() -> None:
    data = _detail()
    data["accounts"] = {"asset": None, "depreciation": None, "expense": None}
    data["journal"] = None
    data["method"]["number"] = 0

    assert (
        read_assets(
            "asset.get",
            FakePort([_page([data])]),
            _request("asset.get", {"asset_id": 31}),
        )
        == data
    )


def test_schedule_returns_chronological_moves_and_can_be_empty() -> None:
    data = _schedule()
    result = read_assets(
        "asset.depreciation_schedule.get",
        FakePort([_page([data])]),
        _request("asset.depreciation_schedule.get", {"asset_id": 31}),
    )
    assert result == data

    data["moves"] = []
    assert (
        read_assets(
            "asset.depreciation_schedule.get",
            FakePort([_page([data])]),
            _request("asset.depreciation_schedule.get", {"asset_id": 31}),
        )["moves"]
        == []
    )


@pytest.mark.parametrize(
    "capability_id", ["asset.get", "asset.depreciation_schedule.get"]
)
def test_single_asset_reads_report_missing_record(capability_id: str) -> None:
    with pytest.raises(AssetReadError) as caught:
        read_assets(
            capability_id,
            FakePort([_page([])]),
            _request(capability_id, {"asset_id": 31}),
        )
    assert caught.value.code == "record_not_found"


def test_out_of_scope_or_unordered_results_fail_closed() -> None:
    cross_company = _detail()
    cross_company["company_id"] = 8
    with pytest.raises(AssetReadError, match="invalid asset detail"):
        read_assets(
            "asset.get",
            FakePort([_page([cross_company])]),
            _request("asset.get", {"asset_id": 31}),
        )

    schedule = _schedule()
    schedule["moves"].append({**schedule["moves"][0], "id": 90, "date": "2025-01-31"})
    with pytest.raises(AssetReadError, match="invalid depreciation schedule"):
        read_assets(
            "asset.depreciation_schedule.get",
            FakePort([_page([schedule])]),
            _request("asset.depreciation_schedule.get", {"asset_id": 31}),
        )


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"company_visible": False, "access_allowed": False}, "company_unavailable"),
        ({"module_installed": False, "access_allowed": False}, "uninstalled"),
        ({"access_allowed": False}, "unauthorized"),
    ],
)
def test_availability_failures_are_explicit(
    overrides: dict[str, Any], code: str
) -> None:
    with pytest.raises(AssetReadError) as caught:
        read_assets(
            "asset.search",
            FakePort([_page([], **overrides)]),
            _request("asset.search", {}),
        )
    assert caught.value.code == code


def _response(capability_id: str, data: dict[str, Any]) -> dict[str, Any]:
    record_ids = (
        [item["id"] for item in data["items"]]
        if capability_id == "asset.search"
        else [data["asset"]["id"]]
        if capability_id == "asset.depreciation_schedule.get"
        else [data["id"]]
    )
    return {
        "schema_version": "v1",
        "request_id": _request(capability_id, {})["request_id"],
        "success": True,
        "capability": capability_id,
        "status": "verified",
        "data": data,
        "warnings": [],
        "error": None,
        "odoo": {
            "database": "v4-dev",
            "company_id": 7,
            "user_id": 5,
            "model": "account.asset",
            "record_ids": record_ids,
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": None,
            "verification": {"result": "passed"},
        },
    }


def test_six_specialized_schemas_accept_the_frozen_contracts() -> None:
    schema_dir = Path(__file__).parents[2] / "schemas" / "v1"
    registry = load_registry()
    cases = {
        "asset.search": (
            _request("asset.search", {"states": ["open"], "limit": 10}),
            {"items": [_summary()], "has_more": False, "next_cursor": None},
        ),
        "asset.get": (_request("asset.get", {"asset_id": 31}), _detail()),
        "asset.depreciation_schedule.get": (
            _request("asset.depreciation_schedule.get", {"asset_id": 31}),
            _schedule(),
        ),
    }
    for capability_id, (request, data) in cases.items():
        request_schema = f"schemas/v1/{capability_id}.request.schema.json"
        response_schema = f"schemas/v1/{capability_id}.response.schema.json"
        assert (schema_dir / f"{capability_id}.request.schema.json").is_file()
        assert (schema_dir / f"{capability_id}.response.schema.json").is_file()
        registry.validate_instance(request_schema, request)
        registry.validate_instance(response_schema, _response(capability_id, data))


@pytest.mark.parametrize(
    ("capability_id", "parameters", "page", "expected_ids"),
    [
        (
            "asset.search",
            {},
            _page([_summary()]),
            [31],
        ),
        (
            "asset.get",
            {"asset_id": 31},
            _page([_detail()]),
            [31],
        ),
        (
            "asset.depreciation_schedule.get",
            {"asset_id": 31},
            _page([_schedule()]),
            [31],
        ),
    ],
)
def test_cli_dispatches_the_three_fixed_asset_reads(
    capability_id: str,
    parameters: dict[str, Any],
    page: dict[str, Any],
    expected_ids: list[int],
) -> None:
    stdout = io.StringIO()
    stderr = io.StringIO()
    port = FakePort([page])

    code = main(
        ["read", capability_id, "--request", "-"],
        stdin=io.StringIO(json.dumps(_request(capability_id, parameters))),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda selected, _request_document: (
            port if selected == capability_id else None
        ),
    )

    document = json.loads(stdout.getvalue())
    assert code == 0
    assert stderr.getvalue() == ""
    assert document["success"] is True
    assert document["capability"] == capability_id
    assert document["odoo"] == {
        "database": "v4-dev",
        "company_id": 7,
        "user_id": 5,
        "model": "account.asset",
        "record_ids": expected_ids,
    }
