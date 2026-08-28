"""Odoo-side runtime for ten fixed financial-report file exports."""

from __future__ import annotations

import base64
import hashlib
from datetime import date
from typing import Any

ACTION = "account.report.fixed_export"
MAX_FILE_BYTES = 64 * 1024 * 1024
CAPABILITY_SPECS = {
    "report.trial_balance.export": {
        "xml_id": "account_reports.trial_balance_report",
        "mode": "range",
    },
    "report.balance_sheet.export": {
        "xml_id": "account_reports.balance_sheet",
        "mode": "single",
    },
    "report.profit_and_loss.export": {
        "xml_id": "account_reports.profit_and_loss",
        "mode": "range",
    },
    "report.cash_flow.export": {
        "xml_id": "account_reports.cash_flow_report",
        "mode": "range",
    },
    "report.tax.export": {
        "xml_id": "account.generic_tax_report",
        "mode": "range",
    },
    "report.general_ledger.export": {
        "xml_id": "account_reports.general_ledger_report",
        "mode": "range",
    },
    "report.partner_ledger.export": {
        "xml_id": "account_reports.partner_ledger_report",
        "mode": "range",
    },
    "report.aged_receivable.export": {
        "xml_id": "account_reports.aged_receivable_report",
        "mode": "single",
    },
    "report.aged_payable.export": {
        "xml_id": "account_reports.aged_payable_report",
        "mode": "single",
    },
    "report.executive_summary.export": {
        "xml_id": "account_reports.executive_summary",
        "mode": "range",
    },
}
_FORMATS = {
    "pdf": {
        "magic": b"%PDF-",
        "mimetype": "application/pdf",
    },
    "xlsx": {
        "magic": b"PK\x03\x04",
        "mimetype": (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    },
}
_PAYLOAD_KEYS = {"capability_id", "company_id", "date_from", "date_to", "format"}


def _failure(failure_type: Any, code: str, message: str, exit_code: int) -> Exception:
    return failure_type(code, message, exit_code=exit_code)


def _protocol_failure(failure_type: Any) -> Exception:
    return _failure(
        failure_type,
        "bridge_protocol_error",
        "The bridge action payload is invalid.",
        7,
    )


def _runtime_failure(failure_type: Any) -> Exception:
    return _failure(
        failure_type,
        "odoo_runtime_error",
        "The Odoo runtime request failed.",
        7,
    )


def _canonical_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _validated_payload(
    payload: Any, company_id: int, failure_type: Any
) -> tuple[dict[str, str], str, str | None, str, str]:
    if not isinstance(payload, dict) or set(payload) != _PAYLOAD_KEYS:
        raise _protocol_failure(failure_type)

    capability_id = payload["capability_id"]
    requested_company_id = payload["company_id"]
    date_from = payload["date_from"]
    date_to = payload["date_to"]
    file_format = payload["format"]
    if (
        not isinstance(capability_id, str)
        or capability_id not in CAPABILITY_SPECS
        or not isinstance(requested_company_id, int)
        or isinstance(requested_company_id, bool)
        or requested_company_id <= 0
        or not isinstance(file_format, str)
        or file_format not in _FORMATS
        or not _canonical_date(date_to)
    ):
        raise _protocol_failure(failure_type)
    if requested_company_id != company_id:
        raise _failure(
            failure_type,
            "company_unavailable",
            "The company is unavailable.",
            3,
        )

    spec = CAPABILITY_SPECS[capability_id]
    if (
        spec["mode"] == "range"
        and (not _canonical_date(date_from) or date_from > date_to)
        or spec["mode"] == "single"
        and date_from is not None
    ):
        raise _protocol_failure(failure_type)
    return spec, capability_id, date_from, date_to, file_format


def _empty_page(
    env: Any,
    *,
    company_visible: bool,
    module_installed: bool,
    access_allowed: bool,
    file_format: str,
) -> dict[str, Any]:
    return {
        "user_id": env.uid,
        "company_visible": company_visible,
        "module_installed": module_installed,
        "access_allowed": access_allowed,
        "filename": None,
        "format": file_format,
        "mimetype": None,
        "byte_count": 0,
        "sha256": None,
        "content_base64": None,
    }


def _file_bytes(value: Any, failure_type: Any) -> bytes:
    if not isinstance(value, (bytes, bytearray, memoryview)):
        raise _runtime_failure(failure_type)
    byte_count = value.nbytes if isinstance(value, memoryview) else len(value)
    if byte_count > MAX_FILE_BYTES:
        raise _runtime_failure(failure_type)
    try:
        result = bytes(value)
    except (TypeError, ValueError) as exc:
        raise _runtime_failure(failure_type) from exc
    if len(result) != byte_count:
        raise _runtime_failure(failure_type)
    return result


def dispatch(
    env: Any,
    payload: dict[str, Any],
    company_id: int,
    *,
    failure_type: Any,
) -> dict[str, Any]:
    spec, _capability_id, date_from, date_to, file_format = _validated_payload(
        payload, company_id, failure_type
    )
    company_visible = bool(
        env["res.company"].search_count([("id", "=", company_id)], limit=1)
    )
    report_registered = env.registry.get("account.report") is not None
    root_report = (
        env.ref(spec["xml_id"], raise_if_not_found=False)
        if report_registered
        else None
    )
    module_installed = bool(report_registered and root_report)
    report_model = env["account.report"] if report_registered else None
    access_allowed = bool(
        company_visible
        and module_installed
        and report_model.has_access("read")
    )
    if not access_allowed:
        return _empty_page(
            env,
            company_visible=company_visible,
            module_installed=module_installed,
            access_allowed=access_allowed,
            file_format=file_format,
        )

    previous_options = {
        "all_entries": False,
        "date": {
            "date_from": date_from if date_from is not None else False,
            "date_to": date_to,
            "mode": spec["mode"],
            "filter": "custom",
        },
    }
    scoped_root_report = root_report.with_context(allowed_company_ids=[company_id])
    options = scoped_root_report.get_options(previous_options)
    report_id = options.get("report_id") if isinstance(options, dict) else None
    if (
        not isinstance(report_id, int)
        or isinstance(report_id, bool)
        or report_id <= 0
    ):
        raise _runtime_failure(failure_type)

    scoped_report_model = report_model.with_context(allowed_company_ids=[company_id])
    effective_report = scoped_report_model.browse(report_id)
    exporter = (
        effective_report.export_to_xlsx
        if file_format == "xlsx"
        else effective_report.export_to_pdf
    )
    native = exporter(options)
    if not isinstance(native, dict):
        raise _runtime_failure(failure_type)
    filename = native.get("file_name")
    native_file_type = native.get("file_type")
    if (
        not isinstance(filename, str)
        or not filename.strip()
        or native_file_type != file_format
    ):
        raise _runtime_failure(failure_type)

    content = _file_bytes(native.get("file_content"), failure_type)
    format_spec = _FORMATS[file_format]
    if not content.startswith(format_spec["magic"]):
        raise _runtime_failure(failure_type)
    return {
        "user_id": env.uid,
        "company_visible": company_visible,
        "module_installed": module_installed,
        "access_allowed": access_allowed,
        "filename": filename,
        "format": file_format,
        "mimetype": format_spec["mimetype"],
        "byte_count": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "content_base64": base64.b64encode(content).decode("ascii"),
    }
