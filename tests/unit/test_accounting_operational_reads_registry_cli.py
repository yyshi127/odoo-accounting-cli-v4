from __future__ import annotations

import io
import json
from functools import partial
from pathlib import Path

import pytest

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.capabilities.core_object_reads import (
    CORE_OBJECT_READ_CAPABILITY_IDS,
)
from odoo_accounting_cli_v4.cli import (
    _CAPABILITY_MODELS,
    _HANDLERS,
    _REQUEST_VALIDATORS,
)

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "capabilities" / "v1" / "registry.json"
UNIT_REFERENCE = "tests/unit/test_accounting_operational_reads_registry_cli.py"
INTEGRATION_REFERENCE = "tests/integration/test_accounting_operational_reads_live.py"

CAPABILITIES = {
    "invoice.duplicate_candidates.list": {
        "handler": "invoice_duplicate_candidates_list",
        "model": "account.move",
        "modules": ["account", "base"],
        "source_models": {
            "res.company",
            "account.move",
            "res.partner",
            "res.currency",
        },
    },
    "invoice.tax_breakdown.inspect": {
        "handler": "invoice_tax_breakdown_inspect",
        "model": "account.move",
        "modules": ["account", "base"],
        "source_models": {
            "res.company",
            "account.move",
            "account.move.line",
            "account.tax",
            "account.tax.repartition.line",
            "res.currency",
        },
    },
    "recurring.journal_entry.search": {
        "handler": "recurring_journal_entry_search",
        "model": "account.move",
        "modules": ["account", "base"],
        "source_models": {
            "res.company",
            "account.move",
            "account.journal",
            "res.partner",
            "res.currency",
        },
    },
    "recurring.journal_entry.get": {
        "handler": "recurring_journal_entry_get",
        "model": "account.move",
        "modules": ["account", "base"],
        "source_models": {
            "res.company",
            "account.move",
            "account.journal",
            "res.partner",
            "res.currency",
        },
    },
    "account.transfer_model.search": {
        "handler": "account_transfer_model_search",
        "model": "account.transfer.model",
        "modules": ["account_transfer", "account_accountant", "account", "base"],
        "source_models": {
            "res.company",
            "account.transfer.model",
            "account.transfer.model.line",
            "account.journal",
            "account.account",
            "account.move",
        },
    },
    "account.transfer_model.get": {
        "handler": "account_transfer_model_get",
        "model": "account.transfer.model",
        "modules": ["account_transfer", "account_accountant", "account", "base"],
        "source_models": {
            "res.company",
            "account.transfer.model",
            "account.transfer.model.line",
            "account.journal",
            "account.account",
            "account.move",
        },
    },
    "partner.credit_exposure.inspect": {
        "handler": "partner_credit_exposure_inspect",
        "model": "res.partner",
        "modules": ["account", "base"],
        "source_models": {
            "res.company",
            "res.partner",
            "res.currency",
            "account.move",
            "account.move.line",
            "account.account",
            "account.invoice.report",
        },
    },
    "journal.sequence_irregularity.list": {
        "handler": "journal_sequence_irregularity_list",
        "model": "account.move",
        "modules": ["account", "base"],
        "source_models": {"res.company", "account.journal", "account.move"},
    },
    "account.lock_exception.search": {
        "handler": "account_lock_exception_search",
        "model": "account.lock_exception",
        "modules": ["account", "base"],
        "source_models": {"res.company", "res.users", "account.lock_exception"},
    },
    "account.lock_exception.get": {
        "handler": "account_lock_exception_get",
        "model": "account.lock_exception",
        "modules": ["account", "base"],
        "source_models": {"res.company", "res.users", "account.lock_exception"},
    },
    "report.external_value.search": {
        "handler": "report_external_value_search",
        "model": "account.report.external.value",
        "modules": ["account", "base"],
        "source_models": {
            "res.company",
            "account.report.external.value",
            "account.report.expression",
            "account.report.line",
            "account.report",
        },
    },
    "report.external_value.get": {
        "handler": "report_external_value_get",
        "model": "account.report.external.value",
        "modules": ["account", "base"],
        "source_models": {
            "res.company",
            "account.report.external.value",
            "account.report.expression",
            "account.report.line",
            "account.report",
        },
    },
}


def _registry() -> dict[str, object]:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))["capabilities"]


def test_registry_freezes_twelve_pure_accounting_reads() -> None:
    registry = _registry()

    for capability_id, expected in CAPABILITIES.items():
        descriptor = registry[capability_id]
        assert descriptor["access"] == "read"
        assert descriptor["handler_key"] == expected["handler"]
        assert descriptor["source"]["modules"] == expected["modules"]
        assert set(descriptor["source"]["models"]) == expected["source_models"]
        assert descriptor["requirements"]["modules"] == expected["modules"]
        assert descriptor["requirements"]["groups"] == [
            "account.group_account_readonly"
        ]
        assert descriptor["status"] == {
            "value": "unconfigured",
            "reason_code": "runtime_context_required",
            "reason": (
                "The fixed read handler is implemented; availability is evaluated "
                "for each configured database, company, and user at runtime."
            ),
        }
        assert descriptor["tests"]["unit"]["status"] == "implemented"
        assert descriptor["tests"]["unit"]["references"] == [UNIT_REFERENCE]
        assert descriptor["tests"]["integration"]["status"] == "implemented"
        assert descriptor["tests"]["integration"]["references"] == [
            INTEGRATION_REFERENCE
        ]

        source_tokens = " ".join(
            [
                *descriptor["source"]["modules"],
                *descriptor["source"]["models"],
                *descriptor["source"]["locations"],
            ]
        ).lower()
        assert "stock" not in source_tokens
        assert "picking" not in source_tokens
        assert "return_slip" not in source_tokens


def test_cli_routes_every_capability_through_the_core_object_read_path() -> None:
    for capability_id, expected in CAPABILITIES.items():
        handler_key = expected["handler"]
        assert capability_id in CORE_OBJECT_READ_CAPABILITY_IDS
        assert _CAPABILITY_MODELS[capability_id] == expected["model"]

        handler = _HANDLERS[handler_key]
        validator = _REQUEST_VALIDATORS[handler_key]
        assert isinstance(handler, partial)
        assert handler.args == (capability_id,)
        assert isinstance(validator, partial)
        assert validator.args == (capability_id,)


def test_batch_has_exactly_twelve_unique_capability_ids() -> None:
    assert len(CAPABILITIES) == 12
    assert len(set(CAPABILITIES)) == 12


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    [
        ("report.external_value.search", {"limit": 10, "cursor": None}),
        ("report.external_value.get", {"external_value_id": 701}),
    ],
)
def test_external_value_cli_preserves_success_record_ids(
    capability_id: str,
    parameters: dict[str, object],
) -> None:
    item = {
        "id": 701,
        "company_id": 7,
        "name": "Manual adjustment",
        "date": "2026-06-30",
        "value": "125.50",
        "text_value": None,
        "report": {"id": 71, "name": "Balance Sheet"},
        "report_line": {"id": 72, "name": "Cash", "code": None},
        "expression": {"id": 73, "label": "balance"},
        "carryover_origin_line": None,
        "carryover_origin_expression_label": None,
    }

    class Port:
        user_id = 42

        def read(self, **_: object) -> dict[str, object]:
            return {
                "user_id": self.user_id,
                "company_visible": True,
                "module_installed": True,
                "access_allowed": True,
                "cursor_found": True,
                "items": [item],
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
        "parameters": parameters,
    }
    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = cli.main(
        ["read", capability_id, "--request", "-"],
        stdin=io.StringIO(json.dumps(request)),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda _capability_id, _request: Port(),
    )

    assert exit_code == 0
    assert stderr.getvalue() == ""
    assert json.loads(stdout.getvalue())["odoo"]["record_ids"] == [701]
