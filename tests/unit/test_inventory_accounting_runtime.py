from __future__ import annotations

from datetime import UTC, date, datetime
from types import SimpleNamespace
from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge import inventory_accounting_runtime as inventory


class Failure(RuntimeError):
    def __init__(self, code: str, message: str, *, exit_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


class Record(SimpleNamespace):
    pass


def _scalar(value: Any) -> Any:
    return value.id if isinstance(value, Record) else value


def _field(record: Record, path: str) -> Any:
    value: Any = record
    for name in path.split("."):
        if value in (None, False) or not hasattr(value, name):
            return None
        value = getattr(value, name)
    return _scalar(value)


def _matches(record: Record, domain: list[Any]) -> bool:
    for term in domain:
        if not isinstance(term, tuple):
            continue
        field, operator, expected = term
        actual = _field(record, field)
        expected = _scalar(expected)
        if operator == "=" and actual != expected:
            return False
        if operator == "!=" and actual == expected:
            return False
        if operator == "in" and actual not in expected:
            return False
        if operator == ">=" and actual < expected:
            return False
        if operator == "<=" and actual > expected:
            return False
        if operator == "<" and actual >= expected:
            return False
    return True


class Model:
    def __init__(
        self,
        name: str,
        rows: list[Record] | None = None,
        *,
        access: bool = True,
    ) -> None:
        self.name = name
        self.rows = rows or []
        self.access = access
        self.calls: list[tuple[Any, ...]] = []

    def with_context(self, **context: Any) -> Model:
        self.calls.append(("with_context", context))
        return self

    def has_access(self, operation: str) -> bool:
        self.calls.append(("has_access", operation))
        return self.access

    def search(
        self,
        domain: list[Any],
        *,
        order: str | None = None,
        limit: int | None = None,
    ) -> list[Record]:
        self.calls.append(("search", domain, order, limit))
        rows = [row for row in self.rows if _matches(row, domain)]
        if order:
            for part in reversed(order.split(",")):
                tokens = part.strip().split()
                field = tokens[0]
                reverse = len(tokens) == 2 and tokens[1] == "desc"
                rows.sort(key=lambda row: _field(row, field), reverse=reverse)
        return rows[:limit] if limit is not None else rows

    def search_count(self, domain: list[Any], *, limit: int | None = None) -> int:
        self.calls.append(("search_count", domain, limit))
        count = sum(_matches(row, domain) for row in self.rows)
        return min(count, limit) if limit is not None else count


class ReportModel(Model):
    def __init__(self, values: dict[str, Any]) -> None:
        super().__init__("stock_account.stock.valuation.report")
        self.values = values

    def with_company(self, company: Record) -> ReportModel:
        self.calls.append(("with_company", company.id))
        return self

    def get_report_values(self, report_date: str | bool) -> dict[str, Any]:
        self.calls.append(("get_report_values", report_date))
        return self.values


class Registry:
    def __init__(self, models: dict[str, Model]) -> None:
        self.models = models

    def get(self, name: str) -> Model | None:
        return self.models.get(name)


class User:
    def has_group(self, group: str) -> bool:
        return group == "account.group_account_readonly"


class Env:
    uid = 5
    user = User()

    def __init__(self, models: dict[str, Model]) -> None:
        self.models = models
        self.registry = Registry(models)

    def __getitem__(self, name: str) -> Model:
        return self.models[name]


def _record(record_id: int, **values: Any) -> Record:
    return Record(id=record_id, **values)


def _fixture() -> tuple[Env, dict[str, Record]]:
    currency = _record(6, name="CNY")
    company = _record(7, name="Demo Company", currency_id=currency)
    product = _record(41, name="Gadget")
    uom = _record(5, name="Units")
    account = _record(31, code="1405", name="Inventory")
    journal = _record(11, code="STJ", name="Stock Journal")
    internal_location = _record(201, usage="internal")
    customer_location = _record(202, usage="customer")
    debit_line = _record(
        101,
        company_id=company,
        account_id=account,
        debit=10,
        credit=0,
    )
    credit_line = _record(
        102,
        company_id=company,
        account_id=account,
        debit=0,
        credit=10,
    )
    stock_entry = _record(
        91,
        company_id=company,
        name="STJ/2025/0001",
        date=date(2025, 1, 4),
        state="posted",
        journal_id=journal,
        line_ids=[debit_line, credit_line],
    )
    stock_move = _record(
        81,
        company_id=company,
        date=datetime(2025, 1, 4, 8, 30, tzinfo=UTC),
        state="done",
        reference="WH/OUT/0001",
        product_id=product,
        quantity=2,
        product_uom=uom,
        value=10,
        is_in=False,
        is_out=True,
        account_move_id=stock_entry,
        company_currency_id=currency,
        location_id=internal_location,
        location_dest_id=customer_location,
    )
    return_move = _record(
        82,
        company_id=company,
        date=datetime(2025, 1, 6, 8, 30, tzinfo=UTC),
        state="done",
        reference="WH/RET/0001",
        product_id=product,
        quantity=2,
        product_uom=uom,
        value=-10,
        is_in=True,
        is_out=False,
        account_move_id=stock_entry,
        company_currency_id=currency,
        location_id=customer_location,
        location_dest_id=internal_location,
    )
    internal_move = _record(
        83,
        company_id=company,
        state="done",
        location_id=internal_location,
        location_dest_id=internal_location,
    )
    sale_line = _record(
        61,
        company_id=company,
        move_ids=[stock_move, return_move, internal_move],
        is_downpayment=False,
    )
    cogs_origin = _record(51, company_id=company, sale_line_ids=[sale_line])
    cogs_invoice = _record(
        71,
        company_id=company,
        name="INV/2025/0001",
        move_type="out_invoice",
        state="posted",
        invoice_line_ids=[cogs_origin],
    )
    cogs_line = _record(
        111,
        company_id=company,
        date=date(2025, 1, 5),
        display_type="cogs",
        parent_state="posted",
        move_id=cogs_invoice,
        cogs_origin_id=cogs_origin,
        account_id=account,
        product_id=product,
        name="Gadget COGS",
        quantity=2,
        debit=10,
        credit=0,
        company_currency_id=currency,
    )

    purchase_invoice_line = _record(
        52,
        company_id=company,
        display_type="product",
        product_id=product,
        name="Unmatched gadget",
        quantity=3,
        price_subtotal=15,
        purchase_line_id=False,
    )
    partner = _record(21, name="Vendor")
    bill = _record(
        72,
        company_id=company,
        name="BILL/2025/0001",
        move_type="in_invoice",
        state="draft",
        partner_id=partner,
        currency_id=currency,
        invoice_line_ids=[purchase_invoice_line],
    )
    match_row = _record(-52, company_id=company, aml_id=purchase_invoice_line)

    sale_invoice_line = _record(
        53,
        company_id=company,
        display_type="product",
        product_id=product,
        quantity=-2,
        sale_line_ids=[sale_line],
    )
    original_invoice_line = _record(
        54,
        company_id=company,
        display_type="product",
        product_id=product,
        sale_line_ids=[sale_line],
    )
    original_invoice = _record(74, invoice_line_ids=[original_invoice_line])
    refund = _record(
        73,
        company_id=company,
        name="RINV/2025/0001",
        move_type="out_refund",
        state="posted",
        invoice_line_ids=[sale_invoice_line],
        reversed_entry_id=original_invoice,
    )

    report_values = {
        "data": {
            "company_id": 7,
            "currency_id": 6,
            "initial_balance": {"value": 0, "lines_by_account_id": {}},
            "ending_stock": {"value": 0, "lines_by_account_id": {}},
            "stock_variation": {"value": 0, "lines": []},
            "accounts_by_id": {},
        },
        "context": {},
    }
    models: dict[str, Model] = {
        "res.company": Model("res.company", [company]),
        "account.move": Model(
            "account.move", [stock_entry, cogs_invoice, bill, refund, original_invoice]
        ),
        "account.move.line": Model("account.move.line", [cogs_line]),
        "stock.move": Model("stock.move", [stock_move]),
        "sale.order.line": Model("sale.order.line", [sale_line]),
        "purchase.order.line": Model("purchase.order.line"),
        "purchase.bill.line.match": Model("purchase.bill.line.match", [match_row]),
        "stock_account.stock.valuation.report": ReportModel(report_values),
    }
    return Env(models), {
        "company": company,
        "cogs_line": cogs_line,
        "stock_move": stock_move,
        "return_move": return_move,
        "sale_line": sale_line,
        "sale_invoice_line": sale_invoice_line,
        "original_invoice": original_invoice,
        "bill": bill,
        "refund": refund,
    }


def _dispatch(
    env: Env, capability_id: str, parameters: dict[str, Any]
) -> dict[str, Any]:
    return inventory.dispatch(
        env,
        {
            "capability_id": capability_id,
            "company_id": 7,
            "parameters": parameters,
        },
        7,
        failure_type=Failure,
    )


def _list_parameters(**overrides: Any) -> dict[str, Any]:
    value = {
        "date_from": None,
        "date_to": None,
        "product_id": None,
        "after": None,
        "limit": 101,
    }
    value.update(overrides)
    return value


def test_cogs_uses_only_posted_sale_documents_and_direct_stock_relations() -> None:
    env, _ = _fixture()
    parameters = _list_parameters(invoice_id=None)

    page = _dispatch(env, "cogs.entries.list", parameters)

    assert page["cursor_found"] is True
    assert page["items"] == [
        {
            "id": 111,
            "date": "2025-01-05",
            "company_id": 7,
            "invoice": {
                "id": 71,
                "name": "INV/2025/0001",
                "move_type": "out_invoice",
                "state": "posted",
            },
            "origin_invoice_line_id": 51,
            "account": {"id": 31, "code": "1405", "name": "Inventory"},
            "product": {"id": 41, "name": "Gadget"},
            "label": "Gadget COGS",
            "quantity": "2",
            "debit": "10",
            "credit": "0",
            "balance": "10",
            "company_currency": {"id": 6, "code": "CNY"},
            "sale_order_line_ids": [61],
            "stock_move_ids": [81],
        }
    ]
    search_domain = next(
        call[1] for call in env.models["account.move.line"].calls if call[0] == "search"
    )
    assert ("display_type", "=", "cogs") in search_domain
    assert ("move_id.move_type", "in", ("out_invoice", "out_refund")) in search_domain


def test_cogs_rejects_cross_company_sale_order_line() -> None:
    env, records = _fixture()
    records["sale_line"].company_id = _record(8, name="Other Company")

    with pytest.raises(Failure) as caught:
        _dispatch(
            env,
            "cogs.entries.list",
            _list_parameters(invoice_id=None),
        )

    assert caught.value.code == "odoo_runtime_error"


def test_cogs_rejects_cross_company_origin_line() -> None:
    env, records = _fixture()
    records["cogs_line"].cogs_origin_id.company_id = _record(8)

    with pytest.raises(Failure) as caught:
        _dispatch(env, "cogs.entries.list", _list_parameters(invoice_id=None))

    assert caught.value.code == "odoo_runtime_error"


def test_inventory_entries_use_stored_account_move_link_not_is_valued() -> None:
    env, _ = _fixture()

    page = _dispatch(env, "inventory.accounting_entries.list", _list_parameters())

    item = page["items"][0]
    assert item["date"] == "2025-01-04T08:30:00Z"
    assert item["account_move"]["journal"] == {
        "id": 11,
        "code": "STJ",
        "name": "Stock Journal",
    }
    assert item["lines"] == [
        {
            "id": 101,
            "account": {"id": 31, "code": "1405", "name": "Inventory"},
            "debit": "10",
            "credit": "0",
            "balance": "10",
        },
        {
            "id": 102,
            "account": {"id": 31, "code": "1405", "name": "Inventory"},
            "debit": "0",
            "credit": "10",
            "balance": "-10",
        },
    ]
    search_domain = next(
        call[1] for call in env.models["stock.move"].calls if call[0] == "search"
    )
    assert ("account_move_id", "!=", False) in search_domain
    assert all(
        term[0] != "is_valued" for term in search_domain if isinstance(term, tuple)
    )


def test_list_cursor_must_resolve_inside_same_filtered_company_scope() -> None:
    env, _ = _fixture()

    page = _dispatch(
        env,
        "cogs.entries.list",
        _list_parameters(invoice_id=None, after=["2025-01-05", 999]),
    )

    assert page["cursor_found"] is False
    assert page["items"] == []
    boundary_domain = next(
        call[1]
        for call in env.models["account.move.line"].calls
        if call[0] == "search_count"
    )
    assert ("company_id", "=", 7) in boundary_domain
    assert ("display_type", "=", "cogs") in boundary_domain


def test_valuation_uses_official_date_only_entry_and_null_extension_totals() -> None:
    env, _ = _fixture()

    page = _dispatch(env, "report.inventory_valuation", {"date": "2025-01-31"})

    assert page["items"] == [
        {
            "as_of_date": "2025-01-31",
            "company": {"id": 7, "name": "Demo Company"},
            "currency": {"id": 6, "code": "CNY"},
            "initial_balance": "0",
            "ending_stock": "0",
            "stock_variation": "0",
            "inventory_loss": None,
            "not_invoiced_delivered_goods": None,
            "not_invoiced_received_goods": None,
            "cost_of_production": None,
            "accounts": [],
        }
    ]
    report_calls = env.models["stock_account.stock.valuation.report"].calls
    assert ("with_company", 7) in report_calls
    assert ("get_report_values", "2025-01-31") in report_calls
    assert inventory.requires_rollback_only(
        {"capability_id": "report.inventory_valuation"}
    )


def test_purchase_matching_scopes_unruled_view_and_never_exposes_negative_id() -> None:
    env, _ = _fixture()

    page = _dispatch(env, "purchase_bill.matching.inspect", {"bill_id": 72})

    item = page["items"][0]
    assert item["id"] == 72
    assert item["is_purchase_matched"] is False
    assert item["lines"][0]["id"] == 52
    assert item["lines"][0]["purchase_line"] is None
    assert item["lines"][0]["unmatched_queue"] is True
    assert "-52" not in repr(item)
    view_domain = next(
        call[1]
        for call in env.models["purchase.bill.line.match"].calls
        if call[0] == "search"
    )
    assert ("company_id", "=", 7) in view_domain
    assert ("aml_id", "in", [52]) in view_domain


def test_cancelled_purchase_bill_reports_actual_empty_unmatched_queue() -> None:
    env, records = _fixture()
    records["bill"].state = "cancel"
    env.models["purchase.bill.line.match"].rows = []

    page = _dispatch(env, "purchase_bill.matching.inspect", {"bill_id": 72})

    item = page["items"][0]
    assert item["is_purchase_matched"] is False
    assert item["lines"][0]["purchase_line"] is None
    assert item["lines"][0]["unmatched_queue"] is False


def test_sale_refund_prefers_current_line_and_filters_to_customer_return_moves() -> (
    None
):
    env, records = _fixture()
    other_sale_line = _record(
        62,
        company_id=records["company"],
        move_ids=[],
        is_downpayment=False,
    )
    records["original_invoice"].invoice_line_ids[0].sale_line_ids = [other_sale_line]

    page = _dispatch(env, "sale_invoice.stock_link.inspect", {"invoice_id": 73})

    item = page["items"][0]
    assert item["move_type"] == "out_refund"
    assert item["lines"][0]["sale_order_line_ids"] == [61]
    assert item["lines"][0]["stock_moves"][0]["id"] == 82
    assert item["stock_move_ids"] == [82]
    assert item["account_move_ids"] == [91]


def test_sale_refund_falls_back_only_for_one_same_product_source_line() -> None:
    env, records = _fixture()
    records["sale_invoice_line"].sale_line_ids = []

    page = _dispatch(env, "sale_invoice.stock_link.inspect", {"invoice_id": 73})

    assert page["items"][0]["lines"][0]["sale_order_line_ids"] == [61]
    assert page["items"][0]["stock_move_ids"] == [82]


def test_sale_refund_does_not_merge_multiple_same_product_source_lines() -> None:
    env, records = _fixture()
    records["sale_invoice_line"].sale_line_ids = []
    first_source = records["original_invoice"].invoice_line_ids[0]
    second_source = _record(
        55,
        company_id=records["company"],
        display_type="product",
        product_id=first_source.product_id,
        sale_line_ids=[records["sale_line"]],
    )
    records["original_invoice"].invoice_line_ids.append(second_source)

    page = _dispatch(env, "sale_invoice.stock_link.inspect", {"invoice_id": 73})

    line = page["items"][0]["lines"][0]
    assert line["sale_order_line_ids"] == []
    assert line["stock_moves"] == []
    assert page["items"][0]["stock_move_ids"] == []


def test_refund_downpayment_uses_customer_destination_direction() -> None:
    env, records = _fixture()
    records["sale_line"].is_downpayment = True

    page = _dispatch(env, "sale_invoice.stock_link.inspect", {"invoice_id": 73})

    assert page["items"][0]["stock_move_ids"] == [81]


def test_refund_downpayment_direction_applies_to_every_invoice_line() -> None:
    env, records = _fixture()
    downpayment_sale_line = _record(
        62,
        company_id=records["company"],
        move_ids=[],
        is_downpayment=True,
    )
    downpayment_invoice_line = _record(
        55,
        company_id=records["company"],
        display_type="product",
        product_id=records["sale_invoice_line"].product_id,
        quantity=0,
        sale_line_ids=[downpayment_sale_line],
    )
    records["refund"].invoice_line_ids.append(downpayment_invoice_line)

    page = _dispatch(env, "sale_invoice.stock_link.inspect", {"invoice_id": 73})

    assert page["items"][0]["lines"][0]["stock_moves"][0]["id"] == 81
    assert page["items"][0]["stock_move_ids"] == [81]


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    [
        ("cogs.entries.list", _list_parameters(invoice_id=None, extra=True)),
        (
            "inventory.accounting_entries.list",
            _list_parameters(after=["2025-01-04 08:30:00", 81]),
        ),
        ("report.inventory_valuation", {"date": "2025-1-31"}),
        ("purchase_bill.matching.inspect", {"bill_id": True}),
    ],
)
def test_runtime_rejects_noncanonical_or_expanded_payloads(
    capability_id: str, parameters: dict[str, Any]
) -> None:
    env, _ = _fixture()

    with pytest.raises(Failure) as caught:
        _dispatch(env, capability_id, parameters)

    assert caught.value.code == "bridge_protocol_error"
    assert caught.value.exit_code == 7


def test_scope_gate_returns_no_items_when_required_acl_is_denied() -> None:
    env, _ = _fixture()
    env.models["sale.order.line"].access = False

    page = _dispatch(env, "sale_invoice.stock_link.inspect", {"invoice_id": 73})

    assert page == {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": False,
        "cursor_found": True,
        "items": [],
    }
