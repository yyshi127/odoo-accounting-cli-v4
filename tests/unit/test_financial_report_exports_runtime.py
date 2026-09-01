from __future__ import annotations

import base64
import hashlib
import io
import json

import pytest

from odoo_accounting_cli_v4.bridge import client, runtime
from odoo_accounting_cli_v4.bridge import financial_report_exports_runtime as exports
from odoo_accounting_cli_v4.bridge.runtime import RuntimeFailure

_REPORT_ONLY = ("account.report",)
_SPECS = {
    "report.trial_balance.export": {
        "xml_id": "account_reports.trial_balance_report",
        "mode": "range",
        "models": _REPORT_ONLY,
    },
    "report.balance_sheet.export": {
        "xml_id": "account_reports.balance_sheet",
        "mode": "single",
        "models": _REPORT_ONLY,
    },
    "report.profit_and_loss.export": {
        "xml_id": "account_reports.profit_and_loss",
        "mode": "range",
        "models": _REPORT_ONLY,
    },
    "report.cash_flow.export": {
        "xml_id": "account_reports.cash_flow_report",
        "mode": "range",
        "models": _REPORT_ONLY,
    },
    "report.tax.export": {
        "xml_id": "account.generic_tax_report",
        "mode": "range",
        "models": _REPORT_ONLY,
    },
    "report.general_ledger.export": {
        "xml_id": "account_reports.general_ledger_report",
        "mode": "range",
        "models": _REPORT_ONLY,
    },
    "report.partner_ledger.export": {
        "xml_id": "account_reports.partner_ledger_report",
        "mode": "range",
        "models": _REPORT_ONLY,
    },
    "report.aged_receivable.export": {
        "xml_id": "account_reports.aged_receivable_report",
        "mode": "single",
        "models": _REPORT_ONLY,
    },
    "report.aged_payable.export": {
        "xml_id": "account_reports.aged_payable_report",
        "mode": "single",
        "models": _REPORT_ONLY,
    },
    "report.executive_summary.export": {
        "xml_id": "account_reports.executive_summary",
        "mode": "range",
        "models": _REPORT_ONLY,
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


class AccessModel:
    def __init__(self, access: bool = True) -> None:
        self.access = access
        self.calls = []

    def has_access(self, operation):
        self.calls.append(("has_access", operation))
        return self.access


class CompanyModel(AccessModel):
    def __init__(
        self,
        visible: bool,
        *,
        access: bool = True,
        country_id: int = 86,
        chart_template: str = "cn_oscg",
    ) -> None:
        super().__init__(access)
        self.visible = visible
        self.country_id = country_id
        self.chart_template = chart_template

    def search_count(self, domain, *, limit):
        self.calls.append(("search_count", domain, limit))
        return int(self.visible)

    def search_read(self, domain, *, fields, limit):
        self.calls.append(("search_read", domain, fields, limit))
        return [
            {
                "id": 7,
                "account_fiscal_country_id": [self.country_id, "Fiscal Country"],
                "chart_template": self.chart_template,
            }
        ]


class CountryModel(AccessModel):
    def __init__(self, code: str, *, access: bool = True) -> None:
        super().__init__(access)
        self.code = code

    def search_read(self, domain, *, fields, limit):
        self.calls.append(("search_read", domain, fields, limit))
        return [{"id": 86, "code": self.code}]


class PartnerModel(AccessModel):
    def __init__(self, available: bool = True, *, access: bool = True) -> None:
        super().__init__(access)
        self.available = available
        self.context = None

    def with_context(self, **context):
        self.context = context
        self.calls.append(("with_context", context))
        return self

    def search_count(self, domain, *, limit):
        self.calls.append(("search_count", domain, limit))
        return int(self.available)


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

    def dispatch_report_action(self, options, action):
        self.calls.append(("dispatch", action, options))
        return self.native


class ReportModel(AccessModel):
    def __init__(self, effective: EffectiveReport, *, access: bool) -> None:
        super().__init__(access)
        self.effective = effective

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
    def __init__(self, model_names: set[str]) -> None:
        self.model_names = model_names

    def get(self, model_name):
        return object() if model_name in self.model_names else None


class FakeEnv:
    uid = 42

    def __init__(
        self,
        *,
        visible: bool = True,
        installed: bool = True,
        xmlid_found: bool = True,
        access: bool = True,
        denied_model: str | None = None,
        missing_model: str | None = None,
        partner_available: bool = True,
        country_code: str = "CN",
        chart_template: str = "cn_oscg",
        native: dict | None = None,
        options: dict | None = None,
    ) -> None:
        self.company = CompanyModel(visible, chart_template=chart_template)
        self.effective = EffectiveReport(
            native
            or {
                "file_name": "report.pdf",
                "file_content": b"%PDF-example",
                "file_type": "pdf",
            }
        )
        self.report_model = ReportModel(self.effective, access=access)
        self.country = CountryModel(country_code)
        self.root = RootReport(options or {"report_id": 91})
        self.models = {
            "res.company": self.company,
            "account.report": self.report_model,
            "account.asset": AccessModel(),
            "account.move": AccessModel(),
            "account.move.line": AccessModel(),
            "account.cash.flow.line": AccessModel(),
            "account.tax": AccessModel(),
            "res.currency": AccessModel(),
            "res.country": self.country,
            "res.partner": PartnerModel(partner_available),
        }
        if denied_model is not None:
            self.models[denied_model].access = False
        registered_models = set(self.models) - {"res.company"}
        if not installed:
            registered_models.remove("account.report")
        if missing_model is not None:
            registered_models.remove(missing_model)
        self.registry = Registry(registered_models)
        self.xmlid_found = xmlid_found
        self.refs = []

    def __getitem__(self, model_name):
        return self.models[model_name]

    def ref(self, xml_id, *, raise_if_not_found):
        self.refs.append((xml_id, raise_if_not_found))
        return self.root if self.xmlid_found else None


@pytest.mark.parametrize(("capability_id", "expected"), _SPECS.items())
def test_all_nineteen_exports_use_the_fixed_spec_acl_and_options(
    capability_id: str, expected: dict
) -> None:
    xml_id = expected["xml_id"]
    mode = expected["mode"]
    country_code = expected.get("fiscal_country_code", "CN")
    chart_template = expected.get("chart_template", "cn_oscg")
    date_from = None if mode == "single" else "2026-01-01"
    env = FakeEnv(country_code=country_code, chart_template=chart_template)

    page = exports.dispatch(
        env,
        _payload(capability_id, date_from=date_from),
        7,
        failure_type=RuntimeFailure,
    )

    actual_spec = exports.CAPABILITY_SPECS[capability_id]
    assert actual_spec["xml_id"] == xml_id
    assert actual_spec["mode"] == mode
    assert actual_spec.get("models", _REPORT_ONLY) == expected["models"]
    assert actual_spec.get("fiscal_country_code") == expected.get(
        "fiscal_country_code"
    )
    assert actual_spec.get("chart_template") == expected.get("chart_template")
    assert actual_spec.get("dispatch_export", False) is expected.get(
        "dispatch_export", False
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
    assert ("has_access", "read") in env.company.calls
    for model_name in expected["models"]:
        assert ("has_access", "read") in env.models[model_name].calls
    if expected.get("dispatch_export"):
        assert env.effective.calls == [
            ("dispatch", "export_to_pdf", {"report_id": 91})
        ]
    else:
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


@pytest.mark.parametrize(
    ("capability_id", "xml_id", "mode", "date_from"),
    [
        (
            "report.customer_statement.export",
            "account_reports.customer_statement_report",
            "range",
            "2026-01-01",
        ),
        (
            "report.followup.export",
            "account_reports.followup_report",
            "single",
            None,
        ),
    ],
)
def test_partner_exports_scope_one_visible_partner_in_native_options(
    capability_id: str, xml_id: str, mode: str, date_from: str | None
) -> None:
    env = FakeEnv(options={"report_id": 91, "partner_ids": [17]})
    payload = _payload(capability_id, date_from=date_from)
    payload["partner_id"] = 17

    page = exports.dispatch(env, payload, 7, failure_type=RuntimeFailure)

    assert exports.CAPABILITY_SPECS[capability_id] == {
        "xml_id": xml_id,
        "mode": mode,
        "models": (
            "account.report",
            "account.move.line",
            "res.currency",
            "res.partner",
        ),
        "partner_parameter": True,
    }
    assert env.refs == [(xml_id, False)]
    assert env.models["res.partner"].calls == [
        ("has_access", "read"),
        (
            "with_context",
            {"active_test": False, "allowed_company_ids": [7]},
        ),
        (
            "search_count",
            [
                ("id", "=", 17),
                "|",
                ("company_id", "=", False),
                ("company_id", "=", 7),
            ],
            1,
        ),
    ]
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
                "partner_ids": [17],
            },
        ),
    ]
    assert env.effective.calls == [("pdf", {"report_id": 91, "partner_ids": [17]})]
    assert page["access_allowed"] is True


def test_partner_export_rejects_a_partner_outside_the_company_scope() -> None:
    env = FakeEnv(
        partner_available=False,
        options={"report_id": 91, "partner_ids": [17]},
    )
    payload = _payload("report.customer_statement.export")
    payload["partner_id"] = 17

    with pytest.raises(RuntimeFailure) as caught:
        exports.dispatch(env, payload, 7, failure_type=RuntimeFailure)

    assert caught.value.code == "company_unavailable"
    assert env.effective.calls == []


def test_partner_export_preserves_partner_read_acl() -> None:
    env = FakeEnv(
        denied_model="res.partner",
        options={"report_id": 91, "partner_ids": [17]},
    )
    payload = _payload("report.followup.export", date_from=None)
    payload["partner_id"] = 17

    page = exports.dispatch(env, payload, 7, failure_type=RuntimeFailure)

    assert page["module_installed"] is True
    assert page["access_allowed"] is False
    assert env.effective.calls == []


@pytest.mark.parametrize("partner_id", [None, 0, True])
def test_partner_export_payload_requires_a_positive_partner(partner_id: object) -> None:
    payload = _payload("report.customer_statement.export")
    if partner_id is not None:
        payload["partner_id"] = partner_id

    with pytest.raises(RuntimeFailure) as caught:
        exports.dispatch(FakeEnv(), payload, 7, failure_type=RuntimeFailure)

    assert caught.value.code == "bridge_protocol_error"


def test_non_partner_export_rejects_partner_payload() -> None:
    payload = _payload()
    payload["partner_id"] = 17

    with pytest.raises(RuntimeFailure) as caught:
        exports.dispatch(FakeEnv(), payload, 7, failure_type=RuntimeFailure)

    assert caught.value.code == "bridge_protocol_error"


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


def test_journal_xlsx_uses_the_native_report_action_dispatcher() -> None:
    env = FakeEnv(
        native={
            "file_name": "journal.xlsx",
            "file_content": b"PK\x03\x04journal",
            "file_type": "xlsx",
        }
    )

    exports.dispatch(
        env,
        _payload("report.journal.export", file_format="xlsx"),
        7,
        failure_type=RuntimeFailure,
    )

    assert env.effective.calls == [
        ("dispatch", "export_to_xlsx", {"report_id": 91})
    ]


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
    ("missing_model", "denied_model", "expected_module_installed"),
    [
        ("account.asset", None, False),
        (None, "account.asset", True),
    ],
)
def test_required_model_registration_and_read_acl_are_enforced(
    missing_model: str | None,
    denied_model: str | None,
    expected_module_installed: bool,
) -> None:
    env = FakeEnv(missing_model=missing_model, denied_model=denied_model)

    page = exports.dispatch(
        env,
        _payload("report.asset.export"),
        7,
        failure_type=RuntimeFailure,
    )

    assert page["module_installed"] is expected_module_installed
    assert page["access_allowed"] is False
    assert env.effective.calls == []


@pytest.mark.parametrize(
    ("capability_id", "country_code", "chart_template"),
    [
        ("report.china.balance_sheet.export", "SG", "cn_oscg"),
        ("report.china.profit_and_loss.export", "CN", "sg"),
        ("report.china.cash_flow.export", "SG", "cn_oscg"),
        ("report.singapore.gst.export", "CN", "sg"),
    ],
)
def test_localized_exports_require_the_company_country_and_chart(
    capability_id: str, country_code: str, chart_template: str
) -> None:
    mode = _SPECS[capability_id]["mode"]
    env = FakeEnv(country_code=country_code, chart_template=chart_template)

    page = exports.dispatch(
        env,
        _payload(capability_id, date_from=None if mode == "single" else "2026-01-01"),
        7,
        failure_type=RuntimeFailure,
    )

    assert page["module_installed"] is False
    assert page["access_allowed"] is False
    assert env.refs == []
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
