from __future__ import annotations

import json

import pytest

from odoo_accounting_cli_v4.config import ConfigError, load_runtime_config


def _write_config(tmp_path):
    path = tmp_path / "runtime.json"
    path.write_text(
        json.dumps(
            {
                "config_schema_version": "v1",
                "bridge": {
                    "argv": ["/usr/bin/python3", "/srv/odacv4/bridge.py"],
                    "timeout_seconds": 15,
                },
                "aliases": {
                    "v4-dev": {
                        "database": "odoo_cli_v4_dev",
                        "companies": {"7": ["v4-agent"]},
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    return path


def test_resolve_returns_only_the_allowlisted_runtime_target(tmp_path) -> None:
    config = load_runtime_config(_write_config(tmp_path))

    target = config.resolve("v4-dev", 7, "v4-agent")

    assert target.alias == "v4-dev"
    assert target.database == "odoo_cli_v4_dev"
    assert target.company_id == 7
    assert target.available_company_ids == (7,)
    assert target.user_login == "v4-agent"
    assert target.bridge_argv == (
        "/usr/bin/python3",
        "/srv/odacv4/bridge.py",
    )
    assert target.timeout_seconds == 15


def test_resolve_exposes_only_companies_allowlisted_for_the_selected_user(
    tmp_path,
) -> None:
    path = _write_config(tmp_path)
    value = json.loads(path.read_text(encoding="utf-8"))
    value["aliases"]["v4-dev"]["companies"] = {
        "7": ["v4-agent"],
        "8": ["other-user", "v4-agent"],
        "9": ["other-user"],
    }
    path.write_text(json.dumps(value), encoding="utf-8")

    target = load_runtime_config(path).resolve("v4-dev", 8, "v4-agent")

    assert target.available_company_ids == (8, 7)


@pytest.mark.parametrize(
    ("alias", "company_id", "user_login", "expected_code"),
    [
        ("unknown", 7, "v4-agent", "database_unavailable"),
        ("v4-dev", 8, "v4-agent", "company_unavailable"),
        ("v4-dev", 7, "other-user", "user_unavailable"),
    ],
)
def test_resolve_rejects_every_unknown_database_company_user_tuple(
    tmp_path,
    alias: str,
    company_id: int,
    user_login: str,
    expected_code: str,
) -> None:
    config = load_runtime_config(_write_config(tmp_path))

    with pytest.raises(ConfigError) as caught:
        config.resolve(alias, company_id, user_login)

    assert caught.value.code == expected_code


@pytest.mark.parametrize(
    "change",
    [
        lambda value: value.update(config_schema_version="v2"),
        lambda value: value["bridge"].update(argv="python bridge.py"),
        lambda value: value["bridge"].update(timeout_seconds=0),
        lambda value: value["aliases"]["v4-dev"].update(database=""),
        lambda value: value["aliases"]["v4-dev"].update(database="postgres"),
        lambda value: value.update(unexpected=True),
    ],
)
def test_invalid_runtime_config_is_rejected(tmp_path, change) -> None:
    path = _write_config(tmp_path)
    value = json.loads(path.read_text(encoding="utf-8"))
    change(value)
    path.write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(ConfigError) as caught:
        load_runtime_config(path)

    assert caught.value.code == "invalid_config"
