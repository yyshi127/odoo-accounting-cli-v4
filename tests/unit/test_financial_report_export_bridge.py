from __future__ import annotations

import pytest

from odoo_accounting_cli_v4.bridge.financial_reports import (
    OdooFinancialReportExportPort,
)


def _page() -> dict:
    return {
        "user_id": 42,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "filename": "general-ledger.pdf",
        "format": "pdf",
        "mimetype": "application/pdf",
        "byte_count": 8,
        "sha256": "0" * 64,
        "content_base64": "JVBERi0=",
    }


def test_export_port_uses_only_the_shared_fixed_action_and_exact_payload() -> None:
    class Client:
        def invoke(self, action, payload):
            assert action == "account.report.fixed_export"
            assert payload == {
                "capability_id": "report.general_ledger.export",
                "company_id": 7,
                "date_from": "2025-01-01",
                "date_to": "2025-01-31",
                "format": "pdf",
            }
            return _page()

    port = OdooFinancialReportExportPort(Client())

    assert port.export(
        capability_id="report.general_ledger.export",
        company_id=7,
        date_from="2025-01-01",
        date_to="2025-01-31",
        format="pdf",
    ) == _page()
    assert port.user_id == 42


@pytest.mark.parametrize(
    "capability_id,date_from",
    [
        ("report.customer_statement.export", "2025-01-01"),
        ("report.followup.export", None),
    ],
)
def test_partner_export_port_sends_one_partner_only_for_partner_reports(
    capability_id: str, date_from: str | None
) -> None:
    class Client:
        def invoke(self, action, payload):
            assert action == "account.report.fixed_export"
            assert payload == {
                "capability_id": capability_id,
                "company_id": 7,
                "date_from": date_from,
                "date_to": "2025-01-31",
                "format": "pdf",
                "partner_id": 17,
            }
            return _page()

    port = OdooFinancialReportExportPort(Client())

    assert (
        port.export(
            capability_id=capability_id,
            company_id=7,
            date_from=date_from,
            date_to="2025-01-31",
            format="pdf",
            partner_id=17,
        )
        == _page()
    )


@pytest.mark.parametrize("partner_id", [None, 0, True])
def test_partner_export_port_requires_a_positive_partner(partner_id: object) -> None:
    class Client:
        def invoke(self, action, payload):
            raise AssertionError("invalid partner payload must not reach the bridge")

    with pytest.raises(ValueError, match="partner_id must be a positive integer"):
        OdooFinancialReportExportPort(Client()).export(
            capability_id="report.customer_statement.export",
            company_id=7,
            date_from="2025-01-01",
            date_to="2025-01-31",
            format="pdf",
            partner_id=partner_id,
        )


def test_export_port_rejects_partner_for_an_unscoped_report() -> None:
    class Client:
        def invoke(self, action, payload):
            raise AssertionError(
                "unsupported partner payload must not reach the bridge"
            )

    with pytest.raises(ValueError, match="partner_id is unsupported"):
        OdooFinancialReportExportPort(Client()).export(
            capability_id="report.general_ledger.export",
            company_id=7,
            date_from="2025-01-01",
            date_to="2025-01-31",
            format="pdf",
            partner_id=17,
        )


def test_export_port_rejects_unknown_capability_and_noncanonical_page() -> None:
    class Client:
        def invoke(self, action, payload):
            return {**_page(), "extra": True}

    port = OdooFinancialReportExportPort(Client())
    with pytest.raises(ValueError, match="Unsupported"):
        port.export(
            capability_id="report.unknown.export",
            company_id=7,
            date_from=None,
            date_to="2025-01-31",
            format="pdf",
        )
    with pytest.raises(ValueError, match="invalid financial-report export"):
        port.export(
            capability_id="report.aged_payable.export",
            company_id=7,
            date_from=None,
            date_to="2025-01-31",
            format="pdf",
        )
    with pytest.raises(ValueError, match="No verified"):
        _ = port.user_id
