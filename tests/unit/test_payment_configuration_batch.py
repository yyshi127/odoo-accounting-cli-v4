from __future__ import annotations

import io
import json
from copy import deepcopy
from types import SimpleNamespace

import pytest
from test_core_writes_runtime import Env, Failure, _payload
from test_fiscal_mapping_writes import request

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4 import payment_configuration_contracts as contracts
from odoo_accounting_cli_v4.bridge import core_writes_runtime as runtime
from odoo_accounting_cli_v4.capabilities import core_writes as public
from odoo_accounting_cli_v4.registry import load_registry

PARAMETERS = {
    "payment.method_line.create": {
        "journal_id": 9,
        "payment_method_id": 2,
        "name": "Receipt",
        "sequence": 10,
        "payment_account_id": 101,
    },
    "payment.method_line.update": {
        "payment_method_line_id": 31,
        "changes": {"name": "Receipt updated", "sequence": 7},
    },
    "payment.method_line.duplicate": {
        "payment_method_line_id": 31,
        "name": "Receipt copy",
    },
    "payment.method_line.remove": {"payment_method_line_id": 31},
    "journal.liquidity_configuration.update": {
        "journal_id": 9,
        "changes": {
            "suspense_account_id": 101,
            "profit_account_id": 102,
            "loss_account_id": 103,
        },
    },
    "journal.bank_account.assign": {"journal_id": 9, "partner_bank_id": 201},
}


def result(capability_id, parameters):
    journal = capability_id.startswith("journal.")
    return {
        "model": "account.journal" if journal else "account.payment.method.line",
        "id": parameters["journal_id"]
        if journal
        else 900
        if capability_id.endswith((".create", ".duplicate"))
        else parameters["payment_method_line_id"],
        "name": parameters.get(
            "name", parameters.get("changes", {}).get("name", "Configuration")
        ),
        "state": "deleted" if capability_id.endswith(".remove") else "active",
        "company_id": 7,
        "move_type": None,
        "source_id": parameters["payment_method_line_id"]
        if capability_id.endswith(".duplicate")
        else None,
        "line_ids": [],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }


@pytest.fixture(scope="module")
def registry():
    return load_registry()


@pytest.mark.parametrize(
    "capability_id", ["payment.method_definition.get", "payment.method_definition.list"]
)
def test_definition_reads_are_distinct_closed_native_contracts(capability_id, registry):
    from test_core_object_reads import FakePort

    from odoo_accounting_cli_v4.capabilities.core_object_reads import (
        CoreObjectReadError,
        read_core_object,
        validate_core_object_read_request,
    )

    item = {"id": 2, "name": "Manual", "code": "manual", "payment_type": "inbound"}
    req = request({"payment_method_id": 2} if capability_id.endswith(".get") else {})
    registry.validate_instance(f"schemas/v1/{capability_id}.request.schema.json", req)
    normalized = validate_core_object_read_request(capability_id, req)[2]
    assert "payment_method_line_id" not in normalized
    result = read_core_object(capability_id, FakePort([item]), req)
    assert (
        result == item if capability_id.endswith(".get") else result["items"] == [item]
    )
    req["parameters"]["model"] = "arbitrary.model"
    with pytest.raises(CoreObjectReadError):
        validate_core_object_read_request(capability_id, req)


@pytest.mark.parametrize("capability_id", PARAMETERS)
def test_closed_schema_runtime_and_public_cli(capability_id, registry, monkeypatch):
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
    assert response["success"] and not stderr.getvalue()
    registry.validate_instance(
        f"schemas/v1/{capability_id}.response.schema.json", response
    )
    wrong = {**expected, "company_id": 8}
    with pytest.raises(public.CoreWriteError):
        public._validate_result(
            capability_id, normalized, wrong, company_id=7, idempotent_replay=False
        )
    with pytest.raises(public.CoreWriteError):
        public.execute_core_write(Port(), capability_id, req, key, "other-command")


@pytest.mark.parametrize("capability_id", PARAMETERS)
@pytest.mark.parametrize("denial", ["group", "acl"])
def test_native_group_acl_denial_never_writes(capability_id, denial):
    env = Env()
    if denial == "group":
        env.denied_group = "account.group_account_manager"
    else:
        env.denied_access = ("account.journal", "read")
    params = contracts.normalize_parameters(capability_id, PARAMETERS[capability_id])
    page = runtime.dispatch(
        env,
        _payload(
            capability_id,
            params,
            key=contracts.idempotency_key(capability_id, params, 7),
        ),
        7,
        Failure,
    )
    assert not page["access_allowed"] and page["result"] is None
    assert not any(
        call[0] in {"create", "write", "unlink", "copy"} for call in env.calls
    )


@pytest.mark.parametrize(
    "cap,params",
    [
        (
            "payment.method_line.create",
            {**PARAMETERS["payment.method_line.create"], "journal_id": True},
        ),
        (
            "payment.method_line.create",
            {**PARAMETERS["payment.method_line.create"], "sequence": True},
        ),
        ("payment.method_line.update", {"payment_method_line_id": 31, "changes": {}}),
        (
            "payment.method_line.update",
            {"payment_method_line_id": 31, "changes": {"journal_id": 19}},
        ),
        (
            "journal.liquidity_configuration.update",
            {"journal_id": 9, "changes": {"suspense_account_id": None}},
        ),
        (
            "payment.method_line.duplicate",
            {"payment_method_line_id": 31, "name": " copy "},
        ),
    ],
)
def test_invalid_fields_are_rejected(cap, params):
    with pytest.raises(ValueError):
        contracts.normalize_parameters(cap, params)


@pytest.mark.parametrize(
    "capability_id",
    ["journal.bank_account.assign", "journal.liquidity_configuration.update"],
)
def test_archived_journal_configuration_keeps_native_archive_state(capability_id):
    expected = {**result(capability_id, PARAMETERS[capability_id]), "state": "archived"}
    assert (
        public._validate_result(
            capability_id,
            PARAMETERS[capability_id],
            expected,
            company_id=7,
            idempotent_replay=False,
        )
        == expected
    )


@pytest.mark.parametrize("used", [False, True])
def test_remove_reports_native_delete_or_detach_without_erasing_history(
    monkeypatch, used
):
    journal = SimpleNamespace(id=9)
    line = SimpleNamespace(
        id=31, name="Receipt", journal_id=journal, invalidate_recordset=lambda: None
    )
    line.unlink = lambda: setattr(line, "journal_id", False)
    line.exists = lambda: line if used else False
    monkeypatch.setattr(runtime, "_payment_line_config_record", lambda *args: line)
    output, replay = runtime._write_payment_configuration_batch(
        None,
        "payment.method_line.remove",
        PARAMETERS["payment.method_line.remove"],
        7,
        Failure,
    )
    assert output["state"] == ("detached" if used else "deleted") and not replay
    public._validate_result(
        "payment.method_line.remove",
        PARAMETERS["payment.method_line.remove"],
        output,
        company_id=7,
        idempotent_replay=False,
    )


def test_copy_restores_native_copy_false_payment_account(monkeypatch):
    journal = SimpleNamespace(id=9, filtered_domain=lambda domain: True)
    method = SimpleNamespace(
        id=2,
        code="manual",
        _get_payment_method_information=lambda: {"manual": {}},
        _get_payment_method_domain=lambda code: [],
    )
    source = SimpleNamespace(
        id=31,
        name="Receipt",
        sequence=10,
        journal_id=journal,
        payment_method_id=method,
        payment_account_id=SimpleNamespace(id=101),
    )
    copied = SimpleNamespace(
        **{
            **vars(source),
            "id": 32,
            "name": "Receipt copy",
            "invalidate_recordset": lambda: None,
        }
    )

    def copy(defaults):
        assert defaults == {"name": "Receipt copy", "payment_account_id": 101}
        return copied

    source.copy = copy
    monkeypatch.setattr(runtime, "_payment_line_config_record", lambda *args: source)
    monkeypatch.setattr(runtime, "_search_one", lambda *args: method)
    monkeypatch.setattr(runtime, "_validate_payment_account", lambda *args: None)
    monkeypatch.setattr(
        runtime,
        "_scoped",
        lambda *args: SimpleNamespace(search=lambda *args, **kwargs: []),
    )
    output, replay = runtime._write_payment_configuration_batch(
        None,
        "payment.method_line.duplicate",
        PARAMETERS["payment.method_line.duplicate"],
        7,
        Failure,
    )
    assert output["id"] == 32 and output["source_id"] == 31 and not replay


def test_conflicting_natural_key_uses_the_shared_conflict_exit_without_create(
    monkeypatch,
):
    class Conflicts:
        def __len__(self):
            return 2

    journal = SimpleNamespace(filtered_domain=lambda domain: True)
    method = SimpleNamespace(
        code="manual",
        _get_payment_method_information=lambda: {"manual": {}},
        _get_payment_method_domain=lambda code: [],
    )
    monkeypatch.setattr(runtime, "_journal_config_record", lambda *args: journal)
    monkeypatch.setattr(runtime, "_search_one", lambda *args: method)
    monkeypatch.setattr(runtime, "_validate_payment_account", lambda *args: None)
    monkeypatch.setattr(
        runtime,
        "_scoped",
        lambda *args: SimpleNamespace(search=lambda *args, **kwargs: Conflicts()),
    )
    with pytest.raises(Failure) as caught:
        runtime._write_payment_configuration_batch(
            None,
            "payment.method_line.create",
            PARAMETERS["payment.method_line.create"],
            7,
            Failure,
        )
    assert caught.value.code == "idempotency_conflict" and caught.value.exit_code == 5
