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


RECEIVABLE_ACTION = "account.move.line.receivable.open_items.search_page"
PAYABLE_ACTION = "account.move.line.payable.open_items.search_page"
ACTIONS = (RECEIVABLE_ACTION, PAYABLE_ACTION)
REQUIRED_MODELS = {
    "res.company",
    "account.move.line",
    "account.move",
    "account.account",
    "account.journal",
    "res.partner",
    "res.currency",
}
OPEN_ITEM_FIELDS = [
    "id",
    "date",
    "date_maturity",
    "name",
    "ref",
    "move_id",
    "journal_id",
    "company_id",
    "partner_id",
    "account_id",
    "currency_id",
    "company_currency_id",
    "debit",
    "credit",
    "balance",
    "amount_currency",
    "amount_residual",
    "amount_residual_currency",
    "reconciled",
    "matching_number",
    "parent_state",
    "account_type",
]
MOVE_FIELDS = ["id", "name", "move_type", "state", "company_id"]
JOURNAL_FIELDS = ["id", "code", "name", "company_id"]
PARTNER_FIELDS = ["id", "complete_name", "ref", "company_id"]
ACCOUNT_FIELDS = [
    "id",
    "code",
    "name",
    "account_type",
    "non_trade",
    "reconcile",
    "company_ids",
]
CURRENCY_FIELDS = ["id", "name"]


def _filters(**overrides: Any) -> dict[str, Any]:
    value = {
        "date_from": None,
        "date_to": None,
        "due_date_from": None,
        "due_date_to": None,
        "partner_id": None,
        "account_id": None,
        "journal_id": None,
        "currency_id": None,
        "query": None,
    }
    value.update(overrides)
    return value


def _payload(**overrides: Any) -> dict[str, Any]:
    value = {
        "company_id": 7,
        "after": None,
        "limit": 3,
        "filters": _filters(),
    }
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
    osv = ModuleType("odoo.osv")
    osv.expression = SimpleNamespace(  # type: ignore[attr-defined]
        AND=lambda domains: combine("&", domains),
        OR=lambda domains: combine("|", domains),
    )
    fields = ModuleType("odoo.fields")
    fields.Domain = Domain  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "odoo", odoo)
    monkeypatch.setitem(sys.modules, "odoo.osv", osv)
    monkeypatch.setitem(sys.modules, "odoo.fields", fields)


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

    def sudo(self, *args: Any, **kwargs: Any):
        raise AssertionError(f"open-items bridge must never sudo {self.name}")


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

    def with_context(self, **context: Any):
        self.calls.append(("context", "res.company", context))
        return self

    def search_read(
        self,
        domain: list[Any],
        *,
        fields: list[str],
        limit: int | None = None,
        order: str | None = None,
    ) -> list[dict[str, Any]]:
        self.calls.append(
            ("search", "res.company", domain, fields, limit, order)
        )
        return [{"id": 7, "parent_path": "1/7/"}]

    def sudo(self, *args: Any, **kwargs: Any):
        raise AssertionError("open-items bridge must never sudo res.company")


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


def _raw_open_item(side: str) -> dict[str, Any]:
    payable = side == "payable"
    return {
        "id": 301,
        "date": "2025-01-20",
        "date_maturity": "2025-02-20",
        "name": "Fixture open item",
        "ref": "ODACV4-FX1-OPEN-ITEM",
        "move_id": [99, "display value must not leak"],
        "journal_id": [8, "display value must not leak"],
        "company_id": [7, "Fixture Company"],
        "partner_id": [9, "display value must not leak"],
        "account_id": [101, "display value must not leak"],
        "currency_id": [6, "display value must not leak"],
        "company_currency_id": [37, "display value must not leak"],
        "debit": 0.0 if payable else 152.55,
        "credit": 152.55 if payable else 0.0,
        "balance": -152.55 if payable else 152.55,
        "amount_currency": -113.0 if payable else 113.0,
        "amount_residual": -85.05 if payable else 85.05,
        "amount_residual_currency": -63.0 if payable else 63.0,
        "reconciled": False,
        "matching_number": "P7",
        "parent_state": "posted",
        "account_type": "liability_payable" if payable else "asset_receivable",
    }


def _responses(side: str) -> dict[str, list[list[dict[str, Any]]]]:
    payable = side == "payable"
    return {
        "account.move.line": [[_raw_open_item(side)]],
        "account.move": [[{
            "id": 99,
            "name": "BILL/2025/0099" if payable else "INV/2025/0099",
            "move_type": "in_invoice" if payable else "out_invoice",
            "state": "posted",
            "company_id": [7, "Fixture Company"],
        }]],
        "account.journal": [[{
            "id": 8,
            "code": "BILL" if payable else "INV",
            "name": "Purchases" if payable else "Sales",
            "company_id": [7, "Fixture Company"],
        }]],
        "res.partner": [[{
            "id": 9,
            "complete_name": "Fixture Vendor" if payable else "Fixture Customer",
            "ref": "VENDOR-9" if payable else "CUSTOMER-9",
            "company_id": [7, "Fixture Company"],
        }]],
        "account.account": [[{
            "id": 101,
            "code": "2100" if payable else "1100",
            "name": "Accounts Payable" if payable else "Accounts Receivable",
            "account_type": "liability_payable" if payable else "asset_receivable",
            "non_trade": False,
            "reconcile": True,
            "company_ids": [7],
        }]],
        "res.currency": [[
            {"id": 6, "name": "CNY"},
            {"id": 37, "name": "SGD"},
        ]],
    }


class _Environment:
    uid = 42

    def __init__(
        self,
        side: str,
        *,
        company_visible: bool = True,
        missing_model: str | None = None,
        denied_model: str | None = None,
    ) -> None:
        self.calls: list[tuple[Any, ...]] = []
        self.models: dict[str, Any] = {
            "res.company": _Companies(
                self.calls,
                visible=company_visible,
                access_allowed=denied_model != "res.company",
            )
        }
        for model_name, responses in _responses(side).items():
            self.models[model_name] = _Model(
                model_name,
                self.calls,
                responses,
                access_allowed=denied_model != model_name,
            )
        self.registry = _Registry(
            self.calls,
            self.models,
            missing_model=missing_model,
        )

    def __getitem__(self, model: str):
        self.calls.append(("model", model))
        if model not in self.models:
            raise AssertionError(f"unexpected generic model access: {model}")
        return self.models[model]


def _side(action: str) -> str:
    return "receivable" if action == RECEIVABLE_ACTION else "payable"


def _search_calls(env: _Environment, model: str) -> list[tuple[Any, ...]]:
    return [call for call in env.calls if call[:2] == ("search", model)]


def _assert_related_read(
    env: _Environment,
    model: str,
    ids: list[int],
    fields: list[str],
) -> None:
    assert _search_calls(env, model) == [
        ("search", model, [("id", "in", ids)], fields, len(ids), "id")
    ]
    assert (
        "context",
        model,
        {"active_test": False, "allowed_company_ids": [7]},
    ) in env.calls


def _expected_item(side: str) -> dict[str, Any]:
    payable = side == "payable"
    return {
        "id": 301,
        "side": side,
        "date": "2025-01-20",
        "due_date": "2025-02-20",
        "name": "Fixture open item",
        "ref": "ODACV4-FX1-OPEN-ITEM",
        "move": {
            "id": 99,
            "name": "BILL/2025/0099" if payable else "INV/2025/0099",
            "move_type": "in_invoice" if payable else "out_invoice",
            "state": "posted",
        },
        "journal": {
            "id": 8,
            "code": "BILL" if payable else "INV",
            "name": "Purchases" if payable else "Sales",
        },
        "company_id": 7,
        "partner": {
            "id": 9,
            "name": "Fixture Vendor" if payable else "Fixture Customer",
            "reference": "VENDOR-9" if payable else "CUSTOMER-9",
        },
        "account": {
            "id": 101,
            "code": "2100" if payable else "1100",
            "name": "Accounts Payable" if payable else "Accounts Receivable",
            "account_type": "liability_payable" if payable else "asset_receivable",
            "non_trade": False,
        },
        "currency": {"id": 6, "code": "CNY"},
        "company_currency": {"id": 37, "code": "SGD"},
        "debit": "0" if payable else "152.55",
        "credit": "152.55" if payable else "0",
        "balance": "-152.55" if payable else "152.55",
        "amount_currency": "-113" if payable else "113",
        "amount_residual": "-85.05" if payable else "85.05",
        "amount_residual_currency": "-63" if payable else "63",
        "reconciled": False,
        "matching_number": "P7",
    }


def test_decode_accepts_only_the_two_fixed_open_item_actions() -> None:
    for action in ACTIONS:
        decoded = runtime._decode_request(io.StringIO(_bridge_request(action)))
        assert decoded["action"] == action


@pytest.mark.parametrize("action", ACTIONS)
def test_open_items_use_exact_scope_filters_cursor_fields_and_related_reads(
    action: str,
) -> None:
    side = _side(action)
    env = _Environment(side)
    payload = _payload(
        after=["2025-01-20", 302],
        filters=_filters(
            date_from="2025-01-01",
            date_to="2025-01-31",
            due_date_from="2025-02-01",
            due_date_to="2025-02-28",
            partner_id=9,
            account_id=101,
            journal_id=8,
            currency_id=6,
            query="needle",
        ),
    )

    result = runtime._dispatch(env, action, payload, 7)

    assert result == {
        "user_id": 42,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "rows": [_expected_item(side)],
    }
    line_call = _search_calls(env, "account.move.line")[0]
    assert line_call[3:] == (OPEN_ITEM_FIELDS, 3, "date desc,id desc")
    domain = line_call[2]
    account_type = "asset_receivable" if side == "receivable" else "liability_payable"
    for term in (
        ("company_id", "=", 7),
        ("parent_state", "=", "posted"),
        ("account_type", "=", account_type),
        ("account_id.reconcile", "=", True),
        ("reconciled", "=", False),
        ("date", ">=", "2025-01-01"),
        ("date", "<=", "2025-01-31"),
        ("date_maturity", ">=", "2025-02-01"),
        ("date_maturity", "<=", "2025-02-28"),
        ("partner_id", "=", 9),
        ("account_id", "=", 101),
        ("journal_id", "=", 8),
        ("currency_id", "=", 6),
        ("move_id.name", "ilike", "needle"),
        ("ref", "ilike", "needle"),
        ("name", "ilike", "needle"),
        ("partner_id.name", "ilike", "needle"),
        ("date", "<", "2025-01-20"),
        ("date", "=", "2025-01-20"),
        ("id", "<", 302),
    ):
        assert term in domain
    query_domain = [
        "|",
        "|",
        "|",
        ("move_id.name", "ilike", "needle"),
        ("ref", "ilike", "needle"),
        ("name", "ilike", "needle"),
        ("partner_id.name", "ilike", "needle"),
    ]
    assert any(
        domain[index : index + len(query_domain)] == query_domain
        for index in range(len(domain) - len(query_domain) + 1)
    )
    assert domain[-5:] == [
        "|",
        ("date", "<", "2025-01-20"),
        "&",
        ("date", "=", "2025-01-20"),
        ("id", "<", 302),
    ]
    assert (
        "context",
        "account.move.line",
        {"active_test": False, "allowed_company_ids": [7]},
    ) in env.calls
    _assert_related_read(env, "account.move", [99], MOVE_FIELDS)
    _assert_related_read(env, "account.journal", [8], JOURNAL_FIELDS)
    _assert_related_read(env, "res.partner", [9], PARTNER_FIELDS)
    _assert_related_read(env, "account.account", [101], ACCOUNT_FIELDS)
    _assert_related_read(env, "res.currency", [6, 37], CURRENCY_FIELDS)


@pytest.mark.parametrize("action", ACTIONS)
def test_every_required_model_and_read_acl_gate_precedes_business_reads(
    action: str,
) -> None:
    side = _side(action)
    for denied_model in sorted(REQUIRED_MODELS):
        env = _Environment(side, denied_model=denied_model)
        result = runtime._dispatch(env, action, _payload(), 7)
        assert result == {
            "user_id": 42,
            "company_visible": denied_model != "res.company",
            "module_installed": True,
            "access_allowed": False,
            "rows": [],
        }
        assert not any(call[0] == "search" for call in env.calls)

    for missing_model in sorted(REQUIRED_MODELS):
        env = _Environment(side, missing_model=missing_model)
        result = runtime._dispatch(env, action, _payload(), 7)
        assert result == {
            "user_id": 42,
            "company_visible": missing_model != "res.company",
            "module_installed": False,
            "access_allowed": False,
            "rows": [],
        }
        assert not any(call[0] == "search" for call in env.calls)


@pytest.mark.parametrize("action", ACTIONS)
def test_invisible_company_returns_empty_gate_result_without_business_reads(
    action: str,
) -> None:
    env = _Environment(_side(action), company_visible=False)

    assert runtime._dispatch(env, action, _payload(), 7) == {
        "user_id": 42,
        "company_visible": False,
        "module_installed": True,
        "access_allowed": False,
        "rows": [],
    }
    assert not any(call[0] == "search" for call in env.calls)


@pytest.mark.parametrize(
    "payload",
    (
        {"company_id": 7, "after": None, "limit": 3},
        {**_payload(), "unexpected": True},
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
        _payload(filters=_filters(due_date_from="2025-03-01", due_date_to="2025-02-01")),
        _payload(filters=_filters(partner_id=True)),
        _payload(filters=_filters(account_id=0)),
        _payload(filters=_filters(journal_id=-1)),
        _payload(filters=_filters(currency_id="6")),
        _payload(filters=_filters(query=" untrimmed")),
        _payload(filters=_filters(query="")),
        _payload(filters=_filters(query="x" * 201)),
    ),
)
@pytest.mark.parametrize("action", ACTIONS)
def test_open_item_payloads_fail_closed_before_model_access(
    action: str,
    payload: dict[str, Any],
) -> None:
    env = _Environment(_side(action))
    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(env, action, payload, 7)
    assert caught.value.code == "bridge_protocol_error"
    assert caught.value.exit_code == 7
    assert not any(call[0] in {"company", "access", "context", "search"} for call in env.calls)


@pytest.mark.parametrize("action", ACTIONS)
def test_open_item_company_mismatch_fails_before_model_access(action: str) -> None:
    env = _Environment(_side(action))
    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(env, action, _payload(company_id=8), 7)
    assert caught.value.code == "company_unavailable"
    assert caught.value.exit_code == 3
    assert not any(call[0] in {"company", "access", "context", "search"} for call in env.calls)


def test_unknown_open_item_action_fails_closed_without_model_access() -> None:
    class Environment:
        registry = object()

        def __getitem__(self, model: str):
            raise AssertionError(f"unknown action must not access {model}")

    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(
            Environment(),
            "account.move.line.open_items.arbitrary",
            _payload(),
            7,
        )
    assert caught.value.code == "bridge_protocol_error"
    assert caught.value.exit_code == 7


@pytest.mark.parametrize(
    ("model", "field", "bad_value"),
    (
        ("account.move", "company_id", [8, "Other Company"]),
        ("account.journal", "company_id", [8, "Other Company"]),
        ("res.partner", "company_id", [8, "Other Company"]),
        ("account.account", "company_ids", [8]),
    ),
)
def test_cross_company_related_records_fail_closed(
    model: str,
    field: str,
    bad_value: Any,
) -> None:
    env = _Environment("receivable")
    env.models[model].responses[0][0][field] = bad_value

    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(env, RECEIVABLE_ACTION, _payload(), 7)
    assert caught.value.code == "odoo_runtime_error"
    assert caught.value.exit_code == 7


def test_missing_related_record_fails_closed() -> None:
    env = _Environment("receivable")
    env.models["account.account"].responses[0] = []

    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(env, RECEIVABLE_ACTION, _payload(), 7)
    assert caught.value.code == "odoo_runtime_error"
    assert caught.value.exit_code == 7


def test_parent_company_related_records_are_accepted_but_siblings_are_not() -> None:
    env = _Environment("receivable")
    env.models["account.journal"].responses[0][0]["company_id"] = [1, "Parent"]
    env.models["res.partner"].responses[0][0]["company_id"] = [1, "Parent"]
    env.models["account.account"].responses[0][0]["company_ids"] = [1]

    result = runtime._dispatch(env, RECEIVABLE_ACTION, _payload(), 7)

    assert result["rows"] == [_expected_item("receivable")]

    for model, field, value in (
        ("account.journal", "company_id", [8, "Sibling"]),
        ("res.partner", "company_id", [8, "Sibling"]),
        ("account.account", "company_ids", [8]),
    ):
        bad_env = _Environment("receivable")
        bad_env.models[model].responses[0][0][field] = value
        with pytest.raises(RuntimeFailure) as caught:
            runtime._dispatch(bad_env, RECEIVABLE_ACTION, _payload(), 7)
        assert caught.value.code == "odoo_runtime_error"


def test_required_odoo_text_is_preserved_even_when_it_is_only_whitespace() -> None:
    env = _Environment("receivable")
    env.models["account.move"].responses[0][0]["name"] = "   "
    env.models["account.journal"].responses[0][0].update(code="   ", name="   ")
    env.models["account.account"].responses[0][0].update(code="   ", name="   ")
    env.models["res.currency"].responses[0][0]["name"] = "   "
    env.models["res.currency"].responses[0][1]["name"] = "  "

    result = runtime._dispatch(env, RECEIVABLE_ACTION, _payload(), 7)

    row = result["rows"][0]
    assert row["move"]["name"] == "   "
    assert row["journal"] == {"id": 8, "code": "   ", "name": "   "}
    assert row["account"]["code"] == "   "
    assert row["account"]["name"] == "   "
    assert row["currency"] == {"id": 6, "code": "   "}
    assert row["company_currency"] == {"id": 37, "code": "  "}
