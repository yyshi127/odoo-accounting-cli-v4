from __future__ import annotations

from copy import deepcopy
from decimal import Decimal

import pytest
from test_order_documents_runtime import (
    Env,
    Failure,
    Model,
    Records,
    _line_parameters,
    _models,
    _payload,
    _purchase_line,
    _purchase_order,
    _record,
    _refs,
    _sale_line,
    _sale_order,
    _search_parameters,
    _summary_parameters,
)

from odoo_accounting_cli_v4.bridge import order_documents_runtime as runtime


class ScopedModel(Model):
    def matching(self, domain):
        def matches(record):
            for field, operator, expected in domain:
                value = record
                for part in field.split("."):
                    value = getattr(value, part)
                value = getattr(value, "id", value)
                if operator == "=" and value != expected:
                    return False
                if operator == "in" and value not in expected:
                    return False
                if operator == ">" and value <= expected:
                    return False
                if operator == "<" and value >= expected:
                    return False
            return True

        return Records(sorted((record for record in self.records if matches(record)), key=lambda record: record.id))

    def search(self, domain, order=None, limit=None):
        original = self.records
        self.records = self.matching(domain)
        try:
            return super().search(domain, order, limit)
        finally:
            self.records = original

    def search_count(self, domain, limit=None):
        self.search_count_calls.append((deepcopy(domain), limit))
        count = len(self.matching(domain))
        return min(count, limit) if limit is not None else count


def fixture(kind):
    refs = _refs()
    order = (_sale_order if kind == "sale" else _purchase_order)(refs=refs)
    line = (_sale_line if kind == "sale" else _purchase_line)(order, refs)
    models = _models(**{f"{kind}_orders": [order], f"{kind}_lines": [line]})
    return refs, order, line, models


def expose(model, record, **values):
    model._fields.update({field: object() for field in values})
    for field, value in values.items():
        setattr(record, field, value)


@pytest.mark.parametrize("kind", ["sale", "purchase"])
@pytest.mark.parametrize("operation", ["get", "search"])
def test_native_header_inputs_and_sale_posted_amounts_are_optional_projections(kind, operation):
    _refs_value, order, _line, models = fixture(kind)
    expose(models[f"{kind}.order"], order, payment_term_id=_record(51), fiscal_position_id=False)
    if kind == "sale":
        expose(models["sale.order"], order, amount_invoiced=Decimal("12.50"), amount_to_invoice=0.0)
    parameters = {"order_id": order.id} if operation == "get" else _search_parameters()
    result = runtime.dispatch(Env(models=models), _payload(f"{kind}.order.{operation}", parameters), 7, failure_type=Failure)["items"][0]
    assert result["payment_term_id"] == 51 and result["fiscal_position_id"] is None
    if kind == "sale":
        assert result["amount_invoiced"] == "12.5" and result["amount_to_invoice"] == "0"
    else:
        assert "amount_invoiced" not in result and "amount_to_invoice" not in result


@pytest.mark.parametrize("kind", ["sale", "purchase"])
@pytest.mark.parametrize("summary", [False, True])
def test_accounting_filters_reach_native_domain_before_cursor_or_aggregate(kind, summary):
    _refs_value, order, _line, models = fixture(kind)
    expose(models[f"{kind}.order"], order, payment_term_id=_record(51), fiscal_position_id=_record(52))
    filters = {"user_id": 5, "payment_term_id": 51, "fiscal_position_id": 52, "invoice_statuses": ["to invoice"]}
    parameters = _summary_parameters(**filters) if summary else _search_parameters(**filters, after=10)
    original = deepcopy(parameters)
    capability = f"{kind}.order.analysis.summary" if summary else f"{kind}.order.search"
    runtime.dispatch(Env(models=models), _payload(capability, parameters), 7, failure_type=Failure)
    model = models[f"{kind}.order"]
    domains = [call["domain"] for call in model.read_group_calls] if summary else [model.search_count_calls[0][0], model.search_calls[0]["domain"]]
    for domain in domains:
        assert ("company_id", "=", 7) in domain
        for field in ("user_id", "payment_term_id", "fiscal_position_id"):
            assert (field, "=", filters[field]) in domain
        assert ("invoice_status", "in", ["to invoice"]) in domain
    assert parameters == original


@pytest.mark.parametrize("summary", [False, True])
def test_omitted_or_null_filters_preserve_legacy_domain_and_parameter_shape(summary):
    base = _summary_parameters() if summary else _search_parameters()
    kind = "sale"
    old = runtime._order_domain(kind, 7, base)
    extended = {**base, "user_id": None, "payment_term_id": None, "fiscal_position_id": None}
    if summary:
        extended["invoice_statuses"] = None
    assert runtime._order_domain(kind, 7, extended) == old
    assert not {"user_id", "payment_term_id", "fiscal_position_id"} & base.keys()


@pytest.mark.parametrize("kind", ["sale", "purchase"])
def test_negative_quantity_and_downpayment_filters_apply_before_native_paging_and_cursor(kind):
    _refs_value, order, negative, models = fixture(kind)
    positive = (_sale_line if kind == "sale" else _purchase_line)(order)
    positive.id = 10
    negative.qty_to_invoice = Decimal(-2)
    positive.is_downpayment = False
    negative.is_downpayment = True
    model = models[f"{kind}.order.line"] = ScopedModel(
        fields=set(models[f"{kind}.order.line"]._fields) | {"is_downpayment"}, records=[positive, negative],
    )
    parameters = _line_parameters(kind, is_downpayment=True, negative_to_invoice_only=True, limit=1)
    env = Env(models=models)
    result = runtime.dispatch(env, _payload(f"{kind}.order.line.search", parameters), 7, failure_type=Failure)
    assert [item["id"] for item in result["items"]] == [negative.id]
    assert result["items"][0]["to_invoice_quantity"] == "-2"
    assert ("qty_to_invoice", "<", 0) in model.search_calls[0]["domain"]
    assert ("is_downpayment", "=", True) in model.search_calls[0]["domain"]
    parameters["after"] = positive.id
    assert not runtime.dispatch(env, _payload(f"{kind}.order.line.search", parameters), 7, failure_type=Failure)["cursor_found"]
    assert ("qty_to_invoice", "<", 0) in model.search_calls[-1]["domain"]
    parameters.update(after=None, is_downpayment=False, negative_to_invoice_only=False)
    assert runtime.dispatch(env, _payload(f"{kind}.order.line.search", parameters), 7, failure_type=Failure)["items"][0]["id"] == positive.id
    assert not any(term[0] == "qty_to_invoice" for term in model.search_calls[-1]["domain"])


@pytest.mark.parametrize("kind", ["sale", "purchase"])
@pytest.mark.parametrize("operation", ["get", "search", "line.get"])
def test_native_line_flags_policy_and_sale_posted_values_are_read_without_recalculation(kind, operation):
    refs, order, line, models = fixture(kind)
    expose(models[f"{kind}.order.line"], line, is_downpayment=True)
    policy = "invoice_policy" if kind == "sale" else "purchase_method"
    expose(models["product.product"], refs["product"], **{policy: "delivery" if kind == "sale" else "receive"})
    if kind == "sale":
        line.qty_invoiced = 4
        expose(models["sale.order.line"], line, invoice_status="to invoice", qty_invoiced_posted=2,
               amount_invoiced=Decimal("20.25"), amount_to_invoice=0)
    models["account.move.line"]._fields["move_id"] = object()
    if operation == "get":
        capability, parameters = f"{kind}.order.get", {"order_id": order.id}
    elif operation == "line.get":
        capability, parameters = f"{kind}.order.line.get", {"line_id": line.id}
    else:
        capability, parameters = f"{kind}.order.line.search", _line_parameters(kind)
    item = runtime.dispatch(Env(models=models), _payload(capability, parameters), 7, failure_type=Failure)["items"][0]
    item = item["lines"][0] if operation == "get" else item
    assert item["is_downpayment"] is True and item[policy] == ("delivery" if kind == "sale" else "receive")
    if kind == "sale":
        assert item["invoiced_quantity"] == "4" and item["posted_invoiced_quantity"] == "2"
        assert item["invoice_status"] == "to invoice" and item["amount_invoiced"] == "20.25" and item["amount_to_invoice"] == "0"


@pytest.mark.parametrize("kind", ["sale", "purchase"])
def test_missing_optional_fields_omit_keys_but_explicit_missing_filter_fails(kind):
    _refs_value, _order, _line, models = fixture(kind)
    env = Env(models=models)
    payload = _payload(f"{kind}.order.line.search", _line_parameters(kind))
    item = runtime.dispatch(env, payload, 7, failure_type=Failure)["items"][0]
    assert not {"is_downpayment", "invoice_policy", "purchase_method", "posted_invoiced_quantity", "amount_invoiced", "amount_to_invoice", "invoice_status"} & item.keys()
    payload["parameters"]["is_downpayment"] = False
    calls = len(models[f"{kind}.order.line"].search_calls)
    with pytest.raises(Failure) as caught:
        runtime.dispatch(env, payload, 7, failure_type=Failure)
    assert caught.value.code == "odoo_runtime_error" and len(models[f"{kind}.order.line"].search_calls) == calls
    with pytest.raises(Failure):
        runtime.dispatch(env, _payload(f"{kind}.order.search", _search_parameters(payment_term_id=51)), 7, failure_type=Failure)


@pytest.mark.parametrize("kind", ["sale", "purchase"])
def test_policy_native_field_with_no_product_is_null(kind):
    _refs_value, _order, line, models = fixture(kind)
    field = "invoice_policy" if kind == "sale" else "purchase_method"
    models["product.product"]._fields[field] = object()
    line.product_id = False
    assert runtime.dispatch(Env(models=models), _payload(f"{kind}.order.line.search", _line_parameters(kind)), 7, failure_type=Failure)["items"][0][field] is None


@pytest.mark.parametrize("kind", ["sale", "purchase"])
def test_line_get_uses_visible_invoice_lines_and_moves_only_without_order_header_acl(kind):
    refs, _order, line, models = fixture(kind)
    other = _record(8, name="Other company")
    moves = [_record(record_id, company_id=refs["company"], name=f"INV/{record_id}", move_type="out_invoice" if kind == "sale" else "in_invoice",
                     state="posted", payment_state="not_paid", amount_total=record_id, currency_id=refs["currency"])
             for record_id in (301, 302, 303)]
    invoice_lines = [_record(401, company_id=refs["company"], move_id=moves[0]),
                     _record(402, company_id=refs["company"], move_id=moves[0]),
                     _record(403, company_id=refs["company"], move_id=moves[1]),
                     _record(404, company_id=refs["company"], move_id=moves[2]),
                     _record(405, company_id=other, move_id=moves[2])]
    line.invoice_lines = Records(invoice_lines)
    models[f"{kind}.order.line"] = ScopedModel(fields=set(models[f"{kind}.order.line"]._fields), records=[line])
    models["account.move.line"] = ScopedModel(fields={"company_id", "move_id"}, records=[invoice_lines[index] for index in (0, 1, 3, 4)])
    models["account.move"] = ScopedModel(fields=set(runtime._INVOICE_FIELDS), records=[moves[0], moves[1]])
    models[f"{kind}.order"]._fields.pop("picking_ids")
    models["stock.picking"].access = False
    env = Env(models=models)
    capability = f"{kind}.order.line.get"
    item = runtime.dispatch(env, _payload(capability, {"line_id": line.id}), 7, failure_type=Failure)["items"][0]
    assert item["invoice_line_ids"] == [401, 402, 404]
    assert [invoice["id"] for invoice in item["invoices"]] == [301]
    assert set(runtime._required_models(capability)) == set(runtime._required_models(f"{kind}.order.line.search")) | {"account.move"}
    assert not models["stock.picking"].access_calls
    for name in (f"{kind}.order.line", "account.move.line", "account.move"):
        assert all(("company_id", "=", 7) in call["domain"] for call in models[name].search_calls)
    assert runtime.dispatch(env, _payload(capability, {"line_id": line.id + 1}), 7, failure_type=Failure)["items"] == []


@pytest.mark.parametrize("model", ["sale.order.line", "account.move.line", "account.move"])
def test_line_get_acl_denial_returns_closed_page_before_search(model):
    _refs_value, _order, line, models = fixture("sale")
    models["account.move.line"]._fields["move_id"] = object()
    models[model].access = False
    page = runtime.dispatch(Env(models=models), _payload("sale.order.line.get", {"line_id": line.id}), 7, failure_type=Failure)
    assert not page["access_allowed"] and page["items"] == []
    assert not any(model.search_calls for model in models.values())


@pytest.mark.parametrize("parameters", [
    {"line_id": True}, {"line_id": None}, {"order_id": 11}, {"line_id": 101, "order_id": 11},
])
def test_line_get_has_exact_positive_id_contract(parameters):
    with pytest.raises(Failure) as caught:
        runtime.dispatch(Env(), _payload("sale.order.line.get", parameters), 7, failure_type=Failure)
    assert caught.value.code == "bridge_protocol_error"


@pytest.mark.parametrize("extension", [
    {"is_downpayment": None}, {"is_downpayment": 1}, {"negative_to_invoice_only": None},
    {"negative_to_invoice_only": 1}, {"negative_to_invoice_only": True, "to_invoice_only": True},
    {"to_refund_only": True},
])
def test_line_extension_filters_are_closed_strict_bools(extension):
    with pytest.raises(Failure) as caught:
        runtime.dispatch(Env(), _payload("sale.order.line.search", _line_parameters("sale", **extension)), 7, failure_type=Failure)
    assert caught.value.code == "bridge_protocol_error"


@pytest.mark.parametrize("model,field,value", [
    ("sale.order.line", "is_downpayment", "false"),
    ("product.product", "invoice_policy", "unknown"),
    ("product.product", "invoice_policy", 0),
    ("sale.order.line", "invoice_status", 0),
    ("sale.order.line", "invoice_status", "unknown"),
    ("sale.order.line", "qty_invoiced_posted", float("nan")),
    ("sale.order.line", "amount_to_invoice", False),
])
def test_new_native_field_drift_fails_closed(model, field, value):
    refs, _order, line, models = fixture("sale")
    record = refs["product"] if model == "product.product" else line
    expose(models[model], record, **{field: value})
    with pytest.raises(Failure) as caught:
        runtime.dispatch(Env(models=models), _payload("sale.order.line.search", _line_parameters("sale")), 7, failure_type=Failure)
    assert caught.value.code == "odoo_runtime_error"


def test_native_negative_posted_values_and_nullable_amounts_are_not_reinterpreted():
    _refs_value, order, line, models = fixture("sale")
    expose(models["sale.order"], order, amount_invoiced=None, amount_to_invoice=Decimal(-4))
    expose(models["sale.order.line"], line, qty_invoiced_posted=Decimal(-2), amount_invoiced=Decimal("-20.25"), amount_to_invoice=None)
    item = runtime.dispatch(Env(models=models), _payload("sale.order.get", {"order_id": order.id}), 7, failure_type=Failure)["items"][0]
    assert item["amount_invoiced"] is None and item["amount_to_invoice"] == "-4"
    assert item["lines"][0]["posted_invoiced_quantity"] == "-2"
    assert item["lines"][0]["amount_invoiced"] == "-20.25" and item["lines"][0]["amount_to_invoice"] is None


@pytest.mark.parametrize("kind", ["sale", "purchase"])
def test_line_get_cross_company_id_cannot_be_read(kind):
    _refs_value, _order, line, models = fixture(kind)
    line.company_id = _record(8)
    models[f"{kind}.order.line"] = ScopedModel(fields=set(models[f"{kind}.order.line"]._fields), records=[line])
    models["account.move.line"]._fields["move_id"] = object()
    page = runtime.dispatch(Env(models=models), _payload(f"{kind}.order.line.get", {"line_id": line.id}), 7, failure_type=Failure)
    assert page["items"] == []
