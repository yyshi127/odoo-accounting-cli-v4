"""Closed contracts for journal accounting-date and journal-item analysis reads."""

from __future__ import annotations

import re
import uuid
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol

JOURNAL_ANALYSIS_CAPABILITY_IDS = frozenset(
    {
        "analytic.line.summary",
        "journal.accounting_date.resolve",
        "journal_item.analysis.summary",
    }
)
GROUP_BY_VALUES = frozenset({"account", "journal"})
_DECIMAL_PATTERN = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_AMOUNT_KEYS = ("debit", "credit", "balance")


class JournalAnalysisPort(Protocol):
    @property
    def user_id(self) -> int: ...

    def read(
        self,
        *,
        capability_id: str,
        company_id: int,
        parameters: dict[str, Any],
    ) -> dict[str, Any]: ...


class JournalAnalysisReadError(RuntimeError):
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


def _invalid(message: str) -> JournalAnalysisReadError:
    return JournalAnalysisReadError("invalid_request", message, exit_code=2)


def _failed(message: str) -> JournalAnalysisReadError:
    return JournalAnalysisReadError("failed_validation", message, exit_code=8)


def _integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _positive_id(value: Any) -> bool:
    return _integer(value) and value > 0


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _canonical_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _decimal(value: Any) -> Decimal | None:
    if (
        not isinstance(value, str)
        or len(value) > 256
        or _DECIMAL_PATTERN.fullmatch(value) is None
    ):
        return None
    try:
        number = Decimal(value)
    except InvalidOperation:
        return None
    return number if number.is_finite() else None


def _envelope(request: Any) -> tuple[str, dict[str, Any], dict[str, Any]]:
    if not isinstance(request, dict) or set(request) != {
        "schema_version",
        "request_id",
        "context",
        "parameters",
    }:
        raise _invalid("The request must match the v1 request envelope.")
    if request["schema_version"] != "v1":
        raise _invalid("schema_version must be 'v1'.")
    request_id = request["request_id"]
    try:
        parsed = uuid.UUID(request_id) if isinstance(request_id, str) else None
    except ValueError as exc:
        raise _invalid("request_id must be a UUID string.") from exc
    if (
        parsed is None
        or str(parsed) != request_id.lower()
        or parsed.version not in {1, 2, 3, 4, 5}
        or parsed.variant != uuid.RFC_4122
    ):
        raise _invalid("request_id must use canonical UUID syntax.")

    context = request["context"]
    if not isinstance(context, dict) or set(context) != {
        "database",
        "company_id",
        "user_login",
        "language",
        "timezone",
    }:
        raise _invalid("context must contain only the required v1 fields.")
    if not all(
        _text(context.get(key))
        for key in ("database", "user_login", "language", "timezone")
    ) or not _positive_id(context.get("company_id")):
        raise _invalid("context contains an invalid value.")
    parameters = request["parameters"]
    if not isinstance(parameters, dict):
        raise _invalid("parameters must be an object.")
    return request_id, context, parameters


def validate_journal_analysis_request(
    capability_id: str, request: Any
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    """Validate one request without exposing generic Odoo query controls."""

    if (
        not isinstance(capability_id, str)
        or capability_id not in JOURNAL_ANALYSIS_CAPABILITY_IDS
    ):
        raise JournalAnalysisReadError(
            "unsupported_capability",
            "The journal-analysis capability is unsupported.",
            exit_code=4,
        )
    request_id, context, parameters = _envelope(request)
    if capability_id == "journal.accounting_date.resolve":
        if (
            set(parameters) != {"journal_id", "date", "has_tax"}
            or not _positive_id(parameters.get("journal_id"))
            or not _canonical_date(parameters.get("date"))
            or not isinstance(parameters.get("has_tax"), bool)
        ):
            raise _invalid(
                "parameters must contain journal_id, date, and boolean has_tax."
            )
        return request_id, context, dict(parameters)

    if capability_id == "analytic.line.summary":
        required = {"date_from", "date_to", "plan_id"}
        if (
            not required <= set(parameters) <= required | {"analytic_account_id"}
            or not _canonical_date(parameters.get("date_from"))
            or not _canonical_date(parameters.get("date_to"))
            or parameters["date_from"] > parameters["date_to"]
            or not _positive_id(parameters.get("plan_id"))
            or (
                parameters.get("analytic_account_id") is not None
                and not _positive_id(parameters["analytic_account_id"])
            )
        ):
            raise _invalid(
                "parameters must contain an ordered date range, plan_id, and optional analytic_account_id."
            )
        return request_id, context, {
            **parameters,
            "analytic_account_id": parameters.get("analytic_account_id"),
        }

    if (
        set(parameters) != {"date_from", "date_to", "group_by"}
        or not _canonical_date(parameters.get("date_from"))
        or not _canonical_date(parameters.get("date_to"))
        or parameters["date_from"] > parameters["date_to"]
        or not isinstance(parameters.get("group_by"), str)
        or parameters["group_by"] not in GROUP_BY_VALUES
    ):
        raise _invalid(
            "parameters must contain an ordered date range and account or journal group_by."
        )
    return request_id, context, dict(parameters)


def _valid_page(port: JournalAnalysisPort, page: Any) -> bool:
    return bool(
        isinstance(page, dict)
        and set(page)
        == {
            "user_id",
            "company_visible",
            "module_installed",
            "access_allowed",
            "cursor_found",
            "items",
        }
        and _positive_id(page["user_id"])
        and _positive_id(port.user_id)
        and page["user_id"] == port.user_id
        and all(
            isinstance(page[key], bool)
            for key in (
                "company_visible",
                "module_installed",
                "access_allowed",
                "cursor_found",
            )
        )
        and isinstance(page["items"], list)
        and all(isinstance(item, dict) for item in page["items"])
        and (
            not page["access_allowed"]
            or page["company_visible"]
            and page["module_installed"]
        )
        and (page["access_allowed"] or not page["items"])
    )


def _availability(page: dict[str, Any]) -> None:
    if not page["company_visible"]:
        raise JournalAnalysisReadError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    if not page["module_installed"]:
        raise JournalAnalysisReadError(
            "uninstalled",
            "The journal-analysis capability is not installed in this database.",
            exit_code=4,
        )
    if not page["access_allowed"]:
        raise JournalAnalysisReadError(
            "unauthorized",
            "The configured user cannot read the requested accounting data.",
            exit_code=3,
        )


def _coded_ref(value: Any) -> bool:
    return bool(
        isinstance(value, dict)
        and set(value) == {"id", "code", "name"}
        and _positive_id(value["id"])
        and _text(value["code"])
        and _text(value["name"])
    )


def _currency(value: Any) -> bool:
    return bool(
        isinstance(value, dict)
        and set(value) == {"id", "code"}
        and _positive_id(value["id"])
        and _text(value["code"])
        and len(value["code"]) <= 3
    )


def _valid_resolution(
    value: Any, *, company_id: int, parameters: dict[str, Any]
) -> bool:
    return bool(
        isinstance(value, dict)
        and set(value)
        == {
            "company_id",
            "journal",
            "requested_date",
            "has_tax",
            "accounting_date",
            "adjusted",
        }
        and value["company_id"] == company_id
        and _coded_ref(value["journal"])
        and value["journal"]["id"] == parameters["journal_id"]
        and value["requested_date"] == parameters["date"]
        and value["has_tax"] is parameters["has_tax"]
        and _canonical_date(value["accounting_date"])
        and isinstance(value["adjusted"], bool)
        and value["adjusted"] == (value["accounting_date"] != value["requested_date"])
    )


def _valid_journal_summary(
    value: Any, *, company_id: int, parameters: dict[str, Any]
) -> bool:
    if not isinstance(value, dict) or set(value) != {
        "company_id",
        "date_from",
        "date_to",
        "basis",
        "group_by",
        "company_currency",
        "groups",
        "totals",
    }:
        return False
    groups = value["groups"]
    totals = value["totals"]
    if not (
        value["company_id"] == company_id
        and value["date_from"] == parameters["date_from"]
        and value["date_to"] == parameters["date_to"]
        and value["basis"] == "posted_entries"
        and value["group_by"] == parameters["group_by"]
        and _currency(value["company_currency"])
        and isinstance(groups, list)
        and isinstance(totals, dict)
        and set(totals) == {"row_count", *_AMOUNT_KEYS}
        and _integer(totals["row_count"])
        and totals["row_count"] >= 0
        and all(_decimal(totals[key]) is not None for key in _AMOUNT_KEYS)
    ):
        return False

    ids: list[int] = []
    count = 0
    amounts = {key: Decimal(0) for key in _AMOUNT_KEYS}
    for group in groups:
        if not (
            isinstance(group, dict)
            and set(group) == {"group", "row_count", *_AMOUNT_KEYS}
            and _coded_ref(group["group"])
            and _integer(group["row_count"])
            and group["row_count"] > 0
            and all(_decimal(group[key]) is not None for key in _AMOUNT_KEYS)
        ):
            return False
        ids.append(group["group"]["id"])
        count += group["row_count"]
        for key in _AMOUNT_KEYS:
            number = _decimal(group[key])
            if number is None:
                return False
            amounts[key] += number
    if ids != sorted(set(ids)) or count != totals["row_count"]:
        return False
    return all(amounts[key] == _decimal(totals[key]) for key in _AMOUNT_KEYS)


def _named_ref(value: Any) -> bool:
    return bool(
        isinstance(value, dict)
        and set(value) == {"id", "name"}
        and _positive_id(value["id"])
        and _text(value["name"])
    )


def _analytic_account_ref(value: Any) -> bool:
    return bool(
        isinstance(value, dict)
        and set(value) == {"id", "name", "code"}
        and _positive_id(value["id"])
        and _text(value["name"])
        and (value["code"] is None or _text(value["code"]))
    )


def _valid_analytic_summary(
    value: Any, *, company_id: int, parameters: dict[str, Any]
) -> bool:
    if not isinstance(value, dict) or set(value) != {
        "company_id",
        "date_from",
        "date_to",
        "basis",
        "group_by",
        "plan",
        "company_currency",
        "groups",
        "totals",
    }:
        return False
    groups = value["groups"]
    totals = value["totals"]
    if not (
        value["company_id"] == company_id
        and value["date_from"] == parameters["date_from"]
        and value["date_to"] == parameters["date_to"]
        and value["basis"] == "analytic_lines"
        and value["group_by"] == "analytic_account"
        and _named_ref(value["plan"])
        and value["plan"]["id"] == parameters["plan_id"]
        and _currency(value["company_currency"])
        and isinstance(groups, list)
        and isinstance(totals, dict)
        and set(totals) == {"row_count", "amount", "unit_amount"}
        and _integer(totals["row_count"])
        and totals["row_count"] >= 0
        and _decimal(totals["amount"]) is not None
        and _decimal(totals["unit_amount"]) is not None
    ):
        return False

    ids: list[int] = []
    row_count = 0
    amount = Decimal(0)
    unit_amount = Decimal(0)
    for group in groups:
        if not (
            isinstance(group, dict)
            and set(group)
            == {"analytic_account", "row_count", "amount", "unit_amount"}
            and _analytic_account_ref(group["analytic_account"])
            and _integer(group["row_count"])
            and group["row_count"] > 0
            and _decimal(group["amount"]) is not None
            and _decimal(group["unit_amount"]) is not None
        ):
            return False
        ids.append(group["analytic_account"]["id"])
        row_count += group["row_count"]
        amount += _decimal(group["amount"]) or Decimal(0)
        unit_amount += _decimal(group["unit_amount"]) or Decimal(0)
    if ids != sorted(set(ids)) or row_count != totals["row_count"]:
        return False
    if parameters["analytic_account_id"] is not None and ids not in (
        [],
        [parameters["analytic_account_id"]],
    ):
        return False
    return bool(
        amount == _decimal(totals["amount"])
        and unit_amount == _decimal(totals["unit_amount"])
    )


def read_journal_analysis(
    port: JournalAnalysisPort, capability_id: str, request: Any
) -> dict[str, Any]:
    """Execute one strictly modelled journal-analysis read."""

    _, context, parameters = validate_journal_analysis_request(capability_id, request)
    page = port.read(
        capability_id=capability_id,
        company_id=context["company_id"],
        parameters=parameters,
    )
    if not _valid_page(port, page):
        raise _failed("Odoo returned an invalid journal-analysis page.")
    _availability(page)
    if not page["cursor_found"] or len(page["items"]) > 1:
        raise _failed("Odoo returned an invalid journal-analysis result count.")

    if capability_id == "journal.accounting_date.resolve":
        if not page["items"]:
            raise JournalAnalysisReadError(
                "record_not_found",
                "The requested journal was not found in the company.",
                exit_code=4,
            )
        if not _valid_resolution(
            page["items"][0], company_id=context["company_id"], parameters=parameters
        ):
            raise _failed("Odoo returned an invalid accounting-date resolution.")
        return page["items"][0]

    if capability_id == "analytic.line.summary":
        if not page["items"]:
            raise JournalAnalysisReadError(
                "record_not_found",
                "The requested analytic plan or account was not found.",
                exit_code=4,
            )
        if not _valid_analytic_summary(
            page["items"][0], company_id=context["company_id"], parameters=parameters
        ):
            raise _failed("Odoo returned an invalid analytic-line summary.")
        return page["items"][0]

    if not page["items"] or not _valid_journal_summary(
        page["items"][0], company_id=context["company_id"], parameters=parameters
    ):
        raise _failed("Odoo returned an invalid journal-item analysis summary.")
    return page["items"][0]
