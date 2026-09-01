from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from pathlib import Path

from odoo_accounting_cli_v4.cli import main
from odoo_accounting_cli_v4.registry import load_registry


def _run_main(args: list[str], input_text: str = "") -> tuple[int, dict, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    exit_code = main(args, stdin=io.StringIO(input_text), stdout=stdout, stderr=stderr)
    lines = stdout.getvalue().splitlines()
    assert len(lines) == 1
    return exit_code, json.loads(lines[0]), stderr.getvalue()


def test_capabilities_list_is_stable_machine_readable_json() -> None:
    exit_code, document, stderr = _run_main(["capabilities", "list"])

    assert exit_code == 0
    assert stderr == ""
    assert document["schema_version"] == "v1"
    assert document["success"] is True
    assert document["capability"] == "capabilities.list"
    assert set(document) == {
        "schema_version",
        "request_id",
        "success",
        "capability",
        "status",
        "data",
        "warnings",
        "error",
        "odoo",
        "audit",
    }
    listed_ids = [item["id"] for item in document["data"]["capabilities"]]
    assert listed_ids == list(load_registry().ids())
    assert len(listed_ids) == 366
    assert (
        next(
            item
            for item in document["data"]["capabilities"]
            if item["id"] == "journal_entry.post"
        )["status"]["reason_code"]
        == "runtime_context_required"
    )
    assert len(document["data"]["registry_digest"]) == 64


def test_capabilities_describe_returns_descriptor_and_schemas() -> None:
    exit_code, document, _ = _run_main(
        ["capabilities", "describe", "account.account.list"]
    )

    assert exit_code == 0
    assert document["data"]["id"] == "account.account.list"
    assert document["data"]["descriptor"]["handler_key"] == "account_account_list"
    assert document["data"]["request_schema"]["type"] == "object"
    assert document["data"]["response_schema"]["type"] == "object"


def test_unknown_capability_is_one_json_error_and_exit_four() -> None:
    exit_code, document, stderr = _run_main(
        ["capabilities", "describe", "does.not.exist"]
    )

    assert exit_code == 4
    assert stderr == ""
    assert document["success"] is False
    assert document["error"] == {
        "code": "capability_not_found",
        "message": "The requested capability is not registered.",
        "details": {},
        "retryable": False,
    }


def test_empty_unknown_capability_is_normalized_to_a_schema_valid_error() -> None:
    exit_code, document, stderr = _run_main(["capabilities", "describe", ""])

    assert exit_code == 4
    assert stderr == ""
    assert document["capability"] == "cli"
    load_registry().validate_instance("schemas/v1/response.schema.json", document)


def test_read_help_needs_no_odoo_configuration() -> None:
    environment = os.environ.copy()
    for name in (
        "ODOO_URL",
        "ODOO_DB",
        "ODOO_USERNAME",
        "ODOO_PASSWORD",
        "ODOO_ACCOUNTING_CLI_V4_CONFIG",
    ):
        environment.pop(name, None)
    project_root = Path(__file__).resolve().parents[2]
    existing_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = os.pathsep.join(
        part for part in (str(project_root / "src"), existing_pythonpath) if part
    )

    result = subprocess.run(
        [sys.executable, "-m", "odoo_accounting_cli_v4", "read", "--help"],
        cwd=project_root,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "--request" in result.stdout
    assert "configuration_missing" not in result.stdout


def test_subprocess_preserves_nonzero_json_error_exit_code() -> None:
    project_root = Path(__file__).resolve().parents[2]
    environment = os.environ.copy()
    existing_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = os.pathsep.join(
        part for part in (str(project_root / "src"), existing_pythonpath) if part
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "odoo_accounting_cli_v4",
            "capabilities",
            "describe",
            "does.not.exist",
        ],
        cwd=project_root,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 4
    assert result.stderr == ""
    assert json.loads(result.stdout)["error"]["code"] == "capability_not_found"


def test_subprocess_argument_error_is_json_and_exit_two() -> None:
    project_root = Path(__file__).resolve().parents[2]
    environment = os.environ.copy()
    existing_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = os.pathsep.join(
        part for part in (str(project_root / "src"), existing_pythonpath) if part
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "odoo_accounting_cli_v4",
            "read",
            "account.account.list",
        ],
        cwd=project_root,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert result.stderr == ""
    assert json.loads(result.stdout)["error"]["code"] == "invalid_arguments"


class _ReadableAccountPort:
    user_id = 42

    def read_page(self, **kwargs):
        assert kwargs == {
            "company_id": 7,
            "after_code": None,
            "after_id": None,
            "limit": 2,
        }
        return {
            "user_id": self.user_id,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "rows": [
                {
                    "id": 9,
                    "code": "1000",
                    "name": "Cash",
                    "account_type": "asset_cash",
                    "active": True,
                    "reconcile": False,
                    "company_ids": [7],
                }
            ],
        }


def _read_request() -> dict:
    return {
        "schema_version": "v1",
        "request_id": "7bc39413-0d69-4092-9319-795d33f3167c",
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "zh_CN",
            "timezone": "Asia/Shanghai",
        },
        "parameters": {"limit": 1, "cursor": None},
    }


def test_read_dispatches_by_allowlisted_capability_and_preserves_context(
    monkeypatch,
) -> None:
    monkeypatch.delenv("ODOO_ACCOUNTING_CLI_V4_CONFIG", raising=False)
    exit_code, document, stderr = _run_main(
        ["read", "account.account.list", "--request", "-"],
        json.dumps(_read_request()),
    )
    assert exit_code == 4
    assert document["error"]["code"] == "unconfigured"
    assert stderr == ""

    stdout = io.StringIO()
    stderr_stream = io.StringIO()
    exit_code = main(
        ["read", "account.account.list", "--request", "-"],
        stdin=io.StringIO(json.dumps(_read_request())),
        stdout=stdout,
        stderr=stderr_stream,
        port_factory=lambda capability, request: _ReadableAccountPort(),
    )
    document = json.loads(stdout.getvalue())
    assert exit_code == 0
    assert stderr_stream.getvalue() == ""
    assert document["success"] is True
    assert document["capability"] == "account.account.list"
    assert document["request_id"] == _read_request()["request_id"]
    assert document["odoo"] == {
        "database": "v4-dev",
        "company_id": 7,
        "user_id": 42,
        "model": "account.account",
        "record_ids": [9],
    }


def test_unexpected_port_failure_never_exposes_internal_text() -> None:
    secret = "password=s3cr3t Traceback /private/database/name"
    stdout = io.StringIO()
    stderr = io.StringIO()
    exit_code = main(
        ["read", "account.account.list", "--request", "-"],
        stdin=io.StringIO(json.dumps(_read_request())),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda capability, request: (_ for _ in ()).throw(
            RuntimeError(secret)
        ),
    )
    combined = stdout.getvalue() + stderr.getvalue()
    assert exit_code == 7
    assert secret not in combined
    assert "s3cr3t" not in combined
    assert json.loads(stdout.getvalue())["error"]["code"] == "runtime_error"


def test_invalid_read_json_keeps_the_selected_capability_and_exit_two() -> None:
    stdout = io.StringIO()
    exit_code = main(
        ["read", "account.account.list", "--request", "-"],
        stdin=io.StringIO('{"request_id":'),
        stdout=stdout,
        stderr=io.StringIO(),
        port_factory=lambda capability, request: _ReadableAccountPort(),
    )
    document = json.loads(stdout.getvalue())
    assert exit_code == 2
    assert document["capability"] == "account.account.list"
    assert document["error"]["code"] == "invalid_request"


def test_invalid_capability_request_is_rejected_before_bridge_creation() -> None:
    request = _read_request()
    request["parameters"]["limit"] = 0
    bridge_called = False

    def port_factory(capability, parsed_request):
        nonlocal bridge_called
        bridge_called = True
        raise AssertionError("the bridge must not see an invalid request")

    stdout = io.StringIO()
    exit_code = main(
        ["read", "account.account.list", "--request", "-"],
        stdin=io.StringIO(json.dumps(request)),
        stdout=stdout,
        stderr=io.StringIO(),
        port_factory=port_factory,
    )
    document = json.loads(stdout.getvalue())

    assert exit_code == 2
    assert bridge_called is False
    assert document["capability"] == "account.account.list"
    assert document["error"]["code"] == "invalid_request"


def test_invalid_request_id_is_not_reflected_into_the_error_envelope() -> None:
    request = _read_request()
    request["request_id"] = "not-a-uuid"
    stdout = io.StringIO()
    exit_code = main(
        ["read", "account.account.list", "--request", "-"],
        stdin=io.StringIO(json.dumps(request)),
        stdout=stdout,
        stderr=io.StringIO(),
        port_factory=lambda capability, parsed_request: _ReadableAccountPort(),
    )
    document = json.loads(stdout.getvalue())

    assert exit_code == 2
    assert document["request_id"] is None
    assert document["error"]["code"] == "invalid_request"
    load_registry().validate_instance(
        "schemas/v1/account.account.list.response.schema.json", document
    )


def test_invalid_command_arguments_are_one_json_document() -> None:
    exit_code, document, stderr = _run_main(["read", "account.account.list"])

    assert exit_code == 2
    assert stderr == ""
    assert document["capability"] == "cli"
    assert document["error"]["code"] == "invalid_arguments"


def test_all_stable_v1_command_shells_return_explicit_unavailable_json() -> None:
    commands = [
        ["doctor"],
        [
            "write",
            "prepare",
            "account.move.create",
            "--request",
            "-",
            "--idempotency-key",
            "key-1",
        ],
        ["write", "approve", "op-1", "--approval", "-"],
        ["write", "execute", "op-1"],
        ["operations", "get", "op-1"],
        ["operations", "verify", "op-1"],
        ["operations", "reverse", "op-1", "--request", "-"],
    ]

    for command in commands:
        exit_code, document, stderr = _run_main(command)
        assert exit_code == 4
        assert stderr == ""
        assert document["success"] is False
        assert document["status"] == "unavailable"
        assert document["error"]["code"] == "command_unavailable"
        load_registry().validate_instance("schemas/v1/response.schema.json", document)
