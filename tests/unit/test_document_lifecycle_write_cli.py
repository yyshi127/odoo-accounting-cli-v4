from __future__ import annotations

import hashlib
import io
import json
from copy import deepcopy
from typing import Any

import pytest

from odoo_accounting_cli_v4.cli import main

_REQUEST_ID = "529c95af-0b85-4c9a-a9d9-1b5982822987"
_CASES: dict[str, dict[str, Any]] = {
    "invoice.update": {"move_id": 91, "changes": {"reference": "PO-91"}},
    "invoice.lines.replace": {
        "move_id": 91,
        "lines": [
            {
                "name": "Replacement line",
                "product_id": None,
                "account_id": 130,
                "quantity": "2",
                "price_unit": "12.50",
                "discount": "0",
                "tax_ids": [],
            }
        ],
    },
    "invoice.cancel": {"move_id": 91},
    "invoice.reset_to_draft": {"move_id": 91},
    "journal_entry.update": {
        "move_id": 92,
        "changes": {"reference": "Adjustment 92"},
    },
    "journal_entry.lines.replace": {
        "move_id": 92,
        "lines": [
            {
                "name": "Debit",
                "account_id": 152,
                "partner_id": None,
                "debit": "50",
                "credit": "0",
            },
            {
                "name": "Credit",
                "account_id": 130,
                "partner_id": None,
                "debit": "0",
                "credit": "50",
            },
        ],
    },
    "journal_entry.cancel": {"move_id": 92},
    "journal_entry.reset_to_draft": {"move_id": 92},
}


def _request(parameters: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": _REQUEST_ID,
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": deepcopy(parameters),
    }


def _key(capability_id: str, parameters: dict[str, Any]) -> str:
    move_id = parameters["move_id"]
    target = parameters.get("changes", parameters.get("lines"))
    if target is None:
        return f"{capability_id}:{move_id}"
    canonical = json.dumps(
        target,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"{capability_id}:{move_id}:{hashlib.sha256(canonical).hexdigest()[:32]}"


class _Port:
    user_id = 42

    def __init__(self, capability_id: str) -> None:
        self.capability_id = capability_id
        self.calls: list[dict[str, Any]] = []

    def execute(self, **payload: Any) -> dict[str, Any]:
        self.calls.append(payload)
        is_invoice = self.capability_id.startswith("invoice.")
        is_cancel = self.capability_id.endswith(".cancel")
        return {
            "user_id": self.user_id,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "idempotent_replay": False,
            "result": {
                "model": "account.move",
                "id": payload["parameters"]["move_id"],
                "name": "INV/2026/0091" if is_invoice else "MISC/2026/0092",
                "state": "cancel" if is_cancel else "draft",
                "company_id": payload["company_id"],
                "move_type": "out_invoice" if is_invoice else "entry",
                "source_id": None,
                "line_ids": [901, 902],
                "partial_reconcile_ids": [],
                "full_reconcile_id": None,
                "reconciled": False,
            },
        }


@pytest.mark.parametrize("capability_id", tuple(_CASES))
def test_document_lifecycle_write_uses_the_existing_minimal_cli_path(
    capability_id: str,
) -> None:
    parameters = _CASES[capability_id]
    idempotency_key = _key(capability_id, parameters)
    port = _Port(capability_id)
    stdout = io.StringIO()
    stderr = io.StringIO()

    code = main(
        [
            "write",
            "run",
            capability_id,
            "--request",
            "-",
            "--idempotency-key",
            idempotency_key,
            "--confirm",
            capability_id,
        ],
        stdin=io.StringIO(json.dumps(_request(parameters))),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda selected, _document: (
            port if selected == capability_id else None
        ),
    )

    document = json.loads(stdout.getvalue())
    assert code == 0
    assert stderr.getvalue() == ""
    assert port.calls == [
        {
            "capability_id": capability_id,
            "company_id": 7,
            "idempotency_key": idempotency_key,
            "confirmation": capability_id,
            "parameters": parameters,
        }
    ]
    assert document["success"] is True
    assert document["capability"] == capability_id
    assert document["odoo"] == {
        "database": "v4-dev",
        "company_id": 7,
        "user_id": 42,
        "model": "account.move",
        "record_ids": [parameters["move_id"]],
    }
