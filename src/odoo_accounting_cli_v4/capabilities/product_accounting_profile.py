"""Strict contract for one company-scoped product accounting profile."""

from __future__ import annotations

import uuid
from typing import Any, Protocol

from odoo_accounting_cli_v4.capabilities.master_data_lists import MasterDataListError

CAPABILITY_ID = "product.accounting_profile.get"
_ACCOUNT_KEYS = (
    "income",
    "expense",
    "stock_valuation",
    "stock_input",
    "stock_output",
)
_ACCOUNT_MODULE_KEYS = frozenset({"income", "expense"})
_VALUATION_VALUES = frozenset({"periodic", "real_time"})
_COST_METHOD_VALUES = frozenset({"standard", "fifo", "average"})


class ProductAccountingProfilePort(Protocol):
    @property
    def user_id(self) -> int: ...

    def get_profile(self, *, company_id: int, product_id: int) -> dict[str, Any]: ...


class ProductAccountingProfileError(MasterDataListError):
    """Capability-specific error caught by the existing master-data boundary."""


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _valid_id(value: Any) -> bool:
    return _is_integer(value) and value > 0


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _invalid(message: str) -> ProductAccountingProfileError:
    return ProductAccountingProfileError("invalid_request", message, exit_code=2)


def _failed(message: str) -> ProductAccountingProfileError:
    return ProductAccountingProfileError("failed_validation", message, exit_code=8)


def validate_product_accounting_profile_request(
    request: Any,
) -> tuple[str, dict[str, Any], int]:
    """Validate the closed product accounting profile request."""

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
    if not isinstance(request_id, str):
        raise _invalid("request_id must be a UUID string.")
    try:
        parsed_request_id = uuid.UUID(request_id)
    except (AttributeError, ValueError) as exc:
        raise _invalid("request_id must be a UUID string.") from exc
    if (
        str(parsed_request_id) != request_id.lower()
        or parsed_request_id.version not in {1, 2, 3, 4, 5}
        or parsed_request_id.variant != uuid.RFC_4122
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
    for key in ("database", "user_login", "language", "timezone"):
        if not _is_nonempty_string(context[key]):
            raise _invalid(f"context.{key} must be a non-empty string.")
    if not _valid_id(context["company_id"]):
        raise _invalid("context.company_id must be a positive integer.")

    parameters = request["parameters"]
    if (
        not isinstance(parameters, dict)
        or set(parameters) != {"product_id"}
        or not _valid_id(parameters["product_id"])
    ):
        raise _invalid("parameters must contain one positive integer product_id.")
    return request_id, context, parameters["product_id"]


def _valid_optional_company_id(value: Any, company_id: int) -> bool:
    return value is None or (_valid_id(value) and value == company_id)


def _valid_account(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "code", "name"}
        and _valid_id(value["id"])
        and _is_nonempty_string(value["code"])
        and _is_nonempty_string(value["name"])
    )


def _valid_account_slot(value: Any, *, module_available: bool) -> bool:
    if not isinstance(value, dict) or set(value) != {
        "available",
        "reason_code",
        "account",
    }:
        return False
    if not isinstance(value["available"], bool):
        return False
    if value["available"]:
        return (
            module_available
            and value["reason_code"] is None
            and (value["account"] is None or _valid_account(value["account"]))
        )
    expected_reason = "field_unavailable" if module_available else "module_uninstalled"
    return value["reason_code"] == expected_reason and value["account"] is None


def _valid_selection_slot(
    value: Any, *, module_available: bool, allowed: frozenset[str]
) -> bool:
    if not isinstance(value, dict) or set(value) != {
        "available",
        "reason_code",
        "value",
    }:
        return False
    if not isinstance(value["available"], bool):
        return False
    if value["available"]:
        return (
            module_available
            and value["reason_code"] is None
            and isinstance(value["value"], str)
            and value["value"] in allowed
        )
    expected_reason = "field_unavailable" if module_available else "module_uninstalled"
    return value["reason_code"] == expected_reason and value["value"] is None


def _validate_profile(data: Any, *, company_id: int, product_id: int) -> dict[str, Any]:
    if not isinstance(data, dict) or set(data) != {
        "company_id",
        "product",
        "template",
        "category",
        "modules",
        "accounts",
        "valuation",
        "cost_method",
    }:
        raise _failed("Odoo returned an invalid product accounting profile.")
    product = data["product"]
    template = data["template"]
    category = data["category"]
    modules = data["modules"]
    if (
        data["company_id"] != company_id
        or not isinstance(product, dict)
        or set(product)
        != {"id", "name", "default_code", "active", "company_id", "template_id"}
        or product["id"] != product_id
        or not _is_nonempty_string(product["name"])
        or not (
            product["default_code"] is None
            or _is_nonempty_string(product["default_code"])
        )
        or not isinstance(product["active"], bool)
        or not _valid_optional_company_id(product["company_id"], company_id)
        or not _valid_id(product["template_id"])
        or not isinstance(template, dict)
        or set(template) != {"id", "name", "company_id", "category_id"}
        or not _valid_id(template["id"])
        or product["template_id"] != template["id"]
        or not _is_nonempty_string(template["name"])
        or not _valid_optional_company_id(template["company_id"], company_id)
        or not _valid_id(template["category_id"])
        or product["company_id"] != template["company_id"]
        or not isinstance(category, dict)
        or set(category) != {"id", "name", "complete_name"}
        or not _valid_id(category["id"])
        or template["category_id"] != category["id"]
        or not _is_nonempty_string(category["name"])
        or not _is_nonempty_string(category["complete_name"])
        or not isinstance(modules, dict)
        or set(modules) != {"account", "stock_account"}
        or not all(isinstance(value, bool) for value in modules.values())
        or (modules["stock_account"] and not modules["account"])
    ):
        raise _failed("Odoo returned an inconsistent product accounting profile.")

    accounts = data["accounts"]
    if not isinstance(accounts, dict) or set(accounts) != set(_ACCOUNT_KEYS):
        raise _failed("Odoo returned invalid product accounting accounts.")
    for key in _ACCOUNT_KEYS:
        module_available = (
            modules["account"]
            if key in _ACCOUNT_MODULE_KEYS
            else modules["stock_account"]
        )
        if not _valid_account_slot(accounts[key], module_available=module_available):
            raise _failed("Odoo returned invalid product accounting accounts.")
    if not _valid_selection_slot(
        data["valuation"],
        module_available=modules["stock_account"],
        allowed=_VALUATION_VALUES,
    ) or not _valid_selection_slot(
        data["cost_method"],
        module_available=modules["stock_account"],
        allowed=_COST_METHOD_VALUES,
    ):
        raise _failed("Odoo returned invalid product inventory properties.")
    return dict(data)


def _validate_page(port: ProductAccountingProfilePort, page: Any) -> dict[str, Any] | None:
    if not isinstance(page, dict) or set(page) != {
        "user_id",
        "company_visible",
        "module_installed",
        "access_allowed",
        "data",
    }:
        raise _failed("Odoo returned an invalid product accounting page.")
    data = page["data"]
    if (
        not _valid_id(page["user_id"])
        or not _valid_id(port.user_id)
        or page["user_id"] != port.user_id
        or not isinstance(page["company_visible"], bool)
        or not isinstance(page["module_installed"], bool)
        or not isinstance(page["access_allowed"], bool)
        or not (data is None or isinstance(data, dict))
        or (
            page["access_allowed"]
            and not (page["company_visible"] and page["module_installed"])
        )
        or (not page["access_allowed"] and data is not None)
    ):
        raise _failed("Odoo returned an invalid product accounting page.")
    return data


def get_product_accounting_profile(
    port: ProductAccountingProfilePort, request: dict[str, Any]
) -> dict[str, Any]:
    """Read one product's final company-relative accounting properties."""

    _, context, product_id = validate_product_accounting_profile_request(request)
    page = port.get_profile(
        company_id=context["company_id"], product_id=product_id
    )
    data = _validate_page(port, page)
    if not page["company_visible"]:
        raise ProductAccountingProfileError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    if not page["module_installed"]:
        raise ProductAccountingProfileError(
            "uninstalled",
            "The product capability is not installed in this database.",
            exit_code=4,
        )
    if not page["access_allowed"]:
        raise ProductAccountingProfileError(
            "unauthorized",
            "The configured user cannot read product accounting profiles.",
            exit_code=3,
        )
    if data is None:
        raise ProductAccountingProfileError(
            "record_not_found",
            "The requested product was not found.",
            exit_code=4,
        )
    return _validate_profile(
        data, company_id=context["company_id"], product_id=product_id
    )
