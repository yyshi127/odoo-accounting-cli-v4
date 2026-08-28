from __future__ import annotations

from copy import deepcopy

import pytest

from odoo_accounting_cli_v4.bridge.invoice_analysis_runtime import dispatch


class Failure(RuntimeError):
    def __init__(self, code: str, message: str, *, exit_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


class Ref:
    def __init__(self, record_id: int, name: str) -> None:
        self.id = record_id
        self.display_name = name


class EmptyRef:
    id = False
    display_name = False

    def __bool__(self) -> bool:
        return False


class Company:
    def __init__(self) -> None:
        self.id = 7
        self.currency_id = Ref(6, "CNY")


class Registry:
    def __init__(self, missing: str | None = None) -> None:
        self.missing = missing

    def get(self, model: str):
        return None if model == self.missing else object()


class User:
    def __init__(self, allowed: bool = True) -> None:
        self.allowed = allowed

    def has_group(self, name: str) -> bool:
        assert name == "account.group_account_readonly"
        return self.allowed


class Model:
    def __init__(
        self,
        *,
        fields: set[str] = frozenset(),
        access: bool = True,
        count: int = 0,
        rows: list[dict] | None = None,
        groups: list[tuple] | None = None,
        records: list | None = None,
        cursor_exists: bool = True,
    ) -> None:
        self._fields = {field: object() for field in fields}
        self.access = access
        self.count = count
        self.rows = deepcopy(rows or [])
        self.groups = list(groups or [])
        self.records = list(records or [])
        self.cursor_exists = cursor_exists
        self.contexts: list[dict] = []
        self.search_count_calls: list[tuple[list, int | None]] = []
        self.search_read_calls: list[dict] = []
        self.read_group_calls: list[dict] = []
        self.search_calls: list[tuple[list, int | None]] = []

    def with_context(self, **context):
        self.contexts.append(context)
        return self

    def has_access(self, operation: str) -> bool:
        assert operation == "read"
        return self.access

    def search_count(self, domain: list, limit: int | None = None) -> int:
        self.search_count_calls.append((deepcopy(domain), limit))
        if any(term == ("id", "=", 30) for term in domain):
            return int(self.cursor_exists)
        return self.count

    def search_read(
        self, domain: list, fields: list[str], *, order: str, limit: int
    ) -> list[dict]:
        self.search_read_calls.append(
            {
                "domain": deepcopy(domain),
                "fields": fields,
                "order": order,
                "limit": limit,
            }
        )
        return deepcopy(self.rows[:limit])

    def _read_group(
        self,
        domain: list,
        *,
        groupby: list[str],
        aggregates: list[str],
        order: str,
    ) -> list[tuple]:
        self.read_group_calls.append(
            {
                "domain": deepcopy(domain),
                "groupby": groupby,
                "aggregates": aggregates,
                "order": order,
            }
        )
        return list(self.groups)

    def search(self, domain: list, limit: int | None = None) -> list:
        self.search_calls.append((deepcopy(domain), limit))
        return list(self.records)


REPORT_FIELDS = {
    "move_id",
    "journal_id",
    "company_id",
    "company_currency_id",
    "partner_id",
    "move_type",
    "state",
    "payment_state",
    "invoice_date",
    "invoice_date_due",
    "quantity",
    "product_id",
    "product_uom_id",
    "price_subtotal_currency",
    "price_subtotal",
    "price_total",
    "price_total_currency",
    "price_average",
    "price_margin",
    "inventory_value",
    "currency_id",
}


class Env:
    def __init__(
        self,
        *,
        report: Model | None = None,
        company_visible: bool = True,
        group_allowed: bool = True,
        missing_model: str | None = None,
    ) -> None:
        self.uid = 5
        self.user = User(group_allowed)
        self.registry = Registry(missing_model)
        self.models = {
            "account.invoice.report": report or Model(fields=REPORT_FIELDS),
            "res.company": Model(
                fields={"currency_id"},
                count=int(company_visible),
                records=[Company()] if company_visible else [],
            ),
            "res.currency": Model(fields={"name"}),
            "res.partner": Model(),
            "product.product": Model(),
            "account.journal": Model(),
            "uom.uom": Model(),
        }

    def __getitem__(self, name: str) -> Model:
        return self.models[name]


def _search_parameters(**overrides) -> dict:
    value = {
        "date_from": None,
        "date_to": None,
        "move_types": None,
        "states": None,
        "payment_states": None,
        "partner_id": None,
        "product_id": None,
        "after": None,
        "limit": 101,
    }
    value.update(overrides)
    return value


def _summary_parameters(**overrides) -> dict:
    value = {
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "move_types": None,
        "states": ["posted"],
        "payment_states": None,
        "partner_id": None,
        "product_id": None,
        "group_by": "partner",
    }
    value.update(overrides)
    return value


def _payload(capability_id: str, parameters: dict) -> dict:
    return {
        "capability_id": capability_id,
        "company_id": 7,
        "parameters": parameters,
    }


def _raw_row(row_id: int = 30) -> dict:
    return {
        "id": row_id,
        "move_id": [101, "INV/2026/0001"],
        "journal_id": [11, "Customer Invoices"],
        "company_id": [7, "China Company"],
        "company_currency_id": [6, "CNY"],
        "partner_id": [31, "Acme"],
        "move_type": "out_invoice",
        "state": "posted",
        "payment_state": "not_paid",
        "invoice_date": "2026-08-20",
        "invoice_date_due": "2026-09-20",
        "quantity": 2.0,
        "product_id": [41, "Service"],
        "product_uom_id": [1, "Units"],
        "price_subtotal_currency": 100.0,
        "price_subtotal": 100.0,
        "price_total": 106.0,
        "price_total_currency": 106.0,
        "price_average": 50.0,
        "price_margin": 60.0,
        "inventory_value": 40.0,
        "currency_id": [6, "CNY"],
    }


def test_search_uses_native_search_read_exact_company_and_id_cursor() -> None:
    report = Model(fields=REPORT_FIELDS, rows=[_raw_row(29)], cursor_exists=True)
    env = Env(report=report)
    parameters = _search_parameters(
        date_from="2026-01-01",
        date_to="2026-12-31",
        move_types=["out_invoice"],
        states=["posted"],
        payment_states=["not_paid"],
        partner_id=31,
        product_id=41,
        after=30,
        limit=11,
    )

    result = dispatch(
        env,
        _payload("invoice.analysis.search", parameters),
        7,
        failure_type=Failure,
    )

    assert result["user_id"] == 5
    assert result["cursor_found"] is True
    assert result["items"][0]["id"] == 29
    assert result["items"][0]["total_amount"] == "106"
    call = report.search_read_calls[0]
    assert call["order"] == "id desc"
    assert call["limit"] == 11
    assert ("company_id", "=", 7) in call["domain"]
    assert ("move_type", "in", ["out_invoice"]) in call["domain"]
    assert ("invoice_date", ">=", "2026-01-01") in call["domain"]
    assert ("partner_id", "=", 31) in call["domain"]
    assert ("product_id", "=", 41) in call["domain"]
    assert ("id", "<", 30) in call["domain"]
    assert report.search_count_calls[0][0][-1] == ("id", "=", 30)
    assert report.contexts == [{"allowed_company_ids": [7]}]


def test_missing_cursor_returns_empty_page_without_search_read() -> None:
    report = Model(fields=REPORT_FIELDS, cursor_exists=False)
    result = dispatch(
        Env(report=report),
        _payload("invoice.analysis.search", _search_parameters(after=30)),
        7,
        failure_type=Failure,
    )
    assert result["cursor_found"] is False
    assert result["items"] == []
    assert report.search_read_calls == []


def test_summary_uses_one_native_read_group_and_normalizes_decimal_totals() -> None:
    report = Model(
        fields=REPORT_FIELDS,
        groups=[
            (Ref(32, "Beta"), 1, 1.0, 50.0, 53.0, 30.0, 20.0),
            (Ref(31, "Acme"), 2, 3.0, 150.0, 159.0, 90.0, 60.0),
        ],
    )
    env = Env(report=report)
    result = dispatch(
        env,
        _payload("invoice.analysis.summary", _summary_parameters()),
        7,
        failure_type=Failure,
    )

    summary = result["items"][0]
    assert [group["group"]["id"] for group in summary["groups"]] == [31, 32]
    assert summary["totals"] == {
        "row_count": 3,
        "quantity": "4",
        "untaxed_amount": "200",
        "total_amount": "212",
        "margin": "120",
        "inventory_value": "80",
    }
    call = report.read_group_calls[0]
    assert call["groupby"] == ["partner_id"]
    assert call["order"] == "partner_id asc"
    assert call["aggregates"] == [
        "__count",
        "quantity:sum",
        "price_subtotal:sum",
        "price_total:sum",
        "price_margin:sum",
        "inventory_value:sum",
    ]
    assert ("company_id", "=", 7) in call["domain"]
    assert ("state", "in", ["posted"]) in call["domain"]


@pytest.mark.parametrize(
    ("group_by", "field", "value", "descriptor"),
    [
        ("move_type", "move_type", "out_invoice", {"id": None, "value": "out_invoice"}),
        ("state", "state", "posted", {"id": None, "value": "posted"}),
        (
            "payment_state",
            "payment_state",
            "paid",
            {"id": None, "value": "paid"},
        ),
        ("product", "product_id", Ref(41, "Service"), {"id": 41, "value": "Service"}),
        ("product", "product_id", EmptyRef(), {"id": None, "value": None}),
    ],
)
def test_summary_group_by_mapping_is_fixed(
    group_by: str, field: str, value, descriptor: dict
) -> None:
    report = Model(
        fields=REPORT_FIELDS,
        groups=[(value, 1, 1, 2, 3, 4, 5)],
    )
    result = dispatch(
        Env(report=report),
        _payload("invoice.analysis.summary", _summary_parameters(group_by=group_by)),
        7,
        failure_type=Failure,
    )
    assert result["items"][0]["groups"][0]["group"] == descriptor
    assert report.read_group_calls[0]["groupby"] == [field]


@pytest.mark.parametrize(
    "env",
    [
        Env(company_visible=False),
        Env(group_allowed=False),
        Env(missing_model="account.invoice.report"),
        Env(report=Model(fields=REPORT_FIELDS, access=False)),
    ],
)
def test_scope_failures_return_closed_empty_page(env: Env) -> None:
    page = dispatch(
        env,
        _payload("invoice.analysis.search", _search_parameters()),
        7,
        failure_type=Failure,
    )
    assert page["items"] == []
    assert page["access_allowed"] is False


def test_payload_drift_and_runtime_data_drift_fail_closed() -> None:
    payload = _payload("invoice.analysis.search", _search_parameters())
    payload["extra"] = True
    with pytest.raises(Failure) as caught:
        dispatch(Env(), payload, 7, failure_type=Failure)
    assert caught.value.code == "bridge_protocol_error"

    row = _raw_row()
    row["price_total"] = float("nan")
    with pytest.raises(Failure) as caught:
        dispatch(
            Env(report=Model(fields=REPORT_FIELDS, rows=[row])),
            _payload("invoice.analysis.search", _search_parameters()),
            7,
            failure_type=Failure,
        )
    assert caught.value.code == "odoo_runtime_error"


def test_required_field_drift_is_a_runtime_failure() -> None:
    with pytest.raises(Failure) as caught:
        dispatch(
            Env(report=Model(fields=REPORT_FIELDS - {"price_total"})),
            _payload("invoice.analysis.search", _search_parameters()),
            7,
            failure_type=Failure,
        )
    assert caught.value.code == "odoo_runtime_error"
