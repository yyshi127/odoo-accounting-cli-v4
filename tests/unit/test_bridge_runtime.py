from __future__ import annotations

import io
import json

import pytest

from odoo_accounting_cli_v4.bridge import runtime
from odoo_accounting_cli_v4.bridge.runtime import RuntimeFailure


def _request(**overrides):
    value = {
        "schema_version": "v1",
        "target": {
            "alias": "v4-dev",
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "zh_CN",
            "timezone": "Asia/Shanghai",
        },
        "action": "account.account.read_page",
        "payload": {
            "company_id": 7,
            "after_code": None,
            "after_id": None,
            "limit": 3,
        },
    }
    value.update(overrides)
    return json.dumps(value)


def test_decode_accepts_only_the_fixed_target_and_action_envelope(monkeypatch) -> None:
    monkeypatch.setattr(runtime.sys, "stdin", io.StringIO(_request()))

    value = runtime._decode_request(runtime.sys.stdin)

    assert value["target"]["database"] == "odoo_cli_v4_dev"
    assert value["action"] == "account.account.read_page"


def test_decode_accepts_the_single_allowlisted_core_write_action() -> None:
    value = runtime._decode_request(
        io.StringIO(_request(action="accounting.core_write.execute"))
    )

    assert value["action"] == "accounting.core_write.execute"


def test_decode_accepts_the_core_object_read_action() -> None:
    value = runtime._decode_request(
        io.StringIO(_request(action="accounting.core_object.read"))
    )

    assert value["action"] == "accounting.core_object.read"


def test_decode_accepts_the_budget_report_read_action() -> None:
    value = runtime._decode_request(
        io.StringIO(_request(action="accounting.budget_report.read"))
    )

    assert value["action"] == "accounting.budget_report.read"
    assert (
        runtime._cursor_factory_for("accounting.budget_report.read", {})
        is runtime._read_only_cursor
    )


def test_decode_accepts_the_inventory_accounting_action() -> None:
    value = runtime._decode_request(
        io.StringIO(
            _request(
                action="accounting.inventory.read",
                payload={
                    "capability_id": "report.inventory_valuation",
                    "company_id": 7,
                    "parameters": {"date": "2025-01-31"},
                },
            )
        )
    )

    assert value["action"] == "accounting.inventory.read"


@pytest.mark.parametrize(
    "action",
    [
        "accounting.inventory_master.read",
        "accounting.inventory_operations.read",
        "accounting.order_documents.read",
    ],
)
def test_decode_accepts_narrow_read_actions_with_read_only_cursor(
    action: str,
) -> None:
    value = runtime._decode_request(io.StringIO(_request(action=action)))

    assert value["action"] == action
    assert runtime._cursor_factory_for(action, {}) is runtime._read_only_cursor


def test_inventory_valuation_uses_rollback_only_report_transaction() -> None:
    assert (
        runtime._cursor_factory_for(
            "accounting.inventory.read",
            {
                "capability_id": "report.inventory_valuation",
                "company_id": 7,
                "parameters": {"date": "2025-01-31"},
            },
        )
        is runtime._rollback_only_cursor
    )
    assert (
        runtime._cursor_factory_for(
            "accounting.inventory.read",
            {
                "capability_id": "cogs.entries.list",
                "company_id": 7,
                "parameters": {},
            },
        )
        is runtime._read_only_cursor
    )


@pytest.mark.parametrize(
    "raw",
    [
        "{}",
        _request(action="arbitrary.model.call"),
        _request(action="runtime.identity"),
        _request(action=[]),
        '{"schema_version":"v1","schema_version":"v1"}',
        _request(target={"database": "odoo_cli_v4_dev"}),
    ],
)
def test_decode_rejects_unknown_or_ambiguous_protocol(raw: str) -> None:
    with pytest.raises(RuntimeFailure) as caught:
        runtime._decode_request(io.StringIO(raw))

    assert caught.value.code == "bridge_protocol_error"
    assert caught.value.exit_code == 7


def test_read_only_cursor_forces_postgres_readonly_and_never_commits() -> None:
    calls = []

    class Cursor:
        def execute(self, statement):
            calls.append(("execute", statement))

        def rollback(self):
            calls.append(("rollback",))

        def close(self):
            calls.append(("close",))

        def commit(self):
            raise AssertionError("read bridge must never commit")

    cursor = Cursor()

    class Registry:
        def cursor(self):
            calls.append(("cursor",))
            return cursor

    with runtime._read_only_cursor(Registry()) as observed:
        assert observed is cursor

    assert calls == [
        ("cursor",),
        ("execute", "SET TRANSACTION READ ONLY"),
        ("rollback",),
        ("close",),
    ]


def test_write_cursor_commits_only_after_a_successful_action() -> None:
    calls = []

    class Cursor:
        def commit(self):
            calls.append(("commit",))

        def rollback(self):
            calls.append(("rollback",))

        def close(self):
            calls.append(("close",))

    cursor = Cursor()

    class Registry:
        def cursor(self):
            calls.append(("cursor",))
            return cursor

    with runtime._write_cursor(Registry()) as observed:
        assert observed is cursor

    assert calls == [("cursor",), ("commit",), ("close",)]


def test_write_cursor_rolls_back_a_failed_action() -> None:
    calls = []

    class Cursor:
        def commit(self):
            raise AssertionError("a failed write must not commit")

        def rollback(self):
            calls.append(("rollback",))

        def close(self):
            calls.append(("close",))

    cursor = Cursor()

    class Registry:
        def cursor(self):
            calls.append(("cursor",))
            return cursor

    with (
        pytest.raises(RuntimeError, match="write failed"),
        runtime._write_cursor(Registry()),
    ):
        raise RuntimeError("write failed")

    assert calls == [("cursor",), ("rollback",), ("close",)]


def test_composite_account_page_uses_one_environment_identity_and_read() -> None:
    calls = []

    class Companies:
        def search_count(self, domain, *, limit):
            calls.append(("company", domain, limit))
            return 1

    class Accounts:
        def has_access(self, operation):
            calls.append(("access", operation))
            return True

        def with_context(self, **context):
            calls.append(("context", context))
            return self

        def search_read(self, domain, *, fields, limit, order):
            calls.append(("search", domain, fields, limit, order))
            return [{"id": 10}]

    accounts = Accounts()

    class Registry:
        def get(self, model):
            calls.append(("registry", model))
            return accounts

    class Environment:
        uid = 42
        registry = Registry()

        def __getitem__(self, model):
            return {"res.company": Companies(), "account.account": accounts}[model]

    result = runtime._dispatch(
        Environment(),
        "account.account.read_page",
        {
            "company_id": 7,
            "after_code": None,
            "after_id": None,
            "limit": 3,
        },
        7,
    )

    assert result == {
        "user_id": 42,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "rows": [{"id": 10}],
    }
    assert [item[0] for item in calls].count("search") == 1


def test_inventory_action_delegates_to_the_narrow_runtime(monkeypatch) -> None:
    from odoo_accounting_cli_v4.bridge import inventory_accounting_runtime

    calls = []

    def delegate(env, payload, company_id, *, failure_type):
        calls.append((env, payload, company_id, failure_type))
        return {"items": []}

    monkeypatch.setattr(inventory_accounting_runtime, "dispatch", delegate)
    environment = object()
    payload = {
        "capability_id": "report.inventory_valuation",
        "company_id": 7,
        "parameters": {"date": "2025-01-31"},
    }

    result = runtime._dispatch(environment, "accounting.inventory.read", payload, 7)

    assert result == {"items": []}
    assert calls == [(environment, payload, 7, RuntimeFailure)]


@pytest.mark.parametrize(
    ("action", "runtime_module"),
    [
        (
            "accounting.inventory_master.read",
            "inventory_master_runtime",
        ),
        (
            "accounting.inventory_operations.read",
            "inventory_operations_runtime",
        ),
        (
            "accounting.order_documents.read",
            "order_documents_runtime",
        ),
    ],
)
def test_narrow_read_actions_delegate_to_narrow_runtimes(
    monkeypatch, action: str, runtime_module: str
) -> None:
    from odoo_accounting_cli_v4.bridge import (
        inventory_master_runtime,
        inventory_operations_runtime,
        order_documents_runtime,
    )

    module = {
        "inventory_master_runtime": inventory_master_runtime,
        "inventory_operations_runtime": inventory_operations_runtime,
        "order_documents_runtime": order_documents_runtime,
    }[runtime_module]
    calls = []

    def delegate(env, payload, company_id, *, failure_type):
        calls.append((env, payload, company_id, failure_type))
        return {"items": []}

    monkeypatch.setattr(module, "dispatch", delegate)
    environment = object()
    payload = {
        "capability_id": "warehouse.list",
        "company_id": 7,
        "parameters": {},
    }

    result = runtime._dispatch(environment, action, payload, 7)

    assert result == {"items": []}
    assert calls == [(environment, payload, 7, RuntimeFailure)]


def test_core_object_action_delegates_to_the_narrow_runtime(monkeypatch) -> None:
    from odoo_accounting_cli_v4.bridge import core_object_reads_runtime

    calls = []

    def delegate(env, payload, company_id, *, failure_type):
        calls.append((env, payload, company_id, failure_type))
        return {"items": []}

    monkeypatch.setattr(core_object_reads_runtime, "dispatch", delegate)
    environment = object()
    payload = {
        "capability_id": "journal.get",
        "company_id": 7,
        "parameters": {"journal_id": 9},
    }

    result = runtime._dispatch(environment, "accounting.core_object.read", payload, 7)

    assert result == {"items": []}
    assert calls == [(environment, payload, 7, RuntimeFailure)]


def test_budget_report_action_delegates_to_the_narrow_runtime(monkeypatch) -> None:
    from odoo_accounting_cli_v4.bridge import budget_report_runtime

    calls = []

    def delegate(env, payload, company_id, *, failure_type):
        calls.append((env, payload, company_id, failure_type))
        return {"items": []}

    monkeypatch.setattr(budget_report_runtime, "dispatch", delegate)
    environment = object()
    payload = {"company_id": 7, "parameters": {"budget_id": 71}}

    result = runtime._dispatch(environment, "accounting.budget_report.read", payload, 7)

    assert result == {"items": []}
    assert calls == [(environment, payload, 7, RuntimeFailure)]


def test_inactive_language_is_rejected_before_business_dispatch() -> None:
    calls = []

    class Languages:
        def with_context(self, **context):
            calls.append(("context", context))
            return self

        def search_count(self, domain, *, limit):
            calls.append(("search_count", domain, limit))
            return 0

    class RootEnvironment:
        def __getitem__(self, model):
            assert model == "res.lang"
            return Languages()

    with pytest.raises(RuntimeFailure) as caught:
        runtime._ensure_language_is_active(RootEnvironment(), "zh_CN")

    assert caught.value.code == "language_unavailable"
    assert caught.value.exit_code == 4
    assert calls == [
        ("context", {"active_test": False}),
        (
            "search_count",
            [("code", "=", "zh_CN"), ("active", "=", True)],
            1,
        ),
    ]


def test_main_emits_one_success_json_document(monkeypatch, tmp_path, capsys) -> None:
    odoo_source = tmp_path / "odoo"
    odoo_source.mkdir()
    monkeypatch.setattr(runtime.sys, "stdin", io.StringIO(_request()))
    monkeypatch.setattr(runtime, "execute", lambda *args, **kwargs: {"user_id": 42})

    result = runtime.main(
        [
            "--runtime-config",
            str(tmp_path / "runtime.json"),
            "--odoo-config",
            str(tmp_path / "odoo.conf"),
            "--odoo-source",
            str(odoo_source),
        ]
    )

    output = capsys.readouterr()
    assert result == 0
    assert output.err == ""
    assert json.loads(output.out) == {
        "schema_version": "v1",
        "success": True,
        "data": {"user_id": 42},
        "error": None,
    }
    assert output.out.count("\n") == 1


def test_main_maps_structured_failure_to_one_json_document(
    monkeypatch, tmp_path, capsys
) -> None:
    odoo_source = tmp_path / "odoo"
    odoo_source.mkdir()
    monkeypatch.setattr(runtime.sys, "stdin", io.StringIO(_request()))

    def fail(*args, **kwargs):
        raise RuntimeFailure("unauthorized", "Access denied.", exit_code=3)

    monkeypatch.setattr(runtime, "execute", fail)

    result = runtime.main(["--odoo-source", str(odoo_source)])

    output = capsys.readouterr()
    document = json.loads(output.out)
    assert result == 3
    assert document["success"] is False
    assert document["error"]["code"] == "unauthorized"
    assert output.err == ""
    assert output.out.count("\n") == 1
