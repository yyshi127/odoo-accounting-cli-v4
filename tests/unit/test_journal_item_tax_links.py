from decimal import Decimal

import pytest
import test_core_object_reads as public
import test_core_object_reads_runtime as native

from odoo_accounting_cli_v4.contracts import success_document
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

_fake_odoo_expression = native._fake_odoo_expression
CAPABILITIES = ("journal_item.search", "journal_item.get")


@pytest.fixture(scope="module")
def registry():
    return load_registry()


@pytest.mark.parametrize("capability_id", CAPABILITIES)
@pytest.mark.parametrize(
    "tax_line_id,tax_ids,base,expected",
    [
        (False, [], Decimal("0.00"), (None, [], "0")),
        (None, [], Decimal("-0.00"), (None, [], "0")),
        (False, [11, 5], Decimal(0), (None, [5, 11], "0")),
        (5, [], Decimal("-100.500"), (5, [], "-100.5")),
        (11, [], Decimal("100.500"), (11, [], "100.5")),
    ],
)
def test_journal_item_native_tax_links(
    capability_id, tax_line_id, tax_ids, base, expected
):
    env, fixture = native._fixture()
    line = fixture["journal_lines"][0]
    line.tax_line_id = tax_line_id
    line.tax_ids = tax_ids
    line.tax_base_amount = base
    env.models["account.tax"].access = False

    page = native._dispatch(env, capability_id, native._parameters(capability_id))
    item = page["items"][0]

    assert (item["tax_line_id"], item["tax_ids"], item["tax_base_amount"]) == expected
    assert ("read_options", {"load": None}) in env.models["account.move.line"].calls
    assert env.models["account.tax"].calls == []


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_journal_item_tax_reference_does_not_fetch_name(capability_id):
    env, fixture = native._fixture()
    fixture["journal_lines"][0].tax_line_id = native.Record(id=5)
    page = native._dispatch(env, capability_id, native._parameters(capability_id))
    assert page["items"][0]["tax_line_id"] == 5
    assert env.models["account.tax"].calls == []


@pytest.mark.parametrize("capability_id", CAPABILITIES)
@pytest.mark.parametrize(
    "field,value",
    [("tax_line_id", value) for value in (True, 0, -1, 1.5, "5", {}, [0, "x"])]
    + [("tax_ids", value) for value in (False, None, [True], [0], [-1], [5, 5])]
    + [("tax_base_amount", value) for value in (False, None, "NaN", "Infinity")],
)
def test_journal_item_invalid_native_tax_values(capability_id, field, value):
    env, fixture = native._fixture()
    setattr(fixture["journal_lines"][0], field, value)
    with pytest.raises(native.Failure) as error:
        native._dispatch(env, capability_id, native._parameters(capability_id))
    assert error.value.code == "odoo_runtime_error"


def _read(capability_id, item):
    return public.read_core_object(
        capability_id,
        public.FakePort([item]),
        public._request({"line_id": 31} if capability_id.endswith(".get") else {}),
    )


def _schema(registry, capability_id, item):
    data = (
        item
        if capability_id.endswith(".get")
        else {"items": [item], "has_more": False, "next_cursor": None}
    )
    registry.validate_instance(
        f"schemas/v1/{capability_id}.response.schema.json",
        success_document(
            capability_id,
            data,
            request_id=public.REQUEST_ID,
            database="odoo_cli_v4_dev",
            company_id=7,
            user_id=42,
            model="account.move.line",
            record_ids=[31],
        ),
    )


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_journal_item_tax_contract(capability_id, registry):
    item = public._item(capability_id)
    _read(capability_id, item)
    _schema(registry, capability_id, item)
    item.update(tax_line_id=5, tax_ids=[5, 11], tax_base_amount="-100.5")
    _read(capability_id, item)
    _schema(registry, capability_id, item)


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_journal_item_unnamed_draft_move_contract(capability_id, registry):
    item = public._item(capability_id)
    item["move"].update(name=None, state="draft", move_type="out_invoice")

    _read(capability_id, item)
    _schema(registry, capability_id, item)

    item["move"]["name"] = ""
    with pytest.raises(public.CoreObjectReadError):
        _read(capability_id, item)
    with pytest.raises(InstanceValidationError):
        _schema(registry, capability_id, item)


@pytest.mark.parametrize("capability_id", CAPABILITIES)
@pytest.mark.parametrize(
    "field,value",
    [("tax_line_id", value) for value in (False, 0, -1, "5", [5, "name"])]
    + [("tax_ids", value) for value in (False, None, [False], [0], [5, 5])]
    + [("tax_base_amount", value) for value in (None, False, 100, "NaN", "1e2")],
)
def test_journal_item_invalid_tax_contract(capability_id, field, value, registry):
    item = public._item(capability_id)
    item[field] = value
    with pytest.raises(public.CoreObjectReadError):
        _read(capability_id, item)
    with pytest.raises(InstanceValidationError):
        _schema(registry, capability_id, item)


@pytest.mark.parametrize("capability_id", CAPABILITIES)
@pytest.mark.parametrize("field", ["tax_line_id", "tax_ids", "tax_base_amount"])
def test_journal_item_tax_fields_required(capability_id, field, registry):
    item = public._item(capability_id)
    del item[field]
    with pytest.raises(public.CoreObjectReadError):
        _read(capability_id, item)
    with pytest.raises(InstanceValidationError):
        _schema(registry, capability_id, item)


@pytest.mark.parametrize("capability_id", CAPABILITIES)
@pytest.mark.parametrize("field,value", [("tax_line_id", 5.0), ("tax_ids", [11, 5])])
def test_journal_item_bridge_tax_ids_are_strict_and_sorted(capability_id, field, value):
    item = public._item(capability_id)
    item[field] = value
    with pytest.raises(public.CoreObjectReadError):
        _read(capability_id, item)
