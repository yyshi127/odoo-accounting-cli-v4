"""Odoo-side runtime for fixed China and Singapore readiness inspections."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

ACTION = "accounting.localization_configuration.inspect"
CHINA_CAPABILITY = "localization.china.configuration.inspect"
SINGAPORE_CAPABILITY = "localization.singapore.configuration.inspect"
CAPABILITY_IDS = frozenset({CHINA_CAPABILITY, SINGAPORE_CAPABILITY})

_COMMON_COMPANY_FIELDS = {
    "account_fiscal_country_id",
    "account_purchase_tax_id",
    "account_sale_tax_id",
    "chart_template",
}
_COMMON_FIELDS = {
    "res.company": _COMMON_COMPANY_FIELDS,
    "res.country": {"code"},
    "account.tax": {"amount", "company_id", "name", "type_tax_use"},
    "ir.module.module": {"name", "state"},
}
_CHINA_FIELDS = {
    **_COMMON_FIELDS,
    "account.account": {"company_ids"},
    "account.move": set(),
    "ir.actions.report": {"model", "name", "report_name", "report_type"},
}
_SINGAPORE_FIELDS = {
    **_COMMON_FIELDS,
    "res.company": _COMMON_COMPANY_FIELDS | {"currency_id", "partner_id", "vat"},
    "res.currency": {"name"},
    "account.report": {
        "availability_condition",
        "country_id",
        "name",
        "root_report_id",
    },
    "res.partner.bank": {"partner_id"},
}
_CHINA_MODULES = ("l10n_cn", "l10n_cn_oscg")
_SINGAPORE_MODULES = ("l10n_sg",)
_CHINA_MISSING_ORDER = (
    "fiscal_country",
    "chart_template",
    "l10n_cn",
    "l10n_cn_oscg",
    "accounts",
    "default_sale_tax",
    "default_purchase_tax",
    "fapiao_field",
    "voucher_report",
)
_SINGAPORE_MISSING_ORDER = (
    "fiscal_country",
    "chart_template",
    "currency",
    "default_sale_gst",
    "default_purchase_gst",
    "tax_report",
    "uen",
    "vat",
    "paynow",
)


def _failure(failure_type: Any, code: str, message: str, exit_code: int) -> Exception:
    return failure_type(code, message, exit_code=exit_code)


def _protocol_failure(failure_type: Any) -> Exception:
    return _failure(
        failure_type,
        "bridge_protocol_error",
        "The bridge action payload is invalid.",
        7,
    )


def _runtime_failure(failure_type: Any) -> Exception:
    return _failure(
        failure_type,
        "odoo_runtime_error",
        "The Odoo runtime request failed.",
        7,
    )


def _integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _positive_id(value: Any) -> bool:
    return _integer(value) and value > 0


def _validated_payload(payload: Any, company_id: int, failure_type: Any) -> str:
    if (
        not isinstance(payload, dict)
        or set(payload) != {"capability_id", "company_id", "parameters"}
        or not isinstance(payload["capability_id"], str)
        or payload["capability_id"] not in CAPABILITY_IDS
        or payload["company_id"] != company_id
        or not _positive_id(company_id)
        or payload["parameters"] != {}
    ):
        raise _protocol_failure(failure_type)
    return payload["capability_id"]


def _empty_page(
    env: Any,
    *,
    company_visible: bool,
    module_installed: bool,
    access_allowed: bool,
) -> dict[str, Any]:
    return {
        "user_id": env.uid,
        "company_visible": company_visible,
        "module_installed": module_installed,
        "access_allowed": access_allowed,
        "cursor_found": True,
        "items": [],
    }


def _required_fields(capability_id: str) -> dict[str, set[str]]:
    return _CHINA_FIELDS if capability_id == CHINA_CAPABILITY else _SINGAPORE_FIELDS


def _field_shape_available(env: Any, capability_id: str) -> bool:
    return all(
        fields <= set(getattr(env[model_name], "_fields", {}))
        for model_name, fields in _required_fields(capability_id).items()
    )


def _scope_page(
    env: Any, capability_id: str, company_id: int, failure_type: Any
) -> dict[str, Any]:
    company_visible = bool(
        env["res.company"].search_count([("id", "=", company_id)], limit=1)
    )
    models = tuple(_required_fields(capability_id))
    module_installed = all(env.registry.get(name) is not None for name in models)
    if company_visible and module_installed and not _field_shape_available(
        env, capability_id
    ):
        raise _runtime_failure(failure_type)
    access_allowed = bool(
        company_visible
        and module_installed
        and env.user.has_group("account.group_account_readonly")
        and all(env[name].has_access("read") for name in models)
    )
    return _empty_page(
        env,
        company_visible=company_visible,
        module_installed=module_installed,
        access_allowed=access_allowed,
    )


def _model(env: Any, name: str, company_id: int) -> Any:
    return env[name].with_context(
        allowed_company_ids=[company_id],
        active_test=False,
    )


def _text(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("invalid text")
    return value


def _optional_text(value: Any) -> str | None:
    return None if value in (False, None) else _text(value)


def _reference_id(value: Any) -> int | None:
    if value in (False, None):
        return None
    if isinstance(value, (list, tuple)) and len(value) == 2:
        value = value[0]
    else:
        value = getattr(value, "id", value)
    if not _positive_id(value):
        raise ValueError("invalid record reference")
    return value


def _decimal_text(value: Any) -> str:
    if isinstance(value, bool):
        raise TypeError("invalid decimal")
    number = Decimal(str(value))
    if not number.is_finite():
        raise ValueError("invalid decimal")
    if number == 0:
        return "0"
    rendered = format(number, "f")
    return rendered.rstrip("0").rstrip(".") if "." in rendered else rendered


def _module_states(
    env: Any, company_id: int, names: tuple[str, ...]
) -> dict[str, bool]:
    rows = _model(env, "ir.module.module", company_id).search_read(
        [("name", "in", list(names))],
        fields=["id", "name", "state"],
        order="name",
        limit=len(names) + 1,
    )
    states: dict[str, bool] = {name: False for name in names}
    seen: set[str] = set()
    for row in rows:
        name = row.get("name")
        if name not in states or name in seen or not _positive_id(row.get("id")):
            raise ValueError("invalid module rows")
        seen.add(name)
        states[name] = row.get("state") == "installed"
    return states


def _company_row(
    env: Any,
    company_id: int,
    fields: list[str],
) -> dict[str, Any]:
    rows = _model(env, "res.company", company_id).search_read(
        [("id", "=", company_id)],
        fields=["id", *fields],
        limit=2,
    )
    if len(rows) != 1 or rows[0].get("id") != company_id:
        raise ValueError("company disappeared")
    return rows[0]


def _code(
    env: Any, model_name: str, record_id: int | None, company_id: int
) -> str | None:
    if record_id is None:
        return None
    rows = _model(env, model_name, company_id).search_read(
        [("id", "=", record_id)],
        fields=["id", "code" if model_name == "res.country" else "name"],
        limit=2,
    )
    key = "code" if model_name == "res.country" else "name"
    if len(rows) != 1 or rows[0].get("id") != record_id:
        raise ValueError("related record disappeared")
    return _text(rows[0].get(key))


def _tax(
    env: Any,
    tax_id: int | None,
    company_id: int,
) -> dict[str, Any] | None:
    if tax_id is None:
        return None
    rows = _model(env, "account.tax", company_id).search_read(
        [("id", "=", tax_id), ("company_id", "=", company_id)],
        fields=["id", "name", "amount", "type_tax_use", "company_id"],
        limit=2,
    )
    if len(rows) != 1 or rows[0].get("id") != tax_id:
        raise ValueError("default tax is outside the company scope")
    row = rows[0]
    if _reference_id(row.get("company_id")) != company_id or row.get(
        "type_tax_use"
    ) not in {"sale", "purchase"}:
        raise ValueError("invalid default tax")
    return {
        "id": tax_id,
        "name": _text(row.get("name")),
        "rate": _decimal_text(row.get("amount")),
        "type_tax_use": row["type_tax_use"],
    }


def _tax_ready(value: dict[str, Any] | None, expected_type: str) -> bool:
    return bool(
        value is not None
        and value["type_tax_use"] == expected_type
        and Decimal(value["rate"]) > 0
    )


def _xml_record_id(env: Any, xml_id: str) -> int | None:
    return _reference_id(env.ref(xml_id, raise_if_not_found=False))


def _voucher_report_ready(env: Any, company_id: int) -> bool:
    report_id = _xml_record_id(env, "l10n_cn.account_voucher_cn")
    if report_id is None:
        return False
    rows = _model(env, "ir.actions.report", company_id).search_read(
        [("id", "=", report_id)],
        fields=["id", "name", "model", "report_type", "report_name"],
        limit=2,
    )
    return bool(
        len(rows) == 1
        and rows[0].get("id") == report_id
        and _text(rows[0].get("name"))
        and rows[0].get("model") == "account.move"
        and rows[0].get("report_type") == "qweb-pdf"
        and rows[0].get("report_name") == "l10n_cn.report_voucher"
    )


def _singapore_tax_report(
    env: Any, company_id: int, country_id: int | None
) -> dict[str, Any] | None:
    if country_id is None:
        return None
    report_id = _xml_record_id(env, "l10n_sg.tax_report")
    if report_id is None:
        return None
    rows = _model(env, "account.report", company_id).search_read(
        [("id", "=", report_id), ("country_id", "=", country_id)],
        fields=[
            "id",
            "name",
            "country_id",
            "root_report_id",
            "availability_condition",
        ],
        limit=2,
    )
    if not rows:
        return None
    if len(rows) != 1 or rows[0].get("id") != report_id:
        raise ValueError("ambiguous Singapore tax report")
    row = rows[0]
    if (
        _reference_id(row.get("country_id")) != country_id
        or _reference_id(row.get("root_report_id")) is None
        or row.get("availability_condition") != "country"
    ):
        return None
    return {"id": report_id, "name": _text(row.get("name"))}


def _china_result(env: Any, company_id: int) -> dict[str, Any]:
    modules = _module_states(env, company_id, _CHINA_MODULES)
    if modules["l10n_cn"] and "fapiao" not in getattr(
        env["account.move"], "_fields", {}
    ):
        raise ValueError("installed China localization is missing fapiao")
    company = _company_row(
        env,
        company_id,
        [
            "account_fiscal_country_id",
            "account_purchase_tax_id",
            "account_sale_tax_id",
            "chart_template",
        ],
    )
    fiscal_country_code = _code(
        env,
        "res.country",
        _reference_id(company.get("account_fiscal_country_id")),
        company_id,
    )
    sale_tax = _tax(
        env, _reference_id(company.get("account_sale_tax_id")), company_id
    )
    purchase_tax = _tax(
        env, _reference_id(company.get("account_purchase_tax_id")), company_id
    )
    account_count = _model(env, "account.account", company_id).search_count(
        [("company_ids", "in", [company_id])]
    )
    if not _integer(account_count) or account_count < 0:
        raise ValueError("invalid account count")
    voucher_report_ready = bool(
        modules["l10n_cn"] and _voucher_report_ready(env, company_id)
    )
    result = {
        "company_id": company_id,
        "fiscal_country_code": fiscal_country_code,
        "chart_template": _optional_text(company.get("chart_template")),
        "modules": modules,
        "account_count": account_count,
        "default_sale_tax": sale_tax,
        "default_purchase_tax": purchase_tax,
        "fapiao_field_ready": bool(
            modules["l10n_cn"]
            and "fapiao" in getattr(env["account.move"], "_fields", {})
        ),
        "voucher_report_ready": voucher_report_ready,
    }
    checks = {
        "fiscal_country": fiscal_country_code == "CN",
        "chart_template": result["chart_template"] == "cn_oscg",
        "l10n_cn": modules["l10n_cn"],
        "l10n_cn_oscg": modules["l10n_cn_oscg"],
        "accounts": account_count > 0,
        "default_sale_tax": _tax_ready(sale_tax, "sale"),
        "default_purchase_tax": _tax_ready(purchase_tax, "purchase"),
        "fapiao_field": result["fapiao_field_ready"],
        "voucher_report": voucher_report_ready,
    }
    missing = [name for name in _CHINA_MISSING_ORDER if not checks[name]]
    return {**result, "configured": not missing, "missing": missing}


def _singapore_result(env: Any, company_id: int) -> dict[str, Any]:
    modules = _module_states(env, company_id, _SINGAPORE_MODULES)
    installed = modules["l10n_sg"]
    company_fields = [
        "account_fiscal_country_id",
        "account_purchase_tax_id",
        "account_sale_tax_id",
        "chart_template",
        "currency_id",
        "partner_id",
        "vat",
    ]
    if installed:
        company_fields.append("l10n_sg_unique_entity_number")
        if "l10n_sg_unique_entity_number" not in getattr(
            env["res.company"], "_fields", {}
        ) or not {"proxy_type", "proxy_value"} <= set(
            getattr(env["res.partner.bank"], "_fields", {})
        ):
            raise ValueError("installed Singapore localization fields are unavailable")
    company = _company_row(env, company_id, company_fields)
    country_id = _reference_id(company.get("account_fiscal_country_id"))
    fiscal_country_code = _code(
        env, "res.country", country_id, company_id
    )
    currency_code = _code(
        env,
        "res.currency",
        _reference_id(company.get("currency_id")),
        company_id,
    )
    sale_tax = _tax(
        env, _reference_id(company.get("account_sale_tax_id")), company_id
    )
    purchase_tax = _tax(
        env, _reference_id(company.get("account_purchase_tax_id")), company_id
    )
    tax_report = (
        _singapore_tax_report(env, company_id, country_id) if installed else None
    )
    partner_id = _reference_id(company.get("partner_id"))
    paynow_configured = False
    if installed and partner_id is not None:
        paynow_configured = bool(
            _model(env, "res.partner.bank", company_id).search_count(
                [
                    ("partner_id", "=", partner_id),
                    ("proxy_type", "in", ["mobile", "uen"]),
                    ("proxy_value", "!=", False),
                ],
                limit=1,
            )
        )
    result = {
        "company_id": company_id,
        "fiscal_country_code": fiscal_country_code,
        "chart_template": _optional_text(company.get("chart_template")),
        "currency_code": currency_code,
        "default_sale_tax": sale_tax,
        "default_purchase_tax": purchase_tax,
        "tax_report": tax_report,
        "uen_configured": bool(
            installed
            and _optional_text(company.get("l10n_sg_unique_entity_number"))
        ),
        "vat_configured": bool(_optional_text(company.get("vat"))),
        "paynow_configured": paynow_configured,
    }
    checks = {
        "fiscal_country": fiscal_country_code == "SG",
        "chart_template": result["chart_template"] == "sg",
        "currency": currency_code == "SGD",
        "default_sale_gst": _tax_ready(sale_tax, "sale"),
        "default_purchase_gst": _tax_ready(purchase_tax, "purchase"),
        "tax_report": tax_report is not None,
        "uen": result["uen_configured"],
        "vat": result["vat_configured"],
        "paynow": result["paynow_configured"],
    }
    missing = [name for name in _SINGAPORE_MISSING_ORDER if not checks[name]]
    return {**result, "configured": not missing, "missing": missing}


def dispatch(
    env: Any,
    payload: dict[str, Any],
    company_id: int,
    *,
    failure_type: Any,
) -> dict[str, Any]:
    """Validate, gate, and execute one fixed localization readiness read."""

    try:
        capability_id = _validated_payload(payload, company_id, failure_type)
        page = _scope_page(env, capability_id, company_id, failure_type)
        if not page["access_allowed"]:
            return page
        item = (
            _china_result(env, company_id)
            if capability_id == CHINA_CAPABILITY
            else _singapore_result(env, company_id)
        )
        return {**page, "items": [item]}
    except failure_type:
        raise
    except Exception as exc:
        raise _runtime_failure(failure_type) from exc
