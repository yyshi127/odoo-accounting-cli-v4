from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from odoo_accounting_cli_v4.capabilities.accounting_delivery import (
    ACCOUNTING_DELIVERY_CAPABILITY_IDS,
    AccountingDeliveryError,
    execute_accounting_delivery,
    validate_accounting_delivery_request,
)

REQUEST_ID = "7bc39413-0d69-4092-9319-795d33f3167c"
PARAMETERS: dict[str, dict[str, Any]] = {
    "invoice.send.inspect": {"move_ids": [32, 31]},
    "invoice.send": {"move_ids": [32, 31]},
    "payment.receipt.send.inspect": {"payment_ids": [42, 41]},
    "payment.receipt.send": {"payment_ids": [42, 41]},
    "report.customer_statement.send": {
        "partner_ids": [22, 21],
        "date_from": "2026-08-01",
        "date_to": "2026-08-31",
    },
    "report.followup.send": {
        "partner_ids": [22, 21],
        "as_of": "2026-08-31",
    },
    "invoice.followup.update": {"move_id": 31, "no_followup": True},
}


def _request(capability_id: str) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": deepcopy(PARAMETERS[capability_id]),
    }


def _inspection(record_ids: list[int]) -> dict[str, Any]:
    return {
        "records": [
            {
                "record_id": record_id,
                "partner_id": record_id + 100,
                "recipient_emails": [f"accounts-{record_id}@example.com"],
                "template_id": 4,
                "report_id": 5,
                "sending_methods": ["email"],
                "warnings": [],
                "sendable": True,
            }
            for record_id in record_ids
        ]
    }


def _result(capability_id: str) -> dict[str, Any]:
    if capability_id.endswith(".inspect"):
        ids = [31, 32] if capability_id.startswith("invoice") else [41, 42]
        return _inspection(ids)
    if capability_id == "invoice.followup.update":
        return {"record_id": 31, "no_followup": True}
    ids = (
        [21, 22]
        if capability_id.startswith("report.")
        else ([31, 32] if capability_id.startswith("invoice") else [41, 42])
    )
    return {"record_ids": ids, "processed_count": len(ids)}


class FakePort:
    user_id = 5

    def __init__(
        self,
        capability_id: str,
        *,
        page_overrides: dict[str, Any] | None = None,
    ) -> None:
        self.capability_id = capability_id
        self.page_overrides = deepcopy(page_overrides or {})
        self.calls: list[dict[str, Any]] = []

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(deepcopy(kwargs))
        page = {
            "user_id": 5,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "idempotent_replay": False,
            "result": _result(self.capability_id),
        }
        page.update(deepcopy(self.page_overrides))
        return page


def _execute(capability_id: str, port: FakePort | None = None) -> dict[str, Any]:
    selected = port or FakePort(capability_id)
    if capability_id.endswith(".inspect"):
        return execute_accounting_delivery(
            selected, capability_id, _request(capability_id)
        )
    return execute_accounting_delivery(
        selected,
        capability_id,
        _request(capability_id),
        "delivery:key-0001",
        capability_id,
    )


@pytest.mark.parametrize("capability_id", sorted(ACCOUNTING_DELIVERY_CAPABILITY_IDS))
def test_requests_normalize_targets_and_dispatch_closed_parameters(
    capability_id: str,
) -> None:
    request_id, context, normalized = validate_accounting_delivery_request(
        capability_id, _request(capability_id)
    )
    assert request_id == REQUEST_ID
    assert context["company_id"] == 7
    if capability_id.endswith("followup.update"):
        target = 31
        assert normalized == {
            "record_id": target,
            "no_followup": True,
        }
    else:
        assert normalized["record_ids"] == sorted(normalized["record_ids"])

    port = FakePort(capability_id)
    assert _execute(capability_id, port) == {
        "idempotent_replay": False,
        "result": _result(capability_id),
    }
    assert port.calls == [
        {
            "capability_id": capability_id,
            "company_id": 7,
            "parameters": normalized,
            "idempotency_key": (
                None if capability_id.endswith(".inspect") else "delivery:key-0001"
            ),
        }
    ]


@pytest.mark.parametrize(
    ("capability_id", "parameters", "record_ids"),
    (
        ("invoice.send.inspect", {"move_id": 31}, [31]),
        ("invoice.send", {"move_id": 31}, [31]),
        ("payment.receipt.send.inspect", {"payment_id": 41}, [41]),
        ("payment.receipt.send", {"payment_id": 41}, [41]),
        (
            "report.customer_statement.send",
            {
                "partner_id": 21,
                "date_from": "2026-08-01",
                "date_to": "2026-08-31",
            },
            [21],
        ),
        (
            "report.followup.send",
            {"partner_id": 21, "as_of": "2026-08-31"},
            [21],
        ),
    ),
)
def test_single_targets_normalize_to_record_ids(
    capability_id: str, parameters: dict[str, Any], record_ids: list[int]
) -> None:
    request = _request(capability_id)
    request["parameters"] = parameters
    _, _, normalized = validate_accounting_delivery_request(capability_id, request)
    assert normalized["record_ids"] == record_ids


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    (
        ("invoice.send", {"move_id": 31, "move_ids": [31, 32]}),
        ("invoice.send", {"move_ids": [31]}),
        ("invoice.send", {"move_ids": [31, 31]}),
        ("invoice.send", {"move_ids": list(range(1, 102))}),
        ("payment.receipt.send.inspect", {"payment_ids": [True, 42]}),
        (
            "report.customer_statement.send",
            {
                "partner_id": 21,
                "date_from": "2026-09-01",
                "date_to": "2026-08-31",
            },
        ),
        (
            "report.followup.send",
            {"partner_id": 21, "as_of": "2026/08/31"},
        ),
        (
            "invoice.followup.update",
            {"move_id": 31, "no_followup": 1},
        ),
    ),
)
def test_requests_reject_open_or_invalid_parameters(
    capability_id: str, parameters: dict[str, Any]
) -> None:
    request = _request(capability_id)
    request["parameters"] = parameters
    with pytest.raises(AccountingDeliveryError) as caught:
        validate_accounting_delivery_request(capability_id, request)
    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize(
    ("idempotency_key", "confirmation", "code"),
    (
        (None, "invoice.send", "invalid_idempotency_key"),
        ("short", "invoice.send", "invalid_idempotency_key"),
        ("delivery key 0001", "invoice.send", "invalid_idempotency_key"),
        ("delivery:key-0001", None, "confirmation_required"),
        ("delivery:key-0001", "payment.receipt.send", "confirmation_required"),
    ),
)
def test_writes_require_safe_key_and_exact_confirmation(
    idempotency_key: str | None, confirmation: str | None, code: str
) -> None:
    port = FakePort("invoice.send")
    with pytest.raises(AccountingDeliveryError) as caught:
        execute_accounting_delivery(
            port,
            "invoice.send",
            _request("invoice.send"),
            idempotency_key,
            confirmation,
        )
    assert caught.value.code == code
    assert port.calls == []


def test_inspections_reject_write_controls_and_replay() -> None:
    request = _request("invoice.send.inspect")
    with pytest.raises(AccountingDeliveryError) as caught:
        execute_accounting_delivery(
            FakePort("invoice.send.inspect"),
            "invoice.send.inspect",
            request,
            "delivery:key-0001",
            "invoice.send.inspect",
        )
    assert caught.value.code == "invalid_request"

    with pytest.raises(AccountingDeliveryError) as caught:
        _execute(
            "invoice.send.inspect",
            FakePort(
                "invoice.send.inspect",
                page_overrides={"idempotent_replay": True},
            ),
        )
    assert caught.value.code == "failed_validation"


@pytest.mark.parametrize(
    ("overrides", "code"),
    (
        (
            {"module_installed": False, "access_allowed": False, "result": None},
            "uninstalled",
        ),
        (
            {"company_visible": False, "access_allowed": False, "result": None},
            "company_unavailable",
        ),
        ({"access_allowed": False, "result": None}, "unauthorized"),
        ({"user_id": 6}, "failed_validation"),
        ({"unexpected": True}, "failed_validation"),
    ),
)
def test_page_scope_and_identity_fail_closed(
    overrides: dict[str, Any], code: str
) -> None:
    with pytest.raises(AccountingDeliveryError) as caught:
        _execute("invoice.send", FakePort("invoice.send", page_overrides=overrides))
    assert caught.value.code == code


def test_result_drift_fails_closed() -> None:
    inspection = _inspection([32, 31])
    with pytest.raises(AccountingDeliveryError) as caught:
        _execute(
            "invoice.send.inspect",
            FakePort(
                "invoice.send.inspect",
                page_overrides={"result": inspection},
            ),
        )
    assert caught.value.code == "failed_validation"

    bad_emails = _inspection([31, 32])
    bad_emails["records"][0]["recipient_emails"] = ["z@example.com", "a@example.com"]
    with pytest.raises(AccountingDeliveryError) as caught:
        _execute(
            "invoice.send.inspect",
            FakePort(
                "invoice.send.inspect",
                page_overrides={"result": bad_emails},
            ),
        )
    assert caught.value.code == "failed_validation"

    with pytest.raises(AccountingDeliveryError) as caught:
        _execute(
            "invoice.send",
            FakePort(
                "invoice.send",
                page_overrides={
                    "result": {"record_ids": [31, 32], "processed_count": 1}
                },
            ),
        )
    assert caught.value.code == "failed_validation"

    with pytest.raises(AccountingDeliveryError) as caught:
        _execute(
            "invoice.followup.update",
            FakePort(
                "invoice.followup.update",
                page_overrides={"result": {"record_id": 31, "no_followup": False}},
            ),
        )
    assert caught.value.code == "failed_validation"


def test_write_replay_is_explicit_and_result_remains_request_bound() -> None:
    result = _execute(
        "invoice.send",
        FakePort("invoice.send", page_overrides={"idempotent_replay": True}),
    )
    assert result == {
        "idempotent_replay": True,
        "result": {"record_ids": [31, 32], "processed_count": 2},
    }


def test_missing_records_and_bridge_value_errors_are_explicit() -> None:
    with pytest.raises(AccountingDeliveryError) as caught:
        _execute(
            "invoice.send",
            FakePort("invoice.send", page_overrides={"result": None}),
        )
    assert caught.value.code == "record_not_found"

    class BrokenPort(FakePort):
        def execute(self, **kwargs: Any) -> dict[str, Any]:
            raise ValueError("bad bridge value")

    with pytest.raises(AccountingDeliveryError) as caught:
        _execute("invoice.send", BrokenPort("invoice.send"))
    assert caught.value.code == "failed_validation"
