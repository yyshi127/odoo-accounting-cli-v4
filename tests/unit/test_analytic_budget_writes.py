from __future__ import annotations

import hashlib
import json
from copy import deepcopy

import pytest

from odoo_accounting_cli_v4.capabilities.core_writes import (
    CORE_WRITE_CAPABILITY_IDS,
    CoreWriteError,
    execute_core_write,
    validate_core_write_request,
)

CAPABILITIES = {
    "analytic.account.create",
    "analytic.account.update",
    "budget.create",
    "budget.update_draft",
    "budget.lines.replace",
    "budget.confirm",
    "budget.reset_to_draft",
    "budget.cancel",
    "budget.mark_done",
}
PARAMETERS = {
    "analytic.account.create": {"name": "Project A", "plan_id": 11},
    "analytic.account.update": {
        "analytic_account_id": 21,
        "changes": {"code": "PRJ-A", "partner_id": None, "active": False},
    },
    "budget.create": {
        "name": "FY 2027",
        "date_from": "2027-01-01",
        "date_to": "2027-12-31",
        "budget_type": "both",
    },
    "budget.update_draft": {
        "budget_id": 31,
        "changes": {"name": "FY 2027 revised", "budget_type": "expense"},
    },
    "budget.lines.replace": {
        "budget_id": 32,
        "lines": [
            {"budget_amount": "-1000.50", "analytic_account_ids": [21, 22]},
            {"budget_amount": "0", "analytic_account_ids": [23]},
        ],
    },
    "budget.confirm": {"budget_id": 33},
    "budget.reset_to_draft": {"budget_id": 34},
    "budget.cancel": {"budget_id": 35},
    "budget.mark_done": {"budget_id": 36},
}
BUDGET_STATES = {
    "budget.create": "draft",
    "budget.update_draft": "draft",
    "budget.lines.replace": "draft",
    "budget.confirm": "confirmed",
    "budget.reset_to_draft": "draft",
    "budget.cancel": "canceled",
    "budget.mark_done": "done",
}


def _request(capability_id: str) -> dict:
    return {
        "schema_version": "v1",
        "request_id": "91f91531-a230-4dde-a8bf-e56bb03bdaba",
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": deepcopy(PARAMETERS[capability_id]),
    }


def _digest(value: object) -> str:
    canonical = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(canonical).hexdigest()[:32]


def _key(capability_id: str) -> str:
    parameters = PARAMETERS[capability_id]
    if capability_id in {"analytic.account.create", "budget.create"}:
        return f"{capability_id}:client-request-0001"
    if capability_id == "analytic.account.update":
        return f"{capability_id}:21:{_digest(parameters['changes'])}"
    if capability_id == "budget.update_draft":
        return f"{capability_id}:31:{_digest(parameters['changes'])}"
    if capability_id == "budget.lines.replace":
        return f"{capability_id}:32:{_digest(parameters['lines'])}"
    return f"{capability_id}:{parameters['budget_id']}"


def _result(capability_id: str, **changes) -> dict:
    analytic = capability_id.startswith("analytic.")
    parameters = PARAMETERS[capability_id]
    record_id = (
        901
        if capability_id == "analytic.account.create"
        else parameters["analytic_account_id"]
        if analytic
        else 902
        if capability_id == "budget.create"
        else parameters["budget_id"]
    )
    result = {
        "model": "account.analytic.account" if analytic else "budget.analytic",
        "id": record_id,
        "name": "Project A" if analytic else "FY 2027",
        "state": (
            "archived"
            if capability_id == "analytic.account.update"
            else "active"
            if analytic
            else BUDGET_STATES[capability_id]
        ),
        "company_id": 7,
        "move_type": None,
        "source_id": 11 if analytic else None,
        "line_ids": (
            [] if analytic or capability_id == "budget.create" else [1001, 1002]
        ),
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }
    result.update(changes)
    return result


class FakePort:
    user_id = 42

    def __init__(
        self,
        capability_id: str,
        *,
        result: dict | None = None,
        idempotent_replay: bool = False,
    ) -> None:
        self.capability_id = capability_id
        self.result = deepcopy(_result(capability_id) if result is None else result)
        self.idempotent_replay = idempotent_replay
        self.calls: list[dict] = []

    def execute(self, **kwargs) -> dict:
        self.calls.append(deepcopy(kwargs))
        return {
            "user_id": 42,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "idempotent_replay": self.idempotent_replay,
            "result": deepcopy(self.result),
        }


@pytest.mark.parametrize("capability_id", sorted(CAPABILITIES))
def test_analytic_budget_write_contract_and_dispatch(capability_id: str) -> None:
    assert capability_id in CORE_WRITE_CAPABILITY_IDS
    request = _request(capability_id)
    _, _, normalized = validate_core_write_request(capability_id, request)
    if capability_id == "analytic.account.create":
        assert normalized == {
            "name": "Project A",
            "plan_id": 11,
            "code": None,
            "partner_id": None,
        }

    port = FakePort(capability_id)
    data = execute_core_write(
        port, capability_id, request, _key(capability_id), capability_id
    )

    assert data == {"idempotent_replay": False, "result": _result(capability_id)}
    assert port.calls == [
        {
            "capability_id": capability_id,
            "company_id": 7,
            "idempotency_key": _key(capability_id),
            "confirmation": capability_id,
            "parameters": normalized,
        }
    ]


@pytest.mark.parametrize(
    ("capability_id", "field", "value"),
    [
        ("analytic.account.create", "name", " Project A"),
        ("analytic.account.create", "name", "Project [ODACV4:reserved]"),
        ("analytic.account.create", "plan_id", 0),
        ("analytic.account.update", "changes", {}),
        (
            "analytic.account.update",
            "changes",
            {"name": "Project [ODACV4:reserved]"},
        ),
        ("budget.create", "budget_type", "capital"),
        ("budget.create", "name", "Budget [ODACV4:reserved]"),
        ("budget.create", "date_to", "2026-12-31"),
        ("budget.update_draft", "changes", {}),
        (
            "budget.update_draft",
            "changes",
            {"name": "Budget [ODACV4:reserved]"},
        ),
        (
            "budget.lines.replace",
            "lines",
            [{"budget_amount": "1", "analytic_account_ids": [22, 21]}],
        ),
        (
            "budget.lines.replace",
            "lines",
            [{"budget_amount": "+1", "analytic_account_ids": [21]}],
        ),
    ],
)
def test_analytic_budget_write_rejects_invalid_parameters(
    capability_id: str, field: str, value: object
) -> None:
    request = _request(capability_id)
    request["parameters"][field] = value
    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request(capability_id, request)
    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize(
    "capability_id",
    [
        "analytic.account.update",
        "budget.update_draft",
        "budget.lines.replace",
        "budget.confirm",
    ],
)
def test_analytic_budget_write_rejects_a_wrong_idempotency_key(
    capability_id: str,
) -> None:
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            FakePort(capability_id),
            capability_id,
            _request(capability_id),
            "wrong-key-0001",
            capability_id,
        )
    assert caught.value.code == "invalid_idempotency_key"


@pytest.mark.parametrize(
    ("capability_id", "change"),
    [
        ("analytic.account.create", {"source_id": 99}),
        ("analytic.account.create", {"source_id": None}),
        ("analytic.account.create", {"state": "archived"}),
        ("analytic.account.update", {"id": 99}),
        ("analytic.account.update", {"source_id": None}),
        ("analytic.account.update", {"state": "active"}),
        ("analytic.account.update", {"state": "draft"}),
        ("budget.create", {"model": "budget.line"}),
        ("budget.create", {"line_ids": [1001]}),
        ("budget.update_draft", {"id": 99}),
        ("budget.lines.replace", {"source_id": 32}),
        ("budget.lines.replace", {"line_ids": [1001]}),
        ("budget.confirm", {"state": "draft"}),
        ("budget.reset_to_draft", {"state": "confirmed"}),
        ("budget.cancel", {"state": "cancelled"}),
        ("budget.mark_done", {"reconciled": True}),
    ],
)
def test_analytic_budget_results_fail_closed(capability_id: str, change: dict) -> None:
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            FakePort(capability_id, result=_result(capability_id, **change)),
            capability_id,
            _request(capability_id),
            _key(capability_id),
            capability_id,
        )
    assert caught.value.code == "failed_validation"


def test_analytic_create_accepts_archived_state_only_on_replay() -> None:
    capability_id = "analytic.account.create"
    data = execute_core_write(
        FakePort(
            capability_id,
            result=_result(capability_id, state="archived"),
            idempotent_replay=True,
        ),
        capability_id,
        _request(capability_id),
        _key(capability_id),
        capability_id,
    )
    assert data["idempotent_replay"] is True
    assert data["result"]["state"] == "archived"


@pytest.mark.parametrize("state", ["confirmed", "revised", "done", "canceled"])
def test_budget_create_accepts_transitioned_state_and_changed_lines_on_replay(
    state: str,
) -> None:
    capability_id = "budget.create"
    result = _result(capability_id, state=state, line_ids=[1001, 1002])
    data = execute_core_write(
        FakePort(capability_id, result=result, idempotent_replay=True),
        capability_id,
        _request(capability_id),
        _key(capability_id),
        capability_id,
    )
    assert data == {"idempotent_replay": True, "result": result}


def test_analytic_update_active_change_must_match_the_result_state() -> None:
    capability_id = "analytic.account.update"
    request = _request(capability_id)
    request["parameters"]["changes"]["active"] = True
    key = f"{capability_id}:21:{_digest(request['parameters']['changes'])}"
    data = execute_core_write(
        FakePort(capability_id, result=_result(capability_id, state="active")),
        capability_id,
        request,
        key,
        capability_id,
    )
    assert data["result"]["state"] == "active"


def test_budget_confirm_accepts_revised_state() -> None:
    capability_id = "budget.confirm"
    data = execute_core_write(
        FakePort(capability_id, result=_result(capability_id, state="revised")),
        capability_id,
        _request(capability_id),
        _key(capability_id),
        capability_id,
    )
    assert data["result"]["state"] == "revised"
