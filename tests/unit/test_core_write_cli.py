from __future__ import annotations

import hashlib
import io
import json
from typing import Any

import pytest

from odoo_accounting_cli_v4.cli import main

REQUEST_ID = "46365caa-0f86-4a1a-9df5-138ce70bb18f"
CAPABILITY_ID = "customer_invoice.create"
IDEMPOTENCY_KEY = "core-write-cli-test-1"


def _request() -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": {
            "partner_id": 16,
            "journal_id": 9,
            "invoice_date": "2026-08-24",
            "currency_id": 6,
            "lines": [
                {
                    "name": "CLI write fixture",
                    "account_id": 130,
                    "quantity": "1",
                    "price_unit": "25",
                    "tax_ids": [],
                }
            ],
        },
    }


class _Port:
    user_id = 42

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def execute(self, **payload: Any) -> dict[str, Any]:
        self.calls.append(payload)
        return {
            "user_id": self.user_id,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "idempotent_replay": False,
            "result": {
                "model": "account.move",
                "id": 91,
                "name": None,
                "state": "draft",
                "company_id": 7,
                "move_type": "out_invoice",
                "source_id": None,
                "line_ids": [901, 902],
                "partial_reconcile_ids": [],
                "full_reconcile_id": None,
                "reconciled": False,
            },
        }


def _run(
    port: _Port,
    *,
    capability_id: str = CAPABILITY_ID,
    confirmation: str = CAPABILITY_ID,
) -> tuple[int, dict[str, Any], str]:
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
            IDEMPOTENCY_KEY,
            "--confirm",
            confirmation,
        ],
        stdin=io.StringIO(json.dumps(_request())),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda _capability_id, _request_document: port,
    )
    return code, json.loads(stdout.getvalue()), stderr.getvalue()


def test_write_run_dispatches_the_fixed_capability_and_emits_audit_metadata() -> None:
    port = _Port()

    code, document, stderr = _run(port)

    assert code == 0
    assert stderr == ""
    assert port.calls == [
        {
            "capability_id": CAPABILITY_ID,
            "company_id": 7,
            "idempotency_key": IDEMPOTENCY_KEY,
            "confirmation": CAPABILITY_ID,
            "parameters": _request()["parameters"],
        }
    ]
    assert document["success"] is True
    assert document["capability"] == CAPABILITY_ID
    assert document["odoo"] == {
        "database": "v4-dev",
        "company_id": 7,
        "user_id": 42,
        "model": "account.move",
        "record_ids": [91],
    }
    assert document["audit"] == {
        "operation_id": None,
        "idempotency_key": IDEMPOTENCY_KEY,
        "verification": {
            "company_id": 7,
            "state": "draft",
            "reconciled": False,
            "idempotent_replay": False,
        },
    }


def test_write_run_requires_exact_capability_confirmation_before_invoking_odoo() -> (
    None
):
    port = _Port()

    code, document, stderr = _run(port, confirmation="customer_invoice.post")

    assert code == 2
    assert stderr == ""
    assert port.calls == []
    assert document["success"] is False
    assert document["error"]["code"] == "confirmation_required"
    assert document["audit"]["idempotency_key"] == IDEMPOTENCY_KEY


def test_write_run_rejects_a_registered_read_capability() -> None:
    port = _Port()

    code, document, stderr = _run(port, capability_id="invoice.get")

    assert code == 3
    assert stderr == ""
    assert port.calls == []
    assert document["error"]["code"] == "policy_denied"


def test_existing_prepare_shell_remains_unavailable() -> None:
    stdout = io.StringIO()
    stderr = io.StringIO()

    code = main(
        [
            "write",
            "prepare",
            CAPABILITY_ID,
            "--request",
            "-",
            "--idempotency-key",
            IDEMPOTENCY_KEY,
        ],
        stdin=io.StringIO(json.dumps(_request())),
        stdout=stdout,
        stderr=stderr,
    )

    assert code == 4
    assert stderr.getvalue() == ""
    assert json.loads(stdout.getvalue())["error"]["code"] == "command_unavailable"


@pytest.mark.parametrize(
    ("capability_id", "parameters", "key", "model", "record_id", "state"),
    [
        (
            "fiscal_position.archive",
            {"fiscal_position_id": 91},
            "fiscal_position.archive:91",
            "account.fiscal.position",
            91,
            "archived",
        ),
        (
            "journal.group.create",
            {"name": "CLI journal group", "sequence": 20},
            None,
            "account.journal.group",
            92,
            "active",
        ),
    ],
)
def test_fiscal_position_and_journal_group_use_the_shared_write_cli(
    capability_id: str,
    parameters: dict[str, Any],
    key: str | None,
    model: str,
    record_id: int,
    state: str,
) -> None:
    request = _request()
    request["parameters"] = parameters
    if key is None:
        canonical = json.dumps(
            parameters,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        key = f"{capability_id}:7:{hashlib.sha256(canonical).hexdigest()[:32]}"
    result = {
        "model": model,
        "id": record_id,
        "name": "CLI configuration",
        "state": state,
        "company_id": 7,
        "move_type": None,
        "source_id": None,
        "line_ids": [],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }
    stdout = io.StringIO()
    code = main(
        [
            "write",
            "run",
            capability_id,
            "--request",
            "-",
            "--idempotency-key",
            key,
            "--confirm",
            capability_id,
        ],
        stdin=io.StringIO(json.dumps(request)),
        stdout=stdout,
        stderr=io.StringIO(),
        port_factory=lambda _selected, _document: _ExtendedPort(result),
    )

    document = json.loads(stdout.getvalue())
    assert code == 0
    assert document["odoo"]["model"] == model
    assert document["odoo"]["record_ids"] == [record_id]


def _asset_request(capability_id: str) -> dict[str, Any]:
    request = _request()
    request["parameters"] = (
        {
            "name": "CLI asset",
            "acquisition_date": "2026-08-25",
            "original_value": "1200",
            "salvage_value": "0",
            "account_asset_id": 78,
            "account_depreciation_id": 80,
            "account_depreciation_expense_id": 146,
            "journal_id": 11,
            "method": "linear",
            "method_number": 12,
            "method_period": "1",
            "method_progress_factor": "0.3",
            "prorata_computation_type": "none",
        }
        if capability_id == "asset.create"
        else {"asset_id": 91}
    )
    return request


class _AssetPort:
    user_id = 42

    def __init__(self, capability_id: str) -> None:
        self.capability_id = capability_id
        self.calls: list[dict[str, Any]] = []

    def execute(self, **payload: Any) -> dict[str, Any]:
        self.calls.append(payload)
        return {
            "user_id": self.user_id,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "idempotent_replay": False,
            "result": {
                "model": "account.asset",
                "id": 91,
                "name": "CLI asset [ODACV4:fixture]",
                "state": "draft" if self.capability_id == "asset.create" else "open",
                "company_id": 7,
                "move_type": None,
                "source_id": None,
                "line_ids": [] if self.capability_id == "asset.create" else [901],
                "partial_reconcile_ids": [],
                "full_reconcile_id": None,
                "reconciled": False,
            },
        }


def test_asset_writes_use_the_existing_minimal_write_run_path() -> None:
    cases = {
        "asset.create": (
            "asset-create-cli-key",
            "odoo_native_asset_idempotency_field_unavailable",
        ),
        "asset.validate": (
            "asset.validate:91",
            "server_exchange_currency_constraint_broken",
        ),
    }
    for capability_id, (key, reason_code) in cases.items():
        stdout = io.StringIO()
        stderr = io.StringIO()
        port = _AssetPort(capability_id)
        request = _asset_request(capability_id)

        code = main(
            [
                "write",
                "run",
                capability_id,
                "--request",
                "-",
                "--idempotency-key",
                key,
                "--confirm",
                capability_id,
            ],
            stdin=io.StringIO(json.dumps(request)),
            stdout=stdout,
            stderr=stderr,
            port_factory=lambda selected, _document, port=port, capability_id=capability_id: (
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
                "idempotency_key": key,
                "confirmation": capability_id,
                "parameters": request["parameters"],
            }
        ]
        assert document["odoo"]["model"] == "account.asset"
        assert document["odoo"]["record_ids"] == [91]
        assert document["warnings"] == [
            {"code": "capability_degraded", "reason_code": reason_code}
        ]


class _ExtendedPort:
    user_id = 42

    def __init__(self, result: dict[str, Any]) -> None:
        self.result = result

    def execute(self, **_payload: Any) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "idempotent_replay": False,
            "result": self.result,
        }


def _run_extended(
    capability_id: str,
    parameters: dict[str, Any],
    idempotency_key: str,
    result: dict[str, Any],
) -> tuple[int, dict[str, Any]]:
    request = _request()
    request["parameters"] = parameters
    stdout = io.StringIO()
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
        stdin=io.StringIO(json.dumps(request)),
        stdout=stdout,
        stderr=io.StringIO(),
        port_factory=lambda _selected, _document: _ExtendedPort(result),
    )
    return code, json.loads(stdout.getvalue())


def test_deferred_generation_reports_both_generated_move_ids() -> None:
    result = {
        "model": "account.move",
        "id": 92,
        "name": "MISC/2026/0092",
        "state": "posted",
        "company_id": 7,
        "move_type": "entry",
        "source_id": 91,
        "line_ids": [901, 902, 903, 904],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }

    code, document = _run_extended(
        "deferred_expense.generate_entries",
        {"date_to": "2026-08-31"},
        "deferred_expense.generate_entries:2026-08-31",
        result,
    )

    assert code == 0
    assert document["odoo"]["record_ids"] == [91, 92]


def test_period_transfer_surfaces_the_concurrency_degradation() -> None:
    result = {
        "model": "account.move",
        "id": 93,
        "name": "MISC/2026/0093",
        "state": "draft",
        "company_id": 7,
        "move_type": "entry",
        "source_id": 121,
        "line_ids": [905, 906],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }

    code, document = _run_extended(
        "period.transfer.run",
        {"transfer_model_id": 121, "run_date": "2026-08-31"},
        "period.transfer.run:121:2026-08-31",
        result,
    )

    assert code == 0
    assert document["odoo"]["record_ids"] == [93]
    assert document["warnings"] == [
        {
            "code": "capability_degraded",
            "reason_code": "odoo_transfer_marker_not_concurrency_unique",
        }
    ]


_PROCUREMENT_PAYMENT_TERM_ACCRUAL_PARAMETERS: dict[str, dict[str, Any]] = {
    "purchase.order.bill.create": {"order_id": 201},
    "purchase_bill.match": {
        "bill_id": 301,
        "pairs": [
            {"bill_line_id": 401, "purchase_line_id": 501},
            {"bill_line_id": 402, "purchase_line_id": 502},
        ],
    },
    "purchase_bill.lines.unmatch": {
        "bill_id": 301,
        "bill_line_ids": [401, 402],
    },
    "payment_term.create": {
        "name": "30 Days",
        "company_id": 7,
        "early_discount": True,
        "discount_percentage": "2",
        "discount_days": 10,
        "lines": [
            {
                "value": "percent",
                "value_amount": "100",
                "delay_type": "days_after",
                "nb_days": 30,
            }
        ],
    },
    "payment_term.update": {
        "payment_term_id": 302,
        "sequence": 20,
        "note": "Updated term",
    },
    "payment_term.lines.replace": {
        "payment_term_id": 302,
        "lines": [
            {
                "value": "percent",
                "value_amount": "50",
                "delay_type": "days_after",
                "nb_days": 15,
            },
            {
                "value": "percent",
                "value_amount": "50",
                "delay_type": "days_end_of_month_on_the",
                "nb_days": 30,
                "days_next_month": 10,
            },
        ],
    },
    "payment_term.archive": {"payment_term_id": 302},
    "payment_term.restore": {"payment_term_id": 302},
    "period.accrual.generate": {
        "source_model": "purchase.order",
        "order_ids": [201, 202],
        "date": "2026-08-28",
        "reversal_date": "2026-08-29",
        "journal_id": 11,
        "accrual_account_id": 31,
    },
}
_PROCUREMENT_PAYMENT_TERM_ACCRUAL_KEYS = {
    "purchase.order.bill.create": "purchase.order.bill.create:201",
    "purchase_bill.match": ("purchase_bill.match:301:08ac4a81fff0905c7f971aec3a486e18"),
    "purchase_bill.lines.unmatch": (
        "purchase_bill.lines.unmatch:301:abf9113622f38cefc6fdd8e275527028"
    ),
    "payment_term.create": "cli:payment_term.create:0001",
    "payment_term.update": ("payment_term.update:302:ceffa5ec1c6594dcf0dda5ccc9d28069"),
    "payment_term.lines.replace": (
        "payment_term.lines.replace:302:45d45c9e0ec3e6bd033483c01763fdee"
    ),
    "payment_term.archive": "payment_term.archive:302",
    "payment_term.restore": "payment_term.restore:302",
    "period.accrual.generate": "cli:period.accrual.generate:0001",
}
_PROCUREMENT_PAYMENT_TERM_ACCRUAL_MODELS = {
    "purchase.order.bill.create": "account.move",
    "purchase_bill.match": "account.move",
    "purchase_bill.lines.unmatch": "account.move",
    "payment_term.create": "account.payment.term",
    "payment_term.update": "account.payment.term",
    "payment_term.lines.replace": "account.payment.term",
    "payment_term.archive": "account.payment.term",
    "payment_term.restore": "account.payment.term",
    "period.accrual.generate": "account.move",
}


def _procurement_payment_term_accrual_request(
    capability_id: str,
) -> dict[str, Any]:
    request = _request()
    request["parameters"] = _PROCUREMENT_PAYMENT_TERM_ACCRUAL_PARAMETERS[capability_id]
    return request


def _procurement_payment_term_accrual_result(
    capability_id: str,
) -> dict[str, Any]:
    parameters = _PROCUREMENT_PAYMENT_TERM_ACCRUAL_PARAMETERS[capability_id]
    if capability_id.startswith("payment_term."):
        return {
            "model": "account.payment.term",
            "id": (
                902
                if capability_id == "payment_term.create"
                else parameters["payment_term_id"]
            ),
            "name": "30 Days",
            "state": (
                "archived" if capability_id == "payment_term.archive" else "active"
            ),
            "company_id": 7,
            "move_type": None,
            "source_id": None,
            "line_ids": list(range(601, 601 + len(parameters.get("lines", [])))),
            "partial_reconcile_ids": [],
            "full_reconcile_id": None,
            "reconciled": False,
        }
    if capability_id == "period.accrual.generate":
        return {
            "model": "account.move",
            "id": 903,
            "name": "Accrued Expense entry as of 08/28/2026",
            "state": "posted",
            "company_id": 7,
            "move_type": "entry",
            "source_id": 904,
            "line_ids": [701, 702],
            "partial_reconcile_ids": [],
            "full_reconcile_id": None,
            "reconciled": False,
        }
    if capability_id == "purchase.order.bill.create":
        bill_line_ids = [501]
    elif capability_id == "purchase_bill.match":
        bill_line_ids = [pair["bill_line_id"] for pair in parameters["pairs"]]
    else:
        bill_line_ids = list(parameters["bill_line_ids"])
    return {
        "model": "account.move",
        "id": (
            901
            if capability_id == "purchase.order.bill.create"
            else parameters["bill_id"]
        ),
        "name": "BILL/2026/00901",
        "state": "draft",
        "company_id": 7,
        "move_type": "in_invoice",
        "source_id": (
            parameters["order_id"]
            if capability_id == "purchase.order.bill.create"
            else None
        ),
        "line_ids": bill_line_ids,
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }


class _ProcurementPaymentTermAccrualPort:
    user_id = 42

    def __init__(self, capability_id: str) -> None:
        self.capability_id = capability_id
        self.calls: list[dict[str, Any]] = []

    def execute(self, **payload: Any) -> dict[str, Any]:
        self.calls.append(payload)
        return {
            "user_id": self.user_id,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "idempotent_replay": False,
            "result": _procurement_payment_term_accrual_result(self.capability_id),
        }


def _run_procurement_payment_term_accrual(
    capability_id: str,
    *,
    confirmation: str,
) -> tuple[
    int,
    dict[str, Any],
    str,
    _ProcurementPaymentTermAccrualPort,
    list[tuple[str, dict[str, Any]]],
]:
    request = _procurement_payment_term_accrual_request(capability_id)
    port = _ProcurementPaymentTermAccrualPort(capability_id)
    factory_calls: list[tuple[str, dict[str, Any]]] = []

    def port_factory(
        selected: str, request_document: dict[str, Any]
    ) -> _ProcurementPaymentTermAccrualPort:
        factory_calls.append((selected, request_document))
        return port

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
            _PROCUREMENT_PAYMENT_TERM_ACCRUAL_KEYS[capability_id],
            "--confirm",
            confirmation,
        ],
        stdin=io.StringIO(json.dumps(request)),
        stdout=stdout,
        stderr=stderr,
        port_factory=port_factory,
    )
    return (
        code,
        json.loads(stdout.getvalue()),
        stderr.getvalue(),
        port,
        factory_calls,
    )


def test_new_procurement_payment_term_and_accrual_writes_use_public_cli_path() -> None:
    for (
        capability_id,
        expected_model,
    ) in _PROCUREMENT_PAYMENT_TERM_ACCRUAL_MODELS.items():
        request = _procurement_payment_term_accrual_request(capability_id)
        expected_result = _procurement_payment_term_accrual_result(capability_id)
        code, document, stderr, port, factory_calls = (
            _run_procurement_payment_term_accrual(
                capability_id,
                confirmation=capability_id,
            )
        )

        assert code == 0
        assert stderr == ""
        assert factory_calls == [(capability_id, request)]
        assert port.calls == [
            {
                "capability_id": capability_id,
                "company_id": 7,
                "idempotency_key": (
                    _PROCUREMENT_PAYMENT_TERM_ACCRUAL_KEYS[capability_id]
                ),
                "confirmation": capability_id,
                "parameters": request["parameters"],
            }
        ]
        assert document["success"] is True
        assert document["capability"] == capability_id
        assert document["status"] == "verified"
        assert document["data"] == {
            "idempotent_replay": False,
            "result": expected_result,
        }
        assert document["odoo"] == {
            "database": "v4-dev",
            "company_id": 7,
            "user_id": 42,
            "model": expected_model,
            "record_ids": [expected_result["id"]],
        }
        assert (
            document["audit"]["idempotency_key"]
            == (_PROCUREMENT_PAYMENT_TERM_ACCRUAL_KEYS[capability_id])
        )


def test_new_writes_require_exact_confirmation_and_keep_cli_model_mapping() -> None:
    for (
        capability_id,
        expected_model,
    ) in _PROCUREMENT_PAYMENT_TERM_ACCRUAL_MODELS.items():
        code, document, stderr, port, factory_calls = (
            _run_procurement_payment_term_accrual(
                capability_id,
                confirmation=f"{capability_id}.typo",
            )
        )

        assert code == 2
        assert stderr == ""
        assert len(factory_calls) == 1
        assert factory_calls[0][0] == capability_id
        assert port.calls == []
        assert document["success"] is False
        assert document["capability"] == capability_id
        assert document["error"]["code"] == "confirmation_required"
        assert document["odoo"] == {
            "database": "v4-dev",
            "company_id": 7,
            "user_id": 42,
            "model": expected_model,
            "record_ids": [],
        }
