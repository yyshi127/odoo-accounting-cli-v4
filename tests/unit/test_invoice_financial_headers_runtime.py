from __future__ import annotations

from copy import deepcopy
from decimal import Decimal

import pytest
from test_core_writes_runtime import (
    Env,
    Failure,
    Records,
    _document_parameters,
    _payload,
)

from odoo_accounting_cli_v4.bridge import core_writes_runtime as runtime

CAPABILITIES = ("customer_invoice.create", "vendor_bill.create", "invoice.update")
FIELDS = ("partner_bank_id", "fiscal_position_id")
MOVE_TYPES = ("out_invoice", "in_invoice", "out_refund", "in_refund")


def _env():
    env = Env()
    company_partner = env.add("res.partner", 30, company_id=env.company)
    env.company.partner_id = Records(env, "res.partner", [company_partner])
    for record_id, partner in ((70, company_partner), (71, env.partner)):
        env.add(
            "res.partner.bank",
            record_id,
            partner_id=Records(env, "res.partner", [partner]),
            company_id=partner.company_id,
            active=True,
            currency_id=Records(env, "res.currency", [env.foreign_currency]),
            allow_out_payment=False,
        )
    env.add("account.fiscal.position", 72, company_id=env.company, active=True)
    return env


def _headers(move_type):
    return {
        "partner_bank_id": 70 if move_type in {"out_invoice", "in_refund"} else 71,
        "fiscal_position_id": 72,
    }


def _invoice(env, move_type):
    invoice = env.existing_move(610, move_type=move_type, state="draft")
    invoice.partner_bank_id = Records(env, "res.partner.bank")
    invoice.fiscal_position_id = Records(env, "account.fiscal.position")
    return invoice


def _dispatch(env, capability, parameters, *, key=None):
    request_key = key or runtime._deterministic_key(capability, parameters, 7)
    return runtime.dispatch(
        env,
        _payload(capability, parameters, key=request_key or "financial-header-create"),
        7,
        Failure,
    )


@pytest.mark.parametrize("capability", CAPABILITIES)
@pytest.mark.parametrize("field", FIELDS)
@pytest.mark.parametrize("value", [None, 5])
def test_runtime_accepts_strict_nullable_financial_header_ids(capability, field, value):
    env = Env()
    parameters = (
        {"move_id": 610, "changes": {field: value}}
        if capability == "invoice.update"
        else {**_document_parameters(env, capability), field: value}
    )
    assert runtime._valid_parameters(capability, parameters)


@pytest.mark.parametrize("capability", CAPABILITIES)
@pytest.mark.parametrize("field", FIELDS)
@pytest.mark.parametrize("value", [True, False, 0, -1, "1", 1.0, [], {}])
def test_runtime_rejects_invalid_financial_header_ids(capability, field, value):
    env = Env()
    parameters = (
        {"move_id": 610, "changes": {field: value}}
        if capability == "invoice.update"
        else {**_document_parameters(env, capability), field: value}
    )
    with pytest.raises(Failure) as caught:
        _dispatch(env, capability, parameters)
    assert caught.value.code == "bridge_protocol_error"
    assert env.calls == []


@pytest.mark.parametrize("capability", CAPABILITIES[:2])
@pytest.mark.parametrize("mode", ["omitted", "selected", "cleared"])
def test_create_passes_only_requested_headers_and_replays(capability, mode):
    env = _env()
    parameters = _document_parameters(env, capability)
    headers = _headers(
        "out_invoice" if capability.startswith("customer") else "in_invoice"
    )
    if mode == "selected":
        parameters.update(headers)
    elif mode == "cleared":
        parameters.update(dict.fromkeys(FIELDS))
    before = deepcopy(parameters)
    assert not _dispatch(env, capability, parameters)["idempotent_replay"]
    assert _dispatch(env, capability, parameters)["idempotent_replay"]
    creations = [call for call in env.calls if call[:2] == ("create", "account.move")]
    assert len(creations) == 1
    values = creations[0][2]
    for field in FIELDS:
        if mode == "omitted":
            assert field not in values
        else:
            assert values[field] == (headers[field] if mode == "selected" else False)
    line = values["invoice_line_ids"][0][2]
    assert line["account_id"] == parameters["lines"][0]["account_id"]
    assert line["tax_ids"] == [(6, 0, parameters["lines"][0]["tax_ids"])]
    assert line["price_unit"] == Decimal(parameters["lines"][0]["price_unit"])
    assert parameters == before
    if mode != "selected":
        assert not any(
            call[0] == "search"
            and call[1] in {"res.partner.bank", "account.fiscal.position"}
            for call in env.calls
        )
    else:
        bank_search = next(
            call for call in env.calls if call[:2] == ("search", "res.partner.bank")
        )
        assert all(
            term[0] not in {"currency_id", "allow_out_payment"}
            for term in bank_search[2]
        )


@pytest.mark.parametrize("move_type", MOVE_TYPES)
def test_update_selects_preserves_and_clears_headers_with_immediate_replays(move_type):
    env = _env()
    invoice = _invoice(env, move_type)
    headers = _headers(move_type)
    for changes in (
        headers,
        {"reference": "Keep financial headers"},
        dict.fromkeys(FIELDS),
    ):
        parameters = {"move_id": invoice.id, "changes": changes}
        assert not _dispatch(env, "invoice.update", parameters)["idempotent_replay"]
        assert _dispatch(env, "invoice.update", parameters)["idempotent_replay"]
        assert runtime._current_invoice_changes(invoice, set(changes)) == changes
        if "reference" in changes:
            assert runtime._current_invoice_changes(invoice, set(FIELDS)) == headers
    writes = [call[3] for call in env.calls if call[:2] == ("write", "account.move")]
    assert writes == [
        headers,
        {"ref": "Keep financial headers"},
        dict.fromkeys(FIELDS, False),
    ]
    invoice.state = "posted"
    assert _dispatch(env, "invoice.update", parameters)["idempotent_replay"]
    with pytest.raises(Failure) as caught:
        _dispatch(env, "invoice.update", {"move_id": invoice.id, "changes": headers})
    assert caught.value.code == "state_conflict"
    assert sum(call[:2] == ("write", "account.move") for call in env.calls) == 3


@pytest.mark.parametrize("subject", [*CAPABILITIES[:2], *MOVE_TYPES])
@pytest.mark.parametrize(
    "invalid",
    [
        "bank_missing",
        "bank_company",
        "bank_archived",
        "position_missing",
        "position_company",
        "position_archived",
    ],
)
def test_financial_references_reject_unavailable_records_before_writing(
    subject, invalid
):
    env = _env()
    if subject in MOVE_TYPES:
        capability = "invoice.update"
        invoice = _invoice(env, subject)
        headers = _headers(subject)
        parameters = {"move_id": invoice.id, "changes": headers}
    else:
        capability = subject
        parameters = _document_parameters(env, capability)
        headers = _headers(
            "out_invoice" if capability.startswith("customer") else "in_invoice"
        )
    field, model = (
        ("partner_bank_id", "res.partner.bank")
        if invalid.startswith("bank")
        else ("fiscal_position_id", "account.fiscal.position")
    )
    record = env.models[model].browse(headers[field]).records[0]
    if invalid.endswith("missing"):
        headers[field] = 999
    elif invalid.endswith("company"):
        record.company_id = env.add("res.company", 8, name="Other company")
    else:
        record.active = False
    if capability != "invoice.update":
        parameters.update(headers)
    with pytest.raises(Failure) as caught:
        _dispatch(env, capability, parameters)
    assert caught.value.code == "record_not_found"
    assert not any(call[0] in {"create", "write"} for call in env.calls)


@pytest.mark.parametrize("move_type", MOVE_TYPES)
@pytest.mark.parametrize("bank_id", [70, 71])
def test_update_preserves_explicit_bank_selection_with_a_partner_change(
    move_type, bank_id
):
    env = _env()
    invoice = _invoice(env, move_type)
    parent = env.add("res.partner", 25, company_id=False)
    contact = env.add("res.partner", 26, company_id=False)
    parent.commercial_partner_id = contact.commercial_partner_id = Records(
        env, "res.partner", [parent]
    )
    changes = {"partner_id": contact.id, "partner_bank_id": bank_id}
    assert not _dispatch(
        env, "invoice.update", {"move_id": invoice.id, "changes": changes}
    )["idempotent_replay"]
    search = next(
        call for call in env.calls if call[:2] == ("search", "res.partner.bank")
    )
    assert ("company_id", "in", [False, 7]) in search[2]
    assert all(
        term[0] not in {"partner_id", "currency_id", "allow_out_payment"}
        for term in search[2]
    )
    assert runtime._current_invoice_changes(invoice, set(changes)) == changes
    assert sum(call[:2] == ("write", "account.move") for call in env.calls) == 1


@pytest.mark.parametrize("move_type", ["in_invoice", "out_refund"])
def test_native_company_bank_on_supplier_side_replays_without_an_owner_filter(
    move_type,
):
    env = _env()
    invoice = _invoice(env, move_type)
    invoice.partner_bank_id = env.models["res.partner.bank"].browse(70)
    invoice.state = "posted"
    result = _dispatch(
        env,
        "invoice.update",
        {"move_id": invoice.id, "changes": {"partner_bank_id": 70}},
    )
    assert result["idempotent_replay"]
    assert not any(call[0] == "write" for call in env.calls)


@pytest.mark.parametrize("capability", CAPABILITIES)
@pytest.mark.parametrize("model", ["res.partner.bank", "account.fiscal.position"])
def test_financial_reference_read_access_is_not_bypassed(capability, model):
    env = _env()
    env.denied_access = (model, "read")
    parameters = (
        {"move_id": 610, "changes": _headers("out_invoice")}
        if capability == "invoice.update"
        else {**_document_parameters(env, capability), **_headers("out_invoice")}
    )
    result = _dispatch(env, capability, parameters)
    assert not result["access_allowed"] and result["result"] is None
    assert not any(call[0] in {"create", "write"} for call in env.calls)


@pytest.mark.parametrize("capability", CAPABILITIES[:2])
@pytest.mark.parametrize("field", FIELDS)
def test_create_key_conflicts_if_financial_header_presence_changes(capability, field):
    env = _env()
    parameters = _document_parameters(env, capability)
    _dispatch(env, capability, parameters)
    parameters[field] = None
    with pytest.raises(Failure) as caught:
        _dispatch(env, capability, parameters)
    assert caught.value.code == "idempotency_conflict"
    assert sum(call[:2] == ("create", "account.move") for call in env.calls) == 1


@pytest.mark.parametrize("field", FIELDS)
def test_update_checks_native_readback_before_reporting_success(monkeypatch, field):
    env = _env()
    invoice = _invoice(env, "out_invoice")
    monkeypatch.setattr(Records, "write", lambda *_args: True)
    with pytest.raises(Failure) as caught:
        _dispatch(
            env,
            "invoice.update",
            {"move_id": invoice.id, "changes": {field: _headers("out_invoice")[field]}},
        )
    assert caught.value.code == "odoo_write_error"


@pytest.mark.parametrize("capability", CAPABILITIES)
def test_parent_company_fiscal_positions_follow_native_company_scope(capability):
    env = _env()
    parent = env.add("res.company", 1, name="Parent company")
    env.company.parent_id = Records(env, "res.company", [parent])
    env.models["account.fiscal.position"].browse(72).records[0].company_id = parent
    parameters = (
        {
            "move_id": _invoice(env, "out_invoice").id,
            "changes": {"fiscal_position_id": 72},
        }
        if capability == "invoice.update"
        else {**_document_parameters(env, capability), "fiscal_position_id": 72}
    )
    assert not _dispatch(env, capability, parameters)["idempotent_replay"]
    search = next(
        call for call in env.calls if call[:2] == ("search", "account.fiscal.position")
    )
    assert ("company_id", "parent_of", [7]) in search[2]
    assert ("active", "=", True) in search[2]
    assert all(call[2] == 7 for call in env.calls if call[0] == "company")


def test_current_financial_headers_normalize_native_many2one_records():
    env = _env()
    invoice = _invoice(env, "out_invoice")
    invoice.partner_bank_id = env.models["res.partner.bank"].browse(70)
    invoice.fiscal_position_id = env.models["account.fiscal.position"].browse(72)
    assert runtime._current_invoice_changes(invoice, set(FIELDS)) == _headers(
        "out_invoice"
    )
