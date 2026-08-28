from __future__ import annotations

from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge.core_object_reads import (
    ACTION,
    CAPABILITY_IDS,
    OdooCoreObjectReadPort,
)

EXPECTED_CAPABILITY_IDS = frozenset(
    {
        "partner.search",
        "partner.get",
        "account.account.get",
        "account.tag.get",
        "account.tag.list",
        "analytic.account.get",
        "analytic.account.search",
        "analytic.plan.get",
        "analytic.plan.list",
        "analytic.line.get",
        "analytic.line.search",
        "analytic.distribution_model.get",
        "analytic.distribution_model.list",
        "analytic.applicability.get",
        "analytic.applicability.list",
        "bank.statement.get",
        "bank.statement.search",
        "bank.transaction.get",
        "budget.get",
        "budget.search",
        "budget.line.get",
        "budget.line.list",
        "cash_rounding.get",
        "cash_rounding.list",
        "currency.get",
        "fiscal_position.get",
        "fiscal_position.search",
        "incoterm.get",
        "incoterm.list",
        "journal.get",
        "journal.group.get",
        "journal.group.list",
        "journal_item.get",
        "journal_item.search",
        "partner.accounting.get",
        "partner.bank_account.get",
        "partner.bank_account.search",
        "payment.method.get",
        "payment.method.list",
        "payment_term.get",
        "product.get",
        "product.search",
        "reconciliation.model.get",
        "reconciliation.model.list",
        "reconciliation.full.get",
        "reconciliation.full.list",
        "reconciliation.partial.get",
        "reconciliation.partial.list",
        "tax.get",
        "tax.group.get",
        "tax.group.list",
    }
)


class Client:
    def __init__(self, response: Any) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def invoke(self, action: str, payload: dict[str, Any]) -> Any:
        self.calls.append((action, payload))
        return self.response


def _page(**overrides: Any) -> dict[str, Any]:
    value = {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "cursor_found": True,
        "items": [{"id": 31}],
    }
    value.update(overrides)
    return value


def test_bridge_exports_only_the_fixed_core_object_read_contract() -> None:
    assert ACTION == "accounting.core_object.read"
    assert CAPABILITY_IDS == EXPECTED_CAPABILITY_IDS


@pytest.mark.parametrize("capability_id", sorted(EXPECTED_CAPABILITY_IDS))
def test_port_invokes_the_fixed_action_with_the_exact_payload(
    capability_id: str,
) -> None:
    client = Client(_page())
    port = OdooCoreObjectReadPort(client)
    parameters = {"object_id": 31}

    result = port.read(
        capability_id=capability_id,
        company_id=7,
        parameters=parameters,
    )

    assert result == _page()
    assert port.user_id == 5
    assert client.calls == [
        (
            ACTION,
            {
                "capability_id": capability_id,
                "company_id": 7,
                "parameters": parameters,
            },
        )
    ]


def test_port_rejects_an_unknown_capability_without_invoking_odoo() -> None:
    client = Client(_page())
    port = OdooCoreObjectReadPort(client)

    with pytest.raises(ValueError, match="Unsupported"):
        port.read(capability_id="res.partner.read", company_id=7, parameters={})

    assert client.calls == []


@pytest.mark.parametrize(
    "response",
    [
        None,
        _page(extra=True),
        _page(user_id=True),
        _page(company_visible=1),
        _page(module_installed=None),
        _page(access_allowed="yes"),
        _page(cursor_found=0),
        _page(items={}),
        _page(items=[31]),
    ],
)
def test_port_rejects_a_malformed_page_and_clears_verified_identity(
    response: Any,
) -> None:
    client = Client(_page())
    port = OdooCoreObjectReadPort(client)
    port.read(capability_id="journal.get", company_id=7, parameters={"journal_id": 31})
    client.response = response

    with pytest.raises(ValueError, match="invalid.*page"):
        port.read(
            capability_id="journal.get",
            company_id=7,
            parameters={"journal_id": 31},
        )
    with pytest.raises(ValueError, match="No verified"):
        _ = port.user_id
