from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge import localization_configuration_runtime as runtime


class Failure(RuntimeError):
    def __init__(self, code: str, message: str, *, exit_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


def _related(value: Any) -> Any:
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return value[0]
    return getattr(value, "id", value)


def _matches(row: dict[str, Any], domain: list[tuple[str, str, Any]]) -> bool:
    for field, operator, expected in domain:
        actual = row.get(field)
        related = _related(actual)
        if operator == "=" and related != expected:
            return False
        if operator == "!=" and related == expected:
            return False
        if operator == "in":
            if isinstance(actual, list) and not (
                len(actual) == 2 and _related(actual) == actual[0]
            ):
                if not set(actual) & set(expected):
                    return False
            elif related not in expected:
                return False
    return True


class Model:
    def __init__(
        self,
        rows: list[dict[str, Any]],
        *,
        fields: set[str],
        access: bool = True,
    ) -> None:
        self.rows = rows
        self._fields = {name: object() for name in fields | {"id"}}
        self.access = access
        self.calls: list[tuple[Any, ...]] = []

    def with_context(self, **context: Any) -> Model:
        self.calls.append(("with_context", context))
        return self

    def has_access(self, operation: str) -> bool:
        self.calls.append(("has_access", operation))
        return self.access and operation == "read"

    def search_count(
        self,
        domain: list[tuple[str, str, Any]],
        *,
        limit: int | None = None,
    ) -> int:
        self.calls.append(("search_count", domain, limit))
        count = sum(_matches(row, domain) for row in self.rows)
        return min(count, limit) if limit is not None else count

    def search_read(
        self,
        domain: list[tuple[str, str, Any]],
        *,
        fields: list[str],
        limit: int | None = None,
        order: str | None = None,
    ) -> list[dict[str, Any]]:
        self.calls.append(("search_read", domain, fields, order, limit))
        rows = [row for row in self.rows if _matches(row, domain)]
        if order == "name":
            rows.sort(key=lambda row: row["name"])
        if limit is not None:
            rows = rows[:limit]
        return [{field: row[field] for field in fields} for row in rows]


class User:
    def __init__(self, group_allowed: bool = True) -> None:
        self.group_allowed = group_allowed

    def has_group(self, xml_id: str) -> bool:
        assert xml_id == "account.group_account_readonly"
        return self.group_allowed


class Registry:
    def __init__(self, models: dict[str, Model]) -> None:
        self.models = models

    def get(self, name: str) -> Model | None:
        return self.models.get(name)


class Env:
    uid = 5

    def __init__(
        self,
        models: dict[str, Model],
        references: dict[str, int],
    ) -> None:
        self.models = models
        self.registry = Registry(models)
        self.user = User()
        self.references = references

    def __getitem__(self, name: str) -> Model:
        return self.models[name]

    def ref(self, xml_id: str, *, raise_if_not_found: bool) -> Any:
        assert raise_if_not_found is False
        record_id = self.references.get(xml_id)
        return False if record_id is None else SimpleNamespace(id=record_id)


def _model(
    rows: list[dict[str, Any]], fields: set[str], *, access: bool = True
) -> Model:
    return Model(rows, fields=fields, access=access)


def _china_env() -> Env:
    models = {
        "res.company": _model(
            [
                {
                    "id": 1,
                    "account_fiscal_country_id": [48, "China"],
                    "account_purchase_tax_id": [11, "13%"],
                    "account_sale_tax_id": [5, "13% INC"],
                    "chart_template": "cn_oscg",
                }
            ],
            set(runtime._COMMON_COMPANY_FIELDS),
        ),
        "res.country": _model(
            [{"id": 48, "code": "CN"}], {"code"}
        ),
        "account.tax": _model(
            [
                {
                    "id": 5,
                    "name": "13% INC",
                    "amount": 13.0,
                    "type_tax_use": "sale",
                    "company_id": [1, "China Company"],
                },
                {
                    "id": 11,
                    "name": "13%",
                    "amount": 13.0,
                    "type_tax_use": "purchase",
                    "company_id": [1, "China Company"],
                },
            ],
            set(runtime._COMMON_FIELDS["account.tax"]),
        ),
        "ir.module.module": _model(
            [
                {"id": 101, "name": "l10n_cn", "state": "installed"},
                {"id": 102, "name": "l10n_cn_oscg", "state": "installed"},
            ],
            {"name", "state"},
        ),
        "account.account": _model(
            [
                {"id": record_id, "company_ids": [1]}
                for record_id in range(1, 111)
            ],
            {"company_ids"},
        ),
        "account.move": _model([], {"fapiao"}),
        "ir.actions.report": _model(
            [
                {
                    "id": 201,
                    "name": "Voucher",
                    "model": "account.move",
                    "report_type": "qweb-pdf",
                    "report_name": "l10n_cn.report_voucher",
                }
            ],
            set(runtime._CHINA_FIELDS["ir.actions.report"]),
        ),
    }
    return Env(models, {"l10n_cn.account_voucher_cn": 201})


def _singapore_env() -> Env:
    models = {
        "res.company": _model(
            [
                {
                    "id": 2,
                    "account_fiscal_country_id": [192, "Singapore"],
                    "account_purchase_tax_id": [33, "9% TX"],
                    "account_sale_tax_id": [15, "9% SR"],
                    "chart_template": "sg",
                    "currency_id": [162, "SGD"],
                    "partner_id": [202, "Singapore Company"],
                    "vat": False,
                    "l10n_sg_unique_entity_number": False,
                }
            ],
            set(runtime._SINGAPORE_FIELDS["res.company"])
            | {"l10n_sg_unique_entity_number"},
        ),
        "res.country": _model(
            [{"id": 192, "code": "SG"}], {"code"}
        ),
        "res.currency": _model(
            [{"id": 162, "name": "SGD"}], {"name"}
        ),
        "account.tax": _model(
            [
                {
                    "id": 15,
                    "name": "9% SR",
                    "amount": 9.0,
                    "type_tax_use": "sale",
                    "company_id": [2, "Singapore Company"],
                },
                {
                    "id": 33,
                    "name": "9% TX",
                    "amount": 9.0,
                    "type_tax_use": "purchase",
                    "company_id": [2, "Singapore Company"],
                },
            ],
            set(runtime._COMMON_FIELDS["account.tax"]),
        ),
        "ir.module.module": _model(
            [{"id": 103, "name": "l10n_sg", "state": "installed"}],
            {"name", "state"},
        ),
        "account.report": _model(
            [
                {
                    "id": 22,
                    "name": "Tax Report",
                    "country_id": [192, "Singapore"],
                    "root_report_id": [1, "Tax Report"],
                    "availability_condition": "country",
                }
            ],
            set(runtime._SINGAPORE_FIELDS["account.report"]),
        ),
        "res.partner.bank": _model(
            [], {"partner_id", "proxy_type", "proxy_value"}
        ),
    }
    return Env(models, {"l10n_sg.tax_report": 22})


def _dispatch(env: Env, capability_id: str, company_id: int) -> dict[str, Any]:
    return runtime.dispatch(
        env,
        {
            "capability_id": capability_id,
            "company_id": company_id,
            "parameters": {},
        },
        company_id,
        failure_type=Failure,
    )


def test_china_runtime_reports_the_verified_ready_state() -> None:
    env = _china_env()

    page = _dispatch(env, runtime.CHINA_CAPABILITY, 1)

    assert page == {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "cursor_found": True,
        "items": [
            {
                "company_id": 1,
                "fiscal_country_code": "CN",
                "chart_template": "cn_oscg",
                "modules": {"l10n_cn": True, "l10n_cn_oscg": True},
                "account_count": 110,
                "default_sale_tax": {
                    "id": 5,
                    "name": "13% INC",
                    "rate": "13",
                    "type_tax_use": "sale",
                },
                "default_purchase_tax": {
                    "id": 11,
                    "name": "13%",
                    "rate": "13",
                    "type_tax_use": "purchase",
                },
                "fapiao_field_ready": True,
                "voucher_report_ready": True,
                "configured": True,
                "missing": [],
            }
        ],
    }
    account_call = next(
        call
        for call in env.models["account.account"].calls
        if call[0] == "search_count"
    )
    assert account_call[1] == [("company_ids", "in", [1])]


def test_singapore_runtime_reports_real_incomplete_registration_and_paynow_state() -> None:
    env = _singapore_env()

    item = _dispatch(env, runtime.SINGAPORE_CAPABILITY, 2)["items"][0]

    assert item == {
        "company_id": 2,
        "fiscal_country_code": "SG",
        "chart_template": "sg",
        "currency_code": "SGD",
        "default_sale_tax": {
            "id": 15,
            "name": "9% SR",
            "rate": "9",
            "type_tax_use": "sale",
        },
        "default_purchase_tax": {
            "id": 33,
            "name": "9% TX",
            "rate": "9",
            "type_tax_use": "purchase",
        },
        "tax_report": {"id": 22, "name": "Tax Report"},
        "uen_configured": False,
        "vat_configured": False,
        "paynow_configured": False,
        "configured": False,
        "missing": ["uen", "vat", "paynow"],
    }
    bank_call = next(
        call
        for call in env.models["res.partner.bank"].calls
        if call[0] == "search_count"
    )
    assert ("partner_id", "=", 202) in bank_call[1]
    assert ("proxy_type", "in", ["mobile", "uen"]) in bank_call[1]


def test_runtime_fails_closed_on_acl_field_drift_and_cross_company_tax() -> None:
    env = _china_env()
    env.models["account.tax"].access = False
    page = _dispatch(env, runtime.CHINA_CAPABILITY, 1)
    assert page["access_allowed"] is False
    assert page["items"] == []

    env = _singapore_env()
    del env.models["res.partner.bank"]._fields["proxy_value"]
    with pytest.raises(Failure) as caught:
        _dispatch(env, runtime.SINGAPORE_CAPABILITY, 2)
    assert caught.value.code == "odoo_runtime_error"

    env = _china_env()
    env.models["account.tax"].rows[0]["company_id"] = [2, "Other Company"]
    with pytest.raises(Failure) as caught:
        _dispatch(env, runtime.CHINA_CAPABILITY, 1)
    assert caught.value.code == "odoo_runtime_error"


def test_runtime_uses_fixed_company_context_and_never_escalates_model_access() -> None:
    env = _singapore_env()
    _dispatch(env, runtime.SINGAPORE_CAPABILITY, 2)

    context_calls = [
        call
        for model in env.models.values()
        for call in model.calls
        if call[0] == "with_context"
    ]
    assert context_calls
    assert all(
        call[1] == {"allowed_company_ids": [2], "active_test": False}
        for call in context_calls
    )
    assert not any(
        call[0] == "sudo" for model in env.models.values() for call in model.calls
    )


@pytest.mark.parametrize(
    "payload",
    [
        {
            "capability_id": runtime.CHINA_CAPABILITY,
            "company_id": 1,
            "parameters": {"model": "res.company"},
        },
        {
            "capability_id": "localization.configuration.call",
            "company_id": 1,
            "parameters": {},
        },
        {
            "capability_id": [runtime.CHINA_CAPABILITY],
            "company_id": 1,
            "parameters": {},
        },
        {
            "capability_id": runtime.CHINA_CAPABILITY,
            "company_id": 2,
            "parameters": {},
        },
    ],
)
def test_runtime_rejects_expanded_or_cross_company_payloads(
    payload: dict[str, Any],
) -> None:
    with pytest.raises(Failure) as caught:
        runtime.dispatch(
            _china_env(), payload, 1, failure_type=Failure
        )
    assert caught.value.code == "bridge_protocol_error"
