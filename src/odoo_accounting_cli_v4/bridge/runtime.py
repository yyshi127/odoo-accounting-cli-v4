"""Odoo-side runtime for the narrow V4 read bridge."""

from __future__ import annotations

import argparse
import json
import sys
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
from typing import Any, TextIO

from odoo_accounting_cli_v4.config import ConfigError, load_runtime_config


_MAX_REQUEST_CHARS = 1024 * 1024
_ACCOUNT_FIELDS = (
    "id",
    "code",
    "name",
    "account_type",
    "active",
    "reconcile",
    "company_ids",
)
_MASTER_DATA_ACTIONS: dict[str, dict[str, Any]] = {
    "account.journal.read_page": {
        "model": "account.journal",
        "fields": (
            "id",
            "code",
            "name",
            "type",
            "active",
            "sequence",
            "currency_id",
            "company_id",
        ),
        "cursor_fields": ("sequence", "type", "code", "id"),
        "cursor_operators": (">", ">", ">", ">"),
        "cursor_types": (int, str, str, int),
        "order": "sequence,type,code,id",
        "scope": "company",
    },
    "account.tax.read_page": {
        "model": "account.tax",
        "fields": (
            "id",
            "name",
            "type_tax_use",
            "amount_type",
            "amount",
            "active",
            "sequence",
            "price_include",
            "include_base_amount",
            "is_base_affected",
            "tax_group_id",
            "company_id",
        ),
        "cursor_fields": ("sequence", "id"),
        "cursor_operators": (">", ">"),
        "cursor_types": (int, int),
        "order": "sequence,id",
        "scope": "company",
    },
    "account.payment.term.read_page": {
        "model": "account.payment.term",
        "fields": (
            "id",
            "name",
            "active",
            "company_id",
            "sequence",
            "display_on_invoice",
            "early_discount",
            "discount_percentage",
            "discount_days",
            "early_pay_discount_computation",
            "line_ids",
        ),
        "cursor_fields": ("sequence", "id"),
        "cursor_operators": (">", ">"),
        "cursor_types": (int, int),
        "order": "sequence,id",
        "scope": "shared_company",
    },
    "res.currency.read_page": {
        "model": "res.currency",
        "fields": (
            "id",
            "name",
            "full_name",
            "symbol",
            "active",
            "position",
            "rounding",
            "decimal_places",
            "is_current_company_currency",
        ),
        "cursor_fields": ("active", "name", "id"),
        "cursor_operators": ("<", ">", ">"),
        "cursor_types": (bool, str, int),
        "order": "active desc,name,id",
        "scope": "global",
    },
}
_ACTIONS = {
    "account.account.read_page",
    *_MASTER_DATA_ACTIONS,
}


class RuntimeFailure(RuntimeError):
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


@contextmanager
def _read_only_cursor(registry: Any):
    cursor = registry.cursor()
    try:
        cursor.execute("SET TRANSACTION READ ONLY")
        yield cursor
    finally:
        try:
            cursor.rollback()
        finally:
            cursor.close()


def _decode_request(stdin: TextIO) -> dict[str, Any]:
    raw = stdin.read(_MAX_REQUEST_CHARS + 1)
    if not raw or len(raw) > _MAX_REQUEST_CHARS:
        raise RuntimeFailure(
            "bridge_protocol_error", "The bridge request is invalid.", exit_code=7
        )

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise RuntimeFailure(
                    "bridge_protocol_error",
                    "The bridge request is invalid.",
                    exit_code=7,
                )
            result[key] = value
        return result

    try:
        value = json.loads(raw, object_pairs_hook=reject_duplicates)
    except (json.JSONDecodeError, RuntimeFailure) as exc:
        raise RuntimeFailure(
            "bridge_protocol_error", "The bridge request is invalid.", exit_code=7
        ) from exc
    if not isinstance(value, dict) or set(value) != {
        "schema_version",
        "target",
        "action",
        "payload",
    }:
        raise RuntimeFailure(
            "bridge_protocol_error", "The bridge request is invalid.", exit_code=7
        )
    target = value["target"]
    if (
        value["schema_version"] != "v1"
        or not isinstance(value["action"], str)
        or value["action"] not in _ACTIONS
        or not isinstance(value["payload"], dict)
        or not isinstance(target, dict)
        or set(target)
        != {
            "alias",
            "database",
            "company_id",
            "user_login",
            "language",
            "timezone",
        }
        or not isinstance(target["alias"], str)
        or not target["alias"]
        or not isinstance(target["database"], str)
        or not target["database"]
        or not isinstance(target["company_id"], int)
        or isinstance(target["company_id"], bool)
        or target["company_id"] <= 0
        or not isinstance(target["user_login"], str)
        or not target["user_login"]
        or not isinstance(target["language"], str)
        or not target["language"]
        or not isinstance(target["timezone"], str)
        or not target["timezone"]
    ):
        raise RuntimeFailure(
            "bridge_protocol_error", "The bridge request is invalid.", exit_code=7
        )
    return value


def _validated_target(request: dict[str, Any], config_path: Path):
    target = request["target"]
    try:
        resolved = load_runtime_config(config_path).resolve(
            target["alias"], target["company_id"], target["user_login"]
        )
    except ConfigError as exc:
        if exc.code == "database_unavailable":
            exit_code = 4
        elif exc.code in {"company_unavailable", "user_unavailable"}:
            exit_code = 3
        else:
            exit_code = 7
        raise RuntimeFailure(
            exc.code,
            "The requested Odoo runtime target is unavailable.",
            exit_code=exit_code,
        ) from exc
    if resolved.database != target["database"]:
        raise RuntimeFailure(
            "database_unavailable",
            "The requested Odoo runtime target is unavailable.",
            exit_code=4,
        )
    return resolved


def _require_keys(payload: dict[str, Any], keys: set[str]) -> None:
    if set(payload) != keys:
        raise RuntimeFailure(
            "bridge_protocol_error", "The bridge action payload is invalid.", exit_code=7
        )


def _master_data_after_is_valid(spec: dict[str, Any], after: Any) -> bool:
    if after is None:
        return True
    expected_types = spec["cursor_types"]
    if not isinstance(after, list) or len(after) != len(expected_types):
        return False
    for index, (value, expected_type) in enumerate(zip(after, expected_types, strict=True)):
        if expected_type is bool:
            if not isinstance(value, bool):
                return False
        elif expected_type is int:
            if not isinstance(value, int) or isinstance(value, bool):
                return False
            if index == len(after) - 1 and value <= 0:
                return False
        elif not isinstance(value, str) or not value:
            return False
    return True


def _master_data_cursor_domain(spec: dict[str, Any], after: list[Any]) -> list[Any]:
    fields = spec["cursor_fields"]
    operators = spec["cursor_operators"]
    if fields[0] == "active":
        tail_spec = {
            "cursor_fields": fields[1:],
            "cursor_operators": operators[1:],
        }
        tail = _master_data_cursor_domain(tail_spec, after[1:])
        same_active = ["&", ("active", "=", after[0]), *tail]
        if after[0] is True:
            return ["|", ("active", "=", False), *same_active]
        return same_active
    terms: list[list[Any]] = []
    for index, (field, operator) in enumerate(zip(fields, operators, strict=True)):
        term = [
            *((previous, "=", after[position]) for position, previous in enumerate(fields[:index])),
            (field, operator, after[index]),
        ]
        terms.append(term)
    domain: list[Any] = ["|"] * (len(terms) - 1)
    for term in terms:
        domain.extend(["&"] * (len(term) - 1))
        domain.extend(term)
    return domain


def _master_data_scope_domain(scope: str, company_id: int) -> list[Any]:
    if scope == "company":
        return [("company_id", "=", company_id)]
    if scope == "shared_company":
        return ["|", ("company_id", "=", False), ("company_id", "=", company_id)]
    if scope == "global":
        return []
    raise AssertionError("unknown fixed master-data scope")


def _dispatch_master_data(
    env: Any,
    action: str,
    payload: dict[str, Any],
    company_id: int,
) -> dict[str, Any]:
    spec = _MASTER_DATA_ACTIONS[action]
    _require_keys(payload, {"company_id", "after", "limit"})
    limit = payload["limit"]
    after = payload["after"]
    if (
        not isinstance(payload["company_id"], int)
        or isinstance(payload["company_id"], bool)
        or not isinstance(limit, int)
        or isinstance(limit, bool)
        or not 1 <= limit <= 1001
        or not _master_data_after_is_valid(spec, after)
    ):
        raise RuntimeFailure(
            "bridge_protocol_error",
            "The bridge action payload is invalid.",
            exit_code=7,
        )
    if payload["company_id"] != company_id:
        raise RuntimeFailure(
            "company_unavailable", "The company is unavailable.", exit_code=3
        )

    company_visible = bool(
        env["res.company"].search_count([("id", "=", company_id)], limit=1)
    )
    model_name = spec["model"]
    module_installed = env.registry.get(model_name) is not None
    access_allowed = bool(
        company_visible
        and module_installed
        and env[model_name].has_access("read")
        and (
            action != "account.payment.term.read_page"
            or env["account.payment.term.line"].has_access("read")
        )
    )
    if not access_allowed:
        return {
            "user_id": env.uid,
            "company_visible": company_visible,
            "module_installed": module_installed,
            "access_allowed": access_allowed,
            "rows": [],
        }

    domain = _master_data_scope_domain(spec["scope"], company_id)
    if after is not None:
        cursor_domain = _master_data_cursor_domain(spec, after)
        domain = ["&", *domain, *cursor_domain] if domain else cursor_domain
    rows = (
        env[model_name]
        .with_context(active_test=False, allowed_company_ids=[company_id])
        .search_read(
            domain,
            fields=list(spec["fields"]),
            limit=limit,
            order=spec["order"],
        )
    )
    if action == "account.journal.read_page":
        for row in rows:
            row["currency"] = _reference(row.pop("currency_id"), label="code")
            row["company_id"] = _reference_id(row["company_id"])
    elif action == "account.tax.read_page":
        for row in rows:
            row["amount"] = _decimal_string(row["amount"])
            row["tax_group"] = _reference(row.pop("tax_group_id"), label="name")
            row["company_id"] = _reference_id(row["company_id"])
    elif action == "account.payment.term.read_page":
        line_ids = [line_id for row in rows for line_id in row.pop("line_ids")]
        if len(line_ids) != len(set(line_ids)):
            raise RuntimeFailure(
                "odoo_runtime_error",
                "The Odoo runtime request failed.",
                exit_code=7,
            )
        expected_line_ids = set(line_ids)
        observed_line_ids: set[int] = set()
        lines_by_term: dict[int, list[dict[str, Any]]] = {
            row["id"]: [] for row in rows
        }
        if line_ids:
            line_rows = (
                env["account.payment.term.line"]
                .with_context(active_test=False, allowed_company_ids=[company_id])
                .search_read(
                    [("id", "in", line_ids)],
                    fields=[
                        "id",
                        "payment_id",
                        "value",
                        "value_amount",
                        "delay_type",
                        "nb_days",
                        "days_next_month",
                    ],
                    limit=len(line_ids),
                    order="payment_id,id",
                )
            )
            for line in line_rows:
                line_id = line.get("id")
                if line_id not in expected_line_ids or line_id in observed_line_ids:
                    raise RuntimeFailure(
                        "odoo_runtime_error",
                        "The Odoo runtime request failed.",
                        exit_code=7,
                    )
                observed_line_ids.add(line_id)
                payment_id = _reference_id(line.pop("payment_id"))
                if payment_id not in lines_by_term:
                    raise RuntimeFailure(
                        "odoo_runtime_error",
                        "The Odoo runtime request failed.",
                        exit_code=7,
                    )
                line["value_amount"] = _decimal_string(line["value_amount"])
                if line["days_next_month"] is False:
                    line["days_next_month"] = None
                lines_by_term[payment_id].append(line)
            if observed_line_ids != expected_line_ids:
                raise RuntimeFailure(
                    "odoo_runtime_error",
                    "The Odoo runtime request failed.",
                    exit_code=7,
                )
        for row in rows:
            row["company_id"] = _reference_id(row["company_id"])
            row["discount_percentage"] = _decimal_string(
                row["discount_percentage"]
            )
            row["lines"] = lines_by_term[row["id"]]
    if action == "res.currency.read_page":
        for row in rows:
            row["is_company_currency"] = row.pop("is_current_company_currency")
            row["code"] = row["name"]
            full_name = row.pop("full_name")
            row["name"] = None if full_name is False else full_name
            if row["position"] is False:
                row["position"] = None
            row["rounding"] = _decimal_string(row["rounding"])
    return {
        "user_id": env.uid,
        "company_visible": company_visible,
        "module_installed": module_installed,
        "access_allowed": access_allowed,
        "rows": rows,
    }


def _reference_id(value: Any) -> int | None:
    if value is False or value is None:
        return None
    if (
        isinstance(value, (list, tuple))
        and len(value) == 2
        and isinstance(value[0], int)
        and not isinstance(value[0], bool)
        and value[0] > 0
    ):
        return value[0]
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    raise RuntimeFailure(
        "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
    )


def _reference(value: Any, *, label: str) -> dict[str, Any] | None:
    if value is False or value is None:
        return None
    if (
        isinstance(value, (list, tuple))
        and len(value) == 2
        and isinstance(value[1], str)
        and value[1]
    ):
        return {"id": _reference_id(value), label: value[1]}
    raise RuntimeFailure(
        "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
    )


def _decimal_string(value: Any) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        )
    decimal_value = Decimal(value) if isinstance(value, int) else Decimal(str(value))
    if not decimal_value.is_finite():
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        )
    if decimal_value == 0:
        return "0"
    text = format(decimal_value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _dispatch(env: Any, action: str, payload: dict[str, Any], company_id: int):
    if action == "account.account.read_page":
        _require_keys(
            payload, {"company_id", "after_code", "after_id", "limit"}
        )
        if payload["company_id"] != company_id:
            raise RuntimeFailure(
                "company_unavailable", "The company is unavailable.", exit_code=3
            )
        limit = payload["limit"]
        after_code = payload["after_code"]
        after_id = payload["after_id"]
        if (
            not isinstance(limit, int)
            or isinstance(limit, bool)
            or not 1 <= limit <= 1001
            or (after_code is None) != (after_id is None)
            or (
                after_code is not None
                and (
                    not isinstance(after_code, str)
                    or not after_code
                    or not isinstance(after_id, int)
                    or isinstance(after_id, bool)
                    or after_id <= 0
                )
            )
        ):
            raise RuntimeFailure(
                "bridge_protocol_error",
                "The bridge action payload is invalid.",
                exit_code=7,
            )
        company_visible = bool(
            env["res.company"].search_count([("id", "=", company_id)], limit=1)
        )
        module_installed = env.registry.get("account.account") is not None
        access_allowed = bool(
            company_visible
            and module_installed
            and env["account.account"].has_access("read")
        )
        if not access_allowed:
            return {
                "user_id": env.uid,
                "company_visible": company_visible,
                "module_installed": module_installed,
                "access_allowed": access_allowed,
                "rows": [],
            }
        domain: list[Any] = [("company_ids", "in", [company_id])]
        if after_code is not None:
            from odoo.osv import expression

            domain = expression.AND(
                [
                    domain,
                    [
                        "|",
                        ("code", ">", after_code),
                        "&",
                        ("code", "=", after_code),
                        ("id", ">", after_id),
                    ],
                ]
            )
        rows = (
            env["account.account"]
            .with_context(active_test=False, allowed_company_ids=[company_id])
            .search_read(domain, fields=list(_ACCOUNT_FIELDS), limit=limit, order="code,id")
        )
        return {
            "user_id": env.uid,
            "company_visible": company_visible,
            "module_installed": module_installed,
            "access_allowed": access_allowed,
            "rows": rows,
        }
    if action in _MASTER_DATA_ACTIONS:
        return _dispatch_master_data(env, action, payload, company_id)
    raise RuntimeFailure(
        "bridge_protocol_error", "The bridge action is unavailable.", exit_code=7
    )


def _ensure_language_is_active(root_env: Any, language: str) -> None:
    active = root_env["res.lang"].with_context(active_test=False).search_count(
        [("code", "=", language), ("active", "=", True)], limit=1
    )
    if not active:
        raise RuntimeFailure(
            "language_unavailable",
            "The requested Odoo language is unavailable.",
            exit_code=4,
        )


def execute(request: dict[str, Any], *, config_path: Path, odoo_config: Path):
    target = _validated_target(request, config_path)
    try:
        from odoo import SUPERUSER_ID, api
        from odoo.orm.registry import Registry
        from odoo.tools import config as odoo_runtime_config

        odoo_runtime_config.parse_config(
            ["--config", str(odoo_config), "--database", target.database, "--no-http"]
        )
        registry = Registry(target.database)
        with _read_only_cursor(registry) as cursor:
            root_env = api.Environment(cursor, SUPERUSER_ID, {})
            request_target = request["target"]
            _ensure_language_is_active(root_env, request_target["language"])
            users = root_env["res.users"].with_context(active_test=False).search(
                [("login", "=", target.user_login)], limit=2
            )
            if len(users) != 1 or not users.active:
                raise RuntimeFailure(
                    "user_unavailable", "The configured user is unavailable.", exit_code=3
                )
            context = {
                "allowed_company_ids": [target.company_id],
                "active_test": True,
                "lang": request_target["language"],
                "tz": request_target["timezone"],
            }
            env = api.Environment(cursor, users.id, context)
            return _dispatch(
                env, request["action"], request["payload"], target.company_id
            )
    except RuntimeFailure:
        raise
    except Exception as exc:
        raise RuntimeFailure(
            "odoo_runtime_error",
            "The Odoo runtime request failed.",
            exit_code=7,
            retryable=False,
        ) from exc


def _document(success: bool, *, data=None, error=None) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "success": success,
        "data": data if success else None,
        "error": None if success else error,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--runtime-config",
        type=Path,
        default=Path("/etc/odoo-accounting-cli-v4/runtime.json"),
    )
    parser.add_argument(
        "--odoo-config",
        type=Path,
        default=Path("/etc/odoo-accounting-cli-v4/odoo.conf"),
    )
    parser.add_argument(
        "--odoo-source",
        type=Path,
        required=True,
    )
    args = parser.parse_args(argv)
    if not args.odoo_source.is_absolute() or not args.odoo_source.is_dir():
        result = _document(
            False,
            error={
                "code": "odoo_runtime_error",
                "message": "The Odoo runtime is unavailable.",
                "details": {},
                "retryable": False,
                "exit_code": 7,
            },
        )
        sys.stdout.write(
            json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
        )
        return 7
    sys.path.insert(0, str(args.odoo_source))
    try:
        request = _decode_request(sys.stdin)
        data = execute(
            request, config_path=args.runtime_config, odoo_config=args.odoo_config
        )
        result = _document(True, data=data)
        exit_code = 0
    except RuntimeFailure as exc:
        result = _document(
            False,
            error={
                "code": exc.code,
                "message": str(exc),
                "details": exc.details,
                "retryable": exc.retryable,
                "exit_code": exc.exit_code,
            },
        )
        exit_code = exc.exit_code
    sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    return exit_code
