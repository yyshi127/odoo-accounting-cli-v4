"""Odoo-side runtime for fixed read-only business-document PDF exports."""

from __future__ import annotations

import base64
import hashlib
from typing import Any

ACTION = "ir.actions.report.fixed_document_export"
MAX_FILE_BYTES = 64 * 1024 * 1024
_DOCUMENT_MOVE_TYPES = frozenset(
    {
        "out_invoice",
        "out_refund",
        "out_receipt",
        "in_invoice",
        "in_refund",
        "in_receipt",
    }
)
_ACTIVE_TRANSFER_STATES = frozenset(
    {"draft", "waiting", "confirmed", "assigned", "done"}
)
CAPABILITY_SPECS = {
    "invoice.pdf.export": {
        "model": "account.move",
        "id_parameter": "move_id",
        "layouts": {
            "with_payments": {
                "xml_id": "account.account_invoices",
                "report_name": "account.report_invoice_with_payments",
                "filename_prefix": "invoice-with-payments",
            },
            "without_payments": {
                "xml_id": "account.account_invoices_without_payment",
                "report_name": "account.report_invoice",
                "filename_prefix": "invoice-without-payments",
            },
        },
        "fields": ("move_type", "state"),
        "move_types": _DOCUMENT_MOVE_TYPES,
        "states": frozenset({"draft", "posted"}),
    },
    "payment.receipt.pdf.export": {
        "model": "account.payment",
        "id_parameter": "payment_id",
        "xml_id": "account.action_report_payment_receipt",
        "report_name": "account.report_payment_receipt",
        "filename_prefix": "payment-receipt",
        "fields": ("state",),
        "states": frozenset({"in_process", "paid"}),
    },
    "bank.statement.pdf.export": {
        "model": "account.bank.statement",
        "id_parameter": "statement_id",
        "xml_id": "account.action_report_account_statement",
        "report_name": "account.report_statement",
        "filename_prefix": "bank-statement",
        "fields": (),
    },
    "sale.order.pdf.export": {
        "model": "sale.order",
        "id_parameter": "order_id",
        "xml_id": "sale.action_report_saleorder",
        "report_name": "sale.report_saleorder",
        "filename_prefix": "sale-order",
        "fields": ("state",),
        "states": frozenset({"draft", "sent", "sale"}),
    },
    "purchase.order.pdf.export": {
        "model": "purchase.order",
        "id_parameter": "order_id",
        "xml_id": "purchase.action_report_purchase_order",
        "report_name": "purchase.report_purchaseorder",
        "filename_prefix": "purchase-order",
        "fields": ("state",),
        "states": frozenset({"purchase"}),
    },
    "purchase.rfq.pdf.export": {
        "model": "purchase.order",
        "id_parameter": "order_id",
        "xml_id": "purchase.report_purchase_quotation",
        "report_name": "purchase.report_purchasequotation",
        "filename_prefix": "request-for-quotation",
        "fields": ("state",),
        "states": frozenset({"draft", "sent"}),
    },
    "stock.delivery_slip.pdf.export": {
        "model": "stock.picking",
        "id_parameter": "transfer_id",
        "xml_id": "stock.action_report_delivery",
        "report_name": "stock.report_deliveryslip",
        "filename_prefix": "delivery-slip",
        "fields": ("state", "picking_type_code"),
        "states": _ACTIVE_TRANSFER_STATES,
        "picking_type_codes": frozenset({"outgoing"}),
    },
    "stock.picking_operations.pdf.export": {
        "model": "stock.picking",
        "id_parameter": "transfer_id",
        "xml_id": "stock.action_report_picking",
        "report_name": "stock.report_picking",
        "filename_prefix": "picking-operations",
        "fields": ("state",),
        "states": _ACTIVE_TRANSFER_STATES,
    },
    "stock.return_slip.pdf.export": {
        "model": "stock.picking",
        "id_parameter": "transfer_id",
        "xml_id": "stock.return_label_report",
        "report_name": "stock.report_return_document",
        "filename_prefix": "return-slip",
        "fields": ("state",),
        "states": _ACTIVE_TRANSFER_STATES,
    },
    "localization.china.voucher.render": {
        "model": "account.move",
        "id_parameter": "move_id",
        "xml_id": "l10n_cn_reports.action_report_account_move_print",
        "report_name": "l10n_cn_reports.report_account_move_print",
        "filename_prefix": "china-voucher",
        "fields": ("move_type", "state"),
        "move_types": frozenset({"entry"}),
        "states": frozenset({"posted"}),
        "required_models": ("res.country",),
        "fiscal_country_code": "CN",
        "chart_template": "cn_oscg",
    },
}


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


def _positive_id(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _reference_id(value: Any, failure_type: Any) -> int | None:
    if value is False or value is None:
        return None
    if _positive_id(value):
        return value
    if isinstance(value, (list, tuple)) and len(value) == 2 and _positive_id(value[0]):
        return value[0]
    raise _runtime_failure(failure_type)


def _report_spec(spec: dict[str, Any], layout: str | None) -> dict[str, Any]:
    layouts = spec.get("layouts")
    if layouts is None:
        return spec
    return layouts[layout]


def _validated_payload(
    payload: Any, company_id: int, failure_type: Any
) -> tuple[dict[str, Any], dict[str, Any], int, str | None]:
    if not isinstance(payload, dict):
        raise _protocol_failure(failure_type)
    capability_id = payload.get("capability_id")
    if not isinstance(capability_id, str) or capability_id not in CAPABILITY_SPECS:
        raise _protocol_failure(failure_type)
    spec = CAPABILITY_SPECS[capability_id]
    expected = {"capability_id", "company_id", spec["id_parameter"]}
    layouts = spec.get("layouts")
    if layouts is not None:
        expected.add("layout")
    if set(payload) != expected:
        raise _protocol_failure(failure_type)
    requested_company_id = payload["company_id"]
    target_id = payload[spec["id_parameter"]]
    layout = payload.get("layout")
    if (
        not _positive_id(requested_company_id)
        or requested_company_id != company_id
        or not _positive_id(target_id)
        or layouts is not None
        and (not isinstance(layout, str) or layout not in layouts)
        or layouts is None
        and layout is not None
    ):
        raise _protocol_failure(failure_type)
    return spec, _report_spec(spec, layout), target_id, layout


def _empty_page(
    env: Any,
    *,
    company_visible: bool,
    module_installed: bool,
    access_allowed: bool,
    record_visible: bool = False,
    applicable: bool = False,
) -> dict[str, Any]:
    return {
        "user_id": env.uid,
        "company_visible": company_visible,
        "module_installed": module_installed,
        "access_allowed": access_allowed,
        "record_visible": record_visible,
        "applicable": applicable,
        "filename": None,
        "format": "pdf",
        "mimetype": None,
        "byte_count": 0,
        "sha256": None,
        "content_base64": None,
    }


def _model_available(env: Any, model_name: str) -> bool:
    return env.registry.get(model_name) is not None


def _action_matches(
    report_action: Any,
    *,
    model_name: str,
    report_name: str,
) -> bool:
    return bool(
        report_action
        and getattr(report_action, "model", None) == model_name
        and getattr(report_action, "report_type", None) == "qweb-pdf"
        and getattr(report_action, "report_name", None) == report_name
    )


def _report_group_allowed(env: Any, report_action: Any) -> bool:
    action_groups = getattr(report_action, "group_ids", None)
    if not action_groups:
        return True
    action_group_ids = getattr(action_groups, "ids", None)
    user_groups = getattr(env.user, "all_group_ids", None)
    user_group_ids = getattr(user_groups, "ids", None)
    if not isinstance(action_group_ids, list) or not isinstance(user_group_ids, list):
        return False
    return bool(set(action_group_ids) & set(user_group_ids))


def _record_applicable(
    env: Any,
    *,
    spec: dict[str, Any],
    row: dict[str, Any],
    company_row: dict[str, Any],
    company_id: int,
    failure_type: Any,
) -> bool:
    states = spec.get("states")
    if states is not None and row.get("state") not in states:
        return False
    move_types = spec.get("move_types")
    if move_types is not None and row.get("move_type") not in move_types:
        return False
    picking_type_codes = spec.get("picking_type_codes")
    if (
        picking_type_codes is not None
        and row.get("picking_type_code") not in picking_type_codes
    ):
        return False
    expected_country_code = spec.get("fiscal_country_code")
    if expected_country_code is None:
        return True
    if company_row.get("chart_template") != spec.get("chart_template"):
        return False
    country_id = _reference_id(
        company_row.get("account_fiscal_country_id"), failure_type
    )
    if country_id is None:
        return False
    countries = (
        env["res.country"]
        .with_context(allowed_company_ids=[company_id])
        .search_read(
            [("id", "=", country_id)],
            fields=["id", "code"],
            limit=1,
        )
    )
    return bool(
        len(countries) == 1
        and countries[0].get("id") == country_id
        and countries[0].get("code") == expected_country_code
    )


def _file_bytes(value: Any, failure_type: Any) -> bytes:
    if not isinstance(value, (bytes, bytearray, memoryview)):
        raise _runtime_failure(failure_type)
    byte_count = value.nbytes if isinstance(value, memoryview) else len(value)
    if byte_count > MAX_FILE_BYTES:
        raise _runtime_failure(failure_type)
    try:
        content = bytes(value)
    except (TypeError, ValueError) as exc:
        raise _runtime_failure(failure_type) from exc
    if len(content) != byte_count or not content.startswith(b"%PDF-"):
        raise _runtime_failure(failure_type)
    return content


def dispatch(
    env: Any,
    payload: dict[str, Any],
    company_id: int,
    *,
    failure_type: Any,
) -> dict[str, Any]:
    spec, report_spec, target_id, _layout = _validated_payload(
        payload, company_id, failure_type
    )
    required_models = (
        "res.company",
        "ir.actions.report",
        spec["model"],
        *spec.get("required_models", ()),
    )
    models_available = all(
        _model_available(env, model_name) for model_name in required_models
    )
    report_action = (
        env.ref(report_spec["xml_id"], raise_if_not_found=False)
        if models_available
        else None
    )
    module_installed = bool(
        models_available
        and _action_matches(
            report_action,
            model_name=spec["model"],
            report_name=report_spec["report_name"],
        )
    )

    company_model = env["res.company"]
    company_read_allowed = bool(company_model.has_access("read"))
    company_fields = ["id"]
    if spec.get("fiscal_country_code") is not None:
        company_fields.extend(["account_fiscal_country_id", "chart_template"])
    company_rows = (
        company_model.with_context(allowed_company_ids=[company_id]).search_read(
            [("id", "=", company_id)],
            fields=company_fields,
            limit=1,
        )
        if company_read_allowed
        else []
    )
    if len(company_rows) > 1:
        raise _runtime_failure(failure_type)
    company_visible = bool(
        len(company_rows) == 1 and company_rows[0].get("id") == company_id
    )
    target_model = env[spec["model"]] if models_available else None
    report_model = env["ir.actions.report"] if models_available else None
    extra_access_allowed = bool(
        models_available
        and all(
            env[model_name].has_access("read")
            for model_name in spec.get("required_models", ())
        )
    )
    access_allowed = bool(
        company_visible
        and module_installed
        and company_read_allowed
        and target_model is not None
        and target_model.has_access("read")
        and report_model is not None
        and report_model.has_access("read")
        and extra_access_allowed
        and _report_group_allowed(env, report_action)
    )
    if not access_allowed:
        return _empty_page(
            env,
            company_visible=company_visible,
            module_installed=module_installed,
            access_allowed=False,
        )

    target_fields = ["id", "company_id", *spec.get("fields", ())]
    target_rows = target_model.with_context(
        allowed_company_ids=[company_id]
    ).search_read(
        [("id", "=", target_id), ("company_id", "=", company_id)],
        fields=target_fields,
        limit=1,
    )
    if len(target_rows) > 1:
        raise _runtime_failure(failure_type)
    if not target_rows:
        return _empty_page(
            env,
            company_visible=True,
            module_installed=True,
            access_allowed=True,
        )
    row = target_rows[0]
    if (
        row.get("id") != target_id
        or _reference_id(row.get("company_id"), failure_type) != company_id
    ):
        raise _runtime_failure(failure_type)
    applicable = _record_applicable(
        env,
        spec=spec,
        row=row,
        company_row=company_rows[0],
        company_id=company_id,
        failure_type=failure_type,
    )
    if not applicable:
        return _empty_page(
            env,
            company_visible=True,
            module_installed=True,
            access_allowed=True,
            record_visible=True,
        )

    native = report_model.with_context(
        allowed_company_ids=[company_id],
        report_pdf_no_attachment=True,
    )._render_qweb_pdf(report_spec["xml_id"], res_ids=[target_id])
    if not isinstance(native, (list, tuple)) or len(native) != 2 or native[1] != "pdf":
        raise _runtime_failure(failure_type)
    content = _file_bytes(native[0], failure_type)
    filename = f"{report_spec['filename_prefix']}-{target_id}.pdf"
    return {
        "user_id": env.uid,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "record_visible": True,
        "applicable": True,
        "filename": filename,
        "format": "pdf",
        "mimetype": "application/pdf",
        "byte_count": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "content_base64": base64.b64encode(content).decode("ascii"),
    }
