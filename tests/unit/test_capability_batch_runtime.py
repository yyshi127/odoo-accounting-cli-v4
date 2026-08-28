from __future__ import annotations

import copy
import io
import json
import sys
from datetime import date
from decimal import Decimal
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge import runtime
from odoo_accounting_cli_v4.bridge.runtime import RuntimeFailure

CURRENCY = "res.currency.convert"
BANK = "account.bank.statement.line.search_page"
PRODUCT = "product.product.accounting_profile.get"


@pytest.fixture(autouse=True)
def _fake_odoo_expression(monkeypatch: pytest.MonkeyPatch) -> None:
    def and_domains(domains: list[list[Any]]) -> list[Any]:
        domains = [domain for domain in domains if domain]
        return ["&"] * max(0, len(domains) - 1) + [
            item for domain in domains for item in domain
        ]

    odoo = ModuleType("odoo")
    odoo.__path__ = []  # type: ignore[attr-defined]
    osv = ModuleType("odoo.osv")
    osv.expression = SimpleNamespace(AND=and_domains)  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "odoo", odoo)
    monkeypatch.setitem(sys.modules, "odoo.osv", osv)


def _payload(action: str) -> dict[str, Any]:
    if action == CURRENCY:
        return {
            "company_id": 7,
            "amount": "125.5000",
            "from_currency_id": 2,
            "to_currency_id": 3,
            "date": "2025-02-01",
        }
    if action == BANK:
        return {"company_id": 7, "after": None, "limit": 3}
    return {"company_id": 7, "product_id": 31}


def _request(action: str, payload: dict[str, Any]) -> str:
    return json.dumps(
        {
            "schema_version": "v1",
            "target": {
                "alias": "v4-dev",
                "database": "odoo_cli_v4_dev",
                "company_id": 7,
                "user_login": "v4-agent",
                "language": "en_US",
                "timezone": "Asia/Shanghai",
            },
            "action": action,
            "payload": payload,
        }
    )


class _Registry:
    def __init__(self, env: "_Env") -> None:
        self.env = env

    def get(self, name: str):
        self.env.calls.append(("registry", name))
        return None if name == self.env.missing else self.env.models.get(name, object())


class _Account:
    def __init__(self, *ids: int) -> None:
        self.ids = list(ids)

    def __bool__(self) -> bool:
        return bool(self.ids)


class _Currency:
    def __init__(self, env: "_Env", record_id: int) -> None:
        self.env, self.id = env, record_id

    def _convert(self, amount, target, company, on_date, *, round):
        self.env.calls.append(
            ("convert", self.id, amount, target.id, company.id, on_date, round)
        )
        return Decimal("91.2500")


class _Product:
    id = 31

    def __init__(self, env: "_Env") -> None:
        self.env = env

    def with_company(self, company):
        return self

    def read(self, fields):
        return [
            {
                "display_name": "Office Chair / Blue",
                "default_code": False,
                "active": True,
                "company_id": False,
                "product_tmpl_id": [21, "Untrusted"],
            }
        ]

    def _get_product_accounts(self):
        self.env.calls.append(("product_accounts",))
        return {
            "income": _Account(401),
            "expense": _Account(),
            "stock_valuation": _Account(101),
            "stock_variation": _Account(102),
        }


class _Related:
    def __init__(self, env: "_Env", model: str) -> None:
        self.env, self.model = env, model
        self._fields = (
            {"valuation": object(), "cost_method": object()}
            if model == "product.template"
            else {}
        )

    def with_company(self, company):
        return self

    def read(self, fields):
        if self.model == "product.template":
            return [
                {
                    "name": "Office Chair",
                    "company_id": False,
                    "categ_id": [11, "Untrusted"],
                }
            ]
        return [
            {
                "name": "Office Furniture",
                "complete_name": "All / Office Furniture",
            }
        ]

    def __getitem__(self, field: str) -> str:
        return {"valuation": "real_time", "cost_method": "average"}[field]


class _Model:
    def __init__(self, env: "_Env", name: str) -> None:
        self.env, self.name = env, name

    def has_access(self, operation: str) -> bool:
        self.env.calls.append(("access", self.name, operation))
        return self.name != self.env.denied

    def search_count(self, domain, *, limit=None):
        assert self.name == "res.company"
        return 1

    def with_context(self, **context):
        self.env.calls.append(("context", self.name, context))
        return self

    def search(self, domain, *, limit):
        self.env.calls.append(("search", self.name, domain, limit))
        assert self.name == "product.product"
        return self.env.product

    def browse(self, record_id: int):
        self.env.calls.append(("browse", self.name, record_id))
        if self.name == "res.company":
            return SimpleNamespace(id=record_id)
        if self.name == "res.currency":
            return _Currency(self.env, record_id)
        if self.name == "product.template":
            return self.env.template
        if self.name == "product.category":
            return self.env.category
        raise AssertionError(f"unexpected browse: {self.name}")

    def search_read(self, domain, *, fields, limit, order):
        self.env.calls.append(
            ("search_read", self.name, domain, tuple(fields), limit, order)
        )
        rows = copy.deepcopy(self.env.rows[self.name])
        ids = next(
            (
                term[2]
                for term in domain
                if isinstance(term, tuple) and term[:2] == ("id", "in")
            ),
            None,
        )
        if ids is not None:
            rows = [row for row in rows if row["id"] in ids]
        return [
            {field: copy.deepcopy(row[field]) for field in fields}
            for row in rows[:limit]
        ]

class _Env:
    uid = 42

    def __init__(
        self,
        *,
        missing: str | None = None,
        denied: str | None = None,
    ) -> None:
        self.calls: list[tuple[Any, ...]] = []
        self.missing, self.denied = missing, denied
        self.rows = {
            "res.currency": [{"id": 2, "name": "USD"}, {"id": 3, "name": "EUR"}],
            "account.bank.statement.line": [
                {
                    "id": 80,
                    "company_id": [7, "Untrusted"],
                    "payment_ref": False,
                    "partner_id": [11, "Untrusted"],
                    "journal_id": [12, "Untrusted"],
                    "amount": Decimal("125.5000"),
                    "currency_id": [2, "Untrusted"],
                    "move_id": [30, "Untrusted"],
                    "is_reconciled": True,
                    "payment_ids": [40, 41],
                }
            ],
            "res.partner": [{"id": 11, "complete_name": "Acme Ltd"}],
            "account.journal": [
                {"id": 12, "code": "BNK1", "name": "Main Bank", "company_id": [7, "C"]}
            ],
            "account.move": [
                {
                    "id": 30,
                    "name": "BNK/2025/0001",
                    "state": "posted",
                    "date": date(2025, 1, 25),
                    "ref": "INV/42",
                    "company_id": [7, "C"],
                }
            ],
            "account.payment": [
                {"id": 40, "date": "2025-01-24", "company_id": [7, "C"]},
                {"id": 41, "date": date(2025, 1, 26), "company_id": [7, "C"]},
            ],
            "account.account": [
                {"id": 101, "code": "140500", "name": "Stock Valuation"},
                {"id": 401, "code": "600100", "name": "Sales"},
            ],
        }
        names = {
            "res.company",
            "res.currency",
            "res.currency.rate",
            "account.bank.statement.line",
            "account.move",
            "account.journal",
            "res.partner",
            "account.payment",
            "product.product",
            "product.template",
            "product.category",
            "account.account",
        }
        self.models = {name: _Model(self, name) for name in names}
        self.registry = _Registry(self)
        self.product = _Product(self)
        self.template = _Related(self, "product.template")
        self.category = _Related(self, "product.category")

    def __getitem__(self, name: str):
        self.calls.append(("model", name))
        return self.models[name]


def test_currency_convert_normalizes_and_calls_odoo_convert() -> None:
    env = _Env()
    result = runtime._dispatch(env, CURRENCY, _payload(CURRENCY), 7)

    assert result["conversion"] == {
        "company_id": 7,
        "date": "2025-02-01",
        "amount": "125.5000",
        "converted_amount": "91.25",
        "from_currency": {"id": 2, "code": "USD"},
        "to_currency": {"id": 3, "code": "EUR"},
    }
    conversion_call = ("convert", 2, 125.5, 3, 7, date(2025, 2, 1), True)
    assert conversion_call in env.calls


def test_bank_transaction_normalizes_earliest_automatic_payment_date() -> None:
    env = _Env()
    result = runtime._dispatch(env, BANK, _payload(BANK), 7)

    row = result["rows"][0]
    assert (row["id"], row["company_id"], row["date"]) == (80, 7, "2025-01-25")
    assert row["payment_date"] == "2025-01-24"
    assert (row["name"], row["reference"], row["amount"]) == (None, "INV/42", "125.5")
    assert row["partner"] == {"id": 11, "name": "Acme Ltd"}
    assert row["journal"] == {"id": 12, "code": "BNK1", "name": "Main Bank"}
    assert row["currency"] == {"id": 2, "code": "USD"}
    assert row["move"] == {"id": 30, "name": "BNK/2025/0001", "state": "posted"}
    assert row["reconciled"] is True
    search = next(
        call for call in env.calls if call[:2] == ("search_read", "account.bank.statement.line")
    )
    assert search[2] == [("company_id", "=", 7)]
    assert search[4:] == (3, "date desc,id desc")


def test_product_profile_uses_odoo19_marker_and_final_account_keys() -> None:
    env = _Env()
    data = runtime._dispatch(env, PRODUCT, _payload(PRODUCT), 7)["data"]

    assert data["product"]["name"] == "Office Chair / Blue"
    assert data["product"]["default_code"] is None
    assert data["modules"] == {"account": True, "stock_account": True}
    assert data["accounts"]["income"]["account"] == {
        "id": 401,
        "code": "600100",
        "name": "Sales",
    }
    assert data["accounts"]["expense"]["account"] is None
    assert data["accounts"]["stock_valuation"]["account"]["id"] == 101
    for key in ("stock_input", "stock_output"):
        assert data["accounts"][key] == {
            "available": False,
            "reason_code": "field_unavailable",
            "account": None,
        }
    assert data["valuation"]["value"] == "real_time"
    assert data["cost_method"]["value"] == "average"
    assert ("registry", "product.value") in env.calls
    assert ("product_accounts",) in env.calls


@pytest.mark.parametrize(
    ("action", "nearby"),
    (
        (CURRENCY, "currency.convert"),
        (BANK, "bank.transaction.list"),
        (PRODUCT, "product.accounting_profile.get"),
    ),
)
def test_actions_are_allowlisted_and_payloads_are_closed(
    action: str, nearby: str
) -> None:
    payload = _payload(action)
    assert runtime._decode_request(io.StringIO(_request(action, payload)))["action"] == action

    with pytest.raises(RuntimeFailure):
        runtime._decode_request(io.StringIO(_request(nearby, payload)))
    env = _Env()
    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(env, action, {**payload, "extra": True}, 7)
    assert caught.value.code == "bridge_protocol_error"
    assert env.calls == []


@pytest.mark.parametrize(
    ("action", "missing", "denied", "empty_key", "module_installed"),
    (
        (CURRENCY, "res.currency.rate", None, "conversion", False),
        (BANK, None, "account.journal", "rows", True),
        (PRODUCT, "product.template", None, "data", False),
    ),
)
def test_runtime_gates_return_closed_pages(
    action: str,
    missing: str | None,
    denied: str | None,
    empty_key: str,
    module_installed: bool,
) -> None:
    result = runtime._dispatch(
        _Env(missing=missing, denied=denied), action, _payload(action), 7
    )

    assert result["company_visible"] is True
    assert result["module_installed"] is module_installed
    assert result["access_allowed"] is False
    assert result[empty_key] in (None, [])
