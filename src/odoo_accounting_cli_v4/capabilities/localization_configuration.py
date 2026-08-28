"""Closed contracts for China and Singapore localization readiness reads."""

from __future__ import annotations

import re
import uuid
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol

CAPABILITY_IDS = frozenset(
    {
        "localization.china.configuration.inspect",
        "localization.singapore.configuration.inspect",
    }
)
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
_DECIMAL_PATTERN = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")


class LocalizationConfigurationPort(Protocol):
    @property
    def user_id(self) -> int: ...

    def read(
        self,
        *,
        capability_id: str,
        company_id: int,
        parameters: dict[str, Any],
    ) -> dict[str, Any]: ...


class LocalizationConfigurationReadError(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        exit_code: int,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code
        self.retryable = retryable
        self.details = details or {}


def _invalid(message: str) -> LocalizationConfigurationReadError:
    return LocalizationConfigurationReadError("invalid_request", message, exit_code=2)


def _failed(message: str) -> LocalizationConfigurationReadError:
    return LocalizationConfigurationReadError("failed_validation", message, exit_code=8)


def _integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _positive_id(value: Any) -> bool:
    return _integer(value) and value > 0


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _optional_text(value: Any) -> bool:
    return value is None or _text(value)


def validate_localization_configuration_request(
    capability_id: str, request: Any
) -> tuple[str, dict[str, Any]]:
    """Validate one parameterless v1 localization inspection request."""

    if capability_id not in CAPABILITY_IDS:
        raise LocalizationConfigurationReadError(
            "unsupported_capability",
            "The localization configuration capability is unsupported.",
            exit_code=4,
        )
    if not isinstance(request, dict) or set(request) != {
        "schema_version",
        "request_id",
        "context",
        "parameters",
    }:
        raise _invalid("The request must match the v1 request envelope.")
    if request["schema_version"] != "v1":
        raise _invalid("schema_version must be 'v1'.")
    request_id = request["request_id"]
    try:
        parsed = uuid.UUID(request_id) if isinstance(request_id, str) else None
    except ValueError as exc:
        raise _invalid("request_id must be a UUID string.") from exc
    if (
        parsed is None
        or str(parsed) != request_id.lower()
        or parsed.version not in {1, 2, 3, 4, 5}
        or parsed.variant != uuid.RFC_4122
    ):
        raise _invalid("request_id must use canonical UUID syntax.")
    context = request["context"]
    if not isinstance(context, dict) or set(context) != {
        "database",
        "company_id",
        "user_login",
        "language",
        "timezone",
    }:
        raise _invalid("context must contain only the required v1 fields.")
    if not all(
        _text(context.get(key))
        for key in ("database", "user_login", "language", "timezone")
    ) or not _positive_id(context.get("company_id")):
        raise _invalid("context contains an invalid value.")
    if request["parameters"] != {}:
        raise _invalid(f"{capability_id} accepts no parameters.")
    return request_id, context


def _decimal(value: Any) -> Decimal | None:
    if not isinstance(value, str) or _DECIMAL_PATTERN.fullmatch(value) is None:
        return None
    try:
        number = Decimal(value)
    except InvalidOperation:
        return None
    if not number.is_finite():
        return None
    if number == 0:
        canonical = "0"
    else:
        canonical = format(number, "f")
        if "." in canonical:
            canonical = canonical.rstrip("0").rstrip(".")
    return number if canonical == value else None


def _tax(value: Any) -> bool:
    return bool(
        value is None
        or isinstance(value, dict)
        and set(value) == {"id", "name", "rate", "type_tax_use"}
        and _positive_id(value["id"])
        and _text(value["name"])
        and _decimal(value["rate"]) is not None
        and value["type_tax_use"] in {"sale", "purchase"}
    )


def _tax_ready(value: Any, expected_type: str) -> bool:
    return bool(
        value is not None
        and _tax(value)
        and value["type_tax_use"] == expected_type
        and _decimal(value["rate"]) > 0
    )


def _named(value: Any) -> bool:
    return bool(
        value is None
        or isinstance(value, dict)
        and set(value) == {"id", "name"}
        and _positive_id(value["id"])
        and _text(value["name"])
    )


def _china_result(value: Any, company_id: int) -> bool:
    keys = {
        "company_id",
        "fiscal_country_code",
        "chart_template",
        "modules",
        "account_count",
        "default_sale_tax",
        "default_purchase_tax",
        "fapiao_field_ready",
        "voucher_report_ready",
        "configured",
        "missing",
    }
    if not isinstance(value, dict) or set(value) != keys:
        return False
    modules = value["modules"]
    if not (
        value["company_id"] == company_id
        and _optional_text(value["fiscal_country_code"])
        and _optional_text(value["chart_template"])
        and isinstance(modules, dict)
        and set(modules) == {"l10n_cn", "l10n_cn_oscg"}
        and all(isinstance(item, bool) for item in modules.values())
        and _integer(value["account_count"])
        and value["account_count"] >= 0
        and _tax(value["default_sale_tax"])
        and _tax(value["default_purchase_tax"])
        and isinstance(value["fapiao_field_ready"], bool)
        and isinstance(value["voucher_report_ready"], bool)
        and isinstance(value["configured"], bool)
        and isinstance(value["missing"], list)
    ):
        return False
    checks = {
        "fiscal_country": value["fiscal_country_code"] == "CN",
        "chart_template": value["chart_template"] == "cn_oscg",
        "l10n_cn": modules["l10n_cn"],
        "l10n_cn_oscg": modules["l10n_cn_oscg"],
        "accounts": value["account_count"] > 0,
        "default_sale_tax": _tax_ready(value["default_sale_tax"], "sale"),
        "default_purchase_tax": _tax_ready(
            value["default_purchase_tax"], "purchase"
        ),
        "fapiao_field": value["fapiao_field_ready"],
        "voucher_report": value["voucher_report_ready"],
    }
    expected = [name for name in _CHINA_MISSING_ORDER if not checks[name]]
    return value["missing"] == expected and value["configured"] == (not expected)


def _singapore_result(value: Any, company_id: int) -> bool:
    keys = {
        "company_id",
        "fiscal_country_code",
        "chart_template",
        "currency_code",
        "default_sale_tax",
        "default_purchase_tax",
        "tax_report",
        "uen_configured",
        "vat_configured",
        "paynow_configured",
        "configured",
        "missing",
    }
    if not isinstance(value, dict) or set(value) != keys:
        return False
    if not (
        value["company_id"] == company_id
        and _optional_text(value["fiscal_country_code"])
        and _optional_text(value["chart_template"])
        and _optional_text(value["currency_code"])
        and _tax(value["default_sale_tax"])
        and _tax(value["default_purchase_tax"])
        and _named(value["tax_report"])
        and all(
            isinstance(value[key], bool)
            for key in (
                "uen_configured",
                "vat_configured",
                "paynow_configured",
                "configured",
            )
        )
        and isinstance(value["missing"], list)
    ):
        return False
    checks = {
        "fiscal_country": value["fiscal_country_code"] == "SG",
        "chart_template": value["chart_template"] == "sg",
        "currency": value["currency_code"] == "SGD",
        "default_sale_gst": _tax_ready(value["default_sale_tax"], "sale"),
        "default_purchase_gst": _tax_ready(
            value["default_purchase_tax"], "purchase"
        ),
        "tax_report": value["tax_report"] is not None,
        "uen": value["uen_configured"],
        "vat": value["vat_configured"],
        "paynow": value["paynow_configured"],
    }
    expected = [name for name in _SINGAPORE_MISSING_ORDER if not checks[name]]
    return value["missing"] == expected and value["configured"] == (not expected)


def _validated_page(port: LocalizationConfigurationPort, page: Any) -> list[Any]:
    if not isinstance(page, dict) or set(page) != {
        "user_id",
        "company_visible",
        "module_installed",
        "access_allowed",
        "cursor_found",
        "items",
    }:
        raise _failed("Odoo returned an invalid localization configuration page.")
    if not (
        _positive_id(page["user_id"])
        and page["user_id"] == port.user_id
        and all(
            isinstance(page[key], bool)
            for key in (
                "company_visible",
                "module_installed",
                "access_allowed",
                "cursor_found",
            )
        )
        and isinstance(page["items"], list)
        and all(isinstance(item, dict) for item in page["items"])
        and (
            not page["access_allowed"]
            or page["company_visible"] and page["module_installed"]
        )
        and (page["access_allowed"] or not page["items"])
    ):
        raise _failed("Odoo returned an inconsistent localization configuration page.")
    return page["items"]


def _availability(page: dict[str, Any]) -> None:
    if not page["company_visible"]:
        raise LocalizationConfigurationReadError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    if not page["module_installed"]:
        raise LocalizationConfigurationReadError(
            "uninstalled",
            "The accounting models required for this inspection are unavailable.",
            exit_code=4,
        )
    if not page["access_allowed"]:
        raise LocalizationConfigurationReadError(
            "unauthorized",
            "The configured user cannot inspect localization readiness.",
            exit_code=3,
        )


def read_localization_configuration(
    capability_id: str,
    port: LocalizationConfigurationPort,
    request: dict[str, Any],
) -> dict[str, Any]:
    """Read one verified, company-scoped localization readiness result."""

    _, context = validate_localization_configuration_request(capability_id, request)
    page = port.read(
        capability_id=capability_id,
        company_id=context["company_id"],
        parameters={},
    )
    items = _validated_page(port, page)
    _availability(page)
    if not page["cursor_found"] or len(items) != 1:
        raise _failed("Odoo returned no unique localization configuration result.")
    valid = (
        _china_result(items[0], context["company_id"])
        if capability_id == "localization.china.configuration.inspect"
        else _singapore_result(items[0], context["company_id"])
    )
    if not valid:
        raise _failed("Odoo returned an inconsistent localization readiness result.")
    return items[0]
