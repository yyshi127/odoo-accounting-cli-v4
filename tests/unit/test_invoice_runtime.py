from __future__ import annotations

import copy
import io
import json
import sys
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge import runtime
from odoo_accounting_cli_v4.bridge.runtime import RuntimeFailure

SEARCH_ACTION = "account.move.invoice.search_page"
GET_ACTION = "account.move.invoice.get"
STATUS_ACTION = "account.move.invoice.payment_status.inspect"
DOCUMENT_TYPES = ["out_invoice", "out_refund", "in_invoice", "in_refund"]
INVOICE_LINE_TYPES = ["product", "line_section", "line_subsection", "line_note"]

HEADER_FIELDS = [
    "id",
    "name",
    "move_type",
    "state",
    "date",
    "invoice_date",
    "invoice_date_due",
    "ref",
    "payment_reference",
    "invoice_origin",
    "journal_id",
    "company_id",
    "currency_id",
    "partner_id",
    "amount_untaxed",
    "amount_tax",
    "amount_total",
    "amount_residual",
    "payment_state",
]
INVOICE_LINE_FIELDS = [
    "id",
    "move_id",
    "sequence",
    "display_type",
    "name",
    "product_id",
    "account_id",
    "quantity",
    "price_unit",
    "discount",
    "price_subtotal",
    "price_total",
    "tax_ids",
]
TERM_LINE_FIELDS = [
    "id",
    "move_id",
    "account_id",
    "date_maturity",
    "balance",
    "amount_currency",
    "amount_residual",
    "amount_residual_currency",
    "currency_id",
    "reconciled",
    "matching_number",
]
PARTIAL_FIELDS = [
    "id",
    "max_date",
    "amount",
    "debit_amount_currency",
    "credit_amount_currency",
    "debit_move_id",
    "credit_move_id",
    "exchange_move_id",
]
COUNTERPART_LINE_FIELDS = ["id", "move_id"]
OUTSTANDING_LINE_FIELDS = [
    "id",
    "move_id",
    "company_id",
    "account_id",
    "partner_id",
    "parent_state",
    "reconciled",
    "balance",
    "amount_residual",
    "amount_residual_currency",
    "date",
    "payment_id",
]
COUNTERPART_MOVE_FIELDS = [
    "id",
    "name",
    "move_type",
    "state",
    "date",
    "origin_payment_id",
]
PAYMENT_FIELDS = [
    "id",
    "name",
    "state",
    "date",
    "payment_type",
    "partner_type",
    "amount",
    "currency_id",
    "journal_id",
    "payment_method_line_id",
    "move_id",
    "is_reconciled",
    "is_matched",
]
STATUS_MOVE_FIELDS = [
    "id",
    "name",
    "move_type",
    "state",
    "payment_state",
    "company_id",
    "commercial_partner_id",
    "currency_id",
    "company_currency_id",
    "amount_total",
    "amount_residual",
    "matched_payment_ids",
    "invoice_outstanding_credits_debits_widget",
]

SEARCH_MODELS = {
    "res.company",
    "account.move",
    "account.move.line",
    "account.journal",
    "res.currency",
    "res.partner",
}
GET_MODELS = SEARCH_MODELS | {"account.account", "account.tax", "product.product"}
STATUS_MODELS = SEARCH_MODELS | {
    "account.account",
    "account.partial.reconcile",
    "account.payment",
    "account.payment.method",
    "account.payment.method.line",
}


def _filters(**overrides: Any) -> dict[str, Any]:
    value = {
        "date_from": None,
        "date_to": None,
        "document_types": [],
        "states": [],
        "payment_states": [],
        "journal_id": None,
        "partner_id": None,
        "query": None,
    }
    value.update(overrides)
    return value


def _payload(action: str) -> dict[str, Any]:
    if action == SEARCH_ACTION:
        return {"company_id": 7, "after": None, "limit": 3, "filters": _filters()}
    return {"company_id": 7, "move_id": 99}


def _bridge_request(action: str, payload: dict[str, Any]) -> str:
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


@pytest.fixture(autouse=True)
def _fake_odoo_expression(monkeypatch: pytest.MonkeyPatch) -> None:
    def and_domains(domains: list[list[Any]]) -> list[Any]:
        nonempty = [domain for domain in domains if domain]
        result: list[Any] = ["&"] * max(0, len(nonempty) - 1)
        for domain in nonempty:
            result.extend(domain)
        return result

    odoo = ModuleType("odoo")
    odoo.__path__ = []  # type: ignore[attr-defined]
    osv = ModuleType("odoo.osv")
    osv.expression = SimpleNamespace(AND=and_domains)  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "odoo", odoo)
    monkeypatch.setitem(sys.modules, "odoo.osv", osv)


class _Model:
    def __init__(
        self,
        name: str,
        calls: list[tuple[Any, ...]],
        responses: list[list[dict[str, Any]]] | None = None,
        *,
        access_allowed: bool = True,
    ) -> None:
        self.name = name
        self.calls = calls
        self.responses = copy.deepcopy(responses or [])
        self.access_allowed = access_allowed

    def has_access(self, operation: str) -> bool:
        self.calls.append(("access", self.name, operation))
        return self.access_allowed

    def with_context(self, **context: Any):
        self.calls.append(("context", self.name, context))
        return self

    def sudo(self, *args: Any, **kwargs: Any):
        raise AssertionError(f"invoice bridge must never sudo {self.name}")

    def search_read(
        self,
        domain: list[Any],
        *,
        fields: list[str],
        limit: int | None = None,
        order: str | None = None,
    ) -> list[dict[str, Any]]:
        self.calls.append(("search", self.name, domain, fields, limit, order))
        if not self.responses:
            raise AssertionError(f"unexpected extra read of {self.name}: {domain!r}")
        return copy.deepcopy(self.responses.pop(0))


class _Companies:
    def __init__(
        self,
        calls: list[tuple[Any, ...]],
        *,
        visible: bool,
        access_allowed: bool,
    ) -> None:
        self.calls = calls
        self.visible = visible
        self.access_allowed = access_allowed

    def has_access(self, operation: str) -> bool:
        self.calls.append(("access", "res.company", operation))
        return self.access_allowed

    def search_count(self, domain: list[Any], *, limit: int) -> int:
        self.calls.append(("company", domain, limit))
        return int(self.visible)

    def sudo(self, *args: Any, **kwargs: Any):
        raise AssertionError("invoice bridge must never sudo res.company")


class _Registry:
    def __init__(
        self,
        calls: list[tuple[Any, ...]],
        models: dict[str, Any],
        *,
        missing_model: str | None,
    ) -> None:
        self.calls = calls
        self.models = models
        self.missing_model = missing_model

    def get(self, model: str):
        self.calls.append(("registry", model))
        if model == self.missing_model:
            return None
        return self.models.get(model)


def _raw_header() -> dict[str, Any]:
    return {
        "id": 99,
        "name": "INV/2025/0099",
        "move_type": "out_invoice",
        "state": "posted",
        "date": "2025-01-20",
        "invoice_date": "2025-01-20",
        "invoice_date_due": "2025-02-20",
        "ref": "ODACV4-FX1-CN-INVOICE-TAX-EXCLUDED",
        "payment_reference": "INV/2025/0099",
        "invoice_origin": False,
        "journal_id": [8, "INV Sales"],
        "company_id": [7, "Fixture Company"],
        "currency_id": [6, "CNY"],
        "partner_id": [9, "display value must not leak"],
        "amount_untaxed": 100.0,
        "amount_tax": 13.0,
        "amount_total": 113.0,
        "amount_residual": 63.0,
        "payment_state": "partial",
    }


def _header() -> dict[str, Any]:
    return {
        "id": 99,
        "name": "INV/2025/0099",
        "move_type": "out_invoice",
        "state": "posted",
        "date": "2025-01-20",
        "invoice_date": "2025-01-20",
        "invoice_date_due": "2025-02-20",
        "ref": "ODACV4-FX1-CN-INVOICE-TAX-EXCLUDED",
        "payment_reference": "INV/2025/0099",
        "invoice_origin": None,
        "journal": {"id": 8, "code": "INV", "name": "Sales"},
        "company_id": 7,
        "currency": {"id": 6, "code": "CNY"},
        "partner": {"id": 9, "name": "Fixture Customer"},
        "amount_untaxed": "100",
        "amount_tax": "13",
        "amount_total": "113",
        "amount_residual": "63",
        "payment_state": "partial",
    }


def _responses(
    mode: str, *, present: bool = True
) -> dict[str, list[list[dict[str, Any]]]]:
    base: dict[str, list[list[dict[str, Any]]]] = {
        "account.move": [[_raw_header()] if present else []],
        "account.move.line": [],
        "account.journal": [[{"id": 8, "code": "INV", "name": "Sales"}]],
        "res.currency": [[{"id": 6, "name": "CNY"}]],
        "res.partner": [[{"id": 9, "complete_name": "Fixture Customer"}]],
        "account.account": [],
        "account.tax": [],
        "product.product": [],
        "account.partial.reconcile": [],
        "account.payment": [],
        "account.payment.method": [],
        "account.payment.method.line": [],
    }
    if not present:
        for model in base:
            if model != "account.move":
                base[model] = []
        return base
    if mode == "get":
        base["account.move.line"] = [
            [
                {
                    "id": 301,
                    "move_id": [99, "INV/2025/0099"],
                    "sequence": 100,
                    "display_type": "product",
                    "name": "Fixture service",
                    "product_id": [11, "display value must not leak"],
                    "account_id": [101, "display value must not leak"],
                    "quantity": 1.0,
                    "price_unit": 100.0,
                    "discount": 0.0,
                    "price_subtotal": 100.0,
                    "price_total": 113.0,
                    "tax_ids": [4],
                }
            ]
        ]
        base["account.account"] = [[{"id": 101, "code": "6000", "name": "Sales"}]]
        base["account.tax"] = [
            [
                {
                    "id": 4,
                    "name": "Tax 13%",
                    "type_tax_use": "sale",
                    "amount_type": "percent",
                    "amount": 13.0,
                    "price_include": False,
                }
            ]
        ]
        base["product.product"] = [[{"id": 11, "display_name": "Consulting"}]]
    elif mode == "status":
        status_move = {
            key: value
            for key, value in _raw_header().items()
            if key
            in {
                "id",
                "name",
                "move_type",
                "state",
                "payment_state",
                "company_id",
                "currency_id",
                "amount_total",
                "amount_residual",
            }
        }
        status_move["company_currency_id"] = [37, "SGD"]
        status_move["commercial_partner_id"] = [9, "Fixture Customer"]
        status_move["matched_payment_ids"] = [5]
        status_move["invoice_outstanding_credits_debits_widget"] = {
            "outstanding": True,
            "content": [
                {
                    "journal_name": "BNK1/2025/0060",
                    "amount": 20.0,
                    "currency_id": 6,
                    "id": 602,
                    "move_id": 60,
                    "date": "2025-01-27",
                    "account_payment_id": 6,
                }
            ],
            "move_id": 99,
            "title": "Outstanding credits",
        }
        counterpart_move = {
            "id": 40,
            "name": "BNK1/2025/0040",
            "move_type": "entry",
            "state": "posted",
            "date": "2025-01-25",
            "origin_payment_id": [5, "BNK1/2025/0040"],
        }
        base["account.move"] = [[status_move], [counterpart_move]]
        base["account.move.line"] = [
            [
                {
                    "id": 302,
                    "move_id": [99, "INV/2025/0099"],
                    "account_id": [102, "display value must not leak"],
                    "date_maturity": "2025-02-20",
                    "balance": 152.55,
                    "amount_currency": 113.0,
                    "amount_residual": 85.05,
                    "amount_residual_currency": 63.0,
                    "currency_id": [6, "CNY"],
                    "reconciled": False,
                    "matching_number": "P",
                }
            ],
            [
                {
                    "id": 602,
                    "move_id": [60, "BNK1/2025/0060"],
                    "company_id": [7, "Fixture Company"],
                    "account_id": [102, "Accounts Receivable"],
                    "partner_id": [9, "Fixture Customer"],
                    "parent_state": "posted",
                    "reconciled": False,
                    "balance": -27.0,
                    "amount_residual": -27.0,
                    "amount_residual_currency": -20.0,
                    "date": "2025-01-27",
                    "payment_id": [6, "BNK1/2025/0060"],
                }
            ],
            [{"id": 402, "move_id": [40, "BNK1/2025/0040"]}],
        ]
        base["account.account"] = [
            [
                {
                    "id": 102,
                    "code": "1100",
                    "name": "Accounts Receivable",
                    "account_type": "asset_receivable",
                }
            ]
        ]
        base["account.partial.reconcile"] = [
            [
                {
                    "id": 501,
                    "max_date": "2025-01-25",
                    "amount": 67.5,
                    "debit_amount_currency": 50.0,
                    "credit_amount_currency": 67.5,
                    "debit_move_id": [302, "INV/2025/0099"],
                    "credit_move_id": [402, "BNK1/2025/0040"],
                    "exchange_move_id": False,
                }
            ]
        ]
        base["account.payment"] = [
            [
                {
                    "id": 5,
                    "name": "BNK1/2025/0040",
                    "state": "in_process",
                    "date": "2025-01-25",
                    "payment_type": "inbound",
                    "partner_type": "customer",
                    "amount": 50.0,
                    "currency_id": [6, "CNY"],
                    "journal_id": [10, "BNK1 Bank"],
                    "payment_method_line_id": [55, "Manual"],
                    "move_id": [40, "BNK1/2025/0040"],
                    "is_reconciled": True,
                    "is_matched": False,
                }
            ]
        ]
        base["account.payment.method.line"] = [
            [
                {
                    "id": 55,
                    "payment_method_id": [3, "display value must not leak"],
                }
            ]
        ]
        base["account.payment.method"] = [
            [
                {
                    "id": 3,
                    "code": "manual",
                    "name": "Manual Payment",
                }
            ]
        ]
        base["account.journal"] = [[{"id": 10, "code": "BNK1", "name": "Bank"}]]
        base["res.currency"] = [
            [
                {"id": 6, "name": "CNY"},
                {"id": 37, "name": "SGD"},
            ]
        ]
        base["res.partner"] = []
    return base


class _Environment:
    uid = 42

    def __init__(
        self,
        mode: str,
        *,
        present: bool = True,
        company_visible: bool = True,
        missing_model: str | None = None,
        denied_model: str | None = None,
    ) -> None:
        self.calls: list[tuple[Any, ...]] = []
        responses = _responses(mode, present=present)
        self.models: dict[str, Any] = {
            "res.company": _Companies(
                self.calls,
                visible=company_visible,
                access_allowed=denied_model != "res.company",
            )
        }
        for model_name, model_responses in responses.items():
            self.models[model_name] = _Model(
                model_name,
                self.calls,
                model_responses,
                access_allowed=model_name != denied_model,
            )
        self.registry = _Registry(self.calls, self.models, missing_model=missing_model)

    def __getitem__(self, model: str):
        self.calls.append(("model", model))
        if model not in self.models:
            raise AssertionError(f"unexpected generic model access: {model}")
        return self.models[model]


def _search_calls(env: _Environment, model: str) -> list[tuple[Any, ...]]:
    return [call for call in env.calls if call[:2] == ("search", model)]


def _assert_related_read(
    env: _Environment,
    model: str,
    ids: list[int],
    fields: list[str],
    *,
    call_index: int = 0,
) -> None:
    call = _search_calls(env, model)[call_index]
    assert call[2:] == (
        [("id", "in", ids)],
        ["id", *fields],
        len(ids),
        "id",
    )


def _use_bank_outstanding_candidate(
    env: _Environment,
    *,
    account_type: Any = "asset_cash",
    balance: float = 27.0,
) -> dict[str, Any]:
    candidate = env.models["account.move.line"].responses[1][0]
    candidate.update(
        account_id=[103, "Bank"],
        balance=balance,
        amount_residual=balance,
        amount_residual_currency=20.0 if balance >= 0 else -20.0,
    )
    env.models["account.account"].responses.append(
        [{"id": 103, "account_type": account_type}]
    )
    return candidate


def test_decode_accepts_only_the_three_fixed_invoice_actions() -> None:
    for action in (SEARCH_ACTION, GET_ACTION, STATUS_ACTION):
        assert (
            runtime._decode_request(
                io.StringIO(_bridge_request(action, _payload(action)))
            )["action"]
            == action
        )


def test_search_uses_exact_scope_filters_cursor_order_and_related_reads() -> None:
    env = _Environment("search")
    payload = {
        "company_id": 7,
        "after": ["2025-01-21", 100],
        "limit": 3,
        "filters": _filters(
            date_from="2025-01-01",
            date_to="2025-01-31",
            document_types=["out_invoice", "in_invoice"],
            states=["posted", "cancel"],
            payment_states=["not_paid", "partial"],
            journal_id=8,
            partner_id=9,
            query="needle",
        ),
    }

    result = runtime._dispatch(env, SEARCH_ACTION, payload, 7)

    assert result == {
        "user_id": 42,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "rows": [_header()],
    }
    move_call = _search_calls(env, "account.move")[0]
    assert move_call[3:] == (HEADER_FIELDS, 3, "date desc,id desc")
    domain = move_call[2]
    for term in (
        ("company_id", "=", 7),
        ("move_type", "in", ["out_invoice", "in_invoice"]),
        ("date", ">=", "2025-01-01"),
        ("date", "<=", "2025-01-31"),
        ("state", "in", ["posted", "cancel"]),
        ("payment_state", "in", ["not_paid", "partial"]),
        ("journal_id", "=", 8),
        ("partner_id", "=", 9),
        ("name", "ilike", "needle"),
        ("ref", "ilike", "needle"),
        ("payment_reference", "ilike", "needle"),
        ("invoice_origin", "ilike", "needle"),
        ("date", "<", "2025-01-21"),
        ("date", "=", "2025-01-21"),
        ("id", "<", 100),
    ):
        assert term in domain
    query_terms = [
        "|",
        "|",
        "|",
        ("name", "ilike", "needle"),
        ("ref", "ilike", "needle"),
        ("payment_reference", "ilike", "needle"),
        ("invoice_origin", "ilike", "needle"),
    ]
    assert any(
        domain[index : index + len(query_terms)] == query_terms
        for index in range(len(domain) - len(query_terms) + 1)
    )
    assert domain[-5:] == [
        "|",
        ("date", "<", "2025-01-21"),
        "&",
        ("date", "=", "2025-01-21"),
        ("id", "<", 100),
    ]
    _assert_related_read(env, "account.journal", [8], ["code", "name"])
    _assert_related_read(env, "res.currency", [6], ["name"])
    _assert_related_read(env, "res.partner", [9], ["complete_name"])


def test_get_reads_only_invoice_line_subset_and_exact_related_records() -> None:
    env = _Environment("get")

    result = runtime._dispatch(env, GET_ACTION, _payload(GET_ACTION), 7)

    expected_line = {
        "id": 301,
        "sequence": 100,
        "display_type": "product",
        "name": "Fixture service",
        "product": {"id": 11, "name": "Consulting"},
        "account": {"id": 101, "code": "6000", "name": "Sales"},
        "quantity": "1",
        "price_unit": "100",
        "discount": "0",
        "price_subtotal": "100",
        "price_total": "113",
        "taxes": [
            {
                "id": 4,
                "name": "Tax 13%",
                "type_tax_use": "sale",
                "amount_type": "percent",
                "amount": "13",
                "price_include": False,
            }
        ],
    }
    assert result == {
        "user_id": 42,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "invoice": {**_header(), "lines": [expected_line]},
    }
    move_call = _search_calls(env, "account.move")[0]
    assert move_call[2] == [
        ("id", "=", 99),
        ("company_id", "=", 7),
        ("move_type", "in", DOCUMENT_TYPES),
    ]
    assert move_call[3] == HEADER_FIELDS
    assert move_call[4] == 1
    line_call = _search_calls(env, "account.move.line")[0]
    assert line_call[2] == [
        ("move_id", "=", 99),
        ("display_type", "in", INVOICE_LINE_TYPES),
    ]
    assert line_call[3] == INVOICE_LINE_FIELDS
    assert line_call[5] == "sequence,id"
    _assert_related_read(env, "account.account", [101], ["code", "name"])
    _assert_related_read(
        env,
        "account.tax",
        [4],
        ["name", "type_tax_use", "amount_type", "amount", "price_include"],
    )
    _assert_related_read(env, "product.product", [11], ["display_name"])


def test_payment_status_traverses_explicit_partial_reconcile_and_origin_payment() -> (
    None
):
    env = _Environment("status")

    result = runtime._dispatch(env, STATUS_ACTION, _payload(STATUS_ACTION), 7)

    assert result == {
        "user_id": 42,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "payment_status": {
            "id": 99,
            "name": "INV/2025/0099",
            "move_type": "out_invoice",
            "state": "posted",
            "payment_state": "partial",
            "company_id": 7,
            "currency": {"id": 6, "code": "CNY"},
            "company_currency": {"id": 37, "code": "SGD"},
            "amount_total": "113",
            "amount_residual": "63",
            "receivable_payable_lines": [
                {
                    "id": 302,
                    "account": {
                        "id": 102,
                        "code": "1100",
                        "name": "Accounts Receivable",
                        "account_type": "asset_receivable",
                    },
                    "date_maturity": "2025-02-20",
                    "balance": "152.55",
                    "amount_currency": "113",
                    "amount_residual": "85.05",
                    "amount_residual_currency": "63",
                    "currency": {"id": 6, "code": "CNY"},
                    "reconciled": False,
                    "matching_number": "P",
                }
            ],
            "reconciliations": [
                {
                    "id": 501,
                    "date": "2025-01-25",
                    "amount": "50",
                    "company_amount": "67.5",
                    "currency": {"id": 6, "code": "CNY"},
                    "company_currency": {"id": 37, "code": "SGD"},
                    "invoice_line_id": 302,
                    "counterpart_line_id": 402,
                    "counterpart_move": {
                        "id": 40,
                        "name": "BNK1/2025/0040",
                        "move_type": "entry",
                        "state": "posted",
                        "date": "2025-01-25",
                    },
                    "payment_id": 5,
                    "exchange_move_id": None,
                }
            ],
            "payments": [
                {
                    "id": 5,
                    "name": "BNK1/2025/0040",
                    "state": "in_process",
                    "date": "2025-01-25",
                    "payment_type": "inbound",
                    "partner_type": "customer",
                    "amount": "50",
                    "currency": {"id": 6, "code": "CNY"},
                    "journal": {"id": 10, "code": "BNK1", "name": "Bank"},
                    "payment_method": {
                        "id": 3,
                        "code": "manual",
                        "name": "Manual Payment",
                    },
                    "move_id": 40,
                    "is_reconciled": True,
                    "is_matched": False,
                }
            ],
            "outstanding_items": [
                {
                    "line_id": 602,
                    "move_id": 60,
                    "payment_id": 6,
                    "date": "2025-01-27",
                    "label": "BNK1/2025/0060",
                    "amount": "20",
                    "currency": {"id": 6, "code": "CNY"},
                }
            ],
        },
    }
    move_calls = _search_calls(env, "account.move")
    assert move_calls[0][2] == [
        ("id", "=", 99),
        ("company_id", "=", 7),
        ("move_type", "in", DOCUMENT_TYPES),
    ]
    assert move_calls[0][3] == STATUS_MOVE_FIELDS
    term_call, outstanding_call, counterpart_line_call = _search_calls(
        env, "account.move.line"
    )
    assert term_call[2:] == (
        [
            ("move_id", "=", 99),
            (
                "account_id.account_type",
                "in",
                ["asset_receivable", "liability_payable"],
            ),
        ],
        TERM_LINE_FIELDS,
        None,
        "id",
    )
    assert outstanding_call[2:] == (
        [("id", "in", [602]), ("company_id", "=", 7)],
        OUTSTANDING_LINE_FIELDS,
        1,
        "id",
    )
    partial_call = _search_calls(env, "account.partial.reconcile")[0]
    assert partial_call[2:] == (
        [
            "|",
            ("debit_move_id", "in", [302]),
            ("credit_move_id", "in", [302]),
        ],
        PARTIAL_FIELDS,
        None,
        "max_date,id",
    )
    assert counterpart_line_call[2:] == (
        [("id", "in", [402])],
        COUNTERPART_LINE_FIELDS,
        1,
        "id",
    )
    assert move_calls[1][2:] == (
        [("id", "in", [40]), ("company_id", "=", 7)],
        COUNTERPART_MOVE_FIELDS,
        1,
        "id",
    )
    payment_call = _search_calls(env, "account.payment")[0]
    assert payment_call[2:] == (
        [("id", "in", [5]), ("company_id", "=", 7)],
        PAYMENT_FIELDS,
        1,
        "date desc,id desc",
    )
    _assert_related_read(
        env, "account.account", [102], ["code", "name", "account_type"]
    )
    assert len(_search_calls(env, "account.account")) == 1
    _assert_related_read(
        env, "account.payment.method.line", [55], ["payment_method_id"]
    )
    _assert_related_read(env, "account.payment.method", [3], ["code", "name"])


@pytest.mark.parametrize("bank_label", (False, None, "Bank statement label"))
def test_payment_status_accepts_optional_bank_label_without_exposing_it(
    bank_label: Any,
) -> None:
    env = _Environment("status")
    widget_item = env.models["account.move"].responses[0][0][
        "invoice_outstanding_credits_debits_widget"
    ]["content"][0]
    widget_item["bank_label"] = bank_label

    result = runtime._dispatch(env, STATUS_ACTION, _payload(STATUS_ACTION), 7)

    assert result["payment_status"]["outstanding_items"] == [
        {
            "line_id": 602,
            "move_id": 60,
            "payment_id": 6,
            "date": "2025-01-27",
            "label": "BNK1/2025/0060",
            "amount": "20",
            "currency": {"id": 6, "code": "CNY"},
        }
    ]


def test_payment_status_accepts_scoped_cash_account_bank_candidate() -> None:
    env = _Environment("status")
    _use_bank_outstanding_candidate(env)

    result = runtime._dispatch(env, STATUS_ACTION, _payload(STATUS_ACTION), 7)

    assert result["payment_status"]["outstanding_items"] == [
        {
            "line_id": 602,
            "move_id": 60,
            "payment_id": 6,
            "date": "2025-01-27",
            "label": "BNK1/2025/0060",
            "amount": "20",
            "currency": {"id": 6, "code": "CNY"},
        }
    ]
    _assert_related_read(env, "account.account", [103], ["account_type"], call_index=1)
    assert (
        "context",
        "account.account",
        {"active_test": False, "allowed_company_ids": [7]},
    ) in env.calls


@pytest.mark.parametrize("account_type", ("asset_current", False, None))
def test_payment_status_rejects_non_cash_bank_candidate_account_type(
    account_type: Any,
) -> None:
    env = _Environment("status")
    _use_bank_outstanding_candidate(env, account_type=account_type)

    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(env, STATUS_ACTION, _payload(STATUS_ACTION), 7)

    assert caught.value.code == "odoo_runtime_error"


def test_payment_status_rejects_opposite_sign_cash_account_candidate() -> None:
    env = _Environment("status")
    _use_bank_outstanding_candidate(env, balance=-27.0)

    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(env, STATUS_ACTION, _payload(STATUS_ACTION), 7)

    assert caught.value.code == "odoo_runtime_error"


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("company_id", [8, "Other Company"]),
        ("partner_id", [10, "Other Partner"]),
        ("parent_state", "draft"),
        ("reconciled", True),
        ("balance", 0.0),
        ("date", "2025-01-28"),
        ("move_id", [61, "Other Move"]),
        ("payment_id", [7, "Other Payment"]),
    ),
)
def test_payment_status_rejects_out_of_scope_bank_candidate_line(
    field: str, value: Any
) -> None:
    env = _Environment("status")
    candidate = _use_bank_outstanding_candidate(env)
    candidate[field] = value

    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(env, STATUS_ACTION, _payload(STATUS_ACTION), 7)

    assert caught.value.code == "odoo_runtime_error"


def test_payment_status_rejects_zero_residual_bank_candidate_line() -> None:
    env = _Environment("status")
    candidate = _use_bank_outstanding_candidate(env)
    candidate["amount_residual"] = 0.0
    candidate["amount_residual_currency"] = 0.0

    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(env, STATUS_ACTION, _payload(STATUS_ACTION), 7)

    assert caught.value.code == "odoo_runtime_error"


def test_payment_status_rejects_unknown_outstanding_widget_item_field() -> None:
    env = _Environment("status")
    widget_item = env.models["account.move"].responses[0][0][
        "invoice_outstanding_credits_debits_widget"
    ]["content"][0]
    widget_item["unknown"] = "unexpected"

    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(env, STATUS_ACTION, _payload(STATUS_ACTION), 7)

    assert caught.value.code == "odoo_runtime_error"


@pytest.mark.parametrize("bank_label", (True, 0, "", "   ", []))
def test_payment_status_rejects_invalid_optional_bank_label(bank_label: Any) -> None:
    env = _Environment("status")
    widget_item = env.models["account.move"].responses[0][0][
        "invoice_outstanding_credits_debits_widget"
    ]["content"][0]
    widget_item["bank_label"] = bank_label

    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(env, STATUS_ACTION, _payload(STATUS_ACTION), 7)

    assert caught.value.code == "odoo_runtime_error"


def test_payment_status_returns_empty_outstanding_items_for_false_widget() -> None:
    env = _Environment("status")
    move = env.models["account.move"].responses[0][0]
    move["invoice_outstanding_credits_debits_widget"] = False
    line_responses = env.models["account.move.line"].responses
    env.models["account.move.line"].responses = [line_responses[0], line_responses[2]]

    result = runtime._dispatch(env, STATUS_ACTION, _payload(STATUS_ACTION), 7)

    assert result["payment_status"]["outstanding_items"] == []


def test_payment_status_sorts_outstanding_items_by_date_and_line_desc() -> None:
    env = _Environment("status")
    widget = env.models["account.move"].responses[0][0][
        "invoice_outstanding_credits_debits_widget"
    ]
    second_item = copy.deepcopy(widget["content"][0])
    second_item.update(
        id=603,
        move_id=61,
        account_payment_id=7,
        journal_name="BNK1/2025/0061",
    )
    widget["content"].append(second_item)
    second_line = copy.deepcopy(env.models["account.move.line"].responses[1][0])
    second_line.update(
        id=603,
        move_id=[61, "BNK1/2025/0061"],
        payment_id=[7, "BNK1/2025/0061"],
    )
    env.models["account.move.line"].responses[1].append(second_line)

    result = runtime._dispatch(env, STATUS_ACTION, _payload(STATUS_ACTION), 7)

    assert [
        item["line_id"] for item in result["payment_status"]["outstanding_items"]
    ] == [603, 602]


def test_payment_status_rejects_malformed_outstanding_widget() -> None:
    env = _Environment("status")
    widget = env.models["account.move"].responses[0][0][
        "invoice_outstanding_credits_debits_widget"
    ]
    widget["content"][0]["amount"] = 0.0

    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(env, STATUS_ACTION, _payload(STATUS_ACTION), 7)

    assert caught.value.code == "odoo_runtime_error"


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("company_id", [8, "Other Company"]),
        ("account_id", [999, "Other Account"]),
        ("partner_id", [10, "Other Partner"]),
        ("parent_state", "draft"),
        ("reconciled", True),
        ("balance", 27.0),
        ("amount_residual", 0.0),
    ),
)
def test_payment_status_rejects_out_of_scope_outstanding_line(
    field: str, value: Any
) -> None:
    env = _Environment("status")
    candidate = env.models["account.move.line"].responses[1][0]
    candidate[field] = value
    if field == "account_id":
        env.models["account.account"].responses.append([])
    if field == "amount_residual":
        candidate["amount_residual_currency"] = 0.0

    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(env, STATUS_ACTION, _payload(STATUS_ACTION), 7)

    assert caught.value.code == "odoo_runtime_error"


def test_payment_status_includes_matched_payment_without_an_account_move() -> None:
    env = _Environment("status")
    status_move = env.models["account.move"].responses[0][0]
    status_move["payment_state"] = "in_payment"
    status_move["matched_payment_ids"] = [6]
    status_move["invoice_outstanding_credits_debits_widget"] = False
    env.models["account.partial.reconcile"].responses[0] = []
    env.models["account.move.line"].responses = [
        env.models["account.move.line"].responses[0]
    ]
    payment = env.models["account.payment"].responses[0][0]
    payment.update(id=6, name="Provider payment", move_id=False)

    result = runtime._dispatch(env, STATUS_ACTION, _payload(STATUS_ACTION), 7)

    assert result["payment_status"]["payment_state"] == "in_payment"
    assert result["payment_status"]["reconciliations"] == []
    assert result["payment_status"]["outstanding_items"] == []
    assert result["payment_status"]["payments"] == [
        {
            "id": 6,
            "name": "Provider payment",
            "state": "in_process",
            "date": "2025-01-25",
            "payment_type": "inbound",
            "partner_type": "customer",
            "amount": "50",
            "currency": {"id": 6, "code": "CNY"},
            "journal": {"id": 10, "code": "BNK1", "name": "Bank"},
            "payment_method": {
                "id": 3,
                "code": "manual",
                "name": "Manual Payment",
            },
            "move_id": None,
            "is_reconciled": True,
            "is_matched": False,
        }
    ]
    payment_call = _search_calls(env, "account.payment")[0]
    assert payment_call[2] == [("id", "in", [6]), ("company_id", "=", 7)]


def test_payment_status_uses_credit_side_invoice_currency_amount_when_term_is_credit() -> (
    None
):
    env = _Environment("status")
    move = env.models["account.move"].responses[0][0]
    move["move_type"] = "in_invoice"
    term = env.models["account.move.line"].responses[0][0]
    partial = env.models["account.partial.reconcile"].responses[0][0]
    partial.update(
        debit_amount_currency=77.0,
        credit_amount_currency=49.0,
        debit_move_id=[402, "BNK1/2025/0040"],
        credit_move_id=[term["id"], "BILL/2025/0099"],
    )
    account = env.models["account.account"].responses[0][0]
    account["account_type"] = "liability_payable"

    result = runtime._dispatch(env, STATUS_ACTION, _payload(STATUS_ACTION), 7)

    reconciliation = result["payment_status"]["reconciliations"][0]
    assert reconciliation["amount"] == "49"
    assert reconciliation["company_amount"] == "67.5"
    assert reconciliation["counterpart_line_id"] == 402


@pytest.mark.parametrize(
    ("action", "required_models", "empty_key"),
    (
        (SEARCH_ACTION, SEARCH_MODELS, "rows"),
        (GET_ACTION, GET_MODELS, "invoice"),
        (STATUS_ACTION, STATUS_MODELS, "payment_status"),
    ),
)
def test_company_module_and_every_required_acl_gate_precede_business_reads(
    action: str, required_models: set[str], empty_key: str
) -> None:
    for denied_model in sorted(required_models):
        env = _Environment(
            "search"
            if action == SEARCH_ACTION
            else "get"
            if action == GET_ACTION
            else "status",
            denied_model=denied_model,
        )
        result = runtime._dispatch(env, action, _payload(action), 7)
        assert result["company_visible"] is (denied_model != "res.company")
        assert result["module_installed"] is True
        assert result["access_allowed"] is False
        assert result[empty_key] == ([] if empty_key == "rows" else None)
        assert not _search_calls(env, "account.move")

    missing = min(required_models)
    env = _Environment(
        "search"
        if action == SEARCH_ACTION
        else "get"
        if action == GET_ACTION
        else "status",
        missing_model=missing,
    )
    result = runtime._dispatch(env, action, _payload(action), 7)
    assert result["company_visible"] is True
    assert result["module_installed"] is False
    assert result["access_allowed"] is False
    assert result[empty_key] == ([] if empty_key == "rows" else None)
    assert not _search_calls(env, "account.move")

    env = _Environment(
        "search"
        if action == SEARCH_ACTION
        else "get"
        if action == GET_ACTION
        else "status",
        company_visible=False,
    )
    result = runtime._dispatch(env, action, _payload(action), 7)
    assert result["company_visible"] is False
    assert result["access_allowed"] is False
    assert result[empty_key] == ([] if empty_key == "rows" else None)
    assert not _search_calls(env, "account.move")


@pytest.mark.parametrize("action", (GET_ACTION, STATUS_ACTION))
def test_missing_and_cross_company_records_are_runtime_indistinguishable(
    action: str,
) -> None:
    mode = "get" if action == GET_ACTION else "status"
    missing = runtime._dispatch(
        _Environment(mode, present=False),
        action,
        {"company_id": 7, "move_id": 2_147_483_647},
        7,
    )
    cross_company = runtime._dispatch(
        _Environment(mode, present=False),
        action,
        {"company_id": 7, "move_id": 888},
        7,
    )
    assert cross_company == missing
    empty_key = "invoice" if action == GET_ACTION else "payment_status"
    assert missing[empty_key] is None


@pytest.mark.parametrize(
    ("action", "payload"),
    (
        (SEARCH_ACTION, {"company_id": 7, "after": None, "limit": 3}),
        (
            SEARCH_ACTION,
            {
                "company_id": 7,
                "after": ["2025-1-1", 1],
                "limit": 3,
                "filters": _filters(),
            },
        ),
        (
            SEARCH_ACTION,
            {
                "company_id": 7,
                "after": None,
                "limit": 3,
                "filters": _filters(document_types=["entry"]),
            },
        ),
        (
            SEARCH_ACTION,
            {
                "company_id": 7,
                "after": None,
                "limit": 3,
                "filters": _filters(query=" untrimmed"),
            },
        ),
        (GET_ACTION, {"company_id": 7, "move_id": True}),
        (STATUS_ACTION, {"company_id": 7, "move_id": 0}),
    ),
)
def test_invoice_runtime_payloads_fail_closed(
    action: str, payload: dict[str, Any]
) -> None:
    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(_Environment("search"), action, payload, 7)
    assert caught.value.code == "bridge_protocol_error"
    assert caught.value.exit_code == 7


@pytest.mark.parametrize("action", (SEARCH_ACTION, GET_ACTION, STATUS_ACTION))
def test_invoice_company_mismatch_fails_before_model_access(action: str) -> None:
    payload = _payload(action)
    payload["company_id"] = 8
    env = _Environment("search")
    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(env, action, payload, 7)
    assert caught.value.code == "company_unavailable"
    assert caught.value.exit_code == 3
    assert not any(
        call[0] in {"company", "access", "context", "search"} for call in env.calls
    )


def test_unknown_invoice_action_fails_closed_without_any_model_access() -> None:
    class Environment:
        registry = object()

        def __getitem__(self, model: str):
            raise AssertionError(f"unknown action must not access {model}")

    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(
            Environment(),
            "account.move.invoice.arbitrary",
            {"company_id": 7, "move_id": 99},
            7,
        )
    assert caught.value.code == "bridge_protocol_error"
    assert caught.value.exit_code == 7
