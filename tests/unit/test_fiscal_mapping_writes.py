from __future__ import annotations

import io
import json
from copy import deepcopy
from types import SimpleNamespace
from uuid import uuid4

import pytest
from test_core_writes_runtime import Env, Failure, _payload

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4 import fiscal_mapping_contracts as contracts
from odoo_accounting_cli_v4.bridge import core_writes_runtime as runtime
from odoo_accounting_cli_v4.capabilities import core_writes as public
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

PARAMETERS = {
    "fiscal_position.taxes.replace": {"fiscal_position_id": 11, "tax_ids": [31]},
    "tax.original_taxes.replace": {"tax_id": 31, "original_tax_ids": [32]},
    "fiscal_position.account_mapping.create": {
        "fiscal_position_id": 11,
        "source_account_id": 101,
        "destination_account_id": 102,
    },
    "fiscal_position.account_mapping.update": {
        "account_mapping_id": 21,
        "changes": {"destination_account_id": 103},
    },
    "fiscal_position.account_mapping.delete": {"account_mapping_id": 21},
    "fiscal_position.duplicate": {"fiscal_position_id": 11, "name": "Fiscal copy"},
    "fiscal_position.delete": {"fiscal_position_id": 11},
    "tax.duplicate": {"tax_id": 31, "name": "Tax copy"},
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


def result(capability_id, parameters):
    mapping = capability_id.startswith("fiscal_position.account_mapping.")
    tax = capability_id.startswith("tax.")
    create = capability_id.endswith((".create", ".duplicate"))
    source_id = (
        11
        if mapping
        else parameters["tax_id" if tax else "fiscal_position_id"]
        if capability_id.endswith(".duplicate")
        else None
    )
    return {
        "model": "account.fiscal.position.account"
        if mapping
        else "account.tax"
        if tax
        else "account.fiscal.position",
        "id": 900
        if create
        else parameters[
            "account_mapping_id"
            if mapping
            else "tax_id"
            if tax
            else "fiscal_position_id"
        ],
        "name": None if mapping else parameters.get("name", "Configuration"),
        "state": "deleted"
        if capability_id.endswith(".delete")
        else "recorded"
        if mapping
        else "active",
        "company_id": 7,
        "move_type": None,
        "source_id": source_id,
        "line_ids": [],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }


@pytest.fixture(scope="module")
def registry():
    return load_registry()


@pytest.mark.parametrize("capability_id", PARAMETERS)
def test_fixed_contract_schema_runtime_key_and_public_cli(
    capability_id, registry, monkeypatch
):
    req = request(PARAMETERS[capability_id])
    registry.validate_instance(f"schemas/v1/{capability_id}.request.schema.json", req)
    normalized = public.validate_core_write_request(capability_id, req)[2]
    assert runtime._valid_parameters(capability_id, normalized, 7)
    key = public._expected_idempotency_key(capability_id, normalized, 7)
    assert key == runtime._deterministic_key(capability_id, normalized, 7)
    expected = result(capability_id, normalized)
    assert cli._CAPABILITY_MODELS[capability_id] == expected["model"]

    class Port:
        user_id = 42

        def execute(self, **payload):
            assert payload["parameters"] == normalized
            assert payload["confirmation"] == capability_id
            assert payload["idempotency_key"] == key
            return {
                "user_id": 42,
                "company_visible": True,
                "module_installed": True,
                "access_allowed": True,
                "idempotent_replay": False,
                "result": deepcopy(expected),
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
                "--confirm",
                capability_id,
                "--idempotency-key",
                key,
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
    registry.validate_instance(
        f"schemas/v1/{capability_id}.response.schema.json", response
    )
    bad = deepcopy(expected)
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
def test_manager_or_acl_denial_never_performs_a_write(capability_id, denial):
    env = Env()
    if denial == "group":
        env.denied_group = "account.group_account_manager"
    else:
        env.denied_access = (
            "account.tax"
            if capability_id.startswith("tax.")
            else "account.fiscal.position",
            "read",
        )
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
    "capability,parameters",
    [
        ("fiscal_position.taxes.replace", {"fiscal_position_id": True, "tax_ids": []}),
        (
            "fiscal_position.taxes.replace",
            {"fiscal_position_id": 11, "tax_ids": [31, 31]},
        ),
        ("tax.original_taxes.replace", {"tax_id": 31, "original_tax_ids": [31]}),
        (
            "fiscal_position.account_mapping.create",
            {
                "fiscal_position_id": 11,
                "source_account_id": 101,
                "destination_account_id": 101,
            },
        ),
        (
            "fiscal_position.account_mapping.update",
            {"account_mapping_id": 21, "changes": {}},
        ),
        ("tax.duplicate", {"tax_id": 31, "name": " Copy "}),
    ],
)
def test_invalid_fixed_parameters_are_rejected(capability, parameters):
    with pytest.raises(ValueError):
        contracts.normalize_parameters(capability, parameters)


def test_tax_copy_explicitly_detaches_both_inverse_relations(monkeypatch):
    copied = SimpleNamespace(
        id=22,
        name="Tax copy",
        active=True,
        company_id=SimpleNamespace(id=7),
        fiscal_position_ids=[],
        replacing_tax_ids=[],
        repartition_line_ids=SimpleNamespace(ids=[402, 403]),
        invalidate_recordset=lambda: None,
    )

    def copy(defaults):
        assert defaults == {
            "name": "Tax copy",
            "fiscal_position_ids": [(5, 0, 0)],
            "replacing_tax_ids": [(5, 0, 0)],
        }
        return copied

    source = SimpleNamespace(
        id=31, copy=copy, repartition_line_ids=SimpleNamespace(ids=[302, 303])
    )
    monkeypatch.setattr(
        runtime,
        "_scoped",
        lambda *args: SimpleNamespace(search=lambda *args, **kwargs: []),
    )
    monkeypatch.setattr(runtime, "_tax_config_record", lambda *args: source)
    monkeypatch.setattr(
        runtime, "_tax_copy_signature", lambda record: {"original_tax_ids": []}
    )
    output, replay = runtime._write_fiscal_mapping_batch(
        None, "tax.duplicate", PARAMETERS["tax.duplicate"], 7, Failure
    )
    assert not replay and output["id"] == 22 and output["source_id"] == 31
    assert output["line_ids"] == [402, 403]
