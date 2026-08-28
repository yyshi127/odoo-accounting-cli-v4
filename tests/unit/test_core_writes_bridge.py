from __future__ import annotations

from copy import deepcopy

import pytest

from odoo_accounting_cli_v4.bridge.core_writes import OdooCoreWritePort
from odoo_accounting_cli_v4.registry import load_registry

_EXTENDED_CAPABILITY_IDS = (
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
_EXTENDED_PARAMETERS = {
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
    "reconciliation.automatic.run": {"line_ids": [201, 202, 203]},
    "period.transfer.run": {
        "transfer_model_id": 121,
        "run_date": "2026-08-31",
    },
    "localization.china.period_transfer.run": {"run_date": "2026-08-31"},
}
_EXTENDED_KEYS = {
    "asset.cancel": "asset.cancel:111",
    "asset.dispose": "asset.dispose:112",
    "asset.pause": "asset.pause:113:2026-08-31",
    "deferred_expense.generate_entries": (
        "deferred_expense.generate_entries:2026-08-31"
    ),
    "deferred_revenue.generate_entries": (
        "deferred_revenue.generate_entries:2026-08-31"
    ),
    "multicurrency.revaluation.generate_entries": (
        "multicurrency.revaluation.generate_entries:2026-08-31"
    ),
    "reconciliation.automatic.run": (
        "reconciliation.automatic.run:ba1e24c4838156dc52bf728f0c4c5009"
    ),
    "period.transfer.run": "period.transfer.run:121:2026-08-31",
    "localization.china.period_transfer.run": (
        "localization.china.period_transfer.run:7:2026-08-31"
    ),
}
_EXTENDED_MODELS = {
    "asset.cancel": [
        "res.company",
        "account.asset",
        "account.move",
        "account.move.line",
    ],
    "asset.dispose": [
        "res.company",
        "account.asset",
        "asset.modify",
        "account.move",
        "account.move.line",
    ],
    "asset.pause": [
        "res.company",
        "account.asset",
        "asset.modify",
        "account.move",
        "account.move.line",
    ],
    "deferred_expense.generate_entries": [
        "res.company",
        "account.report",
        "account.deferred.expense.report.handler",
        "account.journal",
        "account.account",
        "account.move",
        "account.move.line",
    ],
    "deferred_revenue.generate_entries": [
        "res.company",
        "account.report",
        "account.deferred.revenue.report.handler",
        "account.journal",
        "account.account",
        "account.move",
        "account.move.line",
    ],
    "multicurrency.revaluation.generate_entries": [
        "res.company",
        "account.report",
        "account.multicurrency.revaluation.wizard",
        "account.journal",
        "account.account",
        "account.move",
        "account.move.line",
        "res.currency",
    ],
    "reconciliation.automatic.run": [
        "res.company",
        "account.auto.reconcile.wizard",
        "account.account",
        "account.move.line",
        "account.partial.reconcile",
        "account.full.reconcile",
    ],
    "period.transfer.run": [
        "res.company",
        "account.transfer.model",
        "account.transfer.model.line",
        "account.move",
        "account.move.line",
    ],
    "localization.china.period_transfer.run": [
        "res.company",
        "res.country",
        "account.transfer.model",
        "account.transfer.model.line",
        "account.move",
        "account.move.line",
    ],
}
_ASSET_ACL = [
    "account.asset:read",
    "account.asset:write",
    "account.move:read",
    "account.move:write",
    "account.move:create",
    "account.move:unlink",
    "account.move.line:read",
    "account.move.line:write",
    "account.move.line:create",
    "account.move.line:unlink",
]
_ASSET_MODIFY_ACL = [
    "account.asset:read",
    "account.asset:write",
    "asset.modify:create",
    *_ASSET_ACL[2:],
]
_DEFERRED_ACL = [
    "account.report:read",
    "account.journal:read",
    "account.account:read",
    "account.move:read",
    "account.move:create",
    "account.move:write",
    "account.move.line:read",
    "account.move.line:create",
    "account.move.line:write",
]
_TRANSFER_ACL = [
    "account.transfer.model:read",
    "account.transfer.model.line:read",
    "account.move:read",
    "account.move:create",
    "account.move:write",
    "account.move.line:read",
    "account.move.line:create",
    "account.move.line:write",
    "account.move.line:unlink",
]
_EXTENDED_ACL = {
    "asset.cancel": _ASSET_ACL,
    "asset.dispose": _ASSET_MODIFY_ACL,
    "asset.pause": _ASSET_MODIFY_ACL,
    "deferred_expense.generate_entries": _DEFERRED_ACL,
    "deferred_revenue.generate_entries": _DEFERRED_ACL,
    "multicurrency.revaluation.generate_entries": [
        "account.report:read",
        "account.journal:read",
        "account.account:read",
        "res.currency:read",
        "account.move:read",
        "account.move:create",
        "account.move:write",
        "account.move.line:read",
        "account.move.line:create",
        "account.move.line:write",
    ],
    "reconciliation.automatic.run": [
        "account.auto.reconcile.wizard:create",
        "account.account:read",
        "account.move.line:read",
        "account.move.line:write",
        "account.partial.reconcile:read",
        "account.partial.reconcile:create",
        "account.full.reconcile:read",
    ],
    "period.transfer.run": _TRANSFER_ACL,
    "localization.china.period_transfer.run": [
        "res.country:read",
        *_TRANSFER_ACL,
    ],
}


def _result() -> dict:
    return {
        "model": "account.move",
        "id": 101,
        "name": "INV/2026/0001",
        "state": "posted",
        "company_id": 7,
        "move_type": "out_invoice",
        "source_id": None,
        "line_ids": [501, 502],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }


def _page(**changes) -> dict:
    page = {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "idempotent_replay": False,
        "result": _result(),
    }
    page.update(changes)
    return page


def _extended_result(capability_id: str) -> dict:
    parameters = _EXTENDED_PARAMETERS[capability_id]
    if capability_id.startswith("asset."):
        return {
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
            "line_ids": [901, 902],
            "partial_reconcile_ids": [],
            "full_reconcile_id": None,
            "reconciled": False,
        }
    if capability_id == "reconciliation.automatic.run":
        return {
            "model": "account.move.line",
            "id": None,
            "name": None,
            "state": "reconciled",
            "company_id": 7,
            "move_type": None,
            "source_id": None,
            "line_ids": [201, 202, 203, 204],
            "partial_reconcile_ids": [301, 302],
            "full_reconcile_id": 401,
            "reconciled": True,
        }
    if capability_id in {
        "period.transfer.run",
        "localization.china.period_transfer.run",
    }:
        return {
            "model": "account.move",
            "id": 801,
            "name": "MISC/2026/0008",
            "state": "draft",
            "company_id": 7,
            "move_type": "entry",
            "source_id": parameters.get("transfer_model_id", 122),
            "line_ids": [921, 922],
            "partial_reconcile_ids": [],
            "full_reconcile_id": None,
            "reconciled": False,
        }
    return {
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


class Client:
    def __init__(self, page: dict) -> None:
        self.page = page
        self.calls: list[tuple[str, dict]] = []

    def invoke(self, action: str, payload: dict) -> dict:
        self.calls.append((action, payload))
        return self.page


def test_port_uses_the_single_fixed_action_and_exact_payload() -> None:
    client = Client(_page())
    port = OdooCoreWritePort(client)
    parameters = {"move_id": 101}

    page = port.execute(
        capability_id="invoice.post",
        company_id=7,
        idempotency_key="invoice.post:101",
        confirmation="invoice.post",
        parameters=parameters,
    )

    assert page == _page()
    assert port.user_id == 5
    assert client.calls == [
        (
            "accounting.core_write.execute",
            {
                "capability_id": "invoice.post",
                "company_id": 7,
                "idempotency_key": "invoice.post:101",
                "confirmation": "invoice.post",
                "parameters": {"move_id": 101},
            },
        )
    ]


def test_port_accepts_a_null_result_for_denied_or_missing_records() -> None:
    port = OdooCoreWritePort(Client(_page(result=None)))

    assert (
        port.execute(
            capability_id="invoice.post",
            company_id=7,
            idempotency_key="invoice.post:101",
            confirmation="invoice.post",
            parameters={"move_id": 101},
        )["result"]
        is None
    )
    assert port.user_id == 5


def test_port_forwards_asset_write_without_opening_the_bridge_contract() -> None:
    page = _page(
        result={
            "model": "account.asset",
            "id": 801,
            "name": "Office laptop [ODACV4:fixture]",
            "state": "draft",
            "company_id": 7,
            "move_type": None,
            "source_id": None,
            "line_ids": [],
            "partial_reconcile_ids": [],
            "full_reconcile_id": None,
            "reconciled": False,
        }
    )
    client = Client(page)
    port = OdooCoreWritePort(client)

    assert (
        port.execute(
            capability_id="asset.create",
            company_id=7,
            idempotency_key="asset-create-key-1",
            confirmation="asset.create",
            parameters={"closed": "upstream-validated"},
        )
        == page
    )
    assert client.calls[0][0] == "accounting.core_write.execute"
    assert client.calls[0][1]["capability_id"] == "asset.create"


@pytest.mark.parametrize("capability_id", _EXTENDED_CAPABILITY_IDS)
def test_port_forwards_each_extended_write_with_frozen_metadata(
    capability_id: str,
) -> None:
    parameters = deepcopy(_EXTENDED_PARAMETERS[capability_id])
    result = _extended_result(capability_id)
    page = _page(result=deepcopy(result))
    client = Client(page)
    port = OdooCoreWritePort(client)

    returned = port.execute(
        capability_id=capability_id,
        company_id=7,
        idempotency_key=_EXTENDED_KEYS[capability_id],
        confirmation=capability_id,
        parameters=parameters,
    )

    descriptor = load_registry().describe(capability_id)
    assert descriptor["access"] == "write"
    assert descriptor["handler_key"] == "core_write"
    assert descriptor["source"]["models"] == _EXTENDED_MODELS[capability_id]
    assert descriptor["requirements"]["groups"] == ["account.group_account_user"]
    assert descriptor["requirements"]["acl"] == _EXTENDED_ACL[capability_id]
    assert parameters == _EXTENDED_PARAMETERS[capability_id]
    assert returned == page
    assert returned["result"] == result
    assert returned["result"]["model"] in descriptor["source"]["models"]
    assert port.user_id == 5
    assert client.calls == [
        (
            "accounting.core_write.execute",
            {
                "capability_id": capability_id,
                "company_id": 7,
                "idempotency_key": _EXTENDED_KEYS[capability_id],
                "confirmation": capability_id,
                "parameters": _EXTENDED_PARAMETERS[capability_id],
            },
        )
    ]


@pytest.mark.parametrize(
    "page",
    [
        {},
        {**_page(), "extra": True},
        _page(user_id=True),
        _page(company_visible=1),
        _page(module_installed=1),
        _page(access_allowed=1),
        _page(idempotent_replay=1),
        _page(result=[]),
    ],
)
def test_port_rejects_malformed_pages_and_clears_user_identity(page: dict) -> None:
    client = Client(_page())
    port = OdooCoreWritePort(client)
    port.execute(
        capability_id="invoice.post",
        company_id=7,
        idempotency_key="invoice.post:101",
        confirmation="invoice.post",
        parameters={"move_id": 101},
    )
    client.page = page

    with pytest.raises(ValueError):
        port.execute(
            capability_id="invoice.post",
            company_id=7,
            idempotency_key="invoice.post:101",
            confirmation="invoice.post",
            parameters={"move_id": 101},
        )
    with pytest.raises(ValueError):
        _ = port.user_id
