"""Closed contracts for five inventory-operation reads."""

from __future__ import annotations

import base64
import binascii
import json
import re
import uuid
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol

INVENTORY_OPERATIONS_CAPABILITY_IDS = frozenset(
    {
        "stock.transfer.search",
        "stock.transfer.get",
        "stock.move.search",
        "inventory.on_hand.summary",
        "inventory.availability.inspect",
    }
)
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000
_CURSOR_VERSION = 1
_SEARCH_CAPABILITIES = frozenset({"stock.transfer.search", "stock.move.search"})
_TRANSFER_STATES = frozenset(
    {"draft", "waiting", "confirmed", "assigned", "done", "cancel"}
)
_MOVE_STATES = frozenset(
    {
        "draft",
        "waiting",
        "confirmed",
        "partially_available",
        "assigned",
        "done",
        "cancel",
    }
)
_DECIMAL_PATTERN = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_UTC_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")


class InventoryOperationsPort(Protocol):
    @property
    def user_id(self) -> int: ...

    def read(
        self,
        *,
        capability_id: str,
        company_id: int,
        parameters: dict[str, Any],
    ) -> dict[str, Any]: ...


class InventoryOperationsReadError(RuntimeError):
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


def _invalid(
    message: str, *, code: str = "invalid_request"
) -> InventoryOperationsReadError:
    return InventoryOperationsReadError(code, message, exit_code=2)


def _failed(message: str) -> InventoryOperationsReadError:
    return InventoryOperationsReadError("failed_validation", message, exit_code=8)


def _integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _positive_id(value: Any) -> bool:
    return _integer(value) and value > 0


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _optional_text(value: Any) -> bool:
    return value is None or _text(value)


def _canonical_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _utc_datetime(value: Any) -> bool:
    if not isinstance(value, str) or _UTC_PATTERN.fullmatch(value) is None:
        return False
    try:
        datetime.fromisoformat(value)
    except ValueError:
        return False
    return True


def _optional_utc_datetime(value: Any) -> bool:
    return value is None or _utc_datetime(value)


def _decimal(value: Any, *, nonnegative: bool = False) -> Decimal | None:
    if (
        not isinstance(value, str)
        or len(value) > 256
        or _DECIMAL_PATTERN.fullmatch(value) is None
    ):
        return None
    try:
        number = Decimal(value)
    except InvalidOperation:
        return None
    if not number.is_finite() or (nonnegative and number < 0):
        return None
    return number


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
    parameters = request["parameters"]
    if not isinstance(parameters, dict):
        raise _invalid("parameters must be an object.")
    return request_id, context, parameters


def _optional_id(parameters: dict[str, Any], key: str) -> int | None:
    value = parameters.get(key)
    if value is not None and not _positive_id(value):
        raise _invalid(f"parameters.{key} must be null or a positive integer.")
    return value


def _date_range(parameters: dict[str, Any]) -> tuple[str | None, str | None]:
    date_from = parameters.get("date_from")
    date_to = parameters.get("date_to")
    if date_from is not None and not _canonical_date(date_from):
        raise _invalid("parameters.date_from must be null or a YYYY-MM-DD date.")
    if date_to is not None and not _canonical_date(date_to):
        raise _invalid("parameters.date_to must be null or a YYYY-MM-DD date.")
    if date_from is not None and date_to is not None and date_from > date_to:
        raise _invalid("parameters.date_from cannot be after parameters.date_to.")
    return date_from, date_to


def _pagination(parameters: dict[str, Any]) -> tuple[int, str | None]:
    limit = parameters.get("limit", DEFAULT_LIMIT)
    if not _integer(limit) or not 1 <= limit <= MAX_LIMIT:
        raise _invalid(f"parameters.limit must be between 1 and {MAX_LIMIT}.")
    cursor = parameters.get("cursor")
    if cursor is not None and (
        not isinstance(cursor, str) or not cursor or len(cursor) > 4096
    ):
        raise _invalid("parameters.cursor must be null or a non-empty cursor string.")
    return limit, cursor


def validate_inventory_operations_request(
    capability_id: str, request: Any
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    """Validate and normalize one inventory-operation request."""

    if (
        not isinstance(capability_id, str)
        or capability_id not in INVENTORY_OPERATIONS_CAPABILITY_IDS
    ):
        raise InventoryOperationsReadError(
            "unsupported_capability",
            "The inventory-operation capability is unsupported.",
            exit_code=4,
        )
    request_id, context, parameters = _envelope(request)

    if capability_id == "stock.transfer.get":
        if set(parameters) != {"transfer_id"} or not _positive_id(
            parameters.get("transfer_id")
        ):
            raise _invalid("parameters must contain one positive transfer_id.")
        return request_id, context, {"transfer_id": parameters["transfer_id"]}

    if capability_id == "stock.transfer.search":
        allowed = {
            "picking_type_id",
            "partner_id",
            "state",
            "date_from",
            "date_to",
            "limit",
            "cursor",
        }
        if not set(parameters) <= allowed:
            raise _invalid("stock.transfer.search contains an unsupported parameter.")
        state = parameters.get("state")
        if state is not None and (
            not isinstance(state, str) or state not in _TRANSFER_STATES
        ):
            raise _invalid("parameters.state is not a supported transfer state.")
        date_from, date_to = _date_range(parameters)
        limit, cursor = _pagination(parameters)
        return (
            request_id,
            context,
            {
                "picking_type_id": _optional_id(parameters, "picking_type_id"),
                "partner_id": _optional_id(parameters, "partner_id"),
                "state": state,
                "date_from": date_from,
                "date_to": date_to,
                "limit": limit,
                "cursor": cursor,
            },
        )

    if capability_id == "stock.move.search":
        allowed = {
            "transfer_id",
            "product_id",
            "state",
            "date_from",
            "date_to",
            "limit",
            "cursor",
        }
        if not set(parameters) <= allowed:
            raise _invalid("stock.move.search contains an unsupported parameter.")
        state = parameters.get("state")
        if state is not None and (
            not isinstance(state, str) or state not in _MOVE_STATES
        ):
            raise _invalid("parameters.state is not a supported stock-move state.")
        date_from, date_to = _date_range(parameters)
        limit, cursor = _pagination(parameters)
        return (
            request_id,
            context,
            {
                "transfer_id": _optional_id(parameters, "transfer_id"),
                "product_id": _optional_id(parameters, "product_id"),
                "state": state,
                "date_from": date_from,
                "date_to": date_to,
                "limit": limit,
                "cursor": cursor,
            },
        )

    if capability_id == "inventory.on_hand.summary":
        if not set(parameters) <= {"warehouse_id", "location_id", "product_id"}:
            raise _invalid(
                "inventory.on_hand.summary contains an unsupported parameter."
            )
        return (
            request_id,
            context,
            {
                key: _optional_id(parameters, key)
                for key in ("warehouse_id", "location_id", "product_id")
            },
        )

    if not set(parameters) <= {"product_id", "warehouse_id", "location_id"}:
        raise _invalid(
            "inventory.availability.inspect contains an unsupported parameter."
        )
    product_id = parameters.get("product_id")
    warehouse_id = _optional_id(parameters, "warehouse_id")
    location_id = _optional_id(parameters, "location_id")
    if not _positive_id(product_id):
        raise _invalid("parameters.product_id must be a positive integer.")
    if warehouse_id is not None and location_id is not None:
        raise _invalid("warehouse_id and location_id are mutually exclusive.")
    return (
        request_id,
        context,
        {
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "location_id": location_id,
        },
    )


def _cursor_filters(parameters: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in parameters.items()
        if key not in {"limit", "cursor"}
    }


def _binding(
    capability_id: str, context: dict[str, Any], parameters: dict[str, Any]
) -> str:
    return json.dumps(
        {
            "capability": capability_id,
            "company_id": context["company_id"],
            "database": context["database"],
            "filters": _cursor_filters(parameters),
            "user_login": context["user_login"],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _encode_cursor(
    capability_id: str,
    after: int,
    *,
    context: dict[str, Any],
    parameters: dict[str, Any],
) -> str:
    raw = json.dumps(
        {
            "after": after,
            "binding": _binding(capability_id, context, parameters),
            "version": _CURSOR_VERSION,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate cursor key")
        result[key] = value
    return result


def _reject_number(value: str) -> Any:
    raise ValueError(f"unsupported cursor number: {value}")


def _decode_cursor(
    capability_id: str,
    cursor: str,
    *,
    context: dict[str, Any],
    parameters: dict[str, Any],
) -> int:
    try:
        raw = base64.b64decode(
            (cursor + "=" * (-len(cursor) % 4)).encode("ascii"),
            altchars=b"-_",
            validate=True,
        )
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_pairs,
            parse_float=_reject_number,
            parse_constant=_reject_number,
        )
    except (ValueError, UnicodeError, json.JSONDecodeError, binascii.Error) as exc:
        raise _invalid("The cursor is invalid.", code="invalid_cursor") from exc
    if (
        not isinstance(value, dict)
        or set(value) != {"after", "binding", "version"}
        or not _integer(value["version"])
        or value["version"] != _CURSOR_VERSION
        or not _positive_id(value["after"])
        or value["binding"] != _binding(capability_id, context, parameters)
    ):
        raise _invalid("The cursor does not match this request.", code="invalid_cursor")
    return value["after"]


def _named_ref(value: Any) -> bool:
    return bool(
        isinstance(value, dict)
        and set(value) == {"id", "name"}
        and _positive_id(value["id"])
        and _text(value["name"])
    )


def _optional_named_ref(value: Any) -> bool:
    return value is None or _named_ref(value)


def _coded_ref(value: Any) -> bool:
    return bool(
        isinstance(value, dict)
        and set(value) == {"id", "code", "name"}
        and _positive_id(value["id"])
        and _text(value["code"])
        and _text(value["name"])
    )


def _product_ref(value: Any) -> bool:
    return bool(
        isinstance(value, dict)
        and set(value) == {"id", "code", "name"}
        and _positive_id(value["id"])
        and _optional_text(value["code"])
        and _text(value["name"])
    )


def _transfer_item(value: Any, *, company_id: int, parameters: dict[str, Any]) -> bool:
    if not isinstance(value, dict) or set(value) != {
        "id",
        "company_id",
        "name",
        "origin",
        "state",
        "operation_type",
        "scheduled_date",
        "completed_date",
        "source_location",
        "destination_location",
        "partner",
    }:
        return False
    operation_type = value["operation_type"]
    if not (
        _positive_id(value["id"])
        and value["company_id"] == company_id
        and _text(value["name"])
        and _optional_text(value["origin"])
        and value["state"] in _TRANSFER_STATES
        and _coded_ref(operation_type)
        and len(operation_type["code"]) <= 64
        and _optional_utc_datetime(value["scheduled_date"])
        and _optional_utc_datetime(value["completed_date"])
        and _named_ref(value["source_location"])
        and _named_ref(value["destination_location"])
        and _optional_named_ref(value["partner"])
    ):
        return False
    scheduled = value["scheduled_date"]
    return not (
        parameters.get("picking_type_id") is not None
        and operation_type["id"] != parameters["picking_type_id"]
        or parameters.get("partner_id") is not None
        and (
            value["partner"] is None
            or value["partner"]["id"] != parameters["partner_id"]
        )
        or parameters.get("state") is not None
        and value["state"] != parameters["state"]
        or parameters.get("date_from") is not None
        and (scheduled is None or scheduled[:10] < parameters["date_from"])
        or parameters.get("date_to") is not None
        and (scheduled is None or scheduled[:10] > parameters["date_to"])
    )


def _move_item(value: Any, *, company_id: int, parameters: dict[str, Any]) -> bool:
    if not isinstance(value, dict) or set(value) != {
        "id",
        "company_id",
        "reference",
        "description_picking",
        "state",
        "date",
        "transfer",
        "product",
        "uom",
        "demand_quantity",
        "moved_quantity",
        "source_location",
        "destination_location",
    }:
        return False
    demand = _decimal(value["demand_quantity"], nonnegative=True)
    moved = _decimal(value["moved_quantity"], nonnegative=True)
    if not (
        _positive_id(value["id"])
        and value["company_id"] == company_id
        and _optional_text(value["reference"])
        and _optional_text(value["description_picking"])
        and value["state"] in _MOVE_STATES
        and _utc_datetime(value["date"])
        and _optional_named_ref(value["transfer"])
        and _product_ref(value["product"])
        and _named_ref(value["uom"])
        and demand is not None
        and moved is not None
        and _named_ref(value["source_location"])
        and _named_ref(value["destination_location"])
    ):
        return False
    return not (
        parameters.get("transfer_id") is not None
        and (
            value["transfer"] is None
            or value["transfer"]["id"] != parameters["transfer_id"]
        )
        or parameters.get("product_id") is not None
        and value["product"]["id"] != parameters["product_id"]
        or parameters.get("state") is not None
        and value["state"] != parameters["state"]
        or parameters.get("date_from") is not None
        and value["date"][:10] < parameters["date_from"]
        or parameters.get("date_to") is not None
        and value["date"][:10] > parameters["date_to"]
    )


def _summary(value: Any, *, company_id: int, parameters: dict[str, Any]) -> bool:
    if not isinstance(value, dict) or set(value) != {
        "company_id",
        "warehouse",
        "location",
        "groups",
    }:
        return False
    if not (
        value["company_id"] == company_id
        and (value["warehouse"] is None or _coded_ref(value["warehouse"]))
        and _optional_named_ref(value["location"])
        and isinstance(value["groups"], list)
        and (
            parameters["warehouse_id"] is None
            and value["warehouse"] is None
            or parameters["warehouse_id"] is not None
            and value["warehouse"] is not None
            and value["warehouse"]["id"] == parameters["warehouse_id"]
        )
        and (
            parameters["location_id"] is None
            and value["location"] is None
            or parameters["location_id"] is not None
            and value["location"] is not None
            and value["location"]["id"] == parameters["location_id"]
        )
    ):
        return False
    ids: list[int] = []
    for group in value["groups"]:
        if not isinstance(group, dict) or set(group) != {
            "product",
            "uom",
            "quantity",
            "reserved_quantity",
            "available_quantity",
        }:
            return False
        quantity = _decimal(group["quantity"])
        reserved = _decimal(group["reserved_quantity"], nonnegative=True)
        available = _decimal(group["available_quantity"])
        if not (
            _product_ref(group["product"])
            and _named_ref(group["uom"])
            and quantity is not None
            and reserved is not None
            and available is not None
            and available == quantity - reserved
            and (
                parameters["product_id"] is None
                or group["product"]["id"] == parameters["product_id"]
            )
        ):
            return False
        ids.append(group["product"]["id"])
    return ids == sorted(set(ids))


def _availability_result(
    value: Any, *, company_id: int, parameters: dict[str, Any]
) -> bool:
    if not isinstance(value, dict) or set(value) != {
        "company_id",
        "product",
        "warehouse",
        "location",
        "uom",
        "on_hand_quantity",
        "free_quantity",
        "incoming_quantity",
        "outgoing_quantity",
        "forecast_quantity",
    }:
        return False
    warehouse = value["warehouse"]
    location = value["location"]
    quantities = {
        key: _decimal(value[key])
        for key in (
            "on_hand_quantity",
            "free_quantity",
            "incoming_quantity",
            "outgoing_quantity",
            "forecast_quantity",
        )
    }
    return bool(
        value["company_id"] == company_id
        and _product_ref(value["product"])
        and value["product"]["id"] == parameters["product_id"]
        and (warehouse is None or _coded_ref(warehouse))
        and _optional_named_ref(location)
        and _named_ref(value["uom"])
        and all(number is not None for number in quantities.values())
        and (
            parameters["warehouse_id"] is None
            and warehouse is None
            or parameters["warehouse_id"] is not None
            and warehouse is not None
            and warehouse["id"] == parameters["warehouse_id"]
        )
        and (
            parameters["location_id"] is None
            and location is None
            or parameters["location_id"] is not None
            and location is not None
            and location["id"] == parameters["location_id"]
        )
    )


def _validate_page(port: InventoryOperationsPort, page: Any) -> None:
    if not isinstance(page, dict) or set(page) != {
        "user_id",
        "company_visible",
        "module_installed",
        "access_allowed",
        "cursor_found",
        "items",
    }:
        raise _failed("Odoo returned an invalid inventory-operation page.")
    if (
        not _positive_id(page["user_id"])
        or not _positive_id(port.user_id)
        or page["user_id"] != port.user_id
        or not all(
            isinstance(page[key], bool)
            for key in (
                "company_visible",
                "module_installed",
                "access_allowed",
                "cursor_found",
            )
        )
        or not isinstance(page["items"], list)
        or any(not isinstance(item, dict) for item in page["items"])
        or page["access_allowed"]
        and not (page["company_visible"] and page["module_installed"])
        or not page["access_allowed"]
        and page["items"]
    ):
        raise _failed("Odoo returned an inconsistent inventory-operation page.")


def _ensure_available(page: dict[str, Any]) -> None:
    if not page["company_visible"]:
        raise InventoryOperationsReadError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    if not page["module_installed"]:
        raise InventoryOperationsReadError(
            "uninstalled",
            "The inventory-operation capability is not installed in this database.",
            exit_code=4,
        )
    if not page["access_allowed"]:
        raise InventoryOperationsReadError(
            "unauthorized",
            "The configured user cannot read the requested inventory data.",
            exit_code=3,
        )


def _search_result(
    capability_id: str,
    items: list[dict[str, Any]],
    *,
    context: dict[str, Any],
    parameters: dict[str, Any],
    after: int | None,
) -> dict[str, Any]:
    validator = (
        _transfer_item if capability_id == "stock.transfer.search" else _move_item
    )
    if len(items) > parameters["limit"] + 1 or any(
        not validator(item, company_id=context["company_id"], parameters=parameters)
        for item in items
    ):
        raise _failed("Odoo returned invalid inventory search results.")
    ids = [item["id"] for item in items]
    if ids != sorted(set(ids), reverse=True) or (
        after is not None and any(item_id >= after for item_id in ids)
    ):
        raise _failed("Odoo returned unordered inventory search results.")
    has_more = len(items) > parameters["limit"]
    visible = items[: parameters["limit"]]
    return {
        "items": visible,
        "has_more": has_more,
        "next_cursor": (
            _encode_cursor(
                capability_id,
                visible[-1]["id"],
                context=context,
                parameters=parameters,
            )
            if has_more
            else None
        ),
    }


def read_inventory_operations(
    port: InventoryOperationsPort, capability_id: str, request: Any
) -> dict[str, Any]:
    """Execute one strictly modelled inventory-operation read."""

    _, context, parameters = validate_inventory_operations_request(
        capability_id, request
    )
    runtime_parameters = dict(parameters)
    after: int | None = None
    if capability_id in _SEARCH_CAPABILITIES:
        if parameters["cursor"] is not None:
            after = _decode_cursor(
                capability_id,
                parameters["cursor"],
                context=context,
                parameters=parameters,
            )
        runtime_parameters = {
            **_cursor_filters(parameters),
            "after": after,
            "limit": parameters["limit"] + 1,
        }
    page = port.read(
        capability_id=capability_id,
        company_id=context["company_id"],
        parameters=runtime_parameters,
    )
    _validate_page(port, page)
    _ensure_available(page)

    if capability_id in _SEARCH_CAPABILITIES:
        if parameters["cursor"] is not None and not page["cursor_found"]:
            raise _invalid(
                "The cursor no longer resolves in this result set.",
                code="invalid_cursor",
            )
        if parameters["cursor"] is None and not page["cursor_found"]:
            raise _failed("Odoo returned an invalid cursor state.")
        return _search_result(
            capability_id,
            page["items"],
            context=context,
            parameters=parameters,
            after=after,
        )

    if not page["cursor_found"] or len(page["items"]) > 1:
        raise _failed("Odoo returned an invalid single inventory result.")
    if not page["items"]:
        raise InventoryOperationsReadError(
            "record_not_found",
            "The requested inventory record or scope was not found.",
            exit_code=4,
        )
    item = page["items"][0]
    valid = False
    if capability_id == "stock.transfer.get":
        valid = (
            _transfer_item(item, company_id=context["company_id"], parameters={})
            and item["id"] == parameters["transfer_id"]
        )
    elif capability_id == "inventory.on_hand.summary":
        valid = _summary(item, company_id=context["company_id"], parameters=parameters)
    else:
        valid = _availability_result(
            item, company_id=context["company_id"], parameters=parameters
        )
    if not valid:
        raise _failed("Odoo returned an invalid inventory-operation result.")
    return item
