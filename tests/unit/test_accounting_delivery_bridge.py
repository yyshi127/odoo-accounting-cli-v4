from __future__ import annotations

from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge.accounting_delivery import (
    ACTION,
    OdooAccountingDeliveryPort,
)


class Client:
    def __init__(self, page: dict[str, Any]) -> None:
        self.page = page
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((action, payload))
        return self.page


def _page(result: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "idempotent_replay": False,
        "result": result,
    }


def _inspect_result() -> dict[str, Any]:
    return {
        "records": [
            {
                "record_id": 11,
                "partner_id": 21,
                "recipient_emails": ["billing@example.com"],
                "template_id": 31,
                "report_id": 41,
                "sending_methods": ["email"],
                "warnings": [],
                "sendable": True,
            }
        ]
    }


@pytest.mark.parametrize(
    ("capability_id", "parameters", "result", "key"),
    [
        ("invoice.send.inspect", {"record_ids": [11]}, _inspect_result(), None),
        (
            "invoice.send",
            {"record_ids": [11, 12]},
            {"record_ids": [11, 12], "processed_count": 2},
            "invoice-send-key-0001",
        ),
        (
            "invoice.followup.update",
            {"record_id": 11, "no_followup": True},
            {"record_id": 11, "no_followup": True},
            "invoice-followup-key-0001",
        ),
    ],
)
def test_port_uses_one_fixed_action_and_closed_payload(
    capability_id: str,
    parameters: dict[str, Any],
    result: dict[str, Any],
    key: str | None,
) -> None:
    client = Client(_page(result))
    port = OdooAccountingDeliveryPort(client)

    assert (
        port.execute(
            capability_id=capability_id,
            company_id=7,
            parameters=parameters,
            idempotency_key=key,
        )
        == client.page
    )
    assert port.user_id == 5
    assert client.calls == [
        (
            ACTION,
            {
                "capability_id": capability_id,
                "company_id": 7,
                "parameters": parameters,
                "idempotency_key": key,
            },
        )
    ]


def test_port_does_not_expose_user_id_after_an_invalid_page() -> None:
    bad = _page(_inspect_result())
    bad["extra"] = True
    port = OdooAccountingDeliveryPort(Client(bad))

    with pytest.raises(ValueError):
        _ = port.user_id
    with pytest.raises(ValueError):
        port.execute(
            capability_id="invoice.send.inspect",
            company_id=7,
            parameters={"record_ids": [11]},
            idempotency_key=None,
        )
    with pytest.raises(ValueError):
        _ = port.user_id


@pytest.mark.parametrize(
    "mutation",
    [
        lambda result: result["records"][0].update(partner_id=None),
        lambda result: result["records"][0].update(recipient_emails=[""]),
        lambda result: result["records"][0].update(warnings=["z", "a"]),
        lambda result: result["records"][0].update(record_id=12),
        lambda result: result["records"][0].update(extra=True),
    ],
)
def test_port_rejects_malformed_or_misaligned_inspect_records(mutation) -> None:
    result = _inspect_result()
    mutation(result)

    with pytest.raises(ValueError):
        OdooAccountingDeliveryPort(Client(_page(result))).execute(
            capability_id="invoice.send.inspect",
            company_id=7,
            parameters={"record_ids": [11]},
            idempotency_key=None,
        )


def test_port_rejects_partial_send_results_and_expanded_updates() -> None:
    with pytest.raises(ValueError):
        OdooAccountingDeliveryPort(
            Client(_page({"record_ids": [11, 12], "processed_count": 1}))
        ).execute(
            capability_id="invoice.send",
            company_id=7,
            parameters={"record_ids": [11, 12]},
            idempotency_key="invoice-send-key-0001",
        )

    with pytest.raises(ValueError):
        OdooAccountingDeliveryPort(
            Client(_page({"record_id": 11, "no_followup": True, "state": "posted"}))
        ).execute(
            capability_id="invoice.followup.update",
            company_id=7,
            parameters={"record_id": 11, "no_followup": True},
            idempotency_key="invoice-followup-key-0001",
        )
