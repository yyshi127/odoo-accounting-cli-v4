from __future__ import annotations

from copy import deepcopy
from datetime import UTC, date, datetime
from types import SimpleNamespace

import pytest

from odoo_accounting_cli_v4.bridge import order_documents_runtime as runtime


class Failure(RuntimeError):
    def __init__(self, code: str, message: str, *, exit_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


class Records(list):
    @property
    def ids(self) -> list[int]:
        return [record.id for record in self]


def _record(record_id: int, **values):
    return SimpleNamespace(id=record_id, **values)


class Registry:
    def __init__(self, missing: str | None = None) -> None:
        self.missing = missing

    def get(self, model: str):
        return None if model == self.missing else object()


class User:
    def __init__(self, allowed: bool = True) -> None:
        self.allowed = allowed
        self.groups: list[str] = []

    def has_group(self, group: str) -> bool:
        self.groups.append(group)
        assert group == "account.group_account_readonly"
        return self.allowed


class Model:
    def __init__(
        self,
        *,
        fields: set[str] = frozenset(),
        access: bool = True,
        records: list | None = None,
        count: int = 1,
        groups: list[tuple] | None = None,
        cursor_exists: bool = True,
    ) -> None:
        self._fields = {field: object() for field in fields}
        self.access = access
        self.records = Records(records or [])
        self.count = count
        self.groups = list(groups or [])
        self.cursor_exists = cursor_exists
        self.company_calls: list[int] = []
        self.context_calls: list[dict] = []
        self.access_calls: list[str] = []
        self.search_calls: list[dict] = []
        self.search_count_calls: list[tuple[list, int | None]] = []
        self.read_group_calls: list[dict] = []

    def with_company(self, company_id: int):
        self.company_calls.append(company_id)
        return self

    def with_context(self, **context):
        self.context_calls.append(context)
        return self

    def has_access(self, operation: str) -> bool:
        self.access_calls.append(operation)
        assert operation == "read"
        return self.access

    def search_count(self, domain: list, limit: int | None = None) -> int:
        self.search_count_calls.append((deepcopy(domain), limit))
        if any(term == ("id", "=", 10) for term in domain):
            return int(self.cursor_exists)
        return self.count

    def search(
        self,
        domain: list,
        order: str | None = None,
        limit: int | None = None,
    ) -> Records:
        self.search_calls.append(
            {"domain": deepcopy(domain), "order": order, "limit": limit}
        )
        values = self.records
        if limit is not None:
            values = Records(values[:limit])
        return Records(values)

    def _read_group(
        self, domain: list, *, groupby: list[str], aggregates: list[str]
    ) -> list[tuple]:
        self.read_group_calls.append(
            {
                "domain": deepcopy(domain),
                "groupby": groupby,
                "aggregates": aggregates,
            }
        )
        return list(self.groups)


def _refs(company_id: int = 7) -> dict[str, object]:
    company = _record(company_id, name="China Company", display_name="China Company")
    currency = _record(6, name="CNY", display_name="CNY")
    partner = _record(
        31,
        display_name="Partner",
        company_id=company,
    )
    product = _record(
        41,
        display_name="Product",
        company_id=company,
    )
    uom = _record(1, display_name="Units")
    return {
        "company": company,
        "currency": currency,
        "partner": partner,
        "product": product,
        "uom": uom,
    }


def _sale_order(order_id: int = 11, refs: dict | None = None):
    refs = refs or _refs()
    return _record(
        order_id,
        company_id=refs["company"],
        name=f"S{order_id:05d}",
        partner_id=refs["partner"],
        state="draft",
        date_order=datetime(2026, 8, 28, 1, 2, 3, tzinfo=UTC),
        currency_id=refs["currency"],
        user_id=False,
        invoice_status="to invoice",
        amount_untaxed=30,
        amount_tax=0,
        amount_total=30,
        invoice_ids=Records(),
        picking_ids=Records(),
        order_line=Records(),
        validity_date=date(2026, 9, 27),
        client_order_ref="CLIENT-1",
        team_id=False,
        delivery_status="pending",
    )


def _purchase_order(order_id: int = 20, refs: dict | None = None):
    refs = refs or _refs()
    return _record(
        order_id,
        company_id=refs["company"],
        name=f"P{order_id:05d}",
        partner_id=refs["partner"],
        state="draft",
        date_order=datetime(2026, 8, 28, 1, 2, 3, tzinfo=UTC),
        currency_id=refs["currency"],
        user_id=False,
        invoice_status="to invoice",
        amount_untaxed=40,
        amount_tax=0,
        amount_total=40,
        invoice_ids=Records(),
        picking_ids=Records(),
        order_line=Records(),
        date_approve=False,
        partner_ref="VENDOR-1",
        origin=False,
        receipt_status="pending",
    )


def _sale_line(order=None, refs: dict | None = None):
    refs = refs or _refs()
    order = order or _sale_order(refs=refs)
    return _record(
        101,
        order_id=order,
        company_id=refs["company"],
        state="draft",
        sequence=10,
        display_type=False,
        name="Product",
        product_id=refs["product"],
        product_uom_id=refs["uom"],
        product_uom_qty=3,
        qty_delivered=0,
        qty_invoiced=0,
        qty_to_invoice=3,
        price_unit=10,
        discount=0,
        price_subtotal=30,
        price_tax=0,
        price_total=30,
        currency_id=refs["currency"],
        tax_ids=Records(),
        invoice_lines=Records(),
        move_ids=Records(),
    )


def _purchase_line(order=None, refs: dict | None = None):
    refs = refs or _refs()
    order = order or _purchase_order(refs=refs)
    return _record(
        201,
        order_id=order,
        company_id=refs["company"],
        state="draft",
        sequence=10,
        display_type=False,
        name="Product",
        product_id=refs["product"],
        product_uom_id=refs["uom"],
        product_qty=5,
        qty_received=2,
        qty_invoiced=0,
        qty_to_invoice=5,
        price_unit=8,
        discount=0,
        price_subtotal=40,
        price_tax=0,
        price_total=40,
        currency_id=refs["currency"],
        tax_ids=Records(),
        invoice_lines=Records(),
        move_ids=Records(),
        date_planned=datetime(2026, 8, 29, 1, 2, 3, tzinfo=UTC),
    )


def _models(
    *,
    sale_orders: list | None = None,
    purchase_orders: list | None = None,
    sale_lines: list | None = None,
    purchase_lines: list | None = None,
    groups: list[tuple] | None = None,
) -> dict[str, Model]:
    return {
        "res.company": Model(fields={"name"}, count=1),
        "res.partner": Model(),
        "res.users": Model(),
        "res.currency": Model(fields={"name"}),
        "crm.team": Model(),
        "sale.order": Model(
            fields=set(runtime._SALE_ORDER_FIELDS),
            records=sale_orders,
            groups=groups,
        ),
        "purchase.order": Model(
            fields=set(runtime._PURCHASE_ORDER_FIELDS),
            records=purchase_orders,
            groups=groups,
        ),
        "sale.order.line": Model(
            fields=set(runtime._SALE_LINE_FIELDS), records=sale_lines, count=1
        ),
        "purchase.order.line": Model(
            fields=set(runtime._PURCHASE_LINE_FIELDS),
            records=purchase_lines,
            count=1,
        ),
        "product.product": Model(),
        "uom.uom": Model(),
        "account.tax": Model(),
        "account.move": Model(fields=set(runtime._INVOICE_FIELDS)),
        "account.move.line": Model(fields={"company_id"}),
        "stock.picking": Model(fields=set(runtime._TRANSFER_FIELDS)),
        "stock.move": Model(fields={"company_id"}),
        "stock.location": Model(fields={"company_id", "complete_name"}),
    }


class Env:
    def __init__(
        self,
        *,
        models: dict[str, Model] | None = None,
        group_allowed: bool = True,
        missing_model: str | None = None,
    ) -> None:
        self.uid = 5
        self.user = User(group_allowed)
        self.registry = Registry(missing_model)
        self.models = models or _models()

    def __getitem__(self, name: str) -> Model:
        return self.models[name]


def _payload(capability_id: str, parameters: dict) -> dict:
    return {
        "capability_id": capability_id,
        "company_id": 7,
        "parameters": parameters,
    }


def _search_parameters(**overrides) -> dict:
    values = {
        "query": None,
        "date_from": None,
        "date_to": None,
        "states": None,
        "partner_id": None,
        "currency_id": None,
        "invoice_statuses": None,
        "after": None,
        "limit": 101,
    }
    values.update(overrides)
    return values


def _line_parameters(kind: str, **overrides) -> dict:
    pending = "to_deliver_only" if kind == "sale" else "to_receive_only"
    values = {
        "order_id": None,
        "date_from": None,
        "date_to": None,
        "partner_id": None,
        "product_id": None,
        "states": None,
        pending: False,
        "to_invoice_only": False,
        "after": None,
        "limit": 101,
    }
    values.update(overrides)
    return values


def _summary_parameters(**overrides) -> dict:
    values = {
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "group_by": "partner",
        "states": None,
        "partner_id": None,
        "currency_id": None,
    }
    values.update(overrides)
    return values


def test_sale_search_uses_company_acl_ascending_cursor_and_no_sudo() -> None:
    refs = _refs()
    order = _sale_order(refs=refs)
    models = _models(sale_orders=[order])
    env = Env(models=models)

    page = runtime.dispatch(
        env,
        _payload(
            "sale.order.search",
            _search_parameters(
                query="CLIENT",
                date_from="2026-08-01",
                states=["draft"],
                partner_id=31,
                currency_id=6,
                invoice_statuses=["to invoice"],
                after=10,
                limit=11,
            ),
        ),
        7,
        failure_type=Failure,
    )

    assert page["user_id"] == 5
    assert page["access_allowed"] is True
    assert page["cursor_found"] is True
    assert page["items"][0]["id"] == 11
    assert set(page["items"][0]) == {
        "id",
        "name",
        "company",
        "partner",
        "state",
        "date_order",
        "currency",
        "user",
        "invoice_status",
        "amount_untaxed",
        "amount_tax",
        "amount_total",
        "invoice_ids",
        "transfer_ids",
        "line_count",
        "validity_date",
        "client_order_ref",
        "team",
        "delivery_status",
    }
    call = models["sale.order"].search_calls[0]
    assert call["order"] == "id asc"
    assert call["limit"] == 11
    assert ("company_id", "=", 7) in call["domain"]
    assert ("date_order", ">=", "2026-08-01 00:00:00") in call["domain"]
    assert ("id", ">", 10) in call["domain"]
    assert ("partner_id", "=", 31) in call["domain"]
    assert ("currency_id", "=", 6) in call["domain"]
    assert env.user.groups == ["account.group_account_readonly"]
    assert models["sale.order"].company_calls == [7]
    assert all(call == "read" for call in models["sale.order"].access_calls)


def test_purchase_line_uses_odoo19_uom_and_ordered_minus_received() -> None:
    refs = _refs()
    order = _purchase_order(refs=refs)
    line = _purchase_line(order, refs)
    models = _models(purchase_orders=[order], purchase_lines=[line])

    page = runtime.dispatch(
        Env(models=models),
        _payload(
            "purchase.order.line.search",
            _line_parameters(
                "purchase",
                order_id=20,
                product_id=41,
                states=["draft"],
                to_receive_only=True,
            ),
        ),
        7,
        failure_type=Failure,
    )

    item = page["items"][0]
    assert item["uom"] == {"id": 1, "name": "Units"}
    assert item["ordered_quantity"] == "5"
    assert item["received_quantity"] == "2"
    assert item["to_receive_quantity"] == "3"
    assert "product_uom_id" in runtime._PURCHASE_LINE_FIELDS
    assert "product_uom" not in runtime._PURCHASE_LINE_FIELDS
    call = models["purchase.order.line"].search_calls[0]
    assert call["order"] == "id asc"
    assert ("order_id", "=", 20) in call["domain"]
    assert ("product_id", "=", 41) in call["domain"]


def test_get_filters_every_linked_graph_by_company() -> None:
    refs = _refs()
    order = _sale_order(refs=refs)
    line = _sale_line(order, refs)
    invoice = _record(
        301,
        company_id=refs["company"],
        name="INV/301",
        move_type="out_invoice",
        state="posted",
        payment_state="not_paid",
        amount_total=30,
        currency_id=refs["currency"],
    )
    source = _record(501, company_id=refs["company"], complete_name="WH/Stock")
    destination = _record(502, company_id=refs["company"], complete_name="Customers")
    transfer = _record(
        401,
        company_id=refs["company"],
        name="WH/OUT/401",
        state="draft",
        location_id=source,
        location_dest_id=destination,
    )
    order.invoice_ids = Records([invoice])
    order.picking_ids = Records([transfer])
    models = _models(sale_orders=[order], sale_lines=[line])
    models["account.move"].records = Records([invoice])
    models["stock.picking"].records = Records([transfer])

    result = runtime.dispatch(
        Env(models=models),
        _payload("sale.order.get", {"order_id": 11}),
        7,
        failure_type=Failure,
    )["items"][0]

    assert result["company"]["id"] == 7
    assert result["lines"][0]["company"]["id"] == 7
    assert result["invoice_ids"] == [301]
    assert result["transfer_ids"] == [401]
    assert result["invoices"][0]["id"] == 301
    assert result["transfers"][0]["id"] == 401
    for model_name in ("account.move", "stock.picking"):
        assert any(
            ("company_id", "=", 7) in call["domain"]
            for call in models[model_name].search_calls
        )


def test_summary_groups_and_totals_each_currency_without_merging() -> None:
    refs = _refs()
    usd = _record(2, name="USD", display_name="USD")
    groups = [
        (refs["partner"], refs["currency"], 1, 30, 3, 33),
        (refs["partner"], usd, 2, 20, 2, 22),
    ]
    models = _models(groups=groups)

    item = runtime.dispatch(
        Env(models=models),
        _payload("sale.order.analysis.summary", _summary_parameters()),
        7,
        failure_type=Failure,
    )["items"][0]

    assert item["company_id"] == 7
    assert len(item["groups"]) == 2
    assert {group["currency"]["id"] for group in item["groups"]} == {2, 6}
    assert item["totals_by_currency"] == [
        {
            "currency": {"id": 2, "code": "USD"},
            "order_count": 2,
            "amount_untaxed": "20",
            "amount_tax": "2",
            "amount_total": "22",
        },
        {
            "currency": {"id": 6, "code": "CNY"},
            "order_count": 1,
            "amount_untaxed": "30",
            "amount_tax": "3",
            "amount_total": "33",
        },
    ]
    call = models["sale.order"].read_group_calls[0]
    assert call["groupby"] == ["partner_id", "currency_id"]
    assert ("company_id", "=", 7) in call["domain"]


@pytest.mark.parametrize(
    "env",
    [
        Env(group_allowed=False),
        Env(missing_model="sale.order"),
        Env(
            models={
                **_models(),
                "sale.order": Model(
                    fields=set(runtime._SALE_ORDER_FIELDS), access=False
                ),
            }
        ),
    ],
)
def test_acl_module_and_group_failures_return_closed_empty_page(env: Env) -> None:
    page = runtime.dispatch(
        env,
        _payload("sale.order.search", _search_parameters()),
        7,
        failure_type=Failure,
    )
    assert page["items"] == []
    assert page["access_allowed"] is False


def test_payload_field_and_decimal_drift_fail_closed() -> None:
    payload = _payload("sale.order.search", _search_parameters())
    payload["extra"] = True
    with pytest.raises(Failure) as caught:
        runtime.dispatch(Env(), payload, 7, failure_type=Failure)
    assert caught.value.code == "bridge_protocol_error"

    models = _models()
    models["sale.order"] = Model(
        fields=set(runtime._SALE_ORDER_FIELDS) - {"picking_ids"}
    )
    with pytest.raises(Failure) as caught:
        runtime.dispatch(
            Env(models=models),
            _payload("sale.order.search", _search_parameters()),
            7,
            failure_type=Failure,
        )
    assert caught.value.code == "odoo_runtime_error"

    order = _sale_order()
    order.amount_total = float("nan")
    with pytest.raises(Failure) as caught:
        runtime.dispatch(
            Env(models=_models(sale_orders=[order])),
            _payload("sale.order.search", _search_parameters()),
            7,
            failure_type=Failure,
        )
    assert caught.value.code == "odoo_runtime_error"
