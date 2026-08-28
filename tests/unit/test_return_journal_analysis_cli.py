from __future__ import annotations

import io
import json

import pytest

from odoo_accounting_cli_v4.cli import main


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
    assert exit_code == 0
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
    ],
)
def test_cli_dispatches_journal_analysis_reads(
    capability_id: str, parameters: dict, record_ids: list[int]
) -> None:
    document = _run(capability_id, parameters, _JournalAnalysisPort())

    assert document["capability"] == capability_id
    assert document["odoo"]["record_ids"] == record_ids
