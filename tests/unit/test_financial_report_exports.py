from __future__ import annotations

import base64
import copy
import hashlib

import pytest

from odoo_accounting_cli_v4.capabilities.financial_reports import (
    FINANCIAL_REPORT_EXPORTS,
    FinancialReportError,
    export_financial_report,
    validate_financial_report_export_request,
)


def _request(capability_id: str, *, export_format: str = "pdf") -> dict:
    parameters = (
        {"as_of": "2025-01-31", "format": export_format}
        if FINANCIAL_REPORT_EXPORTS[capability_id]["mode"] == "single"
        else {
            "date_from": "2025-01-01",
            "date_to": "2025-01-31",
            "format": export_format,
        }
    )
    return {
        "schema_version": "v1",
        "request_id": "28b85ef8-87d1-4537-a13d-762b0459b22e",
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }


def _page(export_format: str = "pdf") -> dict:
    content = b"%PDF-1.7\nreport" if export_format == "pdf" else b"PK\x03\x04xlsx"
    return {
        "user_id": 42,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "filename": f"accounting-report.{export_format}",
        "format": export_format,
        "mimetype": (
            "application/pdf"
            if export_format == "pdf"
            else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        "byte_count": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "content_base64": base64.b64encode(content).decode("ascii"),
    }


class FakePort:
    user_id = 42

    def __init__(self, page: dict) -> None:
        self.page = page
        self.calls: list[dict] = []

    def export(self, **kwargs):
        self.calls.append(kwargs)
        return copy.deepcopy(self.page)


@pytest.mark.parametrize("capability_id", FINANCIAL_REPORT_EXPORTS)
@pytest.mark.parametrize("export_format", ["pdf", "xlsx"])
def test_each_fixed_report_export_returns_verified_binary(
    capability_id: str, export_format: str
) -> None:
    port = FakePort(_page(export_format))

    result = export_financial_report(
        capability_id, port, _request(capability_id, export_format=export_format)
    )

    assert result == {
        key: port.page[key]
        for key in (
            "filename",
            "format",
            "mimetype",
            "byte_count",
            "sha256",
            "content_base64",
        )
    }
    assert port.calls == [
        {
            "capability_id": capability_id,
            "company_id": 7,
            "date_from": (
                None
                if FINANCIAL_REPORT_EXPORTS[capability_id]["mode"] == "single"
                else "2025-01-01"
            ),
            "date_to": "2025-01-31",
            "format": export_format,
        }
    ]


@pytest.mark.parametrize(
    "change",
    [
        lambda request: request["parameters"].update(extra=True),
        lambda request: request["parameters"].update(format="PDF"),
        lambda request: request["parameters"].update(format=[]),
        lambda request: request["parameters"].update(date_from="2025-02-01"),
        lambda request: request["parameters"].update(date_to="2025-02-30"),
    ],
)
def test_export_range_request_is_exact_and_canonical(change) -> None:
    request = _request("report.trial_balance.export")
    change(request)

    with pytest.raises(FinancialReportError) as caught:
        validate_financial_report_export_request(
            "report.trial_balance.export", request
        )

    assert caught.value.code == "invalid_request"
    assert caught.value.exit_code == 2


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("company_visible", False),
        ("module_installed", False),
        ("access_allowed", False),
    ],
)
def test_export_runtime_gates_preserve_financial_report_errors(
    field: str, value: bool
) -> None:
    page = _page()
    page[field] = value
    if field != "access_allowed":
        page["access_allowed"] = False
    for key in ("filename", "mimetype", "sha256", "content_base64"):
        page[key] = None
    page["byte_count"] = 0

    with pytest.raises(FinancialReportError) as caught:
        export_financial_report(
            "report.trial_balance.export",
            FakePort(page),
            _request("report.trial_balance.export"),
        )

    assert caught.value.code == {
        "company_visible": "company_unavailable",
        "module_installed": "uninstalled",
        "access_allowed": "unauthorized",
    }[field]


@pytest.mark.parametrize(
    "change",
    [
        lambda page: page.update(filename="report.txt"),
        lambda page: page.update(mimetype="application/octet-stream"),
        lambda page: page.update(byte_count=1),
        lambda page: page.update(sha256="0" * 64),
        lambda page: page.update(content_base64=page["content_base64"] + "\n"),
        lambda page: page.update(
            content_base64=base64.b64encode(b"not a pdf").decode("ascii"),
            byte_count=len(b"not a pdf"),
            sha256=hashlib.sha256(b"not a pdf").hexdigest(),
        ),
    ],
)
def test_export_rejects_unverified_metadata_or_content(change) -> None:
    page = _page()
    change(page)

    with pytest.raises(FinancialReportError) as caught:
        export_financial_report(
            "report.trial_balance.export",
            FakePort(page),
            _request("report.trial_balance.export"),
        )

    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8
