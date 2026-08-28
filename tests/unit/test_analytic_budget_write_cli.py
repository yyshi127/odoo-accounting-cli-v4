from __future__ import annotations

import hashlib
import io
import json
from copy import deepcopy

import pytest

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.bridge.core_writes import OdooCoreWritePort

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
        "request_id": "92f91531-a230-4dde-a8bf-e56bb03bdaba",
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


class SuccessPort:
    user_id = 42

    def __init__(self, capability_id: str) -> None:
        self.capability_id = capability_id

    def execute(self, **kwargs) -> dict:
        parameters = kwargs["parameters"]
        analytic = self.capability_id.startswith("analytic.")
        record_id = (
            901
            if self.capability_id == "analytic.account.create"
            else parameters["analytic_account_id"]
            if analytic
            else 902
            if self.capability_id == "budget.create"
            else parameters["budget_id"]
        )
        return {
            "user_id": 42,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "idempotent_replay": False,
            "result": {
                "model": (
                    "account.analytic.account" if analytic else "budget.analytic"
                ),
                "id": record_id,
                "name": "Project A" if analytic else "FY 2027",
                "state": (
                    "archived"
                    if self.capability_id == "analytic.account.update"
                    else "active"
                    if analytic
                    else BUDGET_STATES[self.capability_id]
                ),
                "company_id": 7,
                "move_type": None,
                "source_id": 11 if analytic else None,
                "line_ids": (
                    []
                    if analytic or self.capability_id == "budget.create"
                    else [1001, 1002]
                ),
                "partial_reconcile_ids": [],
                "full_reconcile_id": None,
                "reconciled": False,
            },
        }


@pytest.mark.parametrize("capability_id", sorted(CAPABILITIES))
def test_cli_runs_each_analytic_budget_write(capability_id: str) -> None:
    stdout = io.StringIO()
    stderr = io.StringIO()
    exit_code = cli.main(
        [
            "write",
            "run",
            capability_id,
            "--request",
            "-",
            "--idempotency-key",
            _key(capability_id),
            "--confirm",
            capability_id,
        ],
        stdin=io.StringIO(json.dumps(_request(capability_id))),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda selected, _request: SuccessPort(selected),
    )
    document = json.loads(stdout.getvalue())
    assert exit_code == 0
    assert stderr.getvalue() == ""
    assert document["capability"] == capability_id
    assert document["success"] is True
    assert document["odoo"]["model"] == cli._CAPABILITY_MODELS[capability_id]


@pytest.mark.parametrize("capability_id", sorted(CAPABILITIES))
def test_configured_factory_routes_analytic_budget_writes_to_core_port(
    capability_id: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = object()
    client = object()

    class RuntimeConfig:
        def resolve(self, database: str, company_id: int, user_login: str) -> object:
            assert (database, company_id, user_login) == (
                "odoo_cli_v4_dev",
                7,
                "v4-agent",
            )
            return target

    monkeypatch.setattr(cli, "load_runtime_config", lambda _path: RuntimeConfig())
    monkeypatch.setattr(cli, "OdooBridgeClient", lambda *_args, **_kwargs: client)
    port = cli._configured_port_factory(capability_id, _request(capability_id))
    assert type(port) is OdooCoreWritePort
    assert port._client is client
