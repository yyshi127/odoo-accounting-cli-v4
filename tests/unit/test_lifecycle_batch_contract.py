from __future__ import annotations

import hashlib
import io
import json
from copy import deepcopy
from typing import Any

import pytest

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.bridge.core_writes import OdooCoreWritePort
from odoo_accounting_cli_v4.capabilities.core_writes import (
    CoreWriteError,
    execute_core_write,
    validate_core_write_request,
)

REQUEST_ID = "728c170b-f028-4685-818d-e7be3f6ae01b"
COMPANY_ID = 7
MOVE_CAPABILITIES = (
    "invoice.post",
    "invoice.cancel",
    "invoice.reset_to_draft",
    "journal_entry.post",
    "journal_entry.cancel",
    "journal_entry.reset_to_draft",
)
PAYMENT_CAPABILITIES = (
    "payment.post",
    "payment.cancel",
    "payment.reset_to_draft",
)
LIFECYCLE_CAPABILITIES = MOVE_CAPABILITIES + PAYMENT_CAPABILITIES


def _fields(capability_id: str) -> tuple[str, str]:
    if capability_id in MOVE_CAPABILITIES:
        return "move_id", "move_ids"
    return "payment_id", "payment_ids"


def _request(capability_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
    del capability_id
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": COMPANY_ID,
            "user_login": "v4-agent",
            "language": "zh_CN",
            "timezone": "Asia/Shanghai",
        },
        "parameters": deepcopy(parameters),
    }


def _item(capability_id: str, record_id: int, **changes: Any) -> dict[str, Any]:
    if capability_id.startswith("payment."):
        model = "account.payment"
        move_type = None
        state = (
            "in_process"
            if capability_id.endswith(".post")
            else "canceled"
            if capability_id.endswith(".cancel")
            else "draft"
        )
    else:
        model = "account.move"
        move_type = "out_invoice" if capability_id.startswith("invoice.") else "entry"
        state = (
            "posted"
            if capability_id.endswith(".post")
            else "cancel"
            if capability_id.endswith(".cancel")
            else "draft"
        )
    result = {
        "model": model,
        "id": record_id,
        "name": f"Record {record_id}",
        "state": state,
        "company_id": COMPANY_ID,
        "move_type": move_type,
        "source_id": None,
        "line_ids": [record_id * 10 + 1, record_id * 10 + 2],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }
    result.update(changes)
    return result


def _batch_result(capability_id: str, record_ids: list[int]) -> dict[str, Any]:
    return {
        "items": [_item(capability_id, record_id) for record_id in record_ids],
        "processed_count": len(record_ids),
    }


def _page(result: dict[str, Any], *, replay: bool = False) -> dict[str, Any]:
    return {
        "user_id": 42,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "idempotent_replay": replay,
        "result": deepcopy(result),
    }


def _batch_key(capability_id: str, record_ids: list[int]) -> str:
    _, batch_field = _fields(capability_id)
    parameters = {batch_field: sorted(record_ids)}
    canonical = json.dumps(
        parameters, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()[:32]
    return f"{capability_id}:{COMPANY_ID}:{digest}"


def _singular_key(capability_id: str, record_id: int) -> str:
    return f"{capability_id}:{record_id}"


class _PagePort:
    user_id = 42

    def __init__(self, result: dict[str, Any], *, replay: bool = False) -> None:
        self.result = deepcopy(result)
        self.replay = replay
        self.calls: list[dict[str, Any]] = []

    def execute(self, **payload: Any) -> dict[str, Any]:
        self.calls.append(deepcopy(payload))
        return _page(self.result, replay=self.replay)


class _Client:
    def __init__(self, page: dict[str, Any]) -> None:
        self.page = deepcopy(page)
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((action, deepcopy(payload)))
        return deepcopy(self.page)


@pytest.mark.parametrize("capability_id", LIFECYCLE_CAPABILITIES)
def test_public_validator_sorts_each_lifecycle_batch(capability_id: str) -> None:
    _, batch_field = _fields(capability_id)

    _, context, normalized = validate_core_write_request(
        capability_id,
        _request(capability_id, {batch_field: [33, 31, 32]}),
    )

    assert context["company_id"] == COMPANY_ID
    assert normalized == {batch_field: [31, 32, 33]}


INVALID_BATCH_VALUES = (
    pytest.param([], id="empty"),
    pytest.param([31], id="single-item"),
    pytest.param(list(range(1, 102)), id="over-100"),
    pytest.param([31, 31], id="duplicate"),
    pytest.param([0, 31], id="non-positive"),
    pytest.param([True, 31], id="boolean-is-not-an-id"),
)


@pytest.mark.parametrize("capability_id", LIFECYCLE_CAPABILITIES)
@pytest.mark.parametrize("bad_ids", INVALID_BATCH_VALUES)
def test_public_validator_rejects_invalid_lifecycle_batches(
    capability_id: str, bad_ids: list[Any]
) -> None:
    _, batch_field = _fields(capability_id)

    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request(
            capability_id,
            _request(capability_id, {batch_field: bad_ids}),
        )

    assert caught.value.code == "invalid_request"
    assert caught.value.exit_code == 2


@pytest.mark.parametrize("capability_id", LIFECYCLE_CAPABILITIES)
def test_public_validator_rejects_mixed_singular_and_batch_ids(
    capability_id: str,
) -> None:
    singular_field, batch_field = _fields(capability_id)

    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request(
            capability_id,
            _request(
                capability_id,
                {singular_field: 31, batch_field: [31, 32]},
            ),
        )

    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize("capability_id", LIFECYCLE_CAPABILITIES)
def test_batch_key_is_order_independent_and_binds_the_complete_set(
    capability_id: str,
) -> None:
    _, batch_field = _fields(capability_id)
    expected_ids = [31, 33]
    key = _batch_key(capability_id, expected_ids)

    for supplied_ids in ([33, 31], [31, 33]):
        port = _PagePort(_batch_result(capability_id, expected_ids))
        data = execute_core_write(
            port,
            capability_id,
            _request(capability_id, {batch_field: supplied_ids}),
            key,
            capability_id,
        )
        assert data == {
            "idempotent_replay": False,
            "result": _batch_result(capability_id, expected_ids),
        }
        assert port.calls[0]["parameters"] == {batch_field: expected_ids}

    larger_port = _PagePort(_batch_result(capability_id, [31, 33, 35]))
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            larger_port,
            capability_id,
            _request(capability_id, {batch_field: [31, 33, 35]}),
            key,
            capability_id,
        )
    assert caught.value.code == "invalid_idempotency_key"
    assert larger_port.calls == []
    assert key != _batch_key(capability_id, [31, 33, 35])


@pytest.mark.parametrize("capability_id", ("invoice.post", "payment.post"))
def test_bridge_accepts_the_closed_sorted_batch_shape(capability_id: str) -> None:
    _, batch_field = _fields(capability_id)
    result = _batch_result(capability_id, [31, 33])
    client = _Client(_page(result, replay=True))
    port = OdooCoreWritePort(client)

    page = port.execute(
        capability_id=capability_id,
        company_id=COMPANY_ID,
        idempotency_key=_batch_key(capability_id, [31, 33]),
        confirmation=capability_id,
        parameters={batch_field: [31, 33]},
    )

    assert page["result"] == result
    assert page["idempotent_replay"] is True
    assert port.user_id == 42
    assert client.calls[0][0] == "accounting.core_write.execute"


@pytest.mark.parametrize("failure", ("unordered", "count"))
def test_bridge_rejects_malformed_batch_results(failure: str) -> None:
    result = _batch_result("invoice.post", [31, 33])
    if failure == "unordered":
        result["items"].reverse()
    else:
        result["processed_count"] = 3
    port = OdooCoreWritePort(_Client(_page(result)))

    with pytest.raises(ValueError, match="invalid core-write result"):
        port.execute(
            capability_id="invoice.post",
            company_id=COMPANY_ID,
            idempotency_key=_batch_key("invoice.post", [31, 33]),
            confirmation="invoice.post",
            parameters={"move_ids": [31, 33]},
        )


@pytest.mark.parametrize("capability_id", LIFECYCLE_CAPABILITIES)
@pytest.mark.parametrize("failure", ("unordered", "count", "model", "id"))
def test_capability_rejects_batch_result_drift(
    capability_id: str, failure: str
) -> None:
    _, batch_field = _fields(capability_id)
    result = _batch_result(capability_id, [31, 33])
    if failure == "unordered":
        result["items"].reverse()
    elif failure == "count":
        result["processed_count"] = 3
    elif failure == "model":
        result["items"][0]["model"] = (
            "account.move"
            if capability_id.startswith("payment.")
            else "account.payment"
        )
    else:
        result["items"][1]["id"] = 34

    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            _PagePort(result),
            capability_id,
            _request(capability_id, {batch_field: [31, 33]}),
            _batch_key(capability_id, [31, 33]),
            capability_id,
        )

    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8


@pytest.mark.parametrize("capability_id", LIFECYCLE_CAPABILITIES)
def test_cli_emits_batch_record_ids_and_processed_count(capability_id: str) -> None:
    _, batch_field = _fields(capability_id)
    record_ids = [31, 33]
    request = _request(capability_id, {batch_field: list(reversed(record_ids))})
    port = _PagePort(_batch_result(capability_id, record_ids))

    document = cli._execute_write_run(
        capability_id,
        "-",
        _batch_key(capability_id, record_ids),
        capability_id,
        stdin=io.StringIO(json.dumps(request)),
        port_factory=lambda _selected, _request: port,
    )

    assert document["data"] == {
        "idempotent_replay": False,
        "result": _batch_result(capability_id, record_ids),
    }
    assert document["odoo"]["record_ids"] == record_ids
    assert document["audit"]["verification"] == {
        "processed_count": 2,
        "idempotent_replay": False,
    }


@pytest.mark.parametrize("capability_id", LIFECYCLE_CAPABILITIES)
def test_cli_keeps_the_singular_lifecycle_contract(capability_id: str) -> None:
    singular_field, _ = _fields(capability_id)
    record_id = 31
    result = _item(capability_id, record_id)

    document = cli._execute_write_run(
        capability_id,
        "-",
        _singular_key(capability_id, record_id),
        capability_id,
        stdin=io.StringIO(
            json.dumps(_request(capability_id, {singular_field: record_id}))
        ),
        port_factory=lambda _selected, _request: _PagePort(result),
    )

    assert document["data"] == {
        "idempotent_replay": False,
        "result": result,
    }
    assert document["odoo"]["record_ids"] == [record_id]
    assert document["audit"]["verification"] == {
        "company_id": COMPANY_ID,
        "state": result["state"],
        "reconciled": False,
        "idempotent_replay": False,
    }
