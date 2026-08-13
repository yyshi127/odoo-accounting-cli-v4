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
}
_ACTIONS = {
    "account.account.read_page",
    "res.company.accounting_context.read_page",
    *_MASTER_DATA_ACTIONS,
    "account.move.journal_entry.search_page",
    "account.move.journal_entry.get",
    *_FINANCIAL_REPORT_ACTIONS,
}


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


def _dispatch(
    env: Any,
    action: str,
    payload: dict[str, Any],
    company_id: int,
    available_company_ids: tuple[int, ...] | None = None,
):
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
            allowed_company_ids = (
                list(effective_company_ids)
                if request["action"] == "res.company.accounting_context.read_page"
                else [target.company_id]
            )
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
