"""Strict contract for resolving one company-scoped fiscal position."""

from __future__ import annotations

import uuid
from typing import Any, Protocol

from odoo_accounting_cli_v4.capabilities.master_data_lists import MasterDataListError


CAPABILITY_ID = "fiscal_position.resolve"
_PARAMETER_KEYS = {
    "partner_id",
    "delivery_partner_id",
    "account_id",
    "tax_ids",
}
_MAX_TAX_IDS = 100


class FiscalPositionResolvePort(Protocol):
    @property
    def user_id(self) -> int: ...

    def resolve(
        self,
        *,
        company_id: int,
        partner_id: int,
        delivery_partner_id: int | None,
        account_id: int | None,
        tax_ids: list[int] | None,
    ) -> dict[str, Any]: ...


class FiscalPositionResolveError(MasterDataListError):
    """Capability-specific error caught by the existing read boundary."""


def _valid_id(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _invalid(message: str) -> FiscalPositionResolveError:
    return FiscalPositionResolveError("invalid_request", message, exit_code=2)


def _failed(message: str) -> FiscalPositionResolveError:
    return FiscalPositionResolveError("failed_validation", message, exit_code=8)


def validate_fiscal_position_resolve_request(
    request: Any,
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    """Validate and normalize the closed fiscal-position request."""

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
        if not _nonempty_string(context[key]):
            raise _invalid(f"context.{key} must be a non-empty string.")
    if not _valid_id(context["company_id"]):
        raise _invalid("context.company_id must be a positive integer.")

    parameters = request["parameters"]
    if (
        not isinstance(parameters, dict)
        or "partner_id" not in parameters
        or not set(parameters).issubset(_PARAMETER_KEYS)
        or not _valid_id(parameters["partner_id"])
    ):
        raise _invalid(
            "parameters must contain a positive partner_id and only supported mappings."
        )
    for key in ("delivery_partner_id", "account_id"):
        if key in parameters and not _valid_id(parameters[key]):
            raise _invalid(f"parameters.{key} must be a positive integer.")
    tax_ids = parameters.get("tax_ids")
    if "tax_ids" in parameters and (
        not isinstance(tax_ids, list)
        or not 1 <= len(tax_ids) <= _MAX_TAX_IDS
        or any(not _valid_id(item) for item in tax_ids)
        or len(set(tax_ids)) != len(tax_ids)
    ):
        raise _invalid(
            "parameters.tax_ids must contain 1 to 100 unique positive integers."
        )

    normalized = {
        "partner_id": parameters["partner_id"],
        "delivery_partner_id": parameters.get("delivery_partner_id"),
        "account_id": parameters.get("account_id"),
        "tax_ids": None if tax_ids is None else list(tax_ids),
    }
    return request_id, dict(context), normalized


def _validate_page(
    port: FiscalPositionResolvePort, page: Any
) -> dict[str, Any] | None:
    if not isinstance(page, dict) or set(page) != {
        "user_id",
        "company_visible",
        "module_installed",
        "access_allowed",
        "data",
    }:
        raise _failed("Odoo returned an invalid fiscal-position page.")
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
        raise _failed("Odoo returned an invalid fiscal-position page.")
    return data


def _valid_fiscal_position(value: Any) -> bool:
    return (
        value is None
        or (
            isinstance(value, dict)
            and set(value) == {"id", "name"}
            and _valid_id(value["id"])
            and _nonempty_string(value["name"])
        )
    )


def _valid_account_mapping(value: Any, account_id: int | None) -> bool:
    if account_id is None:
        return value is None
    return (
        isinstance(value, dict)
        and set(value) == {"source_id", "mapped_id"}
        and value["source_id"] == account_id
        and _valid_id(value["mapped_id"])
    )


def _valid_tax_mapping(value: Any, tax_ids: list[int] | None) -> bool:
    if tax_ids is None:
        return value is None
    if not isinstance(value, dict) or set(value) != {"source_ids", "mapped_ids"}:
        return False
    source_ids = value["source_ids"]
    mapped_ids = value["mapped_ids"]
    return (
        source_ids == tax_ids
        and isinstance(mapped_ids, list)
        and all(_valid_id(item) for item in mapped_ids)
        and len(set(mapped_ids)) == len(mapped_ids)
    )


def _validate_result(
    data: Any, *, company_id: int, parameters: dict[str, Any]
) -> dict[str, Any]:
    if not isinstance(data, dict) or set(data) != {
        "company_id",
        "partner_id",
        "delivery_partner_id",
        "fiscal_position",
        "account_mapping",
        "tax_mapping",
    }:
        raise _failed("Odoo returned an invalid fiscal-position result.")
    fiscal_position = data["fiscal_position"]
    account_mapping = data["account_mapping"]
    tax_mapping = data["tax_mapping"]
    if (
        data["company_id"] != company_id
        or data["partner_id"] != parameters["partner_id"]
        or data["delivery_partner_id"] != parameters["delivery_partner_id"]
        or not _valid_fiscal_position(fiscal_position)
        or not _valid_account_mapping(account_mapping, parameters["account_id"])
        or not _valid_tax_mapping(tax_mapping, parameters["tax_ids"])
        or (
            fiscal_position is None
            and account_mapping is not None
            and account_mapping["mapped_id"] != account_mapping["source_id"]
        )
        or (
            fiscal_position is None
            and tax_mapping is not None
            and tax_mapping["mapped_ids"] != tax_mapping["source_ids"]
        )
    ):
        raise _failed("Odoo returned an inconsistent fiscal-position result.")
    return {
        "company_id": data["company_id"],
        "partner_id": data["partner_id"],
        "delivery_partner_id": data["delivery_partner_id"],
        "fiscal_position": (
            None if fiscal_position is None else dict(fiscal_position)
        ),
        "account_mapping": (
            None if account_mapping is None else dict(account_mapping)
        ),
        "tax_mapping": (
            None
            if tax_mapping is None
            else {
                "source_ids": list(tax_mapping["source_ids"]),
                "mapped_ids": list(tax_mapping["mapped_ids"]),
            }
        ),
    }


def resolve_fiscal_position(
    port: FiscalPositionResolvePort, request: dict[str, Any]
) -> dict[str, Any]:
    """Resolve Odoo's fiscal position and optional native mappings."""

    _, context, parameters = validate_fiscal_position_resolve_request(request)
    page = port.resolve(company_id=context["company_id"], **parameters)
    data = _validate_page(port, page)
    if not page["company_visible"]:
        raise FiscalPositionResolveError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    if not page["module_installed"]:
        raise FiscalPositionResolveError(
            "module_uninstalled",
            "The fiscal-position capability is not installed in this database.",
            exit_code=4,
        )
    if not page["access_allowed"]:
        raise FiscalPositionResolveError(
            "unauthorized",
            "The configured user cannot resolve fiscal positions.",
            exit_code=3,
        )
    if data is None:
        raise FiscalPositionResolveError(
            "record_not_found",
            "One or more requested accounting records were not found.",
            exit_code=4,
        )
    return _validate_result(
        data, company_id=context["company_id"], parameters=parameters
    )
