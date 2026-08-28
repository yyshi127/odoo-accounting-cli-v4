from __future__ import annotations

from copy import deepcopy
from hashlib import sha256

import pytest

from odoo_accounting_cli_v4.capabilities.core_writes import (
    CoreWriteError,
    execute_core_write,
    validate_core_write_request,
)

REQUEST_ID = "7bc39413-0d69-4092-9319-795d33f3167c"

CAPABILITY_IDS = (
    "asset.cancel",
    "asset.dispose",
    "asset.pause",
    "deferred_expense.generate_entries",
    "deferred_revenue.generate_entries",
    "multicurrency.revaluation.generate_entries",
    "reconciliation.automatic.run",
    "period.transfer.run",
    "localization.china.period_transfer.run",
)

PARAMETERS = {
    "asset.cancel": {"asset_id": 111},
    "asset.dispose": {
        "asset_id": 112,
        "date": "2026-08-31",
        "note": "Disposed after useful life",
    },
    "asset.pause": {
        "asset_id": 113,
        "date": "2026-08-31",
        "note": None,
    },
    "deferred_expense.generate_entries": {"date_to": "2026-08-31"},
    "deferred_revenue.generate_entries": {"date_to": "2026-08-31"},
    "multicurrency.revaluation.generate_entries": {
        "date": "2026-08-31",
        "reversal_date": "2026-09-01",
        "journal_id": 11,
        "expense_provision_account_id": 31,
        "income_provision_account_id": 32,
    },
    "reconciliation.automatic.run": {"line_ids": [203, 201, 202]},
    "period.transfer.run": {
        "transfer_model_id": 121,
        "run_date": "2026-08-31",
    },
    "localization.china.period_transfer.run": {"run_date": "2026-08-31"},
}


def _request(capability_id: str) -> dict:
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "zh_CN",
            "timezone": "Asia/Shanghai",
        },
        "parameters": deepcopy(PARAMETERS[capability_id]),
    }


def _key(capability_id: str) -> str:
    parameters = PARAMETERS[capability_id]
    if capability_id in {"asset.cancel", "asset.dispose"}:
        return f"{capability_id}:{parameters['asset_id']}"
    if capability_id == "asset.pause":
        return f"asset.pause:{parameters['asset_id']}:{parameters['date']}"
    if capability_id.startswith("deferred_"):
        return f"{capability_id}:{parameters['date_to']}"
    if capability_id == "multicurrency.revaluation.generate_entries":
        return f"{capability_id}:{parameters['date']}"
    if capability_id == "reconciliation.automatic.run":
        serialized = ",".join(str(item) for item in sorted(parameters["line_ids"]))
        digest = sha256(serialized.encode()).hexdigest()[:32]
        return f"reconciliation.automatic.run:{digest}"
    if capability_id == "period.transfer.run":
        return (
            f"period.transfer.run:{parameters['transfer_model_id']}:"
            f"{parameters['run_date']}"
        )
    return f"localization.china.period_transfer.run:7:{parameters['run_date']}"


def _result(capability_id: str, **changes) -> dict:
    parameters = PARAMETERS[capability_id]
    if capability_id.startswith("asset."):
        result = {
            "model": "account.asset",
            "id": parameters["asset_id"],
            "name": "Office laptop",
            "state": {
                "asset.cancel": "cancelled",
                "asset.dispose": "close",
                "asset.pause": "paused",
            }[capability_id],
            "company_id": 7,
            "move_type": None,
            "source_id": None,
            "line_ids": [],
            "partial_reconcile_ids": [],
            "full_reconcile_id": None,
            "reconciled": False,
        }
    elif capability_id == "reconciliation.automatic.run":
        result = {
            "model": "account.move.line",
            "id": None,
            "name": None,
            "state": "reconciled",
            "company_id": 7,
            "move_type": None,
            "source_id": None,
            "line_ids": [201, 202, 203, 204],
            "partial_reconcile_ids": [301],
            "full_reconcile_id": 401,
            "reconciled": True,
        }
    elif capability_id in {
        "period.transfer.run",
        "localization.china.period_transfer.run",
    }:
        source_id = parameters.get("transfer_model_id", 122)
        result = {
            "model": "account.move",
            "id": 801,
            "name": "MISC/2026/0008",
            "state": "draft",
            "company_id": 7,
            "move_type": "entry",
            "source_id": source_id,
            "line_ids": [921, 922],
            "partial_reconcile_ids": [],
            "full_reconcile_id": None,
            "reconciled": False,
        }
    else:
        result = {
            "model": "account.move",
            "id": 701,
            "name": "MISC/2026/0007",
            "state": "posted",
            "company_id": 7,
            "move_type": "entry",
            "source_id": 700,
            "line_ids": [901, 902, 903, 904],
            "partial_reconcile_ids": [],
            "full_reconcile_id": None,
            "reconciled": False,
        }
    result.update(changes)
    return result


class FakePort:
    def __init__(self, capability_id: str, *, result: dict | None = None) -> None:
        self._user_id = 42
        self.result = deepcopy(_result(capability_id) if result is None else result)
        self.calls: list[dict] = []

    @property
    def user_id(self) -> int:
        return self._user_id

    def execute(self, **payload) -> dict:
        self.calls.append(deepcopy(payload))
        return {
            "user_id": self._user_id,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "idempotent_replay": False,
            "result": deepcopy(self.result),
        }


@pytest.mark.parametrize("capability_id", CAPABILITY_IDS)
def test_each_extended_write_validates_and_calls_one_fixed_port_operation(
    capability_id: str,
) -> None:
    port = FakePort(capability_id)

    data = execute_core_write(
        port,
        capability_id,
        _request(capability_id),
        _key(capability_id),
        capability_id,
    )

    expected_parameters = deepcopy(PARAMETERS[capability_id])
    if capability_id == "reconciliation.automatic.run":
        expected_parameters["line_ids"] = sorted(expected_parameters["line_ids"])
    assert data == {"idempotent_replay": False, "result": _result(capability_id)}
    assert port.calls == [
        {
            "capability_id": capability_id,
            "company_id": 7,
            "idempotency_key": _key(capability_id),
            "confirmation": capability_id,
            "parameters": expected_parameters,
        }
    ]


@pytest.mark.parametrize("capability_id", CAPABILITY_IDS)
def test_extended_write_parameters_are_closed(capability_id: str) -> None:
    request = _request(capability_id)
    request["parameters"]["extra"] = True

    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request(capability_id, request)

    assert caught.value.code == "invalid_request"
    assert caught.value.exit_code == 2


@pytest.mark.parametrize(
    ("capability_id", "field", "value"),
    [
        ("asset.cancel", "asset_id", 0),
        ("asset.dispose", "date", "2026-08-32"),
        ("asset.dispose", "note", ""),
        ("asset.pause", "note", "x" * 201),
        ("deferred_expense.generate_entries", "date_to", "2026-08-30"),
        ("deferred_revenue.generate_entries", "date_to", "2026-09-29"),
        (
            "multicurrency.revaluation.generate_entries",
            "reversal_date",
            "2026-08-31",
        ),
        ("multicurrency.revaluation.generate_entries", "journal_id", True),
        ("period.transfer.run", "transfer_model_id", -1),
        ("period.transfer.run", "run_date", "31-08-2026"),
        ("localization.china.period_transfer.run", "run_date", "2026-02-30"),
    ],
)
def test_extended_write_rejects_values_outside_the_closed_contract(
    capability_id: str, field: str, value
) -> None:
    request = _request(capability_id)
    request["parameters"][field] = value

    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request(capability_id, request)

    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize(
    "line_ids",
    [
        [201],
        list(range(1, 202)),
        [201, 201],
        [201, True],
    ],
)
def test_automatic_reconciliation_requires_two_to_two_hundred_unique_ids(
    line_ids: list,
) -> None:
    request = _request("reconciliation.automatic.run")
    request["parameters"]["line_ids"] = line_ids

    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request("reconciliation.automatic.run", request)

    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize("capability_id", CAPABILITY_IDS)
def test_extended_write_idempotency_keys_are_deterministic(
    capability_id: str,
) -> None:
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            FakePort(capability_id),
            capability_id,
            _request(capability_id),
            "wrong-key-0001",
            capability_id,
        )

    assert caught.value.code == "invalid_idempotency_key"
    assert caught.value.exit_code == 2


def test_automatic_reconciliation_key_hashes_sorted_line_ids() -> None:
    expected = sha256(b"201,202,203").hexdigest()[:32]
    assert _key("reconciliation.automatic.run") == (
        f"reconciliation.automatic.run:{expected}"
    )


def test_extended_write_confirmation_must_equal_the_capability_id() -> None:
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            FakePort("asset.cancel"),
            "asset.cancel",
            _request("asset.cancel"),
            _key("asset.cancel"),
            "yes",
        )

    assert caught.value.code == "confirmation_required"


@pytest.mark.parametrize(
    ("capability_id", "change"),
    [
        ("asset.cancel", {"id": 999}),
        ("asset.dispose", {"state": "open"}),
        ("asset.pause", {"source_id": 113}),
        ("deferred_expense.generate_entries", {"source_id": None}),
        ("deferred_expense.generate_entries", {"line_ids": []}),
        ("deferred_revenue.generate_entries", {"state": "cancel"}),
        ("multicurrency.revaluation.generate_entries", {"move_type": None}),
        ("reconciliation.automatic.run", {"line_ids": [201, 202]}),
        ("reconciliation.automatic.run", {"partial_reconcile_ids": []}),
        ("reconciliation.automatic.run", {"reconciled": False}),
        ("period.transfer.run", {"source_id": 999}),
        ("period.transfer.run", {"state": "cancel"}),
        ("localization.china.period_transfer.run", {"source_id": None}),
        ("localization.china.period_transfer.run", {"move_type": "out_invoice"}),
    ],
)
def test_extended_write_results_fail_closed_on_business_drift(
    capability_id: str, change: dict
) -> None:
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            FakePort(capability_id, result=_result(capability_id, **change)),
            capability_id,
            _request(capability_id),
            _key(capability_id),
            capability_id,
        )

    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8


@pytest.mark.parametrize(
    "capability_id",
    ["period.transfer.run", "localization.china.period_transfer.run"],
)
def test_period_transfer_accepts_a_posted_move(capability_id: str) -> None:
    result = _result(capability_id, state="posted")

    data = execute_core_write(
        FakePort(capability_id, result=result),
        capability_id,
        _request(capability_id),
        _key(capability_id),
        capability_id,
    )

    assert data["result"] == result
