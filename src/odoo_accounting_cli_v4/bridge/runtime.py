"""Odoo-side runtime for the narrow V4 read bridge."""

from __future__ import annotations

import argparse
import json
import sys
from contextlib import contextmanager
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
_ACTIONS = {
    "account.account.read_page",
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
    raise AssertionError("unreachable action")


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
