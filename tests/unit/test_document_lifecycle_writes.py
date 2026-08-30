from __future__ import annotations

import hashlib
import json
from copy import deepcopy

import pytest

from odoo_accounting_cli_v4.capabilities.core_writes import (
    CORE_WRITE_CAPABILITY_IDS,
    CoreWriteError,
    execute_core_write,
    validate_core_write_request,
)

_CAPABILITIES = (
    "invoice.update",
    "invoice.lines.replace",
    "invoice.cancel",
    "invoice.reset_to_draft",
    "journal_entry.update",
    "journal_entry.lines.replace",
    "journal_entry.cancel",
    "journal_entry.reset_to_draft",
)
_CONTENT_CAPABILITIES = {
    "invoice.update",
    "invoice.lines.replace",
    "journal_entry.update",
    "journal_entry.lines.replace",
}
_PARAMETERS = {
    "invoice.update": {
        "move_id": 101,
        "changes": {
            "partner_id": 21,
            "invoice_date": "2026-08-26",
            "date": "2026-08-27",
            "payment_term_id": None,
            "reference": "发票参考",
            "payment_reference": None,
        },
    },
    "invoice.lines.replace": {
        "move_id": 102,
        "lines": [
            {
                "name": "会计服务",
                "product_id": None,
                "account_id": 31,
                "quantity": "0",
                "price_unit": "-125.50",
                "discount": "100",
                "tax_ids": [8, 9],
            }
        ],
    },
    "invoice.cancel": {"move_id": 103},
    "invoice.reset_to_draft": {"move_id": 104},
    "journal_entry.update": {
        "move_id": 105,
        "changes": {
            "date": "2026-08-26",
            "journal_id": 5,
            "reference": None,
        },
    },
    "journal_entry.lines.replace": {
        "move_id": 106,
        "lines": [
            {
                "name": "Debit",
                "account_id": 31,
                "partner_id": None,
                "debit": "100.00",
                "credit": "0",
            },
            {
                "name": "Credit",
                "account_id": 32,
                "partner_id": 21,
                "debit": "0",
                "credit": "100.00",
            },
        ],
    },
    "journal_entry.cancel": {"move_id": 107},
    "journal_entry.reset_to_draft": {"move_id": 108},
}


def _request(capability_id: str, parameters: dict | None = None) -> dict:
    return {
        "schema_version": "v1",
        "request_id": "7bc39413-0d69-4092-9319-795d33f3167c",
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "zh_CN",
            "timezone": "Asia/Shanghai",
        },
        "parameters": deepcopy(
            _PARAMETERS[capability_id] if parameters is None else parameters
        ),
    }


def _key(capability_id: str, parameters: dict | None = None) -> str:
    values = _PARAMETERS[capability_id] if parameters is None else parameters
    if capability_id not in _CONTENT_CAPABILITIES:
        return f"{capability_id}:{values['move_id']}"
    target = values["changes"] if capability_id.endswith(".update") else values["lines"]
    canonical = json.dumps(
        target,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()[:32]
    return f"{capability_id}:{values['move_id']}:{digest}"


def _result(capability_id: str, **changes) -> dict:
    is_invoice = capability_id.startswith("invoice.")
    state = "cancel" if capability_id.endswith(".cancel") else "draft"
    result = {
        "model": "account.move",
        "id": _PARAMETERS[capability_id]["move_id"],
        "name": "MISC/2026/0001",
        "state": state,
        "company_id": 7,
        "move_type": "out_invoice" if is_invoice else "entry",
        "source_id": None,
        "line_ids": [901, 902],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }
    result.update(changes)
    return result


class _Port:
    def __init__(
        self,
        capability_id: str,
        *,
        result: dict | None = None,
        idempotent_replay: bool = False,
    ) -> None:
        self.capability_id = capability_id
        self.result = deepcopy(_result(capability_id) if result is None else result)
        self.idempotent_replay = idempotent_replay
        self.calls: list[dict] = []

    @property
    def user_id(self) -> int:
        return 42

    def execute(self, **payload) -> dict:
        self.calls.append(deepcopy(payload))
        return {
            "user_id": 42,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "idempotent_replay": self.idempotent_replay,
            "result": deepcopy(self.result),
        }


def test_document_lifecycle_capability_set_is_registered() -> None:
    assert set(_CAPABILITIES) <= CORE_WRITE_CAPABILITY_IDS


@pytest.mark.parametrize("capability_id", _CAPABILITIES)
def test_each_document_lifecycle_contract_calls_the_fixed_port(
    capability_id: str,
) -> None:
    port = _Port(capability_id)
    parameters = deepcopy(_PARAMETERS[capability_id])

    data = execute_core_write(
        port,
        capability_id,
        _request(capability_id),
        _key(capability_id),
        capability_id,
    )

    assert data == {
        "idempotent_replay": False,
        "result": _result(capability_id),
    }
    assert port.calls == [
        {
            "capability_id": capability_id,
            "company_id": 7,
            "idempotency_key": _key(capability_id),
            "confirmation": capability_id,
            "parameters": parameters,
        }
    ]


def test_content_key_uses_the_normalized_unicode_target_only() -> None:
    first = deepcopy(_PARAMETERS["invoice.update"])
    first["changes"] = {
        "reference": "发票参考",
        "partner_id": 21,
    }
    second = deepcopy(first)
    second["changes"] = {
        "partner_id": 21,
        "reference": "发票参考",
    }
    expected = _key("invoice.update", first)

    for parameters in (first, second):
        execute_core_write(
            _Port("invoice.update"),
            "invoice.update",
            _request("invoice.update", parameters),
            expected,
            "invoice.update",
        )


def test_invoice_accounting_date_is_forwarded_and_changes_the_update_key() -> None:
    first = {"move_id": 101, "changes": {"date": "2026-08-27"}}
    second = {"move_id": 101, "changes": {"date": "2026-08-28"}}
    assert _key("invoice.update", first) != _key("invoice.update", second)

    for parameters in (first, second):
        port = _Port("invoice.update")
        execute_core_write(
            port,
            "invoice.update",
            _request("invoice.update", parameters),
            _key("invoice.update", parameters),
            "invoice.update",
        )
        assert port.calls[0]["parameters"] == parameters

    port = _Port("invoice.update")
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            port,
            "invoice.update",
            _request("invoice.update", second),
            _key("invoice.update", first),
            "invoice.update",
        )
    assert caught.value.code == "invalid_idempotency_key"
    assert port.calls == []


@pytest.mark.parametrize(
    ("capability_id", "parameters", "message"),
    [
        ("invoice.update", {"move_id": 1, "changes": {}}, "supported"),
        (
            "invoice.update",
            {"move_id": 1, "changes": {"unknown": 1}},
            "supported",
        ),
        (
            "invoice.update",
            {
                "move_id": 1,
                "changes": {
                    "invoice_date_due": "2026-08-31",
                    "payment_term_id": 3,
                },
            },
            "mutually exclusive",
        ),
        (
            "invoice.update",
            {"move_id": 1, "changes": {"reference": ""}},
            "1-200",
        ),
        (
            "invoice.lines.replace",
            {"move_id": 1, "lines": []},
            "between 1 and 500",
        ),
        (
            "invoice.lines.replace",
            {
                "move_id": 1,
                "lines": [
                    {
                        **_PARAMETERS["invoice.lines.replace"]["lines"][0],
                        "tax_ids": [9, 8],
                    }
                ],
            },
            "sorted unique",
        ),
        (
            "invoice.lines.replace",
            {
                "move_id": 1,
                "lines": [
                    {
                        **_PARAMETERS["invoice.lines.replace"]["lines"][0],
                        "quantity": "-1",
                    }
                ],
            },
            "unsigned",
        ),
        (
            "invoice.lines.replace",
            {
                "move_id": 1,
                "lines": [
                    {
                        **_PARAMETERS["invoice.lines.replace"]["lines"][0],
                        "discount": "100.01",
                    }
                ],
            },
            "between 0 and 100",
        ),
        (
            "journal_entry.update",
            {"move_id": 2, "changes": {}},
            "supported",
        ),
        (
            "journal_entry.update",
            {"move_id": 2, "changes": {"journal_id": True}},
            "positive integer",
        ),
        (
            "journal_entry.lines.replace",
            {
                "move_id": 2,
                "lines": _PARAMETERS["journal_entry.lines.replace"]["lines"][:1],
            },
            "balanced",
        ),
        (
            "journal_entry.lines.replace",
            {
                "move_id": 2,
                "lines": [
                    {
                        **_PARAMETERS["journal_entry.lines.replace"]["lines"][0],
                        "credit": "1",
                    },
                    _PARAMETERS["journal_entry.lines.replace"]["lines"][1],
                ],
            },
            "exactly one positive side",
        ),
    ],
)
def test_document_lifecycle_parameters_fail_closed(
    capability_id: str, parameters: dict, message: str
) -> None:
    with pytest.raises(CoreWriteError, match=message) as caught:
        validate_core_write_request(capability_id, _request(capability_id, parameters))
    assert caught.value.code == "invalid_request"
    assert caught.value.exit_code == 2


@pytest.mark.parametrize("capability_id", sorted(_CONTENT_CAPABILITIES))
@pytest.mark.parametrize("state", ["posted", "cancel"])
def test_content_replay_accepts_a_later_document_state(
    capability_id: str, state: str
) -> None:
    result = _result(capability_id, state=state)

    data = execute_core_write(
        _Port(capability_id, result=result, idempotent_replay=True),
        capability_id,
        _request(capability_id),
        _key(capability_id),
        capability_id,
    )

    assert data == {"idempotent_replay": True, "result": result}
    with pytest.raises(CoreWriteError, match="lifecycle"):
        execute_core_write(
            _Port(capability_id, result=result),
            capability_id,
            _request(capability_id),
            _key(capability_id),
            capability_id,
        )


@pytest.mark.parametrize(
    ("capability_id", "change"),
    [
        ("invoice.update", {"model": "account.payment"}),
        ("invoice.update", {"id": 999}),
        ("invoice.update", {"move_type": "entry"}),
        ("invoice.cancel", {"state": "draft"}),
        ("invoice.reset_to_draft", {"state": "cancel"}),
        ("journal_entry.update", {"move_type": "out_invoice"}),
        ("journal_entry.cancel", {"state": "posted"}),
        ("journal_entry.reset_to_draft", {"source_id": 10}),
    ],
)
def test_document_lifecycle_results_fail_closed_on_business_drift(
    capability_id: str, change: dict
) -> None:
    with pytest.raises(CoreWriteError, match="lifecycle") as caught:
        execute_core_write(
            _Port(capability_id, result=_result(capability_id, **change)),
            capability_id,
            _request(capability_id),
            _key(capability_id),
            capability_id,
        )
    assert caught.value.code == "failed_validation"


def test_document_lifecycle_requires_exact_key_and_confirmation() -> None:
    with pytest.raises(CoreWriteError) as wrong_key:
        execute_core_write(
            _Port("invoice.update"),
            "invoice.update",
            _request("invoice.update"),
            "invoice.update:101:wrong",
            "invoice.update",
        )
    assert wrong_key.value.code == "invalid_idempotency_key"

    with pytest.raises(CoreWriteError) as wrong_confirmation:
        execute_core_write(
            _Port("invoice.cancel"),
            "invoice.cancel",
            _request("invoice.cancel"),
            _key("invoice.cancel"),
            "yes",
        )
    assert wrong_confirmation.value.code == "confirmation_required"
