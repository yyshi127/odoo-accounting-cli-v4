from __future__ import annotations

from copy import deepcopy
from decimal import Decimal

import pytest
import test_core_object_reads as public
import test_core_object_reads_runtime as native

from odoo_accounting_cli_v4 import journal_item_processing_contracts as contracts
from odoo_accounting_cli_v4.bridge import core_object_reads_runtime as runtime
from odoo_accounting_cli_v4.capabilities import core_object_reads, core_writes

_fake_odoo_expression = native._fake_odoo_expression
READ_IDS = ("journal_item.get", "journal_item.search")


def _patch(changes):
    return {"move_id": 81, "lines": [{"line_id": 31, "changes": changes}]}


def _detail():
    return {
        "id": 31, "move_id": 81, "company_id": 7, "parent_state": "draft",
        "move_type": "entry", "display_type": "product", "account_id": 11,
        "product_id": None, "product_uom_id": None, "deductible_amount": "100",
        "date_maturity": None, "amount_residual": "0", "amount_residual_currency": "0",
        "discount_date": None, "discount_amount_currency": "0", "payment_id": None,
        "statement_line_id": None, "no_followup": False, "currency_id": 6,
        "company_currency_id": 6,
    }


def _read(capability_id, item):
    parameters = {"line_id": 31} if capability_id == "journal_item.get" else {}
    return core_object_reads.read_core_object(
        capability_id, public.FakePort([item]), public._request(parameters)
    )


@pytest.mark.parametrize("changes", [
    {"tax_ids": []}, {"tax_ids": [5, 11]},
    {"tax_tag_ids": []}, {"tax_tag_ids": [51, 52]},
    {"tax_repartition_line_id": None}, {"tax_repartition_line_id": 71},
    {"tax_base_amount": "0"}, {"tax_base_amount": "-100.5"},
    {"tax_ids": list(range(1, 101))}, {"tax_tag_ids": list(range(1, 101))},
    {"tax_ids": [], "tax_tag_ids": [], "tax_repartition_line_id": None, "tax_base_amount": "0"},
])
def test_partial_entry_tax_inputs_are_independent_and_omission_stays_omitted(changes):
    parameters = _patch(changes)
    original = deepcopy(parameters)
    normalized = contracts.normalize_parameters("journal_entry.lines.update", parameters)
    _, _, sdk_parameters = core_writes.validate_core_write_request(
        "journal_entry.lines.update", public._request(parameters)
    )
    assert normalized == sdk_parameters == original
    assert parameters == original
    assert set(normalized["lines"][0]["changes"]) == set(changes)


def test_old_partial_patch_and_key_do_not_gain_tax_defaults():
    parameters = _patch({"name": "Existing description", "debit": "10"})
    normalized = contracts.normalize_parameters("journal_entry.lines.update", parameters)
    assert normalized == parameters
    assert not contracts.TAX_FIELDS.intersection(normalized["lines"][0]["changes"])
    assert core_writes._expected_idempotency_key("journal_entry.lines.update", normalized, 7) == (
        contracts.idempotency_key("journal_entry.lines.update", parameters, 7)
    )


BAD_CHANGES = (
    [(field, value) for field in ("tax_ids", "tax_tag_ids")
     for value in (None, False, True, {}, [False], [True], [0], [-1], [1.0], ["1"], [5, 5], [11, 5], list(range(1, 102)))]
    + [("tax_repartition_line_id", value) for value in (False, True, 0, -1, 1.0, "1", [], {})]
    + [("tax_base_amount", value) for value in (None, False, True, 1, 1.5, "-0", "0.0", "1.00", "01", "+1", "1e2", "NaN", "Infinity", " " + "1", "1" * 257)]
    + [("tax_line_id", 5)]
)


@pytest.mark.parametrize("field,value", BAD_CHANGES)
def test_partial_entry_tax_inputs_reject_invalid_ids_and_noncanonical_base(field, value):
    parameters = _patch({field: value})
    with pytest.raises(ValueError):
        contracts.normalize_parameters("journal_entry.lines.update", parameters)
    with pytest.raises(core_writes.CoreWriteError):
        core_writes.validate_core_write_request("journal_entry.lines.update", public._request(parameters))


@pytest.mark.parametrize("extra", [
    {}, {"tax_ids": []}, {"tax_ids": [5, 11]}, {"tax_tag_ids": []},
    {"tax_tag_ids": [51, 52]}, {"tax_line_id": None}, {"tax_line_id": 5},
    {"tax_repartition_line_id": None}, {"tax_repartition_line_id": 71},
    {"tax_base_amount": "0"}, {"tax_base_amount": "-100.5"},
    {"tax_ids": [5, 11], "tax_line_id": 5, "tax_tag_ids": [51, 52],
     "tax_repartition_line_id": 71, "tax_base_amount": "-100.5"},
])
def test_processing_details_accept_old_shape_or_independent_typed_tax_fields(extra):
    item = {**_detail(), **extra}
    assert contracts.valid_read_item(contracts.DETAIL_ID, item, 7)
    assert core_object_reads._valid_item(contracts.DETAIL_ID, item, 7)
    assert len(_detail()) == 20
    assert not contracts.valid_read_item(contracts.DETAIL_ID, item, 8)


@pytest.mark.parametrize("field,value", [
    (field, value) for field, value in BAD_CHANGES
    if field != "tax_line_id" and not (isinstance(value, list) and len(value) > 100)
] + [("tax_line_id", value) for value in (False, True, 0, -1, 1.0, "1", [1, "Tax"])]
  + [("unknown_tax_field", None)])
def test_processing_details_reject_invalid_new_tax_fields(field, value):
    item = {**_detail(), field: value}
    assert not contracts.valid_read_item(contracts.DETAIL_ID, item, 7)
    assert not core_object_reads._valid_item(contracts.DETAIL_ID, item, 7)


@pytest.mark.parametrize("field", ("id", "company_id", "move_id", "display_type", "amount_residual"))
def test_processing_details_keep_existing_fields_required(field):
    item = _detail()
    del item[field]
    assert not contracts.valid_read_item(contracts.DETAIL_ID, item, 7)


@pytest.mark.parametrize("capability_id", READ_IDS)
@pytest.mark.parametrize("extra", [
    {}, {"tax_tag_ids": []}, {"tax_tag_ids": [51, 52]},
    {"tax_repartition_line_id": None}, {"tax_repartition_line_id": 71},
    {"tax_tag_ids": [51, 52], "tax_repartition_line_id": 71},
])
def test_journal_item_get_and_search_keep_old_shape_with_independent_new_fields(capability_id, extra):
    item = {**public._item(capability_id), **extra}
    result = _read(capability_id, item)
    assert (result if capability_id == "journal_item.get" else result["items"][0]) == item
    # Existing full journal-item decimal responses keep their legacy literal format.
    assert item["debit"] == "125.50"


@pytest.mark.parametrize("capability_id", READ_IDS)
@pytest.mark.parametrize("field,value", [
    ("tax_tag_ids", value) for value in (None, False, True, {}, [False], [True], [0], [-1], [1.0], ["1"], [5, 5], [11, 5])
] + [("tax_repartition_line_id", value) for value in (False, True, 0, -1, 1.0, "1", [1, "Tax"])]
  + [("unknown_tax_field", None)])
def test_journal_item_get_and_search_reject_invalid_new_fields(capability_id, field, value):
    item = {**public._item(capability_id), field: value}
    with pytest.raises(core_object_reads.CoreObjectReadError):
        _read(capability_id, item)


@pytest.mark.parametrize("capability_id", READ_IDS)
@pytest.mark.parametrize("repartition", [False, None, 71])
def test_native_journal_item_reads_select_and_normalize_new_tax_projection(capability_id, repartition):
    env, fixture = native._fixture()
    line = fixture["journal_lines"][0]
    line.tax_ids, line.tax_tag_ids = [11, 5], [52, 51]
    line.tax_repartition_line_id = repartition
    line.tax_base_amount = Decimal("-100.500")
    page = native._dispatch(env, capability_id, native._parameters(capability_id))
    item = page["items"][0]
    assert item["tax_ids"] == [5, 11]
    assert item["tax_tag_ids"] == [51, 52]
    assert item["tax_repartition_line_id"] == (71 if repartition == 71 else None)
    assert item["tax_base_amount"] == "-100.5"
    assert core_object_reads._valid_item(capability_id, item, 7)
    selected = native._search_call(env.models["account.move.line"])[4]
    assert contracts.TAX_FIELDS | {"tax_line_id"} <= set(selected)
    assert ("read_options", {"load": None}) in env.models["account.move.line"].calls
    assert env.models["account.tax"].calls == []
    assert env.models["account.account.tag"].calls == []
    assert env.models["account.tax.repartition.line"].calls == []


@pytest.mark.parametrize("capability_id", READ_IDS)
@pytest.mark.parametrize("value", [None, False, [True], [0], [51, 51]])
def test_native_journal_item_reads_reject_invalid_tax_tag_relation(capability_id, value):
    env, fixture = native._fixture()
    fixture["journal_lines"][0].tax_tag_ids = value
    with pytest.raises(native.Failure) as error:
        native._dispatch(env, capability_id, native._parameters(capability_id))
    assert error.value.code == "odoo_runtime_error"


@pytest.mark.parametrize("base,expected", [(Decimal("-100.500"), "-100.5"), (Decimal("-0.00"), "0")])
def test_native_processing_details_select_and_normalize_all_tax_fields(monkeypatch, base, expected):
    raw = {**_detail(), "company_id": [7, "Company"], "move_id": 81,
           "account_id": [11, "Expense"], "tax_ids": [11, 5], "tax_tag_ids": [52, 51],
           "tax_line_id": [5, "Tax"], "tax_repartition_line_id": [71, "Repartition"],
           "tax_base_amount": base, "deductible_amount": 100.0,
           "discount_amount_currency": -0.0, "amount_residual": 0.0,
           "amount_residual_currency": 0.0, "date_maturity": False, "discount_date": False}

    def target_row(_env, target_id, company_id, fields):
        assert (target_id, company_id) == (31, 7)
        assert set(fields) == set(contracts.DETAIL_FIELDS)
        return deepcopy(raw)

    def related_rows(_env, model_name, record_ids, _fields, *, company_id):
        assert company_id == 7
        if model_name == "res.currency":
            assert record_ids == {6}
            return {6: {"id": 6, "name": "CNY"}}
        if model_name == "res.company":
            assert record_ids == {7}
            return {7: {"id": 7, "currency_id": 6}}
        assert model_name == "account.account" and record_ids == {11}
        return {11: {"id": 11, "company_ids": [7]}}

    monkeypatch.setattr(runtime, "_journal_item_target_row", target_row)
    monkeypatch.setattr(runtime, "_related_rows", related_rows)
    items = runtime._journal_item_processing_rows(object(), contracts.DETAIL_ID, {"journal_item_id": 31}, 7)
    assert len(items) == 1
    item = items[0]
    assert item["tax_ids"] == [5, 11] and item["tax_tag_ids"] == [51, 52]
    assert item["tax_line_id"] == 5 and item["tax_repartition_line_id"] == 71
    assert item["tax_base_amount"] == expected
    assert contracts.valid_read_item(contracts.DETAIL_ID, item, 7)
