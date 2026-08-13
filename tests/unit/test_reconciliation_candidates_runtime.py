from __future__ import annotations

import copy
import io
import json
import sys
from types import ModuleType
from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge import runtime
from odoo_accounting_cli_v4.bridge.runtime import RuntimeFailure


ACTION = "account.move.line.reconciliation_candidate.read_page"
REQUIRED_MODELS = {
    "res.company",
    "account.move.line",
    "account.move",
    "account.account",
    "account.journal",
    "res.partner",
    "res.currency",
    "account.reconcile.model",
}
REGISTRY_SENTINEL = "account.reconcile.wizard"
ACCOUNT_TYPES = (
    "asset_receivable",
    "asset_cash",
    "asset_current",
    "asset_non_current",
    "asset_prepayments",
    "asset_fixed",
    "liability_payable",
    "liability_credit_card",
    "liability_current",
    "liability_non_current",
    "equity",
    "equity_unaffected",
    "income",
    "income_other",
    "expense",
    "expense_other",
    "expense_depreciation",
    "expense_direct_cost",
    "off_balance",
)
MOVE_TYPES = {
    "entry",
    "out_invoice",
    "out_refund",
    "in_invoice",
    "in_refund",
    "out_receipt",
    "in_receipt",
}
JOURNAL_TYPES = {"sale", "purchase", "cash", "bank", "credit", "general"}
CANDIDATE_FIELDS = [
    "id",
    "date",
    "invoice_date",
    "date_maturity",
    "parent_state",
    "move_id",
    "move_name",
    "ref",
    "name",
    "account_id",
    "partner_id",
    "journal_id",
    "company_id",
    "company_currency_id",
    "currency_id",
    "balance",
    "amount_currency",
    "amount_residual",
    "amount_residual_currency",
    "reconciled",
    "matching_number",
    "reconcile_model_id",
    "display_type",
    "full_reconcile_id",
]
COMPANY_FIELDS = ["id", "parent_path", "currency_id"]
ACCOUNT_FIELDS = ["id", "code", "name", "account_type", "reconcile"]
MOVE_FIELDS = [
    "id",
    "name",
    "move_type",
    "ref",
    "state",
    "date",
    "invoice_date",
    "company_id",
    "journal_id",
    "company_currency_id",
]
JOURNAL_FIELDS = ["id", "code", "name", "type", "company_id"]
PARTNER_FIELDS = ["id", "name"]
CURRENCY_FIELDS = ["id", "name"]
RECONCILE_MODEL_FIELDS = ["id", "name", "company_id"]


def _filters(**overrides: Any) -> dict[str, Any]:
    value = {
        "date_from": None,
        "date_to": None,
        "states": ["posted"],
        "account_id": None,
        "partner_id": None,
        "journal_id": None,
        "account_kinds": ["receivable", "payable", "other"],
        "query": None,
    }
    value.update(overrides)
    return value


def _payload(**overrides: Any) -> dict[str, Any]:
    value = {
        "company_id": 7,
        "after": None,
        "limit": 4,
        "filters": _filters(),
    }
    value.update(overrides)
    return value


def _bridge_request(payload: dict[str, Any] | None = None) -> str:
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
            "action": ACTION,
            "payload": payload or _payload(),
        }
    )


@pytest.fixture(autouse=True)
def _fake_odoo_domains(monkeypatch: pytest.MonkeyPatch) -> None:
    def combine(operator: str, domains: list[list[Any]]) -> list[Any]:
        nonempty = [list(domain) for domain in domains if domain]
        result: list[Any] = [operator] * max(0, len(nonempty) - 1)
        for domain in nonempty:
            result.extend(domain)
        return result

    class Domain(list[Any]):
        @classmethod
        def AND(cls, domains: list[list[Any]]) -> list[Any]:
            return combine("&", domains)

        @classmethod
        def OR(cls, domains: list[list[Any]]) -> list[Any]:
            return combine("|", domains)

    odoo = ModuleType("odoo")
    odoo.__path__ = []  # type: ignore[attr-defined]
    fields = ModuleType("odoo.fields")
    fields.Domain = Domain  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "odoo", odoo)
    monkeypatch.setitem(sys.modules, "odoo.fields", fields)


def _reference_id(value: Any) -> int | None:
    if value in (False, None):
        return None
    if isinstance(value, (list, tuple)):
        return value[0]
    return value


def _domain_terms(domain: list[Any]) -> list[tuple[Any, ...]]:
    return [term for term in domain if isinstance(term, tuple)]


def _domain_value(domain: list[Any], field: str, operator: str) -> Any:
    for term in _domain_terms(domain):
        if term[:2] == (field, operator):
            return term[2]
    return None


def _project(row: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    requested = list(dict.fromkeys(["id", *fields]))
    return {field: copy.deepcopy(row[field]) for field in requested}


class _Model:
    def __init__(
        self,
        name: str,
        env: "_Environment",
        *,
        access_allowed: bool = True,
    ) -> None:
        self.name = name
        self.env = env
        self.access_allowed = access_allowed
        self.context: dict[str, Any] = {}

    def has_access(self, operation: str) -> bool:
        self.env.calls.append(("access", self.name, operation))
        return self.access_allowed

    def with_context(self, **context: Any):
        self.env.calls.append(("context", self.name, copy.deepcopy(context)))
        self.context.update(context)
        return self

    def search_count(self, domain: list[Any], *, limit: int) -> int:
        self.env.calls.append(
            ("count", self.name, copy.deepcopy(domain), limit)
        )
        return int(bool(self.env.respond(self.name, domain)[:limit]))

    def search_read(
        self,
        domain: list[Any],
        *,
        fields: list[str],
        limit: int | None = None,
        order: str | None = None,
    ) -> list[dict[str, Any]]:
        self.env.calls.append(
            (
                "search",
                self.name,
                copy.deepcopy(domain),
                list(fields),
                limit,
                order,
            )
        )
        rows = self.env.respond(self.name, domain)
        if self.name == "account.move.line" and not self.env.preserve_aml_order:
            rows.sort(key=lambda row: (row["date"], row["id"]), reverse=True)
        elif order == "id":
            rows.sort(key=lambda row: row["id"])
        if limit is not None:
            rows = rows[:limit]
        return [_project(row, fields) for row in rows]

    def sudo(self, *args: Any, **kwargs: Any):
        raise AssertionError(f"reconciliation candidate runtime must never sudo {self.name}")


class _Registry:
    def __init__(
        self,
        env: "_Environment",
        *,
        missing_model: str | None,
    ) -> None:
        self.env = env
        self.missing_model = missing_model

    def get(self, model: str):
        self.env.calls.append(("registry", model))
        if model == self.missing_model:
            return None
        if model == REGISTRY_SENTINEL:
            return object()
        return self.env.models.get(model)


def _candidate(
    record_id: int,
    *,
    date: str,
    move_id: int,
    journal_id: int,
    partner_id: int,
    account_id: int,
    balance: float,
    residual: float,
    name: str | bool,
    ref: str | bool,
    invoice_date: str | bool,
    maturity: str | bool,
    matching: str | bool = False,
    reconcile_model_id: int | bool = False,
) -> dict[str, Any]:
    return {
        "id": record_id,
        "date": date,
        "invoice_date": invoice_date,
        "date_maturity": maturity,
        "parent_state": "posted",
        "move_id": [move_id, "untrusted move display"],
        "move_name": {
            99: "BNK1/2025/00005",
            98: "BILL/2025/00098",
            97: "INV/2025/00097",
        }[move_id],
        "ref": ref,
        "name": name,
        "account_id": [account_id, "untrusted account display"],
        "partner_id": [partner_id, "untrusted partner display"],
        "journal_id": [journal_id, "untrusted journal display"],
        "company_id": [7, "Fixture Company"],
        "company_currency_id": [37, "untrusted currency display"],
        "currency_id": [37, "untrusted currency display"],
        "balance": balance,
        "amount_currency": balance,
        "amount_residual": residual,
        "amount_residual_currency": residual,
        "reconciled": False,
        "matching_number": matching,
        "reconcile_model_id": (
            [reconcile_model_id, "untrusted model display"]
            if reconcile_model_id
            else False
        ),
        "display_type": "payment_term",
        "full_reconcile_id": False,
    }


def _records() -> dict[str, list[dict[str, Any]]]:
    return {
        "res.company": [
            {"id": 1, "parent_path": "1/", "currency_id": [37, "SGD"]},
            {"id": 7, "parent_path": "1/7/", "currency_id": [37, "SGD"]},
            {"id": 8, "parent_path": "8/", "currency_id": [6, "CNY"]},
        ],
        "account.account": [
            {
                "id": 101,
                "code": "1100",
                "name": "Accounts Receivable",
                "account_type": "asset_receivable",
                "reconcile": True,
                "company_ids": [1],
            },
            {
                "id": 102,
                "code": "2100",
                "name": "Accounts Payable",
                "account_type": "liability_payable",
                "reconcile": True,
                "company_ids": [7],
            },
            {
                "id": 103,
                "code": "110101",
                "name": "Bank Suspense",
                "account_type": "asset_current",
                "reconcile": True,
                "company_ids": [1],
            },
            {
                "id": 104,
                "code": "4000",
                "name": "Revenue",
                "account_type": "income",
                "reconcile": False,
                "company_ids": [7],
            },
        ],
        "account.move.line": [
            _candidate(
                303,
                date="2025-01-25",
                move_id=99,
                journal_id=8,
                partner_id=9,
                account_id=103,
                balance=50.0,
                residual=50.0,
                name="Fixture suspense payment",
                ref=False,
                invoice_date=False,
                maturity=False,
                reconcile_model_id=50,
            ),
            _candidate(
                302,
                date="2025-01-21",
                move_id=98,
                journal_id=7,
                partner_id=10,
                account_id=102,
                balance=-113.0,
                residual=-113.0,
                name=False,
                ref="ODACV4-FX1-SG-BILL-TAX-INCLUDED",
                invoice_date="2025-01-21",
                maturity="2025-02-21",
            ),
            _candidate(
                301,
                date="2025-01-20",
                move_id=97,
                journal_id=6,
                partner_id=11,
                account_id=101,
                balance=113.0,
                residual=63.0,
                name="Fixture invoice receivable",
                ref="ODACV4-FX1-SG-INVOICE-TAX-EXCLUDED",
                invoice_date="2025-01-20",
                maturity="2025-02-20",
                matching="P7",
            ),
        ],
        "account.move": [
            {
                "id": 99,
                "name": "BNK1/2025/00005",
                "move_type": "entry",
                "ref": False,
                "state": "posted",
                "date": "2025-01-25",
                "invoice_date": False,
                "company_id": [7, "Fixture Company"],
                "journal_id": [8, "Bank"],
                "company_currency_id": [37, "SGD"],
            },
            {
                "id": 98,
                "name": "BILL/2025/00098",
                "move_type": "in_invoice",
                "ref": "ODACV4-FX1-SG-BILL-TAX-INCLUDED",
                "state": "posted",
                "date": "2025-01-21",
                "invoice_date": "2025-01-21",
                "company_id": [7, "Fixture Company"],
                "journal_id": [7, "Purchases"],
                "company_currency_id": [37, "SGD"],
            },
            {
                "id": 97,
                "name": "INV/2025/00097",
                "move_type": "out_invoice",
                "ref": "ODACV4-FX1-SG-INVOICE-TAX-EXCLUDED",
                "state": "posted",
                "date": "2025-01-20",
                "invoice_date": "2025-01-20",
                "company_id": [7, "Fixture Company"],
                "journal_id": [6, "Sales"],
                "company_currency_id": [37, "SGD"],
            },
        ],
        "account.journal": [
            {
                "id": 6,
                "code": "INV",
                "name": "Sales",
                "type": "sale",
                "company_id": [7, "Fixture Company"],
            },
            {
                "id": 7,
                "code": "BILL",
                "name": "Purchases",
                "type": "purchase",
                "company_id": [7, "Fixture Company"],
            },
            {
                "id": 8,
                "code": "BNK1",
                "name": "Bank",
                "type": "bank",
                "company_id": [1, "Parent Company"],
            },
        ],
        "res.partner": [
            {"id": 9, "name": "Fixture Customer"},
            {"id": 10, "name": "Fixture Vendor"},
            {"id": 11, "name": "Fixture Customer"},
        ],
        "res.currency": [
            {"id": 6, "name": "CNY"},
            {"id": 37, "name": "SGD"},
        ],
        "account.reconcile.model": [
            {"id": 50, "name": "Historical rule", "company_id": [7, "Fixture"]}
        ],
    }


class _Environment:
    uid = 42
    su = False

    def __init__(
        self,
        *,
        company_visible: bool = True,
        missing_model: str | None = None,
        denied_model: str | None = None,
    ) -> None:
        self.calls: list[tuple[Any, ...]] = []
        self.records = _records()
        if not company_visible:
            self.records["res.company"] = [
                row for row in self.records["res.company"] if row["id"] != 7
            ]
        self.preserve_aml_order = False
        self.aml_domain_passthrough_fields: set[str] = set()
        self.models = {
            model: _Model(
                model,
                self,
                access_allowed=denied_model != model,
            )
            for model in REQUIRED_MODELS
        }
        self.registry = _Registry(self, missing_model=missing_model)

    def __getitem__(self, model: str):
        self.calls.append(("model", model))
        if model not in self.models:
            raise AssertionError(f"unexpected model access: {model}")
        return self.models[model]

    def respond(self, model: str, domain: list[Any]) -> list[dict[str, Any]]:
        rows = copy.deepcopy(self.records[model])
        terms = _domain_terms(domain)
        for field, operator, value in terms:
            if (
                model == "account.move.line"
                and field in self.aml_domain_passthrough_fields
            ):
                continue
            if field == "id" and operator == "=":
                rows = [row for row in rows if row["id"] == value]
            elif field == "id" and operator == "in":
                rows = [row for row in rows if row["id"] in value]
            elif field == "company_id" and operator == "=":
                rows = [
                    row for row in rows if _reference_id(row.get("company_id")) == value
                ]
            elif field == "company_id" and operator == "in":
                rows = [
                    row
                    for row in rows
                    if _reference_id(row.get("company_id")) in value
                ]
            elif field == "company_ids" and operator == "in":
                rows = [
                    row
                    for row in rows
                    if set(row.get("company_ids", [])).intersection(value)
                ]
            elif field == "reconcile" and operator == "=":
                rows = [row for row in rows if row.get("reconcile") is value]
            elif field == "account_id" and operator == "in":
                rows = [
                    row for row in rows if _reference_id(row.get("account_id")) in value
                ]
            elif field == "partner_id" and operator == "=":
                rows = [
                    row for row in rows if _reference_id(row.get("partner_id")) == value
                ]
            elif field == "journal_id" and operator == "=":
                rows = [
                    row for row in rows if _reference_id(row.get("journal_id")) == value
                ]
            elif field == "parent_state" and operator == "in":
                rows = [row for row in rows if row.get("parent_state") in value]
            elif field == "display_type" and operator == "not in":
                rows = [row for row in rows if row.get("display_type") not in value]
            elif field == "full_reconcile_id" and operator == "=":
                rows = [
                    row
                    for row in rows
                    if _reference_id(row.get("full_reconcile_id"))
                    == _reference_id(value)
                ]
            elif field == "amount_residual" and operator == "!=":
                rows = [row for row in rows if row.get("amount_residual") != value]
        return rows


def _search_calls(env: _Environment, model: str) -> list[tuple[Any, ...]]:
    return [call for call in env.calls if call[:2] == ("search", model)]


def _expected_candidate(record_id: int) -> dict[str, Any]:
    raw = next(row for row in _records()["account.move.line"] if row["id"] == record_id)
    records = _records()
    move_id = _reference_id(raw["move_id"])
    account_id = _reference_id(raw["account_id"])
    partner_id = _reference_id(raw["partner_id"])
    journal_id = _reference_id(raw["journal_id"])
    currency_id = _reference_id(raw["currency_id"])
    company_currency_id = _reference_id(raw["company_currency_id"])
    reconcile_model_id = _reference_id(raw["reconcile_model_id"])

    def one(model: str, record: int) -> dict[str, Any]:
        return next(row for row in records[model] if row["id"] == record)

    move = one("account.move", move_id)
    account = one("account.account", account_id)
    journal = one("account.journal", journal_id)
    partner = one("res.partner", partner_id)
    currency = one("res.currency", currency_id)
    company_currency = one("res.currency", company_currency_id)
    reconcile_model = (
        one("account.reconcile.model", reconcile_model_id)
        if reconcile_model_id is not None
        else None
    )

    def optional(value: Any) -> str | None:
        return None if value in (False, None, "") else value

    def money(value: Any) -> str:
        if value == 0:
            return "0"
        text = format(value, "f")
        return text.rstrip("0").rstrip(".") if "." in text else text

    return {
        "id": record_id,
        "date": raw["date"],
        "invoice_date": optional(raw["invoice_date"]),
        "date_maturity": optional(raw["date_maturity"]),
        "state": raw["parent_state"],
        "move": {
            "id": move_id,
            "name": optional(move["name"]),
            "move_type": move["move_type"],
            "ref": optional(move["ref"]),
        },
        "label": optional(raw["name"]),
        "account": {
            "id": account_id,
            "code": account["code"],
            "name": account["name"],
            "account_type": account["account_type"],
        },
        "partner": {"id": partner_id, "name": optional(partner["name"])},
        "journal": {
            "id": journal_id,
            "code": journal["code"],
            "name": journal["name"],
            "type": journal["type"],
        },
        "company_id": 7,
        "company_currency": {
            "id": company_currency_id,
            "code": company_currency["name"],
        },
        "currency": {"id": currency_id, "code": currency["name"]},
        "balance": money(raw["balance"]),
        "amount_currency": money(raw["amount_currency"]),
        "amount_residual": money(raw["amount_residual"]),
        "amount_residual_currency": money(raw["amount_residual_currency"]),
        "matching_number": optional(raw["matching_number"]),
        "reconciliation_model": (
            None
            if reconcile_model is None
            else {"id": reconcile_model_id, "name": reconcile_model["name"]}
        ),
    }


def _dispatch(env: _Environment, payload: dict[str, Any] | None = None):
    return runtime._dispatch(env, ACTION, payload or _payload(), 7)


def _assert_runtime_error(env: _Environment, payload: dict[str, Any] | None = None) -> None:
    with pytest.raises(RuntimeFailure) as caught:
        _dispatch(env, payload)
    assert caught.value.code == "odoo_runtime_error"
    assert caught.value.exit_code == 7


def test_fixed_reconciliation_candidate_action_is_allowlisted_by_decoder() -> None:
    decoded = runtime._decode_request(io.StringIO(_bridge_request()))
    assert decoded["action"] == ACTION


def test_default_page_uses_all_three_reconcilable_account_kinds() -> None:
    env = _Environment()

    result = _dispatch(env)

    assert result == {
        "user_id": 42,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "rows": [
            _expected_candidate(303),
            _expected_candidate(302),
            _expected_candidate(301),
        ],
    }
    assert result["rows"][0]["account"]["account_type"] == "asset_current"
    assert result["rows"][0]["reconciliation_model"] == {
        "id": 50,
        "name": "Historical rule",
    }
    assert result["rows"][1]["label"] is None
    assert result["rows"][2]["matching_number"] == "P7"


def test_exact_company_scope_safe_domain_cursor_query_and_related_rereads() -> None:
    env = _Environment()
    payload = _payload(
        after=["2025-01-26", 304],
        filters=_filters(
            date_from="2025-01-01",
            date_to="2025-01-31",
            states=["draft", "posted"],
            account_id=103,
            partner_id=9,
            journal_id=8,
            account_kinds=["other"],
            query="%needle_\\",
        ),
    )

    result = _dispatch(env, payload)

    assert result["rows"] == [_expected_candidate(303)]
    company_calls = _search_calls(env, "res.company")
    assert company_calls == [
        (
            "search",
            "res.company",
            [("id", "=", 7)],
            COMPANY_FIELDS,
            1,
            "id",
        )
    ]
    account_call = _search_calls(env, "account.account")[0]
    assert account_call[2] == [
        ("company_ids", "in", [1, 7]),
        ("reconcile", "=", True),
    ]
    assert account_call[3] == ACCOUNT_FIELDS
    assert "company_ids" not in account_call[3]

    line_call = _search_calls(env, "account.move.line")[0]
    assert line_call[3:] == (CANDIDATE_FIELDS, 4, "date desc,id desc")
    domain = line_call[2]
    for term in (
        ("company_id", "=", 7),
        (
            "display_type",
            "not in",
            ("line_section", "line_subsection", "line_note"),
        ),
        ("account_id", "in", [103]),
        ("full_reconcile_id", "=", False),
        ("amount_residual", "!=", 0),
        ("parent_state", "in", ["draft", "posted"]),
        ("date", ">=", "2025-01-01"),
        ("date", "<=", "2025-01-31"),
        ("partner_id", "=", 9),
        ("journal_id", "=", 8),
        ("name", "ilike", "%needle_\\"),
        ("move_name", "ilike", "%needle_\\"),
        ("ref", "ilike", "%needle_\\"),
        ("partner_id.name", "ilike", "%needle_\\"),
        ("date", "<", "2025-01-26"),
        ("date", "=", "2025-01-26"),
        ("id", "<", 304),
    ):
        assert term in domain
    forbidden_paths = {
        "move_id.name",
        "move_id.ref",
        "account_id.reconcile",
        "account_id.account_type",
    }
    assert not any(term[0] in forbidden_paths for term in _domain_terms(domain))
    query_domain = [
        "|",
        "|",
        "|",
        ("name", "ilike", "%needle_\\"),
        ("move_name", "ilike", "%needle_\\"),
        ("ref", "ilike", "%needle_\\"),
        ("partner_id.name", "ilike", "%needle_\\"),
    ]
    assert any(
        domain[index : index + len(query_domain)] == query_domain
        for index in range(len(domain) - len(query_domain) + 1)
    )
    assert domain[-5:] == [
        "|",
        ("date", "<", "2025-01-26"),
        "&",
        ("date", "=", "2025-01-26"),
        ("id", "<", 304),
    ]

    assert _search_calls(env, "account.move")[0] == (
        "search",
        "account.move",
        [("id", "in", [99]), ("company_id", "=", 7)],
        MOVE_FIELDS,
        1,
        "id",
    )
    assert _search_calls(env, "account.journal")[0] == (
        "search",
        "account.journal",
        [("id", "in", [8]), ("company_id", "in", [1, 7])],
        JOURNAL_FIELDS,
        1,
        "id",
    )
    assert _search_calls(env, "res.partner")[0] == (
        "search",
        "res.partner",
        [("id", "in", [9])],
        PARTNER_FIELDS,
        1,
        "id",
    )
    assert not any(
        term[0] == "company_id"
        for term in _domain_terms(_search_calls(env, "res.partner")[0][2])
    )
    assert _search_calls(env, "res.currency")[0] == (
        "search",
        "res.currency",
        [("id", "in", [37])],
        CURRENCY_FIELDS,
        1,
        "id",
    )
    assert _search_calls(env, "account.reconcile.model")[0] == (
        "search",
        "account.reconcile.model",
        [("id", "in", [50]), ("company_id", "=", 7)],
        RECONCILE_MODEL_FIELDS,
        1,
        "id",
    )
    for model in REQUIRED_MODELS:
        assert (
            "context",
            model,
            {"active_test": False, "allowed_company_ids": [7]},
        ) in env.calls


@pytest.mark.parametrize(
    ("kind", "expected_id", "expected_type"),
    (
        ("receivable", 301, "asset_receivable"),
        ("payable", 302, "liability_payable"),
        ("other", 303, "asset_current"),
    ),
)
def test_account_kinds_are_an_authorized_account_index_intersection(
    kind: str,
    expected_id: int,
    expected_type: str,
) -> None:
    env = _Environment()

    result = _dispatch(env, _payload(filters=_filters(account_kinds=[kind])))

    assert [row["id"] for row in result["rows"]] == [expected_id]
    assert result["rows"][0]["account"]["account_type"] == expected_type
    line_domain = _search_calls(env, "account.move.line")[0][2]
    assert _domain_value(line_domain, "account_id", "in") == [
        {"receivable": 101, "payable": 102, "other": 103}[kind]
    ]


def test_account_id_and_kind_combine_with_and_without_existence_leaks() -> None:
    env = _Environment()
    result = _dispatch(
        env,
        _payload(
            filters=_filters(account_id=101, account_kinds=["payable"])
        ),
    )

    assert result["rows"] == []
    assert not _search_calls(env, "account.move.line")

    absent = _Environment()
    absent_result = _dispatch(
        absent,
        _payload(filters=_filters(account_id=2_147_483_647)),
    )
    assert absent_result == result
    assert not _search_calls(absent, "account.move.line")


def test_all_registry_and_acl_gates_precede_candidate_and_related_reads() -> None:
    env = _Environment()
    _dispatch(env)

    first_candidate_read = next(
        index
        for index, call in enumerate(env.calls)
        if call[:2] == ("search", "account.move.line")
    )
    prefix = env.calls[:first_candidate_read]
    assert REQUIRED_MODELS <= {
        call[1] for call in prefix if call[0] == "registry"
    }
    assert ("registry", REGISTRY_SENTINEL) in prefix
    assert REQUIRED_MODELS == {
        call[1] for call in prefix if call[0] == "access" and call[2] == "read"
    }
    assert not any(call[0] == "access" and call[1] == REGISTRY_SENTINEL for call in env.calls)


@pytest.mark.parametrize("denied_model", sorted(REQUIRED_MODELS))
def test_each_read_acl_denial_is_empty_without_business_reads(
    denied_model: str,
) -> None:
    env = _Environment(denied_model=denied_model)

    result = _dispatch(env)

    assert result == {
        "user_id": 42,
        "company_visible": denied_model != "res.company",
        "module_installed": True,
        "access_allowed": False,
        "rows": [],
    }
    assert not any(call[0] == "search" for call in env.calls)


@pytest.mark.parametrize("missing_model", sorted(REQUIRED_MODELS | {REGISTRY_SENTINEL}))
def test_each_missing_model_or_accountant_sentinel_is_uninstalled(
    missing_model: str,
) -> None:
    env = _Environment(missing_model=missing_model)

    result = _dispatch(env)

    assert result == {
        "user_id": 42,
        "company_visible": missing_model != "res.company",
        "module_installed": False,
        "access_allowed": False,
        "rows": [],
    }
    assert not any(call[0] == "search" for call in env.calls)


def test_invisible_company_is_empty_without_business_reads() -> None:
    env = _Environment(company_visible=False)

    result = _dispatch(env)

    assert result == {
        "user_id": 42,
        "company_visible": False,
        "module_installed": True,
        "access_allowed": False,
        "rows": [],
    }
    assert not _search_calls(env, "account.move.line")


@pytest.mark.parametrize(
    "payload",
    (
        {"company_id": 7, "after": None, "limit": 4},
        {**_payload(), "unexpected": None},
        _payload(company_id=True),
        _payload(after=["2025-1-20", 1]),
        _payload(after=["2025-01-20"]),
        _payload(after=["2025-01-20", True]),
        _payload(limit=0),
        _payload(limit=1002),
        _payload(limit=True),
        _payload(filters={key: value for key, value in _filters().items() if key != "query"}),
        _payload(filters={**_filters(), "unexpected": None}),
        _payload(filters=_filters(date_from="2025-1-01")),
        _payload(filters=_filters(date_from="2025-02-01", date_to="2025-01-01")),
        _payload(filters=_filters(states=[])),
        _payload(filters=_filters(states=["cancel"])),
        _payload(filters=_filters(states=["posted", "draft"])),
        _payload(filters=_filters(states=["draft", "draft"])),
        _payload(filters=_filters(account_id=True)),
        _payload(filters=_filters(partner_id=0)),
        _payload(filters=_filters(journal_id="8")),
        _payload(filters=_filters(account_kinds=["other", "receivable"])),
        _payload(filters=_filters(account_kinds=[])),
        _payload(filters=_filters(account_kinds=["other", "other"])),
        _payload(filters=_filters(account_kinds=["bank"])),
        _payload(filters=_filters(query=" untrimmed")),
        _payload(filters=_filters(query="")),
        _payload(filters=_filters(query="x" * 201)),
    ),
)
def test_malformed_payloads_fail_before_any_model_access(
    payload: dict[str, Any],
) -> None:
    env = _Environment()
    with pytest.raises(RuntimeFailure) as caught:
        _dispatch(env, payload)
    assert caught.value.code == "bridge_protocol_error"
    assert caught.value.exit_code == 7
    assert str(caught.value) == "The bridge action payload is invalid."
    assert not env.calls


def test_company_mismatch_fails_before_any_model_access() -> None:
    env = _Environment()
    with pytest.raises(RuntimeFailure) as caught:
        _dispatch(env, _payload(company_id=8))
    assert caught.value.code == "company_unavailable"
    assert caught.value.exit_code == 3
    assert not env.calls


def test_parent_accounts_and_journals_are_valid_without_reading_company_m2m() -> None:
    env = _Environment()

    result = _dispatch(env, _payload(filters=_filters(account_kinds=["other"])))

    assert [row["id"] for row in result["rows"]] == [303]
    assert result["rows"][0]["journal"]["id"] == 8
    account_call = _search_calls(env, "account.account")[0]
    assert "company_ids" not in account_call[3]
    journal_call = _search_calls(env, "account.journal")[0]
    assert ("company_id", "in", [1, 7]) in journal_call[2]


def test_sibling_account_disappears_safely_and_sibling_journal_fails_closed() -> None:
    account_env = _Environment()
    next(row for row in account_env.records["account.account"] if row["id"] == 103)[
        "company_ids"
    ] = [8]

    account_result = _dispatch(
        account_env, _payload(filters=_filters(account_kinds=["other"]))
    )
    assert account_result["rows"] == []

    journal_env = _Environment()
    next(row for row in journal_env.records["account.journal"] if row["id"] == 8)[
        "company_id"
    ] = [8, "Sibling"]
    _assert_runtime_error(
        journal_env, _payload(filters=_filters(account_kinds=["other"]))
    )


def test_partner_reread_uses_business_rules_without_an_invented_company_domain() -> None:
    env = _Environment()

    result = _dispatch(env, _payload(filters=_filters(account_kinds=["other"])))

    assert result["rows"][0]["partner"] == {"id": 9, "name": "Fixture Customer"}
    partner_call = _search_calls(env, "res.partner")[0]
    assert partner_call[2] == [("id", "in", [9])]
    assert PARTNER_FIELDS == ["id", "name"]


def test_nullable_odoo_text_and_draft_move_name_are_preserved_without_fallback() -> None:
    env = _Environment()
    line = next(row for row in env.records["account.move.line"] if row["id"] == 302)
    move = next(row for row in env.records["account.move"] if row["id"] == 98)
    partner = next(row for row in env.records["res.partner"] if row["id"] == 10)
    line.update(
        parent_state="draft",
        move_name=False,
        ref=False,
        name=False,
        invoice_date=False,
        date_maturity=False,
        matching_number=False,
    )
    move.update(name=False, state="draft", ref=False, invoice_date=False)
    partner["name"] = False

    result = _dispatch(
        env,
        _payload(
            filters=_filters(states=["draft"], account_kinds=["payable"])
        ),
    )

    item = result["rows"][0]
    assert item["state"] == "draft"
    assert item["move"]["name"] is None
    assert item["move"]["ref"] is None
    assert item["label"] is None
    assert item["invoice_date"] is None
    assert item["date_maturity"] is None
    assert item["partner"]["name"] is None
    assert item["matching_number"] is None


def test_absent_partner_and_reconciliation_model_are_preserved_as_null() -> None:
    env = _Environment()
    line = next(row for row in env.records["account.move.line"] if row["id"] == 302)
    line.update(partner_id=False, reconcile_model_id=False)

    item = _dispatch(
        env,
        _payload(filters=_filters(account_kinds=["payable"])),
    )["rows"][0]

    assert item["partner"] is None
    assert item["reconciliation_model"] is None
    assert not _search_calls(env, "res.partner")
    assert not _search_calls(env, "account.reconcile.model")


def test_slash_and_nonempty_whitespace_text_are_never_normalized() -> None:
    env = _Environment()
    line = next(row for row in env.records["account.move.line"] if row["id"] == 303)
    move = next(row for row in env.records["account.move"] if row["id"] == 99)
    account = next(row for row in env.records["account.account"] if row["id"] == 103)
    journal = next(row for row in env.records["account.journal"] if row["id"] == 8)
    reconcile_model = env.records["account.reconcile.model"][0]
    line["move_name"] = "/"
    move["name"] = "/"
    account.update(code="A.1", name=" ")
    journal.update(code=" ", name=" ")
    reconcile_model["name"] = " "

    item = _dispatch(
        env, _payload(filters=_filters(account_kinds=["other"]))
    )["rows"][0]

    assert item["move"]["name"] == "/"
    assert item["account"]["code"] == "A.1"
    assert item["account"]["name"] == " "
    assert item["journal"]["code"] == " "
    assert item["journal"]["name"] == " "
    assert item["reconciliation_model"]["name"] == " "


def test_archived_historical_reconciliation_model_is_exactly_reread_in_target_company() -> None:
    env = _Environment()

    item = _dispatch(
        env, _payload(filters=_filters(account_kinds=["other"]))
    )["rows"][0]

    assert item["reconciliation_model"] == {"id": 50, "name": "Historical rule"}
    assert (
        "context",
        "account.reconcile.model",
        {"active_test": False, "allowed_company_ids": [7]},
    ) in env.calls
    assert _search_calls(env, "account.reconcile.model")[0][2] == [
        ("id", "in", [50]),
        ("company_id", "=", 7),
    ]


def test_ancestor_or_other_company_reconciliation_model_is_rejected() -> None:
    for company_id in (1, 8):
        env = _Environment()
        env.records["account.reconcile.model"][0]["company_id"] = [company_id, "Wrong"]
        _assert_runtime_error(
            env, _payload(filters=_filters(account_kinds=["other"]))
        )


@pytest.mark.parametrize(
    "model",
    (
        "account.move",
        "account.journal",
        "res.partner",
        "res.currency",
        "account.reconcile.model",
    ),
)
def test_missing_related_record_fails_closed(model: str) -> None:
    env = _Environment()
    env.records[model] = []
    _assert_runtime_error(env)


@pytest.mark.parametrize(
    ("raw_field", "bad_value"),
    (
        ("parent_state", "draft"),
        ("move_name", "OTHER/NAME"),
        ("ref", "OTHER-REF"),
        ("date", "2025-01-26"),
        ("invoice_date", "2025-01-24"),
        ("journal_id", [6, "Wrong"]),
        ("company_currency_id", [6, "CNY"]),
        ("company_id", [8, "Other"]),
    ),
)
def test_stored_related_move_provenance_mismatch_fails_closed(
    raw_field: str,
    bad_value: Any,
) -> None:
    env = _Environment()
    line = next(row for row in env.records["account.move.line"] if row["id"] == 303)
    line[raw_field] = bad_value
    if raw_field in {"parent_state", "company_id"}:
        env.aml_domain_passthrough_fields.add(raw_field)
    _assert_runtime_error(
        env, _payload(filters=_filters(account_kinds=["other"]))
    )


def test_foreign_currency_may_have_zero_residual_currency_with_nonzero_company_residual() -> None:
    env = _Environment()
    line = next(row for row in env.records["account.move.line"] if row["id"] == 303)
    line.update(
        currency_id=[6, "CNY"],
        amount_currency=0.0,
        amount_residual_currency=0.0,
    )

    item = _dispatch(
        env, _payload(filters=_filters(account_kinds=["other"]))
    )["rows"][0]

    assert item["currency"] == {"id": 6, "code": "CNY"}
    assert item["company_currency"] == {"id": 37, "code": "SGD"}
    assert item["balance"] == "50"
    assert item["amount_currency"] == "0"
    assert item["amount_residual"] == "50"
    assert item["amount_residual_currency"] == "0"


@pytest.mark.parametrize(
    ("field", "bad_value"),
    (
        ("balance", True),
        ("amount_currency", float("nan")),
        ("amount_residual", float("inf")),
        ("amount_residual", 0.0),
        ("amount_residual_currency", float("-inf")),
        ("reconciled", 0),
    ),
)
def test_malformed_amounts_and_boolean_provenance_fail_closed(
    field: str,
    bad_value: Any,
) -> None:
    env = _Environment()
    line = next(row for row in env.records["account.move.line"] if row["id"] == 303)
    line[field] = bad_value
    if field == "amount_residual" and bad_value == 0:
        env.aml_domain_passthrough_fields.add(field)
    _assert_runtime_error(
        env, _payload(filters=_filters(account_kinds=["other"]))
    )


def test_same_currency_amount_and_residual_equalities_are_enforced() -> None:
    for field, bad_value in (
        ("amount_currency", 49.0),
        ("amount_residual_currency", 49.0),
    ):
        env = _Environment()
        line = next(row for row in env.records["account.move.line"] if row["id"] == 303)
        line[field] = bad_value
        _assert_runtime_error(
            env, _payload(filters=_filters(account_kinds=["other"]))
        )


def test_model_selection_and_required_text_values_fail_closed() -> None:
    mutations = (
        ("account.move", 99, "move_type", "payment"),
        ("account.journal", 8, "type", "opening"),
        ("account.account", 103, "account_type", "bank"),
        ("account.account", 103, "code", "BAD CODE"),
        ("account.account", 103, "code", "BAD-CODE"),
        ("account.account", 103, "code", "A/B"),
        ("account.account", 103, "code", "A" * 65),
        ("account.account", 103, "name", False),
        ("account.journal", 8, "code", "TOO-LONG"),
        ("res.currency", 37, "name", "TOOLONG"),
        ("account.reconcile.model", 50, "name", False),
    )
    for model, record_id, field, bad_value in mutations:
        env = _Environment()
        row = next(row for row in env.records[model] if row["id"] == record_id)
        row[field] = bad_value
        _assert_runtime_error(
            env, _payload(filters=_filters(account_kinds=["other"]))
        )


def test_returned_rows_must_be_unique_and_strictly_descending() -> None:
    duplicate = _Environment()
    duplicate.records["account.move.line"].append(
        copy.deepcopy(duplicate.records["account.move.line"][0])
    )
    _assert_runtime_error(duplicate)

    unordered = _Environment()
    unordered.records["account.move.line"] = list(
        reversed(unordered.records["account.move.line"])
    )
    unordered.preserve_aml_order = True
    _assert_runtime_error(unordered)


@pytest.mark.parametrize("parent_path", (False, "", "1/7", "1/x/7/"))
def test_malformed_or_wrong_root_company_paths_fail_closed(parent_path: Any) -> None:
    env = _Environment()
    target = next(row for row in env.records["res.company"] if row["id"] == 7)
    target["parent_path"] = parent_path
    _assert_runtime_error(env)


def test_parent_path_preserves_ancestor_order_without_assuming_monotonic_ids() -> None:
    env = _Environment()
    target = next(row for row in env.records["res.company"] if row["id"] == 7)
    target["parent_path"] = "8/7/"

    result = _dispatch(env)

    assert [row["id"] for row in result["rows"]] == [302]
    account_call = _search_calls(env, "account.account")[0]
    assert ("company_ids", "in", [8, 7]) in account_call[2]


def test_main_search_never_uses_sudo_and_keeps_target_company_only_context() -> None:
    env = _Environment()

    _dispatch(env)

    assert env.su is False
    contexts = [call for call in env.calls if call[0] == "context"]
    assert contexts
    assert all(call[2]["allowed_company_ids"] == [7] for call in contexts)
    assert all(call[2]["active_test"] is False for call in contexts)


def test_fixed_selection_catalogs_are_exhaustive() -> None:
    assert len(ACCOUNT_TYPES) == 19
    assert MOVE_TYPES == {
        "entry",
        "out_invoice",
        "out_refund",
        "in_invoice",
        "in_refund",
        "out_receipt",
        "in_receipt",
    }
    assert JOURNAL_TYPES == {"sale", "purchase", "cash", "bank", "credit", "general"}
