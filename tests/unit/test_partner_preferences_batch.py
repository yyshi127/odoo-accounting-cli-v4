from __future__ import annotations

import io
import json
from copy import deepcopy
from types import SimpleNamespace

import pytest
from test_core_writes_runtime import Env, Failure, _payload
from test_fiscal_mapping_writes import request

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4 import partner_preferences_contracts as contracts
from odoo_accounting_cli_v4.bridge import core_writes_runtime as runtime
from odoo_accounting_cli_v4.capabilities import core_writes as public
from odoo_accounting_cli_v4.registry import load_registry

PARAMETERS = {
    "partner.payment_preferences.update": {
        "partner_id": 31,
        "changes": {
            "property_inbound_payment_method_line_id": 11,
            "property_outbound_payment_method_line_id": None,
        },
    },
    "partner.invoice_delivery_preferences.update": {
        "partner_id": 31,
        "changes": {
            "invoice_sending_method": "manual",
            "invoice_edi_format": None,
            "invoice_template_pdf_report_id": None,
        },
    },
    "partner.bill_validation_preferences.update": {
        "partner_id": 31,
        "changes": {
            "autopost_bills": "never",
            "ignore_abnormal_invoice_date": False,
            "ignore_abnormal_invoice_amount": True,
        },
    },
    "partner.credit_limit.update": {"partner_id": 31, "credit_limit": "1000"},
    "partner.credit_limit.reset": {"partner_id": 31},
}


def result(capability_id, parameters):
    return {
        "model": "res.partner",
        "id": parameters["partner_id"],
        "name": "Partner",
        "state": "active",
        "company_id": 7,
        "move_type": None,
        "source_id": None,
        "line_ids": [],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }


def read_item(capability_id):
    item = {
        "id": 31,
        "name": "Partner",
        "company_id": 7,
        "commercial_partner_id": 31,
        "shared_partner": False,
    }
    values = {
        "property_inbound_payment_method_line_id": None,
        "property_outbound_payment_method_line_id": None,
        "invoice_sending_method": "manual",
        "invoice_edi_format": None,
        "invoice_template_pdf_report_id": None,
        "autopost_bills": "ask",
        "ignore_abnormal_invoice_date": False,
        "ignore_abnormal_invoice_amount": False,
    }
    item.update(
        {field: values[field] for field in contracts.READ_FIELDS[capability_id]}
    )
    if "invoice_delivery_preferences" in capability_id:
        item.update(
            available_sending_methods=["email", "manual"],
            available_edi_formats=[],
            available_pdf_report_ids=[401],
        )
    return item


@pytest.fixture(scope="module")
def registry():
    return load_registry()


@pytest.mark.parametrize("capability_id", PARAMETERS)
def test_write_contract_schema_key_and_public_cli(capability_id, registry, monkeypatch):
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
            assert (
                payload["parameters"] == normalized
                and payload["confirmation"] == capability_id
                and payload["idempotency_key"] == key
            )
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
    with pytest.raises(public.CoreWriteError):
        public._validate_result(
            capability_id,
            normalized,
            {**expected, "company_id": 8},
            company_id=7,
            idempotent_replay=False,
        )
    with pytest.raises(public.CoreWriteError):
        public.execute_core_write(Port(), capability_id, req, key, "other-command")


@pytest.mark.parametrize("capability_id", contracts.READ_CAPABILITY_IDS)
def test_read_contract_and_public_cli(capability_id, registry, monkeypatch):
    from test_core_object_reads import FakePort

    from odoo_accounting_cli_v4.bridge.core_object_reads_runtime import (
        _valid_parameters,
    )
    from odoo_accounting_cli_v4.capabilities.core_object_reads import (
        validate_core_object_read_request,
    )

    req = request({"partner_id": 31})
    registry.validate_instance(f"schemas/v1/{capability_id}.request.schema.json", req)
    assert _valid_parameters(
        capability_id, validate_core_object_read_request(capability_id, req)[2]
    )
    item = read_item(capability_id)
    assert contracts.valid_read_item(capability_id, item, 7)
    monkeypatch.setattr(cli, "load_registry", lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    assert (
        cli.main(
            ["read", capability_id, "--request", "-"],
            stdin=io.StringIO(json.dumps(req)),
            stdout=stdout,
            stderr=stderr,
            port_factory=lambda *args: FakePort([item]),
        )
        == 0
    )
    response = json.loads(stdout.getvalue())
    assert response["success"] and response["data"] == item and not stderr.getvalue()
    registry.validate_instance(
        f"schemas/v1/{capability_id}.response.schema.json", response
    )
    assert not contracts.valid_read_item(capability_id, {**item, "company_id": 8}, 7)
    assert not contracts.valid_read_item(capability_id, {**item, "company_id": True}, 1)
    assert not contracts.valid_read_item(capability_id, {**item, "parent_id": 19}, 7)


@pytest.mark.parametrize("capability_id", PARAMETERS)
@pytest.mark.parametrize("denial", ["group", "acl"])
def test_native_group_acl_denial_never_writes(capability_id, denial):
    env = Env()
    if denial == "group":
        env.denied_group = "account.group_account_user"
    else:
        env.denied_access = ("res.partner", "read")
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


@pytest.mark.parametrize("capability_id", PARAMETERS)
def test_fixed_contract_round_trip_and_scoped_deterministic_key(capability_id):
    parameters = deepcopy(PARAMETERS[capability_id])
    normalized = contracts.normalize_parameters(capability_id, parameters)
    assert normalized == parameters
    assert contracts.normalize_parameters(capability_id, normalized) == normalized
    key = contracts.idempotency_key(capability_id, normalized, 7)
    assert key != contracts.idempotency_key(capability_id, normalized, 8)
    assert key == contracts.idempotency_key(capability_id, deepcopy(normalized), 7)
    parameters["company_id"] = 8
    with pytest.raises(ValueError):
        contracts.normalize_parameters(capability_id, parameters)


@pytest.mark.parametrize("capability_id", PARAMETERS)
def test_bool_partner_id_is_never_an_identifier(capability_id):
    with pytest.raises(ValueError):
        contracts.normalize_parameters(
            capability_id, {**PARAMETERS[capability_id], "partner_id": True}
        )


@pytest.mark.parametrize(
    "value",
    [True, 1, None, "-1", "1e2", "NaN", "Infinity", "01", ".1", "1.", " 1", "1\n"],
)
def test_credit_limit_invalid_numbers_are_rejected(value):
    with pytest.raises(ValueError):
        contracts.normalize_parameters(
            "partner.credit_limit.update", {"partner_id": 31, "credit_limit": value}
        )


def test_credit_amount_has_no_invented_business_size_cap_and_canonicalizes_zeroes():
    value = "10000000000000.00"
    normalized = contracts.normalize_parameters(
        "partner.credit_limit.update", {"partner_id": 31, "credit_limit": value}
    )
    assert normalized["credit_limit"] == "10000000000000"
    assert contracts.credit_amount("0.00") == 0


@pytest.mark.parametrize(
    "cap,changes",
    [
        (
            "partner.payment_preferences.update",
            {"property_inbound_payment_method_line_id": True},
        ),
        (
            "partner.payment_preferences.update",
            {"property_inbound_payment_method_line_id": 0},
        ),
        (
            "partner.bill_validation_preferences.update",
            {"ignore_abnormal_invoice_date": 1},
        ),
        ("partner.bill_validation_preferences.update", {"autopost_bills": "unknown"}),
        (
            "partner.invoice_delivery_preferences.update",
            {"invoice_edi_format": " padded "},
        ),
        ("partner.invoice_delivery_preferences.update", {"parent_id": 19}),
        ("partner.payment_preferences.update", {}),
    ],
)
def test_invalid_fixed_field_patches_fail(cap, changes):
    with pytest.raises(ValueError):
        contracts.normalize_parameters(cap, {"partner_id": 31, "changes": changes})


def test_credit_reset_invokes_native_inverse_and_restores_nonzero_company_fallback(
    monkeypatch,
):
    partner = SimpleNamespace(
        id=31,
        name="Customer",
        active=True,
        commercial_partner_id=SimpleNamespace(id=31),
        credit_limit=1000,
        use_partner_credit_limit=True,
        invalidate_recordset=lambda fields: None,
    )
    partner._fields = {
        "credit_limit": SimpleNamespace(
            get_company_dependent_fallback=lambda record: 300
        )
    }
    partner.with_company = lambda company: partner
    writes = []

    def write(values):
        writes.append(values)
        assert values == {"use_partner_credit_limit": False}
        partner.credit_limit = 300
        partner.use_partner_credit_limit = False

    partner.write = write
    monkeypatch.setattr(runtime, "_partner", lambda *args: partner)
    monkeypatch.setattr(
        runtime,
        "_scoped",
        lambda *args: SimpleNamespace(
            browse=lambda company: SimpleNamespace(id=company)
        ),
    )
    output, replay = runtime._write_partner_preferences_batch(
        None, "partner.credit_limit.reset", {"partner_id": 31}, 7, RuntimeError
    )
    assert output["id"] == 31 and not replay and len(writes) == 1
    second, replay = runtime._write_partner_preferences_batch(
        None, "partner.credit_limit.reset", {"partner_id": 31}, 7, RuntimeError
    )
    assert second == output and replay and len(writes) == 1


@pytest.mark.parametrize("owner", [None, 8])
def test_read_stored_detached_payment_line_is_truthful_but_foreign_line_is_rejected(
    monkeypatch, owner,
):
    from odoo_accounting_cli_v4.bridge import core_object_reads_runtime as reads

    capability = "partner.payment_preferences.get"
    row = {
        "id": 31, "name": "Partner", "company_id": False,
        "commercial_partner_id": (31, "Partner"),
        "property_inbound_payment_method_line_id": (11, "Historical"),
        "property_outbound_payment_method_line_id": False,
    }
    monkeypatch.setattr(reads, "_related_rows", lambda *args: {
        11: {"company_id": (owner, "Other") if owner else False,
             "payment_type": "inbound", "journal_id": False},
    })
    if owner:
        with pytest.raises(ValueError, match="outside company"):
            reads._normalize_partner_preferences(None, capability, [row], 7)
    else:
        item = reads._normalize_partner_preferences(None, capability, [row], 7)[0]
        assert item["property_inbound_payment_method_line_id"] == 11
        assert item["shared_partner"] and item["company_id"] == 7
