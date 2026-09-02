from __future__ import annotations

import hashlib
import io
import json

import pytest

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.bridge.core_writes import OdooCoreWritePort
from odoo_accounting_cli_v4.cli import main
from odoo_accounting_cli_v4.registry import load_registry

_ACCOUNT_RETURN_WRITE_PARAMETERS = {
    "account.return.create": {
        "return_type_id": 17,
        "date_from": "2027-01-01",
        "date_to": "2027-12-31",
    },
    "account.return.checks.refresh": {"return_id": 61},
    "account.return.check.result.update": {"check_id": 71, "result": "reviewed"},
    "account.return.validate": {"return_id": 61},
    "account.return.mark_submitted": {"return_id": 61},
    "account.return.archive": {"return_id": 61},
    "account.return.restore": {"return_id": 61},
    "account.return.delete": {"return_id": 61},
}

_ACCOUNT_RETURN_WRITE_MODELS = {
    capability_id: (
        "account.return.check"
        if capability_id == "account.return.check.result.update"
        else "account.return"
    )
    for capability_id in _ACCOUNT_RETURN_WRITE_PARAMETERS
}


@pytest.fixture(scope="module")
def account_return_registry() -> object:
    return load_registry()


def _request(parameters: dict) -> dict:
    return {
        "schema_version": "v1",
        "request_id": "6374689a-e98c-4498-8bc1-546e7abfcbf5",
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }


def _run(capability_id: str, parameters: dict, port: object) -> dict:
    stdout = io.StringIO()
    stderr = io.StringIO()
    exit_code = main(
        ["read", capability_id, "--request", "-"],
        stdin=io.StringIO(json.dumps(_request(parameters))),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda selected, parsed: port,
    )
    assert exit_code == 0, (json.loads(stdout.getvalue()), stderr.getvalue())
    assert stderr.getvalue() == ""
    return json.loads(stdout.getvalue())


def _return_item() -> dict:
    return {
        "id": 61,
        "name": "Corporate Tax 2025",
        "active": True,
        "date_from": "2025-01-01",
        "date_to": "2025-12-31",
        "date_deadline": "2026-03-31",
        "date_submission": None,
        "date_lock": None,
        "type": {"id": 17, "name": "Corporate Tax", "category": "account_return"},
        "state": "new",
        "next_state": "reviewed",
        "is_completed": False,
        "company_id": 7,
        "tax_unit_id": None,
        "manually_created": True,
        "check_counts": {"total": 1, "unresolved": 1, "resolved": 0},
    }


def _check_item() -> dict:
    return {
        "id": 71,
        "return": {"id": 61, "name": "Corporate Tax 2025"},
        "code": "ODACV4-CHECK",
        "type": "check",
        "name": "Review the return",
        "message": None,
        "state": "new",
        "result": "todo",
        "records_count": 0,
    }


class _AccountReturnPort:
    user_id = 42

    def read(self, *, capability_id, company_id, parameters):
        assert company_id == 7
        if capability_id in {"account.return.search", "account.return.get"}:
            item = _return_item()
        elif capability_id == "account.return.summary":
            item = {
                "company_id": 7,
                "as_of": "2026-01-31",
                "counts": {
                    "total": 2,
                    "open": 1,
                    "completed": 1,
                    "overdue": 0,
                    "due_today": 0,
                    "due_next_30_days": 1,
                    "later": 0,
                },
            }
        elif capability_id == "account.return.type.list":
            item = {
                "id": 17,
                "name": "Corporate Tax",
                "company_id": 7,
                "category": "account_return",
                "report": None,
                "country": None,
                "auto_generate": False,
                "states_workflow": "generic_state_review_submit",
                "deadline_periodicity": "year",
                "deadline_start_date": "2025-01-01",
                "deadline_days_delay": 90,
            }
        else:
            item = _check_item()
        return {
            "user_id": 42,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "cursor_found": True,
            "items": [item],
        }


@pytest.mark.parametrize(
    ("capability_id", "parameters", "record_ids"),
    [
        ("account.return.search", {"limit": 10}, [61]),
        ("account.return.get", {"return_id": 61}, [61]),
        ("account.return.summary", {"as_of": "2026-01-31"}, []),
        ("account.return.type.list", {"limit": 10}, [17]),
        ("account.return.check.list", {"return_id": 61, "limit": 10}, [71]),
        ("account.return.check.get", {"check_id": 71}, [71]),
    ],
)
def test_cli_dispatches_account_return_reads(
    capability_id: str, parameters: dict, record_ids: list[int]
) -> None:
    document = _run(capability_id, parameters, _AccountReturnPort())

    assert document["capability"] == capability_id
    assert document["odoo"]["record_ids"] == record_ids


class _JournalAnalysisPort:
    user_id = 42

    def read(self, *, capability_id, company_id, parameters):
        assert company_id == 7
        if capability_id == "journal.accounting_date.resolve":
            item = {
                "company_id": 7,
                "journal": {"id": 4, "code": "MISC", "name": "Miscellaneous"},
                "requested_date": "2025-12-31",
                "has_tax": False,
                "accounting_date": "2025-12-31",
                "adjusted": False,
            }
        elif capability_id == "analytic.line.summary":
            item = {
                "company_id": 7,
                "date_from": "2025-01-01",
                "date_to": "2025-12-31",
                "basis": "analytic_lines",
                "group_by": "analytic_account",
                "plan": {"id": 11, "name": "Projects"},
                "company_currency": {"id": 6, "code": "CNY"},
                "groups": [
                    {
                        "analytic_account": {
                            "id": 21,
                            "name": "Project A",
                            "code": "A",
                        },
                        "row_count": 2,
                        "amount": "100",
                        "unit_amount": "4",
                    }
                ],
                "totals": {"row_count": 2, "amount": "100", "unit_amount": "4"},
            }
        else:
            item = {
                "company_id": 7,
                "date_from": "2025-01-01",
                "date_to": "2025-12-31",
                "basis": "posted_entries",
                "group_by": "journal",
                "company_currency": {"id": 6, "code": "CNY"},
                "groups": [
                    {
                        "group": {"id": 4, "code": "MISC", "name": "Miscellaneous"},
                        "row_count": 2,
                        "debit": "100",
                        "credit": "100",
                        "balance": "0",
                    }
                ],
                "totals": {
                    "row_count": 2,
                    "debit": "100",
                    "credit": "100",
                    "balance": "0",
                },
            }
        return {
            "user_id": 42,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "cursor_found": True,
            "items": [item],
        }


@pytest.mark.parametrize(
    ("capability_id", "parameters", "record_ids"),
    [
        (
            "journal.accounting_date.resolve",
            {"journal_id": 4, "date": "2025-12-31", "has_tax": False},
            [4],
        ),
        (
            "journal_item.analysis.summary",
            {
                "date_from": "2025-01-01",
                "date_to": "2025-12-31",
                "group_by": "journal",
            },
            [],
        ),
        (
            "analytic.line.summary",
            {
                "date_from": "2025-01-01",
                "date_to": "2025-12-31",
                "plan_id": 11,
            },
            [],
        ),
    ],
)
def test_cli_dispatches_journal_analysis_reads(
    capability_id: str, parameters: dict, record_ids: list[int]
) -> None:
    document = _run(capability_id, parameters, _JournalAnalysisPort())

    assert document["capability"] == capability_id
    assert document["odoo"]["record_ids"] == record_ids


def _write_key(capability_id: str) -> str:
    parameters = _ACCOUNT_RETURN_WRITE_PARAMETERS[capability_id]
    if capability_id == "account.return.create":
        canonical = json.dumps(
            parameters,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"{capability_id}:7:{digest}"
    if capability_id == "account.return.check.result.update":
        return f"{capability_id}:71:reviewed"
    return f"{capability_id}:61"


class _AccountReturnWritePort:
    user_id = 42

    def __init__(self, capability_id: str) -> None:
        self.capability_id = capability_id

    def execute(self, **kwargs: object) -> dict:
        parameters = _ACCOUNT_RETURN_WRITE_PARAMETERS[self.capability_id]
        assert kwargs == {
            "capability_id": self.capability_id,
            "company_id": 7,
            "idempotency_key": _write_key(self.capability_id),
            "confirmation": self.capability_id,
            "parameters": parameters,
        }
        is_check = self.capability_id == "account.return.check.result.update"
        return {
            "user_id": self.user_id,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "idempotent_replay": False,
            "result": {
                "model": _ACCOUNT_RETURN_WRITE_MODELS[self.capability_id],
                "id": 901
                if self.capability_id == "account.return.create"
                else 71
                if is_check
                else 61,
                "name": "Review the return" if is_check else "Corporate Tax 2027",
                "state": {
                    "account.return.create": "new",
                    "account.return.checks.refresh": "new",
                    "account.return.check.result.update": "reviewed",
                    "account.return.validate": "reviewed",
                    "account.return.mark_submitted": "submitted",
                    "account.return.archive": "archived",
                    "account.return.restore": "new",
                    "account.return.delete": "deleted",
                }[self.capability_id],
                "company_id": 7,
                "move_type": None,
                "source_id": 61 if is_check else 17,
                "line_ids": [],
                "partial_reconcile_ids": [],
                "full_reconcile_id": None,
                "reconciled": False,
            },
        }


@pytest.mark.parametrize(
    "capability_id", sorted(_ACCOUNT_RETURN_WRITE_PARAMETERS)
)
def test_cli_runs_each_account_return_write(
    capability_id: str,
    account_return_registry: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "load_registry", lambda: account_return_registry)
    stdout = io.StringIO()
    stderr = io.StringIO()
    exit_code = main(
        [
            "write",
            "run",
            capability_id,
            "--request",
            "-",
            "--idempotency-key",
            _write_key(capability_id),
            "--confirm",
            capability_id,
        ],
        stdin=io.StringIO(
            json.dumps(_request(_ACCOUNT_RETURN_WRITE_PARAMETERS[capability_id]))
        ),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda selected, _request: _AccountReturnWritePort(selected),
    )

    document = json.loads(stdout.getvalue())
    assert exit_code == 0, (document, stderr.getvalue())
    assert stderr.getvalue() == ""
    assert document["capability"] == capability_id
    assert document["success"] is True
    assert document["odoo"]["model"] == _ACCOUNT_RETURN_WRITE_MODELS[capability_id]


def test_account_return_writes_route_to_the_core_write_port(
    monkeypatch: pytest.MonkeyPatch,
    account_return_registry: object,
) -> None:
    registry = account_return_registry
    target = object()
    client = object()

    class RuntimeConfig:
        def resolve(self, database: str, company_id: int, user_login: str) -> object:
            assert (database, company_id, user_login) == ("v4-dev", 7, "v4-agent")
            return target

    monkeypatch.setattr(cli, "load_runtime_config", lambda _path: RuntimeConfig())
    monkeypatch.setattr(cli, "OdooBridgeClient", lambda *_args, **_kwargs: client)

    for capability_id, model in _ACCOUNT_RETURN_WRITE_MODELS.items():
        descriptor = registry.describe(capability_id)
        assert descriptor["handler_key"] == "core_write"
        assert cli._CAPABILITY_MODELS[capability_id] == model
        port = cli._configured_port_factory(
            capability_id,
            _request(_ACCOUNT_RETURN_WRITE_PARAMETERS[capability_id]),
        )
        assert type(port) is OdooCoreWritePort
        assert port._client is client
