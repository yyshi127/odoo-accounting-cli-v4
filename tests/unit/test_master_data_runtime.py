from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge import runtime
from odoo_accounting_cli_v4.bridge.runtime import RuntimeFailure


@dataclass(frozen=True)
class ActionContract:
    action: str
    model: str
    cursor_fields: tuple[str, ...]
    cursor_operators: tuple[str, ...]
    example_after: tuple[Any, ...]
    fields: tuple[str, ...]
    base_domain: list[Any]
    order: str


_CONTRACTS = (
    ActionContract(
        action="account.journal.read_page",
        model="account.journal",
        cursor_fields=("sequence", "type", "code", "id"),
        cursor_operators=(">", ">", ">", ">"),
        example_after=(10, "sale", "SAJ", 8),
        fields=(
            "id",
            "code",
            "name",
            "type",
            "active",
            "sequence",
            "currency_id",
            "company_id",
        ),
        base_domain=[("company_id", "=", 7)],
        order="sequence,type,code,id",
    ),
    ActionContract(
        action="account.tax.read_page",
        model="account.tax",
        cursor_fields=("sequence", "id"),
        cursor_operators=(">", ">"),
        example_after=(10, 8),
        fields=(
            "id",
            "name",
            "type_tax_use",
            "amount_type",
            "amount",
            "active",
            "sequence",
            "price_include",
            "include_base_amount",
            "is_base_affected",
            "tax_group_id",
            "company_id",
        ),
        base_domain=[("company_id", "=", 7)],
        order="sequence,id",
    ),
    ActionContract(
        action="account.payment.term.read_page",
        model="account.payment.term",
        cursor_fields=("sequence", "id"),
        cursor_operators=(">", ">"),
        example_after=(10, 8),
        fields=(
            "id",
            "name",
            "active",
            "company_id",
            "sequence",
            "display_on_invoice",
            "early_discount",
            "discount_percentage",
            "discount_days",
            "early_pay_discount_computation",
            "line_ids",
        ),
        base_domain=["|", ("company_id", "=", False), ("company_id", "=", 7)],
        order="sequence,id",
    ),
    ActionContract(
        action="res.currency.read_page",
        model="res.currency",
        cursor_fields=("active", "name", "id"),
        cursor_operators=("<", ">", ">"),
        example_after=(True, "USD", 8),
        fields=(
            "id",
            "name",
            "full_name",
            "symbol",
            "active",
            "position",
            "rounding",
            "decimal_places",
            "is_current_company_currency",
        ),
        base_domain=[],
        order="active desc,name,id",
    ),
)


class _Companies:
    def __init__(self, calls: list[tuple[Any, ...]], *, visible: bool = True) -> None:
        self.calls = calls
        self.visible = visible

    def search_count(self, domain, *, limit):
        self.calls.append(("company", domain, limit))
        return int(self.visible)


class _Records:
    def __init__(
        self,
        calls: list[tuple[Any, ...]],
        *,
        model: str,
        access_allowed: bool = True,
    ) -> None:
        self.calls = calls
        self.model = model
        self.access_allowed = access_allowed

    def has_access(self, operation):
        self.calls.append(("access", operation))
        return self.access_allowed

    def with_context(self, **context):
        self.calls.append(("context", context))
        return self

    def search_read(self, domain, *, fields, limit, order):
        self.calls.append(("search", domain, fields, limit, order))
        if self.model == "account.journal":
            return [{
                "id": 99,
                "code": "ZZZ",
                "name": "General",
                "type": "general",
                "active": True,
                "sequence": 11,
                "currency_id": [6, "CNY"],
                "company_id": [7, "Company"],
            }]
        if self.model == "account.tax":
            return [{
                "id": 99,
                "name": "Tax",
                "type_tax_use": "sale",
                "amount_type": "percent",
                "amount": 13.0,
                "active": True,
                "sequence": 11,
                "price_include": False,
                "include_base_amount": False,
                "is_base_affected": True,
                "tax_group_id": [5, "VAT"],
                "company_id": [7, "Company"],
            }]
        if self.model == "account.payment.term":
            return [{
                "id": 99,
                "name": "30 Days",
                "active": True,
                "company_id": False,
                "sequence": 11,
                "display_on_invoice": True,
                "early_discount": False,
                "discount_percentage": 2.0,
                "discount_days": 10,
                "early_pay_discount_computation": "included",
                "line_ids": [501],
            }]
        if self.model == "account.payment.term.line":
            return [{
                "id": 501,
                "payment_id": [99, "30 Days"],
                "value": "percent",
                "value_amount": 100.0,
                "delay_type": "days_after",
                "nb_days": 30,
                "days_next_month": "10",
            }]
        if self.model == "res.currency":
            return [{
                "id": 99,
                "name": "ZZZ",
                "full_name": False,
                "symbol": "Z",
                "active": False,
                "position": False,
                "rounding": 0.01,
                "decimal_places": 2,
                "is_current_company_currency": False,
            }]
        return [{"id": 99}]


class _Registry:
    def __init__(
        self,
        calls: list[tuple[Any, ...]],
        model: str,
        records: _Records,
        *,
        installed: bool = True,
    ) -> None:
        self.calls = calls
        self.model = model
        self.records = records
        self.installed = installed

    def get(self, model):
        self.calls.append(("registry", model))
        assert model == self.model
        return self.records if self.installed else None


class _Environment:
    uid = 42

    def __init__(
        self,
        contract: ActionContract,
        calls: list[tuple[Any, ...]],
        *,
        company_visible: bool = True,
        installed: bool = True,
        access_allowed: bool = True,
    ) -> None:
        self.calls = calls
        self.companies = _Companies(calls, visible=company_visible)
        self.records = _Records(
            calls, model=contract.model, access_allowed=access_allowed
        )
        self.registry = _Registry(
            calls, contract.model, self.records, installed=installed
        )
        self._models = {
            "res.company": self.companies,
            contract.model: self.records,
        }
        if contract.model == "account.payment.term":
            self._models["account.payment.term.line"] = _Records(
                calls, model="account.payment.term.line"
            )

    def __getitem__(self, model):
        self.calls.append(("model", model))
        if model not in self._models:
            raise AssertionError(f"unexpected generic model access: {model}")
        return self._models[model]


def _expected_cursor_domain(contract: ActionContract, after: list[Any]):
    if contract.cursor_fields[0] == "active":
        tail_contract = ActionContract(
            action=contract.action,
            model=contract.model,
            cursor_fields=contract.cursor_fields[1:],
            cursor_operators=contract.cursor_operators[1:],
            example_after=contract.example_after[1:],
            fields=contract.fields,
            base_domain=[],
            order=contract.order,
        )
        tail = _expected_cursor_domain(tail_contract, after[1:])
        same_active = ["&", ("active", "=", after[0]), *tail]
        if after[0] is True:
            return ["|", ("active", "=", False), *same_active]
        return same_active
    terms = []
    for index, (field, operator) in enumerate(
        zip(contract.cursor_fields, contract.cursor_operators, strict=True)
    ):
        terms.append(
            [
                *((previous, "=", after[position]) for position, previous in enumerate(contract.cursor_fields[:index])),
                (field, operator, after[index]),
            ]
        )

    cursor_domain: list[Any] = ["|"] * (len(terms) - 1)
    for term in terms:
        cursor_domain.extend(["&"] * (len(term) - 1))
        cursor_domain.extend(term)
    if not contract.base_domain:
        return cursor_domain
    return ["&", *contract.base_domain, *cursor_domain]


@pytest.mark.parametrize("contract", _CONTRACTS, ids=lambda value: value.action)
def test_composite_master_data_page_has_fixed_orm_contract(contract) -> None:
    calls: list[tuple[Any, ...]] = []
    env = _Environment(contract, calls)
    after = list(contract.example_after)

    result = runtime._dispatch(
        env,
        contract.action,
        {"company_id": 7, "after": after, "limit": 3},
        7,
    )

    expected_rows = {
        "account.journal": [{
            "id": 99, "code": "ZZZ", "name": "General", "type": "general",
            "active": True, "sequence": 11, "currency": {"id": 6, "code": "CNY"},
            "company_id": 7,
        }],
        "account.tax": [{
            "id": 99, "name": "Tax", "type_tax_use": "sale",
            "amount_type": "percent", "amount": "13", "active": True,
            "sequence": 11, "price_include": False, "include_base_amount": False,
            "is_base_affected": True, "tax_group": {"id": 5, "name": "VAT"},
            "company_id": 7,
        }],
        "account.payment.term": [{
            "id": 99, "name": "30 Days", "active": True, "company_id": None,
            "sequence": 11, "display_on_invoice": True, "early_discount": False,
            "discount_percentage": "2", "discount_days": 10,
            "early_pay_discount_computation": "included",
            "lines": [{"id": 501, "value": "percent", "value_amount": "100",
                       "delay_type": "days_after", "nb_days": 30,
                       "days_next_month": "10"}],
        }],
        "res.currency": [{
            "id": 99, "code": "ZZZ", "name": None, "symbol": "Z",
            "active": False, "position": None, "rounding": "0.01",
            "decimal_places": 2, "is_company_currency": False,
        }],
    }[contract.model]
    assert result == {
        "user_id": 42,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "rows": expected_rows,
    }
    assert ("company", [("id", "=", 7)], 1) in calls
    assert ("registry", contract.model) in calls
    assert ("access", "read") in calls
    assert ("context", {"active_test": False, "allowed_company_ids": [7]}) in calls
    assert (
        "search",
        _expected_cursor_domain(contract, after),
        list(contract.fields),
        3,
        contract.order,
    ) in calls
    assert [call[0] for call in calls].count("search") == (
        2 if contract.model == "account.payment.term" else 1
    )


@pytest.mark.parametrize("contract", _CONTRACTS, ids=lambda value: value.action)
def test_master_data_first_page_uses_only_the_fixed_scope_domain(contract) -> None:
    calls: list[tuple[Any, ...]] = []

    runtime._dispatch(
        _Environment(contract, calls),
        contract.action,
        {"company_id": 7, "after": None, "limit": 3},
        7,
    )

    searches = [call for call in calls if call[0] == "search"]
    assert searches[0] == (
        "search",
        contract.base_domain,
        list(contract.fields),
        3,
        contract.order,
    )
    assert len(searches) == (2 if contract.model == "account.payment.term" else 1)


@pytest.mark.parametrize("contract", _CONTRACTS, ids=lambda value: value.action)
@pytest.mark.parametrize(
    ("company_visible", "installed", "access_allowed", "expected"),
    (
        (False, True, True, (False, True, False)),
        (True, False, True, (True, False, False)),
        (True, True, False, (True, True, False)),
    ),
)
def test_composite_master_data_page_gates_company_module_and_acl(
    contract,
    company_visible,
    installed,
    access_allowed,
    expected,
) -> None:
    calls: list[tuple[Any, ...]] = []
    env = _Environment(
        contract,
        calls,
        company_visible=company_visible,
        installed=installed,
        access_allowed=access_allowed,
    )

    result = runtime._dispatch(
        env,
        contract.action,
        {"company_id": 7, "after": None, "limit": 3},
        7,
    )

    assert (
        result["company_visible"],
        result["module_installed"],
        result["access_allowed"],
    ) == expected
    assert result["rows"] == []
    assert not any(call[0] in {"context", "search"} for call in calls)


@pytest.mark.parametrize("contract", _CONTRACTS, ids=lambda value: value.action)
def test_master_data_payload_and_list_cursor_fail_closed(contract) -> None:
    valid_after = list(contract.example_after)
    bool_id = [*valid_after[:-1], True]
    zero_id = [*valid_after[:-1], 0]
    wrong_typed_afters = []
    for index, value in enumerate(valid_after):
        wrong_value = (
            1
            if isinstance(value, bool)
            else ""
            if isinstance(value, str)
            else True
        )
        wrong_after = list(valid_after)
        wrong_after[index] = wrong_value
        wrong_typed_afters.append(wrong_after)
    malformed_payloads = (
        {"company_id": 7, "after": None},
        {"company_id": 7, "after": None, "limit": 3, "model": "res.users"},
        {"company_id": True, "after": None, "limit": 3},
        {"company_id": 7, "after": None, "limit": True},
        {"company_id": 7, "after": None, "limit": 0},
        {"company_id": 7, "after": None, "limit": 1002},
        {"company_id": 7, "after": {}, "limit": 3},
        {"company_id": 7, "after": valid_after[:-1], "limit": 3},
        {"company_id": 7, "after": [*valid_after, "unlink"], "limit": 3},
        {"company_id": 7, "after": bool_id, "limit": 3},
        {"company_id": 7, "after": zero_id, "limit": 3},
        *(
            {"company_id": 7, "after": wrong_after, "limit": 3}
            for wrong_after in wrong_typed_afters
        ),
    )

    for payload in malformed_payloads:
        with pytest.raises(RuntimeFailure) as caught:
            runtime._dispatch(_Environment(contract, []), contract.action, payload, 7)

        assert caught.value.code == "bridge_protocol_error"
        assert caught.value.exit_code == 7


@pytest.mark.parametrize("contract", _CONTRACTS, ids=lambda value: value.action)
def test_master_data_company_mismatch_fails_closed(contract) -> None:
    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(
            _Environment(contract, []),
            contract.action,
            {"company_id": 8, "after": None, "limit": 3},
            7,
        )

    assert caught.value.code == "company_unavailable"
    assert caught.value.exit_code == 3


def test_unknown_master_data_action_fails_closed_without_model_access() -> None:
    class Environment:
        registry = object()

        def __getitem__(self, model):
            raise AssertionError(f"unknown action must not access {model}")

    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(
            Environment(),
            "arbitrary.model.call",
            {"company_id": 7, "after": None, "limit": 3},
            7,
        )

    assert caught.value.code == "bridge_protocol_error"
    assert caught.value.exit_code == 7


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (999999999999.9999, "999999999999.9999"),
        (0.00001, "0.00001"),
        (-0.0, "0"),
    ],
)
def test_decimal_string_preserves_values_without_exponent(value, expected) -> None:
    assert runtime._decimal_string(value) == expected


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_decimal_string_rejects_non_finite_values(value) -> None:
    with pytest.raises(RuntimeFailure) as caught:
        runtime._decimal_string(value)

    assert caught.value.code == "odoo_runtime_error"
    assert caught.value.exit_code == 7
