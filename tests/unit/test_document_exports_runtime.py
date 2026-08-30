from __future__ import annotations

import base64
import copy
import hashlib
import io
import json

import pytest

from odoo_accounting_cli_v4.bridge import document_exports_runtime as exports
from odoo_accounting_cli_v4.bridge import runtime
from odoo_accounting_cli_v4.bridge.runtime import RuntimeFailure

EXPECTED = {
    "invoice.pdf.export": {
        "model": "account.move",
        "id_parameter": "move_id",
        "xml_id": "account.account_invoices",
        "report_name": "account.report_invoice_with_payments",
        "filename_prefix": "invoice-with-payments",
    },
    "payment.receipt.pdf.export": {
        "model": "account.payment",
        "id_parameter": "payment_id",
        "xml_id": "account.action_report_payment_receipt",
        "report_name": "account.report_payment_receipt",
        "filename_prefix": "payment-receipt",
    },
    "bank.statement.pdf.export": {
        "model": "account.bank.statement",
        "id_parameter": "statement_id",
        "xml_id": "account.action_report_account_statement",
        "report_name": "account.report_statement",
        "filename_prefix": "bank-statement",
    },
    "sale.order.pdf.export": {
        "model": "sale.order",
        "id_parameter": "order_id",
        "xml_id": "sale.action_report_saleorder",
        "report_name": "sale.report_saleorder",
        "filename_prefix": "sale-order",
    },
    "purchase.order.pdf.export": {
        "model": "purchase.order",
        "id_parameter": "order_id",
        "xml_id": "purchase.action_report_purchase_order",
        "report_name": "purchase.report_purchaseorder",
        "filename_prefix": "purchase-order",
    },
    "purchase.rfq.pdf.export": {
        "model": "purchase.order",
        "id_parameter": "order_id",
        "xml_id": "purchase.report_purchase_quotation",
        "report_name": "purchase.report_purchasequotation",
        "filename_prefix": "request-for-quotation",
    },
    "stock.delivery_slip.pdf.export": {
        "model": "stock.picking",
        "id_parameter": "transfer_id",
        "xml_id": "stock.action_report_delivery",
        "report_name": "stock.report_deliveryslip",
        "filename_prefix": "delivery-slip",
    },
    "stock.picking_operations.pdf.export": {
        "model": "stock.picking",
        "id_parameter": "transfer_id",
        "xml_id": "stock.action_report_picking",
        "report_name": "stock.report_picking",
        "filename_prefix": "picking-operations",
    },
    "stock.return_slip.pdf.export": {
        "model": "stock.picking",
        "id_parameter": "transfer_id",
        "xml_id": "stock.return_label_report",
        "report_name": "stock.report_return_document",
        "filename_prefix": "return-slip",
    },
    "localization.china.voucher.render": {
        "model": "account.move",
        "id_parameter": "move_id",
        "xml_id": "l10n_cn_reports.action_report_account_move_print",
        "report_name": "l10n_cn_reports.report_account_move_print",
        "filename_prefix": "china-voucher",
    },
}


def _payload(capability_id: str, *, layout: str = "with_payments") -> dict:
    expected = EXPECTED[capability_id]
    payload = {
        "capability_id": capability_id,
        "company_id": 7,
        expected["id_parameter"]: 37,
    }
    if capability_id == "invoice.pdf.export":
        payload["layout"] = layout
    return payload


def _target_row(capability_id: str) -> dict:
    row = {"id": 37, "company_id": 7}
    if capability_id == "invoice.pdf.export":
        row.update(move_type="out_invoice", state="posted")
    elif capability_id == "payment.receipt.pdf.export":
        row["state"] = "paid"
    elif capability_id == "sale.order.pdf.export":
        row["state"] = "sale"
    elif capability_id == "purchase.order.pdf.export":
        row["state"] = "purchase"
    elif capability_id == "purchase.rfq.pdf.export":
        row["state"] = "draft"
    elif capability_id.startswith("stock."):
        row["state"] = "done"
        if capability_id == "stock.delivery_slip.pdf.export":
            row["picking_type_code"] = "outgoing"
    elif capability_id == "localization.china.voucher.render":
        row.update(move_type="entry", state="posted")
    return row


class Registry:
    def __init__(self, models: set[str]) -> None:
        self.models = models

    def get(self, model_name):
        return object() if model_name in self.models else None


class Model:
    def __init__(self, rows: list[dict] | None = None, *, access: bool = True) -> None:
        self.rows = rows or []
        self.access = access
        self.calls: list[tuple] = []

    def has_access(self, operation):
        self.calls.append(("has_access", operation))
        return self.access

    def with_context(self, **context):
        self.calls.append(("with_context", context))
        return self

    def search_read(self, domain, *, fields, limit):
        self.calls.append(("search_read", domain, fields, limit))
        return copy.deepcopy(self.rows)


class ReportModel(Model):
    def __init__(self, native: tuple[bytes, str]) -> None:
        super().__init__()
        self.native = native

    def _render_qweb_pdf(self, xml_id, *, res_ids):
        self.calls.append(("render", xml_id, res_ids))
        return self.native


class ReportAction:
    report_type = "qweb-pdf"
    group_ids = None

    def __init__(self, model: str, report_name: str) -> None:
        self.model = model
        self.report_name = report_name

    def __bool__(self):
        return True


class Ids:
    def __init__(self) -> None:
        self.ids: list[int] = []


class User:
    def __init__(self) -> None:
        self.all_group_ids = Ids()


class Env:
    uid = 42

    def __init__(
        self,
        capability_id: str,
        *,
        company_visible: bool = True,
        report_found: bool = True,
        access_allowed: bool = True,
        record_visible: bool = True,
        applicable: bool = True,
        native: tuple[bytes, str] = (b"%PDF-1.7\ndocument", "pdf"),
    ) -> None:
        self.user = User()
        expected = EXPECTED[capability_id]
        company_row = {"id": 7}
        if capability_id == "localization.china.voucher.render":
            company_row.update(
                account_fiscal_country_id=[86, "China"],
                chart_template="cn_oscg",
            )
        row = _target_row(capability_id)
        if not applicable:
            row["state"] = "cancel"
        self.company = Model([company_row] if company_visible else [])
        self.target = Model([row] if record_visible else [], access=access_allowed)
        self.report = ReportModel(native)
        self.country = Model([{"id": 86, "code": "CN"}])
        self.models = {
            "res.company": self.company,
            expected["model"]: self.target,
            "ir.actions.report": self.report,
            "res.country": self.country,
        }
        self.registry = Registry(set(self.models))
        self.action = (
            ReportAction(expected["model"], expected["report_name"])
            if report_found
            else None
        )
        self.refs: list[tuple] = []

    def __getitem__(self, model_name):
        return self.models[model_name]

    def ref(self, xml_id, *, raise_if_not_found):
        self.refs.append((xml_id, raise_if_not_found))
        return self.action


@pytest.mark.parametrize("capability_id", EXPECTED)
def test_all_fixed_document_specs_render_verified_pdf_without_attachments(
    capability_id: str,
) -> None:
    expected = EXPECTED[capability_id]
    env = Env(capability_id)

    page = exports.dispatch(
        env,
        _payload(capability_id),
        7,
        failure_type=RuntimeFailure,
    )

    spec = exports.CAPABILITY_SPECS[capability_id]
    assert spec["model"] == expected["model"]
    assert spec["id_parameter"] == expected["id_parameter"]
    report_spec = spec["layouts"]["with_payments"] if "layouts" in spec else spec
    assert report_spec["xml_id"] == expected["xml_id"]
    assert report_spec["report_name"] == expected["report_name"]
    assert env.refs == [(expected["xml_id"], False)]
    assert ("has_access", "read") in env.target.calls
    assert (
        "with_context",
        {"allowed_company_ids": [7], "report_pdf_no_attachment": True},
    ) in env.report.calls
    assert ("render", expected["xml_id"], [37]) in env.report.calls
    content = base64.b64decode(page["content_base64"])
    assert content.startswith(b"%PDF-")
    assert page["filename"] == f"{expected['filename_prefix']}-37.pdf"
    assert page["byte_count"] == len(content)
    assert page["sha256"] == hashlib.sha256(content).hexdigest()


def test_invoice_layouts_are_both_frozen_and_not_caller_injectable() -> None:
    layouts = exports.CAPABILITY_SPECS["invoice.pdf.export"]["layouts"]
    assert {
        name: (spec["xml_id"], spec["report_name"]) for name, spec in layouts.items()
    } == {
        "with_payments": (
            "account.account_invoices",
            "account.report_invoice_with_payments",
        ),
        "without_payments": (
            "account.account_invoices_without_payment",
            "account.report_invoice",
        ),
    }

    env = Env("invoice.pdf.export")
    env.action = ReportAction("account.move", "account.report_invoice")
    exports.dispatch(
        env,
        _payload("invoice.pdf.export", layout="without_payments"),
        7,
        failure_type=RuntimeFailure,
    )
    assert env.refs == [("account.account_invoices_without_payment", False)]


@pytest.mark.parametrize(
    "change",
    [
        lambda payload: payload.update(model="res.users"),
        lambda payload: payload.update(xml_id="base.report_users"),
        lambda payload: payload.update(move_id=True),
        lambda payload: payload.update(layout="custom"),
        lambda payload: payload.update(company_id=8),
    ],
)
def test_runtime_payload_is_closed_and_rejects_invalid_ids_or_layout(change) -> None:
    payload = _payload("invoice.pdf.export")
    change(payload)

    with pytest.raises(RuntimeFailure) as caught:
        exports.dispatch(
            Env("invoice.pdf.export"),
            payload,
            7,
            failure_type=RuntimeFailure,
        )

    assert caught.value.code == "bridge_protocol_error"


@pytest.mark.parametrize(
    ("scenario", "expected"),
    [
        ("company", (False, True, False, False, False)),
        ("module", (True, False, False, False, False)),
        ("access", (True, True, False, False, False)),
        ("record", (True, True, True, False, False)),
        ("applicable", (True, True, True, True, False)),
    ],
)
def test_runtime_returns_typed_empty_pages_for_scope_acl_and_record_gates(
    scenario: str,
    expected: tuple[bool, bool, bool, bool, bool],
) -> None:
    env = Env(
        "sale.order.pdf.export",
        company_visible=scenario != "company",
        report_found=scenario != "module",
        access_allowed=scenario != "access",
        record_visible=scenario != "record",
        applicable=scenario != "applicable",
    )

    page = exports.dispatch(
        env,
        _payload("sale.order.pdf.export"),
        7,
        failure_type=RuntimeFailure,
    )

    flags = tuple(
        page[key]
        for key in (
            "company_visible",
            "module_installed",
            "access_allowed",
            "record_visible",
            "applicable",
        )
    )
    assert flags == expected
    assert page["format"] == "pdf"
    assert page["byte_count"] == 0
    assert all(
        page[key] is None
        for key in ("filename", "mimetype", "sha256", "content_base64")
    )
    assert not any(call[0] == "render" for call in env.report.calls)


def test_runtime_rejects_non_pdf_native_content() -> None:
    with pytest.raises(RuntimeFailure) as caught:
        exports.dispatch(
            Env("sale.order.pdf.export", native=(b"not-pdf", "pdf")),
            _payload("sale.order.pdf.export"),
            7,
            failure_type=RuntimeFailure,
        )

    assert caught.value.code == "odoo_runtime_error"


def test_document_export_action_is_allowlisted_with_a_read_only_cursor() -> None:
    request = {
        "schema_version": "v1",
        "target": {
            "alias": "v4-dev",
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "zh_CN",
            "timezone": "Asia/Shanghai",
        },
        "action": exports.ACTION,
        "payload": _payload("sale.order.pdf.export"),
    }

    decoded = runtime._decode_request(io.StringIO(json.dumps(request)))

    assert decoded["action"] == "ir.actions.report.fixed_document_export"
    assert runtime._cursor_factory_for(exports.ACTION, decoded["payload"]) is (
        runtime._read_only_cursor
    )
