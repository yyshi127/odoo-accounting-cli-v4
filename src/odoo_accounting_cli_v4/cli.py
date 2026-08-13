"""Stable command surface for the independent V4 control CLI."""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
import uuid
from collections.abc import Callable, Sequence
from functools import partial
from pathlib import Path
from typing import Any, TextIO

from odoo_accounting_cli_v4 import __version__
from odoo_accounting_cli_v4.bridge.account_accounts import OdooAccountListPort
from odoo_accounting_cli_v4.bridge.client import BridgeError, OdooBridgeClient
from odoo_accounting_cli_v4.bridge.financial_reports import OdooFinancialReportPort
from odoo_accounting_cli_v4.bridge.journal_entries import OdooJournalEntryPort
from odoo_accounting_cli_v4.bridge.master_data import OdooMasterDataPort
from odoo_accounting_cli_v4.capabilities.account_account_list import (
    AccountListError,
    read_account_accounts,
    validate_account_list_request,
)
from odoo_accounting_cli_v4.capabilities.master_data_lists import (
    MasterDataListError,
    read_master_data,
    validate_master_data_request,
)
from odoo_accounting_cli_v4.capabilities.financial_reports import (
    FinancialReportError,
    read_balance_sheet,
    read_trial_balance,
    validate_balance_sheet_request,
    validate_trial_balance_request,
)
from odoo_accounting_cli_v4.capabilities.journal_entries import (
    JournalEntryError,
    get_journal_entry,
    search_journal_entries,
    validate_journal_entry_get_request,
    validate_journal_entry_search_request,
)
from odoo_accounting_cli_v4.contracts import dumps, error_document, success_document
from odoo_accounting_cli_v4.config import ConfigError, load_runtime_config
from odoo_accounting_cli_v4.registry import (
    CapabilityNotFound,
    InstanceValidationError,
    RegistryError,
    load_registry,
)


PortFactory = Callable[[str, dict[str, Any]], object]
_MAX_REQUEST_BYTES = 1024 * 1024
_DEFAULT_RUNTIME_CONFIG = Path("/etc/odoo-accounting-cli-v4/runtime.json")
_HANDLERS: dict[str, Callable[[object, dict[str, Any]], dict[str, Any]]] = {
    "account_account_list": read_account_accounts,
    "company_accounting_context_list": partial(
        read_master_data, "company.accounting_context.list"
    ),
    "journal_list": partial(read_master_data, "journal.list"),
    "tax_list": partial(read_master_data, "tax.list"),
    "payment_term_list": partial(read_master_data, "payment_term.list"),
    "currency_list": partial(read_master_data, "currency.list"),
    "journal_entry_search": search_journal_entries,
    "journal_entry_get": get_journal_entry,
    "report_trial_balance": read_trial_balance,
    "report_balance_sheet": read_balance_sheet,
}
_REQUEST_VALIDATORS: dict[str, Callable[[Any], object]] = {
    "account_account_list": validate_account_list_request,
    "company_accounting_context_list": partial(
        validate_master_data_request, "company.accounting_context.list"
    ),
    "journal_list": partial(validate_master_data_request, "journal.list"),
    "tax_list": partial(validate_master_data_request, "tax.list"),
    "payment_term_list": partial(validate_master_data_request, "payment_term.list"),
    "currency_list": partial(validate_master_data_request, "currency.list"),
    "journal_entry_search": validate_journal_entry_search_request,
    "journal_entry_get": validate_journal_entry_get_request,
    "report_trial_balance": validate_trial_balance_request,
    "report_balance_sheet": validate_balance_sheet_request,
}
_CAPABILITY_MODELS = {
    "account.account.list": "account.account",
    "company.accounting_context.list": "res.company",
    "journal.list": "account.journal",
    "tax.list": "account.tax",
    "payment_term.list": "account.payment.term",
    "currency.list": "res.currency",
    "journal_entry.search": "account.move",
    "journal_entry.get": "account.move",
    "report.trial_balance": "account.report",
    "report.balance_sheet": "account.report",
}


class CliError(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        exit_code: int,
        status: str,
        capability: str,
        request_id: str | None = None,
        details: dict[str, Any] | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code
        self.status = status
        self.capability = capability
        self.request_id = request_id
        self.details = details or {}
        self.retryable = retryable


class _JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliError(
            "invalid_arguments",
            "The command arguments are invalid.",
            exit_code=2,
            status="invalid",
            capability="cli",
        )


def _parser() -> argparse.ArgumentParser:
    parser = _JsonArgumentParser(prog="odoo-accounting-cli-v4")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("version", help="Show bootstrap package metadata as JSON")
    commands.add_parser("doctor", help="Check the configured V4 runtime")

    capabilities = commands.add_parser(
        "capabilities", help="Discover versioned accounting capabilities"
    )
    capability_commands = capabilities.add_subparsers(
        dest="capabilities_command", required=True
    )
    capability_commands.add_parser("list", help="List all registered capabilities")
    describe = capability_commands.add_parser(
        "describe", help="Describe one exact capability ID"
    )
    describe.add_argument("capability_id")

    read = commands.add_parser("read", help="Execute one registered read capability")
    read.add_argument("capability_id")
    read.add_argument(
        "--request",
        required=True,
        dest="request_source",
        metavar="@FILE|-",
        help="Read one v1 JSON request from @FILE or stdin (-)",
    )

    write = commands.add_parser("write", help="Manage approved write operations")
    write_commands = write.add_subparsers(dest="write_command", required=True)
    prepare = write_commands.add_parser("prepare")
    prepare.add_argument("capability_id")
    prepare.add_argument("--request", required=True, dest="request_source")
    prepare.add_argument("--idempotency-key", required=True)
    approve = write_commands.add_parser("approve")
    approve.add_argument("operation_id")
    approve.add_argument("--approval", required=True, dest="approval_source")
    execute = write_commands.add_parser("execute")
    execute.add_argument("operation_id")

    operations = commands.add_parser("operations", help="Inspect write operations")
    operation_commands = operations.add_subparsers(
        dest="operations_command", required=True
    )
    for name in ("get", "verify"):
        operation = operation_commands.add_parser(name)
        operation.add_argument("operation_id")
    reverse = operation_commands.add_parser("reverse")
    reverse.add_argument("operation_id")
    reverse.add_argument("--request", required=True, dest="request_source")
    return parser


def _emit(document: dict[str, Any], stdout: TextIO) -> None:
    stdout.write(dumps(document))
    stdout.write("\n")
    stdout.flush()


def _status_for_exit(exit_code: int) -> str:
    return {
        2: "invalid",
        3: "denied",
        4: "unavailable",
        5: "conflict",
        6: "failed",
        7: "failed",
        8: "failed_validation",
    }.get(exit_code, "failed")


def _safe_request_id(request: dict[str, Any]) -> str | None:
    value = request.get("request_id")
    if not isinstance(value, str):
        return None
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError):
        return None
    return value if str(parsed) == value.lower() else None


def _safe_capability(value: object) -> str:
    return value if isinstance(value, str) and value else "cli"


def _decode_request(raw: str) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise CliError(
                    "invalid_request",
                    "The request contains a duplicate JSON key.",
                    exit_code=2,
                    status="invalid",
                    capability="read",
                )
            value[key] = item
        return value

    try:
        value = json.loads(raw, object_pairs_hook=reject_duplicates)
    except CliError:
        raise
    except json.JSONDecodeError as exc:
        raise CliError(
            "invalid_request",
            "The request is not valid JSON.",
            exit_code=2,
            status="invalid",
            capability="read",
        ) from exc
    if not isinstance(value, dict):
        raise CliError(
            "invalid_request",
            "The request must be a JSON object.",
            exit_code=2,
            status="invalid",
            capability="read",
        )
    return value


def _read_nofollow(path: Path) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise CliError(
            "invalid_request_source",
            "The request file cannot be opened.",
            exit_code=2,
            status="invalid",
            capability="read",
        ) from exc
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_size > _MAX_REQUEST_BYTES:
            raise CliError(
                "invalid_request_source",
                "The request source must be a small regular file.",
                exit_code=2,
                status="invalid",
                capability="read",
            )
        chunks: list[bytes] = []
        remaining = _MAX_REQUEST_BYTES + 1
        while remaining:
            chunk = os.read(descriptor, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        if len(raw) > _MAX_REQUEST_BYTES:
            raise CliError(
                "invalid_request_source",
                "The request file is too large.",
                exit_code=2,
                status="invalid",
                capability="read",
            )
        return raw
    finally:
        os.close(descriptor)


def _load_request(source: str, stdin: TextIO) -> dict[str, Any]:
    if source == "-":
        raw = stdin.read(_MAX_REQUEST_BYTES + 1)
        if len(raw.encode("utf-8")) > _MAX_REQUEST_BYTES:
            raise CliError(
                "invalid_request_source",
                "The request on stdin is too large.",
                exit_code=2,
                status="invalid",
                capability="read",
            )
    elif source.startswith("@") and len(source) > 1:
        try:
            raw = _read_nofollow(Path(source[1:])).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise CliError(
                "invalid_request_source",
                "The request file must be UTF-8 JSON.",
                exit_code=2,
                status="invalid",
                capability="read",
            ) from exc
    else:
        raise CliError(
            "invalid_request_source",
            "--request must be '-' or an @FILE reference.",
            exit_code=2,
            status="invalid",
            capability="read",
        )
    return _decode_request(raw)


def _list_capabilities() -> dict[str, Any]:
    registry = load_registry()
    items = []
    for capability_id in registry.ids():
        descriptor = registry.describe(capability_id)
        items.append(
            {
                "id": capability_id,
                "summary": descriptor["summary"],
                "domain": descriptor["domain"],
                "access": descriptor["access"],
                "status": descriptor["status"],
                "required_slots": descriptor["routing"]["required_slots"],
            }
        )
    document = success_document(
        "capabilities.list",
        {"registry_digest": registry.digest, "capabilities": items},
    )
    registry.validate_instance("schemas/v1/response.schema.json", document)
    return document


def _describe_capability(capability_id: str) -> dict[str, Any]:
    registry = load_registry()
    try:
        descriptor = registry.describe(capability_id)
    except CapabilityNotFound as exc:
        raise CliError(
            "capability_not_found",
            "The requested capability is not registered.",
            exit_code=4,
            status="unavailable",
            capability=capability_id,
        ) from exc
    document = success_document(
        "capabilities.describe",
        {
            "id": capability_id,
            "registry_digest": registry.digest,
            "descriptor": descriptor,
            "request_schema": registry.load_schema(descriptor["schemas"]["request"]),
            "response_schema": registry.load_schema(
                descriptor["schemas"]["response"]
            ),
        },
    )
    registry.validate_instance("schemas/v1/response.schema.json", document)
    return document


def _execute_read(
    capability_id: str,
    request_source: str,
    *,
    stdin: TextIO,
    port_factory: PortFactory | None,
) -> dict[str, Any]:
    registry = load_registry()
    try:
        descriptor = registry.describe(capability_id)
    except CapabilityNotFound as exc:
        raise CliError(
            "capability_not_found",
            "The requested capability is not registered.",
            exit_code=4,
            status="unavailable",
            capability=capability_id,
        ) from exc
    if descriptor["access"] != "read":
        raise CliError(
            "policy_denied",
            "The requested capability is not a read capability.",
            exit_code=3,
            status="denied",
            capability=capability_id,
        )
    if descriptor["status"]["value"] not in {
        "available",
        "degraded",
        "unconfigured",
    }:
        raise CliError(
            "capability_unavailable",
            "The requested capability is not currently available.",
            exit_code=4,
            status="unavailable",
            capability=capability_id,
            details={"reason_code": descriptor["status"]["reason_code"]},
        )

    handler = _HANDLERS.get(descriptor["handler_key"])
    validator = _REQUEST_VALIDATORS.get(descriptor["handler_key"])
    if handler is None or validator is None:
        raise CliError(
            "capability_unavailable",
            "The registered capability has no allowlisted handler.",
            exit_code=4,
            status="unavailable",
            capability=capability_id,
        )

    try:
        request = _load_request(request_source, stdin)
    except CliError as exc:
        raise CliError(
            exc.code,
            str(exc),
            exit_code=exc.exit_code,
            status=exc.status,
            capability=capability_id,
            request_id=exc.request_id,
            details=exc.details,
            retryable=exc.retryable,
        ) from exc
    request_id = _safe_request_id(request)
    try:
        registry.validate_instance(descriptor["schemas"]["request"], request)
        validator(request)
    except InstanceValidationError as exc:
        raise CliError(
            "invalid_request",
            "The request does not match the capability schema.",
            exit_code=2,
            status="invalid",
            capability=capability_id,
            request_id=request_id,
        ) from exc
    except (
        AccountListError,
        MasterDataListError,
        JournalEntryError,
        FinancialReportError,
    ) as exc:
        raise CliError(
            exc.code,
            str(exc),
            exit_code=exc.exit_code,
            status=_status_for_exit(exc.exit_code),
            capability=capability_id,
            request_id=request_id,
            details=exc.details,
            retryable=exc.retryable,
        ) from exc
    if port_factory is None:
        port_factory = _configured_port_factory
    try:
        port = port_factory(capability_id, request)
        data = handler(port, request)
    except (
        AccountListError,
        MasterDataListError,
        JournalEntryError,
        FinancialReportError,
    ) as exc:
        raise CliError(
            exc.code,
            str(exc),
            exit_code=exc.exit_code,
            status=_status_for_exit(exc.exit_code),
            capability=capability_id,
            request_id=request_id,
            details=exc.details,
            retryable=exc.retryable,
        ) from exc
    except ConfigError as exc:
        if exc.code in {"unconfigured", "database_unavailable"}:
            exit_code = 4
        elif exc.code in {"company_unavailable", "user_unavailable"}:
            exit_code = 3
        else:
            exit_code = 7
        raise CliError(
            exc.code,
            "No matching Odoo bridge configuration is active.",
            exit_code=exit_code,
            status=_status_for_exit(exit_code),
            capability=capability_id,
            request_id=request_id,
        ) from exc
    except BridgeError as exc:
        raise CliError(
            exc.code,
            str(exc),
            exit_code=exc.exit_code,
            status=_status_for_exit(exc.exit_code),
            capability=capability_id,
            request_id=request_id,
            details=exc.details,
            retryable=exc.retryable,
        ) from exc

    context = request["context"]
    warnings = []
    if descriptor["status"]["value"] == "degraded":
        warnings.append(
            {
                "code": "capability_degraded",
                "reason_code": descriptor["status"]["reason_code"],
            }
        )
    document = success_document(
        capability_id,
        data,
        request_id=request_id,
        warnings=warnings,
        database=context["database"],
        company_id=context["company_id"],
        user_id=getattr(port, "user_id", None),
        model=_CAPABILITY_MODELS[capability_id],
        record_ids=(
            []
            if capability_id.startswith("report.")
            else (
                [data["id"]]
                if capability_id == "journal_entry.get"
                else [item["id"] for item in data["items"]]
            )
        ),
    )
    try:
        registry.validate_instance(descriptor["schemas"]["response"], document)
    except InstanceValidationError as exc:
        raise CliError(
            "failed_validation",
            "The Odoo result does not match the capability schema.",
            exit_code=8,
            status="failed_validation",
            capability=capability_id,
            request_id=request_id,
        ) from exc
    return document


def _configured_port_factory(
    capability_id: str, request: dict[str, Any]
) -> object:
    if capability_id not in _CAPABILITY_MODELS:
        raise ConfigError("capability_unavailable", "The capability is unavailable.")
    configured_path = os.environ.get("ODOO_ACCOUNTING_CLI_V4_CONFIG")
    path = Path(configured_path) if configured_path else _DEFAULT_RUNTIME_CONFIG
    context = request["context"]
    target = load_runtime_config(path).resolve(
        context["database"], context["company_id"], context["user_login"]
    )
    client = OdooBridgeClient(
        target,
        language=context["language"],
        timezone=context["timezone"],
    )
    if capability_id == "account.account.list":
        return OdooAccountListPort(client)
    if capability_id in {"journal_entry.search", "journal_entry.get"}:
        return OdooJournalEntryPort(client)
    if capability_id in {"report.trial_balance", "report.balance_sheet"}:
        return OdooFinancialReportPort(client, capability_id)
    return OdooMasterDataPort(client, capability_id)


def main(
    argv: Sequence[str] | None = None,
    *,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    port_factory: PortFactory | None = None,
) -> int:
    input_stream = stdin or sys.stdin
    output_stream = stdout or sys.stdout
    error_stream = stderr or sys.stderr
    try:
        args = _parser().parse_args(argv)
        if args.command == "version":
            _emit(
                {
                    "product": "odoo-accounting-cli-v4",
                    "version": __version__,
                    "status": "bootstrap",
                },
                output_stream,
            )
            return 0
        if args.command in {"doctor", "write", "operations"}:
            if args.command == "write":
                capability = f"write.{args.write_command}"
            elif args.command == "operations":
                capability = f"operations.{args.operations_command}"
            else:
                capability = "doctor"
            raise CliError(
                "command_unavailable",
                "This stable command is not implemented in the current bootstrap.",
                exit_code=4,
                status="unavailable",
                capability=capability,
            )
        if args.command == "capabilities":
            if args.capabilities_command == "list":
                document = _list_capabilities()
            elif args.capabilities_command == "describe":
                document = _describe_capability(args.capability_id)
            else:  # pragma: no cover - argparse enforces the choices
                raise AssertionError("unhandled capabilities command")
        elif args.command == "read":
            document = _execute_read(
                args.capability_id,
                args.request_source,
                stdin=input_stream,
                port_factory=port_factory,
            )
        else:  # pragma: no cover - argparse enforces the choices
            raise AssertionError(f"unhandled command: {args.command}")
        _emit(document, output_stream)
        return 0
    except CliError as exc:
        _emit(
            error_document(
                _safe_capability(exc.capability),
                exc.code,
                str(exc),
                request_id=exc.request_id,
                status=exc.status,
                details=exc.details,
                retryable=exc.retryable,
            ),
            output_stream,
        )
        return exc.exit_code
    except (RegistryError, InstanceValidationError):
        error_stream.write("registry validation failed\n")
        _emit(
            error_document(
                "registry",
                "registry_invalid",
                "The installed capability registry failed validation.",
                status="failed_validation",
            ),
            output_stream,
        )
        return 8
    except Exception:
        error_stream.write("internal runtime failure\n")
        _emit(
            error_document(
                _safe_capability(
                    getattr(locals().get("args"), "capability_id", "cli")
                ),
                "runtime_error",
                "The command failed without exposing internal details.",
                status="failed",
                retryable=False,
            ),
            output_stream,
        )
        return 7
