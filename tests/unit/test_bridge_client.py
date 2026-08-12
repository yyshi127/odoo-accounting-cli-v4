from __future__ import annotations

import json
import subprocess

import pytest

from odoo_accounting_cli_v4.bridge.account_accounts import OdooAccountListPort
from odoo_accounting_cli_v4.bridge.client import BridgeError, OdooBridgeClient
from odoo_accounting_cli_v4.capabilities.account_account_list import (
    read_account_accounts,
)


class _Target:
    alias = "v4-dev"
    database = "odoo_cli_v4_dev"
    company_id = 7
    user_login = "v4-agent"
    bridge_argv = ("/usr/bin/python3", "/srv/odacv4/bridge.py")
    timeout_seconds = 15


def _completed(stdout: str, *, returncode: int = 0, stderr: str = ""):
    return subprocess.CompletedProcess(
        args=list(_Target.bridge_argv),
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def test_invoke_uses_argv_without_shell_and_one_json_document(monkeypatch) -> None:
    observed = {}

    def fake_run(argv, **kwargs):
        observed["argv"] = argv
        observed.update(kwargs)
        return _completed(
                json.dumps(
                    {
                        "schema_version": "v1",
                        "success": True,
                        "data": {"ok": True},
                        "error": None,
                    }
                )
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = OdooBridgeClient(
        _Target(), language="zh_CN", timezone="Asia/Shanghai"
    ).invoke("account.account.list", {"limit": 3})

    assert result == {"ok": True}
    assert tuple(observed["argv"]) == _Target.bridge_argv
    assert observed["shell"] is False
    assert observed["text"] is True
    assert observed["capture_output"] is True
    assert observed["timeout"] == 15
    assert json.loads(observed["input"]) == {
        "schema_version": "v1",
        "target": {
            "alias": "v4-dev",
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "zh_CN",
            "timezone": "Asia/Shanghai",
        },
        "action": "account.account.list",
        "payload": {"limit": 3},
    }
    assert observed["input"].endswith("\n")


@pytest.mark.parametrize(
    ("stdout", "expected_code"),
    [
        ("not-json\n", "bridge_protocol_error"),
        (
            '{"schema_version":"v1","success":true,"data":{}}\n'
            '{"schema_version":"v1","success":true,"data":{}}\n',
            "bridge_protocol_error",
        ),
        (
            '{"schema_version":"v1","success":true,"data":{}} trailing\n',
            "bridge_protocol_error",
        ),
    ],
)
def test_invoke_rejects_non_json_or_more_than_one_json_document(
    monkeypatch, stdout: str, expected_code: str
) -> None:
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: _completed(stdout))

    with pytest.raises(BridgeError) as caught:
        OdooBridgeClient(_Target(), language="zh_CN", timezone="Asia/Shanghai").invoke(
            "account.account.list", {}
        )

    assert caught.value.code == expected_code
    assert caught.value.exit_code == 7


def test_invoke_maps_timeout_without_leaking_process_details(monkeypatch) -> None:
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"], output="secret")

    monkeypatch.setattr(subprocess, "run", timeout)

    with pytest.raises(BridgeError) as caught:
        OdooBridgeClient(_Target(), language="zh_CN", timezone="Asia/Shanghai").invoke(
            "account.account.list", {}
        )

    assert caught.value.code == "bridge_timeout"
    assert caught.value.exit_code == 7
    assert caught.value.retryable is True
    assert "secret" not in str(caught.value)


def test_invoke_maps_nonzero_exit_to_runtime_error(monkeypatch) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: _completed("", returncode=9, stderr="traceback secret"),
    )

    with pytest.raises(BridgeError) as caught:
        OdooBridgeClient(_Target(), language="zh_CN", timezone="Asia/Shanghai").invoke(
            "account.account.list", {}
        )

    assert caught.value.code == "bridge_process_error"
    assert caught.value.exit_code == 7
    assert "secret" not in str(caught.value)


def test_invoke_preserves_structured_odoo_error(monkeypatch) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: _completed(
            json.dumps(
                {
                    "schema_version": "v1",
                    "success": False,
                    "data": None,
                    "error": {
                        "code": "unauthorized",
                        "message": "The configured user cannot read accounts.",
                        "details": {"model": "account.account"},
                        "retryable": False,
                        "exit_code": 3,
                    },
                }
            ),
            returncode=3,
        ),
    )

    with pytest.raises(BridgeError) as caught:
        OdooBridgeClient(_Target(), language="zh_CN", timezone="Asia/Shanghai").invoke(
            "account.account.list", {}
        )

    assert caught.value.code == "unauthorized"
    assert caught.value.exit_code == 3
    assert caught.value.retryable is False
    assert caught.value.details == {"model": "account.account"}


@pytest.mark.parametrize("returncode", [0, 2, 7, -15])
def test_invoke_rejects_failure_exit_code_mismatch(monkeypatch, returncode: int) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: _completed(
            json.dumps(
                {
                    "schema_version": "v1",
                    "success": False,
                    "data": None,
                    "error": {
                        "code": "unauthorized",
                        "message": "Access denied.",
                        "details": {},
                        "retryable": False,
                        "exit_code": 3,
                    },
                }
            ),
            returncode=returncode,
        ),
    )

    with pytest.raises(BridgeError) as caught:
        OdooBridgeClient(_Target(), language="zh_CN", timezone="Asia/Shanghai").invoke(
            "account.account.read_page", {}
        )

    assert caught.value.code == "bridge_protocol_error"
    assert caught.value.exit_code == 7


@pytest.mark.parametrize(
    "document",
    [
        {"schema_version": "v1", "success": True, "data": {}, "error": {}},
        {
            "schema_version": "v1",
            "success": True,
            "data": {},
            "error": None,
            "extra": True,
        },
        {"schema_version": "v1", "success": False, "data": {}, "error": {}},
    ],
)
def test_invoke_rejects_noncanonical_response_envelopes(
    monkeypatch, document: dict
) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: _completed(json.dumps(document)),
    )

    with pytest.raises(BridgeError) as caught:
        OdooBridgeClient(_Target(), language="zh_CN", timezone="Asia/Shanghai").invoke(
            "account.account.read_page", {}
        )

    assert caught.value.code == "bridge_protocol_error"


def test_account_list_port_uses_one_composite_protocol_operation() -> None:
    calls = []

    class FakeClient:
        def invoke(self, action, payload):
            calls.append((action, payload))
            return {
                "user_id": 42,
                "company_visible": True,
                "module_installed": True,
                "access_allowed": True,
                "rows": [{"id": 10}],
            }

    port = OdooAccountListPort(FakeClient())

    assert port.read_page(
        company_id=7, after_code="1000", after_id=10, limit=101
    ) == {
        "user_id": 42,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "rows": [{"id": 10}],
    }
    assert port.user_id == 42
    assert calls == [
        (
            "account.account.read_page",
            {
                "company_id": 7,
                "after_code": "1000",
                "after_id": 10,
                "limit": 101,
            },
        ),
    ]


def test_account_list_port_requires_identity_from_the_same_page_response() -> None:
    class FakeClient:
        def invoke(self, action, payload):
            return {
                "user_id": None,
                "company_visible": True,
                "module_installed": True,
                "access_allowed": True,
                "rows": [],
            }

    port = OdooAccountListPort(FakeClient())

    with pytest.raises(ValueError):
        port.read_page(company_id=7, after_code=None, after_id=None, limit=2)


def test_account_list_capability_executes_through_the_odoo_port() -> None:
    calls = []

    class FakeClient:
        def invoke(self, action, payload):
            calls.append((action, payload))
            assert action == "account.account.read_page"
            return {
                "user_id": 42,
                "company_visible": True,
                "module_installed": True,
                "access_allowed": True,
                "rows": [
                    {
                        "id": 10,
                        "code": "1000",
                        "name": "Cash",
                        "account_type": "asset_cash",
                        "active": True,
                        "reconcile": False,
                        "company_ids": [7],
                    }
                ],
            }

    request = {
        "schema_version": "v1",
        "request_id": "7bc39413-0d69-4092-9319-795d33f3167c",
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "zh_CN",
            "timezone": "Asia/Shanghai",
        },
        "parameters": {"limit": 100, "cursor": None},
    }

    result = read_account_accounts(OdooAccountListPort(FakeClient()), request)

    assert result == {
        "items": [
            {
                "id": 10,
                "code": "1000",
                "name": "Cash",
                "account_type": "asset_cash",
                "active": True,
                "reconcile": False,
                "company_ids": [7],
            }
        ],
        "has_more": False,
        "next_cursor": None,
    }
    assert calls == [(
        "account.account.read_page",
        {
            "company_id": 7,
            "after_code": None,
            "after_id": None,
            "limit": 101,
        },
    )]
