"""Closed contracts for high-frequency accounting object reads."""

from __future__ import annotations

import base64
import binascii
import json
import re
import uuid
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol

DEFAULT_LIMIT = 100
MAX_LIMIT = 1000
_CURSOR_VERSION = 1
_DECIMAL_PATTERN = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_DAY_OF_MONTH_PATTERN = re.compile(r"^(?:[0-9]|[12][0-9]|3[01])$")

CORE_OBJECT_GET_CAPABILITY_IDS = frozenset(
    {
        "account.account.get",
        "journal.get",
        "tax.get",
        "payment_term.get",
        "currency.get",
        "partner.get",
        "partner.accounting.get",
        "bank.transaction.get",
        "journal_item.get",
        "product.get",
        "analytic.plan.get",
        "analytic.account.get",
        "fiscal_position.get",
        "account.tag.get",
        "tax.group.get",
        "payment.method.get",
        "reconciliation.model.get",
        "cash_rounding.get",
        "journal.group.get",
        "incoterm.get",
        "partner.bank_account.get",
        "bank.statement.get",
        "reconciliation.partial.get",
        "reconciliation.full.get",
        "analytic.line.get",
        "analytic.distribution_model.get",
        "analytic.applicability.get",
        "budget.get",
        "budget.line.get",
    }
)
CORE_OBJECT_LIST_CAPABILITY_IDS = frozenset(
    {
        "payment.method.list",
        "reconciliation.model.list",
        "analytic.plan.list",
        "account.tag.list",
        "tax.group.list",
        "cash_rounding.list",
        "journal.group.list",
        "incoterm.list",
        "reconciliation.partial.list",
        "reconciliation.full.list",
        "analytic.distribution_model.list",
        "analytic.applicability.list",
    }
)
_CORE_OBJECT_SEARCH_CAPABILITY_IDS = frozenset(
    {
        "journal_item.search",
        "partner.search",
        "product.search",
        "analytic.account.search",
        "fiscal_position.search",
        "partner.bank_account.search",
        "bank.statement.search",
        "analytic.line.search",
        "budget.search",
        "budget.line.list",
    }
)
CORE_OBJECT_READ_CAPABILITY_IDS = frozenset(
    {
        *CORE_OBJECT_GET_CAPABILITY_IDS,
        *CORE_OBJECT_LIST_CAPABILITY_IDS,
        *_CORE_OBJECT_SEARCH_CAPABILITY_IDS,
    }
)

_ID_FIELDS = {
    "account.account.get": "account_id",
    "journal.get": "journal_id",
    "tax.get": "tax_id",
    "payment_term.get": "payment_term_id",
    "currency.get": "currency_id",
    "partner.get": "partner_id",
    "partner.accounting.get": "partner_id",
    "bank.transaction.get": "transaction_id",
    "journal_item.get": "line_id",
    "product.get": "product_id",
    "analytic.plan.get": "plan_id",
    "analytic.account.get": "analytic_account_id",
    "fiscal_position.get": "fiscal_position_id",
    "account.tag.get": "tag_id",
    "tax.group.get": "tax_group_id",
    "payment.method.get": "payment_method_line_id",
    "reconciliation.model.get": "reconciliation_model_id",
    "cash_rounding.get": "cash_rounding_id",
    "journal.group.get": "journal_group_id",
    "incoterm.get": "incoterm_id",
    "partner.bank_account.get": "partner_bank_id",
    "bank.statement.get": "bank_statement_id",
    "reconciliation.partial.get": "partial_reconcile_id",
    "reconciliation.full.get": "full_reconcile_id",
    "analytic.line.get": "analytic_line_id",
    "analytic.distribution_model.get": "distribution_model_id",
    "analytic.applicability.get": "applicability_id",
    "budget.get": "budget_id",
    "budget.line.get": "budget_line_id",
}
_JOURNAL_ITEM_FILTERS = frozenset(
    {
        "date_from",
        "date_to",
        "move_id",
        "account_id",
        "partner_id",
        "journal_id",
        "posted_only",
    }
)
_SEARCH_FILTERS = {
    "partner.search": frozenset(
        {"query", "active", "company_type", "customer", "supplier"}
    ),
    "product.search": frozenset({"query", "active"}),
    "analytic.account.search": frozenset({"query", "active", "plan_id"}),
    "fiscal_position.search": frozenset({"query", "active", "auto_apply"}),
    "partner.bank_account.search": frozenset({"partner_id", "active"}),
    "bank.statement.search": frozenset({"journal_id", "date_from", "date_to"}),
    "analytic.line.search": frozenset(
        {"query", "date_from", "date_to", "analytic_account_id"}
    ),
    "budget.search": frozenset(
        {"query", "state", "budget_type", "date_from", "date_to"}
    ),
    "budget.line.list": frozenset({"budget_id", "plan_id", "analytic_account_id"}),
}


class CoreObjectReadPort(Protocol):
    @property
    def user_id(self) -> int: ...

    def read(
        self,
        *,
        capability_id: str,
        company_id: int,
        parameters: dict[str, Any],
    ) -> dict[str, Any]: ...


class CoreObjectReadError(RuntimeError):
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


def _invalid(message: str, *, code: str = "invalid_request") -> CoreObjectReadError:
    return CoreObjectReadError(code, message, exit_code=2)


def _failed(message: str) -> CoreObjectReadError:
    return CoreObjectReadError("failed_validation", message, exit_code=8)


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _valid_id(value: Any) -> bool:
    return _is_integer(value) and value > 0


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _optional_text(value: Any) -> bool:
    return value is None or isinstance(value, str)


def _canonical_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _optional_date(value: Any) -> bool:
    return value is None or _canonical_date(value)


def _decimal_text(value: Any) -> bool:
    if not isinstance(value, str) or _DECIMAL_PATTERN.fullmatch(value) is None:
        return False
    try:
        return Decimal(value).is_finite()
    except InvalidOperation:
        return False


def _named_reference(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "name"}
        and _valid_id(value["id"])
        and _nonempty(value["name"])
    )


def _coded_reference(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "code", "name"}
        and _valid_id(value["id"])
        and _nonempty(value["code"])
        and _nonempty(value["name"])
    )


def _currency_reference(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "code"}
        and _valid_id(value["id"])
        and _nonempty(value["code"])
        and len(value["code"]) <= 3
    )


def _optional_reference(value: Any, validator: Any) -> bool:
    return value is None or validator(value)


def _validate_envelope(
    capability_id: str, request: Any
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    if capability_id not in CORE_OBJECT_READ_CAPABILITY_IDS:
        raise CoreObjectReadError(
            "unsupported_capability",
            "The core-object read capability is unsupported.",
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
    if not isinstance(request_id, str):
        raise _invalid("request_id must be a UUID string.")
    try:
        parsed = uuid.UUID(request_id)
    except (ValueError, AttributeError) as exc:
        raise _invalid("request_id must be a UUID string.") from exc
    if (
        str(parsed) != request_id.lower()
        or parsed.variant != uuid.RFC_4122
        or parsed.version not in {1, 2, 3, 4, 5}
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
    if any(
        not _nonempty(context.get(field))
        for field in ("database", "user_login", "language", "timezone")
    ) or not _valid_id(context.get("company_id")):
        raise _invalid("context contains an invalid value.")
    parameters = request["parameters"]
    if not isinstance(parameters, dict):
        raise _invalid("parameters must be an object.")
    return request_id, context, parameters


def validate_core_object_read_request(
    capability_id: str, request: Any
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    """Validate and normalize one fixed core-object request."""

    request_id, context, parameters = _validate_envelope(capability_id, request)
    if capability_id in CORE_OBJECT_GET_CAPABILITY_IDS:
        id_field = _ID_FIELDS[capability_id]
        if set(parameters) != {id_field} or not _valid_id(parameters.get(id_field)):
            raise _invalid(f"parameters.{id_field} must be a positive integer.")
        return request_id, context, {id_field: parameters[id_field]}

    if capability_id in CORE_OBJECT_LIST_CAPABILITY_IDS:
        if not set(parameters) <= {"limit", "cursor"}:
            raise _invalid(f"{capability_id} contains an unsupported parameter.")
        filters: dict[str, Any] = {}
    elif capability_id == "analytic.line.search":
        if not set(parameters) <= _SEARCH_FILTERS[capability_id] | {
            "limit",
            "cursor",
        }:
            raise _invalid(f"{capability_id} contains an unsupported parameter.")
        query = parameters.get("query")
        if query is not None and (
            not isinstance(query, str)
            or not 1 <= len(query) <= 200
            or query != query.strip()
        ):
            raise _invalid(
                "parameters.query must be null or a trimmed 1-200 character string."
            )
        date_from = parameters.get("date_from")
        date_to = parameters.get("date_to")
        if not _optional_date(date_from) or not _optional_date(date_to):
            raise _invalid("date_from and date_to must be null or YYYY-MM-DD dates.")
        if date_from is not None and date_to is not None and date_from > date_to:
            raise _invalid("date_from cannot be after date_to.")
        analytic_account_id = parameters.get("analytic_account_id")
        if analytic_account_id is not None and not _valid_id(analytic_account_id):
            raise _invalid(
                "parameters.analytic_account_id must be null or a positive integer."
            )
        filters = {
            "query": query,
            "date_from": date_from,
            "date_to": date_to,
            "analytic_account_id": analytic_account_id,
        }
    elif capability_id == "budget.search":
        if not set(parameters) <= _SEARCH_FILTERS[capability_id] | {
            "limit",
            "cursor",
        }:
            raise _invalid(f"{capability_id} contains an unsupported parameter.")
        query = parameters.get("query")
        if query is not None and (
            not isinstance(query, str)
            or not 1 <= len(query) <= 200
            or query != query.strip()
        ):
            raise _invalid(
                "parameters.query must be null or a trimmed 1-200 character string."
            )
        state = parameters.get("state")
        if state is not None and (
            not isinstance(state, str)
            or state not in {"draft", "confirmed", "revised", "done", "canceled"}
        ):
            raise _invalid("parameters.state contains an unsupported budget state.")
        budget_type = parameters.get("budget_type")
        if budget_type is not None and (
            not isinstance(budget_type, str)
            or budget_type not in {"revenue", "expense", "both"}
        ):
            raise _invalid("parameters.budget_type contains an unsupported value.")
        date_from = parameters.get("date_from")
        date_to = parameters.get("date_to")
        if not _optional_date(date_from) or not _optional_date(date_to):
            raise _invalid("date_from and date_to must be null or YYYY-MM-DD dates.")
        if date_from is not None and date_to is not None and date_from > date_to:
            raise _invalid("date_from cannot be after date_to.")
        filters = {
            "query": query,
            "state": state,
            "budget_type": budget_type,
            "date_from": date_from,
            "date_to": date_to,
        }
    elif capability_id == "budget.line.list":
        if not set(parameters) <= _SEARCH_FILTERS[capability_id] | {
            "limit",
            "cursor",
        }:
            raise _invalid(f"{capability_id} contains an unsupported parameter.")
        budget_id = parameters.get("budget_id")
        if not _valid_id(budget_id):
            raise _invalid("parameters.budget_id must be a positive integer.")
        plan_id = parameters.get("plan_id")
        analytic_account_id = parameters.get("analytic_account_id")
        if (plan_id is None) != (analytic_account_id is None) or (
            plan_id is not None
            and (not _valid_id(plan_id) or not _valid_id(analytic_account_id))
        ):
            raise _invalid(
                "parameters.plan_id and parameters.analytic_account_id must be "
                "null together or positive integers together."
            )
        filters = {
            "budget_id": budget_id,
            "plan_id": plan_id,
            "analytic_account_id": analytic_account_id,
        }
    elif capability_id == "journal_item.search":
        if not set(parameters) <= _JOURNAL_ITEM_FILTERS | {"limit", "cursor"}:
            raise _invalid("journal_item.search contains an unsupported parameter.")
        date_from = parameters.get("date_from")
        date_to = parameters.get("date_to")
        if not _optional_date(date_from) or not _optional_date(date_to):
            raise _invalid("date_from and date_to must be null or YYYY-MM-DD dates.")
        if date_from is not None and date_to is not None and date_from > date_to:
            raise _invalid("date_from cannot be after date_to.")
        filters = {"date_from": date_from, "date_to": date_to}
        for field in ("move_id", "account_id", "partner_id", "journal_id"):
            value = parameters.get(field)
            if value is not None and not _valid_id(value):
                raise _invalid(
                    f"parameters.{field} must be null or a positive integer."
                )
            filters[field] = value
        posted_only = parameters.get("posted_only", False)
        if not isinstance(posted_only, bool):
            raise _invalid("parameters.posted_only must be a boolean.")
        filters["posted_only"] = posted_only
    elif capability_id == "partner.search":
        if not set(parameters) <= _SEARCH_FILTERS[capability_id] | {
            "limit",
            "cursor",
        }:
            raise _invalid(f"{capability_id} contains an unsupported parameter.")
        query = parameters.get("query")
        if query is not None and (
            not isinstance(query, str)
            or not 1 <= len(query) <= 200
            or query != query.strip()
        ):
            raise _invalid(
                "parameters.query must be null or a trimmed 1-200 character string."
            )
        active = parameters.get("active")
        customer = parameters.get("customer")
        supplier = parameters.get("supplier")
        if any(
            value is not None and not isinstance(value, bool)
            for value in (active, customer, supplier)
        ):
            raise _invalid("Partner boolean filters must be null or booleans.")
        company_type = parameters.get("company_type")
        if company_type is not None and (
            not isinstance(company_type, str)
            or company_type not in {"person", "company"}
        ):
            raise _invalid(
                "parameters.company_type must be null, 'person', or 'company'."
            )
        filters = {
            "query": query,
            "active": active,
            "company_type": company_type,
            "customer": customer,
            "supplier": supplier,
        }
    elif capability_id == "partner.bank_account.search":
        if not set(parameters) <= _SEARCH_FILTERS[capability_id] | {
            "limit",
            "cursor",
        }:
            raise _invalid(f"{capability_id} contains an unsupported parameter.")
        partner_id = parameters.get("partner_id")
        if partner_id is not None and not _valid_id(partner_id):
            raise _invalid("parameters.partner_id must be null or a positive integer.")
        active = parameters.get("active")
        if active is not None and not isinstance(active, bool):
            raise _invalid("parameters.active must be null or a boolean.")
        filters = {"partner_id": partner_id, "active": active}
    elif capability_id == "bank.statement.search":
        if not set(parameters) <= _SEARCH_FILTERS[capability_id] | {
            "limit",
            "cursor",
        }:
            raise _invalid(f"{capability_id} contains an unsupported parameter.")
        journal_id = parameters.get("journal_id")
        if journal_id is not None and not _valid_id(journal_id):
            raise _invalid("parameters.journal_id must be null or a positive integer.")
        date_from = parameters.get("date_from")
        date_to = parameters.get("date_to")
        if not _optional_date(date_from) or not _optional_date(date_to):
            raise _invalid("date_from and date_to must be null or YYYY-MM-DD dates.")
        if date_from is not None and date_to is not None and date_from > date_to:
            raise _invalid("date_from cannot be after date_to.")
        filters = {
            "journal_id": journal_id,
            "date_from": date_from,
            "date_to": date_to,
        }
    else:
        allowed = _SEARCH_FILTERS[capability_id]
        if not set(parameters) <= allowed | {"limit", "cursor"}:
            raise _invalid(f"{capability_id} contains an unsupported parameter.")
        query = parameters.get("query")
        if query is not None and (
            not isinstance(query, str)
            or not 1 <= len(query) <= 200
            or query != query.strip()
        ):
            raise _invalid(
                "parameters.query must be null or a trimmed 1-200 character string."
            )
        active = parameters.get("active")
        if active is not None and not isinstance(active, bool):
            raise _invalid("parameters.active must be null or a boolean.")
        filters = {"query": query, "active": active}
        if capability_id == "analytic.account.search":
            plan_id = parameters.get("plan_id")
            if plan_id is not None and not _valid_id(plan_id):
                raise _invalid("parameters.plan_id must be null or a positive integer.")
            filters["plan_id"] = plan_id
        elif capability_id == "fiscal_position.search":
            auto_apply = parameters.get("auto_apply")
            if auto_apply is not None and not isinstance(auto_apply, bool):
                raise _invalid("parameters.auto_apply must be null or a boolean.")
            filters["auto_apply"] = auto_apply

    limit = parameters.get("limit", DEFAULT_LIMIT)
    if not _is_integer(limit) or not 1 <= limit <= MAX_LIMIT:
        raise _invalid(f"parameters.limit must be between 1 and {MAX_LIMIT}.")
    cursor = parameters.get("cursor")
    if cursor is not None and (
        not isinstance(cursor, str) or not cursor or len(cursor) > 4096
    ):
        raise _invalid("parameters.cursor must be null or a non-empty cursor string.")
    return request_id, context, {**filters, "limit": limit, "cursor": cursor}


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate cursor key")
        result[key] = value
    return result


def _reject_json_float(_value: str) -> None:
    raise ValueError("floating-point cursor number")


def _reject_json_constant(_value: str) -> None:
    raise ValueError("non-finite cursor number")


def _cursor_filters(parameters: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in parameters.items()
        if key not in {"limit", "cursor"}
    }


def _encode_cursor(
    record_id: int,
    *,
    capability_id: str,
    context: dict[str, Any],
    filters: dict[str, Any],
) -> str:
    payload = json.dumps(
        {
            "after_id": record_id,
            "capability": capability_id,
            "company_id": context["company_id"],
            "database": context["database"],
            "filters": filters,
            "user_login": context["user_login"],
            "version": _CURSOR_VERSION,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def _decode_cursor(
    cursor: str,
    *,
    capability_id: str,
    context: dict[str, Any],
    filters: dict[str, Any],
) -> int:
    try:
        padding = "=" * (-len(cursor) % 4)
        raw = base64.b64decode(
            (cursor + padding).encode("ascii"), altchars=b"-_", validate=True
        )
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
            parse_float=_reject_json_float,
            parse_constant=_reject_json_constant,
        )
    except (ValueError, UnicodeError, json.JSONDecodeError, binascii.Error) as exc:
        raise _invalid("The cursor is invalid.", code="invalid_cursor") from exc
    if (
        not isinstance(value, dict)
        or set(value)
        != {
            "after_id",
            "capability",
            "company_id",
            "database",
            "filters",
            "user_login",
            "version",
        }
        or not _valid_id(value["after_id"])
        or value["capability"] != capability_id
        or value["company_id"] != context["company_id"]
        or value["database"] != context["database"]
        or value["user_login"] != context["user_login"]
        or value["filters"] != filters
        or not _is_integer(value["version"])
        or value["version"] != _CURSOR_VERSION
    ):
        raise _invalid("The cursor does not match this request.", code="invalid_cursor")
    return value["after_id"]


def _valid_account_item(item: Any, company_id: int) -> bool:
    return (
        isinstance(item, dict)
        and set(item)
        == {"id", "code", "name", "account_type", "active", "reconcile", "company_ids"}
        and _valid_id(item["id"])
        and _nonempty(item["code"])
        and _nonempty(item["name"])
        and _nonempty(item["account_type"])
        and isinstance(item["active"], bool)
        and isinstance(item["reconcile"], bool)
        and isinstance(item["company_ids"], list)
        and item["company_ids"] == sorted(set(item["company_ids"]))
        and all(_valid_id(value) for value in item["company_ids"])
        and company_id in item["company_ids"]
    )


def _valid_master_item(capability_id: str, item: Any, company_id: int) -> bool:
    if not isinstance(item, dict) or not _valid_id(item.get("id")):
        return False
    if capability_id == "journal.get":
        return bool(
            set(item)
            == {
                "id",
                "sequence",
                "code",
                "name",
                "type",
                "active",
                "currency",
                "company_id",
            }
            and _is_integer(item["sequence"])
            and _nonempty(item["code"])
            and _nonempty(item["name"])
            and _nonempty(item["type"])
            and isinstance(item["active"], bool)
            and _optional_reference(item["currency"], _currency_reference)
            and item["company_id"] == company_id
        )
    if capability_id == "tax.get":
        return bool(
            set(item)
            == {
                "id",
                "sequence",
                "name",
                "type_tax_use",
                "amount_type",
                "amount",
                "price_include",
                "include_base_amount",
                "is_base_affected",
                "active",
                "tax_group",
                "company_id",
            }
            and _is_integer(item["sequence"])
            and _nonempty(item["name"])
            and _nonempty(item["type_tax_use"])
            and _nonempty(item["amount_type"])
            and _decimal_text(item["amount"])
            and all(
                isinstance(item[key], bool)
                for key in (
                    "price_include",
                    "include_base_amount",
                    "is_base_affected",
                    "active",
                )
            )
            and _named_reference(item["tax_group"])
            and item["company_id"] == company_id
        )
    if capability_id == "payment_term.get":
        expected = {
            "id",
            "sequence",
            "name",
            "active",
            "company_id",
            "display_on_invoice",
            "early_discount",
            "discount_percentage",
            "discount_days",
            "early_pay_discount_computation",
            "lines",
        }
        lines = item.get("lines")
        return bool(
            set(item) == expected
            and _is_integer(item["sequence"])
            and _nonempty(item["name"])
            and isinstance(item["active"], bool)
            and item["company_id"] in {None, company_id}
            and isinstance(item["display_on_invoice"], bool)
            and isinstance(item["early_discount"], bool)
            and _decimal_text(item["discount_percentage"])
            and _is_integer(item["discount_days"])
            and _nonempty(item["early_pay_discount_computation"])
            and isinstance(lines, list)
            and all(_valid_payment_term_line(line) for line in lines)
        )
    if capability_id == "currency.get":
        return bool(
            set(item)
            == {
                "id",
                "code",
                "name",
                "symbol",
                "rounding",
                "decimal_places",
                "active",
                "position",
                "is_company_currency",
            }
            and _nonempty(item["code"])
            and len(item["code"]) <= 3
            and (item["name"] is None or _nonempty(item["name"]))
            and _nonempty(item["symbol"])
            and _decimal_text(item["rounding"])
            and _is_integer(item["decimal_places"])
            and item["decimal_places"] >= 0
            and isinstance(item["active"], bool)
            and (item["position"] is None or _nonempty(item["position"]))
            and isinstance(item["is_company_currency"], bool)
        )
    return False


def _valid_payment_term_line(line: Any) -> bool:
    return bool(
        isinstance(line, dict)
        and set(line)
        == {"id", "value", "value_amount", "delay_type", "nb_days", "days_next_month"}
        and _valid_id(line["id"])
        and _nonempty(line["value"])
        and _decimal_text(line["value_amount"])
        and _nonempty(line["delay_type"])
        and _is_integer(line["nb_days"])
        and (
            line["days_next_month"] is None
            or (
                isinstance(line["days_next_month"], str)
                and _DAY_OF_MONTH_PATTERN.fullmatch(line["days_next_month"]) is not None
            )
        )
    )


def _valid_partner_item(item: Any, company_id: int) -> bool:
    return bool(
        isinstance(item, dict)
        and set(item)
        == {
            "id",
            "complete_name",
            "ref",
            "active",
            "is_company",
            "company_id",
            "customer_rank",
            "supplier_rank",
            "receivable_account",
            "payable_account",
        }
        and _valid_id(item["id"])
        and _nonempty(item["complete_name"])
        and _optional_text(item["ref"])
        and isinstance(item["active"], bool)
        and isinstance(item["is_company"], bool)
        and item["company_id"] in {None, company_id}
        and _is_integer(item["customer_rank"])
        and item["customer_rank"] >= 0
        and _is_integer(item["supplier_rank"])
        and item["supplier_rank"] >= 0
        and _optional_reference(item["receivable_account"], _coded_reference)
        and _optional_reference(item["payable_account"], _coded_reference)
    )


def _valid_partner_master_item(item: Any, company_id: int) -> bool:
    nullable_text_fields = (
        "vat",
        "reference",
        "email",
        "phone",
        "mobile",
        "street",
        "street2",
        "city",
        "zip",
        "language",
    )
    return bool(
        isinstance(item, dict)
        and set(item)
        == {
            "id",
            "name",
            "display_name",
            "company_type",
            "active",
            "vat",
            "reference",
            "email",
            "phone",
            "mobile",
            "street",
            "street2",
            "city",
            "zip",
            "state",
            "country",
            "language",
            "company_id",
            "parent",
            "customer_rank",
            "supplier_rank",
        }
        and _valid_id(item["id"])
        and _nonempty(item["name"])
        and _nonempty(item["display_name"])
        and isinstance(item["company_type"], str)
        and item["company_type"] in {"person", "company"}
        and isinstance(item["active"], bool)
        and all(_optional_text(item[field]) for field in nullable_text_fields)
        and _optional_reference(item["state"], _named_reference)
        and _optional_reference(item["country"], _named_reference)
        and (item["company_id"] is None or item["company_id"] == company_id)
        and _optional_reference(item["parent"], _named_reference)
        and _is_integer(item["customer_rank"])
        and item["customer_rank"] >= 0
        and _is_integer(item["supplier_rank"])
        and item["supplier_rank"] >= 0
    )


def _valid_bank_item(item: Any, company_id: int) -> bool:
    return bool(
        isinstance(item, dict)
        and set(item)
        == {
            "id",
            "company_id",
            "date",
            "payment_date",
            "name",
            "reference",
            "partner",
            "journal",
            "amount",
            "currency",
            "move",
            "reconciled",
        }
        and _valid_id(item["id"])
        and item["company_id"] == company_id
        and _canonical_date(item["date"])
        and _optional_date(item["payment_date"])
        and _nonempty(item["name"])
        and _optional_text(item["reference"])
        and _optional_reference(item["partner"], _named_reference)
        and _coded_reference(item["journal"])
        and _decimal_text(item["amount"])
        and _currency_reference(item["currency"])
        and isinstance(item["move"], dict)
        and set(item["move"]) == {"id", "name", "state"}
        and _valid_id(item["move"]["id"])
        and _nonempty(item["move"]["name"])
        and item["move"]["state"] in {"draft", "posted", "cancel"}
        and isinstance(item["reconciled"], bool)
    )


def _valid_journal_item(item: Any, company_id: int) -> bool:
    return bool(
        isinstance(item, dict)
        and set(item)
        == {
            "id",
            "company_id",
            "date",
            "date_maturity",
            "move",
            "account",
            "partner",
            "journal",
            "name",
            "reference",
            "debit",
            "credit",
            "balance",
            "amount_currency",
            "currency",
            "reconciled",
            "matching_number",
        }
        and _valid_id(item["id"])
        and item["company_id"] == company_id
        and _canonical_date(item["date"])
        and _optional_date(item["date_maturity"])
        and isinstance(item["move"], dict)
        and set(item["move"]) == {"id", "name", "state", "move_type"}
        and _valid_id(item["move"]["id"])
        and _nonempty(item["move"]["name"])
        and item["move"]["state"] in {"draft", "posted", "cancel"}
        and _nonempty(item["move"]["move_type"])
        and _coded_reference(item["account"])
        and _optional_reference(item["partner"], _named_reference)
        and _coded_reference(item["journal"])
        and isinstance(item["name"], str)
        and _optional_text(item["reference"])
        and all(
            _decimal_text(item[key])
            for key in ("debit", "credit", "balance", "amount_currency")
        )
        and _currency_reference(item["currency"])
        and isinstance(item["reconciled"], bool)
        and _optional_text(item["matching_number"])
    )


def _valid_support_item(capability_id: str, item: Any, company_id: int) -> bool:
    if not isinstance(item, dict) or not _valid_id(item.get("id")):
        return False
    if capability_id in {"payment.method.list", "payment.method.get"}:
        return bool(
            set(item)
            == {
                "id",
                "name",
                "payment_type",
                "sequence",
                "company_id",
                "payment_method",
                "journal",
                "payment_account",
            }
            and _nonempty(item["name"])
            and item["payment_type"] in {"inbound", "outbound"}
            and _is_integer(item["sequence"])
            and item["company_id"] == company_id
            and isinstance(item["payment_method"], dict)
            and set(item["payment_method"]) == {"id", "code", "name"}
            and _valid_id(item["payment_method"]["id"])
            and _nonempty(item["payment_method"]["code"])
            and _nonempty(item["payment_method"]["name"])
            and _coded_reference(item["journal"])
            and _optional_reference(item["payment_account"], _coded_reference)
        )
    return bool(
        set(item)
        == {
            "id",
            "name",
            "sequence",
            "active",
            "company_id",
            "match_amount",
            "match_amount_min",
            "match_amount_max",
            "match_label",
            "match_label_param",
        }
        and _nonempty(item["name"])
        and _is_integer(item["sequence"])
        and isinstance(item["active"], bool)
        and item["company_id"] == company_id
        and _optional_text(item["match_amount"])
        and _decimal_text(item["match_amount_min"])
        and _decimal_text(item["match_amount_max"])
        and _optional_text(item["match_label"])
        and _optional_text(item["match_label_param"])
    )


def _valid_cash_rounding_item(item: Any) -> bool:
    return bool(
        isinstance(item, dict)
        and set(item)
        == {
            "id",
            "name",
            "rounding",
            "strategy",
            "rounding_method",
            "profit_account",
            "loss_account",
        }
        and _valid_id(item["id"])
        and _nonempty(item["name"])
        and _decimal_text(item["rounding"])
        and item["strategy"] in {"biggest_tax", "add_invoice_line"}
        and item["rounding_method"] in {"UP", "DOWN", "HALF-UP"}
        and _optional_reference(item["profit_account"], _coded_reference)
        and _optional_reference(item["loss_account"], _coded_reference)
    )


def _valid_journal_group_item(item: Any, company_id: int) -> bool:
    journals = item.get("excluded_journals") if isinstance(item, dict) else None
    return bool(
        isinstance(item, dict)
        and set(item) == {"id", "name", "sequence", "company_id", "excluded_journals"}
        and _valid_id(item["id"])
        and _nonempty(item["name"])
        and _is_integer(item["sequence"])
        and item["company_id"] in {None, company_id}
        and isinstance(journals, list)
        and all(_coded_reference(journal) for journal in journals)
        and [journal["id"] for journal in journals]
        == sorted({journal["id"] for journal in journals})
    )


def _valid_incoterm_item(item: Any) -> bool:
    return bool(
        isinstance(item, dict)
        and set(item) == {"id", "code", "name", "active"}
        and _valid_id(item["id"])
        and _nonempty(item["code"])
        and _nonempty(item["name"])
        and isinstance(item["active"], bool)
    )


def _sorted_unique_ids(value: Any) -> bool:
    return bool(
        isinstance(value, list)
        and bool(value)
        and all(_valid_id(record_id) for record_id in value)
        and value == sorted(set(value))
    )


def _valid_partner_bank_item(item: Any, company_id: int) -> bool:
    bank = item.get("bank") if isinstance(item, dict) else None
    return bool(
        isinstance(item, dict)
        and set(item)
        == {
            "id",
            "acc_number",
            "account_holder_name",
            "account_type",
            "active",
            "sequence",
            "account_holder",
            "allow_out_payment",
            "bank",
            "currency",
            "company_id",
            "linked_journal",
        }
        and _valid_id(item["id"])
        and _nonempty(item["acc_number"])
        and _optional_text(item["account_holder_name"])
        and _nonempty(item["account_type"])
        and isinstance(item["active"], bool)
        and _is_integer(item["sequence"])
        and _named_reference(item["account_holder"])
        and isinstance(item["allow_out_payment"], bool)
        and (
            bank is None
            or (
                isinstance(bank, dict)
                and set(bank) == {"id", "name", "bic"}
                and _valid_id(bank["id"])
                and _nonempty(bank["name"])
                and _optional_text(bank["bic"])
            )
        )
        and _optional_reference(item["currency"], _currency_reference)
        and item["company_id"] in {None, company_id}
        and _optional_reference(item["linked_journal"], _coded_reference)
    )


def _valid_bank_statement_item(item: Any, company_id: int) -> bool:
    return bool(
        isinstance(item, dict)
        and set(item)
        == {
            "id",
            "name",
            "reference",
            "date",
            "company_id",
            "journal",
            "currency",
            "balance_start",
            "balance_end",
            "balance_end_real",
            "is_complete",
            "is_valid",
            "problem_description",
            "transaction_count",
        }
        and _valid_id(item["id"])
        and _nonempty(item["name"])
        and _optional_text(item["reference"])
        and _optional_date(item["date"])
        and item["company_id"] == company_id
        and _coded_reference(item["journal"])
        and _currency_reference(item["currency"])
        and all(
            _decimal_text(item[field])
            for field in ("balance_start", "balance_end", "balance_end_real")
        )
        and isinstance(item["is_complete"], bool)
        and isinstance(item["is_valid"], bool)
        and _optional_text(item["problem_description"])
        and _is_integer(item["transaction_count"])
        and item["transaction_count"] >= 0
    )


def _valid_partial_reconcile_item(item: Any, company_id: int) -> bool:
    return bool(
        isinstance(item, dict)
        and set(item)
        == {
            "id",
            "company_id",
            "max_date",
            "amount",
            "company_currency",
            "debit_amount_currency",
            "debit_currency",
            "credit_amount_currency",
            "credit_currency",
            "debit_journal_item_id",
            "credit_journal_item_id",
            "full_reconcile_id",
            "exchange_move_id",
            "matching_number",
        }
        and _valid_id(item["id"])
        and item["company_id"] == company_id
        and _canonical_date(item["max_date"])
        and _decimal_text(item["amount"])
        and _currency_reference(item["company_currency"])
        and _decimal_text(item["debit_amount_currency"])
        and _currency_reference(item["debit_currency"])
        and _decimal_text(item["credit_amount_currency"])
        and _currency_reference(item["credit_currency"])
        and _valid_id(item["debit_journal_item_id"])
        and _valid_id(item["credit_journal_item_id"])
        and item["debit_journal_item_id"] != item["credit_journal_item_id"]
        and (item["full_reconcile_id"] is None or _valid_id(item["full_reconcile_id"]))
        and (item["exchange_move_id"] is None or _valid_id(item["exchange_move_id"]))
        and _nonempty(item["matching_number"])
    )


def _valid_full_reconcile_item(item: Any, company_id: int) -> bool:
    return bool(
        isinstance(item, dict)
        and set(item)
        == {
            "id",
            "company_id",
            "matching_number",
            "partial_reconcile_ids",
            "reconciled_journal_item_ids",
        }
        and _valid_id(item["id"])
        and item["company_id"] == company_id
        and item["matching_number"] == str(item["id"])
        and _sorted_unique_ids(item["partial_reconcile_ids"])
        and _sorted_unique_ids(item["reconciled_journal_item_ids"])
    )


def _valid_product_item(item: Any, company_id: int) -> bool:
    return bool(
        isinstance(item, dict)
        and set(item)
        == {
            "id",
            "name",
            "default_code",
            "active",
            "product_type",
            "is_storable",
            "template",
            "category",
            "uom",
            "company_id",
            "currency",
            "standard_price",
            "list_price",
        }
        and _valid_id(item["id"])
        and _nonempty(item["name"])
        and _optional_text(item["default_code"])
        and isinstance(item["active"], bool)
        and item["product_type"] in {"consu", "service", "combo"}
        and isinstance(item["is_storable"], bool)
        and _named_reference(item["template"])
        and _optional_reference(item["category"], _named_reference)
        and _named_reference(item["uom"])
        and item["company_id"] in {None, company_id}
        and _currency_reference(item["currency"])
        and _decimal_text(item["standard_price"])
        and _decimal_text(item["list_price"])
    )


def _valid_plan_item(item: Any) -> bool:
    return bool(
        isinstance(item, dict)
        and set(item) == {"id", "name", "complete_name", "parent", "color"}
        and _valid_id(item["id"])
        and _nonempty(item["name"])
        and _nonempty(item["complete_name"])
        and _optional_reference(item["parent"], _named_reference)
        and _is_integer(item["color"])
    )


def _valid_analytic_item(item: Any, company_id: int) -> bool:
    return bool(
        isinstance(item, dict)
        and set(item)
        == {
            "id",
            "name",
            "code",
            "active",
            "plan",
            "partner",
            "company_id",
            "currency",
            "balance",
        }
        and _valid_id(item["id"])
        and _nonempty(item["name"])
        and _optional_text(item["code"])
        and isinstance(item["active"], bool)
        and _named_reference(item["plan"])
        and _optional_reference(item["partner"], _named_reference)
        and item["company_id"] in {None, company_id}
        and _currency_reference(item["currency"])
        and _decimal_text(item["balance"])
    )


def _valid_fiscal_position_item(item: Any, company_id: int) -> bool:
    states = item.get("states") if isinstance(item, dict) else None
    return bool(
        isinstance(item, dict)
        and set(item)
        == {
            "id",
            "name",
            "active",
            "auto_apply",
            "vat_required",
            "country",
            "country_group",
            "states",
            "company_id",
            "foreign_vat",
        }
        and _valid_id(item["id"])
        and _nonempty(item["name"])
        and isinstance(item["active"], bool)
        and isinstance(item["auto_apply"], bool)
        and isinstance(item["vat_required"], bool)
        and _optional_reference(item["country"], _named_reference)
        and _optional_reference(item["country_group"], _named_reference)
        and isinstance(states, list)
        and all(_named_reference(state) for state in states)
        and [state["id"] for state in states]
        == sorted({state["id"] for state in states})
        and item["company_id"] == company_id
        and _optional_text(item["foreign_vat"])
    )


def _valid_tag_item(item: Any) -> bool:
    return bool(
        isinstance(item, dict)
        and set(item) == {"id", "name", "applicability", "active", "color", "country"}
        and _valid_id(item["id"])
        and _nonempty(item["name"])
        and item["applicability"] in {"accounts", "taxes", "products"}
        and isinstance(item["active"], bool)
        and _is_integer(item["color"])
        and _optional_reference(item["country"], _named_reference)
    )


def _valid_tax_group_item(item: Any, company_id: int) -> bool:
    return bool(
        isinstance(item, dict)
        and set(item)
        == {
            "id",
            "name",
            "sequence",
            "country",
            "preceding_subtotal",
            "company_id",
        }
        and _valid_id(item["id"])
        and _nonempty(item["name"])
        and _is_integer(item["sequence"])
        and _optional_reference(item["country"], _named_reference)
        and _optional_text(item["preceding_subtotal"])
        and item["company_id"] == company_id
    )


def _valid_named_references(value: Any, *, nonempty: bool = True) -> bool:
    return bool(
        isinstance(value, list)
        and (bool(value) or not nonempty)
        and all(_named_reference(reference) for reference in value)
        and [reference["id"] for reference in value]
        == sorted({reference["id"] for reference in value})
    )


def _valid_analytic_line_item(item: Any, company_id: int) -> bool:
    return bool(
        isinstance(item, dict)
        and set(item)
        == {
            "id",
            "date",
            "name",
            "reference",
            "amount",
            "unit_amount",
            "company_id",
            "currency",
            "analytic_accounts",
            "partner",
            "product",
            "uom",
            "general_account",
            "journal_item_id",
        }
        and _valid_id(item["id"])
        and _canonical_date(item["date"])
        and _nonempty(item["name"])
        and _optional_text(item["reference"])
        and _decimal_text(item["amount"])
        and _decimal_text(item["unit_amount"])
        and item["company_id"] == company_id
        and _currency_reference(item["currency"])
        and _valid_named_references(item["analytic_accounts"])
        and _optional_reference(item["partner"], _named_reference)
        and _optional_reference(item["product"], _named_reference)
        and _optional_reference(item["uom"], _named_reference)
        and _optional_reference(item["general_account"], _coded_reference)
        and (item["journal_item_id"] is None or _valid_id(item["journal_item_id"]))
    )


def _valid_distribution_model_item(item: Any, company_id: int) -> bool:
    allocations = item.get("allocations") if isinstance(item, dict) else None
    if not isinstance(allocations, list):
        return False
    allocation_keys: list[tuple[int, ...]] = []
    for allocation in allocations:
        if (
            not isinstance(allocation, dict)
            or set(allocation) != {"analytic_accounts", "percentage"}
            or not _valid_named_references(allocation["analytic_accounts"])
            or not _decimal_text(allocation["percentage"])
        ):
            return False
        allocation_keys.append(
            tuple(reference["id"] for reference in allocation["analytic_accounts"])
        )
    return bool(
        set(item)
        == {
            "id",
            "sequence",
            "company_id",
            "account_prefix",
            "partner",
            "partner_category",
            "product",
            "product_category",
            "allocations",
        }
        and _valid_id(item["id"])
        and _is_integer(item["sequence"])
        and (item["company_id"] is None or item["company_id"] == company_id)
        and _optional_text(item["account_prefix"])
        and _optional_reference(item["partner"], _named_reference)
        and _optional_reference(item["partner_category"], _named_reference)
        and _optional_reference(item["product"], _named_reference)
        and _optional_reference(item["product_category"], _named_reference)
        and allocation_keys == sorted(set(allocation_keys))
    )


def _valid_applicability_item(item: Any, company_id: int) -> bool:
    return bool(
        isinstance(item, dict)
        and set(item)
        == {
            "id",
            "plan",
            "business_domain",
            "applicability",
            "company_id",
            "account_prefix",
            "product_category",
        }
        and _valid_id(item["id"])
        and _optional_reference(item["plan"], _named_reference)
        and isinstance(item["business_domain"], str)
        and item["business_domain"] in {"general", "invoice", "bill"}
        and isinstance(item["applicability"], str)
        and item["applicability"] in {"optional", "mandatory", "unavailable"}
        and (item["company_id"] is None or item["company_id"] == company_id)
        and _optional_text(item["account_prefix"])
        and _optional_reference(item["product_category"], _named_reference)
    )


def _valid_budget_item(item: Any, company_id: int) -> bool:
    return bool(
        isinstance(item, dict)
        and set(item)
        == {
            "id",
            "name",
            "date_from",
            "date_to",
            "state",
            "budget_type",
            "company_id",
            "responsible",
            "revision_of",
        }
        and _valid_id(item["id"])
        and _nonempty(item["name"])
        and _canonical_date(item["date_from"])
        and _canonical_date(item["date_to"])
        and item["date_from"] <= item["date_to"]
        and isinstance(item["state"], str)
        and item["state"] in {"draft", "confirmed", "revised", "done", "canceled"}
        and isinstance(item["budget_type"], str)
        and item["budget_type"] in {"revenue", "expense", "both"}
        and (item["company_id"] is None or item["company_id"] == company_id)
        and _optional_reference(item["responsible"], _named_reference)
        and _optional_reference(item["revision_of"], _named_reference)
    )


def _valid_budget_line_item(item: Any, company_id: int) -> bool:
    return bool(
        isinstance(item, dict)
        and set(item)
        == {
            "id",
            "sequence",
            "budget",
            "date_from",
            "date_to",
            "budget_amount",
            "achieved_amount",
            "achieved_percentage",
            "theoretical_amount",
            "theoretical_percentage",
            "above_budget",
            "state",
            "currency",
            "company_id",
            "analytic_accounts",
        }
        and _valid_id(item["id"])
        and _is_integer(item["sequence"])
        and _named_reference(item["budget"])
        and _canonical_date(item["date_from"])
        and _canonical_date(item["date_to"])
        and item["date_from"] <= item["date_to"]
        and all(
            _decimal_text(item[field])
            for field in (
                "budget_amount",
                "achieved_amount",
                "achieved_percentage",
                "theoretical_amount",
                "theoretical_percentage",
            )
        )
        and isinstance(item["above_budget"], bool)
        and isinstance(item["state"], str)
        and item["state"] in {"draft", "confirmed", "revised", "done", "canceled"}
        and _currency_reference(item["currency"])
        and (item["company_id"] is None or item["company_id"] == company_id)
        and _valid_named_references(item["analytic_accounts"])
    )


def _valid_item(capability_id: str, item: Any, company_id: int) -> bool:
    if capability_id == "account.account.get":
        return _valid_account_item(item, company_id)
    if capability_id in {"journal.get", "tax.get", "payment_term.get", "currency.get"}:
        return _valid_master_item(capability_id, item, company_id)
    if capability_id == "partner.accounting.get":
        return _valid_partner_item(item, company_id)
    if capability_id in {"partner.search", "partner.get"}:
        return _valid_partner_master_item(item, company_id)
    if capability_id == "bank.transaction.get":
        return _valid_bank_item(item, company_id)
    if capability_id in {"journal_item.search", "journal_item.get"}:
        return _valid_journal_item(item, company_id)
    if capability_id in {"product.search", "product.get"}:
        return _valid_product_item(item, company_id)
    if capability_id in {"analytic.plan.list", "analytic.plan.get"}:
        return _valid_plan_item(item)
    if capability_id in {"analytic.account.search", "analytic.account.get"}:
        return _valid_analytic_item(item, company_id)
    if capability_id in {"fiscal_position.search", "fiscal_position.get"}:
        return _valid_fiscal_position_item(item, company_id)
    if capability_id in {"account.tag.list", "account.tag.get"}:
        return _valid_tag_item(item)
    if capability_id in {"tax.group.list", "tax.group.get"}:
        return _valid_tax_group_item(item, company_id)
    if capability_id in {"cash_rounding.list", "cash_rounding.get"}:
        return _valid_cash_rounding_item(item)
    if capability_id in {"journal.group.list", "journal.group.get"}:
        return _valid_journal_group_item(item, company_id)
    if capability_id in {"incoterm.list", "incoterm.get"}:
        return _valid_incoterm_item(item)
    if capability_id in {
        "partner.bank_account.search",
        "partner.bank_account.get",
    }:
        return _valid_partner_bank_item(item, company_id)
    if capability_id in {"bank.statement.search", "bank.statement.get"}:
        return _valid_bank_statement_item(item, company_id)
    if capability_id in {
        "reconciliation.partial.list",
        "reconciliation.partial.get",
    }:
        return _valid_partial_reconcile_item(item, company_id)
    if capability_id in {
        "reconciliation.full.list",
        "reconciliation.full.get",
    }:
        return _valid_full_reconcile_item(item, company_id)
    if capability_id in {"analytic.line.search", "analytic.line.get"}:
        return _valid_analytic_line_item(item, company_id)
    if capability_id in {
        "analytic.distribution_model.list",
        "analytic.distribution_model.get",
    }:
        return _valid_distribution_model_item(item, company_id)
    if capability_id in {
        "analytic.applicability.list",
        "analytic.applicability.get",
    }:
        return _valid_applicability_item(item, company_id)
    if capability_id in {"budget.search", "budget.get"}:
        return _valid_budget_item(item, company_id)
    if capability_id in {"budget.line.list", "budget.line.get"}:
        return _valid_budget_line_item(item, company_id)
    return _valid_support_item(capability_id, item, company_id)


def _validated_page(
    port: CoreObjectReadPort,
    page: Any,
    *,
    capability_id: str,
    company_id: int,
    maximum: int,
) -> list[dict[str, Any]]:
    if (
        not isinstance(page, dict)
        or set(page)
        != {
            "user_id",
            "company_visible",
            "module_installed",
            "access_allowed",
            "cursor_found",
            "items",
        }
        or not _valid_id(page["user_id"])
        or not _valid_id(port.user_id)
        or page["user_id"] != port.user_id
        or any(
            not isinstance(page[key], bool)
            for key in (
                "company_visible",
                "module_installed",
                "access_allowed",
                "cursor_found",
            )
        )
        or not isinstance(page["items"], list)
        or len(page["items"]) > maximum
        or (
            page["access_allowed"]
            and not (page["company_visible"] and page["module_installed"])
        )
        or (not page["access_allowed"] and page["items"])
    ):
        raise _failed("Odoo returned an invalid core-object page.")
    if not page["company_visible"]:
        raise CoreObjectReadError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    if not page["module_installed"]:
        raise CoreObjectReadError(
            "uninstalled", "The required Odoo model is not installed.", exit_code=4
        )
    if not page["access_allowed"]:
        raise CoreObjectReadError(
            "unauthorized",
            "The configured user cannot read this accounting object.",
            exit_code=3,
        )
    if not page["cursor_found"]:
        raise _invalid("The cursor is no longer present.", code="invalid_cursor")
    items = [dict(item) for item in page["items"]]
    if any(not _valid_item(capability_id, item, company_id) for item in items):
        raise _failed("Odoo returned an invalid accounting object.")
    ids = [item["id"] for item in items]
    if ids != sorted(ids) or len(ids) != len(set(ids)):
        raise _failed("Odoo returned accounting objects in an unstable order.")
    return items


def read_core_object(
    capability_id: str,
    port: CoreObjectReadPort,
    request: dict[str, Any],
) -> dict[str, Any]:
    """Read one fixed object or one keyset page without bypassing Odoo ACLs."""

    _, context, parameters = validate_core_object_read_request(capability_id, request)
    company_id = context["company_id"]
    if capability_id in CORE_OBJECT_GET_CAPABILITY_IDS:
        page = port.read(
            capability_id=capability_id,
            company_id=company_id,
            parameters=parameters,
        )
        items = _validated_page(
            port,
            page,
            capability_id=capability_id,
            company_id=company_id,
            maximum=1,
        )
        if not items:
            raise CoreObjectReadError(
                "record_not_found",
                "The requested accounting object was not found.",
                exit_code=4,
            )
        if items[0]["id"] != parameters[_ID_FIELDS[capability_id]]:
            raise _failed("Odoo returned the wrong accounting object.")
        return items[0]

    filters = _cursor_filters(parameters)
    cursor = parameters["cursor"]
    after_id = (
        _decode_cursor(
            cursor,
            capability_id=capability_id,
            context=context,
            filters=filters,
        )
        if cursor
        else None
    )
    limit = parameters["limit"]
    runtime_parameters = {**filters, "after_id": after_id, "limit": limit + 1}
    page = port.read(
        capability_id=capability_id,
        company_id=company_id,
        parameters=runtime_parameters,
    )
    items = _validated_page(
        port,
        page,
        capability_id=capability_id,
        company_id=company_id,
        maximum=limit + 1,
    )
    if capability_id == "budget.line.list" and any(
        item["budget"]["id"] != filters["budget_id"] for item in items
    ):
        raise _failed("Odoo returned a budget line from the wrong budget.")
    if after_id is not None and any(item["id"] <= after_id for item in items):
        raise _failed("Odoo returned an invalid accounting-object cursor page.")
    has_more = len(items) > limit
    visible = items[:limit]
    next_cursor = None
    if has_more and visible:
        next_cursor = _encode_cursor(
            visible[-1]["id"],
            capability_id=capability_id,
            context=context,
            filters=filters,
        )
    return {"items": visible, "has_more": has_more, "next_cursor": next_cursor}
