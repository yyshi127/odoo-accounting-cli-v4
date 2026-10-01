from __future__ import annotations

import io
import json
from copy import deepcopy
from datetime import date
from uuid import uuid4

import pytest
from test_core_writes_runtime import Env, Failure, _payload

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4 import report_budget_contracts as contracts
from odoo_accounting_cli_v4.bridge import core_writes_runtime as runtime
from odoo_accounting_cli_v4.capabilities import core_writes as public
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

PARAMETERS = {
    "report.budget_definition.create": {"name": "Fixture budget"},
    "report.budget_definition.update": {
        "budget_definition_id": 11,
        "changes": {"sequence": 1},
    },
    "report.budget_definition.duplicate": {"budget_definition_id": 11, "name": "Copy"},
    "report.budget_definition.delete": {"budget_definition_id": 11},
    "report.budget_item.create": {
        "budget_definition_id": 11,
        "account_id": 101,
        "date": "2026-01-01",
        "amount": "100",
    },
    "report.budget_item.update": {"budget_item_id": 21, "changes": {"amount": "150"}},
    "report.budget_item.delete": {"budget_item_id": 21},
    "report.budget_account_period.set_total": {
        "budget_definition_id": 11,
        "account_id": 101,
        "date_from": "2026-01-01",
        "date_to": "2026-03-31",
        "total": "500",
        "rounding": 2,
    },
}


def request(parameters):
    return {
        "schema_version": "v1",
        "request_id": str(uuid4()),
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": deepcopy(parameters),
    }


@pytest.fixture(scope="module")
def registry():
    return load_registry()


@pytest.mark.parametrize("capability_id", PARAMETERS)
def test_batch_contract_schema_runtime_key_and_cli_agree(
    capability_id, registry, monkeypatch
):
    req = request(PARAMETERS[capability_id])
    registry.validate_instance(f"schemas/v1/{capability_id}.request.schema.json", req)
    normalized = public.validate_core_write_request(capability_id, req)[2]
    assert runtime._valid_parameters(capability_id, normalized, 7)
    key = public._expected_idempotency_key(capability_id, normalized, 7)
    assert key == runtime._deterministic_key(capability_id, normalized, 7)
    assert runtime._GROUPS[capability_id] == "account.group_account_manager"
    assert {
        "res.company",
        "account.report.budget",
        "account.report.budget.item",
    } <= runtime._MODELS[capability_id]

    item = capability_id.startswith("report.budget_item.")
    create = capability_id.endswith((".create", ".duplicate"))
    source = (
        11
        if item or capability_id.endswith(".duplicate")
        else (101 if capability_id.endswith(".set_total") else None)
    )
    result = {
        "model": "account.report.budget.item" if item else "account.report.budget",
        "id": 100
        if create
        else normalized["budget_item_id" if item else "budget_definition_id"],
        "name": None if item else "Fixture budget",
        "state": "deleted"
        if capability_id.endswith(".delete")
        else "recorded"
        if item
        else "configured",
        "company_id": 7,
        "move_type": None,
        "source_id": source,
        "line_ids": [],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }

    class Port:
        user_id = 42

        def execute(self, **payload):
            assert payload["parameters"] == normalized
            assert payload["confirmation"] == capability_id
            assert payload["idempotency_key"] == key
            return {
                "user_id": self.user_id,
                "company_visible": True,
                "module_installed": True,
                "access_allowed": True,
                "idempotent_replay": False,
                "result": deepcopy(result),
            }

    monkeypatch.setattr(cli, "load_registry", lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    assert (
        cli.main(
            [
                "write",
                "run",
                capability_id,
                "--request",
                "-",
                "--idempotency-key",
                key,
                "--confirm",
                capability_id,
            ],
            stdin=io.StringIO(json.dumps(req)),
            stdout=stdout,
            stderr=stderr,
            port_factory=lambda *args: Port(),
        )
        == 0
    )
    response = json.loads(stdout.getvalue())
    assert response["success"] is True and stderr.getvalue() == ""
    assert cli._CAPABILITY_MODELS[capability_id] == result["model"]
    registry.validate_instance(
        f"schemas/v1/{capability_id}.response.schema.json", response
    )
    bad = deepcopy(result)
    bad["company_id"] = 8
    with pytest.raises(public.CoreWriteError):
        public._validate_result(
            capability_id, normalized, bad, company_id=7, idempotent_replay=False
        )
    with pytest.raises(public.CoreWriteError):
        public.execute_core_write(Port(), capability_id, req, key, "another-command")
    req["parameters"]["company_id"] = 8
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(
            f"schemas/v1/{capability_id}.request.schema.json", req
        )


@pytest.mark.parametrize("capability_id", PARAMETERS)
@pytest.mark.parametrize("denial", ["group", "acl"])
def test_native_group_or_acl_denial_never_invokes_a_budget_write(capability_id, denial):
    env = Env()
    if denial == "group":
        env.denied_group = "account.group_account_manager"
    else:
        env.denied_access = ("account.report.budget", "read")
    parameters = contracts.normalize_parameters(
        capability_id, PARAMETERS[capability_id]
    )
    page = runtime.dispatch(
        env,
        _payload(
            capability_id,
            parameters,
            key=contracts.idempotency_key(capability_id, parameters, 7),
        ),
        7,
        Failure,
    )
    assert page["access_allowed"] is False and page["result"] is None
    assert not any(
        call[0] in {"create", "write", "unlink", "copy"} for call in env.calls
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("amount", 100),
        ("amount", "1.00"),
        ("amount", "-0"),
        ("date", "2026-02-30"),
        ("account_id", True),
        ("account_id", 0),
    ],
)
def test_item_contract_rejects_invalid_native_values(field, value):
    parameters = deepcopy(PARAMETERS["report.budget_item.create"])
    parameters[field] = value
    with pytest.raises(ValueError):
        contracts.normalize_parameters("report.budget_item.create", parameters)


def test_period_keeps_native_partial_first_month_semantics_and_bounds():
    assert contracts.period_months("2026-01-15", "2026-03-20") == [
        date(2026, 2, 1),
        date(2026, 3, 1),
    ]
    for start, end in [
        ("2026-01-15", "2026-01-31"),
        ("2026-02-01", "2026-01-01"),
        ("2000-01-01", "2026-01-01"),
    ]:
        with pytest.raises(ValueError):
            contracts.period_months(start, end)
    for capability_id in (
        "report.budget_definition.update",
        "report.budget_item.update",
    ):
        parameters = deepcopy(PARAMETERS[capability_id])
        parameters["changes"] = {}
        with pytest.raises(ValueError):
            contracts.normalize_parameters(capability_id, parameters)
