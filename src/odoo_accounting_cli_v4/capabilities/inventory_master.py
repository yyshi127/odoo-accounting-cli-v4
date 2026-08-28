"""Closed contracts for five inventory master-data list capabilities."""

from __future__ import annotations

import base64
import binascii
import json
import uuid
from typing import Any, Protocol

INVENTORY_MASTER_CAPABILITY_IDS = frozenset(
    {
        "product.category.list",
        "warehouse.list",
        "stock.location.list",
        "stock.operation_type.list",
        "stock.route.list",
    }
)
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000
_CURSOR_VERSION = 1
_ACTIVE_CAPABILITIES = INVENTORY_MASTER_CAPABILITY_IDS - {"product.category.list"}


class InventoryMasterPort(Protocol):
    @property
    def user_id(self) -> int: ...

    def read(
        self,
        *,
        capability_id: str,
        company_id: int,
        parameters: dict[str, Any],
    ) -> dict[str, Any]: ...


class InventoryMasterReadError(RuntimeError):
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
) -> InventoryMasterReadError:
    return InventoryMasterReadError(code, message, exit_code=2)


def _failed(message: str) -> InventoryMasterReadError:
    return InventoryMasterReadError("failed_validation", message, exit_code=8)


def _integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _positive_id(value: Any) -> bool:
    return _integer(value) and value > 0


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _envelope(request: Any) -> tuple[dict[str, Any], dict[str, Any]]:
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
    if not _positive_id(context.get("company_id")) or not all(
        _text(context.get(key))
        for key in ("database", "user_login", "language", "timezone")
    ):
        raise _invalid("context contains an invalid value.")
    parameters = request["parameters"]
    if not isinstance(parameters, dict):
        raise _invalid("parameters must be an object.")
    return context, parameters


def validate_inventory_master_request(
    capability_id: str, request: Any
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate and normalize one inventory master-data request."""

    if capability_id not in INVENTORY_MASTER_CAPABILITY_IDS:
        raise InventoryMasterReadError(
            "unsupported_capability",
            "The inventory master-data capability is unsupported.",
            exit_code=4,
        )
    context, parameters = _envelope(request)
    allowed = {"limit", "cursor"}
    if capability_id in _ACTIVE_CAPABILITIES:
        allowed.add("active")
    if capability_id == "product.category.list":
        allowed.add("parent_id")
    elif capability_id == "stock.location.list":
        allowed.update({"warehouse_id", "usage"})
    elif capability_id == "stock.operation_type.list":
        allowed.update({"warehouse_id", "code"})
    elif capability_id == "stock.route.list":
        allowed.add("warehouse_id")
    if not set(parameters) <= allowed:
        raise _invalid(f"{capability_id} contains an unsupported parameter.")

    limit = parameters.get("limit", DEFAULT_LIMIT)
    cursor = parameters.get("cursor")
    if not _integer(limit) or not 1 <= limit <= MAX_LIMIT:
        raise _invalid(f"parameters.limit must be between 1 and {MAX_LIMIT}.")
    if cursor is not None and (
        not isinstance(cursor, str) or not cursor or len(cursor) > 4096
    ):
        raise _invalid("parameters.cursor must be null or non-empty text.")
    normalized: dict[str, Any] = {}
    if capability_id in _ACTIVE_CAPABILITIES:
        active = parameters.get("active", True)
        if active is not None and not isinstance(active, bool):
            raise _invalid("parameters.active must be null or boolean.")
        normalized["active"] = active
    if capability_id == "product.category.list":
        parent_id = parameters.get("parent_id")
        if parent_id is not None and not _positive_id(parent_id):
            raise _invalid("parameters.parent_id must be null or a positive integer.")
        normalized["parent_id"] = parent_id
    elif capability_id == "stock.location.list":
        warehouse_id = parameters.get("warehouse_id")
        usage = parameters.get("usage")
        if warehouse_id is not None and not _positive_id(warehouse_id):
            raise _invalid(
                "parameters.warehouse_id must be null or a positive integer."
            )
        if usage is not None and usage not in {
            "supplier",
            "view",
            "internal",
            "customer",
            "inventory",
            "production",
            "transit",
        }:
            raise _invalid("parameters.usage is unsupported.")
        normalized.update({"warehouse_id": warehouse_id, "usage": usage})
    elif capability_id == "stock.operation_type.list":
        warehouse_id = parameters.get("warehouse_id")
        code = parameters.get("code")
        if warehouse_id is not None and not _positive_id(warehouse_id):
            raise _invalid(
                "parameters.warehouse_id must be null or a positive integer."
            )
        if code is not None and (not _text(code) or len(code) > 64):
            raise _invalid("parameters.code must be null or non-empty text.")
        normalized.update({"warehouse_id": warehouse_id, "code": code})
    elif capability_id == "stock.route.list":
        warehouse_id = parameters.get("warehouse_id")
        if warehouse_id is not None and not _positive_id(warehouse_id):
            raise _invalid(
                "parameters.warehouse_id must be null or a positive integer."
            )
        normalized["warehouse_id"] = warehouse_id
    normalized.update({"limit": limit, "cursor": cursor})
    return context, normalized


def _binding(
    capability_id: str, context: dict[str, Any], parameters: dict[str, Any]
) -> str:
    return json.dumps(
        {
            "capability": capability_id,
            "company_id": context["company_id"],
            "database": context["database"],
            "filters": {
                key: value
                for key, value in parameters.items()
                if key not in {"limit", "cursor"}
            },
            "user_login": context["user_login"],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _encode_cursor(
    after: int,
    *,
    capability_id: str,
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
    ).encode()
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate cursor key")
        result[key] = value
    return result


def _reject_number(_value: str) -> None:
    raise ValueError("unsupported cursor number")


def _decode_cursor(
    cursor: str,
    *,
    capability_id: str,
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
            raw.decode(),
            object_pairs_hook=_pairs,
            parse_float=_reject_number,
            parse_constant=_reject_number,
        )
    except (ValueError, UnicodeError, json.JSONDecodeError, binascii.Error) as exc:
        raise _invalid("The cursor is invalid.", code="invalid_cursor") from exc
    if (
        not isinstance(value, dict)
        or set(value) != {"after", "binding", "version"}
        or value["version"] != _CURSOR_VERSION
        or not _integer(value["version"])
        or value["binding"] != _binding(capability_id, context, parameters)
        or not _positive_id(value["after"])
    ):
        raise _invalid("The cursor does not match this request.", code="invalid_cursor")
    return value["after"]


def _optional_id(value: Any) -> bool:
    return value is None or _positive_id(value)


def _category(value: Any, parent_id: int | None) -> bool:
    return bool(
        isinstance(value, dict)
        and set(value) == {"id", "name", "complete_name", "parent_id"}
        and _positive_id(value["id"])
        and _text(value["name"])
        and _text(value["complete_name"])
        and _optional_id(value["parent_id"])
        and (parent_id is None or value["parent_id"] == parent_id)
    )


def _warehouse(value: Any, company_id: int, active: bool | None) -> bool:
    return bool(
        isinstance(value, dict)
        and set(value)
        == {
            "id",
            "name",
            "code",
            "active",
            "company_id",
            "reception_steps",
            "delivery_steps",
        }
        and _positive_id(value["id"])
        and _text(value["name"])
        and _text(value["code"])
        and isinstance(value["active"], bool)
        and (active is None or value["active"] == active)
        and value["company_id"] == company_id
        and value["reception_steps"] in {"one_step", "two_steps", "three_steps"}
        and value["delivery_steps"] in {"ship_only", "pick_ship", "pick_pack_ship"}
    )


def _location(
    value: Any,
    company_id: int,
    active: bool | None,
    warehouse_id: int | None,
    usage: str | None,
) -> bool:
    return bool(
        isinstance(value, dict)
        and set(value)
        == {
            "id",
            "name",
            "complete_name",
            "active",
            "usage",
            "company_id",
            "parent_id",
            "warehouse_id",
        }
        and _positive_id(value["id"])
        and _text(value["name"])
        and _text(value["complete_name"])
        and isinstance(value["active"], bool)
        and (active is None or value["active"] == active)
        and _text(value["usage"])
        and value["company_id"] in {None, company_id}
        and _optional_id(value["parent_id"])
        and _optional_id(value["warehouse_id"])
        and (warehouse_id is None or value["warehouse_id"] == warehouse_id)
        and (usage is None or value["usage"] == usage)
    )


def _operation_type(
    value: Any,
    company_id: int,
    active: bool | None,
    warehouse_id: int | None,
    code: str | None,
) -> bool:
    return bool(
        isinstance(value, dict)
        and set(value)
        == {
            "id",
            "name",
            "active",
            "code",
            "sequence_code",
            "company_id",
            "warehouse_id",
            "source_location_id",
            "destination_location_id",
        }
        and _positive_id(value["id"])
        and _text(value["name"])
        and isinstance(value["active"], bool)
        and (active is None or value["active"] == active)
        and _text(value["code"])
        and _text(value["sequence_code"])
        and value["company_id"] == company_id
        and _optional_id(value["warehouse_id"])
        and _optional_id(value["source_location_id"])
        and _optional_id(value["destination_location_id"])
        and (warehouse_id is None or value["warehouse_id"] == warehouse_id)
        and (code is None or value["code"] == code)
    )


def _route(
    value: Any,
    company_id: int,
    active: bool | None,
    warehouse_id: int | None,
) -> bool:
    if not (
        isinstance(value, dict)
        and set(value)
        == {
            "id",
            "name",
            "active",
            "sequence",
            "company_id",
            "product_selectable",
            "product_category_selectable",
            "warehouse_selectable",
            "warehouse_ids",
        }
        and _positive_id(value["id"])
        and _text(value["name"])
        and isinstance(value["active"], bool)
        and (active is None or value["active"] == active)
        and _integer(value["sequence"])
        and value["company_id"] in {None, company_id}
        and all(
            isinstance(value[key], bool)
            for key in (
                "product_selectable",
                "product_category_selectable",
                "warehouse_selectable",
            )
        )
        and isinstance(value["warehouse_ids"], list)
    ):
        return False
    warehouse_ids = value["warehouse_ids"]
    return (
        all(_positive_id(item) for item in warehouse_ids)
        and warehouse_ids == sorted(set(warehouse_ids))
        and (warehouse_id is None or warehouse_id in warehouse_ids)
    )


def _valid_item(
    capability_id: str,
    value: Any,
    *,
    company_id: int,
    parameters: dict[str, Any],
) -> bool:
    if capability_id == "product.category.list":
        return _category(value, parameters["parent_id"])
    if capability_id == "warehouse.list":
        return _warehouse(value, company_id, parameters["active"])
    if capability_id == "stock.location.list":
        return _location(
            value,
            company_id,
            parameters["active"],
            parameters["warehouse_id"],
            parameters["usage"],
        )
    if capability_id == "stock.operation_type.list":
        return _operation_type(
            value,
            company_id,
            parameters["active"],
            parameters["warehouse_id"],
            parameters["code"],
        )
    return _route(
        value,
        company_id,
        parameters["active"],
        parameters["warehouse_id"],
    )


def _page(port: InventoryMasterPort, value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, dict) or set(value) != {
        "user_id",
        "company_visible",
        "module_installed",
        "access_allowed",
        "cursor_found",
        "items",
    }:
        raise _failed("Odoo returned an invalid inventory-master page.")
    if not (
        _positive_id(value["user_id"])
        and value["user_id"] == port.user_id
        and all(
            isinstance(value[key], bool)
            for key in (
                "company_visible",
                "module_installed",
                "access_allowed",
                "cursor_found",
            )
        )
        and isinstance(value["items"], list)
        and all(isinstance(item, dict) for item in value["items"])
        and (
            not value["access_allowed"]
            or value["company_visible"]
            and value["module_installed"]
        )
        and (value["access_allowed"] or not value["items"])
    ):
        raise _failed("Odoo returned an inconsistent inventory-master page.")
    return value["items"]


def _availability(page: dict[str, Any]) -> None:
    if not page["company_visible"]:
        raise InventoryMasterReadError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    if not page["module_installed"]:
        raise InventoryMasterReadError(
            "uninstalled",
            "The required Odoo inventory model is not installed.",
            exit_code=4,
        )
    if not page["access_allowed"]:
        raise InventoryMasterReadError(
            "unauthorized",
            "The configured user cannot read this inventory master data.",
            exit_code=3,
        )


def read_inventory_master(
    port: InventoryMasterPort, capability_id: str, request: Any
) -> dict[str, Any]:
    """Execute one validated inventory master-data list."""

    context, parameters = validate_inventory_master_request(capability_id, request)
    after = None
    if parameters["cursor"] is not None:
        after = _decode_cursor(
            parameters["cursor"],
            capability_id=capability_id,
            context=context,
            parameters=parameters,
        )
    runtime_parameters = {
        key: value
        for key, value in parameters.items()
        if key not in {"limit", "cursor"}
    }
    runtime_parameters.update({"after": after, "limit": parameters["limit"] + 1})
    page = port.read(
        capability_id=capability_id,
        company_id=context["company_id"],
        parameters=runtime_parameters,
    )
    items = _page(port, page)
    _availability(page)
    if parameters["cursor"] is not None and not page["cursor_found"]:
        raise _invalid("The cursor no longer resolves.", code="invalid_cursor")
    if len(items) > parameters["limit"] + 1 or any(
        not _valid_item(
            capability_id,
            item,
            company_id=context["company_id"],
            parameters=parameters,
        )
        for item in items
    ):
        raise _failed("Odoo returned invalid inventory-master rows.")
    ids = [item["id"] for item in items]
    if ids != sorted(set(ids), reverse=True) or (
        after is not None and any(item_id >= after for item_id in ids)
    ):
        raise _failed("Odoo returned unordered inventory-master rows.")
    has_more = len(items) > parameters["limit"]
    visible = items[: parameters["limit"]]
    return {
        "items": visible,
        "has_more": has_more,
        "next_cursor": (
            _encode_cursor(
                visible[-1]["id"],
                capability_id=capability_id,
                context=context,
                parameters=parameters,
            )
            if has_more
            else None
        ),
    }
