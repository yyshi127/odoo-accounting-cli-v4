from __future__ import annotations

import base64
import hashlib
import io
import json

import pytest

from odoo_accounting_cli_v4.bridge import client, runtime
from odoo_accounting_cli_v4.bridge import financial_report_exports_runtime as exports
from odoo_accounting_cli_v4.bridge.runtime import RuntimeFailure

_SPECS = {
    "report.trial_balance.export": (
        "account_reports.trial_balance_report",
        "range",
    ),
    "report.balance_sheet.export": ("account_reports.balance_sheet", "single"),
    "report.profit_and_loss.export": (
        "account_reports.profit_and_loss",
        "range",
    ),
    "report.cash_flow.export": ("account_reports.cash_flow_report", "range"),
    "report.tax.export": ("account.generic_tax_report", "range"),
    "report.general_ledger.export": (
        "account_reports.general_ledger_report",
        "range",
    ),
    "report.partner_ledger.export": (
        "account_reports.partner_ledger_report",
        "range",
    ),
    "report.aged_receivable.export": (
        "account_reports.aged_receivable_report",
        "single",
    ),
    "report.aged_payable.export": (
        "account_reports.aged_payable_report",
        "single",
    ),
    "report.executive_summary.export": (
        "account_reports.executive_summary",
        "range",
    ),
}


def _payload(
    capability_id: str = "report.trial_balance.export",
    *,
    date_from: str | None = "2026-01-01",
    file_format: str = "pdf",
) -> dict:
    return {
        "capability_id": capability_id,
        "company_id": 7,
        "date_from": date_from,
        "date_to": "2026-08-28",
        "format": file_format,
    }


class CompanyModel:
    def __init__(self, visible: bool) -> None:
        self.visible = visible
        self.calls = []

    def search_count(self, domain, *, limit):
        self.calls.append((domain, limit))
        return int(self.visible)


class EffectiveReport:
    def __init__(self, native: dict) -> None:
        self.native = native
        self.calls = []

    def export_to_pdf(self, options):
        self.calls.append(("pdf", options))
        return self.native

    def export_to_xlsx(self, options):
        self.calls.append(("xlsx", options))
        return self.native


class ReportModel:
    def __init__(self, effective: EffectiveReport, *, access: bool) -> None:
        self.effective = effective
        self.access = access
        self.calls = []

    def has_access(self, operation):
        self.calls.append(("has_access", operation))
        return self.access

    def with_context(self, **context):
        self.calls.append(("with_context", context))
        return self

    def browse(self, report_id):
        self.calls.append(("browse", report_id))
        return self.effective


class RootReport:
    def __init__(self, options: dict) -> None:
        self.options = options
        self.calls = []

    def __bool__(self):
        return True

    def with_context(self, **context):
        self.calls.append(("with_context", context))
        return self

    def get_options(self, previous_options):
        self.calls.append(("get_options", previous_options))
        return self.options


class Registry:
    def __init__(self, installed: bool) -> None:
        self.installed = installed

    def get(self, model_name):
        assert model_name == "account.report"
        return object() if self.installed else None


class FakeEnv:
    uid = 42

    def __init__(
        self,
        *,
        visible: bool = True,
        installed: bool = True,
        xmlid_found: bool = True,
        access: bool = True,
        native: dict | None = None,
        options: dict | None = None,
    ) -> None:
        self.company = CompanyModel(visible)
        self.effective = EffectiveReport(
            native
            or {
                "file_name": "report.pdf",
                "file_content": b"%PDF-example",
                "file_type": "pdf",
            }
        )
        self.report_model = ReportModel(self.effective, access=access)
        self.root = RootReport(options or {"report_id": 91})
        self.registry = Registry(installed)
        self.xmlid_found = xmlid_found
        self.refs = []

    def __getitem__(self, model_name):
        return {
            "res.company": self.company,
            "account.report": self.report_model,
        }[model_name]

    def ref(self, xml_id, *, raise_if_not_found):
        self.refs.append((xml_id, raise_if_not_found))
        return self.root if self.xmlid_found else None


@pytest.mark.parametrize(("capability_id", "expected"), _SPECS.items())
def test_all_ten_exports_use_the_fixed_xmlid_mode_and_options(
    capability_id: str, expected: tuple[str, str]
) -> None:
    xml_id, mode = expected
    date_from = None if mode == "single" else "2026-01-01"
    env = FakeEnv()

    page = exports.dispatch(
        env,
        _payload(capability_id, date_from=date_from),
        7,
        failure_type=RuntimeFailure,
    )

    assert env.refs == [(xml_id, False)]
    assert env.root.calls == [
        ("with_context", {"allowed_company_ids": [7]}),
        (
            "get_options",
            {
                "all_entries": False,
                "date": {
                    "date_from": date_from if date_from is not None else False,
                    "date_to": "2026-08-28",
                    "mode": mode,
                    "filter": "custom",
                },
            },
        ),
    ]
    assert env.report_model.calls == [
        ("has_access", "read"),
        ("with_context", {"allowed_company_ids": [7]}),
        ("browse", 91),
    ]
    assert env.effective.calls == [("pdf", {"report_id": 91})]
    assert page == {
        "user_id": 42,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "filename": "report.pdf",
        "format": "pdf",
        "mimetype": "application/pdf",
        "byte_count": 12,
        "sha256": hashlib.sha256(b"%PDF-example").hexdigest(),
        "content_base64": base64.b64encode(b"%PDF-example").decode("ascii"),
    }


def test_xlsx_accepts_bytes_like_content_and_uses_standard_base64() -> None:
    content = memoryview(b"PK\x03\x04xlsx")
    env = FakeEnv(
        native={
            "file_name": "report.xlsx",
            "file_content": content,
            "file_type": "xlsx",
        }
    )

    page = exports.dispatch(
        env,
        _payload(file_format="xlsx"),
        7,
        failure_type=RuntimeFailure,
    )

    assert env.effective.calls == [("xlsx", {"report_id": 91})]
    assert page["mimetype"] == (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert page["content_base64"] == "UEsDBHhsc3g="
    assert base64.b64decode(page["content_base64"], validate=True) == bytes(content)


@pytest.mark.parametrize(
    ("visible", "installed", "xmlid_found", "access", "expected"),
    [
        (False, True, True, True, (False, True, False)),
        (True, False, False, True, (True, False, False)),
        (True, True, False, True, (True, False, False)),
        (True, True, True, False, (True, True, False)),
    ],
)
def test_scope_or_access_failure_returns_only_empty_file_metadata(
    visible: bool,
    installed: bool,
    xmlid_found: bool,
    access: bool,
    expected: tuple[bool, bool, bool],
) -> None:
    env = FakeEnv(
        visible=visible,
        installed=installed,
        xmlid_found=xmlid_found,
        access=access,
    )

    page = exports.dispatch(
        env,
        _payload(),
        7,
        failure_type=RuntimeFailure,
    )

    company_visible, module_installed, access_allowed = expected
    assert page == {
        "user_id": 42,
        "company_visible": company_visible,
        "module_installed": module_installed,
        "access_allowed": access_allowed,
        "filename": None,
        "format": "pdf",
        "mimetype": None,
        "byte_count": 0,
        "sha256": None,
        "content_base64": None,
    }
    assert env.effective.calls == []


@pytest.mark.parametrize(
    "native",
    [
        {
            "file_name": "report.pdf",
            "file_content": "%PDF-text-is-not-bytes",
            "file_type": "pdf",
        },
        {
            "file_name": "report.pdf",
            "file_content": b"not-a-pdf",
            "file_type": "pdf",
        },
        {
            "file_name": "report.pdf",
            "file_content": b"%PDF-example",
            "file_type": "xlsx",
        },
    ],
)
def test_native_type_file_type_and_magic_are_verified(native: dict) -> None:
    with pytest.raises(RuntimeFailure) as caught:
        exports.dispatch(
            FakeEnv(native=native),
            _payload(),
            7,
            failure_type=RuntimeFailure,
        )

    assert caught.value.code == "odoo_runtime_error"


def test_decoded_file_size_has_a_fixed_hard_limit(monkeypatch) -> None:
    monkeypatch.setattr(exports, "MAX_FILE_BYTES", 8)
    env = FakeEnv(
        native={
            "file_name": "report.pdf",
            "file_content": b"%PDF-nine",
            "file_type": "pdf",
        }
    )

    with pytest.raises(RuntimeFailure) as caught:
        exports.dispatch(env, _payload(), 7, failure_type=RuntimeFailure)

    assert caught.value.code == "odoo_runtime_error"


@pytest.mark.parametrize(
    "payload",
    [
        {**_payload(), "unexpected": True},
        _payload("trial_balance"),
        _payload("report.balance_sheet.export", date_from="2026-01-01"),
        _payload(date_from=None),
        {**_payload(), "date_to": "2026-02-30"},
        {**_payload(), "format": "csv"},
        {**_payload(), "format": []},
        {**_payload(), "capability_id": []},
    ],
)
def test_payload_is_closed_and_dates_follow_the_report_mode(payload: dict) -> None:
    with pytest.raises(RuntimeFailure) as caught:
        exports.dispatch(FakeEnv(), payload, 7, failure_type=RuntimeFailure)

    assert caught.value.code == "bridge_protocol_error"


def test_fixed_export_action_is_allowlisted_and_uses_the_read_only_cursor() -> None:
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
        "payload": _payload(),
    }

    decoded = runtime._decode_request(io.StringIO(json.dumps(request)))

    assert decoded["action"] == exports.ACTION
    assert runtime._cursor_factory_for(exports.ACTION, decoded["payload"]) is (
        runtime._read_only_cursor
    )


def test_bridge_response_limit_can_carry_the_fixed_export_limit() -> None:
    maximum_base64_chars = 4 * ((exports.MAX_FILE_BYTES + 2) // 3)

    assert client._MAX_RESPONSE_CHARS > maximum_base64_chars
