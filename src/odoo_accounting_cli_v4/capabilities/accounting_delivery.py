"""Closed contracts for accounting document delivery and follow-up updates."""

from __future__ import annotations

import re
import uuid
from copy import deepcopy
from datetime import date
from typing import Any, Protocol

ACCOUNTING_DELIVERY_READ_CAPABILITY_IDS = frozenset(
    {
        "invoice.send.inspect",
        "payment.receipt.send.inspect",
    }
)
ACCOUNTING_DELIVERY_WRITE_CAPABILITY_IDS = frozenset(
    {
        "invoice.send",
        "payment.receipt.send",
        "report.customer_statement.send",
        "report.followup.send",
        "invoice.followup.update",
    }
)
ACCOUNTING_DELIVERY_CAPABILITY_IDS = (
    ACCOUNTING_DELIVERY_READ_CAPABILITY_IDS | ACCOUNTING_DELIVERY_WRITE_CAPABILITY_IDS
)

_CONTEXT_KEYS = {
    "database",
    "company_id",
    "user_login",
    "language",
    "timezone",
}
_PAGE_KEYS = {
    "user_id",
    "company_visible",
    "module_installed",
    "access_allowed",
    "idempotent_replay",
    "result",
}
_IDEMPOTENCY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")


class AccountingDeliveryPort(Protocol):
    @property
    def user_id(self) -> int: ...

    def execute(
        self,
        *,
        capability_id: str,
        company_id: int,
        parameters: dict[str, Any],
        idempotency_key: str | None,
    ) -> dict[str, Any]: ...


class AccountingDeliveryError(RuntimeError):
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


def _invalid(message: str, *, code: str = "invalid_request") -> AccountingDeliveryError:
    return AccountingDeliveryError(code, message, exit_code=2)


def _failed(message: str) -> AccountingDeliveryError:
    return AccountingDeliveryError("failed_validation", message, exit_code=8)


def _positive_id(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _envelope(request: Any) -> tuple[str, dict[str, Any], dict[str, Any]]:
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
    if not isinstance(context, dict) or set(context) != _CONTEXT_KEYS:
        raise _invalid("context must contain only the required v1 fields.")
    if not all(
        _text(context.get(key))
        for key in ("database", "user_login", "language", "timezone")
    ) or not _positive_id(context.get("company_id")):
        raise _invalid("context contains an invalid value.")
    parameters = request["parameters"]
    if not isinstance(parameters, dict):
        raise _invalid("parameters must be an object.")
    return request_id, dict(context), parameters


def _record_ids(parameters: dict[str, Any], *, singular: str, plural: str) -> list[int]:
    if set(parameters) == {singular}:
        value = parameters[singular]
        if not _positive_id(value):
            raise _invalid(f"parameters.{singular} must be a positive integer.")
        return [value]
    if set(parameters) != {plural}:
        raise _invalid(
            f"parameters must contain exactly one {singular} or one {plural}."
        )
    values = parameters[plural]
    if (
        not isinstance(values, list)
        or not 2 <= len(values) <= 100
        or any(not _positive_id(value) for value in values)
        or len(set(values)) != len(values)
    ):
        raise _invalid(
            f"parameters.{plural} must contain 2 to 100 distinct positive integers."
        )
    return sorted(values)


def _dated_record_ids(
    parameters: dict[str, Any],
    *,
    singular: str,
    plural: str,
    date_fields: tuple[str, ...],
) -> dict[str, Any]:
    selection_keys = set(parameters) - set(date_fields)
    selection = {key: parameters[key] for key in selection_keys}
    record_ids = _record_ids(selection, singular=singular, plural=plural)
    if set(parameters) != selection_keys | set(date_fields):
        raise _invalid("The report delivery parameters do not match the contract.")
    for field in date_fields:
        if field not in parameters or not _date(parameters[field]):
            raise _invalid(f"parameters.{field} must be a YYYY-MM-DD date.")
    if date_fields == ("date_from", "date_to") and (
        parameters["date_from"] > parameters["date_to"]
    ):
        raise _invalid("parameters.date_from must be on or before date_to.")
    return {
        "record_ids": record_ids,
        **{field: parameters[field] for field in date_fields},
    }


def validate_accounting_delivery_request(
    capability_id: str, request: Any
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    """Validate and normalize one accounting delivery request."""

    if (
        not isinstance(capability_id, str)
        or capability_id not in ACCOUNTING_DELIVERY_CAPABILITY_IDS
    ):
        raise AccountingDeliveryError(
            "unsupported_capability",
            "The accounting delivery capability is unsupported.",
            exit_code=4,
        )
    request_id, context, parameters = _envelope(request)
    if capability_id in {"invoice.send.inspect", "invoice.send"}:
        normalized = {
            "record_ids": _record_ids(parameters, singular="move_id", plural="move_ids")
        }
    elif capability_id in {
        "payment.receipt.send.inspect",
        "payment.receipt.send",
    }:
        normalized = {
            "record_ids": _record_ids(
                parameters, singular="payment_id", plural="payment_ids"
            )
        }
    elif capability_id == "report.customer_statement.send":
        normalized = _dated_record_ids(
            parameters,
            singular="partner_id",
            plural="partner_ids",
            date_fields=("date_from", "date_to"),
        )
    elif capability_id == "report.followup.send":
        normalized = _dated_record_ids(
            parameters,
            singular="partner_id",
            plural="partner_ids",
            date_fields=("as_of",),
        )
    else:
        target_key = "move_id"
        if set(parameters) != {target_key, "no_followup"}:
            raise _invalid(
                f"parameters must contain only {target_key} and no_followup."
            )
        if not _positive_id(parameters[target_key]):
            raise _invalid(f"parameters.{target_key} must be a positive integer.")
        if not isinstance(parameters["no_followup"], bool):
            raise _invalid("parameters.no_followup must be a boolean.")
        normalized = {
            "record_id": parameters[target_key],
            "no_followup": parameters["no_followup"],
        }
    return request_id, context, normalized


def _validated_page(
    port: AccountingDeliveryPort,
    capability_id: str,
    page: Any,
) -> tuple[bool, dict[str, Any] | None]:
    try:
        port_user_id = port.user_id
    except (AttributeError, ValueError) as exc:
        raise _failed(
            "The Odoo bridge returned an invalid accounting delivery page."
        ) from exc
    if (
        not isinstance(page, dict)
        or set(page) != _PAGE_KEYS
        or not _positive_id(page["user_id"])
        or not _positive_id(port_user_id)
        or page["user_id"] != port_user_id
        or any(
            not isinstance(page[key], bool)
            for key in (
                "company_visible",
                "module_installed",
                "access_allowed",
                "idempotent_replay",
            )
        )
        or page["access_allowed"]
        and not (page["company_visible"] and page["module_installed"])
        or page["result"] is not None
        and not (
            page["company_visible"]
            and page["module_installed"]
            and page["access_allowed"]
            and isinstance(page["result"], dict)
        )
        or page["idempotent_replay"]
        and page["result"] is None
        or capability_id in ACCOUNTING_DELIVERY_READ_CAPABILITY_IDS
        and page["idempotent_replay"]
    ):
        raise _failed("The Odoo bridge returned an invalid accounting delivery page.")
    if not page["module_installed"]:
        raise AccountingDeliveryError(
            "uninstalled",
            "The Odoo module required by this accounting delivery is unavailable.",
            exit_code=4,
        )
    if not page["company_visible"]:
        raise AccountingDeliveryError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    if not page["access_allowed"]:
        raise AccountingDeliveryError(
            "unauthorized",
            "The configured user cannot execute this accounting delivery.",
            exit_code=3,
        )
    return page["idempotent_replay"], page["result"]


def _strict_ids(value: Any) -> bool:
    return (
        isinstance(value, list)
        and all(_positive_id(item) for item in value)
        and value == sorted(set(value))
    )


def _sorted_unique_texts(value: Any, *, allow_empty: bool = True) -> bool:
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(
            isinstance(item, str) and item == item.strip() and bool(item)
            for item in value
        )
        and value == sorted(set(value))
    )


def _inspection_record(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value)
        == {
            "record_id",
            "partner_id",
            "recipient_emails",
            "template_id",
            "report_id",
            "sending_methods",
            "warnings",
            "sendable",
        }
        and _positive_id(value["record_id"])
        and _positive_id(value["partner_id"])
        and _sorted_unique_texts(value["recipient_emails"])
        and (value["template_id"] is None or _positive_id(value["template_id"]))
        and (value["report_id"] is None or _positive_id(value["report_id"]))
        and _sorted_unique_texts(value["sending_methods"])
        and _sorted_unique_texts(value["warnings"])
        and isinstance(value["sendable"], bool)
    )


def _validate_inspection_result(
    parameters: dict[str, Any], result: Any
) -> dict[str, Any]:
    records = result.get("records") if isinstance(result, dict) else None
    if (
        not isinstance(result, dict)
        or set(result) != {"records"}
        or not isinstance(records, list)
        or not all(_inspection_record(record) for record in records)
        or [record["record_id"] for record in records] != parameters["record_ids"]
    ):
        raise _failed("Odoo returned an invalid accounting delivery inspection.")
    return deepcopy(result)


def _validate_send_result(parameters: dict[str, Any], result: Any) -> dict[str, Any]:
    if (
        not isinstance(result, dict)
        or set(result) != {"record_ids", "processed_count"}
        or not _strict_ids(result["record_ids"])
        or result["record_ids"] != parameters["record_ids"]
        or not isinstance(result["processed_count"], int)
        or isinstance(result["processed_count"], bool)
        or result["processed_count"] != len(result["record_ids"])
    ):
        raise _failed("Odoo returned an invalid accounting delivery result.")
    return deepcopy(result)


def _validate_update_result(parameters: dict[str, Any], result: Any) -> dict[str, Any]:
    if (
        not isinstance(result, dict)
        or set(result) != {"record_id", "no_followup"}
        or result["record_id"] != parameters["record_id"]
        or result["no_followup"] is not parameters["no_followup"]
    ):
        raise _failed("Odoo returned an invalid follow-up update result.")
    return deepcopy(result)


def _validate_result(
    capability_id: str, parameters: dict[str, Any], result: Any
) -> dict[str, Any]:
    if capability_id in ACCOUNTING_DELIVERY_READ_CAPABILITY_IDS:
        return _validate_inspection_result(parameters, result)
    if capability_id in {
        "invoice.send",
        "payment.receipt.send",
        "report.customer_statement.send",
        "report.followup.send",
    }:
        return _validate_send_result(parameters, result)
    return _validate_update_result(parameters, result)


def execute_accounting_delivery(
    port: AccountingDeliveryPort,
    capability_id: str,
    request: dict[str, Any],
    idempotency_key: str | None = None,
    confirmation: str | None = None,
) -> dict[str, Any]:
    """Execute one delivery capability and fail closed on bridge drift."""

    _, context, parameters = validate_accounting_delivery_request(
        capability_id, request
    )
    is_write = capability_id in ACCOUNTING_DELIVERY_WRITE_CAPABILITY_IDS
    if is_write:
        if (
            not isinstance(idempotency_key, str)
            or _IDEMPOTENCY_PATTERN.fullmatch(idempotency_key) is None
        ):
            raise _invalid(
                "idempotency_key must contain 8 to 128 safe characters.",
                code="invalid_idempotency_key",
            )
        if confirmation != capability_id:
            raise _invalid(
                "confirmation must exactly equal the capability ID.",
                code="confirmation_required",
            )
    elif idempotency_key is not None or confirmation is not None:
        raise _invalid("Read-only delivery inspection does not accept write controls.")

    try:
        page = port.execute(
            capability_id=capability_id,
            company_id=context["company_id"],
            parameters=deepcopy(parameters),
            idempotency_key=idempotency_key,
        )
    except ValueError as exc:
        raise _failed(
            "The Odoo bridge returned an invalid accounting delivery page."
        ) from exc
    idempotent_replay, result = _validated_page(port, capability_id, page)
    if result is None:
        raise AccountingDeliveryError(
            "record_not_found",
            "One or more requested accounting delivery records were not found.",
            exit_code=4,
        )
    return {
        "idempotent_replay": idempotent_replay,
        "result": _validate_result(capability_id, parameters, result),
    }
