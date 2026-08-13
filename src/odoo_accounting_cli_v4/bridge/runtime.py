"""Odoo-side runtime for the narrow V4 read bridge."""

from __future__ import annotations

import argparse
import json
import sys
from contextlib import contextmanager
from datetime import date as date_type
from decimal import Decimal
from pathlib import Path
from typing import Any, TextIO

from odoo_accounting_cli_v4.config import ConfigError, load_runtime_config


_MAX_REQUEST_CHARS = 1024 * 1024
_ACCOUNT_FIELDS = (
    "id",
    "code",
    "name",
    "account_type",
    "active",
    "reconcile",
    "company_ids",
)
_MASTER_DATA_ACTIONS: dict[str, dict[str, Any]] = {
    "account.journal.read_page": {
        "model": "account.journal",
        "fields": (
            "id",
            "code",
            "name",
            "type",
            "active",
            "sequence",
            "currency_id",
            "company_id",
        ),
        "cursor_fields": ("sequence", "type", "code", "id"),
        "cursor_operators": (">", ">", ">", ">"),
        "cursor_types": (int, str, str, int),
        "order": "sequence,type,code,id",
        "scope": "company",
    },
    "account.tax.read_page": {
        "model": "account.tax",
        "fields": (
            "id",
            "name",
            "type_tax_use",
            "amount_type",
            "amount",
            "active",
            "sequence",
            "price_include",
            "include_base_amount",
            "is_base_affected",
            "tax_group_id",
            "company_id",
        ),
        "cursor_fields": ("sequence", "id"),
        "cursor_operators": (">", ">"),
        "cursor_types": (int, int),
        "order": "sequence,id",
        "scope": "company",
    },
    "account.payment.term.read_page": {
        "model": "account.payment.term",
        "fields": (
            "id",
            "name",
            "active",
            "company_id",
            "sequence",
            "display_on_invoice",
            "early_discount",
            "discount_percentage",
            "discount_days",
            "early_pay_discount_computation",
            "line_ids",
        ),
        "cursor_fields": ("sequence", "id"),
        "cursor_operators": (">", ">"),
        "cursor_types": (int, int),
        "order": "sequence,id",
        "scope": "shared_company",
    },
    "res.currency.read_page": {
        "model": "res.currency",
        "fields": (
            "id",
            "name",
            "full_name",
            "symbol",
            "active",
            "position",
            "rounding",
            "decimal_places",
            "is_current_company_currency",
        ),
        "cursor_fields": ("active", "name", "id"),
        "cursor_operators": ("<", ">", ">"),
        "cursor_types": (bool, str, int),
        "order": "active desc,name,id",
        "scope": "global",
    },
}
_FINANCIAL_REPORT_ACTIONS = {
    "account.report.trial_balance.read_page": {
        "xml_id": "account_reports.trial_balance_report",
        "key": "trial_balance",
        "mode": "range",
    },
    "account.report.balance_sheet.read_page": {
        "xml_id": "account_reports.balance_sheet",
        "key": "balance_sheet",
        "mode": "single",
    },
    "account.report.profit_and_loss.read_page": {
        "xml_id": "account_reports.profit_and_loss",
        "key": "profit_and_loss",
        "mode": "range",
    },
    "account.report.cash_flow.read_page": {
        "xml_id": "account_reports.cash_flow_report",
        "key": "cash_flow",
        "mode": "range",
    },
    "account.report.tax.read_page": {
        "xml_id": "account.generic_tax_report",
        "key": "tax",
        "mode": "range",
    },
}
_INVOICE_ACTIONS = {
    "account.move.invoice.search_page",
    "account.move.invoice.get",
    "account.move.invoice.payment_status.inspect",
}
_INVOICE_DOCUMENT_TYPES = (
    "out_invoice",
    "out_refund",
    "in_invoice",
    "in_refund",
)
_INVOICE_STATES = ("draft", "posted", "cancel")
_INVOICE_PAYMENT_STATES = (
    "not_paid",
    "in_payment",
    "paid",
    "partial",
    "reversed",
    "blocked",
    "invoicing_legacy",
)
_INVOICE_HEADER_FIELDS = (
    "id",
    "name",
    "move_type",
    "state",
    "date",
    "invoice_date",
    "invoice_date_due",
    "ref",
    "payment_reference",
    "invoice_origin",
    "journal_id",
    "company_id",
    "currency_id",
    "partner_id",
    "amount_untaxed",
    "amount_tax",
    "amount_total",
    "amount_residual",
    "payment_state",
)
_INVOICE_STATUS_MOVE_FIELDS = (
    "id",
    "name",
    "move_type",
    "state",
    "payment_state",
    "company_id",
    "currency_id",
    "company_currency_id",
    "amount_total",
    "amount_residual",
    "matched_payment_ids",
)
_INVOICE_LINE_TYPES = (
    "product",
    "line_section",
    "line_subsection",
    "line_note",
)
_INVOICE_LINE_FIELDS = (
    "id",
    "move_id",
    "sequence",
    "display_type",
    "name",
    "product_id",
    "account_id",
    "quantity",
    "price_unit",
    "discount",
    "price_subtotal",
    "price_total",
    "tax_ids",
)
_INVOICE_TERM_LINE_FIELDS = (
    "id",
    "move_id",
    "account_id",
    "date_maturity",
    "balance",
    "amount_currency",
    "amount_residual",
    "amount_residual_currency",
    "currency_id",
    "reconciled",
    "matching_number",
)
_INVOICE_PARTIAL_FIELDS = (
    "id",
    "max_date",
    "amount",
    "debit_amount_currency",
    "credit_amount_currency",
    "debit_move_id",
    "credit_move_id",
    "exchange_move_id",
)
_INVOICE_COUNTERPART_LINE_FIELDS = ("id", "move_id")
_INVOICE_COUNTERPART_MOVE_FIELDS = (
    "id",
    "name",
    "move_type",
    "state",
    "date",
    "origin_payment_id",
)
_INVOICE_PAYMENT_FIELDS = (
    "id",
    "name",
    "state",
    "date",
    "payment_type",
    "partner_type",
    "amount",
    "currency_id",
    "journal_id",
    "payment_method_line_id",
    "move_id",
    "is_reconciled",
    "is_matched",
)
_INVOICE_SEARCH_MODELS = (
    "res.company",
    "account.move",
    "account.move.line",
    "account.journal",
    "res.currency",
    "res.partner",
)
_INVOICE_GET_MODELS = (
    *_INVOICE_SEARCH_MODELS,
    "account.account",
    "account.tax",
    "product.product",
)
_INVOICE_STATUS_MODELS = (
    *_INVOICE_SEARCH_MODELS,
    "account.account",
    "account.partial.reconcile",
    "account.payment",
    "account.payment.method",
    "account.payment.method.line",
)
_PAYMENT_ACTIONS = {
    "account.payment.search_page",
    "account.payment.get",
}
_PAYMENT_STATES = ("draft", "in_process", "paid", "canceled", "rejected")
_PAYMENT_TYPES = ("inbound", "outbound")
_PAYMENT_PARTNER_TYPES = ("customer", "supplier")
_PAYMENT_DOCUMENT_TYPES = (
    "out_invoice",
    "out_refund",
    "in_invoice",
    "in_refund",
    "out_receipt",
    "in_receipt",
)
_PAYMENT_SALE_DOCUMENT_TYPES = {"out_invoice", "out_refund", "out_receipt"}
_PAYMENT_PURCHASE_DOCUMENT_TYPES = {"in_invoice", "in_refund", "in_receipt"}
_PAYMENT_DOCUMENT_STATES = {"draft", "posted", "cancel"}
_PAYMENT_DOCUMENT_PAYMENT_STATES = {
    "not_paid",
    "in_payment",
    "paid",
    "partial",
    "reversed",
    "blocked",
    "invoicing_legacy",
}
_PAYMENT_FIELDS = (
    "id",
    "name",
    "date",
    "state",
    "payment_type",
    "partner_type",
    "amount",
    "amount_signed",
    "amount_company_currency_signed",
    "currency_id",
    "company_currency_id",
    "company_id",
    "partner_id",
    "journal_id",
    "memo",
    "payment_reference",
    "payment_method_line_id",
    "move_id",
    "is_reconciled",
    "is_matched",
)
_PAYMENT_JOURNAL_FIELDS = ("id", "code", "name", "company_id")
_PAYMENT_CURRENCY_FIELDS = ("id", "name")
_PAYMENT_PARTNER_FIELDS = ("id", "name", "company_id")
_PAYMENT_METHOD_LINE_FIELDS = (
    "id",
    "name",
    "journal_id",
    "payment_method_id",
)
_PAYMENT_METHOD_FIELDS = ("id", "code", "name", "payment_type")
_PAYMENT_MOVE_FIELDS = (
    "id",
    "name",
    "state",
    "date",
    "move_type",
    "payment_state",
    "company_id",
)
_PAYMENT_MOVE_LINE_FIELDS = ("id", "move_id", "account_id", "company_id")
_PAYMENT_ACCOUNT_FIELDS = (
    "id",
    "account_type",
    "reconcile",
)
_PAYMENT_PARTIAL_FIELDS = (
    "id",
    "debit_move_id",
    "credit_move_id",
    "exchange_move_id",
    "company_id",
)
_PAYMENT_SEARCH_MODELS = (
    "res.company",
    "account.payment",
    "account.move",
    "account.journal",
    "res.currency",
    "res.partner",
    "account.payment.method.line",
    "account.payment.method",
)
_PAYMENT_GET_MODELS = (
    *_PAYMENT_SEARCH_MODELS,
    "account.move.line",
    "account.account",
    "account.partial.reconcile",
)
_OPEN_ITEM_ACTION_SIDES = {
    "account.move.line.receivable.open_items.search_page": (
        "receivable",
        "asset_receivable",
    ),
    "account.move.line.payable.open_items.search_page": (
        "payable",
        "liability_payable",
    ),
}
_OPEN_ITEM_FIELDS = (
    "id",
    "date",
    "date_maturity",
    "name",
    "ref",
    "move_id",
    "journal_id",
    "company_id",
    "partner_id",
    "account_id",
    "currency_id",
    "company_currency_id",
    "debit",
    "credit",
    "balance",
    "amount_currency",
    "amount_residual",
    "amount_residual_currency",
    "reconciled",
    "matching_number",
    "parent_state",
    "account_type",
)
_OPEN_ITEM_MODELS = (
    "res.company",
    "account.move.line",
    "account.move",
    "account.account",
    "account.journal",
    "res.partner",
    "res.currency",
)
_ACTIONS = {
    "account.account.read_page",
    "res.company.accounting_context.read_page",
    *_MASTER_DATA_ACTIONS,
    "account.move.journal_entry.search_page",
    "account.move.journal_entry.get",
    *_INVOICE_ACTIONS,
    *_PAYMENT_ACTIONS,
    *_OPEN_ITEM_ACTION_SIDES,
    "res.partner.accounting.search_page",
    *_FINANCIAL_REPORT_ACTIONS,
    "res.users.accounting_access.inspect",
    "res.company.accounting_configuration.inspect",
    "accounting.environment.diagnostic.inspect",
}

_ACCOUNTING_ACCESS_GROUPS = (
    "base.group_user",
    "account.group_account_readonly",
    "account.group_account_invoice",
    "account.group_account_user",
    "account.group_account_manager",
)
_ACCOUNTING_ACCESS_MODELS = (
    "account.account",
    "account.journal",
    "account.move",
    "account.move.line",
    "account.report",
    "account.tax",
)
_DIAGNOSTIC_MODULES = ("account", "account_reports", "base")
_DIAGNOSTIC_MODELS = (
    "account.account",
    "account.journal",
    "account.move",
    "account.move.line",
    "account.report",
    "account.tax",
    "ir.module.module",
    "res.company",
    "res.users",
)


class RuntimeFailure(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        exit_code: int,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code
        self.retryable = retryable
        self.details = details or {}


@contextmanager
def _read_only_cursor(registry: Any):
    cursor = registry.cursor()
    try:
        cursor.execute("SET TRANSACTION READ ONLY")
        yield cursor
    finally:
        try:
            cursor.rollback()
        finally:
            cursor.close()


def _decode_request(stdin: TextIO) -> dict[str, Any]:
    raw = stdin.read(_MAX_REQUEST_CHARS + 1)
    if not raw or len(raw) > _MAX_REQUEST_CHARS:
        raise RuntimeFailure(
            "bridge_protocol_error", "The bridge request is invalid.", exit_code=7
        )

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise RuntimeFailure(
                    "bridge_protocol_error",
                    "The bridge request is invalid.",
                    exit_code=7,
                )
            result[key] = value
        return result

    try:
        value = json.loads(raw, object_pairs_hook=reject_duplicates)
    except (json.JSONDecodeError, RuntimeFailure) as exc:
        raise RuntimeFailure(
            "bridge_protocol_error", "The bridge request is invalid.", exit_code=7
        ) from exc
    if not isinstance(value, dict) or set(value) != {
        "schema_version",
        "target",
        "action",
        "payload",
    }:
        raise RuntimeFailure(
            "bridge_protocol_error", "The bridge request is invalid.", exit_code=7
        )
    target = value["target"]
    if (
        value["schema_version"] != "v1"
        or not isinstance(value["action"], str)
        or value["action"] not in _ACTIONS
        or not isinstance(value["payload"], dict)
        or not isinstance(target, dict)
        or set(target)
        != {
            "alias",
            "database",
            "company_id",
            "user_login",
            "language",
            "timezone",
        }
        or not isinstance(target["alias"], str)
        or not target["alias"]
        or not isinstance(target["database"], str)
        or not target["database"]
        or not isinstance(target["company_id"], int)
        or isinstance(target["company_id"], bool)
        or target["company_id"] <= 0
        or not isinstance(target["user_login"], str)
        or not target["user_login"]
        or not isinstance(target["language"], str)
        or not target["language"]
        or not isinstance(target["timezone"], str)
        or not target["timezone"]
    ):
        raise RuntimeFailure(
            "bridge_protocol_error", "The bridge request is invalid.", exit_code=7
        )
    return value


def _validated_target(request: dict[str, Any], config_path: Path):
    target = request["target"]
    try:
        resolved = load_runtime_config(config_path).resolve(
            target["alias"], target["company_id"], target["user_login"]
        )
    except ConfigError as exc:
        if exc.code == "database_unavailable":
            exit_code = 4
        elif exc.code in {"company_unavailable", "user_unavailable"}:
            exit_code = 3
        else:
            exit_code = 7
        raise RuntimeFailure(
            exc.code,
            "The requested Odoo runtime target is unavailable.",
            exit_code=exit_code,
        ) from exc
    if resolved.database != target["database"]:
        raise RuntimeFailure(
            "database_unavailable",
            "The requested Odoo runtime target is unavailable.",
            exit_code=4,
        )
    return resolved


def _require_keys(payload: dict[str, Any], keys: set[str]) -> None:
    if set(payload) != keys:
        raise RuntimeFailure(
            "bridge_protocol_error", "The bridge action payload is invalid.", exit_code=7
        )


def _master_data_after_is_valid(spec: dict[str, Any], after: Any) -> bool:
    if after is None:
        return True
    expected_types = spec["cursor_types"]
    if not isinstance(after, list) or len(after) != len(expected_types):
        return False
    for index, (value, expected_type) in enumerate(zip(after, expected_types, strict=True)):
        if expected_type is bool:
            if not isinstance(value, bool):
                return False
        elif expected_type is int:
            if not isinstance(value, int) or isinstance(value, bool):
                return False
            if index == len(after) - 1 and value <= 0:
                return False
        elif not isinstance(value, str) or not value:
            return False
    return True


def _master_data_cursor_domain(spec: dict[str, Any], after: list[Any]) -> list[Any]:
    fields = spec["cursor_fields"]
    operators = spec["cursor_operators"]
    if fields[0] == "active":
        tail_spec = {
            "cursor_fields": fields[1:],
            "cursor_operators": operators[1:],
        }
        tail = _master_data_cursor_domain(tail_spec, after[1:])
        same_active = ["&", ("active", "=", after[0]), *tail]
        if after[0] is True:
            return ["|", ("active", "=", False), *same_active]
        return same_active
    terms: list[list[Any]] = []
    for index, (field, operator) in enumerate(zip(fields, operators, strict=True)):
        term = [
            *((previous, "=", after[position]) for position, previous in enumerate(fields[:index])),
            (field, operator, after[index]),
        ]
        terms.append(term)
    domain: list[Any] = ["|"] * (len(terms) - 1)
    for term in terms:
        domain.extend(["&"] * (len(term) - 1))
        domain.extend(term)
    return domain


def _master_data_scope_domain(scope: str, company_id: int) -> list[Any]:
    if scope == "company":
        return [("company_id", "=", company_id)]
    if scope == "shared_company":
        return ["|", ("company_id", "=", False), ("company_id", "=", company_id)]
    if scope == "global":
        return []
    raise AssertionError("unknown fixed master-data scope")


def _dispatch_master_data(
    env: Any,
    action: str,
    payload: dict[str, Any],
    company_id: int,
) -> dict[str, Any]:
    spec = _MASTER_DATA_ACTIONS[action]
    _require_keys(payload, {"company_id", "after", "limit"})
    limit = payload["limit"]
    after = payload["after"]
    if (
        not isinstance(payload["company_id"], int)
        or isinstance(payload["company_id"], bool)
        or not isinstance(limit, int)
        or isinstance(limit, bool)
        or not 1 <= limit <= 1001
        or not _master_data_after_is_valid(spec, after)
    ):
        raise RuntimeFailure(
            "bridge_protocol_error",
            "The bridge action payload is invalid.",
            exit_code=7,
        )
    if payload["company_id"] != company_id:
        raise RuntimeFailure(
            "company_unavailable", "The company is unavailable.", exit_code=3
        )

    company_visible = bool(
        env["res.company"].search_count([("id", "=", company_id)], limit=1)
    )
    model_name = spec["model"]
    module_installed = env.registry.get(model_name) is not None
    access_allowed = bool(
        company_visible
        and module_installed
        and env[model_name].has_access("read")
        and (
            action != "account.payment.term.read_page"
            or env["account.payment.term.line"].has_access("read")
        )
    )
    if not access_allowed:
        return {
            "user_id": env.uid,
            "company_visible": company_visible,
            "module_installed": module_installed,
            "access_allowed": access_allowed,
            "rows": [],
        }

    domain = _master_data_scope_domain(spec["scope"], company_id)
    if after is not None:
        cursor_domain = _master_data_cursor_domain(spec, after)
        domain = ["&", *domain, *cursor_domain] if domain else cursor_domain
    rows = (
        env[model_name]
        .with_context(active_test=False, allowed_company_ids=[company_id])
        .search_read(
            domain,
            fields=list(spec["fields"]),
            limit=limit,
            order=spec["order"],
        )
    )
    if action == "account.journal.read_page":
        for row in rows:
            row["currency"] = _reference(row.pop("currency_id"), label="code")
            row["company_id"] = _reference_id(row["company_id"])
    elif action == "account.tax.read_page":
        for row in rows:
            row["amount"] = _decimal_string(row["amount"])
            row["tax_group"] = _reference(row.pop("tax_group_id"), label="name")
            row["company_id"] = _reference_id(row["company_id"])
    elif action == "account.payment.term.read_page":
        line_ids = [line_id for row in rows for line_id in row.pop("line_ids")]
        if len(line_ids) != len(set(line_ids)):
            raise RuntimeFailure(
                "odoo_runtime_error",
                "The Odoo runtime request failed.",
                exit_code=7,
            )
        expected_line_ids = set(line_ids)
        observed_line_ids: set[int] = set()
        lines_by_term: dict[int, list[dict[str, Any]]] = {
            row["id"]: [] for row in rows
        }
        if line_ids:
            line_rows = (
                env["account.payment.term.line"]
                .with_context(active_test=False, allowed_company_ids=[company_id])
                .search_read(
                    [("id", "in", line_ids)],
                    fields=[
                        "id",
                        "payment_id",
                        "value",
                        "value_amount",
                        "delay_type",
                        "nb_days",
                        "days_next_month",
                    ],
                    limit=len(line_ids),
                    order="payment_id,id",
                )
            )
            for line in line_rows:
                line_id = line.get("id")
                if line_id not in expected_line_ids or line_id in observed_line_ids:
                    raise RuntimeFailure(
                        "odoo_runtime_error",
                        "The Odoo runtime request failed.",
                        exit_code=7,
                    )
                observed_line_ids.add(line_id)
                payment_id = _reference_id(line.pop("payment_id"))
                if payment_id not in lines_by_term:
                    raise RuntimeFailure(
                        "odoo_runtime_error",
                        "The Odoo runtime request failed.",
                        exit_code=7,
                    )
                line["value_amount"] = _decimal_string(line["value_amount"])
                if line["days_next_month"] is False:
                    line["days_next_month"] = None
                lines_by_term[payment_id].append(line)
            if observed_line_ids != expected_line_ids:
                raise RuntimeFailure(
                    "odoo_runtime_error",
                    "The Odoo runtime request failed.",
                    exit_code=7,
                )
        for row in rows:
            row["company_id"] = _reference_id(row["company_id"])
            row["discount_percentage"] = _decimal_string(
                row["discount_percentage"]
            )
            row["lines"] = lines_by_term[row["id"]]
    if action == "res.currency.read_page":
        for row in rows:
            row["is_company_currency"] = row.pop("is_current_company_currency")
            row["code"] = row["name"]
            full_name = row.pop("full_name")
            row["name"] = None if full_name is False else full_name
            if row["position"] is False:
                row["position"] = None
            row["rounding"] = _decimal_string(row["rounding"])
    return {
        "user_id": env.uid,
        "company_visible": company_visible,
        "module_installed": module_installed,
        "access_allowed": access_allowed,
        "rows": rows,
    }


def _dispatch_company_contexts(
    env: Any,
    payload: dict[str, Any],
    company_id: int,
    available_company_ids: tuple[int, ...],
) -> dict[str, Any]:
    _require_keys(payload, {"company_id", "after", "limit"})
    after = payload["after"]
    limit = payload["limit"]
    if (
        not isinstance(payload["company_id"], int)
        or isinstance(payload["company_id"], bool)
        or not isinstance(limit, int)
        or isinstance(limit, bool)
        or not 1 <= limit <= 1001
        or (
            after is not None
            and (
                not isinstance(after, list)
                or len(after) != 1
                or not isinstance(after[0], int)
                or isinstance(after[0], bool)
                or after[0] <= 0
            )
        )
        or not isinstance(available_company_ids, tuple)
        or not available_company_ids
        or company_id not in available_company_ids
        or any(
            not isinstance(available_id, int)
            or isinstance(available_id, bool)
            or available_id <= 0
            for available_id in available_company_ids
        )
        or len(available_company_ids) != len(set(available_company_ids))
    ):
        raise RuntimeFailure(
            "bridge_protocol_error", "The bridge action payload is invalid.", exit_code=7
        )
    if payload["company_id"] != company_id:
        raise RuntimeFailure(
            "company_unavailable", "The company is unavailable.", exit_code=3
        )

    company_model = env["res.company"]
    company_visible = bool(
        company_model.search_count([("id", "=", company_id)], limit=1)
    )
    module_installed = env.registry.get("account.account") is not None
    access_allowed = bool(
        company_visible
        and module_installed
        and company_model.has_access("read")
        and env["res.currency"].has_access("read")
        and env["res.country"].has_access("read")
    )
    if not access_allowed:
        return {
            "user_id": env.uid,
            "company_visible": company_visible,
            "module_installed": module_installed,
            "access_allowed": access_allowed,
            "rows": [],
        }

    domain: list[Any] = [("id", "in", list(available_company_ids))]
    if after is not None:
        domain.append(("id", ">", after[0]))
    rows = (
        company_model.with_context(
            active_test=False,
            allowed_company_ids=list(available_company_ids),
        ).search_read(
            domain,
            fields=[
                "id",
                "name",
                "sequence",
                "active",
                "currency_id",
                "country_id",
                "account_fiscal_country_id",
                "chart_template",
                "tax_calculation_rounding_method",
                "fiscalyear_last_month",
                "fiscalyear_last_day",
            ],
            limit=limit,
            order="id",
        )
    )
    allowed_set = set(available_company_ids)
    if any(row.get("id") not in allowed_set for row in rows):
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        )

    currency_ids = {_reference_id(row["currency_id"]) for row in rows}
    if None in currency_ids:
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        )
    country_ids = {
        reference_id
        for row in rows
        for reference_id in (
            _reference_id(row["country_id"]),
            _reference_id(row["account_fiscal_country_id"]),
        )
        if reference_id is not None
    }
    currency_rows = env["res.currency"].with_context(active_test=False).search_read(
        [("id", "in", list(currency_ids))],
        fields=["id", "name", "decimal_places"],
        limit=len(currency_ids),
        order="id",
    )
    country_rows = env["res.country"].with_context(active_test=False).search_read(
        [("id", "in", list(country_ids))],
        fields=["id", "code", "name"],
        limit=len(country_ids),
        order="id",
    )
    currencies = {row["id"]: row for row in currency_rows}
    countries = {row["id"]: row for row in country_rows}
    if set(currencies) != currency_ids or set(countries) != country_ids:
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        )

    for row in rows:
        currency_id = _reference_id(row.pop("currency_id"))
        country_id = _reference_id(row.pop("country_id"))
        fiscal_country_id = _reference_id(row.pop("account_fiscal_country_id"))
        currency = currencies[currency_id]
        row["currency"] = {
            "id": currency_id,
            "code": currency["name"],
            "decimal_places": currency["decimal_places"],
        }
        row["country"] = dict(countries[country_id]) if country_id else None
        row["fiscal_country"] = (
            dict(countries[fiscal_country_id]) if fiscal_country_id else None
        )
        row["current"] = row["id"] == company_id
        if row["chart_template"] is False:
            row["chart_template"] = None
        if row["tax_calculation_rounding_method"] is False:
            row["tax_calculation_rounding_method"] = None
        try:
            month = int(row.pop("fiscalyear_last_month"))
        except (TypeError, ValueError) as exc:
            raise RuntimeFailure(
                "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
            ) from exc
        row["fiscal_year_end"] = {
            "month": month,
            "day": row.pop("fiscalyear_last_day"),
        }
    return {
        "user_id": env.uid,
        "company_visible": company_visible,
        "module_installed": module_installed,
        "access_allowed": access_allowed,
        "rows": rows,
    }


def _reference_id(value: Any) -> int | None:
    if value is False or value is None:
        return None
    if (
        isinstance(value, (list, tuple))
        and len(value) == 2
        and isinstance(value[0], int)
        and not isinstance(value[0], bool)
        and value[0] > 0
    ):
        return value[0]
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    raise RuntimeFailure(
        "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
    )


def _reference(value: Any, *, label: str) -> dict[str, Any] | None:
    if value is False or value is None:
        return None
    if (
        isinstance(value, (list, tuple))
        and len(value) == 2
        and isinstance(value[1], str)
        and value[1]
    ):
        return {"id": _reference_id(value), label: value[1]}
    raise RuntimeFailure(
        "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
    )


def _decimal_string(value: Any) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        )
    decimal_value = value if isinstance(value, Decimal) else Decimal(str(value))
    if not decimal_value.is_finite():
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        )
    if decimal_value == 0:
        return "0"
    text = format(decimal_value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _date_string(value: Any) -> str:
    if isinstance(value, date_type):
        return value.isoformat()
    if isinstance(value, str):
        try:
            parsed = date_type.fromisoformat(value)
        except ValueError as exc:
            raise RuntimeFailure(
                "odoo_runtime_error",
                "The Odoo runtime request failed.",
                exit_code=7,
            ) from exc
        if parsed.isoformat() == value:
            return value
    raise RuntimeFailure(
        "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
    )


def _is_canonical_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return date_type.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _optional_string(value: Any) -> str | None:
    if value is False or value is None:
        return None
    if isinstance(value, str):
        return value
    raise RuntimeFailure(
        "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
    )


def _related_rows(
    env: Any,
    model_name: str,
    record_ids: set[int],
    fields: tuple[str, ...],
    company_id: int,
) -> dict[int, dict[str, Any]]:
    if not record_ids:
        return {}
    rows = (
        env[model_name]
        .with_context(active_test=False, allowed_company_ids=[company_id])
        .search_read(
            [("id", "in", sorted(record_ids))],
            fields=["id", *fields],
            limit=len(record_ids),
            order="id",
        )
    )
    result: dict[int, dict[str, Any]] = {}
    for row in rows:
        record_id = row.get("id")
        if (
            not isinstance(record_id, int)
            or isinstance(record_id, bool)
            or record_id not in record_ids
            or record_id in result
        ):
            raise RuntimeFailure(
                "odoo_runtime_error",
                "The Odoo runtime request failed.",
                exit_code=7,
            )
        result[record_id] = row
    if set(result) != record_ids:
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        )
    return result


def _journal_reference(row: dict[str, Any]) -> dict[str, Any]:
    if any(
        not isinstance(row.get(key), str) or not row[key].strip()
        for key in ("code", "name")
    ):
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        )
    return {"id": row["id"], "code": row["code"], "name": row["name"]}


def _currency_reference(row: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(row.get("name"), str) or not row["name"].strip():
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        )
    return {"id": row["id"], "code": row["name"]}


def _named_reference(row: dict[str, Any]) -> dict[str, Any]:
    name = row.get("complete_name")
    if not isinstance(name, str) or not name.strip():
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        )
    return {"id": row["id"], "name": name}


def _account_reference(row: dict[str, Any]) -> dict[str, Any]:
    if any(
        not isinstance(row.get(key), str) or not row[key].strip()
        for key in ("code", "name")
    ):
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        )
    return {"id": row["id"], "code": row["code"], "name": row["name"]}


def _journal_entry_filters_are_valid(filters: Any) -> bool:
    if not isinstance(filters, dict) or set(filters) != {
        "date_from",
        "date_to",
        "states",
        "journal_id",
        "partner_id",
        "query",
    }:
        return False
    for key in ("date_from", "date_to"):
        value = filters[key]
        if value is not None and not _is_canonical_date(value):
            return False
    if (
        filters["date_from"] is not None
        and filters["date_to"] is not None
        and filters["date_from"] > filters["date_to"]
    ):
        return False
    states = filters["states"]
    if not isinstance(states, list) or any(
        not isinstance(state, str) for state in states
    ):
        return False
    canonical_states = [state for state in ("draft", "posted", "cancel") if state in states]
    if (
        states != canonical_states
        or len(states) != len(set(states))
    ):
        return False
    for key in ("journal_id", "partner_id"):
        value = filters[key]
        if value is not None and (
            not isinstance(value, int) or isinstance(value, bool) or value <= 0
        ):
            return False
    query = filters["query"]
    return query is None or (
        isinstance(query, str)
        and query == query.strip()
        and 1 <= len(query) <= 200
    )


def _journal_entry_gate(
    env: Any, company_id: int, *, include_accounts: bool
) -> tuple[bool, bool, bool]:
    company_visible = bool(
        env["res.company"].search_count([("id", "=", company_id)], limit=1)
    )
    models = [
        "account.move",
        "account.move.line",
        "account.journal",
        "res.currency",
        "res.partner",
    ]
    if include_accounts:
        models.append("account.account")
    module_installed = all(env.registry.get(model_name) is not None for model_name in models)
    access_allowed = bool(
        company_visible
        and module_installed
        and all(env[model_name].has_access("read") for model_name in models)
    )
    return company_visible, module_installed, access_allowed


def _journal_entry_domain(
    company_id: int,
    after: list[Any] | None,
    filters: dict[str, Any],
) -> list[Any]:
    from odoo.osv import expression

    domains: list[list[Any]] = [
        [("company_id", "=", company_id), ("move_type", "=", "entry")]
    ]
    if filters["date_from"] is not None:
        domains.append([("date", ">=", filters["date_from"])])
    if filters["date_to"] is not None:
        domains.append([("date", "<=", filters["date_to"])])
    if filters["states"]:
        domains.append([("state", "in", filters["states"])])
    if filters["journal_id"] is not None:
        domains.append([("journal_id", "=", filters["journal_id"])])
    if filters["partner_id"] is not None:
        domains.append([("partner_id", "=", filters["partner_id"])])
    if filters["query"] is not None:
        domains.append(
            ["|", ("name", "ilike", filters["query"]), ("ref", "ilike", filters["query"])]
        )
    if after is not None:
        domains.append(
            [
                "|",
                ("date", "<", after[0]),
                "&",
                ("date", "=", after[0]),
                ("id", "<", after[1]),
            ]
        )
    return expression.AND(domains)


def _journal_entry_related(
    env: Any, moves: list[dict[str, Any]], lines: list[dict[str, Any]], company_id: int
) -> dict[str, dict[int, dict[str, Any]]]:
    journal_ids = {
        journal_id
        for row in moves
        if (journal_id := _reference_id(row["journal_id"])) is not None
    }
    currency_ids = {
        currency_id
        for row in moves
        if (currency_id := _reference_id(row["company_currency_id"])) is not None
    }
    partner_ids = {
        partner_id
        for row in [*moves, *lines]
        if (partner_id := _reference_id(row.get("partner_id"))) is not None
    }
    account_ids = {
        account_id
        for row in lines
        if (account_id := _reference_id(row.get("account_id"))) is not None
    }
    currency_ids.update(
        currency_id
        for row in lines
        for key in ("company_currency_id", "currency_id")
        if (currency_id := _reference_id(row.get(key))) is not None
    )
    return {
        "journals": _related_rows(
            env, "account.journal", journal_ids, ("code", "name"), company_id
        ),
        "currencies": _related_rows(
            env, "res.currency", currency_ids, ("name",), company_id
        ),
        "partners": _related_rows(
            env, "res.partner", partner_ids, ("complete_name",), company_id
        ),
        "accounts": _related_rows(
            env, "account.account", account_ids, ("code", "name"), company_id
        ),
    }


def _safe_related(
    related: dict[str, dict[int, dict[str, Any]]], group: str, record_id: int | None
) -> dict[str, Any]:
    if record_id is None:
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        )
    try:
        return related[group][record_id]
    except KeyError as exc:
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        ) from exc


def _journal_entry_header(
    move: dict[str, Any], related: dict[str, dict[int, dict[str, Any]]]
) -> dict[str, Any]:
    journal_id = _reference_id(move.pop("journal_id"))
    company_id = _reference_id(move.pop("company_id"))
    currency_id = _reference_id(move.pop("company_currency_id"))
    partner_id = _reference_id(move.pop("partner_id"))
    move["name"] = _optional_string(move["name"])
    move["date"] = _date_string(move["date"])
    move["ref"] = _optional_string(move["ref"])
    move["journal"] = _journal_reference(_safe_related(related, "journals", journal_id))
    move["company_id"] = company_id
    move["currency"] = _currency_reference(
        _safe_related(related, "currencies", currency_id)
    )
    move["partner"] = (
        _named_reference(_safe_related(related, "partners", partner_id))
        if partner_id is not None
        else None
    )
    return move


def _dispatch_journal_entry_search(
    env: Any, payload: dict[str, Any], company_id: int
) -> dict[str, Any]:
    _require_keys(payload, {"company_id", "after", "limit", "filters"})
    after = payload["after"]
    limit = payload["limit"]
    if (
        not isinstance(payload["company_id"], int)
        or isinstance(payload["company_id"], bool)
        or not isinstance(limit, int)
        or isinstance(limit, bool)
        or not 1 <= limit <= 1001
        or (
            after is not None
            and (
                not isinstance(after, list)
                or len(after) != 2
                or not _is_canonical_date(after[0])
                or not isinstance(after[1], int)
                or isinstance(after[1], bool)
                or after[1] <= 0
            )
        )
        or not _journal_entry_filters_are_valid(payload["filters"])
    ):
        raise RuntimeFailure(
            "bridge_protocol_error", "The bridge action payload is invalid.", exit_code=7
        )
    if payload["company_id"] != company_id:
        raise RuntimeFailure(
            "company_unavailable", "The company is unavailable.", exit_code=3
        )
    company_visible, module_installed, access_allowed = _journal_entry_gate(
        env, company_id, include_accounts=False
    )
    if not access_allowed:
        return {
            "user_id": env.uid,
            "company_visible": company_visible,
            "module_installed": module_installed,
            "access_allowed": access_allowed,
            "rows": [],
        }
    move_fields = [
        "id",
        "name",
        "date",
        "state",
        "ref",
        "journal_id",
        "company_id",
        "company_currency_id",
        "partner_id",
    ]
    moves = (
        env["account.move"]
        .with_context(active_test=False, allowed_company_ids=[company_id])
        .search_read(
            _journal_entry_domain(company_id, after, payload["filters"]),
            fields=move_fields,
            limit=limit,
            order="date desc,id desc",
        )
    )
    move_ids = [row["id"] for row in moves]
    lines = []
    if move_ids:
        lines = (
            env["account.move.line"]
            .with_context(active_test=False, allowed_company_ids=[company_id])
            .search_read(
                [("move_id", "in", move_ids)],
                fields=["id", "move_id", "debit", "credit", "balance"],
                order="move_id,id",
            )
        )
    totals = {
        move_id: {"debit": Decimal(0), "credit": Decimal(0), "balance": Decimal(0)}
        for move_id in move_ids
    }
    for line in lines:
        move_id = _reference_id(line["move_id"])
        if move_id not in totals:
            raise RuntimeFailure(
                "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
            )
        for field in ("debit", "credit", "balance"):
            value = line[field]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise RuntimeFailure(
                    "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
                )
            totals[move_id][field] += Decimal(str(value))
    related = _journal_entry_related(env, moves, [], company_id)
    rows = []
    observed_move_ids: set[int] = set()
    for move in moves:
        move_id = move["id"]
        if (
            not isinstance(move_id, int)
            or isinstance(move_id, bool)
            or move_id <= 0
            or move_id in observed_move_ids
        ):
            raise RuntimeFailure(
                "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
            )
        observed_move_ids.add(move_id)
        row = _journal_entry_header(move, related)
        row.update(
            {
                field: _decimal_string(value)
                for field, value in totals[move_id].items()
            }
        )
        rows.append(row)
    return {
        "user_id": env.uid,
        "company_visible": company_visible,
        "module_installed": module_installed,
        "access_allowed": access_allowed,
        "rows": rows,
    }


def _dispatch_journal_entry_get(
    env: Any, payload: dict[str, Any], company_id: int
) -> dict[str, Any]:
    _require_keys(payload, {"company_id", "move_id"})
    if (
        not isinstance(payload["company_id"], int)
        or isinstance(payload["company_id"], bool)
        or not isinstance(payload["move_id"], int)
        or isinstance(payload["move_id"], bool)
        or payload["move_id"] <= 0
    ):
        raise RuntimeFailure(
            "bridge_protocol_error", "The bridge action payload is invalid.", exit_code=7
        )
    if payload["company_id"] != company_id:
        raise RuntimeFailure(
            "company_unavailable", "The company is unavailable.", exit_code=3
        )
    company_visible, module_installed, access_allowed = _journal_entry_gate(
        env, company_id, include_accounts=True
    )
    if not access_allowed:
        return {
            "user_id": env.uid,
            "company_visible": company_visible,
            "module_installed": module_installed,
            "access_allowed": access_allowed,
            "entry": None,
        }
    move_fields = [
        "id",
        "name",
        "date",
        "state",
        "ref",
        "journal_id",
        "company_id",
        "company_currency_id",
        "partner_id",
    ]
    moves = (
        env["account.move"]
        .with_context(active_test=False, allowed_company_ids=[company_id])
        .search_read(
            [
                ("id", "=", payload["move_id"]),
                ("company_id", "=", company_id),
                ("move_type", "=", "entry"),
            ],
            fields=move_fields,
            limit=1,
        )
    )
    if not moves:
        return {
            "user_id": env.uid,
            "company_visible": company_visible,
            "module_installed": module_installed,
            "access_allowed": access_allowed,
            "entry": None,
        }
    lines = (
        env["account.move.line"]
        .with_context(active_test=False, allowed_company_ids=[company_id])
        .search_read(
            [("move_id", "=", payload["move_id"])],
            fields=[
                "id",
                "move_id",
                "sequence",
                "display_type",
                "name",
                "account_id",
                "partner_id",
                "debit",
                "credit",
                "balance",
                "company_currency_id",
                "amount_currency",
                "currency_id",
                "date_maturity",
                "reconciled",
                "matching_number",
            ],
            order="sequence,id",
        )
    )
    related = _journal_entry_related(env, moves, lines, company_id)
    entry = _journal_entry_header(moves[0], related)
    totals = {"debit": Decimal(0), "credit": Decimal(0), "balance": Decimal(0)}
    normalized_lines = []
    for line in lines:
        if _reference_id(line.pop("move_id")) != entry["id"]:
            raise RuntimeFailure(
                "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
            )
        account_id = _reference_id(line.pop("account_id"))
        partner_id = _reference_id(line.pop("partner_id"))
        company_currency_id = _reference_id(line.pop("company_currency_id"))
        currency_id = _reference_id(line.pop("currency_id"))
        line["display_type"] = _optional_string(line["display_type"])
        line["name"] = _optional_string(line["name"])
        line["partner"] = (
            _named_reference(_safe_related(related, "partners", partner_id))
            if partner_id is not None
            else None
        )
        line["account"] = (
            _account_reference(_safe_related(related, "accounts", account_id))
            if account_id is not None
            else None
        )
        if (
            line["display_type"] in {"line_section", "line_subsection", "line_note"}
            and line["account"] is not None
        ) or (
            line["display_type"] not in {"line_section", "line_subsection", "line_note"}
            and line["account"] is None
        ):
            raise RuntimeFailure(
                "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
            )
        line["company_currency"] = _currency_reference(
            _safe_related(related, "currencies", company_currency_id)
        )
        line["currency"] = (
            _currency_reference(_safe_related(related, "currencies", currency_id))
            if currency_id is not None
            else None
        )
        line["date_maturity"] = (
            _date_string(line["date_maturity"])
            if line["date_maturity"] not in (False, None)
            else None
        )
        line["matching_number"] = _optional_string(line["matching_number"])
        for field in ("debit", "credit", "balance", "amount_currency"):
            raw = line[field]
            line[field] = _decimal_string(raw)
            if field in totals:
                totals[field] += Decimal(str(raw))
        normalized_lines.append(line)
    entry["lines"] = normalized_lines
    entry["totals"] = {
        field: _decimal_string(value) for field, value in totals.items()
    }
    return {
        "user_id": env.uid,
        "company_visible": company_visible,
        "module_installed": module_installed,
        "access_allowed": access_allowed,
        "entry": entry,
    }


def _invoice_choices_are_canonical(value: Any, allowed: tuple[str, ...]) -> bool:
    return (
        isinstance(value, list)
        and all(isinstance(item, str) for item in value)
        and len(value) == len(set(value))
        and value == [item for item in allowed if item in value]
    )


def _invoice_search_payload_is_valid(payload: Any) -> bool:
    if not isinstance(payload, dict) or set(payload) != {
        "company_id",
        "after",
        "limit",
        "filters",
    }:
        return False
    if (
        not isinstance(payload["company_id"], int)
        or isinstance(payload["company_id"], bool)
        or payload["company_id"] <= 0
        or not isinstance(payload["limit"], int)
        or isinstance(payload["limit"], bool)
        or not 1 <= payload["limit"] <= 1001
    ):
        return False
    after = payload["after"]
    if after is not None and (
        not isinstance(after, list)
        or len(after) != 2
        or not _is_canonical_date(after[0])
        or not isinstance(after[1], int)
        or isinstance(after[1], bool)
        or after[1] <= 0
    ):
        return False
    filters = payload["filters"]
    if not isinstance(filters, dict) or set(filters) != {
        "date_from",
        "date_to",
        "document_types",
        "states",
        "payment_states",
        "journal_id",
        "partner_id",
        "query",
    }:
        return False
    for key in ("date_from", "date_to"):
        if filters[key] is not None and not _is_canonical_date(filters[key]):
            return False
    if (
        filters["date_from"] is not None
        and filters["date_to"] is not None
        and filters["date_from"] > filters["date_to"]
    ):
        return False
    if not _invoice_choices_are_canonical(
        filters["document_types"], _INVOICE_DOCUMENT_TYPES
    ) or not _invoice_choices_are_canonical(filters["states"], _INVOICE_STATES):
        return False
    if not _invoice_choices_are_canonical(
        filters["payment_states"], _INVOICE_PAYMENT_STATES
    ):
        return False
    for key in ("journal_id", "partner_id"):
        value = filters[key]
        if value is not None and (
            not isinstance(value, int) or isinstance(value, bool) or value <= 0
        ):
            return False
    query = filters["query"]
    return query is None or (
        isinstance(query, str)
        and query == query.strip()
        and 1 <= len(query) <= 200
    )


def _invoice_id_payload_is_valid(payload: Any) -> bool:
    return (
        isinstance(payload, dict)
        and set(payload) == {"company_id", "move_id"}
        and isinstance(payload["company_id"], int)
        and not isinstance(payload["company_id"], bool)
        and payload["company_id"] > 0
        and isinstance(payload["move_id"], int)
        and not isinstance(payload["move_id"], bool)
        and payload["move_id"] > 0
    )


def _invoice_gate(
    env: Any, company_id: int, required_models: tuple[str, ...]
) -> tuple[bool, bool, bool]:
    if env.registry.get("res.company") is None:
        return False, False, False
    company_read_allowed = bool(env["res.company"].has_access("read"))
    company_visible = bool(
        company_read_allowed
        and env["res.company"].search_count([("id", "=", company_id)], limit=1)
    )
    module_installed = all(
        env.registry.get(model_name) is not None
        for model_name in required_models
        if model_name != "res.company"
    )
    if not module_installed:
        return company_visible, False, False
    access_allowed = bool(
        company_visible
        and all(
            env[model_name].has_access("read")
            for model_name in required_models
            if model_name != "res.company"
        )
    )
    return company_visible, module_installed, access_allowed


def _empty_invoice_result(
    env: Any,
    *,
    company_visible: bool,
    module_installed: bool,
    access_allowed: bool,
    result_key: str,
) -> dict[str, Any]:
    return {
        "user_id": env.uid,
        "company_visible": company_visible,
        "module_installed": module_installed,
        "access_allowed": access_allowed,
        result_key: [] if result_key == "rows" else None,
    }


def _invoice_domain(
    company_id: int, after: list[Any] | None, filters: dict[str, Any]
) -> list[Any]:
    from odoo.osv import expression

    document_types = filters["document_types"] or list(_INVOICE_DOCUMENT_TYPES)
    domains: list[list[Any]] = [
        [
            ("company_id", "=", company_id),
            ("move_type", "in", document_types),
        ]
    ]
    if filters["date_from"] is not None:
        domains.append([("date", ">=", filters["date_from"])])
    if filters["date_to"] is not None:
        domains.append([("date", "<=", filters["date_to"])])
    if filters["states"]:
        domains.append([("state", "in", filters["states"])])
    if filters["payment_states"]:
        domains.append([("payment_state", "in", filters["payment_states"])])
    if filters["journal_id"] is not None:
        domains.append([("journal_id", "=", filters["journal_id"])])
    if filters["partner_id"] is not None:
        domains.append([("partner_id", "=", filters["partner_id"])])
    if filters["query"] is not None:
        domains.append(
            [
                "|",
                "|",
                "|",
                ("name", "ilike", filters["query"]),
                ("ref", "ilike", filters["query"]),
                ("payment_reference", "ilike", filters["query"]),
                ("invoice_origin", "ilike", filters["query"]),
            ]
        )
    if after is not None:
        domains.append(
            [
                "|",
                ("date", "<", after[0]),
                "&",
                ("date", "=", after[0]),
                ("id", "<", after[1]),
            ]
        )
    return expression.AND(domains)


def _invoice_header_related(
    env: Any, moves: list[dict[str, Any]], company_id: int
) -> dict[str, dict[int, dict[str, Any]]]:
    journal_ids = {
        record_id
        for move in moves
        if (record_id := _reference_id(move.get("journal_id"))) is not None
    }
    currency_ids = {
        record_id
        for move in moves
        if (record_id := _reference_id(move.get("currency_id"))) is not None
    }
    partner_ids = {
        record_id
        for move in moves
        if (record_id := _reference_id(move.get("partner_id"))) is not None
    }
    return {
        "journals": _related_rows(
            env, "account.journal", journal_ids, ("code", "name"), company_id
        ),
        "currencies": _related_rows(
            env, "res.currency", currency_ids, ("name",), company_id
        ),
        "partners": _related_rows(
            env, "res.partner", partner_ids, ("complete_name",), company_id
        ),
    }


def _optional_date(value: Any) -> str | None:
    return None if value in (False, None) else _date_string(value)


def _invoice_header(
    raw: dict[str, Any],
    related: dict[str, dict[int, dict[str, Any]]],
    company_id: int,
) -> dict[str, Any]:
    if set(raw) != set(_INVOICE_HEADER_FIELDS):
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        )
    row = dict(raw)
    record_id = row.get("id")
    journal_id = _reference_id(row.pop("journal_id"))
    row_company_id = _reference_id(row.pop("company_id"))
    currency_id = _reference_id(row.pop("currency_id"))
    partner_id = _reference_id(row.pop("partner_id"))
    if (
        not isinstance(record_id, int)
        or isinstance(record_id, bool)
        or record_id <= 0
        or row_company_id != company_id
    ):
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        )
    row["name"] = _optional_string(row["name"])
    row["date"] = _date_string(row["date"])
    row["invoice_date"] = _optional_date(row["invoice_date"])
    row["invoice_date_due"] = _optional_date(row["invoice_date_due"])
    for field in ("ref", "payment_reference", "invoice_origin"):
        row[field] = _optional_string(row[field])
    row["journal"] = _journal_reference(
        _safe_related(related, "journals", journal_id)
    )
    row["company_id"] = row_company_id
    row["currency"] = _currency_reference(
        _safe_related(related, "currencies", currency_id)
    )
    row["partner"] = (
        _named_reference(_safe_related(related, "partners", partner_id))
        if partner_id is not None
        else None
    )
    for field in (
        "amount_untaxed",
        "amount_tax",
        "amount_total",
        "amount_residual",
    ):
        row[field] = _decimal_string(row[field])
    return row


def _dispatch_invoice_search(
    env: Any, payload: dict[str, Any], company_id: int
) -> dict[str, Any]:
    if not _invoice_search_payload_is_valid(payload):
        raise RuntimeFailure(
            "bridge_protocol_error", "The bridge action payload is invalid.", exit_code=7
        )
    if payload["company_id"] != company_id:
        raise RuntimeFailure(
            "company_unavailable", "The company is unavailable.", exit_code=3
        )
    company_visible, module_installed, access_allowed = _invoice_gate(
        env, company_id, _INVOICE_SEARCH_MODELS
    )
    if not access_allowed:
        return _empty_invoice_result(
            env,
            company_visible=company_visible,
            module_installed=module_installed,
            access_allowed=access_allowed,
            result_key="rows",
        )
    moves = (
        env["account.move"]
        .with_context(active_test=False, allowed_company_ids=[company_id])
        .search_read(
            _invoice_domain(company_id, payload["after"], payload["filters"]),
            fields=list(_INVOICE_HEADER_FIELDS),
            limit=payload["limit"],
            order="date desc,id desc",
        )
    )
    related = _invoice_header_related(env, moves, company_id)
    rows = [_invoice_header(move, related, company_id) for move in moves]
    return {
        "user_id": env.uid,
        "company_visible": company_visible,
        "module_installed": module_installed,
        "access_allowed": access_allowed,
        "rows": rows,
    }


def _many2many_ids(value: Any) -> list[int]:
    if value in (False, None):
        return []
    if (
        not isinstance(value, list)
        or any(
            not isinstance(record_id, int)
            or isinstance(record_id, bool)
            or record_id <= 0
            for record_id in value
        )
        or len(value) != len(set(value))
    ):
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        )
    return sorted(value)


def _dispatch_invoice_get(
    env: Any, payload: dict[str, Any], company_id: int
) -> dict[str, Any]:
    if not _invoice_id_payload_is_valid(payload):
        raise RuntimeFailure(
            "bridge_protocol_error", "The bridge action payload is invalid.", exit_code=7
        )
    if payload["company_id"] != company_id:
        raise RuntimeFailure(
            "company_unavailable", "The company is unavailable.", exit_code=3
        )
    company_visible, module_installed, access_allowed = _invoice_gate(
        env, company_id, _INVOICE_GET_MODELS
    )
    if not access_allowed:
        return _empty_invoice_result(
            env,
            company_visible=company_visible,
            module_installed=module_installed,
            access_allowed=access_allowed,
            result_key="invoice",
        )
    moves = (
        env["account.move"]
        .with_context(active_test=False, allowed_company_ids=[company_id])
        .search_read(
            [
                ("id", "=", payload["move_id"]),
                ("company_id", "=", company_id),
                ("move_type", "in", list(_INVOICE_DOCUMENT_TYPES)),
            ],
            fields=list(_INVOICE_HEADER_FIELDS),
            limit=1,
        )
    )
    if not moves:
        return _empty_invoice_result(
            env,
            company_visible=company_visible,
            module_installed=module_installed,
            access_allowed=access_allowed,
            result_key="invoice",
        )
    lines = (
        env["account.move.line"]
        .with_context(active_test=False, allowed_company_ids=[company_id])
        .search_read(
            [
                ("move_id", "=", payload["move_id"]),
                ("display_type", "in", list(_INVOICE_LINE_TYPES)),
            ],
            fields=list(_INVOICE_LINE_FIELDS),
            order="sequence,id",
        )
    )
    account_ids = {
        record_id
        for line in lines
        if (record_id := _reference_id(line.get("account_id"))) is not None
    }
    product_ids = {
        record_id
        for line in lines
        if (record_id := _reference_id(line.get("product_id"))) is not None
    }
    line_tax_ids = {line["id"]: _many2many_ids(line.get("tax_ids")) for line in lines}
    tax_ids = {record_id for values in line_tax_ids.values() for record_id in values}
    accounts = _related_rows(
        env, "account.account", account_ids, ("code", "name"), company_id
    )
    taxes = _related_rows(
        env,
        "account.tax",
        tax_ids,
        ("name", "type_tax_use", "amount_type", "amount", "price_include"),
        company_id,
    )
    products = _related_rows(
        env, "product.product", product_ids, ("display_name",), company_id
    )
    related = _invoice_header_related(env, moves, company_id)
    invoice = _invoice_header(moves[0], related, company_id)
    normalized_lines: list[dict[str, Any]] = []
    for raw in lines:
        if set(raw) != set(_INVOICE_LINE_FIELDS):
            raise RuntimeFailure(
                "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
            )
        line = dict(raw)
        line_id = line.get("id")
        if (
            not isinstance(line_id, int)
            or isinstance(line_id, bool)
            or line_id <= 0
            or _reference_id(line.pop("move_id")) != invoice["id"]
        ):
            raise RuntimeFailure(
                "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
            )
        product_id = _reference_id(line.pop("product_id"))
        account_id = _reference_id(line.pop("account_id"))
        tax_values = line_tax_ids[line_id]
        line.pop("tax_ids")
        line["display_type"] = _optional_string(line["display_type"])
        line["name"] = _optional_string(line["name"])
        line["product"] = (
            {
                "id": product_id,
                "name": products[product_id]["display_name"],
            }
            if product_id is not None and product_id in products
            else None
        )
        line["account"] = (
            _account_reference(accounts[account_id])
            if account_id is not None and account_id in accounts
            else None
        )
        if (
            line["display_type"]
            in {"line_section", "line_subsection", "line_note"}
        ) != (line["account"] is None):
            raise RuntimeFailure(
                "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
            )
        for field in (
            "quantity",
            "price_unit",
            "discount",
            "price_subtotal",
            "price_total",
        ):
            line[field] = _decimal_string(line[field])
        line["taxes"] = []
        for tax_id in tax_values:
            tax = taxes[tax_id]
            if not isinstance(tax.get("price_include"), bool):
                raise RuntimeFailure(
                    "odoo_runtime_error",
                    "The Odoo runtime request failed.",
                    exit_code=7,
                )
            line["taxes"].append(
                {
                    "id": tax_id,
                    "name": tax["name"],
                    "type_tax_use": tax["type_tax_use"],
                    "amount_type": tax["amount_type"],
                    "amount": _decimal_string(tax["amount"]),
                    "price_include": tax["price_include"],
                }
            )
        normalized_lines.append(line)
    invoice["lines"] = normalized_lines
    return {
        "user_id": env.uid,
        "company_visible": company_visible,
        "module_installed": module_installed,
        "access_allowed": access_allowed,
        "invoice": invoice,
    }


def _indexed_rows(
    rows: list[dict[str, Any]], expected_ids: set[int]
) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for row in rows:
        record_id = row.get("id")
        if (
            not isinstance(record_id, int)
            or isinstance(record_id, bool)
            or record_id not in expected_ids
            or record_id in result
        ):
            raise RuntimeFailure(
                "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
            )
        result[record_id] = row
    if set(result) != expected_ids:
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        )
    return result


def _dispatch_invoice_payment_status(
    env: Any, payload: dict[str, Any], company_id: int
) -> dict[str, Any]:
    if not _invoice_id_payload_is_valid(payload):
        raise RuntimeFailure(
            "bridge_protocol_error", "The bridge action payload is invalid.", exit_code=7
        )
    if payload["company_id"] != company_id:
        raise RuntimeFailure(
            "company_unavailable", "The company is unavailable.", exit_code=3
        )
    company_visible, module_installed, access_allowed = _invoice_gate(
        env, company_id, _INVOICE_STATUS_MODELS
    )
    if not access_allowed:
        return _empty_invoice_result(
            env,
            company_visible=company_visible,
            module_installed=module_installed,
            access_allowed=access_allowed,
            result_key="payment_status",
        )
    moves = (
        env["account.move"]
        .with_context(active_test=False, allowed_company_ids=[company_id])
        .search_read(
            [
                ("id", "=", payload["move_id"]),
                ("company_id", "=", company_id),
                ("move_type", "in", list(_INVOICE_DOCUMENT_TYPES)),
            ],
            fields=list(_INVOICE_STATUS_MOVE_FIELDS),
            limit=1,
        )
    )
    if not moves:
        return _empty_invoice_result(
            env,
            company_visible=company_visible,
            module_installed=module_installed,
            access_allowed=access_allowed,
            result_key="payment_status",
        )
    move = dict(moves[0])
    if set(move) != set(_INVOICE_STATUS_MOVE_FIELDS):
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        )
    move_id = move.get("id")
    move_company_id = _reference_id(move.pop("company_id"))
    move_currency_id = _reference_id(move.pop("currency_id"))
    company_currency_id = _reference_id(move.pop("company_currency_id"))
    if (
        not isinstance(move_id, int)
        or isinstance(move_id, bool)
        or move_id != payload["move_id"]
        or move_company_id != company_id
        or move_currency_id is None
        or company_currency_id is None
    ):
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        )

    term_lines = (
        env["account.move.line"]
        .with_context(active_test=False, allowed_company_ids=[company_id])
        .search_read(
            [
                ("move_id", "=", move_id),
                (
                    "account_id.account_type",
                    "in",
                    ["asset_receivable", "liability_payable"],
                ),
            ],
            fields=list(_INVOICE_TERM_LINE_FIELDS),
            order="id",
        )
    )
    term_ids = {
        line_id
        for line in term_lines
        if isinstance((line_id := line.get("id")), int)
        and not isinstance(line_id, bool)
        and line_id > 0
    }
    if len(term_ids) != len(term_lines):
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        )
    account_ids = {
        record_id
        for line in term_lines
        if (record_id := _reference_id(line.get("account_id"))) is not None
    }
    accounts = _related_rows(
        env,
        "account.account",
        account_ids,
        ("code", "name", "account_type"),
        company_id,
    )

    partials: list[dict[str, Any]] = []
    if term_ids:
        partials = (
            env["account.partial.reconcile"]
            .with_context(active_test=False, allowed_company_ids=[company_id])
            .search_read(
                [
                    "|",
                    ("debit_move_id", "in", sorted(term_ids)),
                    ("credit_move_id", "in", sorted(term_ids)),
                ],
                fields=list(_INVOICE_PARTIAL_FIELDS),
                order="max_date,id",
            )
        )
    partial_details: list[dict[str, Any]] = []
    counterpart_line_ids: set[int] = set()
    observed_partial_ids: set[int] = set()
    for partial in partials:
        if set(partial) != set(_INVOICE_PARTIAL_FIELDS):
            raise RuntimeFailure(
                "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
            )
        partial_id = partial.get("id")
        debit_line_id = _reference_id(partial["debit_move_id"])
        credit_line_id = _reference_id(partial["credit_move_id"])
        debit_is_invoice = debit_line_id in term_ids
        credit_is_invoice = credit_line_id in term_ids
        if (
            not isinstance(partial_id, int)
            or isinstance(partial_id, bool)
            or partial_id <= 0
            or partial_id in observed_partial_ids
            or debit_is_invoice == credit_is_invoice
        ):
            raise RuntimeFailure(
                "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
            )
        observed_partial_ids.add(partial_id)
        invoice_line_id = debit_line_id if debit_is_invoice else credit_line_id
        counterpart_line_id = credit_line_id if debit_is_invoice else debit_line_id
        if invoice_line_id is None or counterpart_line_id is None:
            raise RuntimeFailure(
                "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
            )
        partial_details.append(
            {
                "raw": partial,
                "invoice_line_id": invoice_line_id,
                "counterpart_line_id": counterpart_line_id,
                "invoice_amount": partial[
                    "debit_amount_currency"
                    if debit_is_invoice
                    else "credit_amount_currency"
                ],
            }
        )
        counterpart_line_ids.add(counterpart_line_id)

    counterpart_lines: dict[int, dict[str, Any]] = {}
    if counterpart_line_ids:
        rows = (
            env["account.move.line"]
            .with_context(active_test=False, allowed_company_ids=[company_id])
            .search_read(
                [("id", "in", sorted(counterpart_line_ids))],
                fields=list(_INVOICE_COUNTERPART_LINE_FIELDS),
                limit=len(counterpart_line_ids),
                order="id",
            )
        )
        counterpart_lines = _indexed_rows(rows, counterpart_line_ids)
    counterpart_move_ids = {
        record_id
        for row in counterpart_lines.values()
        if (record_id := _reference_id(row.get("move_id"))) is not None
    }
    counterpart_moves: dict[int, dict[str, Any]] = {}
    if counterpart_move_ids:
        rows = (
            env["account.move"]
            .with_context(active_test=False, allowed_company_ids=[company_id])
            .search_read(
                [
                    ("id", "in", sorted(counterpart_move_ids)),
                    ("company_id", "=", company_id),
                ],
                fields=list(_INVOICE_COUNTERPART_MOVE_FIELDS),
                limit=len(counterpart_move_ids),
                order="id",
            )
        )
        counterpart_moves = _indexed_rows(rows, counterpart_move_ids)
    payment_ids = set(_many2many_ids(move.pop("matched_payment_ids")))
    payment_ids.update(
        record_id
        for row in counterpart_moves.values()
        if (record_id := _reference_id(row.get("origin_payment_id"))) is not None
    )
    payment_rows: list[dict[str, Any]] = []
    if payment_ids:
        payment_rows = (
            env["account.payment"]
            .with_context(active_test=False, allowed_company_ids=[company_id])
            .search_read(
                [
                    ("id", "in", sorted(payment_ids)),
                    ("company_id", "=", company_id),
                ],
                fields=list(_INVOICE_PAYMENT_FIELDS),
                limit=len(payment_ids),
                order="date desc,id desc",
            )
        )
        _indexed_rows(payment_rows, payment_ids)

    method_line_ids = {
        record_id
        for row in payment_rows
        if (record_id := _reference_id(row.get("payment_method_line_id"))) is not None
    }
    method_lines = _related_rows(
        env,
        "account.payment.method.line",
        method_line_ids,
        ("payment_method_id",),
        company_id,
    )
    method_ids = {
        record_id
        for row in method_lines.values()
        if (record_id := _reference_id(row.get("payment_method_id"))) is not None
    }
    methods = _related_rows(
        env,
        "account.payment.method",
        method_ids,
        ("code", "name"),
        company_id,
    )
    journal_ids = {
        record_id
        for row in payment_rows
        if (record_id := _reference_id(row.get("journal_id"))) is not None
    }
    journals = _related_rows(
        env, "account.journal", journal_ids, ("code", "name"), company_id
    )
    currency_ids = {move_currency_id, company_currency_id}
    currency_ids.update(
        record_id
        for row in term_lines
        if (record_id := _reference_id(row.get("currency_id"))) is not None
    )
    currency_ids.update(
        record_id
        for row in payment_rows
        if (record_id := _reference_id(row.get("currency_id"))) is not None
    )
    currencies = _related_rows(
        env, "res.currency", currency_ids, ("name",), company_id
    )

    normalized_term_lines: list[dict[str, Any]] = []
    term_currency_ids: dict[int, int] = {}
    for raw in term_lines:
        if set(raw) != set(_INVOICE_TERM_LINE_FIELDS):
            raise RuntimeFailure(
                "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
            )
        line = dict(raw)
        line_id = line["id"]
        if _reference_id(line.pop("move_id")) != move_id:
            raise RuntimeFailure(
                "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
            )
        account_id = _reference_id(line.pop("account_id"))
        line_currency_id = _reference_id(line.pop("currency_id"))
        if account_id is None or line_currency_id is None:
            raise RuntimeFailure(
                "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
            )
        account = _account_reference(accounts[account_id])
        account_type = accounts[account_id].get("account_type")
        if account_type not in {"asset_receivable", "liability_payable"}:
            raise RuntimeFailure(
                "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
            )
        account["account_type"] = account_type
        line["account"] = account
        line["date_maturity"] = _optional_date(line["date_maturity"])
        for field in (
            "balance",
            "amount_currency",
            "amount_residual",
            "amount_residual_currency",
        ):
            line[field] = _decimal_string(line[field])
        line["currency"] = _currency_reference(currencies[line_currency_id])
        if not isinstance(line.get("reconciled"), bool):
            raise RuntimeFailure(
                "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
            )
        line["matching_number"] = _optional_string(line["matching_number"])
        term_currency_ids[line_id] = line_currency_id
        normalized_term_lines.append(line)

    reconciliations: list[dict[str, Any]] = []
    for detail in partial_details:
        partial = detail["raw"]
        counterpart_line = counterpart_lines[detail["counterpart_line_id"]]
        counterpart_move_id = _reference_id(counterpart_line.get("move_id"))
        if counterpart_move_id is None:
            raise RuntimeFailure(
                "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
            )
        counterpart_move = counterpart_moves[counterpart_move_id]
        payment_id = _reference_id(counterpart_move.get("origin_payment_id"))
        reconciliation_currency_id = term_currency_ids[detail["invoice_line_id"]]
        reconciliations.append(
            {
                "id": partial["id"],
                "date": _date_string(partial["max_date"]),
                "amount": _decimal_string(detail["invoice_amount"]),
                "company_amount": _decimal_string(partial["amount"]),
                "currency": _currency_reference(
                    currencies[reconciliation_currency_id]
                ),
                "company_currency": _currency_reference(
                    currencies[company_currency_id]
                ),
                "counterpart_line_id": detail["counterpart_line_id"],
                "counterpart_move": {
                    "id": counterpart_move_id,
                    "name": _optional_string(counterpart_move["name"]),
                    "move_type": counterpart_move["move_type"],
                    "state": counterpart_move["state"],
                    "date": _date_string(counterpart_move["date"]),
                },
                "payment_id": payment_id,
                "exchange_move_id": _reference_id(partial["exchange_move_id"]),
            }
        )

    payments: list[dict[str, Any]] = []
    for raw in payment_rows:
        if set(raw) != set(_INVOICE_PAYMENT_FIELDS):
            raise RuntimeFailure(
                "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
            )
        payment = dict(raw)
        currency_id = _reference_id(payment.pop("currency_id"))
        journal_id = _reference_id(payment.pop("journal_id"))
        method_line_id = _reference_id(payment.pop("payment_method_line_id"))
        payment_move_id = _reference_id(payment.pop("move_id"))
        if currency_id is None or journal_id is None or method_line_id is None:
            raise RuntimeFailure(
                "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
            )
        method_line = method_lines[method_line_id]
        method_id = _reference_id(method_line.get("payment_method_id"))
        if method_id is None:
            raise RuntimeFailure(
                "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
            )
        payment["name"] = _optional_string(payment["name"])
        payment["date"] = _date_string(payment["date"])
        payment["amount"] = _decimal_string(payment["amount"])
        payment["currency"] = _currency_reference(currencies[currency_id])
        payment["journal"] = _journal_reference(journals[journal_id])
        method = methods[method_id]
        if any(
            not isinstance(method.get(key), str) or not method[key].strip()
            for key in ("code", "name")
        ):
            raise RuntimeFailure(
                "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
            )
        payment["payment_method"] = {
            "id": method_id,
            "code": method["code"],
            "name": method["name"],
        }
        payment["move_id"] = payment_move_id
        if not isinstance(payment.get("is_reconciled"), bool) or not isinstance(
            payment.get("is_matched"), bool
        ):
            raise RuntimeFailure(
                "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
            )
        payments.append(payment)

    move["name"] = _optional_string(move["name"])
    move["company_id"] = move_company_id
    move["currency"] = _currency_reference(currencies[move_currency_id])
    move["company_currency"] = _currency_reference(
        currencies[company_currency_id]
    )
    move["amount_total"] = _decimal_string(move["amount_total"])
    move["amount_residual"] = _decimal_string(move["amount_residual"])
    move["receivable_payable_lines"] = normalized_term_lines
    move["reconciliations"] = reconciliations
    move["payments"] = payments
    return {
        "user_id": env.uid,
        "company_visible": company_visible,
        "module_installed": module_installed,
        "access_allowed": access_allowed,
        "payment_status": move,
    }


def _payment_runtime_failure() -> RuntimeFailure:
    return RuntimeFailure(
        "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
    )


def _payment_search_payload_is_valid(payload: Any) -> bool:
    if not isinstance(payload, dict) or set(payload) != {
        "company_id",
        "after",
        "limit",
        "filters",
    }:
        return False
    if (
        not isinstance(payload["company_id"], int)
        or isinstance(payload["company_id"], bool)
        or payload["company_id"] <= 0
        or not isinstance(payload["limit"], int)
        or isinstance(payload["limit"], bool)
        or not 1 <= payload["limit"] <= 1001
    ):
        return False
    after = payload["after"]
    if after is not None and (
        not isinstance(after, list)
        or len(after) != 2
        or not _is_canonical_date(after[0])
        or not isinstance(after[1], int)
        or isinstance(after[1], bool)
        or after[1] <= 0
    ):
        return False
    filters = payload["filters"]
    if not isinstance(filters, dict) or set(filters) != {
        "date_from",
        "date_to",
        "states",
        "payment_types",
        "partner_types",
        "journal_id",
        "partner_id",
        "currency_id",
        "query",
    }:
        return False
    for field in ("date_from", "date_to"):
        if filters[field] is not None and not _is_canonical_date(filters[field]):
            return False
    if (
        filters["date_from"] is not None
        and filters["date_to"] is not None
        and filters["date_from"] > filters["date_to"]
    ):
        return False
    if not _invoice_choices_are_canonical(
        filters["states"], _PAYMENT_STATES
    ) or not _invoice_choices_are_canonical(
        filters["payment_types"], _PAYMENT_TYPES
    ) or not _invoice_choices_are_canonical(
        filters["partner_types"], _PAYMENT_PARTNER_TYPES
    ):
        return False
    for field in ("journal_id", "partner_id", "currency_id"):
        value = filters[field]
        if value is not None and (
            not isinstance(value, int) or isinstance(value, bool) or value <= 0
        ):
            return False
    query = filters["query"]
    return query is None or (
        isinstance(query, str)
        and query == query.strip()
        and 1 <= len(query) <= 200
    )


def _payment_get_payload_is_valid(payload: Any) -> bool:
    return (
        isinstance(payload, dict)
        and set(payload) == {"company_id", "payment_id"}
        and isinstance(payload["company_id"], int)
        and not isinstance(payload["company_id"], bool)
        and payload["company_id"] > 0
        and isinstance(payload["payment_id"], int)
        and not isinstance(payload["payment_id"], bool)
        and payload["payment_id"] > 0
    )


def _payment_gate(
    env: Any, company_id: int, required_models: tuple[str, ...]
) -> tuple[bool, bool, bool]:
    installed = {
        model_name: env.registry.get(model_name) is not None
        for model_name in required_models
    }
    company_read_allowed = bool(
        installed["res.company"] and env["res.company"].has_access("read")
    )
    company_visible = bool(
        company_read_allowed
        and env["res.company"].search_count([("id", "=", company_id)], limit=1)
    )
    module_installed = all(installed.values())
    access_allowed = bool(
        company_visible
        and module_installed
        and all(
            env[model_name].has_access("read")
            for model_name in required_models
            if model_name != "res.company"
        )
    )
    return company_visible, module_installed, access_allowed


def _empty_payment_result(
    env: Any,
    *,
    company_visible: bool,
    module_installed: bool,
    access_allowed: bool,
    result_key: str,
) -> dict[str, Any]:
    return {
        "user_id": env.uid,
        "company_visible": company_visible,
        "module_installed": module_installed,
        "access_allowed": access_allowed,
        result_key: [] if result_key == "rows" else None,
    }


def _payment_company_scope(env: Any, company_id: int) -> list[int]:
    rows = (
        env["res.company"]
        .with_context(active_test=False, allowed_company_ids=[company_id])
        .search_read(
            [("id", "=", company_id)],
            fields=["id", "parent_path"],
            limit=1,
            order="id",
        )
    )
    if (
        not isinstance(rows, list)
        or len(rows) != 1
        or not isinstance(rows[0], dict)
        or set(rows[0]) != {"id", "parent_path"}
        or rows[0].get("id") != company_id
    ):
        raise _payment_runtime_failure()
    return _payment_company_path(rows[0], company_id)


def _payment_company_path(row: dict[str, Any], company_id: int) -> list[int]:
    if set(row) != {"id", "parent_path"} or row.get("id") != company_id:
        raise _payment_runtime_failure()
    parent_path = row.get("parent_path")
    if not isinstance(parent_path, str) or not parent_path.endswith("/"):
        raise _payment_runtime_failure()
    parts = parent_path[:-1].split("/")
    if (
        not parts
        or any(not part.isdigit() or part.startswith("0") for part in parts)
    ):
        raise _payment_runtime_failure()
    scope = [int(part) for part in parts]
    if (
        any(value <= 0 for value in scope)
        or len(scope) != len(set(scope))
        or scope[-1] != company_id
    ):
        raise _payment_runtime_failure()
    return scope


def _payment_graph_scope(
    env: Any, company_id: int, available_company_ids: tuple[int, ...]
) -> list[int]:
    if (
        not available_company_ids
        or company_id not in available_company_ids
        or len(available_company_ids) != len(set(available_company_ids))
        or any(
            not isinstance(value, int)
            or isinstance(value, bool)
            or value <= 0
            for value in available_company_ids
        )
    ):
        raise _payment_runtime_failure()
    configured_ids = [
        company_id,
        *sorted(value for value in available_company_ids if value != company_id),
    ]
    rows = (
        env["res.company"]
        .with_context(
            active_test=False,
            allowed_company_ids=configured_ids,
        )
        .search_read(
            [("id", "in", configured_ids)],
            fields=["id", "parent_path"],
            limit=len(configured_ids),
            order="id",
        )
    )
    if not isinstance(rows, list):
        raise _payment_runtime_failure()
    paths: dict[int, list[int]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise _payment_runtime_failure()
        record_id = row.get("id")
        if (
            not isinstance(record_id, int)
            or isinstance(record_id, bool)
            or record_id not in available_company_ids
            or record_id in paths
        ):
            raise _payment_runtime_failure()
        paths[record_id] = _payment_company_path(row, record_id)
    if company_id not in paths:
        raise _payment_runtime_failure()
    root_company_id = paths[company_id][0]
    same_root_ids = sorted(
        record_id
        for record_id, path in paths.items()
        if path[0] == root_company_id
    )
    if company_id not in same_root_ids:
        raise _payment_runtime_failure()
    return [company_id, *(value for value in same_root_ids if value != company_id)]


def _payment_domain(
    company_id: int, after: list[Any] | None, filters: dict[str, Any]
) -> list[Any]:
    from odoo.fields import Domain

    domains: list[list[Any]] = [[("company_id", "=", company_id)]]
    for filter_name, model_field, operator in (
        ("date_from", "date", ">="),
        ("date_to", "date", "<="),
        ("states", "state", "in"),
        ("payment_types", "payment_type", "in"),
        ("partner_types", "partner_type", "in"),
        ("journal_id", "journal_id", "="),
        ("partner_id", "partner_id", "="),
        ("currency_id", "currency_id", "="),
    ):
        if filters[filter_name] not in (None, []):
            domains.append(
                [(model_field, operator, filters[filter_name])]
            )
    if filters["query"] is not None:
        domains.append(
            [
                "|",
                "|",
                ("name", "ilike", filters["query"]),
                ("memo", "ilike", filters["query"]),
                ("payment_reference", "ilike", filters["query"]),
            ]
        )
    if after is not None:
        domains.append(
            [
                "|",
                ("date", "<", after[0]),
                "&",
                ("date", "=", after[0]),
                ("id", "<", after[1]),
            ]
        )
    return list(Domain.AND(domains))


def _payment_read_index(
    env: Any,
    model_name: str,
    record_ids: set[int],
    domain: list[Any],
    fields: tuple[str, ...],
    company_id: int,
    *,
    allowed_company_ids: list[int] | None = None,
) -> dict[int, dict[str, Any]]:
    if not record_ids:
        return {}
    rows = (
        env[model_name]
        .with_context(
            active_test=False,
            allowed_company_ids=allowed_company_ids or [company_id],
        )
        .search_read(
            domain,
            fields=list(fields),
            limit=len(record_ids),
            order="id",
        )
    )
    result: dict[int, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != set(fields):
            raise _payment_runtime_failure()
        record_id = row.get("id")
        if (
            not isinstance(record_id, int)
            or isinstance(record_id, bool)
            or record_id not in record_ids
            or record_id in result
        ):
            raise _payment_runtime_failure()
        result[record_id] = row
    if set(result) != record_ids:
        raise _payment_runtime_failure()
    return result


def _payment_optional_text(value: Any) -> str | None:
    if value is False or value is None:
        return None
    if isinstance(value, str) and len(value) > 0:
        return value
    raise _payment_runtime_failure()


def _payment_required_text(value: Any) -> str:
    if isinstance(value, str) and len(value) > 0:
        return value
    raise _payment_runtime_failure()


def _payment_related(
    env: Any,
    raw_rows: list[dict[str, Any]],
    company_id: int,
    company_scope: list[int],
) -> dict[str, dict[int, dict[str, Any]]]:
    journal_ids: set[int] = set()
    currency_ids: set[int] = set()
    partner_ids: set[int] = set()
    method_line_ids: set[int] = set()
    move_ids: set[int] = set()
    for raw in raw_rows:
        if not isinstance(raw, dict) or set(raw) != set(_PAYMENT_FIELDS):
            raise _payment_runtime_failure()
        if _reference_id(raw.get("company_id")) != company_id:
            raise _payment_runtime_failure()
        journal_id = _reference_id(raw.get("journal_id"))
        currency_id = _reference_id(raw.get("currency_id"))
        company_currency_id = _reference_id(raw.get("company_currency_id"))
        method_line_id = _reference_id(raw.get("payment_method_line_id"))
        if (
            journal_id is None
            or currency_id is None
            or company_currency_id is None
            or method_line_id is None
        ):
            raise _payment_runtime_failure()
        journal_ids.add(journal_id)
        currency_ids.update((currency_id, company_currency_id))
        method_line_ids.add(method_line_id)
        partner_id = _reference_id(raw.get("partner_id"))
        if partner_id is not None:
            partner_ids.add(partner_id)
        move_id = _reference_id(raw.get("move_id"))
        if move_id is not None:
            move_ids.add(move_id)

    journals = _payment_read_index(
        env,
        "account.journal",
        journal_ids,
        [
            ("id", "in", sorted(journal_ids)),
            ("company_id", "in", company_scope),
        ],
        _PAYMENT_JOURNAL_FIELDS,
        company_id,
    )
    currencies = _payment_read_index(
        env,
        "res.currency",
        currency_ids,
        [("id", "in", sorted(currency_ids))],
        _PAYMENT_CURRENCY_FIELDS,
        company_id,
    )
    partners = _payment_read_index(
        env,
        "res.partner",
        partner_ids,
        [
            ("id", "in", sorted(partner_ids)),
            ("company_id", "in", [False, *company_scope]),
        ],
        _PAYMENT_PARTNER_FIELDS,
        company_id,
    )
    method_lines = _payment_read_index(
        env,
        "account.payment.method.line",
        method_line_ids,
        [
            ("id", "in", sorted(method_line_ids)),
            ("journal_id", "in", [False, *sorted(journal_ids)]),
        ],
        _PAYMENT_METHOD_LINE_FIELDS,
        company_id,
    )
    method_ids = {
        method_id
        for line in method_lines.values()
        if (method_id := _reference_id(line.get("payment_method_id"))) is not None
    }
    if len(method_ids) == 0 and method_line_ids:
        raise _payment_runtime_failure()
    methods = _payment_read_index(
        env,
        "account.payment.method",
        method_ids,
        [("id", "in", sorted(method_ids))],
        _PAYMENT_METHOD_FIELDS,
        company_id,
    )
    moves = _payment_read_index(
        env,
        "account.move",
        move_ids,
        [
            ("id", "in", sorted(move_ids)),
            ("company_id", "=", company_id),
        ],
        _PAYMENT_MOVE_FIELDS,
        company_id,
    )
    return {
        "journals": journals,
        "currencies": currencies,
        "partners": partners,
        "method_lines": method_lines,
        "methods": methods,
        "moves": moves,
    }


def _payment_common(
    raw: dict[str, Any],
    related: dict[str, dict[int, dict[str, Any]]],
    company_id: int,
    company_scope: list[int],
) -> dict[str, Any]:
    if set(raw) != set(_PAYMENT_FIELDS):
        raise _payment_runtime_failure()
    row = dict(raw)
    record_id = row.get("id")
    currency_id = _reference_id(row.pop("currency_id"))
    company_currency_id = _reference_id(row.pop("company_currency_id"))
    row_company_id = _reference_id(row.pop("company_id"))
    partner_id = _reference_id(row.pop("partner_id"))
    journal_id = _reference_id(row.pop("journal_id"))
    method_line_id = _reference_id(row.pop("payment_method_line_id"))
    move_id = _reference_id(row.pop("move_id"))
    if (
        not isinstance(record_id, int)
        or isinstance(record_id, bool)
        or record_id <= 0
        or row_company_id != company_id
        or currency_id is None
        or company_currency_id is None
        or journal_id is None
        or method_line_id is None
        or row.get("state") not in _PAYMENT_STATES
        or row.get("payment_type") not in _PAYMENT_TYPES
        or row.get("partner_type") not in _PAYMENT_PARTNER_TYPES
        or not isinstance(row.get("is_reconciled"), bool)
        or not isinstance(row.get("is_matched"), bool)
    ):
        raise _payment_runtime_failure()

    journal = related["journals"][journal_id]
    journal_company_id = _reference_id(journal.get("company_id"))
    journal_code = _payment_required_text(journal.get("code"))
    journal_name = _payment_required_text(journal.get("name"))
    if journal_company_id not in company_scope or len(journal_code) > 5:
        raise _payment_runtime_failure()

    currency = related["currencies"][currency_id]
    company_currency = related["currencies"][company_currency_id]
    currency_code = _payment_required_text(currency.get("name"))
    company_currency_code = _payment_required_text(company_currency.get("name"))
    if len(currency_code) > 3 or len(company_currency_code) > 3:
        raise _payment_runtime_failure()

    partner = None
    if partner_id is not None:
        partner_row = related["partners"][partner_id]
        partner_company_id = _reference_id(partner_row.get("company_id"))
        if partner_company_id is not None and partner_company_id not in company_scope:
            raise _payment_runtime_failure()
        partner = {
            "id": partner_id,
            "name": _payment_optional_text(partner_row.get("name")),
        }

    method_line = related["method_lines"][method_line_id]
    line_journal_id = _reference_id(method_line.get("journal_id"))
    method_id = _reference_id(method_line.get("payment_method_id"))
    if (
        method_id is None
        or (line_journal_id is not None and line_journal_id != journal_id)
    ):
        raise _payment_runtime_failure()
    method = related["methods"][method_id]
    method_code = _payment_required_text(method.get("code"))
    method_name = _payment_required_text(method.get("name"))
    if method.get("payment_type") != row["payment_type"]:
        raise _payment_runtime_failure()

    journal_entry = None
    if move_id is not None:
        move = related["moves"][move_id]
        if (
            _reference_id(move.get("company_id")) != company_id
            or move.get("move_type") != "entry"
            or move.get("state") not in _PAYMENT_DOCUMENT_STATES
        ):
            raise _payment_runtime_failure()
        journal_entry = {
            "id": move_id,
            "name": _payment_optional_text(move.get("name")),
            "state": move["state"],
            "date": _date_string(move.get("date")),
        }

    row["name"] = _payment_optional_text(row.get("name"))
    row["date"] = _date_string(row.get("date"))
    row["memo"] = _payment_optional_text(row.get("memo"))
    row["payment_reference"] = _payment_optional_text(
        row.get("payment_reference")
    )
    amount = _decimal_string(row.get("amount"))
    amount_signed = _decimal_string(row.get("amount_signed"))
    company_signed = _decimal_string(row.get("amount_company_currency_signed"))
    amount_decimal = Decimal(amount)
    signed_decimal = Decimal(amount_signed)
    expected_signed = (
        amount_decimal if row["payment_type"] == "inbound" else -amount_decimal
    )
    if (
        amount_decimal < 0
        or signed_decimal != expected_signed
    ):
        raise _payment_runtime_failure()
    row["amount"] = amount
    row["amount_signed"] = amount_signed
    row["amount_company_currency_signed"] = company_signed
    row["currency"] = {"id": currency_id, "code": currency_code}
    row["company_currency"] = {
        "id": company_currency_id,
        "code": company_currency_code,
    }
    row["company_id"] = company_id
    row["partner"] = partner
    row["journal"] = {
        "id": journal_id,
        "code": journal_code,
        "name": journal_name,
    }
    row["payment_method_line"] = {
        "id": method_line_id,
        "name": _payment_optional_text(method_line.get("name")),
        "journal_id": line_journal_id,
    }
    row["payment_method"] = {
        "id": method_id,
        "code": method_code,
        "name": method_name,
        "payment_type": method["payment_type"],
    }
    row["move_id"] = move_id
    row["journal_entry"] = journal_entry
    return row


def _dispatch_payment_search(
    env: Any, payload: dict[str, Any], company_id: int
) -> dict[str, Any]:
    if not _payment_search_payload_is_valid(payload):
        raise RuntimeFailure(
            "bridge_protocol_error", "The bridge action payload is invalid.", exit_code=7
        )
    if payload["company_id"] != company_id:
        raise RuntimeFailure(
            "company_unavailable", "The company is unavailable.", exit_code=3
        )
    company_visible, module_installed, access_allowed = _payment_gate(
        env, company_id, _PAYMENT_SEARCH_MODELS
    )
    if not access_allowed:
        return _empty_payment_result(
            env,
            company_visible=company_visible,
            module_installed=module_installed,
            access_allowed=access_allowed,
            result_key="rows",
        )
    company_scope = _payment_company_scope(env, company_id)
    raw_rows = (
        env["account.payment"]
        .with_context(active_test=False, allowed_company_ids=[company_id])
        .search_read(
            _payment_domain(company_id, payload["after"], payload["filters"]),
            fields=list(_PAYMENT_FIELDS),
            limit=payload["limit"],
            order="date desc,id desc",
        )
    )
    if not isinstance(raw_rows, list):
        raise _payment_runtime_failure()
    related = _payment_related(env, raw_rows, company_id, company_scope)
    rows: list[dict[str, Any]] = []
    previous = tuple(payload["after"]) if payload["after"] is not None else None
    observed_ids: set[int] = set()
    for raw in raw_rows:
        row = _payment_common(raw, related, company_id, company_scope)
        current = (row["date"], row["id"])
        if row["id"] in observed_ids or (previous is not None and current >= previous):
            raise _payment_runtime_failure()
        observed_ids.add(row["id"])
        previous = current
        row.pop("journal_entry")
        rows.append(row)
    return {
        "user_id": env.uid,
        "company_visible": company_visible,
        "module_installed": module_installed,
        "access_allowed": access_allowed,
        "rows": rows,
    }


def _payment_document(
    raw: dict[str, Any], *, record_id: int, graph_scope: list[int]
) -> dict[str, Any]:
    if (
        set(raw) != set(_PAYMENT_MOVE_FIELDS)
        or raw.get("id") != record_id
        or _reference_id(raw.get("company_id")) not in graph_scope
        or raw.get("move_type") not in _PAYMENT_DOCUMENT_TYPES
        or raw.get("state") not in _PAYMENT_DOCUMENT_STATES
        or raw.get("payment_state") not in _PAYMENT_DOCUMENT_PAYMENT_STATES
    ):
        raise _payment_runtime_failure()
    _date_string(raw.get("date"))
    return {
        "id": record_id,
        "name": _payment_optional_text(raw.get("name")),
        "move_type": raw["move_type"],
        "state": raw["state"],
        "payment_state": raw["payment_state"],
        "company_id": _reference_id(raw.get("company_id")),
    }


def _payment_read_documents(
    env: Any,
    record_ids: set[int],
    company_id: int,
    graph_scope: list[int],
) -> list[dict[str, Any]]:
    rows = _payment_read_index(
        env,
        "account.move",
        record_ids,
        [
            ("id", "in", sorted(record_ids)),
            ("company_id", "in", graph_scope),
            ("move_type", "in", list(_PAYMENT_DOCUMENT_TYPES)),
        ],
        _PAYMENT_MOVE_FIELDS,
        company_id,
        allowed_company_ids=graph_scope,
    )
    return [
        _payment_document(
            rows[record_id], record_id=record_id, graph_scope=graph_scope
        )
        for record_id in sorted(rows)
    ]


def _payment_read_direct_documents(
    env: Any,
    record_ids: set[int],
    company_id: int,
    graph_scope: list[int],
) -> list[dict[str, Any]]:
    rows = _payment_read_index(
        env,
        "account.move",
        record_ids,
        [
            ("id", "in", sorted(record_ids)),
            ("company_id", "in", graph_scope),
        ],
        _PAYMENT_MOVE_FIELDS,
        company_id,
        allowed_company_ids=graph_scope,
    )
    document_ids: set[int] = set()
    for record_id, row in rows.items():
        if (
            _reference_id(row.get("company_id")) not in graph_scope
            or row.get("state") not in _PAYMENT_DOCUMENT_STATES
            or not isinstance(row.get("move_type"), str)
            or not row["move_type"]
        ):
            raise _payment_runtime_failure()
        _payment_optional_text(row.get("name"))
        _date_string(row.get("date"))
        if row["move_type"] in _PAYMENT_DOCUMENT_TYPES:
            document_ids.add(record_id)
    return [
        _payment_document(
            rows[record_id], record_id=record_id, graph_scope=graph_scope
        )
        for record_id in sorted(document_ids)
    ]


def _payment_reconciled_documents(
    env: Any,
    *,
    payment_move_id: int | None,
    company_id: int,
    company_scope: list[int],
    graph_scope: list[int],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if payment_move_id is None:
        return [], []
    payment_lines = (
        env["account.move.line"]
        .with_context(active_test=False, allowed_company_ids=[company_id])
        .search_read(
            [
                ("move_id", "=", payment_move_id),
                ("company_id", "=", company_id),
                (
                    "account_id.account_type",
                    "in",
                    ["asset_receivable", "liability_payable"],
                ),
            ],
            fields=list(_PAYMENT_MOVE_LINE_FIELDS),
            order="id",
        )
    )
    payment_line_accounts: dict[int, int] = {}
    account_ids: set[int] = set()
    for line in payment_lines:
        if not isinstance(line, dict) or set(line) != set(_PAYMENT_MOVE_LINE_FIELDS):
            raise _payment_runtime_failure()
        line_id = line.get("id")
        account_id = _reference_id(line.get("account_id"))
        if (
            not isinstance(line_id, int)
            or isinstance(line_id, bool)
            or line_id <= 0
            or line_id in payment_line_accounts
            or _reference_id(line.get("move_id")) != payment_move_id
            or _reference_id(line.get("company_id")) != company_id
            or account_id is None
        ):
            raise _payment_runtime_failure()
        payment_line_accounts[line_id] = account_id
        account_ids.add(account_id)
    if not payment_line_accounts:
        return [], []

    accounts = _payment_read_index(
        env,
        "account.account",
        account_ids,
        [
            ("id", "in", sorted(account_ids)),
            ("company_ids", "in", company_scope),
        ],
        _PAYMENT_ACCOUNT_FIELDS,
        company_id,
    )
    for account in accounts.values():
        if (
            account.get("account_type")
            not in {"asset_receivable", "liability_payable"}
            or account.get("reconcile") is not True
        ):
            raise _payment_runtime_failure()

    payment_line_ids = set(payment_line_accounts)
    partials = (
        env["account.partial.reconcile"]
        .with_context(active_test=False, allowed_company_ids=graph_scope)
        .search_read(
            [
                ("company_id", "in", graph_scope),
                "|",
                ("debit_move_id", "in", sorted(payment_line_ids)),
                ("credit_move_id", "in", sorted(payment_line_ids)),
            ],
            fields=list(_PAYMENT_PARTIAL_FIELDS),
            order="id",
        )
    )
    counterpart_accounts: dict[int, int] = {}
    observed_partial_ids: set[int] = set()
    for partial in partials:
        if not isinstance(partial, dict) or set(partial) != set(
            _PAYMENT_PARTIAL_FIELDS
        ):
            raise _payment_runtime_failure()
        partial_id = partial.get("id")
        debit_line_id = _reference_id(partial.get("debit_move_id"))
        credit_line_id = _reference_id(partial.get("credit_move_id"))
        debit_is_payment = debit_line_id in payment_line_ids
        credit_is_payment = credit_line_id in payment_line_ids
        _reference_id(partial.get("exchange_move_id"))
        if (
            not isinstance(partial_id, int)
            or isinstance(partial_id, bool)
            or partial_id <= 0
            or partial_id in observed_partial_ids
            or _reference_id(partial.get("company_id")) not in graph_scope
            or not (debit_is_payment or credit_is_payment)
        ):
            raise _payment_runtime_failure()
        observed_partial_ids.add(partial_id)
        if debit_is_payment and credit_is_payment:
            if (
                debit_line_id == credit_line_id
                or payment_line_accounts[debit_line_id]
                != payment_line_accounts[credit_line_id]
            ):
                raise _payment_runtime_failure()
            continue
        payment_line_id = debit_line_id if debit_is_payment else credit_line_id
        counterpart_line_id = credit_line_id if debit_is_payment else debit_line_id
        if payment_line_id is None or counterpart_line_id is None:
            raise _payment_runtime_failure()
        expected_account_id = payment_line_accounts[payment_line_id]
        previous_account_id = counterpart_accounts.setdefault(
            counterpart_line_id, expected_account_id
        )
        if previous_account_id != expected_account_id:
            raise _payment_runtime_failure()

    counterpart_line_ids = set(counterpart_accounts)
    counterpart_lines = _payment_read_index(
        env,
        "account.move.line",
        counterpart_line_ids,
        [
            ("id", "in", sorted(counterpart_line_ids)),
            ("company_id", "in", graph_scope),
        ],
        _PAYMENT_MOVE_LINE_FIELDS,
        company_id,
        allowed_company_ids=graph_scope,
    )
    counterpart_move_ids: set[int] = set()
    counterpart_line_companies: dict[int, int] = {}
    counterpart_line_moves: dict[int, int] = {}
    for line_id, line in counterpart_lines.items():
        move_id = _reference_id(line.get("move_id"))
        account_id = _reference_id(line.get("account_id"))
        line_company_id = _reference_id(line.get("company_id"))
        if (
            move_id is None
            or account_id != counterpart_accounts[line_id]
            or line_company_id not in graph_scope
        ):
            raise _payment_runtime_failure()
        counterpart_move_ids.add(move_id)
        counterpart_line_companies[line_id] = line_company_id
        counterpart_line_moves[line_id] = move_id

    counterpart_moves = _payment_read_index(
        env,
        "account.move",
        counterpart_move_ids,
        [
            ("id", "in", sorted(counterpart_move_ids)),
            ("company_id", "in", graph_scope),
        ],
        _PAYMENT_MOVE_FIELDS,
        company_id,
        allowed_company_ids=graph_scope,
    )
    for line_id, move_id in counterpart_line_moves.items():
        if _reference_id(counterpart_moves[move_id].get("company_id")) != (
            counterpart_line_companies[line_id]
        ):
            raise _payment_runtime_failure()
    document_ids: set[int] = set()
    for move_id, move in counterpart_moves.items():
        if (
            _reference_id(move.get("company_id")) not in graph_scope
            or move.get("state") not in _PAYMENT_DOCUMENT_STATES
            or not isinstance(move.get("move_type"), str)
            or not move["move_type"]
        ):
            raise _payment_runtime_failure()
        _payment_optional_text(move.get("name"))
        _date_string(move.get("date"))
        if move["move_type"] in _PAYMENT_DOCUMENT_TYPES:
            document_ids.add(move_id)

    documents = _payment_read_documents(
        env, document_ids, company_id, graph_scope
    )
    invoices = [
        document
        for document in documents
        if document["move_type"] in _PAYMENT_SALE_DOCUMENT_TYPES
    ]
    bills = [
        document
        for document in documents
        if document["move_type"] in _PAYMENT_PURCHASE_DOCUMENT_TYPES
    ]
    return invoices, bills


def _dispatch_payment_get(
    env: Any,
    payload: dict[str, Any],
    company_id: int,
    available_company_ids: tuple[int, ...],
) -> dict[str, Any]:
    if not _payment_get_payload_is_valid(payload):
        raise RuntimeFailure(
            "bridge_protocol_error", "The bridge action payload is invalid.", exit_code=7
        )
    if payload["company_id"] != company_id:
        raise RuntimeFailure(
            "company_unavailable", "The company is unavailable.", exit_code=3
        )
    company_visible, module_installed, access_allowed = _payment_gate(
        env, company_id, _PAYMENT_GET_MODELS
    )
    if not access_allowed:
        return _empty_payment_result(
            env,
            company_visible=company_visible,
            module_installed=module_installed,
            access_allowed=access_allowed,
            result_key="payment",
        )
    company_scope = _payment_company_scope(env, company_id)
    graph_scope = _payment_graph_scope(
        env, company_id, available_company_ids
    )
    fields = [*_PAYMENT_FIELDS, "invoice_ids"]
    rows = (
        env["account.payment"]
        .with_context(active_test=False, allowed_company_ids=graph_scope)
        .search_read(
            [
                ("id", "=", payload["payment_id"]),
                ("company_id", "=", company_id),
            ],
            fields=fields,
            limit=1,
            order="id",
        )
    )
    if not rows:
        return _empty_payment_result(
            env,
            company_visible=company_visible,
            module_installed=module_installed,
            access_allowed=access_allowed,
            result_key="payment",
        )
    if (
        not isinstance(rows, list)
        or len(rows) != 1
        or not isinstance(rows[0], dict)
        or set(rows[0]) != set(fields)
    ):
        raise _payment_runtime_failure()
    raw = dict(rows[0])
    invoice_ids = set(_many2many_ids(raw.pop("invoice_ids")))
    related = _payment_related(env, [raw], company_id, company_scope)
    payment = _payment_common(raw, related, company_id, company_scope)
    if payment["id"] != payload["payment_id"]:
        raise _payment_runtime_failure()
    direct_documents = _payment_read_direct_documents(
        env, invoice_ids, company_id, graph_scope
    )
    reconciled_invoices, reconciled_bills = _payment_reconciled_documents(
        env,
        payment_move_id=payment["move_id"],
        company_id=company_id,
        company_scope=company_scope,
        graph_scope=graph_scope,
    )
    payment["invoice_ids"] = direct_documents
    payment["reconciled_invoices"] = reconciled_invoices
    payment["reconciled_bills"] = reconciled_bills
    return {
        "user_id": env.uid,
        "company_visible": company_visible,
        "module_installed": module_installed,
        "access_allowed": access_allowed,
        "payment": payment,
    }


def _open_item_payload_is_valid(payload: Any) -> bool:
    if not isinstance(payload, dict) or set(payload) != {
        "company_id",
        "after",
        "limit",
        "filters",
    }:
        return False
    if (
        not isinstance(payload["company_id"], int)
        or isinstance(payload["company_id"], bool)
        or payload["company_id"] <= 0
        or not isinstance(payload["limit"], int)
        or isinstance(payload["limit"], bool)
        or not 1 <= payload["limit"] <= 1001
    ):
        return False
    after = payload["after"]
    if after is not None and (
        not isinstance(after, list)
        or len(after) != 2
        or not _is_canonical_date(after[0])
        or not isinstance(after[1], int)
        or isinstance(after[1], bool)
        or after[1] <= 0
    ):
        return False
    filters = payload["filters"]
    if not isinstance(filters, dict) or set(filters) != {
        "date_from",
        "date_to",
        "due_date_from",
        "due_date_to",
        "partner_id",
        "account_id",
        "journal_id",
        "currency_id",
        "query",
    }:
        return False
    for field in ("date_from", "date_to", "due_date_from", "due_date_to"):
        if filters[field] is not None and not _is_canonical_date(filters[field]):
            return False
    if (
        filters["date_from"] is not None
        and filters["date_to"] is not None
        and filters["date_from"] > filters["date_to"]
    ) or (
        filters["due_date_from"] is not None
        and filters["due_date_to"] is not None
        and filters["due_date_from"] > filters["due_date_to"]
    ):
        return False
    for field in ("partner_id", "account_id", "journal_id", "currency_id"):
        value = filters[field]
        if value is not None and (
            not isinstance(value, int) or isinstance(value, bool) or value <= 0
        ):
            return False
    query = filters["query"]
    return query is None or (
        isinstance(query, str)
        and query == query.strip()
        and 1 <= len(query) <= 200
    )


def _open_item_gate(env: Any, company_id: int) -> tuple[bool, bool, bool]:
    company_installed = env.registry.get("res.company") is not None
    company_read_allowed = bool(
        company_installed and env["res.company"].has_access("read")
    )
    company_visible = bool(
        company_read_allowed
        and env["res.company"].search_count([("id", "=", company_id)], limit=1)
    )
    module_installed = all(
        env.registry.get(model_name) is not None
        for model_name in _OPEN_ITEM_MODELS
    )
    access_allowed = bool(
        company_visible
        and module_installed
        and all(env[model_name].has_access("read") for model_name in _OPEN_ITEM_MODELS)
    )
    return company_visible, module_installed, access_allowed


def _open_item_domain(
    company_id: int,
    account_type: str,
    after: list[Any] | None,
    filters: dict[str, Any],
) -> list[Any]:
    from odoo.fields import Domain

    domains: list[list[Any]] = [
        [
            ("company_id", "=", company_id),
            ("parent_state", "=", "posted"),
            ("account_type", "=", account_type),
            ("account_id.reconcile", "=", True),
            ("reconciled", "=", False),
        ]
    ]
    for filter_name, model_field, operator in (
        ("date_from", "date", ">="),
        ("date_to", "date", "<="),
        ("due_date_from", "date_maturity", ">="),
        ("due_date_to", "date_maturity", "<="),
        ("partner_id", "partner_id", "="),
        ("account_id", "account_id", "="),
        ("journal_id", "journal_id", "="),
        ("currency_id", "currency_id", "="),
    ):
        if filters[filter_name] is not None:
            domains.append([(model_field, operator, filters[filter_name])])
    if filters["query"] is not None:
        domains.append(
            list(
                Domain.OR(
                    [
                        [("move_id.name", "ilike", filters["query"])],
                        [("ref", "ilike", filters["query"])],
                        [("name", "ilike", filters["query"])],
                        [("partner_id.name", "ilike", filters["query"])],
                    ]
                )
            )
        )
    if after is not None:
        domains.append(
            [
                "|",
                ("date", "<", after[0]),
                "&",
                ("date", "=", after[0]),
                ("id", "<", after[1]),
            ]
        )
    return list(Domain.AND(domains))


def _open_item_related(
    env: Any, rows: list[dict[str, Any]], company_id: int
) -> dict[str, dict[int, dict[str, Any]]]:
    def ids(field: str) -> set[int]:
        return {
            record_id
            for row in rows
            if (record_id := _reference_id(row.get(field))) is not None
        }

    currency_ids = ids("currency_id") | ids("company_currency_id")
    return {
        "moves": _related_rows(
            env,
            "account.move",
            ids("move_id"),
            ("name", "move_type", "state", "company_id"),
            company_id,
        ),
        "journals": _related_rows(
            env,
            "account.journal",
            ids("journal_id"),
            ("code", "name", "company_id"),
            company_id,
        ),
        "partners": _related_rows(
            env,
            "res.partner",
            ids("partner_id"),
            ("complete_name", "ref", "company_id"),
            company_id,
        ),
        "accounts": _related_rows(
            env,
            "account.account",
            ids("account_id"),
            (
                "code",
                "name",
                "account_type",
                "non_trade",
                "reconcile",
                "company_ids",
            ),
            company_id,
        ),
        "currencies": _related_rows(
            env,
            "res.currency",
            currency_ids,
            ("name",),
            company_id,
        ),
    }


def _open_item_runtime_failure() -> RuntimeFailure:
    return RuntimeFailure(
        "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
    )


def _open_item_optional_text(value: Any) -> str | None:
    if value in (False, None, ""):
        return None
    if isinstance(value, str):
        return value
    raise _open_item_runtime_failure()


def _open_item_required_text(value: Any) -> str:
    if isinstance(value, str) and value:
        return value
    raise _open_item_runtime_failure()


def _open_item_company_scope(env: Any, company_id: int) -> set[int]:
    rows = (
        env["res.company"]
        .with_context(active_test=False, allowed_company_ids=[company_id])
        .search_read(
            [("id", "=", company_id)],
            fields=["id", "parent_path"],
            limit=1,
            order="id",
        )
    )
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise _open_item_runtime_failure()
    row = rows[0]
    if set(row) != {"id", "parent_path"} or row["id"] != company_id:
        raise _open_item_runtime_failure()
    parent_path = row["parent_path"]
    if not isinstance(parent_path, str) or not parent_path.endswith("/"):
        raise _open_item_runtime_failure()
    parts = parent_path[:-1].split("/")
    try:
        company_scope = {int(part) for part in parts}
    except (TypeError, ValueError) as exc:
        raise _open_item_runtime_failure() from exc
    if (
        not parts
        or any(not part.isdigit() or part.startswith("0") for part in parts)
        or len(company_scope) != len(parts)
        or any(value <= 0 for value in company_scope)
        or int(parts[-1]) != company_id
    ):
        raise _open_item_runtime_failure()
    return company_scope


def _open_item_journal_reference(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "code": _open_item_required_text(row.get("code")),
        "name": _open_item_required_text(row.get("name")),
    }


def _open_item_account_reference(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "code": _open_item_required_text(row.get("code")),
        "name": _open_item_required_text(row.get("name")),
    }


def _open_item_currency_reference(row: dict[str, Any]) -> dict[str, Any]:
    code = _open_item_required_text(row.get("name"))
    if len(code) > 3:
        raise _open_item_runtime_failure()
    return {"id": row["id"], "code": code}


def _dispatch_open_item_search(
    env: Any, action: str, payload: dict[str, Any], company_id: int
) -> dict[str, Any]:
    if not _open_item_payload_is_valid(payload):
        raise RuntimeFailure(
            "bridge_protocol_error",
            "The bridge action payload is invalid.",
            exit_code=7,
        )
    if payload["company_id"] != company_id:
        raise RuntimeFailure(
            "company_unavailable", "The company is unavailable.", exit_code=3
        )
    side, account_type = _OPEN_ITEM_ACTION_SIDES[action]
    company_visible, module_installed, access_allowed = _open_item_gate(
        env, company_id
    )
    if not access_allowed:
        return {
            "user_id": env.uid,
            "company_visible": company_visible,
            "module_installed": module_installed,
            "access_allowed": access_allowed,
            "rows": [],
        }
    company_scope = _open_item_company_scope(env, company_id)
    raw_rows = (
        env["account.move.line"]
        .with_context(active_test=False, allowed_company_ids=[company_id])
        .search_read(
            _open_item_domain(
                company_id, account_type, payload["after"], payload["filters"]
            ),
            fields=list(_OPEN_ITEM_FIELDS),
            limit=payload["limit"],
            order="date desc,id desc",
        )
    )
    related = _open_item_related(env, raw_rows, company_id)
    normalized: list[dict[str, Any]] = []
    observed_ids: set[int] = set()
    allowed_move_types = {
        "entry",
        "out_invoice",
        "out_refund",
        "in_invoice",
        "in_refund",
        "out_receipt",
        "in_receipt",
    }
    for raw in raw_rows:
        if not isinstance(raw, dict) or set(raw) != set(_OPEN_ITEM_FIELDS):
            raise _open_item_runtime_failure()
        row = dict(raw)
        record_id = row.get("id")
        if (
            not isinstance(record_id, int)
            or isinstance(record_id, bool)
            or record_id <= 0
            or record_id in observed_ids
        ):
            raise _open_item_runtime_failure()
        observed_ids.add(record_id)
        move_id = _reference_id(row.pop("move_id"))
        journal_id = _reference_id(row.pop("journal_id"))
        row_company_id = _reference_id(row.pop("company_id"))
        partner_id = _reference_id(row.pop("partner_id"))
        account_id = _reference_id(row.pop("account_id"))
        currency_id = _reference_id(row.pop("currency_id"))
        company_currency_id = _reference_id(row.pop("company_currency_id"))
        if (
            row_company_id != company_id
            or move_id is None
            or journal_id is None
            or account_id is None
            or currency_id is None
            or company_currency_id is None
            or row.pop("parent_state") != "posted"
            or row.pop("account_type") != account_type
            or row.get("reconciled") is not False
        ):
            raise _open_item_runtime_failure()

        move = _safe_related(related, "moves", move_id)
        journal = _safe_related(related, "journals", journal_id)
        account = _safe_related(related, "accounts", account_id)
        currency = _safe_related(related, "currencies", currency_id)
        company_currency = _safe_related(
            related, "currencies", company_currency_id
        )
        move_company_id = _reference_id(move.get("company_id"))
        journal_company_id = _reference_id(journal.get("company_id"))
        account_company_ids = account.get("company_ids")
        if (
            move_company_id != company_id
            or journal_company_id not in company_scope
            or not isinstance(move.get("name"), str)
            or not move["name"]
            or move.get("move_type") not in allowed_move_types
            or move.get("state") != "posted"
            or not isinstance(account_company_ids, list)
            or any(
                not isinstance(value, int)
                or isinstance(value, bool)
                or value <= 0
                for value in account_company_ids
            )
            or not company_scope.intersection(account_company_ids)
            or account.get("account_type") != account_type
            or account.get("reconcile") is not True
            or not isinstance(account.get("non_trade"), bool)
        ):
            raise _open_item_runtime_failure()

        partner = None
        if partner_id is not None:
            partner_row = _safe_related(related, "partners", partner_id)
            partner_company_id = _reference_id(partner_row.get("company_id"))
            if partner_company_id is not None and partner_company_id not in company_scope:
                raise _open_item_runtime_failure()
            partner = {
                "id": partner_id,
                "name": _open_item_optional_text(
                    partner_row.get("complete_name")
                ),
                "reference": _open_item_optional_text(partner_row.get("ref")),
            }

        row["side"] = side
        row["date"] = _date_string(row["date"])
        row["due_date"] = (
            None
            if row.pop("date_maturity") in (False, None)
            else _date_string(raw["date_maturity"])
        )
        row["name"] = _open_item_optional_text(row["name"])
        row["ref"] = _open_item_optional_text(row["ref"])
        row["matching_number"] = _open_item_optional_text(
            row["matching_number"]
        )
        row["move"] = {
            "id": move_id,
            "name": move["name"],
            "move_type": move["move_type"],
            "state": move["state"],
        }
        row["journal"] = _open_item_journal_reference(journal)
        row["company_id"] = company_id
        row["partner"] = partner
        row["account"] = {
            **_open_item_account_reference(account),
            "account_type": account["account_type"],
            "non_trade": account["non_trade"],
        }
        row["currency"] = _open_item_currency_reference(currency)
        row["company_currency"] = _open_item_currency_reference(company_currency)
        raw_amounts = {
            field: row[field]
            for field in (
                "debit",
                "credit",
                "balance",
                "amount_currency",
                "amount_residual",
                "amount_residual_currency",
            )
        }
        try:
            balanced = (
                Decimal(str(raw_amounts["debit"]))
                - Decimal(str(raw_amounts["credit"]))
                == Decimal(str(raw_amounts["balance"]))
            )
        except (ArithmeticError, TypeError, ValueError) as exc:
            raise _open_item_runtime_failure() from exc
        if not balanced:
            raise _open_item_runtime_failure()
        for field, value in raw_amounts.items():
            row[field] = _decimal_string(value)
        normalized.append(row)
    return {
        "user_id": env.uid,
        "company_visible": company_visible,
        "module_installed": module_installed,
        "access_allowed": access_allowed,
        "rows": normalized,
    }


def _partner_accounting_payload_is_valid(payload: Any, company_id: int) -> bool:
    if not isinstance(payload, dict) or set(payload) != {
        "company_id",
        "after",
        "limit",
        "filters",
    }:
        return False
    if (
        not isinstance(payload["company_id"], int)
        or isinstance(payload["company_id"], bool)
        or not isinstance(payload["limit"], int)
        or isinstance(payload["limit"], bool)
        or not 1 <= payload["limit"] <= 1001
    ):
        return False
    after = payload["after"]
    if after is not None and (
        not isinstance(after, list)
        or len(after) != 2
        or not isinstance(after[0], str)
        or not after[0]
        or not isinstance(after[1], int)
        or isinstance(after[1], bool)
        or after[1] <= 0
    ):
        return False
    filters = payload["filters"]
    if not isinstance(filters, dict) or set(filters) != {"role", "query"}:
        return False
    query = filters["query"]
    return filters["role"] in {"both", "customer", "vendor"} and (
        query is None
        or (
            isinstance(query, str)
            and query == query.strip()
            and 1 <= len(query) <= 200
        )
    )


def _partner_accounting_domain(
    company_id: int, after: list[Any] | None, filters: dict[str, Any]
) -> list[Any]:
    company_domain: list[Any] = [
        "|",
        ("company_id", "=", False),
        ("company_id", "=", company_id),
    ]
    role = filters["role"]
    if role == "customer":
        role_domain: list[Any] = [("customer_rank", ">", 0)]
    elif role == "vendor":
        role_domain = [("supplier_rank", ">", 0)]
    else:
        role_domain = [
            "|",
            ("customer_rank", ">", 0),
            ("supplier_rank", ">", 0),
        ]
    domains: list[list[Any]] = [company_domain, role_domain]
    if filters["query"] is not None:
        domains.append(
            [
                "|",
                ("complete_name", "ilike", filters["query"]),
                ("ref", "ilike", filters["query"]),
            ]
        )
    if after is not None:
        domains.append(
            [
                "|",
                ("complete_name", ">", after[0]),
                "&",
                ("complete_name", "=", after[0]),
                ("id", ">", after[1]),
            ]
        )
    from odoo.osv import expression

    return expression.AND(domains)


def _dispatch_partner_accounting_search(
    env: Any, payload: dict[str, Any], company_id: int
) -> dict[str, Any]:
    if not _partner_accounting_payload_is_valid(payload, company_id):
        raise RuntimeFailure(
            "bridge_protocol_error",
            "The bridge action payload is invalid.",
            exit_code=7,
        )
    if payload["company_id"] != company_id:
        raise RuntimeFailure(
            "company_unavailable", "The company is unavailable.", exit_code=3
        )
    company_visible = bool(
        env["res.company"].search_count([("id", "=", company_id)], limit=1)
    )
    required_models = ("res.partner", "account.account")
    module_installed = all(env.registry.get(name) is not None for name in required_models)
    access_allowed = bool(
        company_visible
        and module_installed
        and all(env[name].has_access("read") for name in required_models)
    )
    if not access_allowed:
        return {
            "user_id": env.uid,
            "company_visible": company_visible,
            "module_installed": module_installed,
            "access_allowed": access_allowed,
            "rows": [],
        }
    rows = (
        env["res.partner"]
        .with_context(active_test=False, allowed_company_ids=[company_id])
        .search_read(
            _partner_accounting_domain(company_id, payload["after"], payload["filters"]),
            fields=[
                "id",
                "complete_name",
                "ref",
                "active",
                "is_company",
                "company_id",
                "customer_rank",
                "supplier_rank",
                "property_account_receivable_id",
                "property_account_payable_id",
            ],
            limit=payload["limit"],
            order="complete_name,id",
        )
    )
    account_ids = {
        account_id
        for row in rows
        for key in (
            "property_account_receivable_id",
            "property_account_payable_id",
        )
        if (account_id := _reference_id(row.get(key))) is not None
    }
    accounts = _related_rows(
        env, "account.account", account_ids, ("code", "name"), company_id
    )
    normalized: list[dict[str, Any]] = []
    for raw in rows:
        row = dict(raw)
        receivable_id = _reference_id(row.pop("property_account_receivable_id"))
        payable_id = _reference_id(row.pop("property_account_payable_id"))
        row["company_id"] = _reference_id(row["company_id"])
        row["ref"] = _optional_string(row["ref"])
        row["receivable_account"] = (
            _account_reference(accounts[receivable_id])
            if receivable_id is not None and receivable_id in accounts
            else None
        )
        row["payable_account"] = (
            _account_reference(accounts[payable_id])
            if payable_id is not None and payable_id in accounts
            else None
        )
        normalized.append(row)
    return {
        "user_id": env.uid,
        "company_visible": company_visible,
        "module_installed": module_installed,
        "access_allowed": access_allowed,
        "rows": normalized,
    }


def _empty_financial_report_page(
    env: Any,
    *,
    company_visible: bool,
    module_installed: bool,
    access_allowed: bool,
) -> dict[str, Any]:
    return {
        "user_id": env.uid,
        "company_visible": company_visible,
        "module_installed": module_installed,
        "access_allowed": access_allowed,
        "cursor_found": True,
        "report": {},
        "date": {},
        "currency": {},
        "basis": "",
        "columns": [],
        "lines": [],
    }


def _dispatch_financial_report(
    env: Any, action: str, payload: dict[str, Any], company_id: int
) -> dict[str, Any]:
    spec = _FINANCIAL_REPORT_ACTIONS[action]
    _require_keys(
        payload,
        {"company_id", "date_from", "date_to", "after_line_id", "limit"},
    )
    limit = payload["limit"]
    after_line_id = payload["after_line_id"]
    if (
        not isinstance(payload["company_id"], int)
        or isinstance(payload["company_id"], bool)
        or not (
            (_is_canonical_date(payload["date_from"]) and spec["mode"] == "range")
            or (payload["date_from"] is None and spec["mode"] == "single")
        )
        or not _is_canonical_date(payload["date_to"])
        or (
            payload["date_from"] is not None
            and payload["date_from"] > payload["date_to"]
        )
        or not isinstance(limit, int)
        or isinstance(limit, bool)
        or not 1 <= limit <= 1001
        or not (
            after_line_id is None
            or (isinstance(after_line_id, str) and bool(after_line_id.strip()))
        )
    ):
        raise RuntimeFailure(
            "bridge_protocol_error", "The bridge action payload is invalid.", exit_code=7
        )
    if payload["company_id"] != company_id:
        raise RuntimeFailure(
            "company_unavailable", "The company is unavailable.", exit_code=3
        )

    company_model = env["res.company"]
    company_visible = bool(
        company_model.search_count([("id", "=", company_id)], limit=1)
    )
    required_models = ("account.report", "account.move.line", "res.currency")
    models_installed = all(
        env.registry.get(model_name) is not None for model_name in required_models
    )
    root_report = (
        env.ref(spec["xml_id"], raise_if_not_found=False)
        if models_installed
        else None
    )
    module_installed = bool(models_installed and root_report)
    access_allowed = bool(
        company_visible
        and module_installed
        and company_model.has_access("read")
        and all(env[model_name].has_access("read") for model_name in required_models)
    )
    if not access_allowed:
        return _empty_financial_report_page(
            env,
            company_visible=company_visible,
            module_installed=module_installed,
            access_allowed=access_allowed,
        )

    previous_options = {
        "all_entries": False,
        "date": {
            "date_from": payload["date_from"] or False,
            "date_to": payload["date_to"],
            "mode": spec["mode"],
            "filter": "custom",
        },
    }
    options = root_report.get_options(previous_options)
    option_date = options.get("date") if isinstance(options, dict) else None
    report_id = options.get("report_id") if isinstance(options, dict) else None
    raw_columns = options.get("columns") if isinstance(options, dict) else None
    if (
        not isinstance(options, dict)
        or options.get("readonly_query") is not True
        or options.get("all_entries") is not False
        or not isinstance(option_date, dict)
        or not _is_canonical_date(option_date.get("date_from"))
        or (
            payload["date_from"] is not None
            and option_date.get("date_from") != payload["date_from"]
        )
        or option_date.get("date_to") != payload["date_to"]
        or option_date.get("mode") != spec["mode"]
        or option_date.get("filter") != "custom"
        or not isinstance(report_id, int)
        or isinstance(report_id, bool)
        or report_id <= 0
        or not isinstance(raw_columns, list)
        or not raw_columns
    ):
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        )

    columns: list[dict[str, Any]] = []
    for index, column in enumerate(raw_columns):
        if (
            not isinstance(column, dict)
            or column.get("figure_type") != "monetary"
            or not isinstance(column.get("name"), str)
            or not column["name"].strip()
            or not isinstance(column.get("expression_label"), str)
            or not column["expression_label"].strip()
        ):
            raise RuntimeFailure(
                "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
            )
        columns.append(
            {
                "index": index,
                "label": column["name"],
                "expression_label": column["expression_label"],
            }
        )

    effective_report = env["account.report"].browse(report_id)
    if (
        getattr(effective_report, "id", None) != report_id
        or not isinstance(getattr(effective_report, "name", None), str)
        or not effective_report.name.strip()
    ):
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        )
    information = effective_report.get_report_information_readonly(options)
    raw_lines = information.get("lines") if isinstance(information, dict) else None
    if not isinstance(raw_lines, list):
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        )

    normalized_lines: list[dict[str, Any]] = []
    line_ids: set[str] = set()
    for line in raw_lines:
        raw_cells = line.get("columns") if isinstance(line, dict) else None
        line_id = line.get("id") if isinstance(line, dict) else None
        parent_id = line.get("parent_id") if isinstance(line, dict) else None
        unfoldable = line.get("unfoldable", False) if isinstance(line, dict) else None
        if (
            not isinstance(line, dict)
            or not isinstance(line_id, str)
            or not line_id.strip()
            or line_id in line_ids
            or not (
                parent_id in (False, None)
                or (isinstance(parent_id, str) and bool(parent_id.strip()))
            )
            or not isinstance(line.get("name"), str)
            or not line["name"].strip()
            or not isinstance(line.get("level"), int)
            or isinstance(line["level"], bool)
            or line["level"] < 0
            or not isinstance(unfoldable, bool)
            or not isinstance(raw_cells, list)
            or len(raw_cells) != len(columns)
        ):
            raise RuntimeFailure(
                "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
            )
        values: list[str | None] = []
        for index, cell in enumerate(raw_cells):
            if (
                not isinstance(cell, dict)
                or cell.get("expression_label") != columns[index]["expression_label"]
            ):
                raise RuntimeFailure(
                    "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
                )
            raw_value = cell.get("no_format")
            values.append(
                None
                if raw_value is None or isinstance(raw_value, bool)
                else _decimal_string(raw_value)
            )
        line_ids.add(line_id)
        normalized_lines.append(
            {
                "id": line_id,
                "parent_id": None if parent_id in (False, None) else parent_id,
                "name": line["name"],
                "level": line["level"],
                "unfoldable": unfoldable,
                "values": values,
            }
        )

    start = 0
    cursor_found = True
    if after_line_id is not None:
        try:
            start = next(
                index + 1
                for index, line in enumerate(normalized_lines)
                if line["id"] == after_line_id
            )
        except StopIteration:
            cursor_found = False
    visible_lines = normalized_lines[start : start + limit] if cursor_found else []

    companies = company_model.search_read(
        [("id", "=", company_id)], fields=["id", "currency_id"], limit=1
    )
    if len(companies) != 1 or companies[0].get("id") != company_id:
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        )
    currency_id = _reference_id(companies[0].get("currency_id"))
    currencies = env["res.currency"].search_read(
        [("id", "=", currency_id)],
        fields=["id", "name", "decimal_places"],
        limit=1,
    )
    if (
        len(currencies) != 1
        or currencies[0].get("id") != currency_id
        or not isinstance(currencies[0].get("name"), str)
        or not currencies[0]["name"].strip()
        or not isinstance(currencies[0].get("decimal_places"), int)
        or isinstance(currencies[0]["decimal_places"], bool)
        or currencies[0]["decimal_places"] < 0
    ):
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        )
    return {
        "user_id": env.uid,
        "company_visible": company_visible,
        "module_installed": module_installed,
        "access_allowed": access_allowed,
        "cursor_found": cursor_found,
        "report": {"key": spec["key"], "name": effective_report.name},
        "date": {
            "from": option_date["date_from"],
            "to": option_date["date_to"],
        },
        "currency": {
            "id": currency_id,
            "code": currencies[0]["name"],
            "decimal_places": currencies[0]["decimal_places"],
        },
        "basis": "posted_entries",
        "columns": columns,
        "lines": visible_lines,
    }


def _single_related_row(
    env: Any, model_name: str, record_id: int | None, fields: list[str]
) -> dict[str, Any] | None:
    if record_id is None:
        return None
    rows = env[model_name].search_read(
        [("id", "=", record_id)], fields=["id", *fields], limit=1
    )
    if len(rows) != 1 or rows[0].get("id") != record_id:
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        )
    return rows[0]


def _dispatch_company_accounting_configuration(
    env: Any, payload: dict[str, Any], company_id: int
) -> dict[str, Any]:
    _require_keys(payload, {"company_id"})
    if payload["company_id"] != company_id:
        raise RuntimeFailure(
            "company_unavailable", "The company is unavailable.", exit_code=3
        )
    required_models = ("res.company", "res.currency", "res.country", "account.account")
    company_visible = bool(
        env["res.company"].search_count([("id", "=", company_id)], limit=1)
    )
    module_installed = all(
        env.registry.get(model_name) is not None for model_name in required_models
    )
    access_allowed = bool(
        company_visible
        and module_installed
        and all(env[model_name].has_access("read") for model_name in required_models)
    )
    if not access_allowed:
        return {
            "user_id": env.uid,
            "company_visible": company_visible,
            "module_installed": module_installed,
            "access_allowed": access_allowed,
            "data": {},
        }
    fields = [
        "id",
        "name",
        "currency_id",
        "country_id",
        "account_fiscal_country_id",
        "chart_template",
        "tax_calculation_rounding_method",
        "fiscalyear_last_month",
        "fiscalyear_last_day",
        "anglo_saxon_accounting",
        "bank_account_code_prefix",
        "cash_account_code_prefix",
        "transfer_account_code_prefix",
        "account_journal_suspense_account_id",
        "account_default_pos_receivable_account_id",
        "account_opening_move_id",
        "account_opening_date",
    ]
    rows = env["res.company"].with_context(active_test=False).search_read(
        [("id", "=", company_id)], fields=fields, limit=1
    )
    if len(rows) != 1 or rows[0].get("id") != company_id:
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        )
    row = rows[0]
    currency_id = _reference_id(row["currency_id"])
    country_id = _reference_id(row["country_id"])
    fiscal_country_id = _reference_id(row["account_fiscal_country_id"])
    suspense_id = _reference_id(row["account_journal_suspense_account_id"])
    pos_receivable_id = _reference_id(row["account_default_pos_receivable_account_id"])
    currency = _single_related_row(env, "res.currency", currency_id, ["name"])
    country = _single_related_row(env, "res.country", country_id, ["name", "code"])
    fiscal_country = _single_related_row(
        env, "res.country", fiscal_country_id, ["name", "code"]
    )
    suspense = _single_related_row(env, "account.account", suspense_id, ["code", "name"])
    pos_receivable = _single_related_row(
        env, "account.account", pos_receivable_id, ["code", "name"]
    )
    if currency is None:
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        )
    try:
        fiscal_month = int(row["fiscalyear_last_month"])
    except (TypeError, ValueError) as exc:
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        ) from exc
    data = {
        "company": {"id": row["id"], "name": row["name"]},
        "currency": {"id": currency["id"], "code": currency["name"]},
        "country": None
        if country is None
        else {
            "id": country["id"],
            "code": country["code"],
            "name": country["name"],
        },
        "fiscal_country": None
        if fiscal_country is None
        else {
            "id": fiscal_country["id"],
            "code": fiscal_country["code"],
            "name": fiscal_country["name"],
        },
        "chart_template": _optional_string(row["chart_template"]),
        "tax_calculation_rounding_method": row["tax_calculation_rounding_method"],
        "fiscal_year_end": {"month": fiscal_month, "day": row["fiscalyear_last_day"]},
        "anglo_saxon_accounting": row["anglo_saxon_accounting"],
        "account_code_prefixes": {
            "bank": _optional_string(row["bank_account_code_prefix"]),
            "cash": _optional_string(row["cash_account_code_prefix"]),
            "transfer": _optional_string(row["transfer_account_code_prefix"]),
        },
        "suspense_account": None
        if suspense is None
        else {
            "id": suspense["id"],
            "code": suspense["code"],
            "name": suspense["name"],
        },
        "pos_receivable_account": None
        if pos_receivable is None
        else {
            "id": pos_receivable["id"],
            "code": pos_receivable["code"],
            "name": pos_receivable["name"],
        },
        "opening": {
            "date": None
            if row["account_opening_date"] in (False, None)
            else _date_string(row["account_opening_date"]),
            "move_id": _reference_id(row["account_opening_move_id"]),
        },
    }
    return {
        "user_id": env.uid,
        "company_visible": company_visible,
        "module_installed": module_installed,
        "access_allowed": access_allowed,
        "data": data,
    }


def _dispatch_accounting_environment_diagnostic(
    env: Any, payload: dict[str, Any], company_id: int
) -> dict[str, Any]:
    _require_keys(payload, {"company_id"})
    if payload["company_id"] != company_id:
        raise RuntimeFailure(
            "company_unavailable", "The company is unavailable.", exit_code=3
        )
    company_visible = bool(
        env["res.company"].search_count([("id", "=", company_id)], limit=1)
    )
    module_installed = all(
        env.registry.get(model_name) is not None for model_name in _DIAGNOSTIC_MODELS
    )
    access_allowed = bool(
        company_visible
        and module_installed
        and env["res.company"].has_access("read")
        and env["res.users"].has_access("read")
        and env["ir.module.module"].has_access("read")
    )
    if not access_allowed:
        return {
            "user_id": env.uid,
            "company_visible": company_visible,
            "module_installed": module_installed,
            "access_allowed": access_allowed,
            "data": {},
        }
    company_rows = env["res.company"].search_read(
        [("id", "=", company_id)], fields=["id", "name"], limit=1
    )
    module_rows = env["ir.module.module"].search_read(
        [("name", "in", list(_DIAGNOSTIC_MODULES))],
        fields=["name", "state", "latest_version"],
        order="name",
    )
    if len(company_rows) != 1 or company_rows[0].get("id") != company_id:
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        )
    if [row.get("name") for row in module_rows] != list(_DIAGNOSTIC_MODULES):
        raise RuntimeFailure(
            "odoo_runtime_error", "The Odoo runtime request failed.", exit_code=7
        )
    modules = [
        {
            "name": row["name"],
            "state": row["state"],
            "version": _optional_string(row["latest_version"]),
        }
        for row in module_rows
    ]
    data = {
        "company": company_rows[0],
        "user": {"id": env.user.id, "login": env.user.login},
        "modules": modules,
        "models": [
            {
                "model": model_name,
                "available": env.registry.get(model_name) is not None,
                "read": bool(
                    env.registry.get(model_name) is not None
                    and env[model_name].has_access("read")
                ),
            }
            for model_name in _DIAGNOSTIC_MODELS
        ],
        "transaction_read_only": True,
    }
    return {
        "user_id": env.uid,
        "company_visible": company_visible,
        "module_installed": module_installed,
        "access_allowed": access_allowed,
        "data": data,
    }


def _dispatch(
    env: Any,
    action: str,
    payload: dict[str, Any],
    company_id: int,
    available_company_ids: tuple[int, ...] | None = None,
):
    if action == "res.company.accounting_configuration.inspect":
        return _dispatch_company_accounting_configuration(env, payload, company_id)
    if action == "accounting.environment.diagnostic.inspect":
        return _dispatch_accounting_environment_diagnostic(env, payload, company_id)
    if action == "res.users.accounting_access.inspect":
        _require_keys(payload, {"company_id"})
        if (
            not isinstance(payload["company_id"], int)
            or isinstance(payload["company_id"], bool)
            or payload["company_id"] != company_id
        ):
            raise RuntimeFailure(
                "company_unavailable", "The company is unavailable.", exit_code=3
            )
        company_visible = bool(
            env["res.company"].search_count([("id", "=", company_id)], limit=1)
        )
        required_models = (
            "res.users",
            "res.groups",
            "ir.model.access",
            *_ACCOUNTING_ACCESS_MODELS,
        )
        module_installed = all(
            env.registry.get(model_name) is not None for model_name in required_models
        )
        access_allowed = bool(
            company_visible
            and module_installed
            and env["res.users"].has_access("read")
            and env["res.groups"].has_access("read")
        )
        if not access_allowed:
            return {
                "user_id": env.uid,
                "company_visible": company_visible,
                "module_installed": module_installed,
                "access_allowed": access_allowed,
                "user": {},
                "company_id": company_id,
                "groups": [],
                "model_acl": [],
            }
        user = env.user
        return {
            "user_id": env.uid,
            "company_visible": company_visible,
            "module_installed": module_installed,
            "access_allowed": access_allowed,
            "user": {
                "id": user.id,
                "login": user.login,
                "name": user.name,
                "active": user.active,
                "company_ids": sorted(user.company_ids.ids),
            },
            "company_id": company_id,
            "groups": [
                {"xml_id": xml_id, "member": user.has_group(xml_id)}
                for xml_id in _ACCOUNTING_ACCESS_GROUPS
            ],
            "model_acl": [
                {
                    "model": model_name,
                    **{
                        operation: env[model_name].has_access(operation)
                        for operation in ("read", "create", "write", "unlink")
                    },
                }
                for model_name in _ACCOUNTING_ACCESS_MODELS
            ],
        }
    if action == "account.account.read_page":
        _require_keys(
            payload, {"company_id", "after_code", "after_id", "limit"}
        )
        if payload["company_id"] != company_id:
            raise RuntimeFailure(
                "company_unavailable", "The company is unavailable.", exit_code=3
            )
        limit = payload["limit"]
        after_code = payload["after_code"]
        after_id = payload["after_id"]
        if (
            not isinstance(limit, int)
            or isinstance(limit, bool)
            or not 1 <= limit <= 1001
            or (after_code is None) != (after_id is None)
            or (
                after_code is not None
                and (
                    not isinstance(after_code, str)
                    or not after_code
                    or not isinstance(after_id, int)
                    or isinstance(after_id, bool)
                    or after_id <= 0
                )
            )
        ):
            raise RuntimeFailure(
                "bridge_protocol_error",
                "The bridge action payload is invalid.",
                exit_code=7,
            )
        company_visible = bool(
            env["res.company"].search_count([("id", "=", company_id)], limit=1)
        )
        module_installed = env.registry.get("account.account") is not None
        access_allowed = bool(
            company_visible
            and module_installed
            and env["account.account"].has_access("read")
        )
        if not access_allowed:
            return {
                "user_id": env.uid,
                "company_visible": company_visible,
                "module_installed": module_installed,
                "access_allowed": access_allowed,
                "rows": [],
            }
        domain: list[Any] = [("company_ids", "in", [company_id])]
        if after_code is not None:
            from odoo.osv import expression

            domain = expression.AND(
                [
                    domain,
                    [
                        "|",
                        ("code", ">", after_code),
                        "&",
                        ("code", "=", after_code),
                        ("id", ">", after_id),
                    ],
                ]
            )
        rows = (
            env["account.account"]
            .with_context(active_test=False, allowed_company_ids=[company_id])
            .search_read(domain, fields=list(_ACCOUNT_FIELDS), limit=limit, order="code,id")
        )
        return {
            "user_id": env.uid,
            "company_visible": company_visible,
            "module_installed": module_installed,
            "access_allowed": access_allowed,
            "rows": rows,
        }
    if action in _MASTER_DATA_ACTIONS:
        return _dispatch_master_data(env, action, payload, company_id)
    if action == "res.company.accounting_context.read_page":
        if available_company_ids is None:
            raise RuntimeFailure(
                "bridge_protocol_error",
                "The bridge action payload is invalid.",
                exit_code=7,
            )
        return _dispatch_company_contexts(
            env, payload, company_id, available_company_ids
        )
    if action == "account.move.journal_entry.search_page":
        return _dispatch_journal_entry_search(env, payload, company_id)
    if action == "account.move.journal_entry.get":
        return _dispatch_journal_entry_get(env, payload, company_id)
    if action == "account.move.invoice.search_page":
        return _dispatch_invoice_search(env, payload, company_id)
    if action == "account.move.invoice.get":
        return _dispatch_invoice_get(env, payload, company_id)
    if action == "account.move.invoice.payment_status.inspect":
        return _dispatch_invoice_payment_status(env, payload, company_id)
    if action == "account.payment.search_page":
        return _dispatch_payment_search(env, payload, company_id)
    if action == "account.payment.get":
        if available_company_ids is None:
            raise RuntimeFailure(
                "bridge_protocol_error",
                "The bridge action payload is invalid.",
                exit_code=7,
            )
        return _dispatch_payment_get(
            env, payload, company_id, available_company_ids
        )
    if action in _OPEN_ITEM_ACTION_SIDES:
        return _dispatch_open_item_search(env, action, payload, company_id)
    if action == "res.partner.accounting.search_page":
        return _dispatch_partner_accounting_search(env, payload, company_id)
    if action in _FINANCIAL_REPORT_ACTIONS:
        return _dispatch_financial_report(env, action, payload, company_id)
    raise RuntimeFailure(
        "bridge_protocol_error", "The bridge action is unavailable.", exit_code=7
    )


def _ensure_language_is_active(root_env: Any, language: str) -> None:
    active = root_env["res.lang"].with_context(active_test=False).search_count(
        [("code", "=", language), ("active", "=", True)], limit=1
    )
    if not active:
        raise RuntimeFailure(
            "language_unavailable",
            "The requested Odoo language is unavailable.",
            exit_code=4,
        )


def _effective_company_ids(users: Any, target: Any) -> tuple[int, ...]:
    user_company_ids = set(users.company_ids.ids)
    if target.company_id not in user_company_ids:
        raise RuntimeFailure(
            "company_unavailable", "The company is unavailable.", exit_code=3
        )
    return tuple(
        company_id
        for company_id in target.available_company_ids
        if company_id in user_company_ids
    )


def execute(request: dict[str, Any], *, config_path: Path, odoo_config: Path):
    target = _validated_target(request, config_path)
    try:
        from odoo import SUPERUSER_ID, api
        from odoo.orm.registry import Registry
        from odoo.tools import config as odoo_runtime_config

        odoo_runtime_config.parse_config(
            ["--config", str(odoo_config), "--database", target.database, "--no-http"]
        )
        registry = Registry(target.database)
        with _read_only_cursor(registry) as cursor:
            root_env = api.Environment(cursor, SUPERUSER_ID, {})
            request_target = request["target"]
            _ensure_language_is_active(root_env, request_target["language"])
            users = root_env["res.users"].with_context(active_test=False).search(
                [("login", "=", target.user_login)], limit=2
            )
            if len(users) != 1 or not users.active:
                raise RuntimeFailure(
                    "user_unavailable", "The configured user is unavailable.", exit_code=3
                )
            effective_company_ids = _effective_company_ids(users, target)
            if request["action"] == "res.company.accounting_context.read_page":
                allowed_company_ids = list(effective_company_ids)
            elif request["action"] == "account.payment.get":
                allowed_company_ids = [
                    target.company_id,
                    *(
                        value
                        for value in effective_company_ids
                        if value != target.company_id
                    ),
                ]
            else:
                allowed_company_ids = [target.company_id]
            context = {
                "allowed_company_ids": allowed_company_ids,
                "active_test": True,
                "lang": request_target["language"],
                "tz": request_target["timezone"],
            }
            env = api.Environment(cursor, users.id, context)
            return _dispatch(
                env,
                request["action"],
                request["payload"],
                target.company_id,
                effective_company_ids,
            )
    except RuntimeFailure:
        raise
    except Exception as exc:
        raise RuntimeFailure(
            "odoo_runtime_error",
            "The Odoo runtime request failed.",
            exit_code=7,
            retryable=False,
        ) from exc


def _document(success: bool, *, data=None, error=None) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "success": success,
        "data": data if success else None,
        "error": None if success else error,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--runtime-config",
        type=Path,
        default=Path("/etc/odoo-accounting-cli-v4/runtime.json"),
    )
    parser.add_argument(
        "--odoo-config",
        type=Path,
        default=Path("/etc/odoo-accounting-cli-v4/odoo.conf"),
    )
    parser.add_argument(
        "--odoo-source",
        type=Path,
        required=True,
    )
    args = parser.parse_args(argv)
    if not args.odoo_source.is_absolute() or not args.odoo_source.is_dir():
        result = _document(
            False,
            error={
                "code": "odoo_runtime_error",
                "message": "The Odoo runtime is unavailable.",
                "details": {},
                "retryable": False,
                "exit_code": 7,
            },
        )
        sys.stdout.write(
            json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
        )
        return 7
    sys.path.insert(0, str(args.odoo_source))
    try:
        request = _decode_request(sys.stdin)
        data = execute(
            request, config_path=args.runtime_config, odoo_config=args.odoo_config
        )
        result = _document(True, data=data)
        exit_code = 0
    except RuntimeFailure as exc:
        result = _document(
            False,
            error={
                "code": exc.code,
                "message": str(exc),
                "details": exc.details,
                "retryable": exc.retryable,
                "exit_code": exc.exit_code,
            },
        )
        exit_code = exc.exit_code
    sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    return exit_code
