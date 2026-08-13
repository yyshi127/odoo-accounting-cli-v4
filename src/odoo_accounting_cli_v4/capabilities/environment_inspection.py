"""Strict contracts for fixed company and environment inspections."""

from __future__ import annotations

import uuid
from typing import Any, Protocol

from odoo_accounting_cli_v4.capabilities.master_data_lists import MasterDataListError


_CAPABILITIES = {
    "company.accounting_configuration.inspect",
    "diagnostic.accounting_environment.inspect",
}
_DIAGNOSTIC_MODULES = ["account", "account_reports", "base"]
_DIAGNOSTIC_MODELS = [
    "account.account",
    "account.journal",
    "account.move",
    "account.move.line",
    "account.report",
    "account.tax",
    "ir.module.module",
    "res.company",
    "res.users",
]


class EnvironmentInspectionPort(Protocol):
    @property
    def user_id(self) -> int: ...

    def inspect(self, *, company_id: int) -> dict[str, Any]: ...


def _invalid(message: str) -> MasterDataListError:
    return MasterDataListError("invalid_request", message, exit_code=2)


def validate_environment_inspection_request(
    capability_id: str, request: Any
) -> dict[str, Any]:
    if capability_id not in _CAPABILITIES:
        raise MasterDataListError(
            "unsupported_capability", "The inspection is unsupported.", exit_code=4
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
    try:
        parsed = uuid.UUID(request["request_id"])
    except (AttributeError, TypeError, ValueError) as exc:
        raise _invalid("request_id must be a UUID string.") from exc
    if str(parsed) != request["request_id"].lower():
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
    if any(
        not isinstance(context[key], str) or not context[key].strip()
        for key in ("database", "user_login", "language", "timezone")
    ):
        raise _invalid("The string context fields must be non-empty.")
    if (
        not isinstance(context["company_id"], int)
        or isinstance(context["company_id"], bool)
        or context["company_id"] <= 0
    ):
        raise _invalid("context.company_id must be a positive integer.")
    if request["parameters"] != {}:
        raise _invalid(f"{capability_id} accepts no parameters.")
    return context


def read_environment_inspection(
    capability_id: str,
    port: EnvironmentInspectionPort,
    request: dict[str, Any],
) -> dict[str, Any]:
    context = validate_environment_inspection_request(capability_id, request)
    page = port.inspect(company_id=context["company_id"])
    if page["company_visible"] is not True:
        raise MasterDataListError(
            "company_unavailable", "The company is unavailable.", exit_code=3
        )
    if page["module_installed"] is not True:
        raise MasterDataListError(
            "module_uninstalled", "The required Odoo models are unavailable.", exit_code=4
        )
    if page["access_allowed"] is not True:
        raise MasterDataListError(
            "unauthorized", "The configured user cannot run the inspection.", exit_code=3
        )
    if page["user_id"] != port.user_id:
        raise MasterDataListError(
            "failed_validation", "The Odoo user identity is inconsistent.", exit_code=8
        )
    data = page["data"]
    try:
        if data["company"]["id"] != context["company_id"]:
            raise ValueError
        if capability_id == "diagnostic.accounting_environment.inspect":
            if data["user"]["id"] != page["user_id"]:
                raise ValueError
            if [item["name"] for item in data["modules"]] != _DIAGNOSTIC_MODULES:
                raise ValueError
            if [item["model"] for item in data["models"]] != _DIAGNOSTIC_MODELS:
                raise ValueError
            if data["transaction_read_only"] is not True:
                raise ValueError
    except (KeyError, TypeError, ValueError) as exc:
        raise MasterDataListError(
            "failed_validation",
            "The Odoo inspection result is inconsistent.",
            exit_code=8,
        ) from exc
    return data
