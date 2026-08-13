"""Strict contract for the configured user's accounting-access inspection."""

from __future__ import annotations

import uuid
from typing import Any, Protocol

from odoo_accounting_cli_v4.capabilities.master_data_lists import MasterDataListError


CAPABILITY_ID = "user.accounting_access.inspect"
_GROUPS = (
    "base.group_user",
    "account.group_account_readonly",
    "account.group_account_invoice",
    "account.group_account_user",
    "account.group_account_manager",
)
_MODELS = (
    "account.account",
    "account.journal",
    "account.move",
    "account.move.line",
    "account.report",
    "account.tax",
)


class AccountingAccessPort(Protocol):
    @property
    def user_id(self) -> int: ...

    def inspect(self, *, company_id: int) -> dict[str, Any]: ...


def _invalid(message: str) -> MasterDataListError:
    return MasterDataListError("invalid_request", message, exit_code=2)


def _failed(message: str) -> MasterDataListError:
    return MasterDataListError("failed_validation", message, exit_code=8)


def validate_accounting_access_request(request: Any) -> dict[str, Any]:
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
        request_id = uuid.UUID(request["request_id"])
    except (AttributeError, TypeError, ValueError) as exc:
        raise _invalid("request_id must be a UUID string.") from exc
    if str(request_id) != request["request_id"].lower():
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
        raise _invalid("user.accounting_access.inspect accepts no parameters.")
    return context


def read_accounting_access(
    port: AccountingAccessPort, request: dict[str, Any]
) -> dict[str, Any]:
    context = validate_accounting_access_request(request)
    page = port.inspect(company_id=context["company_id"])
    if page.get("company_visible") is not True:
        raise MasterDataListError(
            "company_unavailable", "The company is unavailable.", exit_code=3
        )
    if page.get("module_installed") is not True:
        raise MasterDataListError(
            "module_uninstalled", "The required Odoo models are unavailable.", exit_code=4
        )
    if page.get("access_allowed") is not True:
        raise MasterDataListError(
            "unauthorized", "The configured user cannot inspect its access.", exit_code=3
        )
    if page.get("user_id") != port.user_id:
        raise _failed("The Odoo user identity is inconsistent.")
    user = page.get("user")
    groups = page.get("groups")
    model_acl = page.get("model_acl")
    if (
        page.get("company_id") != context["company_id"]
        or not isinstance(user, dict)
        or set(user) != {"id", "login", "name", "active", "company_ids"}
        or user.get("id") != port.user_id
        or user.get("login") != context["user_login"]
        or not isinstance(user.get("name"), str)
        or not user["name"].strip()
        or user.get("active") is not True
        or not isinstance(user.get("company_ids"), list)
        or context["company_id"] not in user["company_ids"]
        or not isinstance(groups, list)
        or [item.get("xml_id") for item in groups if isinstance(item, dict)]
        != list(_GROUPS)
        or any(set(item) != {"xml_id", "member"} or not isinstance(item["member"], bool) for item in groups)
        or not isinstance(model_acl, list)
        or [item.get("model") for item in model_acl if isinstance(item, dict)]
        != list(_MODELS)
        or any(
            set(item) != {"model", "read", "create", "write", "unlink"}
            or any(not isinstance(item[key], bool) for key in ("read", "create", "write", "unlink"))
            for item in model_acl
        )
    ):
        raise _failed("The Odoo access result is invalid.")
    return {
        "user": user,
        "company_id": page["company_id"],
        "groups": groups,
        "model_acl": model_acl,
    }
