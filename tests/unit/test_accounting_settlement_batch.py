from __future__ import annotations

import hashlib
import io
import json
from copy import deepcopy
from datetime import date
from types import SimpleNamespace

import pytest
from test_company_processing_batch import result as config_result
from test_core_object_reads_runtime import Env, Model, Records, _record
from test_core_writes_runtime import Failure
from test_fiscal_mapping_writes import request

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4 import settlement_preview_contracts as preview
from odoo_accounting_cli_v4.bridge import core_object_reads_runtime as read_runtime
from odoo_accounting_cli_v4.bridge import core_writes_runtime as runtime
from odoo_accounting_cli_v4.capabilities import core_object_reads, core_writes
from odoo_accounting_cli_v4.registry import load_registry

ACCOUNT_FIELDS = ("tax_payable_account_id", "tax_receivable_account_id", "advance_tax_payment_account_id")
PARAMETERS = {
    "tax.group.create": {"name": "Settlement tax group", "sequence": 10, "preceding_subtotal": None,
                         "tax_payable_account_id": 51, "tax_receivable_account_id": 52, "advance_tax_payment_account_id": 53},
    "tax.group.update": {"tax_group_id": 31, "changes": {field: None for field in ACCOUNT_FIELDS}},
    "bank.statement.create": {"transaction_ids": [42, 41], "reference": "Opening balance", "balance_start": "100", "balance_end_real": "100.75"},
    "bank.statement.update": {"statement_id": 31, "changes": {"balance_start": "-2.5"}},
}
READ_PARAMETERS = {
    preview.TAX_ID: {"tax_ids": [32, 31], "currency_id": 6, "price_unit": "-100", "quantity": "2", "is_refund": True},
    preview.PAYMENT_TERM_ID: {"payment_term_id": 31, "date_ref": "2026-10-02", "currency_id": 6,
                             "tax_amount": "40", "tax_amount_currency": "10", "untaxed_amount": "400", "untaxed_amount_currency": "100"},
    "tax.group.get": {"tax_group_id": 31},
    "tax.group.list": {},
}


def result(capability_id, parameters):
    return {**config_result("", {}), "model": "account.tax.group" if capability_id.startswith("tax.group.") else "account.bank.statement",
            "id": parameters.get("tax_group_id", parameters.get("statement_id", 31)),
            "state": "active" if capability_id.startswith("tax.group.") else "complete",
            "line_ids": [] if capability_id.startswith("tax.group.") else [41, 42]}


@pytest.fixture(scope="module")
def registry():
    return load_registry()


def read_item(capability_id):
    if capability_id.startswith("tax.group."):
        return {"id": 31, "company_id": 7, "name": "Settlement tax group", "sequence": 10, "country": None,
                "preceding_subtotal": None, **{field: value for field, value in zip(ACCOUNT_FIELDS, (51, 52, None))}}
    parameters = preview.normalize_parameters(capability_id, READ_PARAMETERS[capability_id])
    item = {"id": 7 if capability_id == preview.TAX_ID else 31, "company_id": 7, "currency_id": 6, "input": parameters}
    if capability_id == preview.TAX_ID:
        return {**item, "total_excluded": "-200", "total_included": "-230", "total_void": "-200", "base_tag_ids": [61],
                "taxes": [{"tax_id": 31, "tax_repartition_line_id": 71, "name": "VAT", "amount": "-30", "base": "-200",
                           "sequence": 1, "account_id": 51, "price_include": False, "tax_exigibility": "on_invoice", "group_tax_id": 32, "tag_ids": [62]}]}
    return {**item, "company_currency_id": 5, "total_amount": "440", "discount_percentage": "0", "discount_date": None,
            "discount_balance": "0", "discount_amount_currency": "0", "line_ids": [
                {"date": "2026-10-12", "company_amount": "176", "foreign_amount": "44"},
                {"date": "2026-11-01", "company_amount": "264", "foreign_amount": "66"}]}


@pytest.mark.parametrize("capability_id", READ_PARAMETERS)
def test_public_read_cli_closed_schema_parameters_and_company_binding(capability_id, registry, monkeypatch):
    expected, req = read_item(capability_id), request(READ_PARAMETERS[capability_id])
    normalized = core_object_reads.validate_core_object_read_request(capability_id, req)[2]

    class Port:
        user_id = 42

        def read(self, **payload):
            assert payload["company_id"] == 7
            if capability_id in preview.READ_IDS:
                assert payload["parameters"] == normalized
            return {"user_id": 42, "company_visible": True, "module_installed": True, "access_allowed": True,
                    "cursor_found": True, "items": [expected]}

    registry.validate_instance(f"schemas/v1/{capability_id}.request.schema.json", req)
    monkeypatch.setattr(cli, "load_registry", lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    code = cli.main(["read", capability_id, "--request", "-"], stdin=io.StringIO(json.dumps(req)), stdout=stdout, stderr=stderr, port_factory=lambda *args: Port())
    assert code == 0, stdout.getvalue()
    response = json.loads(stdout.getvalue())
    registry.validate_instance(f"schemas/v1/{capability_id}.response.schema.json", response)
    assert response["data"] == (expected if capability_id != "tax.group.list" else {"items": [expected], "has_more": False, "next_cursor": None})
    assert not stderr.getvalue()
    for field, value in (("company_id", 8), ("extra", True)):
        original = deepcopy(expected)
        expected[field] = value
        with pytest.raises(core_object_reads.CoreObjectReadError):
            core_object_reads.read_core_object(capability_id, Port(), req)
        expected.clear()
        expected.update(original)


@pytest.mark.parametrize("capability_id", preview.READ_IDS)
def test_preview_result_is_bound_to_exact_normalized_input_and_target(capability_id):
    item = read_item(capability_id)
    assert preview.valid_read_item(capability_id, item, 7)
    for field, value in (("id", 99), ("currency_id", 8), ("company_id", 8), ("extra", True)):
        assert not preview.valid_read_item(capability_id, {**item, field: value}, 7)
    changed = deepcopy(item)
    changed["input"]["currency_id"] = 8
    assert not preview.valid_read_item(capability_id, changed, 7)
    normalized = preview.normalize_parameters(capability_id, READ_PARAMETERS[capability_id])
    changed = deepcopy(item)
    changed["input"]["price_unit" if capability_id == preview.TAX_ID else "tax_amount"] = "9"
    assert preview.valid_read_item(capability_id, changed, 7)

    class Port:
        user_id = 42

        def read(self, **payload):
            assert payload["parameters"] == normalized
            return {"user_id": 42, "company_visible": True, "module_installed": True, "access_allowed": True, "cursor_found": True, "items": [changed]}

    with pytest.raises(core_object_reads.CoreObjectReadError):
        core_object_reads.read_core_object(capability_id, Port(), request(READ_PARAMETERS[capability_id]))


@pytest.mark.parametrize("capability_id,changes", [
    (preview.TAX_ID, {"tax_ids": [31, 31]}), (preview.TAX_ID, {"tax_ids": [False]}),
    (preview.TAX_ID, {"tax_ids": list(range(1, 102))}), (preview.TAX_ID, {"price_unit": 100}),
    (preview.TAX_ID, {"price_unit": "110.0"}), (preview.TAX_ID, {"quantity": "1.0"}),
    (preview.TAX_ID, {"quantity": "NaN"}), (preview.TAX_ID, {"is_refund": 1}),
    (preview.TAX_ID, {"product_id": 0}), (preview.TAX_ID, {"handle_price_include": None}),
    (preview.PAYMENT_TERM_ID, {"date_ref": "2026-02-30"}), (preview.PAYMENT_TERM_ID, {"sign": True}),
    (preview.PAYMENT_TERM_ID, {"sign": 0}), (preview.PAYMENT_TERM_ID, {"cash_rounding_id": False}),
    (preview.PAYMENT_TERM_ID, {"tax_amount_currency": 10}), (preview.PAYMENT_TERM_ID, {"untaxed_amount": "Infinity"}),
])
def test_preview_parameters_are_closed_typed_and_bounded(capability_id, changes):
    with pytest.raises(ValueError):
        preview.normalize_parameters(capability_id, {**READ_PARAMETERS[capability_id], **changes})


def test_tax_preview_empty_signed_zero_values_sort_and_explicit_native_defaults():
    params = {"tax_ids": [], "currency_id": 6, "price_unit": "0", "quantity": "-2"}
    normalized = preview.normalize_parameters(preview.TAX_ID, params)
    assert normalized == {"tax_ids": [], "currency_id": 6, "price_unit": "0", "quantity": "-2",
                          "product_id": None, "partner_id": None, "is_refund": False, "handle_price_include": True, "include_caba_tags": False}
    assert params["quantity"] == "-2"
    assert preview.normalize_parameters(preview.TAX_ID, READ_PARAMETERS[preview.TAX_ID])["tax_ids"] == [31, 32]
    assert READ_PARAMETERS[preview.TAX_ID]["tax_ids"] == [32, 31]


def test_native_tax_repartition_rows_keep_order_and_repeated_tax_ids():
    item = read_item(preview.TAX_ID)
    item["taxes"] += [{**item["taxes"][0], "tax_repartition_line_id": 72}]
    assert preview.valid_read_item(preview.TAX_ID, item, 7)
    for field, value in (("tax_repartition_line_id", False), ("tag_ids", [62, 62]), ("amount", 15), ("account_id", 0)):
        changed = deepcopy(item)
        changed["taxes"][0][field] = value
        assert not preview.valid_read_item(preview.TAX_ID, changed, 7)


@pytest.mark.parametrize("capability_id", PARAMETERS)
def test_public_write_schema_confirmation_key_and_native_result_binding(capability_id, registry, monkeypatch):
    params, expected = PARAMETERS[capability_id], result(capability_id, PARAMETERS[capability_id])
    req = request(params)
    normalized = core_writes.validate_core_write_request(capability_id, req)[2]
    key = core_writes._expected_idempotency_key(capability_id, normalized, 7) or "settlement:create:31"
    assert runtime._valid_parameters(capability_id, normalized, 7)
    assert runtime._deterministic_key(capability_id, normalized, 7) == core_writes._expected_idempotency_key(capability_id, normalized, 7)
    registry.validate_instance(f"schemas/v1/{capability_id}.request.schema.json", req)

    class Port:
        user_id = 42

        def execute(self, **payload):
            assert payload["parameters"] == normalized and payload["company_id"] == 7
            assert payload["confirmation"] == capability_id and payload["idempotency_key"] == key
            return {"user_id": 42, "company_visible": True, "module_installed": True, "access_allowed": True,
                    "idempotent_replay": False, "result": expected}

    monkeypatch.setattr(cli, "load_registry", lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    code = cli.main(["write", "run", capability_id, "--request", "-", "--confirm", capability_id, "--idempotency-key", key],
                    stdin=io.StringIO(json.dumps(req)), stdout=stdout, stderr=stderr, port_factory=lambda *args: Port())
    assert code == 0, stdout.getvalue()
    response = json.loads(stdout.getvalue())
    registry.validate_instance(f"schemas/v1/{capability_id}.response.schema.json", response)
    assert response["data"]["result"] == expected and not stderr.getvalue()
    for confirmation in (None, "other.operation"):
        with pytest.raises(core_writes.CoreWriteError):
            core_writes.execute_core_write(Port(), capability_id, req, key, confirmation)
    for field, value in (("company_id", 8), ("model", "res.partner"), ("extra", True)):
        with pytest.raises(core_writes.CoreWriteError):
            core_writes._validate_result(capability_id, normalized, {**expected, field: value}, company_id=7, idempotent_replay=False)


@pytest.mark.parametrize("capability_id", ["tax.group.create", "tax.group.update"])
@pytest.mark.parametrize("value", [False, 0, -1, 1.5, "51"])
def test_settlement_accounts_are_nullable_positive_native_ids(capability_id, value):
    params = deepcopy(PARAMETERS[capability_id])
    values = params if capability_id.endswith("create") else params["changes"]
    values["tax_payable_account_id"] = value
    with pytest.raises(core_writes.CoreWriteError):
        core_writes.validate_core_write_request(capability_id, request(params))


@pytest.mark.parametrize("capability_id", PARAMETERS)
def test_optional_extensions_do_not_change_legacy_normalized_keys(capability_id):
    params = deepcopy(PARAMETERS[capability_id])
    values = params if capability_id.endswith("create") else params["changes"]
    for field in (*ACCOUNT_FIELDS, "balance_start"):
        values.pop(field, None)
    if not values:
        values["reference" if capability_id.startswith("bank.") else "sequence"] = "Old reference" if capability_id.startswith("bank.") else 20
    normalized = core_writes.validate_core_write_request(capability_id, request(params))[2]
    old_values = normalized if capability_id.endswith("create") else normalized["changes"]
    assert not {*ACCOUNT_FIELDS, "balance_start"} & set(old_values)
    digest = hashlib.sha256(json.dumps(old_values, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()[:32]
    expected = f"{capability_id}:{7 if capability_id.endswith('create') else 31}:{digest}"
    assert core_writes._expected_idempotency_key(capability_id, normalized, 7) == expected
    assert runtime._deterministic_key(capability_id, normalized, 7) == expected


@pytest.mark.parametrize("value", [True, None, 1, "NaN", "1e3", "00", "-0"])
def test_statement_start_is_a_canonical_signed_decimal_string(value):
    with pytest.raises(core_writes.CoreWriteError):
        core_writes.validate_core_write_request("bank.statement.update", request({"statement_id": 31, "changes": {"balance_start": value}}))


@pytest.mark.parametrize("changes", [{"balance_start": "-2.5"}, {"balance_start": "0", "balance_end_real": "9"}])
def test_statement_start_native_recomputation_explicit_end_override_and_serial_replay(changes, monkeypatch):
    writes = []
    statement = SimpleNamespace(id=31, company_id=SimpleNamespace(id=7), reference="Opening", balance_start=100.0,
                                balance_end=100.75, balance_end_real=100.75, currency_id=SimpleNamespace(round=lambda value: round(float(value), 2)),
                                invalidate_recordset=lambda fields: None)

    def write(values):
        writes.append(dict(values))
        if "balance_start" in values:
            statement.balance_start = float(values["balance_start"])
            statement.balance_end = statement.balance_start + 0.75
            statement.balance_end_real = statement.balance_end
        if "balance_end_real" in values:
            statement.balance_end_real = float(values["balance_end_real"])

    statement.write = write
    monkeypatch.setattr(runtime, "_search_one", lambda *args: statement)
    monkeypatch.setattr(runtime, "_bank_statement_result", lambda *args: result("bank.statement.update", {"statement_id": 31}))
    parameters = {"statement_id": 31, "changes": changes}
    assert runtime._update_bank_statement(None, parameters, 7, Failure)[1] is False
    assert set(writes[0]) == set(changes)
    assert statement.balance_end_real == float(changes.get("balance_end_real", statement.balance_end))
    assert runtime._update_bank_statement(None, parameters, 7, Failure)[1] is True and len(writes) == 1


def test_statement_start_rejects_failed_native_ending_balance_readback(monkeypatch):
    statement = SimpleNamespace(id=31, reference=None, balance_start=100.0, balance_end=100.75, balance_end_real=99.0,
                                currency_id=SimpleNamespace(round=lambda value: round(float(value), 2)), invalidate_recordset=lambda fields: None)
    statement.write = lambda values: setattr(statement, "balance_start", float(values["balance_start"]))
    monkeypatch.setattr(runtime, "_search_one", lambda *args: statement)
    with pytest.raises(Failure) as caught:
        runtime._update_bank_statement(None, {"statement_id": 31, "changes": {"balance_start": "0"}}, 7, Failure)
    assert caught.value.code == "odoo_write_error" and caught.value.exit_code == 6


@pytest.mark.parametrize("empty", [False, True])
def test_native_tax_compute_receives_signed_arguments_and_preserves_repartition_order(empty, monkeypatch):
    company, currency = _record(7), _record(6, active=True)
    taxes = [_record(31, company_id=company, active=True, amount_type="percent", children_tax_ids=Records())]
    env = Env({"res.company": Model("res.company", [company]), "res.currency": Model("res.currency", [currency]),
               "account.tax": Model("account.tax", taxes), "product.product": Model("product.product"), "res.partner": Model("res.partner")})
    monkeypatch.setattr(Records, "filtered", lambda rows, predicate: Records(row for row in rows if predicate(row)), raising=False)
    monkeypatch.setattr(Records, "children_tax_ids", property(lambda rows: Records(child for row in rows for child in row.children_tax_ids)), raising=False)
    calls = []

    def compute(rows, price_unit, **kwargs):
        calls.append((rows.ids, price_unit, kwargs))
        row = {"id": 31, "name": "VAT", "amount": -15.0, "base": -100.0, "sequence": -1, "account_id": False,
               "price_include": True, "tax_exigibility": "on_invoice", "group": False, "tag_ids": [62, 61, 62]}
        return {"total_excluded": -100, "total_included": -130 if rows else -100, "total_void": -100,
                "base_tags": [62, 61, 62], "taxes": [{**row, "tax_repartition_line_id": 72}, {**row, "tax_repartition_line_id": 71}] if rows else []}

    monkeypatch.setattr(Records, "compute_all", compute, raising=False)
    parameters = preview.normalize_parameters(preview.TAX_ID, {"tax_ids": [] if empty else [31], "currency_id": 6,
                     "price_unit": "-100", "quantity": "-2", "is_refund": True, "handle_price_include": False, "include_caba_tags": True})
    item = read_runtime._tax_compute_rows(env, parameters, 7)[0]
    ids, price_unit, kwargs = calls[0]
    assert ids == parameters["tax_ids"] and price_unit == -100.0
    assert kwargs["quantity"] == -2.0 and kwargs["is_refund"] and kwargs["include_caba_tags"] and not kwargs["handle_price_include"]
    assert kwargs["currency"].id == 6 and not kwargs["product"] and not kwargs["partner"]
    assert item["base_tag_ids"] == [61, 62] and item["input"] == parameters
    assert [row["tax_repartition_line_id"] for row in item["taxes"]] == ([] if empty else [72, 71])
    assert all(row["tag_ids"] == [61, 62] and row["account_id"] is None for row in item["taxes"])
    assert ("with_company", 7) in env.models["account.tax"].calls


@pytest.mark.parametrize("discount", [False, True])
def test_native_term_compute_passes_both_currencies_date_sign_rounding_and_default_discount(discount, monkeypatch):
    currency = _record(6, active=True)
    company = _record(7, currency_id=_record(5))
    term = _record(31, company_id=False, active=False)
    rounding = _record(77)
    env = Env({"res.company": Model("res.company", [company]), "res.currency": Model("res.currency", [currency]),
               "account.payment.term": Model("account.payment.term", [term]), "account.cash.rounding": Model("account.cash.rounding", [rounding])})
    calls = []

    def compute(rows, **kwargs):
        calls.append((rows.id, kwargs))
        return {"total_amount": -440.0, "discount_percentage": 2.0 if discount else 0.0,
                "discount_date": date(2026, 10, 12) if discount else False, "discount_balance": -432.0 if discount else 0,
                **({"discount_amount_currency": -108.0} if discount else {}),
                "line_ids": [{"date": date(2026, 11, 1), "company_amount": -440.0, "foreign_amount": -110.0}]}

    monkeypatch.setattr(Records, "_compute_terms", compute, raising=False)
    parameters = preview.normalize_parameters(preview.PAYMENT_TERM_ID, {
        **READ_PARAMETERS[preview.PAYMENT_TERM_ID], "tax_amount": "-40", "tax_amount_currency": "-10",
        "untaxed_amount": "-400", "untaxed_amount_currency": "-100", "sign": -1, "cash_rounding_id": 77 if discount else None})
    item = read_runtime._payment_term_compute_rows(env, parameters, 7)[0]
    identifier, kwargs = calls[0]
    assert identifier == 31 and kwargs["date_ref"] == date(2026, 10, 2) and kwargs["sign"] == -1
    assert [kwargs[field] for field in ("tax_amount", "tax_amount_currency", "untaxed_amount", "untaxed_amount_currency")] == [-40.0, -10.0, -400.0, -100.0]
    assert kwargs["company"].id == 7 and kwargs["currency"].id == 6
    assert (kwargs["cash_rounding"].id if kwargs["cash_rounding"] else None) == (77 if discount else None)
    assert item["discount_amount_currency"] == ("-108" if discount else "0")
    assert item["company_currency_id"] == 5 and item["line_ids"][0]["date"] == "2026-11-01"
    assert item["input"] == parameters


def test_tax_group_settlement_patch_preserves_omitted_fields_and_checks_native_parent_company_domain(monkeypatch):
    company = SimpleNamespace(id=7, account_fiscal_country_id=False, country_id=False)
    group = SimpleNamespace(id=31, company_id=company, country_id=False, name="Settlement", sequence=10, preceding_subtotal=False,
                            tax_payable_account_id=SimpleNamespace(id=51), tax_receivable_account_id=SimpleNamespace(id=52), advance_tax_payment_account_id=False,
                            invalidate_recordset=lambda fields: None)
    writes, references = [], []

    def write(values):
        writes.append(values)
        for field, value in values.items():
            setattr(group, field, SimpleNamespace(id=value) if value else False)

    group.write = write
    monkeypatch.setattr(runtime, "_search_one", lambda env, model, *args: company if model == "res.company" else group)
    monkeypatch.setattr(runtime, "_ensure_ids", lambda env, model, ids, domain, *args: references.append((model, ids, domain)) or [])
    monkeypatch.setattr(runtime, "_reference_result", lambda *args, **kwargs: result("tax.group.update", {"tax_group_id": 31}))
    parameters = {"tax_group_id": 31, "changes": {"tax_payable_account_id": 53}}
    assert runtime._write_tax_group(None, "tax.group.update", parameters, 7, Failure)[1] is False
    assert writes == [{"tax_payable_account_id": 53}]
    assert group.tax_receivable_account_id.id == 52 and not group.advance_tax_payment_account_id
    assert references and references[0][0] == "account.account"
    assert ("company_ids", "parent_of", [7]) in references[0][2]
    assert runtime._write_tax_group(None, "tax.group.update", parameters, 7, Failure)[1] is True and len(writes) == 1
