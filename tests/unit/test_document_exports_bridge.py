from __future__ import annotations

import pytest

from odoo_accounting_cli_v4.bridge.document_exports import OdooDocumentExportPort
from odoo_accounting_cli_v4.capabilities.document_exports import DOCUMENT_EXPORT_SPECS


def _page(capability_id: str) -> dict:
    return {
        "user_id": 42,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "record_visible": True,
        "applicable": True,
        "filename": "document.pdf",
        "format": "pdf",
        "mimetype": "application/pdf",
        "byte_count": 8,
        "sha256": "0" * 64,
        "content_base64": "JVBERi0=",
    }


@pytest.mark.parametrize("capability_id", sorted(DOCUMENT_EXPORT_SPECS))
def test_port_uses_one_fixed_action_and_preserves_the_frozen_id_key(
    capability_id: str,
) -> None:
    spec = DOCUMENT_EXPORT_SPECS[capability_id]
    expected_payload = {
        "capability_id": capability_id,
        "company_id": 7,
        spec["id_parameter"]: 37,
    }
    layout = "without_payments" if capability_id == "invoice.pdf.export" else None
    if layout is not None:
        expected_payload["layout"] = layout

    class Client:
        def invoke(self, action, payload):
            assert action == "ir.actions.report.fixed_document_export"
            assert payload == expected_payload
            assert "model" not in payload
            assert "xml_id" not in payload
            return _page(capability_id)

    port = OdooDocumentExportPort(Client())

    assert port.export(
        capability_id=capability_id,
        company_id=7,
        target_id=37,
        layout=layout,
    ) == _page(capability_id)
    assert port.user_id == 42


def test_port_rejects_unknown_capability_and_noncanonical_page() -> None:
    class Client:
        def invoke(self, action, payload):
            return {**_page("invoice.pdf.export"), "extra": True}

    port = OdooDocumentExportPort(Client())
    with pytest.raises(ValueError, match="Unsupported"):
        port.export(
            capability_id="report.injected.pdf.export",
            company_id=7,
            target_id=37,
            layout=None,
        )
    with pytest.raises(ValueError, match="invalid document export"):
        port.export(
            capability_id="invoice.pdf.export",
            company_id=7,
            target_id=37,
            layout="with_payments",
        )
    with pytest.raises(ValueError, match="No verified"):
        _ = port.user_id
