"""Strict runtime configuration for the local Odoo bridge."""

from __future__ import annotations

import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any


_MAX_CONFIG_BYTES = 1024 * 1024
_ALLOWED_DATABASES = frozenset({"odoo_cli_v4_dev", "odoo_cli_v4_e2e"})


class ConfigError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class RuntimeTarget:
    alias: str
    database: str
    company_id: int
    available_company_ids: tuple[int, ...]
    user_login: str
    bridge_argv: tuple[str, ...]
    timeout_seconds: int


@dataclass(frozen=True)
class RuntimeConfig:
    bridge_argv: tuple[str, ...]
    timeout_seconds: int
    aliases: dict[str, tuple[str, dict[int, tuple[str, ...]]]]

    def resolve(
        self, alias: str, company_id: int, user_login: str
    ) -> RuntimeTarget:
        entry = self.aliases.get(alias)
        if entry is None:
            raise ConfigError("database_unavailable", "The database alias is unavailable.")
        database, companies = entry
        users = companies.get(company_id)
        if users is None:
            raise ConfigError("company_unavailable", "The company is unavailable.")
        if user_login not in users:
            raise ConfigError("user_unavailable", "The user is unavailable.")
        available_company_ids = (
            company_id,
            *sorted(
                configured_company_id
                for configured_company_id, configured_users in companies.items()
                if configured_company_id != company_id
                and user_login in configured_users
            ),
        )
        return RuntimeTarget(
            alias=alias,
            database=database,
            company_id=company_id,
            available_company_ids=available_company_ids,
            user_login=user_login,
            bridge_argv=self.bridge_argv,
            timeout_seconds=self.timeout_seconds,
        )


def _invalid() -> ConfigError:
    return ConfigError("invalid_config", "The runtime configuration is invalid.")


def _read_regular_file(path: Path) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ConfigError(
            "unconfigured", "The runtime configuration is unavailable."
        ) from exc
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_size > _MAX_CONFIG_BYTES:
            raise _invalid()
        data = os.read(descriptor, _MAX_CONFIG_BYTES + 1)
        if len(data) > _MAX_CONFIG_BYTES:
            raise _invalid()
        return data
    finally:
        os.close(descriptor)


def _decode(raw: bytes) -> dict[str, Any]:
    def object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise _invalid()
            result[key] = value
        return result

    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=object_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, ConfigError) as exc:
        raise _invalid() from exc
    if not isinstance(value, dict):
        raise _invalid()
    return value


def load_runtime_config(path: str | Path) -> RuntimeConfig:
    value = _decode(_read_regular_file(Path(path)))
    if set(value) != {"config_schema_version", "bridge", "aliases"}:
        raise _invalid()
    if value["config_schema_version"] != "v1":
        raise _invalid()

    bridge = value["bridge"]
    if not isinstance(bridge, dict) or set(bridge) != {"argv", "timeout_seconds"}:
        raise _invalid()
    argv = bridge["argv"]
    timeout = bridge["timeout_seconds"]
    if (
        not isinstance(argv, list)
        or not argv
        or any(
            not isinstance(item, str)
            or not item
            for item in argv
        )
        or not (argv[0].startswith("/") or Path(argv[0]).is_absolute())
        or not isinstance(timeout, int)
        or isinstance(timeout, bool)
        or not 1 <= timeout <= 300
    ):
        raise _invalid()

    raw_aliases = value["aliases"]
    if not isinstance(raw_aliases, dict) or not raw_aliases:
        raise _invalid()
    aliases: dict[str, tuple[str, dict[int, tuple[str, ...]]]] = {}
    for alias, raw_entry in raw_aliases.items():
        if not isinstance(alias, str) or not alias or not isinstance(raw_entry, dict):
            raise _invalid()
        if set(raw_entry) != {"database", "companies"}:
            raise _invalid()
        database = raw_entry["database"]
        raw_companies = raw_entry["companies"]
        if not isinstance(database, str) or database not in _ALLOWED_DATABASES:
            raise _invalid()
        if not isinstance(raw_companies, dict) or not raw_companies:
            raise _invalid()
        companies: dict[int, tuple[str, ...]] = {}
        for raw_company_id, raw_users in raw_companies.items():
            try:
                company_id = int(raw_company_id)
            except (TypeError, ValueError) as exc:
                raise _invalid() from exc
            if str(company_id) != raw_company_id or company_id <= 0:
                raise _invalid()
            if (
                not isinstance(raw_users, list)
                or not raw_users
                or any(not isinstance(user, str) or not user for user in raw_users)
                or len(raw_users) != len(set(raw_users))
            ):
                raise _invalid()
            companies[company_id] = tuple(raw_users)
        aliases[alias] = (database, companies)
    return RuntimeConfig(tuple(argv), timeout, aliases)
