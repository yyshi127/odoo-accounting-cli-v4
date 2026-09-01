"""Odoo-side runtime for fixed financial-report file exports."""

from __future__ import annotations

import base64
import hashlib
from datetime import date
from typing import Any

from odoo_accounting_cli_v4.bridge import financial_report_journals

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
    "report.journal.export": {
        "xml_id": "account_reports.journal_report",
        "mode": "range",
        "models": (
            "account.report",
            "account.move",
            "account.move.line",
            "res.currency",
        ),
        "dispatch_export": True,
    },
    "report.asset.export": {
        "xml_id": "account_asset.assets_report",
        "mode": "range",
        "models": (
            "account.report",
            "account.asset",
            "account.move",
            "account.move.line",
            "res.currency",
        ),
    },
    "report.deferred_expense.export": {
        "xml_id": "account_reports.deferred_expense_report",
        "mode": "range",
        "models": (
            "account.report",
            "account.move",
            "account.move.line",
            "res.currency",
        ),
    },
    "report.deferred_revenue.export": {
        "xml_id": "account_reports.deferred_revenue_report",
        "mode": "range",
        "models": (
            "account.report",
            "account.move",
            "account.move.line",
            "res.currency",
        ),
    },
    "report.multicurrency_revaluation.export": {
        "xml_id": "account_reports.multicurrency_revaluation_report",
        "mode": "single",
        "models": ("account.report", "account.move.line", "res.currency"),
    },
    "report.china.balance_sheet.export": {
        "xml_id": "l10n_cn_reports.account_financial_report_cn_balancesheet0",
        "mode": "single",
        "models": (
            "account.report",
            "account.move.line",
            "res.currency",
            "res.country",
        ),
        "fiscal_country_code": "CN",
        "chart_template": "cn_oscg",
    },
    "report.china.profit_and_loss.export": {
        "xml_id": "l10n_cn_reports.account_financial_report_cn_profitloss0",
        "mode": "range",
        "models": (
            "account.report",
            "account.move.line",
            "res.currency",
            "res.country",
        ),
        "fiscal_country_code": "CN",
        "chart_template": "cn_oscg",
    },
    "report.china.cash_flow.export": {
        "xml_id": "l10n_cn_reports.account_report_cn_cs_flow",
        "mode": "range",
        "models": (
            "account.report",
            "account.move.line",
            "account.cash.flow.line",
            "res.currency",
            "res.country",
        ),
        "fiscal_country_code": "CN",
        "chart_template": "cn_oscg",
    },
    "report.singapore.gst.export": {
        "xml_id": "l10n_sg.tax_report",
        "mode": "range",
        "models": (
            "account.report",
            "account.move.line",
            "account.tax",
            "res.currency",
            "res.country",
        ),
        "fiscal_country_code": "SG",
        "chart_template": "sg",
    },
    "report.customer_statement.export": {
        "xml_id": "account_reports.customer_statement_report",
        "mode": "range",
        "models": (
            "account.report",
            "account.move.line",
            "res.currency",
            "res.partner",
        ),
        "partner_parameter": True,
    },
    "report.followup.export": {
        "xml_id": "account_reports.followup_report",
        "mode": "single",
        "models": (
            "account.report",
            "account.move.line",
            "res.currency",
            "res.partner",
        ),
        "partner_parameter": True,
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


def _reference_id(value: Any, failure_type: Any) -> int | None:
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
    raise _runtime_failure(failure_type)


def _validated_payload(
    payload: Any, company_id: int, failure_type: Any
) -> tuple[dict[str, Any], str, str | None, str, str]:
    if not isinstance(payload, dict) or not (
        _PAYLOAD_KEYS <= set(payload) <= _PAYLOAD_KEYS | {"journal_ids", "partner_id"}
    ):
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
    if "journal_ids" in payload:
        if capability_id not in {
            f"report.{key}.export" for key in financial_report_journals.REPORT_KEYS
        }:
            raise _protocol_failure(failure_type)
        financial_report_journals.validate_journal_ids(payload["journal_ids"], failure_type)

    spec = CAPABILITY_SPECS[capability_id]
    partner_id = payload.get("partner_id")
    if (
        spec.get("partner_parameter") is True
        and (
            "partner_id" not in payload
            or not isinstance(partner_id, int)
            or isinstance(partner_id, bool)
            or partner_id <= 0
        )
        or spec.get("partner_parameter") is not True
        and "partner_id" in payload
    ):
        raise _protocol_failure(failure_type)
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
    journal_ids = sorted(payload["journal_ids"]) if "journal_ids" in payload else None
    partner_id = payload.get("partner_id")
    company_model = env["res.company"]
    company_visible = bool(
        company_model.search_count([("id", "=", company_id)], limit=1)
    )
    required_models = spec.get("models", ("account.report",))
    if journal_ids is not None:
        required_models = (*required_models, "account.journal")
    models_installed = all(
        env.registry.get(model_name) is not None for model_name in required_models
    )
    localization_applicable = True
    expected_country_code = spec.get("fiscal_country_code")
    if company_visible and models_installed and expected_country_code is not None:
        companies = company_model.search_read(
            [("id", "=", company_id)],
            fields=["id", "account_fiscal_country_id", "chart_template"],
            limit=1,
        )
        if len(companies) != 1 or companies[0].get("id") != company_id:
            raise _runtime_failure(failure_type)
        fiscal_country_id = _reference_id(
            companies[0].get("account_fiscal_country_id"), failure_type
        )
        countries = env["res.country"].search_read(
            [("id", "=", fiscal_country_id)], fields=["id", "code"], limit=1
        )
        localization_applicable = bool(
            len(countries) == 1
            and countries[0].get("id") == fiscal_country_id
            and countries[0].get("code") == expected_country_code
            and companies[0].get("chart_template") == spec.get("chart_template")
        )
    root_report = (
        env.ref(spec["xml_id"], raise_if_not_found=False)
        if models_installed and localization_applicable
        else None
    )
    module_installed = bool(
        models_installed and localization_applicable and root_report
    )
    access_allowed = bool(
        company_visible
        and module_installed
        and company_model.has_access("read")
        and all(env[model_name].has_access("read") for model_name in required_models)
    )
    if not access_allowed:
        return _empty_page(
            env,
            company_visible=company_visible,
            module_installed=module_installed,
            access_allowed=access_allowed,
            file_format=file_format,
        )

    if spec.get("partner_parameter") is True:
        partner_available = bool(
            env["res.partner"]
            .with_context(active_test=False, allowed_company_ids=[company_id])
            .search_count(
                [
                    ("id", "=", partner_id),
                    "|",
                    ("company_id", "=", False),
                    ("company_id", "=", company_id),
                ],
                limit=1,
            )
        )
        if not partner_available:
            raise _failure(
                failure_type,
                "company_unavailable",
                "The company-scoped partner is unavailable.",
                3,
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
    if journal_ids is not None:
        previous_options["journals"] = financial_report_journals.journal_options(
            env, company_id, journal_ids, failure_type
        )
    if partner_id is not None:
        previous_options["partner_ids"] = [partner_id]
    scoped_root_report = root_report.with_context(allowed_company_ids=[company_id])
    options = scoped_root_report.get_options(previous_options)
    report_id = options.get("report_id") if isinstance(options, dict) else None
    if (
        not isinstance(report_id, int)
        or isinstance(report_id, bool)
        or report_id <= 0
        or (
            spec.get("partner_parameter") is True
            and options.get("partner_ids") != [partner_id]
        )
    ):
        raise _runtime_failure(failure_type)

    report_model = env["account.report"]
    scoped_report_model = report_model.with_context(allowed_company_ids=[company_id])
    effective_report = scoped_report_model.browse(report_id)
    if journal_ids is not None:
        financial_report_journals.verify_journal_options(
            effective_report, options, journal_ids, failure_type
        )
    export_action = f"export_to_{file_format}"
    if spec.get("dispatch_export") is True:
        native = effective_report.dispatch_report_action(options, export_action)
    else:
        native = getattr(effective_report, export_action)(options)
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
