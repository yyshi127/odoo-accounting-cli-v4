from __future__ import annotations

import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest

from odoo_accounting_cli_v4.capabilities.core_writes import (
    CORE_WRITE_CAPABILITY_IDS,
    CoreWriteError,
    _expected_idempotency_key,
    execute_core_write,
    validate_core_write_request,
)
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

REQUEST_ID = "7bc39413-0d69-4092-9319-795d33f3167c"
_DEFAULT_RESULT = object()


def _invoice_parameters() -> dict:
    return {
        "partner_id": 21,
        "journal_id": 4,
        "invoice_date": "2026-08-24",
        "currency_id": 6,
        "lines": [
            {
                "name": "Accounting service",
                "account_id": 31,
                "quantity": "2.00",
                "price_unit": "125.50",
                "tax_ids": [8, 9],
            }
        ],
    }


def _journal_parameters() -> dict:
    return {
        "journal_id": 5,
        "date": "2026-08-24",
        "lines": [
            {
                "name": "Debit",
                "account_id": 31,
                "partner_id": None,
                "debit": "100.00",
                "credit": "0",
            },
            {
                "name": "Credit",
                "account_id": 32,
                "partner_id": 21,
                "debit": "0",
                "credit": "100.00",
            },
        ],
    }


def _sale_order_line() -> dict:
    return {
        "product_id": 51,
        "name": "Consulting service",
        "quantity": "3",
        "uom_id": 1,
        "price_unit": "10.5",
        "discount": "0",
        "tax_ids": [8, 9],
    }


def _purchase_order_line() -> dict:
    return {
        **_sale_order_line(),
        "product_id": 52,
        "name": "Purchased service",
        "quantity": "5",
        "price_unit": "8",
        "date_planned": "2026-08-30 02:03:04",
    }


PARAMETERS = {
    "customer_invoice.create": _invoice_parameters(),
    "vendor_bill.create": _invoice_parameters(),
    "invoice.update": {"move_id": 114, "changes": {"reference": "PO-114"}},
    "invoice.lines.replace": {
        "move_id": 115,
        "lines": [
            {
                "name": "Replacement invoice line",
                "product_id": None,
                "account_id": 31,
                "quantity": "2",
                "price_unit": "125.50",
                "discount": "5",
                "tax_ids": [8, 9],
            }
        ],
    },
    "invoice.cancel": {"move_id": 116},
    "invoice.reset_to_draft": {"move_id": 117},
    "invoice.post": {"move_id": 101},
    "journal_entry.create": _journal_parameters(),
    "journal_entry.update": {
        "move_id": 118,
        "changes": {"reference": "Adjustment 118"},
    },
    "journal_entry.lines.replace": {
        "move_id": 119,
        "lines": _journal_parameters()["lines"],
    },
    "journal_entry.cancel": {"move_id": 120},
    "journal_entry.reset_to_draft": {"move_id": 121},
    "journal_entry.post": {"move_id": 102},
    "journal_entry.reverse": {
        "move_id": 103,
        "date": "2026-08-24",
        "reason": "Correction",
    },
    "receivable.payment.register": {
        "move_id": 104,
        "journal_id": 7,
        "payment_date": "2026-08-24",
    },
    "payable.payment.register": {
        "move_id": 105,
        "journal_id": 7,
        "payment_date": "2026-08-24",
    },
    "reconciliation.apply": {"line_ids": [202, 201]},
    "payment.cancel": {"payment_id": 106},
    "payment.create": {
        "payment_type": "inbound",
        "partner_type": "customer",
        "partner_id": 21,
        "amount": "125.50",
        "currency_id": 6,
        "journal_id": 7,
        "payment_method_line_id": 9,
        "date": "2026-08-24",
        "payment_reference": None,
    },
    "payment.update_draft": {
        "payment_id": 122,
        "changes": {"amount": "130.00", "payment_reference": "Receipt 122"},
    },
    "payment.reset_to_draft": {"payment_id": 123},
    "customer_credit_note.create": {
        "move_id": 107,
        "date": "2026-08-24",
        "reason": "Customer credit",
    },
    "vendor_refund.create": {
        "move_id": 108,
        "date": "2026-08-24",
        "reason": "Vendor refund",
    },
    "payment.post": {"payment_id": 109},
    "reconciliation.undo": {"line_ids": [204, 203]},
    "bank.transaction.record": {
        "journal_id": 7,
        "date": "2026-08-24",
        "amount": "-125.50",
        "payment_ref": "Bank fee",
        "partner_id": None,
    },
    "bank.transaction.update": {
        "transaction_id": 124,
        "changes": {"partner_id": 21, "payment_ref": "Transfer 124"},
    },
    "bank.transaction.match": {
        "transaction_id": 125,
        "candidate_line_ids": [301, 302],
    },
    "bank.transaction.unmatch": {"transaction_id": 126},
    "reconciliation.write_off": {
        "transaction_id": 127,
        "write_off_account_id": 31,
        "label": "Bank fee",
        "expected_residual_amount": "-2.50",
    },
    "analytic.account.create": {
        "name": "Project Alpha",
        "plan_id": 11,
        "code": None,
        "partner_id": None,
    },
    "analytic.account.update": {
        "analytic_account_id": 128,
        "changes": {"code": "ALPHA", "partner_id": None, "active": False},
    },
    "budget.create": {
        "name": "FY 2027",
        "date_from": "2027-01-01",
        "date_to": "2027-12-31",
        "budget_type": "both",
    },
    "budget.update_draft": {
        "budget_id": 129,
        "changes": {"name": "FY 2027 revised", "budget_type": "expense"},
    },
    "budget.lines.replace": {
        "budget_id": 130,
        "lines": [
            {"budget_amount": "1000.00", "analytic_account_ids": [21, 22]},
            {"budget_amount": "-250.00", "analytic_account_ids": [23]},
        ],
    },
    "budget.confirm": {"budget_id": 131},
    "budget.reset_to_draft": {"budget_id": 132},
    "budget.cancel": {"budget_id": 133},
    "budget.mark_done": {"budget_id": 134},
    "partner.create": {"name": "Acme", "company_type": "company"},
    "partner.update": {
        "partner_id": 135,
        "changes": {"reference": None, "email": "billing@example.com"},
    },
    "partner.archive": {"partner_id": 136},
    "partner.restore": {"partner_id": 137},
    "partner.accounting.update": {
        "partner_id": 138,
        "changes": {
            "property_account_receivable_id": 301,
            "property_payment_term_id": None,
        },
    },
    "partner.bank_account.create": {
        "partner_id": 135,
        "account_number": "JP1234567890",
    },
    "partner.bank_account.update": {
        "partner_bank_id": 139,
        "changes": {"account_holder_name": "Acme Treasury", "bank_id": None},
    },
    "partner.bank_account.archive": {"partner_bank_id": 140},
    "partner.bank_account.restore": {"partner_bank_id": 141},
    "account.account.create": {
        "code": "1100",
        "name": "Trade Receivables",
        "account_type": "asset_receivable",
    },
    "account.account.update": {
        "account_id": 142,
        "changes": {"name": "Customer Receivables", "reconcile": True},
    },
    "account.account.archive": {"account_id": 143},
    "account.account.restore": {"account_id": 144},
    "journal.create": {"name": "Bank", "code": "bnk", "type": "bank"},
    "journal.update": {
        "journal_id": 145,
        "changes": {"code": "bn2", "currency_id": None},
    },
    "journal.archive": {"journal_id": 146},
    "journal.restore": {"journal_id": 147},
    "tax.create": {
        "name": "Sales Tax 15%",
        "type_tax_use": "sale",
        "amount_type": "percent",
        "amount": 15.0,
    },
    "tax.update": {
        "tax_id": 148,
        "changes": {"amount": 12.5, "invoice_label": None},
    },
    "tax.archive": {"tax_id": 149},
    "tax.restore": {"tax_id": 150},
    "asset.create": {
        "name": "Office laptop",
        "acquisition_date": "2026-08-24",
        "original_value": "12000.00",
        "salvage_value": "0",
        "account_asset_id": 78,
        "account_depreciation_id": 80,
        "account_depreciation_expense_id": 146,
        "journal_id": 11,
        "method": "linear",
        "method_number": 5,
        "method_period": "12",
        "method_progress_factor": "0.30",
        "prorata_computation_type": "constant_periods",
    },
    "asset.validate": {"asset_id": 110},
    "asset.cancel": {"asset_id": 111},
    "asset.dispose": {
        "asset_id": 112,
        "date": "2026-08-31",
        "note": "Disposed after useful life",
    },
    "asset.pause": {
        "asset_id": 113,
        "date": "2026-08-31",
        "note": None,
    },
    "deferred_expense.generate_entries": {"date_to": "2026-08-31"},
    "deferred_revenue.generate_entries": {"date_to": "2026-08-31"},
    "multicurrency.revaluation.generate_entries": {
        "date": "2026-08-31",
        "reversal_date": "2026-09-01",
        "journal_id": 11,
        "expense_provision_account_id": 31,
        "income_provision_account_id": 32,
    },
    "reconciliation.automatic.run": {"line_ids": [203, 201, 202]},
    "period.transfer.run": {
        "transfer_model_id": 121,
        "run_date": "2026-08-31",
    },
    "localization.china.period_transfer.run": {"run_date": "2026-08-31"},
    "sale.order.create": {
        "partner_id": 31,
        "pricelist_id": 41,
        "date_order": "2026-08-28 01:02:03",
        "client_order_ref": "CLIENT-31",
        "validity_date": "2026-09-30",
        "commitment_date": "2026-09-01 08:00:00",
        "payment_term_id": None,
        "lines": [_sale_order_line()],
    },
    "sale.order.update_draft": {
        "order_id": 101,
        "changes": {
            "client_order_ref": "CLIENT-UPDATED",
            "validity_date": None,
            "commitment_date": "2026-09-02 08:00:00",
            "payment_term_id": 12,
        },
    },
    "sale.order.lines.replace": {"order_id": 101, "lines": [_sale_order_line()]},
    "sale.order.confirm": {"order_id": 101},
    "sale.order.cancel": {"order_id": 101},
    "sale.order.reset_to_draft": {"order_id": 101},
    "purchase.order.create": {
        "partner_id": 32,
        "currency_id": 6,
        "picking_type_id": 2,
        "date_order": "2026-08-28 01:02:03",
        "partner_ref": "VENDOR-32",
        "payment_term_id": 13,
        "incoterm_id": None,
        "lines": [_purchase_order_line()],
    },
    "purchase.order.update_draft": {
        "order_id": 201,
        "changes": {
            "partner_ref": "VENDOR-UPDATED",
            "date_order": "2026-08-29 01:02:03",
            "payment_term_id": None,
            "incoterm_id": 3,
        },
    },
    "purchase.order.lines.replace": {
        "order_id": 201,
        "lines": [_purchase_order_line()],
    },
    "purchase.order.confirm": {"order_id": 201},
    "purchase.order.cancel": {"order_id": 201},
    "purchase.order.reset_to_draft": {"order_id": 201},
    "purchase.order.bill.create": {"order_id": 201},
    "purchase_bill.match": {
        "bill_id": 301,
        "pairs": [
            {"bill_line_id": 402, "purchase_line_id": 502},
            {"bill_line_id": 401, "purchase_line_id": 501},
        ],
    },
    "purchase_bill.lines.unmatch": {"bill_id": 301, "bill_line_ids": [402, 401]},
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
        "order_ids": [202, 201],
        "date": "2026-08-28",
        "reversal_date": "2026-08-29",
        "journal_id": 11,
        "accrual_account_id": 31,
    },
    "fiscal_position.create": {
        "name": "European Union",
        "state_ids": [3, 1],
    },
    "fiscal_position.update": {
        "fiscal_position_id": 303,
        "changes": {"sequence": 20, "note": "Updated position"},
    },
    "fiscal_position.account_mappings.replace": {
        "fiscal_position_id": 303,
        "mappings": [
            {"source_account_id": 402, "destination_account_id": 502},
            {"source_account_id": 401, "destination_account_id": 501},
        ],
    },
    "fiscal_position.archive": {"fiscal_position_id": 303},
    "fiscal_position.restore": {"fiscal_position_id": 303},
    "journal.group.create": {
        "name": "Liquidity",
        "excluded_journal_ids": [12, 11],
    },
    "journal.group.update": {
        "journal_group_id": 304,
        "changes": {"sequence": 10, "excluded_journal_ids": [14, 13]},
    },
}


def _request(capability_id: str) -> dict:
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "zh_CN",
            "timezone": "Asia/Shanghai",
        },
        "parameters": deepcopy(PARAMETERS[capability_id]),
    }


def _key(capability_id: str) -> str:
    if capability_id in {
        "payment_term.create",
        "period.accrual.generate",
    }:
        return f"smoke:{capability_id}:0001"
    if capability_id == "purchase.order.bill.create":
        return f"purchase.order.bill.create:{PARAMETERS[capability_id]['order_id']}"
    if capability_id in {
        "purchase_bill.match",
        "purchase_bill.lines.unmatch",
        "payment_term.update",
        "payment_term.lines.replace",
        "payment_term.archive",
        "payment_term.restore",
        "fiscal_position.create",
        "fiscal_position.update",
        "fiscal_position.account_mappings.replace",
        "fiscal_position.archive",
        "fiscal_position.restore",
        "journal.group.create",
        "journal.group.update",
    }:
        _, context, parameters = validate_core_write_request(
            capability_id, _request(capability_id)
        )
        key = _expected_idempotency_key(
            capability_id, parameters, context["company_id"]
        )
        assert key is not None
        return key
    if capability_id.startswith(("account.account.", "journal.", "tax.")):
        _, context, parameters = validate_core_write_request(
            capability_id, _request(capability_id)
        )
        key = _expected_idempotency_key(
            capability_id, parameters, context["company_id"]
        )
        assert key is not None
        return key
    if capability_id in {"sale.order.create", "purchase.order.create"}:
        return "order-create-safe-key-001"
    if capability_id in {
        "customer_invoice.create",
        "vendor_bill.create",
        "journal_entry.create",
        "bank.transaction.record",
        "asset.create",
        "payment.create",
        "analytic.account.create",
        "budget.create",
    }:
        return f"smoke:{capability_id}:0001"
    parameters = PARAMETERS[capability_id]
    if capability_id.startswith(("sale.order.", "purchase.order.")):
        if capability_id.endswith((".update_draft", ".lines.replace")):
            target = (
                parameters["changes"]
                if capability_id.endswith(".update_draft")
                else parameters["lines"]
            )
            digest = sha256(
                json.dumps(
                    target,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()[:32]
            return f"{capability_id}:{parameters['order_id']}:{digest}"
        return f"{capability_id}:{parameters['order_id']}"
    if capability_id == "partner.create":
        normalized = dict(parameters)
        for field in (
            "vat",
            "reference",
            "email",
            "phone",
            "mobile",
            "street",
            "street2",
            "city",
            "zip",
            "state_id",
            "country_id",
            "language",
        ):
            normalized.setdefault(field, None)
        digest = sha256(
            json.dumps(
                normalized,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()[:32]
        return f"partner.create:{digest}"
    if capability_id in {"partner.update", "partner.accounting.update"}:
        digest = sha256(
            json.dumps(
                parameters["changes"],
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()[:32]
        return f"{capability_id}:{parameters['partner_id']}:{digest}"
    if capability_id in {"partner.archive", "partner.restore"}:
        return f"{capability_id}:{parameters['partner_id']}"
    if capability_id == "partner.bank_account.create":
        digest = sha256(parameters["account_number"].encode("utf-8")).hexdigest()[:32]
        return f"{capability_id}:{parameters['partner_id']}:{digest}"
    if capability_id == "partner.bank_account.update":
        digest = sha256(
            json.dumps(
                parameters["changes"],
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()[:32]
        return f"{capability_id}:{parameters['partner_bank_id']}:{digest}"
    if capability_id in {
        "partner.bank_account.archive",
        "partner.bank_account.restore",
    }:
        return f"{capability_id}:{parameters['partner_bank_id']}"
    if capability_id in {"reconciliation.apply", "reconciliation.undo"}:
        first, second = sorted(parameters["line_ids"])
        return f"{capability_id}:{first}:{second}"
    if capability_id == "asset.validate":
        return f"asset.validate:{parameters['asset_id']}"
    if capability_id in {"asset.cancel", "asset.dispose"}:
        return f"{capability_id}:{parameters['asset_id']}"
    if capability_id == "asset.pause":
        return f"asset.pause:{parameters['asset_id']}:{parameters['date']}"
    if capability_id.startswith("deferred_"):
        return f"{capability_id}:{parameters['date_to']}"
    if capability_id == "multicurrency.revaluation.generate_entries":
        return f"{capability_id}:{parameters['date']}"
    if capability_id == "reconciliation.automatic.run":
        canonical_ids = ",".join(str(item) for item in sorted(parameters["line_ids"]))
        digest = sha256(canonical_ids.encode("ascii")).hexdigest()[:32]
        return f"reconciliation.automatic.run:{digest}"
    if capability_id == "period.transfer.run":
        return (
            f"period.transfer.run:{parameters['transfer_model_id']}:"
            f"{parameters['run_date']}"
        )
    if capability_id == "localization.china.period_transfer.run":
        return f"localization.china.period_transfer.run:7:{parameters['run_date']}"
    if capability_id == "payment.update_draft":
        target = parameters["changes"]
        digest = sha256(
            json.dumps(
                target,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()[:32]
        return f"payment.update_draft:{parameters['payment_id']}:{digest}"
    if capability_id == "payment.reset_to_draft":
        return f"payment.reset_to_draft:{parameters['payment_id']}"
    if capability_id == "bank.transaction.unmatch":
        return f"bank.transaction.unmatch:{parameters['transaction_id']}"
    if capability_id in {
        "bank.transaction.update",
        "bank.transaction.match",
        "reconciliation.write_off",
    }:
        target = (
            parameters["changes"]
            if capability_id == "bank.transaction.update"
            else parameters["candidate_line_ids"]
            if capability_id == "bank.transaction.match"
            else {
                "write_off_account_id": parameters["write_off_account_id"],
                "expected_residual_amount": parameters["expected_residual_amount"],
                "label": parameters["label"],
            }
        )
        digest = sha256(
            json.dumps(
                target,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()[:32]
        return f"{capability_id}:{parameters['transaction_id']}:{digest}"
    if capability_id in {
        "analytic.account.update",
        "budget.update_draft",
        "budget.lines.replace",
    }:
        target = (
            parameters["lines"]
            if capability_id == "budget.lines.replace"
            else parameters["changes"]
        )
        digest = sha256(
            json.dumps(
                target,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()[:32]
        primary = parameters.get("analytic_account_id", parameters.get("budget_id"))
        return f"{capability_id}:{primary}:{digest}"
    if capability_id in {
        "budget.confirm",
        "budget.reset_to_draft",
        "budget.cancel",
        "budget.mark_done",
    }:
        return f"{capability_id}:{parameters['budget_id']}"
    target = parameters.get("changes", parameters.get("lines"))
    if capability_id.endswith((".update", ".lines.replace")) and target is not None:
        canonical = json.dumps(
            target,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = sha256(canonical).hexdigest()[:32]
        return f"{capability_id}:{parameters['move_id']}:{digest}"
    primary = parameters.get("move_id", parameters.get("payment_id"))
    return f"{capability_id}:{primary}"


def _result(capability_id: str, **changes) -> dict:
    parameters = PARAMETERS[capability_id]
    if capability_id.startswith("fiscal_position."):
        result = {
            "model": "account.fiscal.position",
            "id": (
                905
                if capability_id == "fiscal_position.create"
                else parameters["fiscal_position_id"]
            ),
            "name": "European Union",
            "state": (
                "archived" if capability_id == "fiscal_position.archive" else "active"
            ),
            "company_id": 7,
            "move_type": None,
            "source_id": None,
            "line_ids": list(range(801, 801 + len(parameters.get("mappings", [])))),
            "partial_reconcile_ids": [],
            "full_reconcile_id": None,
            "reconciled": False,
        }
        result.update(changes)
        return result
    if capability_id.startswith("journal.group."):
        result = {
            "model": "account.journal.group",
            "id": 906
            if capability_id == "journal.group.create"
            else parameters["journal_group_id"],
            "name": "Liquidity",
            "state": "active",
            "company_id": 7,
            "move_type": None,
            "source_id": None,
            "line_ids": [],
            "partial_reconcile_ids": [],
            "full_reconcile_id": None,
            "reconciled": False,
        }
        result.update(changes)
        return result
    if capability_id in {
        "purchase.order.bill.create",
        "purchase_bill.match",
        "purchase_bill.lines.unmatch",
    }:
        result = {
            "model": "account.move",
            "id": 901
            if capability_id == "purchase.order.bill.create"
            else parameters["bill_id"],
            "name": "BILL/2026/00901",
            "state": "draft",
            "company_id": 7,
            "move_type": "in_invoice",
            "source_id": 201,
            "line_ids": (
                [501]
                if capability_id == "purchase.order.bill.create"
                else sorted(pair["bill_line_id"] for pair in parameters["pairs"])
                if capability_id == "purchase_bill.match"
                else sorted(parameters["bill_line_ids"])
            ),
            "partial_reconcile_ids": [],
            "full_reconcile_id": None,
            "reconciled": False,
        }
        if capability_id != "purchase.order.bill.create":
            result["source_id"] = None
        result.update(changes)
        return result
    if capability_id.startswith("payment_term."):
        result = {
            "model": "account.payment.term",
            "id": 902
            if capability_id == "payment_term.create"
            else parameters["payment_term_id"],
            "name": "30 Days",
            "state": "archived"
            if capability_id == "payment_term.archive"
            else "active",
            "company_id": 7,
            "move_type": None,
            "source_id": None,
            "line_ids": list(range(601, 601 + len(parameters.get("lines", [])))),
            "partial_reconcile_ids": [],
            "full_reconcile_id": None,
            "reconciled": False,
        }
        result.update(changes)
        return result
    if capability_id == "period.accrual.generate":
        result = {
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
        result.update(changes)
        return result
    if capability_id.startswith(("sale.order.", "purchase.order.")):
        sale = capability_id.startswith("sale.order.")
        result = {
            "model": "sale.order" if sale else "purchase.order",
            "id": 901 if capability_id.endswith(".create") else parameters["order_id"],
            "name": "S00901" if sale else "P00901",
            "state": (
                "sale"
                if capability_id == "sale.order.confirm"
                else "purchase"
                if capability_id == "purchase.order.confirm"
                else "cancel"
                if capability_id.endswith(".cancel")
                else "draft"
            ),
            "company_id": 7,
            "move_type": None,
            "source_id": 31 if sale else 32,
            "line_ids": list(range(501, 501 + len(parameters.get("lines", [None])))),
            "partial_reconcile_ids": [],
            "full_reconcile_id": None,
            "reconciled": False,
        }
        result.update(changes)
        return result
    is_payment = capability_id.startswith(("receivable.", "payable.", "payment."))
    is_reconcile = capability_id in {
        "reconciliation.apply",
        "reconciliation.undo",
        "reconciliation.automatic.run",
    }
    is_bank_transaction = (
        capability_id.startswith("bank.transaction.")
        or capability_id == "reconciliation.write_off"
    )
    is_asset = capability_id in {
        "asset.create",
        "asset.validate",
        "asset.cancel",
        "asset.dispose",
        "asset.pause",
    }
    is_partner_bank = capability_id.startswith("partner.bank_account.")
    is_partner = capability_id.startswith("partner.") and not is_partner_bank
    is_analytic = capability_id.startswith("analytic.account.")
    is_budget = capability_id.startswith("budget.")
    is_accounting_configuration = capability_id.startswith(
        ("account.account.", "journal.", "tax.")
    )
    result_id = parameters.get(
        "move_id",
        parameters.get(
            "payment_id",
            parameters.get("transaction_id", parameters.get("asset_id", 501)),
        ),
    )
    result = {
        "model": (
            "account.move.line"
            if is_reconcile
            else (
                "account.payment"
                if is_payment
                else (
                    "account.bank.statement.line"
                    if is_bank_transaction
                    else ("account.asset" if is_asset else "account.move")
                )
            )
        ),
        "id": None if is_reconcile else result_id,
        "name": (
            None
            if is_reconcile
            else ("BNK1/2026/0001" if is_payment else "MISC/2026/0001")
        ),
        "state": (
            "reconciled"
            if capability_id in {"reconciliation.apply", "reconciliation.automatic.run"}
            else (
                "unreconciled"
                if capability_id == "reconciliation.undo"
                else ("in_process" if is_payment else "posted")
            )
        ),
        "company_id": 7,
        "move_type": None if (is_payment or is_reconcile or is_asset) else "entry",
        "source_id": None,
        "line_ids": (
            (
                sorted(parameters["line_ids"])
                + ([204] if capability_id == "reconciliation.automatic.run" else [])
            )
            if is_reconcile
            else [901, 902]
        ),
        "partial_reconcile_ids": (
            [301]
            if capability_id in {"reconciliation.apply", "reconciliation.automatic.run"}
            else []
        ),
        "full_reconcile_id": (
            401
            if capability_id in {"reconciliation.apply", "reconciliation.automatic.run"}
            else None
        ),
        "reconciled": capability_id
        in {"reconciliation.apply", "reconciliation.automatic.run"},
    }
    if capability_id == "customer_invoice.create":
        result.update(id=501, state="draft", move_type="out_invoice")
    elif capability_id == "vendor_bill.create":
        result.update(id=502, state="draft", move_type="in_invoice")
    elif capability_id == "invoice.post":
        result["move_type"] = "out_invoice"
    elif capability_id.startswith("invoice."):
        result.update(
            state="cancel" if capability_id == "invoice.cancel" else "draft",
            move_type="out_invoice",
        )
    elif capability_id == "journal_entry.reverse":
        result.update(id=503, source_id=103)
    elif capability_id == "customer_credit_note.create":
        result.update(id=504, state="draft", move_type="out_refund", source_id=107)
    elif capability_id == "vendor_refund.create":
        result.update(id=505, state="draft", move_type="in_refund", source_id=108)
    elif capability_id == "journal_entry.create":
        result["state"] = "draft"
    elif capability_id in {
        "journal_entry.update",
        "journal_entry.lines.replace",
        "journal_entry.cancel",
        "journal_entry.reset_to_draft",
    }:
        result["state"] = (
            "cancel" if capability_id == "journal_entry.cancel" else "draft"
        )
    elif capability_id.startswith(("receivable.", "payable.")):
        result.update(id=601, source_id=parameters["move_id"])
    elif capability_id == "payment.cancel":
        result["state"] = "canceled"
    elif capability_id in {
        "payment.create",
        "payment.update_draft",
        "payment.reset_to_draft",
    }:
        result.update(
            id=602 if capability_id == "payment.create" else result_id,
            state="draft",
        )
    elif is_partner:
        result.update(
            model="res.partner",
            id=(811 if capability_id == "partner.create" else parameters["partner_id"]),
            name="Acme",
            state=("archived" if capability_id == "partner.archive" else "active"),
            move_type=None,
            source_id=None,
            line_ids=[],
        )
    elif is_partner_bank:
        result.update(
            model="res.partner.bank",
            id=(
                812
                if capability_id == "partner.bank_account.create"
                else parameters["partner_bank_id"]
            ),
            name="JP1234567890",
            state=(
                "archived"
                if capability_id == "partner.bank_account.archive"
                else "active"
            ),
            move_type=None,
            source_id=parameters.get("partner_id", 135),
            line_ids=[],
        )
    elif is_accounting_configuration:
        primary_field = (
            "account_id"
            if capability_id.startswith("account.account.")
            else "journal_id"
            if capability_id.startswith("journal.")
            else "tax_id"
        )
        result.update(
            model=(
                "account.account"
                if capability_id.startswith("account.account.")
                else "account.journal"
                if capability_id.startswith("journal.")
                else "account.tax"
            ),
            id=(
                {
                    "account.account.create": 813,
                    "journal.create": 814,
                    "tax.create": 815,
                }[capability_id]
                if capability_id.endswith(".create")
                else parameters[primary_field]
            ),
            name="Configured record",
            state="archived" if capability_id.endswith(".archive") else "active",
            move_type=None,
            source_id=None,
            line_ids=[],
        )
    elif is_analytic:
        result.update(
            model="account.analytic.account",
            id=(
                801
                if capability_id == "analytic.account.create"
                else parameters["analytic_account_id"]
            ),
            name="Project Alpha [ODACV4:fixture]",
            state=(
                "active" if capability_id == "analytic.account.create" else "archived"
            ),
            move_type=None,
            source_id=parameters.get("plan_id", 11),
            line_ids=[],
        )
    elif is_budget:
        result.update(
            model="budget.analytic",
            id=(802 if capability_id == "budget.create" else parameters["budget_id"]),
            name="FY 2027 [ODACV4:fixture]",
            state={
                "budget.create": "draft",
                "budget.update_draft": "draft",
                "budget.lines.replace": "draft",
                "budget.confirm": "confirmed",
                "budget.reset_to_draft": "draft",
                "budget.cancel": "canceled",
                "budget.mark_done": "done",
            }[capability_id],
            move_type=None,
            source_id=None,
            line_ids=(
                []
                if capability_id == "budget.create"
                else [1001, 1002]
                if capability_id == "budget.lines.replace"
                else [1001]
            ),
        )
    elif is_bank_transaction:
        result.update(
            id=701 if capability_id == "bank.transaction.record" else result_id,
            name="BNK1/2026/0002",
            source_id=702,
            reconciled=capability_id
            in {"bank.transaction.match", "reconciliation.write_off"},
        )
    elif capability_id == "asset.create":
        result.update(
            id=801,
            name="Office laptop [ODACV4:fixture]",
            state="draft",
            line_ids=[],
        )
    elif capability_id == "asset.validate":
        result.update(
            id=parameters["asset_id"],
            name="Office laptop [ODACV4:fixture]",
            state="open",
            line_ids=[910],
        )
    elif capability_id in {"asset.cancel", "asset.dispose", "asset.pause"}:
        result.update(
            id=parameters["asset_id"],
            name="Office laptop [ODACV4:fixture]",
            state={
                "asset.cancel": "cancelled",
                "asset.dispose": "close",
                "asset.pause": "paused",
            }[capability_id],
            line_ids=[],
        )
    elif capability_id in {
        "deferred_expense.generate_entries",
        "deferred_revenue.generate_entries",
        "multicurrency.revaluation.generate_entries",
    }:
        result.update(id=701, source_id=700, line_ids=[901, 902, 903, 904])
    elif capability_id in {
        "period.transfer.run",
        "localization.china.period_transfer.run",
    }:
        result.update(
            id=801,
            state="draft",
            source_id=parameters.get("transfer_model_id", 122),
            line_ids=[921, 922],
        )
    result.update(changes)
    return result


class FakePort:
    def __init__(
        self,
        capability_id: str,
        *,
        result: dict | None | object = _DEFAULT_RESULT,
        **gate,
    ) -> None:
        self.capability_id = capability_id
        self._user_id = gate.pop("user_id", 42)
        self.result = deepcopy(
            _result(capability_id) if result is _DEFAULT_RESULT else result
        )
        self.company_visible = gate.pop("company_visible", True)
        self.module_installed = gate.pop("module_installed", True)
        self.access_allowed = gate.pop("access_allowed", True)
        self.idempotent_replay = gate.pop("idempotent_replay", False)
        assert not gate
        self.calls: list[dict] = []

    @property
    def user_id(self) -> int:
        return self._user_id

    def execute(self, **payload) -> dict:
        self.calls.append(deepcopy(payload))
        return {
            "user_id": self._user_id,
            "company_visible": self.company_visible,
            "module_installed": self.module_installed,
            "access_allowed": self.access_allowed,
            "idempotent_replay": self.idempotent_replay,
            "result": deepcopy(self.result),
        }


@pytest.mark.parametrize("capability_id", sorted(CORE_WRITE_CAPABILITY_IDS))
def test_each_core_write_validates_and_calls_one_fixed_port_operation(
    capability_id: str,
) -> None:
    request = _request(capability_id)
    port = FakePort(capability_id)

    data = execute_core_write(
        port,
        capability_id,
        request,
        _key(capability_id),
        capability_id,
    )

    expected_parameters = deepcopy(PARAMETERS[capability_id])
    if capability_id in {
        "reconciliation.apply",
        "reconciliation.undo",
        "reconciliation.automatic.run",
    }:
        expected_parameters["line_ids"] = sorted(expected_parameters["line_ids"])
    elif capability_id == "purchase_bill.match":
        expected_parameters["pairs"] = sorted(
            expected_parameters["pairs"], key=lambda item: item["bill_line_id"]
        )
    elif capability_id == "purchase_bill.lines.unmatch":
        expected_parameters["bill_line_ids"] = sorted(
            expected_parameters["bill_line_ids"]
        )
    elif capability_id == "period.accrual.generate":
        expected_parameters["order_ids"] = sorted(expected_parameters["order_ids"])
    elif capability_id.startswith(("fiscal_position.", "journal.group.")):
        expected_parameters = validate_core_write_request(capability_id, request)[2]
    elif capability_id == "partner.create":
        for field in (
            "vat",
            "reference",
            "email",
            "phone",
            "mobile",
            "street",
            "street2",
            "city",
            "zip",
            "state_id",
            "country_id",
            "language",
        ):
            expected_parameters.setdefault(field, None)
    elif capability_id == "partner.bank_account.create":
        expected_parameters.update(
            account_holder_name=None,
            bank_id=None,
            currency_id=None,
        )
    elif capability_id.startswith(("account.account.", "journal.", "tax.")):
        expected_parameters = validate_core_write_request(capability_id, request)[2]
    assert data == {"idempotent_replay": False, "result": _result(capability_id)}
    assert port.calls == [
        {
            "capability_id": capability_id,
            "company_id": 7,
            "idempotency_key": _key(capability_id),
            "confirmation": capability_id,
            "parameters": expected_parameters,
        }
    ]


def test_payment_term_rejects_fixed_only_lines_at_contract_validation() -> None:
    request = _request("payment_term.create")
    request["parameters"]["early_discount"] = False
    request["parameters"]["discount_percentage"] = "0"
    request["parameters"]["discount_days"] = 0
    request["parameters"]["lines"] = [
        {
            "value": "fixed",
            "value_amount": "100",
            "delay_type": "days_after",
            "nb_days": 30,
        }
    ]

    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request("payment_term.create", request)

    assert caught.value.code == "invalid_request"


def test_purchase_bill_create_requires_order_scoped_idempotency_key() -> None:
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            FakePort("purchase.order.bill.create"),
            "purchase.order.bill.create",
            _request("purchase.order.bill.create"),
            "caller-safe-but-nondeterministic-key",
            "purchase.order.bill.create",
        )

    assert caught.value.code == "invalid_idempotency_key"


@pytest.mark.parametrize(
    ("capability_id", "change"),
    (
        ("purchase.order.bill.create", {"source_id": 999}),
        ("purchase.order.bill.create", {"line_ids": []}),
        ("purchase_bill.match", {"source_id": 201}),
        ("purchase_bill.match", {"line_ids": [401]}),
        ("purchase_bill.lines.unmatch", {"source_id": 201}),
        ("purchase_bill.lines.unmatch", {"line_ids": [402, 401]}),
    ),
)
def test_purchase_bill_result_is_bound_to_source_and_requested_lines(
    capability_id: str, change: dict
) -> None:
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            FakePort(capability_id, result=_result(capability_id, **change)),
            capability_id,
            _request(capability_id),
            _key(capability_id),
            capability_id,
        )

    assert caught.value.code == "failed_validation"


@pytest.mark.parametrize(
    "capability_id",
    [
        "customer_invoice.create",
        "vendor_bill.create",
        "journal_entry.create",
        "customer_credit_note.create",
        "vendor_refund.create",
    ],
)
def test_create_replay_accepts_the_records_current_posted_state(
    capability_id: str,
) -> None:
    request = _request(capability_id)
    posted_result = _result(capability_id, state="posted")

    replay = execute_core_write(
        FakePort(
            capability_id,
            result=posted_result,
            idempotent_replay=True,
        ),
        capability_id,
        request,
        _key(capability_id),
        capability_id,
    )

    assert replay == {"idempotent_replay": True, "result": posted_result}
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            FakePort(capability_id, result=posted_result),
            capability_id,
            request,
            _key(capability_id),
            capability_id,
        )
    assert caught.value.code == "failed_validation"


def test_asset_create_replay_accepts_a_later_open_state() -> None:
    result = _result("asset.create", state="open", line_ids=[910])
    replay = execute_core_write(
        FakePort("asset.create", result=result, idempotent_replay=True),
        "asset.create",
        _request("asset.create"),
        _key("asset.create"),
        "asset.create",
    )
    assert replay == {"idempotent_replay": True, "result": result}


def test_journal_entry_must_be_nonzero_and_balanced() -> None:
    request = _request("journal_entry.create")
    request["parameters"]["lines"][1]["credit"] = "99.99"
    with pytest.raises(CoreWriteError, match="balanced") as caught:
        validate_core_write_request("journal_entry.create", request)
    assert caught.value.code == "invalid_request"
    assert caught.value.exit_code == 2


@pytest.mark.parametrize("value", [1, 1.0, True, "01", "1e2", "NaN", " 1", "1\n"])
def test_decimal_fields_reject_json_numbers_and_noncanonical_text(value) -> None:
    request = _request("customer_invoice.create")
    request["parameters"]["lines"][0]["quantity"] = value
    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request("customer_invoice.create", request)
    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize(
    ("field", "value"),
    [("quantity", "0"), ("quantity", "-1"), ("price_unit", "-0.01")],
)
def test_invoice_amount_signs_match_the_fixed_runtime_contract(
    field: str, value: str
) -> None:
    request = _request("customer_invoice.create")
    request["parameters"]["lines"][0][field] = value
    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request("customer_invoice.create", request)
    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize(
    "value",
    [0, 1, True, "0", "-0", "0.00", "01", "1e2", "NaN", " 1", "1\n"],
)
def test_bank_transaction_amount_is_a_canonical_nonzero_signed_decimal(
    value,
) -> None:
    request = _request("bank.transaction.record")
    request["parameters"]["amount"] = value
    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request("bank.transaction.record", request)
    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize("partner_id", [0, -1, True, "21"])
def test_bank_transaction_partner_is_null_or_a_positive_id(partner_id) -> None:
    request = _request("bank.transaction.record")
    request["parameters"]["partner_id"] = partner_id
    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request("bank.transaction.record", request)
    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("original_value", "0"),
        ("original_value", 120),
        ("salvage_value", "12000.01"),
        ("method_number", 0),
        ("method_number", 1201),
        ("method_period", "6"),
        ("method_progress_factor", "0"),
        ("method_progress_factor", "1.01"),
        ("prorata_computation_type", "monthly"),
    ],
)
def test_asset_create_rejects_values_outside_the_closed_contract(
    field: str, value
) -> None:
    request = _request("asset.create")
    request["parameters"][field] = value
    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request("asset.create", request)
    assert caught.value.code == "invalid_request"


def test_asset_create_reserves_the_visible_marker_suffix() -> None:
    request = _request("asset.create")
    request["parameters"]["name"] = "Laptop [ODACV4:user-supplied]"
    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request("asset.create", request)
    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize(
    ("capability_id", "change"),
    [
        ("customer_credit_note.create", {"move_type": "out_invoice"}),
        ("customer_credit_note.create", {"source_id": 999}),
        ("vendor_refund.create", {"move_type": "out_refund"}),
        ("vendor_refund.create", {"state": "posted"}),
        ("payment.post", {"state": "draft"}),
        ("payment.post", {"id": 999}),
        ("payment.post", {"source_id": 109}),
        ("reconciliation.undo", {"state": "reconciled"}),
        ("reconciliation.undo", {"line_ids": [203, 205]}),
        ("reconciliation.undo", {"partial_reconcile_ids": [301]}),
        ("bank.transaction.record", {"state": "draft"}),
        ("bank.transaction.record", {"model": "account.move"}),
        ("bank.transaction.record", {"move_type": None}),
        ("bank.transaction.record", {"source_id": None}),
        ("bank.transaction.record", {"line_ids": []}),
        ("asset.create", {"model": "account.move"}),
        ("asset.create", {"state": "open"}),
        ("asset.create", {"line_ids": [901]}),
        ("asset.validate", {"id": 999}),
        ("asset.validate", {"state": "draft"}),
        ("asset.validate", {"move_type": "entry"}),
    ],
)
def test_second_batch_results_fail_closed_on_business_drift(
    capability_id: str, change: dict
) -> None:
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            FakePort(capability_id, result=_result(capability_id, **change)),
            capability_id,
            _request(capability_id),
            _key(capability_id),
            capability_id,
        )
    assert caught.value.code == "failed_validation"


@pytest.mark.parametrize(
    ("capability_id", "key"),
    [
        ("invoice.post", "invoice.post:999"),
        ("journal_entry.reverse", "journal_entry.reverse:103:again"),
        ("reconciliation.apply", "reconciliation.apply:202:201"),
        ("payment.cancel", "payment.cancel:000106"),
        ("payment.post", "payment.post:000109"),
        ("reconciliation.undo", "reconciliation.undo:204:203"),
        ("asset.validate", "asset.validate:999"),
        ("asset.cancel", "asset.cancel:999"),
        ("asset.dispose", "asset.dispose:999"),
        ("asset.pause", "asset.pause:113:2026-09-01"),
        (
            "deferred_expense.generate_entries",
            "deferred_expense.generate_entries:2026-09-30",
        ),
        (
            "deferred_revenue.generate_entries",
            "deferred_revenue.generate_entries:2026-09-30",
        ),
        (
            "multicurrency.revaluation.generate_entries",
            "multicurrency.revaluation.generate_entries:2026-09-30",
        ),
        ("reconciliation.automatic.run", "reconciliation.automatic.run:wrong"),
        ("period.transfer.run", "period.transfer.run:999:2026-08-31"),
        (
            "localization.china.period_transfer.run",
            "localization.china.period_transfer.run:8:2026-08-31",
        ),
        ("analytic.account.update", "analytic.account.update:128:wrong"),
        ("budget.update_draft", "budget.update_draft:129:wrong"),
        ("budget.lines.replace", "budget.lines.replace:130:wrong"),
        ("budget.confirm", "budget.confirm:999"),
        ("budget.reset_to_draft", "budget.reset_to_draft:999"),
        ("budget.cancel", "budget.cancel:999"),
        ("budget.mark_done", "budget.mark_done:999"),
    ],
)
def test_noncreate_idempotency_keys_are_deterministic(
    capability_id: str, key: str
) -> None:
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            FakePort(capability_id),
            capability_id,
            _request(capability_id),
            key,
            capability_id,
        )
    assert caught.value.code == "invalid_idempotency_key"
    assert caught.value.exit_code == 2


def test_confirmation_must_equal_the_capability_id() -> None:
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            FakePort("invoice.post"),
            "invoice.post",
            _request("invoice.post"),
            _key("invoice.post"),
            "yes",
        )
    assert caught.value.code == "confirmation_required"


@pytest.mark.parametrize(
    ("port", "code"),
    [
        (
            FakePort(
                "invoice.post",
                result=None,
                module_installed=False,
                access_allowed=False,
            ),
            "uninstalled",
        ),
        (
            FakePort(
                "invoice.post", result=None, company_visible=False, access_allowed=False
            ),
            "company_unavailable",
        ),
        (FakePort("invoice.post", result=None, access_allowed=False), "unauthorized"),
        (FakePort("invoice.post", result=None), "record_not_found"),
    ],
)
def test_runtime_availability_and_missing_record_failures_are_typed(
    port: FakePort, code: str
) -> None:
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            port,
            "invoice.post",
            _request("invoice.post"),
            _key("invoice.post"),
            "invoice.post",
        )
    assert caught.value.code == code


@pytest.mark.parametrize(
    "change",
    [
        {"company_id": 8},
        {"id": 999},
        {"model": "res.partner"},
        {"line_ids": [902, 901]},
        {"partial_reconcile_ids": [301, 301]},
        {"reconciled": 1},
    ],
)
def test_malformed_or_mismatched_results_fail_closed(change: dict) -> None:
    result = _result("invoice.post", **change)
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            FakePort("invoice.post", result=result),
            "invoice.post",
            _request("invoice.post"),
            _key("invoice.post"),
            "invoice.post",
        )
    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8


def _success_response(capability_id: str) -> dict:
    result = _result(capability_id)
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "success": True,
        "capability": capability_id,
        "status": "verified",
        "data": {"idempotent_replay": False, "result": result},
        "warnings": [],
        "error": None,
        "odoo": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_id": 42,
            "model": result["model"],
            "record_ids": (
                result["line_ids"]
                if capability_id
                in {
                    "reconciliation.apply",
                    "reconciliation.undo",
                    "reconciliation.automatic.run",
                }
                else [result["id"]]
            ),
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": _key(capability_id),
            "verification": {"result": "passed"},
        },
    }


@pytest.mark.parametrize("capability_id", sorted(CORE_WRITE_CAPABILITY_IDS))
def test_dedicated_schemas_accept_each_closed_request_and_response(
    capability_id: str,
) -> None:
    schema_dir = Path(__file__).parents[2] / "schemas" / "v1"
    assert (schema_dir / f"{capability_id}.request.schema.json").is_file()
    assert (schema_dir / f"{capability_id}.response.schema.json").is_file()
    registry = load_registry()
    registry.validate_instance(
        f"schemas/v1/{capability_id}.request.schema.json", _request(capability_id)
    )
    registry.validate_instance(
        f"schemas/v1/{capability_id}.response.schema.json",
        _success_response(capability_id),
    )


@pytest.mark.parametrize(
    "capability_id",
    [
        "customer_credit_note.create",
        "vendor_refund.create",
        "payment.post",
        "reconciliation.undo",
        "bank.transaction.record",
    ],
)
def test_second_batch_requests_reject_additional_parameters(
    capability_id: str,
) -> None:
    request = _request(capability_id)
    request["parameters"]["extra"] = True
    with pytest.raises(CoreWriteError):
        validate_core_write_request(capability_id, request)
    with pytest.raises(InstanceValidationError):
        load_registry().validate_instance(
            f"schemas/v1/{capability_id}.request.schema.json", request
        )


def test_schema_rejects_a_json_number_for_an_accounting_decimal() -> None:
    request = _request("journal_entry.create")
    request["parameters"]["lines"][0]["debit"] = 100
    with pytest.raises(InstanceValidationError):
        load_registry().validate_instance(
            "schemas/v1/journal_entry.create.request.schema.json", request
        )


@pytest.mark.parametrize(
    "capability_id", ["customer_invoice.create", "vendor_bill.create"]
)
def test_invoice_create_accepts_the_frozen_optional_header_and_line_fields(
    capability_id: str,
) -> None:
    request = _request(capability_id)
    request["parameters"].update(
        invoice_date_due=None,
        payment_term_id=12,
        reference=None,
        payment_reference="PAY-2026-001",
    )
    request["parameters"]["lines"][0].update(
        product_id=None,
        discount="12.50",
        analytic_distribution={"2,4": "60.25", "7": "39.75"},
    )

    normalized = validate_core_write_request(capability_id, request)[2]

    assert normalized == request["parameters"]
    load_registry().validate_instance(
        f"schemas/v1/{capability_id}.request.schema.json", request
    )


@pytest.mark.parametrize(
    "capability_id", ["customer_invoice.create", "vendor_bill.create"]
)
def test_invoice_due_date_and_payment_term_are_mutually_exclusive_when_nonnull(
    capability_id: str,
) -> None:
    request = _request(capability_id)
    request["parameters"].update(
        invoice_date_due="2026-09-30",
        payment_term_id=12,
    )

    with pytest.raises(CoreWriteError):
        validate_core_write_request(capability_id, request)
    with pytest.raises(InstanceValidationError):
        load_registry().validate_instance(
            f"schemas/v1/{capability_id}.request.schema.json", request
        )


@pytest.mark.parametrize(
    "distribution",
    [
        {},
        {"2,1": "100"},
        {"1,2": "50", "2,3": "50"},
        {"01": "100"},
        {"1": "0"},
        {"1": "100.0000"},
        {"1": "1.23456"},
        {"1": 50},
    ],
)
def test_analytic_distribution_rejects_noncanonical_or_ambiguous_values(
    distribution,
) -> None:
    request = _request("invoice.lines.replace")
    request["parameters"]["lines"][0]["analytic_distribution"] = distribution

    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request("invoice.lines.replace", request)

    assert caught.value.code == "invalid_request"


def test_analytic_distribution_accepts_null_and_does_not_default_when_omitted() -> None:
    request = _request("invoice.lines.replace")
    original = deepcopy(request["parameters"])
    assert validate_core_write_request("invoice.lines.replace", request)[2] == original

    request["parameters"]["lines"][0]["analytic_distribution"] = None
    normalized = validate_core_write_request("invoice.lines.replace", request)[2]
    assert normalized["lines"][0]["analytic_distribution"] is None


@pytest.mark.parametrize(
    "capability_id", ["customer_credit_note.create", "vendor_refund.create"]
)
def test_refund_accepts_replacement_lines_and_multiple_operation_keys(
    capability_id: str,
) -> None:
    request = _request(capability_id)
    request["parameters"]["lines"] = deepcopy(
        PARAMETERS["invoice.lines.replace"]["lines"]
    )
    request["parameters"]["lines"][0]["analytic_distribution"] = {"11": "100"}
    _, context, normalized = validate_core_write_request(capability_id, request)

    assert normalized == request["parameters"]
    assert (
        _expected_idempotency_key(capability_id, normalized, context["company_id"])
        is None
    )
    for operation_key in ("refund-operation:0001", "refund-operation:0002"):
        execute_core_write(
            FakePort(capability_id),
            capability_id,
            request,
            operation_key,
            capability_id,
        )

    load_registry().validate_instance(
        f"schemas/v1/{capability_id}.request.schema.json", request
    )


def test_journal_currency_and_analytic_fields_share_one_contract() -> None:
    registry = load_registry()
    for capability_id in (
        "journal_entry.create",
        "journal_entry.lines.replace",
    ):
        request = _request(capability_id)
        request["parameters"]["lines"][0].update(
            currency_id=6,
            amount_currency="100.00",
            analytic_distribution={"11": "100"},
        )
        request["parameters"]["lines"][1].update(
            currency_id=6,
            amount_currency="-100.00",
            analytic_distribution=None,
        )
        if capability_id == "journal_entry.create":
            request["parameters"]["reference"] = None

        normalized = validate_core_write_request(capability_id, request)[2]

        assert normalized == request["parameters"]
        registry.validate_instance(
            f"schemas/v1/{capability_id}.request.schema.json", request
        )


@pytest.mark.parametrize(
    "currency_fields",
    [
        {"currency_id": 6},
        {"amount_currency": "100"},
        {"currency_id": None, "amount_currency": "100"},
        {"currency_id": 6, "amount_currency": None},
        {"currency_id": 6, "amount_currency": "0"},
        {"currency_id": 6, "amount_currency": "-100"},
    ],
)
def test_journal_currency_pair_and_sign_fail_closed(currency_fields: dict) -> None:
    request = _request("journal_entry.create")
    request["parameters"]["lines"][0].update(currency_fields)

    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request("journal_entry.create", request)

    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize(
    "capability_id",
    ["receivable.payment.register", "payable.payment.register"],
)
def test_partial_payment_uses_a_caller_chosen_operation_key(
    capability_id: str,
) -> None:
    request = _request(capability_id)
    request["parameters"]["amount"] = "50.25"
    _, context, normalized = validate_core_write_request(capability_id, request)

    assert (
        _expected_idempotency_key(capability_id, normalized, context["company_id"])
        is None
    )
    for operation_key in ("partial-payment:0001", "partial-payment:0002"):
        execute_core_write(
            FakePort(capability_id),
            capability_id,
            request,
            operation_key,
            capability_id,
        )
    load_registry().validate_instance(
        f"schemas/v1/{capability_id}.request.schema.json", request
    )


@pytest.mark.parametrize("amount", [0, "0", "01", "50.0", "-1", "1e2"])
def test_partial_payment_amount_must_be_a_positive_canonical_decimal(
    amount,
) -> None:
    request = _request("receivable.payment.register")
    request["parameters"]["amount"] = amount

    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request("receivable.payment.register", request)

    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize(
    "capability_id",
    ["receivable.payment.register", "payable.payment.register"],
)
def test_full_payment_keeps_the_legacy_exact_idempotency_key(
    capability_id: str,
) -> None:
    _, context, normalized = validate_core_write_request(
        capability_id, _request(capability_id)
    )
    assert (
        _expected_idempotency_key(capability_id, normalized, context["company_id"])
        == f"{capability_id}:{normalized['move_id']}"
    )


def test_reconciliation_accepts_legacy_and_invoice_modes() -> None:
    registry = load_registry()

    legacy_apply = _request("reconciliation.apply")
    assert validate_core_write_request("reconciliation.apply", legacy_apply)[2] == {
        "line_ids": [201, 202]
    }

    invoice_apply = _request("reconciliation.apply")
    invoice_apply["parameters"] = {"invoice_id": 104, "outstanding_line_id": 202}
    apply_result = _result(
        "reconciliation.apply", source_id=104, line_ids=[201, 202, 203]
    )
    apply_key = "reconciliation.apply:104:202"
    _, apply_context, apply_parameters = validate_core_write_request(
        "reconciliation.apply", invoice_apply
    )
    assert (
        _expected_idempotency_key(
            "reconciliation.apply",
            apply_parameters,
            apply_context["company_id"],
        )
        == apply_key
    )
    assert (
        execute_core_write(
            FakePort("reconciliation.apply", result=apply_result),
            "reconciliation.apply",
            invoice_apply,
            apply_key,
            "reconciliation.apply",
        )["result"]
        == apply_result
    )
    registry.validate_instance(
        "schemas/v1/reconciliation.apply.request.schema.json", invoice_apply
    )

    invoice_undo = _request("reconciliation.undo")
    invoice_undo["parameters"] = {
        "invoice_id": 104,
        "partial_reconcile_id": 301,
        "invoice_line_id": 202,
        "counterpart_line_id": 201,
    }
    undo_result = _result("reconciliation.undo", source_id=104, line_ids=[201, 202])
    undo_key = "reconciliation.undo:104:301:201:202"
    _, undo_context, undo_parameters = validate_core_write_request(
        "reconciliation.undo", invoice_undo
    )
    assert (
        _expected_idempotency_key(
            "reconciliation.undo",
            undo_parameters,
            undo_context["company_id"],
        )
        == undo_key
    )
    assert (
        execute_core_write(
            FakePort("reconciliation.undo", result=undo_result),
            "reconciliation.undo",
            invoice_undo,
            undo_key,
            "reconciliation.undo",
        )["result"]
        == undo_result
    )
    for remaining_result in (
        _result(
            "reconciliation.undo",
            source_id=104,
            line_ids=[202, 203],
            state="partial",
            partial_reconcile_ids=[302],
        ),
        _result(
            "reconciliation.undo",
            source_id=104,
            line_ids=[202, 204],
            state="partial",
            partial_reconcile_ids=[303],
            full_reconcile_id=401,
        ),
        _result(
            "reconciliation.undo",
            source_id=104,
            line_ids=[201, 202],
            state="reconciled",
            partial_reconcile_ids=[302],
            full_reconcile_id=401,
            reconciled=True,
        ),
    ):
        assert (
            execute_core_write(
                FakePort("reconciliation.undo", result=remaining_result),
                "reconciliation.undo",
                invoice_undo,
                undo_key,
                "reconciliation.undo",
            )["result"]
            == remaining_result
        )
    registry.validate_instance(
        "schemas/v1/reconciliation.undo.request.schema.json", invoice_undo
    )


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    [
        (
            "reconciliation.apply",
            {"line_ids": [201, 202], "invoice_id": 104, "outstanding_line_id": 202},
        ),
        (
            "reconciliation.undo",
            {
                "invoice_id": 104,
                "partial_reconcile_id": 301,
                "invoice_line_id": 201,
            },
        ),
        (
            "reconciliation.undo",
            {
                "invoice_id": 104,
                "partial_reconcile_id": 301,
                "invoice_line_id": 201,
                "counterpart_line_id": 201,
            },
        ),
    ],
)
def test_reconciliation_modes_are_closed_and_unambiguous(
    capability_id: str, parameters: dict
) -> None:
    request = _request(capability_id)
    request["parameters"] = parameters

    with pytest.raises(CoreWriteError):
        validate_core_write_request(capability_id, request)
    if "invoice_line_id" in parameters and parameters[
        "invoice_line_id"
    ] == parameters.get("counterpart_line_id"):
        load_registry().validate_instance(
            f"schemas/v1/{capability_id}.request.schema.json", request
        )
    else:
        with pytest.raises(InstanceValidationError):
            load_registry().validate_instance(
                f"schemas/v1/{capability_id}.request.schema.json", request
            )


@pytest.mark.parametrize(
    ("capability_id", "parameters", "result_changes", "key"),
    [
        (
            "reconciliation.apply",
            {"invoice_id": 104, "outstanding_line_id": 202},
            {"source_id": 104, "line_ids": [201, 203]},
            "reconciliation.apply:104:202",
        ),
        (
            "reconciliation.undo",
            {
                "invoice_id": 104,
                "partial_reconcile_id": 301,
                "invoice_line_id": 201,
                "counterpart_line_id": 202,
            },
            {"source_id": 104, "line_ids": [202, 203]},
            "reconciliation.undo:104:301:201:202",
        ),
        (
            "reconciliation.undo",
            {
                "invoice_id": 104,
                "partial_reconcile_id": 301,
                "invoice_line_id": 201,
                "counterpart_line_id": 202,
            },
            {
                "source_id": 104,
                "line_ids": [201, 202],
                "state": "partial",
                "partial_reconcile_ids": [301, 302],
            },
            "reconciliation.undo:104:301:201:202",
        ),
        (
            "reconciliation.undo",
            {
                "invoice_id": 104,
                "partial_reconcile_id": 301,
                "invoice_line_id": 201,
                "counterpart_line_id": 202,
            },
            {
                "source_id": 104,
                "line_ids": [201],
                "state": "partial",
                "partial_reconcile_ids": [302],
            },
            "reconciliation.undo:104:301:201:202",
        ),
    ],
)
def test_invoice_mode_reconciliation_results_fail_closed(
    capability_id: str,
    parameters: dict,
    result_changes: dict,
    key: str,
) -> None:
    request = _request(capability_id)
    request["parameters"] = parameters

    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            FakePort(capability_id, result=_result(capability_id, **result_changes)),
            capability_id,
            request,
            key,
            capability_id,
        )

    assert caught.value.code == "failed_validation"


@pytest.mark.parametrize(
    ("capability_id", "path"),
    [
        ("customer_invoice.create", "parameters"),
        ("invoice.lines.replace", "line"),
        ("journal_entry.create", "line"),
        ("receivable.payment.register", "parameters"),
    ],
)
def test_new_contract_surfaces_remain_closed(capability_id: str, path: str) -> None:
    request = _request(capability_id)
    target = (
        request["parameters"]["lines"][0] if path == "line" else request["parameters"]
    )
    target["unsupported"] = True

    with pytest.raises(CoreWriteError):
        validate_core_write_request(capability_id, request)
    with pytest.raises(InstanceValidationError):
        load_registry().validate_instance(
            f"schemas/v1/{capability_id}.request.schema.json", request
        )
