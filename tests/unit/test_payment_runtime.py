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


SEARCH_ACTION = "account.payment.search_page"
GET_ACTION = "account.payment.get"
ACTIONS = (SEARCH_ACTION, GET_ACTION)

SEARCH_MODELS = {
    "res.company",
    "account.payment",
    "account.move",
    "account.journal",
    "res.currency",
    "res.partner",
    "account.payment.method.line",
    "account.payment.method",
}
GET_MODELS = SEARCH_MODELS | {
    "account.move.line",
    "account.account",
    "account.partial.reconcile",
}

PAYMENT_FIELDS = [
    "id",
    "name",
    "date",
    "state",
    "payment_type",
    "partner_type",
    "amount",
    "amount_signed",
    "amount_company_currency_signed",
    "currency_id",
    "company_currency_id",
    "company_id",
    "partner_id",
    "journal_id",
    "memo",
    "payment_reference",
    "payment_method_line_id",
    "move_id",
    "is_reconciled",
    "is_matched",
]
JOURNAL_FIELDS = ["id", "code", "name", "company_id"]
CURRENCY_FIELDS = ["id", "name"]
PARTNER_FIELDS = ["id", "name", "company_id"]
METHOD_LINE_FIELDS = [
    "id",
    "name",
    "journal_id",
    "payment_method_id",
]
METHOD_FIELDS = ["id", "code", "name", "payment_type"]
PAYMENT_MOVE_LINE_FIELDS = ["id", "move_id", "account_id", "company_id"]
ACCOUNT_FIELDS = ["id", "account_type", "reconcile"]
PARTIAL_FIELDS = [
    "id",
    "debit_move_id",
    "credit_move_id",
    "exchange_move_id",
    "company_id",
]
COUNTERPART_LINE_FIELDS = ["id", "move_id", "account_id", "company_id"]
MOVE_FIELDS = [
    "id",
    "name",
    "state",
    "date",
    "move_type",
    "payment_state",
    "company_id",
]
DOCUMENT_TYPES = [
    "out_invoice",
    "out_refund",
    "in_invoice",
    "in_refund",
    "out_receipt",
    "in_receipt",
]


def _filters(**overrides: Any) -> dict[str, Any]:
    value = {
        "date_from": None,
        "date_to": None,
        "states": [],
        "payment_types": [],
        "partner_types": [],
        "journal_id": None,
        "partner_id": None,
        "currency_id": None,
        "query": None,
    }
    value.update(overrides)
    return value


def _payload(action: str, **overrides: Any) -> dict[str, Any]:
    if action == SEARCH_ACTION:
        value = {
            "company_id": 7,
            "after": None,
            "limit": 3,
            "filters": _filters(),
        }
    else:
        value = {"company_id": 7, "payment_id": 5}
    value.update(overrides)
    return value


def _bridge_request(action: str, payload: dict[str, Any] | None = None) -> str:
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
            "payload": payload or _payload(action),
        }
    )


@pytest.fixture(autouse=True)
def _fake_odoo_expression(monkeypatch: pytest.MonkeyPatch) -> None:
    def combine(operator: str, domains: list[list[Any]]) -> list[Any]:
        nonempty = [list(domain) for domain in domains if domain]
        result: list[Any] = [operator] * max(0, len(nonempty) - 1)
        for domain in nonempty:
            result.extend(domain)
        return result

    odoo = ModuleType("odoo")
    odoo.__path__ = []  # type: ignore[attr-defined]
    fields = ModuleType("odoo.fields")
    fields.Domain = SimpleNamespace(  # type: ignore[attr-defined]
        AND=lambda domains: combine("&", domains),
    )
    osv = ModuleType("odoo.osv")
    osv.expression = SimpleNamespace(  # type: ignore[attr-defined]
        AND=lambda domains: combine("&", domains),
        OR=lambda domains: combine("|", domains),
    )
    monkeypatch.setitem(sys.modules, "odoo", odoo)
    monkeypatch.setitem(sys.modules, "odoo.fields", fields)
    monkeypatch.setitem(sys.modules, "odoo.osv", osv)


def _reference_id(value: Any) -> int | None:
    if value in (False, None):
        return None
    return value[0] if isinstance(value, (list, tuple)) else value


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
        self.env.calls.append(("context", self.name, context))
        self.context.update(context)
        return self

    def search_read(
        self,
        domain: list[Any],
        *,
        fields: list[str],
        limit: int | None = None,
        order: str | None = None,
    ) -> list[dict[str, Any]]:
        self.env.calls.append(
            ("search", self.name, copy.deepcopy(domain), list(fields), limit, order)
        )
        rows = self.env.respond(self.name, domain)
        if limit is not None:
            rows = rows[:limit]
        projected = [_project(row, fields) for row in rows]
        if self.name == "account.payment" and "invoice_ids" in fields:
            allowed_company_ids = set(self.context.get("allowed_company_ids", []))
            move_companies = {
                row["id"]: _reference_id(row["company_id"])
                for row in self.env.records["account.move"]
            }
            for row in projected:
                row["invoice_ids"] = [
                    record_id
                    for record_id in row["invoice_ids"]
                    if move_companies.get(record_id) in allowed_company_ids
                ]
        return projected

    def sudo(self, *args: Any, **kwargs: Any):
        raise AssertionError(f"payment bridge must never sudo {self.name}")


class _Companies(_Model):
    def search_count(self, domain: list[Any], *, limit: int) -> int:
        self.env.calls.append(("company", copy.deepcopy(domain), limit))
        return int(self.env.company_visible)


class _Registry:
    def __init__(self, env: "_Environment", missing_model: str | None) -> None:
        self.env = env
        self.missing_model = missing_model

    def get(self, model: str):
        self.env.calls.append(("registry", model))
        if model == self.missing_model:
            return None
        return self.env.models.get(model)


def _raw_payment(*, company_id: int = 7, get: bool = False) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": 5,
        "name": "PBNK1/2025/00005",
        "date": "2025-01-25",
        "state": "in_process",
        "payment_type": "outbound",
        "partner_type": "supplier",
        "amount": 125.5,
        "amount_signed": -125.5,
        "amount_company_currency_signed": -168.75,
        "currency_id": [6, "display value must not leak"],
        "company_currency_id": [37, "display value must not leak"],
        "company_id": [company_id, "Fixture Company"],
        "partner_id": [9, "display value must not leak"],
        "journal_id": [10, "display value must not leak"],
        "memo": False,
        "payment_reference": "WIRE-5",
        "payment_method_line_id": [55, "display value must not leak"],
        "move_id": [40, "display value must not leak"],
        "is_reconciled": True,
        "is_matched": False,
    }
    if get:
        row["invoice_ids"] = [91, 90]
    return row


def _records(*, get: bool) -> dict[str, list[dict[str, Any]]]:
    records: dict[str, list[dict[str, Any]]] = {
        "res.company": [{"id": 7, "parent_path": "7/"}],
        "account.payment": [_raw_payment(get=get)],
        "account.journal": [{
            "id": 10,
            "code": "BNK1",
            "name": "Bank",
            "company_id": [7, "Fixture Company"],
        }],
        "res.currency": [
            {"id": 6, "name": "CNY"},
            {"id": 37, "name": "SGD"},
        ],
        "res.partner": [{
            "id": 9,
            "name": "Fixture Vendor",
            "company_id": False,
        }],
        "account.payment.method.line": [{
            "id": 55,
            "name": "Manual (Bank)",
            "journal_id": [10, "display value must not leak"],
            "payment_method_id": [3, "display value must not leak"],
        }],
        "account.payment.method": [{
            "id": 3,
            "code": "manual",
            "name": "Manual Payment",
            "payment_type": "outbound",
        }],
        "account.move": [{
            "id": 40,
            "name": "PBNK1/2025/00005",
            "state": "posted",
            "date": "2025-01-25",
            "move_type": "entry",
            "payment_state": "not_paid",
            "company_id": [7, "Fixture Company"],
        }],
        "account.move.line": [],
        "account.account": [],
        "account.partial.reconcile": [],
    }
    if get:
        records["account.move"].extend([
            {
                "id": 90,
                "name": "INV/2025/00090",
                "state": "posted",
                "date": "2025-01-20",
                "move_type": "out_invoice",
                "payment_state": "partial",
                "company_id": [7, "Fixture Company"],
            },
            {
                "id": 91,
                "name": "RCPT/2025/00091",
                "state": "posted",
                "date": "2025-01-21",
                "move_type": "in_receipt",
                "payment_state": "paid",
                "company_id": [7, "Fixture Company"],
            },
            {
                "id": 70,
                "name": "MISC/2025/00070",
                "state": "posted",
                "date": "2025-01-19",
                "move_type": "entry",
                "payment_state": False,
                "company_id": [7, "Fixture Company"],
            },
        ])
        records["account.move.line"] = [
            {
                "id": 401,
                "move_id": [40, "display value must not leak"],
                "account_id": [102, "display value must not leak"],
                "company_id": [7, "Fixture Company"],
            },
            *[
                {
                    "id": line_id,
                    "move_id": [move_id, "display value must not leak"],
                    "account_id": [102, "display value must not leak"],
                    "company_id": [7, "Fixture Company"],
                }
                for line_id, move_id in ((601, 90), (602, 91), (603, 70))
            ],
        ]
        records["account.account"] = [{
            "id": 102,
            "account_type": "liability_payable",
            "reconcile": True,
        }]
        records["account.partial.reconcile"] = [
            {
                "id": 501,
                "debit_move_id": [601, "display value must not leak"],
                "credit_move_id": [401, "display value must not leak"],
                "exchange_move_id": False,
                "company_id": [7, "Fixture Company"],
            },
            {
                "id": 502,
                "debit_move_id": [601, "display value must not leak"],
                "credit_move_id": [401, "display value must not leak"],
                "exchange_move_id": False,
                "company_id": [7, "Fixture Company"],
            },
            {
                "id": 503,
                "debit_move_id": [401, "display value must not leak"],
                "credit_move_id": [602, "display value must not leak"],
                "exchange_move_id": False,
                "company_id": [7, "Fixture Company"],
            },
            {
                "id": 504,
                "debit_move_id": [603, "display value must not leak"],
                "credit_move_id": [401, "display value must not leak"],
                "exchange_move_id": [71, "ignored exchange move"],
                "company_id": [7, "Fixture Company"],
            },
        ]
    return records


class _Environment:
    uid = 42

    def __init__(
        self,
        action: str,
        *,
        company_visible: bool = True,
        missing_model: str | None = None,
        denied_model: str | None = None,
    ) -> None:
        self.action = action
        self.company_visible = company_visible
        self.calls: list[tuple[Any, ...]] = []
        self.records = _records(get=action == GET_ACTION)
        self.models: dict[str, Any] = {}
        for model in sorted(GET_MODELS):
            cls = _Companies if model == "res.company" else _Model
            self.models[model] = cls(
                model,
                self,
                access_allowed=denied_model != model,
            )
        self.registry = _Registry(self, missing_model)

    def __getitem__(self, model: str):
        self.calls.append(("model", model))
        if model not in self.models:
            raise AssertionError(f"unexpected model access: {model}")
        return self.models[model]

    def respond(self, model: str, domain: list[Any]) -> list[dict[str, Any]]:
        rows = copy.deepcopy(self.records.get(model, []))
        terms = _domain_terms(domain)
        if model == "account.payment":
            wanted_id = _domain_value(domain, "id", "=")
            wanted_company = _domain_value(domain, "company_id", "=")
            return [
                row
                for row in rows
                if (wanted_id is None or row["id"] == wanted_id)
                and (
                    wanted_company is None
                    or _reference_id(row["company_id"]) == wanted_company
                )
            ]
        if model == "account.move.line":
            move_id = _domain_value(domain, "move_id", "=")
            ids = _domain_value(domain, "id", "in")
            if move_id is not None:
                return [row for row in rows if _reference_id(row["move_id"]) == move_id]
            if ids is not None:
                return [row for row in rows if row["id"] in ids]
        ids = _domain_value(domain, "id", "in")
        exact_id = _domain_value(domain, "id", "=")
        if ids is not None:
            rows = [row for row in rows if row["id"] in ids]
        if exact_id is not None:
            rows = [row for row in rows if row["id"] == exact_id]
        company = _domain_value(domain, "company_id", "=")
        if company is not None and model != "account.partial.reconcile":
            rows = [
                row
                for row in rows
                if "company_id" not in row
                or _reference_id(row["company_id"]) == company
            ]
        move_types = _domain_value(domain, "move_type", "in")
        if move_types is not None:
            rows = [row for row in rows if row.get("move_type") in move_types]
        return rows


def _search_calls(env: _Environment, model: str) -> list[tuple[Any, ...]]:
    return [call for call in env.calls if call[:2] == ("search", model)]


def _expected_common() -> dict[str, Any]:
    return {
        "id": 5,
        "name": "PBNK1/2025/00005",
        "date": "2025-01-25",
        "state": "in_process",
        "payment_type": "outbound",
        "partner_type": "supplier",
        "amount": "125.5",
        "amount_signed": "-125.5",
        "amount_company_currency_signed": "-168.75",
        "currency": {"id": 6, "code": "CNY"},
        "company_currency": {"id": 37, "code": "SGD"},
        "company_id": 7,
        "partner": {"id": 9, "name": "Fixture Vendor"},
        "journal": {"id": 10, "code": "BNK1", "name": "Bank"},
        "memo": None,
        "payment_reference": "WIRE-5",
        "payment_method_line": {
            "id": 55,
            "name": "Manual (Bank)",
            "journal_id": 10,
        },
        "payment_method": {
            "id": 3,
            "code": "manual",
            "name": "Manual Payment",
            "payment_type": "outbound",
        },
        "move_id": 40,
        "is_reconciled": True,
        "is_matched": False,
    }


def _document(
    record_id: int,
    name: str,
    move_type: str,
    payment_state: str,
    company_id: int = 7,
) -> dict[str, Any]:
    return {
        "id": record_id,
        "name": name,
        "move_type": move_type,
        "state": "posted",
        "payment_state": payment_state,
        "company_id": company_id,
    }


def _expected_get() -> dict[str, Any]:
    return {
        **_expected_common(),
        "journal_entry": {
            "id": 40,
            "name": "PBNK1/2025/00005",
            "state": "posted",
            "date": "2025-01-25",
        },
        "invoice_ids": [
            _document(90, "INV/2025/00090", "out_invoice", "partial"),
            _document(91, "RCPT/2025/00091", "in_receipt", "paid"),
        ],
        "reconciled_invoices": [
            _document(90, "INV/2025/00090", "out_invoice", "partial")
        ],
        "reconciled_bills": [
            _document(91, "RCPT/2025/00091", "in_receipt", "paid")
        ],
    }


def _dispatch(
    env: _Environment,
    action: str,
    payload: dict[str, Any] | None = None,
    available_company_ids: tuple[int, ...] | None = None,
):
    if available_company_ids is None and action == GET_ACTION:
        available_company_ids = (7,)
    return runtime._dispatch(
        env,
        action,
        payload or _payload(action),
        7,
        available_company_ids,
    )


def _assert_runtime_error(env: _Environment, action: str) -> None:
    with pytest.raises(RuntimeFailure) as caught:
        _dispatch(env, action)
    assert caught.value.code == "odoo_runtime_error"
    assert caught.value.exit_code == 7


def test_decode_accepts_only_the_two_fixed_payment_actions() -> None:
    for action in ACTIONS:
        decoded = runtime._decode_request(io.StringIO(_bridge_request(action)))
        assert decoded["action"] == action


def test_search_uses_exact_company_filters_descending_cursor_and_related_rereads() -> None:
    env = _Environment(SEARCH_ACTION)
    filters = _filters(
        date_from="2025-01-01",
        date_to="2025-01-31",
        states=["in_process", "paid"],
        payment_types=["inbound", "outbound"],
        partner_types=["customer", "supplier"],
        journal_id=10,
        partner_id=9,
        currency_id=6,
        query="needle",
    )
    payload = _payload(
        SEARCH_ACTION,
        after=["2025-01-25", 6],
        filters=filters,
    )

    result = _dispatch(env, SEARCH_ACTION, payload)

    assert result == {
        "user_id": 42,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "rows": [_expected_common()],
    }
    payment_call = _search_calls(env, "account.payment")[0]
    assert payment_call[3:] == (PAYMENT_FIELDS, 3, "date desc,id desc")
    assert payment_call[2] == [
        "&",
        "&",
        "&",
        "&",
        "&",
        "&",
        "&",
        "&",
        "&",
        "&",
        ("company_id", "=", 7),
        ("date", ">=", "2025-01-01"),
        ("date", "<=", "2025-01-31"),
        ("state", "in", ["in_process", "paid"]),
        ("payment_type", "in", ["inbound", "outbound"]),
        ("partner_type", "in", ["customer", "supplier"]),
        ("journal_id", "=", 10),
        ("partner_id", "=", 9),
        ("currency_id", "=", 6),
        "|",
        "|",
        ("name", "ilike", "needle"),
        ("memo", "ilike", "needle"),
        ("payment_reference", "ilike", "needle"),
        "|",
        ("date", "<", "2025-01-25"),
        "&",
        ("date", "=", "2025-01-25"),
        ("id", "<", 6),
    ]
    assert (
        "context",
        "account.payment",
        {"active_test": False, "allowed_company_ids": [7]},
    ) in env.calls

    journal_call = _search_calls(env, "account.journal")[0]
    assert journal_call[2] == [("id", "in", [10]), ("company_id", "in", [7])]
    assert journal_call[3] == JOURNAL_FIELDS
    currency_call = _search_calls(env, "res.currency")[0]
    assert currency_call[2] == [("id", "in", [6, 37])]
    assert currency_call[3] == CURRENCY_FIELDS
    partner_call = _search_calls(env, "res.partner")[0]
    assert partner_call[2] == [
        ("id", "in", [9]),
        ("company_id", "in", [False, 7]),
    ]
    assert partner_call[3] == PARTNER_FIELDS
    method_line_call = _search_calls(env, "account.payment.method.line")[0]
    assert method_line_call[2] == [
        ("id", "in", [55]),
        ("journal_id", "in", [False, 10]),
    ]
    assert method_line_call[3] == METHOD_LINE_FIELDS
    method_call = _search_calls(env, "account.payment.method")[0]
    assert method_call[2] == [("id", "in", [3])]
    assert method_call[3] == METHOD_FIELDS
    move_call = _search_calls(env, "account.move")[0]
    assert ("id", "in", [40]) in _domain_terms(move_call[2])
    assert ("company_id", "=", 7) in _domain_terms(move_call[2])


def test_get_explicitly_traverses_reconciliations_and_keeps_three_provenances() -> None:
    env = _Environment(GET_ACTION)

    result = _dispatch(env, GET_ACTION)

    assert result == {
        "user_id": 42,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "payment": _expected_get(),
    }
    payment_call = _search_calls(env, "account.payment")[0]
    assert payment_call[2] == [("id", "=", 5), ("company_id", "=", 7)]
    assert payment_call[3] == [*PAYMENT_FIELDS, "invoice_ids"]
    assert payment_call[4:] == (1, "id")

    payment_line_call = next(
        call
        for call in _search_calls(env, "account.move.line")
        if ("move_id", "=", 40) in _domain_terms(call[2])
    )
    assert payment_line_call[2] == [
        ("move_id", "=", 40),
        ("company_id", "=", 7),
        (
            "account_id.account_type",
            "in",
            ["asset_receivable", "liability_payable"],
        ),
    ]
    assert payment_line_call[3] == PAYMENT_MOVE_LINE_FIELDS
    assert payment_line_call[5] == "id"

    account_call = _search_calls(env, "account.account")[0]
    assert ("id", "in", [102]) in _domain_terms(account_call[2])
    assert ("company_ids", "in", [7]) in _domain_terms(account_call[2])
    assert account_call[3] == ACCOUNT_FIELDS

    partial_call = _search_calls(env, "account.partial.reconcile")[0]
    assert partial_call[2] == [
        ("company_id", "in", [7]),
        "|",
        ("debit_move_id", "in", [401]),
        ("credit_move_id", "in", [401]),
    ]
    assert partial_call[3] == PARTIAL_FIELDS
    assert partial_call[5] == "id"

    counterpart_call = next(
        call
        for call in _search_calls(env, "account.move.line")
        if ("id", "in", [601, 602, 603]) in _domain_terms(call[2])
    )
    assert counterpart_call[2] == [
        ("id", "in", [601, 602, 603]),
        ("company_id", "in", [7]),
    ]
    assert counterpart_call[3] == COUNTERPART_LINE_FIELDS

    document_calls = [
        call
        for call in _search_calls(env, "account.move")
        if ("move_type", "in", DOCUMENT_TYPES) in _domain_terms(call[2])
    ]
    assert document_calls
    assert all(
        ("company_id", "in", [7]) in _domain_terms(call[2])
        for call in document_calls
    )
    assert all(call[3] == MOVE_FIELDS for call in document_calls)


@pytest.mark.parametrize(
    ("action", "required_models", "result_key"),
    (
        (SEARCH_ACTION, SEARCH_MODELS, "rows"),
        (GET_ACTION, GET_MODELS, "payment"),
    ),
)
def test_every_required_model_and_read_acl_gate_precedes_business_reads(
    action: str,
    required_models: set[str],
    result_key: str,
) -> None:
    for denied_model in sorted(required_models):
        env = _Environment(action, denied_model=denied_model)
        result = _dispatch(env, action)
        assert result == {
            "user_id": 42,
            "company_visible": denied_model != "res.company",
            "module_installed": True,
            "access_allowed": False,
            result_key: [] if result_key == "rows" else None,
        }
        assert not any(call[0] == "search" for call in env.calls)

    for missing_model in sorted(required_models):
        env = _Environment(action, missing_model=missing_model)
        result = _dispatch(env, action)
        assert result == {
            "user_id": 42,
            "company_visible": missing_model != "res.company",
            "module_installed": False,
            "access_allowed": False,
            result_key: [] if result_key == "rows" else None,
        }
        assert not any(call[0] == "search" for call in env.calls)


@pytest.mark.parametrize("action", ACTIONS)
def test_invisible_company_is_empty_without_business_reads(action: str) -> None:
    env = _Environment(action, company_visible=False)

    result = _dispatch(env, action)

    assert result["company_visible"] is False
    assert result["module_installed"] is True
    assert result["access_allowed"] is False
    assert result["rows" if action == SEARCH_ACTION else "payment"] == (
        [] if action == SEARCH_ACTION else None
    )
    assert not any(call[0] == "search" for call in env.calls)


@pytest.mark.parametrize(
    "payload",
    (
        {"company_id": 7, "after": None, "limit": 3},
        {**_payload(SEARCH_ACTION), "unexpected": True},
        _payload(SEARCH_ACTION, company_id=True),
        _payload(SEARCH_ACTION, after=["2025-1-25", 5]),
        _payload(SEARCH_ACTION, after=["2025-01-25"]),
        _payload(SEARCH_ACTION, after=["2025-01-25", True]),
        _payload(SEARCH_ACTION, limit=0),
        _payload(SEARCH_ACTION, limit=1002),
        _payload(SEARCH_ACTION, limit=True),
        _payload(
            SEARCH_ACTION,
            filters={key: value for key, value in _filters().items() if key != "query"},
        ),
        _payload(SEARCH_ACTION, filters={**_filters(), "unexpected": None}),
        _payload(SEARCH_ACTION, filters=_filters(date_from="2025-1-01")),
        _payload(
            SEARCH_ACTION,
            filters=_filters(date_from="2025-02-01", date_to="2025-01-01"),
        ),
        _payload(SEARCH_ACTION, filters=_filters(states=["paid", "draft"])),
        _payload(SEARCH_ACTION, filters=_filters(states=["draft", "draft"])),
        _payload(SEARCH_ACTION, filters=_filters(states=["posted"])),
        _payload(SEARCH_ACTION, filters=_filters(payment_types=["internal"])),
        _payload(SEARCH_ACTION, filters=_filters(partner_types=["employee"])),
        _payload(SEARCH_ACTION, filters=_filters(journal_id=True)),
        _payload(SEARCH_ACTION, filters=_filters(partner_id=0)),
        _payload(SEARCH_ACTION, filters=_filters(currency_id="6")),
        _payload(SEARCH_ACTION, filters=_filters(query=" untrimmed")),
        _payload(SEARCH_ACTION, filters=_filters(query="untrimmed\n")),
        _payload(SEARCH_ACTION, filters=_filters(query="")),
        _payload(SEARCH_ACTION, filters=_filters(query="x" * 201)),
    ),
)
def test_search_payloads_fail_closed_before_model_access(payload: dict[str, Any]) -> None:
    env = _Environment(SEARCH_ACTION)
    with pytest.raises(RuntimeFailure) as caught:
        _dispatch(env, SEARCH_ACTION, payload)
    assert caught.value.code == "bridge_protocol_error"
    assert caught.value.exit_code == 7
    assert not any(call[0] in {"company", "access", "context", "search"} for call in env.calls)


@pytest.mark.parametrize(
    "payload",
    (
        {"company_id": 7},
        {"company_id": 7, "payment_id": 5, "unexpected": None},
        {"company_id": True, "payment_id": 5},
        {"company_id": 7, "payment_id": True},
        {"company_id": 7, "payment_id": 0},
        {"company_id": 7, "payment_id": "5"},
    ),
)
def test_get_payloads_fail_closed_before_model_access(payload: dict[str, Any]) -> None:
    env = _Environment(GET_ACTION)
    with pytest.raises(RuntimeFailure) as caught:
        _dispatch(env, GET_ACTION, payload)
    assert caught.value.code == "bridge_protocol_error"
    assert caught.value.exit_code == 7
    assert not any(call[0] in {"company", "access", "context", "search"} for call in env.calls)


@pytest.mark.parametrize("action", ACTIONS)
def test_company_mismatch_fails_before_model_access(action: str) -> None:
    env = _Environment(action)
    with pytest.raises(RuntimeFailure) as caught:
        _dispatch(env, action, _payload(action, company_id=8))
    assert caught.value.code == "company_unavailable"
    assert caught.value.exit_code == 3
    assert not any(call[0] in {"company", "access", "context", "search"} for call in env.calls)


def test_missing_and_cross_company_get_are_indistinguishable() -> None:
    missing = _Environment(GET_ACTION)
    missing.records["account.payment"] = []
    cross_company = _Environment(GET_ACTION)
    cross_company.records["account.payment"][0]["company_id"] = [8, "Other"]

    missing_result = _dispatch(missing, GET_ACTION)
    cross_result = _dispatch(cross_company, GET_ACTION)

    assert missing_result == cross_result == {
        "user_id": 42,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "payment": None,
    }
    assert _search_calls(missing, "account.payment")[0][2] == [
        ("id", "=", 5),
        ("company_id", "=", 7),
    ]
    assert _search_calls(cross_company, "account.payment")[0][2] == [
        ("id", "=", 5),
        ("company_id", "=", 7),
    ]


def test_detached_historical_method_line_is_preserved_with_null_fields() -> None:
    env = _Environment(SEARCH_ACTION)
    line = env.records["account.payment.method.line"][0]
    line["name"] = False
    line["journal_id"] = False

    result = _dispatch(env, SEARCH_ACTION)

    expected = _expected_common()
    expected["payment_method_line"] = {"id": 55, "name": None, "journal_id": None}
    assert result["rows"] == [expected]
    method_line_domain = _search_calls(env, "account.payment.method.line")[0][2]
    assert ("journal_id", "in", [False, 10]) in _domain_terms(method_line_domain)


def test_partner_name_false_is_preserved_as_null() -> None:
    env = _Environment(SEARCH_ACTION)
    env.records["res.partner"][0]["name"] = False

    result = _dispatch(env, SEARCH_ACTION)

    expected = _expected_common()
    expected["partner"] = {"id": 9, "name": None}
    assert result["rows"] == [expected]


def test_nonempty_whitespace_text_is_preserved() -> None:
    env = _Environment(SEARCH_ACTION)
    env.records["account.payment"][0]["memo"] = " "
    env.records["account.journal"][0]["name"] = " "

    result = _dispatch(env, SEARCH_ACTION)

    expected = _expected_common()
    expected["memo"] = " "
    expected["journal"]["name"] = " "
    assert result["rows"] == [expected]


def test_parent_company_journal_partner_and_account_are_valid_relations() -> None:
    env = _Environment(GET_ACTION)
    env.records["res.company"][0]["parent_path"] = "3/7/"
    env.records["account.journal"][0]["company_id"] = [3, "Parent Company"]
    env.records["res.partner"][0]["company_id"] = [3, "Parent Company"]

    result = _dispatch(env, GET_ACTION)

    assert result["payment"] == _expected_get()
    journal_call = _search_calls(env, "account.journal")[0]
    assert ("company_id", "in", [3, 7]) in _domain_terms(journal_call[2])
    partner_call = _search_calls(env, "res.partner")[0]
    assert ("company_id", "in", [False, 3, 7]) in _domain_terms(partner_call[2])
    account_call = _search_calls(env, "account.account")[0]
    assert ("company_ids", "in", [3, 7]) in _domain_terms(account_call[2])


def test_get_allows_only_configured_visible_same_root_reconciliation_companies() -> None:
    env = _Environment(GET_ACTION)
    env.records["res.company"].append({"id": 8, "parent_path": "7/8/"})
    for move in env.records["account.move"]:
        if move["id"] in {70, 90, 91}:
            move["company_id"] = [8, "Child Company"]
    for line in env.records["account.move.line"]:
        if line["id"] in {601, 602, 603}:
            line["company_id"] = [8, "Child Company"]
    for partial in env.records["account.partial.reconcile"]:
        partial["company_id"] = [8, "Child Company"]

    result = _dispatch(env, GET_ACTION, available_company_ids=(7, 8))

    expected = _expected_get()
    expected["invoice_ids"] = [
        _document(90, "INV/2025/00090", "out_invoice", "partial", 8),
        _document(91, "RCPT/2025/00091", "in_receipt", "paid", 8),
    ]
    expected["reconciled_invoices"] = [
        _document(90, "INV/2025/00090", "out_invoice", "partial", 8)
    ]
    expected["reconciled_bills"] = [
        _document(91, "RCPT/2025/00091", "in_receipt", "paid", 8)
    ]
    assert result["payment"] == expected
    assert any(
        call == (
            "context",
            "account.partial.reconcile",
            {"active_test": False, "allowed_company_ids": [7, 8]},
        )
        for call in env.calls
    )
    assert all(
        ("company_id", "=", 7) in _domain_terms(call[2])
        for call in _search_calls(env, "account.payment")
    )
    assert (
        "context",
        "account.payment",
        {"active_test": False, "allowed_company_ids": [7, 8]},
    ) in env.calls
    payment_line_call = next(
        call
        for call in _search_calls(env, "account.move.line")
        if ("move_id", "=", 40) in _domain_terms(call[2])
    )
    assert ("company_id", "=", 7) in _domain_terms(payment_line_call[2])

    unavailable = _Environment(GET_ACTION)
    unavailable.records = copy.deepcopy(env.records)
    _assert_runtime_error(unavailable, GET_ACTION)


def test_get_keeps_the_requested_company_first_in_multi_company_contexts() -> None:
    env = _Environment(GET_ACTION)
    env.records["res.company"].append({"id": 3, "parent_path": "7/3/"})

    result = _dispatch(env, GET_ACTION, available_company_ids=(3, 7))

    assert result["payment"] == _expected_get()
    assert (
        "context",
        "res.company",
        {"active_test": False, "allowed_company_ids": [7, 3]},
    ) in env.calls


def test_null_payment_move_skips_reconciliation_and_returns_null_journal_entry() -> None:
    env = _Environment(GET_ACTION)
    payment = env.records["account.payment"][0]
    payment["move_id"] = False
    payment["invoice_ids"] = []
    env.records["account.move.line"] = []
    env.records["account.partial.reconcile"] = []

    result = _dispatch(env, GET_ACTION)

    expected = _expected_common()
    expected["move_id"] = None
    assert result["payment"] == {
        **expected,
        "journal_entry": None,
        "invoice_ids": [],
        "reconciled_invoices": [],
        "reconciled_bills": [],
    }
    assert not _search_calls(env, "account.move.line")
    assert not _search_calls(env, "account.partial.reconcile")


def test_non_document_direct_links_are_authorized_and_ignored() -> None:
    env = _Environment(GET_ACTION)
    env.records["account.payment"][0]["invoice_ids"].append(70)

    result = _dispatch(env, GET_ACTION)

    assert result["payment"] == _expected_get()
    direct_call = next(
        call
        for call in _search_calls(env, "account.move")
        if ("id", "in", [70, 90, 91]) in _domain_terms(call[2])
    )
    assert not any(
        term[:2] == ("move_type", "in") for term in _domain_terms(direct_call[2])
    )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    (
        ("amount", -1.0),
        ("amount", float("nan")),
        ("amount_signed", 125.5),
        ("amount_signed", float("inf")),
        ("amount_company_currency_signed", float("-inf")),
        ("is_reconciled", 1),
        ("is_matched", 0),
    ),
)
def test_invalid_decimal_sign_and_boolean_values_fail_closed(
    field: str, bad_value: Any
) -> None:
    env = _Environment(SEARCH_ACTION)
    env.records["account.payment"][0][field] = bad_value
    _assert_runtime_error(env, SEARCH_ACTION)


def test_zero_amount_allows_force_balance_company_currency_amount() -> None:
    env = _Environment(SEARCH_ACTION)
    payment = env.records["account.payment"][0]
    payment.update(amount=0.0, amount_signed=0.0, amount_company_currency_signed=1.0)

    result = _dispatch(env, SEARCH_ACTION)

    assert result["rows"][0]["amount"] == "0"
    assert result["rows"][0]["amount_signed"] == "0"
    assert result["rows"][0]["amount_company_currency_signed"] == "1"


@pytest.mark.parametrize(
    ("model", "mutation"),
    (
        ("account.journal", lambda row: row.update(company_id=[8, "Other"])),
        ("account.payment.method.line", lambda row: row.update(journal_id=[11, "Other"])),
        ("account.payment.method", lambda row: row.update(payment_type="inbound")),
        ("account.move", lambda row: row.update(company_id=[8, "Other"])),
    ),
)
def test_cross_company_or_inconsistent_common_related_rows_fail_closed(
    model: str, mutation: Any
) -> None:
    env = _Environment(SEARCH_ACTION)
    mutation(env.records[model][0])
    _assert_runtime_error(env, SEARCH_ACTION)


@pytest.mark.parametrize(
    "model",
    (
        "account.journal",
        "res.currency",
        "res.partner",
        "account.payment.method.line",
        "account.payment.method",
        "account.move",
    ),
)
def test_missing_common_related_rows_fail_closed(model: str) -> None:
    env = _Environment(SEARCH_ACTION)
    env.records[model] = []
    _assert_runtime_error(env, SEARCH_ACTION)


@pytest.mark.parametrize(
    ("model", "record_id", "field", "bad_value"),
    (
        ("account.move.line", 401, "company_id", [8, "Other"]),
        ("account.account", 102, "reconcile", False),
        ("account.partial.reconcile", 501, "company_id", [8, "Other"]),
        ("account.move.line", 601, "company_id", [8, "Other"]),
        ("account.move", 90, "company_id", [8, "Other"]),
    ),
)
def test_cross_company_reconciliation_graph_fails_closed(
    model: str,
    record_id: int,
    field: str,
    bad_value: Any,
) -> None:
    env = _Environment(GET_ACTION)
    row = next(row for row in env.records[model] if row["id"] == record_id)
    row[field] = bad_value
    _assert_runtime_error(env, GET_ACTION)


def test_partial_reconcile_without_a_payment_side_fails_closed() -> None:
    env = _Environment(GET_ACTION)
    partial = env.records["account.partial.reconcile"][0]
    partial["debit_move_id"] = [601, "counterpart"]
    partial["credit_move_id"] = [602, "counterpart"]
    _assert_runtime_error(env, GET_ACTION)


def test_partial_reconcile_between_two_payment_lines_is_safely_ignored() -> None:
    env = _Environment(GET_ACTION)
    env.records["account.move.line"].append({
        "id": 402,
        "move_id": [40, "payment move"],
        "account_id": [102, "same reconcilable account"],
        "company_id": [7, "Fixture Company"],
    })
    env.records["account.partial.reconcile"].append({
        "id": 505,
        "debit_move_id": [401, "payment line"],
        "credit_move_id": [402, "payment line"],
        "exchange_move_id": False,
        "company_id": [7, "Fixture Company"],
    })

    payment = _dispatch(env, GET_ACTION)["payment"]

    assert [row["id"] for row in payment["reconciled_invoices"]] == [90]
    assert [row["id"] for row in payment["reconciled_bills"]] == [91]


def test_missing_counterpart_line_fails_but_non_document_move_is_ignored() -> None:
    missing = _Environment(GET_ACTION)
    missing.records["account.move.line"] = [
        row for row in missing.records["account.move.line"] if row["id"] != 601
    ]
    _assert_runtime_error(missing, GET_ACTION)

    valid = _Environment(GET_ACTION)
    result = _dispatch(valid, GET_ACTION)
    assert all(
        document["id"] != 70
        for key in ("reconciled_invoices", "reconciled_bills")
        for document in result["payment"][key]
    )


def test_direct_and_reconciled_documents_are_not_merged_or_made_disjoint() -> None:
    env = _Environment(GET_ACTION)

    payment = _dispatch(env, GET_ACTION)["payment"]

    assert [row["id"] for row in payment["invoice_ids"]] == [90, 91]
    assert [row["id"] for row in payment["reconciled_invoices"]] == [90]
    assert [row["id"] for row in payment["reconciled_bills"]] == [91]
    assert payment["invoice_ids"][0] == payment["reconciled_invoices"][0]
    assert payment["invoice_ids"][1] == payment["reconciled_bills"][0]


def test_unknown_payment_action_fails_closed_without_model_access() -> None:
    class Environment:
        registry = object()

        def __getitem__(self, model: str):
            raise AssertionError(f"unknown action must not access {model}")

    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(
            Environment(),
            "account.payment.arbitrary",
            _payload(GET_ACTION),
            7,
        )
    assert caught.value.code == "bridge_protocol_error"
    assert caught.value.exit_code == 7
